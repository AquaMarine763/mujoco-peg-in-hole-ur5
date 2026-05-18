from __future__ import annotations

import argparse
import csv
import itertools
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco import (
    GuardedPolicyConfig,
    GuardedPolicyController,
    MujocoGuardStateProvider,
    OracleControllerConfig,
    PegInHoleMujocoEnv,
)
from peg_in_hole_mujoco.sim_config import parse_args_with_config


AGENTS = {
    "sac": SAC,
    "ppo": PPO,
    "a2c": A2C,
}


CONTROL_RANGES = {
    "control_action_scale_range": (0.8, 1.2),
    "control_action_noise_std_range": (0.0, 0.0008),
    "control_action_delay_range": (0, 2),
    "control_action_filter_alpha_range": (0.55, 1.0),
}


CONTACT_LIGHT_RANGES = {
    "contact_friction_multiplier_range": (0.7, 1.3),
    "contact_solref_time_multiplier_range": (0.8, 1.25),
    "contact_solref_damping_multiplier_range": (0.8, 1.2),
    "contact_solimp_width_multiplier_range": (0.8, 1.2),
    "dynamics_joint_damping_multiplier_range": (0.8, 1.2),
    "dynamics_actuator_kp_multiplier_range": (0.8, 1.2),
}


@dataclass(frozen=True)
class Scenario:
    name: str
    level: str
    control_action_scale_range: tuple[float, float] = (1.0, 1.0)
    control_action_noise_std_range: tuple[float, float] = (0.0, 0.0)
    control_action_delay_range: tuple[int, int] = (0, 0)
    control_action_filter_alpha_range: tuple[float, float] = (1.0, 1.0)
    geometry_hole_center_xy_jitter: tuple[float, float] = (0.002, 0.002)
    geometry_fixture_height_jitter: float = 0.001
    geometry_table_height_jitter: float = 0.001
    geometry_hole_half_size_range: tuple[float, float] = (0.017, 0.021)
    geometry_peg_radius_range: tuple[float, float] = (0.0115, 0.0125)
    contact_friction_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solref_time_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solref_damping_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solimp_width_multiplier_range: tuple[float, float] = (1.0, 1.0)
    dynamics_joint_damping_multiplier_range: tuple[float, float] = (1.0, 1.0)
    dynamics_actuator_kp_multiplier_range: tuple[float, float] = (1.0, 1.0)


@dataclass(frozen=True)
class GuardCandidate:
    name: str
    scenario_filter: str = "geometry"
    guard_start_xy: float = 0.060
    guard_start_z: float = 0.100
    guard_risk_xy: float = 0.0
    guard_blend: float = 1.0
    guard_min_policy_steps: int = 0
    guard_block_down_when_unaligned: bool = False
    guard_release_on_high: bool = False
    guard_action_gain: float = 1.0
    guarded_align_xy_tolerance: float = 0.025
    guarded_insert_xy_tolerance: float = 0.005
    guarded_retract_xy_tolerance: float = 0.012
    guarded_preinsert_height: float = 0.0
    guarded_max_xy_action: float = 0.005
    guarded_max_down_action: float = 0.0035
    guarded_max_up_action: float = 0.005
    guarded_prediction_steps: float = 1.0
    guarded_oracle_mode: str = "guarded_two_stage"


CORE_SCENARIOS = (
    Scenario("clean", "none"),
    Scenario("visual_camera", "visual_camera"),
    Scenario("visual_camera_control", "visual_camera_control", **CONTROL_RANGES),
    Scenario("full_light_geometry", "full_light_geometry", **CONTROL_RANGES),
    Scenario(
        "full_contact_light",
        "full_contact_light",
        **CONTROL_RANGES,
        **CONTACT_LIGHT_RANGES,
    ),
)


HARD_BUCKET_SCENARIO = Scenario(
    "hard_full_light_bucket",
    "full_light_geometry",
    control_action_scale_range=(0.8, 1.1),
    control_action_noise_std_range=(0.0, 0.00025),
    control_action_delay_range=(2, 2),
    control_action_filter_alpha_range=(0.55, 0.70),
)


