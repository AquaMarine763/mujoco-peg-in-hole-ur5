from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco import (
    GuardedPolicyConfig,
    GuardedPolicyController,
    MujocoGuardStateProvider,
    OracleControllerConfig,
    PegInHoleMujocoEnv,
)
from peg_in_hole_mujoco.policy_interface import (
    ActionTransformResult,
    MujocoActionExecutor,
    MujocoObservationProvider,
    PolicyInferenceSession,
    SB3PolicyAdapter,
    SafetyConfig,
    SafetyFilter,
    write_trace_csv,
)


AGENTS = {
    "sac": SAC,
    "ppo": PPO,
    "a2c": A2C,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a trained policy through the deployment-style inference interface.")
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("results/policy_inference_trace.csv"))
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=120_000)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--control-frequency-hz", type=float, default=50.0)
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
    parser.add_argument(
        "--domain-randomization-level",
        choices=["none", "visual", "visual_camera", "visual_camera_control", "full_light_geometry", "full_contact_light", "full"],
        default="none",
    )
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--control-action-scale-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--control-action-noise-std-range", nargs=2, type=float, default=(0.0, 0.0008))
    parser.add_argument("--control-action-delay-range", nargs=2, type=int, default=(0, 2))
    parser.add_argument("--control-action-filter-alpha-range", nargs=2, type=float, default=(0.55, 1.0))
    parser.add_argument("--geometry-hole-center-xy-jitter", nargs=2, type=float, default=(0.002, 0.002))
    parser.add_argument("--geometry-fixture-height-jitter", type=float, default=0.001)
    parser.add_argument("--geometry-table-height-jitter", type=float, default=0.001)
    parser.add_argument("--geometry-hole-half-size-range", nargs=2, type=float, default=(0.017, 0.021))
    parser.add_argument("--geometry-peg-radius-range", nargs=2, type=float, default=(0.0115, 0.0125))
    parser.add_argument("--contact-friction-multiplier-range", nargs=2, type=float, default=(0.7, 1.3))
    parser.add_argument("--contact-solref-time-multiplier-range", nargs=2, type=float, default=(0.8, 1.25))
    parser.add_argument("--contact-solref-damping-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--contact-solimp-width-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--dynamics-joint-damping-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--dynamics-actuator-kp-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--target-low", nargs=3, type=float, default=(0.50, 0.00, 0.65))
    parser.add_argument("--target-high", nargs=3, type=float, default=(0.60, 0.10, 0.65))
    parser.add_argument("--ik-control-mode", choices=["position", "pose"], default="position")
    parser.add_argument("--ik-orientation-weight", type=float, default=0.12)
    parser.add_argument("--ik-posture-weight", type=float, default=0.01)
    parser.add_argument("--ik-step-limit", type=float, default=0.06)
    parser.add_argument("--ik-max-iterations", type=int, default=24)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--approach-xy-tolerance", type=float, default=0.06)
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
    parser.add_argument("--safety-max-action", type=float, default=0.005)
    parser.add_argument("--safety-workspace-low", nargs=3, type=float, default=(0.30, -0.25, 0.55))
    parser.add_argument("--safety-workspace-high", nargs=3, type=float, default=(0.75, 0.25, 0.85))
    parser.add_argument("--safety-action-filter-alpha", type=float, default=1.0)
    parser.add_argument("--guarded-policy", action="store_true")
    parser.add_argument(
        "--guard-scenario-filter",
        choices=["none", "all", "geometry", "hard"],
        default="geometry",
    )
    parser.add_argument("--guard-scenario-name", default="deployment")
    parser.add_argument("--guard-start-xy", type=float, default=0.060)
    parser.add_argument("--guard-start-z", type=float, default=0.100)
    parser.add_argument("--guard-risk-xy", type=float, default=0.0)
    parser.add_argument("--guard-blend", type=float, default=0.75)
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
    parser.add_argument("--contact-recovery-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--contact-recovery-z-max", type=float, default=0.050)
    parser.add_argument("--contact-recovery-lift-height", type=float, default=0.060)
    parser.add_argument("--contact-recovery-lift-z-tolerance", type=float, default=0.010)
    parser.add_argument("--contact-recovery-max-down-action", type=float, default=0.001)
    parser.add_argument("--timeout-progress-xy-tolerance", type=float, default=0.010)
    parser.add_argument("--timeout-progress-z-max", type=float, default=0.060)
    parser.add_argument("--timeout-progress-max-down-action", type=float, default=0.0015)
    return parser.parse_args()


