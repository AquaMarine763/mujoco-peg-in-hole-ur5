from __future__ import annotations

import argparse
import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco import OracleControllerConfig, PegInHoleMujocoEnv, oracle_action
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
class ClearanceTier:
    name: str
    hole_half_size_range: tuple[float, float]
    peg_radius_range: tuple[float, float]


@dataclass(frozen=True)
class Scenario:
    name: str
    level: str
    control_action_scale_range: tuple[float, float] = (1.0, 1.0)
    control_action_noise_std_range: tuple[float, float] = (0.0, 0.0)
    control_action_delay_range: tuple[int, int] = (0, 0)
    control_action_filter_alpha_range: tuple[float, float] = (1.0, 1.0)
    contact_friction_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solref_time_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solref_damping_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solimp_width_multiplier_range: tuple[float, float] = (1.0, 1.0)
    dynamics_joint_damping_multiplier_range: tuple[float, float] = (1.0, 1.0)
    dynamics_actuator_kp_multiplier_range: tuple[float, float] = (1.0, 1.0)


CLEARANCE_TIERS = {
    "wide_legacy": ClearanceTier("wide_legacy", (0.025, 0.029), (0.0115, 0.0125)),
    "medium": ClearanceTier("medium", (0.020, 0.024), (0.0115, 0.0125)),
    "narrow": ClearanceTier("narrow", (0.017, 0.021), (0.0115, 0.0125)),
    "tight": ClearanceTier("tight", (0.015, 0.018), (0.0115, 0.0125)),
}


SCENARIOS = {
    "visual_camera": Scenario("visual_camera", "visual_camera"),
    "visual_camera_control": Scenario("visual_camera_control", "visual_camera_control", **CONTROL_RANGES),
    "full_light_geometry": Scenario("full_light_geometry", "full_light_geometry", **CONTROL_RANGES),
    "hard_full_light_bucket": Scenario(
        "hard_full_light_bucket",
        "full_light_geometry",
        control_action_scale_range=(0.8, 1.1),
        control_action_noise_std_range=(0.0, 0.00025),
        control_action_delay_range=(2, 2),
        control_action_filter_alpha_range=(0.55, 0.70),
    ),
    "full_contact_light": Scenario(
        "full_contact_light",
        "full_contact_light",
        **CONTROL_RANGES,
        **CONTACT_LIGHT_RANGES,
    ),
}


SCALAR_DIAGNOSTIC_KEYS = (
    "hole_half_size",
    "peg_radius",
    "hole_clearance",
    "control_action_scale_multiplier",
    "control_action_noise_std",
    "control_action_delay",
    "control_action_filter_alpha",
    "fixture_height_offset",
    "table_height_offset",
    "contact_friction_multiplier",
    "contact_solref_time_multiplier",
    "contact_solref_damping_multiplier",
    "contact_solimp_width_multiplier",
    "joint_damping_multiplier",
    "actuator_kp_multiplier",
    "action_tracking_error",
    "ik_target_error",
    "ik_orientation_error",
    "ik_iterations",
    "peg_tilt_angle_deg",
    "joint_limit_min_normalized_margin",
    "joint_target_error",
)
TEXT_DIAGNOSTIC_KEYS = (
    "geometry_profile",
    "geometry_name",
    "peg_shape",
    "hole_shape",
)
VECTOR_DIAGNOSTIC_KEYS = (
    "hole_center_offset",
    "action_target_tip_delta",
    "action_actual_tip_delta",
    "action_tip_delta_error",
    "joint_target_qpos",
    "joint_qpos_after_action",
)
DATASET_SCHEMA_VERSION = "image_correction_v7_insert_settle_control_state"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect image corrective samples from policy-visited failure windows."
    )
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=10_000)
    parser.add_argument("--samples-per-config", type=int, default=None)
    parser.add_argument("--max-episodes-per-config", type=int, default=1000)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=990_000)
    parser.add_argument("--compressed", action="store_true")
    parser.add_argument(
        "--scenario-preset",
        choices=[
            "visual",
            "visual_control",
            "geometry",
            "hard",
            "targeted",
            "contact",
            "high_start_targeted",
        ],
        default="targeted",
    )
    parser.add_argument(
        "--tier-preset",
        choices=["wide", "medium", "narrow", "tight", "wide_medium", "medium_narrow", "all"],
        default="medium",
    )
    parser.add_argument(
        "--geometry-profile",
        choices=["single", "round_square", "square_square", "mixed_basic"],
        default="single",
    )
    parser.add_argument("--geometry-square-peg-half-size-range", nargs=2, type=float, default=(0.0105, 0.0125))
    parser.add_argument("--geometry-mixed-square-probability", type=float, default=0.5)
    parser.add_argument(
        "--selection",
        choices=[
            "failure_window",
            "near_hole_failure_window",
            "near_hole",
            "failed_episode_near_hole",
            "failed_episode_all",
            "timeout_progress_window",
            "timeout_progress_failure_window",
            "insert_drift_window",
            "insert_drift_failure_window",
            "insert_settle_window",
            "insert_settle_failure_window",
            "balanced_v4b_window",
            "balanced_v4b_failure_window",
            "approach_window",
            "approach_failure_window",
            "fixture_wall_window",
            "fixture_wall_failure_window",
        ],
        default="failure_window",
    )
    parser.add_argument(
        "--episode-outcome-filter",
        choices=["any", "collision", "timeout", "terminated_failure"],
        default="any",
        help="Keep corrective samples only from episodes with this final outcome.",
    )
    parser.add_argument(
        "--keep-success-episodes",
        action="store_true",
        help="Allow DAgger-style near-hole samples from successful policy episodes.",
    )
    parser.add_argument("--failure-window-steps", type=int, default=8)
    parser.add_argument("--near-hole-xy", type=float, default=0.03)
    parser.add_argument("--near-hole-z", type=float, default=0.10)
    parser.add_argument("--min-correction-norm", type=float, default=0.004)
    parser.add_argument("--max-samples-per-episode", type=int, default=8)
    parser.add_argument("--image-width", type=int, default=100)
    parser.add_argument("--image-height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--near-hole-crop-offset", nargs=2, type=int, default=(0, 0))
    parser.add_argument("--include-control-state", action="store_true")
    parser.add_argument("--image-frame-stack", type=int, default=1)
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
    parser.add_argument("--ik-control-mode", choices=["position", "pose"], default="position")
    parser.add_argument("--ik-orientation-weight", type=float, default=0.12)
    parser.add_argument("--ik-posture-weight", type=float, default=0.01)
    parser.add_argument("--ik-step-limit", type=float, default=0.06)
    parser.add_argument("--ik-max-iterations", type=int, default=24)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
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
    parser.add_argument("--oracle-action-gain", type=float, default=1.0)
    parser.add_argument(
        "--oracle-mode",
        choices=[
            "guarded_two_stage",
            "high_start_two_phase",
            "contact_aware_recovery",
            "timeout_descent_progress",
        ],
        default="guarded_two_stage",
    )
    parser.add_argument("--guarded-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guarded-max-down-action", type=float, default=0.0035)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.005)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)
    parser.add_argument("--guarded-lift-before-lateral", action="store_true")
    parser.add_argument("--guarded-lift-before-lateral-xy-tolerance", type=float, default=0.020)
    parser.add_argument("--guarded-lift-before-lateral-z-margin", type=float, default=0.010)
    parser.add_argument("--contact-recovery-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--contact-recovery-z-max", type=float, default=0.050)
    parser.add_argument("--contact-recovery-lift-height", type=float, default=0.060)
    parser.add_argument("--contact-recovery-lift-z-tolerance", type=float, default=0.010)
    parser.add_argument("--contact-recovery-max-down-action", type=float, default=0.001)
    parser.add_argument("--timeout-progress-xy-tolerance", type=float, default=0.010)
    parser.add_argument("--timeout-progress-z-max", type=float, default=0.060)
    parser.add_argument("--timeout-progress-max-down-action", type=float, default=0.0015)
    parser.add_argument(
        "--insert-drift-correction-labels",
        action="store_true",
        help="Use late-stage insert-band drift labels with recenter and slow-insert phases.",
    )
    parser.add_argument("--insert-drift-window-xy-max", type=float, default=0.015)
    parser.add_argument("--insert-drift-window-z-max", type=float, default=0.038)
    parser.add_argument("--insert-drift-stable-xy", type=float, default=0.0045)
    parser.add_argument("--insert-drift-stable-steps", type=int, default=4)
    parser.add_argument("--insert-drift-correction-max-xy-action", type=float, default=0.003)
    parser.add_argument("--insert-drift-correction-max-down-action", type=float, default=0.001)
    parser.add_argument(
        "--insert-settle-correction-labels",
        action="store_true",
        help=(
            "Use late-stage insert labels that separate recenter, settle, lift-recenter, "
            "and slow-insert phases."
        ),
    )
    parser.add_argument("--insert-settle-window-xy-max", type=float, default=0.015)
    parser.add_argument("--insert-settle-window-z-max", type=float, default=0.045)
    parser.add_argument("--insert-settle-insert-xy", type=float, default=0.0065)
    parser.add_argument("--insert-settle-settle-xy", type=float, default=0.010)
    parser.add_argument("--insert-settle-stable-steps", type=int, default=2)
    parser.add_argument("--insert-settle-hover-height", type=float, default=0.030)
    parser.add_argument("--insert-settle-hover-z-tolerance", type=float, default=0.006)
    parser.add_argument("--insert-settle-lift-z-max", type=float, default=0.016)
    parser.add_argument("--insert-settle-max-xy-action", type=float, default=0.0025)
    parser.add_argument("--insert-settle-max-down-action", type=float, default=0.0015)
    parser.add_argument(
        "--balanced-v4b-labels",
        action="store_true",
        help="Use safety-balanced near-hole labels with block/hover/lift/down phases.",
    )
    parser.add_argument("--balanced-v4b-window-xy", type=float, default=0.020)
    parser.add_argument("--balanced-v4b-window-z-max", type=float, default=0.080)
    parser.add_argument("--balanced-v4b-stable-xy", type=float, default=0.0045)
    parser.add_argument("--balanced-v4b-stable-steps", type=int, default=4)
    parser.add_argument("--balanced-v4b-low-z", type=float, default=0.040)
    parser.add_argument("--balanced-v4b-hover-height", type=float, default=0.050)
    parser.add_argument("--balanced-v4b-hover-z-tolerance", type=float, default=0.010)
    parser.add_argument("--balanced-v4b-max-down-action", type=float, default=0.0012)
    parser.add_argument(
        "--approach-correction-labels",
        action="store_true",
        help="Use high-approach recenter labels before the peg enters fixture height.",
    )
    parser.add_argument("--approach-window-xy-min", type=float, default=0.020)
    parser.add_argument("--approach-window-xy-max", type=float, default=0.160)
    parser.add_argument("--approach-window-z-min", type=float, default=0.060)
    parser.add_argument("--approach-window-z-max", type=float, default=0.180)
    parser.add_argument("--approach-correction-target-height", type=float, default=0.120)
    parser.add_argument("--approach-correction-max-down-action", type=float, default=0.0)
    parser.add_argument(
        "--fixture-wall-correction-labels",
        action="store_true",
        help="Use pre-contact fixture-wall labels for high-offset, mid-height states.",
    )
    parser.add_argument("--fixture-wall-window-xy-min", type=float, default=0.020)
    parser.add_argument("--fixture-wall-window-xy-max", type=float, default=0.090)
    parser.add_argument("--fixture-wall-window-z-min", type=float, default=0.040)
    parser.add_argument("--fixture-wall-window-z-max", type=float, default=0.080)
    parser.add_argument("--fixture-wall-correction-target-height", type=float, default=0.080)
    parser.add_argument("--fixture-wall-correction-max-xy-action", type=float, default=0.003)
    parser.add_argument("--fixture-wall-correction-max-down-action", type=float, default=0.0)
    parser.add_argument("--recovery-branch-rollout", action="store_true")
    parser.add_argument("--recovery-branch-from-near-hole", action="store_true")
    parser.add_argument("--recovery-branch-max-starts-per-episode", type=int, default=2)
    parser.add_argument("--recovery-branch-max-steps", type=int, default=90)
    parser.add_argument("--recovery-branch-stride", type=int, default=3)
    parser.add_argument("--recovery-branch-stop-on-success", action="store_true")
    parser.add_argument("--recovery-branch-clear-control-history", action="store_true")
    parser.add_argument("--recovery-branch-synthetic-stages", action="store_true")
    return parse_args_with_config(parser)