BASE_GUARD = GuardCandidate("guard_xy060_z100_blend100_down0035_align025")


FOCUSED_CANDIDATES = (
    GuardCandidate("no_guard", scenario_filter="none"),
    BASE_GUARD,
    GuardCandidate("guard_xy040_z100_blend100_down0035_align025", guard_start_xy=0.040),
    GuardCandidate("guard_xy050_z100_blend100_down0035_align025", guard_start_xy=0.050),
    GuardCandidate("guard_xy070_z100_blend100_down0035_align025", guard_start_xy=0.070),
    GuardCandidate("guard_xy060_z060_blend100_down0035_align025", guard_start_z=0.060),
    GuardCandidate("guard_xy060_z080_blend100_down0035_align025", guard_start_z=0.080),
    GuardCandidate("guard_xy060_z100_blend075_down0035_align025", guard_blend=0.75),
    GuardCandidate("guard_xy060_z100_blend050_down0035_align025", guard_blend=0.50),
    GuardCandidate("guard_xy060_z100_blend100_down0025_align025", guarded_max_down_action=0.0025),
    GuardCandidate("guard_xy060_z100_blend100_down0045_align025", guarded_max_down_action=0.0045),
    GuardCandidate("guard_xy060_z100_blend100_down0035_align020", guarded_align_xy_tolerance=0.020),
    GuardCandidate("guard_xy060_z100_blend100_down0035_align015", guarded_align_xy_tolerance=0.015),
)


SMOKE_CANDIDATES = (
    FOCUSED_CANDIDATES[0],
    FOCUSED_CANDIDATES[1],
    FOCUSED_CANDIDATES[3],
    FOCUSED_CANDIDATES[6],
    FOCUSED_CANDIDATES[7],
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan deployment-time guarded insertion parameters."
    )
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=91_000)
    parser.add_argument("--output-csv", type=Path, default=Path("results/guarded_policy_param_scan.csv"))
    parser.add_argument("--output-md", type=Path, default=Path("results/guarded_policy_param_scan.md"))
    parser.add_argument("--preset", choices=["smoke", "focused", "grid"], default="focused")
    parser.add_argument("--scenario-preset", choices=["hard", "targeted", "core"], default="targeted")
    parser.add_argument("--guard-scenario-filter", choices=["all", "geometry", "hard"], default="geometry")
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--near-hole-crop-offset", nargs=2, type=int, default=(0, 0))
    parser.add_argument("--wrist-camera-pos-offset", nargs=3, type=float, default=(0.0, 0.0, 0.0))
    parser.add_argument(
        "--wrist-camera-rot-offset-deg",
        nargs=3,
        type=float,
        default=(0.0, 0.0, 0.0),
    )
    parser.add_argument("--wrist-camera-fovy", type=float, default=None)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument(
        "--initialization-mode",
        choices=["fixed", "target_relative_high_start"],
        default="fixed",
    )
    parser.add_argument("--initial-tip-z-above-range", nargs=2, type=float, default=(0.15, 0.25))
    parser.add_argument("--initial-tip-xy-offset-range", nargs=2, type=float, default=(0.08, 0.16))
    parser.add_argument(
        "--initial-tip-xy-angle-range-deg",
        nargs=2,
        type=float,
        default=(0.0, 360.0),
    )
    parser.add_argument("--initial-ik-max-attempts", type=int, default=20)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--geometry-hole-center-xy-jitter", nargs=2, type=float, default=(0.002, 0.002))
    parser.add_argument("--geometry-fixture-height-jitter", type=float, default=0.001)
    parser.add_argument("--geometry-table-height-jitter", type=float, default=0.001)
    parser.add_argument("--geometry-hole-half-size-range", nargs=2, type=float, default=(0.017, 0.021))
    parser.add_argument("--geometry-peg-radius-range", nargs=2, type=float, default=(0.0115, 0.0125))
    parser.add_argument("--approach-xy-tolerance", type=float, default=0.02)
    parser.add_argument("--approach-height", type=float, default=0.08)
    parser.add_argument("--staged-xy-weight", type=float, default=2.0)
    parser.add_argument("--staged-z-weight", type=float, default=1.0)
    parser.add_argument("--success-bonus", type=float, default=120.0)
    parser.add_argument("--collision-penalty", type=float, default=300.0)
    parser.add_argument("--timeout-penalty", type=float, default=10.0)
    parser.add_argument("--progress-reward-scale", type=float, default=20.0)
    parser.add_argument("--distance-reward-scale", type=float, default=2.0)
    parser.add_argument("--action-penalty-scale", type=float, default=0.002)
    parser.add_argument("--action-alignment-scale", type=float, default=2.0)
    parser.add_argument("--guard-risk-xy", type=float, default=0.0)
    parser.add_argument("--guard-block-down-when-unaligned", action="store_true")
    parser.add_argument(
        "--scan-guard-block-down-when-unaligned",
        action="store_true",
        help="For grid scans, include both block-down=false and true candidates.",
    )
    parser.add_argument("--guard-release-on-high", action="store_true")
    parser.add_argument("--guard-action-gain", type=float, default=1.0)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.005)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)
    parser.add_argument("--guard-start-xy-values", nargs="+", type=float, default=(0.04, 0.05, 0.06, 0.07))
    parser.add_argument("--guard-start-z-values", nargs="+", type=float, default=(0.06, 0.08, 0.10))
    parser.add_argument("--guard-blend-values", nargs="+", type=float, default=(0.5, 0.75, 1.0))
    parser.add_argument("--guard-min-policy-step-values", nargs="+", type=int, default=(0,))
    parser.add_argument("--guarded-max-down-action-values", nargs="+", type=float, default=(0.0025, 0.0035, 0.0045))
    parser.add_argument("--guarded-align-xy-tolerance-values", nargs="+", type=float, default=(0.015, 0.020, 0.025))
    parser.add_argument(
        "--guarded-oracle-mode-values",
        nargs="+",
        choices=["guarded_two_stage", "high_start_two_phase"],
        default=("guarded_two_stage",),
    )
    parser.add_argument("--include-no-guard-baseline", action="store_true", default=True)
    parser.add_argument("--no-no-guard-baseline", dest="include_no_guard_baseline", action="store_false")
    parser.add_argument("--max-configs", type=int, default=None)
    return parse_args_with_config(parser)


