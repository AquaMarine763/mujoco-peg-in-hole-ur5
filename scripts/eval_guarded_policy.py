from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import A2C, PPO, SAC

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


HARD_BUCKET_SCENARIO = Scenario(
    "hard_full_light_bucket",
    "full_light_geometry",
    control_action_scale_range=(0.8, 1.1),
    control_action_noise_std_range=(0.0, 0.00025),
    control_action_delay_range=(2, 2),
    control_action_filter_alpha_range=(0.55, 0.70),
)


STEP_TRACE_FIELDNAMES = [
    "scenario",
    "level",
    "control_mode",
    "image_ablation",
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
    "guard_final_servo_active",
    "guard_final_servo_triggered",
    "guard_final_servo_recovery_triggered",
    "guard_final_servo_exhausted",
    "guard_final_servo_phase",
    "guard_final_servo_phase_steps",
    "guard_final_servo_stable_steps",
    "guard_final_servo_stall_steps",
    "guard_final_servo_retry_count",
    "guard_final_servo_descent_allowed",
    "guard_final_servo_down_blocked",
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
    "ik_target_error",
    "ik_orientation_error",
    "ik_iterations",
    "peg_tilt_angle_deg",
    "joint_limit_min_normalized_margin",
    "joint_damping_multiplier",
    "actuator_kp_multiplier",
    "control_action_scale_multiplier",
    "control_action_noise_std",
    "control_action_delay",
    "control_action_filter_alpha",
    "hole_half_size",
    "peg_radius",
    "hole_clearance",
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
        "--guard-scenario-filter",
        choices=["none", "all", "geometry", "hard"],
        default="all",
        help="Limit guarded insertion to none, all, geometry/contact scenarios, or only the hard bucket.",
    )
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
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
    parser.add_argument("--ik-control-mode", choices=["position", "pose"], default="position")
    parser.add_argument("--ik-orientation-weight", type=float, default=0.12)
    parser.add_argument("--ik-posture-weight", type=float, default=0.01)
    parser.add_argument("--ik-step-limit", type=float, default=0.06)
    parser.add_argument("--ik-max-iterations", type=int, default=24)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--geometry-hole-half-size-range", nargs=2, type=float, default=(0.017, 0.021))
    parser.add_argument("--nominal-joint-damping-multiplier", type=float, default=1.0)
    parser.add_argument("--nominal-actuator-kp-multiplier", type=float, default=1.0)
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
    parser.add_argument("--guard-final-servo-enabled", action="store_true")
    parser.add_argument("--guard-final-servo-start-xy", type=float, default=0.012)
    parser.add_argument("--guard-final-servo-start-z", type=float, default=0.070)
    parser.add_argument("--guard-final-servo-min-start-z", type=float, default=0.010)
    parser.add_argument("--guard-final-servo-hover-height", type=float, default=0.040)
    parser.add_argument("--guard-final-servo-hover-z-tolerance", type=float, default=0.010)
    parser.add_argument("--guard-final-servo-stable-xy", type=float, default=0.0045)
    parser.add_argument("--guard-final-servo-stable-steps", type=int, default=6)
    parser.add_argument("--guard-final-servo-release-xy", type=float, default=0.008)
    parser.add_argument("--guard-final-servo-max-xy-action", type=float, default=0.0025)
    parser.add_argument("--guard-final-servo-max-down-action", type=float, default=0.0015)
    parser.add_argument("--guard-final-servo-descend-xy-bias", nargs=2, type=float, default=(0.0, 0.0))
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