def make_env(args: argparse.Namespace) -> PegInHoleMujocoEnv:
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
        target_low=tuple(args.target_low),
        target_high=tuple(args.target_high),
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
        domain_randomization_level=args.domain_randomization_level,
        control_action_scale_range=tuple(args.control_action_scale_range),
        control_action_noise_std_range=tuple(args.control_action_noise_std_range),
        control_action_delay_range=tuple(args.control_action_delay_range),
        control_action_filter_alpha_range=tuple(args.control_action_filter_alpha_range),
        geometry_hole_center_xy_jitter=tuple(args.geometry_hole_center_xy_jitter),
        geometry_fixture_height_jitter=args.geometry_fixture_height_jitter,
        geometry_table_height_jitter=args.geometry_table_height_jitter,
        geometry_hole_half_size_range=tuple(args.geometry_hole_half_size_range),
        geometry_peg_radius_range=tuple(args.geometry_peg_radius_range),
        contact_friction_multiplier_range=tuple(args.contact_friction_multiplier_range),
        contact_solref_time_multiplier_range=tuple(args.contact_solref_time_multiplier_range),
        contact_solref_damping_multiplier_range=tuple(args.contact_solref_damping_multiplier_range),
        contact_solimp_width_multiplier_range=tuple(args.contact_solimp_width_multiplier_range),
        dynamics_joint_damping_multiplier_range=tuple(args.dynamics_joint_damping_multiplier_range),
        dynamics_actuator_kp_multiplier_range=tuple(args.dynamics_actuator_kp_multiplier_range),
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