def make_env(args: argparse.Namespace, scenario: Scenario) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode=args.observation_mode,
        image_width=args.width,
        image_height=args.height,
        include_near_hole_crop=args.include_near_hole_crop,
        near_hole_crop_size=args.near_hole_crop_size,
        near_hole_crop_offset=tuple(args.near_hole_crop_offset),
        wrist_camera_pos_offset=tuple(args.wrist_camera_pos_offset),
        wrist_camera_rot_offset_deg=tuple(args.wrist_camera_rot_offset_deg),
        wrist_camera_fovy=args.wrist_camera_fovy,
        max_steps=args.max_steps,
        action_scale=args.action_scale,
        initialization_mode=args.initialization_mode,
        initial_tip_z_above_range=tuple(args.initial_tip_z_above_range),
        initial_tip_xy_offset_range=tuple(args.initial_tip_xy_offset_range),
        initial_tip_xy_angle_range_deg=tuple(args.initial_tip_xy_angle_range_deg),
        initial_ik_max_attempts=args.initial_ik_max_attempts,
        success_xy_tolerance=args.success_xy_tolerance,
        success_z_tolerance=args.success_z_tolerance,
        approach_xy_tolerance=args.approach_xy_tolerance,
        approach_height=args.approach_height,
        staged_xy_weight=args.staged_xy_weight,
        staged_z_weight=args.staged_z_weight,
        success_bonus=args.success_bonus,
        collision_penalty=args.collision_penalty,
        timeout_penalty=args.timeout_penalty,
        progress_reward_scale=args.progress_reward_scale,
        distance_reward_scale=args.distance_reward_scale,
        action_penalty_scale=args.action_penalty_scale,
        action_alignment_scale=args.action_alignment_scale,
        domain_randomization_level=scenario.level,
        control_action_scale_range=scenario.control_action_scale_range,
        control_action_noise_std_range=scenario.control_action_noise_std_range,
        control_action_delay_range=scenario.control_action_delay_range,
        control_action_filter_alpha_range=scenario.control_action_filter_alpha_range,
        geometry_hole_center_xy_jitter=tuple(args.geometry_hole_center_xy_jitter),
        geometry_fixture_height_jitter=args.geometry_fixture_height_jitter,
        geometry_table_height_jitter=args.geometry_table_height_jitter,
        geometry_hole_half_size_range=tuple(args.geometry_hole_half_size_range),
        geometry_peg_radius_range=tuple(args.geometry_peg_radius_range),
        contact_friction_multiplier_range=scenario.contact_friction_multiplier_range,
        contact_solref_time_multiplier_range=scenario.contact_solref_time_multiplier_range,
        contact_solref_damping_multiplier_range=scenario.contact_solref_damping_multiplier_range,
        contact_solimp_width_multiplier_range=scenario.contact_solimp_width_multiplier_range,
        dynamics_joint_damping_multiplier_range=scenario.dynamics_joint_damping_multiplier_range,
        dynamics_actuator_kp_multiplier_range=scenario.dynamics_actuator_kp_multiplier_range,
    )


