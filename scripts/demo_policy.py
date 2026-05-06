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
        render_mode="rgb_array",
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
        "success": bool(info.get("insertion_success", False)),
        "collision": bool(info.get("collision", False)),
        "dist_xy": float(info.get("dist_xy", float("nan"))),
        "dist_z": float(info.get("dist_z", float("nan"))),
        "shaped_distance": float(info.get("shaped_distance", float("nan"))),
        "desired_z": float(info.get("desired_z", float("nan"))),
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
                        info=info,
                        terminated=terminated,
                        truncated=truncated,
                    )
                )
                if terminated or truncated:
                    print(
                        "episode={episode} return={ret:.3f} success={success} "
                        "collision={collision} steps={steps} guard_steps={guard_steps} "
                        "dist_xy={dist_xy:.5f} dist_z={dist_z:.5f}".format(
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
                            dist_xy=info["dist_xy"],
                            dist_z=info["dist_z"],
                        )
                    )
                    break
    finally:
        demo_renderer.close()
        env.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(args.output, frames, fps=args.fps)
    print(f"saved demo to {args.output}")
    if args.trajectory_output is not None:
        save_trajectory_csv(args.trajectory_output, trajectory_rows)


if __name__ == "__main__":
    main()
