from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import torch
from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco.approach_adapter import ApproachAdapterPolicy
from peg_in_hole_mujoco.final_insert_adapter import FinalInsertAdapterPolicy
from peg_in_hole_mujoco import (
    GuardedPolicyConfig,
    GuardedPolicyController,
    GuardedPolicyStep,
    MujocoGuardStateProvider,
    OracleControllerConfig,
    PegInHoleMujocoEnv,
    oracle_action_from_state,
)
from peg_in_hole_mujoco.sim_config import parse_args_with_config
from peg_in_hole_mujoco.visual_yaw_runtime import (
    PROFILE_PERIOD_DEG,
    VisualYawPrediction,
    VisualYawRuntime,
)


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


SQUARE_POSE_YAW_ALIGN_PHASES = frozenset(
    (
        "square_fast_settle",
        "square_fast_settle_pre_pop_guard_hold",
        "square_fast_settle_clearance_hold",
        "square_fast_settle_contact_soft_hold",
        "square_fast_settle_contact_soft_hold_release_continue",
        "square_fast_settle_contact_soft_hold_release_pop_hold",
        "square_low_z_relief_lift",
        "square_low_z_relief_recenter",
        "square_high_z_descend",
        "square_high_z_descend_low_z_hold",
        "square_margin_yaw_settle_lift",
        "square_margin_yaw_settle_recenter",
        "square_tilt_reinsert_lift",
        "square_tilt_reinsert_recenter",
        "square_contact_pop_hold",
        "square_no_contact_pop_hold",
        "square_contact_brake_preemptive_hold",
        "square_contact_brake_lift",
        "square_contact_brake_recenter",
    )
)


HARD_BUCKET_SCENARIO = Scenario(
    "hard_full_light_bucket",
    "full_light_geometry",
    control_action_scale_range=(0.8, 1.1),
    control_action_noise_std_range=(0.0, 0.00025),
    control_action_delay_range=(2, 2),
    control_action_filter_alpha_range=(0.55, 0.70),
)


@dataclass(frozen=True)
class VisualYawAlignResult:
    active: bool = False
    applied: bool = False
    blocked_down: bool = False
    aligned_descent: bool = False
    aligned_descent_stable_steps: int = 0
    low_z_late_finish_descent: bool = False
    target_hold: bool = False
    low_visibility_brake: bool = False
    large_xy_low_z_brake: bool = False
    descent_abort_active: bool = False
    descent_abort_triggered: bool = False
    descent_abort_phase: str = "inactive"
    descent_abort_attempts: int = 0
    reacquire_active: bool = False
    reacquire_triggered: bool = False
    reacquire_phase: str = "inactive"
    reacquire_attempts: int = 0
    wrong_basin_hold_active: bool = False
    wrong_basin_hold_triggered: bool = False
    wrong_basin_hold_steps_remaining: int = 0
    wrong_basin_hold_attempts: int = 0
    low_z_lateral_pop_recovery_active: bool = False
    low_z_lateral_pop_recovery_triggered: bool = False
    low_z_lateral_pop_recovery_phase: str = "inactive"
    low_z_lateral_pop_recovery_attempts: int = 0
    low_z_lateral_pop_recovery_steps_remaining: int = 0
    reason: str = "disabled"
    prediction: VisualYawPrediction | None = None
    correction_deg: float = 0.0


def make_hard_bucket_scenario(args: argparse.Namespace) -> Scenario:
    overrides: dict[str, tuple[float, float] | tuple[int, int]] = {}
    if args.hard_control_scale_range is not None:
        overrides["control_action_scale_range"] = tuple(args.hard_control_scale_range)
    if args.hard_control_noise_std_range is not None:
        overrides["control_action_noise_std_range"] = tuple(args.hard_control_noise_std_range)
    if args.hard_control_delay_range is not None:
        overrides["control_action_delay_range"] = tuple(args.hard_control_delay_range)
    if args.hard_control_filter_alpha_range is not None:
        overrides["control_action_filter_alpha_range"] = tuple(args.hard_control_filter_alpha_range)
    if not overrides:
        return HARD_BUCKET_SCENARIO
    return replace(HARD_BUCKET_SCENARIO, **overrides)


STEP_TRACE_FIELDNAMES = [
    "scenario",
    "level",
    "control_mode",
    "image_ablation",
    "image_ablation_target",
    "control_state_ablation",
    "episode",
    "seed",
    "episode_outcome",
    "step",
    "pre_step_count",
    "post_step_count",
    "terminated",
    "truncated",
    "success",
    "collision",
    "collision_contact_count",
    "collision_contact_pairs",
    "peg_hole_contact_count",
    "peg_hole_contact_pairs",
    "peg_hole_contact_wall_count",
    "peg_hole_contact_plate_count",
    "peg_hole_contact_has_wall",
    "peg_hole_contact_has_plate",
    "peg_hole_contact_hole_plate",
    "peg_hole_contact_hole_north",
    "peg_hole_contact_hole_south",
    "peg_hole_contact_hole_east",
    "peg_hole_contact_hole_west",
    "peg_hole_contact_min_dist",
    "peg_hole_contact_max_dist",
    "timeout",
    "pre_dist_xy",
    "pre_dist_z",
    "pre_z_above_target",
    "pre_peg_tip_x",
    "pre_peg_tip_y",
    "pre_peg_tip_z",
    "pre_target_x",
    "pre_target_y",
    "pre_target_z",
    "post_dist_xy",
    "post_dist_z",
    "post_z_above_target",
    "post_peg_tip_x",
    "post_peg_tip_y",
    "post_peg_tip_z",
    "post_target_x",
    "post_target_y",
    "post_target_z",
    "dist_xy_delta",
    "dist_z_delta",
    "tip_z_delta",
    "guard_enabled",
    "guard_active",
    "guarded",
    "guard_should_activate",
    "guard_can_activate",
    "guard_activated",
    "guard_down_blocked",
    "guard_steps_since_reset",
    "guard_dist_xy",
    "guard_z_above_target",
    "guard_retry_active",
    "guard_retry_triggered",
    "guard_retry_count",
    "guard_retry_stall_steps",
    "guard_retry_active_steps",
    "guard_insert_latched",
    "guard_insert_latch_activated",
    "guard_insert_latch_released",
    "guard_insert_latch_steps",
    "guard_insert_latch_descent_allowed",
    "guard_hover_active",
    "guard_hover_stable_steps",
    "guard_hover_descent_allowed",
    "guard_hover_descent_latched",
    "guard_hover_down_blocked",
    "guard_near_action_limited",
    "guard_fixture_clearance_active",
    "guard_fixture_clearance_triggered",
    "guard_fixture_clearance_released",
    "guard_fixture_clearance_phase",
    "guard_fixture_clearance_steps",
    "guard_fixture_clearance_realign_steps",
    "guard_preinsert_recenter_active",
    "guard_preinsert_recenter_triggered",
    "guard_preinsert_recenter_released",
    "guard_preinsert_recenter_steps",
    "guard_preinsert_recenter_stable_steps",
    "guard_preinsert_recenter_down_blocked",
    "guard_approach_recenter_active",
    "guard_approach_recenter_triggered",
    "guard_approach_recenter_released",
    "guard_approach_recenter_steps",
    "guard_approach_recenter_stable_steps",
    "guard_approach_recenter_down_blocked",
    "guard_early_approach_assist_active",
    "guard_early_approach_assist_triggered",
    "guard_early_approach_assist_released",
    "guard_early_approach_assist_steps",
    "guard_early_approach_assist_down_blocked",
    "guard_stateful_recovery_active",
    "guard_stateful_recovery_triggered",
    "guard_stateful_recovery_released",
    "guard_stateful_recovery_exhausted",
    "guard_stateful_recovery_phase",
    "guard_stateful_recovery_phase_steps",
    "guard_stateful_recovery_stall_steps",
    "guard_stateful_recovery_stable_steps",
    "guard_stateful_recovery_attempts",
    "guard_stateful_recovery_down_blocked",
    "guard_final_servo_active",
    "guard_final_servo_triggered",
    "guard_final_servo_rearmed",
    "guard_final_servo_recovery_triggered",
    "guard_final_servo_exhausted",
    "guard_final_servo_phase",
    "guard_final_servo_phase_transition_reason",
    "guard_final_servo_phase_steps",
    "guard_final_servo_stable_steps",
    "guard_final_servo_stall_steps",
    "guard_final_servo_low_recenter_stall_steps",
    "guard_final_servo_low_recenter_best_dist_xy",
    "guard_final_servo_retry_count",
    "guard_final_servo_rearm_attempts",
    "guard_final_servo_rearm_cooldown_steps",
    "guard_final_servo_rearm_stable_steps",
    "guard_final_servo_descent_allowed",
    "guard_final_servo_down_blocked",
    "guard_final_servo_square_recovery_active",
    "guard_final_servo_square_recovery_triggered",
    "guard_final_servo_square_recovery_tilt_steps",
    "guard_final_servo_square_recovery_escape_active",
    "guard_final_servo_square_recovery_escape_triggered",
    "guard_final_servo_square_recovery_escape_early_contact_steps",
    "guard_final_servo_square_recovery_escape_early_risk_steps",
    "guard_final_servo_square_recovery_escape_direct_fast_settle_active",
    "guard_final_servo_square_recovery_escape_late_recenter_descend_active",
    "guard_final_servo_square_contact_brake_active",
    "guard_final_servo_square_contact_brake_triggered",
    "guard_final_servo_square_contact_brake_wall_steps",
    "guard_final_servo_square_contact_brake_attempts",
    "guard_final_servo_square_contact_brake_preemptive_hold_active",
    "guard_final_servo_square_contact_brake_preemptive_hold_triggered",
    "guard_final_servo_square_contact_brake_preemptive_hold_wall_steps",
    "guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy",
    "guard_final_servo_square_fast_settle_clearance_hold_attempts",
    "guard_final_servo_square_fast_settle_clean_steps",
    "guard_final_servo_square_fast_settle_low_z_relief_attempts",
    "guard_final_servo_square_fast_settle_low_z_stall_relief_attempts",
    "guard_final_servo_square_fast_settle_contact_soft_hold_active",
    "guard_final_servo_square_fast_settle_contact_soft_hold_attempts",
    "guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_active",
    "guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_attempts",
    "guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_active",
    "guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_attempts",
    "guard_final_servo_square_fast_settle_contact_pop_hold_active",
    "guard_final_servo_square_fast_settle_contact_pop_hold_attempts",
    "guard_final_servo_square_fast_settle_no_contact_pop_hold_active",
    "guard_final_servo_square_fast_settle_no_contact_pop_hold_attempts",
    "guard_final_servo_square_fast_settle_pre_pop_guard_active",
    "guard_final_servo_square_fast_settle_pre_pop_guard_attempts",
    "guard_final_servo_square_fast_settle_pre_pop_limit_active",
    "guard_final_servo_square_fast_settle_severe_pop_reapproach_active",
    "guard_final_servo_square_fast_settle_severe_pop_reapproach_attempts",
    "guard_final_servo_square_high_z_descend_low_z_hold_active",
    "guard_final_servo_square_high_z_descend_low_z_hold_attempts",
    "guard_final_servo_contact_unjam_wall_steps",
    "guard_final_servo_contact_reinsert_orient_tip_lock_active",
    "guard_final_servo_contact_reinsert_orient_tip_lock_drift_xy",
    "guard_final_servo_near_miss_steps",
    "approach_adapter_active",
    "approach_adapter_residual_x",
    "approach_adapter_residual_y",
    "approach_adapter_residual_z",
    "final_insert_adapter_active",
    "final_insert_adapter_reason",
    "final_insert_adapter_raw_action_x",
    "final_insert_adapter_raw_action_y",
    "final_insert_adapter_raw_action_z",
    "final_insert_adapter_action_x",
    "final_insert_adapter_action_y",
    "final_insert_adapter_action_z",
    "final_insert_adapter_lift_pulse_active",
    "final_insert_adapter_lift_pulse_steps_remaining",
    "final_insert_macro_recovery_active",
    "final_insert_macro_recovery_triggered",
    "final_insert_macro_recovery_phase",
    "final_insert_macro_recovery_reason",
    "final_insert_macro_recovery_attempt",
    "final_insert_macro_recovery_steps_remaining",
    "final_insert_macro_recovery_action_x",
    "final_insert_macro_recovery_action_y",
    "final_insert_macro_recovery_action_z",
    "base_policy_action_x",
    "base_policy_action_y",
    "base_policy_action_z",
    "policy_action_x",
    "policy_action_y",
    "policy_action_z",
    "guarded_action_x",
    "guarded_action_y",
    "guarded_action_z",
    "final_action_x",
    "final_action_y",
    "final_action_z",
    "commanded_action_x",
    "commanded_action_y",
    "commanded_action_z",
    "applied_action_x",
    "applied_action_y",
    "applied_action_z",
    "action_tracking_error",
    "action_tip_delta_error_x",
    "action_tip_delta_error_y",
    "action_tip_delta_error_z",
    "ik_control_mode",
    "ik_orientation_weight",
    "ik_target_error",
    "ik_orientation_error",
    "pose_ik_target_raw_yaw_deg",
    "pose_ik_target_square_yaw_error_deg",
    "guard_square_pose_yaw_align_active",
    "guard_visual_yaw_align_active",
    "guard_visual_yaw_align_applied",
    "guard_visual_yaw_align_blocked_down",
    "guard_visual_yaw_align_aligned_descent",
    "guard_visual_yaw_align_aligned_descent_stable_steps",
    "guard_visual_yaw_align_low_z_late_finish_descent",
    "guard_visual_yaw_align_target_hold",
    "guard_visual_yaw_align_low_visibility_brake",
    "guard_visual_yaw_align_large_xy_low_z_brake",
    "guard_visual_yaw_align_descent_abort_active",
    "guard_visual_yaw_align_descent_abort_triggered",
    "guard_visual_yaw_align_descent_abort_phase",
    "guard_visual_yaw_align_descent_abort_attempts",
    "guard_visual_yaw_align_reacquire_active",
    "guard_visual_yaw_align_reacquire_triggered",
    "guard_visual_yaw_align_reacquire_phase",
    "guard_visual_yaw_align_reacquire_attempts",
    "guard_visual_yaw_align_wrong_basin_hold_active",
    "guard_visual_yaw_align_wrong_basin_hold_triggered",
    "guard_visual_yaw_align_wrong_basin_hold_steps_remaining",
    "guard_visual_yaw_align_wrong_basin_hold_attempts",
    "guard_visual_yaw_align_low_z_lateral_pop_recovery_active",
    "guard_visual_yaw_align_low_z_lateral_pop_recovery_triggered",
    "guard_visual_yaw_align_low_z_lateral_pop_recovery_phase",
    "guard_visual_yaw_align_low_z_lateral_pop_recovery_attempts",
    "guard_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining",
    "guard_visual_yaw_align_reason",
    "guard_visual_yaw_align_profile",
    "guard_visual_yaw_align_pred_signed_error_deg",
    "guard_visual_yaw_align_pred_abs_error_deg",
    "guard_visual_yaw_align_correction_deg",
    "guard_visual_yaw_align_raw_norm",
    "guard_visual_yaw_align_cam_std",
    "guard_visual_yaw_align_crop_std",
    "ik_iterations",
    "peg_tilt_angle_deg",
    "joint_limit_min_normalized_margin",
    "joint_damping_multiplier",
    "actuator_kp_multiplier",
    "control_action_scale_multiplier",
    "control_action_noise_std",
    "control_action_delay",
    "control_action_filter_alpha",
    "geometry_profile",
    "geometry_name",
    "peg_shape",
    "hole_shape",
    "hole_half_size",
    "peg_radius",
    "hole_clearance",
    "success_shape_yaw_required",
    "success_shape_yaw_ok",
    "success_shape_yaw_error_deg",
    "success_shape_yaw_tolerance_deg",
    "shape_yaw_clearance",
    "shape_yaw_signed_error_deg",
    "shape_yaw_error_deg",
    "square_peg_raw_yaw_deg",
    "square_peg_yaw_error_deg",
    "square_peg_topdown_half_width_x",
    "square_peg_topdown_half_width_y",
    "square_peg_topdown_max_half_width",
    "square_peg_topdown_clearance_margin",
    "square_peg_tilt_lateral_extent_x",
    "square_peg_tilt_lateral_extent_y",
    "square_peg_tilt_lateral_extent_max",
    "square_peg_tilted_half_width_x",
    "square_peg_tilted_half_width_y",
    "square_peg_tilted_max_half_width",
    "square_peg_tilted_clearance_margin",
]


def build_parser(
    description: str = "Evaluate a learned policy with deployment-time guarded insertion.",
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=description
    )
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=90_000)
    parser.add_argument("--output-csv", type=Path, default=Path("results/eval_guarded_policy_latest.csv"))
    parser.add_argument("--output-md", type=Path, default=Path("results/eval_guarded_policy_latest.md"))
    parser.add_argument("--episode-output-csv", type=Path, default=None)
    parser.add_argument("--step-output-csv", type=Path, default=None)
    parser.add_argument(
        "--step-trace-outcome-filter",
        choices=["any", "success", "collision", "timeout", "failure"],
        default="timeout",
        help="Select which episode outcomes contribute step-level traces.",
    )
    parser.add_argument("--include-hard-bucket", action="store_true")
    parser.add_argument("--hard-bucket-only", action="store_true")
    parser.add_argument(
        "--control-mode",
        choices=["guarded", "policy", "guard_only"],
        default="guarded",
        help="Use the learned policy with guard, the learned policy only, or the privileged guard/oracle only.",
    )
    parser.add_argument(
        "--image-ablation",
        choices=["normal", "black", "noise", "shuffle"],
        default="normal",
        help="Corrupt image observations before policy inference for visual contribution audits.",
    )
    parser.add_argument(
        "--image-ablation-target",
        choices=["all", "cam_image", "near_hole_crop"],
        default="all",
        help="Select which image observation key is affected by --image-ablation.",
    )
    parser.add_argument(
        "--control-state-ablation",
        choices=["normal", "zero", "noise", "shuffle"],
        default="normal",
        help="Corrupt only the control_state observation key before policy inference.",
    )
    parser.add_argument("--approach-adapter", type=Path, default=None)
    parser.add_argument("--approach-adapter-enabled", action="store_true")
    parser.add_argument("--approach-adapter-trigger-xy", type=float, default=0.100)
    parser.add_argument("--approach-adapter-release-xy", type=float, default=0.060)
    parser.add_argument("--approach-adapter-min-z", type=float, default=0.120)
    parser.add_argument("--approach-adapter-max-z", type=float, default=0.270)
    parser.add_argument(
        "--approach-adapter-latch-enabled",
        action="store_true",
        help=(
            "Once the approach adapter activates, keep it active until release_xy, "
            "latched_min_z, or max_steps is reached."
        ),
    )
    parser.add_argument(
        "--approach-adapter-latched-min-z",
        type=float,
        default=None,
        help="Lower Z bound for an already-active latched adapter. Defaults to min-z.",
    )
    parser.add_argument(
        "--approach-adapter-max-steps",
        type=int,
        default=0,
        help="Maximum consecutive latched adapter steps. 0 disables the step cap.",
    )
    parser.add_argument(
        "--approach-adapter-episode-max-steps",
        type=int,
        default=0,
        help="Maximum total adapter-active steps per episode. 0 disables the episode budget.",
    )
    parser.add_argument("--approach-adapter-max-xy-residual", type=float, default=0.003)
    parser.add_argument("--approach-adapter-max-z-residual", type=float, default=0.0)
    parser.add_argument("--approach-adapter-scale", type=float, default=1.0)
    parser.add_argument(
        "--approach-adapter-mode",
        choices=["residual", "override_xy"],
        default="residual",
        help="Add adapter output as a residual or let it own XY in the gated region.",
    )
    parser.add_argument(
        "--approach-adapter-apply-z",
        action="store_true",
        help="Also apply the adapter Z residual. By default only XY residuals are used.",
    )
    parser.add_argument("--final-insert-adapter", type=Path, default=None)
    parser.add_argument("--final-insert-adapter-enabled", action="store_true")
    parser.add_argument(
        "--final-insert-adapter-mode",
        choices=["override", "override_xy", "residual"],
        default="override",
        help="Use the adapter as the full final action, XY override on guarded action, or residual on guarded action.",
    )
    parser.add_argument(
        "--final-insert-adapter-phase",
        default="square_fast_settle",
        help="Guard final-servo phase where the final-insert adapter may run. Use 'any' to disable phase filtering.",
    )
    parser.add_argument(
        "--final-insert-adapter-geometry-name",
        default="square_square",
        help="Geometry name where the final-insert adapter may run. Use 'any' to disable geometry filtering.",
    )
    parser.add_argument("--final-insert-adapter-max-xy", type=float, default=0.008)
    parser.add_argument("--final-insert-adapter-min-z", type=float, default=0.020)
    parser.add_argument("--final-insert-adapter-max-z", type=float, default=0.055)
    parser.add_argument("--final-insert-adapter-min-phase-steps", type=int, default=0)
    parser.add_argument("--final-insert-adapter-min-stall-steps", type=int, default=0)
    parser.add_argument("--final-insert-adapter-square-risk-gate-enabled", action="store_true")
    parser.add_argument("--final-insert-adapter-square-risk-min-stall-steps", type=int, default=0)
    parser.add_argument("--final-insert-adapter-square-risk-xy-min", type=float, default=0.0)
    parser.add_argument("--final-insert-adapter-square-risk-topdown-margin-max", type=float, default=0.0)
    parser.add_argument("--final-insert-adapter-square-risk-tilted-margin-max", type=float, default=0.0)
    parser.add_argument("--final-insert-adapter-square-risk-wall-topdown-margin-max", type=float, default=0.0)
    parser.add_argument("--final-insert-adapter-square-risk-wall-tilted-margin-max", type=float, default=0.0)
    parser.add_argument(
        "--final-insert-adapter-wall-contact-required",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require current peg-hole wall contact before applying the adapter.",
    )
    parser.add_argument("--final-insert-adapter-max-xy-action", type=float, default=0.002)
    parser.add_argument("--final-insert-adapter-max-up-action", type=float, default=0.0025)
    parser.add_argument("--final-insert-adapter-max-down-action", type=float, default=0.0008)
    parser.add_argument(
        "--final-insert-adapter-max-consecutive-steps",
        type=int,
        default=0,
        help="Default 0 keeps the adapter unlimited. Positive values bound one continuous takeover burst.",
    )
    parser.add_argument(
        "--final-insert-adapter-cooldown-steps",
        type=int,
        default=0,
        help="Steps to keep the adapter inactive after a bounded takeover burst.",
    )
    parser.add_argument(
        "--final-insert-adapter-handoff-on-down-action",
        action="store_true",
        help="Treat a predicted downward final-insert adapter action as a handoff signal and keep the guarded action.",
    )
    parser.add_argument(
        "--final-insert-adapter-handoff-on-aligned-no-contact",
        action="store_true",
        help="Keep the guarded action when the tip is aligned, high, and not touching a hole wall.",
    )
    parser.add_argument("--final-insert-adapter-handoff-xy", type=float, default=0.002)
    parser.add_argument("--final-insert-adapter-handoff-min-z", type=float, default=0.025)
    parser.add_argument("--final-insert-adapter-handoff-max-z", type=float, default=0.060)
    parser.add_argument(
        "--final-insert-adapter-handoff-z-action-threshold",
        type=float,
        default=-0.0001,
        help="Z-action threshold for handoff-on-down-action. Predictions at or below this value hand control back.",
    )
    parser.add_argument("--final-insert-adapter-lift-pulse-enabled", action="store_true")
    parser.add_argument("--final-insert-adapter-lift-pulse-active-steps", type=int, default=80)
    parser.add_argument("--final-insert-adapter-lift-pulse-stall-steps", type=int, default=80)
    parser.add_argument("--final-insert-adapter-lift-pulse-steps", type=int, default=10)
    parser.add_argument("--final-insert-adapter-lift-pulse-period-steps", type=int, default=120)
    parser.add_argument("--final-insert-adapter-lift-pulse-z-action", type=float, default=0.0015)
    parser.add_argument(
        "--final-insert-adapter-progress-window-steps",
        type=int,
        default=20,
        help="Pre-step history window used to compute adapter progress features.",
    )
    parser.add_argument("--final-insert-macro-recovery-enabled", action="store_true")
    parser.add_argument(
        "--final-insert-macro-recovery-phase",
        default="square_fast_settle",
        help="Guard final-servo phase where the macro recovery may trigger. Use 'any' to disable phase filtering.",
    )
    parser.add_argument(
        "--final-insert-macro-recovery-geometry-name",
        default="square_square",
        help="Geometry name where the macro recovery may trigger. Use 'any' to disable geometry filtering.",
    )
    parser.add_argument("--final-insert-macro-recovery-min-stall-steps", type=int, default=80)
    parser.add_argument("--final-insert-macro-recovery-min-active-steps", type=int, default=80)
    parser.add_argument("--final-insert-macro-recovery-min-z", type=float, default=0.025)
    parser.add_argument("--final-insert-macro-recovery-max-z", type=float, default=0.055)
    parser.add_argument("--final-insert-macro-recovery-max-xy", type=float, default=0.006)
    parser.add_argument(
        "--final-insert-macro-recovery-wall-contact-required",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require peg-hole wall contact before starting the macro recovery.",
    )
    parser.add_argument("--final-insert-macro-recovery-lift-steps", type=int, default=20)
    parser.add_argument("--final-insert-macro-recovery-align-steps", type=int, default=80)
    parser.add_argument("--final-insert-macro-recovery-hold-steps", type=int, default=10)
    parser.add_argument("--final-insert-macro-recovery-lift-action", type=float, default=0.002)
    parser.add_argument("--final-insert-macro-recovery-max-xy-action", type=float, default=0.0015)
    parser.add_argument("--final-insert-macro-recovery-max-attempts", type=int, default=2)
    parser.add_argument("--final-insert-macro-recovery-abort-xy", type=float, default=0.012)
    parser.add_argument("--final-insert-macro-recovery-abort-lift-steps", type=int, default=20)
    parser.add_argument("--final-insert-macro-recovery-abort-lift-action", type=float, default=0.005)
    parser.add_argument(
        "--final-insert-macro-recovery-abort-when-final-servo-inactive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Abort the macro recovery with a short lift if final-servo drops out mid-macro.",
    )
    parser.add_argument(
        "--guard-scenario-filter",
        choices=["none", "all", "geometry", "hard"],
        default="all",
        help="Limit guarded insertion to none, all, geometry/contact scenarios, or only the hard bucket.",
    )
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--near-hole-crop-source-size", type=int, default=None)
    parser.add_argument("--near-hole-crop-source-size-range", nargs=2, type=int, default=None)
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
    parser.add_argument("--frame-skip", type=int, default=10)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument(
        "--initialization-mode",
        choices=["fixed", "target_relative_high_start"],
        default="fixed",
    )
    parser.add_argument("--initial-tip-z-above-range", nargs=2, type=float, default=(0.15, 0.25))
    parser.add_argument("--initial-tip-xy-offset-range", nargs=2, type=float, default=(0.08, 0.16))
    parser.add_argument("--initial-tip-xy-angle-range-deg", nargs=2, type=float, default=(0.0, 360.0))
    parser.add_argument("--initial-ik-max-attempts", type=int, default=20)
    parser.add_argument(
        "--ik-control-mode",
        choices=["position", "pose", "pose_tip_priority"],
        default="position",
    )
    parser.add_argument("--ik-orientation-weight", type=float, default=0.12)
    parser.add_argument("--guard-near-ik-orientation-weight", type=float, default=None)
    parser.add_argument("--guard-final-servo-ik-orientation-weight", type=float, default=None)
    parser.add_argument("--guard-final-servo-tip-priority-ik-enabled", action="store_true")
    parser.add_argument("--guard-square-pose-yaw-align-enabled", action="store_true")
    parser.add_argument(
        "--guard-square-pose-yaw-align-ik-control-mode",
        choices=["pose", "pose_tip_priority"],
        default="pose_tip_priority",
    )
    parser.add_argument(
        "--guard-square-pose-yaw-align-ik-orientation-weight",
        type=float,
        default=0.25,
    )
    parser.add_argument("--guard-visual-yaw-align-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-model", type=Path, default=None)
    parser.add_argument("--guard-visual-yaw-align-device", default="auto")
    parser.add_argument(
        "--guard-visual-yaw-align-profiles",
        nargs="+",
        default=["square_square", "triangle_triangle", "hex_hex", "rectangular_key"],
    )
    parser.add_argument(
        "--guard-visual-yaw-align-activation-mode",
        choices=["final_servo", "near_control"],
        default="final_servo",
    )
    parser.add_argument("--guard-visual-yaw-align-max-xy", type=float, default=0.014)
    parser.add_argument("--guard-visual-yaw-align-min-z", type=float, default=0.010)
    parser.add_argument("--guard-visual-yaw-align-max-z", type=float, default=0.080)
    parser.add_argument("--guard-visual-yaw-align-max-wall-contact", type=int, default=0)
    parser.add_argument("--guard-visual-yaw-align-min-raw-norm", type=float, default=0.08)
    parser.add_argument("--guard-visual-yaw-align-min-cam-std", type=float, default=18.0)
    parser.add_argument("--guard-visual-yaw-align-min-crop-std", type=float, default=16.0)
    parser.add_argument("--guard-visual-yaw-align-deadband-deg", type=float, default=2.0)
    parser.add_argument("--guard-visual-yaw-align-max-correction-deg", type=float, default=10.0)
    parser.add_argument("--guard-visual-yaw-align-temporal-action-gate-enabled", action="store_true")
    parser.add_argument(
        "--guard-visual-yaw-align-temporal-action-gate-profiles",
        nargs="+",
        default=["rectangular_key"],
    )
    parser.add_argument("--guard-visual-yaw-align-temporal-action-gate-window", type=int, default=3)
    parser.add_argument("--guard-visual-yaw-align-temporal-action-gate-max-delta-deg", type=float, default=12.0)
    parser.add_argument("--guard-visual-yaw-align-temporal-action-gate-min-pred-yaw-deg", type=float, default=30.0)
    parser.add_argument("--guard-visual-yaw-align-temporal-action-gate-max-pred-yaw-deg", type=float, default=120.0)
    parser.add_argument("--guard-visual-yaw-align-temporal-action-gate-block-descent", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-temporal-action-gate-reset-target", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-block-descent", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-block-descent-deg", type=float, default=6.0)
    parser.add_argument("--guard-visual-yaw-align-hold-z-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-hold-z-min", type=float, default=0.045)
    parser.add_argument("--guard-visual-yaw-align-hold-up-action", type=float, default=0.003)
    parser.add_argument("--guard-visual-yaw-align-hold-xy-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-hold-xy-tolerance", type=float, default=0.003)
    parser.add_argument("--guard-visual-yaw-align-hold-max-xy-action", type=float, default=0.003)
    parser.add_argument("--guard-visual-yaw-align-hold-target-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-hold-target-steps", type=int, default=0)
    parser.add_argument("--guard-visual-yaw-align-hold-target-arm-yaw-deg", type=float, default=3.0)
    parser.add_argument("--guard-visual-yaw-align-hold-target-release-yaw-deg", type=float, default=180.0)
    parser.add_argument("--guard-visual-yaw-align-hold-target-release-xy", type=float, default=0.18)
    parser.add_argument("--guard-visual-yaw-align-hold-target-min-z", type=float, default=0.0)
    parser.add_argument("--guard-visual-yaw-align-hold-target-max-z", type=float, default=0.18)
    parser.add_argument("--guard-visual-yaw-align-hold-target-block-descent", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-low-visibility-brake-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-low-visibility-brake-min-pred-yaw-deg", type=float, default=12.0)
    parser.add_argument("--guard-visual-yaw-align-low-visibility-brake-min-xy", type=float, default=0.020)
    parser.add_argument("--guard-visual-yaw-align-low-visibility-brake-max-z", type=float, default=0.080)
    parser.add_argument("--guard-visual-yaw-align-low-visibility-brake-up-action", type=float, default=0.008)
    parser.add_argument("--guard-visual-yaw-align-low-visibility-brake-flush-history", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-large-xy-low-z-brake-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-large-xy-low-z-brake-min-xy", type=float, default=0.060)
    parser.add_argument("--guard-visual-yaw-align-large-xy-low-z-brake-max-z", type=float, default=0.010)
    parser.add_argument("--guard-visual-yaw-align-large-xy-low-z-brake-up-action", type=float, default=0.008)
    parser.add_argument("--guard-visual-yaw-align-large-xy-low-z-brake-flush-history", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-enabled", action="store_true")
    parser.add_argument(
        "--guard-visual-yaw-align-low-z-lateral-pop-recovery-profiles",
        nargs="+",
        default=["rectangular_key"],
    )
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-max-attempts", type=int, default=0)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-trigger-min-step", type=int, default=700)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-trigger-min-xy", type=float, default=0.040)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-trigger-max-z", type=float, default=0.045)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-trigger-prev-xy", type=float, default=0.008)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-trigger-xy-jump", type=float, default=0.012)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-lift-target-z", type=float, default=0.075)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-lift-z-tolerance", type=float, default=0.006)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-lift-max-steps", type=int, default=30)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-recenter-release-xy", type=float, default=0.014)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-recenter-max-steps", type=int, default=80)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-max-up-action", type=float, default=0.008)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-max-xy-action", type=float, default=0.010)
    parser.add_argument("--guard-visual-yaw-align-low-z-lateral-pop-recovery-flush-history", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-descent-abort-enabled", action="store_true")
    parser.add_argument(
        "--guard-visual-yaw-align-descent-abort-profiles",
        nargs="+",
        default=["rectangular_key"],
    )
    parser.add_argument("--guard-visual-yaw-align-descent-abort-max-attempts", type=int, default=0)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-min-step", type=int, default=0)
    parser.add_argument(
        "--guard-visual-yaw-align-descent-abort-require-unreliable-visual",
        action="store_true",
    )
    parser.add_argument(
        "--guard-visual-yaw-align-descent-abort-allow-large-pred-yaw",
        action="store_true",
    )
    parser.add_argument("--guard-visual-yaw-align-descent-abort-large-pred-yaw-deg", type=float, default=45.0)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-min-xy", type=float, default=0.060)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-max-z", type=float, default=0.080)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-lift-target-z", type=float, default=0.105)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-lift-z-tolerance", type=float, default=0.006)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-lift-max-steps", type=int, default=60)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-recenter-max-steps", type=int, default=220)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-recenter-release-xy", type=float, default=0.018)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-max-up-action", type=float, default=0.008)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-max-xy-action", type=float, default=0.010)
    parser.add_argument("--guard-visual-yaw-align-descent-abort-flush-history", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-reacquire-enabled", action="store_true")
    parser.add_argument(
        "--guard-visual-yaw-align-reacquire-profiles",
        nargs="+",
        default=["rectangular_key"],
    )
    parser.add_argument("--guard-visual-yaw-align-reacquire-max-attempts", type=int, default=0)
    parser.add_argument("--guard-visual-yaw-align-reacquire-min-step", type=int, default=700)
    parser.add_argument("--guard-visual-yaw-align-reacquire-trigger-min-xy", type=float, default=0.020)
    parser.add_argument("--guard-visual-yaw-align-reacquire-trigger-max-xy", type=float, default=0.180)
    parser.add_argument("--guard-visual-yaw-align-reacquire-trigger-min-z", type=float, default=0.000)
    parser.add_argument("--guard-visual-yaw-align-reacquire-trigger-max-z", type=float, default=0.090)
    parser.add_argument("--guard-visual-yaw-align-reacquire-trigger-min-pred-yaw-deg", type=float, default=45.0)
    parser.add_argument("--guard-visual-yaw-align-reacquire-trigger-require-visible", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-reacquire-trigger-require-stable-delta", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-reacquire-trigger-stable-window", type=int, default=3)
    parser.add_argument("--guard-visual-yaw-align-reacquire-trigger-max-delta-deg", type=float, default=12.0)
    parser.add_argument("--guard-visual-yaw-align-reacquire-xy-gate-trigger-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-reacquire-xy-gate-min-xy", type=float, default=0.080)
    parser.add_argument("--guard-visual-yaw-align-reacquire-lift-target-z", type=float, default=0.115)
    parser.add_argument("--guard-visual-yaw-align-reacquire-lift-z-tolerance", type=float, default=0.006)
    parser.add_argument("--guard-visual-yaw-align-reacquire-lift-max-steps", type=int, default=45)
    parser.add_argument("--guard-visual-yaw-align-reacquire-recenter-max-steps", type=int, default=90)
    parser.add_argument("--guard-visual-yaw-align-reacquire-recenter-release-xy", type=float, default=0.014)
    parser.add_argument("--guard-visual-yaw-align-reacquire-max-up-action", type=float, default=0.006)
    parser.add_argument("--guard-visual-yaw-align-reacquire-max-xy-action", type=float, default=0.006)
    parser.add_argument("--guard-visual-yaw-align-reacquire-flush-history", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-reacquire-relaxed-yaw-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-reacquire-relaxed-yaw-min-pred-yaw-deg", type=float, default=30.0)
    parser.add_argument("--guard-visual-yaw-align-reacquire-relaxed-yaw-max-correction-deg", type=float, default=45.0)
    parser.add_argument("--guard-visual-yaw-align-reacquire-relaxed-yaw-min-z", type=float, default=0.050)
    parser.add_argument("--guard-visual-yaw-align-reacquire-relaxed-yaw-max-z", type=float, default=0.130)
    parser.add_argument("--guard-visual-yaw-align-reacquire-relaxed-yaw-require-visible", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-reacquire-relaxed-yaw-require-stable-delta", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-reacquire-relaxed-yaw-stable-window", type=int, default=3)
    parser.add_argument("--guard-visual-yaw-align-reacquire-relaxed-yaw-max-delta-deg", type=float, default=12.0)
    parser.add_argument("--guard-visual-yaw-align-reacquire-relaxed-yaw-allow-visible-reapply", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-reacquire-descent-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-reacquire-descent-yaw-deg", type=float, default=8.0)
    parser.add_argument("--guard-visual-yaw-align-reacquire-descent-xy", type=float, default=0.035)
    parser.add_argument("--guard-visual-yaw-align-reacquire-descent-min-z", type=float, default=0.025)
    parser.add_argument("--guard-visual-yaw-align-reacquire-descent-max-z", type=float, default=0.130)
    parser.add_argument("--guard-visual-yaw-align-reacquire-descent-max-down-action", type=float, default=0.003)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-enabled", action="store_true")
    parser.add_argument(
        "--guard-visual-yaw-align-wrong-basin-hold-profiles",
        nargs="+",
        default=["rectangular_key"],
    )
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-min-pred-yaw-deg", type=float, default=120.0)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-require-visible", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-require-stable-delta", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-stable-window", type=int, default=3)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-max-delta-deg", type=float, default=12.0)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-steps", type=int, default=160)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-release-yaw-deg", type=float, default=8.0)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-release-xy", type=float, default=0.018)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-max-xy", type=float, default=0.030)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-min-z", type=float, default=0.000)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-max-z", type=float, default=0.140)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-max-xy-action", type=float, default=0.008)
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-block-descent", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-wrong-basin-hold-flush-history", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-recenter-after-yaw-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-recenter-release-xy", type=float, default=0.006)
    parser.add_argument("--guard-visual-yaw-align-recenter-block-descent", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-latch-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-latch-steps", type=int, default=80)
    parser.add_argument("--guard-visual-yaw-align-latch-max-xy", type=float, default=0.18)
    parser.add_argument("--guard-visual-yaw-align-latch-min-z", type=float, default=0.0)
    parser.add_argument("--guard-visual-yaw-align-latch-max-z", type=float, default=0.18)
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-enabled", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-yaw-deg", type=float, default=1.0)
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-xy", type=float, default=0.020)
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-min-z", type=float, default=0.010)
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-max-z", type=float, default=0.180)
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-required-steps", type=int, default=1)
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-require-visible", action="store_true")
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-latch-steps", type=int, default=0)
    parser.add_argument(
        "--guard-visual-yaw-align-aligned-descent-latch-release-xy",
        type=float,
        default=0.020,
    )
    parser.add_argument(
        "--guard-visual-yaw-align-aligned-descent-latch-release-yaw-deg",
        type=float,
        default=8.0,
    )
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-latch-min-z", type=float, default=0.0)
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-latch-max-z", type=float, default=0.180)
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-max-down-action", type=float, default=0.004)
    parser.add_argument("--guard-visual-yaw-align-aligned-descent-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guard-visual-yaw-align-low-z-late-finish-descent-enabled", action="store_true")
    parser.add_argument(
        "--guard-visual-yaw-align-low-z-late-finish-descent-profiles",
        nargs="+",
        default=["rectangular_key"],
    )
    parser.add_argument("--guard-visual-yaw-align-low-z-late-finish-descent-min-step", type=int, default=850)
    parser.add_argument("--guard-visual-yaw-align-low-z-late-finish-descent-max-xy", type=float, default=0.006)
    parser.add_argument("--guard-visual-yaw-align-low-z-late-finish-descent-min-z", type=float, default=0.015)
    parser.add_argument("--guard-visual-yaw-align-low-z-late-finish-descent-max-z", type=float, default=0.045)
    parser.add_argument("--guard-visual-yaw-align-low-z-late-finish-descent-max-yaw-deg", type=float, default=8.0)
    parser.add_argument("--guard-visual-yaw-align-low-z-late-finish-descent-max-xy-action", type=float, default=0.001)
    parser.add_argument("--guard-visual-yaw-align-low-z-late-finish-descent-max-down-action", type=float, default=0.003)
    parser.add_argument("--guard-visual-yaw-align-low-z-late-finish-descent-flush-history", action="store_true")
    parser.add_argument(
        "--guard-visual-yaw-align-ik-control-mode",
        choices=["pose", "pose_tip_priority"],
        default="pose_tip_priority",
    )
    parser.add_argument(
        "--guard-visual-yaw-align-ik-orientation-weight",
        type=float,
        default=0.18,
    )
    parser.add_argument("--guard-contact-unjam-ik-orientation-weight", type=float, default=None)
    parser.add_argument("--guard-contact-reinsert-orient-ik-orientation-weight", type=float, default=None)
    parser.add_argument("--guard-contact-reinsert-high-ik-orientation-weight", type=float, default=None)
    parser.add_argument("--guard-contact-reinsert-tip-priority-ik-enabled", action="store_true")
    parser.add_argument("--ik-posture-weight", type=float, default=0.01)
    parser.add_argument("--ik-step-limit", type=float, default=0.06)
    parser.add_argument("--ik-max-iterations", type=int, default=24)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--success-shape-yaw-tolerance-deg", type=float, default=None)
    parser.add_argument(
        "--success-shape-yaw-profiles",
        nargs="+",
        default=["square_square", "triangle_triangle", "hex_hex", "slot_slot", "rectangular_key"],
    )
    parser.add_argument("--geometry-hole-half-size-range", nargs=2, type=float, default=(0.017, 0.021))
    parser.add_argument("--geometry-peg-radius-range", nargs=2, type=float, default=(0.0115, 0.0125))
    parser.add_argument("--geometry-hole-center-xy-jitter", nargs=2, type=float, default=None)
    parser.add_argument("--geometry-fixture-height-jitter", type=float, default=None)
    parser.add_argument("--geometry-table-height-jitter", type=float, default=None)
    parser.add_argument(
        "--geometry-profile",
        choices=[
            "single",
            "round_round",
            "round_square",
            "square_square",
            "hex_hex",
            "triangle_triangle",
            "slot_slot",
            "rectangular_key",
            "mixed_basic",
            "mixed_same_shape",
        ],
        default="single",
    )
    parser.add_argument("--geometry-fixture-mode", choices=["box_wall", "true_mesh"], default="box_wall")
    parser.add_argument(
        "--geometry-true-fixture-variant",
        choices=["nominal", "tight_yaw"],
        default="nominal",
    )
    parser.add_argument("--geometry-square-peg-half-size-range", nargs=2, type=float, default=(0.0105, 0.0125))
    parser.add_argument("--geometry-mixed-square-probability", type=float, default=0.5)
    parser.add_argument("--enable-peg-tip-visual-helpers", action="store_true")
    parser.add_argument("--hard-control-scale-range", nargs=2, type=float, default=None)
    parser.add_argument("--hard-control-noise-std-range", nargs=2, type=float, default=None)
    parser.add_argument("--hard-control-delay-range", nargs=2, type=int, default=None)
    parser.add_argument("--hard-control-filter-alpha-range", nargs=2, type=float, default=None)
    parser.add_argument("--nominal-joint-damping-multiplier", type=float, default=1.0)
    parser.add_argument("--nominal-actuator-kp-multiplier", type=float, default=1.0)
    parser.add_argument("--guard-near-actuator-kp-enabled", action="store_true")
    parser.add_argument("--guard-near-actuator-kp-multiplier", type=float, default=3.0)
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
    parser.add_argument("--guard-start-xy", type=float, default=0.060)
    parser.add_argument("--guard-start-z", type=float, default=0.100)
    parser.add_argument("--guard-risk-xy", type=float, default=0.0)
    parser.add_argument("--guard-blend", type=float, default=1.0)
    parser.add_argument("--guard-min-policy-steps", type=int, default=0)
    parser.add_argument("--guard-block-down-when-unaligned", action="store_true")
    parser.add_argument("--guard-release-on-high", action="store_true")
    parser.add_argument("--guard-retry-enabled", action="store_true")
    parser.add_argument("--guard-retry-stall-steps", type=int, default=80)
    parser.add_argument("--guard-retry-xy-tolerance", type=float, default=0.015)
    parser.add_argument("--guard-retry-z-max", type=float, default=0.060)
    parser.add_argument("--guard-retry-lift-height", type=float, default=0.080)
    parser.add_argument("--guard-retry-release-xy", type=float, default=0.005)
    parser.add_argument("--guard-retry-max-attempts", type=int, default=2)
    parser.add_argument("--guard-retry-max-steps", type=int, default=120)
    parser.add_argument("--guard-insert-latch-enabled", action="store_true")
    parser.add_argument("--guard-insert-latch-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guard-insert-latch-release-xy", type=float, default=0.009)
    parser.add_argument("--guard-insert-latch-resume-xy", type=float, default=0.005)
    parser.add_argument("--guard-insert-latch-recenter-height", type=float, default=0.0)
    parser.add_argument("--guard-insert-latch-recenter-z-tolerance", type=float, default=0.0)
    parser.add_argument("--guard-insert-latch-max-down-action", type=float, default=0.0)
    parser.add_argument("--guard-hover-enabled", action="store_true")
    parser.add_argument("--guard-hover-xy-tolerance", type=float, default=0.004)
    parser.add_argument("--guard-hover-release-xy", type=float, default=0.006)
    parser.add_argument("--guard-hover-height", type=float, default=0.050)
    parser.add_argument("--guard-hover-z-tolerance", type=float, default=0.010)
    parser.add_argument("--guard-hover-required-steps", type=int, default=6)
    parser.add_argument("--guard-hover-max-down-action", type=float, default=0.002)
    parser.add_argument("--guard-near-action-scale-enabled", action="store_true")
    parser.add_argument("--guard-near-action-xy-tolerance", type=float, default=0.020)
    parser.add_argument("--guard-near-action-z-threshold", type=float, default=0.070)
    parser.add_argument("--guard-near-max-xy-action", type=float, default=0.002)
    parser.add_argument("--guard-near-max-down-action", type=float, default=0.0015)
    parser.add_argument("--guard-fixture-clearance-enabled", action="store_true")
    parser.add_argument("--guard-fixture-clearance-xy-min", type=float, default=0.020)
    parser.add_argument("--guard-fixture-clearance-xy-max", type=float, default=0.090)
    parser.add_argument("--guard-fixture-clearance-z-max", type=float, default=0.060)
    parser.add_argument("--guard-fixture-clearance-lift-height", type=float, default=0.100)
    parser.add_argument("--guard-fixture-clearance-max-up-action", type=float, default=0.005)
    parser.add_argument("--guard-fixture-clearance-realign-enabled", action="store_true")
    parser.add_argument("--guard-fixture-clearance-realign-start-z", type=float, default=0.0)
    parser.add_argument("--guard-fixture-clearance-realign-xy", type=float, default=0.020)
    parser.add_argument("--guard-fixture-clearance-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guard-fixture-clearance-max-down-action", type=float, default=0.0)
    parser.add_argument("--guard-fixture-clearance-max-steps", type=int, default=240)
    parser.add_argument("--guard-fixture-clearance-retreat-enabled", action="store_true")
    parser.add_argument("--guard-fixture-clearance-retreat-release-xy", type=float, default=0.070)
    parser.add_argument("--guard-fixture-clearance-retreat-max-xy-action", type=float, default=0.003)
    parser.add_argument("--guard-preinsert-recenter-enabled", action="store_true")
    parser.add_argument("--guard-preinsert-recenter-start-z", type=float, default=0.025)
    parser.add_argument("--guard-preinsert-recenter-min-z", type=float, default=0.0)
    parser.add_argument("--guard-preinsert-recenter-trigger-xy", type=float, default=0.004)
    parser.add_argument("--guard-preinsert-recenter-stable-xy", type=float, default=0.0035)
    parser.add_argument("--guard-preinsert-recenter-height", type=float, default=0.025)
    parser.add_argument("--guard-preinsert-recenter-z-tolerance", type=float, default=0.006)
    parser.add_argument("--guard-preinsert-recenter-stable-steps", type=int, default=3)
    parser.add_argument("--guard-preinsert-recenter-max-steps", type=int, default=80)
    parser.add_argument("--guard-preinsert-recenter-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guard-preinsert-recenter-max-up-action", type=float, default=0.005)
    parser.add_argument("--guard-preinsert-recenter-lift-before-lateral", action="store_true")
    parser.add_argument("--guard-approach-recenter-enabled", action="store_true")
    parser.add_argument(
        "--guard-approach-recenter-requires-stateful-recovery",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--guard-approach-recenter-start-z", type=float, default=0.075)
    parser.add_argument("--guard-approach-recenter-min-z", type=float, default=0.045)
    parser.add_argument("--guard-approach-recenter-trigger-xy", type=float, default=0.010)
    parser.add_argument("--guard-approach-recenter-max-xy", type=float, default=0.030)
    parser.add_argument("--guard-approach-recenter-stable-xy", type=float, default=0.005)
    parser.add_argument("--guard-approach-recenter-height", type=float, default=0.060)
    parser.add_argument("--guard-approach-recenter-z-tolerance", type=float, default=0.012)
    parser.add_argument("--guard-approach-recenter-stable-steps", type=int, default=2)
    parser.add_argument("--guard-approach-recenter-max-steps", type=int, default=220)
    parser.add_argument("--guard-approach-recenter-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guard-approach-recenter-max-up-action", type=float, default=0.005)
    parser.add_argument("--guard-approach-recenter-xy-bias", nargs=2, type=float, default=(0.0, 0.0))
    parser.add_argument("--guard-early-approach-assist-enabled", action="store_true")
    parser.add_argument("--guard-early-approach-assist-trigger-xy", type=float, default=0.100)
    parser.add_argument("--guard-early-approach-assist-release-xy", type=float, default=0.060)
    parser.add_argument("--guard-early-approach-assist-min-z", type=float, default=0.120)
    parser.add_argument("--guard-early-approach-assist-max-z", type=float, default=0.240)
    parser.add_argument("--guard-early-approach-assist-target-height", type=float, default=0.140)
    parser.add_argument("--guard-early-approach-assist-max-xy-action", type=float, default=0.008)
    parser.add_argument("--guard-early-approach-assist-max-up-action", type=float, default=0.005)
    parser.add_argument("--guard-early-approach-assist-max-steps", type=int, default=300)
    parser.add_argument("--guard-stateful-recovery-enabled", action="store_true")
    parser.add_argument("--guard-stateful-recovery-trigger-xy-min", type=float, default=0.006)
    parser.add_argument("--guard-stateful-recovery-trigger-xy-max", type=float, default=0.030)
    parser.add_argument("--guard-stateful-recovery-trigger-z-max", type=float, default=0.130)
    parser.add_argument("--guard-stateful-recovery-lift-height", type=float, default=0.060)
    parser.add_argument("--guard-stateful-recovery-lift-z-tolerance", type=float, default=0.006)
    parser.add_argument("--guard-stateful-recovery-release-xy", type=float, default=0.0048)
    parser.add_argument("--guard-stateful-recovery-resume-xy", type=float, default=0.0065)
    parser.add_argument("--guard-stateful-recovery-resume-z", type=float, default=0.012)
    parser.add_argument("--guard-stateful-recovery-stable-steps", type=int, default=4)
    parser.add_argument("--guard-stateful-recovery-stall-steps", type=int, default=100)
    parser.add_argument("--guard-stateful-recovery-min-xy-progress", type=float, default=0.00035)
    parser.add_argument("--guard-stateful-recovery-min-actual-xy-motion", type=float, default=0.00012)
    parser.add_argument("--guard-stateful-recovery-min-command-xy", type=float, default=0.0025)
    parser.add_argument("--guard-stateful-recovery-max-attempts", type=int, default=1)
    parser.add_argument("--guard-stateful-recovery-max-steps", type=int, default=220)
    parser.add_argument("--guard-stateful-recovery-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guard-stateful-recovery-max-down-action", type=float, default=0.0015)
    parser.add_argument("--guard-stateful-recovery-max-up-action", type=float, default=0.005)
    parser.add_argument("--guard-final-servo-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-start-xy", type=float, default=0.012)
    parser.add_argument("--guard-final-servo-start-z", type=float, default=0.070)
    parser.add_argument("--guard-final-servo-min-start-z", type=float, default=0.010)
    parser.add_argument("--guard-final-servo-hover-height", type=float, default=0.040)
    parser.add_argument("--guard-final-servo-hover-z-tolerance", type=float, default=0.010)
    parser.add_argument("--guard-final-servo-stable-xy", type=float, default=0.0045)
    parser.add_argument("--guard-final-servo-descent-start-xy", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-stable-steps", type=int, default=6)
    parser.add_argument("--guard-final-servo-release-xy", type=float, default=0.008)
    parser.add_argument("--guard-final-servo-align-timeout-steps", type=int, default=0)
    parser.add_argument("--guard-final-servo-align-timeout-xy", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-align-hover-escape-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-align-hover-escape-steps", type=int, default=20)
    parser.add_argument("--guard-final-servo-align-hover-escape-xy", type=float, default=0.006)
    parser.add_argument("--guard-final-servo-align-hover-escape-min-z", type=float, default=0.060)
    parser.add_argument("--guard-final-servo-align-hover-escape-max-z", type=float, default=0.100)
    parser.add_argument("--guard-final-servo-rearm-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-rearm-cooldown-steps", type=int, default=20)
    parser.add_argument("--guard-final-servo-rearm-stable-steps", type=int, default=3)
    parser.add_argument("--guard-final-servo-rearm-xy-max", type=float, default=0.006)
    parser.add_argument("--guard-final-servo-rearm-z-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-rearm-z-max", type=float, default=0.060)
    parser.add_argument("--guard-final-servo-rearm-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-rearm-tilt-max-deg", type=float, default=6.0)
    parser.add_argument("--guard-final-servo-rearm-margin-min", type=float, default=-0.001)
    parser.add_argument("--guard-final-servo-rearm-max-attempts", type=int, default=1)
    parser.add_argument(
        "--guard-final-servo-priority-over-fixture-clearance",
        action="store_true",
        help=(
            "Keep an active final-servo/recovery phase from being preempted by "
            "fixture-clearance. Default off for diagnostic use."
        ),
    )
    parser.add_argument("--guard-final-servo-max-xy-action", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-max-down-action", type=float, default=0.0015)
    parser.add_argument("--guard-final-servo-low-recenter-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-low-recenter-z-max", type=float, default=0.012)
    parser.add_argument(
        "--guard-final-servo-low-recenter-trigger-xy",
        type=float,
        default=0.0065,
    )
    parser.add_argument(
        "--guard-final-servo-low-recenter-release-xy",
        type=float,
        default=0.0055,
    )
    parser.add_argument("--guard-final-servo-low-recenter-height", type=float, default=0.010)
    parser.add_argument("--guard-final-servo-low-recenter-stable-steps", type=int, default=2)
    parser.add_argument("--guard-final-servo-low-recenter-max-steps", type=int, default=120)
    parser.add_argument(
        "--guard-final-servo-low-recenter-max-up-action",
        type=float,
        default=0.003,
    )
    parser.add_argument("--guard-final-servo-low-recenter-stall-steps", type=int, default=0)
    parser.add_argument(
        "--guard-final-servo-low-recenter-min-xy-progress",
        type=float,
        default=0.0001,
    )
    parser.add_argument("--guard-final-servo-descend-xy-bias", nargs=2, type=float, default=(0.0, 0.0))
    parser.add_argument(
        "--guard-final-servo-descend-xy-bias-max-clearance",
        type=float,
        default=float("inf"),
    )
    parser.add_argument("--guard-final-servo-descend-xy-bias-requires-stateful-recovery", action="store_true")
    parser.add_argument("--guard-final-servo-lift-height", type=float, default=0.060)
    parser.add_argument("--guard-final-servo-stall-steps", type=int, default=80)
    parser.add_argument("--guard-final-servo-min-z-progress", type=float, default=0.002)
    parser.add_argument("--guard-final-servo-max-retries", type=int, default=2)
    parser.add_argument("--guard-final-servo-max-recovery-steps", type=int, default=160)
    parser.add_argument(
        "--guard-final-servo-recovery-mode",
        choices=["lift_recenter", "soft_unjam"],
        default="lift_recenter",
    )
    parser.add_argument("--guard-final-servo-soft-unjam-lift", type=float, default=0.006)
    parser.add_argument("--guard-final-servo-soft-unjam-min-height", type=float, default=0.012)
    parser.add_argument("--guard-final-servo-soft-unjam-z-tolerance", type=float, default=0.001)
    parser.add_argument("--guard-final-servo-soft-unjam-hold-steps", type=int, default=4)
    parser.add_argument("--guard-final-servo-soft-unjam-max-up-action", type=float, default=0.002)
    parser.add_argument("--guard-final-servo-square-recovery-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-tilt-deg", type=float, default=12.0)
    parser.add_argument("--guard-final-servo-square-recovery-tilt-steps", type=int, default=12)
    parser.add_argument("--guard-final-servo-square-recovery-z-max", type=float, default=0.025)
    parser.add_argument("--guard-final-servo-square-recovery-xy-max", type=float, default=0.014)
    parser.add_argument("--guard-final-servo-square-recovery-lift-height", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-recovery-escape-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-xy", type=float, default=0.014)
    parser.add_argument("--guard-final-servo-square-recovery-escape-z-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-recovery-escape-z-max", type=float, default=0.060)
    parser.add_argument("--guard-final-servo-square-recovery-escape-height", type=float, default=0.080)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-height-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-height", type=float, default=0.055)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-height-min-steps-since-reset", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-release-xy", type=float, default=0.006)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-release-xy", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-release-min-steps-since-reset", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-max-steps", type=int, default=180)
    parser.add_argument("--guard-final-servo-square-recovery-escape-max-xy-action", type=float, default=0.004)
    parser.add_argument("--guard-final-servo-square-recovery-escape-max-up-action", type=float, default=0.005)
    parser.add_argument("--guard-final-servo-square-recovery-escape-max-clearance", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-contact-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-contact-wall-steps", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-contact-xy-max", type=float, default=0.008)
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-contact-z-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-contact-z-max", type=float, default=0.045)
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-contact-margin-threshold", type=float, default=0.0)
    parser.add_argument(
        "--guard-final-servo-square-recovery-escape-early-contact-require-bad-margin",
        action="store_true",
    )
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-risk-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-risk-steps", type=int, default=3)
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-risk-xy-max", type=float, default=0.008)
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-risk-z-min", type=float, default=0.028)
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-risk-z-max", type=float, default=0.060)
    parser.add_argument("--guard-final-servo-square-recovery-escape-early-risk-margin-threshold", type=float, default=-0.0003)
    parser.add_argument("--guard-final-servo-square-recovery-escape-pre-lift-steps", type=int, default=6)
    parser.add_argument("--guard-final-servo-square-recovery-escape-pre-lift-on-trigger", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-xy-max", type=float, default=0.006)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-z-min", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-z-max", type=float, default=0.065)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-max-steps", type=int, default=24)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-min-steps-since-reset", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-max-steps-since-reset", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-from-escape-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-from-escape-min-phase-steps", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-max-down-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-max-down-z-min", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-max-xy-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-direct-fast-settle-fast-down-margin-min", type=float, default=-1.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-no-up-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-descend-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-descend-xy-max", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-descend-z-min", type=float, default=0.045)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-descend-z-max", type=float, default=0.075)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-descend-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-descend-margin-min", type=float, default=-0.0015)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-descend-max-down-action", type=float, default=0.0015)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-drift-lift-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-drift-lift-min-phase-steps", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-drift-lift-xy-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-drift-lift-z-min", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-drift-lift-z-max", type=float, default=0.050)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-drift-lift-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-drift-lift-yaw-min-deg", type=float, default=3.4)
    parser.add_argument("--guard-final-servo-square-recovery-escape-recenter-drift-lift-tilt-min-deg", type=float, default=999999.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-min-steps-since-reset", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-min-phase-steps", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-xy-max", type=float, default=0.009)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-z-min", type=float, default=0.040)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-z-max", type=float, default=0.055)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-margin-min", type=float, default=-0.0030)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-margin-max", type=float, default=-0.0003)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-tilt-max-deg", type=float, default=2.5)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-max-down-action", type=float, default=0.0015)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-max-xy-action", type=float, default=0.0040)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-hold-release-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-recenter-descend-hold-z-min", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-min-steps-since-reset", type=int, default=940)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-min-phase-steps", type=int, default=5)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-min-brake-attempts", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-xy-max", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-z-min", type=float, default=0.038)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-z-max", type=float, default=0.048)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-margin-min", type=float, default=-0.0015)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-topdown-margin-min", type=float, default=0.0003)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-yaw-max-deg", type=float, default=5.5)
    parser.add_argument("--guard-final-servo-square-recovery-escape-late-clean-direct-finish-tilt-max-deg", type=float, default=2.2)
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-xy-min", type=float, default=0.014)
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-xy-max", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-z-min", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-z-max", type=float, default=0.055)
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-max-contact-pop-hold-attempts", type=int, default=999999)
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-margin-min", type=float, default=-1.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-topdown-margin-min", type=float, default=-1.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-yaw-max-deg", type=float, default=180.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-tilt-max-deg", type=float, default=180.0)
    parser.add_argument("--guard-final-servo-square-recovery-escape-flush-control-history", action="store_true")
    parser.add_argument("--guard-final-servo-split-recovery-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-contact-reinsert-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-contact-unjam-wall-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-contact-unjam-tilt-deg", type=float, default=12.0)
    parser.add_argument("--guard-final-servo-contact-unjam-z-max", type=float, default=0.025)
    parser.add_argument("--guard-final-servo-contact-unjam-xy-max", type=float, default=0.014)
    parser.add_argument("--guard-final-servo-contact-unjam-lift-height", type=float, default=0.055)
    parser.add_argument("--guard-final-servo-contact-unjam-release-xy", type=float, default=0.0055)
    parser.add_argument("--guard-final-servo-contact-unjam-max-up-action", type=float, default=0.005)
    parser.add_argument("--guard-final-servo-contact-unjam-wall-bias", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-contact-reinsert-orient-hold-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-contact-reinsert-orient-tilt-deg", type=float, default=10.0)
    parser.add_argument("--guard-final-servo-contact-reinsert-orient-stable-steps", type=int, default=4)
    parser.add_argument("--guard-final-servo-contact-reinsert-orient-max-steps", type=int, default=80)
    parser.add_argument("--guard-final-servo-contact-reinsert-orient-max-xy-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-contact-reinsert-orient-tip-lock-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-contact-reinsert-orient-tip-lock-drift-gain", type=float, default=2.0)
    parser.add_argument("--guard-final-servo-contact-reinsert-orient-tip-lock-max-offset", type=float, default=0.004)
    parser.add_argument("--guard-final-servo-contact-reinsert-high-reapproach-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-contact-reinsert-high-reapproach-height", type=float, default=0.055)
    parser.add_argument("--guard-final-servo-contact-reinsert-high-reapproach-release-xy", type=float, default=0.0045)
    parser.add_argument("--guard-final-servo-contact-reinsert-high-reapproach-stable-steps", type=int, default=4)
    parser.add_argument("--guard-final-servo-contact-reinsert-high-reapproach-max-steps", type=int, default=180)
    parser.add_argument("--guard-final-servo-contact-reinsert-high-reapproach-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guard-final-servo-contact-reinsert-high-reapproach-max-up-action", type=float, default=0.005)
    parser.add_argument("--guard-final-servo-contact-reinsert-descend-max-steps", type=int, default=180)
    parser.add_argument("--guard-final-servo-contact-reinsert-micro-align-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-contact-reinsert-micro-align-z-max", type=float, default=0.012)
    parser.add_argument("--guard-final-servo-contact-reinsert-micro-align-xy-max", type=float, default=0.0068)
    parser.add_argument("--guard-final-servo-contact-reinsert-micro-align-release-xy", type=float, default=0.0050)
    parser.add_argument("--guard-final-servo-contact-reinsert-micro-align-tilt-deg", type=float, default=9.0)
    parser.add_argument("--guard-final-servo-contact-reinsert-micro-align-max-steps", type=int, default=120)
    parser.add_argument("--guard-final-servo-contact-reinsert-micro-align-stall-steps", type=int, default=40)
    parser.add_argument("--guard-final-servo-contact-reinsert-micro-align-min-xy-progress", type=float, default=0.00003)
    parser.add_argument("--guard-final-servo-contact-reinsert-micro-align-max-xy-action", type=float, default=0.0015)
    parser.add_argument("--guard-final-servo-contact-reinsert-micro-align-up-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-near-miss-steps", type=int, default=40)
    parser.add_argument("--guard-final-servo-near-miss-xy-max", type=float, default=0.0065)
    parser.add_argument("--guard-final-servo-near-miss-z-max", type=float, default=0.055)
    parser.add_argument("--guard-final-servo-near-miss-contact-max", type=int, default=1)
    parser.add_argument("--guard-final-servo-near-miss-tilt-max-deg", type=float, default=8.0)
    parser.add_argument("--guard-final-servo-near-miss-max-steps", type=int, default=180)
    parser.add_argument("--guard-final-servo-near-miss-max-down-action", type=float, default=0.0015)
    parser.add_argument("--guard-final-servo-near-miss-xy-bias", nargs=2, type=float, default=(0.0, 0.0))
    parser.add_argument("--guard-final-servo-square-fast-settle-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-xy-max", type=float, default=0.008)
    parser.add_argument("--guard-final-servo-square-fast-settle-z-max", type=float, default=0.040)
    parser.add_argument("--guard-final-servo-square-fast-settle-release-xy", type=float, default=0.005)
    parser.add_argument("--guard-final-servo-square-fast-settle-tilt-max-deg", type=float, default=8.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-max-steps", type=int, default=260)
    parser.add_argument("--guard-final-servo-square-fast-settle-max-xy-action", type=float, default=0.008)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-max-xy-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-threshold", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-max-down-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-down-threshold", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-max-down-action", type=float, default=0.0020)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-unjam-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-max-down-action", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-max-xy-action", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-xy-max", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-z-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-z-max", type=float, default=0.060)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-min-brake-attempts", type=int, default=3)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-min-phase-steps", type=int, default=10)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-tilt-max-deg", type=float, default=8.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-margin-min", type=float, default=-1.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-down-boost-min-clean-steps", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-min-steps-since-reset", type=int, default=960)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-min-brake-attempts", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-min-phase-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-min-clean-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-xy-max", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-z-min", type=float, default=0.010)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-z-max", type=float, default=0.024)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-margin-min", type=float, default=0.0002)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-topdown-margin-min", type=float, default=0.0006)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-yaw-max-deg", type=float, default=1.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-tilt-max-deg", type=float, default=1.5)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-max-down-action", type=float, default=0.0035)
    parser.add_argument("--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-max-xy-action", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-contact-down-guard-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-contact-down-guard-min-steps-since-reset", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-contact-down-guard-wall-count", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-contact-down-guard-xy-max", type=float, default=0.004)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-contact-down-guard-z-max", type=float, default=0.030)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-contact-down-guard-min-brake-attempts", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-contact-down-guard-max-up-action", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-steps", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-wall-count", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-xy-min", type=float, default=0.010)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-xy-max", type=float, default=0.024)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-z-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-z-max", type=float, default=0.042)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-contact-max", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-min-phase-steps", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-min-brake-attempts", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-max-attempts", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-max-up-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-min-phase-steps", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-xy-min", type=float, default=0.016)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-xy-max", type=float, default=0.026)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-z-min", type=float, default=0.036)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-z-max", type=float, default=0.045)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-contact-max", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-margin-min", type=float, default=-0.0015)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-topdown-margin-min", type=float, default=0.0005)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-yaw-max-deg", type=float, default=1.25)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-tilt-max-deg", type=float, default=3.5)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-min-attempts", type=int, default=3)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-xy-min", type=float, default=0.008)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-xy-max", type=float, default=0.016)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-z-min", type=float, default=0.034)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-z-max", type=float, default=0.044)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-contact-max", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-margin-min", type=float, default=0.0004)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-topdown-margin-min", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-yaw-max-deg", type=float, default=1.6)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-tilt-max-deg", type=float, default=1.6)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-steps", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-xy-min", type=float, default=0.014)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-xy-max", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-z-min", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-z-max", type=float, default=0.055)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-min-brake-attempts", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-max-contact-pop-hold-attempts", type=int, default=999999)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-min-contact-pop-hold-phase-steps", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-max-attempts", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-margin-min", type=float, default=-0.0045)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-topdown-margin-min", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-yaw-max-deg", type=float, default=5.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-tilt-max-deg", type=float, default=5.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-no-contact-pop-hold-max-up-action", type=float, default=0.0015)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-steps", type=int, default=3)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-xy-max", type=float, default=0.0030)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-z-min", type=float, default=0.024)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-z-max", type=float, default=0.033)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-contact-max", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-min-phase-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-max-phase-steps", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-min-brake-attempts", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-min-soft-hold-attempts", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-max-attempts", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-margin-min", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-margin-max", type=float, default=0.00075)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-topdown-margin-min", type=float, default=0.0007)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-topdown-margin-max", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-yaw-max-deg", type=float, default=1.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-tilt-min-deg", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-tilt-max-deg", type=float, default=1.3)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-guard-max-up-action", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-limit-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-limit-max-xy-action", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-pre-pop-limit-max-down-action", type=float, default=0.0006)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-xy-min", type=float, default=0.018)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-xy-max", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-z-min", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-z-max", type=float, default=0.055)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-contact-max", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-min-brake-attempts", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-min-steps-since-reset", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-max-attempts", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-height", type=float, default=0.070)
    parser.add_argument(
        "--guard-final-servo-square-fast-settle-severe-pop-reapproach-pre-lift-enabled",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-margin-min", type=float, default=-0.006)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-topdown-margin-min", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-yaw-max-deg", type=float, default=6.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-severe-pop-reapproach-tilt-max-deg", type=float, default=6.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-xy-max", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-z-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-z-max", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-margin-threshold", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-margin-min", type=float, default=-0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-wall-count", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-contact-max", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-min-brake-attempts", type=int, default=3)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-min-phase-steps", type=int, default=12)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-max-attempts", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-fast-settle-clearance-hold-max-up-action", type=float, default=0.0008)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-wall-count", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-xy-max", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-z-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-z-max", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-margin-min", type=float, default=-0.0012)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-margin-threshold", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-contact-max", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-min-brake-attempts", type=int, default=3)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-min-phase-steps", type=int, default=12)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-max-attempts", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-lift-height", type=float, default=0.004)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-target-z-max", type=float, default=0.040)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-lift-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-recenter-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-release-xy", type=float, default=0.0020)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-max-up-action", type=float, default=0.0020)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-relief-max-xy-action", type=float, default=0.0010)
    parser.add_argument(
        "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-start-z-min",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-xy-max",
        type=float,
        default=0.035,
    )
    parser.add_argument(
        "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-z-max",
        type=float,
        default=0.050,
    )
    parser.add_argument(
        "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-max-steps",
        type=int,
        default=24,
    )
    parser.add_argument(
        "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-contact-pop-min-attempts",
        type=int,
        default=999999,
    )
    parser.add_argument(
        "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-contact-pop-xy-max",
        type=float,
        default=0.035,
    )
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-xy-max", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-z-min", type=float, default=0.026)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-z-max", type=float, default=0.032)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-margin-min", type=float, default=0.0002)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-margin-threshold", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-min-brake-attempts", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-min-phase-steps", type=int, default=38)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-min-stall-steps", type=int, default=12)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-max-attempts", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-hold-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-hold-steps", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-hold-max-up-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-low-z-stall-relief-hold-min-contact-pop-hold-attempts", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-steps", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-xy-max", type=float, default=0.0040)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-z-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-z-max", type=float, default=0.040)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-margin-min", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-margin-max", type=float, default=1.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-yaw-max-deg", type=float, default=1.5)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-tilt-max-deg", type=float, default=2.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-wall-count", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-contact-max", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-min-phase-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-min-steps-since-reset", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-subsequent-min-phase-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-subsequent-min-steps-since-reset", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-subsequent-z-max", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-subsequent-margin-min", type=float, default=-1.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-max-attempts", type=int, default=3)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-max-up-action", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-extend-until-clear-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-extend-until-clear-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-extend-until-clear-max-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-extend-until-clear-min-steps-since-reset", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-steps", type=int, default=20)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-xy-max", type=float, default=0.0035)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-z-min", type=float, default=0.018)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-z-max", type=float, default=0.040)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-margin-min", type=float, default=0.0002)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-yaw-max-deg", type=float, default=1.5)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-tilt-max-deg", type=float, default=2.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-max-xy-action", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-max-down-action", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-wall-count", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-xy-min", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-xy-max", type=float, default=0.0040)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-z-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-z-max", type=float, default=0.040)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-contact-max", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-margin-min", type=float, default=-1.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-yaw-max-deg", type=float, default=2.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-tilt-max-deg", type=float, default=2.5)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-max-phase-steps", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-min-soft-hold-attempts", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-soft-hold-first-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-steps", type=int, default=3)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-wall-count", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-xy-min", type=float, default=0.009)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-xy-max", type=float, default=0.014)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-z-min", type=float, default=0.030)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-z-max", type=float, default=0.037)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-contact-max", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-margin-min", type=float, default=-1.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-yaw-max-deg", type=float, default=1.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-tilt-max-deg", type=float, default=3.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-max-phase-steps", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-min-soft-hold-attempts", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-max-attempts", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-max-up-action", type=float, default=0.0005)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-xy-min", type=float, default=0.018)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-xy-max", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-z-min", type=float, default=0.035)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-z-max", type=float, default=0.050)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-margin-min", type=float, default=-0.0015)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-topdown-margin-min", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-yaw-max-deg", type=float, default=1.25)
    parser.add_argument("--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-tilt-max-deg", type=float, default=3.2)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-finish-continue-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-late-finish-continue-min-steps-since-reset", type=int, default=850)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-finish-continue-xy-max", type=float, default=0.0030)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-finish-continue-z-min", type=float, default=0.018)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-finish-continue-z-max", type=float, default=0.034)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-finish-continue-margin-min", type=float, default=0.0002)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-finish-continue-topdown-margin-min", type=float, default=-1.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-finish-continue-yaw-max-deg", type=float, default=1.5)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-finish-continue-tilt-max-deg", type=float, default=2.0)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-finish-continue-contact-max", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-escape-veto-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-fast-settle-late-escape-veto-min-steps-since-reset", type=int, default=900)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-escape-veto-xy-max", type=float, default=0.012)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-escape-veto-z-min", type=float, default=0.036)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-escape-veto-z-max", type=float, default=0.040)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-escape-veto-contact-max", type=int, default=0)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-escape-veto-margin-min", type=float, default=-0.0010)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-escape-veto-topdown-margin-min", type=float, default=0.0005)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-escape-veto-yaw-max-deg", type=float, default=1.5)
    parser.add_argument("--guard-final-servo-square-fast-settle-late-escape-veto-tilt-max-deg", type=float, default=1.6)
    parser.add_argument("--guard-final-servo-square-contact-brake-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-contact-brake-wall-steps", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-contact-brake-xy-max", type=float, default=0.008)
    parser.add_argument("--guard-final-servo-square-contact-brake-z-min", type=float, default=0.020)
    parser.add_argument("--guard-final-servo-square-contact-brake-z-max", type=float, default=0.045)
    parser.add_argument("--guard-final-servo-square-contact-brake-lift-height", type=float, default=0.012)
    parser.add_argument("--guard-final-servo-square-contact-brake-lift-z-max", type=float, default=0.060)
    parser.add_argument("--guard-final-servo-square-contact-brake-release-xy", type=float, default=0.005)
    parser.add_argument("--guard-final-servo-square-contact-brake-stable-steps", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-contact-brake-max-steps", type=int, default=50)
    parser.add_argument("--guard-final-servo-square-contact-brake-max-attempts", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-contact-brake-max-xy-action", type=float, default=0.003)
    parser.add_argument("--guard-final-servo-square-contact-brake-max-up-action", type=float, default=0.003)
    parser.add_argument("--guard-final-servo-square-contact-brake-max-clearance", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-contact-brake-margin-threshold", type=float, default=0.0)
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-require-bad-margin",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-repeat-margin-gate-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-repeat-margin-threshold",
        type=float,
        default=-0.0010,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-release-flush-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-release-flush-steps",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-release-flush-min-brake-attempts",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-release-flush-min-steps-since-reset",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-release-flush-xy-max",
        type=float,
        default=0.0040,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-release-flush-z-min",
        type=float,
        default=0.020,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-release-flush-z-max",
        type=float,
        default=0.035,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-release-flush-contact-max",
        type=int,
        default=8,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-escape-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-reset-attempts-after-escape-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-continue-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-continue-min-steps-since-reset",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-continue-xy-max",
        type=float,
        default=0.010,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-continue-z-min",
        type=float,
        default=0.020,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-continue-z-max",
        type=float,
        default=0.045,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-continue-contact-max",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-continue-tilt-max-deg",
        type=float,
        default=8.0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-continue-margin-min",
        type=float,
        default=-0.0015,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-continue-topdown-margin-min",
        type=float,
        default=-1.0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-exhausted-continue-yaw-max-deg",
        type=float,
        default=180.0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-wall-steps",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-steps",
        type=int,
        default=8,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-min-brake-attempts",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-xy-max",
        type=float,
        default=0.004,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-z-min",
        type=float,
        default=0.020,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-z-max",
        type=float,
        default=0.040,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-max-up-action",
        type=float,
        default=0.003,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-max-clearance",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-margin-threshold",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-require-bad-margin",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-yaw-min-deg",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-expanded-xy-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-expanded-xy-max",
        type=float,
        default=0.008,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-expanded-z-min",
        type=float,
        default=0.034,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-expanded-margin-min",
        type=float,
        default=-0.0005,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-expanded-yaw-max-deg",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-max-brake-attempts",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-contact-max",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-xy-max",
        type=float,
        default=0.0045,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-z-min",
        type=float,
        default=0.020,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-z-max",
        type=float,
        default=0.045,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-margin-min",
        type=float,
        default=0.0002,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-tilt-max-deg",
        type=float,
        default=2.0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-min-phase-steps",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-xy-min",
        type=float,
        default=0.010,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-xy-max",
        type=float,
        default=0.026,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-z-min",
        type=float,
        default=0.036,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-z-max",
        type=float,
        default=0.045,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-contact-max",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-margin-min",
        type=float,
        default=-0.0035,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-topdown-margin-min",
        type=float,
        default=0.0005,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-yaw-max-deg",
        type=float,
        default=1.25,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-tilt-max-deg",
        type=float,
        default=4.6,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-enabled",
        action="store_true",
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-min-brake-attempts",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-min-phase-steps",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-min-steps-since-reset",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-contact-max",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-xy-max",
        type=float,
        default=0.0030,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-z-min",
        type=float,
        default=0.020,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-z-max",
        type=float,
        default=0.045,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-margin-min",
        type=float,
        default=0.0002,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-yaw-max-deg",
        type=float,
        default=1.5,
    )
    parser.add_argument(
        "--guard-final-servo-square-contact-brake-late-lift-release-tilt-max-deg",
        type=float,
        default=2.0,
    )
    parser.add_argument("--guard-final-servo-square-high-z-descend-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-high-z-descend-stall-steps", type=int, default=18)
    parser.add_argument("--guard-final-servo-square-high-z-descend-xy-max", type=float, default=0.0055)
    parser.add_argument("--guard-final-servo-square-high-z-descend-z-min", type=float, default=0.026)
    parser.add_argument("--guard-final-servo-square-high-z-descend-z-max", type=float, default=0.045)
    parser.add_argument("--guard-final-servo-square-high-z-descend-contact-max", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-high-z-descend-tilt-max-deg", type=float, default=3.0)
    parser.add_argument("--guard-final-servo-square-high-z-descend-margin-min", type=float, default=-0.0015)
    parser.add_argument("--guard-final-servo-square-high-z-descend-max-steps", type=int, default=90)
    parser.add_argument("--guard-final-servo-square-high-z-descend-max-xy-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-high-z-descend-max-down-action", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-square-high-z-descend-low-z-threshold", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-high-z-descend-low-z-max-xy-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-high-z-descend-staged-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-high-z-descend-mid-z-threshold", type=float, default=0.034)
    parser.add_argument("--guard-final-servo-square-high-z-descend-mid-z-max-xy-action", type=float, default=0.0010)
    parser.add_argument("--guard-final-servo-square-high-z-descend-mid-z-max-down-action", type=float, default=0.0015)
    parser.add_argument("--guard-final-servo-square-high-z-descend-low-z-max-down-action", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-high-z-descend-low-z-hold-steps", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-high-z-descend-low-z-hold-min-phase-steps", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-high-z-descend-low-z-hold-max-attempts", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-high-z-descend-low-z-hold-xy-max", type=float, default=0.0055)
    parser.add_argument("--guard-final-servo-square-high-z-descend-low-z-hold-max-up-action", type=float, default=0.003)
    parser.add_argument("--guard-final-servo-square-high-z-descend-contact-brake-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-high-z-descend-contact-brake-wall-count", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-high-z-descend-contact-brake-z-max", type=float, default=0.030)
    parser.add_argument("--guard-final-servo-square-high-z-descend-contact-brake-xy-max", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-stall-steps", type=int, default=12)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-xy-max", type=float, default=0.008)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-z-min", type=float, default=0.026)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-z-max", type=float, default=0.045)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-contact-max", type=int, default=8)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-margin-threshold", type=float, default=0.0)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-yaw-deg", type=float, default=4.0)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-release-xy", type=float, default=0.0048)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-lift-height", type=float, default=0.018)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-stable-steps", type=int, default=3)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-max-steps", type=int, default=60)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-max-attempts", type=int, default=1)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-max-xy-action", type=float, default=0.003)
    parser.add_argument("--guard-final-servo-square-margin-yaw-settle-max-up-action", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-wall-steps", type=int, default=4)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-stall-steps", type=int, default=16)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-tilt-deg", type=float, default=9.0)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-margin-threshold", type=float, default=-0.003)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-xy-max", type=float, default=0.008)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-z-min", type=float, default=0.012)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-z-max", type=float, default=0.060)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-lift-height", type=float, default=0.010)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-release-xy", type=float, default=0.0048)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-release-tilt-deg", type=float, default=8.0)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-stable-steps", type=int, default=3)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-max-steps", type=int, default=40)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-max-attempts", type=int, default=2)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-max-xy-action", type=float, default=0.003)
    parser.add_argument("--guard-final-servo-square-tilt-reinsert-max-up-action", type=float, default=0.0025)
    parser.add_argument(
        "--guarded-oracle-mode",
        choices=[
            "guarded_two_stage",
            "high_start_two_phase",
            "contact_aware_recovery",
            "timeout_descent_progress",
        ],
        default="guarded_two_stage",
    )
    parser.add_argument("--guard-action-gain", type=float, default=1.0)
    parser.add_argument("--guarded-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guarded-max-down-action", type=float, default=0.0035)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.005)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)
    parser.add_argument("--guarded-hold-z-until-insert", action="store_true")
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
    return parser


def parse_args() -> argparse.Namespace:
    return parse_args_with_config(build_parser())


def validate_ordered_pair(
    name: str,
    values: tuple[float, float] | list[float] | tuple[int, int] | list[int] | None,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
    allow_equal: bool = True,
) -> None:
    if values is None:
        return
    if len(values) != 2:
        raise ValueError(f"{name} requires two values.")
    low, high = values
    if allow_equal:
        ordered = low <= high
        relation = "<="
    else:
        ordered = low < high
        relation = "<"
    if not ordered:
        raise ValueError(f"{name} must satisfy low {relation} high.")
    if min_value is not None and (low < min_value or high < min_value):
        raise ValueError(f"{name} values must be >= {min_value}.")
    if max_value is not None and (low > max_value or high > max_value):
        raise ValueError(f"{name} values must be <= {max_value}.")


def make_env(args: argparse.Namespace, scenario: Scenario) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode=args.observation_mode,
        image_width=args.width,
        image_height=args.height,
        include_near_hole_crop=args.include_near_hole_crop,
        near_hole_crop_size=args.near_hole_crop_size,
        near_hole_crop_source_size=args.near_hole_crop_source_size,
        near_hole_crop_source_size_range=(
            tuple(args.near_hole_crop_source_size_range)
            if args.near_hole_crop_source_size_range is not None
            else None
        ),
        near_hole_crop_offset=tuple(args.near_hole_crop_offset),
        include_control_state=args.include_control_state,
        image_frame_stack=args.image_frame_stack,
        wrist_camera_pos_offset=tuple(args.wrist_camera_pos_offset),
        wrist_camera_rot_offset_deg=tuple(args.wrist_camera_rot_offset_deg),
        wrist_camera_fovy=args.wrist_camera_fovy,
        max_steps=args.max_steps,
        frame_skip=args.frame_skip,
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
        success_shape_yaw_tolerance_deg=args.success_shape_yaw_tolerance_deg,
        success_shape_yaw_profiles=tuple(args.success_shape_yaw_profiles),
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
        geometry_hole_center_xy_jitter=(
            tuple(args.geometry_hole_center_xy_jitter)
            if args.geometry_hole_center_xy_jitter is not None
            else scenario.geometry_hole_center_xy_jitter
        ),
        geometry_fixture_height_jitter=(
            args.geometry_fixture_height_jitter
            if args.geometry_fixture_height_jitter is not None
            else scenario.geometry_fixture_height_jitter
        ),
        geometry_table_height_jitter=(
            args.geometry_table_height_jitter
            if args.geometry_table_height_jitter is not None
            else scenario.geometry_table_height_jitter
        ),
        geometry_hole_half_size_range=tuple(args.geometry_hole_half_size_range),
        geometry_peg_radius_range=tuple(args.geometry_peg_radius_range),
        geometry_profile=args.geometry_profile,
        geometry_fixture_mode=args.geometry_fixture_mode,
        geometry_true_fixture_variant=args.geometry_true_fixture_variant,
        enable_peg_tip_visual_helpers=bool(args.enable_peg_tip_visual_helpers),
        geometry_square_peg_half_size_range=tuple(args.geometry_square_peg_half_size_range),
        geometry_mixed_square_probability=args.geometry_mixed_square_probability,
        contact_friction_multiplier_range=scenario.contact_friction_multiplier_range,
        contact_solref_time_multiplier_range=scenario.contact_solref_time_multiplier_range,
        contact_solref_damping_multiplier_range=scenario.contact_solref_damping_multiplier_range,
        contact_solimp_width_multiplier_range=scenario.contact_solimp_width_multiplier_range,
        dynamics_joint_damping_multiplier_range=scenario.dynamics_joint_damping_multiplier_range,
        dynamics_actuator_kp_multiplier_range=scenario.dynamics_actuator_kp_multiplier_range,
        nominal_joint_damping_multiplier=args.nominal_joint_damping_multiplier,
        nominal_actuator_kp_multiplier=args.nominal_actuator_kp_multiplier,
    )


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
        guard_retry_enabled=args.guard_retry_enabled,
        guard_retry_stall_steps=args.guard_retry_stall_steps,
        guard_retry_xy_tolerance=args.guard_retry_xy_tolerance,
        guard_retry_z_max=args.guard_retry_z_max,
        guard_retry_lift_height=args.guard_retry_lift_height,
        guard_retry_release_xy=args.guard_retry_release_xy,
        guard_retry_max_attempts=args.guard_retry_max_attempts,
        guard_retry_max_steps=args.guard_retry_max_steps,
        guard_insert_latch_enabled=args.guard_insert_latch_enabled,
        guard_insert_latch_xy_tolerance=args.guard_insert_latch_xy_tolerance,
        guard_insert_latch_release_xy=args.guard_insert_latch_release_xy,
        guard_insert_latch_resume_xy=args.guard_insert_latch_resume_xy,
        guard_insert_latch_recenter_height=args.guard_insert_latch_recenter_height,
        guard_insert_latch_recenter_z_tolerance=args.guard_insert_latch_recenter_z_tolerance,
        guard_insert_latch_max_down_action=args.guard_insert_latch_max_down_action,
        guard_hover_enabled=args.guard_hover_enabled,
        guard_hover_xy_tolerance=args.guard_hover_xy_tolerance,
        guard_hover_release_xy=args.guard_hover_release_xy,
        guard_hover_height=args.guard_hover_height,
        guard_hover_z_tolerance=args.guard_hover_z_tolerance,
        guard_hover_required_steps=args.guard_hover_required_steps,
        guard_hover_max_down_action=args.guard_hover_max_down_action,
        guard_near_action_scale_enabled=args.guard_near_action_scale_enabled,
        guard_near_action_xy_tolerance=args.guard_near_action_xy_tolerance,
        guard_near_action_z_threshold=args.guard_near_action_z_threshold,
        guard_near_max_xy_action=args.guard_near_max_xy_action,
        guard_near_max_down_action=args.guard_near_max_down_action,
        guard_fixture_clearance_enabled=args.guard_fixture_clearance_enabled,
        guard_fixture_clearance_xy_min=args.guard_fixture_clearance_xy_min,
        guard_fixture_clearance_xy_max=args.guard_fixture_clearance_xy_max,
        guard_fixture_clearance_z_max=args.guard_fixture_clearance_z_max,
        guard_fixture_clearance_lift_height=args.guard_fixture_clearance_lift_height,
        guard_fixture_clearance_max_up_action=args.guard_fixture_clearance_max_up_action,
        guard_fixture_clearance_realign_enabled=args.guard_fixture_clearance_realign_enabled,
        guard_fixture_clearance_realign_start_z=args.guard_fixture_clearance_realign_start_z,
        guard_fixture_clearance_realign_xy=args.guard_fixture_clearance_realign_xy,
        guard_fixture_clearance_max_xy_action=args.guard_fixture_clearance_max_xy_action,
        guard_fixture_clearance_max_down_action=args.guard_fixture_clearance_max_down_action,
        guard_fixture_clearance_max_steps=args.guard_fixture_clearance_max_steps,
        guard_fixture_clearance_retreat_enabled=args.guard_fixture_clearance_retreat_enabled,
        guard_fixture_clearance_retreat_release_xy=args.guard_fixture_clearance_retreat_release_xy,
        guard_fixture_clearance_retreat_max_xy_action=args.guard_fixture_clearance_retreat_max_xy_action,
        guard_preinsert_recenter_enabled=args.guard_preinsert_recenter_enabled,
        guard_preinsert_recenter_start_z=args.guard_preinsert_recenter_start_z,
        guard_preinsert_recenter_min_z=args.guard_preinsert_recenter_min_z,
        guard_preinsert_recenter_trigger_xy=args.guard_preinsert_recenter_trigger_xy,
        guard_preinsert_recenter_stable_xy=args.guard_preinsert_recenter_stable_xy,
        guard_preinsert_recenter_height=args.guard_preinsert_recenter_height,
        guard_preinsert_recenter_z_tolerance=args.guard_preinsert_recenter_z_tolerance,
        guard_preinsert_recenter_stable_steps=args.guard_preinsert_recenter_stable_steps,
        guard_preinsert_recenter_max_steps=args.guard_preinsert_recenter_max_steps,
        guard_preinsert_recenter_max_xy_action=args.guard_preinsert_recenter_max_xy_action,
        guard_preinsert_recenter_max_up_action=args.guard_preinsert_recenter_max_up_action,
        guard_preinsert_recenter_lift_before_lateral=(
            args.guard_preinsert_recenter_lift_before_lateral
        ),
        guard_approach_recenter_enabled=args.guard_approach_recenter_enabled,
        guard_approach_recenter_requires_stateful_recovery=(
            args.guard_approach_recenter_requires_stateful_recovery
        ),
        guard_approach_recenter_start_z=args.guard_approach_recenter_start_z,
        guard_approach_recenter_min_z=args.guard_approach_recenter_min_z,
        guard_approach_recenter_trigger_xy=args.guard_approach_recenter_trigger_xy,
        guard_approach_recenter_max_xy=args.guard_approach_recenter_max_xy,
        guard_approach_recenter_stable_xy=args.guard_approach_recenter_stable_xy,
        guard_approach_recenter_height=args.guard_approach_recenter_height,
        guard_approach_recenter_z_tolerance=args.guard_approach_recenter_z_tolerance,
        guard_approach_recenter_stable_steps=args.guard_approach_recenter_stable_steps,
        guard_approach_recenter_max_steps=args.guard_approach_recenter_max_steps,
        guard_approach_recenter_max_xy_action=args.guard_approach_recenter_max_xy_action,
        guard_approach_recenter_max_up_action=args.guard_approach_recenter_max_up_action,
        guard_approach_recenter_xy_bias=tuple(args.guard_approach_recenter_xy_bias),
        guard_early_approach_assist_enabled=args.guard_early_approach_assist_enabled,
        guard_early_approach_assist_trigger_xy=(
            args.guard_early_approach_assist_trigger_xy
        ),
        guard_early_approach_assist_release_xy=(
            args.guard_early_approach_assist_release_xy
        ),
        guard_early_approach_assist_min_z=args.guard_early_approach_assist_min_z,
        guard_early_approach_assist_max_z=args.guard_early_approach_assist_max_z,
        guard_early_approach_assist_target_height=(
            args.guard_early_approach_assist_target_height
        ),
        guard_early_approach_assist_max_xy_action=(
            args.guard_early_approach_assist_max_xy_action
        ),
        guard_early_approach_assist_max_up_action=(
            args.guard_early_approach_assist_max_up_action
        ),
        guard_early_approach_assist_max_steps=(
            args.guard_early_approach_assist_max_steps
        ),
        guard_stateful_recovery_enabled=args.guard_stateful_recovery_enabled,
        guard_stateful_recovery_trigger_xy_min=args.guard_stateful_recovery_trigger_xy_min,
        guard_stateful_recovery_trigger_xy_max=args.guard_stateful_recovery_trigger_xy_max,
        guard_stateful_recovery_trigger_z_max=args.guard_stateful_recovery_trigger_z_max,
        guard_stateful_recovery_lift_height=args.guard_stateful_recovery_lift_height,
        guard_stateful_recovery_lift_z_tolerance=args.guard_stateful_recovery_lift_z_tolerance,
        guard_stateful_recovery_release_xy=args.guard_stateful_recovery_release_xy,
        guard_stateful_recovery_resume_xy=args.guard_stateful_recovery_resume_xy,
        guard_stateful_recovery_resume_z=args.guard_stateful_recovery_resume_z,
        guard_stateful_recovery_stable_steps=args.guard_stateful_recovery_stable_steps,
        guard_stateful_recovery_stall_steps=args.guard_stateful_recovery_stall_steps,
        guard_stateful_recovery_min_xy_progress=args.guard_stateful_recovery_min_xy_progress,
        guard_stateful_recovery_min_actual_xy_motion=(
            args.guard_stateful_recovery_min_actual_xy_motion
        ),
        guard_stateful_recovery_min_command_xy=args.guard_stateful_recovery_min_command_xy,
        guard_stateful_recovery_max_attempts=args.guard_stateful_recovery_max_attempts,
        guard_stateful_recovery_max_steps=args.guard_stateful_recovery_max_steps,
        guard_stateful_recovery_max_xy_action=args.guard_stateful_recovery_max_xy_action,
        guard_stateful_recovery_max_down_action=args.guard_stateful_recovery_max_down_action,
        guard_stateful_recovery_max_up_action=args.guard_stateful_recovery_max_up_action,
        guard_final_servo_enabled=args.guard_final_servo_enabled,
        guard_final_servo_start_xy=args.guard_final_servo_start_xy,
        guard_final_servo_start_z=args.guard_final_servo_start_z,
        guard_final_servo_min_start_z=args.guard_final_servo_min_start_z,
        guard_final_servo_hover_height=args.guard_final_servo_hover_height,
        guard_final_servo_hover_z_tolerance=args.guard_final_servo_hover_z_tolerance,
        guard_final_servo_stable_xy=args.guard_final_servo_stable_xy,
        guard_final_servo_descent_start_xy=args.guard_final_servo_descent_start_xy,
        guard_final_servo_stable_steps=args.guard_final_servo_stable_steps,
        guard_final_servo_release_xy=args.guard_final_servo_release_xy,
        guard_final_servo_align_timeout_steps=(
            args.guard_final_servo_align_timeout_steps
        ),
        guard_final_servo_align_timeout_xy=args.guard_final_servo_align_timeout_xy,
        guard_final_servo_align_hover_escape_enabled=(
            args.guard_final_servo_align_hover_escape_enabled
        ),
        guard_final_servo_align_hover_escape_steps=(
            args.guard_final_servo_align_hover_escape_steps
        ),
        guard_final_servo_align_hover_escape_xy=(
            args.guard_final_servo_align_hover_escape_xy
        ),
        guard_final_servo_align_hover_escape_min_z=(
            args.guard_final_servo_align_hover_escape_min_z
        ),
        guard_final_servo_align_hover_escape_max_z=(
            args.guard_final_servo_align_hover_escape_max_z
        ),
        guard_final_servo_rearm_enabled=args.guard_final_servo_rearm_enabled,
        guard_final_servo_rearm_cooldown_steps=(
            args.guard_final_servo_rearm_cooldown_steps
        ),
        guard_final_servo_rearm_stable_steps=(
            args.guard_final_servo_rearm_stable_steps
        ),
        guard_final_servo_rearm_xy_max=args.guard_final_servo_rearm_xy_max,
        guard_final_servo_rearm_z_min=args.guard_final_servo_rearm_z_min,
        guard_final_servo_rearm_z_max=args.guard_final_servo_rearm_z_max,
        guard_final_servo_rearm_contact_max=(
            args.guard_final_servo_rearm_contact_max
        ),
        guard_final_servo_rearm_tilt_max_deg=(
            args.guard_final_servo_rearm_tilt_max_deg
        ),
        guard_final_servo_rearm_margin_min=args.guard_final_servo_rearm_margin_min,
        guard_final_servo_rearm_max_attempts=(
            args.guard_final_servo_rearm_max_attempts
        ),
        guard_final_servo_priority_over_fixture_clearance=(
            args.guard_final_servo_priority_over_fixture_clearance
        ),
        guard_final_servo_max_xy_action=args.guard_final_servo_max_xy_action,
        guard_final_servo_max_down_action=args.guard_final_servo_max_down_action,
        guard_final_servo_low_recenter_enabled=args.guard_final_servo_low_recenter_enabled,
        guard_final_servo_low_recenter_z_max=args.guard_final_servo_low_recenter_z_max,
        guard_final_servo_low_recenter_trigger_xy=(
            args.guard_final_servo_low_recenter_trigger_xy
        ),
        guard_final_servo_low_recenter_release_xy=(
            args.guard_final_servo_low_recenter_release_xy
        ),
        guard_final_servo_low_recenter_height=args.guard_final_servo_low_recenter_height,
        guard_final_servo_low_recenter_stable_steps=(
            args.guard_final_servo_low_recenter_stable_steps
        ),
        guard_final_servo_low_recenter_max_steps=(
            args.guard_final_servo_low_recenter_max_steps
        ),
        guard_final_servo_low_recenter_max_up_action=(
            args.guard_final_servo_low_recenter_max_up_action
        ),
        guard_final_servo_low_recenter_stall_steps=(
            args.guard_final_servo_low_recenter_stall_steps
        ),
        guard_final_servo_low_recenter_min_xy_progress=(
            args.guard_final_servo_low_recenter_min_xy_progress
        ),
        guard_final_servo_descend_xy_bias=tuple(args.guard_final_servo_descend_xy_bias),
        guard_final_servo_descend_xy_bias_max_clearance=(
            args.guard_final_servo_descend_xy_bias_max_clearance
        ),
        guard_final_servo_descend_xy_bias_requires_stateful_recovery=(
            args.guard_final_servo_descend_xy_bias_requires_stateful_recovery
        ),
        guard_final_servo_lift_height=args.guard_final_servo_lift_height,
        guard_final_servo_stall_steps=args.guard_final_servo_stall_steps,
        guard_final_servo_min_z_progress=args.guard_final_servo_min_z_progress,
        guard_final_servo_max_retries=args.guard_final_servo_max_retries,
        guard_final_servo_max_recovery_steps=args.guard_final_servo_max_recovery_steps,
        guard_final_servo_recovery_mode=args.guard_final_servo_recovery_mode,
        guard_final_servo_soft_unjam_lift=args.guard_final_servo_soft_unjam_lift,
        guard_final_servo_soft_unjam_min_height=args.guard_final_servo_soft_unjam_min_height,
        guard_final_servo_soft_unjam_z_tolerance=args.guard_final_servo_soft_unjam_z_tolerance,
        guard_final_servo_soft_unjam_hold_steps=args.guard_final_servo_soft_unjam_hold_steps,
        guard_final_servo_soft_unjam_max_up_action=args.guard_final_servo_soft_unjam_max_up_action,
        guard_final_servo_square_recovery_enabled=(
            args.guard_final_servo_square_recovery_enabled
        ),
        guard_final_servo_square_recovery_tilt_deg=(
            args.guard_final_servo_square_recovery_tilt_deg
        ),
        guard_final_servo_square_recovery_tilt_steps=(
            args.guard_final_servo_square_recovery_tilt_steps
        ),
        guard_final_servo_square_recovery_z_max=(
            args.guard_final_servo_square_recovery_z_max
        ),
        guard_final_servo_square_recovery_xy_max=(
            args.guard_final_servo_square_recovery_xy_max
        ),
        guard_final_servo_square_recovery_lift_height=(
            args.guard_final_servo_square_recovery_lift_height
        ),
        guard_final_servo_square_recovery_escape_enabled=(
            args.guard_final_servo_square_recovery_escape_enabled
        ),
        guard_final_servo_square_recovery_escape_xy=(
            args.guard_final_servo_square_recovery_escape_xy
        ),
        guard_final_servo_square_recovery_escape_z_min=(
            args.guard_final_servo_square_recovery_escape_z_min
        ),
        guard_final_servo_square_recovery_escape_z_max=(
            args.guard_final_servo_square_recovery_escape_z_max
        ),
        guard_final_servo_square_recovery_escape_height=(
            args.guard_final_servo_square_recovery_escape_height
        ),
        guard_final_servo_square_recovery_escape_late_height_enabled=(
            args.guard_final_servo_square_recovery_escape_late_height_enabled
        ),
        guard_final_servo_square_recovery_escape_late_height=(
            args.guard_final_servo_square_recovery_escape_late_height
        ),
        guard_final_servo_square_recovery_escape_late_height_min_steps_since_reset=(
            args.guard_final_servo_square_recovery_escape_late_height_min_steps_since_reset
        ),
        guard_final_servo_square_recovery_escape_release_xy=(
            args.guard_final_servo_square_recovery_escape_release_xy
        ),
        guard_final_servo_square_recovery_escape_late_release_xy=(
            args.guard_final_servo_square_recovery_escape_late_release_xy
        ),
        guard_final_servo_square_recovery_escape_late_release_min_steps_since_reset=(
            args.guard_final_servo_square_recovery_escape_late_release_min_steps_since_reset
        ),
        guard_final_servo_square_recovery_escape_max_steps=(
            args.guard_final_servo_square_recovery_escape_max_steps
        ),
        guard_final_servo_square_recovery_escape_max_xy_action=(
            args.guard_final_servo_square_recovery_escape_max_xy_action
        ),
        guard_final_servo_square_recovery_escape_max_up_action=(
            args.guard_final_servo_square_recovery_escape_max_up_action
        ),
        guard_final_servo_square_recovery_escape_max_clearance=(
            args.guard_final_servo_square_recovery_escape_max_clearance
        ),
        guard_final_servo_square_recovery_escape_early_contact_enabled=(
            args.guard_final_servo_square_recovery_escape_early_contact_enabled
        ),
        guard_final_servo_square_recovery_escape_early_contact_wall_steps=(
            args.guard_final_servo_square_recovery_escape_early_contact_wall_steps
        ),
        guard_final_servo_square_recovery_escape_early_contact_xy_max=(
            args.guard_final_servo_square_recovery_escape_early_contact_xy_max
        ),
        guard_final_servo_square_recovery_escape_early_contact_z_min=(
            args.guard_final_servo_square_recovery_escape_early_contact_z_min
        ),
        guard_final_servo_square_recovery_escape_early_contact_z_max=(
            args.guard_final_servo_square_recovery_escape_early_contact_z_max
        ),
        guard_final_servo_square_recovery_escape_early_contact_margin_threshold=(
            args.guard_final_servo_square_recovery_escape_early_contact_margin_threshold
        ),
        guard_final_servo_square_recovery_escape_early_contact_require_bad_margin=(
            args.guard_final_servo_square_recovery_escape_early_contact_require_bad_margin
        ),
        guard_final_servo_square_recovery_escape_early_risk_enabled=(
            args.guard_final_servo_square_recovery_escape_early_risk_enabled
        ),
        guard_final_servo_square_recovery_escape_early_risk_steps=(
            args.guard_final_servo_square_recovery_escape_early_risk_steps
        ),
        guard_final_servo_square_recovery_escape_early_risk_xy_max=(
            args.guard_final_servo_square_recovery_escape_early_risk_xy_max
        ),
        guard_final_servo_square_recovery_escape_early_risk_z_min=(
            args.guard_final_servo_square_recovery_escape_early_risk_z_min
        ),
        guard_final_servo_square_recovery_escape_early_risk_z_max=(
            args.guard_final_servo_square_recovery_escape_early_risk_z_max
        ),
        guard_final_servo_square_recovery_escape_early_risk_margin_threshold=(
            args.guard_final_servo_square_recovery_escape_early_risk_margin_threshold
        ),
        guard_final_servo_square_recovery_escape_pre_lift_steps=(
            args.guard_final_servo_square_recovery_escape_pre_lift_steps
        ),
        guard_final_servo_square_recovery_escape_pre_lift_on_trigger=(
            args.guard_final_servo_square_recovery_escape_pre_lift_on_trigger
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_enabled=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_enabled
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_xy_max=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_xy_max
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_z_min=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_z_min
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_z_max=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_z_max
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_contact_max=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_contact_max
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_max_steps=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_steps
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_min_steps_since_reset=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_min_steps_since_reset
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_max_steps_since_reset=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_steps_since_reset
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_from_escape_enabled=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_from_escape_enabled
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_from_escape_min_phase_steps=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_from_escape_min_phase_steps
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_max_down_action=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_down_action
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_max_down_z_min=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_down_z_min
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_max_xy_action=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_xy_action
        ),
        guard_final_servo_square_recovery_escape_direct_fast_settle_fast_down_margin_min=(
            args.guard_final_servo_square_recovery_escape_direct_fast_settle_fast_down_margin_min
        ),
        guard_final_servo_square_recovery_escape_recenter_no_up_enabled=(
            args.guard_final_servo_square_recovery_escape_recenter_no_up_enabled
        ),
        guard_final_servo_square_recovery_escape_recenter_descend_enabled=(
            args.guard_final_servo_square_recovery_escape_recenter_descend_enabled
        ),
        guard_final_servo_square_recovery_escape_recenter_descend_xy_max=(
            args.guard_final_servo_square_recovery_escape_recenter_descend_xy_max
        ),
        guard_final_servo_square_recovery_escape_recenter_descend_z_min=(
            args.guard_final_servo_square_recovery_escape_recenter_descend_z_min
        ),
        guard_final_servo_square_recovery_escape_recenter_descend_z_max=(
            args.guard_final_servo_square_recovery_escape_recenter_descend_z_max
        ),
        guard_final_servo_square_recovery_escape_recenter_descend_contact_max=(
            args.guard_final_servo_square_recovery_escape_recenter_descend_contact_max
        ),
        guard_final_servo_square_recovery_escape_recenter_descend_margin_min=(
            args.guard_final_servo_square_recovery_escape_recenter_descend_margin_min
        ),
        guard_final_servo_square_recovery_escape_recenter_descend_max_down_action=(
            args.guard_final_servo_square_recovery_escape_recenter_descend_max_down_action
        ),
        guard_final_servo_square_recovery_escape_recenter_drift_lift_enabled=(
            args.guard_final_servo_square_recovery_escape_recenter_drift_lift_enabled
        ),
        guard_final_servo_square_recovery_escape_recenter_drift_lift_min_phase_steps=(
            args.guard_final_servo_square_recovery_escape_recenter_drift_lift_min_phase_steps
        ),
        guard_final_servo_square_recovery_escape_recenter_drift_lift_xy_min=(
            args.guard_final_servo_square_recovery_escape_recenter_drift_lift_xy_min
        ),
        guard_final_servo_square_recovery_escape_recenter_drift_lift_z_min=(
            args.guard_final_servo_square_recovery_escape_recenter_drift_lift_z_min
        ),
        guard_final_servo_square_recovery_escape_recenter_drift_lift_z_max=(
            args.guard_final_servo_square_recovery_escape_recenter_drift_lift_z_max
        ),
        guard_final_servo_square_recovery_escape_recenter_drift_lift_contact_max=(
            args.guard_final_servo_square_recovery_escape_recenter_drift_lift_contact_max
        ),
        guard_final_servo_square_recovery_escape_recenter_drift_lift_yaw_min_deg=(
            args.guard_final_servo_square_recovery_escape_recenter_drift_lift_yaw_min_deg
        ),
        guard_final_servo_square_recovery_escape_recenter_drift_lift_tilt_min_deg=(
            args.guard_final_servo_square_recovery_escape_recenter_drift_lift_tilt_min_deg
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_enabled=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_enabled
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_min_steps_since_reset=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_min_steps_since_reset
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_min_phase_steps=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_min_phase_steps
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_xy_max=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_xy_max
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_z_min=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_z_min
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_z_max=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_z_max
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_contact_max=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_contact_max
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_margin_min=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_margin_min
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_margin_max=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_margin_max
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_tilt_max_deg=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_tilt_max_deg
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_max_down_action=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_max_down_action
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_max_xy_action=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_max_xy_action
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_hold_release_enabled=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_hold_release_enabled
        ),
        guard_final_servo_square_recovery_escape_late_recenter_descend_hold_z_min=(
            args.guard_final_servo_square_recovery_escape_late_recenter_descend_hold_z_min
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_enabled=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_enabled
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_steps_since_reset=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_steps_since_reset
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_phase_steps=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_phase_steps
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_brake_attempts=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_brake_attempts
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_xy_max=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_xy_max
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_z_min=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_z_min
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_z_max=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_z_max
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_contact_max=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_contact_max
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_margin_min=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_margin_min
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_topdown_margin_min=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_topdown_margin_min
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_yaw_max_deg=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_yaw_max_deg
        ),
        guard_final_servo_square_recovery_escape_late_clean_direct_finish_tilt_max_deg=(
            args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_tilt_max_deg
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_enabled=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_enabled
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_xy_min=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_xy_min
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_xy_max=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_xy_max
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_z_min=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_z_min
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_z_max=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_z_max
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_contact_max=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_contact_max
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_max_contact_pop_hold_attempts=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_max_contact_pop_hold_attempts
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_margin_min=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_margin_min
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_topdown_margin_min=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_topdown_margin_min
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_yaw_max_deg=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_yaw_max_deg
        ),
        guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_tilt_max_deg=(
            args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_tilt_max_deg
        ),
        guard_final_servo_split_recovery_enabled=(
            args.guard_final_servo_split_recovery_enabled
        ),
        guard_final_servo_contact_reinsert_enabled=(
            args.guard_final_servo_contact_reinsert_enabled
        ),
        guard_final_servo_contact_unjam_wall_steps=(
            args.guard_final_servo_contact_unjam_wall_steps
        ),
        guard_final_servo_contact_unjam_tilt_deg=(
            args.guard_final_servo_contact_unjam_tilt_deg
        ),
        guard_final_servo_contact_unjam_z_max=(
            args.guard_final_servo_contact_unjam_z_max
        ),
        guard_final_servo_contact_unjam_xy_max=(
            args.guard_final_servo_contact_unjam_xy_max
        ),
        guard_final_servo_contact_unjam_lift_height=(
            args.guard_final_servo_contact_unjam_lift_height
        ),
        guard_final_servo_contact_unjam_release_xy=(
            args.guard_final_servo_contact_unjam_release_xy
        ),
        guard_final_servo_contact_unjam_max_up_action=(
            args.guard_final_servo_contact_unjam_max_up_action
        ),
        guard_final_servo_contact_unjam_wall_bias=(
            args.guard_final_servo_contact_unjam_wall_bias
        ),
        guard_final_servo_contact_reinsert_orient_hold_enabled=(
            args.guard_final_servo_contact_reinsert_orient_hold_enabled
        ),
        guard_final_servo_contact_reinsert_orient_tilt_deg=(
            args.guard_final_servo_contact_reinsert_orient_tilt_deg
        ),
        guard_final_servo_contact_reinsert_orient_stable_steps=(
            args.guard_final_servo_contact_reinsert_orient_stable_steps
        ),
        guard_final_servo_contact_reinsert_orient_max_steps=(
            args.guard_final_servo_contact_reinsert_orient_max_steps
        ),
        guard_final_servo_contact_reinsert_orient_max_xy_action=(
            args.guard_final_servo_contact_reinsert_orient_max_xy_action
        ),
        guard_final_servo_contact_reinsert_orient_tip_lock_enabled=(
            args.guard_final_servo_contact_reinsert_orient_tip_lock_enabled
        ),
        guard_final_servo_contact_reinsert_orient_tip_lock_drift_gain=(
            args.guard_final_servo_contact_reinsert_orient_tip_lock_drift_gain
        ),
        guard_final_servo_contact_reinsert_orient_tip_lock_max_offset=(
            args.guard_final_servo_contact_reinsert_orient_tip_lock_max_offset
        ),
        guard_final_servo_contact_reinsert_high_reapproach_enabled=(
            args.guard_final_servo_contact_reinsert_high_reapproach_enabled
        ),
        guard_final_servo_contact_reinsert_high_reapproach_height=(
            args.guard_final_servo_contact_reinsert_high_reapproach_height
        ),
        guard_final_servo_contact_reinsert_high_reapproach_release_xy=(
            args.guard_final_servo_contact_reinsert_high_reapproach_release_xy
        ),
        guard_final_servo_contact_reinsert_high_reapproach_stable_steps=(
            args.guard_final_servo_contact_reinsert_high_reapproach_stable_steps
        ),
        guard_final_servo_contact_reinsert_high_reapproach_max_steps=(
            args.guard_final_servo_contact_reinsert_high_reapproach_max_steps
        ),
        guard_final_servo_contact_reinsert_high_reapproach_max_xy_action=(
            args.guard_final_servo_contact_reinsert_high_reapproach_max_xy_action
        ),
        guard_final_servo_contact_reinsert_high_reapproach_max_up_action=(
            args.guard_final_servo_contact_reinsert_high_reapproach_max_up_action
        ),
        guard_final_servo_contact_reinsert_descend_max_steps=(
            args.guard_final_servo_contact_reinsert_descend_max_steps
        ),
        guard_final_servo_contact_reinsert_micro_align_enabled=(
            args.guard_final_servo_contact_reinsert_micro_align_enabled
        ),
        guard_final_servo_contact_reinsert_micro_align_z_max=(
            args.guard_final_servo_contact_reinsert_micro_align_z_max
        ),
        guard_final_servo_contact_reinsert_micro_align_xy_max=(
            args.guard_final_servo_contact_reinsert_micro_align_xy_max
        ),
        guard_final_servo_contact_reinsert_micro_align_release_xy=(
            args.guard_final_servo_contact_reinsert_micro_align_release_xy
        ),
        guard_final_servo_contact_reinsert_micro_align_tilt_deg=(
            args.guard_final_servo_contact_reinsert_micro_align_tilt_deg
        ),
        guard_final_servo_contact_reinsert_micro_align_max_steps=(
            args.guard_final_servo_contact_reinsert_micro_align_max_steps
        ),
        guard_final_servo_contact_reinsert_micro_align_stall_steps=(
            args.guard_final_servo_contact_reinsert_micro_align_stall_steps
        ),
        guard_final_servo_contact_reinsert_micro_align_min_xy_progress=(
            args.guard_final_servo_contact_reinsert_micro_align_min_xy_progress
        ),
        guard_final_servo_contact_reinsert_micro_align_max_xy_action=(
            args.guard_final_servo_contact_reinsert_micro_align_max_xy_action
        ),
        guard_final_servo_contact_reinsert_micro_align_up_action=(
            args.guard_final_servo_contact_reinsert_micro_align_up_action
        ),
        guard_final_servo_near_miss_steps=args.guard_final_servo_near_miss_steps,
        guard_final_servo_near_miss_xy_max=args.guard_final_servo_near_miss_xy_max,
        guard_final_servo_near_miss_z_max=args.guard_final_servo_near_miss_z_max,
        guard_final_servo_near_miss_contact_max=(
            args.guard_final_servo_near_miss_contact_max
        ),
        guard_final_servo_near_miss_tilt_max_deg=(
            args.guard_final_servo_near_miss_tilt_max_deg
        ),
        guard_final_servo_near_miss_max_steps=args.guard_final_servo_near_miss_max_steps,
        guard_final_servo_near_miss_max_down_action=(
            args.guard_final_servo_near_miss_max_down_action
        ),
        guard_final_servo_near_miss_xy_bias=(
            tuple(args.guard_final_servo_near_miss_xy_bias)
        ),
        guard_final_servo_square_fast_settle_enabled=(
            args.guard_final_servo_square_fast_settle_enabled
        ),
        guard_final_servo_square_fast_settle_xy_max=(
            args.guard_final_servo_square_fast_settle_xy_max
        ),
        guard_final_servo_square_fast_settle_z_max=(
            args.guard_final_servo_square_fast_settle_z_max
        ),
        guard_final_servo_square_fast_settle_release_xy=(
            args.guard_final_servo_square_fast_settle_release_xy
        ),
        guard_final_servo_square_fast_settle_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_max=(
            args.guard_final_servo_square_fast_settle_contact_max
        ),
        guard_final_servo_square_fast_settle_max_steps=(
            args.guard_final_servo_square_fast_settle_max_steps
        ),
        guard_final_servo_square_fast_settle_max_xy_action=(
            args.guard_final_servo_square_fast_settle_max_xy_action
        ),
        guard_final_servo_square_fast_settle_low_z_max_xy_action=(
            args.guard_final_servo_square_fast_settle_low_z_max_xy_action
        ),
        guard_final_servo_square_fast_settle_low_z_threshold=(
            args.guard_final_servo_square_fast_settle_low_z_threshold
        ),
        guard_final_servo_square_fast_settle_low_z_max_down_action=(
            args.guard_final_servo_square_fast_settle_low_z_max_down_action
        ),
        guard_final_servo_square_fast_settle_low_z_down_threshold=(
            args.guard_final_servo_square_fast_settle_low_z_down_threshold
        ),
        guard_final_servo_square_fast_settle_max_down_action=(
            args.guard_final_servo_square_fast_settle_max_down_action
        ),
        guard_final_servo_square_fast_settle_contact_unjam_enabled=(
            args.guard_final_servo_square_fast_settle_contact_unjam_enabled
        ),
        guard_final_servo_square_fast_settle_late_down_boost_enabled=(
            args.guard_final_servo_square_fast_settle_late_down_boost_enabled
        ),
        guard_final_servo_square_fast_settle_late_down_boost_max_down_action=(
            args.guard_final_servo_square_fast_settle_late_down_boost_max_down_action
        ),
        guard_final_servo_square_fast_settle_late_down_boost_max_xy_action=(
            args.guard_final_servo_square_fast_settle_late_down_boost_max_xy_action
        ),
        guard_final_servo_square_fast_settle_late_down_boost_xy_max=(
            args.guard_final_servo_square_fast_settle_late_down_boost_xy_max
        ),
        guard_final_servo_square_fast_settle_late_down_boost_z_min=(
            args.guard_final_servo_square_fast_settle_late_down_boost_z_min
        ),
        guard_final_servo_square_fast_settle_late_down_boost_z_max=(
            args.guard_final_servo_square_fast_settle_late_down_boost_z_max
        ),
        guard_final_servo_square_fast_settle_late_down_boost_min_brake_attempts=(
            args.guard_final_servo_square_fast_settle_late_down_boost_min_brake_attempts
        ),
        guard_final_servo_square_fast_settle_late_down_boost_contact_max=(
            args.guard_final_servo_square_fast_settle_late_down_boost_contact_max
        ),
        guard_final_servo_square_fast_settle_late_down_boost_min_phase_steps=(
            args.guard_final_servo_square_fast_settle_late_down_boost_min_phase_steps
        ),
        guard_final_servo_square_fast_settle_late_down_boost_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_late_down_boost_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_late_down_boost_margin_min=(
            args.guard_final_servo_square_fast_settle_late_down_boost_margin_min
        ),
        guard_final_servo_square_fast_settle_late_down_boost_min_clean_steps=(
            args.guard_final_servo_square_fast_settle_late_down_boost_min_clean_steps
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_enabled=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_enabled
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_steps_since_reset=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_steps_since_reset
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_brake_attempts=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_brake_attempts
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_phase_steps=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_phase_steps
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_clean_steps=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_clean_steps
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_xy_max=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_xy_max
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_z_min=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_z_min
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_z_max=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_z_max
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_contact_max=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_contact_max
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_margin_min=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_margin_min
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_topdown_margin_min=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_topdown_margin_min
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_max_down_action=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_max_down_action
        ),
        guard_final_servo_square_fast_settle_very_late_clean_tail_boost_max_xy_action=(
            args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_max_xy_action
        ),
        guard_final_servo_square_fast_settle_low_z_contact_down_guard_enabled=(
            args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_enabled
        ),
        guard_final_servo_square_fast_settle_low_z_contact_down_guard_min_steps_since_reset=(
            args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_min_steps_since_reset
        ),
        guard_final_servo_square_fast_settle_low_z_contact_down_guard_wall_count=(
            args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_wall_count
        ),
        guard_final_servo_square_fast_settle_low_z_contact_down_guard_xy_max=(
            args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_xy_max
        ),
        guard_final_servo_square_fast_settle_low_z_contact_down_guard_z_max=(
            args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_z_max
        ),
        guard_final_servo_square_fast_settle_low_z_contact_down_guard_min_brake_attempts=(
            args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_min_brake_attempts
        ),
        guard_final_servo_square_fast_settle_low_z_contact_down_guard_max_up_action=(
            args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_max_up_action
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_enabled=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_enabled
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_steps=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_steps
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_wall_count=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_wall_count
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_xy_min=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_xy_min
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_xy_max=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_xy_max
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_z_min=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_z_min
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_z_max=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_z_max
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_contact_max=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_contact_max
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_min_phase_steps=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_min_phase_steps
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_min_brake_attempts=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_min_brake_attempts
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_max_attempts=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_max_attempts
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_max_up_action=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_max_up_action
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_enabled=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_enabled
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_min_phase_steps=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_min_phase_steps
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_xy_min=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_xy_min
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_xy_max=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_xy_max
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_z_min=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_z_min
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_z_max=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_z_max
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_contact_max=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_contact_max
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_topdown_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_topdown_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_pop_hold_recenter_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_enabled=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_enabled
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_min_attempts=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_min_attempts
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_xy_min=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_xy_min
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_xy_max=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_xy_max
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_z_min=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_z_min
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_z_max=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_z_max
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_contact_max=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_contact_max
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_topdown_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_topdown_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_enabled=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_enabled
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_steps=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_steps
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_xy_min=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_xy_min
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_xy_max=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_xy_max
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_z_min=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_z_min
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_z_max=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_z_max
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_contact_max=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_contact_max
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_min_brake_attempts=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_min_brake_attempts
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_max_contact_pop_hold_attempts=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_max_contact_pop_hold_attempts
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_min_contact_pop_hold_phase_steps=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_min_contact_pop_hold_phase_steps
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_max_attempts=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_max_attempts
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_margin_min=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_margin_min
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_topdown_margin_min=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_topdown_margin_min
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_no_contact_pop_hold_max_up_action=(
            args.guard_final_servo_square_fast_settle_no_contact_pop_hold_max_up_action
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_enabled=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_enabled
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_steps=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_steps
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_xy_max=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_xy_max
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_z_min=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_z_min
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_z_max=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_z_max
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_contact_max=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_contact_max
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_min_phase_steps=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_min_phase_steps
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_max_phase_steps=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_max_phase_steps
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_min_brake_attempts=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_min_brake_attempts
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_min_soft_hold_attempts=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_min_soft_hold_attempts
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_max_attempts=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_max_attempts
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_margin_min=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_margin_min
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_margin_max=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_margin_max
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_min=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_min
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_max=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_max
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_tilt_min_deg=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_tilt_min_deg
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_pre_pop_guard_max_up_action=(
            args.guard_final_servo_square_fast_settle_pre_pop_guard_max_up_action
        ),
        guard_final_servo_square_fast_settle_pre_pop_limit_enabled=(
            args.guard_final_servo_square_fast_settle_pre_pop_limit_enabled
        ),
        guard_final_servo_square_fast_settle_pre_pop_limit_max_xy_action=(
            args.guard_final_servo_square_fast_settle_pre_pop_limit_max_xy_action
        ),
        guard_final_servo_square_fast_settle_pre_pop_limit_max_down_action=(
            args.guard_final_servo_square_fast_settle_pre_pop_limit_max_down_action
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_enabled=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_enabled
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_xy_min=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_xy_min
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_xy_max=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_xy_max
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_z_min=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_z_min
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_z_max=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_z_max
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_contact_max=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_contact_max
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_min_brake_attempts=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_min_brake_attempts
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_min_steps_since_reset=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_min_steps_since_reset
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_max_attempts=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_max_attempts
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_height=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_height
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_pre_lift_enabled=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_pre_lift_enabled
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_margin_min=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_margin_min
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_topdown_margin_min=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_topdown_margin_min
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_severe_pop_reapproach_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_severe_pop_reapproach_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_clearance_hold_enabled=(
            args.guard_final_servo_square_fast_settle_clearance_hold_enabled
        ),
        guard_final_servo_square_fast_settle_clearance_hold_steps=(
            args.guard_final_servo_square_fast_settle_clearance_hold_steps
        ),
        guard_final_servo_square_fast_settle_clearance_hold_xy_max=(
            args.guard_final_servo_square_fast_settle_clearance_hold_xy_max
        ),
        guard_final_servo_square_fast_settle_clearance_hold_z_min=(
            args.guard_final_servo_square_fast_settle_clearance_hold_z_min
        ),
        guard_final_servo_square_fast_settle_clearance_hold_z_max=(
            args.guard_final_servo_square_fast_settle_clearance_hold_z_max
        ),
        guard_final_servo_square_fast_settle_clearance_hold_margin_threshold=(
            args.guard_final_servo_square_fast_settle_clearance_hold_margin_threshold
        ),
        guard_final_servo_square_fast_settle_clearance_hold_margin_min=(
            args.guard_final_servo_square_fast_settle_clearance_hold_margin_min
        ),
        guard_final_servo_square_fast_settle_clearance_hold_wall_count=(
            args.guard_final_servo_square_fast_settle_clearance_hold_wall_count
        ),
        guard_final_servo_square_fast_settle_clearance_hold_contact_max=(
            args.guard_final_servo_square_fast_settle_clearance_hold_contact_max
        ),
        guard_final_servo_square_fast_settle_clearance_hold_min_brake_attempts=(
            args.guard_final_servo_square_fast_settle_clearance_hold_min_brake_attempts
        ),
        guard_final_servo_square_fast_settle_clearance_hold_min_phase_steps=(
            args.guard_final_servo_square_fast_settle_clearance_hold_min_phase_steps
        ),
        guard_final_servo_square_fast_settle_clearance_hold_max_attempts=(
            args.guard_final_servo_square_fast_settle_clearance_hold_max_attempts
        ),
        guard_final_servo_square_fast_settle_clearance_hold_max_up_action=(
            args.guard_final_servo_square_fast_settle_clearance_hold_max_up_action
        ),
        guard_final_servo_square_fast_settle_low_z_relief_enabled=(
            args.guard_final_servo_square_fast_settle_low_z_relief_enabled
        ),
        guard_final_servo_square_fast_settle_low_z_relief_wall_count=(
            args.guard_final_servo_square_fast_settle_low_z_relief_wall_count
        ),
        guard_final_servo_square_fast_settle_low_z_relief_xy_max=(
            args.guard_final_servo_square_fast_settle_low_z_relief_xy_max
        ),
        guard_final_servo_square_fast_settle_low_z_relief_z_min=(
            args.guard_final_servo_square_fast_settle_low_z_relief_z_min
        ),
        guard_final_servo_square_fast_settle_low_z_relief_z_max=(
            args.guard_final_servo_square_fast_settle_low_z_relief_z_max
        ),
        guard_final_servo_square_fast_settle_low_z_relief_margin_min=(
            args.guard_final_servo_square_fast_settle_low_z_relief_margin_min
        ),
        guard_final_servo_square_fast_settle_low_z_relief_margin_threshold=(
            args.guard_final_servo_square_fast_settle_low_z_relief_margin_threshold
        ),
        guard_final_servo_square_fast_settle_low_z_relief_contact_max=(
            args.guard_final_servo_square_fast_settle_low_z_relief_contact_max
        ),
        guard_final_servo_square_fast_settle_low_z_relief_min_brake_attempts=(
            args.guard_final_servo_square_fast_settle_low_z_relief_min_brake_attempts
        ),
        guard_final_servo_square_fast_settle_low_z_relief_min_phase_steps=(
            args.guard_final_servo_square_fast_settle_low_z_relief_min_phase_steps
        ),
        guard_final_servo_square_fast_settle_low_z_relief_max_attempts=(
            args.guard_final_servo_square_fast_settle_low_z_relief_max_attempts
        ),
        guard_final_servo_square_fast_settle_low_z_relief_lift_height=(
            args.guard_final_servo_square_fast_settle_low_z_relief_lift_height
        ),
        guard_final_servo_square_fast_settle_low_z_relief_target_z_max=(
            args.guard_final_servo_square_fast_settle_low_z_relief_target_z_max
        ),
        guard_final_servo_square_fast_settle_low_z_relief_lift_steps=(
            args.guard_final_servo_square_fast_settle_low_z_relief_lift_steps
        ),
        guard_final_servo_square_fast_settle_low_z_relief_recenter_steps=(
            args.guard_final_servo_square_fast_settle_low_z_relief_recenter_steps
        ),
        guard_final_servo_square_fast_settle_low_z_relief_release_xy=(
            args.guard_final_servo_square_fast_settle_low_z_relief_release_xy
        ),
        guard_final_servo_square_fast_settle_low_z_relief_max_up_action=(
            args.guard_final_servo_square_fast_settle_low_z_relief_max_up_action
        ),
        guard_final_servo_square_fast_settle_low_z_relief_max_xy_action=(
            args.guard_final_servo_square_fast_settle_low_z_relief_max_xy_action
        ),
        guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_enabled=(
            args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_enabled
        ),
        guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_start_z_min=(
            args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_start_z_min
        ),
        guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_xy_max=(
            args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_xy_max
        ),
        guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_z_max=(
            args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_z_max
        ),
        guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_max_steps=(
            args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_max_steps
        ),
        guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_contact_pop_min_attempts=(
            args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_contact_pop_min_attempts
        ),
        guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_contact_pop_xy_max=(
            args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_contact_pop_xy_max
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_enabled=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_enabled
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_xy_max=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_xy_max
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_z_min=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_z_min
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_z_max=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_z_max
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_margin_min=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_margin_min
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_margin_threshold=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_margin_threshold
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_contact_max=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_contact_max
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_min_brake_attempts=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_min_brake_attempts
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_min_phase_steps=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_min_phase_steps
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_min_stall_steps=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_min_stall_steps
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_max_attempts=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_max_attempts
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_hold_enabled=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_enabled
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_hold_steps=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_steps
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_hold_max_up_action=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_max_up_action
        ),
        guard_final_servo_square_fast_settle_low_z_stall_relief_hold_min_contact_pop_hold_attempts=(
            args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_min_contact_pop_hold_attempts
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_enabled=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_enabled
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_steps=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_steps
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_xy_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_xy_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_z_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_z_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_z_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_z_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_margin_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_margin_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_wall_count=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_wall_count
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_contact_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_contact_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_min_phase_steps=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_min_phase_steps
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_min_steps_since_reset=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_min_steps_since_reset
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_min_phase_steps=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_min_phase_steps
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_min_steps_since_reset=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_min_steps_since_reset
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_z_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_z_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_max_attempts=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_max_attempts
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_max_up_action=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_max_up_action
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_enabled=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_enabled
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_contact_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_contact_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_max_steps=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_max_steps
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_min_steps_since_reset=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_min_steps_since_reset
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_enabled=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_enabled
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_steps=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_steps
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_xy_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_xy_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_z_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_z_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_z_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_z_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_contact_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_contact_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_max_xy_action=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_max_xy_action
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_max_down_action=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_max_down_action
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_enabled=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_enabled
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_wall_count=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_wall_count
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_xy_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_xy_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_xy_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_xy_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_z_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_z_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_z_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_z_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_contact_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_contact_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_max_phase_steps=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_max_phase_steps
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_min_soft_hold_attempts=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_min_soft_hold_attempts
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_soft_hold_first_enabled=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_soft_hold_first_enabled
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_enabled=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_enabled
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_steps=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_steps
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_wall_count=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_wall_count
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_xy_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_xy_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_xy_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_xy_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_z_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_z_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_z_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_z_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_contact_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_contact_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_phase_steps=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_phase_steps
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_min_soft_hold_attempts=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_min_soft_hold_attempts
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_attempts=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_attempts
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_up_action=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_up_action
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_enabled=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_enabled
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_xy_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_xy_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_xy_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_xy_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_z_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_z_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_z_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_z_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_contact_max=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_contact_max
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_topdown_margin_min=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_topdown_margin_min
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_late_finish_continue_enabled=(
            args.guard_final_servo_square_fast_settle_late_finish_continue_enabled
        ),
        guard_final_servo_square_fast_settle_late_finish_continue_min_steps_since_reset=(
            args.guard_final_servo_square_fast_settle_late_finish_continue_min_steps_since_reset
        ),
        guard_final_servo_square_fast_settle_late_finish_continue_xy_max=(
            args.guard_final_servo_square_fast_settle_late_finish_continue_xy_max
        ),
        guard_final_servo_square_fast_settle_late_finish_continue_z_min=(
            args.guard_final_servo_square_fast_settle_late_finish_continue_z_min
        ),
        guard_final_servo_square_fast_settle_late_finish_continue_z_max=(
            args.guard_final_servo_square_fast_settle_late_finish_continue_z_max
        ),
        guard_final_servo_square_fast_settle_late_finish_continue_margin_min=(
            args.guard_final_servo_square_fast_settle_late_finish_continue_margin_min
        ),
        guard_final_servo_square_fast_settle_late_finish_continue_topdown_margin_min=(
            args.guard_final_servo_square_fast_settle_late_finish_continue_topdown_margin_min
        ),
        guard_final_servo_square_fast_settle_late_finish_continue_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_late_finish_continue_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_late_finish_continue_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_late_finish_continue_tilt_max_deg
        ),
        guard_final_servo_square_fast_settle_late_finish_continue_contact_max=(
            args.guard_final_servo_square_fast_settle_late_finish_continue_contact_max
        ),
        guard_final_servo_square_fast_settle_late_escape_veto_enabled=(
            args.guard_final_servo_square_fast_settle_late_escape_veto_enabled
        ),
        guard_final_servo_square_fast_settle_late_escape_veto_min_steps_since_reset=(
            args.guard_final_servo_square_fast_settle_late_escape_veto_min_steps_since_reset
        ),
        guard_final_servo_square_fast_settle_late_escape_veto_xy_max=(
            args.guard_final_servo_square_fast_settle_late_escape_veto_xy_max
        ),
        guard_final_servo_square_fast_settle_late_escape_veto_z_min=(
            args.guard_final_servo_square_fast_settle_late_escape_veto_z_min
        ),
        guard_final_servo_square_fast_settle_late_escape_veto_z_max=(
            args.guard_final_servo_square_fast_settle_late_escape_veto_z_max
        ),
        guard_final_servo_square_fast_settle_late_escape_veto_contact_max=(
            args.guard_final_servo_square_fast_settle_late_escape_veto_contact_max
        ),
        guard_final_servo_square_fast_settle_late_escape_veto_margin_min=(
            args.guard_final_servo_square_fast_settle_late_escape_veto_margin_min
        ),
        guard_final_servo_square_fast_settle_late_escape_veto_topdown_margin_min=(
            args.guard_final_servo_square_fast_settle_late_escape_veto_topdown_margin_min
        ),
        guard_final_servo_square_fast_settle_late_escape_veto_yaw_max_deg=(
            args.guard_final_servo_square_fast_settle_late_escape_veto_yaw_max_deg
        ),
        guard_final_servo_square_fast_settle_late_escape_veto_tilt_max_deg=(
            args.guard_final_servo_square_fast_settle_late_escape_veto_tilt_max_deg
        ),
        guard_final_servo_square_contact_brake_enabled=(
            args.guard_final_servo_square_contact_brake_enabled
        ),
        guard_final_servo_square_contact_brake_wall_steps=(
            args.guard_final_servo_square_contact_brake_wall_steps
        ),
        guard_final_servo_square_contact_brake_xy_max=(
            args.guard_final_servo_square_contact_brake_xy_max
        ),
        guard_final_servo_square_contact_brake_z_min=(
            args.guard_final_servo_square_contact_brake_z_min
        ),
        guard_final_servo_square_contact_brake_z_max=(
            args.guard_final_servo_square_contact_brake_z_max
        ),
        guard_final_servo_square_contact_brake_lift_height=(
            args.guard_final_servo_square_contact_brake_lift_height
        ),
        guard_final_servo_square_contact_brake_lift_z_max=(
            args.guard_final_servo_square_contact_brake_lift_z_max
        ),
        guard_final_servo_square_contact_brake_release_xy=(
            args.guard_final_servo_square_contact_brake_release_xy
        ),
        guard_final_servo_square_contact_brake_stable_steps=(
            args.guard_final_servo_square_contact_brake_stable_steps
        ),
        guard_final_servo_square_contact_brake_max_steps=(
            args.guard_final_servo_square_contact_brake_max_steps
        ),
        guard_final_servo_square_contact_brake_max_attempts=(
            args.guard_final_servo_square_contact_brake_max_attempts
        ),
        guard_final_servo_square_contact_brake_max_xy_action=(
            args.guard_final_servo_square_contact_brake_max_xy_action
        ),
        guard_final_servo_square_contact_brake_max_up_action=(
            args.guard_final_servo_square_contact_brake_max_up_action
        ),
        guard_final_servo_square_contact_brake_max_clearance=(
            args.guard_final_servo_square_contact_brake_max_clearance
        ),
        guard_final_servo_square_contact_brake_margin_threshold=(
            args.guard_final_servo_square_contact_brake_margin_threshold
        ),
        guard_final_servo_square_contact_brake_require_bad_margin=(
            args.guard_final_servo_square_contact_brake_require_bad_margin
        ),
        guard_final_servo_square_contact_brake_repeat_margin_gate_enabled=(
            args.guard_final_servo_square_contact_brake_repeat_margin_gate_enabled
        ),
        guard_final_servo_square_contact_brake_repeat_margin_threshold=(
            args.guard_final_servo_square_contact_brake_repeat_margin_threshold
        ),
        guard_final_servo_square_contact_brake_release_flush_enabled=(
            args.guard_final_servo_square_contact_brake_release_flush_enabled
        ),
        guard_final_servo_square_contact_brake_release_flush_steps=(
            args.guard_final_servo_square_contact_brake_release_flush_steps
        ),
        guard_final_servo_square_contact_brake_release_flush_min_brake_attempts=(
            args.guard_final_servo_square_contact_brake_release_flush_min_brake_attempts
        ),
        guard_final_servo_square_contact_brake_release_flush_min_steps_since_reset=(
            args.guard_final_servo_square_contact_brake_release_flush_min_steps_since_reset
        ),
        guard_final_servo_square_contact_brake_release_flush_xy_max=(
            args.guard_final_servo_square_contact_brake_release_flush_xy_max
        ),
        guard_final_servo_square_contact_brake_release_flush_z_min=(
            args.guard_final_servo_square_contact_brake_release_flush_z_min
        ),
        guard_final_servo_square_contact_brake_release_flush_z_max=(
            args.guard_final_servo_square_contact_brake_release_flush_z_max
        ),
        guard_final_servo_square_contact_brake_release_flush_contact_max=(
            args.guard_final_servo_square_contact_brake_release_flush_contact_max
        ),
        guard_final_servo_square_contact_brake_exhausted_escape_enabled=(
            args.guard_final_servo_square_contact_brake_exhausted_escape_enabled
        ),
        guard_final_servo_square_contact_brake_reset_attempts_after_escape_enabled=(
            args.guard_final_servo_square_contact_brake_reset_attempts_after_escape_enabled
        ),
        guard_final_servo_square_contact_brake_exhausted_continue_enabled=(
            args.guard_final_servo_square_contact_brake_exhausted_continue_enabled
        ),
        guard_final_servo_square_contact_brake_exhausted_continue_min_steps_since_reset=(
            args.guard_final_servo_square_contact_brake_exhausted_continue_min_steps_since_reset
        ),
        guard_final_servo_square_contact_brake_exhausted_continue_xy_max=(
            args.guard_final_servo_square_contact_brake_exhausted_continue_xy_max
        ),
        guard_final_servo_square_contact_brake_exhausted_continue_z_min=(
            args.guard_final_servo_square_contact_brake_exhausted_continue_z_min
        ),
        guard_final_servo_square_contact_brake_exhausted_continue_z_max=(
            args.guard_final_servo_square_contact_brake_exhausted_continue_z_max
        ),
        guard_final_servo_square_contact_brake_exhausted_continue_contact_max=(
            args.guard_final_servo_square_contact_brake_exhausted_continue_contact_max
        ),
        guard_final_servo_square_contact_brake_exhausted_continue_tilt_max_deg=(
            args.guard_final_servo_square_contact_brake_exhausted_continue_tilt_max_deg
        ),
        guard_final_servo_square_contact_brake_exhausted_continue_margin_min=(
            args.guard_final_servo_square_contact_brake_exhausted_continue_margin_min
        ),
        guard_final_servo_square_contact_brake_exhausted_continue_topdown_margin_min=(
            args.guard_final_servo_square_contact_brake_exhausted_continue_topdown_margin_min
        ),
        guard_final_servo_square_contact_brake_exhausted_continue_yaw_max_deg=(
            args.guard_final_servo_square_contact_brake_exhausted_continue_yaw_max_deg
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_enabled=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_enabled
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_wall_steps=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_wall_steps
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_steps=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_steps
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_min_brake_attempts=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_min_brake_attempts
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_xy_max=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_xy_max
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_z_min=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_z_min
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_z_max=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_z_max
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_max_up_action=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_max_up_action
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_max_clearance=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_max_clearance
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_margin_threshold=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_margin_threshold
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_require_bad_margin=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_require_bad_margin
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_yaw_min_deg=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_yaw_min_deg
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy_enabled=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy_enabled
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy_max=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy_max
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_expanded_z_min=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_z_min
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_expanded_margin_min=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_margin_min
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_expanded_yaw_max_deg=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_yaw_max_deg
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_clean_release_enabled=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_enabled
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_clean_release_max_brake_attempts=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_max_brake_attempts
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_clean_release_contact_max=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_contact_max
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_clean_release_xy_max=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_xy_max
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_clean_release_z_min=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_z_min
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_clean_release_z_max=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_z_max
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_clean_release_margin_min=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_margin_min
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_clean_release_tilt_max_deg=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_tilt_max_deg
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_enabled=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_enabled
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_min_phase_steps=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_min_phase_steps
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_xy_min=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_xy_min
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_xy_max=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_xy_max
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_z_min=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_z_min
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_z_max=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_z_max
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_contact_max=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_contact_max
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_margin_min=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_margin_min
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_topdown_margin_min=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_topdown_margin_min
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_yaw_max_deg=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_yaw_max_deg
        ),
        guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_tilt_max_deg=(
            args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_tilt_max_deg
        ),
        guard_final_servo_square_contact_brake_late_lift_release_enabled=(
            args.guard_final_servo_square_contact_brake_late_lift_release_enabled
        ),
        guard_final_servo_square_contact_brake_late_lift_release_min_brake_attempts=(
            args.guard_final_servo_square_contact_brake_late_lift_release_min_brake_attempts
        ),
        guard_final_servo_square_contact_brake_late_lift_release_min_phase_steps=(
            args.guard_final_servo_square_contact_brake_late_lift_release_min_phase_steps
        ),
        guard_final_servo_square_contact_brake_late_lift_release_min_steps_since_reset=(
            args.guard_final_servo_square_contact_brake_late_lift_release_min_steps_since_reset
        ),
        guard_final_servo_square_contact_brake_late_lift_release_contact_max=(
            args.guard_final_servo_square_contact_brake_late_lift_release_contact_max
        ),
        guard_final_servo_square_contact_brake_late_lift_release_xy_max=(
            args.guard_final_servo_square_contact_brake_late_lift_release_xy_max
        ),
        guard_final_servo_square_contact_brake_late_lift_release_z_min=(
            args.guard_final_servo_square_contact_brake_late_lift_release_z_min
        ),
        guard_final_servo_square_contact_brake_late_lift_release_z_max=(
            args.guard_final_servo_square_contact_brake_late_lift_release_z_max
        ),
        guard_final_servo_square_contact_brake_late_lift_release_margin_min=(
            args.guard_final_servo_square_contact_brake_late_lift_release_margin_min
        ),
        guard_final_servo_square_contact_brake_late_lift_release_yaw_max_deg=(
            args.guard_final_servo_square_contact_brake_late_lift_release_yaw_max_deg
        ),
        guard_final_servo_square_contact_brake_late_lift_release_tilt_max_deg=(
            args.guard_final_servo_square_contact_brake_late_lift_release_tilt_max_deg
        ),
        guard_final_servo_square_high_z_descend_enabled=(
            args.guard_final_servo_square_high_z_descend_enabled
        ),
        guard_final_servo_square_high_z_descend_stall_steps=(
            args.guard_final_servo_square_high_z_descend_stall_steps
        ),
        guard_final_servo_square_high_z_descend_xy_max=(
            args.guard_final_servo_square_high_z_descend_xy_max
        ),
        guard_final_servo_square_high_z_descend_z_min=(
            args.guard_final_servo_square_high_z_descend_z_min
        ),
        guard_final_servo_square_high_z_descend_z_max=(
            args.guard_final_servo_square_high_z_descend_z_max
        ),
        guard_final_servo_square_high_z_descend_contact_max=(
            args.guard_final_servo_square_high_z_descend_contact_max
        ),
        guard_final_servo_square_high_z_descend_tilt_max_deg=(
            args.guard_final_servo_square_high_z_descend_tilt_max_deg
        ),
        guard_final_servo_square_high_z_descend_margin_min=(
            args.guard_final_servo_square_high_z_descend_margin_min
        ),
        guard_final_servo_square_high_z_descend_max_steps=(
            args.guard_final_servo_square_high_z_descend_max_steps
        ),
        guard_final_servo_square_high_z_descend_max_xy_action=(
            args.guard_final_servo_square_high_z_descend_max_xy_action
        ),
        guard_final_servo_square_high_z_descend_max_down_action=(
            args.guard_final_servo_square_high_z_descend_max_down_action
        ),
        guard_final_servo_square_high_z_descend_low_z_threshold=(
            args.guard_final_servo_square_high_z_descend_low_z_threshold
        ),
        guard_final_servo_square_high_z_descend_low_z_max_xy_action=(
            args.guard_final_servo_square_high_z_descend_low_z_max_xy_action
        ),
        guard_final_servo_square_high_z_descend_staged_enabled=(
            args.guard_final_servo_square_high_z_descend_staged_enabled
        ),
        guard_final_servo_square_high_z_descend_mid_z_threshold=(
            args.guard_final_servo_square_high_z_descend_mid_z_threshold
        ),
        guard_final_servo_square_high_z_descend_mid_z_max_xy_action=(
            args.guard_final_servo_square_high_z_descend_mid_z_max_xy_action
        ),
        guard_final_servo_square_high_z_descend_mid_z_max_down_action=(
            args.guard_final_servo_square_high_z_descend_mid_z_max_down_action
        ),
        guard_final_servo_square_high_z_descend_low_z_max_down_action=(
            args.guard_final_servo_square_high_z_descend_low_z_max_down_action
        ),
        guard_final_servo_square_high_z_descend_low_z_hold_steps=(
            args.guard_final_servo_square_high_z_descend_low_z_hold_steps
        ),
        guard_final_servo_square_high_z_descend_low_z_hold_min_phase_steps=(
            args.guard_final_servo_square_high_z_descend_low_z_hold_min_phase_steps
        ),
        guard_final_servo_square_high_z_descend_low_z_hold_max_attempts=(
            args.guard_final_servo_square_high_z_descend_low_z_hold_max_attempts
        ),
        guard_final_servo_square_high_z_descend_low_z_hold_xy_max=(
            args.guard_final_servo_square_high_z_descend_low_z_hold_xy_max
        ),
        guard_final_servo_square_high_z_descend_low_z_hold_max_up_action=(
            args.guard_final_servo_square_high_z_descend_low_z_hold_max_up_action
        ),
        guard_final_servo_square_high_z_descend_contact_brake_enabled=(
            args.guard_final_servo_square_high_z_descend_contact_brake_enabled
        ),
        guard_final_servo_square_high_z_descend_contact_brake_wall_count=(
            args.guard_final_servo_square_high_z_descend_contact_brake_wall_count
        ),
        guard_final_servo_square_high_z_descend_contact_brake_z_max=(
            args.guard_final_servo_square_high_z_descend_contact_brake_z_max
        ),
        guard_final_servo_square_high_z_descend_contact_brake_xy_max=(
            args.guard_final_servo_square_high_z_descend_contact_brake_xy_max
        ),
        guard_final_servo_square_margin_yaw_settle_enabled=(
            args.guard_final_servo_square_margin_yaw_settle_enabled
        ),
        guard_final_servo_square_margin_yaw_settle_stall_steps=(
            args.guard_final_servo_square_margin_yaw_settle_stall_steps
        ),
        guard_final_servo_square_margin_yaw_settle_xy_max=(
            args.guard_final_servo_square_margin_yaw_settle_xy_max
        ),
        guard_final_servo_square_margin_yaw_settle_z_min=(
            args.guard_final_servo_square_margin_yaw_settle_z_min
        ),
        guard_final_servo_square_margin_yaw_settle_z_max=(
            args.guard_final_servo_square_margin_yaw_settle_z_max
        ),
        guard_final_servo_square_margin_yaw_settle_contact_max=(
            args.guard_final_servo_square_margin_yaw_settle_contact_max
        ),
        guard_final_servo_square_margin_yaw_settle_margin_threshold=(
            args.guard_final_servo_square_margin_yaw_settle_margin_threshold
        ),
        guard_final_servo_square_margin_yaw_settle_yaw_deg=(
            args.guard_final_servo_square_margin_yaw_settle_yaw_deg
        ),
        guard_final_servo_square_margin_yaw_settle_release_xy=(
            args.guard_final_servo_square_margin_yaw_settle_release_xy
        ),
        guard_final_servo_square_margin_yaw_settle_lift_height=(
            args.guard_final_servo_square_margin_yaw_settle_lift_height
        ),
        guard_final_servo_square_margin_yaw_settle_stable_steps=(
            args.guard_final_servo_square_margin_yaw_settle_stable_steps
        ),
        guard_final_servo_square_margin_yaw_settle_max_steps=(
            args.guard_final_servo_square_margin_yaw_settle_max_steps
        ),
        guard_final_servo_square_margin_yaw_settle_max_attempts=(
            args.guard_final_servo_square_margin_yaw_settle_max_attempts
        ),
        guard_final_servo_square_margin_yaw_settle_max_xy_action=(
            args.guard_final_servo_square_margin_yaw_settle_max_xy_action
        ),
        guard_final_servo_square_margin_yaw_settle_max_up_action=(
            args.guard_final_servo_square_margin_yaw_settle_max_up_action
        ),
        guard_final_servo_square_tilt_reinsert_enabled=(
            args.guard_final_servo_square_tilt_reinsert_enabled
        ),
        guard_final_servo_square_tilt_reinsert_wall_steps=(
            args.guard_final_servo_square_tilt_reinsert_wall_steps
        ),
        guard_final_servo_square_tilt_reinsert_stall_steps=(
            args.guard_final_servo_square_tilt_reinsert_stall_steps
        ),
        guard_final_servo_square_tilt_reinsert_tilt_deg=(
            args.guard_final_servo_square_tilt_reinsert_tilt_deg
        ),
        guard_final_servo_square_tilt_reinsert_margin_threshold=(
            args.guard_final_servo_square_tilt_reinsert_margin_threshold
        ),
        guard_final_servo_square_tilt_reinsert_xy_max=(
            args.guard_final_servo_square_tilt_reinsert_xy_max
        ),
        guard_final_servo_square_tilt_reinsert_z_min=(
            args.guard_final_servo_square_tilt_reinsert_z_min
        ),
        guard_final_servo_square_tilt_reinsert_z_max=(
            args.guard_final_servo_square_tilt_reinsert_z_max
        ),
        guard_final_servo_square_tilt_reinsert_lift_height=(
            args.guard_final_servo_square_tilt_reinsert_lift_height
        ),
        guard_final_servo_square_tilt_reinsert_release_xy=(
            args.guard_final_servo_square_tilt_reinsert_release_xy
        ),
        guard_final_servo_square_tilt_reinsert_release_tilt_deg=(
            args.guard_final_servo_square_tilt_reinsert_release_tilt_deg
        ),
        guard_final_servo_square_tilt_reinsert_stable_steps=(
            args.guard_final_servo_square_tilt_reinsert_stable_steps
        ),
        guard_final_servo_square_tilt_reinsert_max_steps=(
            args.guard_final_servo_square_tilt_reinsert_max_steps
        ),
        guard_final_servo_square_tilt_reinsert_max_attempts=(
            args.guard_final_servo_square_tilt_reinsert_max_attempts
        ),
        guard_final_servo_square_tilt_reinsert_max_xy_action=(
            args.guard_final_servo_square_tilt_reinsert_max_xy_action
        ),
        guard_final_servo_square_tilt_reinsert_max_up_action=(
            args.guard_final_servo_square_tilt_reinsert_max_up_action
        ),
        oracle=OracleControllerConfig(
            mode=args.guarded_oracle_mode,
            action_gain=args.guard_action_gain,
            guarded_align_xy_tolerance=args.guarded_align_xy_tolerance,
            guarded_insert_xy_tolerance=args.guarded_insert_xy_tolerance,
            guarded_retract_xy_tolerance=args.guarded_retract_xy_tolerance,
            guarded_preinsert_height=args.guarded_preinsert_height,
            guarded_max_xy_action=args.guarded_max_xy_action,
            guarded_max_down_action=args.guarded_max_down_action,
            guarded_max_up_action=args.guarded_max_up_action,
            guarded_prediction_steps=args.guarded_prediction_steps,
            guarded_hold_z_until_insert=args.guarded_hold_z_until_insert,
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
        ),
    )


def clone_observation(obs: Any) -> Any:
    if isinstance(obs, dict):
        return {key: clone_observation(value) for key, value in obs.items()}
    if isinstance(obs, np.ndarray):
        return obs.copy()
    return obs


def should_ablate_image_key(key: str, target: str) -> bool:
    return target == "all" or key == target


def black_like(obs: Any, *, target: str = "all") -> Any:
    if isinstance(obs, dict):
        return {
            key: black_like(value, target="all") if should_ablate_image_key(key, target) else clone_observation(value)
            for key, value in obs.items()
        }
    if isinstance(obs, np.ndarray):
        if obs.dtype == np.uint8:
            return np.zeros_like(obs)
        return obs.copy()
    return obs


def noise_like(obs: Any, rng: np.random.Generator, *, target: str = "all") -> Any:
    if isinstance(obs, dict):
        return {
            key: noise_like(value, rng, target="all") if should_ablate_image_key(key, target) else clone_observation(value)
            for key, value in obs.items()
        }
    if isinstance(obs, np.ndarray) and obs.dtype == np.uint8:
        return rng.integers(0, 256, size=obs.shape, dtype=np.uint8)
    if isinstance(obs, np.ndarray):
        return obs.copy()
    return obs


def preserve_non_image_values(ablated: Any, original: Any) -> Any:
    if isinstance(ablated, dict) and isinstance(original, dict):
        merged = {}
        for key, value in ablated.items():
            merged[key] = preserve_non_image_values(value, original.get(key, value))
        return merged
    if isinstance(ablated, np.ndarray) and isinstance(original, np.ndarray):
        if ablated.dtype != np.uint8:
            return original.copy()
    return ablated


def policy_observation(
    obs: Any,
    *,
    image_ablation: str,
    image_ablation_target: str,
    control_state_ablation: str,
    rng: np.random.Generator,
    image_shuffle_bank: list[Any],
    control_state_shuffle_bank: list[np.ndarray],
) -> Any:
    if image_ablation == "normal":
        image_obs = obs
    elif image_ablation == "black":
        image_obs = black_like(obs, target=image_ablation_target)
    elif image_ablation == "noise":
        image_obs = noise_like(obs, rng, target=image_ablation_target)
    elif image_ablation == "shuffle":
        image_obs = shuffled_image_observation(
            obs,
            target=image_ablation_target,
            rng=rng,
            shuffle_bank=image_shuffle_bank,
        )
    else:
        raise ValueError(f"Unknown image ablation mode: {image_ablation}")
    return ablate_control_state(
        image_obs,
        mode=control_state_ablation,
        rng=rng,
        shuffle_bank=control_state_shuffle_bank,
    )


def approach_adapter_gate(
    args: argparse.Namespace,
    info: dict[str, Any],
    *,
    latched: bool = False,
    latch_steps: int = 0,
    episode_steps: int = 0,
) -> bool:
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    z_above_target = float(tip[2] - target[2])
    dist_xy = float(info["dist_xy"])
    if not args.approach_adapter_enabled:
        return False
    if (
        args.approach_adapter_episode_max_steps > 0
        and episode_steps >= args.approach_adapter_episode_max_steps
    ):
        return False
    if args.approach_adapter_latch_enabled and latched:
        latched_min_z = (
            args.approach_adapter_min_z
            if args.approach_adapter_latched_min_z is None
            else args.approach_adapter_latched_min_z
        )
        under_step_cap = (
            args.approach_adapter_max_steps <= 0
            or latch_steps < args.approach_adapter_max_steps
        )
        return bool(
            under_step_cap
            and dist_xy >= args.approach_adapter_release_xy
            and latched_min_z
            <= z_above_target
            <= args.approach_adapter_max_z
        )
    return bool(
        dist_xy >= args.approach_adapter_trigger_xy
        and args.approach_adapter_min_z
        <= z_above_target
        <= args.approach_adapter_max_z
    )


def limit_xy_vector(vector: np.ndarray, max_norm: float) -> np.ndarray:
    limited = np.asarray(vector, dtype=np.float64).copy()
    if max_norm <= 0.0:
        limited[:2] = 0.0
        return limited
    norm = float(np.linalg.norm(limited[:2]))
    if norm > max_norm:
        limited[:2] *= max_norm / norm
    return limited


def apply_approach_adapter(
    *,
    adapter: ApproachAdapterPolicy | None,
    args: argparse.Namespace,
    obs: Any,
    info: dict[str, Any],
    policy_action: np.ndarray,
    action_low: np.ndarray,
    action_high: np.ndarray,
    latched: bool = False,
    latch_steps: int = 0,
    episode_steps: int = 0,
) -> tuple[np.ndarray, np.ndarray, bool]:
    if adapter is None or not approach_adapter_gate(
        args,
        info,
        latched=latched,
        latch_steps=latch_steps,
        episode_steps=episode_steps,
    ):
        return policy_action, np.zeros(3, dtype=np.float32), False
    if not isinstance(obs, dict):
        raise ValueError("approach adapter requires dict observations.")
    residual = adapter.predict(obs).astype(np.float64)
    residual *= float(args.approach_adapter_scale)
    residual = limit_xy_vector(residual, args.approach_adapter_max_xy_residual)
    base_action = np.asarray(policy_action, dtype=np.float64)
    if args.approach_adapter_mode == "override_xy":
        adapted = base_action.copy()
        adapted[:2] = residual[:2]
        if args.approach_adapter_apply_z:
            adapted[2] = float(
                np.clip(
                    residual[2],
                    -args.approach_adapter_max_z_residual,
                    args.approach_adapter_max_z_residual,
                )
            )
        modification = adapted - base_action
    else:
        if args.approach_adapter_apply_z:
            residual[2] = float(
                np.clip(
                    residual[2],
                    -args.approach_adapter_max_z_residual,
                    args.approach_adapter_max_z_residual,
                )
            )
        else:
            residual[2] = 0.0
        adapted = base_action + residual
        modification = residual
    if not args.approach_adapter_apply_z:
        adapted[2] = base_action[2]
        modification[2] = 0.0
    adapted = np.clip(
        adapted,
        action_low,
        action_high,
    )
    modification = adapted - base_action
    return adapted.astype(np.float32), modification.astype(np.float32), True


def final_insert_progress_features(
    history: list[tuple[float, float]],
    window_steps: int,
) -> tuple[float, float]:
    if len(history) <= 1:
        return 0.0, 0.0
    current_dist_xy, current_z = history[-1]
    start_index = max(0, len(history) - 1 - window_steps)
    previous_dist_xy, previous_z = history[start_index]
    return float(previous_z - current_z), float(previous_dist_xy - current_dist_xy)


@dataclass
class FinalInsertMacroRecoveryState:
    phase: str = "inactive"
    phase_steps_remaining: int = 0
    attempts: int = 0
    active_streak: int = 0


def final_insert_macro_recovery_candidate(
    *,
    args: argparse.Namespace,
    info: dict[str, Any],
    step: GuardedPolicyStep | None,
) -> tuple[bool, str]:
    if not args.final_insert_macro_recovery_enabled:
        return False, "disabled"
    if step is None:
        return False, "no_guard_step"
    if not bool(step.guard_final_servo_active):
        return False, "not_final_servo"
    phase = str(step.guard_final_servo_phase)
    if (
        args.final_insert_macro_recovery_phase != "any"
        and phase != args.final_insert_macro_recovery_phase
    ):
        return False, f"phase:{phase}"
    geometry_name = str(info.get("geometry_name", ""))
    if (
        args.final_insert_macro_recovery_geometry_name != "any"
        and geometry_name != args.final_insert_macro_recovery_geometry_name
    ):
        return False, f"geometry:{geometry_name}"
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    z_above_target = float(tip[2] - target[2])
    dist_xy = float(info["dist_xy"])
    if dist_xy > args.final_insert_macro_recovery_max_xy:
        return False, "xy_outside"
    if not (
        args.final_insert_macro_recovery_min_z
        <= z_above_target
        <= args.final_insert_macro_recovery_max_z
    ):
        return False, "z_outside"
    return True, "candidate"


def final_insert_macro_recovery_action(
    *,
    args: argparse.Namespace,
    info: dict[str, Any],
    state: FinalInsertMacroRecoveryState,
    action_low: np.ndarray,
    action_high: np.ndarray,
) -> tuple[np.ndarray, bool, str, int, int]:
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    rel = target - tip
    phase = state.phase
    action = np.zeros(3, dtype=np.float64)
    if phase == "lift":
        action[2] = float(args.final_insert_macro_recovery_lift_action)
    elif phase == "abort_lift":
        action[2] = float(args.final_insert_macro_recovery_abort_lift_action)
    elif phase in ("align", "hold"):
        action[:2] = limit_xy_vector(rel[:2], args.final_insert_macro_recovery_max_xy_action)
        action[2] = 0.0
    else:
        return np.asarray(action, dtype=np.float32), False, phase, state.attempts, 0

    action = np.clip(action, action_low, action_high)
    state.phase_steps_remaining = max(0, int(state.phase_steps_remaining) - 1)
    if state.phase_steps_remaining <= 0:
        if phase == "lift":
            state.phase = "align"
            state.phase_steps_remaining = int(args.final_insert_macro_recovery_align_steps)
        elif phase == "align":
            state.phase = "hold"
            state.phase_steps_remaining = int(args.final_insert_macro_recovery_hold_steps)
        else:
            state.phase = "inactive"
            state.phase_steps_remaining = 0
            state.active_streak = 0
    return (
        action.astype(np.float32),
        True,
        phase,
        state.attempts,
        state.phase_steps_remaining,
    )


def final_insert_adapter_gate(
    *,
    args: argparse.Namespace,
    info: dict[str, Any],
    step: GuardedPolicyStep | None,
) -> tuple[bool, str]:
    if not args.final_insert_adapter_enabled:
        return False, "disabled"
    if step is None:
        return False, "no_guard_step"
    if not bool(step.guard_final_servo_active):
        return False, "not_final_servo"
    phase = str(step.guard_final_servo_phase)
    if args.final_insert_adapter_phase != "any" and phase != args.final_insert_adapter_phase:
        return False, f"phase:{phase}"
    geometry_name = str(info.get("geometry_name", ""))
    if (
        args.final_insert_adapter_geometry_name != "any"
        and geometry_name != args.final_insert_adapter_geometry_name
    ):
        return False, f"geometry:{geometry_name}"
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    z_above_target = float(tip[2] - target[2])
    dist_xy = float(info["dist_xy"])
    if dist_xy > args.final_insert_adapter_max_xy:
        return False, "xy_outside"
    if not (
        args.final_insert_adapter_min_z
        <= z_above_target
        <= args.final_insert_adapter_max_z
    ):
        return False, "z_outside"
    if step.guard_final_servo_phase_steps < args.final_insert_adapter_min_phase_steps:
        return False, "phase_steps"
    if step.guard_final_servo_stall_steps < args.final_insert_adapter_min_stall_steps:
        if not args.final_insert_adapter_square_risk_gate_enabled:
            return False, "stall_steps"
        if (
            step.guard_final_servo_stall_steps
            < args.final_insert_adapter_square_risk_min_stall_steps
        ):
            return False, "stall_steps"
        risk_reason = final_insert_adapter_square_risk_reason(args=args, info=info)
        if risk_reason is None:
            return False, "risk_gate"
    else:
        risk_reason = None
    wall_count = int(info.get("peg_hole_contact_wall_count", 0))
    if args.final_insert_adapter_wall_contact_required and wall_count <= 0:
        return False, "no_wall_contact"
    if risk_reason is not None:
        return True, risk_reason
    return True, "wall_contact" if wall_count > 0 else "near_final_insert"


def final_insert_adapter_square_risk_reason(
    *,
    args: argparse.Namespace,
    info: dict[str, Any],
) -> str | None:
    dist_xy = float(info["dist_xy"])
    topdown_margin = float(info.get("square_peg_topdown_clearance_margin", float("inf")))
    tilted_margin = float(info.get("square_peg_tilted_clearance_margin", float("inf")))
    wall_count = int(info.get("peg_hole_contact_wall_count", 0))

    if (
        args.final_insert_adapter_square_risk_xy_min > 0.0
        and dist_xy >= args.final_insert_adapter_square_risk_xy_min
    ):
        return "risk_xy"
    if topdown_margin <= args.final_insert_adapter_square_risk_topdown_margin_max:
        return "risk_topdown_margin"
    if tilted_margin <= args.final_insert_adapter_square_risk_tilted_margin_max:
        return "risk_tilted_margin"
    if wall_count > 0 and (
        topdown_margin
        <= args.final_insert_adapter_square_risk_wall_topdown_margin_max
        or tilted_margin
        <= args.final_insert_adapter_square_risk_wall_tilted_margin_max
    ):
        return "risk_wall_margin"
    return None


def final_insert_adapter_feature_dict(
    *,
    info: dict[str, Any],
    step: GuardedPolicyStep,
    z_progress_window: float,
    xy_progress_window: float,
) -> dict[str, float]:
    tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    target = np.asarray(info["target_pos"], dtype=np.float64)
    rel = target - tip
    z_above_target = float(tip[2] - target[2])
    return {
        "rel_x": float(rel[0]),
        "rel_y": float(rel[1]),
        "z_above_target": z_above_target,
        "dist_xy": float(info["dist_xy"]),
        "dist_z": float(info["dist_z"]),
        "peg_tilt_angle_deg": float(info.get("peg_tilt_angle_deg", 0.0)),
        "square_peg_yaw_error_deg": float(info.get("square_peg_yaw_error_deg", 0.0)),
        "square_peg_topdown_clearance_margin": float(
            info.get("square_peg_topdown_clearance_margin", 0.0)
        ),
        "square_peg_tilted_clearance_margin": float(
            info.get("square_peg_tilted_clearance_margin", 0.0)
        ),
        "peg_hole_contact_wall_count": float(
            int(info.get("peg_hole_contact_wall_count", 0))
        ),
        "peg_hole_contact_plate_count": float(
            int(info.get("peg_hole_contact_plate_count", 0))
        ),
        "wall_north": float(int(info.get("peg_hole_contact_hole_north", 0)) > 0),
        "wall_south": float(int(info.get("peg_hole_contact_hole_south", 0)) > 0),
        "wall_east": float(int(info.get("peg_hole_contact_hole_east", 0)) > 0),
        "wall_west": float(int(info.get("peg_hole_contact_hole_west", 0)) > 0),
        "z_progress_window": float(z_progress_window),
        "xy_progress_window": float(xy_progress_window),
        "guard_final_servo_phase_steps": float(step.guard_final_servo_phase_steps),
        "guard_final_servo_stall_steps": float(step.guard_final_servo_stall_steps),
    }


def clip_final_insert_adapter_action(
    *,
    action: np.ndarray,
    args: argparse.Namespace,
    action_low: np.ndarray,
    action_high: np.ndarray,
) -> np.ndarray:
    clipped = np.asarray(action, dtype=np.float64).copy().reshape(3)
    clipped = limit_xy_vector(clipped, args.final_insert_adapter_max_xy_action)
    clipped[2] = float(
        np.clip(
            clipped[2],
            -args.final_insert_adapter_max_down_action,
            args.final_insert_adapter_max_up_action,
        )
    )
    return np.clip(clipped, action_low, action_high).astype(np.float32)


def apply_final_insert_adapter(
    *,
    adapter: FinalInsertAdapterPolicy | None,
    args: argparse.Namespace,
    info: dict[str, Any],
    step: GuardedPolicyStep | None,
    action: np.ndarray,
    action_low: np.ndarray,
    action_high: np.ndarray,
    z_progress_window: float,
    xy_progress_window: float,
    active_streak: int,
    cooldown_remaining: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool, str]:
    active, reason = final_insert_adapter_gate(args=args, info=info, step=step)
    if active and cooldown_remaining > 0:
        active = False
        reason = "cooldown"
    if (
        active
        and args.final_insert_adapter_max_consecutive_steps > 0
        and active_streak >= args.final_insert_adapter_max_consecutive_steps
    ):
        active = False
        reason = "max_consecutive"
    if active and args.final_insert_adapter_handoff_on_aligned_no_contact:
        tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
        target = np.asarray(info["target_pos"], dtype=np.float64)
        z_above_target = float(tip[2] - target[2])
        wall_count = int(info.get("peg_hole_contact_wall_count", 0))
        if (
            wall_count <= 0
            and float(info["dist_xy"]) <= args.final_insert_adapter_handoff_xy
            and args.final_insert_adapter_handoff_min_z
            <= z_above_target
            <= args.final_insert_adapter_handoff_max_z
        ):
            active = False
            reason = "handoff_state"
    if adapter is None or not active or step is None:
        zeros = np.zeros(3, dtype=np.float32)
        return np.asarray(action, dtype=np.float32), zeros, zeros, False, reason
    features = final_insert_adapter_feature_dict(
        info=info,
        step=step,
        z_progress_window=z_progress_window,
        xy_progress_window=xy_progress_window,
    )
    raw_action = adapter.predict(features).reshape(3)
    clipped_adapter_action = clip_final_insert_adapter_action(
        action=raw_action,
        args=args,
        action_low=action_low,
        action_high=action_high,
    )
    base_action = np.asarray(action, dtype=np.float64).reshape(3)
    if (
        args.final_insert_adapter_handoff_on_down_action
        and clipped_adapter_action[2]
        <= args.final_insert_adapter_handoff_z_action_threshold
    ):
        return (
            np.clip(base_action, action_low, action_high).astype(np.float32),
            raw_action.astype(np.float32),
            clipped_adapter_action.astype(np.float32),
            False,
            "handoff_prediction",
        )
    if args.final_insert_adapter_mode == "override":
        final_action = clipped_adapter_action
    elif args.final_insert_adapter_mode == "override_xy":
        final_action = base_action.copy()
        final_action[:2] = clipped_adapter_action[:2]
        final_action = np.clip(final_action, action_low, action_high)
    elif args.final_insert_adapter_mode == "residual":
        final_action = np.clip(base_action + clipped_adapter_action, action_low, action_high)
    else:
        raise ValueError(f"Unknown final insert adapter mode: {args.final_insert_adapter_mode}")
    return (
        final_action.astype(np.float32),
        raw_action.astype(np.float32),
        clipped_adapter_action.astype(np.float32),
        True,
        reason,
    )


def maybe_apply_final_insert_lift_pulse(
    *,
    args: argparse.Namespace,
    action: np.ndarray,
    step: GuardedPolicyStep | None,
    step_index: int,
    adapter_active: bool,
    active_streak: int,
    pulse_steps_remaining: int,
    last_pulse_step: int,
    action_low: np.ndarray,
    action_high: np.ndarray,
) -> tuple[np.ndarray, int, int, bool]:
    if (
        not args.final_insert_adapter_lift_pulse_enabled
        or not adapter_active
        or step is None
    ):
        return np.asarray(action, dtype=np.float32), 0, last_pulse_step, False

    remaining = int(pulse_steps_remaining)
    if remaining <= 0:
        enough_active_steps = (
            active_streak >= args.final_insert_adapter_lift_pulse_active_steps
        )
        enough_stall_steps = (
            step.guard_final_servo_stall_steps
            >= args.final_insert_adapter_lift_pulse_stall_steps
        )
        period_elapsed = (
            step_index - last_pulse_step
            >= args.final_insert_adapter_lift_pulse_period_steps
        )
        if enough_active_steps and enough_stall_steps and period_elapsed:
            remaining = args.final_insert_adapter_lift_pulse_steps
            last_pulse_step = step_index

    if remaining <= 0:
        return np.asarray(action, dtype=np.float32), 0, last_pulse_step, False

    pulsed_action = np.asarray(action, dtype=np.float64).copy().reshape(3)
    pulsed_action[2] = float(
        np.clip(
            args.final_insert_adapter_lift_pulse_z_action,
            action_low[2],
            action_high[2],
        )
    )
    return (
        np.clip(pulsed_action, action_low, action_high).astype(np.float32),
        remaining - 1,
        last_pulse_step,
        True,
    )


def maybe_apply_final_insert_macro_recovery(
    *,
    args: argparse.Namespace,
    action: np.ndarray,
    info: dict[str, Any],
    step: GuardedPolicyStep | None,
    state: FinalInsertMacroRecoveryState,
    action_low: np.ndarray,
    action_high: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, bool, bool, str, int, int, str]:
    base_action = np.asarray(action, dtype=np.float32)
    recovery_action = np.zeros(3, dtype=np.float32)
    triggered = False
    reason = "inactive"

    if state.phase == "inactive":
        candidate, reason = final_insert_macro_recovery_candidate(
            args=args,
            info=info,
            step=step,
        )
        if candidate:
            state.active_streak += 1
        else:
            state.active_streak = 0
        wall_count = int(info.get("peg_hole_contact_wall_count", 0))
        enough_contact = (
            not args.final_insert_macro_recovery_wall_contact_required
            or wall_count > 0
        )
        enough_stall = (
            step is not None
            and step.guard_final_servo_stall_steps
            >= args.final_insert_macro_recovery_min_stall_steps
        )
        enough_active = (
            state.active_streak >= args.final_insert_macro_recovery_min_active_steps
        )
        under_attempt_limit = (
            state.attempts < args.final_insert_macro_recovery_max_attempts
        )
        if (
            candidate
            and under_attempt_limit
            and enough_active
            and enough_stall
            and enough_contact
        ):
            state.attempts += 1
            state.phase = "lift"
            state.phase_steps_remaining = int(args.final_insert_macro_recovery_lift_steps)
            triggered = True
        else:
            if candidate and not under_attempt_limit:
                reason = "max_attempts"
            elif candidate and not enough_active:
                reason = "active_steps"
            elif candidate and not enough_stall:
                reason = "stall_steps"
            elif candidate and not enough_contact:
                reason = "no_wall_contact"
            return base_action, recovery_action, False, False, "inactive", state.attempts, 0, reason
    else:
        dist_xy = float(info["dist_xy"])
        final_servo_active = step is not None and bool(step.guard_final_servo_active)
        abort_for_xy = dist_xy > args.final_insert_macro_recovery_abort_xy
        abort_for_final_servo = (
            args.final_insert_macro_recovery_abort_when_final_servo_inactive
            and not final_servo_active
        )
        if state.phase != "abort_lift" and (abort_for_xy or abort_for_final_servo):
            state.phase = "abort_lift"
            state.phase_steps_remaining = int(
                args.final_insert_macro_recovery_abort_lift_steps
            )
            if abort_for_xy:
                reason = "abort_xy"
            else:
                reason = "abort_final_servo_inactive"
        elif state.phase != "abort_lift":
            reason = "active"

    recovery_action, active, phase, attempt, remaining = final_insert_macro_recovery_action(
        args=args,
        info=info,
        state=state,
        action_low=action_low,
        action_high=action_high,
    )
    if not active:
        return base_action, recovery_action, False, triggered, phase, attempt, remaining, reason
    return recovery_action, recovery_action, True, triggered, phase, attempt, remaining, reason


def shuffled_image_observation(
    obs: Any,
    *,
    target: str,
    rng: np.random.Generator,
    shuffle_bank: list[Any],
) -> Any:
    if shuffle_bank:
        index = int(rng.integers(0, len(shuffle_bank)))
        source = clone_observation(shuffle_bank[index])
    else:
        source = black_like(obs, target=target)
    shuffle_bank.append(clone_observation(obs))
    if target == "all":
        return preserve_non_image_values(source, obs)
    if isinstance(obs, dict):
        ablated = clone_observation(obs)
        if target in obs:
            if isinstance(source, dict) and target in source:
                ablated[target] = clone_observation(source[target])
            else:
                ablated[target] = np.zeros_like(np.asarray(obs[target]))
        return ablated
    return preserve_non_image_values(source, obs)


def ablate_control_state(
    obs: Any,
    *,
    mode: str,
    rng: np.random.Generator,
    shuffle_bank: list[np.ndarray],
) -> Any:
    if mode == "normal":
        return obs
    if not isinstance(obs, dict) or "control_state" not in obs:
        return obs
    ablated = dict(obs)
    control_state = np.asarray(obs["control_state"])
    if mode == "zero":
        ablated["control_state"] = np.zeros_like(control_state)
    elif mode == "noise":
        ablated["control_state"] = rng.normal(
            loc=0.0,
            scale=1.0,
            size=control_state.shape,
        ).astype(control_state.dtype, copy=False)
    elif mode == "shuffle":
        if shuffle_bank:
            index = int(rng.integers(0, len(shuffle_bank)))
            ablated["control_state"] = shuffle_bank[index].copy()
        else:
            ablated["control_state"] = np.zeros_like(control_state)
        shuffle_bank.append(control_state.copy())
    else:
        raise ValueError(f"Unknown control-state ablation mode: {mode}")
    return ablated


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def range_text(values: tuple[Any, Any]) -> str:
    return f"{values[0]}:{values[1]}"


def vector3_columns(prefix: str, value: Any) -> dict[str, float]:
    array = np.asarray(value, dtype=np.float64).reshape(-1)
    if array.size != 3:
        raise ValueError(f"{prefix} must contain exactly 3 values.")
    return {
        f"{prefix}_x": float(array[0]),
        f"{prefix}_y": float(array[1]),
        f"{prefix}_z": float(array[2]),
    }


def maybe_vector3_columns(prefix: str, value: Any | None) -> dict[str, float]:
    if value is None:
        return {
            f"{prefix}_x": float("nan"),
            f"{prefix}_y": float("nan"),
            f"{prefix}_z": float("nan"),
        }
    return vector3_columns(prefix, value)


def episode_matches_step_trace_filter(outcome: str, outcome_filter: str) -> bool:
    if outcome_filter == "any":
        return True
    if outcome_filter == "success":
        return outcome == "success"
    if outcome_filter == "collision":
        return outcome == "collision"
    if outcome_filter == "timeout":
        return outcome == "timeout"
    if outcome_filter == "failure":
        return outcome != "success"
    raise ValueError(f"Unknown step trace outcome filter: {outcome_filter}")


def build_step_trace_row(
    *,
    scenario: Scenario,
    args: argparse.Namespace,
    episode: int,
    episode_seed: int,
    outcome: str,
    pre_info: dict[str, Any],
    post_info: dict[str, Any],
    policy_action: np.ndarray,
    final_action: np.ndarray,
    step: GuardedPolicyStep | None,
    guard_enabled: bool,
    guarded: bool,
    step_index: int,
    base_policy_action: np.ndarray | None = None,
    approach_adapter_residual: np.ndarray | None = None,
    approach_adapter_active: bool = False,
    final_insert_adapter_raw_action: np.ndarray | None = None,
    final_insert_adapter_action: np.ndarray | None = None,
    final_insert_adapter_active: bool = False,
    final_insert_adapter_reason: str = "inactive",
    final_insert_adapter_lift_pulse_active: bool = False,
    final_insert_adapter_lift_pulse_steps_remaining: int = 0,
    final_insert_macro_recovery_action: np.ndarray | None = None,
    final_insert_macro_recovery_active: bool = False,
    final_insert_macro_recovery_triggered: bool = False,
    final_insert_macro_recovery_phase: str = "inactive",
    final_insert_macro_recovery_reason: str = "inactive",
    final_insert_macro_recovery_attempt: int = 0,
    final_insert_macro_recovery_steps_remaining: int = 0,
    guard_square_pose_yaw_align_active: bool = False,
    visual_yaw_align_result: VisualYawAlignResult | None = None,
) -> dict[str, Any]:
    pre_tip = np.asarray(pre_info["peg_tip_pos"], dtype=np.float64)
    pre_target = np.asarray(pre_info["target_pos"], dtype=np.float64)
    post_tip = np.asarray(post_info["peg_tip_pos"], dtype=np.float64)
    post_target = np.asarray(post_info["target_pos"], dtype=np.float64)
    pre_dist_xy = float(pre_info["dist_xy"])
    pre_dist_z = float(pre_info["dist_z"])
    post_dist_xy = float(post_info["dist_xy"])
    post_dist_z = float(post_info["dist_z"])
    pre_z_above_target = float(pre_tip[2] - pre_target[2])
    post_z_above_target = float(post_tip[2] - post_target[2])
    step_guard = step is not None
    base_policy = (
        np.asarray(policy_action, dtype=np.float64)
        if base_policy_action is None
        else np.asarray(base_policy_action, dtype=np.float64)
    )
    adapter_residual = (
        np.zeros(3, dtype=np.float64)
        if approach_adapter_residual is None
        else np.asarray(approach_adapter_residual, dtype=np.float64)
    )
    final_insert_raw = (
        np.zeros(3, dtype=np.float64)
        if final_insert_adapter_raw_action is None
        else np.asarray(final_insert_adapter_raw_action, dtype=np.float64)
    )
    final_insert_action = (
        np.zeros(3, dtype=np.float64)
        if final_insert_adapter_action is None
        else np.asarray(final_insert_adapter_action, dtype=np.float64)
    )
    visual_yaw = visual_yaw_align_result or VisualYawAlignResult()
    visual_yaw_pred = visual_yaw.prediction
    final_insert_macro_action = (
        np.zeros(3, dtype=np.float64)
        if final_insert_macro_recovery_action is None
        else np.asarray(final_insert_macro_recovery_action, dtype=np.float64)
    )
    row: dict[str, Any] = {
        "scenario": scenario.name,
        "level": scenario.level,
        "control_mode": args.control_mode,
        "image_ablation": args.image_ablation,
        "image_ablation_target": args.image_ablation_target,
        "control_state_ablation": args.control_state_ablation,
        "episode": episode,
        "seed": episode_seed,
        "episode_outcome": outcome,
        "step": step_index,
        "pre_step_count": int(pre_info["step_count"]),
        "post_step_count": int(post_info["step_count"]),
        "terminated": bool(post_info["insertion_success"] or post_info["collision"]),
        "truncated": bool(post_info["step_count"] >= args.max_steps and not post_info["insertion_success"]),
        "success": bool(post_info["insertion_success"]),
        "collision": bool(post_info["collision"]),
        "collision_contact_count": int(post_info.get("collision_contact_count", 0)),
        "collision_contact_pairs": str(post_info.get("collision_contact_pairs", "")),
        "peg_hole_contact_count": int(post_info.get("peg_hole_contact_count", 0)),
        "peg_hole_contact_pairs": str(post_info.get("peg_hole_contact_pairs", "")),
        "peg_hole_contact_wall_count": int(post_info.get("peg_hole_contact_wall_count", 0)),
        "peg_hole_contact_plate_count": int(post_info.get("peg_hole_contact_plate_count", 0)),
        "peg_hole_contact_has_wall": bool(post_info.get("peg_hole_contact_has_wall", False)),
        "peg_hole_contact_has_plate": bool(post_info.get("peg_hole_contact_has_plate", False)),
        "peg_hole_contact_hole_plate": int(post_info.get("peg_hole_contact_hole_plate", 0)),
        "peg_hole_contact_hole_north": int(post_info.get("peg_hole_contact_hole_north", 0)),
        "peg_hole_contact_hole_south": int(post_info.get("peg_hole_contact_hole_south", 0)),
        "peg_hole_contact_hole_east": int(post_info.get("peg_hole_contact_hole_east", 0)),
        "peg_hole_contact_hole_west": int(post_info.get("peg_hole_contact_hole_west", 0)),
        "peg_hole_contact_min_dist": float(post_info.get("peg_hole_contact_min_dist", np.nan)),
        "peg_hole_contact_max_dist": float(post_info.get("peg_hole_contact_max_dist", np.nan)),
        "timeout": bool(post_info["step_count"] >= args.max_steps and not post_info["insertion_success"]),
        "pre_dist_xy": pre_dist_xy,
        "pre_dist_z": pre_dist_z,
        "pre_z_above_target": pre_z_above_target,
        **vector3_columns("pre_peg_tip", pre_tip),
        **vector3_columns("pre_target", pre_target),
        "post_dist_xy": post_dist_xy,
        "post_dist_z": post_dist_z,
        "post_z_above_target": post_z_above_target,
        **vector3_columns("post_peg_tip", post_tip),
        **vector3_columns("post_target", post_target),
        "dist_xy_delta": pre_dist_xy - post_dist_xy,
        "dist_z_delta": pre_dist_z - post_dist_z,
        "tip_z_delta": float(post_tip[2] - pre_tip[2]),
        "guard_enabled": guard_enabled,
        "guard_active": bool(step.guard_active) if step_guard else guarded,
        "guarded": guarded,
        "guard_should_activate": bool(step.guard_should_activate) if step_guard else False,
        "guard_can_activate": bool(step.guard_can_activate) if step_guard else False,
        "guard_activated": bool(step.guard_activated) if step_guard else False,
        "guard_down_blocked": bool(step.guard_down_blocked) if step_guard else False,
        "guard_steps_since_reset": int(step.guard_steps_since_reset) if step_guard else step_index,
        "guard_dist_xy": float(step.guard_dist_xy) if step_guard else pre_dist_xy,
        "guard_z_above_target": float(step.guard_z_above_target) if step_guard else pre_z_above_target,
        "guard_retry_active": bool(step.guard_retry_active) if step_guard else False,
        "guard_retry_triggered": bool(step.guard_retry_triggered) if step_guard else False,
        "guard_retry_count": int(step.guard_retry_count) if step_guard else 0,
        "guard_retry_stall_steps": int(step.guard_retry_stall_steps) if step_guard else 0,
        "guard_retry_active_steps": int(step.guard_retry_active_steps) if step_guard else 0,
        "guard_insert_latched": bool(step.guard_insert_latched) if step_guard else False,
        "guard_insert_latch_activated": bool(step.guard_insert_latch_activated) if step_guard else False,
        "guard_insert_latch_released": bool(step.guard_insert_latch_released) if step_guard else False,
        "guard_insert_latch_steps": int(step.guard_insert_latch_steps) if step_guard else 0,
        "guard_insert_latch_descent_allowed": bool(step.guard_insert_latch_descent_allowed) if step_guard else False,
        "guard_hover_active": bool(step.guard_hover_active) if step_guard else False,
        "guard_hover_stable_steps": int(step.guard_hover_stable_steps) if step_guard else 0,
        "guard_hover_descent_allowed": bool(step.guard_hover_descent_allowed) if step_guard else False,
        "guard_hover_descent_latched": bool(step.guard_hover_descent_latched) if step_guard else False,
        "guard_hover_down_blocked": bool(step.guard_hover_down_blocked) if step_guard else False,
        "guard_near_action_limited": bool(step.guard_near_action_limited) if step_guard else False,
        "guard_fixture_clearance_active": (
            bool(step.guard_fixture_clearance_active) if step_guard else False
        ),
        "guard_fixture_clearance_triggered": (
            bool(step.guard_fixture_clearance_triggered) if step_guard else False
        ),
        "guard_fixture_clearance_released": (
            bool(step.guard_fixture_clearance_released) if step_guard else False
        ),
        "guard_fixture_clearance_phase": (
            str(step.guard_fixture_clearance_phase) if step_guard else "none"
        ),
        "guard_fixture_clearance_steps": (
            int(step.guard_fixture_clearance_steps) if step_guard else 0
        ),
        "guard_fixture_clearance_realign_steps": (
            int(step.guard_fixture_clearance_realign_steps) if step_guard else 0
        ),
        "guard_preinsert_recenter_active": (
            bool(step.guard_preinsert_recenter_active) if step_guard else False
        ),
        "guard_preinsert_recenter_triggered": (
            bool(step.guard_preinsert_recenter_triggered) if step_guard else False
        ),
        "guard_preinsert_recenter_released": (
            bool(step.guard_preinsert_recenter_released) if step_guard else False
        ),
        "guard_preinsert_recenter_steps": (
            int(step.guard_preinsert_recenter_steps) if step_guard else 0
        ),
        "guard_preinsert_recenter_stable_steps": (
            int(step.guard_preinsert_recenter_stable_steps) if step_guard else 0
        ),
        "guard_preinsert_recenter_down_blocked": (
            bool(step.guard_preinsert_recenter_down_blocked) if step_guard else False
        ),
        "guard_approach_recenter_active": (
            bool(step.guard_approach_recenter_active) if step_guard else False
        ),
        "guard_approach_recenter_triggered": (
            bool(step.guard_approach_recenter_triggered) if step_guard else False
        ),
        "guard_approach_recenter_released": (
            bool(step.guard_approach_recenter_released) if step_guard else False
        ),
        "guard_approach_recenter_steps": (
            int(step.guard_approach_recenter_steps) if step_guard else 0
        ),
        "guard_approach_recenter_stable_steps": (
            int(step.guard_approach_recenter_stable_steps) if step_guard else 0
        ),
        "guard_approach_recenter_down_blocked": (
            bool(step.guard_approach_recenter_down_blocked) if step_guard else False
        ),
        "guard_early_approach_assist_active": (
            bool(step.guard_early_approach_assist_active) if step_guard else False
        ),
        "guard_early_approach_assist_triggered": (
            bool(step.guard_early_approach_assist_triggered) if step_guard else False
        ),
        "guard_early_approach_assist_released": (
            bool(step.guard_early_approach_assist_released) if step_guard else False
        ),
        "guard_early_approach_assist_steps": (
            int(step.guard_early_approach_assist_steps) if step_guard else 0
        ),
        "guard_early_approach_assist_down_blocked": (
            bool(step.guard_early_approach_assist_down_blocked) if step_guard else False
        ),
        "guard_stateful_recovery_active": (
            bool(step.guard_stateful_recovery_active) if step_guard else False
        ),
        "guard_stateful_recovery_triggered": (
            bool(step.guard_stateful_recovery_triggered) if step_guard else False
        ),
        "guard_stateful_recovery_released": (
            bool(step.guard_stateful_recovery_released) if step_guard else False
        ),
        "guard_stateful_recovery_exhausted": (
            bool(step.guard_stateful_recovery_exhausted) if step_guard else False
        ),
        "guard_stateful_recovery_phase": (
            str(step.guard_stateful_recovery_phase) if step_guard else "inactive"
        ),
        "guard_stateful_recovery_phase_steps": (
            int(step.guard_stateful_recovery_phase_steps) if step_guard else 0
        ),
        "guard_stateful_recovery_stall_steps": (
            int(step.guard_stateful_recovery_stall_steps) if step_guard else 0
        ),
        "guard_stateful_recovery_stable_steps": (
            int(step.guard_stateful_recovery_stable_steps) if step_guard else 0
        ),
        "guard_stateful_recovery_attempts": (
            int(step.guard_stateful_recovery_attempts) if step_guard else 0
        ),
        "guard_stateful_recovery_down_blocked": (
            bool(step.guard_stateful_recovery_down_blocked) if step_guard else False
        ),
        "guard_final_servo_active": bool(step.guard_final_servo_active) if step_guard else False,
        "guard_final_servo_triggered": (
            bool(step.guard_final_servo_triggered) if step_guard else False
        ),
        "guard_final_servo_rearmed": (
            bool(step.guard_final_servo_rearmed) if step_guard else False
        ),
        "guard_final_servo_recovery_triggered": (
            bool(step.guard_final_servo_recovery_triggered) if step_guard else False
        ),
        "guard_final_servo_exhausted": (
            bool(step.guard_final_servo_exhausted) if step_guard else False
        ),
        "guard_final_servo_phase": (
            str(step.guard_final_servo_phase) if step_guard else "inactive"
        ),
        "guard_final_servo_phase_transition_reason": (
            str(step.guard_final_servo_phase_transition_reason)
            if step_guard
            else "none"
        ),
        "guard_final_servo_phase_steps": (
            int(step.guard_final_servo_phase_steps) if step_guard else 0
        ),
        "guard_final_servo_stable_steps": (
            int(step.guard_final_servo_stable_steps) if step_guard else 0
        ),
        "guard_final_servo_stall_steps": (
            int(step.guard_final_servo_stall_steps) if step_guard else 0
        ),
        "guard_final_servo_low_recenter_stall_steps": (
            int(step.guard_final_servo_low_recenter_stall_steps) if step_guard else 0
        ),
        "guard_final_servo_low_recenter_best_dist_xy": (
            float(step.guard_final_servo_low_recenter_best_dist_xy)
            if step_guard
            and np.isfinite(step.guard_final_servo_low_recenter_best_dist_xy)
            else np.nan
        ),
        "guard_final_servo_retry_count": (
            int(step.guard_final_servo_retry_count) if step_guard else 0
        ),
        "guard_final_servo_rearm_attempts": (
            int(step.guard_final_servo_rearm_attempts) if step_guard else 0
        ),
        "guard_final_servo_rearm_cooldown_steps": (
            int(step.guard_final_servo_rearm_cooldown_steps) if step_guard else 0
        ),
        "guard_final_servo_rearm_stable_steps": (
            int(step.guard_final_servo_rearm_stable_steps) if step_guard else 0
        ),
        "guard_final_servo_descent_allowed": (
            bool(step.guard_final_servo_descent_allowed) if step_guard else False
        ),
        "guard_final_servo_down_blocked": (
            bool(step.guard_final_servo_down_blocked) if step_guard else False
        ),
        "guard_final_servo_square_recovery_active": (
            bool(step.guard_final_servo_square_recovery_active) if step_guard else False
        ),
        "guard_final_servo_square_recovery_triggered": (
            bool(step.guard_final_servo_square_recovery_triggered) if step_guard else False
        ),
        "guard_final_servo_square_recovery_tilt_steps": (
            int(step.guard_final_servo_square_recovery_tilt_steps) if step_guard else 0
        ),
        "guard_final_servo_square_recovery_escape_active": (
            bool(step.guard_final_servo_square_recovery_escape_active)
            if step_guard
            else False
        ),
        "guard_final_servo_square_recovery_escape_triggered": (
            bool(step.guard_final_servo_square_recovery_escape_triggered)
            if step_guard
            else False
        ),
        "guard_final_servo_square_recovery_escape_early_contact_steps": (
            int(step.guard_final_servo_square_recovery_escape_early_contact_steps)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_recovery_escape_early_risk_steps": (
            int(step.guard_final_servo_square_recovery_escape_early_risk_steps)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_recovery_escape_direct_fast_settle_active": (
            bool(
                step.guard_final_servo_square_recovery_escape_direct_fast_settle_active
            )
            if step_guard
            else False
        ),
        "guard_final_servo_square_recovery_escape_late_recenter_descend_active": (
            bool(
                step.guard_final_servo_square_recovery_escape_late_recenter_descend_active
            )
            if step_guard
            else False
        ),
        "guard_final_servo_square_contact_brake_active": (
            bool(step.guard_final_servo_square_contact_brake_active)
            if step_guard
            else False
        ),
        "guard_final_servo_square_contact_brake_triggered": (
            bool(step.guard_final_servo_square_contact_brake_triggered)
            if step_guard
            else False
        ),
        "guard_final_servo_square_contact_brake_wall_steps": (
            int(step.guard_final_servo_square_contact_brake_wall_steps)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_contact_brake_attempts": (
            int(step.guard_final_servo_square_contact_brake_attempts)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_contact_brake_preemptive_hold_active": (
            bool(step.guard_final_servo_square_contact_brake_preemptive_hold_active)
            if step_guard
            else False
        ),
        "guard_final_servo_square_contact_brake_preemptive_hold_triggered": (
            bool(step.guard_final_servo_square_contact_brake_preemptive_hold_triggered)
            if step_guard
            else False
        ),
        "guard_final_servo_square_contact_brake_preemptive_hold_wall_steps": (
            int(step.guard_final_servo_square_contact_brake_preemptive_hold_wall_steps)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy": (
            bool(step.guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy)
            if step_guard
            else False
        ),
        "guard_final_servo_square_fast_settle_clearance_hold_attempts": (
            int(step.guard_final_servo_square_fast_settle_clearance_hold_attempts)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_fast_settle_clean_steps": (
            int(step.guard_final_servo_square_fast_settle_clean_steps)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_fast_settle_low_z_relief_attempts": (
            int(step.guard_final_servo_square_fast_settle_low_z_relief_attempts)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_fast_settle_low_z_stall_relief_attempts": (
            int(
                step.guard_final_servo_square_fast_settle_low_z_stall_relief_attempts
            )
            if step_guard
            else 0
        ),
        "guard_final_servo_square_fast_settle_contact_soft_hold_active": (
            bool(step.guard_final_servo_square_fast_settle_contact_soft_hold_active)
            if step_guard
            else False
        ),
        "guard_final_servo_square_fast_settle_contact_soft_hold_attempts": (
            int(step.guard_final_servo_square_fast_settle_contact_soft_hold_attempts)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_active": (
            bool(
                step.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_active
            )
            if step_guard
            else False
        ),
        "guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_attempts": (
            int(
                step.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_attempts
            )
            if step_guard
            else 0
        ),
        "guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_active": (
            bool(
                step.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_active
            )
            if step_guard
            else False
        ),
        "guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_attempts": (
            int(
                step.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_attempts
            )
            if step_guard
            else 0
        ),
        "guard_final_servo_square_fast_settle_contact_pop_hold_active": (
            bool(step.guard_final_servo_square_fast_settle_contact_pop_hold_active)
            if step_guard
            else False
        ),
        "guard_final_servo_square_fast_settle_contact_pop_hold_attempts": (
            int(step.guard_final_servo_square_fast_settle_contact_pop_hold_attempts)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_fast_settle_no_contact_pop_hold_active": (
            bool(step.guard_final_servo_square_fast_settle_no_contact_pop_hold_active)
            if step_guard
            else False
        ),
        "guard_final_servo_square_fast_settle_no_contact_pop_hold_attempts": (
            int(step.guard_final_servo_square_fast_settle_no_contact_pop_hold_attempts)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_fast_settle_pre_pop_guard_active": (
            bool(step.guard_final_servo_square_fast_settle_pre_pop_guard_active)
            if step_guard
            else False
        ),
        "guard_final_servo_square_fast_settle_pre_pop_guard_attempts": (
            int(step.guard_final_servo_square_fast_settle_pre_pop_guard_attempts)
            if step_guard
            else 0
        ),
        "guard_final_servo_square_fast_settle_pre_pop_limit_active": (
            bool(step.guard_final_servo_square_fast_settle_pre_pop_limit_active)
            if step_guard
            else False
        ),
        "guard_final_servo_square_fast_settle_severe_pop_reapproach_active": (
            bool(
                step.guard_final_servo_square_fast_settle_severe_pop_reapproach_active
            )
            if step_guard
            else False
        ),
        "guard_final_servo_square_fast_settle_severe_pop_reapproach_attempts": (
            int(
                step.guard_final_servo_square_fast_settle_severe_pop_reapproach_attempts
            )
            if step_guard
            else 0
        ),
        "guard_final_servo_square_high_z_descend_low_z_hold_active": (
            bool(step.guard_final_servo_square_high_z_descend_low_z_hold_active)
            if step_guard
            else False
        ),
        "guard_final_servo_square_high_z_descend_low_z_hold_attempts": (
            int(step.guard_final_servo_square_high_z_descend_low_z_hold_attempts)
            if step_guard
            else 0
        ),
        "guard_final_servo_contact_unjam_wall_steps": (
            int(step.guard_final_servo_contact_unjam_wall_steps) if step_guard else 0
        ),
        "guard_final_servo_contact_reinsert_orient_tip_lock_active": (
            bool(step.guard_final_servo_contact_reinsert_orient_tip_lock_active)
            if step_guard
            else False
        ),
        "guard_final_servo_contact_reinsert_orient_tip_lock_drift_xy": (
            float(step.guard_final_servo_contact_reinsert_orient_tip_lock_drift_xy)
            if step_guard
            else 0.0
        ),
        "guard_final_servo_near_miss_steps": (
            int(step.guard_final_servo_near_miss_steps) if step_guard else 0
        ),
        "approach_adapter_active": bool(approach_adapter_active),
        **vector3_columns("approach_adapter_residual", adapter_residual),
        "final_insert_adapter_active": bool(final_insert_adapter_active),
        "final_insert_adapter_reason": str(final_insert_adapter_reason),
        **vector3_columns("final_insert_adapter_raw_action", final_insert_raw),
        **vector3_columns("final_insert_adapter_action", final_insert_action),
        "final_insert_adapter_lift_pulse_active": bool(
            final_insert_adapter_lift_pulse_active
        ),
        "final_insert_adapter_lift_pulse_steps_remaining": int(
            final_insert_adapter_lift_pulse_steps_remaining
        ),
        "final_insert_macro_recovery_active": bool(final_insert_macro_recovery_active),
        "final_insert_macro_recovery_triggered": bool(
            final_insert_macro_recovery_triggered
        ),
        "final_insert_macro_recovery_phase": str(final_insert_macro_recovery_phase),
        "final_insert_macro_recovery_reason": str(final_insert_macro_recovery_reason),
        "final_insert_macro_recovery_attempt": int(final_insert_macro_recovery_attempt),
        "final_insert_macro_recovery_steps_remaining": int(
            final_insert_macro_recovery_steps_remaining
        ),
        **vector3_columns("final_insert_macro_recovery_action", final_insert_macro_action),
        **vector3_columns("base_policy_action", base_policy),
        **vector3_columns("policy_action", policy_action),
        **maybe_vector3_columns("guarded_action", None if step is None or step.guarded_action is None else step.guarded_action),
        **vector3_columns("final_action", final_action),
        **vector3_columns("commanded_action", post_info["commanded_action"]),
        **vector3_columns("applied_action", post_info["applied_action"]),
        "action_tracking_error": float(post_info["action_tracking_error"]),
        **vector3_columns("action_tip_delta_error", post_info["action_tip_delta_error"]),
        "ik_control_mode": str(post_info.get("ik_control_mode", "")),
        "ik_orientation_weight": float(post_info.get("ik_orientation_weight", np.nan)),
        "ik_target_error": float(post_info.get("ik_target_error", np.nan)),
        "ik_orientation_error": float(post_info.get("ik_orientation_error", np.nan)),
        "pose_ik_target_raw_yaw_deg": float(
            post_info.get("pose_ik_target_raw_yaw_deg", np.nan)
        ),
        "pose_ik_target_square_yaw_error_deg": float(
            post_info.get("pose_ik_target_square_yaw_error_deg", np.nan)
        ),
        "guard_square_pose_yaw_align_active": bool(
            guard_square_pose_yaw_align_active
        ),
        "guard_visual_yaw_align_active": bool(visual_yaw.active),
        "guard_visual_yaw_align_applied": bool(visual_yaw.applied),
        "guard_visual_yaw_align_blocked_down": bool(visual_yaw.blocked_down),
        "guard_visual_yaw_align_aligned_descent": bool(
            visual_yaw.aligned_descent
        ),
        "guard_visual_yaw_align_aligned_descent_stable_steps": int(
            visual_yaw.aligned_descent_stable_steps
        ),
        "guard_visual_yaw_align_low_z_late_finish_descent": bool(
            visual_yaw.low_z_late_finish_descent
        ),
        "guard_visual_yaw_align_target_hold": bool(visual_yaw.target_hold),
        "guard_visual_yaw_align_low_visibility_brake": bool(
            visual_yaw.low_visibility_brake
        ),
        "guard_visual_yaw_align_large_xy_low_z_brake": bool(
            visual_yaw.large_xy_low_z_brake
        ),
        "guard_visual_yaw_align_descent_abort_active": bool(
            visual_yaw.descent_abort_active
        ),
        "guard_visual_yaw_align_descent_abort_triggered": bool(
            visual_yaw.descent_abort_triggered
        ),
        "guard_visual_yaw_align_descent_abort_phase": str(
            visual_yaw.descent_abort_phase
        ),
        "guard_visual_yaw_align_descent_abort_attempts": int(
            visual_yaw.descent_abort_attempts
        ),
        "guard_visual_yaw_align_reacquire_active": bool(
            visual_yaw.reacquire_active
        ),
        "guard_visual_yaw_align_reacquire_triggered": bool(
            visual_yaw.reacquire_triggered
        ),
        "guard_visual_yaw_align_reacquire_phase": str(
            visual_yaw.reacquire_phase
        ),
        "guard_visual_yaw_align_reacquire_attempts": int(
            visual_yaw.reacquire_attempts
        ),
        "guard_visual_yaw_align_wrong_basin_hold_active": bool(
            visual_yaw.wrong_basin_hold_active
        ),
        "guard_visual_yaw_align_wrong_basin_hold_triggered": bool(
            visual_yaw.wrong_basin_hold_triggered
        ),
        "guard_visual_yaw_align_wrong_basin_hold_steps_remaining": int(
            visual_yaw.wrong_basin_hold_steps_remaining
        ),
        "guard_visual_yaw_align_wrong_basin_hold_attempts": int(
            visual_yaw.wrong_basin_hold_attempts
        ),
        "guard_visual_yaw_align_low_z_lateral_pop_recovery_active": bool(
            visual_yaw.low_z_lateral_pop_recovery_active
        ),
        "guard_visual_yaw_align_low_z_lateral_pop_recovery_triggered": bool(
            visual_yaw.low_z_lateral_pop_recovery_triggered
        ),
        "guard_visual_yaw_align_low_z_lateral_pop_recovery_phase": str(
            visual_yaw.low_z_lateral_pop_recovery_phase
        ),
        "guard_visual_yaw_align_low_z_lateral_pop_recovery_attempts": int(
            visual_yaw.low_z_lateral_pop_recovery_attempts
        ),
        "guard_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining": int(
            visual_yaw.low_z_lateral_pop_recovery_steps_remaining
        ),
        "guard_visual_yaw_align_reason": str(visual_yaw.reason),
        "guard_visual_yaw_align_profile": (
            str(visual_yaw_pred.profile) if visual_yaw_pred is not None else ""
        ),
        "guard_visual_yaw_align_pred_signed_error_deg": (
            float(visual_yaw_pred.signed_error_deg)
            if visual_yaw_pred is not None
            else np.nan
        ),
        "guard_visual_yaw_align_pred_abs_error_deg": (
            float(visual_yaw_pred.abs_error_deg)
            if visual_yaw_pred is not None
            else np.nan
        ),
        "guard_visual_yaw_align_correction_deg": float(visual_yaw.correction_deg),
        "guard_visual_yaw_align_raw_norm": (
            float(visual_yaw_pred.raw_norm) if visual_yaw_pred is not None else np.nan
        ),
        "guard_visual_yaw_align_cam_std": (
            float(visual_yaw_pred.cam_std) if visual_yaw_pred is not None else np.nan
        ),
        "guard_visual_yaw_align_crop_std": (
            float(visual_yaw_pred.crop_std) if visual_yaw_pred is not None else np.nan
        ),
        "ik_iterations": int(post_info.get("ik_iterations", 0)),
        "peg_tilt_angle_deg": float(post_info.get("peg_tilt_angle_deg", np.nan)),
        "joint_limit_min_normalized_margin": float(
            post_info.get("joint_limit_min_normalized_margin", np.nan)
        ),
        "joint_damping_multiplier": float(post_info.get("joint_damping_multiplier", 1.0)),
        "actuator_kp_multiplier": float(post_info.get("actuator_kp_multiplier", 1.0)),
        "control_action_scale_multiplier": float(post_info.get("control_action_scale_multiplier", 1.0)),
        "control_action_noise_std": float(post_info.get("control_action_noise_std", 0.0)),
        "control_action_delay": int(post_info.get("control_action_delay", 0)),
        "control_action_filter_alpha": float(post_info.get("control_action_filter_alpha", 1.0)),
        "geometry_profile": str(post_info.get("geometry_profile", "")),
        "geometry_name": str(post_info.get("geometry_name", "")),
        "peg_shape": str(post_info.get("peg_shape", "")),
        "hole_shape": str(post_info.get("hole_shape", "")),
        "hole_half_size": float(post_info.get("hole_half_size", np.nan)),
        "peg_radius": float(post_info.get("peg_radius", np.nan)),
        "hole_clearance": float(post_info.get("hole_clearance", np.nan)),
        "success_shape_yaw_required": bool(
            post_info.get("success_shape_yaw_required", False)
        ),
        "success_shape_yaw_ok": bool(post_info.get("success_shape_yaw_ok", True)),
        "success_shape_yaw_error_deg": float(
            post_info.get("success_shape_yaw_error_deg", np.nan)
        ),
        "success_shape_yaw_tolerance_deg": float(
            post_info.get("success_shape_yaw_tolerance_deg", np.nan)
        ),
        "shape_yaw_clearance": float(post_info.get("shape_yaw_clearance", np.nan)),
        "shape_yaw_signed_error_deg": float(
            post_info.get("shape_yaw_signed_error_deg", np.nan)
        ),
        "shape_yaw_error_deg": float(post_info.get("shape_yaw_error_deg", np.nan)),
        "square_peg_raw_yaw_deg": float(post_info.get("square_peg_raw_yaw_deg", np.nan)),
        "square_peg_yaw_error_deg": float(post_info.get("square_peg_yaw_error_deg", np.nan)),
        "square_peg_topdown_half_width_x": float(
            post_info.get("square_peg_topdown_half_width_x", np.nan)
        ),
        "square_peg_topdown_half_width_y": float(
            post_info.get("square_peg_topdown_half_width_y", np.nan)
        ),
        "square_peg_topdown_max_half_width": float(
            post_info.get("square_peg_topdown_max_half_width", np.nan)
        ),
        "square_peg_topdown_clearance_margin": float(
            post_info.get("square_peg_topdown_clearance_margin", np.nan)
        ),
        "square_peg_tilt_lateral_extent_x": float(
            post_info.get("square_peg_tilt_lateral_extent_x", np.nan)
        ),
        "square_peg_tilt_lateral_extent_y": float(
            post_info.get("square_peg_tilt_lateral_extent_y", np.nan)
        ),
        "square_peg_tilt_lateral_extent_max": float(
            post_info.get("square_peg_tilt_lateral_extent_max", np.nan)
        ),
        "square_peg_tilted_half_width_x": float(
            post_info.get("square_peg_tilted_half_width_x", np.nan)
        ),
        "square_peg_tilted_half_width_y": float(
            post_info.get("square_peg_tilted_half_width_y", np.nan)
        ),
        "square_peg_tilted_max_half_width": float(
            post_info.get("square_peg_tilted_max_half_width", np.nan)
        ),
        "square_peg_tilted_clearance_margin": float(
            post_info.get("square_peg_tilted_clearance_margin", np.nan)
        ),
    }
    return row


def guard_near_control_active(
    step: GuardedPolicyStep | None,
    args: argparse.Namespace,
) -> bool:
    if step is None:
        return False
    return (
        bool(step.guard_stateful_recovery_active)
        or bool(step.guard_approach_recenter_active)
        or bool(step.guard_fixture_clearance_active)
        or bool(step.guard_final_servo_active)
        or (
            bool(step.guard_active)
            and step.guard_dist_xy <= args.guard_final_servo_release_xy
            and step.guard_z_above_target <= args.guard_start_z
        )
    )


def square_pose_yaw_align_active(
    step: GuardedPolicyStep | None,
    pre_info: dict[str, Any],
    args: argparse.Namespace,
) -> bool:
    if not args.guard_square_pose_yaw_align_enabled:
        return False
    if step is None or not bool(step.guard_final_servo_active):
        return False
    if str(pre_info.get("peg_shape", "")) != "square":
        return False
    if str(pre_info.get("hole_shape", "")) != "square":
        return False
    return str(step.guard_final_servo_phase) in SQUARE_POSE_YAW_ALIGN_PHASES


def apply_guard_square_pose_yaw_align(
    env: PegInHoleMujocoEnv,
    step: GuardedPolicyStep | None,
    pre_info: dict[str, Any],
    args: argparse.Namespace,
) -> bool:
    env.reset_pose_ik_target_xmat()
    active = square_pose_yaw_align_active(step, pre_info, args)
    if not active:
        return False
    env.set_pose_ik_target_to_nearest_square_hole_yaw()
    env.set_ik_control_mode(args.guard_square_pose_yaw_align_ik_control_mode)
    env.set_ik_orientation_weight(
        args.guard_square_pose_yaw_align_ik_orientation_weight
    )
    return True


def visual_yaw_align_near_control_active(
    step: GuardedPolicyStep | None,
    args: argparse.Namespace,
) -> bool:
    if args.guard_visual_yaw_align_activation_mode == "near_control":
        return guard_near_control_active(step, args)
    return step is not None and bool(step.guard_final_servo_active)


def visual_yaw_align_has_visible_prediction(reason: str) -> bool:
    return reason in {
        "applied",
        "deadband",
        "yaw_ok_recenter",
        "target_hold_deadband",
        "target_hold_yaw_ok_recenter",
    }


def visual_yaw_prediction_has_visible_stats(
    prediction: VisualYawPrediction | None,
    args: argparse.Namespace,
) -> bool:
    if prediction is None or not prediction.valid:
        return False
    return bool(
        prediction.raw_norm >= args.guard_visual_yaw_align_min_raw_norm
        and prediction.cam_std >= args.guard_visual_yaw_align_min_cam_std
        and prediction.crop_std >= args.guard_visual_yaw_align_min_crop_std
    )


def wrapped_visual_yaw_delta_deg(delta_deg: float, profile: str) -> float:
    period_deg = float(PROFILE_PERIOD_DEG.get(profile, 360.0))
    if not np.isfinite(delta_deg) or not np.isfinite(period_deg) or period_deg <= 0.0:
        return float("nan")
    return float((delta_deg + 0.5 * period_deg) % period_deg - 0.5 * period_deg)


def visual_yaw_reacquire_delta_stable(
    history: list[float],
    *,
    profile: str,
    window: int,
    max_delta_deg: float,
) -> bool:
    if window <= 1:
        return bool(history)
    if len(history) < window:
        return False
    values = history[-window:]
    for previous, current in zip(values, values[1:]):
        delta = wrapped_visual_yaw_delta_deg(current - previous, profile)
        if not np.isfinite(delta) or abs(delta) > max_delta_deg:
            return False
    return True


def apply_guard_visual_yaw_align(
    env: PegInHoleMujocoEnv,
    estimator: VisualYawRuntime | None,
    obs: Any,
    step: GuardedPolicyStep | None,
    pre_info: dict[str, Any],
    args: argparse.Namespace,
) -> VisualYawAlignResult:
    if not args.guard_visual_yaw_align_enabled:
        return VisualYawAlignResult(reason="disabled")
    if estimator is None:
        return VisualYawAlignResult(reason="missing_estimator")
    if not isinstance(obs, dict):
        return VisualYawAlignResult(reason="non_dict_obs")
    profile = str(pre_info.get("geometry_name", pre_info.get("geometry_profile", "")))
    if profile not in set(args.guard_visual_yaw_align_profiles):
        return VisualYawAlignResult(reason=f"profile_not_enabled:{profile}")
    if not visual_yaw_align_near_control_active(step, args):
        return VisualYawAlignResult(reason="inactive_phase")

    dist_xy = float(pre_info.get("dist_xy", np.inf))
    target_pos = np.asarray(pre_info.get("target_pos", [np.nan, np.nan, np.nan]), dtype=np.float64)
    peg_tip_pos = np.asarray(pre_info.get("peg_tip_pos", [np.nan, np.nan, np.nan]), dtype=np.float64)
    z_above_target = float(peg_tip_pos[2] - target_pos[2])
    if not np.isfinite(dist_xy) or dist_xy > args.guard_visual_yaw_align_max_xy:
        return VisualYawAlignResult(reason="xy_gate")
    if (
        not np.isfinite(z_above_target)
        or z_above_target < args.guard_visual_yaw_align_min_z
        or z_above_target > args.guard_visual_yaw_align_max_z
    ):
        return VisualYawAlignResult(reason="z_gate")
    wall_contact_count = int(pre_info.get("peg_hole_contact_wall_count", 0))
    if wall_contact_count > args.guard_visual_yaw_align_max_wall_contact:
        return VisualYawAlignResult(reason="contact_gate")

    prediction = estimator.predict(obs, profile=profile)
    if not prediction.valid:
        return VisualYawAlignResult(reason=prediction.reason, prediction=prediction)
    if prediction.raw_norm < args.guard_visual_yaw_align_min_raw_norm:
        return VisualYawAlignResult(reason="raw_norm_gate", prediction=prediction)
    if prediction.cam_std < args.guard_visual_yaw_align_min_cam_std:
        return VisualYawAlignResult(reason="cam_std_gate", prediction=prediction)
    if prediction.crop_std < args.guard_visual_yaw_align_min_crop_std:
        return VisualYawAlignResult(reason="crop_std_gate", prediction=prediction)
    if prediction.abs_error_deg < args.guard_visual_yaw_align_deadband_deg:
        if (
            args.guard_visual_yaw_align_recenter_after_yaw_enabled
            and dist_xy > args.guard_visual_yaw_align_recenter_release_xy
        ):
            return VisualYawAlignResult(
                active=True,
                applied=False,
                blocked_down=bool(args.guard_visual_yaw_align_recenter_block_descent),
                reason="yaw_ok_recenter",
                prediction=prediction,
            )
        return VisualYawAlignResult(reason="deadband", prediction=prediction)

    correction_deg = float(
        np.clip(
            -prediction.signed_error_deg,
            -args.guard_visual_yaw_align_max_correction_deg,
            args.guard_visual_yaw_align_max_correction_deg,
        )
    )
    env.set_pose_ik_target_by_planar_yaw_correction(correction_deg)
    env.set_ik_control_mode(args.guard_visual_yaw_align_ik_control_mode)
    env.set_ik_orientation_weight(args.guard_visual_yaw_align_ik_orientation_weight)
    block_down = bool(
        args.guard_visual_yaw_align_block_descent
        and prediction.abs_error_deg >= args.guard_visual_yaw_align_block_descent_deg
    )
    return VisualYawAlignResult(
        active=True,
        applied=True,
        blocked_down=block_down,
        reason="applied",
        prediction=prediction,
        correction_deg=correction_deg,
    )


def should_start_guard_visual_yaw_reacquire(
    *,
    step: GuardedPolicyStep | None,
    pre_info: dict[str, Any],
    result: VisualYawAlignResult,
    pred_history: list[float] | None,
    attempts: int,
    active_phase: str,
    dist_xy: float,
    z_above_target: float,
    args: argparse.Namespace,
) -> bool:
    if not args.guard_visual_yaw_align_reacquire_enabled:
        return False
    if args.guard_visual_yaw_align_reacquire_max_attempts <= 0:
        return False
    if attempts >= args.guard_visual_yaw_align_reacquire_max_attempts:
        return False
    if active_phase != "inactive":
        return False
    profile = str(pre_info.get("geometry_name", pre_info.get("geometry_profile", "")))
    if profile not in set(args.guard_visual_yaw_align_reacquire_profiles):
        return False
    if not visual_yaw_align_near_control_active(step, args):
        return False
    if int(pre_info.get("step_count", 0)) < args.guard_visual_yaw_align_reacquire_min_step:
        return False
    if not np.isfinite(dist_xy) or not np.isfinite(z_above_target):
        return False
    if (
        dist_xy < args.guard_visual_yaw_align_reacquire_trigger_min_xy
        or dist_xy > args.guard_visual_yaw_align_reacquire_trigger_max_xy
    ):
        return False
    if (
        z_above_target < args.guard_visual_yaw_align_reacquire_trigger_min_z
        or z_above_target > args.guard_visual_yaw_align_reacquire_trigger_max_z
    ):
        return False
    wall_contact_count = int(pre_info.get("peg_hole_contact_wall_count", 0))
    if wall_contact_count > args.guard_visual_yaw_align_max_wall_contact:
        return False

    prediction = result.prediction
    prediction_visible_ok = bool(
        not args.guard_visual_yaw_align_reacquire_trigger_require_visible
        or visual_yaw_prediction_has_visible_stats(prediction, args)
    )
    prediction_delta_ok = bool(
        not args.guard_visual_yaw_align_reacquire_trigger_require_stable_delta
        or visual_yaw_reacquire_delta_stable(
            pred_history or [],
            profile=profile,
            window=args.guard_visual_yaw_align_reacquire_trigger_stable_window,
            max_delta_deg=args.guard_visual_yaw_align_reacquire_trigger_max_delta_deg,
        )
    )
    prediction_large = bool(
        prediction is not None
        and prediction.valid
        and prediction.abs_error_deg
        >= args.guard_visual_yaw_align_reacquire_trigger_min_pred_yaw_deg
        and prediction_visible_ok
        and prediction_delta_ok
    )
    xy_gate_large = bool(
        args.guard_visual_yaw_align_reacquire_xy_gate_trigger_enabled
        and prediction_visible_ok
        and prediction_delta_ok
        and result.reason
        in {
            "xy_gate",
            "latch_xy_gate",
            "target_hold_xy_gate",
        }
        and dist_xy >= args.guard_visual_yaw_align_reacquire_xy_gate_min_xy
    )
    return prediction_large or xy_gate_large


def should_start_guard_visual_yaw_low_z_lateral_pop_recovery(
    *,
    step: GuardedPolicyStep | None,
    pre_info: dict[str, Any],
    attempts: int,
    active_phase: str,
    dist_xy: float,
    prev_dist_xy: float,
    z_above_target: float,
    args: argparse.Namespace,
) -> bool:
    if not args.guard_visual_yaw_align_low_z_lateral_pop_recovery_enabled:
        return False
    if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_max_attempts <= 0:
        return False
    if attempts >= args.guard_visual_yaw_align_low_z_lateral_pop_recovery_max_attempts:
        return False
    if active_phase != "inactive":
        return False
    profile = str(pre_info.get("geometry_name", pre_info.get("geometry_profile", "")))
    if profile not in set(args.guard_visual_yaw_align_low_z_lateral_pop_recovery_profiles):
        return False
    if not visual_yaw_align_near_control_active(step, args):
        return False
    if (
        int(pre_info.get("step_count", 0))
        < args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_min_step
    ):
        return False
    if not np.isfinite(dist_xy) or not np.isfinite(z_above_target):
        return False
    if (
        z_above_target
        > args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_max_z
    ):
        return False

    current_large = bool(
        dist_xy
        >= args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_min_xy
    )
    sudden_pop = bool(
        np.isfinite(prev_dist_xy)
        and prev_dist_xy
        <= args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_prev_xy
        and dist_xy - prev_dist_xy
        >= args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_xy_jump
    )
    return current_large or sudden_pop


def apply_guard_near_ik_orientation_weight(
    env: PegInHoleMujocoEnv,
    step: GuardedPolicyStep | None,
    args: argparse.Namespace,
) -> bool:
    env.set_ik_control_mode(args.ik_control_mode)
    if (
        args.guard_final_servo_tip_priority_ik_enabled
        and step is not None
        and step.guard_final_servo_active
    ):
        env.set_ik_control_mode("pose_tip_priority")
    contact_unjam_active = (
        step is not None and str(step.guard_final_servo_phase).startswith("contact_unjam")
    )
    if (
        args.guard_contact_unjam_ik_orientation_weight is not None
        and contact_unjam_active
    ):
        env.set_ik_orientation_weight(args.guard_contact_unjam_ik_orientation_weight)
        return True
    contact_reinsert_high_active = step is not None and str(
        step.guard_final_servo_phase
    ) in (
        "contact_reinsert_high_lift",
        "contact_reinsert_high_realign",
    )
    if (
        args.guard_contact_reinsert_high_ik_orientation_weight is not None
        and contact_reinsert_high_active
    ):
        env.set_ik_orientation_weight(
            args.guard_contact_reinsert_high_ik_orientation_weight
        )
        return True
    contact_reinsert_orient_active = step is not None and str(
        step.guard_final_servo_phase
    ) in (
        "contact_reinsert_orient_hold",
        "contact_reinsert_descend",
        "contact_reinsert_micro_align",
    )
    if (
        args.guard_contact_reinsert_tip_priority_ik_enabled
        and contact_reinsert_orient_active
    ):
        env.set_ik_control_mode("pose_tip_priority")
    if (
        args.guard_contact_reinsert_orient_ik_orientation_weight is not None
        and contact_reinsert_orient_active
    ):
        env.set_ik_orientation_weight(
            args.guard_contact_reinsert_orient_ik_orientation_weight
        )
        return True
    if (
        args.guard_final_servo_ik_orientation_weight is not None
        and step is not None
        and step.guard_final_servo_active
    ):
        env.set_ik_orientation_weight(args.guard_final_servo_ik_orientation_weight)
        return True
    active = (
        args.guard_near_ik_orientation_weight is not None
        and guard_near_control_active(step, args)
    )
    env.set_ik_orientation_weight(
        args.guard_near_ik_orientation_weight if active else args.ik_orientation_weight
    )
    return active


def evaluate_scenario(
    args: argparse.Namespace,
    scenario: Scenario,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    env = make_env(args, scenario)
    model = (
        None
        if args.control_mode == "guard_only"
        else AGENTS[args.agent].load(args.model, env=env, device=args.device)
    )
    approach_adapter = (
        ApproachAdapterPolicy.load(args.approach_adapter, device=args.device)
        if args.approach_adapter_enabled and args.approach_adapter is not None
        else None
    )
    final_insert_adapter = (
        FinalInsertAdapterPolicy.load(args.final_insert_adapter, device=args.device)
        if args.final_insert_adapter_enabled and args.final_insert_adapter is not None
        else None
    )
    visual_yaw_estimator = (
        VisualYawRuntime(
            args.guard_visual_yaw_align_model,
            device=args.guard_visual_yaw_align_device,
        )
        if args.guard_visual_yaw_align_enabled
        and args.guard_visual_yaw_align_model is not None
        else None
    )
    guarded_controller = GuardedPolicyController(make_guarded_config(args))
    guard_state_provider = MujocoGuardStateProvider(env)
    guard_enabled = (
        args.control_mode == "guard_only"
        or (
            args.control_mode == "guarded"
            and guarded_controller.scenario_uses_guard(scenario.name, scenario.level)
        )
    )
    ablation_rng = np.random.default_rng(args.seed + 1_000_003)
    image_shuffle_bank: list[Any] = []
    control_state_shuffle_bank: list[np.ndarray] = []
    successes = 0
    collisions = 0
    timeouts = 0
    guarded_episodes = 0
    retry_episodes = 0
    latch_episodes = 0
    hover_episodes = 0
    fixture_clearance_episodes = 0
    returns: list[float] = []
    steps: list[float] = []
    guarded_steps: list[float] = []
    retry_steps: list[float] = []
    retry_triggers: list[float] = []
    latch_steps: list[float] = []
    latch_triggers: list[float] = []
    latch_descent_steps: list[float] = []
    hover_steps: list[float] = []
    hover_latched_steps: list[float] = []
    hover_blocked_steps: list[float] = []
    near_limited_steps: list[float] = []
    fixture_clearance_steps: list[float] = []
    fixture_clearance_realign_steps: list[float] = []
    fixture_clearance_triggers: list[float] = []
    preinsert_recenter_episodes = 0
    preinsert_recenter_steps: list[float] = []
    preinsert_recenter_triggers: list[float] = []
    preinsert_recenter_releases: list[float] = []
    preinsert_recenter_blocked_steps: list[float] = []
    approach_recenter_episodes = 0
    approach_recenter_steps: list[float] = []
    approach_recenter_triggers: list[float] = []
    approach_recenter_releases: list[float] = []
    approach_recenter_blocked_steps: list[float] = []
    approach_adapter_episodes = 0
    approach_adapter_steps: list[float] = []
    final_insert_adapter_episodes = 0
    final_insert_adapter_steps: list[float] = []
    final_insert_adapter_lift_pulse_steps: list[float] = []
    final_insert_macro_recovery_episodes = 0
    final_insert_macro_recovery_steps: list[float] = []
    final_insert_macro_recovery_triggers: list[float] = []
    visual_yaw_align_episodes = 0
    visual_yaw_align_steps: list[float] = []
    visual_yaw_align_blocked_steps: list[float] = []
    early_approach_assist_episodes = 0
    early_approach_assist_steps: list[float] = []
    early_approach_assist_triggers: list[float] = []
    early_approach_assist_releases: list[float] = []
    early_approach_assist_blocked_steps: list[float] = []
    stateful_recovery_episodes = 0
    stateful_recovery_steps: list[float] = []
    stateful_recovery_triggers: list[float] = []
    stateful_recovery_releases: list[float] = []
    stateful_recovery_exhausted_steps: list[float] = []
    final_servo_episodes = 0
    final_servo_steps: list[float] = []
    final_servo_triggers: list[float] = []
    final_servo_rearms: list[float] = []
    final_servo_recovery_triggers: list[float] = []
    final_servo_descent_steps: list[float] = []
    final_servo_exhausted_steps: list[float] = []
    final_dist_xy: list[float] = []
    final_dist_z: list[float] = []
    episode_rows: list[dict[str, Any]] = []
    trace_steps = args.step_output_csv is not None
    step_rows: list[dict[str, Any]] = []

    try:
        for episode in range(args.episodes):
            episode_seed = args.seed + episode
            env.set_ik_control_mode(args.ik_control_mode)
            env.set_ik_orientation_weight(args.ik_orientation_weight)
            obs, info = env.reset(seed=episode_seed)
            guarded_controller.reset()
            episode_base_actuator_kp_multiplier = float(
                info.get("actuator_kp_multiplier", args.nominal_actuator_kp_multiplier)
            )
            episode_return = 0.0
            episode_guard_steps = 0
            episode_retry_steps = 0
            episode_retry_triggers = 0
            episode_latch_steps = 0
            episode_latch_triggers = 0
            episode_latch_descent_steps = 0
            episode_hover_steps = 0
            episode_hover_latched_steps = 0
            episode_hover_blocked_steps = 0
            episode_near_limited_steps = 0
            episode_fixture_clearance_steps = 0
            episode_fixture_clearance_realign_steps = 0
            episode_fixture_clearance_triggers = 0
            episode_preinsert_recenter_steps = 0
            episode_preinsert_recenter_triggers = 0
            episode_preinsert_recenter_releases = 0
            episode_preinsert_recenter_blocked_steps = 0
            episode_approach_recenter_steps = 0
            episode_approach_recenter_triggers = 0
            episode_approach_recenter_releases = 0
            episode_approach_recenter_blocked_steps = 0
            episode_approach_adapter_steps = 0
            episode_final_insert_adapter_steps = 0
            episode_final_insert_adapter_lift_pulse_steps = 0
            episode_final_insert_macro_recovery_steps = 0
            episode_final_insert_macro_recovery_triggers = 0
            episode_visual_yaw_align_steps = 0
            episode_visual_yaw_align_blocked_steps = 0
            episode_visual_yaw_align_latch_steps_remaining = 0
            episode_visual_yaw_align_aligned_descent_stable_steps = 0
            episode_visual_yaw_align_aligned_descent_latch_steps_remaining = 0
            episode_visual_yaw_align_hold_target_steps_remaining = 0
            episode_visual_yaw_align_hold_target_xmat: np.ndarray | None = None
            episode_visual_yaw_align_descent_abort_phase = "inactive"
            episode_visual_yaw_align_descent_abort_steps_remaining = 0
            episode_visual_yaw_align_descent_abort_attempts = 0
            episode_visual_yaw_align_pred_history: list[float] = []
            episode_visual_yaw_align_reacquire_phase = "inactive"
            episode_visual_yaw_align_reacquire_steps_remaining = 0
            episode_visual_yaw_align_reacquire_attempts = 0
            episode_visual_yaw_align_reacquire_pred_history: list[float] = []
            episode_visual_yaw_align_wrong_basin_hold_steps_remaining = 0
            episode_visual_yaw_align_wrong_basin_hold_xmat: np.ndarray | None = None
            episode_visual_yaw_align_wrong_basin_hold_attempts = 0
            episode_visual_yaw_align_low_z_lateral_pop_recovery_phase = "inactive"
            episode_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining = 0
            episode_visual_yaw_align_low_z_lateral_pop_recovery_attempts = 0
            episode_visual_yaw_align_prev_dist_xy = float("nan")
            episode_early_approach_assist_steps = 0
            episode_early_approach_assist_triggers = 0
            episode_early_approach_assist_releases = 0
            episode_early_approach_assist_blocked_steps = 0
            episode_stateful_recovery_steps = 0
            episode_stateful_recovery_triggers = 0
            episode_stateful_recovery_releases = 0
            episode_stateful_recovery_exhausted_steps = 0
            episode_final_servo_steps = 0
            episode_final_servo_triggers = 0
            episode_final_servo_rearms = 0
            episode_final_servo_recovery_triggers = 0
            episode_final_servo_descent_steps = 0
            episode_final_servo_exhausted_steps = 0
            episode_step_rows: list[dict[str, Any]] = []
            min_dist_xy = float(info["dist_xy"])
            min_dist_z = float(info["dist_z"])
            low_z_steps = 0
            low_z_misaligned_steps = 0
            insert_band_steps = 0
            insert_band_misaligned_steps = 0
            near_xy_steps = 0
            approach_adapter_latched = False
            approach_adapter_latch_steps = 0
            final_insert_progress_history: list[tuple[float, float]] = []
            final_insert_adapter_active_streak = 0
            final_insert_adapter_cooldown_remaining = 0
            final_insert_adapter_lift_pulse_remaining = 0
            final_insert_adapter_last_lift_pulse_step = -10**9
            final_insert_macro_recovery_state = FinalInsertMacroRecoveryState()
            while True:
                pre_info = {key: value for key, value in info.items()}
                pre_tip = np.asarray(pre_info["peg_tip_pos"], dtype=np.float64)
                pre_target = np.asarray(pre_info["target_pos"], dtype=np.float64)
                pre_z_above_target = float(pre_tip[2] - pre_target[2])
                final_insert_progress_history.append(
                    (float(pre_info["dist_xy"]), pre_z_above_target)
                )
                (
                    final_insert_z_progress,
                    final_insert_xy_progress,
                ) = final_insert_progress_features(
                    final_insert_progress_history,
                    args.final_insert_adapter_progress_window_steps,
                )
                final_insert_adapter_raw_action = np.zeros(3, dtype=np.float32)
                final_insert_adapter_action = np.zeros(3, dtype=np.float32)
                final_insert_adapter_active = False
                final_insert_adapter_reason = "inactive"
                final_insert_adapter_lift_pulse_active = False
                final_insert_macro_recovery_action = np.zeros(3, dtype=np.float32)
                final_insert_macro_recovery_active = False
                final_insert_macro_recovery_triggered = False
                final_insert_macro_recovery_phase = "inactive"
                final_insert_macro_recovery_reason = "inactive"
                final_insert_macro_recovery_attempt = 0
                final_insert_macro_recovery_steps_remaining = 0
                if args.control_mode == "guard_only":
                    state = guard_state_provider.state_from_info(pre_info)
                    policy_action = np.zeros(3, dtype=np.float32)
                    base_policy_action = policy_action.copy()
                    approach_adapter_residual = np.zeros(3, dtype=np.float32)
                    approach_adapter_active = False
                    action = oracle_action_from_state(
                        peg_tip_pos=state.peg_tip_pos,
                        target_pos=state.target_pos,
                        applied_action=state.applied_action,
                        approach_height=state.approach_height,
                        action_low=state.action_low,
                        action_high=state.action_high,
                        config=make_guarded_config(args).oracle,
                    )
                    guarded = True
                    step = None
                else:
                    assert model is not None
                    model_obs = policy_observation(
                        obs,
                        image_ablation=args.image_ablation,
                        image_ablation_target=args.image_ablation_target,
                        control_state_ablation=args.control_state_ablation,
                        rng=ablation_rng,
                        image_shuffle_bank=image_shuffle_bank,
                        control_state_shuffle_bank=control_state_shuffle_bank,
                    )
                    policy_action, _ = model.predict(model_obs, deterministic=True)
                    base_policy_action = np.asarray(policy_action, dtype=np.float32).reshape(3)
                    (
                        policy_action,
                        approach_adapter_residual,
                        approach_adapter_active,
                    ) = apply_approach_adapter(
                        adapter=approach_adapter,
                        args=args,
                        obs=model_obs,
                        info=pre_info,
                        policy_action=base_policy_action,
                        action_low=np.asarray(env.action_space.low, dtype=np.float64),
                        action_high=np.asarray(env.action_space.high, dtype=np.float64),
                        latched=approach_adapter_latched,
                        latch_steps=approach_adapter_latch_steps,
                        episode_steps=episode_approach_adapter_steps,
                    )
                    if args.approach_adapter_latch_enabled:
                        if approach_adapter_active:
                            approach_adapter_latched = True
                            approach_adapter_latch_steps += 1
                        else:
                            approach_adapter_latched = False
                            approach_adapter_latch_steps = 0
                    if args.control_mode == "policy":
                        action = policy_action
                        guarded = False
                        step = None
                    else:
                        step = guarded_controller.step_with_provider(
                            guard_state_provider,
                            pre_info,
                            policy_action,
                            scenario_name=scenario.name,
                            scenario_level=scenario.level,
                        )
                        action = step.action
                        guarded = step.guarded
                (
                    action,
                    final_insert_adapter_raw_action,
                    final_insert_adapter_action,
                    final_insert_adapter_active,
                    final_insert_adapter_reason,
                ) = apply_final_insert_adapter(
                    adapter=final_insert_adapter,
                    args=args,
                    info=pre_info,
                    step=step,
                    action=np.asarray(action, dtype=np.float32),
                    action_low=np.asarray(env.action_space.low, dtype=np.float64),
                    action_high=np.asarray(env.action_space.high, dtype=np.float64),
                    z_progress_window=final_insert_z_progress,
                    xy_progress_window=final_insert_xy_progress,
                    active_streak=final_insert_adapter_active_streak,
                    cooldown_remaining=final_insert_adapter_cooldown_remaining,
                )
                if final_insert_adapter_cooldown_remaining > 0:
                    final_insert_adapter_cooldown_remaining -= 1
                if final_insert_adapter_active:
                    final_insert_adapter_active_streak += 1
                    if (
                        args.final_insert_adapter_max_consecutive_steps > 0
                        and final_insert_adapter_active_streak
                        >= args.final_insert_adapter_max_consecutive_steps
                    ):
                        final_insert_adapter_cooldown_remaining = max(
                            final_insert_adapter_cooldown_remaining,
                            args.final_insert_adapter_cooldown_steps,
                        )
                else:
                    final_insert_adapter_active_streak = 0
                    final_insert_adapter_lift_pulse_remaining = 0
                (
                    action,
                    final_insert_adapter_lift_pulse_remaining,
                    final_insert_adapter_last_lift_pulse_step,
                    final_insert_adapter_lift_pulse_active,
                ) = maybe_apply_final_insert_lift_pulse(
                    args=args,
                    action=np.asarray(action, dtype=np.float32),
                    step=step,
                    step_index=int(pre_info["step_count"]),
                    adapter_active=final_insert_adapter_active,
                    active_streak=final_insert_adapter_active_streak,
                    pulse_steps_remaining=final_insert_adapter_lift_pulse_remaining,
                    last_pulse_step=final_insert_adapter_last_lift_pulse_step,
                    action_low=np.asarray(env.action_space.low, dtype=np.float64),
                    action_high=np.asarray(env.action_space.high, dtype=np.float64),
                )
                (
                    action,
                    final_insert_macro_recovery_action,
                    final_insert_macro_recovery_active,
                    final_insert_macro_recovery_triggered,
                    final_insert_macro_recovery_phase,
                    final_insert_macro_recovery_attempt,
                    final_insert_macro_recovery_steps_remaining,
                    final_insert_macro_recovery_reason,
                ) = maybe_apply_final_insert_macro_recovery(
                    args=args,
                    action=np.asarray(action, dtype=np.float32),
                    info=pre_info,
                    step=step,
                    state=final_insert_macro_recovery_state,
                    action_low=np.asarray(env.action_space.low, dtype=np.float64),
                    action_high=np.asarray(env.action_space.high, dtype=np.float64),
                )
                episode_guard_steps += int(guarded)
                episode_approach_adapter_steps += int(approach_adapter_active)
                episode_final_insert_adapter_steps += int(final_insert_adapter_active)
                episode_final_insert_adapter_lift_pulse_steps += int(
                    final_insert_adapter_lift_pulse_active
                )
                episode_final_insert_macro_recovery_steps += int(
                    final_insert_macro_recovery_active
                )
                episode_final_insert_macro_recovery_triggers += int(
                    final_insert_macro_recovery_triggered
                )
                if step is not None:
                    episode_retry_steps += int(step.guard_retry_active)
                    episode_retry_triggers += int(step.guard_retry_triggered)
                    episode_latch_steps += int(step.guard_insert_latched)
                    episode_latch_triggers += int(step.guard_insert_latch_activated)
                    episode_latch_descent_steps += int(step.guard_insert_latch_descent_allowed)
                    episode_hover_steps += int(step.guard_hover_active)
                    episode_hover_latched_steps += int(step.guard_hover_descent_latched)
                    episode_hover_blocked_steps += int(step.guard_hover_down_blocked)
                    episode_near_limited_steps += int(step.guard_near_action_limited)
                    episode_fixture_clearance_steps += int(
                        step.guard_fixture_clearance_active
                    )
                    episode_fixture_clearance_realign_steps += int(
                        step.guard_fixture_clearance_phase == "realign"
                    )
                    episode_fixture_clearance_triggers += int(
                        step.guard_fixture_clearance_triggered
                    )
                    episode_preinsert_recenter_steps += int(
                        step.guard_preinsert_recenter_active
                    )
                    episode_preinsert_recenter_triggers += int(
                        step.guard_preinsert_recenter_triggered
                    )
                    episode_preinsert_recenter_releases += int(
                        step.guard_preinsert_recenter_released
                    )
                    episode_preinsert_recenter_blocked_steps += int(
                        step.guard_preinsert_recenter_down_blocked
                    )
                    episode_approach_recenter_steps += int(
                        step.guard_approach_recenter_active
                    )
                    episode_approach_recenter_triggers += int(
                        step.guard_approach_recenter_triggered
                    )
                    episode_approach_recenter_releases += int(
                        step.guard_approach_recenter_released
                    )
                    episode_approach_recenter_blocked_steps += int(
                        step.guard_approach_recenter_down_blocked
                    )
                    episode_early_approach_assist_steps += int(
                        step.guard_early_approach_assist_active
                    )
                    episode_early_approach_assist_triggers += int(
                        step.guard_early_approach_assist_triggered
                    )
                    episode_early_approach_assist_releases += int(
                        step.guard_early_approach_assist_released
                    )
                    episode_early_approach_assist_blocked_steps += int(
                        step.guard_early_approach_assist_down_blocked
                    )
                    episode_stateful_recovery_steps += int(
                        step.guard_stateful_recovery_active
                    )
                    episode_stateful_recovery_triggers += int(
                        step.guard_stateful_recovery_triggered
                    )
                    episode_stateful_recovery_releases += int(
                        step.guard_stateful_recovery_released
                    )
                    episode_stateful_recovery_exhausted_steps += int(
                        step.guard_stateful_recovery_exhausted
                    )
                    episode_final_servo_steps += int(step.guard_final_servo_active)
                    episode_final_servo_triggers += int(step.guard_final_servo_triggered)
                    episode_final_servo_rearms += int(step.guard_final_servo_rearmed)
                    episode_final_servo_recovery_triggers += int(
                        step.guard_final_servo_recovery_triggered
                    )
                    episode_final_servo_descent_steps += int(
                        step.guard_final_servo_descent_allowed
                    )
                    episode_final_servo_exhausted_steps += int(
                        step.guard_final_servo_exhausted
                    )
                near_control_active = guard_near_control_active(step, args)
                if args.guard_near_actuator_kp_enabled:
                    env.set_arm_actuator_kp_multiplier(
                        args.guard_near_actuator_kp_multiplier
                        if near_control_active
                        else episode_base_actuator_kp_multiplier
                    )
                apply_guard_near_ik_orientation_weight(env, step, args)
                guard_square_pose_yaw_align_active = apply_guard_square_pose_yaw_align(
                    env,
                    step,
                    pre_info,
                    args,
                )
                visual_yaw_align_previous_target_xmat = env.get_pose_ik_target_xmat()
                visual_yaw_align_result = apply_guard_visual_yaw_align(
                    env,
                    visual_yaw_estimator,
                    obs,
                    step,
                    pre_info,
                    args,
                )
                target_pos = np.asarray(
                    pre_info.get("target_pos", [np.nan, np.nan, np.nan]),
                    dtype=np.float64,
                )
                peg_tip_pos = np.asarray(
                    pre_info.get("peg_tip_pos", [np.nan, np.nan, np.nan]),
                    dtype=np.float64,
                )
                dist_xy_for_visual_yaw = float(pre_info.get("dist_xy", np.inf))
                z_above_target_for_visual_yaw = float(peg_tip_pos[2] - target_pos[2])
                wall_contact_count_for_visual_yaw = int(
                    pre_info.get("peg_hole_contact_wall_count", 0)
                )
                if args.guard_visual_yaw_align_latch_enabled:
                    profile_for_visual_yaw = str(
                        pre_info.get(
                            "geometry_name",
                            pre_info.get("geometry_profile", ""),
                        )
                    )
                    latch_allowed = bool(
                        profile_for_visual_yaw in set(args.guard_visual_yaw_align_profiles)
                        and visual_yaw_align_near_control_active(step, args)
                        and np.isfinite(dist_xy_for_visual_yaw)
                        and np.isfinite(z_above_target_for_visual_yaw)
                        and dist_xy_for_visual_yaw <= args.guard_visual_yaw_align_latch_max_xy
                        and args.guard_visual_yaw_align_latch_min_z
                        <= z_above_target_for_visual_yaw
                        <= args.guard_visual_yaw_align_latch_max_z
                    )
                    latch_refresh = bool(
                        visual_yaw_align_result.active
                        or visual_yaw_align_result.applied
                        or visual_yaw_align_result.blocked_down
                    )
                    if latch_refresh:
                        episode_visual_yaw_align_latch_steps_remaining = (
                            args.guard_visual_yaw_align_latch_steps
                        )
                    elif (
                        latch_allowed
                        and episode_visual_yaw_align_latch_steps_remaining > 0
                        and visual_yaw_align_result.reason
                        in {
                            "xy_gate",
                            "z_gate",
                            "raw_norm_gate",
                            "cam_std_gate",
                            "crop_std_gate",
                            "deadband",
                        }
                    ):
                        visual_yaw_align_result = VisualYawAlignResult(
                            active=True,
                            applied=False,
                            blocked_down=True,
                            reason=f"latch_{visual_yaw_align_result.reason}",
                            prediction=visual_yaw_align_result.prediction,
                        )
                        episode_visual_yaw_align_latch_steps_remaining -= 1
                    elif not latch_allowed:
                        episode_visual_yaw_align_latch_steps_remaining = 0

                visual_yaw_prediction = visual_yaw_align_result.prediction
                profile_for_visual_yaw_action_gate = str(
                    pre_info.get(
                        "geometry_name",
                        pre_info.get("geometry_profile", ""),
                    )
                )
                if (
                    visual_yaw_prediction is not None
                    and visual_yaw_prediction.valid
                    and np.isfinite(visual_yaw_prediction.signed_error_deg)
                    and visual_yaw_prediction_has_visible_stats(
                        visual_yaw_prediction,
                        args,
                    )
                ):
                    episode_visual_yaw_align_pred_history.append(
                        float(visual_yaw_prediction.signed_error_deg)
                    )
                    max_history = max(
                        1,
                        args.guard_visual_yaw_align_temporal_action_gate_window,
                        args.guard_visual_yaw_align_reacquire_trigger_stable_window,
                        args.guard_visual_yaw_align_wrong_basin_hold_stable_window,
                    )
                    episode_visual_yaw_align_pred_history = (
                        episode_visual_yaw_align_pred_history[-max_history:]
                    )
                else:
                    episode_visual_yaw_align_pred_history = []

                if (
                    args.guard_visual_yaw_align_temporal_action_gate_enabled
                    and visual_yaw_align_result.applied
                    and profile_for_visual_yaw_action_gate
                    in set(args.guard_visual_yaw_align_temporal_action_gate_profiles)
                    and visual_yaw_prediction is not None
                    and visual_yaw_prediction.valid
                ):
                    temporal_gate_reason = ""
                    if (
                        visual_yaw_prediction.abs_error_deg
                        >= args.guard_visual_yaw_align_temporal_action_gate_max_pred_yaw_deg
                    ):
                        temporal_gate_reason = "large_yaw"
                    elif (
                        visual_yaw_prediction.abs_error_deg
                        >= args.guard_visual_yaw_align_temporal_action_gate_min_pred_yaw_deg
                        and not visual_yaw_reacquire_delta_stable(
                            episode_visual_yaw_align_pred_history,
                            profile=profile_for_visual_yaw_action_gate,
                            window=args.guard_visual_yaw_align_temporal_action_gate_window,
                            max_delta_deg=(
                                args.guard_visual_yaw_align_temporal_action_gate_max_delta_deg
                            ),
                        )
                    ):
                        temporal_gate_reason = "unstable_yaw"
                    if temporal_gate_reason:
                        if args.guard_visual_yaw_align_temporal_action_gate_reset_target:
                            env.set_pose_ik_target_xmat(
                                visual_yaw_align_previous_target_xmat
                            )
                        visual_yaw_align_result = replace(
                            visual_yaw_align_result,
                            active=True,
                            applied=False,
                            blocked_down=bool(
                                args.guard_visual_yaw_align_temporal_action_gate_block_descent
                            ),
                            aligned_descent=False,
                            target_hold=False,
                            reason=f"temporal_action_gate_{temporal_gate_reason}",
                            correction_deg=0.0,
                        )
                if args.guard_visual_yaw_align_hold_target_enabled:
                    if visual_yaw_align_result.applied:
                        episode_visual_yaw_align_hold_target_xmat = (
                            env.get_pose_ik_target_xmat()
                        )
                    hold_target_can_arm = bool(
                        visual_yaw_prediction is not None
                        and visual_yaw_prediction.valid
                        and visual_yaw_prediction.abs_error_deg
                        <= args.guard_visual_yaw_align_hold_target_arm_yaw_deg
                        and episode_visual_yaw_align_hold_target_xmat is not None
                        and visual_yaw_align_result.reason
                        in {
                            "applied",
                            "deadband",
                            "yaw_ok_recenter",
                        }
                    )
                    if hold_target_can_arm:
                        episode_visual_yaw_align_hold_target_steps_remaining = (
                            args.guard_visual_yaw_align_hold_target_steps
                        )

                    hold_target_prediction_ok = bool(
                        visual_yaw_prediction is None
                        or not visual_yaw_prediction.valid
                        or visual_yaw_prediction.abs_error_deg
                        <= args.guard_visual_yaw_align_hold_target_release_yaw_deg
                    )
                    hold_target_allowed = bool(
                        episode_visual_yaw_align_hold_target_xmat is not None
                        and visual_yaw_align_near_control_active(step, args)
                        and np.isfinite(dist_xy_for_visual_yaw)
                        and dist_xy_for_visual_yaw
                        <= args.guard_visual_yaw_align_hold_target_release_xy
                        and np.isfinite(z_above_target_for_visual_yaw)
                        and args.guard_visual_yaw_align_hold_target_min_z
                        <= z_above_target_for_visual_yaw
                        <= args.guard_visual_yaw_align_hold_target_max_z
                        and wall_contact_count_for_visual_yaw
                        <= args.guard_visual_yaw_align_max_wall_contact
                        and hold_target_prediction_ok
                    )
                    if (
                        not visual_yaw_align_result.applied
                        and episode_visual_yaw_align_hold_target_steps_remaining > 0
                        and hold_target_allowed
                    ):
                        env.set_pose_ik_target_xmat(
                            episode_visual_yaw_align_hold_target_xmat
                        )
                        env.set_ik_control_mode(
                            args.guard_visual_yaw_align_ik_control_mode
                        )
                        env.set_ik_orientation_weight(
                            args.guard_visual_yaw_align_ik_orientation_weight
                        )
                        visual_yaw_align_result = replace(
                            visual_yaw_align_result,
                            active=True,
                            blocked_down=bool(
                                args.guard_visual_yaw_align_hold_target_block_descent
                            ),
                            target_hold=True,
                            reason=f"target_hold_{visual_yaw_align_result.reason}",
                        )
                        episode_visual_yaw_align_hold_target_steps_remaining -= 1
                    elif not hold_target_allowed:
                        episode_visual_yaw_align_hold_target_steps_remaining = 0

                visual_yaw_wrong_basin_hold_triggered = False
                if args.guard_visual_yaw_align_wrong_basin_hold_enabled:
                    profile_for_wrong_basin_hold = profile_for_visual_yaw_action_gate
                    wrong_basin_hold_profile_ok = bool(
                        profile_for_wrong_basin_hold
                        in set(args.guard_visual_yaw_align_wrong_basin_hold_profiles)
                    )
                    wrong_basin_hold_visible_ok = bool(
                        not args.guard_visual_yaw_align_wrong_basin_hold_require_visible
                        or visual_yaw_prediction_has_visible_stats(
                            visual_yaw_prediction,
                            args,
                        )
                    )
                    wrong_basin_hold_stable_ok = bool(
                        not args.guard_visual_yaw_align_wrong_basin_hold_require_stable_delta
                        or visual_yaw_reacquire_delta_stable(
                            episode_visual_yaw_align_pred_history,
                            profile=profile_for_wrong_basin_hold,
                            window=(
                                args.guard_visual_yaw_align_wrong_basin_hold_stable_window
                            ),
                            max_delta_deg=(
                                args.guard_visual_yaw_align_wrong_basin_hold_max_delta_deg
                            ),
                        )
                    )
                    wrong_basin_hold_allowed = bool(
                        wrong_basin_hold_profile_ok
                        and visual_yaw_align_near_control_active(step, args)
                        and np.isfinite(dist_xy_for_visual_yaw)
                        and dist_xy_for_visual_yaw
                        <= args.guard_visual_yaw_align_wrong_basin_hold_max_xy
                        and np.isfinite(z_above_target_for_visual_yaw)
                        and args.guard_visual_yaw_align_wrong_basin_hold_min_z
                        <= z_above_target_for_visual_yaw
                        <= args.guard_visual_yaw_align_wrong_basin_hold_max_z
                        and wall_contact_count_for_visual_yaw
                        <= args.guard_visual_yaw_align_max_wall_contact
                    )
                    wrong_basin_hold_release = bool(
                        episode_visual_yaw_align_wrong_basin_hold_xmat is not None
                        and visual_yaw_prediction is not None
                        and visual_yaw_prediction.valid
                        and visual_yaw_prediction.abs_error_deg
                        <= args.guard_visual_yaw_align_wrong_basin_hold_release_yaw_deg
                        and np.isfinite(dist_xy_for_visual_yaw)
                        and dist_xy_for_visual_yaw
                        <= args.guard_visual_yaw_align_wrong_basin_hold_release_xy
                        and np.isfinite(z_above_target_for_visual_yaw)
                        and args.guard_visual_yaw_align_wrong_basin_hold_min_z
                        <= z_above_target_for_visual_yaw
                        <= args.guard_visual_yaw_align_wrong_basin_hold_max_z
                    )
                    if wrong_basin_hold_release or not wrong_basin_hold_allowed:
                        episode_visual_yaw_align_wrong_basin_hold_steps_remaining = 0
                        episode_visual_yaw_align_wrong_basin_hold_xmat = None
                    wrong_basin_hold_can_trigger = bool(
                        wrong_basin_hold_allowed
                        and visual_yaw_align_result.applied
                        and visual_yaw_prediction is not None
                        and visual_yaw_prediction.valid
                        and np.isfinite(visual_yaw_prediction.abs_error_deg)
                        and visual_yaw_prediction.abs_error_deg
                        >= args.guard_visual_yaw_align_wrong_basin_hold_min_pred_yaw_deg
                        and wrong_basin_hold_visible_ok
                        and wrong_basin_hold_stable_ok
                        and args.guard_visual_yaw_align_wrong_basin_hold_steps > 0
                    )
                    if wrong_basin_hold_can_trigger:
                        if (
                            episode_visual_yaw_align_wrong_basin_hold_xmat is None
                            or episode_visual_yaw_align_wrong_basin_hold_steps_remaining
                            <= 0
                        ):
                            episode_visual_yaw_align_wrong_basin_hold_attempts += 1
                            visual_yaw_wrong_basin_hold_triggered = True
                        episode_visual_yaw_align_wrong_basin_hold_xmat = (
                            env.get_pose_ik_target_xmat()
                        )
                        episode_visual_yaw_align_wrong_basin_hold_steps_remaining = (
                            args.guard_visual_yaw_align_wrong_basin_hold_steps
                        )

                    if (
                        episode_visual_yaw_align_wrong_basin_hold_xmat is not None
                        and episode_visual_yaw_align_wrong_basin_hold_steps_remaining
                        > 0
                    ):
                        env.set_pose_ik_target_xmat(
                            episode_visual_yaw_align_wrong_basin_hold_xmat
                        )
                        env.set_ik_control_mode(
                            args.guard_visual_yaw_align_ik_control_mode
                        )
                        env.set_ik_orientation_weight(
                            args.guard_visual_yaw_align_ik_orientation_weight
                        )
                        visual_yaw_align_result = replace(
                            visual_yaw_align_result,
                            active=True,
                            blocked_down=bool(
                                args.guard_visual_yaw_align_wrong_basin_hold_block_descent
                            ),
                            aligned_descent=False,
                            target_hold=False,
                            wrong_basin_hold_active=True,
                            wrong_basin_hold_triggered=(
                                visual_yaw_wrong_basin_hold_triggered
                            ),
                            wrong_basin_hold_steps_remaining=(
                                episode_visual_yaw_align_wrong_basin_hold_steps_remaining
                            ),
                            wrong_basin_hold_attempts=(
                                episode_visual_yaw_align_wrong_basin_hold_attempts
                            ),
                            reason=(
                                "wrong_basin_hold_"
                                + f"{visual_yaw_align_result.reason}"
                            ),
                        )

                aligned_descent_candidate = bool(
                    args.guard_visual_yaw_align_aligned_descent_enabled
                    and (
                        not args.guard_visual_yaw_align_aligned_descent_require_visible
                        or visual_yaw_align_has_visible_prediction(
                            visual_yaw_align_result.reason
                        )
                    )
                    and visual_yaw_prediction is not None
                    and visual_yaw_prediction.valid
                    and visual_yaw_prediction.abs_error_deg
                    <= args.guard_visual_yaw_align_aligned_descent_yaw_deg
                    and np.isfinite(dist_xy_for_visual_yaw)
                    and dist_xy_for_visual_yaw
                    <= args.guard_visual_yaw_align_aligned_descent_xy
                    and np.isfinite(z_above_target_for_visual_yaw)
                    and z_above_target_for_visual_yaw
                    >= args.guard_visual_yaw_align_aligned_descent_min_z
                    and z_above_target_for_visual_yaw
                    <= args.guard_visual_yaw_align_aligned_descent_max_z
                )
                if args.guard_visual_yaw_align_aligned_descent_enabled:
                    if aligned_descent_candidate:
                        episode_visual_yaw_align_aligned_descent_stable_steps += 1
                    else:
                        episode_visual_yaw_align_aligned_descent_stable_steps = 0
                    visual_yaw_align_result = replace(
                        visual_yaw_align_result,
                        aligned_descent_stable_steps=(
                            episode_visual_yaw_align_aligned_descent_stable_steps
                        ),
                    )

                if (
                    aligned_descent_candidate
                    and episode_visual_yaw_align_aligned_descent_stable_steps
                    >= args.guard_visual_yaw_align_aligned_descent_required_steps
                ):
                    episode_visual_yaw_align_aligned_descent_latch_steps_remaining = (
                        args.guard_visual_yaw_align_aligned_descent_latch_steps
                    )
                    visual_yaw_align_result = replace(
                        visual_yaw_align_result,
                        active=True,
                        blocked_down=False,
                        aligned_descent=True,
                        aligned_descent_stable_steps=(
                            episode_visual_yaw_align_aligned_descent_stable_steps
                        ),
                        reason="aligned_descent",
                    )
                elif (
                    args.guard_visual_yaw_align_aligned_descent_enabled
                    and episode_visual_yaw_align_aligned_descent_latch_steps_remaining
                    > 0
                ):
                    latch_prediction_ok = bool(
                        (
                            not args.guard_visual_yaw_align_aligned_descent_require_visible
                            or visual_yaw_align_has_visible_prediction(
                                visual_yaw_align_result.reason
                            )
                        )
                        and (
                            visual_yaw_prediction is None
                            or not visual_yaw_prediction.valid
                            or visual_yaw_prediction.abs_error_deg
                            <= args.guard_visual_yaw_align_aligned_descent_latch_release_yaw_deg
                        )
                    )
                    latch_allowed = bool(
                        visual_yaw_align_near_control_active(step, args)
                        and np.isfinite(dist_xy_for_visual_yaw)
                        and dist_xy_for_visual_yaw
                        <= args.guard_visual_yaw_align_aligned_descent_latch_release_xy
                        and np.isfinite(z_above_target_for_visual_yaw)
                        and args.guard_visual_yaw_align_aligned_descent_latch_min_z
                        <= z_above_target_for_visual_yaw
                        <= args.guard_visual_yaw_align_aligned_descent_latch_max_z
                        and wall_contact_count_for_visual_yaw
                        <= args.guard_visual_yaw_align_max_wall_contact
                        and latch_prediction_ok
                    )
                    if latch_allowed:
                        visual_yaw_align_result = replace(
                            visual_yaw_align_result,
                            active=True,
                            blocked_down=False,
                            aligned_descent=True,
                            aligned_descent_stable_steps=(
                                episode_visual_yaw_align_aligned_descent_stable_steps
                            ),
                            reason="aligned_descent_latch",
                        )
                        episode_visual_yaw_align_aligned_descent_latch_steps_remaining -= 1
                    else:
                        episode_visual_yaw_align_aligned_descent_latch_steps_remaining = 0

                low_z_late_finish_descent = bool(
                    args.guard_visual_yaw_align_low_z_late_finish_descent_enabled
                    and profile_for_visual_yaw_action_gate
                    in set(args.guard_visual_yaw_align_low_z_late_finish_descent_profiles)
                    and visual_yaw_align_near_control_active(step, args)
                    and episode_visual_yaw_align_descent_abort_phase == "inactive"
                    and episode_visual_yaw_align_reacquire_phase == "inactive"
                    and int(pre_info.get("step_count", 0))
                    >= args.guard_visual_yaw_align_low_z_late_finish_descent_min_step
                    and visual_yaw_prediction is not None
                    and visual_yaw_prediction.valid
                    and np.isfinite(visual_yaw_prediction.abs_error_deg)
                    and visual_yaw_prediction.abs_error_deg
                    <= args.guard_visual_yaw_align_low_z_late_finish_descent_max_yaw_deg
                    and np.isfinite(dist_xy_for_visual_yaw)
                    and dist_xy_for_visual_yaw
                    <= args.guard_visual_yaw_align_low_z_late_finish_descent_max_xy
                    and np.isfinite(z_above_target_for_visual_yaw)
                    and args.guard_visual_yaw_align_low_z_late_finish_descent_min_z
                    <= z_above_target_for_visual_yaw
                    <= args.guard_visual_yaw_align_low_z_late_finish_descent_max_z
                    and wall_contact_count_for_visual_yaw
                    <= args.guard_visual_yaw_align_max_wall_contact
                    and (
                        visual_yaw_align_result.aligned_descent
                        or visual_yaw_align_result.reason
                        in {
                            "applied",
                            "deadband",
                            "yaw_ok_recenter",
                            "target_hold_yaw_ok_recenter",
                            "raw_norm_gate",
                            "cam_std_gate",
                            "crop_std_gate",
                            "target_hold_raw_norm_gate",
                            "target_hold_cam_std_gate",
                            "target_hold_crop_std_gate",
                        }
                    )
                )
                if low_z_late_finish_descent:
                    visual_yaw_align_result = replace(
                        visual_yaw_align_result,
                        active=True,
                        blocked_down=False,
                        aligned_descent=True,
                        low_z_late_finish_descent=True,
                        target_hold=False,
                        reason=(
                            "low_z_late_finish_descent_"
                            + f"{visual_yaw_align_result.reason}"
                        ),
                    )

                low_visibility_brake = bool(
                    args.guard_visual_yaw_align_low_visibility_brake_enabled
                    and visual_yaw_prediction is not None
                    and visual_yaw_prediction.valid
                    and visual_yaw_prediction.abs_error_deg
                    >= args.guard_visual_yaw_align_low_visibility_brake_min_pred_yaw_deg
                    and visual_yaw_align_result.reason
                    in {
                        "raw_norm_gate",
                        "cam_std_gate",
                        "crop_std_gate",
                        "target_hold_raw_norm_gate",
                        "target_hold_cam_std_gate",
                        "target_hold_crop_std_gate",
                    }
                    and np.isfinite(dist_xy_for_visual_yaw)
                    and dist_xy_for_visual_yaw
                    >= args.guard_visual_yaw_align_low_visibility_brake_min_xy
                    and np.isfinite(z_above_target_for_visual_yaw)
                    and z_above_target_for_visual_yaw
                    <= args.guard_visual_yaw_align_low_visibility_brake_max_z
                )
                if low_visibility_brake:
                    visual_yaw_align_result = replace(
                        visual_yaw_align_result,
                        active=True,
                        blocked_down=True,
                        aligned_descent=False,
                        low_visibility_brake=True,
                        reason="low_visibility_brake",
                    )

                profile_for_visual_yaw_brake = str(
                    pre_info.get(
                        "geometry_name",
                        pre_info.get("geometry_profile", ""),
                    )
                )
                large_xy_low_z_brake = bool(
                    args.guard_visual_yaw_align_large_xy_low_z_brake_enabled
                    and args.guard_visual_yaw_align_enabled
                    and profile_for_visual_yaw_brake
                    in set(args.guard_visual_yaw_align_profiles)
                    and visual_yaw_align_near_control_active(step, args)
                    and np.isfinite(dist_xy_for_visual_yaw)
                    and dist_xy_for_visual_yaw
                    >= args.guard_visual_yaw_align_large_xy_low_z_brake_min_xy
                    and np.isfinite(z_above_target_for_visual_yaw)
                    and z_above_target_for_visual_yaw
                    <= args.guard_visual_yaw_align_large_xy_low_z_brake_max_z
                )
                if large_xy_low_z_brake:
                    visual_yaw_align_result = replace(
                        visual_yaw_align_result,
                        active=True,
                        blocked_down=True,
                        aligned_descent=False,
                        target_hold=False,
                        large_xy_low_z_brake=True,
                        reason="large_xy_low_z_brake",
                    )

                visual_yaw_descent_abort_triggered = False
                if (
                    args.guard_visual_yaw_align_descent_abort_enabled
                    and args.guard_visual_yaw_align_descent_abort_max_attempts > 0
                    and episode_visual_yaw_align_descent_abort_phase == "inactive"
                    and episode_visual_yaw_align_reacquire_phase == "inactive"
                    and episode_visual_yaw_align_descent_abort_attempts
                    < args.guard_visual_yaw_align_descent_abort_max_attempts
                    and int(pre_info.get("step_count", 0))
                    >= args.guard_visual_yaw_align_descent_abort_min_step
                    and (
                        not args.guard_visual_yaw_align_descent_abort_require_unreliable_visual
                        or not visual_yaw_align_has_visible_prediction(
                            visual_yaw_align_result.reason
                        )
                        or (
                            args.guard_visual_yaw_align_descent_abort_allow_large_pred_yaw
                            and visual_yaw_prediction is not None
                            and visual_yaw_prediction.valid
                            and visual_yaw_prediction.abs_error_deg
                            >= args.guard_visual_yaw_align_descent_abort_large_pred_yaw_deg
                        )
                    )
                    and profile_for_visual_yaw_brake
                    in set(args.guard_visual_yaw_align_descent_abort_profiles)
                    and visual_yaw_align_near_control_active(step, args)
                    and np.isfinite(dist_xy_for_visual_yaw)
                    and dist_xy_for_visual_yaw
                    >= args.guard_visual_yaw_align_descent_abort_min_xy
                    and np.isfinite(z_above_target_for_visual_yaw)
                    and z_above_target_for_visual_yaw
                    <= args.guard_visual_yaw_align_descent_abort_max_z
                    and wall_contact_count_for_visual_yaw
                    <= args.guard_visual_yaw_align_max_wall_contact
                ):
                    episode_visual_yaw_align_descent_abort_phase = "lift"
                    episode_visual_yaw_align_descent_abort_steps_remaining = (
                        args.guard_visual_yaw_align_descent_abort_lift_max_steps
                    )
                    episode_visual_yaw_align_descent_abort_attempts += 1
                    visual_yaw_descent_abort_triggered = True
                    episode_visual_yaw_align_latch_steps_remaining = 0
                    episode_visual_yaw_align_aligned_descent_stable_steps = 0
                    episode_visual_yaw_align_aligned_descent_latch_steps_remaining = 0
                    episode_visual_yaw_align_hold_target_steps_remaining = 0
                    episode_visual_yaw_align_hold_target_xmat = None
                    episode_visual_yaw_align_wrong_basin_hold_steps_remaining = 0
                    episode_visual_yaw_align_wrong_basin_hold_xmat = None
                    env.reset_pose_ik_target_xmat()

                if episode_visual_yaw_align_descent_abort_phase == "lift":
                    if (
                        z_above_target_for_visual_yaw
                        >= args.guard_visual_yaw_align_descent_abort_lift_target_z
                        - args.guard_visual_yaw_align_descent_abort_lift_z_tolerance
                        or episode_visual_yaw_align_descent_abort_steps_remaining <= 0
                    ):
                        episode_visual_yaw_align_descent_abort_phase = "recenter"
                        episode_visual_yaw_align_descent_abort_steps_remaining = (
                            args.guard_visual_yaw_align_descent_abort_recenter_max_steps
                        )
                elif episode_visual_yaw_align_descent_abort_phase == "recenter":
                    descent_abort_done = bool(
                        dist_xy_for_visual_yaw
                        <= args.guard_visual_yaw_align_descent_abort_recenter_release_xy
                        and z_above_target_for_visual_yaw
                        >= args.guard_visual_yaw_align_descent_abort_lift_target_z
                        - args.guard_visual_yaw_align_descent_abort_lift_z_tolerance
                    )
                    if (
                        descent_abort_done
                        or episode_visual_yaw_align_descent_abort_steps_remaining <= 0
                    ):
                        episode_visual_yaw_align_descent_abort_phase = "inactive"
                        episode_visual_yaw_align_descent_abort_steps_remaining = 0

                if episode_visual_yaw_align_descent_abort_phase != "inactive":
                    env.reset_pose_ik_target_xmat()
                    visual_yaw_align_result = replace(
                        visual_yaw_align_result,
                        active=True,
                        blocked_down=True,
                        aligned_descent=False,
                        target_hold=False,
                        descent_abort_active=True,
                        descent_abort_triggered=visual_yaw_descent_abort_triggered,
                        descent_abort_phase=episode_visual_yaw_align_descent_abort_phase,
                        descent_abort_attempts=episode_visual_yaw_align_descent_abort_attempts,
                        reason=(
                            "descent_abort_"
                            + f"{episode_visual_yaw_align_descent_abort_phase}_"
                            + f"{visual_yaw_align_result.reason}"
                        ),
                    )

                visual_yaw_reacquire_triggered = False
                visual_yaw_reacquire_descent = False
                if (
                    episode_visual_yaw_align_descent_abort_phase == "inactive"
                    and should_start_guard_visual_yaw_reacquire(
                    step=step,
                    pre_info=pre_info,
                    result=visual_yaw_align_result,
                    pred_history=episode_visual_yaw_align_pred_history,
                    attempts=episode_visual_yaw_align_reacquire_attempts,
                    active_phase=episode_visual_yaw_align_reacquire_phase,
                    dist_xy=dist_xy_for_visual_yaw,
                    z_above_target=z_above_target_for_visual_yaw,
                    args=args,
                    )
                ):
                    episode_visual_yaw_align_reacquire_phase = "lift"
                    episode_visual_yaw_align_reacquire_steps_remaining = (
                        args.guard_visual_yaw_align_reacquire_lift_max_steps
                    )
                    episode_visual_yaw_align_reacquire_attempts += 1
                    episode_visual_yaw_align_reacquire_pred_history = []
                    visual_yaw_reacquire_triggered = True
                    episode_visual_yaw_align_latch_steps_remaining = 0
                    episode_visual_yaw_align_aligned_descent_stable_steps = 0
                    episode_visual_yaw_align_aligned_descent_latch_steps_remaining = 0
                    episode_visual_yaw_align_hold_target_steps_remaining = 0
                    episode_visual_yaw_align_hold_target_xmat = None
                    episode_visual_yaw_align_wrong_basin_hold_steps_remaining = 0
                    episode_visual_yaw_align_wrong_basin_hold_xmat = None
                    env.reset_pose_ik_target_xmat()

                if episode_visual_yaw_align_reacquire_phase == "lift":
                    if (
                        z_above_target_for_visual_yaw
                        >= args.guard_visual_yaw_align_reacquire_lift_target_z
                        - args.guard_visual_yaw_align_reacquire_lift_z_tolerance
                        or episode_visual_yaw_align_reacquire_steps_remaining <= 0
                    ):
                        episode_visual_yaw_align_reacquire_phase = "recenter"
                        episode_visual_yaw_align_reacquire_steps_remaining = (
                            args.guard_visual_yaw_align_reacquire_recenter_max_steps
                        )
                elif episode_visual_yaw_align_reacquire_phase == "recenter":
                    reacquire_recenter_done = bool(
                        dist_xy_for_visual_yaw
                        <= args.guard_visual_yaw_align_reacquire_recenter_release_xy
                        and z_above_target_for_visual_yaw
                        >= args.guard_visual_yaw_align_reacquire_lift_target_z
                        - args.guard_visual_yaw_align_reacquire_lift_z_tolerance
                    )
                    if (
                        reacquire_recenter_done
                        or episode_visual_yaw_align_reacquire_steps_remaining <= 0
                    ):
                        episode_visual_yaw_align_reacquire_phase = "inactive"
                        episode_visual_yaw_align_reacquire_steps_remaining = 0
                        episode_visual_yaw_align_reacquire_pred_history = []

                if episode_visual_yaw_align_reacquire_phase != "inactive":
                    if (
                        visual_yaw_prediction is not None
                        and visual_yaw_prediction.valid
                        and np.isfinite(visual_yaw_prediction.signed_error_deg)
                    ):
                        episode_visual_yaw_align_reacquire_pred_history.append(
                            float(visual_yaw_prediction.signed_error_deg)
                        )
                        max_history = max(
                            1,
                            args.guard_visual_yaw_align_reacquire_relaxed_yaw_stable_window,
                        )
                        episode_visual_yaw_align_reacquire_pred_history = (
                            episode_visual_yaw_align_reacquire_pred_history[-max_history:]
                        )
                    else:
                        episode_visual_yaw_align_reacquire_pred_history = []
                    reacquire_relaxed_visible_ok = bool(
                        not args.guard_visual_yaw_align_reacquire_relaxed_yaw_require_visible
                        or visual_yaw_prediction_has_visible_stats(
                            visual_yaw_prediction,
                            args,
                        )
                    )
                    reacquire_relaxed_delta_ok = bool(
                        not args.guard_visual_yaw_align_reacquire_relaxed_yaw_require_stable_delta
                        or visual_yaw_reacquire_delta_stable(
                            episode_visual_yaw_align_reacquire_pred_history,
                            profile=str(
                                pre_info.get(
                                    "geometry_name",
                                    pre_info.get("geometry_profile", ""),
                                )
                            ),
                            window=(
                                args.guard_visual_yaw_align_reacquire_relaxed_yaw_stable_window
                            ),
                            max_delta_deg=(
                                args.guard_visual_yaw_align_reacquire_relaxed_yaw_max_delta_deg
                            ),
                        )
                    )
                    reacquire_relaxed_reason_ok = bool(
                        visual_yaw_align_result.reason
                        in {
                            "raw_norm_gate",
                            "cam_std_gate",
                            "crop_std_gate",
                            "low_visibility_brake",
                            "target_hold_raw_norm_gate",
                            "target_hold_cam_std_gate",
                            "target_hold_crop_std_gate",
                        }
                        or (
                            args.guard_visual_yaw_align_reacquire_relaxed_yaw_allow_visible_reapply
                            and visual_yaw_align_has_visible_prediction(
                                visual_yaw_align_result.reason
                            )
                        )
                    )
                    if (
                        args.guard_visual_yaw_align_reacquire_relaxed_yaw_enabled
                        and (
                            not visual_yaw_align_result.applied
                            or args.guard_visual_yaw_align_reacquire_relaxed_yaw_allow_visible_reapply
                        )
                        and visual_yaw_prediction is not None
                        and visual_yaw_prediction.valid
                        and visual_yaw_prediction.abs_error_deg
                        >= args.guard_visual_yaw_align_reacquire_relaxed_yaw_min_pred_yaw_deg
                        and reacquire_relaxed_visible_ok
                        and reacquire_relaxed_delta_ok
                        and np.isfinite(z_above_target_for_visual_yaw)
                        and args.guard_visual_yaw_align_reacquire_relaxed_yaw_min_z
                        <= z_above_target_for_visual_yaw
                        <= args.guard_visual_yaw_align_reacquire_relaxed_yaw_max_z
                        and reacquire_relaxed_reason_ok
                    ):
                        relaxed_correction_deg = float(
                            np.clip(
                                -visual_yaw_prediction.signed_error_deg,
                                -args.guard_visual_yaw_align_reacquire_relaxed_yaw_max_correction_deg,
                                args.guard_visual_yaw_align_reacquire_relaxed_yaw_max_correction_deg,
                            )
                        )
                        env.set_pose_ik_target_by_planar_yaw_correction(
                            relaxed_correction_deg
                        )
                        env.set_ik_control_mode(
                            args.guard_visual_yaw_align_ik_control_mode
                        )
                        env.set_ik_orientation_weight(
                            args.guard_visual_yaw_align_ik_orientation_weight
                        )
                        visual_yaw_align_result = replace(
                            visual_yaw_align_result,
                            active=True,
                            applied=True,
                            blocked_down=True,
                            aligned_descent=False,
                            target_hold=False,
                            reason=(
                                "reacquire_relaxed_yaw_"
                                f"{visual_yaw_align_result.reason}"
                            ),
                            correction_deg=relaxed_correction_deg,
                        )
                    visual_yaw_reacquire_descent = bool(
                        args.guard_visual_yaw_align_reacquire_descent_enabled
                        and episode_visual_yaw_align_reacquire_phase == "recenter"
                        and visual_yaw_prediction is not None
                        and visual_yaw_prediction.valid
                        and visual_yaw_prediction.abs_error_deg
                        <= args.guard_visual_yaw_align_reacquire_descent_yaw_deg
                        and visual_yaw_align_has_visible_prediction(
                            visual_yaw_align_result.reason
                        )
                        and np.isfinite(dist_xy_for_visual_yaw)
                        and dist_xy_for_visual_yaw
                        <= args.guard_visual_yaw_align_reacquire_descent_xy
                        and np.isfinite(z_above_target_for_visual_yaw)
                        and args.guard_visual_yaw_align_reacquire_descent_min_z
                        <= z_above_target_for_visual_yaw
                        <= args.guard_visual_yaw_align_reacquire_descent_max_z
                    )
                    visual_yaw_align_result = replace(
                        visual_yaw_align_result,
                        active=True,
                        blocked_down=not visual_yaw_reacquire_descent,
                        aligned_descent=visual_yaw_reacquire_descent,
                        target_hold=False,
                        reacquire_active=True,
                        reacquire_triggered=visual_yaw_reacquire_triggered,
                        reacquire_phase=episode_visual_yaw_align_reacquire_phase,
                        reacquire_attempts=episode_visual_yaw_align_reacquire_attempts,
                        reason=(
                            (
                                "reacquire_descent_"
                                if visual_yaw_reacquire_descent
                                else "reacquire_"
                            )
                            + f"{episode_visual_yaw_align_reacquire_phase}_"
                            + f"{visual_yaw_align_result.reason}"
                        ),
                    )
                else:
                    episode_visual_yaw_align_reacquire_pred_history = []

                visual_yaw_low_z_lateral_pop_recovery_triggered = False
                if (
                    episode_visual_yaw_align_descent_abort_phase == "inactive"
                    and episode_visual_yaw_align_reacquire_phase == "inactive"
                    and should_start_guard_visual_yaw_low_z_lateral_pop_recovery(
                        step=step,
                        pre_info=pre_info,
                        attempts=(
                            episode_visual_yaw_align_low_z_lateral_pop_recovery_attempts
                        ),
                        active_phase=(
                            episode_visual_yaw_align_low_z_lateral_pop_recovery_phase
                        ),
                        dist_xy=dist_xy_for_visual_yaw,
                        prev_dist_xy=episode_visual_yaw_align_prev_dist_xy,
                        z_above_target=z_above_target_for_visual_yaw,
                        args=args,
                    )
                ):
                    episode_visual_yaw_align_low_z_lateral_pop_recovery_phase = "lift"
                    episode_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining = (
                        args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_max_steps
                    )
                    episode_visual_yaw_align_low_z_lateral_pop_recovery_attempts += 1
                    visual_yaw_low_z_lateral_pop_recovery_triggered = True
                    episode_visual_yaw_align_latch_steps_remaining = 0
                    episode_visual_yaw_align_aligned_descent_stable_steps = 0
                    episode_visual_yaw_align_aligned_descent_latch_steps_remaining = 0
                    episode_visual_yaw_align_hold_target_steps_remaining = 0
                    episode_visual_yaw_align_hold_target_xmat = None
                    episode_visual_yaw_align_wrong_basin_hold_steps_remaining = 0
                    episode_visual_yaw_align_wrong_basin_hold_xmat = None
                    env.reset_pose_ik_target_xmat()

                if (
                    episode_visual_yaw_align_low_z_lateral_pop_recovery_phase
                    == "lift"
                ):
                    if (
                        z_above_target_for_visual_yaw
                        >= args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_target_z
                        - args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_z_tolerance
                        or episode_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining
                        <= 0
                    ):
                        episode_visual_yaw_align_low_z_lateral_pop_recovery_phase = (
                            "recenter"
                        )
                        episode_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining = (
                            args.guard_visual_yaw_align_low_z_lateral_pop_recovery_recenter_max_steps
                        )
                elif (
                    episode_visual_yaw_align_low_z_lateral_pop_recovery_phase
                    == "recenter"
                ):
                    low_z_lateral_pop_recovery_done = bool(
                        dist_xy_for_visual_yaw
                        <= args.guard_visual_yaw_align_low_z_lateral_pop_recovery_recenter_release_xy
                        and z_above_target_for_visual_yaw
                        >= args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_target_z
                        - args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_z_tolerance
                    )
                    if (
                        low_z_lateral_pop_recovery_done
                        or episode_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining
                        <= 0
                    ):
                        episode_visual_yaw_align_low_z_lateral_pop_recovery_phase = (
                            "inactive"
                        )
                        episode_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining = 0

                if (
                    episode_visual_yaw_align_low_z_lateral_pop_recovery_phase
                    != "inactive"
                ):
                    env.reset_pose_ik_target_xmat()
                    visual_yaw_align_result = replace(
                        visual_yaw_align_result,
                        active=True,
                        blocked_down=True,
                        aligned_descent=False,
                        target_hold=False,
                        low_z_lateral_pop_recovery_active=True,
                        low_z_lateral_pop_recovery_triggered=(
                            visual_yaw_low_z_lateral_pop_recovery_triggered
                        ),
                        low_z_lateral_pop_recovery_phase=(
                            episode_visual_yaw_align_low_z_lateral_pop_recovery_phase
                        ),
                        low_z_lateral_pop_recovery_attempts=(
                            episode_visual_yaw_align_low_z_lateral_pop_recovery_attempts
                        ),
                        low_z_lateral_pop_recovery_steps_remaining=(
                            episode_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining
                        ),
                        reason=(
                            "low_z_lateral_pop_recovery_"
                            + f"{episode_visual_yaw_align_low_z_lateral_pop_recovery_phase}_"
                            + f"{visual_yaw_align_result.reason}"
                        ),
                    )

                if (
                    visual_yaw_align_result.blocked_down
                    or visual_yaw_align_result.aligned_descent
                    or visual_yaw_align_result.low_visibility_brake
                    or visual_yaw_align_result.large_xy_low_z_brake
                    or visual_yaw_align_result.descent_abort_active
                    or visual_yaw_align_result.reacquire_active
                    or visual_yaw_align_result.wrong_basin_hold_active
                    or visual_yaw_align_result.low_z_lateral_pop_recovery_active
                ):
                    action = np.asarray(action, dtype=np.float32).copy()
                    if visual_yaw_align_result.descent_abort_active:
                        xy_error = target_pos[:2] - peg_tip_pos[:2]
                        xy_error_norm = float(np.linalg.norm(xy_error))
                        if visual_yaw_align_result.descent_abort_phase == "recenter":
                            if (
                                np.all(np.isfinite(xy_error))
                                and xy_error_norm
                                > args.guard_visual_yaw_align_descent_abort_recenter_release_xy
                            ):
                                action[:2] = (
                                    xy_error
                                    / max(xy_error_norm, 1e-9)
                                    * min(
                                        args.guard_visual_yaw_align_descent_abort_max_xy_action,
                                        xy_error_norm,
                                    )
                                ).astype(np.float32)
                            else:
                                action[:2] = 0.0
                        else:
                            action[:2] = 0.0
                        if (
                            visual_yaw_align_result.descent_abort_phase == "lift"
                            or z_above_target_for_visual_yaw
                            < args.guard_visual_yaw_align_descent_abort_lift_target_z
                            - args.guard_visual_yaw_align_descent_abort_lift_z_tolerance
                        ):
                            action[2] = max(
                                float(action[2]),
                                args.guard_visual_yaw_align_descent_abort_max_up_action,
                            )
                        else:
                            action[2] = max(float(action[2]), 0.0)
                    elif visual_yaw_align_result.reacquire_active:
                        xy_error = target_pos[:2] - peg_tip_pos[:2]
                        xy_error_norm = float(np.linalg.norm(xy_error))
                        if visual_yaw_align_result.reacquire_phase == "recenter":
                            if (
                                np.all(np.isfinite(xy_error))
                                and xy_error_norm
                                > args.guard_visual_yaw_align_reacquire_recenter_release_xy
                            ):
                                action[:2] = (
                                    xy_error
                                    / max(xy_error_norm, 1e-9)
                                    * min(
                                        args.guard_visual_yaw_align_reacquire_max_xy_action,
                                        xy_error_norm,
                                    )
                                ).astype(np.float32)
                            else:
                                action[:2] = 0.0
                        else:
                            action[:2] = 0.0
                        if (
                            visual_yaw_align_result.reacquire_phase == "lift"
                            or z_above_target_for_visual_yaw
                            < args.guard_visual_yaw_align_reacquire_lift_target_z
                            - args.guard_visual_yaw_align_reacquire_lift_z_tolerance
                        ):
                            action[2] = max(
                                float(action[2]),
                                args.guard_visual_yaw_align_reacquire_max_up_action,
                            )
                        elif visual_yaw_reacquire_descent:
                            action[2] = -float(
                                args.guard_visual_yaw_align_reacquire_descent_max_down_action
                            )
                        else:
                            action[2] = max(float(action[2]), 0.0)
                    elif visual_yaw_align_result.low_z_lateral_pop_recovery_active:
                        xy_error = target_pos[:2] - peg_tip_pos[:2]
                        xy_error_norm = float(np.linalg.norm(xy_error))
                        if (
                            visual_yaw_align_result.low_z_lateral_pop_recovery_phase
                            == "recenter"
                        ):
                            if (
                                np.all(np.isfinite(xy_error))
                                and xy_error_norm
                                > args.guard_visual_yaw_align_low_z_lateral_pop_recovery_recenter_release_xy
                            ):
                                action[:2] = (
                                    xy_error
                                    / max(xy_error_norm, 1e-9)
                                    * min(
                                        args.guard_visual_yaw_align_low_z_lateral_pop_recovery_max_xy_action,
                                        xy_error_norm,
                                    )
                                ).astype(np.float32)
                            else:
                                action[:2] = 0.0
                        else:
                            action[:2] = 0.0
                        if (
                            visual_yaw_align_result.low_z_lateral_pop_recovery_phase
                            == "lift"
                            or z_above_target_for_visual_yaw
                            < args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_target_z
                            - args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_z_tolerance
                        ):
                            action[2] = max(
                                float(action[2]),
                                args.guard_visual_yaw_align_low_z_lateral_pop_recovery_max_up_action,
                            )
                        else:
                            action[2] = max(float(action[2]), 0.0)
                    elif visual_yaw_align_result.blocked_down:
                        action[2] = max(float(action[2]), 0.0)
                    if (
                        not visual_yaw_align_result.descent_abort_active
                        and not visual_yaw_align_result.reacquire_active
                        and not visual_yaw_align_result.low_z_lateral_pop_recovery_active
                        and (
                            args.guard_visual_yaw_align_hold_xy_enabled
                            or visual_yaw_align_result.aligned_descent
                            or visual_yaw_align_result.wrong_basin_hold_active
                        )
                    ):
                        xy_error = target_pos[:2] - peg_tip_pos[:2]
                        xy_error_norm = float(np.linalg.norm(xy_error))
                        xy_tolerance = (
                            0.0
                            if visual_yaw_align_result.aligned_descent
                            else (
                                args.guard_visual_yaw_align_wrong_basin_hold_release_xy
                                if visual_yaw_align_result.wrong_basin_hold_active
                                else args.guard_visual_yaw_align_hold_xy_tolerance
                            )
                        )
                        xy_action_limit = (
                            (
                                args.guard_visual_yaw_align_low_z_late_finish_descent_max_xy_action
                                if visual_yaw_align_result.low_z_late_finish_descent
                                else args.guard_visual_yaw_align_aligned_descent_max_xy_action
                            )
                            if visual_yaw_align_result.aligned_descent
                            else (
                                args.guard_visual_yaw_align_wrong_basin_hold_max_xy_action
                                if visual_yaw_align_result.wrong_basin_hold_active
                                else args.guard_visual_yaw_align_hold_max_xy_action
                            )
                        )
                        if (
                            np.all(np.isfinite(xy_error))
                            and xy_error_norm > xy_tolerance
                        ):
                            action[:2] = (
                                xy_error
                                / max(xy_error_norm, 1e-9)
                                * min(
                                    xy_action_limit,
                                    xy_error_norm,
                                )
                            ).astype(np.float32)
                        else:
                            action[:2] = 0.0
                    if visual_yaw_align_result.descent_abort_active:
                        pass
                    elif visual_yaw_align_result.reacquire_active:
                        pass
                    elif visual_yaw_align_result.low_z_lateral_pop_recovery_active:
                        pass
                    elif visual_yaw_align_result.aligned_descent:
                        max_down_action = (
                            args.guard_visual_yaw_align_low_z_late_finish_descent_max_down_action
                            if visual_yaw_align_result.low_z_late_finish_descent
                            else args.guard_visual_yaw_align_aligned_descent_max_down_action
                        )
                        action[2] = -float(max_down_action)
                    elif visual_yaw_align_result.low_visibility_brake:
                        action[2] = max(
                            float(action[2]),
                            args.guard_visual_yaw_align_low_visibility_brake_up_action,
                        )
                    elif visual_yaw_align_result.large_xy_low_z_brake:
                        action[:2] = 0.0
                        action[2] = max(
                            float(action[2]),
                            args.guard_visual_yaw_align_large_xy_low_z_brake_up_action,
                        )
                    elif args.guard_visual_yaw_align_hold_z_enabled:
                        z_above_target = z_above_target_for_visual_yaw
                        if (
                            np.isfinite(z_above_target)
                            and z_above_target < args.guard_visual_yaw_align_hold_z_min
                        ):
                            action[2] = max(
                                float(action[2]),
                                args.guard_visual_yaw_align_hold_up_action,
                            )
                    if (
                        visual_yaw_align_result.low_visibility_brake
                        and args.guard_visual_yaw_align_low_visibility_brake_flush_history
                    ):
                        env.flush_control_randomization_history(
                            np.asarray(action, dtype=np.float32)
                        )
                    if (
                        visual_yaw_align_result.large_xy_low_z_brake
                        and args.guard_visual_yaw_align_large_xy_low_z_brake_flush_history
                    ):
                        env.flush_control_randomization_history(
                            np.asarray(action, dtype=np.float32)
                        )
                    if (
                        visual_yaw_align_result.descent_abort_active
                        and args.guard_visual_yaw_align_descent_abort_flush_history
                    ):
                        env.flush_control_randomization_history(
                            np.asarray(action, dtype=np.float32)
                        )
                    if (
                        visual_yaw_align_result.reacquire_active
                        and args.guard_visual_yaw_align_reacquire_flush_history
                    ):
                        env.flush_control_randomization_history(
                            np.asarray(action, dtype=np.float32)
                        )
                    if (
                        visual_yaw_align_result.low_z_lateral_pop_recovery_active
                        and args.guard_visual_yaw_align_low_z_lateral_pop_recovery_flush_history
                    ):
                        env.flush_control_randomization_history(
                            np.asarray(action, dtype=np.float32)
                        )
                    if (
                        visual_yaw_align_result.low_z_late_finish_descent
                        and args.guard_visual_yaw_align_low_z_late_finish_descent_flush_history
                    ):
                        env.flush_control_randomization_history(
                            np.asarray(action, dtype=np.float32)
                        )
                    if (
                        visual_yaw_align_result.wrong_basin_hold_active
                        and args.guard_visual_yaw_align_wrong_basin_hold_flush_history
                    ):
                        env.flush_control_randomization_history(
                            np.asarray(action, dtype=np.float32)
                        )
                if episode_visual_yaw_align_descent_abort_phase != "inactive":
                    episode_visual_yaw_align_descent_abort_steps_remaining = max(
                        episode_visual_yaw_align_descent_abort_steps_remaining - 1,
                        0,
                    )
                if episode_visual_yaw_align_reacquire_phase != "inactive":
                    episode_visual_yaw_align_reacquire_steps_remaining = max(
                        episode_visual_yaw_align_reacquire_steps_remaining - 1,
                        0,
                    )
                if (
                    episode_visual_yaw_align_low_z_lateral_pop_recovery_phase
                    != "inactive"
                ):
                    episode_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining = max(
                        episode_visual_yaw_align_low_z_lateral_pop_recovery_steps_remaining
                        - 1,
                        0,
                    )
                if episode_visual_yaw_align_wrong_basin_hold_xmat is not None:
                    episode_visual_yaw_align_wrong_basin_hold_steps_remaining = max(
                        episode_visual_yaw_align_wrong_basin_hold_steps_remaining - 1,
                        0,
                    )
                    if episode_visual_yaw_align_wrong_basin_hold_steps_remaining <= 0:
                        episode_visual_yaw_align_wrong_basin_hold_xmat = None
                episode_visual_yaw_align_steps += int(visual_yaw_align_result.applied)
                episode_visual_yaw_align_blocked_steps += int(
                    visual_yaw_align_result.blocked_down
                )
                episode_visual_yaw_align_prev_dist_xy = dist_xy_for_visual_yaw
                if (
                    args.guard_final_servo_square_recovery_escape_flush_control_history
                    and step is not None
                    and step.guard_final_servo_square_recovery_escape_triggered
                ):
                    env.flush_control_randomization_history(np.asarray(action, dtype=np.float32))
                obs, reward, terminated, truncated, info = env.step(action)
                episode_return += float(reward)
                dist_xy = float(info["dist_xy"])
                dist_z = float(info["dist_z"])
                min_dist_xy = min(min_dist_xy, dist_xy)
                min_dist_z = min(min_dist_z, dist_z)
                low_z_steps += int(dist_z <= 0.04)
                low_z_misaligned_steps += int(dist_z <= 0.04 and dist_xy > args.success_xy_tolerance)
                insert_band_steps += int(dist_z <= 0.02)
                insert_band_misaligned_steps += int(dist_z <= 0.02 and dist_xy > args.success_xy_tolerance)
                near_xy_steps += int(dist_xy <= args.guarded_align_xy_tolerance)
                if trace_steps:
                    episode_step_rows.append(
                        build_step_trace_row(
                            scenario=scenario,
                            args=args,
                            episode=episode,
                            episode_seed=episode_seed,
                            outcome="pending",
                            pre_info=pre_info,
                            post_info=info,
                            policy_action=policy_action,
                            final_action=np.asarray(action, dtype=np.float32),
                            base_policy_action=base_policy_action,
                            approach_adapter_residual=approach_adapter_residual,
                            approach_adapter_active=approach_adapter_active,
                            final_insert_adapter_raw_action=(
                                final_insert_adapter_raw_action
                            ),
                            final_insert_adapter_action=final_insert_adapter_action,
                            final_insert_adapter_active=final_insert_adapter_active,
                            final_insert_adapter_reason=final_insert_adapter_reason,
                            final_insert_adapter_lift_pulse_active=(
                                final_insert_adapter_lift_pulse_active
                            ),
                            final_insert_adapter_lift_pulse_steps_remaining=(
                                final_insert_adapter_lift_pulse_remaining
                            ),
                            final_insert_macro_recovery_action=(
                                final_insert_macro_recovery_action
                            ),
                            final_insert_macro_recovery_active=(
                                final_insert_macro_recovery_active
                            ),
                            final_insert_macro_recovery_triggered=(
                                final_insert_macro_recovery_triggered
                            ),
                            final_insert_macro_recovery_phase=(
                                final_insert_macro_recovery_phase
                            ),
                            final_insert_macro_recovery_reason=(
                                final_insert_macro_recovery_reason
                            ),
                            final_insert_macro_recovery_attempt=(
                                final_insert_macro_recovery_attempt
                            ),
                            final_insert_macro_recovery_steps_remaining=(
                                final_insert_macro_recovery_steps_remaining
                            ),
                            guard_square_pose_yaw_align_active=(
                                guard_square_pose_yaw_align_active
                            ),
                            visual_yaw_align_result=visual_yaw_align_result,
                            step=step,
                            guard_enabled=guard_enabled,
                            guarded=guarded,
                            step_index=int(pre_info["step_count"]),
                        )
                    )
                if terminated or truncated:
                    break

            success = bool(info["insertion_success"])
            collision = bool(info["collision"])
            timeout = bool(truncated and not success)
            if success:
                outcome = "success"
            elif collision:
                outcome = "collision"
            elif timeout:
                outcome = "timeout"
            else:
                outcome = "terminated_failure"

            successes += int(success)
            collisions += int(collision)
            timeouts += int(timeout)
            guarded_episodes += int(episode_guard_steps > 0)
            retry_episodes += int(episode_retry_steps > 0 or episode_retry_triggers > 0)
            latch_episodes += int(episode_latch_steps > 0 or episode_latch_triggers > 0)
            hover_episodes += int(episode_hover_steps > 0)
            fixture_clearance_episodes += int(
                episode_fixture_clearance_steps > 0
                or episode_fixture_clearance_triggers > 0
            )
            preinsert_recenter_episodes += int(
                episode_preinsert_recenter_steps > 0
                or episode_preinsert_recenter_triggers > 0
            )
            approach_recenter_episodes += int(
                episode_approach_recenter_steps > 0
                or episode_approach_recenter_triggers > 0
            )
            approach_adapter_episodes += int(episode_approach_adapter_steps > 0)
            final_insert_adapter_episodes += int(episode_final_insert_adapter_steps > 0)
            final_insert_macro_recovery_episodes += int(
                episode_final_insert_macro_recovery_steps > 0
                or episode_final_insert_macro_recovery_triggers > 0
            )
            visual_yaw_align_episodes += int(episode_visual_yaw_align_steps > 0)
            early_approach_assist_episodes += int(
                episode_early_approach_assist_steps > 0
                or episode_early_approach_assist_triggers > 0
            )
            stateful_recovery_episodes += int(
                episode_stateful_recovery_steps > 0
                or episode_stateful_recovery_triggers > 0
            )
            final_servo_episodes += int(
                episode_final_servo_steps > 0
                or episode_final_servo_triggers > 0
            )
            returns.append(episode_return)
            step_count = int(info["step_count"])
            steps.append(float(step_count))
            guarded_steps.append(float(episode_guard_steps))
            retry_steps.append(float(episode_retry_steps))
            retry_triggers.append(float(episode_retry_triggers))
            latch_steps.append(float(episode_latch_steps))
            latch_triggers.append(float(episode_latch_triggers))
            latch_descent_steps.append(float(episode_latch_descent_steps))
            hover_steps.append(float(episode_hover_steps))
            hover_latched_steps.append(float(episode_hover_latched_steps))
            hover_blocked_steps.append(float(episode_hover_blocked_steps))
            near_limited_steps.append(float(episode_near_limited_steps))
            fixture_clearance_steps.append(float(episode_fixture_clearance_steps))
            fixture_clearance_realign_steps.append(float(episode_fixture_clearance_realign_steps))
            fixture_clearance_triggers.append(float(episode_fixture_clearance_triggers))
            preinsert_recenter_steps.append(float(episode_preinsert_recenter_steps))
            preinsert_recenter_triggers.append(float(episode_preinsert_recenter_triggers))
            preinsert_recenter_releases.append(float(episode_preinsert_recenter_releases))
            preinsert_recenter_blocked_steps.append(
                float(episode_preinsert_recenter_blocked_steps)
            )
            approach_recenter_steps.append(float(episode_approach_recenter_steps))
            approach_recenter_triggers.append(float(episode_approach_recenter_triggers))
            approach_recenter_releases.append(float(episode_approach_recenter_releases))
            approach_recenter_blocked_steps.append(float(episode_approach_recenter_blocked_steps))
            approach_adapter_steps.append(float(episode_approach_adapter_steps))
            final_insert_adapter_steps.append(float(episode_final_insert_adapter_steps))
            final_insert_adapter_lift_pulse_steps.append(
                float(episode_final_insert_adapter_lift_pulse_steps)
            )
            final_insert_macro_recovery_steps.append(
                float(episode_final_insert_macro_recovery_steps)
            )
            final_insert_macro_recovery_triggers.append(
                float(episode_final_insert_macro_recovery_triggers)
            )
            visual_yaw_align_steps.append(float(episode_visual_yaw_align_steps))
            visual_yaw_align_blocked_steps.append(
                float(episode_visual_yaw_align_blocked_steps)
            )
            early_approach_assist_steps.append(
                float(episode_early_approach_assist_steps)
            )
            early_approach_assist_triggers.append(
                float(episode_early_approach_assist_triggers)
            )
            early_approach_assist_releases.append(
                float(episode_early_approach_assist_releases)
            )
            early_approach_assist_blocked_steps.append(
                float(episode_early_approach_assist_blocked_steps)
            )
            stateful_recovery_steps.append(float(episode_stateful_recovery_steps))
            stateful_recovery_triggers.append(float(episode_stateful_recovery_triggers))
            stateful_recovery_releases.append(float(episode_stateful_recovery_releases))
            stateful_recovery_exhausted_steps.append(
                float(episode_stateful_recovery_exhausted_steps)
            )
            final_servo_steps.append(float(episode_final_servo_steps))
            final_servo_triggers.append(float(episode_final_servo_triggers))
            final_servo_rearms.append(float(episode_final_servo_rearms))
            final_servo_recovery_triggers.append(float(episode_final_servo_recovery_triggers))
            final_servo_descent_steps.append(float(episode_final_servo_descent_steps))
            final_servo_exhausted_steps.append(float(episode_final_servo_exhausted_steps))
            final_xy = float(info["dist_xy"])
            final_z = float(info["dist_z"])
            final_dist_xy.append(final_xy)
            final_dist_z.append(final_z)
            scale = float(info.get("control_action_scale_multiplier", 1.0))
            noise = float(info.get("control_action_noise_std", 0.0))
            delay = int(info.get("control_action_delay", 0))
            filter_alpha = float(info.get("control_action_filter_alpha", 1.0))
            joint_damping_multiplier = float(info.get("joint_damping_multiplier", 1.0))
            actuator_kp_multiplier = float(info.get("actuator_kp_multiplier", 1.0))
            geometry_profile = str(info.get("geometry_profile", ""))
            geometry_name = str(info.get("geometry_name", ""))
            peg_shape = str(info.get("peg_shape", ""))
            hole_shape = str(info.get("hole_shape", ""))
            hole_half_size = float(info.get("hole_half_size", np.nan))
            peg_radius = float(info.get("peg_radius", np.nan))
            final_peg_tilt_angle_deg = float(info.get("peg_tilt_angle_deg", np.nan))
            final_shape_yaw_error_deg = float(info.get("shape_yaw_error_deg", np.nan))
            success_shape_yaw_required = bool(
                info.get("success_shape_yaw_required", False)
            )
            success_shape_yaw_ok = bool(info.get("success_shape_yaw_ok", True))
            success_shape_yaw_error_deg = float(
                info.get("success_shape_yaw_error_deg", np.nan)
            )
            success_shape_yaw_tolerance_deg = float(
                info.get("success_shape_yaw_tolerance_deg", np.nan)
            )
            final_square_peg_yaw_error_deg = float(
                info.get("square_peg_yaw_error_deg", np.nan)
            )
            final_square_peg_topdown_clearance_margin = float(
                info.get("square_peg_topdown_clearance_margin", np.nan)
            )
            final_square_peg_tilted_clearance_margin = float(
                info.get("square_peg_tilted_clearance_margin", np.nan)
            )
            episode_rows.append(
                {
                    "scenario": scenario.name,
                    "level": scenario.level,
                    "control_mode": args.control_mode,
                    "image_ablation": args.image_ablation,
                    "image_ablation_target": args.image_ablation_target,
                    "control_state_ablation": args.control_state_ablation,
                    "episode": episode,
                    "seed": episode_seed,
                    "outcome": outcome,
                    "success": success,
                    "collision": collision,
                    "timeout": timeout,
                    "steps": step_count,
                    "episode_return": episode_return,
                    "guard_steps": episode_guard_steps,
                    "guard_step_fraction": episode_guard_steps / max(step_count, 1),
                    "retry_steps": episode_retry_steps,
                    "latch_steps": episode_latch_steps,
                    "hover_steps": episode_hover_steps,
                    "near_limited_steps": episode_near_limited_steps,
                    "fixture_clearance_steps": episode_fixture_clearance_steps,
                    "fixture_clearance_realign_steps": episode_fixture_clearance_realign_steps,
                    "fixture_clearance_triggers": episode_fixture_clearance_triggers,
                    "preinsert_recenter_steps": episode_preinsert_recenter_steps,
                    "preinsert_recenter_triggers": episode_preinsert_recenter_triggers,
                    "preinsert_recenter_releases": episode_preinsert_recenter_releases,
                    "preinsert_recenter_blocked_steps": (
                        episode_preinsert_recenter_blocked_steps
                    ),
                    "approach_recenter_steps": episode_approach_recenter_steps,
                    "approach_recenter_triggers": episode_approach_recenter_triggers,
                    "approach_recenter_releases": episode_approach_recenter_releases,
                    "approach_recenter_blocked_steps": (
                        episode_approach_recenter_blocked_steps
                    ),
                    "approach_adapter_steps": episode_approach_adapter_steps,
                    "approach_adapter_step_fraction": (
                        episode_approach_adapter_steps / max(step_count, 1)
                    ),
                    "final_insert_adapter_steps": episode_final_insert_adapter_steps,
                    "final_insert_adapter_step_fraction": (
                        episode_final_insert_adapter_steps / max(step_count, 1)
                    ),
                    "final_insert_adapter_lift_pulse_steps": (
                        episode_final_insert_adapter_lift_pulse_steps
                    ),
                    "final_insert_macro_recovery_steps": (
                        episode_final_insert_macro_recovery_steps
                    ),
                    "final_insert_macro_recovery_triggers": (
                        episode_final_insert_macro_recovery_triggers
                    ),
                    "visual_yaw_align_steps": episode_visual_yaw_align_steps,
                    "visual_yaw_align_step_fraction": (
                        episode_visual_yaw_align_steps / max(step_count, 1)
                    ),
                    "visual_yaw_align_blocked_steps": (
                        episode_visual_yaw_align_blocked_steps
                    ),
                    "early_approach_assist_steps": episode_early_approach_assist_steps,
                    "early_approach_assist_triggers": (
                        episode_early_approach_assist_triggers
                    ),
                    "early_approach_assist_releases": (
                        episode_early_approach_assist_releases
                    ),
                    "early_approach_assist_blocked_steps": (
                        episode_early_approach_assist_blocked_steps
                    ),
                    "stateful_recovery_steps": episode_stateful_recovery_steps,
                    "stateful_recovery_triggers": episode_stateful_recovery_triggers,
                    "stateful_recovery_releases": episode_stateful_recovery_releases,
                    "stateful_recovery_exhausted_steps": (
                        episode_stateful_recovery_exhausted_steps
                    ),
                    "final_servo_steps": episode_final_servo_steps,
                    "final_servo_triggers": episode_final_servo_triggers,
                    "final_servo_rearms": episode_final_servo_rearms,
                    "final_servo_recovery_triggers": episode_final_servo_recovery_triggers,
                    "final_servo_descent_steps": episode_final_servo_descent_steps,
                    "final_servo_exhausted_steps": episode_final_servo_exhausted_steps,
                    "final_dist_xy": final_xy,
                    "final_dist_z": final_z,
                    "min_dist_xy": min_dist_xy,
                    "min_dist_z": min_dist_z,
                    "near_xy_steps": near_xy_steps,
                    "low_z_steps": low_z_steps,
                    "low_z_misaligned_steps": low_z_misaligned_steps,
                    "insert_band_steps": insert_band_steps,
                    "insert_band_misaligned_steps": insert_band_misaligned_steps,
                    "joint_damping_multiplier": joint_damping_multiplier,
                    "actuator_kp_multiplier": actuator_kp_multiplier,
                    "control_action_scale_multiplier": scale,
                    "control_action_noise_std": noise,
                    "control_action_delay": delay,
                    "control_action_filter_alpha": filter_alpha,
                    "geometry_profile": geometry_profile,
                    "geometry_name": geometry_name,
                    "peg_shape": peg_shape,
                    "hole_shape": hole_shape,
                    "hole_half_size": hole_half_size,
                    "peg_radius": peg_radius,
                    "hole_clearance": float(info.get("hole_clearance", np.nan)),
                    "success_shape_yaw_required": success_shape_yaw_required,
                    "success_shape_yaw_ok": success_shape_yaw_ok,
                    "success_shape_yaw_error_deg": success_shape_yaw_error_deg,
                    "success_shape_yaw_tolerance_deg": success_shape_yaw_tolerance_deg,
                    "shape_yaw_clearance": float(info.get("shape_yaw_clearance", np.nan)),
                    "final_peg_tilt_angle_deg": final_peg_tilt_angle_deg,
                    "final_shape_yaw_error_deg": final_shape_yaw_error_deg,
                    "final_square_peg_yaw_error_deg": final_square_peg_yaw_error_deg,
                    "final_square_peg_topdown_clearance_margin": (
                        final_square_peg_topdown_clearance_margin
                    ),
                    "final_square_peg_tilted_clearance_margin": (
                        final_square_peg_tilted_clearance_margin
                    ),
                }
            )
            if trace_steps and episode_matches_step_trace_filter(outcome, args.step_trace_outcome_filter):
                for row in episode_step_rows:
                    row["episode_outcome"] = outcome
                step_rows.extend(episode_step_rows)
    finally:
        env.close()

    mean_steps = mean(steps)
    mean_guarded_steps = mean(guarded_steps)
    mean_retry_steps = mean(retry_steps)
    mean_latch_steps = mean(latch_steps)
    mean_latch_descent_steps = mean(latch_descent_steps)
    mean_hover_steps = mean(hover_steps)
    mean_hover_latched_steps = mean(hover_latched_steps)
    mean_hover_blocked_steps = mean(hover_blocked_steps)
    mean_near_limited_steps = mean(near_limited_steps)
    mean_fixture_clearance_steps = mean(fixture_clearance_steps)
    mean_fixture_clearance_realign_steps = mean(fixture_clearance_realign_steps)
    mean_preinsert_recenter_steps = mean(preinsert_recenter_steps)
    mean_approach_adapter_steps = mean(approach_adapter_steps)
    mean_final_insert_adapter_steps = mean(final_insert_adapter_steps)
    mean_final_insert_adapter_lift_pulse_steps = mean(
        final_insert_adapter_lift_pulse_steps
    )
    mean_final_insert_macro_recovery_steps = mean(
        final_insert_macro_recovery_steps
    )
    mean_visual_yaw_align_steps = mean(visual_yaw_align_steps)
    mean_visual_yaw_align_blocked_steps = mean(visual_yaw_align_blocked_steps)
    mean_early_approach_assist_steps = mean(early_approach_assist_steps)
    mean_stateful_recovery_steps = mean(stateful_recovery_steps)
    mean_final_servo_steps = mean(final_servo_steps)
    mean_final_servo_descent_steps = mean(final_servo_descent_steps)
    summary = {
        "name": scenario.name,
        "level": scenario.level,
        "control_mode": args.control_mode,
        "image_ablation": args.image_ablation,
        "image_ablation_target": args.image_ablation_target,
        "control_state_ablation": args.control_state_ablation,
        "episodes": args.episodes,
        "success_rate": successes / args.episodes,
        "collision_rate": collisions / args.episodes,
        "timeout_rate": timeouts / args.episodes,
        "mean_return": mean(returns),
        "mean_steps": mean_steps,
        "mean_guarded_steps": mean_guarded_steps,
        "mean_guarded_step_fraction": mean_guarded_steps / max(mean_steps, 1e-9),
        "guarded_episode_rate": guarded_episodes / args.episodes,
        "mean_retry_steps": mean_retry_steps,
        "mean_retry_step_fraction": mean_retry_steps / max(mean_steps, 1e-9),
        "mean_retry_triggers": mean(retry_triggers),
        "retry_episode_rate": retry_episodes / args.episodes,
        "mean_latch_steps": mean_latch_steps,
        "mean_latch_step_fraction": mean_latch_steps / max(mean_steps, 1e-9),
        "mean_latch_triggers": mean(latch_triggers),
        "mean_latch_descent_steps": mean_latch_descent_steps,
        "mean_latch_descent_fraction": mean_latch_descent_steps / max(mean_latch_steps, 1e-9),
        "latch_episode_rate": latch_episodes / args.episodes,
        "mean_hover_steps": mean_hover_steps,
        "mean_hover_step_fraction": mean_hover_steps / max(mean_steps, 1e-9),
        "mean_hover_latched_steps": mean_hover_latched_steps,
        "mean_hover_latched_fraction": mean_hover_latched_steps / max(mean_hover_steps, 1e-9),
        "mean_hover_blocked_steps": mean_hover_blocked_steps,
        "mean_hover_blocked_fraction": mean_hover_blocked_steps / max(mean_hover_steps, 1e-9),
        "hover_episode_rate": hover_episodes / args.episodes,
        "mean_near_limited_steps": mean_near_limited_steps,
        "mean_near_limited_fraction": mean_near_limited_steps / max(mean_steps, 1e-9),
        "mean_fixture_clearance_steps": mean_fixture_clearance_steps,
        "mean_fixture_clearance_fraction": mean_fixture_clearance_steps / max(mean_steps, 1e-9),
        "mean_fixture_clearance_realign_steps": mean_fixture_clearance_realign_steps,
        "mean_fixture_clearance_realign_fraction": mean_fixture_clearance_realign_steps / max(mean_steps, 1e-9),
        "mean_fixture_clearance_triggers": mean(fixture_clearance_triggers),
        "fixture_clearance_episode_rate": fixture_clearance_episodes / args.episodes,
        "mean_preinsert_recenter_steps": mean_preinsert_recenter_steps,
        "mean_preinsert_recenter_fraction": (
            mean_preinsert_recenter_steps / max(mean_steps, 1e-9)
        ),
        "mean_preinsert_recenter_triggers": mean(preinsert_recenter_triggers),
        "mean_preinsert_recenter_releases": mean(preinsert_recenter_releases),
        "mean_preinsert_recenter_blocked_steps": mean(preinsert_recenter_blocked_steps),
        "preinsert_recenter_episode_rate": preinsert_recenter_episodes / args.episodes,
        "mean_approach_recenter_steps": mean(approach_recenter_steps),
        "mean_approach_recenter_fraction": (
            mean(approach_recenter_steps) / max(mean_steps, 1e-9)
        ),
        "mean_approach_recenter_triggers": mean(approach_recenter_triggers),
        "mean_approach_recenter_releases": mean(approach_recenter_releases),
        "mean_approach_recenter_blocked_steps": mean(approach_recenter_blocked_steps),
        "approach_recenter_episode_rate": approach_recenter_episodes / args.episodes,
        "approach_adapter_enabled": bool(
            args.approach_adapter_enabled and args.approach_adapter is not None
        ),
        "mean_approach_adapter_steps": mean_approach_adapter_steps,
        "mean_approach_adapter_fraction": (
            mean_approach_adapter_steps / max(mean_steps, 1e-9)
        ),
        "approach_adapter_episode_rate": approach_adapter_episodes / args.episodes,
        "final_insert_adapter_enabled": bool(
            args.final_insert_adapter_enabled and args.final_insert_adapter is not None
        ),
        "mean_final_insert_adapter_steps": mean_final_insert_adapter_steps,
        "mean_final_insert_adapter_fraction": (
            mean_final_insert_adapter_steps / max(mean_steps, 1e-9)
        ),
        "mean_final_insert_adapter_lift_pulse_steps": (
            mean_final_insert_adapter_lift_pulse_steps
        ),
        "final_insert_adapter_episode_rate": (
            final_insert_adapter_episodes / args.episodes
        ),
        "final_insert_macro_recovery_enabled": bool(
            args.final_insert_macro_recovery_enabled
        ),
        "mean_final_insert_macro_recovery_steps": (
            mean_final_insert_macro_recovery_steps
        ),
        "mean_final_insert_macro_recovery_fraction": (
            mean_final_insert_macro_recovery_steps / max(mean_steps, 1e-9)
        ),
        "mean_final_insert_macro_recovery_triggers": mean(
            final_insert_macro_recovery_triggers
        ),
        "final_insert_macro_recovery_episode_rate": (
            final_insert_macro_recovery_episodes / args.episodes
        ),
        "visual_yaw_align_enabled": bool(args.guard_visual_yaw_align_enabled),
        "mean_visual_yaw_align_steps": mean_visual_yaw_align_steps,
        "mean_visual_yaw_align_fraction": (
            mean_visual_yaw_align_steps / max(mean_steps, 1e-9)
        ),
        "mean_visual_yaw_align_blocked_steps": (
            mean_visual_yaw_align_blocked_steps
        ),
        "visual_yaw_align_episode_rate": visual_yaw_align_episodes / args.episodes,
        "mean_early_approach_assist_steps": mean_early_approach_assist_steps,
        "mean_early_approach_assist_fraction": (
            mean_early_approach_assist_steps / max(mean_steps, 1e-9)
        ),
        "mean_early_approach_assist_triggers": mean(
            early_approach_assist_triggers
        ),
        "mean_early_approach_assist_releases": mean(
            early_approach_assist_releases
        ),
        "mean_early_approach_assist_blocked_steps": mean(
            early_approach_assist_blocked_steps
        ),
        "early_approach_assist_episode_rate": (
            early_approach_assist_episodes / args.episodes
        ),
        "mean_stateful_recovery_steps": mean_stateful_recovery_steps,
        "mean_stateful_recovery_fraction": (
            mean_stateful_recovery_steps / max(mean_steps, 1e-9)
        ),
        "mean_stateful_recovery_triggers": mean(stateful_recovery_triggers),
        "mean_stateful_recovery_releases": mean(stateful_recovery_releases),
        "mean_stateful_recovery_exhausted_steps": mean(
            stateful_recovery_exhausted_steps
        ),
        "stateful_recovery_episode_rate": stateful_recovery_episodes / args.episodes,
        "mean_final_servo_steps": mean_final_servo_steps,
        "mean_final_servo_step_fraction": mean_final_servo_steps / max(mean_steps, 1e-9),
        "mean_final_servo_triggers": mean(final_servo_triggers),
        "mean_final_servo_rearms": mean(final_servo_rearms),
        "mean_final_servo_recovery_triggers": mean(final_servo_recovery_triggers),
        "mean_final_servo_descent_steps": mean_final_servo_descent_steps,
        "mean_final_servo_descent_fraction": mean_final_servo_descent_steps / max(mean_final_servo_steps, 1e-9),
        "mean_final_servo_exhausted_steps": mean(final_servo_exhausted_steps),
        "final_servo_episode_rate": final_servo_episodes / args.episodes,
        "guard_enabled": guard_enabled,
        "mean_final_dist_xy": mean(final_dist_xy),
        "mean_final_dist_z": mean(final_dist_z),
        "nominal_joint_damping_multiplier": args.nominal_joint_damping_multiplier,
        "nominal_actuator_kp_multiplier": args.nominal_actuator_kp_multiplier,
        "control_scale_range": range_text(scenario.control_action_scale_range),
        "control_noise_std_range": range_text(scenario.control_action_noise_std_range),
        "control_delay_range": range_text(scenario.control_action_delay_range),
        "control_filter_alpha_range": range_text(scenario.control_action_filter_alpha_range),
    }
    return summary, episode_rows, step_rows


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    fieldnames: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        if rows:
            writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        else:
            if fieldnames is None:
                raise ValueError(f"Cannot write empty CSV without fieldnames: {path}")
            writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)
    print(f"saved CSV report to {path}")


def write_markdown(path: Path, args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Guarded Policy Evaluation",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Observation mode: `{args.observation_mode}`",
        f"- Control mode: `{args.control_mode}`",
        f"- Image ablation: `{args.image_ablation}`",
        f"- Image ablation target: `{args.image_ablation_target}`",
        f"- Control-state ablation: `{args.control_state_ablation}`",
        f"- Approach adapter: `{args.approach_adapter}` enabled `{args.approach_adapter_enabled}`",
        f"- Approach adapter XY/Z gate: `{args.approach_adapter_trigger_xy}->{args.approach_adapter_release_xy}/{args.approach_adapter_min_z}-{args.approach_adapter_max_z}`",
        f"- Approach adapter latch/min-z/max consecutive/episode steps: `{args.approach_adapter_latch_enabled}/{args.approach_adapter_latched_min_z}/{args.approach_adapter_max_steps}/{args.approach_adapter_episode_max_steps}`",
        f"- Approach adapter mode/residual limit/scale/apply Z: `{args.approach_adapter_mode}/{args.approach_adapter_max_xy_residual}/{args.approach_adapter_max_z_residual}/{args.approach_adapter_scale}/{args.approach_adapter_apply_z}`",
        f"- Final insert adapter: `{args.final_insert_adapter}` enabled `{args.final_insert_adapter_enabled}` mode `{args.final_insert_adapter_mode}`",
        f"- Final insert adapter phase/geometry/contact required: `{args.final_insert_adapter_phase}/{args.final_insert_adapter_geometry_name}/{args.final_insert_adapter_wall_contact_required}`",
        f"- Final insert adapter XY/Z/min phase/min stall gate: `{args.final_insert_adapter_max_xy}/{args.final_insert_adapter_min_z}-{args.final_insert_adapter_max_z}/{args.final_insert_adapter_min_phase_steps}/{args.final_insert_adapter_min_stall_steps}`",
        f"- Final insert adapter square risk gate enabled/min stall/XY/topdown/tilted/wall: `{args.final_insert_adapter_square_risk_gate_enabled}/{args.final_insert_adapter_square_risk_min_stall_steps}/{args.final_insert_adapter_square_risk_xy_min}/{args.final_insert_adapter_square_risk_topdown_margin_max}/{args.final_insert_adapter_square_risk_tilted_margin_max}/{args.final_insert_adapter_square_risk_wall_topdown_margin_max}:{args.final_insert_adapter_square_risk_wall_tilted_margin_max}`",
        f"- Final insert adapter action caps XY/up/down/window: `{args.final_insert_adapter_max_xy_action}/{args.final_insert_adapter_max_up_action}/{args.final_insert_adapter_max_down_action}/{args.final_insert_adapter_progress_window_steps}`",
        f"- Final insert adapter max consecutive/cooldown steps: `{args.final_insert_adapter_max_consecutive_steps}/{args.final_insert_adapter_cooldown_steps}`",
        f"- Final insert adapter handoff on down/threshold: `{args.final_insert_adapter_handoff_on_down_action}/{args.final_insert_adapter_handoff_z_action_threshold}`",
        f"- Final insert adapter handoff aligned/no-contact XY/Z: `{args.final_insert_adapter_handoff_on_aligned_no_contact}/{args.final_insert_adapter_handoff_xy}/{args.final_insert_adapter_handoff_min_z}-{args.final_insert_adapter_handoff_max_z}`",
        f"- Final insert adapter lift pulse enabled/active/stall/steps/period/Z: `{args.final_insert_adapter_lift_pulse_enabled}/{args.final_insert_adapter_lift_pulse_active_steps}/{args.final_insert_adapter_lift_pulse_stall_steps}/{args.final_insert_adapter_lift_pulse_steps}/{args.final_insert_adapter_lift_pulse_period_steps}/{args.final_insert_adapter_lift_pulse_z_action}`",
        f"- Final insert macro recovery enabled/phase/geometry/contact: `{args.final_insert_macro_recovery_enabled}/{args.final_insert_macro_recovery_phase}/{args.final_insert_macro_recovery_geometry_name}/{args.final_insert_macro_recovery_wall_contact_required}`",
        f"- Final insert macro recovery gate XY/Z/active/stall/attempts: `{args.final_insert_macro_recovery_max_xy}/{args.final_insert_macro_recovery_min_z}-{args.final_insert_macro_recovery_max_z}/{args.final_insert_macro_recovery_min_active_steps}/{args.final_insert_macro_recovery_min_stall_steps}/{args.final_insert_macro_recovery_max_attempts}`",
        f"- Final insert macro recovery lift/align/hold/action caps: `{args.final_insert_macro_recovery_lift_steps}/{args.final_insert_macro_recovery_align_steps}/{args.final_insert_macro_recovery_hold_steps}/{args.final_insert_macro_recovery_lift_action}/{args.final_insert_macro_recovery_max_xy_action}`",
        f"- Final insert macro recovery abort XY/lift steps/lift action/final-servo inactive: `{args.final_insert_macro_recovery_abort_xy}/{args.final_insert_macro_recovery_abort_lift_steps}/{args.final_insert_macro_recovery_abort_lift_action}/{args.final_insert_macro_recovery_abort_when_final_servo_inactive}`",
        f"- Episodes per scenario: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Frame skip: `{args.frame_skip}`",
        f"- Step trace CSV: `{args.step_output_csv}`",
        f"- Step trace outcome filter: `{args.step_trace_outcome_filter}`",
        f"- Near-hole crop size/source size: `{args.near_hole_crop_size}/{args.near_hole_crop_source_size or args.near_hole_crop_size}`",
        f"- Near-hole crop source size range: `{args.near_hole_crop_source_size_range}`",
        f"- Near-hole crop offset: `{tuple(args.near_hole_crop_offset)}`",
        f"- Include control state: `{args.include_control_state}`",
        f"- Image frame stack: `{args.image_frame_stack}`",
        f"- Wrist camera pos offset: `{tuple(args.wrist_camera_pos_offset)}`",
        f"- Wrist camera rot offset deg: `{tuple(args.wrist_camera_rot_offset_deg)}`",
        f"- Wrist camera FOV override: `{args.wrist_camera_fovy}`",
        f"- IK control mode: `{args.ik_control_mode}`",
        f"- IK orientation/posture weight: `{args.ik_orientation_weight}/{args.ik_posture_weight}`",
        f"- Guard near IK orientation weight: `{args.guard_near_ik_orientation_weight}`",
        f"- Guard final servo IK orientation weight: `{args.guard_final_servo_ik_orientation_weight}`",
        f"- Guard final servo tip-priority IK enabled: `{args.guard_final_servo_tip_priority_ik_enabled}`",
        f"- Guard square pose yaw-align enabled/mode/weight: `{args.guard_square_pose_yaw_align_enabled}/{args.guard_square_pose_yaw_align_ik_control_mode}/{args.guard_square_pose_yaw_align_ik_orientation_weight}`",
        f"- Guard visual yaw-align enabled/model/mode/weight: `{args.guard_visual_yaw_align_enabled}/{args.guard_visual_yaw_align_model}/{args.guard_visual_yaw_align_ik_control_mode}/{args.guard_visual_yaw_align_ik_orientation_weight}`",
        f"- Guard visual yaw-align gates XY/Z/contact/raw/std/deadband/max correction/block: `{args.guard_visual_yaw_align_max_xy}/{args.guard_visual_yaw_align_min_z}-{args.guard_visual_yaw_align_max_z}/{args.guard_visual_yaw_align_max_wall_contact}/{args.guard_visual_yaw_align_min_raw_norm}/{args.guard_visual_yaw_align_min_cam_std}:{args.guard_visual_yaw_align_min_crop_std}/{args.guard_visual_yaw_align_deadband_deg}/{args.guard_visual_yaw_align_max_correction_deg}/{args.guard_visual_yaw_align_block_descent}:{args.guard_visual_yaw_align_block_descent_deg}`",
        f"- Guard visual yaw-align temporal action gate enabled/profiles/window/delta/min-max yaw/block/reset: `{args.guard_visual_yaw_align_temporal_action_gate_enabled}/{','.join(args.guard_visual_yaw_align_temporal_action_gate_profiles)}/{args.guard_visual_yaw_align_temporal_action_gate_window}/{args.guard_visual_yaw_align_temporal_action_gate_max_delta_deg}/{args.guard_visual_yaw_align_temporal_action_gate_min_pred_yaw_deg}-{args.guard_visual_yaw_align_temporal_action_gate_max_pred_yaw_deg}/{args.guard_visual_yaw_align_temporal_action_gate_block_descent}:{args.guard_visual_yaw_align_temporal_action_gate_reset_target}`",
        f"- Guard visual yaw-align target hold enabled/steps/arm yaw/release yaw/XY/Z/block: `{args.guard_visual_yaw_align_hold_target_enabled}/{args.guard_visual_yaw_align_hold_target_steps}/{args.guard_visual_yaw_align_hold_target_arm_yaw_deg}/{args.guard_visual_yaw_align_hold_target_release_yaw_deg}/{args.guard_visual_yaw_align_hold_target_release_xy}/{args.guard_visual_yaw_align_hold_target_min_z}-{args.guard_visual_yaw_align_hold_target_max_z}/{args.guard_visual_yaw_align_hold_target_block_descent}`",
        f"- Guard visual yaw-align low-visibility brake enabled/yaw/XY/Z/up/flush: `{args.guard_visual_yaw_align_low_visibility_brake_enabled}/{args.guard_visual_yaw_align_low_visibility_brake_min_pred_yaw_deg}/{args.guard_visual_yaw_align_low_visibility_brake_min_xy}/{args.guard_visual_yaw_align_low_visibility_brake_max_z}/{args.guard_visual_yaw_align_low_visibility_brake_up_action}/{args.guard_visual_yaw_align_low_visibility_brake_flush_history}`",
        f"- Guard visual yaw-align large-XY/low-Z brake enabled/XY/Z/up/flush: `{args.guard_visual_yaw_align_large_xy_low_z_brake_enabled}/{args.guard_visual_yaw_align_large_xy_low_z_brake_min_xy}/{args.guard_visual_yaw_align_large_xy_low_z_brake_max_z}/{args.guard_visual_yaw_align_large_xy_low_z_brake_up_action}/{args.guard_visual_yaw_align_large_xy_low_z_brake_flush_history}`",
        f"- Guard visual yaw-align low-Z lateral-pop recovery enabled/profiles/attempts/step/trigger XY/Z/prev+jump/lift/recenter/actions/flush: `{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_enabled}/{','.join(args.guard_visual_yaw_align_low_z_lateral_pop_recovery_profiles)}/{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_max_attempts}/{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_min_step}/{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_min_xy}/{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_max_z}/{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_prev_xy}+{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_xy_jump}/{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_target_z}:{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_z_tolerance}:{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_max_steps}/{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_recenter_release_xy}:{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_recenter_max_steps}/{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_max_up_action}:{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_max_xy_action}/{args.guard_visual_yaw_align_low_z_lateral_pop_recovery_flush_history}`",
        f"- Guard visual yaw-align descent-abort enabled/profiles/attempts/step/unreliable-visual/large-yaw/trigger XYmin/Zmax/lift/recenter/actions/flush: `{args.guard_visual_yaw_align_descent_abort_enabled}/{','.join(args.guard_visual_yaw_align_descent_abort_profiles)}/{args.guard_visual_yaw_align_descent_abort_max_attempts}/{args.guard_visual_yaw_align_descent_abort_min_step}/{args.guard_visual_yaw_align_descent_abort_require_unreliable_visual}/{args.guard_visual_yaw_align_descent_abort_allow_large_pred_yaw}:{args.guard_visual_yaw_align_descent_abort_large_pred_yaw_deg}/{args.guard_visual_yaw_align_descent_abort_min_xy}:{args.guard_visual_yaw_align_descent_abort_max_z}/{args.guard_visual_yaw_align_descent_abort_lift_target_z}:{args.guard_visual_yaw_align_descent_abort_lift_z_tolerance}:{args.guard_visual_yaw_align_descent_abort_lift_max_steps}/{args.guard_visual_yaw_align_descent_abort_recenter_release_xy}:{args.guard_visual_yaw_align_descent_abort_recenter_max_steps}/{args.guard_visual_yaw_align_descent_abort_max_up_action}:{args.guard_visual_yaw_align_descent_abort_max_xy_action}/{args.guard_visual_yaw_align_descent_abort_flush_history}`",
        f"- Guard visual yaw-align re-acquire enabled/profiles/attempts/step/trigger XY/Z/yaw/trigger visible-stable/xy-gate/lift/recenter/actions/flush/relaxed yaw/descent: `{args.guard_visual_yaw_align_reacquire_enabled}/{','.join(args.guard_visual_yaw_align_reacquire_profiles)}/{args.guard_visual_yaw_align_reacquire_max_attempts}/{args.guard_visual_yaw_align_reacquire_min_step}/{args.guard_visual_yaw_align_reacquire_trigger_min_xy}-{args.guard_visual_yaw_align_reacquire_trigger_max_xy}/{args.guard_visual_yaw_align_reacquire_trigger_min_z}-{args.guard_visual_yaw_align_reacquire_trigger_max_z}/{args.guard_visual_yaw_align_reacquire_trigger_min_pred_yaw_deg}/{args.guard_visual_yaw_align_reacquire_trigger_require_visible}:{args.guard_visual_yaw_align_reacquire_trigger_require_stable_delta}:{args.guard_visual_yaw_align_reacquire_trigger_stable_window}:{args.guard_visual_yaw_align_reacquire_trigger_max_delta_deg}/{args.guard_visual_yaw_align_reacquire_xy_gate_trigger_enabled}:{args.guard_visual_yaw_align_reacquire_xy_gate_min_xy}/{args.guard_visual_yaw_align_reacquire_lift_target_z}:{args.guard_visual_yaw_align_reacquire_lift_z_tolerance}:{args.guard_visual_yaw_align_reacquire_lift_max_steps}/{args.guard_visual_yaw_align_reacquire_recenter_release_xy}:{args.guard_visual_yaw_align_reacquire_recenter_max_steps}/{args.guard_visual_yaw_align_reacquire_max_up_action}:{args.guard_visual_yaw_align_reacquire_max_xy_action}/{args.guard_visual_yaw_align_reacquire_flush_history}/{args.guard_visual_yaw_align_reacquire_relaxed_yaw_enabled}:{args.guard_visual_yaw_align_reacquire_relaxed_yaw_min_pred_yaw_deg}:{args.guard_visual_yaw_align_reacquire_relaxed_yaw_max_correction_deg}:{args.guard_visual_yaw_align_reacquire_relaxed_yaw_min_z}-{args.guard_visual_yaw_align_reacquire_relaxed_yaw_max_z}:{args.guard_visual_yaw_align_reacquire_relaxed_yaw_require_visible}:{args.guard_visual_yaw_align_reacquire_relaxed_yaw_require_stable_delta}:{args.guard_visual_yaw_align_reacquire_relaxed_yaw_stable_window}:{args.guard_visual_yaw_align_reacquire_relaxed_yaw_max_delta_deg}:{args.guard_visual_yaw_align_reacquire_relaxed_yaw_allow_visible_reapply}/{args.guard_visual_yaw_align_reacquire_descent_enabled}:{args.guard_visual_yaw_align_reacquire_descent_yaw_deg}:{args.guard_visual_yaw_align_reacquire_descent_xy}:{args.guard_visual_yaw_align_reacquire_descent_min_z}-{args.guard_visual_yaw_align_reacquire_descent_max_z}:{args.guard_visual_yaw_align_reacquire_descent_max_down_action}`",
        f"- Guard visual yaw-align wrong-basin hold enabled/profiles/yaw/visible/stable/steps/release XY/max XY/Z/action/block/flush: `{args.guard_visual_yaw_align_wrong_basin_hold_enabled}/{','.join(args.guard_visual_yaw_align_wrong_basin_hold_profiles)}/{args.guard_visual_yaw_align_wrong_basin_hold_min_pred_yaw_deg}/{args.guard_visual_yaw_align_wrong_basin_hold_require_visible}/{args.guard_visual_yaw_align_wrong_basin_hold_require_stable_delta}:{args.guard_visual_yaw_align_wrong_basin_hold_stable_window}:{args.guard_visual_yaw_align_wrong_basin_hold_max_delta_deg}/{args.guard_visual_yaw_align_wrong_basin_hold_steps}/{args.guard_visual_yaw_align_wrong_basin_hold_release_yaw_deg}:{args.guard_visual_yaw_align_wrong_basin_hold_release_xy}/{args.guard_visual_yaw_align_wrong_basin_hold_max_xy}/{args.guard_visual_yaw_align_wrong_basin_hold_min_z}-{args.guard_visual_yaw_align_wrong_basin_hold_max_z}/{args.guard_visual_yaw_align_wrong_basin_hold_max_xy_action}/{args.guard_visual_yaw_align_wrong_basin_hold_block_descent}/{args.guard_visual_yaw_align_wrong_basin_hold_flush_history}`",
        f"- Guard visual yaw-align aligned descent enabled/yaw/XY/Z/steps/visible/down/XY action: `{args.guard_visual_yaw_align_aligned_descent_enabled}/{args.guard_visual_yaw_align_aligned_descent_yaw_deg}/{args.guard_visual_yaw_align_aligned_descent_xy}/{args.guard_visual_yaw_align_aligned_descent_min_z}-{args.guard_visual_yaw_align_aligned_descent_max_z}/{args.guard_visual_yaw_align_aligned_descent_required_steps}/{args.guard_visual_yaw_align_aligned_descent_require_visible}/{args.guard_visual_yaw_align_aligned_descent_max_down_action}/{args.guard_visual_yaw_align_aligned_descent_max_xy_action}`",
        f"- Guard visual yaw-align aligned descent latch steps/release XY/yaw/Z: `{args.guard_visual_yaw_align_aligned_descent_latch_steps}/{args.guard_visual_yaw_align_aligned_descent_latch_release_xy}/{args.guard_visual_yaw_align_aligned_descent_latch_release_yaw_deg}/{args.guard_visual_yaw_align_aligned_descent_latch_min_z}-{args.guard_visual_yaw_align_aligned_descent_latch_max_z}`",
        f"- Guard visual yaw-align low-Z late-finish descent enabled/profiles/step/XY/Z/yaw/actions/flush: `{args.guard_visual_yaw_align_low_z_late_finish_descent_enabled}/{','.join(args.guard_visual_yaw_align_low_z_late_finish_descent_profiles)}/{args.guard_visual_yaw_align_low_z_late_finish_descent_min_step}/{args.guard_visual_yaw_align_low_z_late_finish_descent_max_xy}/{args.guard_visual_yaw_align_low_z_late_finish_descent_min_z}-{args.guard_visual_yaw_align_low_z_late_finish_descent_max_z}/{args.guard_visual_yaw_align_low_z_late_finish_descent_max_yaw_deg}/{args.guard_visual_yaw_align_low_z_late_finish_descent_max_xy_action}:{args.guard_visual_yaw_align_low_z_late_finish_descent_max_down_action}/{args.guard_visual_yaw_align_low_z_late_finish_descent_flush_history}`",
        f"- Guard contact unjam IK orientation weight: `{args.guard_contact_unjam_ik_orientation_weight}`",
        f"- Guard contact reinsert orient IK orientation weight: `{args.guard_contact_reinsert_orient_ik_orientation_weight}`",
        f"- Guard contact reinsert high IK orientation weight: `{args.guard_contact_reinsert_high_ik_orientation_weight}`",
        f"- Guard contact reinsert tip-priority IK enabled: `{args.guard_contact_reinsert_tip_priority_ik_enabled}`",
        f"- IK step limit/max iterations: `{args.ik_step_limit}/{args.ik_max_iterations}`",
        f"- Nominal joint damping / actuator Kp multiplier: `{args.nominal_joint_damping_multiplier}/{args.nominal_actuator_kp_multiplier}`",
        f"- Guard near actuator Kp enabled/multiplier: `{args.guard_near_actuator_kp_enabled}/{args.guard_near_actuator_kp_multiplier}`",
        f"- Guard start XY: `{args.guard_start_xy}`",
        f"- Guard start Z above target: `{args.guard_start_z}`",
        f"- Guard risk XY: `{args.guard_risk_xy}`",
        f"- Guard scenario filter: `{args.guard_scenario_filter}`",
        f"- Guard blend: `{args.guard_blend}`",
        f"- Guard min policy steps: `{args.guard_min_policy_steps}`",
        f"- Guard block down when unaligned: `{args.guard_block_down_when_unaligned}`",
        f"- Guard retry enabled: `{args.guard_retry_enabled}`",
        f"- Guard retry stall steps: `{args.guard_retry_stall_steps}`",
        f"- Guard retry XY/Z band: `{args.guard_retry_xy_tolerance}/{args.guard_retry_z_max}`",
        f"- Guard retry lift/release/max attempts/max steps: `{args.guard_retry_lift_height}/{args.guard_retry_release_xy}/{args.guard_retry_max_attempts}/{args.guard_retry_max_steps}`",
        f"- Guard insert latch enabled: `{args.guard_insert_latch_enabled}`",
        f"- Guard insert latch XY/release XY: `{args.guard_insert_latch_xy_tolerance}/{args.guard_insert_latch_release_xy}`",
        f"- Guard insert latch resume/recenter/z tol/max down: `{args.guard_insert_latch_resume_xy}/{args.guard_insert_latch_recenter_height}/{args.guard_insert_latch_recenter_z_tolerance}/{args.guard_insert_latch_max_down_action}`",
        f"- Guard hover enabled: `{args.guard_hover_enabled}`",
        f"- Guard hover XY/release/height/Z tol/steps/max down: `{args.guard_hover_xy_tolerance}/{args.guard_hover_release_xy}/{args.guard_hover_height}/{args.guard_hover_z_tolerance}/{args.guard_hover_required_steps}/{args.guard_hover_max_down_action}`",
        f"- Guard near action scale enabled: `{args.guard_near_action_scale_enabled}`",
        f"- Guard near XY/Z/max XY/max down: `{args.guard_near_action_xy_tolerance}/{args.guard_near_action_z_threshold}/{args.guard_near_max_xy_action}/{args.guard_near_max_down_action}`",
        f"- Guard fixture clearance enabled: `{args.guard_fixture_clearance_enabled}`",
        f"- Guard fixture clearance XY/Z/lift/max up: `{args.guard_fixture_clearance_xy_min}-{args.guard_fixture_clearance_xy_max}/{args.guard_fixture_clearance_z_max}/{args.guard_fixture_clearance_lift_height}/{args.guard_fixture_clearance_max_up_action}`",
        f"- Guard fixture clearance realign enabled: `{args.guard_fixture_clearance_realign_enabled}`",
        f"- Guard fixture clearance realign start Z/XY/max XY/max down/max steps: `{args.guard_fixture_clearance_realign_start_z}/{args.guard_fixture_clearance_realign_xy}/{args.guard_fixture_clearance_max_xy_action}/{args.guard_fixture_clearance_max_down_action}/{args.guard_fixture_clearance_max_steps}`",
        f"- Guard fixture clearance retreat enabled/release XY/max XY: `{args.guard_fixture_clearance_retreat_enabled}/{args.guard_fixture_clearance_retreat_release_xy}/{args.guard_fixture_clearance_retreat_max_xy_action}`",
        f"- Guard preinsert recenter enabled: `{args.guard_preinsert_recenter_enabled}`",
        f"- Guard preinsert recenter start/min Z, trigger/stable XY: `{args.guard_preinsert_recenter_start_z}/{args.guard_preinsert_recenter_min_z}/{args.guard_preinsert_recenter_trigger_xy}/{args.guard_preinsert_recenter_stable_xy}`",
        f"- Guard preinsert recenter height/Z tol/stable/max steps/max XY/max up: `{args.guard_preinsert_recenter_height}/{args.guard_preinsert_recenter_z_tolerance}/{args.guard_preinsert_recenter_stable_steps}/{args.guard_preinsert_recenter_max_steps}/{args.guard_preinsert_recenter_max_xy_action}/{args.guard_preinsert_recenter_max_up_action}`",
        f"- Guard preinsert recenter lift before lateral: `{args.guard_preinsert_recenter_lift_before_lateral}`",
        f"- Guard stateful recovery enabled: `{args.guard_stateful_recovery_enabled}`",
        f"- Guard stateful recovery trigger XY/Z/stall: `{args.guard_stateful_recovery_trigger_xy_min}-{args.guard_stateful_recovery_trigger_xy_max}/{args.guard_stateful_recovery_trigger_z_max}/{args.guard_stateful_recovery_stall_steps}`",
        f"- Guard stateful recovery lift/release/resume/stable/max attempts: `{args.guard_stateful_recovery_lift_height}/{args.guard_stateful_recovery_release_xy}/{args.guard_stateful_recovery_resume_xy}/{args.guard_stateful_recovery_stable_steps}/{args.guard_stateful_recovery_max_attempts}`",
        f"- Guard final servo enabled: `{args.guard_final_servo_enabled}`",
        f"- Guard final servo start XY/Z/min Z: `{args.guard_final_servo_start_xy}/{args.guard_final_servo_start_z}/{args.guard_final_servo_min_start_z}`",
        f"- Guard final servo hover/stable/descent-start/release: `{args.guard_final_servo_hover_height}/{args.guard_final_servo_stable_xy}/{args.guard_final_servo_descent_start_xy}/{args.guard_final_servo_release_xy}`",
        f"- Guard final servo stable/stall/retries: `{args.guard_final_servo_stable_steps}/{args.guard_final_servo_stall_steps}/{args.guard_final_servo_max_retries}`",
        f"- Guard final servo align timeout steps/XY: `{args.guard_final_servo_align_timeout_steps}/{args.guard_final_servo_align_timeout_xy}`",
        f"- Guard final servo align-hover escape enabled/steps/XY/Z: `{args.guard_final_servo_align_hover_escape_enabled}/{args.guard_final_servo_align_hover_escape_steps}/{args.guard_final_servo_align_hover_escape_xy}/{args.guard_final_servo_align_hover_escape_min_z}-{args.guard_final_servo_align_hover_escape_max_z}`",
        f"- Guard final servo rearm enabled/cooldown/stable/XY/Z/contact/tilt/margin/max attempts: `{args.guard_final_servo_rearm_enabled}/{args.guard_final_servo_rearm_cooldown_steps}/{args.guard_final_servo_rearm_stable_steps}/{args.guard_final_servo_rearm_xy_max}/{args.guard_final_servo_rearm_z_min}-{args.guard_final_servo_rearm_z_max}/{args.guard_final_servo_rearm_contact_max}/{args.guard_final_servo_rearm_tilt_max_deg}/{args.guard_final_servo_rearm_margin_min}/{args.guard_final_servo_rearm_max_attempts}`",
        f"- Guard final servo priority over fixture clearance: `{args.guard_final_servo_priority_over_fixture_clearance}`",
        f"- Guard final servo low recenter enabled/Z/trigger/release/height/steps/max steps/stall: `{args.guard_final_servo_low_recenter_enabled}/{args.guard_final_servo_low_recenter_z_max}/{args.guard_final_servo_low_recenter_trigger_xy}/{args.guard_final_servo_low_recenter_release_xy}/{args.guard_final_servo_low_recenter_height}/{args.guard_final_servo_low_recenter_stable_steps}/{args.guard_final_servo_low_recenter_max_steps}/{args.guard_final_servo_low_recenter_stall_steps}`",
        f"- Guard final servo max XY/down/descend bias/lift/recovery steps: `{args.guard_final_servo_max_xy_action}/{args.guard_final_servo_max_down_action}/{tuple(args.guard_final_servo_descend_xy_bias)}/{args.guard_final_servo_lift_height}/{args.guard_final_servo_max_recovery_steps}`",
        f"- Guard final servo descend bias max clearance: `{args.guard_final_servo_descend_xy_bias_max_clearance}`",
        f"- Guard final servo descend bias requires stateful recovery: `{args.guard_final_servo_descend_xy_bias_requires_stateful_recovery}`",
        f"- Guard final servo recovery mode/soft lift/min height/z tol/hold/max up: `{args.guard_final_servo_recovery_mode}/{args.guard_final_servo_soft_unjam_lift}/{args.guard_final_servo_soft_unjam_min_height}/{args.guard_final_servo_soft_unjam_z_tolerance}/{args.guard_final_servo_soft_unjam_hold_steps}/{args.guard_final_servo_soft_unjam_max_up_action}`",
        f"- Guard final servo square recovery enabled/tilt/steps/XY/Z/lift: `{args.guard_final_servo_square_recovery_enabled}/{args.guard_final_servo_square_recovery_tilt_deg}/{args.guard_final_servo_square_recovery_tilt_steps}/{args.guard_final_servo_square_recovery_xy_max}/{args.guard_final_servo_square_recovery_z_max}/{args.guard_final_servo_square_recovery_lift_height}`",
        f"- Guard final servo square recovery escape enabled/XY/Z/height/late height/release/late release/max steps/max XY/max up/max clearance/early/pre-lift/on-trigger/flush control history: `{args.guard_final_servo_square_recovery_escape_enabled}/{args.guard_final_servo_square_recovery_escape_xy}/{args.guard_final_servo_square_recovery_escape_z_min}-{args.guard_final_servo_square_recovery_escape_z_max}/{args.guard_final_servo_square_recovery_escape_height}/{args.guard_final_servo_square_recovery_escape_late_height_enabled}:{args.guard_final_servo_square_recovery_escape_late_height}@{args.guard_final_servo_square_recovery_escape_late_height_min_steps_since_reset}/{args.guard_final_servo_square_recovery_escape_release_xy}/{args.guard_final_servo_square_recovery_escape_late_release_xy}@{args.guard_final_servo_square_recovery_escape_late_release_min_steps_since_reset}/{args.guard_final_servo_square_recovery_escape_max_steps}/{args.guard_final_servo_square_recovery_escape_max_xy_action}/{args.guard_final_servo_square_recovery_escape_max_up_action}/{args.guard_final_servo_square_recovery_escape_max_clearance}/{args.guard_final_servo_square_recovery_escape_early_contact_enabled}:{args.guard_final_servo_square_recovery_escape_early_contact_wall_steps}:{args.guard_final_servo_square_recovery_escape_early_contact_xy_max}:{args.guard_final_servo_square_recovery_escape_early_contact_z_min}-{args.guard_final_servo_square_recovery_escape_early_contact_z_max}:{args.guard_final_servo_square_recovery_escape_early_contact_margin_threshold}:require_bad_margin={args.guard_final_servo_square_recovery_escape_early_contact_require_bad_margin}/{args.guard_final_servo_square_recovery_escape_pre_lift_steps}/{args.guard_final_servo_square_recovery_escape_pre_lift_on_trigger}/{args.guard_final_servo_square_recovery_escape_flush_control_history}`",
        f"- Guard final servo square recovery escape direct fast-settle enabled/XY/Zmin-Zmax/contact/max steps/min-max episode steps/from escape/max down@Z/max XY/fast-down margin min: `{args.guard_final_servo_square_recovery_escape_direct_fast_settle_enabled}/{args.guard_final_servo_square_recovery_escape_direct_fast_settle_xy_max}/{args.guard_final_servo_square_recovery_escape_direct_fast_settle_z_min}-{args.guard_final_servo_square_recovery_escape_direct_fast_settle_z_max}/{args.guard_final_servo_square_recovery_escape_direct_fast_settle_contact_max}/{args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_steps}/{args.guard_final_servo_square_recovery_escape_direct_fast_settle_min_steps_since_reset}-{args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_steps_since_reset}/{args.guard_final_servo_square_recovery_escape_direct_fast_settle_from_escape_enabled}:{args.guard_final_servo_square_recovery_escape_direct_fast_settle_from_escape_min_phase_steps}/{args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_down_action}@{args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_down_z_min}/{args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_xy_action}/{args.guard_final_servo_square_recovery_escape_direct_fast_settle_fast_down_margin_min}`",
        f"- Guard final servo square recovery escape recenter no-up/descend enabled/XY/Z/contact/margin/max down: `{args.guard_final_servo_square_recovery_escape_recenter_no_up_enabled}/{args.guard_final_servo_square_recovery_escape_recenter_descend_enabled}/{args.guard_final_servo_square_recovery_escape_recenter_descend_xy_max}/{args.guard_final_servo_square_recovery_escape_recenter_descend_z_min}-{args.guard_final_servo_square_recovery_escape_recenter_descend_z_max}/{args.guard_final_servo_square_recovery_escape_recenter_descend_contact_max}/{args.guard_final_servo_square_recovery_escape_recenter_descend_margin_min}/{args.guard_final_servo_square_recovery_escape_recenter_descend_max_down_action}`",
        f"- Guard final servo square recovery escape recenter drift-lift enabled/min phase/XY/Z/contact/yaw/tilt: `{args.guard_final_servo_square_recovery_escape_recenter_drift_lift_enabled}/{args.guard_final_servo_square_recovery_escape_recenter_drift_lift_min_phase_steps}/{args.guard_final_servo_square_recovery_escape_recenter_drift_lift_xy_min}/{args.guard_final_servo_square_recovery_escape_recenter_drift_lift_z_min}-{args.guard_final_servo_square_recovery_escape_recenter_drift_lift_z_max}/{args.guard_final_servo_square_recovery_escape_recenter_drift_lift_contact_max}/{args.guard_final_servo_square_recovery_escape_recenter_drift_lift_yaw_min_deg}/{args.guard_final_servo_square_recovery_escape_recenter_drift_lift_tilt_min_deg}`",
        f"- Guard final servo square recovery escape late recenter descend enabled/min episode/min phase/XY/Z/contact/margin/tilt/max down/max XY/hold release@Z: `{args.guard_final_servo_square_recovery_escape_late_recenter_descend_enabled}/{args.guard_final_servo_square_recovery_escape_late_recenter_descend_min_steps_since_reset}/{args.guard_final_servo_square_recovery_escape_late_recenter_descend_min_phase_steps}/{args.guard_final_servo_square_recovery_escape_late_recenter_descend_xy_max}/{args.guard_final_servo_square_recovery_escape_late_recenter_descend_z_min}-{args.guard_final_servo_square_recovery_escape_late_recenter_descend_z_max}/{args.guard_final_servo_square_recovery_escape_late_recenter_descend_contact_max}/{args.guard_final_servo_square_recovery_escape_late_recenter_descend_margin_min}-{args.guard_final_servo_square_recovery_escape_late_recenter_descend_margin_max}/{args.guard_final_servo_square_recovery_escape_late_recenter_descend_tilt_max_deg}/{args.guard_final_servo_square_recovery_escape_late_recenter_descend_max_down_action}/{args.guard_final_servo_square_recovery_escape_late_recenter_descend_max_xy_action}/{args.guard_final_servo_square_recovery_escape_late_recenter_descend_hold_release_enabled}@{args.guard_final_servo_square_recovery_escape_late_recenter_descend_hold_z_min}`",
        f"- Guard final servo square recovery escape late clean direct finish enabled/min episode/min phase/brake/XY/Z/contact/margins/yaw/tilt: `{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_enabled}/{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_steps_since_reset}/{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_phase_steps}/{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_brake_attempts}/{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_xy_max}/{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_z_min}-{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_z_max}/{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_contact_max}/{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_margin_min}:{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_topdown_margin_min}/{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_yaw_max_deg}/{args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_tilt_max_deg}`",
        f"- Guard final servo square recovery escape no-contact XY-pop recenter enabled/XY/Z/contact/max pop-hold/margins/yaw/tilt: `{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_enabled}/{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_xy_min}-{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_xy_max}/{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_z_min}-{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_z_max}/{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_contact_max}/{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_max_contact_pop_hold_attempts}/{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_margin_min}:{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_topdown_margin_min}/{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_yaw_max_deg}/{args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_tilt_max_deg}`",
        f"- Guard final servo square recovery escape early-risk enabled/steps/XY/Z/margin: `{args.guard_final_servo_square_recovery_escape_early_risk_enabled}/{args.guard_final_servo_square_recovery_escape_early_risk_steps}/{args.guard_final_servo_square_recovery_escape_early_risk_xy_max}/{args.guard_final_servo_square_recovery_escape_early_risk_z_min}-{args.guard_final_servo_square_recovery_escape_early_risk_z_max}/{args.guard_final_servo_square_recovery_escape_early_risk_margin_threshold}`",
        f"- Guard final servo split recovery enabled: `{args.guard_final_servo_split_recovery_enabled}`",
        f"- Guard final servo contact reinsert enabled: `{args.guard_final_servo_contact_reinsert_enabled}`",
        f"- Guard final servo contact unjam steps/tilt/XY/Z/lift/release/max up/wall bias: `{args.guard_final_servo_contact_unjam_wall_steps}/{args.guard_final_servo_contact_unjam_tilt_deg}/{args.guard_final_servo_contact_unjam_xy_max}/{args.guard_final_servo_contact_unjam_z_max}/{args.guard_final_servo_contact_unjam_lift_height}/{args.guard_final_servo_contact_unjam_release_xy}/{args.guard_final_servo_contact_unjam_max_up_action}/{args.guard_final_servo_contact_unjam_wall_bias}`",
        f"- Guard final servo contact reinsert orient hold/tilt/steps/max steps/max XY/tip lock/gain/max offset/descend max: `{args.guard_final_servo_contact_reinsert_orient_hold_enabled}/{args.guard_final_servo_contact_reinsert_orient_tilt_deg}/{args.guard_final_servo_contact_reinsert_orient_stable_steps}/{args.guard_final_servo_contact_reinsert_orient_max_steps}/{args.guard_final_servo_contact_reinsert_orient_max_xy_action}/{args.guard_final_servo_contact_reinsert_orient_tip_lock_enabled}/{args.guard_final_servo_contact_reinsert_orient_tip_lock_drift_gain}/{args.guard_final_servo_contact_reinsert_orient_tip_lock_max_offset}/{args.guard_final_servo_contact_reinsert_descend_max_steps}`",
        f"- Guard final servo contact reinsert high reapproach enabled/height/release/stable/max steps/max XY/max up: `{args.guard_final_servo_contact_reinsert_high_reapproach_enabled}/{args.guard_final_servo_contact_reinsert_high_reapproach_height}/{args.guard_final_servo_contact_reinsert_high_reapproach_release_xy}/{args.guard_final_servo_contact_reinsert_high_reapproach_stable_steps}/{args.guard_final_servo_contact_reinsert_high_reapproach_max_steps}/{args.guard_final_servo_contact_reinsert_high_reapproach_max_xy_action}/{args.guard_final_servo_contact_reinsert_high_reapproach_max_up_action}`",
        f"- Guard final servo contact reinsert micro align enabled/Z/XY/release/tilt/max/stall/progress/max XY/up: `{args.guard_final_servo_contact_reinsert_micro_align_enabled}/{args.guard_final_servo_contact_reinsert_micro_align_z_max}/{args.guard_final_servo_contact_reinsert_micro_align_xy_max}/{args.guard_final_servo_contact_reinsert_micro_align_release_xy}/{args.guard_final_servo_contact_reinsert_micro_align_tilt_deg}/{args.guard_final_servo_contact_reinsert_micro_align_max_steps}/{args.guard_final_servo_contact_reinsert_micro_align_stall_steps}/{args.guard_final_servo_contact_reinsert_micro_align_min_xy_progress}/{args.guard_final_servo_contact_reinsert_micro_align_max_xy_action}/{args.guard_final_servo_contact_reinsert_micro_align_up_action}`",
        f"- Guard final servo near-miss steps/XY/Z/contact/tilt/max steps/max down/bias: `{args.guard_final_servo_near_miss_steps}/{args.guard_final_servo_near_miss_xy_max}/{args.guard_final_servo_near_miss_z_max}/{args.guard_final_servo_near_miss_contact_max}/{args.guard_final_servo_near_miss_tilt_max_deg}/{args.guard_final_servo_near_miss_max_steps}/{args.guard_final_servo_near_miss_max_down_action}/{tuple(args.guard_final_servo_near_miss_xy_bias)}`",
        f"- Guard final servo square fast settle enabled/XY/Z/release/contact/tilt/max steps/max XY/low-Z XY@Z/max down/low-Z down@Z: `{args.guard_final_servo_square_fast_settle_enabled}/{args.guard_final_servo_square_fast_settle_xy_max}/{args.guard_final_servo_square_fast_settle_z_max}/{args.guard_final_servo_square_fast_settle_release_xy}/{args.guard_final_servo_square_fast_settle_contact_max}/{args.guard_final_servo_square_fast_settle_tilt_max_deg}/{args.guard_final_servo_square_fast_settle_max_steps}/{args.guard_final_servo_square_fast_settle_max_xy_action}/{args.guard_final_servo_square_fast_settle_low_z_max_xy_action}@{args.guard_final_servo_square_fast_settle_low_z_threshold}/{args.guard_final_servo_square_fast_settle_max_down_action}/{args.guard_final_servo_square_fast_settle_low_z_max_down_action}@{args.guard_final_servo_square_fast_settle_low_z_down_threshold}`",
        f"- Guard final servo square fast settle late down boost enabled/max down/max XY/XY/Z/brake/contact/phase/margin/clean: `{args.guard_final_servo_square_fast_settle_late_down_boost_enabled}/{args.guard_final_servo_square_fast_settle_late_down_boost_max_down_action}/{args.guard_final_servo_square_fast_settle_late_down_boost_max_xy_action}/{args.guard_final_servo_square_fast_settle_late_down_boost_xy_max}/{args.guard_final_servo_square_fast_settle_late_down_boost_z_min}-{args.guard_final_servo_square_fast_settle_late_down_boost_z_max}/{args.guard_final_servo_square_fast_settle_late_down_boost_min_brake_attempts}/{args.guard_final_servo_square_fast_settle_late_down_boost_contact_max}/{args.guard_final_servo_square_fast_settle_late_down_boost_min_phase_steps}/{args.guard_final_servo_square_fast_settle_late_down_boost_margin_min}/{args.guard_final_servo_square_fast_settle_late_down_boost_min_clean_steps}`",
        f"- Guard final servo square fast settle low-Z contact down guard enabled/min step/wall/XY/Z/brake/max up: `{args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_enabled}/{args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_min_steps_since_reset}/{args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_wall_count}/{args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_xy_max}/{args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_z_max}/{args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_min_brake_attempts}/{args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_max_up_action}`",
        f"- Guard final servo square fast settle contact-pop hold enabled/steps/wall/XY/Z/contact/phase/brake/attempts/max up: `{args.guard_final_servo_square_fast_settle_contact_pop_hold_enabled}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_steps}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_wall_count}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_xy_min}-{args.guard_final_servo_square_fast_settle_contact_pop_hold_xy_max}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_z_min}-{args.guard_final_servo_square_fast_settle_contact_pop_hold_z_max}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_contact_max}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_min_phase_steps}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_min_brake_attempts}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_max_attempts}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_max_up_action}`",
        f"- Guard final servo square fast settle contact-pop hold recenter enabled/phase/XY/Z/contact/margins/yaw/tilt: `{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_enabled}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_min_phase_steps}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_xy_min}-{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_xy_max}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_z_min}-{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_z_max}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_contact_max}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_margin_min}:{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_topdown_margin_min}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_tilt_max_deg}`",
        f"- Guard final servo square fast settle contact-pop exhausted recenter enabled/attempts/XY/Z/contact/margins/yaw/tilt: `{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_enabled}/{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_min_attempts}/{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_xy_min}-{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_xy_max}/{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_z_min}-{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_z_max}/{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_contact_max}/{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_margin_min}:{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_topdown_margin_min}/{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_tilt_max_deg}`",
        f"- Guard final servo square fast settle no-contact pop-hold enabled/steps/XY/Z/contact/brake/pop attempts/pop phase/attempts/margins/yaw/tilt/max up: `{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_enabled}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_steps}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_xy_min}-{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_xy_max}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_z_min}-{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_z_max}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_contact_max}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_min_brake_attempts}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_max_contact_pop_hold_attempts}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_min_contact_pop_hold_phase_steps}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_max_attempts}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_margin_min}:{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_topdown_margin_min}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_tilt_max_deg}/{args.guard_final_servo_square_fast_settle_no_contact_pop_hold_max_up_action}`",
        f"- Guard final servo square fast settle pre-pop guard enabled/steps/XY/Z/contact/phase/brake/soft-hold/attempts/margins/yaw/tilt/max up: `{args.guard_final_servo_square_fast_settle_pre_pop_guard_enabled}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_steps}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_xy_max}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_z_min}-{args.guard_final_servo_square_fast_settle_pre_pop_guard_z_max}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_contact_max}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_min_phase_steps}-{args.guard_final_servo_square_fast_settle_pre_pop_guard_max_phase_steps}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_min_brake_attempts}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_min_soft_hold_attempts}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_max_attempts}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_margin_min}-{args.guard_final_servo_square_fast_settle_pre_pop_guard_margin_max}:{args.guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_min}-{args.guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_max}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_tilt_min_deg}-{args.guard_final_servo_square_fast_settle_pre_pop_guard_tilt_max_deg}/{args.guard_final_servo_square_fast_settle_pre_pop_guard_max_up_action}`",
        f"- Guard final servo square fast settle pre-pop limit enabled/max XY/max down: `{args.guard_final_servo_square_fast_settle_pre_pop_limit_enabled}/{args.guard_final_servo_square_fast_settle_pre_pop_limit_max_xy_action}/{args.guard_final_servo_square_fast_settle_pre_pop_limit_max_down_action}`",
        f"- Guard final servo square fast settle severe-pop reapproach enabled/XY/Z/contact/brake/min step/attempts/height/pre-lift/margins/yaw/tilt: `{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_enabled}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_xy_min}-{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_xy_max}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_z_min}-{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_z_max}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_contact_max}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_min_brake_attempts}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_min_steps_since_reset}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_max_attempts}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_height}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_pre_lift_enabled}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_margin_min}:{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_topdown_margin_min}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_severe_pop_reapproach_tilt_max_deg}`",
        f"- Guard final servo square fast settle clearance hold enabled/steps/XY/Z/margin/wall/contact/brake/phase/attempts/max up: `{args.guard_final_servo_square_fast_settle_clearance_hold_enabled}/{args.guard_final_servo_square_fast_settle_clearance_hold_steps}/{args.guard_final_servo_square_fast_settle_clearance_hold_xy_max}/{args.guard_final_servo_square_fast_settle_clearance_hold_z_min}-{args.guard_final_servo_square_fast_settle_clearance_hold_z_max}/{args.guard_final_servo_square_fast_settle_clearance_hold_margin_min}-{args.guard_final_servo_square_fast_settle_clearance_hold_margin_threshold}/{args.guard_final_servo_square_fast_settle_clearance_hold_wall_count}/{args.guard_final_servo_square_fast_settle_clearance_hold_contact_max}/{args.guard_final_servo_square_fast_settle_clearance_hold_min_brake_attempts}/{args.guard_final_servo_square_fast_settle_clearance_hold_min_phase_steps}/{args.guard_final_servo_square_fast_settle_clearance_hold_max_attempts}/{args.guard_final_servo_square_fast_settle_clearance_hold_max_up_action}`",
        f"- Guard final servo square fast settle low-Z relief enabled/wall/XY/Z/margin/contact/brake/phase/attempts/lift/steps/release/max up/max XY/wide recenter: `{args.guard_final_servo_square_fast_settle_low_z_relief_enabled}/{args.guard_final_servo_square_fast_settle_low_z_relief_wall_count}/{args.guard_final_servo_square_fast_settle_low_z_relief_xy_max}/{args.guard_final_servo_square_fast_settle_low_z_relief_z_min}-{args.guard_final_servo_square_fast_settle_low_z_relief_z_max}/{args.guard_final_servo_square_fast_settle_low_z_relief_margin_min}-{args.guard_final_servo_square_fast_settle_low_z_relief_margin_threshold}/{args.guard_final_servo_square_fast_settle_low_z_relief_contact_max}/{args.guard_final_servo_square_fast_settle_low_z_relief_min_brake_attempts}/{args.guard_final_servo_square_fast_settle_low_z_relief_min_phase_steps}/{args.guard_final_servo_square_fast_settle_low_z_relief_max_attempts}/{args.guard_final_servo_square_fast_settle_low_z_relief_lift_height}@{args.guard_final_servo_square_fast_settle_low_z_relief_target_z_max}/{args.guard_final_servo_square_fast_settle_low_z_relief_lift_steps}:{args.guard_final_servo_square_fast_settle_low_z_relief_recenter_steps}/{args.guard_final_servo_square_fast_settle_low_z_relief_release_xy}/{args.guard_final_servo_square_fast_settle_low_z_relief_max_up_action}/{args.guard_final_servo_square_fast_settle_low_z_relief_max_xy_action}/{args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_enabled}:start>={args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_start_z_min}:xy<={args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_xy_max}:z<={args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_z_max}:steps={args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_max_steps}:pop>={args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_contact_pop_min_attempts}:popxy<={args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_contact_pop_xy_max}`",
        f"- Guard final servo square fast settle low-Z stall relief enabled/XY/Z/margin/contact/brake/phase/stall/attempts/hold: `{args.guard_final_servo_square_fast_settle_low_z_stall_relief_enabled}/{args.guard_final_servo_square_fast_settle_low_z_stall_relief_xy_max}/{args.guard_final_servo_square_fast_settle_low_z_stall_relief_z_min}-{args.guard_final_servo_square_fast_settle_low_z_stall_relief_z_max}/{args.guard_final_servo_square_fast_settle_low_z_stall_relief_margin_min}-{args.guard_final_servo_square_fast_settle_low_z_stall_relief_margin_threshold}/{args.guard_final_servo_square_fast_settle_low_z_stall_relief_contact_max}/{args.guard_final_servo_square_fast_settle_low_z_stall_relief_min_brake_attempts}/{args.guard_final_servo_square_fast_settle_low_z_stall_relief_min_phase_steps}/{args.guard_final_servo_square_fast_settle_low_z_stall_relief_min_stall_steps}/{args.guard_final_servo_square_fast_settle_low_z_stall_relief_max_attempts}/{args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_enabled}:{args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_steps}:{args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_max_up_action}:min_contact_pop={args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_min_contact_pop_hold_attempts}`",
        f"- Guard final servo square fast settle contact soft-hold enabled/steps/XY/Z/margin/yaw/tilt/wall/contact/phase/episode step/subsequent phase/subsequent episode step/subsequent Z max/subsequent margin min/attempts/max up/extend: `{args.guard_final_servo_square_fast_settle_contact_soft_hold_enabled}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_steps}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_xy_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_z_min}-{args.guard_final_servo_square_fast_settle_contact_soft_hold_z_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_margin_min}-{args.guard_final_servo_square_fast_settle_contact_soft_hold_margin_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_tilt_max_deg}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_wall_count}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_contact_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_min_phase_steps}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_min_steps_since_reset}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_min_phase_steps}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_min_steps_since_reset}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_z_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_margin_min}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_max_attempts}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_max_up_action}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_enabled}:{args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_contact_max}:{args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_max_steps}@{args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_min_steps_since_reset}`",
        f"- Guard final servo square fast settle contact soft-hold release-continue enabled/steps/XY/Z/margin/yaw/tilt/contact/max XY/max down: `{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_enabled}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_steps}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_xy_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_z_min}-{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_z_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_margin_min}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_tilt_max_deg}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_contact_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_max_xy_action}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_max_down_action}`",
        f"- Guard final servo square fast settle contact soft-hold release contact-brake enabled/wall/XY/Z/contact/margin/yaw/tilt/max phase/min soft-hold/soft-hold-first: `{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_enabled}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_wall_count}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_xy_min}-{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_xy_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_z_min}-{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_z_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_contact_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_margin_min}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_tilt_max_deg}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_max_phase_steps}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_min_soft_hold_attempts}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_soft_hold_first_enabled}`",
        f"- Guard final servo square fast settle contact soft-hold release pop-hold enabled/steps/wall/XY/Z/contact/margin/yaw/tilt/max phase/min soft-hold/max attempts/max up: `{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_enabled}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_steps}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_wall_count}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_xy_min}-{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_xy_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_z_min}-{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_z_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_contact_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_margin_min}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_tilt_max_deg}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_phase_steps}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_min_soft_hold_attempts}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_attempts}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_up_action}`",
        f"- Guard final servo square fast settle contact soft-hold large-pop recenter enabled/XY/Z/contact/margins/yaw/tilt: `{args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_enabled}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_xy_min}-{args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_xy_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_z_min}-{args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_z_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_contact_max}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_margin_min}:{args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_topdown_margin_min}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_tilt_max_deg}`",
        f"- Guard final servo square fast settle late finish continue enabled/step/XY/Z/margin/topdown/yaw/tilt/contact: `{args.guard_final_servo_square_fast_settle_late_finish_continue_enabled}/{args.guard_final_servo_square_fast_settle_late_finish_continue_min_steps_since_reset}/{args.guard_final_servo_square_fast_settle_late_finish_continue_xy_max}/{args.guard_final_servo_square_fast_settle_late_finish_continue_z_min}-{args.guard_final_servo_square_fast_settle_late_finish_continue_z_max}/{args.guard_final_servo_square_fast_settle_late_finish_continue_margin_min}/{args.guard_final_servo_square_fast_settle_late_finish_continue_topdown_margin_min}/{args.guard_final_servo_square_fast_settle_late_finish_continue_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_late_finish_continue_tilt_max_deg}/{args.guard_final_servo_square_fast_settle_late_finish_continue_contact_max}`",
        f"- Guard final servo square fast settle late escape veto enabled/step/XY/Z/contact/margin/topdown/yaw/tilt: `{args.guard_final_servo_square_fast_settle_late_escape_veto_enabled}/{args.guard_final_servo_square_fast_settle_late_escape_veto_min_steps_since_reset}/{args.guard_final_servo_square_fast_settle_late_escape_veto_xy_max}/{args.guard_final_servo_square_fast_settle_late_escape_veto_z_min}-{args.guard_final_servo_square_fast_settle_late_escape_veto_z_max}/{args.guard_final_servo_square_fast_settle_late_escape_veto_contact_max}/{args.guard_final_servo_square_fast_settle_late_escape_veto_margin_min}/{args.guard_final_servo_square_fast_settle_late_escape_veto_topdown_margin_min}/{args.guard_final_servo_square_fast_settle_late_escape_veto_yaw_max_deg}/{args.guard_final_servo_square_fast_settle_late_escape_veto_tilt_max_deg}`",
        f"- Guard final servo square contact brake enabled/wall/XY/Z/lift/release/stable/max steps/max attempts/max XY/max up/clearance/margin/require bad margin/repeat margin/exhausted escape/reset/exhausted continue: `{args.guard_final_servo_square_contact_brake_enabled}/{args.guard_final_servo_square_contact_brake_wall_steps}/{args.guard_final_servo_square_contact_brake_xy_max}/{args.guard_final_servo_square_contact_brake_z_min}-{args.guard_final_servo_square_contact_brake_z_max}/{args.guard_final_servo_square_contact_brake_lift_height}@{args.guard_final_servo_square_contact_brake_lift_z_max}/{args.guard_final_servo_square_contact_brake_release_xy}/{args.guard_final_servo_square_contact_brake_stable_steps}/{args.guard_final_servo_square_contact_brake_max_steps}/{args.guard_final_servo_square_contact_brake_max_attempts}/{args.guard_final_servo_square_contact_brake_max_xy_action}/{args.guard_final_servo_square_contact_brake_max_up_action}/{args.guard_final_servo_square_contact_brake_max_clearance}/{args.guard_final_servo_square_contact_brake_margin_threshold}/{args.guard_final_servo_square_contact_brake_require_bad_margin}/{args.guard_final_servo_square_contact_brake_repeat_margin_gate_enabled}:{args.guard_final_servo_square_contact_brake_repeat_margin_threshold}/{args.guard_final_servo_square_contact_brake_exhausted_escape_enabled}/{args.guard_final_servo_square_contact_brake_reset_attempts_after_escape_enabled}/{args.guard_final_servo_square_contact_brake_exhausted_continue_enabled}:{args.guard_final_servo_square_contact_brake_exhausted_continue_min_steps_since_reset}:{args.guard_final_servo_square_contact_brake_exhausted_continue_xy_max}:{args.guard_final_servo_square_contact_brake_exhausted_continue_z_min}-{args.guard_final_servo_square_contact_brake_exhausted_continue_z_max}:{args.guard_final_servo_square_contact_brake_exhausted_continue_contact_max}:{args.guard_final_servo_square_contact_brake_exhausted_continue_tilt_max_deg}:{args.guard_final_servo_square_contact_brake_exhausted_continue_margin_min}:{args.guard_final_servo_square_contact_brake_exhausted_continue_topdown_margin_min}:{args.guard_final_servo_square_contact_brake_exhausted_continue_yaw_max_deg}`",
        f"- Guard final servo square contact brake release flush enabled/steps/min attempts/min step/XY/Z/contact: `{args.guard_final_servo_square_contact_brake_release_flush_enabled}/{args.guard_final_servo_square_contact_brake_release_flush_steps}/{args.guard_final_servo_square_contact_brake_release_flush_min_brake_attempts}/{args.guard_final_servo_square_contact_brake_release_flush_min_steps_since_reset}/{args.guard_final_servo_square_contact_brake_release_flush_xy_max}/{args.guard_final_servo_square_contact_brake_release_flush_z_min}-{args.guard_final_servo_square_contact_brake_release_flush_z_max}/{args.guard_final_servo_square_contact_brake_release_flush_contact_max}`",
        f"- Guard final servo square contact brake preemptive hold enabled/wall/steps/min attempts/XY/Z/max up/clearance/margin/require bad margin/yaw min/expanded XY/clean release: `{args.guard_final_servo_square_contact_brake_preemptive_hold_enabled}/{args.guard_final_servo_square_contact_brake_preemptive_hold_wall_steps}/{args.guard_final_servo_square_contact_brake_preemptive_hold_steps}/{args.guard_final_servo_square_contact_brake_preemptive_hold_min_brake_attempts}/{args.guard_final_servo_square_contact_brake_preemptive_hold_xy_max}/{args.guard_final_servo_square_contact_brake_preemptive_hold_z_min}-{args.guard_final_servo_square_contact_brake_preemptive_hold_z_max}/{args.guard_final_servo_square_contact_brake_preemptive_hold_max_up_action}/{args.guard_final_servo_square_contact_brake_preemptive_hold_max_clearance}/{args.guard_final_servo_square_contact_brake_preemptive_hold_margin_threshold}/{args.guard_final_servo_square_contact_brake_preemptive_hold_require_bad_margin}/{args.guard_final_servo_square_contact_brake_preemptive_hold_yaw_min_deg}/{args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy_enabled}:{args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy_max}@{args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_z_min}:margin>={args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_margin_min}:yaw<={args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_yaw_max_deg}/{args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_enabled}:brake<={args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_max_brake_attempts}:contact<={args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_contact_max}:xy<={args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_xy_max}:z={args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_z_min}-{args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_z_max}:margin>={args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_margin_min}:tilt<={args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_tilt_max_deg}`",
        f"- Guard final servo square contact brake preemptive hold pop recenter enabled/phase/XY/Z/contact/margins/yaw/tilt: `{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_enabled}/{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_min_phase_steps}/{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_xy_min}-{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_xy_max}/{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_z_min}-{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_z_max}/{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_contact_max}/{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_margin_min}:{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_topdown_margin_min}/{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_yaw_max_deg}/{args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_tilt_max_deg}`",
        f"- Guard final servo square contact brake late lift release enabled/brake/phase/step/contact/XY/Z/margin/yaw/tilt: `{args.guard_final_servo_square_contact_brake_late_lift_release_enabled}/{args.guard_final_servo_square_contact_brake_late_lift_release_min_brake_attempts}/{args.guard_final_servo_square_contact_brake_late_lift_release_min_phase_steps}/{args.guard_final_servo_square_contact_brake_late_lift_release_min_steps_since_reset}/{args.guard_final_servo_square_contact_brake_late_lift_release_contact_max}/{args.guard_final_servo_square_contact_brake_late_lift_release_xy_max}/{args.guard_final_servo_square_contact_brake_late_lift_release_z_min}-{args.guard_final_servo_square_contact_brake_late_lift_release_z_max}/{args.guard_final_servo_square_contact_brake_late_lift_release_margin_min}/{args.guard_final_servo_square_contact_brake_late_lift_release_yaw_max_deg}/{args.guard_final_servo_square_contact_brake_late_lift_release_tilt_max_deg}`",
        f"- Guard final servo square high-Z descend enabled/stall/XY/Z/contact/tilt/margin/max/max XY/down/low-Z XY/down/staged/mid/hold/low-Z brake: `{args.guard_final_servo_square_high_z_descend_enabled}/{args.guard_final_servo_square_high_z_descend_stall_steps}/{args.guard_final_servo_square_high_z_descend_xy_max}/{args.guard_final_servo_square_high_z_descend_z_min}-{args.guard_final_servo_square_high_z_descend_z_max}/{args.guard_final_servo_square_high_z_descend_contact_max}/{args.guard_final_servo_square_high_z_descend_tilt_max_deg}/{args.guard_final_servo_square_high_z_descend_margin_min}/{args.guard_final_servo_square_high_z_descend_max_steps}/{args.guard_final_servo_square_high_z_descend_max_xy_action}/{args.guard_final_servo_square_high_z_descend_max_down_action}/{args.guard_final_servo_square_high_z_descend_low_z_max_xy_action}@{args.guard_final_servo_square_high_z_descend_low_z_threshold}/{args.guard_final_servo_square_high_z_descend_low_z_max_down_action}@{args.guard_final_servo_square_high_z_descend_low_z_threshold}/{args.guard_final_servo_square_high_z_descend_staged_enabled}:{args.guard_final_servo_square_high_z_descend_mid_z_max_xy_action}:{args.guard_final_servo_square_high_z_descend_mid_z_max_down_action}@{args.guard_final_servo_square_high_z_descend_mid_z_threshold}/{args.guard_final_servo_square_high_z_descend_low_z_hold_steps}:{args.guard_final_servo_square_high_z_descend_low_z_hold_min_phase_steps}:{args.guard_final_servo_square_high_z_descend_low_z_hold_max_attempts}:{args.guard_final_servo_square_high_z_descend_low_z_hold_xy_max}:{args.guard_final_servo_square_high_z_descend_low_z_hold_max_up_action}/{args.guard_final_servo_square_high_z_descend_contact_brake_enabled}:{args.guard_final_servo_square_high_z_descend_contact_brake_wall_count}@{args.guard_final_servo_square_high_z_descend_contact_brake_z_max}:{args.guard_final_servo_square_high_z_descend_contact_brake_xy_max}`",
        f"- Guard final servo square margin/yaw settle enabled/stall/XY/Z/contact/margin/yaw/lift/max attempts: `{args.guard_final_servo_square_margin_yaw_settle_enabled}/{args.guard_final_servo_square_margin_yaw_settle_stall_steps}/{args.guard_final_servo_square_margin_yaw_settle_xy_max}/{args.guard_final_servo_square_margin_yaw_settle_z_min}-{args.guard_final_servo_square_margin_yaw_settle_z_max}/{args.guard_final_servo_square_margin_yaw_settle_contact_max}/{args.guard_final_servo_square_margin_yaw_settle_margin_threshold}/{args.guard_final_servo_square_margin_yaw_settle_yaw_deg}/{args.guard_final_servo_square_margin_yaw_settle_lift_height}/{args.guard_final_servo_square_margin_yaw_settle_max_attempts}`",
        f"- Guard approach recenter enabled/requires stateful recovery: `{args.guard_approach_recenter_enabled}/{args.guard_approach_recenter_requires_stateful_recovery}`",
        f"- Guard approach recenter XY window/stable/bias: `{args.guard_approach_recenter_trigger_xy}-{args.guard_approach_recenter_max_xy}/{args.guard_approach_recenter_stable_xy}/{tuple(args.guard_approach_recenter_xy_bias)}`",
        f"- Guard approach recenter Z window/height/tolerance/max steps: `{args.guard_approach_recenter_min_z}-{args.guard_approach_recenter_start_z}/{args.guard_approach_recenter_height}/{args.guard_approach_recenter_z_tolerance}/{args.guard_approach_recenter_max_steps}`",
        f"- Guard early approach assist enabled: `{args.guard_early_approach_assist_enabled}`",
        f"- Guard early approach assist XY/Z/target/max steps: `{args.guard_early_approach_assist_trigger_xy}->{args.guard_early_approach_assist_release_xy}/{args.guard_early_approach_assist_min_z}-{args.guard_early_approach_assist_max_z}/{args.guard_early_approach_assist_target_height}/{args.guard_early_approach_assist_max_steps}`",
        f"- Guarded oracle mode: `{args.guarded_oracle_mode}`",
        f"- Guarded align/insert XY: `{args.guarded_align_xy_tolerance}/{args.guarded_insert_xy_tolerance}`",
        f"- Guarded max XY/down/up action: `{args.guarded_max_xy_action}/{args.guarded_max_down_action}/{args.guarded_max_up_action}`",
        f"- Guarded prediction steps: `{args.guarded_prediction_steps}`",
        f"- Guarded hold Z until insert: `{args.guarded_hold_z_until_insert}`",
        f"- Guarded lift before lateral: `{args.guarded_lift_before_lateral}`",
        f"- Guarded lift-before-lateral XY/Z margin: `{args.guarded_lift_before_lateral_xy_tolerance}/{args.guarded_lift_before_lateral_z_margin}`",
        f"- Contact recovery XY/Z/lift/Z tol/max down: `{args.contact_recovery_xy_tolerance}/{args.contact_recovery_z_max}/{args.contact_recovery_lift_height}/{args.contact_recovery_lift_z_tolerance}/{args.contact_recovery_max_down_action}`",
        f"- Timeout progress XY/Z/max down: `{args.timeout_progress_xy_tolerance}/{args.timeout_progress_z_max}/{args.timeout_progress_max_down_action}`",
        "",
        "| Scenario | Level | Mode | Image | Image target | Control state | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Retry steps | Latch steps | Hover steps | Near limited | Fixture steps | Fixture realign | Preinsert | Approach rec | Adapter | Final insert adapter | Final insert pulse | Final insert macro | Visual yaw | Early approach | Stateful rec | Final servo | Final servo descend | Final XY | Final Z |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {name} | {level} | {control_mode} | {image_ablation} | {image_ablation_target} | {control_state_ablation} | {guard_enabled} | {success_rate:.3f} | {collision_rate:.3f} | "
            "{timeout_rate:.3f} | {mean_return:.3f} | {mean_steps:.1f} | "
            "{mean_guarded_steps:.1f} ({mean_guarded_step_fraction:.2f}) | "
            "{mean_retry_steps:.1f} ({mean_retry_step_fraction:.2f}) | "
            "{mean_latch_steps:.1f} ({mean_latch_step_fraction:.2f}, down {mean_latch_descent_fraction:.2f}) | "
            "{mean_hover_steps:.1f} ({mean_hover_step_fraction:.2f}, latched {mean_hover_latched_fraction:.2f}, block {mean_hover_blocked_fraction:.2f}) | "
            "{mean_near_limited_steps:.1f} ({mean_near_limited_fraction:.2f}) | "
            "{mean_fixture_clearance_steps:.1f} ({mean_fixture_clearance_fraction:.2f}) | "
            "{mean_fixture_clearance_realign_steps:.1f} ({mean_fixture_clearance_realign_fraction:.2f}) | "
            "{mean_preinsert_recenter_steps:.1f} ({mean_preinsert_recenter_fraction:.2f}, trig {mean_preinsert_recenter_triggers:.2f}, rel {mean_preinsert_recenter_releases:.2f}) | "
            "{mean_approach_recenter_steps:.1f} ({mean_approach_recenter_fraction:.2f}, trig {mean_approach_recenter_triggers:.2f}, rel {mean_approach_recenter_releases:.2f}) | "
            "{mean_approach_adapter_steps:.1f} ({mean_approach_adapter_fraction:.2f}) | "
            "{mean_final_insert_adapter_steps:.1f} ({mean_final_insert_adapter_fraction:.2f}) | "
            "{mean_final_insert_adapter_lift_pulse_steps:.1f} | "
            "{mean_final_insert_macro_recovery_steps:.1f} ({mean_final_insert_macro_recovery_fraction:.2f}, trig {mean_final_insert_macro_recovery_triggers:.2f}) | "
            "{mean_visual_yaw_align_steps:.1f} ({mean_visual_yaw_align_fraction:.2f}, block {mean_visual_yaw_align_blocked_steps:.1f}) | "
            "{mean_early_approach_assist_steps:.1f} ({mean_early_approach_assist_fraction:.2f}, trig {mean_early_approach_assist_triggers:.2f}, rel {mean_early_approach_assist_releases:.2f}) | "
            "{mean_stateful_recovery_steps:.1f} ({mean_stateful_recovery_fraction:.2f}, trig {mean_stateful_recovery_triggers:.2f}, rel {mean_stateful_recovery_releases:.2f}) | "
            "{mean_final_servo_steps:.1f} ({mean_final_servo_step_fraction:.2f}, trig {mean_final_servo_triggers:.2f}, rearm {mean_final_servo_rearms:.2f}, rec {mean_final_servo_recovery_triggers:.2f}) | "
            "{mean_final_servo_descent_steps:.1f} ({mean_final_servo_descent_fraction:.2f}) | {mean_final_dist_xy:.5f} | "
            "{mean_final_dist_z:.5f} |".format(**row)
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved Markdown report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")
    if args.image_ablation != "normal" and args.observation_mode != "image":
        raise ValueError("--image-ablation requires --observation-mode image.")
    if args.image_ablation != "normal" and args.image_ablation_target == "near_hole_crop":
        if not args.include_near_hole_crop:
            raise ValueError("--image-ablation-target near_hole_crop requires --include-near-hole-crop.")
    if args.near_hole_crop_size <= 0:
        raise ValueError("--near-hole-crop-size must be positive.")
    if args.near_hole_crop_source_size is not None and args.near_hole_crop_source_size <= 0:
        raise ValueError("--near-hole-crop-source-size must be positive when set.")
    if args.near_hole_crop_source_size_range is not None:
        if args.near_hole_crop_source_size_range[0] <= 0:
            raise ValueError("--near-hole-crop-source-size-range must stay positive.")
        if args.near_hole_crop_source_size_range[0] > args.near_hole_crop_source_size_range[1]:
            raise ValueError("--near-hole-crop-source-size-range must be increasing.")
    if args.control_state_ablation != "normal":
        if args.observation_mode != "image":
            raise ValueError("--control-state-ablation requires --observation-mode image.")
        if not args.include_control_state:
            raise ValueError("--control-state-ablation requires --include-control-state.")
    if args.approach_adapter_enabled:
        if args.approach_adapter is None:
            raise ValueError("--approach-adapter-enabled requires --approach-adapter.")
        if args.observation_mode != "image":
            raise ValueError("--approach-adapter-enabled requires image observations.")
        if not args.include_near_hole_crop:
            raise ValueError("--approach-adapter-enabled requires --include-near-hole-crop.")
        if not args.include_control_state:
            raise ValueError("--approach-adapter-enabled requires --include-control-state.")
    if args.approach_adapter_trigger_xy <= 0.0:
        raise ValueError("--approach-adapter-trigger-xy must be positive.")
    if args.approach_adapter_release_xy <= 0.0:
        raise ValueError("--approach-adapter-release-xy must be positive.")
    if args.approach_adapter_release_xy >= args.approach_adapter_trigger_xy:
        raise ValueError("--approach-adapter-release-xy must be less than trigger XY.")
    if args.approach_adapter_min_z < 0.0:
        raise ValueError("--approach-adapter-min-z cannot be negative.")
    if args.approach_adapter_max_z <= args.approach_adapter_min_z:
        raise ValueError("--approach-adapter-max-z must exceed min Z.")
    if args.approach_adapter_latched_min_z is not None:
        if args.approach_adapter_latched_min_z < 0.0:
            raise ValueError("--approach-adapter-latched-min-z cannot be negative.")
        if args.approach_adapter_latched_min_z > args.approach_adapter_min_z:
            raise ValueError(
                "--approach-adapter-latched-min-z must be <= --approach-adapter-min-z."
            )
    if args.approach_adapter_max_steps < 0:
        raise ValueError("--approach-adapter-max-steps cannot be negative.")
    if args.approach_adapter_episode_max_steps < 0:
        raise ValueError("--approach-adapter-episode-max-steps cannot be negative.")
    if args.approach_adapter_max_xy_residual < 0.0:
        raise ValueError("--approach-adapter-max-xy-residual cannot be negative.")
    if args.approach_adapter_max_z_residual < 0.0:
        raise ValueError("--approach-adapter-max-z-residual cannot be negative.")
    if args.approach_adapter_scale < 0.0:
        raise ValueError("--approach-adapter-scale cannot be negative.")
    if args.final_insert_adapter_enabled and args.final_insert_adapter is None:
        raise ValueError("--final-insert-adapter-enabled requires --final-insert-adapter.")
    if args.final_insert_adapter_max_xy <= 0.0:
        raise ValueError("--final-insert-adapter-max-xy must be positive.")
    if args.final_insert_adapter_min_z < 0.0:
        raise ValueError("--final-insert-adapter-min-z cannot be negative.")
    if args.final_insert_adapter_max_z <= args.final_insert_adapter_min_z:
        raise ValueError("--final-insert-adapter-max-z must exceed min Z.")
    if args.final_insert_adapter_min_phase_steps < 0:
        raise ValueError("--final-insert-adapter-min-phase-steps cannot be negative.")
    if args.final_insert_adapter_min_stall_steps < 0:
        raise ValueError("--final-insert-adapter-min-stall-steps cannot be negative.")
    if args.final_insert_adapter_square_risk_min_stall_steps < 0:
        raise ValueError(
            "--final-insert-adapter-square-risk-min-stall-steps cannot be negative."
        )
    if args.final_insert_adapter_square_risk_xy_min < 0.0:
        raise ValueError("--final-insert-adapter-square-risk-xy-min cannot be negative.")
    if args.final_insert_adapter_max_xy_action < 0.0:
        raise ValueError("--final-insert-adapter-max-xy-action cannot be negative.")
    if args.final_insert_adapter_max_up_action < 0.0:
        raise ValueError("--final-insert-adapter-max-up-action cannot be negative.")
    if args.final_insert_adapter_max_down_action < 0.0:
        raise ValueError("--final-insert-adapter-max-down-action cannot be negative.")
    if args.final_insert_adapter_max_consecutive_steps < 0:
        raise ValueError("--final-insert-adapter-max-consecutive-steps cannot be negative.")
    if args.final_insert_adapter_cooldown_steps < 0:
        raise ValueError("--final-insert-adapter-cooldown-steps cannot be negative.")
    if args.final_insert_adapter_handoff_xy <= 0.0:
        raise ValueError("--final-insert-adapter-handoff-xy must be positive.")
    if args.final_insert_adapter_handoff_min_z < 0.0:
        raise ValueError("--final-insert-adapter-handoff-min-z cannot be negative.")
    if args.final_insert_adapter_handoff_max_z <= args.final_insert_adapter_handoff_min_z:
        raise ValueError("--final-insert-adapter-handoff-max-z must exceed min Z.")
    if args.final_insert_adapter_handoff_z_action_threshold > 0.0:
        raise ValueError("--final-insert-adapter-handoff-z-action-threshold cannot be positive.")
    if args.final_insert_adapter_lift_pulse_active_steps <= 0:
        raise ValueError("--final-insert-adapter-lift-pulse-active-steps must be positive.")
    if args.final_insert_adapter_lift_pulse_stall_steps <= 0:
        raise ValueError("--final-insert-adapter-lift-pulse-stall-steps must be positive.")
    if args.final_insert_adapter_lift_pulse_steps <= 0:
        raise ValueError("--final-insert-adapter-lift-pulse-steps must be positive.")
    if args.final_insert_adapter_lift_pulse_period_steps <= 0:
        raise ValueError("--final-insert-adapter-lift-pulse-period-steps must be positive.")
    if args.final_insert_adapter_lift_pulse_z_action <= 0.0:
        raise ValueError("--final-insert-adapter-lift-pulse-z-action must be positive.")
    if args.final_insert_adapter_progress_window_steps <= 0:
        raise ValueError("--final-insert-adapter-progress-window-steps must be positive.")
    if args.final_insert_macro_recovery_min_stall_steps < 0:
        raise ValueError("--final-insert-macro-recovery-min-stall-steps cannot be negative.")
    if args.final_insert_macro_recovery_min_active_steps < 0:
        raise ValueError("--final-insert-macro-recovery-min-active-steps cannot be negative.")
    if args.final_insert_macro_recovery_min_z < 0.0:
        raise ValueError("--final-insert-macro-recovery-min-z cannot be negative.")
    if args.final_insert_macro_recovery_max_z <= args.final_insert_macro_recovery_min_z:
        raise ValueError("--final-insert-macro-recovery-max-z must exceed min Z.")
    if args.final_insert_macro_recovery_max_xy <= 0.0:
        raise ValueError("--final-insert-macro-recovery-max-xy must be positive.")
    if args.final_insert_macro_recovery_lift_steps <= 0:
        raise ValueError("--final-insert-macro-recovery-lift-steps must be positive.")
    if args.final_insert_macro_recovery_align_steps <= 0:
        raise ValueError("--final-insert-macro-recovery-align-steps must be positive.")
    if args.final_insert_macro_recovery_hold_steps <= 0:
        raise ValueError("--final-insert-macro-recovery-hold-steps must be positive.")
    if args.final_insert_macro_recovery_lift_action <= 0.0:
        raise ValueError("--final-insert-macro-recovery-lift-action must be positive.")
    if args.final_insert_macro_recovery_max_xy_action < 0.0:
        raise ValueError("--final-insert-macro-recovery-max-xy-action cannot be negative.")
    if args.final_insert_macro_recovery_max_attempts < 0:
        raise ValueError("--final-insert-macro-recovery-max-attempts cannot be negative.")
    if args.final_insert_macro_recovery_abort_xy <= 0.0:
        raise ValueError("--final-insert-macro-recovery-abort-xy must be positive.")
    if args.final_insert_macro_recovery_abort_lift_steps <= 0:
        raise ValueError("--final-insert-macro-recovery-abort-lift-steps must be positive.")
    if args.final_insert_macro_recovery_abort_lift_action <= 0.0:
        raise ValueError("--final-insert-macro-recovery-abort-lift-action must be positive.")
    if (
        args.success_shape_yaw_tolerance_deg is not None
        and args.success_shape_yaw_tolerance_deg < 0.0
    ):
        raise ValueError("--success-shape-yaw-tolerance-deg cannot be negative.")
    valid_success_yaw_profiles = {
        "square_square",
        "triangle_triangle",
        "hex_hex",
        "slot_slot",
        "rectangular_key",
    }
    invalid_success_yaw_profiles = sorted(
        set(args.success_shape_yaw_profiles) - valid_success_yaw_profiles
    )
    if invalid_success_yaw_profiles:
        raise ValueError(
            "--success-shape-yaw-profiles contains unsupported profile(s): "
            + ", ".join(invalid_success_yaw_profiles)
        )
    validate_ordered_pair("--initial-tip-z-above-range", args.initial_tip_z_above_range, min_value=0.0)
    validate_ordered_pair("--initial-tip-xy-offset-range", args.initial_tip_xy_offset_range, min_value=0.0)
    validate_ordered_pair("--geometry-hole-half-size-range", args.geometry_hole_half_size_range, min_value=0.0)
    validate_ordered_pair("--geometry-peg-radius-range", args.geometry_peg_radius_range, min_value=0.0)
    validate_ordered_pair(
        "--geometry-square-peg-half-size-range",
        args.geometry_square_peg_half_size_range,
        min_value=0.0,
    )
    validate_ordered_pair(
        "--geometry-hole-center-xy-jitter",
        args.geometry_hole_center_xy_jitter,
        min_value=0.0,
    )
    validate_ordered_pair("--hard-control-scale-range", args.hard_control_scale_range, min_value=0.0)
    validate_ordered_pair(
        "--hard-control-noise-std-range",
        args.hard_control_noise_std_range,
        min_value=0.0,
    )
    validate_ordered_pair("--hard-control-delay-range", args.hard_control_delay_range, min_value=0.0)
    validate_ordered_pair(
        "--hard-control-filter-alpha-range",
        args.hard_control_filter_alpha_range,
        min_value=0.0,
        max_value=1.0,
    )
    if (
        args.hard_control_filter_alpha_range is not None
        and args.hard_control_filter_alpha_range[0] <= 0.0
    ):
        raise ValueError("--hard-control-filter-alpha-range values must be > 0.")
    if args.geometry_fixture_height_jitter is not None and args.geometry_fixture_height_jitter < 0.0:
        raise ValueError("--geometry-fixture-height-jitter cannot be negative.")
    if args.geometry_table_height_jitter is not None and args.geometry_table_height_jitter < 0.0:
        raise ValueError("--geometry-table-height-jitter cannot be negative.")
    if not 0.0 <= args.geometry_mixed_square_probability <= 1.0:
        raise ValueError("--geometry-mixed-square-probability must be between 0 and 1.")
    if args.ik_orientation_weight < 0.0:
        raise ValueError("--ik-orientation-weight cannot be negative.")
    if (
        args.guard_near_ik_orientation_weight is not None
        and args.guard_near_ik_orientation_weight < 0.0
    ):
        raise ValueError("--guard-near-ik-orientation-weight cannot be negative.")
    if (
        args.guard_final_servo_ik_orientation_weight is not None
        and args.guard_final_servo_ik_orientation_weight < 0.0
    ):
        raise ValueError("--guard-final-servo-ik-orientation-weight cannot be negative.")
    if args.guard_square_pose_yaw_align_ik_orientation_weight < 0.0:
        raise ValueError(
            "--guard-square-pose-yaw-align-ik-orientation-weight cannot be negative."
        )
    if args.guard_visual_yaw_align_enabled:
        if args.guard_visual_yaw_align_model is None:
            raise ValueError(
                "--guard-visual-yaw-align-enabled requires --guard-visual-yaw-align-model."
            )
        if args.observation_mode != "image":
            raise ValueError("--guard-visual-yaw-align requires --observation-mode image.")
        if not args.include_near_hole_crop:
            raise ValueError("--guard-visual-yaw-align requires --include-near-hole-crop.")
        if args.guard_visual_yaw_align_max_xy <= 0.0:
            raise ValueError("--guard-visual-yaw-align-max-xy must be positive.")
        if args.guard_visual_yaw_align_min_z < 0.0:
            raise ValueError("--guard-visual-yaw-align-min-z cannot be negative.")
        if args.guard_visual_yaw_align_max_z <= args.guard_visual_yaw_align_min_z:
            raise ValueError("--guard-visual-yaw-align-max-z must be greater than min-z.")
        if args.guard_visual_yaw_align_max_wall_contact < 0:
            raise ValueError("--guard-visual-yaw-align-max-wall-contact cannot be negative.")
        if args.guard_visual_yaw_align_min_raw_norm < 0.0:
            raise ValueError("--guard-visual-yaw-align-min-raw-norm cannot be negative.")
        if args.guard_visual_yaw_align_min_cam_std < 0.0:
            raise ValueError("--guard-visual-yaw-align-min-cam-std cannot be negative.")
        if args.guard_visual_yaw_align_min_crop_std < 0.0:
            raise ValueError("--guard-visual-yaw-align-min-crop-std cannot be negative.")
        if args.guard_visual_yaw_align_deadband_deg < 0.0:
            raise ValueError("--guard-visual-yaw-align-deadband-deg cannot be negative.")
        if args.guard_visual_yaw_align_max_correction_deg <= 0.0:
            raise ValueError("--guard-visual-yaw-align-max-correction-deg must be positive.")
        if args.guard_visual_yaw_align_temporal_action_gate_window <= 0:
            raise ValueError(
                "--guard-visual-yaw-align-temporal-action-gate-window must be positive."
            )
        if args.guard_visual_yaw_align_temporal_action_gate_max_delta_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-temporal-action-gate-max-delta-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_temporal_action_gate_min_pred_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-temporal-action-gate-min-pred-yaw-deg cannot be negative."
            )
        if (
            args.guard_visual_yaw_align_temporal_action_gate_max_pred_yaw_deg
            <= args.guard_visual_yaw_align_temporal_action_gate_min_pred_yaw_deg
        ):
            raise ValueError(
                "--guard-visual-yaw-align-temporal-action-gate-max-pred-yaw-deg must exceed min-pred-yaw-deg."
            )
        if args.guard_visual_yaw_align_block_descent_deg < 0.0:
            raise ValueError("--guard-visual-yaw-align-block-descent-deg cannot be negative.")
        if args.guard_visual_yaw_align_hold_z_min < 0.0:
            raise ValueError("--guard-visual-yaw-align-hold-z-min cannot be negative.")
        if args.guard_visual_yaw_align_hold_up_action < 0.0:
            raise ValueError("--guard-visual-yaw-align-hold-up-action cannot be negative.")
        if args.guard_visual_yaw_align_hold_xy_tolerance < 0.0:
            raise ValueError("--guard-visual-yaw-align-hold-xy-tolerance cannot be negative.")
        if args.guard_visual_yaw_align_hold_max_xy_action < 0.0:
            raise ValueError("--guard-visual-yaw-align-hold-max-xy-action cannot be negative.")
        if args.guard_visual_yaw_align_hold_target_steps < 0:
            raise ValueError("--guard-visual-yaw-align-hold-target-steps cannot be negative.")
        if args.guard_visual_yaw_align_hold_target_arm_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-hold-target-arm-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_hold_target_release_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-hold-target-release-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_hold_target_release_xy <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-hold-target-release-xy must be positive."
            )
        if args.guard_visual_yaw_align_hold_target_min_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-hold-target-min-z cannot be negative."
            )
        if (
            args.guard_visual_yaw_align_hold_target_max_z
            <= args.guard_visual_yaw_align_hold_target_min_z
        ):
            raise ValueError(
                "--guard-visual-yaw-align-hold-target-max-z must exceed hold-target-min-z."
            )
        if args.guard_visual_yaw_align_low_visibility_brake_min_pred_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-visibility-brake-min-pred-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_low_visibility_brake_min_xy < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-visibility-brake-min-xy cannot be negative."
            )
        if args.guard_visual_yaw_align_low_visibility_brake_max_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-visibility-brake-max-z cannot be negative."
            )
        if args.guard_visual_yaw_align_low_visibility_brake_up_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-visibility-brake-up-action cannot be negative."
            )
        if args.guard_visual_yaw_align_large_xy_low_z_brake_min_xy < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-large-xy-low-z-brake-min-xy cannot be negative."
            )
        if args.guard_visual_yaw_align_large_xy_low_z_brake_max_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-large-xy-low-z-brake-max-z cannot be negative."
            )
        if args.guard_visual_yaw_align_large_xy_low_z_brake_up_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-large-xy-low-z-brake-up-action cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_max_attempts < 0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-max-attempts cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_min_step < 0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-trigger-min-step cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_min_xy < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-trigger-min-xy cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_max_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-trigger-max-z cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_prev_xy < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-trigger-prev-xy cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_trigger_xy_jump < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-trigger-xy-jump cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_target_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-lift-target-z cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_z_tolerance < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-lift-z-tolerance cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_lift_max_steps <= 0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-lift-max-steps must be positive."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_recenter_release_xy <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-recenter-release-xy must be positive."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_recenter_max_steps <= 0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-recenter-max-steps must be positive."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_max_up_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-max-up-action cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_lateral_pop_recovery_max_xy_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-lateral-pop-recovery-max-xy-action cannot be negative."
            )
        if args.guard_visual_yaw_align_descent_abort_max_attempts < 0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-max-attempts cannot be negative."
            )
        if args.guard_visual_yaw_align_descent_abort_min_step < 0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-min-step cannot be negative."
            )
        if args.guard_visual_yaw_align_descent_abort_large_pred_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-large-pred-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_descent_abort_min_xy < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-min-xy cannot be negative."
            )
        if args.guard_visual_yaw_align_descent_abort_max_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-max-z cannot be negative."
            )
        if args.guard_visual_yaw_align_descent_abort_lift_target_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-lift-target-z cannot be negative."
            )
        if args.guard_visual_yaw_align_descent_abort_lift_z_tolerance < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-lift-z-tolerance cannot be negative."
            )
        if args.guard_visual_yaw_align_descent_abort_lift_max_steps <= 0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-lift-max-steps must be positive."
            )
        if args.guard_visual_yaw_align_descent_abort_recenter_max_steps <= 0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-recenter-max-steps must be positive."
            )
        if args.guard_visual_yaw_align_descent_abort_recenter_release_xy <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-recenter-release-xy must be positive."
            )
        if args.guard_visual_yaw_align_descent_abort_max_up_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-max-up-action cannot be negative."
            )
        if args.guard_visual_yaw_align_descent_abort_max_xy_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-descent-abort-max-xy-action cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_max_attempts < 0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-max-attempts cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_min_step < 0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-min-step cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_trigger_min_xy < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-trigger-min-xy cannot be negative."
            )
        if (
            args.guard_visual_yaw_align_reacquire_trigger_max_xy
            <= args.guard_visual_yaw_align_reacquire_trigger_min_xy
        ):
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-trigger-max-xy must exceed trigger-min-xy."
            )
        if args.guard_visual_yaw_align_reacquire_trigger_min_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-trigger-min-z cannot be negative."
            )
        if (
            args.guard_visual_yaw_align_reacquire_trigger_max_z
            <= args.guard_visual_yaw_align_reacquire_trigger_min_z
        ):
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-trigger-max-z must exceed trigger-min-z."
            )
        if args.guard_visual_yaw_align_reacquire_trigger_min_pred_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-trigger-min-pred-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_trigger_stable_window <= 0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-trigger-stable-window must be positive."
            )
        if args.guard_visual_yaw_align_reacquire_trigger_max_delta_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-trigger-max-delta-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_xy_gate_min_xy < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-xy-gate-min-xy cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_lift_target_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-lift-target-z cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_lift_z_tolerance < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-lift-z-tolerance cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_lift_max_steps <= 0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-lift-max-steps must be positive."
            )
        if args.guard_visual_yaw_align_reacquire_recenter_max_steps <= 0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-recenter-max-steps must be positive."
            )
        if args.guard_visual_yaw_align_reacquire_recenter_release_xy <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-recenter-release-xy must be positive."
            )
        if args.guard_visual_yaw_align_reacquire_max_up_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-max-up-action cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_max_xy_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-max-xy-action cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_relaxed_yaw_min_pred_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-relaxed-yaw-min-pred-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_relaxed_yaw_max_correction_deg <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-relaxed-yaw-max-correction-deg must be positive."
            )
        if args.guard_visual_yaw_align_reacquire_relaxed_yaw_min_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-relaxed-yaw-min-z cannot be negative."
            )
        if (
            args.guard_visual_yaw_align_reacquire_relaxed_yaw_max_z
            <= args.guard_visual_yaw_align_reacquire_relaxed_yaw_min_z
        ):
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-relaxed-yaw-max-z must exceed relaxed-yaw-min-z."
            )
        if args.guard_visual_yaw_align_reacquire_relaxed_yaw_stable_window <= 0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-relaxed-yaw-stable-window must be positive."
            )
        if args.guard_visual_yaw_align_reacquire_relaxed_yaw_max_delta_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-relaxed-yaw-max-delta-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_descent_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-descent-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_reacquire_descent_xy <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-descent-xy must be positive."
            )
        if args.guard_visual_yaw_align_reacquire_descent_min_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-descent-min-z cannot be negative."
            )
        if (
            args.guard_visual_yaw_align_reacquire_descent_max_z
            <= args.guard_visual_yaw_align_reacquire_descent_min_z
        ):
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-descent-max-z must exceed descent-min-z."
            )
        if args.guard_visual_yaw_align_reacquire_descent_max_down_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-reacquire-descent-max-down-action cannot be negative."
            )
        if args.guard_visual_yaw_align_wrong_basin_hold_min_pred_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-wrong-basin-hold-min-pred-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_wrong_basin_hold_stable_window <= 0:
            raise ValueError(
                "--guard-visual-yaw-align-wrong-basin-hold-stable-window must be positive."
            )
        if args.guard_visual_yaw_align_wrong_basin_hold_max_delta_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-wrong-basin-hold-max-delta-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_wrong_basin_hold_steps < 0:
            raise ValueError(
                "--guard-visual-yaw-align-wrong-basin-hold-steps cannot be negative."
            )
        if args.guard_visual_yaw_align_wrong_basin_hold_release_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-wrong-basin-hold-release-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_wrong_basin_hold_release_xy <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-wrong-basin-hold-release-xy must be positive."
            )
        if args.guard_visual_yaw_align_wrong_basin_hold_max_xy <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-wrong-basin-hold-max-xy must be positive."
            )
        if args.guard_visual_yaw_align_wrong_basin_hold_min_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-wrong-basin-hold-min-z cannot be negative."
            )
        if (
            args.guard_visual_yaw_align_wrong_basin_hold_max_z
            <= args.guard_visual_yaw_align_wrong_basin_hold_min_z
        ):
            raise ValueError(
                "--guard-visual-yaw-align-wrong-basin-hold-max-z must exceed wrong-basin-hold-min-z."
            )
        if args.guard_visual_yaw_align_wrong_basin_hold_max_xy_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-wrong-basin-hold-max-xy-action cannot be negative."
            )
        if args.guard_visual_yaw_align_recenter_release_xy < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-recenter-release-xy cannot be negative."
            )
        if args.guard_visual_yaw_align_latch_steps < 0:
            raise ValueError("--guard-visual-yaw-align-latch-steps cannot be negative.")
        if args.guard_visual_yaw_align_latch_max_xy <= 0.0:
            raise ValueError("--guard-visual-yaw-align-latch-max-xy must be positive.")
        if args.guard_visual_yaw_align_latch_min_z < 0.0:
            raise ValueError("--guard-visual-yaw-align-latch-min-z cannot be negative.")
        if args.guard_visual_yaw_align_latch_max_z <= args.guard_visual_yaw_align_latch_min_z:
            raise ValueError(
                "--guard-visual-yaw-align-latch-max-z must exceed latch-min-z."
            )
        if args.guard_visual_yaw_align_aligned_descent_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_aligned_descent_xy <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-xy must be positive."
            )
        if args.guard_visual_yaw_align_aligned_descent_min_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-min-z cannot be negative."
            )
        if (
            args.guard_visual_yaw_align_aligned_descent_max_z
            <= args.guard_visual_yaw_align_aligned_descent_min_z
        ):
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-max-z must exceed aligned-descent-min-z."
            )
        if args.guard_visual_yaw_align_aligned_descent_required_steps < 1:
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-required-steps must be >= 1."
            )
        if args.guard_visual_yaw_align_aligned_descent_latch_steps < 0:
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-latch-steps cannot be negative."
            )
        if args.guard_visual_yaw_align_aligned_descent_latch_release_xy <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-latch-release-xy must be positive."
            )
        if args.guard_visual_yaw_align_aligned_descent_latch_release_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-latch-release-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_aligned_descent_latch_min_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-latch-min-z cannot be negative."
            )
        if (
            args.guard_visual_yaw_align_aligned_descent_latch_max_z
            <= args.guard_visual_yaw_align_aligned_descent_latch_min_z
        ):
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-latch-max-z must exceed latch-min-z."
            )
        if args.guard_visual_yaw_align_aligned_descent_max_down_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-max-down-action cannot be negative."
            )
        if args.guard_visual_yaw_align_aligned_descent_max_xy_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-aligned-descent-max-xy-action cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_late_finish_descent_min_step < 0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-late-finish-descent-min-step cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_late_finish_descent_max_xy <= 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-late-finish-descent-max-xy must be positive."
            )
        if args.guard_visual_yaw_align_low_z_late_finish_descent_min_z < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-late-finish-descent-min-z cannot be negative."
            )
        if (
            args.guard_visual_yaw_align_low_z_late_finish_descent_max_z
            <= args.guard_visual_yaw_align_low_z_late_finish_descent_min_z
        ):
            raise ValueError(
                "--guard-visual-yaw-align-low-z-late-finish-descent-max-z must exceed min-z."
            )
        if args.guard_visual_yaw_align_low_z_late_finish_descent_max_yaw_deg < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-late-finish-descent-max-yaw-deg cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_late_finish_descent_max_xy_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-late-finish-descent-max-xy-action cannot be negative."
            )
        if args.guard_visual_yaw_align_low_z_late_finish_descent_max_down_action < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-low-z-late-finish-descent-max-down-action cannot be negative."
            )
        if args.guard_visual_yaw_align_ik_orientation_weight < 0.0:
            raise ValueError(
                "--guard-visual-yaw-align-ik-orientation-weight cannot be negative."
            )
    if (
        args.guard_contact_unjam_ik_orientation_weight is not None
        and args.guard_contact_unjam_ik_orientation_weight < 0.0
    ):
        raise ValueError("--guard-contact-unjam-ik-orientation-weight cannot be negative.")
    if (
        args.guard_contact_reinsert_orient_ik_orientation_weight is not None
        and args.guard_contact_reinsert_orient_ik_orientation_weight < 0.0
    ):
        raise ValueError(
            "--guard-contact-reinsert-orient-ik-orientation-weight cannot be negative."
        )
    if (
        args.guard_contact_reinsert_high_ik_orientation_weight is not None
        and args.guard_contact_reinsert_high_ik_orientation_weight < 0.0
    ):
        raise ValueError(
            "--guard-contact-reinsert-high-ik-orientation-weight cannot be negative."
        )
    if args.guard_start_xy <= 0.0 or args.guard_start_z <= 0.0:
        raise ValueError("--guard-start-xy and --guard-start-z must be positive.")
    if args.guard_risk_xy < 0.0 or args.guard_risk_xy > args.guard_start_xy:
        raise ValueError("--guard-risk-xy must be between 0 and --guard-start-xy.")
    if args.guard_near_actuator_kp_multiplier <= 0.0:
        raise ValueError("--guard-near-actuator-kp-multiplier must be positive.")
    if args.guard_retry_stall_steps <= 0:
        raise ValueError("--guard-retry-stall-steps must be positive.")
    if args.guard_retry_max_steps <= 0:
        raise ValueError("--guard-retry-max-steps must be positive.")
    if args.guard_insert_latch_release_xy < args.guard_insert_latch_xy_tolerance:
        raise ValueError("--guard-insert-latch-release-xy must be >= --guard-insert-latch-xy-tolerance.")
    if args.guard_insert_latch_resume_xy > args.guard_insert_latch_release_xy:
        raise ValueError("--guard-insert-latch-resume-xy must be <= --guard-insert-latch-release-xy.")
    if args.guard_insert_latch_recenter_height < 0.0:
        raise ValueError("--guard-insert-latch-recenter-height cannot be negative.")
    if args.guard_insert_latch_max_down_action < 0.0:
        raise ValueError("--guard-insert-latch-max-down-action cannot be negative.")
    if args.guard_hover_release_xy < args.guard_hover_xy_tolerance:
        raise ValueError("--guard-hover-release-xy must be >= --guard-hover-xy-tolerance.")
    if args.guard_hover_required_steps <= 0:
        raise ValueError("--guard-hover-required-steps must be positive.")
    if args.guard_hover_height <= 0.0 or args.guard_hover_z_tolerance <= 0.0:
        raise ValueError("--guard-hover-height and --guard-hover-z-tolerance must be positive.")
    if args.guard_hover_max_down_action < 0.0:
        raise ValueError("--guard-hover-max-down-action cannot be negative.")
    if args.guard_near_action_xy_tolerance <= 0.0 or args.guard_near_action_z_threshold <= 0.0:
        raise ValueError("--guard-near-action-xy-tolerance and --guard-near-action-z-threshold must be positive.")
    if args.guard_near_max_xy_action <= 0.0:
        raise ValueError("--guard-near-max-xy-action must be positive.")
    if args.guard_near_max_down_action < 0.0:
        raise ValueError("--guard-near-max-down-action cannot be negative.")
    if args.guard_fixture_clearance_xy_min < 0.0:
        raise ValueError("--guard-fixture-clearance-xy-min cannot be negative.")
    if args.guard_fixture_clearance_xy_max <= args.guard_fixture_clearance_xy_min:
        raise ValueError("--guard-fixture-clearance-xy-max must be greater than --guard-fixture-clearance-xy-min.")
    if args.guard_fixture_clearance_z_max <= 0.0:
        raise ValueError("--guard-fixture-clearance-z-max must be positive.")
    if args.guard_fixture_clearance_lift_height <= args.guard_fixture_clearance_z_max:
        raise ValueError("--guard-fixture-clearance-lift-height must be greater than --guard-fixture-clearance-z-max.")
    if args.guard_fixture_clearance_max_up_action <= 0.0:
        raise ValueError("--guard-fixture-clearance-max-up-action must be positive.")
    if args.guard_fixture_clearance_realign_start_z < 0.0:
        raise ValueError("--guard-fixture-clearance-realign-start-z cannot be negative.")
    if args.guard_fixture_clearance_realign_xy <= 0.0:
        raise ValueError("--guard-fixture-clearance-realign-xy must be positive.")
    if args.guard_fixture_clearance_max_xy_action <= 0.0:
        raise ValueError("--guard-fixture-clearance-max-xy-action must be positive.")
    if args.guard_fixture_clearance_max_down_action < 0.0:
        raise ValueError("--guard-fixture-clearance-max-down-action cannot be negative.")
    if args.guard_fixture_clearance_max_steps <= 0:
        raise ValueError("--guard-fixture-clearance-max-steps must be positive.")
    if args.guard_fixture_clearance_retreat_release_xy <= args.guard_fixture_clearance_xy_min:
        raise ValueError("--guard-fixture-clearance-retreat-release-xy must be greater than --guard-fixture-clearance-xy-min.")
    if args.guard_fixture_clearance_retreat_max_xy_action <= 0.0:
        raise ValueError("--guard-fixture-clearance-retreat-max-xy-action must be positive.")
    if args.guard_preinsert_recenter_start_z <= 0.0:
        raise ValueError("--guard-preinsert-recenter-start-z must be positive.")
    if args.guard_preinsert_recenter_min_z < 0.0:
        raise ValueError("--guard-preinsert-recenter-min-z cannot be negative.")
    if args.guard_preinsert_recenter_min_z > args.guard_preinsert_recenter_start_z:
        raise ValueError("--guard-preinsert-recenter-min-z must be <= start-z.")
    if args.guard_preinsert_recenter_trigger_xy <= 0.0:
        raise ValueError("--guard-preinsert-recenter-trigger-xy must be positive.")
    if args.guard_preinsert_recenter_stable_xy <= 0.0:
        raise ValueError("--guard-preinsert-recenter-stable-xy must be positive.")
    if args.guard_preinsert_recenter_stable_xy > args.guard_preinsert_recenter_trigger_xy:
        raise ValueError("--guard-preinsert-recenter-stable-xy must be <= trigger-xy.")
    if args.guard_preinsert_recenter_height <= 0.0:
        raise ValueError("--guard-preinsert-recenter-height must be positive.")
    if args.guard_preinsert_recenter_z_tolerance <= 0.0:
        raise ValueError("--guard-preinsert-recenter-z-tolerance must be positive.")
    if args.guard_preinsert_recenter_stable_steps <= 0:
        raise ValueError("--guard-preinsert-recenter-stable-steps must be positive.")
    if args.guard_preinsert_recenter_max_steps <= 0:
        raise ValueError("--guard-preinsert-recenter-max-steps must be positive.")
    if args.guard_preinsert_recenter_max_xy_action <= 0.0:
        raise ValueError("--guard-preinsert-recenter-max-xy-action must be positive.")
    if args.guard_preinsert_recenter_max_up_action <= 0.0:
        raise ValueError("--guard-preinsert-recenter-max-up-action must be positive.")
    if args.guard_approach_recenter_start_z <= 0.0:
        raise ValueError("--guard-approach-recenter-start-z must be positive.")
    if args.guard_approach_recenter_min_z < 0.0:
        raise ValueError("--guard-approach-recenter-min-z cannot be negative.")
    if args.guard_approach_recenter_min_z > args.guard_approach_recenter_start_z:
        raise ValueError("--guard-approach-recenter-min-z must be <= start-z.")
    if args.guard_approach_recenter_trigger_xy <= 0.0:
        raise ValueError("--guard-approach-recenter-trigger-xy must be positive.")
    if args.guard_approach_recenter_max_xy <= args.guard_approach_recenter_trigger_xy:
        raise ValueError("--guard-approach-recenter-max-xy must be greater than trigger-xy.")
    if args.guard_approach_recenter_stable_xy <= 0.0:
        raise ValueError("--guard-approach-recenter-stable-xy must be positive.")
    if args.guard_approach_recenter_stable_xy > args.guard_approach_recenter_trigger_xy:
        raise ValueError("--guard-approach-recenter-stable-xy must be <= trigger-xy.")
    if args.guard_approach_recenter_height <= 0.0:
        raise ValueError("--guard-approach-recenter-height must be positive.")
    if args.guard_approach_recenter_z_tolerance <= 0.0:
        raise ValueError("--guard-approach-recenter-z-tolerance must be positive.")
    if args.guard_approach_recenter_stable_steps <= 0:
        raise ValueError("--guard-approach-recenter-stable-steps must be positive.")
    if args.guard_approach_recenter_max_steps <= 0:
        raise ValueError("--guard-approach-recenter-max-steps must be positive.")
    if args.guard_approach_recenter_max_xy_action <= 0.0:
        raise ValueError("--guard-approach-recenter-max-xy-action must be positive.")
    if args.guard_approach_recenter_max_up_action <= 0.0:
        raise ValueError("--guard-approach-recenter-max-up-action must be positive.")
    if len(args.guard_approach_recenter_xy_bias) != 2:
        raise ValueError("--guard-approach-recenter-xy-bias must contain two values.")
    if args.guard_early_approach_assist_trigger_xy <= 0.0:
        raise ValueError("--guard-early-approach-assist-trigger-xy must be positive.")
    if args.guard_early_approach_assist_release_xy <= 0.0:
        raise ValueError("--guard-early-approach-assist-release-xy must be positive.")
    if (
        args.guard_early_approach_assist_release_xy
        >= args.guard_early_approach_assist_trigger_xy
    ):
        raise ValueError(
            "--guard-early-approach-assist-release-xy must be less than trigger-xy."
        )
    if args.guard_early_approach_assist_min_z < 0.0:
        raise ValueError("--guard-early-approach-assist-min-z cannot be negative.")
    if args.guard_early_approach_assist_max_z <= args.guard_early_approach_assist_min_z:
        raise ValueError(
            "--guard-early-approach-assist-max-z must be greater than min-z."
        )
    if args.guard_early_approach_assist_target_height <= 0.0:
        raise ValueError("--guard-early-approach-assist-target-height must be positive.")
    if args.guard_early_approach_assist_max_xy_action <= 0.0:
        raise ValueError("--guard-early-approach-assist-max-xy-action must be positive.")
    if args.guard_early_approach_assist_max_up_action <= 0.0:
        raise ValueError("--guard-early-approach-assist-max-up-action must be positive.")
    if args.guard_early_approach_assist_max_steps <= 0:
        raise ValueError("--guard-early-approach-assist-max-steps must be positive.")
    if args.guard_stateful_recovery_trigger_xy_min < 0.0:
        raise ValueError("--guard-stateful-recovery-trigger-xy-min cannot be negative.")
    if args.guard_stateful_recovery_trigger_xy_max <= args.guard_stateful_recovery_trigger_xy_min:
        raise ValueError("--guard-stateful-recovery-trigger-xy-max must be greater than trigger-xy-min.")
    if args.guard_stateful_recovery_trigger_z_max <= 0.0:
        raise ValueError("--guard-stateful-recovery-trigger-z-max must be positive.")
    if args.guard_stateful_recovery_lift_height <= 0.0:
        raise ValueError("--guard-stateful-recovery-lift-height must be positive.")
    if args.guard_stateful_recovery_lift_z_tolerance <= 0.0:
        raise ValueError("--guard-stateful-recovery-lift-z-tolerance must be positive.")
    if args.guard_stateful_recovery_release_xy <= 0.0:
        raise ValueError("--guard-stateful-recovery-release-xy must be positive.")
    if args.guard_stateful_recovery_resume_xy < args.guard_stateful_recovery_release_xy:
        raise ValueError("--guard-stateful-recovery-resume-xy must be >= release-xy.")
    if args.guard_stateful_recovery_resume_z <= 0.0:
        raise ValueError("--guard-stateful-recovery-resume-z must be positive.")
    if args.guard_stateful_recovery_stable_steps <= 0:
        raise ValueError("--guard-stateful-recovery-stable-steps must be positive.")
    if args.guard_stateful_recovery_stall_steps <= 0:
        raise ValueError("--guard-stateful-recovery-stall-steps must be positive.")
    if args.guard_stateful_recovery_min_xy_progress < 0.0:
        raise ValueError("--guard-stateful-recovery-min-xy-progress cannot be negative.")
    if args.guard_stateful_recovery_min_actual_xy_motion < 0.0:
        raise ValueError("--guard-stateful-recovery-min-actual-xy-motion cannot be negative.")
    if args.guard_stateful_recovery_min_command_xy < 0.0:
        raise ValueError("--guard-stateful-recovery-min-command-xy cannot be negative.")
    if args.guard_stateful_recovery_max_attempts < 0:
        raise ValueError("--guard-stateful-recovery-max-attempts cannot be negative.")
    if args.guard_stateful_recovery_max_steps <= 0:
        raise ValueError("--guard-stateful-recovery-max-steps must be positive.")
    if args.guard_stateful_recovery_max_xy_action <= 0.0:
        raise ValueError("--guard-stateful-recovery-max-xy-action must be positive.")
    if args.guard_stateful_recovery_max_down_action < 0.0:
        raise ValueError("--guard-stateful-recovery-max-down-action cannot be negative.")
    if args.guard_stateful_recovery_max_up_action <= 0.0:
        raise ValueError("--guard-stateful-recovery-max-up-action must be positive.")
    if args.guard_final_servo_start_xy <= 0.0 or args.guard_final_servo_start_z <= 0.0:
        raise ValueError("--guard-final-servo-start-xy/z must be positive.")
    if args.guard_final_servo_min_start_z < 0.0:
        raise ValueError("--guard-final-servo-min-start-z cannot be negative.")
    if args.guard_final_servo_min_start_z > args.guard_final_servo_start_z:
        raise ValueError("--guard-final-servo-min-start-z must be <= start-z.")
    if args.guard_final_servo_hover_height <= 0.0 or args.guard_final_servo_hover_z_tolerance <= 0.0:
        raise ValueError("--guard-final-servo-hover-height/z-tolerance must be positive.")
    if args.guard_final_servo_stable_xy <= 0.0:
        raise ValueError("--guard-final-servo-stable-xy must be positive.")
    if args.guard_final_servo_descent_start_xy < 0.0:
        raise ValueError("--guard-final-servo-descent-start-xy cannot be negative.")
    if (
        args.guard_final_servo_descent_start_xy > 0.0
        and args.guard_final_servo_descent_start_xy < args.guard_final_servo_stable_xy
    ):
        raise ValueError(
            "--guard-final-servo-descent-start-xy must be >= --guard-final-servo-stable-xy."
        )
    if args.guard_final_servo_stable_steps <= 0:
        raise ValueError("--guard-final-servo-stable-steps must be positive.")
    if args.guard_final_servo_release_xy < args.guard_final_servo_stable_xy:
        raise ValueError("--guard-final-servo-release-xy must be >= stable-xy.")
    if args.guard_final_servo_align_timeout_steps < 0:
        raise ValueError("--guard-final-servo-align-timeout-steps cannot be negative.")
    if args.guard_final_servo_align_timeout_xy < 0.0:
        raise ValueError("--guard-final-servo-align-timeout-xy cannot be negative.")
    if args.guard_final_servo_align_hover_escape_steps <= 0:
        raise ValueError("--guard-final-servo-align-hover-escape-steps must be positive.")
    if args.guard_final_servo_align_hover_escape_xy <= 0.0:
        raise ValueError("--guard-final-servo-align-hover-escape-xy must be positive.")
    if args.guard_final_servo_align_hover_escape_min_z < 0.0:
        raise ValueError("--guard-final-servo-align-hover-escape-min-z cannot be negative.")
    if (
        args.guard_final_servo_align_hover_escape_max_z
        <= args.guard_final_servo_align_hover_escape_min_z
    ):
        raise ValueError(
            "--guard-final-servo-align-hover-escape-max-z must exceed min Z."
        )
    if args.guard_final_servo_rearm_cooldown_steps < 0:
        raise ValueError("--guard-final-servo-rearm-cooldown-steps cannot be negative.")
    if args.guard_final_servo_rearm_stable_steps <= 0:
        raise ValueError("--guard-final-servo-rearm-stable-steps must be positive.")
    if args.guard_final_servo_rearm_xy_max <= 0.0:
        raise ValueError("--guard-final-servo-rearm-xy-max must be positive.")
    if args.guard_final_servo_rearm_z_min < 0.0:
        raise ValueError("--guard-final-servo-rearm-z-min cannot be negative.")
    if args.guard_final_servo_rearm_z_max <= args.guard_final_servo_rearm_z_min:
        raise ValueError("--guard-final-servo-rearm-z-max must exceed z-min.")
    if args.guard_final_servo_rearm_contact_max < 0:
        raise ValueError("--guard-final-servo-rearm-contact-max cannot be negative.")
    if args.guard_final_servo_rearm_tilt_max_deg <= 0.0:
        raise ValueError("--guard-final-servo-rearm-tilt-max-deg must be positive.")
    if args.guard_final_servo_rearm_margin_min > 0.0:
        raise ValueError("--guard-final-servo-rearm-margin-min must be <= 0.")
    if args.guard_final_servo_rearm_max_attempts < 0:
        raise ValueError("--guard-final-servo-rearm-max-attempts cannot be negative.")
    if args.guard_final_servo_max_xy_action <= 0.0:
        raise ValueError("--guard-final-servo-max-xy-action must be positive.")
    if args.guard_final_servo_max_down_action < 0.0:
        raise ValueError("--guard-final-servo-max-down-action cannot be negative.")
    if args.guard_final_servo_low_recenter_stall_steps < 0:
        raise ValueError("--guard-final-servo-low-recenter-stall-steps cannot be negative.")
    if args.guard_final_servo_low_recenter_min_xy_progress < 0.0:
        raise ValueError("--guard-final-servo-low-recenter-min-xy-progress cannot be negative.")
    if len(args.guard_final_servo_descend_xy_bias) != 2:
        raise ValueError("--guard-final-servo-descend-xy-bias requires two values.")
    if args.guard_final_servo_descend_xy_bias_max_clearance < 0.0:
        raise ValueError("--guard-final-servo-descend-xy-bias-max-clearance cannot be negative.")
    if args.guard_final_servo_lift_height <= args.guard_final_servo_hover_height:
        raise ValueError("--guard-final-servo-lift-height must be greater than hover-height.")
    if args.guard_final_servo_stall_steps <= 0:
        raise ValueError("--guard-final-servo-stall-steps must be positive.")
    if args.guard_final_servo_min_z_progress <= 0.0:
        raise ValueError("--guard-final-servo-min-z-progress must be positive.")
    if args.guard_final_servo_max_retries < 0:
        raise ValueError("--guard-final-servo-max-retries cannot be negative.")
    if args.guard_final_servo_max_recovery_steps <= 0:
        raise ValueError("--guard-final-servo-max-recovery-steps must be positive.")
    if args.guard_final_servo_soft_unjam_lift <= 0.0:
        raise ValueError("--guard-final-servo-soft-unjam-lift must be positive.")
    if args.guard_final_servo_soft_unjam_min_height < 0.0:
        raise ValueError("--guard-final-servo-soft-unjam-min-height cannot be negative.")
    if args.guard_final_servo_soft_unjam_z_tolerance <= 0.0:
        raise ValueError("--guard-final-servo-soft-unjam-z-tolerance must be positive.")
    if args.guard_final_servo_soft_unjam_hold_steps < 0:
        raise ValueError("--guard-final-servo-soft-unjam-hold-steps cannot be negative.")
    if args.guard_final_servo_soft_unjam_max_up_action <= 0.0:
        raise ValueError("--guard-final-servo-soft-unjam-max-up-action must be positive.")
    if args.guard_final_servo_square_recovery_tilt_deg <= 0.0:
        raise ValueError("--guard-final-servo-square-recovery-tilt-deg must be positive.")
    if args.guard_final_servo_square_recovery_tilt_steps <= 0:
        raise ValueError("--guard-final-servo-square-recovery-tilt-steps must be positive.")
    if args.guard_final_servo_square_recovery_z_max <= 0.0:
        raise ValueError("--guard-final-servo-square-recovery-z-max must be positive.")
    if args.guard_final_servo_square_recovery_xy_max <= 0.0:
        raise ValueError("--guard-final-servo-square-recovery-xy-max must be positive.")
    if args.guard_final_servo_square_recovery_lift_height <= args.guard_final_servo_hover_height:
        raise ValueError(
            "--guard-final-servo-square-recovery-lift-height must be greater than "
            "--guard-final-servo-hover-height."
        )
    if args.guard_final_servo_square_recovery_escape_xy <= 0.0:
        raise ValueError("--guard-final-servo-square-recovery-escape-xy must be positive.")
    if args.guard_final_servo_square_recovery_escape_z_min < 0.0:
        raise ValueError("--guard-final-servo-square-recovery-escape-z-min cannot be negative.")
    if args.guard_final_servo_square_recovery_escape_z_max <= 0.0:
        raise ValueError("--guard-final-servo-square-recovery-escape-z-max must be positive.")
    if (
        args.guard_final_servo_square_recovery_escape_z_min
        > args.guard_final_servo_square_recovery_escape_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-z-min must be <= z-max."
        )
    if (
        args.guard_final_servo_square_recovery_escape_height
        <= args.guard_final_servo_hover_height
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-height must be greater than "
            "--guard-final-servo-hover-height."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_height
        <= args.guard_final_servo_hover_height
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-height must be "
            "greater than --guard-final-servo-hover-height."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_height
        > args.guard_final_servo_square_recovery_escape_height
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-height must be <= "
            "--guard-final-servo-square-recovery-escape-height."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_height_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-height-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_release_xy <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-release-xy must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_release_xy
        > args.guard_final_servo_square_recovery_escape_xy
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-release-xy must be <= "
            "--guard-final-servo-square-recovery-escape-xy."
        )
    if args.guard_final_servo_square_recovery_escape_late_release_xy < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-release-xy cannot be "
            "negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_release_xy
        > args.guard_final_servo_square_recovery_escape_xy
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-release-xy must be <= "
            "--guard-final-servo-square-recovery-escape-xy."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_release_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-release-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_max_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-max-steps must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_max_xy_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-max-xy-action must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_max_up_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-max-up-action must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_max_clearance < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-max-clearance cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_early_contact_wall_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-early-contact-wall-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_early_contact_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-early-contact-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_early_contact_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-early-contact-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_early_contact_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-early-contact-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_early_contact_z_min
        > args.guard_final_servo_square_recovery_escape_early_contact_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-early-contact-z-min "
            "must be <= early-contact-z-max."
        )
    if args.guard_final_servo_square_recovery_escape_early_risk_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-early-risk-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_early_risk_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-early-risk-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_early_risk_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-early-risk-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_early_risk_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-early-risk-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_early_risk_z_min
        > args.guard_final_servo_square_recovery_escape_early_risk_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-early-risk-z-min "
            "must be <= early-risk-z-max."
        )
    if args.guard_final_servo_square_recovery_escape_pre_lift_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-pre-lift-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_direct_fast_settle_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_direct_fast_settle_xy_max
        > args.guard_final_servo_square_recovery_escape_xy
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-xy-max "
            "must be <= --guard-final-servo-square-recovery-escape-xy."
        )
    if args.guard_final_servo_square_recovery_escape_direct_fast_settle_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-z-max "
            "must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_direct_fast_settle_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_direct_fast_settle_z_min
        > args.guard_final_servo_square_recovery_escape_direct_fast_settle_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-z-min "
            "must be <= direct-fast-settle-z-max."
        )
    if args.guard_final_servo_square_recovery_escape_direct_fast_settle_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-max-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_direct_fast_settle_min_steps_since_reset < 0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_steps_since_reset < 0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-max-steps-since-reset "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_steps_since_reset
        > 0
        and args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_steps_since_reset
        < args.guard_final_servo_square_recovery_escape_direct_fast_settle_min_steps_since_reset
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-max-steps-since-reset "
            "must be >= min-steps-since-reset when enabled."
        )
    if (
        args.guard_final_servo_square_recovery_escape_direct_fast_settle_from_escape_min_phase_steps
        <= 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-from-escape-min-phase-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_down_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-max-down-action "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_down_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-max-down-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_direct_fast_settle_max_xy_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-direct-fast-settle-max-xy-action "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_recenter_descend_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-descend-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_recenter_descend_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-descend-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_recenter_descend_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-descend-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_recenter_descend_z_min
        > args.guard_final_servo_square_recovery_escape_recenter_descend_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-descend-z-min "
            "must be <= recenter-descend-z-max."
        )
    if args.guard_final_servo_square_recovery_escape_recenter_descend_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-descend-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_recenter_descend_max_down_action
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-descend-max-down-action "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_recenter_drift_lift_min_phase_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-drift-lift-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_recenter_drift_lift_xy_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-drift-lift-xy-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_recenter_drift_lift_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-drift-lift-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_recenter_drift_lift_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-drift-lift-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_recenter_drift_lift_z_min
        > args.guard_final_servo_square_recovery_escape_recenter_drift_lift_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-drift-lift-z-min "
            "must be <= drift-lift-z-max."
        )
    if args.guard_final_servo_square_recovery_escape_recenter_drift_lift_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-drift-lift-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_recenter_drift_lift_yaw_min_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-drift-lift-yaw-min-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_recenter_drift_lift_tilt_min_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-recenter-drift-lift-tilt-min-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_recenter_descend_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-min-steps-since-reset "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_recenter_descend_min_phase_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_late_recenter_descend_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_recovery_escape_late_recenter_descend_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_recovery_escape_late_recenter_descend_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_recenter_descend_z_min
        > args.guard_final_servo_square_recovery_escape_late_recenter_descend_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-z-min "
            "must be <= late-recenter-descend-z-max."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_recenter_descend_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_recenter_descend_margin_min
        > args.guard_final_servo_square_recovery_escape_late_recenter_descend_margin_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-margin-min "
            "must be <= margin-max."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_recenter_descend_tilt_max_deg
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-tilt-max-deg "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_recenter_descend_max_down_action
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-max-down-action "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_recenter_descend_max_xy_action
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-max-xy-action "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_recenter_descend_hold_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-recenter-descend-hold-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-min-steps-since-reset "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_phase_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-min-phase-steps "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_min_brake_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-min-brake-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_z_min
        > args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-z-min "
            "must be <= z-max."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_topdown_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-topdown-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_yaw_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_late_clean_direct_finish_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-late-clean-direct-finish-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_xy_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-xy-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_xy_min
        > args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-xy-min "
            "must be <= xy-max."
        )
    if (
        args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_z_min
        > args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-z-min "
            "must be <= z-max."
        )
    if (
        args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_max_contact_pop_hold_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-max-contact-pop-hold-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_yaw_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_recovery_escape_no_contact_xy_pop_recenter_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-recovery-escape-no-contact-xy-pop-recenter-tilt-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_contact_unjam_wall_steps <= 0:
        raise ValueError("--guard-final-servo-contact-unjam-wall-steps must be positive.")
    if args.guard_final_servo_contact_unjam_tilt_deg <= 0.0:
        raise ValueError("--guard-final-servo-contact-unjam-tilt-deg must be positive.")
    if args.guard_final_servo_contact_unjam_z_max <= 0.0:
        raise ValueError("--guard-final-servo-contact-unjam-z-max must be positive.")
    if args.guard_final_servo_contact_unjam_xy_max <= 0.0:
        raise ValueError("--guard-final-servo-contact-unjam-xy-max must be positive.")
    if args.guard_final_servo_contact_unjam_lift_height <= args.guard_final_servo_hover_height:
        raise ValueError(
            "--guard-final-servo-contact-unjam-lift-height must be greater than "
            "--guard-final-servo-hover-height."
        )
    if args.guard_final_servo_contact_unjam_release_xy <= 0.0:
        raise ValueError("--guard-final-servo-contact-unjam-release-xy must be positive.")
    if args.guard_final_servo_contact_unjam_release_xy > args.guard_final_servo_release_xy:
        raise ValueError("--guard-final-servo-contact-unjam-release-xy must be <= release-xy.")
    if args.guard_final_servo_contact_unjam_max_up_action <= 0.0:
        raise ValueError("--guard-final-servo-contact-unjam-max-up-action must be positive.")
    if args.guard_final_servo_contact_unjam_wall_bias < 0.0:
        raise ValueError("--guard-final-servo-contact-unjam-wall-bias cannot be negative.")
    if args.guard_final_servo_contact_unjam_wall_bias > args.guard_final_servo_contact_unjam_release_xy:
        raise ValueError(
            "--guard-final-servo-contact-unjam-wall-bias must be <= "
            "--guard-final-servo-contact-unjam-release-xy."
        )
    if args.guard_final_servo_contact_reinsert_orient_tilt_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-orient-tilt-deg must be positive."
        )
    if args.guard_final_servo_contact_reinsert_orient_stable_steps <= 0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-orient-stable-steps must be positive."
        )
    if args.guard_final_servo_contact_reinsert_orient_max_steps <= 0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-orient-max-steps must be positive."
        )
    if args.guard_final_servo_contact_reinsert_orient_max_xy_action < 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-orient-max-xy-action cannot be negative."
        )
    if args.guard_final_servo_contact_reinsert_orient_tip_lock_drift_gain < 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-orient-tip-lock-drift-gain cannot be negative."
        )
    if args.guard_final_servo_contact_reinsert_orient_tip_lock_max_offset <= 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-orient-tip-lock-max-offset must be positive."
        )
    if (
        args.guard_final_servo_contact_reinsert_high_reapproach_height
        <= args.guard_final_servo_hover_height
    ):
        raise ValueError(
            "--guard-final-servo-contact-reinsert-high-reapproach-height must be "
            "greater than --guard-final-servo-hover-height."
        )
    if args.guard_final_servo_contact_reinsert_high_reapproach_release_xy <= 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-high-reapproach-release-xy must be positive."
        )
    if (
        args.guard_final_servo_contact_reinsert_high_reapproach_release_xy
        > args.guard_final_servo_release_xy
    ):
        raise ValueError(
            "--guard-final-servo-contact-reinsert-high-reapproach-release-xy must be <= "
            "--guard-final-servo-release-xy."
        )
    if args.guard_final_servo_contact_reinsert_high_reapproach_stable_steps <= 0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-high-reapproach-stable-steps must be positive."
        )
    if args.guard_final_servo_contact_reinsert_high_reapproach_max_steps <= 0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-high-reapproach-max-steps must be positive."
        )
    if args.guard_final_servo_contact_reinsert_high_reapproach_max_xy_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-high-reapproach-max-xy-action must be positive."
        )
    if args.guard_final_servo_contact_reinsert_high_reapproach_max_up_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-high-reapproach-max-up-action must be positive."
        )
    if args.guard_final_servo_contact_reinsert_descend_max_steps <= 0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-descend-max-steps must be positive."
        )
    if args.guard_final_servo_contact_reinsert_micro_align_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-micro-align-z-max must be positive."
        )
    if args.guard_final_servo_contact_reinsert_micro_align_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-micro-align-xy-max must be positive."
        )
    if args.guard_final_servo_contact_reinsert_micro_align_release_xy <= 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-micro-align-release-xy must be positive."
        )
    if (
        args.guard_final_servo_contact_reinsert_micro_align_release_xy
        > args.guard_final_servo_contact_reinsert_micro_align_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-contact-reinsert-micro-align-release-xy must be <= "
            "--guard-final-servo-contact-reinsert-micro-align-xy-max."
        )
    if args.guard_final_servo_contact_reinsert_micro_align_tilt_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-micro-align-tilt-deg must be positive."
        )
    if args.guard_final_servo_contact_reinsert_micro_align_max_steps <= 0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-micro-align-max-steps must be positive."
        )
    if args.guard_final_servo_contact_reinsert_micro_align_stall_steps <= 0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-micro-align-stall-steps must be positive."
        )
    if args.guard_final_servo_contact_reinsert_micro_align_min_xy_progress < 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-micro-align-min-xy-progress cannot be negative."
        )
    if args.guard_final_servo_contact_reinsert_micro_align_max_xy_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-micro-align-max-xy-action must be positive."
        )
    if args.guard_final_servo_contact_reinsert_micro_align_up_action < 0.0:
        raise ValueError(
            "--guard-final-servo-contact-reinsert-micro-align-up-action cannot be negative."
        )
    if args.guard_final_servo_near_miss_steps <= 0:
        raise ValueError("--guard-final-servo-near-miss-steps must be positive.")
    if args.guard_final_servo_near_miss_xy_max <= 0.0:
        raise ValueError("--guard-final-servo-near-miss-xy-max must be positive.")
    if args.guard_final_servo_near_miss_z_max <= 0.0:
        raise ValueError("--guard-final-servo-near-miss-z-max must be positive.")
    if args.guard_final_servo_near_miss_contact_max < 0:
        raise ValueError("--guard-final-servo-near-miss-contact-max cannot be negative.")
    if args.guard_final_servo_near_miss_tilt_max_deg <= 0.0:
        raise ValueError("--guard-final-servo-near-miss-tilt-max-deg must be positive.")
    if args.guard_final_servo_near_miss_max_steps <= 0:
        raise ValueError("--guard-final-servo-near-miss-max-steps must be positive.")
    if args.guard_final_servo_near_miss_max_down_action < 0.0:
        raise ValueError("--guard-final-servo-near-miss-max-down-action cannot be negative.")
    if len(args.guard_final_servo_near_miss_xy_bias) != 2:
        raise ValueError("--guard-final-servo-near-miss-xy-bias requires two values.")
    if args.guard_final_servo_square_fast_settle_xy_max <= 0.0:
        raise ValueError("--guard-final-servo-square-fast-settle-xy-max must be positive.")
    if args.guard_final_servo_square_fast_settle_z_max <= 0.0:
        raise ValueError("--guard-final-servo-square-fast-settle-z-max must be positive.")
    if args.guard_final_servo_square_fast_settle_release_xy <= 0.0:
        raise ValueError("--guard-final-servo-square-fast-settle-release-xy must be positive.")
    if (
        args.guard_final_servo_square_fast_settle_release_xy
        > args.guard_final_servo_square_fast_settle_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-release-xy must be <= "
            "--guard-final-servo-square-fast-settle-xy-max."
        )
    if args.guard_final_servo_square_fast_settle_tilt_max_deg <= 0.0:
        raise ValueError("--guard-final-servo-square-fast-settle-tilt-max-deg must be positive.")
    if args.guard_final_servo_square_fast_settle_contact_max < 0:
        raise ValueError("--guard-final-servo-square-fast-settle-contact-max cannot be negative.")
    if args.guard_final_servo_square_fast_settle_max_steps <= 0:
        raise ValueError("--guard-final-servo-square-fast-settle-max-steps must be positive.")
    if args.guard_final_servo_square_fast_settle_max_xy_action <= 0.0:
        raise ValueError("--guard-final-servo-square-fast-settle-max-xy-action must be positive.")
    if args.guard_final_servo_square_fast_settle_low_z_max_xy_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-max-xy-action cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_threshold < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-threshold cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_max_xy_action > 0.0
        and args.guard_final_servo_square_fast_settle_low_z_threshold <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-threshold must be positive "
            "when low-z XY limiting is enabled."
        )
    if args.guard_final_servo_square_fast_settle_low_z_max_down_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-max-down-action cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_down_threshold < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-down-threshold cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_max_down_action > 0.0
        and args.guard_final_servo_square_fast_settle_low_z_down_threshold <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-down-threshold must be "
            "positive when low-z down limiting is enabled."
        )
    if args.guard_final_servo_square_fast_settle_max_down_action < 0.0:
        raise ValueError("--guard-final-servo-square-fast-settle-max-down-action cannot be negative.")
    if args.guard_final_servo_square_fast_settle_late_down_boost_max_down_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-max-down-action "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_late_down_boost_max_xy_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-max-xy-action "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_late_down_boost_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-xy-max must be positive."
        )
    if args.guard_final_servo_square_fast_settle_late_down_boost_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-z-min cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_late_down_boost_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-z-max must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_late_down_boost_z_min
        > args.guard_final_servo_square_fast_settle_late_down_boost_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-z-min must be <= z-max."
        )
    if args.guard_final_servo_square_fast_settle_late_down_boost_min_brake_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-min-brake-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_late_down_boost_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_late_down_boost_min_phase_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_late_down_boost_margin_min < -1.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-margin-min "
            "must be >= -1.0."
        )
    if args.guard_final_servo_square_fast_settle_late_down_boost_min_clean_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-down-boost-min-clean-steps "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-min-steps-since-reset "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_brake_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-min-brake-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_phase_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-min-phase-steps "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_min_clean_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-min-clean-steps "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_z_min
        > args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-z-min "
            "must be <= very-late-clean-tail-boost-z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_topdown_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-topdown-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_yaw_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_max_down_action
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-max-down-action "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_very_late_clean_tail_boost_max_xy_action
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-very-late-clean-tail-boost-max-xy-action "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-contact-down-guard-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_wall_count <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-contact-down-guard-wall-count "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-contact-down-guard-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-contact-down-guard-z-max "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_min_brake_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-contact-down-guard-min-brake-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_contact_down_guard_max_up_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-contact-down-guard-max-up-action "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_wall_count <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-wall-count "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_xy_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-xy-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_hold_xy_min
        > args.guard_final_servo_square_fast_settle_contact_pop_hold_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-xy-min "
            "must be <= xy-max."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_hold_z_min
        > args.guard_final_servo_square_fast_settle_contact_pop_hold_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_min_phase_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_min_brake_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-min-brake-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_max_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-max-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_max_up_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-max-up-action "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_min_phase_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_xy_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-xy-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_xy_min
        > args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-xy-min "
            "must be <= xy-max."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_z_min
        > args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_yaw_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-yaw-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_contact_pop_hold_recenter_tilt_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-hold-recenter-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_min_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-min-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_xy_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-xy-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_xy_min
        > args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-xy-min "
            "must be <= xy-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_z_min
        > args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-z-min "
            "must be <= z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_yaw_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_pop_exhausted_recenter_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-pop-exhausted-recenter-tilt-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_xy_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-xy-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_no_contact_pop_hold_xy_min
        > args.guard_final_servo_square_fast_settle_no_contact_pop_hold_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-xy-min "
            "must be <= xy-max."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_no_contact_pop_hold_z_min
        > args.guard_final_servo_square_fast_settle_no_contact_pop_hold_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_no_contact_pop_hold_min_brake_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-min-brake-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_no_contact_pop_hold_max_contact_pop_hold_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-max-contact-pop-hold-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_no_contact_pop_hold_min_contact_pop_hold_phase_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-min-contact-pop-hold-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_max_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-max-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_margin_min < -1.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_fast_settle_no_contact_pop_hold_topdown_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-topdown-margin-min "
            "must be >= -1.0."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_yaw_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-yaw-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_tilt_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-tilt-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_no_contact_pop_hold_max_up_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-no-contact-pop-hold-max-up-action "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_pre_pop_guard_z_min
        > args.guard_final_servo_square_fast_settle_pre_pop_guard_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_min_phase_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_max_phase_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-max-phase-steps "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_pre_pop_guard_max_phase_steps
        > 0
        and args.guard_final_servo_square_fast_settle_pre_pop_guard_max_phase_steps
        < args.guard_final_servo_square_fast_settle_pre_pop_guard_min_phase_steps
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-max-phase-steps "
            "must be >= min-phase-steps when enabled."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_min_brake_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-min-brake-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_pre_pop_guard_min_soft_hold_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-min-soft-hold-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_max_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-max-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_margin_min < -1.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_fast_settle_pre_pop_guard_margin_max
        < args.guard_final_servo_square_fast_settle_pre_pop_guard_margin_min
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-margin-max "
            "must be >= margin-min."
        )
    if (
        args.guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-topdown-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_max
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-topdown-margin-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_max
        > 0.0
        and args.guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_min
        > args.guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-topdown-margin-max "
            "must be >= topdown-margin-min when enabled."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_yaw_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-yaw-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_tilt_min_deg < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-tilt-min-deg "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_tilt_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_pre_pop_guard_tilt_max_deg
        < args.guard_final_servo_square_fast_settle_pre_pop_guard_tilt_min_deg
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-tilt-max-deg "
            "must be >= tilt-min-deg."
        )
    if args.guard_final_servo_square_fast_settle_pre_pop_guard_max_up_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-guard-max-up-action "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_pre_pop_limit_max_xy_action
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-limit-max-xy-action "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_pre_pop_limit_max_down_action
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-pre-pop-limit-max-down-action "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_xy_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-xy-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_xy_min
        > args.guard_final_servo_square_fast_settle_severe_pop_reapproach_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-xy-min "
            "must be <= xy-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_z_min
        > args.guard_final_servo_square_fast_settle_severe_pop_reapproach_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-z-min "
            "must be <= z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_min_brake_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-min-brake-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-min-steps-since-reset "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_max_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-max-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_height
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-height "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_topdown_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-topdown-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_yaw_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_severe_pop_reapproach_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-severe-pop-reapproach-tilt-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_clearance_hold_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-steps must be positive."
        )
    if args.guard_final_servo_square_fast_settle_clearance_hold_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-xy-max must be positive."
        )
    if args.guard_final_servo_square_fast_settle_clearance_hold_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-z-min cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_clearance_hold_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-z-max must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_clearance_hold_z_min
        > args.guard_final_servo_square_fast_settle_clearance_hold_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-z-min must be <= z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_clearance_hold_margin_min
        > args.guard_final_servo_square_fast_settle_clearance_hold_margin_threshold
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-margin-min "
            "must be <= margin-threshold."
        )
    if args.guard_final_servo_square_fast_settle_clearance_hold_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_clearance_hold_wall_count < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-wall-count "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_clearance_hold_min_brake_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-min-brake-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_clearance_hold_min_phase_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_clearance_hold_max_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-max-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_clearance_hold_max_up_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-clearance-hold-max-up-action "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_wall_count <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-wall-count must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-xy-max must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-z-min cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-z-max must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_relief_z_min
        > args.guard_final_servo_square_fast_settle_low_z_relief_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-z-min must be <= z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_relief_margin_min
        > args.guard_final_servo_square_fast_settle_low_z_relief_margin_threshold
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-margin-min "
            "must be <= margin-threshold."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-contact-max cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_min_brake_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-min-brake-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_min_phase_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_max_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-max-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_lift_height <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-lift-height must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_target_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-target-z-max must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_relief_target_z_max
        < args.guard_final_servo_square_fast_settle_low_z_relief_z_min
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-target-z-max "
            "must be >= z-min."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_lift_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-lift-steps must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_recenter_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-recenter-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_release_xy <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-release-xy must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_relief_release_xy
        > args.guard_final_servo_square_fast_settle_low_z_relief_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-release-xy "
            "must be <= xy-max."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_max_up_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-max-up-action "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_relief_max_xy_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-max-xy-action "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_start_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-start-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_max_steps
        <= 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-max-steps "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_contact_pop_min_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-contact-pop-min-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_relief_wide_recenter_contact_pop_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-relief-wide-recenter-contact-pop-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_stall_relief_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_low_z_stall_relief_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_low_z_stall_relief_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_stall_relief_z_min
        > args.guard_final_servo_square_fast_settle_low_z_stall_relief_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-z-min "
            "must be <= z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_stall_relief_margin_min
        > args.guard_final_servo_square_fast_settle_low_z_stall_relief_margin_threshold
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-margin-min "
            "must be <= margin-threshold."
        )
    if args.guard_final_servo_square_fast_settle_low_z_stall_relief_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_stall_relief_min_brake_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-min-brake-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_stall_relief_min_phase_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-min-phase-steps "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_stall_relief_min_stall_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-min-stall-steps "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_stall_relief_max_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-max-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_steps
        <= 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-hold-steps "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_max_up_action
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-hold-max-up-action "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_low_z_stall_relief_hold_min_contact_pop_hold_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-low-z-stall-relief-hold-min-contact-pop-hold-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_z_min
        > args.guard_final_servo_square_fast_settle_contact_soft_hold_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_yaw_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_margin_max
        < args.guard_final_servo_square_fast_settle_contact_soft_hold_margin_min
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-margin-max "
            "must be >= --guard-final-servo-square-fast-settle-contact-soft-hold-margin-min."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_tilt_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-tilt-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_wall_count <= 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-wall-count "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_min_phase_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_min_steps_since_reset < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_min_phase_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-subsequent-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_min_steps_since_reset < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-subsequent-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_z_max < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-subsequent-z-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_subsequent_margin_min < -1.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-subsequent-margin-min "
            "must be >= -1.0."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_max_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-max-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_contact_soft_hold_max_up_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-max-up-action "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-extend-until-clear-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_max_steps
        <= 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-extend-until-clear-max-steps "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_max_steps
        < args.guard_final_servo_square_fast_settle_contact_soft_hold_steps
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-extend-until-clear-max-steps "
            "must be >= --guard-final-servo-square-fast-settle-contact-soft-hold-steps."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_extend_until_clear_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-extend-until-clear-min-steps-since-reset "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_steps
        <= 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-steps "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_z_min
        > args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-z-min "
            "must be <= release-continue-z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_yaw_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_max_xy_action
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-max-xy-action "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_continue_max_down_action
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-continue-max-down-action "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_wall_count
        <= 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-wall-count "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_xy_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-xy-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_xy_min
        > args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-xy-min "
            "must be <= release-contact-brake-xy-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_z_min
        > args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-z-min "
            "must be <= release-contact-brake-z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_yaw_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_max_phase_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-max-phase-steps "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_min_soft_hold_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-contact-brake-min-soft-hold-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_steps
        <= 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-steps "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_wall_count
        <= 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-wall-count "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_xy_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-xy-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_xy_min
        > args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-xy-min "
            "must be <= xy-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_z_min
        > args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-z-min "
            "must be <= z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_yaw_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_phase_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-max-phase-steps "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_min_soft_hold_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-min-soft-hold-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-max-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_release_pop_hold_max_up_action
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-release-pop-hold-max-up-action "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_xy_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-xy-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_xy_min
        > args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-xy-min "
            "must be <= xy-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_z_min
        > args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-z-min "
            "must be <= z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_yaw_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_contact_soft_hold_large_pop_recenter_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-contact-soft-hold-large-pop-recenter-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_late_finish_continue_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-finish-continue-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_late_finish_continue_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-finish-continue-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_late_finish_continue_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-finish-continue-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_late_finish_continue_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-finish-continue-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_late_finish_continue_z_min
        > args.guard_final_servo_square_fast_settle_late_finish_continue_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-finish-continue-z-min "
            "must be <= z-max."
        )
    if (
        args.guard_final_servo_square_fast_settle_late_finish_continue_topdown_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-finish-continue-topdown-margin-min "
            "must be >= -1.0."
        )
    if (
        args.guard_final_servo_square_fast_settle_late_finish_continue_yaw_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-finish-continue-yaw-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_late_finish_continue_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-finish-continue-tilt-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_late_finish_continue_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-finish-continue-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_fast_settle_late_escape_veto_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-escape-veto-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_late_escape_veto_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-escape-veto-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_late_escape_veto_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-escape-veto-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_late_escape_veto_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-escape-veto-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_fast_settle_late_escape_veto_z_min
        > args.guard_final_servo_square_fast_settle_late_escape_veto_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-escape-veto-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_fast_settle_late_escape_veto_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-escape-veto-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_fast_settle_late_escape_veto_yaw_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-escape-veto-yaw-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_fast_settle_late_escape_veto_tilt_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-fast-settle-late-escape-veto-tilt-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_wall_steps <= 0:
        raise ValueError("--guard-final-servo-square-contact-brake-wall-steps must be positive.")
    if args.guard_final_servo_square_contact_brake_xy_max <= 0.0:
        raise ValueError("--guard-final-servo-square-contact-brake-xy-max must be positive.")
    if args.guard_final_servo_square_contact_brake_z_min < 0.0:
        raise ValueError("--guard-final-servo-square-contact-brake-z-min cannot be negative.")
    if args.guard_final_servo_square_contact_brake_z_max <= 0.0:
        raise ValueError("--guard-final-servo-square-contact-brake-z-max must be positive.")
    if (
        args.guard_final_servo_square_contact_brake_z_min
        > args.guard_final_servo_square_contact_brake_z_max
    ):
        raise ValueError("--guard-final-servo-square-contact-brake-z-min must be <= z-max.")
    if args.guard_final_servo_square_contact_brake_lift_height <= 0.0:
        raise ValueError("--guard-final-servo-square-contact-brake-lift-height must be positive.")
    if args.guard_final_servo_square_contact_brake_lift_z_max <= 0.0:
        raise ValueError("--guard-final-servo-square-contact-brake-lift-z-max must be positive.")
    if (
        args.guard_final_servo_square_contact_brake_lift_z_max
        < args.guard_final_servo_square_contact_brake_z_max
    ):
        raise ValueError("--guard-final-servo-square-contact-brake-lift-z-max must be >= z-max.")
    if args.guard_final_servo_square_contact_brake_release_xy <= 0.0:
        raise ValueError("--guard-final-servo-square-contact-brake-release-xy must be positive.")
    if (
        args.guard_final_servo_square_contact_brake_release_xy
        > args.guard_final_servo_square_contact_brake_xy_max
    ):
        raise ValueError("--guard-final-servo-square-contact-brake-release-xy must be <= xy-max.")
    if args.guard_final_servo_square_contact_brake_stable_steps <= 0:
        raise ValueError("--guard-final-servo-square-contact-brake-stable-steps must be positive.")
    if args.guard_final_servo_square_contact_brake_max_steps <= 0:
        raise ValueError("--guard-final-servo-square-contact-brake-max-steps must be positive.")
    if args.guard_final_servo_square_contact_brake_max_attempts < 0:
        raise ValueError("--guard-final-servo-square-contact-brake-max-attempts cannot be negative.")
    if args.guard_final_servo_square_contact_brake_max_xy_action <= 0.0:
        raise ValueError("--guard-final-servo-square-contact-brake-max-xy-action must be positive.")
    if args.guard_final_servo_square_contact_brake_max_up_action <= 0.0:
        raise ValueError("--guard-final-servo-square-contact-brake-max-up-action must be positive.")
    if args.guard_final_servo_square_contact_brake_max_clearance < 0.0:
        raise ValueError("--guard-final-servo-square-contact-brake-max-clearance cannot be negative.")
    if args.guard_final_servo_square_contact_brake_release_flush_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-release-flush-steps "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_release_flush_min_brake_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-release-flush-min-brake-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_contact_brake_release_flush_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-release-flush-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_release_flush_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-release-flush-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_release_flush_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-release-flush-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_release_flush_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-release-flush-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_release_flush_z_min
        > args.guard_final_servo_square_contact_brake_release_flush_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-release-flush-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_contact_brake_release_flush_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-release-flush-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_contact_brake_exhausted_continue_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-exhausted-continue-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_exhausted_continue_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-exhausted-continue-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_exhausted_continue_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-exhausted-continue-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_exhausted_continue_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-exhausted-continue-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_exhausted_continue_z_min
        > args.guard_final_servo_square_contact_brake_exhausted_continue_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-exhausted-continue-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_contact_brake_exhausted_continue_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-exhausted-continue-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_exhausted_continue_tilt_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-exhausted-continue-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_exhausted_continue_topdown_margin_min
        < -1.0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-exhausted-continue-topdown-margin-min "
            "must be >= -1.0."
        )
    if args.guard_final_servo_square_contact_brake_exhausted_continue_yaw_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-exhausted-continue-yaw-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_wall_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-wall-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-steps "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_min_brake_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-min-brake-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_z_min
        > args.guard_final_servo_square_contact_brake_preemptive_hold_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_max_up_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-max-up-action "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_max_clearance < 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-max-clearance "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_yaw_min_deg < 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-yaw-min-deg "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-expanded-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_xy_max
        < args.guard_final_servo_square_contact_brake_preemptive_hold_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-expanded-xy-max "
            "must be >= --guard-final-servo-square-contact-brake-preemptive-hold-xy-max."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-expanded-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_expanded_yaw_max_deg
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-expanded-yaw-max-deg "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_max_brake_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-max-brake-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_contact_max
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-contact-max "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_xy_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_z_min
        < 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-z-min "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_z_max
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_z_min
        > args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-z-min "
            "must be <= z-max."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_clean_release_tilt_max_deg
        <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-clean-release-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_min_phase_steps
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_xy_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-xy-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-xy-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_xy_min
        > args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_xy_max
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-xy-min "
            "must be <= xy-max."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_z_min
        > args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_yaw_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-yaw-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_preemptive_hold_pop_recenter_tilt_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-preemptive-hold-pop-recenter-tilt-max-deg "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_late_lift_release_min_brake_attempts
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-late-lift-release-min-brake-attempts "
            "cannot be negative."
        )
    if (
        args.guard_final_servo_square_contact_brake_late_lift_release_min_phase_steps
        <= 0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-late-lift-release-min-phase-steps "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_late_lift_release_min_steps_since_reset
        < 0
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-late-lift-release-min-steps-since-reset "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_late_lift_release_contact_max < 0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-late-lift-release-contact-max "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_late_lift_release_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-late-lift-release-xy-max "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_late_lift_release_z_min < 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-late-lift-release-z-min "
            "cannot be negative."
        )
    if args.guard_final_servo_square_contact_brake_late_lift_release_z_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-late-lift-release-z-max "
            "must be positive."
        )
    if (
        args.guard_final_servo_square_contact_brake_late_lift_release_z_min
        > args.guard_final_servo_square_contact_brake_late_lift_release_z_max
    ):
        raise ValueError(
            "--guard-final-servo-square-contact-brake-late-lift-release-z-min "
            "must be <= z-max."
        )
    if args.guard_final_servo_square_contact_brake_late_lift_release_yaw_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-late-lift-release-yaw-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_contact_brake_late_lift_release_tilt_max_deg <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-contact-brake-late-lift-release-tilt-max-deg "
            "must be positive."
        )
    if args.guard_final_servo_square_high_z_descend_stall_steps < 0:
        raise ValueError("--guard-final-servo-square-high-z-descend-stall-steps cannot be negative.")
    if args.guard_final_servo_square_high_z_descend_xy_max <= 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-xy-max must be positive.")
    if args.guard_final_servo_square_high_z_descend_z_min < 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-z-min cannot be negative.")
    if args.guard_final_servo_square_high_z_descend_z_max <= 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-z-max must be positive.")
    if args.guard_final_servo_square_high_z_descend_z_min > args.guard_final_servo_square_high_z_descend_z_max:
        raise ValueError("--guard-final-servo-square-high-z-descend-z-min must be <= z-max.")
    if args.guard_final_servo_square_high_z_descend_contact_max < 0:
        raise ValueError("--guard-final-servo-square-high-z-descend-contact-max cannot be negative.")
    if args.guard_final_servo_square_high_z_descend_tilt_max_deg <= 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-tilt-max-deg must be positive.")
    if args.guard_final_servo_square_high_z_descend_margin_min > 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-margin-min must be <= 0.")
    if args.guard_final_servo_square_high_z_descend_max_steps <= 0:
        raise ValueError("--guard-final-servo-square-high-z-descend-max-steps must be positive.")
    if args.guard_final_servo_square_high_z_descend_max_xy_action < 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-max-xy-action cannot be negative.")
    if args.guard_final_servo_square_high_z_descend_max_down_action < 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-max-down-action cannot be negative.")
    if args.guard_final_servo_square_high_z_descend_low_z_threshold < 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-low-z-threshold cannot be negative.")
    if args.guard_final_servo_square_high_z_descend_low_z_max_xy_action < 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-low-z-max-xy-action cannot be negative.")
    if args.guard_final_servo_square_high_z_descend_mid_z_threshold < 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-mid-z-threshold cannot be negative.")
    if (
        args.guard_final_servo_square_high_z_descend_staged_enabled
        and args.guard_final_servo_square_high_z_descend_low_z_threshold <= 0.0
    ):
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-low-z-threshold must be "
            "positive when staged high-Z descend is enabled."
        )
    if (
        args.guard_final_servo_square_high_z_descend_staged_enabled
        and args.guard_final_servo_square_high_z_descend_mid_z_threshold
        < args.guard_final_servo_square_high_z_descend_low_z_threshold
    ):
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-mid-z-threshold must be "
            ">= low-z-threshold when staged high-Z descend is enabled."
        )
    if args.guard_final_servo_square_high_z_descend_mid_z_max_xy_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-mid-z-max-xy-action cannot be negative."
        )
    if args.guard_final_servo_square_high_z_descend_mid_z_max_down_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-mid-z-max-down-action cannot be negative."
        )
    if args.guard_final_servo_square_high_z_descend_low_z_max_down_action < 0.0:
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-low-z-max-down-action cannot be negative."
        )
    if args.guard_final_servo_square_high_z_descend_low_z_hold_steps <= 0:
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-low-z-hold-steps must be positive."
        )
    if args.guard_final_servo_square_high_z_descend_low_z_hold_min_phase_steps < 0:
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-low-z-hold-min-phase-steps "
            "cannot be negative."
        )
    if args.guard_final_servo_square_high_z_descend_low_z_hold_max_attempts < 0:
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-low-z-hold-max-attempts "
            "cannot be negative."
        )
    if args.guard_final_servo_square_high_z_descend_low_z_hold_xy_max <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-low-z-hold-xy-max must be positive."
        )
    if args.guard_final_servo_square_high_z_descend_low_z_hold_max_up_action <= 0.0:
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-low-z-hold-max-up-action "
            "must be positive."
        )
    if args.guard_final_servo_square_high_z_descend_contact_brake_wall_count < 0:
        raise ValueError(
            "--guard-final-servo-square-high-z-descend-contact-brake-wall-count "
            "cannot be negative."
        )
    if args.guard_final_servo_square_high_z_descend_contact_brake_z_max <= 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-contact-brake-z-max must be positive.")
    if args.guard_final_servo_square_high_z_descend_contact_brake_xy_max < 0.0:
        raise ValueError("--guard-final-servo-square-high-z-descend-contact-brake-xy-max cannot be negative.")
    if args.guard_final_servo_square_margin_yaw_settle_stall_steps < 0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-stall-steps cannot be negative.")
    if args.guard_final_servo_square_margin_yaw_settle_xy_max <= 0.0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-xy-max must be positive.")
    if args.guard_final_servo_square_margin_yaw_settle_z_min < 0.0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-z-min cannot be negative.")
    if args.guard_final_servo_square_margin_yaw_settle_z_max <= 0.0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-z-max must be positive.")
    if (
        args.guard_final_servo_square_margin_yaw_settle_z_min
        > args.guard_final_servo_square_margin_yaw_settle_z_max
    ):
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-z-min must be <= z-max.")
    if args.guard_final_servo_square_margin_yaw_settle_contact_max < 0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-contact-max cannot be negative.")
    if args.guard_final_servo_square_margin_yaw_settle_yaw_deg <= 0.0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-yaw-deg must be positive.")
    if args.guard_final_servo_square_margin_yaw_settle_release_xy <= 0.0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-release-xy must be positive.")
    if (
        args.guard_final_servo_square_margin_yaw_settle_release_xy
        > args.guard_final_servo_square_margin_yaw_settle_xy_max
    ):
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-release-xy must be <= xy-max.")
    if args.guard_final_servo_square_margin_yaw_settle_lift_height <= 0.0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-lift-height must be positive.")
    if args.guard_final_servo_square_margin_yaw_settle_stable_steps <= 0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-stable-steps must be positive.")
    if args.guard_final_servo_square_margin_yaw_settle_max_steps <= 0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-max-steps must be positive.")
    if args.guard_final_servo_square_margin_yaw_settle_max_attempts < 0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-max-attempts cannot be negative.")
    if args.guard_final_servo_square_margin_yaw_settle_max_xy_action <= 0.0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-max-xy-action must be positive.")
    if args.guard_final_servo_square_margin_yaw_settle_max_up_action <= 0.0:
        raise ValueError("--guard-final-servo-square-margin-yaw-settle-max-up-action must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_wall_steps <= 0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-wall-steps must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_stall_steps < 0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-stall-steps cannot be negative.")
    if args.guard_final_servo_square_tilt_reinsert_tilt_deg <= 0.0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-tilt-deg must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_margin_threshold > 0.0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-margin-threshold must be <= 0.")
    if args.guard_final_servo_square_tilt_reinsert_xy_max <= 0.0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-xy-max must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_z_min < 0.0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-z-min cannot be negative.")
    if args.guard_final_servo_square_tilt_reinsert_z_max <= 0.0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-z-max must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_z_min > args.guard_final_servo_square_tilt_reinsert_z_max:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-z-min must be <= z-max.")
    if args.guard_final_servo_square_tilt_reinsert_lift_height <= 0.0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-lift-height must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_release_xy <= 0.0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-release-xy must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_release_xy > args.guard_final_servo_square_tilt_reinsert_xy_max:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-release-xy must be <= xy-max.")
    if args.guard_final_servo_square_tilt_reinsert_release_tilt_deg <= 0.0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-release-tilt-deg must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_stable_steps <= 0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-stable-steps must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_max_steps <= 0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-max-steps must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_max_attempts < 0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-max-attempts cannot be negative.")
    if args.guard_final_servo_square_tilt_reinsert_max_xy_action <= 0.0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-max-xy-action must be positive.")
    if args.guard_final_servo_square_tilt_reinsert_max_up_action <= 0.0:
        raise ValueError("--guard-final-servo-square-tilt-reinsert-max-up-action must be positive.")
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

    hard_bucket_scenario = make_hard_bucket_scenario(args)
    scenarios = [hard_bucket_scenario] if args.hard_bucket_only else list(CORE_SCENARIOS)
    if args.include_hard_bucket and not args.hard_bucket_only:
        scenarios.append(hard_bucket_scenario)

    rows = []
    episode_rows = []
    step_rows = []
    for scenario in scenarios:
        row, scenario_episode_rows, scenario_step_rows = evaluate_scenario(args, scenario)
        rows.append(row)
        episode_rows.extend(scenario_episode_rows)
        step_rows.extend(scenario_step_rows)
        print(
            "{name}: success={success_rate:.3f} collision={collision_rate:.3f} "
            "timeout={timeout_rate:.3f} guard_steps={mean_guarded_steps:.1f} "
            "retry_steps={mean_retry_steps:.1f} latch_steps={mean_latch_steps:.1f} "
            "hover_steps={mean_hover_steps:.1f} hover_latched={mean_hover_latched_steps:.1f} "
            "near_limited={mean_near_limited_steps:.1f} fixture_steps={mean_fixture_clearance_steps:.1f} "
            "fixture_realign={mean_fixture_clearance_realign_steps:.1f} "
            "preinsert={mean_preinsert_recenter_steps:.1f} "
            "approach={mean_approach_recenter_steps:.1f} "
            "adapter={mean_approach_adapter_steps:.1f} "
            "early_approach={mean_early_approach_assist_steps:.1f} "
            "stateful_recovery={mean_stateful_recovery_steps:.1f} "
            "final_servo={mean_final_servo_steps:.1f} "
            "return={mean_return:.3f}".format(**row)
        )

    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, args, rows)
    if args.episode_output_csv is not None:
        write_csv(args.episode_output_csv, episode_rows)
    if args.step_output_csv is not None:
        write_csv(args.step_output_csv, step_rows, fieldnames=STEP_TRACE_FIELDNAMES)


if __name__ == "__main__":
    main()
