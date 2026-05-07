from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco import (
    GuardedPolicyConfig,
    GuardedPolicyController,
    OracleControllerConfig,
    RealGuardStateProvider,
)
from peg_in_hole_mujoco.policy_interface import (
    ActionTransformResult,
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
    RealTargetCalibration,
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
    "include_near_hole_crop": False,
    "near_hole_crop_size": 64,
    "crop_xywh": None,
    "rotate_k": 0,
    "flip_horizontal": False,
    "flip_vertical": False,
    "max_steps": 50,
    "safety_max_action": 0.002,
    "safety_action_filter_alpha": 0.6,
    "safety_workspace_low": (0.45, -0.10, 0.60),
    "safety_workspace_high": (0.65, 0.15, 0.82),
    "peg_tip_pos": (0.55, 0.05, 0.78),
    "target_pos": (0.55, 0.05, 0.65),
    "target_calibration": None,
    "pose_trace": None,
    "tcp_pose_trace": None,
    "pose_frame": "robot_base",
    "tcp_to_peg_tip_xyz": (0.0, 0.0, -0.11),
    "guard_approach_height": 0.08,
    "guard_action_limit": 0.002,
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
    parser.add_argument("--pose-trace", type=Path, default=None)
    parser.add_argument("--tcp-pose-trace", type=Path, default=None)
    parser.add_argument("--pose-frame", default=None)
    parser.add_argument("--tcp-to-peg-tip-xyz", nargs=3, type=float, default=None)
    parser.add_argument("--control-frequency-hz", type=float, default=None)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--include-near-hole-crop", dest="include_near_hole_crop", action="store_true", default=None)
    parser.add_argument("--no-include-near-hole-crop", dest="include_near_hole_crop", action="store_false")
    parser.add_argument("--near-hole-crop-size", type=int, default=None)
    parser.add_argument("--crop-xywh", nargs=4, type=int, default=None)
    parser.add_argument("--rotate-k", type=int, default=None)
    parser.add_argument("--flip-horizontal", action="store_true", default=None)
    parser.add_argument("--flip-vertical", action="store_true", default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--safety-max-action", type=float, default=None)
    parser.add_argument("--safety-action-filter-alpha", type=float, default=None)
    parser.add_argument("--safety-workspace-low", nargs=3, type=float, default=None)
    parser.add_argument("--safety-workspace-high", nargs=3, type=float, default=None)
    parser.add_argument("--peg-tip-pos", nargs=3, type=float, default=None)
    parser.add_argument("--target-pos", nargs=3, type=float, default=None)
    parser.add_argument("--target-calibration", type=Path, default=None)
    parser.add_argument("--guarded-policy", action="store_true")
    parser.add_argument(
        "--guard-scenario-filter",
        choices=["none", "all", "geometry", "hard"],
        default="geometry",
    )
    parser.add_argument("--guard-scenario-name", default="real_ur5_dryrun")
    parser.add_argument(
        "--guard-scenario-level",
        choices=["none", "visual_camera_control", "full_light_geometry", "full_contact_light", "full"],
        default="full_light_geometry",
    )
    parser.add_argument("--guard-start-xy", type=float, default=0.060)
    parser.add_argument("--guard-start-z", type=float, default=0.080)
    parser.add_argument("--guard-risk-xy", type=float, default=0.0)
    parser.add_argument("--guard-blend", type=float, default=0.75)
    parser.add_argument("--guard-min-policy-steps", type=int, default=0)
    parser.add_argument("--guard-block-down-when-unaligned", action="store_true")
    parser.add_argument("--guard-release-on-high", action="store_true")
    parser.add_argument("--guard-action-gain", type=float, default=1.0)
    parser.add_argument("--guard-action-limit", type=float, default=None)
    parser.add_argument("--guard-approach-height", type=float, default=None)
    parser.add_argument("--guarded-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.002)
    parser.add_argument("--guarded-max-down-action", type=float, default=0.0015)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.002)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)
    return parser.parse_args()


def parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return ""
    if text.lower() in ("none", "null"):
        return None
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    if text.startswith("[") and text.endswith("]"):
        content = text[1:-1].strip()
        if not content:
            return []
        return [parse_scalar(part) for part in content.split(",")]
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


def get_optional_int_tuple(args: argparse.Namespace, config: dict[str, Any], name: str, size: int) -> tuple[int, ...] | None:
    value = get_value(args, config, name)
    if value is None:
        return None
    if len(value) != size:
        raise ValueError(f"{name} must contain {size} values.")
    return tuple(int(item) for item in value)


def get_tcp_to_peg_tip_xyz(
    args: argparse.Namespace,
    config: dict[str, Any],
) -> tuple[float, float, float]:
    if args.tcp_to_peg_tip_xyz is not None:
        value = args.tcp_to_peg_tip_xyz
    elif "tcp_to_peg_tip_xyz" in config:
        value = config["tcp_to_peg_tip_xyz"]
    elif "tool0_to_peg_tip_xyz" in config:
        value = config["tool0_to_peg_tip_xyz"]
    else:
        value = DEFAULTS["tcp_to_peg_tip_xyz"]
    if len(value) != 3:
        raise ValueError("tcp_to_peg_tip_xyz must contain three values.")
    return tuple(float(item) for item in value)


def get_target_calibration(
    args: argparse.Namespace,
    config: dict[str, Any],
) -> RealTargetCalibration | None:
    path = get_value(args, config, "target_calibration")
    if path is None:
        return None
    return RealTargetCalibration.from_file(path)


def make_policy(args: argparse.Namespace):
    if args.zero_policy:
        return ZeroPolicyAdapter()
    if args.model is None:
        raise ValueError("Provide --model or use --zero-policy.")
    model = AGENTS[args.agent].load(args.model, device=args.device)
    return SB3PolicyAdapter(model, deterministic=not args.stochastic)


def make_guarded_config(args: argparse.Namespace) -> GuardedPolicyConfig:
    return GuardedPolicyConfig(
        scenario_filter=args.guard_scenario_filter,
        guard_start_xy=args.guard_start_xy,
        guard_start_z=args.guard_start_z,
        guard_risk_xy=args.guard_risk_xy,
        guard_blend=args.guard_blend,
        guard_min_policy_steps=args.guard_min_policy_steps,
        guard_block_down_when_unaligned=args.guard_block_down_when_unaligned,
        guard_release_on_high=args.guard_release_on_high,
        oracle=OracleControllerConfig(
            mode="guarded_two_stage",
            action_gain=args.guard_action_gain,
            guarded_align_xy_tolerance=args.guarded_align_xy_tolerance,
            guarded_insert_xy_tolerance=args.guarded_insert_xy_tolerance,
            guarded_retract_xy_tolerance=args.guarded_retract_xy_tolerance,
            guarded_preinsert_height=args.guarded_preinsert_height,
            guarded_max_xy_action=args.guarded_max_xy_action,
            guarded_max_down_action=args.guarded_max_down_action,
            guarded_max_up_action=args.guarded_max_up_action,
            guarded_prediction_steps=args.guarded_prediction_steps,
        ),
    )


class RealGuardedActionTransformer:
    def __init__(
        self,
        config: GuardedPolicyConfig,
        state_provider: RealGuardStateProvider,
        scenario_name: str,
        scenario_level: str,
    ) -> None:
        self.controller = GuardedPolicyController(config)
        self.state_provider = state_provider
        self.scenario_name = scenario_name
        self.scenario_level = scenario_level
        self.guard_enabled = self.controller.scenario_uses_guard(scenario_name, scenario_level)

    def reset(self) -> None:
        self.controller.reset()

    def initial_diagnostics(self) -> dict[str, Any]:
        return {
            "guard_enabled": self.guard_enabled,
            "guard_active": False,
            "guard_should_activate": False,
            "guard_can_activate": False,
            "guard_activated": False,
            "guard_down_blocked": False,
            "guard_steps_since_reset": 0,
            "guard_min_policy_steps": self.controller.config.guard_min_policy_steps,
            "guard_dist_xy": float("nan"),
            "guard_z_above_target": float("nan"),
        }

    def transform(self, info: dict[str, Any], policy_action: np.ndarray) -> ActionTransformResult:
        step = self.controller.step_with_provider(
            self.state_provider,
            info,
            policy_action,
            scenario_name=self.scenario_name,
            scenario_level=self.scenario_level,
        )
        return ActionTransformResult(
            action=step.action,
            diagnostics={
                "guard_enabled": self.guard_enabled,
                "guard_active": step.guarded,
                "guard_should_activate": step.guard_should_activate,
                "guard_can_activate": step.guard_can_activate,
                "guard_activated": step.guard_activated,
                "guard_down_blocked": step.guard_down_blocked,
                "guard_steps_since_reset": step.guard_steps_since_reset,
                "guard_min_policy_steps": self.controller.config.guard_min_policy_steps,
                "guard_dist_xy": step.guard_dist_xy,
                "guard_z_above_target": step.guard_z_above_target,
                "policy_action": step.policy_action,
                "guarded_action": step.guarded_action,
                "final_action": step.action,
            },
        )


def main() -> None:
    args = parse_args()
    config = load_simple_yaml(args.config)

    camera_config = RealCameraConfig(
        image_width=int(get_value(args, config, "image_width") if args.width is None else args.width),
        image_height=int(get_value(args, config, "image_height") if args.height is None else args.height),
        include_near_hole_crop=bool(get_value(args, config, "include_near_hole_crop")),
        near_hole_crop_size=int(
            get_value(args, config, "near_hole_crop_size")
            if args.near_hole_crop_size is None
            else args.near_hole_crop_size
        ),
        crop_xywh=get_optional_int_tuple(args, config, "crop_xywh", 4),
        rotate_k=int(get_value(args, config, "rotate_k")),
        flip_horizontal=bool(get_value(args, config, "flip_horizontal")),
        flip_vertical=bool(get_value(args, config, "flip_vertical")),
        peg_tip_pos=get_tuple(args, config, "peg_tip_pos"),
        target_pos=get_tuple(args, config, "target_pos"),
    )
    target_calibration = get_target_calibration(args, config)
    observation_provider = RealCameraObservationProvider(
        config=camera_config,
        image_path=args.image_path,
        image_dir=args.image_dir,
        pose_trace_path=get_value(args, config, "pose_trace"),
        tcp_pose_trace_path=get_value(args, config, "tcp_pose_trace"),
        target_calibration=target_calibration,
        pose_frame=str(get_value(args, config, "pose_frame")),
        tcp_to_peg_tip_xyz=get_tcp_to_peg_tip_xyz(args, config),
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
    action_transformer = None
    if args.guarded_policy:
        guard_state_provider = RealGuardStateProvider(
            approach_height=float(get_value(args, config, "guard_approach_height")),
            action_limit=float(get_value(args, config, "guard_action_limit")),
        )
        action_transformer = RealGuardedActionTransformer(
            make_guarded_config(args),
            guard_state_provider,
            args.guard_scenario_name,
            args.guard_scenario_level,
        )
    session = PolicyInferenceSession(
        observation_provider=observation_provider,
        action_executor=action_executor,
        policy=make_policy(args),
        safety_filter=safety_filter,
        control_frequency_hz=float(get_value(args, config, "control_frequency_hz")),
        action_transformer=action_transformer,
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
            guard_steps = sum(int(row.get("guard_active", False)) for row in episode_rows)
            print(
                "episode={episode} success={success} collision={collision} "
                "truncated={truncated} steps={steps} guard_steps={guard_steps} return={ret:.3f} "
                "dist_xy={dist_xy:.5f} dist_z={dist_z:.5f}".format(
                    episode=result.episode,
                    success=result.success,
                    collision=result.collision,
                    truncated=result.truncated,
                    steps=result.steps,
                    guard_steps=guard_steps,
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
