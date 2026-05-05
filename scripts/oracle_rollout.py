from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from peg_in_hole_mujoco import PegInHoleMujocoEnv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the staged Cartesian oracle in the MuJoCo peg-in-hole env.")
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="state")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-gain", type=float, default=1.0)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--image-width", type=int, default=100)
    parser.add_argument("--image-height", type=int, default=100)
    return parser.parse_args()


def oracle_action(env: PegInHoleMujocoEnv, info: dict, action_gain: float) -> np.ndarray:
    tip = info["peg_tip_pos"].astype(np.float64)
    target = info["target_pos"].astype(np.float64)
    desired = np.asarray([target[0], target[1], info["desired_z"]], dtype=np.float64)
    action = action_gain * (desired - tip)
    return np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32)


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

    successes = 0
    collisions = 0
    try:
        for episode in range(1, args.episodes + 1):
            obs, info = env.reset(seed=args.seed + episode)
            del obs
            episode_return = 0.0
            while True:
                action = oracle_action(env, info, args.action_gain)
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
