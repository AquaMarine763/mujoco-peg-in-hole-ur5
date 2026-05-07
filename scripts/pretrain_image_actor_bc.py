from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from stable_baselines3 import SAC

from peg_in_hole_mujoco import PegInHoleMujocoEnv
from peg_in_hole_mujoco.sim_config import parse_args_with_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Behavior-clone an image SAC actor from expert image/action data.")
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--validation-split", type=float, default=0.1)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=40_000)
    parser.add_argument("--image-width", type=int, default=100)
    parser.add_argument("--image-height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
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
    parser.add_argument("--buffer-size", type=int, default=100_000)
    parser.add_argument("--learning-starts", type=int, default=1_000)
    parser.add_argument("--ent-coef", default="auto_0.01")
    return parse_args_with_config(parser)


def make_env(args: argparse.Namespace) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode="image",
        image_width=args.image_width,
        image_height=args.image_height,
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
    )


def load_or_create_model(args: argparse.Namespace, env: PegInHoleMujocoEnv) -> SAC:
    if args.model is not None:
        return SAC.load(args.model, env=env, device=args.device)
    return SAC(
        "MultiInputPolicy",
        env,
        device=args.device,
        learning_rate=args.learning_rate,
        buffer_size=args.buffer_size,
        learning_starts=args.learning_starts,
        ent_coef=args.ent_coef,
        seed=args.seed,
        verbose=1,
    )


def center_crop_images(images: np.ndarray, crop_size: int) -> np.ndarray:
    if crop_size <= 0:
        raise ValueError("crop_size must be positive.")
    if images.ndim != 4 or images.shape[-1] != 1:
        raise ValueError(f"Expected image batch shape (N, H, W, 1), got {images.shape}")
    height, width = images.shape[1:3]
    source_size = min(crop_size, height, width)
    y0 = max(0, (height - source_size) // 2)
    x0 = max(0, (width - source_size) // 2)
    crop = images[:, y0 : y0 + source_size, x0 : x0 + source_size, :]
    if crop.shape[1] == crop_size and crop.shape[2] == crop_size:
        return np.ascontiguousarray(crop)
    y_idx = np.linspace(0, crop.shape[1] - 1, crop_size).round().astype(np.int64)
    x_idx = np.linspace(0, crop.shape[2] - 1, crop_size).round().astype(np.int64)
    return np.ascontiguousarray(crop[:, y_idx][:, :, x_idx, :])


def load_near_hole_crops(dataset: np.lib.npyio.NpzFile, images: np.ndarray, crop_size: int) -> np.ndarray:
    if "near_hole_crops" in dataset:
        crops = dataset["near_hole_crops"]
        if crops.dtype != np.uint8:
            raise ValueError(f"Expected uint8 near_hole_crops, got {crops.dtype}")
        return crops
    return center_crop_images(images, crop_size)


def to_actor_obs(
    images: np.ndarray,
    near_hole_crops: np.ndarray | None,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    tensor = torch.as_tensor(images, device=device)
    if tensor.ndim != 4 or tensor.shape[-1] != 1:
        raise ValueError(f"Expected image batch shape (N, H, W, 1), got {tuple(tensor.shape)}")
    obs = {"cam_image": tensor.permute(0, 3, 1, 2)}
    if near_hole_crops is not None:
        crop_tensor = torch.as_tensor(near_hole_crops, device=device)
        if crop_tensor.ndim != 4 or crop_tensor.shape[-1] != 1:
            raise ValueError(
                f"Expected crop batch shape (N, H, W, 1), got {tuple(crop_tensor.shape)}"
            )
        obs["near_hole_crop"] = crop_tensor.permute(0, 3, 1, 2)
    return obs


def batch_loss(
    actor: torch.nn.Module,
    images: np.ndarray,
    near_hole_crops: np.ndarray | None,
    actions: np.ndarray,
    indices: np.ndarray,
    device: torch.device,
) -> torch.Tensor:
    crop_batch = near_hole_crops[indices] if near_hole_crops is not None else None
    obs = to_actor_obs(images[indices], crop_batch, device)
    target = torch.as_tensor(actions[indices], dtype=torch.float32, device=device)
    pred = actor(obs, deterministic=True)
    return F.mse_loss(pred, target)


def mean_loss(
    actor: torch.nn.Module,
    images: np.ndarray,
    near_hole_crops: np.ndarray | None,
    actions: np.ndarray,
    indices: np.ndarray,
    batch_size: int,
    device: torch.device,
) -> float:
    losses = []
    actor.eval()
    with torch.no_grad():
        for start in range(0, len(indices), batch_size):
            batch_indices = indices[start : start + batch_size]
            loss = batch_loss(actor, images, near_hole_crops, actions, batch_indices, device)
            losses.append(float(loss.detach().cpu()))
    actor.train()
    return float(np.mean(losses)) if losses else 0.0


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    dataset = np.load(args.dataset)
    images = dataset["cam_images"]
    near_hole_crops = (
        load_near_hole_crops(dataset, images, args.near_hole_crop_size)
        if args.include_near_hole_crop
        else None
    )
    actions = dataset["actions"].astype(np.float32)
    if images.dtype != np.uint8:
        raise ValueError(f"Expected uint8 cam_images, got {images.dtype}")
    if actions.ndim != 2 or actions.shape[1] != 3:
        raise ValueError(f"Expected actions shape (N, 3), got {actions.shape}")

    env = make_env(args)
    model = load_or_create_model(args, env)
    actor = model.policy.actor
    device = model.device
    optimizer = torch.optim.Adam(actor.parameters(), lr=args.learning_rate)

    indices = rng.permutation(len(images))
    val_size = int(len(indices) * args.validation_split)
    val_indices = indices[:val_size]
    train_indices = indices[val_size:]
    if len(train_indices) == 0:
        raise ValueError("Training split is empty; reduce --validation-split or add samples.")

    actor.train()
    for epoch in range(args.epochs):
        epoch_indices = rng.permutation(train_indices)
        train_losses = []
        for start in range(0, len(epoch_indices), args.batch_size):
            batch_indices = epoch_indices[start : start + args.batch_size]
            loss = batch_loss(actor, images, near_hole_crops, actions, batch_indices, device)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.detach().cpu()))

        val_loss = mean_loss(
            actor,
            images,
            near_hole_crops,
            actions,
            val_indices,
            args.batch_size,
            device,
        )
        print(
            f"epoch={epoch + 1} "
            f"train_loss={np.mean(train_losses):.6f} "
            f"val_loss={val_loss:.6f}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    model.save(args.output)
    env.close()
    print(f"saved image behavior-cloned model to {args.output}")


if __name__ == "__main__":
    main()
