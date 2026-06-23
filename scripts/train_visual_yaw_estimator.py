from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, Subset

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from peg_in_hole_mujoco.sim_config import parse_args_with_config


DEFAULT_PROFILE_ORDER = (
    "square_square",
    "triangle_triangle",
    "hex_hex",
    "rectangular_key",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a visual shape-yaw estimator from NPZ yaw-label data.")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--validation-split", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=907_000)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--no-profile-onehot", action="store_true")
    parser.add_argument("--num-workers", type=int, default=0)
    return parse_args_with_config(parser)


def resolve_device(device: str) -> torch.device:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device)


class VisualYawDataset(Dataset[tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]]):
    def __init__(
        self,
        dataset_path: Path,
        *,
        profile_order: tuple[str, ...] = DEFAULT_PROFILE_ORDER,
    ):
        data = np.load(dataset_path, allow_pickle=False)
        required = (
            "cam_image",
            "near_hole_crop",
            "geometry_profile",
            "shape_yaw_label_sin",
            "shape_yaw_label_cos",
            "shape_yaw_period_deg",
        )
        missing = [key for key in required if key not in data.files]
        if missing:
            raise ValueError(f"dataset is missing required yaw keys: {missing}")

        self.cam = torch.from_numpy(data["cam_image"].astype(np.float32) / 255.0).permute(0, 3, 1, 2).contiguous()
        self.crop = torch.from_numpy(data["near_hole_crop"].astype(np.float32) / 255.0).permute(0, 3, 1, 2).contiguous()
        target = np.stack(
            [data["shape_yaw_label_sin"], data["shape_yaw_label_cos"]],
            axis=1,
        ).astype(np.float32)
        self.target = torch.from_numpy(target)
        self.period_deg = torch.from_numpy(data["shape_yaw_period_deg"].astype(np.float32))
        self.profile_names = data["geometry_profile"].astype(str)
        self.profile_order = tuple(profile_order)
        profile_to_id = {profile: index for index, profile in enumerate(self.profile_order)}
        missing_profiles = sorted(set(self.profile_names) - set(profile_to_id))
        if missing_profiles:
            raise ValueError(f"dataset contains unknown profiles: {missing_profiles}")
        self.profile_id = torch.tensor([profile_to_id[name] for name in self.profile_names], dtype=torch.long)

    def __len__(self) -> int:
        return int(self.cam.shape[0])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        return (
            self.cam[index],
            self.crop[index],
            self.profile_id[index],
            self.target[index],
            self.period_deg[index],
        )


class ConvEncoder(nn.Module):
    def __init__(self, in_channels: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, 16, kernel_size=5, stride=2, padding=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 96, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
        )

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return self.net(image)


class VisualYawEstimator(nn.Module):
    def __init__(
        self,
        *,
        cam_channels: int,
        crop_channels: int,
        profile_count: int,
        include_profile_onehot: bool,
    ):
        super().__init__()
        self.include_profile_onehot = bool(include_profile_onehot)
        self.profile_count = int(profile_count)
        self.cam_encoder = ConvEncoder(cam_channels)
        self.crop_encoder = ConvEncoder(crop_channels)
        head_input = 96 + 96 + (profile_count if include_profile_onehot else 0)
        self.head = nn.Sequential(
            nn.Linear(head_input, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 2),
        )

    def forward(self, cam: torch.Tensor, crop: torch.Tensor, profile_id: torch.Tensor) -> torch.Tensor:
        features = [self.cam_encoder(cam), self.crop_encoder(crop)]
        if self.include_profile_onehot:
            onehot = torch.nn.functional.one_hot(profile_id, num_classes=self.profile_count).float()
            features.append(onehot)
        pred = self.head(torch.cat(features, dim=1))
        return pred / pred.norm(dim=1, keepdim=True).clamp_min(1e-6)


@dataclass
class EpochMetrics:
    epoch: int
    train_loss: float
    val_loss: float
    val_mean_abs_yaw_error_deg: float
    val_p95_abs_yaw_error_deg: float