def make_guarded_config(candidate: GuardCandidate) -> GuardedPolicyConfig:
    return GuardedPolicyConfig(
        scenario_filter=candidate.scenario_filter,
        guard_start_xy=candidate.guard_start_xy,
        guard_start_z=candidate.guard_start_z,
        guard_risk_xy=candidate.guard_risk_xy,
        guard_blend=candidate.guard_blend,
        guard_min_policy_steps=candidate.guard_min_policy_steps,
        guard_block_down_when_unaligned=candidate.guard_block_down_when_unaligned,
        guard_release_on_high=candidate.guard_release_on_high,
        oracle=OracleControllerConfig(
            mode=candidate.guarded_oracle_mode,
            action_gain=candidate.guard_action_gain,
            guarded_align_xy_tolerance=candidate.guarded_align_xy_tolerance,
            guarded_insert_xy_tolerance=candidate.guarded_insert_xy_tolerance,
            guarded_retract_xy_tolerance=candidate.guarded_retract_xy_tolerance,
            guarded_preinsert_height=candidate.guarded_preinsert_height,
            guarded_max_xy_action=candidate.guarded_max_xy_action,
            guarded_max_down_action=candidate.guarded_max_down_action,
            guarded_max_up_action=candidate.guarded_max_up_action,
            guarded_prediction_steps=candidate.guarded_prediction_steps,
        ),
    )


def value_name(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".").replace(".", "p")


def grid_candidates(args: argparse.Namespace) -> list[GuardCandidate]:
    candidates = []
    if args.include_no_guard_baseline:
        candidates.append(GuardCandidate("no_guard", scenario_filter="none"))
    block_down_values = (
        (False, True)
        if args.scan_guard_block_down_when_unaligned
        else (bool(args.guard_block_down_when_unaligned),)
    )
    for xy, z, blend, min_steps, down, align, oracle_mode, block_down in itertools.product(
        args.guard_start_xy_values,
        args.guard_start_z_values,
        args.guard_blend_values,
        args.guard_min_policy_step_values,
        args.guarded_max_down_action_values,
        args.guarded_align_xy_tolerance_values,
        args.guarded_oracle_mode_values,
        block_down_values,
    ):
        candidates.append(
            GuardCandidate(
                name=(
                    f"guard_xy{value_name(xy)}_z{value_name(z)}_blend{value_name(blend)}_"
                    f"min{min_steps}_"
                    f"down{value_name(down)}_align{value_name(align)}_"
                    f"{oracle_mode.replace('_', '')}_block{int(block_down)}"
                ),
                scenario_filter=args.guard_scenario_filter,
                guard_start_xy=xy,
                guard_start_z=z,
                guard_risk_xy=args.guard_risk_xy,
                guard_blend=blend,
                guard_min_policy_steps=min_steps,
                guard_block_down_when_unaligned=block_down,
                guard_release_on_high=args.guard_release_on_high,
                guard_action_gain=args.guard_action_gain,
                guarded_align_xy_tolerance=align,
                guarded_insert_xy_tolerance=args.guarded_insert_xy_tolerance,
                guarded_retract_xy_tolerance=args.guarded_retract_xy_tolerance,
                guarded_preinsert_height=args.guarded_preinsert_height,
                guarded_max_xy_action=args.guarded_max_xy_action,
                guarded_max_down_action=down,
                guarded_max_up_action=args.guarded_max_up_action,
                guarded_prediction_steps=args.guarded_prediction_steps,
                guarded_oracle_mode=oracle_mode,
            )
        )
    return candidates


