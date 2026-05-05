from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco.policy_interface import (
    PolicyInferenceSession,
    SB3PolicyAdapter,
    SafetyConfig,
    SafetyFilter,
    write_trace_csv,
)
from peg_in_hole_mujoco.real_backend import (
    DryRunUR5ActionExecutor,
    RealCameraConfig,
    RealCameraObservationProvider,
    ZeroPolicyAdapter,
)


AGENTS = {
    "sac": SAC,
    "ppo": PPO,
    "a2c": A2C,
}


DEFAULTS = {
    "control_frequency_hz": 20.0,
    "image_width": 100,
    "image_height": 100,
    "max_steps": 50,
    "safety_max_action": 0.002,
    "safety_action_filter_alpha": 0.6,
    "safety_workspace_low": (0.45, -0.10, 0.60),
    "safety_workspace_high": (0.65, 0.15, 0.82),
    "peg_tip_pos": (0.55, 0.05, 0.78),
    "target_pos": (0.55, 0.05, 0.65),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run the real-robot policy interface without moving hardware.")
    parser.add_argument("--config", type=Path, default=Path("configs/real_ur5_dryrun.yaml"))
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--zero-policy", action="store_true")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("results/real_policy_dryrun_trace.csv"))
    parser.add_argument("--seed", type=int, default=130_000)
    parser.add_argument("--image-path", type=Path, default=None)
    parser.add_argument("--image-dir", type=Path, default=None)
    parser.add_argument("--control-frequency-hz", type=float, default=None)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--safety-max-action", type=float, default=None)
    parser.add_argument("--safety-action-filter-alpha", type=float, default=None)
    parser.add_argument("--safety-workspace-low", nargs=3, type=float, default=None)
    parser.add_argument("--safety-workspace-high", nargs=3, type=float, default=None)
    parser.add_argument("--peg-tip-pos", nargs=3, type=float, default=None)
    parser.add_argument("--target-pos", nargs=3, type=float, default=None)
    return parser.parse_args()


def parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return ""
    if text.startswith("[") and text.endswith("]"):
        return [parse_scalar(part) for part in text[1:-1].split(",")]
    try:
        if any(char in text.lower() for char in (".", "e")):
            return float(text)
        return int(text)
    except ValueError:
        return text.strip("'\"")


def load_simple_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    config: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        config[key.strip()] = parse_scalar(value)
    return config


def get_value(args: argparse.Namespace, config: dict[str, Any], name: str) -> Any:
    value = getattr(args, name, None)
    if value is not None:
        return value
    return config.get(name, DEFAULTS[name])


def get_tuple(args: argparse.Namespace, config: dict[str, Any], name: str) -> tuple[float, float, float]:
    value = get_value(args, config, name)
    if len(value) != 3:
        raise ValueError(f"{name} must contain three values.")
    return tuple(float(item) for item in value)


def make_policy(args: argparse.Namespace):
    if args.zero_policy:
        return ZeroPolicyAdapter()
    if args.model is None:
        raise ValueError("Provide --model or use --zero-policy.")
    model = AGENTS[args.agent].load(args.model, device=args.device)
    return SB3PolicyAdapter(model, deterministic=not args.stochastic)


def main() -> None:
    args = parse_args()
    config = load_simple_yaml(args.config)

    camera_config = RealCameraConfig(
        image_width=int(get_value(args, config, "image_width") if args.width is None else args.width),
        image_height=int(get_value(args, config, "image_height") if args.height is None else args.height),
        peg_tip_pos=get_tuple(args, config, "peg_tip_pos"),
        target_pos=get_tuple(args, config, "target_pos"),
    )
    observation_provider = RealCameraObservationProvider(
        config=camera_config,
        image_path=args.image_path,
        image_dir=args.image_dir,
    )
    action_executor = DryRunUR5ActionExecutor(
        observation_provider=observation_provider,
        max_steps=int(get_value(args, config, "max_steps")),
    )
    safety_filter = SafetyFilter(
        SafetyConfig(
            max_action=float(get_value(args, config, "safety_max_action")),
            workspace_low=get_tuple(args, config, "safety_workspace_low"),
            workspace_high=get_tuple(args, config, "safety_workspace_high"),
            action_filter_alpha=float(get_value(args, config, "safety_action_filter_alpha")),
        )
    )
    session = PolicyInferenceSession(
        observation_provider=observation_provider,
        action_executor=action_executor,
        policy=make_policy(args),
        safety_filter=safety_filter,
        control_frequency_hz=float(get_value(args, config, "control_frequency_hz")),
    )

    rows = []
    results = []
    try:
        for episode_index in range(args.episodes):
            result, episode_rows = session.run_episode(
                episode=episode_index + 1,
                seed=args.seed + episode_index,
            )
            rows.extend(episode_rows)
            results.append(result)
            print(
                "episode={episode} success={success} collision={collision} "
                "truncated={truncated} steps={steps} return={ret:.3f} "
                "dist_xy={dist_xy:.5f} dist_z={dist_z:.5f}".format(
                    episode=result.episode,
                    success=result.success,
                    collision=result.collision,
                    truncated=result.truncated,
                    steps=result.steps,
                    ret=result.episode_return,
                    dist_xy=result.final_dist_xy,
                    dist_z=result.final_dist_z,
                )
            )
    finally:
        session.close()

    write_trace_csv(args.output, rows)
    print(f"saved real dry-run trace to {args.output}")
    if results:
        print(f"episodes={len(results)}")
        print(f"actions_logged={sum(result.steps for result in results)}")


if __name__ == "__main__":
    main()
