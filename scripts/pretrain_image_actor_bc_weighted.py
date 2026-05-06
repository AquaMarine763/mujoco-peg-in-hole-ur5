from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from stable_baselines3 import SAC

from peg_in_hole_mujoco import PegInHoleMujocoEnv


@dataclass
class LoadedDataset:
    path: Path
    images: np.ndarray
    near_hole_crops: np.ndarray | None
    actions: np.ndarray
    train_indices: np.ndarray
    val_indices: np.ndarray


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Behavior-clone an image SAC actor from weighted expert datasets."
    )
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--datasets", nargs="+", type=Path, required=True)
    parser.add_argument("--dataset-weights", nargs="+", type=float, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--samples-per-epoch", type=int, default=300_000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=5e-6)
    parser.add_argument("--validation-split", type=float, default=0.05)
    parser.add_argument("--validation-batches", type=int, default=20)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=410_000)
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
    return parser.parse_args()


def normalize_weights(weights: list[float], count: int) -> np.ndarray:
    if len(weights) != count:
        raise ValueError("--dataset-weights must match --datasets length.")
    array = np.asarray(weights, dtype=np.float64)
    if np.any(array < 0.0) or float(array.sum()) <= 0.0:
        raise ValueError("--dataset-weights must be non-negative and sum to a positive value.")
    return array / array.sum()


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


def load_or_derive_crops(
    dataset: np.lib.npyio.NpzFile,
    images: np.ndarray,
    crop_size: int,
) -> np.ndarray:
    if "near_hole_crops" in dataset:
        crops = np.asarray(dataset["near_hole_crops"], dtype=np.uint8)
        if crops.ndim != 4 or crops.shape[-1] != 1:
            raise ValueError(f"Expected near_hole_crops shape (N, H, W, 1), got {crops.shape}")
        return crops
    return center_crop_images(images, crop_size)


def load_dataset(
    path: Path,
    rng: np.random.Generator,
    validation_split: float,
    include_near_hole_crop: bool,
    near_hole_crop_size: int,
) -> LoadedDataset:
    with np.load(path) as dataset:
        images = np.asarray(dataset["cam_images"], dtype=np.uint8)
        near_hole_crops = (
            load_or_derive_crops(dataset, images, near_hole_crop_size)
            if include_near_hole_crop
            else None
        )
        actions = np.asarray(dataset["actions"], dtype=np.float32)
    if images.ndim != 4 or images.shape[-1] != 1:
        raise ValueError(f"{path}: expected cam_images shape (N, H, W, 1), got {images.shape}")
    if actions.ndim != 2 or actions.shape[1] != 3:
        raise ValueError(f"{path}: expected actions shape (N, 3), got {actions.shape}")

    indices = rng.permutation(len(images))
    val_size = int(len(indices) * validation_split)
    val_indices = indices[:val_size]
    train_indices = indices[val_size:]
    if len(train_indices) == 0:
        raise ValueError(f"{path}: training split is empty.")
    if len(val_indices) == 0:
        val_indices = train_indices
    return LoadedDataset(path, images, near_hole_crops, actions, train_indices, val_indices)


def to_actor_obs(
    images: np.ndarray,
    near_hole_crops: np.ndarray | None,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    tensor = torch.as_tensor(images, device=device)
    obs = {"cam_image": tensor.permute(0, 3, 1, 2)}
    if near_hole_crops is not None:
        crop_tensor = torch.as_tensor(near_hole_crops, device=device)
        obs["near_hole_crop"] = crop_tensor.permute(0, 3, 1, 2)
    return obs


def batch_loss(
    actor: torch.nn.Module,
    dataset: LoadedDataset,
    indices: np.ndarray,
    device: torch.device,
) -> torch.Tensor:
    crop_batch = (
        dataset.near_hole_crops[indices]
        if dataset.near_hole_crops is not None
        else None
    )
    obs = to_actor_obs(dataset.images[indices], crop_batch, device)
    target = torch.as_tensor(dataset.actions[indices], dtype=torch.float32, device=device)
    pred = actor(obs, deterministic=True)
    return F.mse_loss(pred, target)


def weighted_validation_loss(
    actor: torch.nn.Module,
    datasets: list[LoadedDataset],
    dataset_weights: np.ndarray,
    batch_size: int,
    validation_batches: int,
    rng: np.random.Generator,
    device: torch.device,
) -> float:
    losses: list[float] = []
    actor.eval()
    with torch.no_grad():
        for dataset, weight in zip(datasets, dataset_weights):
            dataset_losses = []
            for _ in range(validation_batches):
                indices = rng.choice(dataset.val_indices, size=batch_size, replace=True)
                loss = batch_loss(actor, dataset, indices, device)
                dataset_losses.append(float(loss.detach().cpu()))
            losses.append(float(weight) * float(np.mean(dataset_losses)))
    actor.train()
    return float(np.sum(losses))


def main() -> None:
    args = parse_args()
    if args.epochs <= 0:
        raise ValueError("--epochs must be positive.")
    if args.samples_per_epoch <= 0:
        raise ValueError("--samples-per-epoch must be positive.")

    rng = np.random.default_rng(args.seed)
    weights = (
        normalize_weights(args.dataset_weights, len(args.datasets))
        if args.dataset_weights is not None
        else normalize_weights([1.0] * len(args.datasets), len(args.datasets))
    )
    datasets = [
        load_dataset(
            path,
            rng,
            args.validation_split,
            args.include_near_hole_crop,
            args.near_hole_crop_size,
        )
        for path in args.datasets
    ]
    for dataset, weight in zip(datasets, weights):
        print(
            f"dataset={dataset.path} samples={len(dataset.images)} "
            f"train={len(dataset.train_indices)} val={len(dataset.val_indices)} weight={weight:.3f}"
        )

    env = make_env(args)
    model = load_or_create_model(args, env)
    actor = model.policy.actor
    device = model.device
    optimizer = torch.optim.Adam(actor.parameters(), lr=args.learning_rate)
    batches_per_epoch = int(np.ceil(args.samples_per_epoch / args.batch_size))

    actor.train()
    for epoch in range(args.epochs):
        train_losses = []
        for _ in range(batches_per_epoch):
            dataset_index = int(rng.choice(len(datasets), p=weights))
            dataset = datasets[dataset_index]
            indices = rng.choice(dataset.train_indices, size=args.batch_size, replace=True)
            loss = batch_loss(actor, dataset, indices, device)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.detach().cpu()))

        val_loss = weighted_validation_loss(
            actor,
            datasets,
            weights,
            args.batch_size,
            args.validation_batches,
            rng,
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
    print(f"saved weighted image behavior-cloned model to {args.output}")


if __name__ == "__main__":
    main()