def make_env(args: argparse.Namespace, scenario: Scenario) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode=args.observation_mode,
        image_width=args.width,
        image_height=args.height,
        include_near_hole_crop=args.include_near_hole_crop,
        near_hole_crop_size=args.near_hole_crop_size,
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
        geometry_hole_center_xy_jitter=scenario.geometry_hole_center_xy_jitter,
        geometry_fixture_height_jitter=scenario.geometry_fixture_height_jitter,
        geometry_table_height_jitter=scenario.geometry_table_height_jitter,
        geometry_hole_half_size_range=tuple(args.geometry_hole_half_size_range),
        geometry_peg_radius_range=scenario.geometry_peg_radius_range,
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
        guard_final_servo_enabled=args.guard_final_servo_enabled,
        guard_final_servo_start_xy=args.guard_final_servo_start_xy,
        guard_final_servo_start_z=args.guard_final_servo_start_z,
        guard_final_servo_min_start_z=args.guard_final_servo_min_start_z,
        guard_final_servo_hover_height=args.guard_final_servo_hover_height,
        guard_final_servo_hover_z_tolerance=args.guard_final_servo_hover_z_tolerance,
        guard_final_servo_stable_xy=args.guard_final_servo_stable_xy,
        guard_final_servo_stable_steps=args.guard_final_servo_stable_steps,
        guard_final_servo_release_xy=args.guard_final_servo_release_xy,
        guard_final_servo_max_xy_action=args.guard_final_servo_max_xy_action,
        guard_final_servo_max_down_action=args.guard_final_servo_max_down_action,
        guard_final_servo_descend_xy_bias=tuple(args.guard_final_servo_descend_xy_bias),
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


def black_like(obs: Any) -> Any:
    if isinstance(obs, dict):
        return {key: black_like(value) for key, value in obs.items()}
    if isinstance(obs, np.ndarray):
        if obs.dtype == np.uint8:
            return np.zeros_like(obs)
        return obs.copy()
    return obs