def candidates_for_args(args: argparse.Namespace) -> list[GuardCandidate]:
    if args.preset == "smoke":
        candidates = list(SMOKE_CANDIDATES)
    elif args.preset == "focused":
        candidates = list(FOCUSED_CANDIDATES)
    else:
        candidates = grid_candidates(args)

    default_oracle_mode = args.guarded_oracle_mode_values[0]
    candidates = [
        candidate if candidate.scenario_filter == "none" else GuardCandidate(
            name=candidate.name,
            scenario_filter=args.guard_scenario_filter,
            guard_start_xy=candidate.guard_start_xy,
            guard_start_z=candidate.guard_start_z,
            guard_risk_xy=args.guard_risk_xy,
            guard_blend=candidate.guard_blend,
            guard_min_policy_steps=candidate.guard_min_policy_steps,
            guard_block_down_when_unaligned=args.guard_block_down_when_unaligned,
            guard_release_on_high=args.guard_release_on_high,
            guard_action_gain=args.guard_action_gain,
            guarded_align_xy_tolerance=candidate.guarded_align_xy_tolerance,
            guarded_insert_xy_tolerance=args.guarded_insert_xy_tolerance,
            guarded_retract_xy_tolerance=args.guarded_retract_xy_tolerance,
            guarded_preinsert_height=args.guarded_preinsert_height,
            guarded_max_xy_action=args.guarded_max_xy_action,
            guarded_max_down_action=candidate.guarded_max_down_action,
            guarded_max_up_action=args.guarded_max_up_action,
            guarded_prediction_steps=args.guarded_prediction_steps,
            guarded_oracle_mode=default_oracle_mode,
        )
        for candidate in candidates
    ]
    if args.max_configs is not None:
        candidates = candidates[: args.max_configs]
    return candidates


def scenarios_for_args(args: argparse.Namespace) -> list[Scenario]:
    if args.scenario_preset == "hard":
        return [HARD_BUCKET_SCENARIO]
    if args.scenario_preset == "targeted":
        return [
            CORE_SCENARIOS[2],
            CORE_SCENARIOS[3],
            CORE_SCENARIOS[4],
            HARD_BUCKET_SCENARIO,
        ]
    return list(CORE_SCENARIOS) + [HARD_BUCKET_SCENARIO]


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def range_text(values: tuple[Any, Any]) -> str:
    return f"{values[0]}:{values[1]}"


