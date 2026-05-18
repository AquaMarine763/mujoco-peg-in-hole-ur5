from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import mujoco
import numpy as np
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a trained policy rollout to a GIF or video.")
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("demo_state.gif"))
    parser.add_argument("--observation-mode", choices=["image", "state"], default="state")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument("--width", type=int, default=100, help="Policy observation image width.")
    parser.add_argument("--height", type=int, default=100, help="Policy observation image height.")
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
    parser.add_argument("--render-width", type=int, default=640, help="Output demo frame width.")
    parser.add_argument("--render-height", type=int, default=480, help="Output demo frame height.")
    parser.add_argument("--render-camera", default="overview", help="MuJoCo camera used for the output demo.")
    parser.add_argument(
        "--render-cameras",
        nargs="+",
        default=None,
        help="Optional list of MuJoCo cameras to concatenate horizontally. Overrides --render-camera.",
    )
    parser.add_argument("--trajectory-output", type=Path, default=None, help="Optional CSV file for rollout diagnostics.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--domain-randomization", action="store_true")
    parser.add_argument(
        "--domain-randomization-level",
        choices=["none", "visual", "visual_camera", "visual_camera_control", "full_light_geometry", "full_contact_light", "full"],
        default="none",
    )
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--control-action-scale-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument(
        "--control-action-noise-std-range",
        nargs=2,
        type=float,
        default=(0.0, 0.0008),
    )
    parser.add_argument("--control-action-delay-range", nargs=2, type=int, default=(0, 2))
    parser.add_argument(
        "--control-action-filter-alpha-range",
        nargs=2,
        type=float,
        default=(0.55, 1.0),
    )
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
    parser.add_argument("--nominal-joint-damping-multiplier", type=float, default=1.0)
    parser.add_argument("--nominal-actuator-kp-multiplier", type=float, default=1.0)
    parser.add_argument("--target-low", nargs=3, type=float, default=(0.50, 0.00, 0.65))
    parser.add_argument("--target-high", nargs=3, type=float, default=(0.60, 0.10, 0.65))
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
    parser.add_argument("--guarded-policy", action="store_true")
    parser.add_argument(
        "--guard-scenario-filter",
        choices=["none", "all", "geometry", "hard"],
        default="geometry",
    )
    parser.add_argument("--guard-scenario-name", default="demo")
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
    parser.add_argument("--contact-recovery-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--contact-recovery-z-max", type=float, default=0.050)
    parser.add_argument("--contact-recovery-lift-height", type=float, default=0.060)
    parser.add_argument("--contact-recovery-lift-z-tolerance", type=float, default=0.010)
    parser.add_argument("--contact-recovery-max-down-action", type=float, default=0.001)
    parser.add_argument("--timeout-progress-xy-tolerance", type=float, default=0.010)
    parser.add_argument("--timeout-progress-z-max", type=float, default=0.060)
    parser.add_argument("--timeout-progress-max-down-action", type=float, default=0.0015)
    return parse_args_with_config(parser)


def make_env(args: argparse.Namespace) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode=args.observation_mode,
        render_mode="rgb_array",
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
        action_scale=args.action_scale,
        target_low=tuple(args.target_low),
        target_high=tuple(args.target_high),
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
        randomize_domain=args.domain_randomization,
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
        nominal_joint_damping_multiplier=args.nominal_joint_damping_multiplier,
        nominal_actuator_kp_multiplier=args.nominal_actuator_kp_multiplier,
    )


def render_demo_frame(
    env: PegInHoleMujocoEnv,
    renderer: mujoco.Renderer,
    camera_names: list[str],
) -> np.ndarray:
    camera_frames = []
    for camera_name in camera_names:
        renderer.update_scene(env.data, camera=camera_name)
        camera_frames.append(renderer.render().copy())
    if len(camera_frames) == 1:
        return camera_frames[0]
    return np.concatenate(camera_frames, axis=1)


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


def vector_fields(prefix: str, value: Any, size: int) -> dict[str, float]:
    labels = ("x", "y", "z") if size == 3 else tuple(str(index) for index in range(size))
    if value is None:
        return {f"{prefix}_{label}": float("nan") for label in labels}
    array = np.asarray(value, dtype=np.float64).reshape(-1)
    return {
        f"{prefix}_{label}": float(array[index]) if index < array.size else float("nan")
        for index, label in enumerate(labels)
    }


