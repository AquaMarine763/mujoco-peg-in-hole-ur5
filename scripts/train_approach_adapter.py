from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from peg_in_hole_mujoco.approach_adapter import (
    ApproachAdapterConfig,
    ApproachAdapterNet,
    save_adapter_checkpoint,
)
from peg_in_hole_mujoco.sim_config import parse_args_with_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a gated high-start approach residual adapter."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--extra-datasets",
        type=Path,
        nargs="*",
        default=[],
        help="Optional additional datasets concatenated after applying the same filters.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--validation-split", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=651_000)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--phase", default="early_approach_assist")
    parser.add_argument("--trigger-only", action="store_true")
    parser.add_argument("--xy-only", action="store_true")
    parser.add_argument(
        "--use-full-image",
        action="store_true",
        help="Use both cam_images and near_hole_crops. Default keeps v1 crop-only behavior.",
    )
    parser.add_argument(
        "--target-source",
        choices=["correction", "raw_action"],
        default="correction",
    )
    parser.add_argument("--target-scale", type=float, default=1.0)
    return parse_args_with_config(parser)


def load_arrays(
    args: argparse.Namespace,
) -> tuple[np.ndarray | None, np.ndarray, np.ndarray, np.ndarray]:
    dataset_paths = [args.dataset, *args.extra_datasets]
    image_parts: list[np.ndarray] = []
    crop_parts: list[np.ndarray] = []
    control_parts: list[np.ndarray] = []
    target_parts: list[np.ndarray] = []
    for path in dataset_paths:
        images, crops, control_state, targets = load_dataset_arrays(args, path)
        if images is not None:
            image_parts.append(images)
        crop_parts.append(crops)
        control_parts.append(control_state)
        target_parts.append(targets)
    images = np.concatenate(image_parts, axis=0) if image_parts else None
    return (
        images,
        np.concatenate(crop_parts, axis=0),
        np.concatenate(control_parts, axis=0),
        np.concatenate(target_parts, axis=0),
    )


def load_dataset_arrays(
    args: argparse.Namespace,
    path: Path,
) -> tuple[np.ndarray | None, np.ndarray, np.ndarray, np.ndarray]:
    with np.load(path) as dataset:
        if args.use_full_image and "cam_images" not in dataset:
            raise ValueError(f"{path}: expected cam_images array.")
        if "near_hole_crops" not in dataset:
            raise ValueError(f"{path}: expected near_hole_crops array.")
        if "control_state" not in dataset:
            raise ValueError(f"{path}: expected control_state array.")
        if args.target_source == "raw_action":
            if "raw_actions" not in dataset:
                raise ValueError(f"{path}: expected raw_actions array.")
            targets = np.asarray(dataset["raw_actions"], dtype=np.float32)
        elif "correction_raw_actions" in dataset:
            targets = np.asarray(dataset["correction_raw_actions"], dtype=np.float32)
        elif "raw_actions" in dataset and "policy_raw_actions" in dataset:
            targets = (
                np.asarray(dataset["raw_actions"], dtype=np.float32)
                - np.asarray(dataset["policy_raw_actions"], dtype=np.float32)
            )
        else:
            raise ValueError(
                f"{path}: expected correction_raw_actions or raw/policy raw actions."
            )
        images = np.asarray(dataset["cam_images"], dtype=np.uint8) if args.use_full_image else None
        crops = np.asarray(dataset["near_hole_crops"], dtype=np.uint8)
        control_state = np.asarray(dataset["control_state"], dtype=np.float32)
        mask = np.ones(len(crops), dtype=bool)
        if "recovery_phase" in dataset and args.phase:
            phases = np.asarray(dataset["recovery_phase"]).astype(str)
            mask &= phases == str(args.phase)
        if args.trigger_only and "early_approach_assist_trigger_window" in dataset:
            mask &= np.asarray(dataset["early_approach_assist_trigger_window"], dtype=bool)
    if not np.any(mask):
        raise ValueError("No samples remain after phase/window filtering.")
    if images is not None:
        images = images[mask]
    crops = crops[mask]
    control_state = control_state[mask]
    targets = targets[mask] * float(args.target_scale)
    if args.xy_only:
        targets[:, 2] = 0.0
    return images, crops, control_state, targets


def make_splits(sample_count: int, validation_split: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    indices = rng.permutation(sample_count)
    val_count = int(sample_count * validation_split)
    if sample_count > 1:
        val_count = max(1, min(val_count, sample_count - 1))
    val_indices = indices[:val_count]
    train_indices = indices[val_count:] if val_count else indices
    return train_indices, val_indices


def make_loader(
    images: np.ndarray | None,
    crops: np.ndarray,
    control_state: np.ndarray,
    targets: np.ndarray,
    indices: np.ndarray,
    batch_size: int,
    shuffle: bool,
) -> DataLoader:
    crop_tensor = image_array_to_tensor(crops[indices])
    control_tensor = torch.as_tensor(control_state[indices], dtype=torch.float32)
    target_tensor = torch.as_tensor(targets[indices], dtype=torch.float32)
    if images is not None:
        image_tensor = image_array_to_tensor(images[indices])
        dataset = TensorDataset(image_tensor, crop_tensor, control_tensor, target_tensor)
    else:
        dataset = TensorDataset(crop_tensor, control_tensor, target_tensor)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
    )