def split_indices(length: int, validation_split: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    if not 0.0 < validation_split < 1.0:
        raise ValueError("--validation-split must be between 0 and 1.")
    rng = np.random.default_rng(seed)
    indices = np.arange(length)
    rng.shuffle(indices)
    val_count = max(1, int(round(length * validation_split)))
    train_indices = indices[val_count:]
    val_indices = indices[:val_count]
    if train_indices.size == 0:
        raise ValueError("dataset is too small for the requested validation split.")
    return train_indices, val_indices


def angular_error_deg(pred: torch.Tensor, target: torch.Tensor, period_deg: torch.Tensor) -> torch.Tensor:
    pred_angle = torch.atan2(pred[:, 0], pred[:, 1])
    target_angle = torch.atan2(target[:, 0], target[:, 1])
    phase_error = torch.atan2(torch.sin(pred_angle - target_angle), torch.cos(pred_angle - target_angle))
    return torch.abs(phase_error) * period_deg / (2.0 * torch.pi)


def evaluate(
    model: VisualYawEstimator,
    loader: DataLoader,
    device: torch.device,
) -> tuple[float, float, float]:
    model.eval()
    losses: list[float] = []
    errors: list[np.ndarray] = []
    with torch.no_grad():
        for cam, crop, profile_id, target, period_deg in loader:
            cam = cam.to(device)
            crop = crop.to(device)
            profile_id = profile_id.to(device)
            target = target.to(device)
            period_deg = period_deg.to(device)
            pred = model(cam, crop, profile_id)
            loss = torch.mean((pred - target) ** 2)
            losses.append(float(loss.item()))
            errors.append(angular_error_deg(pred, target, period_deg).cpu().numpy())
    flat_errors = np.concatenate(errors, axis=0) if errors else np.asarray([], dtype=np.float32)
    return (
        float(np.mean(losses)) if losses else float("nan"),
        float(np.mean(flat_errors)) if flat_errors.size else float("nan"),
        float(np.percentile(flat_errors, 95)) if flat_errors.size else float("nan"),
    )


def evaluate_profile_breakdown(
    model: VisualYawEstimator,
    dataset: VisualYawDataset,
    indices: np.ndarray,
    device: torch.device,
    *,
    batch_size: int,
    num_workers: int,
) -> dict[str, dict[str, float]]:
    breakdown: dict[str, dict[str, float]] = {}
    profile_ids = dataset.profile_id.numpy()
    for profile_index, profile in enumerate(dataset.profile_order):
        profile_indices = indices[profile_ids[indices] == profile_index]
        if profile_indices.size == 0:
            continue
        loader = DataLoader(
            Subset(dataset, profile_indices.tolist()),
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
        )
        loss, mean_error, p95_error = evaluate(model, loader, device)
        breakdown[profile] = {
            "samples": float(profile_indices.size),
            "loss": float(loss),
            "mean_abs_yaw_error_deg": float(mean_error),
            "p95_abs_yaw_error_deg": float(p95_error),
        }
    return breakdown


def train(args: argparse.Namespace) -> tuple[VisualYawEstimator, list[EpochMetrics], dict[str, Any]]:
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = resolve_device(args.device)
    dataset = VisualYawDataset(args.dataset)
    train_indices, val_indices = split_indices(len(dataset), args.validation_split, args.seed)
    train_loader = DataLoader(
        Subset(dataset, train_indices.tolist()),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
    )
    val_loader = DataLoader(
        Subset(dataset, val_indices.tolist()),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )
    model = VisualYawEstimator(
        cam_channels=int(dataset.cam.shape[1]),
        crop_channels=int(dataset.crop.shape[1]),
        profile_count=len(dataset.profile_order),
        include_profile_onehot=not args.no_profile_onehot,
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    history: list[EpochMetrics] = []
    best_state_dict: dict[str, torch.Tensor] | None = None
    best_epoch = 0
    best_val_error = float("inf")
    for epoch in range(1, args.epochs + 1):
        model.train()
        train_losses: list[float] = []
        for cam, crop, profile_id, target, _period_deg in train_loader:
            cam = cam.to(device)
            crop = crop.to(device)
            profile_id = profile_id.to(device)
            target = target.to(device)
            pred = model(cam, crop, profile_id)
            loss = torch.mean((pred - target) ** 2)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.item()))
        val_loss, val_mean_error, val_p95_error = evaluate(model, val_loader, device)
        metrics = EpochMetrics(
            epoch=epoch,
            train_loss=float(np.mean(train_losses)),
            val_loss=val_loss,
            val_mean_abs_yaw_error_deg=val_mean_error,
            val_p95_abs_yaw_error_deg=val_p95_error,
        )
        history.append(metrics)
        if metrics.val_mean_abs_yaw_error_deg < best_val_error:
            best_val_error = metrics.val_mean_abs_yaw_error_deg
            best_epoch = epoch
            best_state_dict = deepcopy(model.state_dict())
        print(
            f"epoch={epoch} train_loss={metrics.train_loss:.6f} "
            f"val_loss={metrics.val_loss:.6f} "
            f"val_yaw_mean={metrics.val_mean_abs_yaw_error_deg:.3f} "
            f"val_yaw_p95={metrics.val_p95_abs_yaw_error_deg:.3f}"
        )
    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)
    profile_breakdown = evaluate_profile_breakdown(
        model,
        dataset,
        val_indices,
        device,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
    )
    metadata = {
        "dataset": str(args.dataset),
        "samples": len(dataset),
        "train_samples": int(train_indices.size),
        "val_samples": int(val_indices.size),
        "best_epoch": int(best_epoch),
        "best_val_mean_abs_yaw_error_deg": float(best_val_error),
        "val_profile_breakdown": profile_breakdown,
        "profile_order": list(dataset.profile_order),
        "include_profile_onehot": not args.no_profile_onehot,
        "cam_shape": list(dataset.cam.shape[1:]),
        "crop_shape": list(dataset.crop.shape[1:]),
        "device": str(device),
    }
    return model, history, metadata