def trajectory_row(
    *,
    episode: int,
    step: int,
    reward: float,
    episode_return: float,
    policy_action: np.ndarray,
    final_action: np.ndarray | None,
    guarded_action: np.ndarray | None,
    guard_enabled: bool,
    guard_active: bool,
    guard_should_activate: bool = False,
    guard_can_activate: bool = False,
    guard_activated: bool = False,
    guard_down_blocked: bool = False,
    guard_steps_since_reset: int = -1,
    guard_min_policy_steps: int = 0,
    guard_dist_xy: float = float("nan"),
    guard_z_above_target: float = float("nan"),
    guard_retry_active: bool = False,
    guard_retry_triggered: bool = False,
    guard_retry_count: int = 0,
    guard_retry_stall_steps: int = 0,
    guard_retry_active_steps: int = 0,
    guard_insert_latched: bool = False,
    guard_insert_latch_activated: bool = False,
    guard_insert_latch_released: bool = False,
    guard_insert_latch_steps: int = 0,
    guard_insert_latch_descent_allowed: bool = False,
    guard_hover_active: bool = False,
    guard_hover_stable_steps: int = 0,
    guard_hover_descent_allowed: bool = False,
    guard_hover_descent_latched: bool = False,
    guard_hover_down_blocked: bool = False,
    guard_near_action_limited: bool = False,
    guard_fixture_clearance_active: bool = False,
    guard_fixture_clearance_triggered: bool = False,
    guard_fixture_clearance_released: bool = False,
    guard_fixture_clearance_phase: str = "none",
    guard_fixture_clearance_steps: int = 0,
    guard_fixture_clearance_realign_steps: int = 0,
    guard_final_servo_active: bool = False,
    guard_final_servo_triggered: bool = False,
    guard_final_servo_recovery_triggered: bool = False,
    guard_final_servo_exhausted: bool = False,
    guard_final_servo_phase: str = "inactive",
    guard_final_servo_phase_steps: int = 0,
    guard_final_servo_stable_steps: int = 0,
    guard_final_servo_stall_steps: int = 0,
    guard_final_servo_retry_count: int = 0,
    guard_final_servo_descent_allowed: bool = False,
    guard_final_servo_down_blocked: bool = False,
    info: dict[str, Any],
    terminated: bool,
    truncated: bool,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "episode": episode,
        "step": step,
        "reward": float(reward),
        "episode_return": float(episode_return),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "guard_enabled": bool(guard_enabled),
        "guard_active": bool(guard_active),
        "guard_should_activate": bool(guard_should_activate),
        "guard_can_activate": bool(guard_can_activate),
        "guard_activated": bool(guard_activated),
        "guard_down_blocked": bool(guard_down_blocked),
        "guard_steps_since_reset": int(guard_steps_since_reset),
        "guard_min_policy_steps": int(guard_min_policy_steps),
        "guard_dist_xy": float(guard_dist_xy),
        "guard_z_above_target": float(guard_z_above_target),
        "guard_retry_active": bool(guard_retry_active),
        "guard_retry_triggered": bool(guard_retry_triggered),
        "guard_retry_count": int(guard_retry_count),
        "guard_retry_stall_steps": int(guard_retry_stall_steps),
        "guard_retry_active_steps": int(guard_retry_active_steps),
        "guard_insert_latched": bool(guard_insert_latched),
        "guard_insert_latch_activated": bool(guard_insert_latch_activated),
        "guard_insert_latch_released": bool(guard_insert_latch_released),
        "guard_insert_latch_steps": int(guard_insert_latch_steps),
        "guard_insert_latch_descent_allowed": bool(guard_insert_latch_descent_allowed),
        "guard_hover_active": bool(guard_hover_active),
        "guard_hover_stable_steps": int(guard_hover_stable_steps),
        "guard_hover_descent_allowed": bool(guard_hover_descent_allowed),
        "guard_hover_descent_latched": bool(guard_hover_descent_latched),
        "guard_hover_down_blocked": bool(guard_hover_down_blocked),
        "guard_near_action_limited": bool(guard_near_action_limited),
        "guard_fixture_clearance_active": bool(guard_fixture_clearance_active),
        "guard_fixture_clearance_triggered": bool(guard_fixture_clearance_triggered),
        "guard_fixture_clearance_released": bool(guard_fixture_clearance_released),
        "guard_fixture_clearance_phase": str(guard_fixture_clearance_phase),
        "guard_fixture_clearance_steps": int(guard_fixture_clearance_steps),
        "guard_fixture_clearance_realign_steps": int(guard_fixture_clearance_realign_steps),
        "guard_final_servo_active": bool(guard_final_servo_active),
        "guard_final_servo_triggered": bool(guard_final_servo_triggered),
        "guard_final_servo_recovery_triggered": bool(guard_final_servo_recovery_triggered),
        "guard_final_servo_exhausted": bool(guard_final_servo_exhausted),
        "guard_final_servo_phase": str(guard_final_servo_phase),
        "guard_final_servo_phase_steps": int(guard_final_servo_phase_steps),
        "guard_final_servo_stable_steps": int(guard_final_servo_stable_steps),
        "guard_final_servo_stall_steps": int(guard_final_servo_stall_steps),
        "guard_final_servo_retry_count": int(guard_final_servo_retry_count),
        "guard_final_servo_descent_allowed": bool(guard_final_servo_descent_allowed),
        "guard_final_servo_down_blocked": bool(guard_final_servo_down_blocked),
        "success": bool(info.get("insertion_success", False)),
        "collision": bool(info.get("collision", False)),
        "dist_xy": float(info.get("dist_xy", float("nan"))),
        "dist_z": float(info.get("dist_z", float("nan"))),
        "shaped_distance": float(info.get("shaped_distance", float("nan"))),
        "desired_z": float(info.get("desired_z", float("nan"))),
        "action_tracking_error": float(info.get("action_tracking_error", float("nan"))),
        "ik_control_mode": str(info.get("ik_control_mode", "")),
        "ik_target_error": float(info.get("ik_target_error", float("nan"))),
        "ik_orientation_error": float(info.get("ik_orientation_error", float("nan"))),
        "ik_iterations": int(info.get("ik_iterations", -1)),
        "peg_tilt_angle_deg": float(info.get("peg_tilt_angle_deg", float("nan"))),
        "joint_limit_min_normalized_margin": float(
            info.get("joint_limit_min_normalized_margin", float("nan"))
        ),
        "joint_target_error": float(info.get("joint_target_error", float("nan"))),
        "control_action_scale_multiplier": float(info.get("control_action_scale_multiplier", float("nan"))),
        "control_action_noise_std": float(info.get("control_action_noise_std", float("nan"))),
        "control_action_delay": int(info.get("control_action_delay", -1)),
        "control_action_filter_alpha": float(info.get("control_action_filter_alpha", float("nan"))),
        "fixture_height_offset": float(info.get("fixture_height_offset", float("nan"))),
        "table_height_offset": float(info.get("table_height_offset", float("nan"))),
        "hole_half_size": float(info.get("hole_half_size", float("nan"))),
        "peg_radius": float(info.get("peg_radius", float("nan"))),
        "contact_friction_multiplier": float(info.get("contact_friction_multiplier", float("nan"))),
        "contact_solref_time_multiplier": float(info.get("contact_solref_time_multiplier", float("nan"))),
        "contact_solref_damping_multiplier": float(info.get("contact_solref_damping_multiplier", float("nan"))),
        "contact_solimp_width_multiplier": float(info.get("contact_solimp_width_multiplier", float("nan"))),
        "joint_damping_multiplier": float(info.get("joint_damping_multiplier", float("nan"))),
        "actuator_kp_multiplier": float(info.get("actuator_kp_multiplier", float("nan"))),
    }
    row.update(vector_fields("target", info.get("target_pos", (float("nan"),) * 3), 3))
    row.update(vector_fields("peg_tip", info.get("peg_tip_pos", (float("nan"),) * 3), 3))
    row.update(vector_fields("policy_action", policy_action, 3))
    row.update(vector_fields("guarded_action", guarded_action, 3))
    row.update(vector_fields("final_action", final_action, 3))
    row.update(vector_fields("commanded_action", info.get("commanded_action", (float("nan"),) * 3), 3))
    row.update(vector_fields("applied_action", info.get("applied_action", (float("nan"),) * 3), 3))
    row.update(vector_fields("action_tip_pos_before", info.get("action_tip_pos_before", (float("nan"),) * 3), 3))
    row.update(vector_fields("action_target_tip_pos", info.get("action_target_tip_pos", (float("nan"),) * 3), 3))
    row.update(vector_fields("action_target_tip_delta", info.get("action_target_tip_delta", (float("nan"),) * 3), 3))
    row.update(vector_fields("action_actual_tip_delta", info.get("action_actual_tip_delta", (float("nan"),) * 3), 3))
    row.update(vector_fields("action_tip_delta_error", info.get("action_tip_delta_error", (float("nan"),) * 3), 3))
    row.update(vector_fields("ik_tip_pos", info.get("ik_tip_pos", (float("nan"),) * 3), 3))
    row.update(vector_fields("joint_qpos_before_action", info.get("joint_qpos_before_action", (float("nan"),) * 6), 6))
    row.update(vector_fields("joint_target_qpos", info.get("joint_target_qpos", (float("nan"),) * 6), 6))
    row.update(vector_fields("joint_qpos_after_action", info.get("joint_qpos_after_action", (float("nan"),) * 6), 6))
    row.update(vector_fields("hole_center_offset", info.get("hole_center_offset", (float("nan"),) * 2), 2))
    return row


