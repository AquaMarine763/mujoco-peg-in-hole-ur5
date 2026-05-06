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
    parser.add_argument("--geometry-hole-half-size-range", nargs=2, type=float, default=(0.025, 0.029))
    parser.add_argument("--geometry-peg-radius-range", nargs=2, type=float, default=(0.0115, 0.0125))
    parser.add_argument("--contact-friction-multiplier-range", nargs=2, type=float, default=(0.7, 1.3))
    parser.add_argument("--contact-solref-time-multiplier-range", nargs=2, type=float, default=(0.8, 1.25))
    parser.add_argument("--contact-solref-damping-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--contact-solimp-width-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--dynamics-joint-damping-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--dynamics-actuator-kp-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--target-low", nargs=3, type=float, default=(0.50, 0.00, 0.65))
    parser.add_argument("--target-high", nargs=3, type=float, default=(0.60, 0.10, 0.65))
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
    parser.add_argument("--guard-action-gain", type=float, default=1.0)
    parser.add_argument("--guarded-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guarded-max-down-action", type=float, default=0.0035)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.005)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)
    return parser.parse_args()


def make_env(args: argparse.Namespace) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode=args.observation_mode,
        image_width=args.width,
        image_height=args.height,
        include_near_hole_crop=args.include_near_hole_crop,
        near_hole_crop_size=args.near_hole_crop_size,
        max_steps=args.max_steps,
        action_scale=args.action_scale,
        target_low=tuple(args.target_low),
        target_high=tuple(args.target_high),
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
        guarded_step = self.controller.step(
            self.env,
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