def tiers_for_args(args: argparse.Namespace) -> list[ClearanceTier]:
    if args.tier_preset == "wide":
        return [CLEARANCE_TIERS["wide_legacy"]]
    if args.tier_preset == "medium":
        return [CLEARANCE_TIERS["medium"]]
    if args.tier_preset == "narrow":
        return [CLEARANCE_TIERS["narrow"]]
    if args.tier_preset == "tight":
        return [CLEARANCE_TIERS["tight"]]
    if args.tier_preset == "wide_medium":
        return [CLEARANCE_TIERS["wide_legacy"], CLEARANCE_TIERS["medium"]]
    if args.tier_preset == "medium_narrow":
        return [CLEARANCE_TIERS["medium"], CLEARANCE_TIERS["narrow"]]
    return list(CLEARANCE_TIERS.values())


def scenarios_for_args(args: argparse.Namespace) -> list[Scenario]:
    if args.scenario_preset == "visual":
        return [SCENARIOS["visual_camera"]]
    if args.scenario_preset == "visual_control":
        return [SCENARIOS["visual_camera"], SCENARIOS["visual_camera_control"]]
    if args.scenario_preset == "geometry":
        return [SCENARIOS["full_light_geometry"]]
    if args.scenario_preset == "hard":
        return [SCENARIOS["hard_full_light_bucket"]]
    if args.scenario_preset == "contact":
        return [SCENARIOS["full_light_geometry"], SCENARIOS["full_contact_light"]]
    if args.scenario_preset == "high_start_targeted":
        return [
            SCENARIOS["visual_camera"],
            SCENARIOS["visual_camera_control"],
            SCENARIOS["hard_full_light_bucket"],
        ]
    return [SCENARIOS["full_light_geometry"], SCENARIOS["hard_full_light_bucket"]]


def make_env(args: argparse.Namespace, scenario: Scenario, tier: ClearanceTier) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode="image",
        image_width=args.image_width,
        image_height=args.image_height,
        include_near_hole_crop=args.include_near_hole_crop,
        near_hole_crop_size=args.near_hole_crop_size,
        near_hole_crop_offset=tuple(args.near_hole_crop_offset),
        include_control_state=args.include_control_state,
        image_frame_stack=args.image_frame_stack,
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
        ik_control_mode=args.ik_control_mode,
        ik_orientation_weight=args.ik_orientation_weight,
        ik_posture_weight=args.ik_posture_weight,
        ik_step_limit=args.ik_step_limit,
        ik_max_iterations=args.ik_max_iterations,
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
        geometry_hole_center_xy_jitter=(0.002, 0.002),
        geometry_fixture_height_jitter=0.001,
        geometry_table_height_jitter=0.001,
        geometry_hole_half_size_range=tier.hole_half_size_range,
        geometry_peg_radius_range=tier.peg_radius_range,
        geometry_profile=args.geometry_profile,
        geometry_square_peg_half_size_range=tuple(args.geometry_square_peg_half_size_range),
        geometry_mixed_square_probability=args.geometry_mixed_square_probability,
        contact_friction_multiplier_range=scenario.contact_friction_multiplier_range,
        contact_solref_time_multiplier_range=scenario.contact_solref_time_multiplier_range,
        contact_solref_damping_multiplier_range=scenario.contact_solref_damping_multiplier_range,
        contact_solimp_width_multiplier_range=scenario.contact_solimp_width_multiplier_range,
        dynamics_joint_damping_multiplier_range=scenario.dynamics_joint_damping_multiplier_range,
        dynamics_actuator_kp_multiplier_range=scenario.dynamics_actuator_kp_multiplier_range,
    )


def make_oracle_config(args: argparse.Namespace) -> OracleControllerConfig:
    return OracleControllerConfig(
        mode=args.oracle_mode,
        action_gain=args.oracle_action_gain,
        guarded_align_xy_tolerance=args.guarded_align_xy_tolerance,
        guarded_insert_xy_tolerance=args.guarded_insert_xy_tolerance,
        guarded_retract_xy_tolerance=args.guarded_retract_xy_tolerance,
        guarded_preinsert_height=args.guarded_preinsert_height,
        guarded_max_xy_action=args.guarded_max_xy_action,
        guarded_max_down_action=args.guarded_max_down_action,
        guarded_max_up_action=args.guarded_max_up_action,
        guarded_prediction_steps=args.guarded_prediction_steps,
        guarded_lift_before_lateral=args.guarded_lift_before_lateral,
        guarded_lift_before_lateral_xy_tolerance=args.guarded_lift_before_lateral_xy_tolerance,
        guarded_lift_before_lateral_z_margin=args.guarded_lift_before_lateral_z_margin,
        contact_recovery_xy_tolerance=args.contact_recovery_xy_tolerance,
        contact_recovery_z_max=args.contact_recovery_z_max,
        contact_recovery_lift_height=args.contact_recovery_lift_height,
        contact_recovery_lift_z_tolerance=args.contact_recovery_lift_z_tolerance,
        contact_recovery_max_down_action=args.contact_recovery_max_down_action,
        timeout_progress_xy_tolerance=args.timeout_progress_xy_tolerance,
        timeout_progress_z_max=args.timeout_progress_z_max,
        timeout_progress_max_down_action=args.timeout_progress_max_down_action,
    )


def action_cosine(a: np.ndarray, b: np.ndarray) -> float:
    a_norm = float(np.linalg.norm(a))
    b_norm = float(np.linalg.norm(b))
    if a_norm <= 1e-12 or b_norm <= 1e-12:
        return float("nan")
    return float(np.dot(a, b) / (a_norm * b_norm))


def recovery_phase(
    *,
    dist_xy: float,
    z_above_target: float,
    oracle_action_raw: np.ndarray,
    ever_within_insert_xy: bool,
    alignment_stable_steps: int,
    args: argparse.Namespace,
) -> str:
    if is_fixture_wall_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        args=args,
    ):
        if is_fixture_wall_lift_before_lateral_state(
            dist_xy=dist_xy,
            z_above_target=z_above_target,
            args=args,
        ):
            return "fixture_wall_lift_before_lateral"
        return "fixture_wall_recenter"
    if is_insert_drift_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        ever_within_insert_xy=ever_within_insert_xy,
        args=args,
    ):
        if (
            dist_xy <= args.insert_drift_stable_xy
            and alignment_stable_steps >= args.insert_drift_stable_steps
        ):
            return "insert_drift_slow_insert"
        return "insert_drift_recenter"
    if is_insert_settle_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        ever_within_insert_xy=ever_within_insert_xy,
        args=args,
    ):
        if (
            dist_xy <= args.insert_settle_insert_xy
            and alignment_stable_steps >= args.insert_settle_stable_steps
        ):
            return "insert_settle_slow_insert"
        if (
            z_above_target <= args.insert_settle_lift_z_max
            and dist_xy > args.insert_settle_insert_xy
        ):
            return "insert_settle_lift_recenter"
        if dist_xy <= args.insert_settle_settle_xy:
            return "insert_settle_settle"
        return "insert_settle_recenter"
    if is_approach_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        args=args,
    ):
        return "approach_recenter"
    if (
        dist_xy > args.contact_recovery_xy_tolerance
        and z_above_target <= args.contact_recovery_z_max
        and oracle_action_raw[2] > 1e-6
    ):
        return "unjam_lift"
    if dist_xy > args.guarded_insert_xy_tolerance:
        if (
            dist_xy <= args.timeout_progress_xy_tolerance
            and z_above_target <= args.timeout_progress_z_max
            and oracle_action_raw[2] < -1e-6
        ):
            return "progress_insert"
        return "realign"
    if oracle_action_raw[2] < -1e-6:
        return "slow_insert"
    return "hold"


def is_approach_window(
    *,
    dist_xy: float,
    z_above_target: float,
    args: argparse.Namespace,
) -> bool:
    return bool(
        args.approach_window_xy_min
        <= dist_xy
        <= args.approach_window_xy_max
        and args.approach_window_z_min
        <= z_above_target
        <= args.approach_window_z_max
    )


def is_fixture_wall_window(
    *,
    dist_xy: float,
    z_above_target: float,
    args: argparse.Namespace,
) -> bool:
    return bool(
        args.fixture_wall_window_xy_min
        <= dist_xy
        <= args.fixture_wall_window_xy_max
        and args.fixture_wall_window_z_min
        <= z_above_target
        <= args.fixture_wall_window_z_max
    )


def is_fixture_wall_lift_before_lateral_state(
    *,
    dist_xy: float,
    z_above_target: float,
    args: argparse.Namespace,
) -> bool:
    return bool(
        args.guarded_lift_before_lateral
        and dist_xy > args.guarded_lift_before_lateral_xy_tolerance
        and z_above_target
        < args.fixture_wall_correction_target_height
        - args.guarded_lift_before_lateral_z_margin
    )


def is_insert_drift_window(
    *,
    dist_xy: float,
    z_above_target: float,
    ever_within_insert_xy: bool,
    args: argparse.Namespace,
) -> bool:
    return bool(
        ever_within_insert_xy
        and dist_xy <= args.insert_drift_window_xy_max
        and z_above_target <= args.insert_drift_window_z_max
    )


def is_insert_settle_window(
    *,
    dist_xy: float,
    z_above_target: float,
    ever_within_insert_xy: bool,
    args: argparse.Namespace,
) -> bool:
    return bool(
        ever_within_insert_xy
        and dist_xy <= args.insert_settle_window_xy_max
        and z_above_target <= args.insert_settle_window_z_max
    )


def limit_xy_action(action: np.ndarray, max_xy_action: float) -> np.ndarray:
    limited = action.copy()
    if max_xy_action <= 0.0:
        limited[:2] = 0.0
        return limited
    xy_norm = float(np.linalg.norm(limited[:2]))
    if xy_norm > max_xy_action:
        limited[:2] *= max_xy_action / xy_norm
    return limited


def limit_z_action(
    action: np.ndarray,
    *,
    max_down_action: float,
    max_up_action: float,
) -> np.ndarray:
    limited = action.copy()
    if limited[2] < 0.0:
        limited[2] = max(limited[2], -max(0.0, max_down_action))
    else:
        limited[2] = min(limited[2], max(0.0, max_up_action))
    return limited


def action_toward_desired(
    env: PegInHoleMujocoEnv,
    *,
    control_tip: np.ndarray,
    desired: np.ndarray,
    args: argparse.Namespace,
    max_down_action: float,
) -> np.ndarray:
    action = float(args.oracle_action_gain) * (desired - control_tip)
    action = limit_xy_action(action, args.guarded_max_xy_action)
    action = limit_z_action(
        action,
        max_down_action=max_down_action,
        max_up_action=args.guarded_max_up_action,
    )
    return np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32)


def balanced_v4b_corrective_action(
    env: PegInHoleMujocoEnv,
    info: dict[str, Any],
    *,
    args: argparse.Namespace,
    alignment_stable_steps: int,
    ever_within_insert_xy: bool,
) -> tuple[np.ndarray, str, bool, bool]:
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    applied_action = np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64)
    control_tip = tip + float(args.guarded_prediction_steps) * applied_action
    dist_xy = float(np.linalg.norm(control_tip[:2] - target[:2]))
    z_above_target = float(control_tip[2] - target[2])
    drift_after_alignment = bool(
        ever_within_insert_xy
        and dist_xy > args.balanced_v4b_stable_xy
        and dist_xy <= args.balanced_v4b_window_xy
    )

    if (
        z_above_target <= args.balanced_v4b_low_z
        and dist_xy > args.balanced_v4b_stable_xy
    ):
        desired = np.asarray(
            [
                control_tip[0],
                control_tip[1],
                target[2] + args.contact_recovery_lift_height,
            ],
            dtype=np.float64,
        )
        return (
            action_toward_desired(
                env,
                control_tip=control_tip,
                desired=desired,
                args=args,
                max_down_action=0.0,
            ),
            "unjam_lift",
            drift_after_alignment,
            True,
        )

    stable_for_insert = (
        dist_xy <= args.balanced_v4b_stable_xy
        and alignment_stable_steps >= args.balanced_v4b_stable_steps
    )
    if stable_for_insert:
        desired = np.asarray([target[0], target[1], target[2]], dtype=np.float64)
        return (
            action_toward_desired(
                env,
                control_tip=control_tip,
                desired=desired,
                args=args,
                max_down_action=args.balanced_v4b_max_down_action,
            ),
            "stable_slow_insert",
            drift_after_alignment,
            False,
        )

    hover_z = float(target[2] + args.balanced_v4b_hover_height)
    needs_hover_lift = (
        z_above_target
        < args.balanced_v4b_hover_height - args.balanced_v4b_hover_z_tolerance
    )
    if needs_hover_lift or drift_after_alignment:
        desired_z = hover_z if needs_hover_lift else float(control_tip[2])
        desired = np.asarray([target[0], target[1], desired_z], dtype=np.float64)
        return (
            action_toward_desired(
                env,
                control_tip=control_tip,
                desired=desired,
                args=args,
                max_down_action=0.0,
            ),
            "hover_recenter",
            drift_after_alignment,
            True,
        )

    desired = np.asarray([target[0], target[1], control_tip[2]], dtype=np.float64)
    return (
        action_toward_desired(
            env,
            control_tip=control_tip,
            desired=desired,
            args=args,
            max_down_action=0.0,
        ),
        "block_down",
        drift_after_alignment,
        True,
    )