def image_array_to_tensor(images: np.ndarray) -> torch.Tensor:
    tensor = torch.as_tensor(images)
    if tensor.ndim != 4:
        raise ValueError(f"Expected image batch rank 4, got {tuple(tensor.shape)}.")
    if tensor.shape[1] in (1, 3, 4):
        return tensor
    return tensor.permute(0, 3, 1, 2)


def predict_batch(
    net: ApproachAdapterNet,
    batch: tuple[torch.Tensor, ...],
    device: torch.device,
    control_mean: torch.Tensor,
    control_std: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    if len(batch) == 4:
        image, crop, control_state, target = batch
        image = image.to(device)
    else:
        crop, control_state, target = batch
        image = None
    crop = crop.to(device)
    control_state = (control_state.to(device) - control_mean) / control_std
    target = target.to(device)
    pred = net(crop, control_state, image=image)
    return pred, target


def evaluate(
    net: ApproachAdapterNet,
    loader: DataLoader,
    device: torch.device,
    control_mean: torch.Tensor,
    control_std: torch.Tensor,
) -> float:
    net.eval()
    losses: list[float] = []
    with torch.no_grad():
        for batch in loader:
            pred, target = predict_batch(net, batch, device, control_mean, control_std)
            losses.append(float(F.mse_loss(pred, target).detach().cpu()))
    net.train()
    return float(np.mean(losses)) if losses else float("nan")


def main() -> None:
    args = parse_args()
    if args.epochs <= 0:
        raise ValueError("--epochs must be positive.")
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be positive.")
    if not 0.0 <= args.validation_split < 1.0:
        raise ValueError("--validation-split must be in [0, 1).")

    torch.manual_seed(args.seed)
    images, crops, control_state, targets = load_arrays(args)
    train_indices, val_indices = make_splits(
        len(crops),
        args.validation_split,
        args.seed,
    )
    control_mean_np = control_state[train_indices].mean(axis=0).astype(np.float32)
    control_std_np = control_state[train_indices].std(axis=0).astype(np.float32)
    control_std_np = np.maximum(control_std_np, 1e-6)
    device = torch.device(args.device)
    control_mean = torch.as_tensor(control_mean_np, dtype=torch.float32, device=device).reshape(1, -1)
    control_std = torch.as_tensor(control_std_np, dtype=torch.float32, device=device).reshape(1, -1)

    config = ApproachAdapterConfig(
        crop_channels=int(crops.shape[-1]),
        control_dim=int(control_state.shape[1]),
        hidden_dim=int(args.hidden_dim),
        image_channels=int(images.shape[-1]) if images is not None else 0,
        use_full_image=bool(images is not None),
    )
    net = ApproachAdapterNet(config).to(device)
    optimizer = torch.optim.Adam(net.parameters(), lr=args.learning_rate)
    train_loader = make_loader(
        images,
        crops,
        control_state,
        targets,
        train_indices,
        args.batch_size,
        shuffle=True,
    )
    val_loader = make_loader(
        images,
        crops,
        control_state,
        targets,
        val_indices,
        args.batch_size,
        shuffle=False,
    )

    history: list[dict[str, float]] = []
    for epoch in range(1, args.epochs + 1):
        losses: list[float] = []
        for batch in train_loader:
            pred, target = predict_batch(net, batch, device, control_mean, control_std)
            loss = F.mse_loss(pred, target)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        train_loss = float(np.mean(losses))
        val_loss = evaluate(net, val_loader, device, control_mean, control_std)
        history.append({"epoch": float(epoch), "train_loss": train_loss, "val_loss": val_loss})
        print(f"epoch={epoch} train_loss={train_loss:.8f} val_loss={val_loss:.8f}")

    metadata = {
        "dataset": str(args.dataset),
        "extra_datasets": [str(path) for path in args.extra_datasets],
        "samples": int(len(crops)),
        "train_samples": int(len(train_indices)),
        "val_samples": int(len(val_indices)),
        "phase": args.phase,
        "trigger_only": bool(args.trigger_only),
        "xy_only": bool(args.xy_only),
        "use_full_image": bool(images is not None),
        "image_shape": list(images.shape[1:]) if images is not None else None,
        "crop_shape": list(crops.shape[1:]),
        "target_source": args.target_source,
        "target_scale": float(args.target_scale),
        "target_abs_mean": np.mean(np.abs(targets), axis=0).astype(float).tolist(),
        "target_abs_max": np.max(np.abs(targets), axis=0).astype(float).tolist(),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "learning_rate": float(args.learning_rate),
        "history": history,
    }
    save_adapter_checkpoint(
        path=args.output,
        net=net.cpu(),
        control_mean=control_mean_np,
        control_std=control_std_np,
        metadata=metadata,
    )
    metadata_path = args.metadata_output or args.output.with_suffix(args.output.suffix + ".json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved approach adapter to {args.output}")
    print(f"saved metadata to {metadata_path}")


if __name__ == "__main__":
    main()
