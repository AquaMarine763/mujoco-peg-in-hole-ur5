from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from peg_in_hole_mujoco import PegInHoleMujocoEnv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run random actions in the MuJoCo peg-in-hole env.")
    parser.add_argument("--observation-mode", choices=["image", "state"], default="state")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--domain-randomization", action="store_true")
    parser.add_argument("--save-first-frame", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    env = PegInHoleMujocoEnv(
        observation_mode=args.observation_mode,
        randomize_domain=args.domain_randomization,
        render_mode="rgb_array",
    )

    rng = np.random.default_rng(args.seed)
    total_steps = 0
    try:
        for episode in range(1, args.episodes + 1):
            obs, info = env.reset(seed=args.seed + episode)
            del obs

            if episode == 1 and args.save_first_frame is not None:
                frame = env.render()
                args.save_first_frame.parent.mkdir(parents=True, exist_ok=True)
                np.save(args.save_first_frame, frame)

            episode_reward = 0.0
            while True:
                action = rng.uniform(env.action_space.low, env.action_space.high)
                obs, reward, terminated, truncated, info = env.step(action)
                del obs
                episode_reward += reward
                total_steps += 1
                if terminated or truncated:
                    break

            print(
                "episode={episode} steps={steps} reward={reward:.3f} "
                "success={success} collision={collision} dist_xy={dist_xy:.4f} dist_z={dist_z:.4f}".format(
                    episode=episode,
                    steps=info["step_count"],
                    reward=episode_reward,
                    success=info["insertion_success"],
                    collision=info["collision"],
                    dist_xy=info["dist_xy"],
                    dist_z=info["dist_z"],
                )
            )
    finally:
        env.close()

    print(f"total_steps={total_steps}")


if __name__ == "__main__":
    main()