def approach_recenter_corrective_action(
    env: PegInHoleMujocoEnv,
    info: dict[str, Any],
    *,
    args: argparse.Namespace,
) -> np.ndarray:
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    applied_action = np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64)
    control_tip = tip + float(args.guarded_prediction_steps) * applied_action
    desired = np.asarray(
        [
            target[0],
            target[1],
            target[2] + args.approach_correction_target_height,
        ],
        dtype=np.float64,
    )
    return action_toward_desired(
        env,
        control_tip=control_tip,
        desired=desired,
        args=args,
        max_down_action=args.approach_correction_max_down_action,
    )


def fixture_wall_precontact_corrective_action(
    env: PegInHoleMujocoEnv,
    info: dict[str, Any],
    *,
    args: argparse.Namespace,
) -> tuple[np.ndarray, str]:
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    applied_action = np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64)
    control_tip = tip + float(args.guarded_prediction_steps) * applied_action
    dist_xy = float(np.linalg.norm(control_tip[:2] - target[:2]))
    z_above_target = float(control_tip[2] - target[2])
    if is_fixture_wall_lift_before_lateral_state(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        args=args,
    ):
        desired = np.asarray(
            [
                control_tip[0],
                control_tip[1],
                target[2] + args.fixture_wall_correction_target_height,
            ],
            dtype=np.float64,
        )
        action = action_toward_desired(
            env,
            control_tip=control_tip,
            desired=desired,
            args=args,
            max_down_action=0.0,
        )
        return action, "fixture_wall_lift_before_lateral"

    desired = np.asarray(
        [
            target[0],
            target[1],
            target[2] + args.fixture_wall_correction_target_height,
        ],
        dtype=np.float64,
    )
    action = float(args.oracle_action_gain) * (desired - control_tip)
    action = limit_xy_action(action, args.fixture_wall_correction_max_xy_action)
    action = limit_z_action(
        action,
        max_down_action=args.fixture_wall_correction_max_down_action,
        max_up_action=args.guarded_max_up_action,
    )
    return (
        np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32),
        "fixture_wall_recenter",
    )


def insert_drift_corrective_action(
    env: PegInHoleMujocoEnv,
    info: dict[str, Any],
    *,
    args: argparse.Namespace,
    alignment_stable_steps: int,
    ever_within_insert_xy: bool,
) -> tuple[np.ndarray, str, bool, bool]:
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    applied_action = np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64)
    control_tip = tip + float(args.guarded_prediction_steps) * applied_action
    dist_xy = float(np.linalg.norm(control_tip[:2] - target[:2]))
    stable_insert = bool(
        ever_within_insert_xy
        and dist_xy <= args.insert_drift_stable_xy
        and alignment_stable_steps >= args.insert_drift_stable_steps
    )
    if stable_insert:
        desired = np.asarray([target[0], target[1], target[2]], dtype=np.float64)
        action = float(args.oracle_action_gain) * (desired - control_tip)
        action = limit_xy_action(action, args.insert_drift_correction_max_xy_action)
        action = limit_z_action(
            action,
            max_down_action=args.insert_drift_correction_max_down_action,
            max_up_action=args.guarded_max_up_action,
        )
        return (
            np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32),
            "insert_drift_slow_insert",
            False,
            False,
        )

    desired = np.asarray([target[0], target[1], control_tip[2]], dtype=np.float64)
    action = float(args.oracle_action_gain) * (desired - control_tip)
    action = limit_xy_action(action, args.insert_drift_correction_max_xy_action)
    action = limit_z_action(
        action,
        max_down_action=0.0,
        max_up_action=args.guarded_max_up_action,
    )
    return (
        np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32),
        "insert_drift_recenter",
        True,
        True,
    )


def insert_settle_corrective_action(
    env: PegInHoleMujocoEnv,
    info: dict[str, Any],
    *,
    args: argparse.Namespace,
    alignment_stable_steps: int,
    ever_within_insert_xy: bool,
) -> tuple[np.ndarray, str, bool, bool]:
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    applied_action = np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64)
    control_tip = tip + float(args.guarded_prediction_steps) * applied_action
    dist_xy = float(np.linalg.norm(control_tip[:2] - target[:2]))
    z_above_target = float(control_tip[2] - target[2])
    stable_for_insert = bool(
        ever_within_insert_xy
        and dist_xy <= args.insert_settle_insert_xy
        and alignment_stable_steps >= args.insert_settle_stable_steps
    )

    if stable_for_insert:
        desired = np.asarray([target[0], target[1], target[2]], dtype=np.float64)
        action = float(args.oracle_action_gain) * (desired - control_tip)
        action = limit_xy_action(action, args.insert_settle_max_xy_action)
        action = limit_z_action(
            action,
            max_down_action=args.insert_settle_max_down_action,
            max_up_action=args.guarded_max_up_action,
        )
        return (
            np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32),
            "insert_settle_slow_insert",
            False,
            False,
        )

    needs_lift = bool(
        z_above_target <= args.insert_settle_lift_z_max
        and dist_xy > args.insert_settle_insert_xy
    )
    target_hover_z = float(target[2] + args.insert_settle_hover_height)
    if needs_lift:
        desired = np.asarray([target[0], target[1], target_hover_z], dtype=np.float64)
        action = float(args.oracle_action_gain) * (desired - control_tip)
        action = limit_xy_action(action, args.insert_settle_max_xy_action)
        action = limit_z_action(
            action,
            max_down_action=0.0,
            max_up_action=args.guarded_max_up_action,
        )
        return (
            np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32),
            "insert_settle_lift_recenter",
            True,
            True,
        )

    if dist_xy <= args.insert_settle_settle_xy:
        desired_z = target_hover_z
        desired = np.asarray([target[0], target[1], desired_z], dtype=np.float64)
        action = float(args.oracle_action_gain) * (desired - control_tip)
        action = limit_xy_action(action, args.insert_settle_max_xy_action)
        action = limit_z_action(
            action,
            max_down_action=args.insert_settle_max_down_action,
            max_up_action=args.guarded_max_up_action,
        )
        return (
            np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32),
            "insert_settle_settle",
            True,
            True,
        )

    desired = np.asarray([target[0], target[1], control_tip[2]], dtype=np.float64)
    action = float(args.oracle_action_gain) * (desired - control_tip)
    action = limit_xy_action(action, args.insert_settle_max_xy_action)
    action = limit_z_action(
        action,
        max_down_action=0.0,
        max_up_action=args.guarded_max_up_action,
    )
    return (
        np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32),
        "insert_settle_recenter",
        True,
        True,
    )


def corrective_action_for_state(
    env: PegInHoleMujocoEnv,
    info: dict[str, Any],
    oracle_config: OracleControllerConfig,
    *,
    args: argparse.Namespace,
    alignment_stable_steps: int,
    ever_within_insert_xy: bool,
) -> tuple[np.ndarray, str | None, bool, bool]:
    dist_xy = float(info["dist_xy"])
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    z_above_target = float(tip[2] - target[2])
    if args.fixture_wall_correction_labels and is_fixture_wall_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        args=args,
    ):
        corrective_action, phase = fixture_wall_precontact_corrective_action(
            env,
            info,
            args=args,
        )
        return (
            corrective_action.astype(np.float64),
            phase,
            False,
            True,
        )
    if args.insert_settle_correction_labels and is_insert_settle_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        ever_within_insert_xy=ever_within_insert_xy,
        args=args,
    ):
        return insert_settle_corrective_action(
            env,
            info,
            args=args,
            alignment_stable_steps=alignment_stable_steps,
            ever_within_insert_xy=ever_within_insert_xy,
        )
    if args.insert_drift_correction_labels and is_insert_drift_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        ever_within_insert_xy=ever_within_insert_xy,
        args=args,
    ):
        return insert_drift_corrective_action(
            env,
            info,
            args=args,
            alignment_stable_steps=alignment_stable_steps,
            ever_within_insert_xy=ever_within_insert_xy,
        )
    if args.approach_correction_labels and is_approach_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        args=args,
    ):
        return (
            approach_recenter_corrective_action(env, info, args=args).astype(np.float64),
            "approach_recenter",
            False,
            True,
        )
    if args.balanced_v4b_labels:
        return balanced_v4b_corrective_action(
            env,
            info,
            args=args,
            alignment_stable_steps=alignment_stable_steps,
            ever_within_insert_xy=ever_within_insert_xy,
        )
    return oracle_action(env, info, oracle_config).astype(np.float64), None, False, False


def read_diagnostics(info: dict[str, Any]) -> dict[str, float | np.ndarray]:
    hole_half_size = float(info.get("hole_half_size", np.nan))
    peg_radius = float(info.get("peg_radius", np.nan))
    hole_center_offset = np.asarray(
        info.get("hole_center_offset", [np.nan, np.nan]),
        dtype=np.float32,
    )
    if hole_center_offset.shape != (2,):
        hole_center_offset = np.full(2, np.nan, dtype=np.float32)
    return {
        "hole_half_size": hole_half_size,
        "peg_radius": peg_radius,
        "hole_clearance": hole_half_size - peg_radius,
        "control_action_scale_multiplier": float(
            info.get("control_action_scale_multiplier", np.nan)
        ),
        "control_action_noise_std": float(info.get("control_action_noise_std", np.nan)),
        "control_action_delay": float(info.get("control_action_delay", -1)),
        "control_action_filter_alpha": float(info.get("control_action_filter_alpha", np.nan)),
        "fixture_height_offset": float(info.get("fixture_height_offset", np.nan)),
        "table_height_offset": float(info.get("table_height_offset", np.nan)),
        "contact_friction_multiplier": float(info.get("contact_friction_multiplier", np.nan)),
        "contact_solref_time_multiplier": float(info.get("contact_solref_time_multiplier", np.nan)),
        "contact_solref_damping_multiplier": float(
            info.get("contact_solref_damping_multiplier", np.nan)
        ),
        "contact_solimp_width_multiplier": float(
            info.get("contact_solimp_width_multiplier", np.nan)
        ),
        "joint_damping_multiplier": float(info.get("joint_damping_multiplier", np.nan)),
        "actuator_kp_multiplier": float(info.get("actuator_kp_multiplier", np.nan)),
        "action_tracking_error": float(info.get("action_tracking_error", np.nan)),
        "ik_target_error": float(info.get("ik_target_error", np.nan)),
        "ik_iterations": float(info.get("ik_iterations", -1)),
        "joint_target_error": float(info.get("joint_target_error", np.nan)),
        "geometry_profile": str(info.get("geometry_profile", "")),
        "geometry_name": str(info.get("geometry_name", "")),
        "peg_shape": str(info.get("peg_shape", "")),
        "hole_shape": str(info.get("hole_shape", "")),
        "hole_center_offset": hole_center_offset.astype(np.float32, copy=True),
        "action_target_tip_delta": np.asarray(
            info.get("action_target_tip_delta", [np.nan, np.nan, np.nan]),
            dtype=np.float32,
        ),
        "action_actual_tip_delta": np.asarray(
            info.get("action_actual_tip_delta", [np.nan, np.nan, np.nan]),
            dtype=np.float32,
        ),
        "action_tip_delta_error": np.asarray(
            info.get("action_tip_delta_error", [np.nan, np.nan, np.nan]),
            dtype=np.float32,
        ),
        "joint_target_qpos": np.asarray(
            info.get("joint_target_qpos", [np.nan] * 6),
            dtype=np.float32,
        ),
        "joint_qpos_after_action": np.asarray(
            info.get("joint_qpos_after_action", [np.nan] * 6),
            dtype=np.float32,
        ),
    }


def outcome(info: dict[str, Any], truncated: bool) -> str:
    if bool(info["insertion_success"]):
        return "success"
    if bool(info["collision"]):
        return "collision"
    if truncated:
        return "timeout"
    return "terminated_failure"