def save_checkpoint(
    path: Path,
    model: VisualYawEstimator,
    history: list[EpochMetrics],
    metadata: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "schema": "visual_yaw_estimator_v1",
            "model_state_dict": model.state_dict(),
            "history": [metric.__dict__ for metric in history],
            "metadata": metadata,
            "args": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        },
        path,
    )


def write_report(path: Path, history: list[EpochMetrics], metadata: dict[str, Any], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best = min(history, key=lambda metric: metric.val_mean_abs_yaw_error_deg)
    lines = [
        "# Visual Yaw Estimator",
        "",
        f"- Dataset: `{args.dataset}`",
        f"- Output: `{args.output}`",
        f"- Samples train/val: `{metadata['train_samples']}/{metadata['val_samples']}`",
        f"- Profile one-hot: `{metadata['include_profile_onehot']}`",
        f"- Best epoch: `{best.epoch}`",
        f"- Best val mean yaw error: `{best.val_mean_abs_yaw_error_deg:.3f} deg`",
        f"- Best val p95 yaw error: `{best.val_p95_abs_yaw_error_deg:.3f} deg`",
        "",
        "## Per-Profile Validation",
        "",
        "| Profile | Samples | Loss | Mean yaw err deg | P95 yaw err deg |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for profile, row in metadata.get("val_profile_breakdown", {}).items():
        lines.append(
            f"| `{profile}` | {int(row['samples'])} | {row['loss']:.6f} | "
            f"{row['mean_abs_yaw_error_deg']:.3f} | {row['p95_abs_yaw_error_deg']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Training History",
            "",
        "| Epoch | Train loss | Val loss | Val mean yaw err deg | Val p95 yaw err deg |",
        "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for metric in history:
        lines.append(
            f"| {metric.epoch} | {metric.train_loss:.6f} | {metric.val_loss:.6f} | "
            f"{metric.val_mean_abs_yaw_error_deg:.3f} | {metric.val_p95_abs_yaw_error_deg:.3f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    model, history, metadata = train(args)
    save_checkpoint(args.output, model, history, metadata, args)
    report_path = args.output_md if args.output_md is not None else args.output.with_suffix(".md")
    write_report(report_path, history, metadata, args)
    print(f"saved visual yaw estimator to {args.output}")
    print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