class GuardedDeploymentActionTransformer:
    def __init__(
        self,
        env: PegInHoleMujocoEnv,
        config: GuardedPolicyConfig,
        scenario_name: str,
        scenario_level: str,
    ) -> None:
        self.env = env
        self.controller = GuardedPolicyController(config)
        self.state_provider = MujocoGuardStateProvider(env)
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
            "guard_retry_active": False,
            "guard_retry_triggered": False,
            "guard_retry_count": 0,
            "guard_retry_stall_steps": 0,
            "guard_retry_active_steps": 0,
            "guard_insert_latched": False,
            "guard_insert_latch_activated": False,
            "guard_insert_latch_released": False,
            "guard_insert_latch_steps": 0,
            "guard_insert_latch_descent_allowed": False,
            "guard_hover_active": False,
            "guard_hover_stable_steps": 0,
            "guard_hover_descent_allowed": False,
            "guard_hover_descent_latched": False,
            "guard_hover_down_blocked": False,
            "guard_near_action_limited": False,
            "guard_fixture_clearance_active": False,
            "guard_fixture_clearance_triggered": False,
            "guard_fixture_clearance_released": False,
            "guard_fixture_clearance_phase": "none",
            "guard_fixture_clearance_steps": 0,
            "guard_fixture_clearance_realign_steps": 0,
            "guard_final_servo_active": False,
            "guard_final_servo_triggered": False,
            "guard_final_servo_recovery_triggered": False,
            "guard_final_servo_exhausted": False,
            "guard_final_servo_phase": "inactive",
            "guard_final_servo_phase_steps": 0,
            "guard_final_servo_stable_steps": 0,
            "guard_final_servo_stall_steps": 0,
            "guard_final_servo_retry_count": 0,
            "guard_final_servo_descent_allowed": False,
            "guard_final_servo_down_blocked": False,
        }

    def transform(self, info: dict[str, Any], policy_action: np.ndarray) -> ActionTransformResult:
        guarded_step = self.controller.step_with_provider(
            self.state_provider,
            info,
            policy_action,
            scenario_name=self.scenario_name,
            scenario_level=self.scenario_level,
        )
        return ActionTransformResult(
            action=guarded_step.action,
            diagnostics={
                "guard_enabled": self.guard_enabled,
                "guard_active": guarded_step.guarded,
                "guard_should_activate": guarded_step.guard_should_activate,
                "guard_can_activate": guarded_step.guard_can_activate,
                "guard_activated": guarded_step.guard_activated,
                "guard_down_blocked": guarded_step.guard_down_blocked,
                "guard_steps_since_reset": guarded_step.guard_steps_since_reset,
                "guard_min_policy_steps": self.controller.config.guard_min_policy_steps,
                "guard_dist_xy": guarded_step.guard_dist_xy,
                "guard_z_above_target": guarded_step.guard_z_above_target,
                "guard_retry_active": guarded_step.guard_retry_active,
                "guard_retry_triggered": guarded_step.guard_retry_triggered,
                "guard_retry_count": guarded_step.guard_retry_count,
                "guard_retry_stall_steps": guarded_step.guard_retry_stall_steps,
                "guard_retry_active_steps": guarded_step.guard_retry_active_steps,
                "guard_insert_latched": guarded_step.guard_insert_latched,
                "guard_insert_latch_activated": guarded_step.guard_insert_latch_activated,
                "guard_insert_latch_released": guarded_step.guard_insert_latch_released,
                "guard_insert_latch_steps": guarded_step.guard_insert_latch_steps,
                "guard_insert_latch_descent_allowed": guarded_step.guard_insert_latch_descent_allowed,
                "guard_hover_active": guarded_step.guard_hover_active,
                "guard_hover_stable_steps": guarded_step.guard_hover_stable_steps,
                "guard_hover_descent_allowed": guarded_step.guard_hover_descent_allowed,
                "guard_hover_descent_latched": guarded_step.guard_hover_descent_latched,
                "guard_hover_down_blocked": guarded_step.guard_hover_down_blocked,
                "guard_near_action_limited": guarded_step.guard_near_action_limited,
                "guard_fixture_clearance_active": guarded_step.guard_fixture_clearance_active,
                "guard_fixture_clearance_triggered": guarded_step.guard_fixture_clearance_triggered,
                "guard_fixture_clearance_released": guarded_step.guard_fixture_clearance_released,
                "guard_fixture_clearance_phase": guarded_step.guard_fixture_clearance_phase,
                "guard_fixture_clearance_steps": guarded_step.guard_fixture_clearance_steps,
                "guard_fixture_clearance_realign_steps": guarded_step.guard_fixture_clearance_realign_steps,
                "guard_final_servo_active": guarded_step.guard_final_servo_active,
                "guard_final_servo_triggered": guarded_step.guard_final_servo_triggered,
                "guard_final_servo_recovery_triggered": guarded_step.guard_final_servo_recovery_triggered,
                "guard_final_servo_exhausted": guarded_step.guard_final_servo_exhausted,
                "guard_final_servo_phase": guarded_step.guard_final_servo_phase,
                "guard_final_servo_phase_steps": guarded_step.guard_final_servo_phase_steps,
                "guard_final_servo_stable_steps": guarded_step.guard_final_servo_stable_steps,
                "guard_final_servo_stall_steps": guarded_step.guard_final_servo_stall_steps,
                "guard_final_servo_retry_count": guarded_step.guard_final_servo_retry_count,
                "guard_final_servo_descent_allowed": guarded_step.guard_final_servo_descent_allowed,
                "guard_final_servo_down_blocked": guarded_step.guard_final_servo_down_blocked,
                "policy_action": guarded_step.policy_action,
                "guarded_action": guarded_step.guarded_action,
                "final_action": guarded_step.action,
            },
        )


def main() -> None:
    args = parse_args()
    env = make_env(args)
    model = AGENTS[args.agent].load(args.model, env=env, device=args.device)
    policy = SB3PolicyAdapter(model, deterministic=not args.stochastic)
    safety_filter = SafetyFilter(
        SafetyConfig(
            max_action=args.safety_max_action,
            workspace_low=tuple(args.safety_workspace_low),
            workspace_high=tuple(args.safety_workspace_high),
            action_filter_alpha=args.safety_action_filter_alpha,
        )
    )
    action_transformer = (
        GuardedDeploymentActionTransformer(
            env,
            make_guarded_config(args),
            args.guard_scenario_name,
            args.domain_randomization_level,
        )
        if args.guarded_policy
        else None
    )
    session = PolicyInferenceSession(
        observation_provider=MujocoObservationProvider(env),
        action_executor=MujocoActionExecutor(env),
        policy=policy,
        safety_filter=safety_filter,
        control_frequency_hz=args.control_frequency_hz,
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
    print(f"saved inference trace to {args.output}")
    if results:
        success_rate = sum(int(result.success) for result in results) / len(results)
        collision_rate = sum(int(result.collision) for result in results) / len(results)
        mean_steps = sum(result.steps for result in results) / len(results)
        print(f"episodes={len(results)}")
        print(f"success_rate={success_rate:.3f}")
        print(f"collision_rate={collision_rate:.3f}")
        print(f"mean_steps={mean_steps:.1f}")


if __name__ == "__main__":
    main()