def should_keep_sample(sample: dict[str, Any], args: argparse.Namespace) -> bool:
    if float(sample["correction_norm"]) < args.min_correction_norm:
        return False
    if (
        args.episode_outcome_filter != "any"
        and sample["episode_outcome"] != args.episode_outcome_filter
    ):
        return False
    if bool(sample.get("recovery_branch", False)):
        return True
    if args.selection == "failed_episode_all":
        return True
    if args.selection in ("timeout_progress_window", "timeout_progress_failure_window"):
        in_progress_window = (
            bool(sample["episode_timeout"])
            and bool(sample["timeout_progress_window"])
        )
        if args.selection == "timeout_progress_failure_window":
            return bool(in_progress_window and sample["failure_window"])
        return bool(in_progress_window)
    if args.selection in ("insert_drift_window", "insert_drift_failure_window"):
        in_insert_drift_window = bool(sample["insert_drift_window"])
        if args.selection == "insert_drift_failure_window":
            return bool(in_insert_drift_window and sample["failure_window"])
        return in_insert_drift_window
    if args.selection in ("insert_settle_window", "insert_settle_failure_window"):
        in_insert_settle_window = bool(sample["insert_settle_window"])
        if args.selection == "insert_settle_failure_window":
            return bool(in_insert_settle_window and sample["failure_window"])
        return in_insert_settle_window
    if args.selection in ("balanced_v4b_window", "balanced_v4b_failure_window"):
        in_balanced_window = bool(sample["balanced_v4b_window"])
        if args.selection == "balanced_v4b_failure_window":
            return bool(in_balanced_window and sample["failure_window"])
        return in_balanced_window
    if args.selection in ("approach_window", "approach_failure_window"):
        in_approach_window = bool(sample["approach_window"])
        if args.selection == "approach_failure_window":
            return bool(in_approach_window and sample["failure_window"])
        return in_approach_window
    if args.selection in ("fixture_wall_window", "fixture_wall_failure_window"):
        in_fixture_wall_window = bool(sample["fixture_wall_window"])
        if args.selection == "fixture_wall_failure_window":
            return bool(in_fixture_wall_window and sample["failure_window"])
        return in_fixture_wall_window
    if args.selection == "failed_episode_near_hole":
        return bool(sample["near_hole"])
    if args.selection == "near_hole":
        return bool(sample["near_hole"])
    if args.selection == "near_hole_failure_window":
        return bool(sample["failure_window"] and sample["near_hole"])
    return bool(sample["failure_window"])


def snapshot_env(env: PegInHoleMujocoEnv) -> dict[str, Any]:
    return {
        "qpos": env.data.qpos.copy(),
        "qvel": env.data.qvel.copy(),
        "ctrl": env.data.ctrl.copy(),
        "act": env.data.act.copy() if env.data.act is not None else None,
        "mocap_pos": env.data.mocap_pos.copy(),
        "mocap_quat": env.data.mocap_quat.copy(),
        "time": float(env.data.time),
        "step_count": int(env.step_count),
        "previous_shaped_distance": float(env.previous_shaped_distance),
        "action_delay_buffer": [action.copy() for action in env.action_delay_buffer],
        "previous_filtered_action": env.previous_filtered_action.copy(),
        "last_commanded_action": env.last_commanded_action.copy(),
        "last_applied_action": env.last_applied_action.copy(),
        "last_tip_pos_before_action": env.last_tip_pos_before_action.copy(),
        "last_target_tip_pos": env.last_target_tip_pos.copy(),
        "last_target_tip_delta": env.last_target_tip_delta.copy(),
        "last_ik_tip_pos": env.last_ik_tip_pos.copy(),
        "last_ik_target_error": float(env.last_ik_target_error),
        "last_ik_iterations": int(env.last_ik_iterations),
        "last_joint_qpos_before_action": env.last_joint_qpos_before_action.copy(),
        "last_joint_target_qpos": env.last_joint_target_qpos.copy(),
        "last_joint_qpos_after_action": env.last_joint_qpos_after_action.copy(),
        "last_joint_target_error": float(env.last_joint_target_error),
        "last_actual_tip_delta": env.last_actual_tip_delta.copy(),
        "last_tip_delta_error": env.last_tip_delta_error.copy(),
        "last_action_tracking_error": float(env.last_action_tracking_error),
        "rng_state": copy.deepcopy(env.np_random.bit_generator.state),
    }


def restore_env(env: PegInHoleMujocoEnv, snapshot: dict[str, Any]) -> None:
    env.data.qpos[:] = snapshot["qpos"]
    env.data.qvel[:] = snapshot["qvel"]
    env.data.ctrl[:] = snapshot["ctrl"]
    if snapshot["act"] is not None and env.data.act is not None:
        env.data.act[:] = snapshot["act"]
    env.data.mocap_pos[:] = snapshot["mocap_pos"]
    env.data.mocap_quat[:] = snapshot["mocap_quat"]
    env.data.time = float(snapshot["time"])
    env.step_count = int(snapshot["step_count"])
    env.previous_shaped_distance = float(snapshot["previous_shaped_distance"])
    env.action_delay_buffer = [action.copy() for action in snapshot["action_delay_buffer"]]
    env.previous_filtered_action = snapshot["previous_filtered_action"].copy()
    env.last_commanded_action = snapshot["last_commanded_action"].copy()
    env.last_applied_action = snapshot["last_applied_action"].copy()
    env.last_tip_pos_before_action = snapshot["last_tip_pos_before_action"].copy()
    env.last_target_tip_pos = snapshot["last_target_tip_pos"].copy()
    env.last_target_tip_delta = snapshot["last_target_tip_delta"].copy()
    env.last_ik_tip_pos = snapshot["last_ik_tip_pos"].copy()
    env.last_ik_target_error = float(snapshot["last_ik_target_error"])
    env.last_ik_iterations = int(snapshot["last_ik_iterations"])
    env.last_joint_qpos_before_action = snapshot["last_joint_qpos_before_action"].copy()
    env.last_joint_target_qpos = snapshot["last_joint_target_qpos"].copy()
    env.last_joint_qpos_after_action = snapshot["last_joint_qpos_after_action"].copy()
    env.last_joint_target_error = float(snapshot["last_joint_target_error"])
    env.last_actual_tip_delta = snapshot["last_actual_tip_delta"].copy()
    env.last_tip_delta_error = snapshot["last_tip_delta_error"].copy()
    env.last_action_tracking_error = float(snapshot["last_action_tracking_error"])
    env.np_random.bit_generator.state = copy.deepcopy(snapshot["rng_state"])
    import mujoco

    mujoco.mj_forward(env.model, env.data)


def make_sample(
    env: PegInHoleMujocoEnv,
    obs: dict[str, np.ndarray],
    info: dict[str, Any],
    policy_action: np.ndarray,
    corrective_action: np.ndarray,
    *,
    args: argparse.Namespace,
    tier: ClearanceTier,
    scenario: Scenario,
    episode_id: int,
    seed: int,
    recovery_branch: bool = False,
    synthetic_recovery_state: bool = False,
    branch_id: int = -1,
    branch_step_id: int = -1,
    branch_source_step_id: int = -1,
    phase_override: str | None = None,
    alignment_stable_steps: int = 0,
    ever_within_insert_xy: bool = False,
    drift_after_alignment: bool = False,
    descent_should_block: bool = False,
) -> dict[str, Any]:
    policy_action = np.asarray(policy_action, dtype=np.float64).reshape(3)
    corrective_action = np.asarray(corrective_action, dtype=np.float64).reshape(3)
    correction = corrective_action - policy_action
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    z_above_target = float(tip[2] - target[2])
    dist_xy = float(info["dist_xy"])
    near_hole = dist_xy <= args.near_hole_xy and z_above_target <= args.near_hole_z
    contact_recovery_window = (
        dist_xy > args.contact_recovery_xy_tolerance
        and z_above_target <= args.contact_recovery_z_max
    )
    timeout_progress_window = (
        dist_xy <= args.timeout_progress_xy_tolerance
        and z_above_target <= args.timeout_progress_z_max
    )
    insert_drift_window = is_insert_drift_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        ever_within_insert_xy=ever_within_insert_xy,
        args=args,
    )
    insert_settle_window = is_insert_settle_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        ever_within_insert_xy=ever_within_insert_xy,
        args=args,
    )
    balanced_v4b_window = (
        dist_xy <= args.balanced_v4b_window_xy
        and z_above_target <= args.balanced_v4b_window_z_max
    )
    approach_window = is_approach_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        args=args,
    )
    fixture_wall_window = is_fixture_wall_window(
        dist_xy=dist_xy,
        z_above_target=z_above_target,
        args=args,
    )
    sample_recovery_phase = (
        phase_override
        if phase_override is not None
        else recovery_phase(
            dist_xy=dist_xy,
            z_above_target=z_above_target,
            oracle_action_raw=corrective_action,
            ever_within_insert_xy=ever_within_insert_xy,
            alignment_stable_steps=alignment_stable_steps,
            args=args,
        )
    )
    cosine = action_cosine(policy_action, corrective_action)
    return {
        "cam_image": obs["cam_image"].copy(),
        "near_hole_crop": (
            obs["near_hole_crop"].copy() if args.include_near_hole_crop else None
        ),
        "control_state": (
            obs["control_state"].copy() if args.include_control_state else None
        ),
        "raw_action": corrective_action.astype(np.float32),
        "action": (corrective_action / env.action_scale).astype(np.float32),
        "policy_raw_action": policy_action.astype(np.float32),
        "policy_action": (policy_action / env.action_scale).astype(np.float32),
        "correction_raw_action": correction.astype(np.float32),
        "target_pos": target.astype(np.float32),
        "peg_tip_pos": tip.astype(np.float32),
        "desired_z": float(info["desired_z"]),
        "tier": tier.name,
        "scenario": scenario.name,
        "episode_id": episode_id,
        "seed": seed,
        "step_id": int(info["step_count"]),
        "dist_xy": dist_xy,
        "dist_z": float(info["dist_z"]),
        "z_above_target": z_above_target,
        "near_hole": bool(near_hole),
        "contact_recovery_window": bool(contact_recovery_window),
        "timeout_progress_window": bool(timeout_progress_window),
        "insert_drift_window": bool(insert_drift_window),
        "insert_settle_window": bool(insert_settle_window),
        "balanced_v4b_window": bool(balanced_v4b_window),
        "approach_window": bool(approach_window),
        "fixture_wall_window": bool(fixture_wall_window),
        "alignment_stable_steps": int(alignment_stable_steps),
        "ever_within_insert_xy": bool(ever_within_insert_xy),
        "drift_after_alignment": bool(drift_after_alignment),
        "descent_should_block": bool(descent_should_block),
        "recovery_phase": sample_recovery_phase,
        "oracle_lift_action": bool(corrective_action[2] > 1e-6),
        "oracle_down_action": bool(corrective_action[2] < -1e-6),
        "recovery_branch": bool(recovery_branch),
        "synthetic_recovery_state": bool(synthetic_recovery_state),
        "branch_id": int(branch_id),
        "branch_step_id": int(branch_step_id),
        "branch_source_step_id": int(branch_source_step_id),
        "policy_norm": float(np.linalg.norm(policy_action)),
        "oracle_norm": float(np.linalg.norm(corrective_action)),
        "correction_norm": float(np.linalg.norm(correction)),
        "correction_xy_norm": float(np.linalg.norm(correction[:2])),
        "action_cosine": cosine,
        "opposed_actions": bool(cosine < 0.0),
        "policy_down_or_oracle_up": bool(policy_action[2] < 0.0 and corrective_action[2] > 0.0),
        "policy_down_oracle_less_down": bool(policy_action[2] < corrective_action[2]),
        "diagnostics": read_diagnostics(info),
    }


