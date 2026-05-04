from __future__ import annotations

import argparse
from pathlib import Path

from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco import PegInHoleMujocoEnv


AGENTS = {
    "sac": SAC,
    "ppo": PPO,
    "a2c": A2C,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained SB3 policy.")
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--episodes", type=int, default=100)
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
    parser.add_argument("--success-xy-tolerance", type=float, default=0.02)
    parser.add_argument("--success-z-tolerance", type=float, default=0.06)
    parser.add_argument("--approach-xy-tolerance", type=float, default=0.06)
    parser.add_argument("--approach-height", type=float, default=0.08)
    parser.add_argument("--staged-xy-weight", type=float, default=2.0)
    parser.add_argument("--staged-z-weight", type=float, default=1.0)
    parser.add_argument("--success-bonus", type=float, default=50.0)
    parser.add_argument("--collision-penalty", type=float, default=150.0)
    parser.add_argument("--timeout-penalty", type=float, default=10.0)
    parser.add_argument("--progress-reward-scale", type=float, default=10.0)
    parser.add_argument("--distance-reward-scale", type=float, default=1.0)
    parser.add_argument("--action-penalty-scale", type=float, default=0.002)
    parser.add_argument("--action-alignment-scale", type=float, default=0.5)
    return parser.parse_args()


def make_env(args: argparse.Namespace) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        observation_mode=args.observation_mode,
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


def main() -> None:
    args = parse_args()
    env = make_env(args)
    model = AGENTS[args.agent].load(args.model, env=env, device=args.device)

    successes = 0
    collisions = 0
    returns = []

    try:
        for episode in range(args.episodes):
            obs, info = env.reset(seed=args.seed + episode)
            del info
            episode_return = 0.0
            while True:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_return += reward
                if terminated or truncated:
                    break
            successes += int(info["insertion_success"])
            collisions += int(info["collision"])
            returns.append(episode_return)
            print(
                "episode={episode} return={ret:.3f} success={success} "
                "collision={collision} steps={steps}".format(
                    episode=episode + 1,
                    ret=episode_return,
                    success=info["insertion_success"],
                    collision=info["collision"],
                    steps=info["step_count"],
                )
            )
    finally:
        env.close()

    print(f"episodes={args.episodes}")
    print(f"success_rate={successes / args.episodes:.3f}")
    print(f"collision_rate={collisions / args.episodes:.3f}")
    print(f"mean_return={sum(returns) / len(returns):.3f}")


if __name__ == "__main__":
    main()
