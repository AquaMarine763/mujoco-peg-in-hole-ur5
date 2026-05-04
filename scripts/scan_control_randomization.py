from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from stable_baselines3 import SAC

from peg_in_hole_mujoco import PegInHoleMujocoEnv


@dataclass(frozen=True)
class ScanConfig:
    name: str
    scale_range: tuple[float, float] = (1.0, 1.0)
    noise_std_range: tuple[float, float] = (0.0, 0.0)
    delay_range: tuple[int, int] = (0, 0)
    filter_alpha_range: tuple[float, float] = (1.0, 1.0)


SCAN_CONFIGS = (
    ScanConfig("visual_camera_reference"),
    ScanConfig("scale_only", scale_range=(0.8, 1.2)),
    ScanConfig("noise_only", noise_std_range=(0.0, 0.0008)),
    ScanConfig("delay_only", delay_range=(0, 2)),
    ScanConfig("filter_only", filter_alpha_range=(0.55, 1.0)),
    ScanConfig("delay_filter", delay_range=(0, 2), filter_alpha_range=(0.55, 1.0)),
    ScanConfig(
        "default_control",
        scale_range=(0.8, 1.2),
        noise_std_range=(0.0, 0.0008),
        delay_range=(0, 2),
        filter_alpha_range=(0.55, 1.0),
    ),
    ScanConfig("high_noise", noise_std_range=(0.0, 0.0015)),
    ScanConfig("high_delay", delay_range=(0, 3)),
    ScanConfig(
        "high_all",
        scale_range=(0.75, 1.25),
        noise_std_range=(0.0, 0.0015),
        delay_range=(0, 3),
        filter_alpha_range=(0.4, 1.0),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan control randomization sensitivity.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/control_randomization_scan.csv"))
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=70_000)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    return parser.parse_args()


def make_env(args: argparse.Namespace, config: ScanConfig) -> PegInHoleMujocoEnv:
    level = (
        "visual_camera"
        if config.name == "visual_camera_reference"
        else "visual_camera_control"
    )
    return PegInHoleMujocoEnv(
        observation_mode="image",
        max_steps=args.max_steps,
        action_scale=args.action_scale,
        success_xy_tolerance=args.success_xy_tolerance,
        success_z_tolerance=args.success_z_tolerance,
        success_bonus=120.0,
        collision_penalty=300.0,
        progress_reward_scale=20.0,
        distance_reward_scale=2.0,
        action_alignment_scale=2.0,
        domain_randomization_level=level,
        control_action_scale_range=config.scale_range,
        control_action_noise_std_range=config.noise_std_range,
        control_action_delay_range=config.delay_range,
        control_action_filter_alpha_range=config.filter_alpha_range,
    )


def evaluate_config(args: argparse.Namespace, config: ScanConfig) -> dict[str, object]:
    env = make_env(args, config)
    model = SAC.load(args.model, env=env, device=args.device)
    successes = 0
    collisions = 0
    timeouts = 0
    returns: list[float] = []
    steps: list[int] = []

    try:
        for episode in range(args.episodes):
            obs, _ = env.reset(seed=args.seed + episode)
            episode_return = 0.0
            while True:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_return += reward
                if terminated or truncated:
                    break
            successes += int(info["insertion_success"])
            collisions += int(info["collision"])
            timeouts += int(truncated and not info["insertion_success"])
            returns.append(episode_return)
            steps.append(int(info["step_count"]))
    finally:
        env.close()

    return {
        "name": config.name,
        "episodes": args.episodes,
        "success_rate": successes / args.episodes,
        "collision_rate": collisions / args.episodes,
        "timeout_rate": timeouts / args.episodes,
        "mean_return": sum(returns) / len(returns),
        "mean_steps": sum(steps) / len(steps),
        "scale_range": f"{config.scale_range[0]}:{config.scale_range[1]}",
        "noise_std_range": f"{config.noise_std_range[0]}:{config.noise_std_range[1]}",
        "delay_range": f"{config.delay_range[0]}:{config.delay_range[1]}",
        "filter_alpha_range": (
            f"{config.filter_alpha_range[0]}:{config.filter_alpha_range[1]}"
        ),
    }


def main() -> None:
    args = parse_args()
    rows = []
    for config in SCAN_CONFIGS:
        row = evaluate_config(args, config)
        rows.append(row)
        print(
            "{name}: success={success_rate:.3f} collision={collision_rate:.3f} "
            "timeout={timeout_rate:.3f} return={mean_return:.3f} steps={mean_steps:.1f}".format(
                **row
            )
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved scan results to {args.output}")


if __name__ == "__main__":
    main()