def collect_recovery_branch_samples(
    env: PegInHoleMujocoEnv,
    model: Any,
    oracle_config: OracleControllerConfig,
    *,
    args: argparse.Namespace,
    tier: ClearanceTier,
    scenario: Scenario,
    episode_id: int,
    seed: int,
    start_sample: dict[str, Any],
    branch_id: int,
) -> list[dict[str, Any]]:
    snapshot = start_sample.get("_env_snapshot")
    if snapshot is None:
        return []

    restore_env(env, snapshot)
    if args.recovery_branch_clear_control_history:
        env.action_delay_buffer = [
            np.zeros(3, dtype=np.float64) for _ in range(env.current_action_delay)
        ]
        env.previous_filtered_action = np.zeros(3, dtype=np.float64)
        env.last_commanded_action = np.zeros(3, dtype=np.float64)
        env.last_applied_action = np.zeros(3, dtype=np.float64)
    rows: list[dict[str, Any]] = []
    source_step_id = int(start_sample["step_id"])
    previous_phase = ""
    alignment_stable_steps = int(start_sample.get("alignment_stable_steps", 0))
    ever_within_insert_xy = bool(start_sample.get("ever_within_insert_xy", False))
    for branch_step_id in range(args.recovery_branch_max_steps):
        obs = env._get_obs()
        info = env._get_info()
        current_dist_xy = float(info["dist_xy"])
        if current_dist_xy <= args.balanced_v4b_stable_xy:
            alignment_stable_steps += 1
        else:
            alignment_stable_steps = 0
        ever_within_insert_xy = bool(
            ever_within_insert_xy
            or current_dist_xy <= args.guarded_insert_xy_tolerance
        )
        policy_action, _ = model.predict(obs, deterministic=True)
        policy_action = np.asarray(policy_action, dtype=np.float64).reshape(3)
        (
            corrective_action,
            phase_override,
            drift_after_alignment,
            descent_should_block,
        ) = corrective_action_for_state(
            env,
            info,
            oracle_config,
            args=args,
            alignment_stable_steps=alignment_stable_steps,
            ever_within_insert_xy=ever_within_insert_xy,
        )
        sample = make_sample(
            env,
            obs,
            info,
            policy_action,
            corrective_action,
            args=args,
            tier=tier,
            scenario=scenario,
            episode_id=episode_id,
            seed=seed,
            recovery_branch=True,
            branch_id=branch_id,
            branch_step_id=branch_step_id,
            branch_source_step_id=source_step_id,
            phase_override=phase_override,
            alignment_stable_steps=alignment_stable_steps,
            ever_within_insert_xy=ever_within_insert_xy,
            drift_after_alignment=drift_after_alignment,
            descent_should_block=descent_should_block,
        )
        phase_changed = sample["recovery_phase"] != previous_phase
        if branch_step_id % args.recovery_branch_stride == 0 or phase_changed:
            rows.append(sample)
        previous_phase = str(sample["recovery_phase"])

        _, _, terminated, truncated, next_info = env.step(corrective_action.astype(np.float32))
        if terminated or truncated:
            if args.recovery_branch_stop_on_success or bool(next_info["collision"]):
                break
    return rows


def set_tip_kinematic_state(env: PegInHoleMujocoEnv, tip_target: np.ndarray) -> None:
    qpos = env._solve_position_ik(np.asarray(tip_target, dtype=np.float64))
    env._set_arm_qpos(env.data, qpos)
    env._set_arm_control(qpos)
    env.data.qvel[:] = 0.0
    import mujoco

    mujoco.mj_forward(env.model, env.data)
    env._reset_action_tracking_diagnostics()
    env.previous_shaped_distance, _ = env._staged_distance()


def collect_synthetic_recovery_stage_samples(
    env: PegInHoleMujocoEnv,
    model: Any,
    oracle_config: OracleControllerConfig,
    *,
    args: argparse.Namespace,
    tier: ClearanceTier,
    scenario: Scenario,
    episode_id: int,
    seed: int,
    start_sample: dict[str, Any],
    branch_id: int,
) -> list[dict[str, Any]]:
    snapshot = start_sample.get("_env_snapshot")
    if snapshot is None:
        return []

    restore_env(env, snapshot)
    info = env._get_info()
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    lift_z = float(target[2] + args.contact_recovery_lift_height)
    stage_targets = (
        np.asarray([tip[0], tip[1], lift_z], dtype=np.float64),
        np.asarray([target[0], target[1], lift_z], dtype=np.float64),
    )

    rows: list[dict[str, Any]] = []
    source_step_id = int(start_sample["step_id"])
    for synthetic_index, tip_target in enumerate(stage_targets):
        restore_env(env, snapshot)
        if args.recovery_branch_clear_control_history:
            env.action_delay_buffer = [
                np.zeros(3, dtype=np.float64) for _ in range(env.current_action_delay)
            ]
            env.previous_filtered_action = np.zeros(3, dtype=np.float64)
            env.last_commanded_action = np.zeros(3, dtype=np.float64)
            env.last_applied_action = np.zeros(3, dtype=np.float64)
        set_tip_kinematic_state(env, tip_target)
        obs = env._get_obs()
        info = env._get_info()
        policy_action, _ = model.predict(obs, deterministic=True)
        current_dist_xy = float(info["dist_xy"])
        alignment_stable_steps = (
            args.balanced_v4b_stable_steps
            if current_dist_xy <= args.balanced_v4b_stable_xy
            else 0
        )
        ever_within_insert_xy = bool(
            start_sample.get("ever_within_insert_xy", False)
            or current_dist_xy <= args.guarded_insert_xy_tolerance
        )
        (
            corrective_action,
            phase_override,
            drift_after_alignment,
            descent_should_block,
        ) = corrective_action_for_state(
            env,
            info,
            oracle_config,
            args=args,
            alignment_stable_steps=alignment_stable_steps,
            ever_within_insert_xy=ever_within_insert_xy,
        )
        rows.append(
            make_sample(
                env,
                obs,
                info,
                np.asarray(policy_action, dtype=np.float64).reshape(3),
                corrective_action,
                args=args,
                tier=tier,
                scenario=scenario,
                episode_id=episode_id,
                seed=seed,
                recovery_branch=True,
                synthetic_recovery_state=True,
                branch_id=branch_id,
                branch_step_id=10_000 + synthetic_index,
                branch_source_step_id=source_step_id,
                phase_override=phase_override,
                alignment_stable_steps=alignment_stable_steps,
                ever_within_insert_xy=ever_within_insert_xy,
                drift_after_alignment=drift_after_alignment,
                descent_should_block=descent_should_block,
            )
        )
    return rows