def evaluate_candidate(
    args: argparse.Namespace,
    env: PegInHoleMujocoEnv,
    model: Any,
    scenario: Scenario,
    candidate: GuardCandidate,
) -> dict[str, Any]:
    guarded_controller = GuardedPolicyController(make_guarded_config(candidate))
    guard_state_provider = MujocoGuardStateProvider(env)
    guard_enabled = guarded_controller.scenario_uses_guard(scenario.name, scenario.level)
    successes = 0
    collisions = 0
    timeouts = 0
    guarded_episodes = 0
    returns: list[float] = []
    steps: list[float] = []
    guarded_steps: list[float] = []
    final_dist_xy: list[float] = []
    final_dist_z: list[float] = []

    for episode in range(args.episodes):
        obs, info = env.reset(seed=args.seed + episode)
        guarded_controller.reset()
        episode_return = 0.0
        episode_guard_steps = 0
        while True:
            policy_action, _ = model.predict(obs, deterministic=True)
            step = guarded_controller.step_with_provider(
                guard_state_provider,
                info,
                policy_action,
                scenario_name=scenario.name,
                scenario_level=scenario.level,
            )
            obs, reward, terminated, truncated, info = env.step(step.action)
            episode_return += float(reward)
            episode_guard_steps += int(step.guarded)
            if terminated or truncated:
                break

        successes += int(info["insertion_success"])
        collisions += int(info["collision"])
        timeouts += int(truncated and not info["insertion_success"])
        guarded_episodes += int(episode_guard_steps > 0)
        returns.append(episode_return)
        steps.append(float(info["step_count"]))
        guarded_steps.append(float(episode_guard_steps))
        final_dist_xy.append(float(info["dist_xy"]))
        final_dist_z.append(float(info["dist_z"]))

    mean_steps = mean(steps)
    mean_guarded_steps = mean(guarded_steps)
    return {
        "candidate": candidate.name,
        "scenario": scenario.name,
        "level": scenario.level,
        "episodes": args.episodes,
        "success_rate": successes / args.episodes,
        "collision_rate": collisions / args.episodes,
        "timeout_rate": timeouts / args.episodes,
        "mean_return": mean(returns),
        "mean_steps": mean_steps,
        "mean_guarded_steps": mean_guarded_steps,
        "mean_guarded_step_fraction": mean_guarded_steps / max(mean_steps, 1e-9),
        "guarded_episode_rate": guarded_episodes / args.episodes,
        "guard_enabled": guard_enabled,
        "mean_final_dist_xy": mean(final_dist_xy),
        "mean_final_dist_z": mean(final_dist_z),
        "scenario_filter": candidate.scenario_filter,
        "guard_start_xy": candidate.guard_start_xy,
        "guard_start_z": candidate.guard_start_z,
        "guard_risk_xy": candidate.guard_risk_xy,
        "guard_blend": candidate.guard_blend,
        "guard_min_policy_steps": candidate.guard_min_policy_steps,
        "guard_block_down_when_unaligned": candidate.guard_block_down_when_unaligned,
        "guard_release_on_high": candidate.guard_release_on_high,
        "guard_action_gain": candidate.guard_action_gain,
        "guarded_align_xy_tolerance": candidate.guarded_align_xy_tolerance,
        "guarded_insert_xy_tolerance": candidate.guarded_insert_xy_tolerance,
        "guarded_retract_xy_tolerance": candidate.guarded_retract_xy_tolerance,
        "guarded_preinsert_height": candidate.guarded_preinsert_height,
        "guarded_max_xy_action": candidate.guarded_max_xy_action,
        "guarded_max_down_action": candidate.guarded_max_down_action,
        "guarded_max_up_action": candidate.guarded_max_up_action,
        "guarded_prediction_steps": candidate.guarded_prediction_steps,
        "guarded_oracle_mode": candidate.guarded_oracle_mode,
        "control_scale_range": range_text(scenario.control_action_scale_range),
        "control_noise_std_range": range_text(scenario.control_action_noise_std_range),
        "control_delay_range": range_text(scenario.control_action_delay_range),
        "control_filter_alpha_range": range_text(scenario.control_action_filter_alpha_range),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved CSV report to {path}")


def aggregate_rows(rows: list[dict[str, Any]], scenario_names: list[str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["candidate"]), []).append(row)

    aggregates = []
    for candidate, candidate_rows in grouped.items():
        row: dict[str, Any] = {"candidate": candidate}
        for scenario_name in scenario_names:
            match = next(item for item in candidate_rows if item["scenario"] == scenario_name)
            row[f"{scenario_name}_success"] = match["success_rate"]
            row[f"{scenario_name}_collision"] = match["collision_rate"]
        row["mean_success"] = mean([float(item["success_rate"]) for item in candidate_rows])
        row["mean_collision"] = mean([float(item["collision_rate"]) for item in candidate_rows])
        row["mean_guarded_steps"] = mean([float(item["mean_guarded_steps"]) for item in candidate_rows])
        row["mean_guarded_episode_rate"] = mean(
            [float(item["guarded_episode_rate"]) for item in candidate_rows]
        )
        aggregates.append(row)
    return sorted(
        aggregates,
        key=lambda item: (float(item["mean_success"]), -float(item["mean_collision"])),
        reverse=True,
    )


def write_markdown(
    path: Path,
    args: argparse.Namespace,
    rows: list[dict[str, Any]],
    scenario_names: list[str],
    candidate_count: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    aggregate = aggregate_rows(rows, scenario_names)
    success_columns = " | ".join(scenario_names)
    success_header = " | ".join(["---:"] * len(scenario_names))
    lines = [
        "# Guarded Policy Parameter Scan",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Preset: `{args.preset}`",
        f"- Scenario preset: `{args.scenario_preset}`",
        f"- Candidates: `{candidate_count}`",
        f"- Episodes per candidate/scenario: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Guard scenario filter: `{args.guard_scenario_filter}`",
        f"- Initialization mode: `{args.initialization_mode}`",
        f"- Initial tip Z above target range: `{list(args.initial_tip_z_above_range)}`",
        f"- Initial tip XY offset range: `{list(args.initial_tip_xy_offset_range)}`",
        f"- Guarded oracle mode values: `{list(args.guarded_oracle_mode_values)}`",
        f"- Scan block-down values: `{args.scan_guard_block_down_when_unaligned}`",
        "",
        "## Candidate Summary",
        "",
        f"| Candidate | {success_columns} | Mean success | Mean collision | Guard steps | Guard ep. |",
        f"| --- | {success_header} | ---: | ---: | ---: | ---: |",
    ]
    for item in aggregate:
        scenario_values = " | ".join(
            f"{float(item[f'{scenario_name}_success']):.3f}" for scenario_name in scenario_names
        )
        lines.append(
            f"| `{item['candidate']}` | {scenario_values} | "
            f"{float(item['mean_success']):.3f} | {float(item['mean_collision']):.3f} | "
            f"{float(item['mean_guarded_steps']):.1f} | "
            f"{float(item['mean_guarded_episode_rate']):.3f} |"
        )

    lines.extend(
        [
            "",
            "## Per-Scenario Rows",
            "",
            "| Candidate | Scenario | Success | Collision | Timeout | Return | Steps | Guard steps | Guard ep. | Final XY | Final Z |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            "| `{candidate}` | {scenario} | {success_rate:.3f} | {collision_rate:.3f} | "
            "{timeout_rate:.3f} | {mean_return:.3f} | {mean_steps:.1f} | "
            "{mean_guarded_steps:.1f} | {guarded_episode_rate:.3f} | "
            "{mean_final_dist_xy:.5f} | {mean_final_dist_z:.5f} |".format(**row)
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved Markdown report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")

    candidates = candidates_for_args(args)
    scenarios = scenarios_for_args(args)
    rows: list[dict[str, Any]] = []
    model = AGENTS[args.agent].load(args.model, device=args.device)

    for scenario in scenarios:
        for candidate in candidates:
            # Domain randomization mutates MuJoCo model parameters. A fresh env per
            # candidate keeps matched-seed comparisons independent and reproducible.
            env = make_env(args, scenario)
            try:
                row = evaluate_candidate(args, env, model, scenario, candidate)
                rows.append(row)
                print(
                    "{candidate} / {scenario}: success={success_rate:.3f} "
                    "collision={collision_rate:.3f} guard_steps={mean_guarded_steps:.1f} "
                    "return={mean_return:.3f}".format(**row)
                )
            finally:
                env.close()

    scenario_names = [scenario.name for scenario in scenarios]
    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, args, rows, scenario_names, len(candidates))


if __name__ == "__main__":
    main()