def noise_like(obs: Any, rng: np.random.Generator) -> Any:
    if isinstance(obs, dict):
        return {key: noise_like(value, rng) for key, value in obs.items()}
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
    mode: str,
    rng: np.random.Generator,
    shuffle_bank: list[Any],
) -> Any:
    if mode == "normal":
        return obs
    if mode == "black":
        return black_like(obs)
    if mode == "noise":
        return noise_like(obs, rng)
    if mode == "shuffle":
        if shuffle_bank:
            index = int(rng.integers(0, len(shuffle_bank)))
            ablated = clone_observation(shuffle_bank[index])
        else:
            ablated = black_like(obs)
        shuffle_bank.append(clone_observation(obs))
        return preserve_non_image_values(ablated, obs)
    raise ValueError(f"Unknown image ablation mode: {mode}")


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
    row: dict[str, Any] = {
        "scenario": scenario.name,
        "level": scenario.level,
        "control_mode": args.control_mode,
        "image_ablation": args.image_ablation,
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
        "guard_final_servo_active": bool(step.guard_final_servo_active) if step_guard else False,
        "guard_final_servo_triggered": (
            bool(step.guard_final_servo_triggered) if step_guard else False
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
        "guard_final_servo_phase_steps": (
            int(step.guard_final_servo_phase_steps) if step_guard else 0
        ),
        "guard_final_servo_stable_steps": (
            int(step.guard_final_servo_stable_steps) if step_guard else 0
        ),
        "guard_final_servo_stall_steps": (
            int(step.guard_final_servo_stall_steps) if step_guard else 0
        ),
        "guard_final_servo_retry_count": (
            int(step.guard_final_servo_retry_count) if step_guard else 0
        ),
        "guard_final_servo_descent_allowed": (
            bool(step.guard_final_servo_descent_allowed) if step_guard else False
        ),
        "guard_final_servo_down_blocked": (
            bool(step.guard_final_servo_down_blocked) if step_guard else False
        ),
        **vector3_columns("policy_action", policy_action),
        **maybe_vector3_columns("guarded_action", None if step is None or step.guarded_action is None else step.guarded_action),
        **vector3_columns("final_action", final_action),
        **vector3_columns("commanded_action", post_info["commanded_action"]),
        **vector3_columns("applied_action", post_info["applied_action"]),
        "action_tracking_error": float(post_info["action_tracking_error"]),
        **vector3_columns("action_tip_delta_error", post_info["action_tip_delta_error"]),
        "ik_control_mode": str(post_info.get("ik_control_mode", "")),
        "ik_target_error": float(post_info.get("ik_target_error", np.nan)),
        "ik_orientation_error": float(post_info.get("ik_orientation_error", np.nan)),
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
        "hole_half_size": float(post_info.get("hole_half_size", np.nan)),
        "peg_radius": float(post_info.get("peg_radius", np.nan)),
        "hole_clearance": float(post_info.get("hole_half_size", np.nan) - post_info.get("peg_radius", np.nan)),
    }
    return row


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
    shuffle_bank: list[Any] = []
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
    final_servo_episodes = 0
    final_servo_steps: list[float] = []
    final_servo_triggers: list[float] = []
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
            obs, info = env.reset(seed=episode_seed)
            guarded_controller.reset()
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
            episode_final_servo_steps = 0
            episode_final_servo_triggers = 0
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
            while True:
                pre_info = {key: value for key, value in info.items()}
                if args.control_mode == "guard_only":
                    state = guard_state_provider.state_from_info(pre_info)
                    policy_action = np.zeros(3, dtype=np.float32)
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
                        mode=args.image_ablation,
                        rng=ablation_rng,
                        shuffle_bank=shuffle_bank,
                    )
                    policy_action, _ = model.predict(model_obs, deterministic=True)
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
                episode_guard_steps += int(guarded)
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
                    episode_final_servo_steps += int(step.guard_final_servo_active)
                    episode_final_servo_triggers += int(step.guard_final_servo_triggered)
                    episode_final_servo_recovery_triggers += int(
                        step.guard_final_servo_recovery_triggered
                    )
                    episode_final_servo_descent_steps += int(
                        step.guard_final_servo_descent_allowed
                    )
                    episode_final_servo_exhausted_steps += int(
                        step.guard_final_servo_exhausted
                    )
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
            final_servo_steps.append(float(episode_final_servo_steps))
            final_servo_triggers.append(float(episode_final_servo_triggers))
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
            hole_half_size = float(info.get("hole_half_size", np.nan))
            peg_radius = float(info.get("peg_radius", np.nan))
            episode_rows.append(
                {
                    "scenario": scenario.name,
                    "level": scenario.level,
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
                    "final_servo_steps": episode_final_servo_steps,
                    "final_servo_triggers": episode_final_servo_triggers,
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
                    "hole_half_size": hole_half_size,
                    "peg_radius": peg_radius,
                    "hole_clearance": hole_half_size - peg_radius,
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
    mean_final_servo_steps = mean(final_servo_steps)
    mean_final_servo_descent_steps = mean(final_servo_descent_steps)
    summary = {
        "name": scenario.name,
        "level": scenario.level,
        "control_mode": args.control_mode,
        "image_ablation": args.image_ablation,
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
        "mean_final_servo_steps": mean_final_servo_steps,
        "mean_final_servo_step_fraction": mean_final_servo_steps / max(mean_steps, 1e-9),
        "mean_final_servo_triggers": mean(final_servo_triggers),
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
        f"- Episodes per scenario: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Frame skip: `{args.frame_skip}`",
        f"- Step trace CSV: `{args.step_output_csv}`",
        f"- Step trace outcome filter: `{args.step_trace_outcome_filter}`",
        f"- Near-hole crop offset: `{tuple(args.near_hole_crop_offset)}`",
        f"- Include control state: `{args.include_control_state}`",
        f"- Image frame stack: `{args.image_frame_stack}`",
        f"- Wrist camera pos offset: `{tuple(args.wrist_camera_pos_offset)}`",
        f"- Wrist camera rot offset deg: `{tuple(args.wrist_camera_rot_offset_deg)}`",
        f"- Wrist camera FOV override: `{args.wrist_camera_fovy}`",
        f"- IK control mode: `{args.ik_control_mode}`",
        f"- IK orientation/posture weight: `{args.ik_orientation_weight}/{args.ik_posture_weight}`",
        f"- IK step limit/max iterations: `{args.ik_step_limit}/{args.ik_max_iterations}`",
        f"- Nominal joint damping / actuator Kp multiplier: `{args.nominal_joint_damping_multiplier}/{args.nominal_actuator_kp_multiplier}`",
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
        f"- Guard insert latch resume/recenter/max down: `{args.guard_insert_latch_resume_xy}/{args.guard_insert_latch_recenter_height}/{args.guard_insert_latch_max_down_action}`",
        f"- Guard hover enabled: `{args.guard_hover_enabled}`",
        f"- Guard hover XY/release/height/Z tol/steps/max down: `{args.guard_hover_xy_tolerance}/{args.guard_hover_release_xy}/{args.guard_hover_height}/{args.guard_hover_z_tolerance}/{args.guard_hover_required_steps}/{args.guard_hover_max_down_action}`",
        f"- Guard near action scale enabled: `{args.guard_near_action_scale_enabled}`",
        f"- Guard near XY/Z/max XY/max down: `{args.guard_near_action_xy_tolerance}/{args.guard_near_action_z_threshold}/{args.guard_near_max_xy_action}/{args.guard_near_max_down_action}`",
        f"- Guard fixture clearance enabled: `{args.guard_fixture_clearance_enabled}`",
        f"- Guard fixture clearance XY/Z/lift/max up: `{args.guard_fixture_clearance_xy_min}-{args.guard_fixture_clearance_xy_max}/{args.guard_fixture_clearance_z_max}/{args.guard_fixture_clearance_lift_height}/{args.guard_fixture_clearance_max_up_action}`",
        f"- Guard fixture clearance realign enabled: `{args.guard_fixture_clearance_realign_enabled}`",
        f"- Guard fixture clearance realign start Z/XY/max XY/max down/max steps: `{args.guard_fixture_clearance_realign_start_z}/{args.guard_fixture_clearance_realign_xy}/{args.guard_fixture_clearance_max_xy_action}/{args.guard_fixture_clearance_max_down_action}/{args.guard_fixture_clearance_max_steps}`",
        f"- Guard preinsert recenter enabled: `{args.guard_preinsert_recenter_enabled}`",
        f"- Guard preinsert recenter start/min Z, trigger/stable XY: `{args.guard_preinsert_recenter_start_z}/{args.guard_preinsert_recenter_min_z}/{args.guard_preinsert_recenter_trigger_xy}/{args.guard_preinsert_recenter_stable_xy}`",
        f"- Guard preinsert recenter height/Z tol/stable/max steps/max XY/max up: `{args.guard_preinsert_recenter_height}/{args.guard_preinsert_recenter_z_tolerance}/{args.guard_preinsert_recenter_stable_steps}/{args.guard_preinsert_recenter_max_steps}/{args.guard_preinsert_recenter_max_xy_action}/{args.guard_preinsert_recenter_max_up_action}`",
        f"- Guard final servo enabled: `{args.guard_final_servo_enabled}`",
        f"- Guard final servo start XY/Z/min Z: `{args.guard_final_servo_start_xy}/{args.guard_final_servo_start_z}/{args.guard_final_servo_min_start_z}`",
        f"- Guard final servo hover/stable/release: `{args.guard_final_servo_hover_height}/{args.guard_final_servo_stable_xy}/{args.guard_final_servo_release_xy}`",
        f"- Guard final servo stable/stall/retries: `{args.guard_final_servo_stable_steps}/{args.guard_final_servo_stall_steps}/{args.guard_final_servo_max_retries}`",
        f"- Guard final servo max XY/down/descend bias/lift/recovery steps: `{args.guard_final_servo_max_xy_action}/{args.guard_final_servo_max_down_action}/{tuple(args.guard_final_servo_descend_xy_bias)}/{args.guard_final_servo_lift_height}/{args.guard_final_servo_max_recovery_steps}`",
        f"- Guard final servo recovery mode/soft lift/min height/z tol/hold/max up: `{args.guard_final_servo_recovery_mode}/{args.guard_final_servo_soft_unjam_lift}/{args.guard_final_servo_soft_unjam_min_height}/{args.guard_final_servo_soft_unjam_z_tolerance}/{args.guard_final_servo_soft_unjam_hold_steps}/{args.guard_final_servo_soft_unjam_max_up_action}`",
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
        "| Scenario | Level | Mode | Image | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Retry steps | Latch steps | Hover steps | Near limited | Fixture steps | Fixture realign | Preinsert | Final servo | Final servo descend | Final XY | Final Z |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {name} | {level} | {control_mode} | {image_ablation} | {guard_enabled} | {success_rate:.3f} | {collision_rate:.3f} | "
            "{timeout_rate:.3f} | {mean_return:.3f} | {mean_steps:.1f} | "
            "{mean_guarded_steps:.1f} ({mean_guarded_step_fraction:.2f}) | "
            "{mean_retry_steps:.1f} ({mean_retry_step_fraction:.2f}) | "
            "{mean_latch_steps:.1f} ({mean_latch_step_fraction:.2f}, down {mean_latch_descent_fraction:.2f}) | "
            "{mean_hover_steps:.1f} ({mean_hover_step_fraction:.2f}, latched {mean_hover_latched_fraction:.2f}, block {mean_hover_blocked_fraction:.2f}) | "
            "{mean_near_limited_steps:.1f} ({mean_near_limited_fraction:.2f}) | "
            "{mean_fixture_clearance_steps:.1f} ({mean_fixture_clearance_fraction:.2f}) | "
            "{mean_fixture_clearance_realign_steps:.1f} ({mean_fixture_clearance_realign_fraction:.2f}) | "
            "{mean_preinsert_recenter_steps:.1f} ({mean_preinsert_recenter_fraction:.2f}, trig {mean_preinsert_recenter_triggers:.2f}, rel {mean_preinsert_recenter_releases:.2f}) | "
            "{mean_final_servo_steps:.1f} ({mean_final_servo_step_fraction:.2f}, trig {mean_final_servo_triggers:.2f}, rec {mean_final_servo_recovery_triggers:.2f}) | "
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
    if args.guard_start_xy <= 0.0 or args.guard_start_z <= 0.0:
        raise ValueError("--guard-start-xy and --guard-start-z must be positive.")
    if args.guard_risk_xy < 0.0 or args.guard_risk_xy > args.guard_start_xy:
        raise ValueError("--guard-risk-xy must be between 0 and --guard-start-xy.")
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
    if args.guard_final_servo_stable_steps <= 0:
        raise ValueError("--guard-final-servo-stable-steps must be positive.")
    if args.guard_final_servo_release_xy < args.guard_final_servo_stable_xy:
        raise ValueError("--guard-final-servo-release-xy must be >= stable-xy.")
    if args.guard_final_servo_max_xy_action <= 0.0:
        raise ValueError("--guard-final-servo-max-xy-action must be positive.")
    if args.guard_final_servo_max_down_action < 0.0:
        raise ValueError("--guard-final-servo-max-down-action cannot be negative.")
    if len(args.guard_final_servo_descend_xy_bias) != 2:
        raise ValueError("--guard-final-servo-descend-xy-bias requires two values.")
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

    scenarios = [HARD_BUCKET_SCENARIO] if args.hard_bucket_only else list(CORE_SCENARIOS)
    if args.include_hard_bucket and not args.hard_bucket_only:
        scenarios.append(HARD_BUCKET_SCENARIO)

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