def run_episode(
    env: PegInHoleMujocoEnv,
    model: Any,
    oracle_config: OracleControllerConfig,
    *,
    args: argparse.Namespace,
    tier: ClearanceTier,
    scenario: Scenario,
    episode_id: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    obs, info = env.reset(seed=seed)
    rows: list[dict[str, Any]] = []
    episode_return = 0.0
    terminated = False
    truncated = False
    alignment_stable_steps = 0
    ever_within_insert_xy = False

    while True:
        current_dist_xy = float(info["dist_xy"])
        if current_dist_xy <= args.balanced_v4b_stable_xy:
            alignment_stable_steps += 1
        else:
            alignment_stable_steps = 0
        ever_within_insert_xy = bool(
            ever_within_insert_xy
            or current_dist_xy <= args.guarded_insert_xy_tolerance
        )
        policy_action, _ = model.predict(obs, deterministic=True)
        policy_action = np.asarray(policy_action, dtype=np.float64).reshape(3)
        (
            corrective_action,
            phase_override,
            drift_after_alignment,
            descent_should_block,
        ) = corrective_action_for_state(
            env,
            info,
            oracle_config,
            args=args,
            alignment_stable_steps=alignment_stable_steps,
            ever_within_insert_xy=ever_within_insert_xy,
        )
        sample = make_sample(
            env,
            obs,
            info,
            policy_action,
            corrective_action,
            args=args,
            tier=tier,
            scenario=scenario,
            episode_id=episode_id,
            seed=seed,
            phase_override=phase_override,
            alignment_stable_steps=alignment_stable_steps,
            ever_within_insert_xy=ever_within_insert_xy,
            drift_after_alignment=drift_after_alignment,
            descent_should_block=descent_should_block,
        )
        branch_window = (
            bool(sample["near_hole"])
            and (
                bool(sample["contact_recovery_window"])
                or bool(args.recovery_branch_from_near_hole)
            )
        )
        if (
            args.recovery_branch_rollout
            and branch_window
            and float(sample["correction_norm"]) >= args.min_correction_norm
        ):
            sample["_env_snapshot"] = snapshot_env(env)
        rows.append(sample)

        obs, reward, terminated, truncated, info = env.step(policy_action.astype(np.float32))
        episode_return += float(reward)
        if terminated or truncated:
            break

    final_step = int(info["step_count"])
    episode_outcome = outcome(info, truncated)
    for sample in rows:
        sample["episode_outcome"] = episode_outcome
        sample["episode_success"] = bool(info["insertion_success"])
        sample["episode_collision"] = bool(info["collision"])
        sample["episode_timeout"] = bool(truncated and not info["insertion_success"])
        sample["final_step"] = final_step
        sample["steps_to_end"] = final_step - int(sample["step_id"])
        sample["failure_window"] = bool(
            not info["insertion_success"]
            and int(sample["steps_to_end"]) <= args.failure_window_steps
        )

    if args.recovery_branch_rollout and rows and not rows[-1]["episode_success"]:
        branch_starts = [
            sample
            for sample in rows
            if should_keep_sample(sample, args) and "_env_snapshot" in sample
        ]
        branch_starts.sort(key=lambda item: float(item["correction_norm"]), reverse=True)
        for branch_id, start_sample in enumerate(
            branch_starts[: args.recovery_branch_max_starts_per_episode]
        ):
            branch_rows = collect_recovery_branch_samples(
                env,
                model,
                oracle_config,
                args=args,
                tier=tier,
                scenario=scenario,
                episode_id=episode_id,
                seed=seed,
                start_sample=start_sample,
                branch_id=branch_id,
            )
            for branch_sample in branch_rows:
                branch_sample["episode_outcome"] = episode_outcome
                branch_sample["episode_success"] = False
                branch_sample["episode_collision"] = bool(info["collision"])
                branch_sample["episode_timeout"] = bool(
                    truncated and not info["insertion_success"]
                )
                branch_sample["final_step"] = final_step
                branch_sample["steps_to_end"] = final_step - int(branch_sample["step_id"])
                branch_sample["failure_window"] = True
            rows.extend(branch_rows)
            if args.recovery_branch_synthetic_stages:
                synthetic_rows = collect_synthetic_recovery_stage_samples(
                    env,
                    model,
                    oracle_config,
                    args=args,
                    tier=tier,
                    scenario=scenario,
                    episode_id=episode_id,
                    seed=seed,
                    start_sample=start_sample,
                    branch_id=branch_id,
                )
                for synthetic_sample in synthetic_rows:
                    synthetic_sample["episode_outcome"] = episode_outcome
                    synthetic_sample["episode_success"] = False
                    synthetic_sample["episode_collision"] = bool(info["collision"])
                    synthetic_sample["episode_timeout"] = bool(
                        truncated and not info["insertion_success"]
                    )
                    synthetic_sample["final_step"] = final_step
                    synthetic_sample["steps_to_end"] = (
                        final_step - int(synthetic_sample["branch_source_step_id"])
                    )
                    synthetic_sample["failure_window"] = True
                rows.extend(synthetic_rows)

    episode_summary = {
        "tier": tier.name,
        "scenario": scenario.name,
        "episode_id": episode_id,
        "seed": seed,
        "outcome": episode_outcome,
        "success": bool(info["insertion_success"]),
        "collision": bool(info["collision"]),
        "timeout": bool(truncated and not info["insertion_success"]),
        "steps": final_step,
        "episode_return": float(episode_return),
        "final_dist_xy": float(info["dist_xy"]),
        "final_dist_z": float(info["dist_z"]),
        "hole_clearance": float(info.get("hole_half_size", np.nan) - info.get("peg_radius", np.nan)),
    }
    return rows, episode_summary


def select_episode_samples(rows: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    if rows and rows[-1]["episode_success"] and not args.keep_success_episodes:
        return []
    candidates = [sample for sample in rows if should_keep_sample(sample, args)]
    if args.fixture_wall_correction_labels or args.selection.startswith("fixture_wall"):
        grouped: dict[str, list[dict[str, Any]]] = {
            "fixture_wall_lift_before_lateral": [],
            "fixture_wall_recenter": [],
            "insert_drift_recenter": [],
            "insert_drift_slow_insert": [],
            "approach_recenter": [],
            "realign": [],
            "progress_insert": [],
            "slow_insert": [],
            "hover_recenter": [],
            "block_down": [],
            "unjam_lift": [],
            "hold": [],
        }
        for sample in candidates:
            grouped.setdefault(str(sample["recovery_phase"]), []).append(sample)
        for phase_samples in grouped.values():
            phase_samples.sort(key=lambda item: float(item["correction_norm"]), reverse=True)

        selected: list[dict[str, Any]] = []
        phases = (
            "fixture_wall_lift_before_lateral",
            "fixture_wall_recenter",
            "insert_drift_recenter",
            "insert_drift_slow_insert",
            "approach_recenter",
            "realign",
            "progress_insert",
            "slow_insert",
            "hover_recenter",
            "block_down",
            "unjam_lift",
            "hold",
        )
        while len(selected) < args.max_samples_per_episode:
            added = False
            for phase in phases:
                phase_samples = grouped.get(phase, [])
                if phase_samples and len(selected) < args.max_samples_per_episode:
                    selected.append(phase_samples.pop(0))
                    added = True
            if not added:
                break
        if selected:
            return selected

    if args.insert_drift_correction_labels or args.selection.startswith("insert_drift"):
        grouped: dict[str, list[dict[str, Any]]] = {
            "insert_drift_recenter": [],
            "insert_drift_slow_insert": [],
            "progress_insert": [],
            "slow_insert": [],
            "realign": [],
            "hold": [],
        }
        for sample in candidates:
            grouped.setdefault(str(sample["recovery_phase"]), []).append(sample)
        for phase_samples in grouped.values():
            phase_samples.sort(key=lambda item: float(item["correction_norm"]), reverse=True)

        selected: list[dict[str, Any]] = []
        phases = (
            "insert_drift_recenter",
            "insert_drift_slow_insert",
            "progress_insert",
            "slow_insert",
            "realign",
            "hold",
        )
        while len(selected) < args.max_samples_per_episode:
            added = False
            for phase in phases:
                phase_samples = grouped.get(phase, [])
                if phase_samples and len(selected) < args.max_samples_per_episode:
                    selected.append(phase_samples.pop(0))
                    added = True
            if not added:
                break
        if selected:
            return selected

    if args.insert_settle_correction_labels or args.selection.startswith("insert_settle"):
        grouped: dict[str, list[dict[str, Any]]] = {
            "insert_settle_slow_insert": [],
            "insert_settle_settle": [],
            "insert_settle_lift_recenter": [],
            "insert_settle_recenter": [],
            "progress_insert": [],
            "slow_insert": [],
            "realign": [],
            "hold": [],
        }
        for sample in candidates:
            grouped.setdefault(str(sample["recovery_phase"]), []).append(sample)
        for phase_samples in grouped.values():
            phase_samples.sort(key=lambda item: float(item["correction_norm"]), reverse=True)

        selected: list[dict[str, Any]] = []
        phases = (
            "insert_settle_slow_insert",
            "insert_settle_settle",
            "insert_settle_lift_recenter",
            "insert_settle_recenter",
            "progress_insert",
            "slow_insert",
            "realign",
            "hold",
        )
        while len(selected) < args.max_samples_per_episode:
            added = False
            for phase in phases:
                phase_samples = grouped.get(phase, [])
                if phase_samples and len(selected) < args.max_samples_per_episode:
                    selected.append(phase_samples.pop(0))
                    added = True
            if not added:
                break
        if selected:
            return selected

    if args.approach_correction_labels or args.selection.startswith("approach"):
        grouped: dict[str, list[dict[str, Any]]] = {
            "approach_recenter": [],
            "realign": [],
            "progress_insert": [],
            "slow_insert": [],
            "hover_recenter": [],
            "block_down": [],
            "unjam_lift": [],
            "hold": [],
        }
        for sample in candidates:
            grouped.setdefault(str(sample["recovery_phase"]), []).append(sample)
        for phase_samples in grouped.values():
            phase_samples.sort(key=lambda item: float(item["correction_norm"]), reverse=True)

        selected: list[dict[str, Any]] = []
        phases = (
            "approach_recenter",
            "realign",
            "progress_insert",
            "slow_insert",
            "hover_recenter",
            "block_down",
            "unjam_lift",
            "hold",
        )
        while len(selected) < args.max_samples_per_episode:
            added = False
            for phase in phases:
                phase_samples = grouped.get(phase, [])
                if phase_samples and len(selected) < args.max_samples_per_episode:
                    selected.append(phase_samples.pop(0))
                    added = True
            if not added:
                break
        if selected:
            return selected

    if args.balanced_v4b_labels and args.selection.startswith("balanced_v4b"):
        grouped: dict[str, list[dict[str, Any]]] = {
            "stable_slow_insert": [],
            "hover_recenter": [],
            "block_down": [],
            "unjam_lift": [],
        }
        for sample in candidates:
            grouped.setdefault(str(sample["recovery_phase"]), []).append(sample)
        for phase_samples in grouped.values():
            phase_samples.sort(key=lambda item: float(item["correction_norm"]), reverse=True)

        selected: list[dict[str, Any]] = []
        phases = ("stable_slow_insert", "hover_recenter", "block_down", "unjam_lift")
        while len(selected) < args.max_samples_per_episode:
            added = False
            for phase in phases:
                phase_samples = grouped.get(phase, [])
                if phase_samples and len(selected) < args.max_samples_per_episode:
                    selected.append(phase_samples.pop(0))
                    added = True
            if not added:
                break
        if selected:
            return selected

    if args.recovery_branch_rollout:
        grouped: dict[str, list[dict[str, Any]]] = {
            "fixture_wall_lift_before_lateral": [],
            "fixture_wall_recenter": [],
            "unjam_lift": [],
            "realign": [],
            "slow_insert": [],
            "hold": [],
            "progress_insert": [],
            "insert_drift_recenter": [],
            "insert_drift_slow_insert": [],
        }
        for sample in candidates:
            grouped.setdefault(str(sample["recovery_phase"]), []).append(sample)
        for phase_samples in grouped.values():
            phase_samples.sort(key=lambda item: float(item["correction_norm"]), reverse=True)

        selected: list[dict[str, Any]] = []
        phases = (
            "fixture_wall_lift_before_lateral",
            "fixture_wall_recenter",
            "insert_drift_slow_insert",
            "insert_drift_recenter",
            "progress_insert",
            "slow_insert",
            "realign",
            "unjam_lift",
            "hold",
        )
        while len(selected) < args.max_samples_per_episode:
            added = False
            for phase in phases:
                phase_samples = grouped.get(phase, [])
                if phase_samples and len(selected) < args.max_samples_per_episode:
                    selected.append(phase_samples.pop(0))
                    added = True
            if not added:
                break
        if selected:
            return selected

    candidates.sort(key=lambda item: float(item["correction_norm"]), reverse=True)
    return candidates[: args.max_samples_per_episode]


def append_samples(
    buffers: dict[str, list[Any]],
    selected: list[dict[str, Any]],
    remaining: int,
) -> int:
    keep = min(remaining, len(selected))
    for sample in selected[:keep]:
        buffers["cam_images"].append(sample["cam_image"])
        if sample["near_hole_crop"] is not None:
            buffers["near_hole_crops"].append(sample["near_hole_crop"])
        if sample["control_state"] is not None:
            buffers["control_state"].append(sample["control_state"])
        for key in (
            "action",
            "raw_action",
            "policy_action",
            "policy_raw_action",
            "correction_raw_action",
            "target_pos",
            "peg_tip_pos",
        ):
            buffers[key].append(sample[key])
        for key in (
            "desired_z",
            "episode_id",
            "seed",
            "step_id",
            "dist_xy",
            "dist_z",
            "z_above_target",
            "near_hole",
            "contact_recovery_window",
            "timeout_progress_window",
            "insert_drift_window",
            "insert_settle_window",
            "balanced_v4b_window",
            "approach_window",
            "fixture_wall_window",
            "alignment_stable_steps",
            "ever_within_insert_xy",
            "drift_after_alignment",
            "descent_should_block",
            "oracle_lift_action",
            "oracle_down_action",
            "recovery_branch",
            "synthetic_recovery_state",
            "branch_id",
            "branch_step_id",
            "branch_source_step_id",
            "policy_norm",
            "oracle_norm",
            "correction_norm",
            "correction_xy_norm",
            "action_cosine",
            "opposed_actions",
            "policy_down_or_oracle_up",
            "policy_down_oracle_less_down",
            "final_step",
            "steps_to_end",
            "failure_window",
            "episode_success",
            "episode_collision",
            "episode_timeout",
        ):
            buffers[key].append(sample[key])
        buffers["tier"].append(sample["tier"])
        buffers["scenario"].append(sample["scenario"])
        buffers["episode_outcome"].append(sample["episode_outcome"])
        buffers["recovery_phase"].append(sample["recovery_phase"])
        for key, value in sample["diagnostics"].items():
            buffers[key].append(value)
    return keep


def empty_buffers() -> dict[str, list[Any]]:
    keys = [
        "cam_images",
        "near_hole_crops",
        "control_state",
        "action",
        "raw_action",
        "policy_action",
        "policy_raw_action",
        "correction_raw_action",
        "target_pos",
        "peg_tip_pos",
        "desired_z",
        "episode_id",
        "seed",
        "step_id",
        "dist_xy",
        "dist_z",
        "z_above_target",
        "near_hole",
        "contact_recovery_window",
        "timeout_progress_window",
        "insert_drift_window",
        "insert_settle_window",
        "balanced_v4b_window",
        "approach_window",
        "fixture_wall_window",
        "alignment_stable_steps",
        "ever_within_insert_xy",
        "drift_after_alignment",
        "descent_should_block",
        "oracle_lift_action",
        "oracle_down_action",
        "recovery_branch",
        "synthetic_recovery_state",
        "branch_id",
        "branch_step_id",
        "branch_source_step_id",
        "policy_norm",
        "oracle_norm",
        "correction_norm",
        "correction_xy_norm",
        "action_cosine",
        "opposed_actions",
        "policy_down_or_oracle_up",
        "policy_down_oracle_less_down",
        "final_step",
        "steps_to_end",
        "failure_window",
        "episode_success",
        "episode_collision",
        "episode_timeout",
        "tier",
        "scenario",
        "episode_outcome",
        "recovery_phase",
        *SCALAR_DIAGNOSTIC_KEYS,
        *TEXT_DIAGNOSTIC_KEYS,
        *VECTOR_DIAGNOSTIC_KEYS,
    ]
    return {key: [] for key in keys}


def summarize_float_array(values: np.ndarray) -> dict[str, float]:
    if values.size == 0:
        return {"mean": float("nan"), "min": float("nan"), "max": float("nan")}
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {"mean": float("nan"), "min": float("nan"), "max": float("nan")}
    return {
        "mean": float(np.mean(finite)),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
    }


def summarize_text_array(values: np.ndarray) -> dict[str, int]:
    unique, counts = np.unique(values.astype(str), return_counts=True)
    return {str(key): int(value) for key, value in zip(unique, counts)}


def build_arrays(
    buffers: dict[str, list[Any]],
    include_near_hole_crop: bool,
    include_control_state: bool,
) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {
        "cam_images": np.asarray(buffers["cam_images"], dtype=np.uint8),
        "actions": np.asarray(buffers["action"], dtype=np.float32),
        "raw_actions": np.asarray(buffers["raw_action"], dtype=np.float32),
        "policy_actions": np.asarray(buffers["policy_action"], dtype=np.float32),
        "policy_raw_actions": np.asarray(buffers["policy_raw_action"], dtype=np.float32),
        "correction_raw_actions": np.asarray(buffers["correction_raw_action"], dtype=np.float32),
        "target_pos": np.asarray(buffers["target_pos"], dtype=np.float32),
        "peg_tip_pos": np.asarray(buffers["peg_tip_pos"], dtype=np.float32),
        "desired_z": np.asarray(buffers["desired_z"], dtype=np.float32),
        "episode_id": np.asarray(buffers["episode_id"], dtype=np.int32),
        "seed": np.asarray(buffers["seed"], dtype=np.int32),
        "step_id": np.asarray(buffers["step_id"], dtype=np.int32),
        "dist_xy": np.asarray(buffers["dist_xy"], dtype=np.float32),
        "dist_z": np.asarray(buffers["dist_z"], dtype=np.float32),
        "z_above_target": np.asarray(buffers["z_above_target"], dtype=np.float32),
        "near_hole": np.asarray(buffers["near_hole"], dtype=np.bool_),
        "contact_recovery_window": np.asarray(
            buffers["contact_recovery_window"],
            dtype=np.bool_,
        ),
        "timeout_progress_window": np.asarray(
            buffers["timeout_progress_window"],
            dtype=np.bool_,
        ),
        "insert_drift_window": np.asarray(
            buffers["insert_drift_window"],
            dtype=np.bool_,
        ),
        "insert_settle_window": np.asarray(
            buffers["insert_settle_window"],
            dtype=np.bool_,
        ),
        "balanced_v4b_window": np.asarray(
            buffers["balanced_v4b_window"],
            dtype=np.bool_,
        ),
        "approach_window": np.asarray(buffers["approach_window"], dtype=np.bool_),
        "fixture_wall_window": np.asarray(
            buffers["fixture_wall_window"],
            dtype=np.bool_,
        ),
        "alignment_stable_steps": np.asarray(
            buffers["alignment_stable_steps"],
            dtype=np.int32,
        ),
        "ever_within_insert_xy": np.asarray(
            buffers["ever_within_insert_xy"],
            dtype=np.bool_,
        ),
        "drift_after_alignment": np.asarray(
            buffers["drift_after_alignment"],
            dtype=np.bool_,
        ),
        "descent_should_block": np.asarray(
            buffers["descent_should_block"],
            dtype=np.bool_,
        ),
        "oracle_lift_action": np.asarray(buffers["oracle_lift_action"], dtype=np.bool_),
        "oracle_down_action": np.asarray(buffers["oracle_down_action"], dtype=np.bool_),
        "recovery_branch": np.asarray(buffers["recovery_branch"], dtype=np.bool_),
        "synthetic_recovery_state": np.asarray(
            buffers["synthetic_recovery_state"],
            dtype=np.bool_,
        ),
        "branch_id": np.asarray(buffers["branch_id"], dtype=np.int32),
        "branch_step_id": np.asarray(buffers["branch_step_id"], dtype=np.int32),
        "branch_source_step_id": np.asarray(
            buffers["branch_source_step_id"],
            dtype=np.int32,
        ),
        "policy_norm": np.asarray(buffers["policy_norm"], dtype=np.float32),
        "oracle_norm": np.asarray(buffers["oracle_norm"], dtype=np.float32),
        "correction_norm": np.asarray(buffers["correction_norm"], dtype=np.float32),
        "correction_xy_norm": np.asarray(buffers["correction_xy_norm"], dtype=np.float32),
        "action_cosine": np.asarray(buffers["action_cosine"], dtype=np.float32),
        "opposed_actions": np.asarray(buffers["opposed_actions"], dtype=np.bool_),
        "policy_down_or_oracle_up": np.asarray(buffers["policy_down_or_oracle_up"], dtype=np.bool_),
        "policy_down_oracle_less_down": np.asarray(
            buffers["policy_down_oracle_less_down"],
            dtype=np.bool_,
        ),
        "final_step": np.asarray(buffers["final_step"], dtype=np.int32),
        "steps_to_end": np.asarray(buffers["steps_to_end"], dtype=np.int32),
        "failure_window": np.asarray(buffers["failure_window"], dtype=np.bool_),
        "episode_success": np.asarray(buffers["episode_success"], dtype=np.bool_),
        "episode_collision": np.asarray(buffers["episode_collision"], dtype=np.bool_),
        "episode_timeout": np.asarray(buffers["episode_timeout"], dtype=np.bool_),
        "tier": np.asarray(buffers["tier"]),
        "scenario": np.asarray(buffers["scenario"]),
        "episode_outcome": np.asarray(buffers["episode_outcome"]),
        "recovery_phase": np.asarray(buffers["recovery_phase"]),
    }
    if include_near_hole_crop:
        arrays["near_hole_crops"] = np.asarray(buffers["near_hole_crops"], dtype=np.uint8)
    if include_control_state:
        arrays["control_state"] = np.asarray(buffers["control_state"], dtype=np.float32)
    for key in SCALAR_DIAGNOSTIC_KEYS:
        dtype = np.int32 if key in ("control_action_delay", "ik_iterations") else np.float32
        arrays[key] = np.asarray(buffers[key], dtype=dtype)
    for key in TEXT_DIAGNOSTIC_KEYS:
        arrays[key] = np.asarray(buffers[key])
    for key in VECTOR_DIAGNOSTIC_KEYS:
        arrays[key] = np.asarray(buffers[key], dtype=np.float32)
    return arrays


def array_metadata(arrays: dict[str, np.ndarray]) -> dict[str, dict[str, object]]:
    return {
        key: {"shape": list(value.shape), "dtype": str(value.dtype)}
        for key, value in sorted(arrays.items())
    }


def main() -> None:
    args = parse_args()
    if args.samples <= 0:
        raise ValueError("--samples must be positive.")
    if args.max_samples_per_episode <= 0:
        raise ValueError("--max-samples-per-episode must be positive.")
    if args.failure_window_steps <= 0:
        raise ValueError("--failure-window-steps must be positive.")
    if args.guarded_lift_before_lateral_xy_tolerance <= 0.0:
        raise ValueError("--guarded-lift-before-lateral-xy-tolerance must be positive.")
    if args.guarded_lift_before_lateral_z_margin < 0.0:
        raise ValueError("--guarded-lift-before-lateral-z-margin cannot be negative.")
    if args.contact_recovery_xy_tolerance <= 0.0:
        raise ValueError("--contact-recovery-xy-tolerance must be positive.")
    if args.contact_recovery_z_max <= 0.0:
        raise ValueError("--contact-recovery-z-max must be positive.")
    if args.contact_recovery_lift_height <= 0.0:
        raise ValueError("--contact-recovery-lift-height must be positive.")
    if args.contact_recovery_lift_z_tolerance <= 0.0:
        raise ValueError("--contact-recovery-lift-z-tolerance must be positive.")
    if args.contact_recovery_max_down_action < 0.0:
        raise ValueError("--contact-recovery-max-down-action cannot be negative.")
    if args.timeout_progress_xy_tolerance <= 0.0:
        raise ValueError("--timeout-progress-xy-tolerance must be positive.")
    if args.timeout_progress_z_max <= 0.0:
        raise ValueError("--timeout-progress-z-max must be positive.")
    if args.timeout_progress_max_down_action < 0.0:
        raise ValueError("--timeout-progress-max-down-action cannot be negative.")
    if args.insert_drift_window_xy_max <= 0.0:
        raise ValueError("--insert-drift-window-xy-max must be positive.")
    if args.insert_drift_window_z_max <= 0.0:
        raise ValueError("--insert-drift-window-z-max must be positive.")
    if args.insert_drift_stable_xy <= 0.0:
        raise ValueError("--insert-drift-stable-xy must be positive.")
    if args.insert_drift_stable_xy > args.insert_drift_window_xy_max:
        raise ValueError("--insert-drift-stable-xy cannot exceed --insert-drift-window-xy-max.")
    if args.insert_drift_stable_steps <= 0:
        raise ValueError("--insert-drift-stable-steps must be positive.")
    if args.insert_drift_correction_max_xy_action <= 0.0:
        raise ValueError("--insert-drift-correction-max-xy-action must be positive.")
    if args.insert_drift_correction_max_down_action < 0.0:
        raise ValueError("--insert-drift-correction-max-down-action cannot be negative.")
    if args.insert_settle_window_xy_max <= 0.0:
        raise ValueError("--insert-settle-window-xy-max must be positive.")
    if args.insert_settle_window_z_max <= 0.0:
        raise ValueError("--insert-settle-window-z-max must be positive.")
    if args.insert_settle_insert_xy <= 0.0:
        raise ValueError("--insert-settle-insert-xy must be positive.")
    if args.insert_settle_insert_xy > args.insert_settle_window_xy_max:
        raise ValueError("--insert-settle-insert-xy cannot exceed --insert-settle-window-xy-max.")
    if args.insert_settle_settle_xy < args.insert_settle_insert_xy:
        raise ValueError("--insert-settle-settle-xy must be >= --insert-settle-insert-xy.")
    if args.insert_settle_settle_xy > args.insert_settle_window_xy_max:
        raise ValueError("--insert-settle-settle-xy cannot exceed --insert-settle-window-xy-max.")
    if args.insert_settle_stable_steps <= 0:
        raise ValueError("--insert-settle-stable-steps must be positive.")
    if args.insert_settle_hover_height <= 0.0:
        raise ValueError("--insert-settle-hover-height must be positive.")
    if args.insert_settle_hover_z_tolerance < 0.0:
        raise ValueError("--insert-settle-hover-z-tolerance cannot be negative.")
    if args.insert_settle_lift_z_max < 0.0:
        raise ValueError("--insert-settle-lift-z-max cannot be negative.")
    if args.insert_settle_max_xy_action <= 0.0:
        raise ValueError("--insert-settle-max-xy-action must be positive.")
    if args.insert_settle_max_down_action < 0.0:
        raise ValueError("--insert-settle-max-down-action cannot be negative.")
    if args.balanced_v4b_window_xy <= 0.0:
        raise ValueError("--balanced-v4b-window-xy must be positive.")
    if args.balanced_v4b_window_z_max <= 0.0:
        raise ValueError("--balanced-v4b-window-z-max must be positive.")
    if args.balanced_v4b_stable_xy <= 0.0:
        raise ValueError("--balanced-v4b-stable-xy must be positive.")
    if args.balanced_v4b_stable_xy > args.balanced_v4b_window_xy:
        raise ValueError("--balanced-v4b-stable-xy cannot exceed --balanced-v4b-window-xy.")
    if args.balanced_v4b_stable_steps <= 0:
        raise ValueError("--balanced-v4b-stable-steps must be positive.")
    if args.balanced_v4b_low_z < 0.0:
        raise ValueError("--balanced-v4b-low-z cannot be negative.")
    if args.balanced_v4b_hover_height <= 0.0:
        raise ValueError("--balanced-v4b-hover-height must be positive.")
    if args.balanced_v4b_hover_z_tolerance < 0.0:
        raise ValueError("--balanced-v4b-hover-z-tolerance cannot be negative.")
    if args.balanced_v4b_max_down_action < 0.0:
        raise ValueError("--balanced-v4b-max-down-action cannot be negative.")
    if args.approach_window_xy_min < 0.0:
        raise ValueError("--approach-window-xy-min cannot be negative.")
    if args.approach_window_xy_max <= args.approach_window_xy_min:
        raise ValueError("--approach-window-xy-max must exceed --approach-window-xy-min.")
    if args.approach_window_z_min < 0.0:
        raise ValueError("--approach-window-z-min cannot be negative.")
    if args.approach_window_z_max <= args.approach_window_z_min:
        raise ValueError("--approach-window-z-max must exceed --approach-window-z-min.")
    if args.approach_correction_target_height <= 0.0:
        raise ValueError("--approach-correction-target-height must be positive.")
    if args.approach_correction_max_down_action < 0.0:
        raise ValueError("--approach-correction-max-down-action cannot be negative.")
    if args.fixture_wall_window_xy_min < 0.0:
        raise ValueError("--fixture-wall-window-xy-min cannot be negative.")
    if args.fixture_wall_window_xy_max <= args.fixture_wall_window_xy_min:
        raise ValueError(
            "--fixture-wall-window-xy-max must exceed --fixture-wall-window-xy-min."
        )
    if args.fixture_wall_window_z_min < 0.0:
        raise ValueError("--fixture-wall-window-z-min cannot be negative.")
    if args.fixture_wall_window_z_max <= args.fixture_wall_window_z_min:
        raise ValueError(
            "--fixture-wall-window-z-max must exceed --fixture-wall-window-z-min."
        )
    if args.fixture_wall_correction_target_height <= 0.0:
        raise ValueError("--fixture-wall-correction-target-height must be positive.")
    if args.fixture_wall_correction_max_xy_action <= 0.0:
        raise ValueError("--fixture-wall-correction-max-xy-action must be positive.")
    if args.fixture_wall_correction_max_down_action < 0.0:
        raise ValueError("--fixture-wall-correction-max-down-action cannot be negative.")
    if args.recovery_branch_max_starts_per_episode <= 0:
        raise ValueError("--recovery-branch-max-starts-per-episode must be positive.")
    if args.recovery_branch_max_steps <= 0:
        raise ValueError("--recovery-branch-max-steps must be positive.")
    if args.recovery_branch_stride <= 0:
        raise ValueError("--recovery-branch-stride must be positive.")
    if args.image_frame_stack <= 0:
        raise ValueError("--image-frame-stack must be positive.")

    configs = [(tier, scenario) for tier in tiers_for_args(args) for scenario in scenarios_for_args(args)]
    target_per_config = (
        args.samples_per_config
        if args.samples_per_config is not None
        else int(np.ceil(args.samples / len(configs)))
    )
    oracle_config = make_oracle_config(args)
    buffers = empty_buffers()
    episode_summaries: list[dict[str, Any]] = []
    config_summaries: list[dict[str, Any]] = []
    global_episode_id = 0

    for config_index, (tier, scenario) in enumerate(configs):
        env = make_env(args, scenario, tier)
        model = AGENTS[args.agent].load(args.model, env=env, device=args.device)
        config_samples = 0
        config_episodes = 0
        config_successes = 0
        config_collisions = 0
        config_timeouts = 0
        try:
            while (
                config_samples < target_per_config
                and config_episodes < args.max_episodes_per_config
                and len(buffers["cam_images"]) < args.samples
            ):
                seed = args.seed + config_index * args.max_episodes_per_config + config_episodes
                episode_rows, episode_summary = run_episode(
                    env,
                    model,
                    oracle_config,
                    args=args,
                    tier=tier,
                    scenario=scenario,
                    episode_id=global_episode_id,
                    seed=seed,
                )
                global_episode_id += 1
                config_episodes += 1
                config_successes += int(episode_summary["success"])
                config_collisions += int(episode_summary["collision"])
                config_timeouts += int(episode_summary["timeout"])
                episode_summaries.append(episode_summary)
                selected = select_episode_samples(episode_rows, args)
                kept = append_samples(
                    buffers,
                    selected,
                    min(args.samples - len(buffers["cam_images"]), target_per_config - config_samples),
                )
                config_samples += kept
        finally:
            env.close()

        config_summaries.append(
            {
                "tier": tier.name,
                "scenario": scenario.name,
                "episodes_completed": config_episodes,
                "samples": config_samples,
                "success_rate": config_successes / max(config_episodes, 1),
                "collision_rate": config_collisions / max(config_episodes, 1),
                "timeout_rate": config_timeouts / max(config_episodes, 1),
            }
        )
        print(
            "{tier}/{scenario}: samples={samples} episodes={episodes} "
            "success={success:.3f} collision={collision:.3f}".format(
                tier=tier.name,
                scenario=scenario.name,
                samples=config_samples,
                episodes=config_episodes,
                success=config_summaries[-1]["success_rate"],
                collision=config_summaries[-1]["collision_rate"],
            )
        )

    arrays = build_arrays(
        buffers,
        args.include_near_hole_crop,
        args.include_control_state,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.compressed:
        np.savez_compressed(args.output, **arrays)
    else:
        np.savez(args.output, **arrays)

    metadata = {
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "samples": int(arrays["actions"].shape[0]),
        "model": str(args.model),
        "model_path": str(args.model_path) if args.model_path is not None else "default",
        "scenario_preset": args.scenario_preset,
        "tier_preset": args.tier_preset,
        "geometry_profile": args.geometry_profile,
        "geometry_square_peg_half_size_range": list(args.geometry_square_peg_half_size_range),
        "geometry_mixed_square_probability": args.geometry_mixed_square_probability,
        "initialization_mode": args.initialization_mode,
        "initial_tip_z_above_range": list(args.initial_tip_z_above_range),
        "initial_tip_xy_offset_range": list(args.initial_tip_xy_offset_range),
        "initial_tip_xy_angle_range_deg": list(args.initial_tip_xy_angle_range_deg),
        "initial_ik_max_attempts": args.initial_ik_max_attempts,
        "ik_control_mode": args.ik_control_mode,
        "ik_orientation_weight": args.ik_orientation_weight,
        "ik_posture_weight": args.ik_posture_weight,
        "ik_step_limit": args.ik_step_limit,
        "ik_max_iterations": args.ik_max_iterations,
        "selection": args.selection,
        "episode_outcome_filter": args.episode_outcome_filter,
        "keep_success_episodes": args.keep_success_episodes,
        "failure_window_steps": args.failure_window_steps,
        "near_hole_xy": args.near_hole_xy,
        "near_hole_z": args.near_hole_z,
        "min_correction_norm": args.min_correction_norm,
        "max_samples_per_episode": args.max_samples_per_episode,
        "samples_per_config": target_per_config,
        "max_episodes_per_config": args.max_episodes_per_config,
        "episodes_completed": len(episode_summaries),
        "config_summaries": config_summaries,
        "image_width": args.image_width,
        "image_height": args.image_height,
        "include_near_hole_crop": args.include_near_hole_crop,
        "include_control_state": args.include_control_state,
        "image_frame_stack": args.image_frame_stack,
        "near_hole_crop_size": args.near_hole_crop_size,
        "near_hole_crop_offset": list(args.near_hole_crop_offset),
        "wrist_camera_pos_offset": list(args.wrist_camera_pos_offset),
        "wrist_camera_rot_offset_deg": list(args.wrist_camera_rot_offset_deg),
        "wrist_camera_fovy": args.wrist_camera_fovy,
        "success_xy_tolerance": args.success_xy_tolerance,
        "success_z_tolerance": args.success_z_tolerance,
        "approach_xy_tolerance": args.approach_xy_tolerance,
        "oracle_mode": args.oracle_mode,
        "oracle_action_gain": args.oracle_action_gain,
        "guarded_align_xy_tolerance": args.guarded_align_xy_tolerance,
        "guarded_insert_xy_tolerance": args.guarded_insert_xy_tolerance,
        "guarded_retract_xy_tolerance": args.guarded_retract_xy_tolerance,
        "guarded_preinsert_height": args.guarded_preinsert_height,
        "guarded_max_xy_action": args.guarded_max_xy_action,
        "guarded_max_down_action": args.guarded_max_down_action,
        "guarded_max_up_action": args.guarded_max_up_action,
        "guarded_prediction_steps": args.guarded_prediction_steps,
        "guarded_lift_before_lateral": args.guarded_lift_before_lateral,
        "guarded_lift_before_lateral_xy_tolerance": (
            args.guarded_lift_before_lateral_xy_tolerance
        ),
        "guarded_lift_before_lateral_z_margin": args.guarded_lift_before_lateral_z_margin,
        "contact_recovery_xy_tolerance": args.contact_recovery_xy_tolerance,
        "contact_recovery_z_max": args.contact_recovery_z_max,
        "contact_recovery_lift_height": args.contact_recovery_lift_height,
        "contact_recovery_lift_z_tolerance": args.contact_recovery_lift_z_tolerance,
        "contact_recovery_max_down_action": args.contact_recovery_max_down_action,
        "timeout_progress_xy_tolerance": args.timeout_progress_xy_tolerance,
        "timeout_progress_z_max": args.timeout_progress_z_max,
        "timeout_progress_max_down_action": args.timeout_progress_max_down_action,
        "insert_drift_correction_labels": args.insert_drift_correction_labels,
        "insert_drift_window_xy_max": args.insert_drift_window_xy_max,
        "insert_drift_window_z_max": args.insert_drift_window_z_max,
        "insert_drift_stable_xy": args.insert_drift_stable_xy,
        "insert_drift_stable_steps": args.insert_drift_stable_steps,
        "insert_drift_correction_max_xy_action": args.insert_drift_correction_max_xy_action,
        "insert_drift_correction_max_down_action": args.insert_drift_correction_max_down_action,
        "insert_settle_correction_labels": args.insert_settle_correction_labels,
        "insert_settle_window_xy_max": args.insert_settle_window_xy_max,
        "insert_settle_window_z_max": args.insert_settle_window_z_max,
        "insert_settle_insert_xy": args.insert_settle_insert_xy,
        "insert_settle_settle_xy": args.insert_settle_settle_xy,
        "insert_settle_stable_steps": args.insert_settle_stable_steps,
        "insert_settle_hover_height": args.insert_settle_hover_height,
        "insert_settle_hover_z_tolerance": args.insert_settle_hover_z_tolerance,
        "insert_settle_lift_z_max": args.insert_settle_lift_z_max,
        "insert_settle_max_xy_action": args.insert_settle_max_xy_action,
        "insert_settle_max_down_action": args.insert_settle_max_down_action,
        "balanced_v4b_labels": args.balanced_v4b_labels,
        "balanced_v4b_window_xy": args.balanced_v4b_window_xy,
        "balanced_v4b_window_z_max": args.balanced_v4b_window_z_max,
        "balanced_v4b_stable_xy": args.balanced_v4b_stable_xy,
        "balanced_v4b_stable_steps": args.balanced_v4b_stable_steps,
        "balanced_v4b_low_z": args.balanced_v4b_low_z,
        "balanced_v4b_hover_height": args.balanced_v4b_hover_height,
        "balanced_v4b_hover_z_tolerance": args.balanced_v4b_hover_z_tolerance,
        "balanced_v4b_max_down_action": args.balanced_v4b_max_down_action,
        "approach_correction_labels": args.approach_correction_labels,
        "approach_window_xy_min": args.approach_window_xy_min,
        "approach_window_xy_max": args.approach_window_xy_max,
        "approach_window_z_min": args.approach_window_z_min,
        "approach_window_z_max": args.approach_window_z_max,
        "approach_correction_target_height": args.approach_correction_target_height,
        "approach_correction_max_down_action": args.approach_correction_max_down_action,
        "fixture_wall_correction_labels": args.fixture_wall_correction_labels,
        "fixture_wall_window_xy_min": args.fixture_wall_window_xy_min,
        "fixture_wall_window_xy_max": args.fixture_wall_window_xy_max,
        "fixture_wall_window_z_min": args.fixture_wall_window_z_min,
        "fixture_wall_window_z_max": args.fixture_wall_window_z_max,
        "fixture_wall_correction_target_height": args.fixture_wall_correction_target_height,
        "fixture_wall_correction_max_xy_action": args.fixture_wall_correction_max_xy_action,
        "fixture_wall_correction_max_down_action": args.fixture_wall_correction_max_down_action,
        "recovery_branch_rollout": args.recovery_branch_rollout,
        "recovery_branch_from_near_hole": args.recovery_branch_from_near_hole,
        "recovery_branch_max_starts_per_episode": args.recovery_branch_max_starts_per_episode,
        "recovery_branch_max_steps": args.recovery_branch_max_steps,
        "recovery_branch_stride": args.recovery_branch_stride,
        "recovery_branch_stop_on_success": args.recovery_branch_stop_on_success,
        "recovery_branch_clear_control_history": args.recovery_branch_clear_control_history,
        "recovery_branch_synthetic_stages": args.recovery_branch_synthetic_stages,
        "array_metadata": array_metadata(arrays),
        "diagnostics": {
            "correction_norm": summarize_float_array(arrays["correction_norm"]),
            "action_cosine": summarize_float_array(arrays["action_cosine"]),
            "hole_clearance": summarize_float_array(arrays["hole_clearance"]),
            "geometry_name": summarize_text_array(arrays["geometry_name"]),
            "peg_shape": summarize_text_array(arrays["peg_shape"]),
            "control_action_delay": summarize_float_array(
                arrays["control_action_delay"].astype(np.float32)
            ),
            "control_action_filter_alpha": summarize_float_array(
                arrays["control_action_filter_alpha"]
            ),
            "near_hole_rate": float(np.mean(arrays["near_hole"])) if arrays["near_hole"].size else 0.0,
            "contact_recovery_window_rate": float(np.mean(arrays["contact_recovery_window"]))
            if arrays["contact_recovery_window"].size
            else 0.0,
            "timeout_progress_window_rate": float(np.mean(arrays["timeout_progress_window"]))
            if arrays["timeout_progress_window"].size
            else 0.0,
            "insert_drift_window_rate": float(np.mean(arrays["insert_drift_window"]))
            if arrays["insert_drift_window"].size
            else 0.0,
            "insert_settle_window_rate": float(np.mean(arrays["insert_settle_window"]))
            if arrays["insert_settle_window"].size
            else 0.0,
            "balanced_v4b_window_rate": float(np.mean(arrays["balanced_v4b_window"]))
            if arrays["balanced_v4b_window"].size
            else 0.0,
            "approach_window_rate": float(np.mean(arrays["approach_window"]))
            if arrays["approach_window"].size
            else 0.0,
            "fixture_wall_window_rate": float(np.mean(arrays["fixture_wall_window"]))
            if arrays["fixture_wall_window"].size
            else 0.0,
            "ever_within_insert_xy_rate": float(np.mean(arrays["ever_within_insert_xy"]))
            if arrays["ever_within_insert_xy"].size
            else 0.0,
            "drift_after_alignment_rate": float(np.mean(arrays["drift_after_alignment"]))
            if arrays["drift_after_alignment"].size
            else 0.0,
            "descent_should_block_rate": float(np.mean(arrays["descent_should_block"]))
            if arrays["descent_should_block"].size
            else 0.0,
            "alignment_stable_steps": summarize_float_array(
                arrays["alignment_stable_steps"].astype(np.float32)
            ),
            "oracle_lift_action_rate": float(np.mean(arrays["oracle_lift_action"]))
            if arrays["oracle_lift_action"].size
            else 0.0,
            "recovery_branch_rate": float(np.mean(arrays["recovery_branch"]))
            if arrays["recovery_branch"].size
            else 0.0,
            "synthetic_recovery_state_rate": float(np.mean(arrays["synthetic_recovery_state"]))
            if arrays["synthetic_recovery_state"].size
            else 0.0,
            "opposed_action_rate": float(np.mean(arrays["opposed_actions"]))
            if arrays["opposed_actions"].size
            else 0.0,
            "policy_down_or_oracle_up_rate": float(
                np.mean(arrays["policy_down_or_oracle_up"])
            )
            if arrays["policy_down_or_oracle_up"].size
            else 0.0,
        },
    }
    metadata_path = args.output.with_suffix(args.output.suffix + ".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved correction dataset to {args.output}")
    print(f"saved metadata to {metadata_path}")
    print(f"samples={arrays['actions'].shape[0]} episodes_completed={len(episode_summaries)}")


if __name__ == "__main__":
    main()
