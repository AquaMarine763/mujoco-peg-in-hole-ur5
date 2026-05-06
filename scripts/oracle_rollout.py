from __future__ import annotations

import argparse
from pathlib import Path

from peg_in_hole_mujoco import OracleControllerConfig, PegInHoleMujocoEnv, oracle_action


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the staged Cartesian oracle in the MuJoCo peg-in-hole env.")
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="state")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-gain", type=float, default=1.0)
    parser.add_argument("--oracle-mode", choices=["staged", "guarded_two_stage"], default="staged")
    parser.add_argument("--guarded-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guarded-max-down-action", type=float, default=0.0035)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.005)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--image-width", type=int, default=100)
    parser.add_argument("--image-height", type=int, default=100)
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    env = PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode=args.observation_mode,
        image_width=args.image_width,
        image_height=args.image_height,
        max_steps=args.max_steps,
        success_xy_tolerance=args.success_xy_tolerance,
        success_z_tolerance=args.success_z_tolerance,
    )
    oracle_config = OracleControllerConfig(
        mode=args.oracle_mode,
        action_gain=args.action_gain,
        guarded_align_xy_tolerance=args.guarded_align_xy_tolerance,
        guarded_insert_xy_tolerance=args.guarded_insert_xy_tolerance,
        guarded_retract_xy_tolerance=args.guarded_retract_xy_tolerance,
        guarded_preinsert_height=args.guarded_preinsert_height,
        guarded_max_xy_action=args.guarded_max_xy_action,
        guarded_max_down_action=args.guarded_max_down_action,
        guarded_max_up_action=args.guarded_max_up_action,
        guarded_prediction_steps=args.guarded_prediction_steps,
    )

    successes = 0
    collisions = 0
    try:
        for episode in range(1, args.episodes + 1):
            obs, info = env.reset(seed=args.seed + episode)
            del obs
            episode_return = 0.0
            while True:
                action = oracle_action(env, info, oracle_config)
                obs, reward, terminated, truncated, info = env.step(action)
                del obs
                episode_return += reward
                if terminated or truncated:
                    break

            successes += int(info["insertion_success"])
            collisions += int(info["collision"])
            print(
                "episode={episode} steps={steps} reward={reward:.3f} "
                "success={success} collision={collision} dist_xy={dist_xy:.4f} dist_z={dist_z:.4f}".format(
                    episode=episode,
                    steps=info["step_count"],
                    reward=episode_return,
                    success=info["insertion_success"],
                    collision=info["collision"],
                    dist_xy=info["dist_xy"],
                    dist_z=info["dist_z"],
                )
            )
    finally:
        env.close()

    print(
        "episodes={episodes} success_rate={success_rate:.3f} collision_rate={collision_rate:.3f}".format(
            episodes=args.episodes,
            success_rate=successes / max(args.episodes, 1),
            collision_rate=collisions / max(args.episodes, 1),
        )
    )


if __name__ == "__main__":
    main()