def save_trajectory_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved trajectory diagnostics to {path}")


def save_demo_frames(imageio: Any, path: Path, frames: list[np.ndarray], fps: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        imageio.mimsave(path, frames, fps=fps)
        print(f"saved demo to {path}")
        return path
    except ValueError as exc:
        video_suffixes = {".mp4", ".mov", ".avi", ".mkv"}
        if path.suffix.lower() not in video_suffixes:
            raise
        fallback = path.with_suffix(".gif")
        imageio.mimsave(fallback, frames, fps=fps)
        print(f"video backend unavailable for {path}: {exc}")
        print(f"saved GIF fallback to {fallback}")
        return fallback


def main() -> None:
    try:
        import imageio.v2 as imageio
    except ImportError as exc:
        raise ImportError("Install imageio with `python -m pip install imageio` to save demos.") from exc

    args = parse_args()
    env = make_env(args)
    model = AGENTS[args.agent].load(args.model, env=env, device=args.device)
    guarded_controller = (
        GuardedPolicyController(make_guarded_config(args)) if args.guarded_policy else None
    )
    guard_state_provider = MujocoGuardStateProvider(env) if guarded_controller is not None else None
    guard_enabled = (
        guarded_controller.scenario_uses_guard(
            args.guard_scenario_name,
            args.domain_randomization_level,
        )
        if guarded_controller is not None
        else False
    )
    demo_renderer = mujoco.Renderer(env.model, height=args.render_height, width=args.render_width)
    render_cameras = args.render_cameras if args.render_cameras is not None else [args.render_camera]
    frames = []
    trajectory_rows = []

    try:
        for episode in range(args.episodes):
            obs, info = env.reset(seed=args.seed + episode)
            if guarded_controller is not None:
                guarded_controller.reset()
            frames.append(render_demo_frame(env, demo_renderer, render_cameras))
            episode_return = 0.0
            trajectory_rows.append(
                trajectory_row(
                    episode=episode + 1,
                    step=0,
                    reward=0.0,
                    episode_return=episode_return,
                    policy_action=np.zeros(3, dtype=np.float64),
                    final_action=np.zeros(3, dtype=np.float64),
                    guarded_action=None,
                    guard_enabled=guard_enabled,
                    guard_active=False,
                    guard_min_policy_steps=args.guard_min_policy_steps,
                    info=info,
                    terminated=False,
                    truncated=False,
                )
            )
            while True:
                policy_action, _ = model.predict(obs, deterministic=True)
                if guarded_controller is not None:
                    guarded_step = guarded_controller.step_with_provider(
                        guard_state_provider,
                        info,
                        np.asarray(policy_action, dtype=np.float32),
                        scenario_name=args.guard_scenario_name,
                        scenario_level=args.domain_randomization_level,
                    )
                    action = guarded_step.action
                    guarded_action = guarded_step.guarded_action
                    guard_active = guarded_step.guarded
                    guard_should_activate = guarded_step.guard_should_activate
                    guard_can_activate = guarded_step.guard_can_activate
                    guard_activated = guarded_step.guard_activated
                    guard_down_blocked = guarded_step.guard_down_blocked
                    guard_steps_since_reset = guarded_step.guard_steps_since_reset
                    guard_dist_xy = guarded_step.guard_dist_xy
                    guard_z_above_target = guarded_step.guard_z_above_target
                    guard_retry_active = guarded_step.guard_retry_active
                    guard_retry_triggered = guarded_step.guard_retry_triggered
                    guard_retry_count = guarded_step.guard_retry_count
                    guard_retry_stall_steps = guarded_step.guard_retry_stall_steps
                    guard_retry_active_steps = guarded_step.guard_retry_active_steps
                    guard_insert_latched = guarded_step.guard_insert_latched
                    guard_insert_latch_activated = guarded_step.guard_insert_latch_activated
                    guard_insert_latch_released = guarded_step.guard_insert_latch_released
                    guard_insert_latch_steps = guarded_step.guard_insert_latch_steps
                    guard_insert_latch_descent_allowed = (
                        guarded_step.guard_insert_latch_descent_allowed
                    )
                    guard_hover_active = guarded_step.guard_hover_active
                    guard_hover_stable_steps = guarded_step.guard_hover_stable_steps
                    guard_hover_descent_allowed = guarded_step.guard_hover_descent_allowed
                    guard_hover_descent_latched = guarded_step.guard_hover_descent_latched
                    guard_hover_down_blocked = guarded_step.guard_hover_down_blocked
                    guard_near_action_limited = guarded_step.guard_near_action_limited
                    guard_fixture_clearance_active = (
                        guarded_step.guard_fixture_clearance_active
                    )
                    guard_fixture_clearance_triggered = (
                        guarded_step.guard_fixture_clearance_triggered
                    )
                    guard_fixture_clearance_released = (
                        guarded_step.guard_fixture_clearance_released
                    )
                    guard_fixture_clearance_phase = guarded_step.guard_fixture_clearance_phase
                    guard_fixture_clearance_steps = guarded_step.guard_fixture_clearance_steps
                    guard_fixture_clearance_realign_steps = (
                        guarded_step.guard_fixture_clearance_realign_steps
                    )
                    guard_final_servo_active = guarded_step.guard_final_servo_active
                    guard_final_servo_triggered = guarded_step.guard_final_servo_triggered
                    guard_final_servo_recovery_triggered = (
                        guarded_step.guard_final_servo_recovery_triggered
                    )
                    guard_final_servo_exhausted = guarded_step.guard_final_servo_exhausted
                    guard_final_servo_phase = guarded_step.guard_final_servo_phase
                    guard_final_servo_phase_steps = guarded_step.guard_final_servo_phase_steps
                    guard_final_servo_stable_steps = guarded_step.guard_final_servo_stable_steps
                    guard_final_servo_stall_steps = guarded_step.guard_final_servo_stall_steps
                    guard_final_servo_retry_count = guarded_step.guard_final_servo_retry_count
                    guard_final_servo_descent_allowed = (
                        guarded_step.guard_final_servo_descent_allowed
                    )
                    guard_final_servo_down_blocked = guarded_step.guard_final_servo_down_blocked
                else:
                    action = np.asarray(policy_action, dtype=np.float32)
                    guarded_action = None
                    guard_active = False
                    guard_should_activate = False
                    guard_can_activate = False
                    guard_activated = False
                    guard_down_blocked = False
                    guard_steps_since_reset = -1
                    guard_dist_xy = float("nan")
                    guard_z_above_target = float("nan")
                    guard_retry_active = False
                    guard_retry_triggered = False
                    guard_retry_count = 0
                    guard_retry_stall_steps = 0
                    guard_retry_active_steps = 0
                    guard_insert_latched = False
                    guard_insert_latch_activated = False
                    guard_insert_latch_released = False
                    guard_insert_latch_steps = 0
                    guard_insert_latch_descent_allowed = False
                    guard_hover_active = False
                    guard_hover_stable_steps = 0
                    guard_hover_descent_allowed = False
                    guard_hover_descent_latched = False
                    guard_hover_down_blocked = False
                    guard_near_action_limited = False
                    guard_fixture_clearance_active = False
                    guard_fixture_clearance_triggered = False
                    guard_fixture_clearance_released = False
                    guard_fixture_clearance_phase = "none"
                    guard_fixture_clearance_steps = 0
                    guard_fixture_clearance_realign_steps = 0
                    guard_final_servo_active = False
                    guard_final_servo_triggered = False
                    guard_final_servo_recovery_triggered = False
                    guard_final_servo_exhausted = False
                    guard_final_servo_phase = "inactive"
                    guard_final_servo_phase_steps = 0
                    guard_final_servo_stable_steps = 0
                    guard_final_servo_stall_steps = 0
                    guard_final_servo_retry_count = 0
                    guard_final_servo_descent_allowed = False
                    guard_final_servo_down_blocked = False
                obs, reward, terminated, truncated, info = env.step(action)
                episode_return += reward
                frames.append(render_demo_frame(env, demo_renderer, render_cameras))
                trajectory_rows.append(
                    trajectory_row(
                        episode=episode + 1,
                        step=int(info["step_count"]),
                        reward=float(reward),
                        episode_return=episode_return,
                        policy_action=np.asarray(policy_action, dtype=np.float64),
                        final_action=np.asarray(action, dtype=np.float64),
                        guarded_action=guarded_action,
                        guard_enabled=guard_enabled,
                        guard_active=guard_active,
                        guard_should_activate=guard_should_activate,
                        guard_can_activate=guard_can_activate,
                        guard_activated=guard_activated,
                        guard_down_blocked=guard_down_blocked,
                        guard_steps_since_reset=guard_steps_since_reset,
                        guard_min_policy_steps=args.guard_min_policy_steps,
                        guard_dist_xy=guard_dist_xy,
                        guard_z_above_target=guard_z_above_target,
                        guard_retry_active=guard_retry_active,
                        guard_retry_triggered=guard_retry_triggered,
                        guard_retry_count=guard_retry_count,
                        guard_retry_stall_steps=guard_retry_stall_steps,
                        guard_retry_active_steps=guard_retry_active_steps,
                        guard_insert_latched=guard_insert_latched,
                        guard_insert_latch_activated=guard_insert_latch_activated,
                        guard_insert_latch_released=guard_insert_latch_released,
                        guard_insert_latch_steps=guard_insert_latch_steps,
                        guard_insert_latch_descent_allowed=guard_insert_latch_descent_allowed,
                        guard_hover_active=guard_hover_active,
                        guard_hover_stable_steps=guard_hover_stable_steps,
                        guard_hover_descent_allowed=guard_hover_descent_allowed,
                        guard_hover_descent_latched=guard_hover_descent_latched,
                        guard_hover_down_blocked=guard_hover_down_blocked,
                        guard_near_action_limited=guard_near_action_limited,
                        guard_fixture_clearance_active=guard_fixture_clearance_active,
                        guard_fixture_clearance_triggered=guard_fixture_clearance_triggered,
                        guard_fixture_clearance_released=guard_fixture_clearance_released,
                        guard_fixture_clearance_phase=guard_fixture_clearance_phase,
                        guard_fixture_clearance_steps=guard_fixture_clearance_steps,
                        guard_fixture_clearance_realign_steps=guard_fixture_clearance_realign_steps,
                        guard_final_servo_active=guard_final_servo_active,
                        guard_final_servo_triggered=guard_final_servo_triggered,
                        guard_final_servo_recovery_triggered=guard_final_servo_recovery_triggered,
                        guard_final_servo_exhausted=guard_final_servo_exhausted,
                        guard_final_servo_phase=guard_final_servo_phase,
                        guard_final_servo_phase_steps=guard_final_servo_phase_steps,
                        guard_final_servo_stable_steps=guard_final_servo_stable_steps,
                        guard_final_servo_stall_steps=guard_final_servo_stall_steps,
                        guard_final_servo_retry_count=guard_final_servo_retry_count,
                        guard_final_servo_descent_allowed=guard_final_servo_descent_allowed,
                        guard_final_servo_down_blocked=guard_final_servo_down_blocked,
                        info=info,
                        terminated=terminated,
                        truncated=truncated,
                    )
                )
                if terminated or truncated:
                    print(
                        "episode={episode} return={ret:.3f} success={success} "
                        "collision={collision} steps={steps} guard_steps={guard_steps} "
                        "retry_count={retry_count} dist_xy={dist_xy:.5f} dist_z={dist_z:.5f}".format(
                            episode=episode + 1,
                            ret=episode_return,
                            success=info["insertion_success"],
                            collision=info["collision"],
                            steps=info["step_count"],
                            guard_steps=(
                                guarded_controller.guard_steps
                                if guarded_controller is not None
                                else 0
                            ),
                            retry_count=(
                                guarded_controller.guard_retry_count
                                if guarded_controller is not None
                                else 0
                            ),
                            dist_xy=info["dist_xy"],
                            dist_z=info["dist_z"],
                        )
                    )
                    break
    finally:
        demo_renderer.close()
        env.close()

    save_demo_frames(imageio, args.output, frames, args.fps)
    if args.trajectory_output is not None:
        save_trajectory_csv(args.trajectory_output, trajectory_rows)


if __name__ == "__main__":
    main()
