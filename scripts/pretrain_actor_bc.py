from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from stable_baselines3 import SAC

from peg_in_hole_mujoco import PegInHoleMujocoEnv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Behavior-clone the SAC actor from a staged oracle.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=50_000)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--noise-std", type=float, default=0.001)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=20_000)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--target-low", nargs=3, type=float, default=(0.50, 0.00, 0.65))
    parser.add_argument("--target-high", nargs=3, type=float, default=(0.60, 0.10, 0.65))
    parser.add_argument("--success-xy-tolerance", type=float, default=0.015)
    parser.add_argument("--success-z-tolerance", type=float, default=0.045)
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
        observation_mode="state",
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
    )


def oracle_action(env: PegInHoleMujocoEnv, info: dict) -> np.ndarray:
    tip = info["peg_tip_pos"].astype(np.float64)
    target = info["target_pos"].astype(np.float64)
    desired = np.asarray([target[0], target[1], info["desired_z"]], dtype=np.float64)
    action = np.clip(desired - tip, -env.action_scale, env.action_scale)
    return action.astype(np.float32)


def collect_dataset(args: argparse.Namespace, env: PegInHoleMujocoEnv) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(args.seed)
    observations = []
    actions = []
    episode = 0
    obs, info = env.reset(seed=args.seed + episode)

    while len(observations) < args.samples:
        action = oracle_action(env, info)
        observations.append(obs.astype(np.float32))
        actions.append((action / env.action_scale).astype(np.float32))

        noisy_action = action + rng.normal(0.0, args.noise_std, size=action.shape)
        noisy_action = np.clip(noisy_action, env.action_space.low, env.action_space.high)
        obs, _, terminated, truncated, info = env.step(noisy_action.astype(np.float32))
        if terminated or truncated:
            episode += 1
            obs, info = env.reset(seed=args.seed + episode)

    return np.asarray(observations, dtype=np.float32), np.asarray(actions, dtype=np.float32)


def main() -> None:
    args = parse_args()
    env = make_env(args)
    model = SAC.load(args.model, env=env, device=args.device)

    observations, actions = collect_dataset(args, env)
    device = model.device
    obs_tensor = torch.as_tensor(observations, device=device)
    action_tensor = torch.as_tensor(actions, device=device)

    actor = model.policy.actor
    actor.train()
    optimizer = torch.optim.Adam(actor.parameters(), lr=args.learning_rate)
    rng = np.random.default_rng(args.seed)

    for epoch in range(args.epochs):
        indices = rng.permutation(len(observations))
        losses = []
        for start in range(0, len(indices), args.batch_size):
            batch_indices = indices[start : start + args.batch_size]
            pred = actor(obs_tensor[batch_indices], deterministic=True)
            loss = F.mse_loss(pred, action_tensor[batch_indices])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        print(f"epoch={epoch + 1} loss={np.mean(losses):.6f}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    model.save(args.output)
    env.close()
    print(f"saved behavior-cloned model to {args.output}")


if __name__ == "__main__":
    main()
