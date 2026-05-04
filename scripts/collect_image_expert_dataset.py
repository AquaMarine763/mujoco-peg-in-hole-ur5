from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from stable_baselines3 import SAC

from peg_in_hole_mujoco import PegInHoleMujocoEnv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect wrist-camera images with expert Cartesian actions.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=50_000)
    parser.add_argument("--expert-model", type=Path, default=None)
    parser.add_argument("--rollout-noise-std", type=float, default=0.0005)
    parser.add_argument("--seed", type=int, default=30_000)
    parser.add_argument("--compressed", action="store_true")
    parser.add_argument("--domain-randomization", action="store_true")
    parser.add_argument(
        "--domain-randomization-level",
        choices=["none", "visual", "visual_camera", "visual_camera_control", "full"],
        default="none",
    )
    parser.add_argument("--image-width", type=int, default=100)
    parser.add_argument("--image-height", type=int, default=100)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
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
    return parser.parse_args()


def make_env(args: argparse.Namespace) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        observation_mode="image",
        image_width=args.image_width,
        image_height=args.image_height,
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
    )


def oracle_action(env: PegInHoleMujocoEnv, info: dict) -> np.ndarray:
    tip = info["peg_tip_pos"].astype(np.float64)
    target = info["target_pos"].astype(np.float64)
    desired = np.asarray([target[0], target[1], info["desired_z"]], dtype=np.float64)
    return np.clip(desired - tip, -env.action_scale, env.action_scale).astype(np.float32)


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    env = make_env(args)
    expert = SAC.load(args.expert_model, device="cpu") if args.expert_model is not None else None

    images: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    raw_actions: list[np.ndarray] = []
    target_positions: list[np.ndarray] = []
    peg_tip_positions: list[np.ndarray] = []
    desired_zs: list[float] = []
    episode_ids: list[int] = []
    step_ids: list[int] = []
    successes = 0
    collisions = 0
    episodes = 0

    obs, info = env.reset(seed=args.seed)
    try:
        while len(images) < args.samples:
            if expert is None:
                action = oracle_action(env, info)
            else:
                state_obs = env._get_state_obs()
                action, _ = expert.predict(state_obs, deterministic=True)
                action = np.asarray(action, dtype=np.float32)

            images.append(obs["cam_image"].copy())
            raw_actions.append(action.copy())
            actions.append((action / env.action_scale).astype(np.float32))
            target_positions.append(info["target_pos"].copy())
            peg_tip_positions.append(info["peg_tip_pos"].copy())
            desired_zs.append(float(info["desired_z"]))
            episode_ids.append(episodes)
            step_ids.append(int(info["step_count"]))

            rollout_action = action + rng.normal(0.0, args.rollout_noise_std, size=action.shape)
            rollout_action = np.clip(rollout_action, env.action_space.low, env.action_space.high)
            obs, _, terminated, truncated, info = env.step(rollout_action.astype(np.float32))

            if terminated or truncated:
                successes += int(info["insertion_success"])
                collisions += int(info["collision"])
                episodes += 1
                obs, info = env.reset(seed=args.seed + episodes)
    finally:
        env.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    arrays = {
        "cam_images": np.asarray(images, dtype=np.uint8),
        "actions": np.asarray(actions, dtype=np.float32),
        "raw_actions": np.asarray(raw_actions, dtype=np.float32),
        "target_pos": np.asarray(target_positions, dtype=np.float32),
        "peg_tip_pos": np.asarray(peg_tip_positions, dtype=np.float32),
        "desired_z": np.asarray(desired_zs, dtype=np.float32),
        "episode_id": np.asarray(episode_ids, dtype=np.int32),
        "step_id": np.asarray(step_ids, dtype=np.int32),
    }
    if args.compressed:
        np.savez_compressed(args.output, **arrays)
    else:
        np.savez(args.output, **arrays)

    metadata = {
        "samples": len(images),
        "episodes_completed": episodes,
        "successes": successes,
        "collisions": collisions,
        "expert": "oracle" if expert is None else str(args.expert_model),
        "rollout_noise_std": args.rollout_noise_std,
        "success_xy_tolerance": args.success_xy_tolerance,
        "success_z_tolerance": args.success_z_tolerance,
        "domain_randomization": args.domain_randomization,
        "domain_randomization_level": args.domain_randomization_level,
        "target_low": list(args.target_low),
        "target_high": list(args.target_high),
    }
    metadata_path = args.output.with_suffix(args.output.suffix + ".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved dataset to {args.output}")
    print(f"saved metadata to {metadata_path}")
    print(
        "episodes_completed={episodes} success_rate={success_rate:.3f} "
        "collision_rate={collision_rate:.3f}".format(
            episodes=episodes,
            success_rate=successes / max(episodes, 1),
            collision_rate=collisions / max(episodes, 1),
        )
    )


if __name__ == "__main__":
    main()
