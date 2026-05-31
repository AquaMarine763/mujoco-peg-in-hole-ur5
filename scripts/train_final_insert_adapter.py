from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from peg_in_hole_mujoco.final_insert_adapter import (
    FinalInsertAdapterConfig,
    FinalInsertAdapterNet,
    save_final_insert_adapter_checkpoint,
)
from peg_in_hole_mujoco.sim_config import parse_args_with_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a low-dimensional final-insert correction adapter."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--extra-datasets",
        nargs="*",
        type=Path,
        default=[],
        help="Additional NPZ datasets with the same feature_names.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=0.0)
    parser.add_argument("--validation-split", type=float, default=0.33)
    parser.add_argument(
        "--split-mode",
        choices=["episode", "random"],
        default="episode",
        help="Use trace-episode validation by default to avoid pure row leakage.",
    )
    parser.add_argument("--seed", type=int, default=910_000)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--num-hidden-layers", type=int, default=2)
    parser.add_argument(
        "--target-scale",
        type=float,
        default=1000.0,
        help="Scale target actions during training. 1000 means meters -> millimeters.",
    )
    parser.add_argument(
        "--feature-clip",
        type=float,
        default=10.0,
        help="Clamp normalized features to this absolute value.",
    )
    parser.add_argument(
        "--label-phase",
        nargs="*",
        default=[],
        help="Optional label_phase filter, e.g. contact_lift micro_recenter.",
    )
    parser.add_argument(
        "--balance-label-phases",
        action="store_true",
        help="Use inverse-frequency sample weights for label_phase.",
    )
    parser.add_argument("--log-interval", type=int, default=25)
    return parse_args_with_config(parser)


def load_arrays(args: argparse.Namespace) -> dict[str, np.ndarray]:
    dataset_paths = [args.dataset, *args.extra_datasets]
    feature_parts: list[np.ndarray] = []
    target_parts: list[np.ndarray] = []
    label_parts: list[np.ndarray] = []
    source_parts: list[np.ndarray] = []
    episode_parts: list[np.ndarray] = []
    seed_parts: list[np.ndarray] = []
    step_parts: list[np.ndarray] = []
    feature_names: tuple[str, ...] | None = None

    for path in dataset_paths:
        with np.load(path, allow_pickle=False) as dataset:
            if "features" not in dataset or "target_actions" not in dataset:
                raise ValueError(f"{path}: expected features and target_actions arrays.")
            if "feature_names" not in dataset:
                raise ValueError(f"{path}: expected feature_names array.")
            current_feature_names = tuple(str(name) for name in dataset["feature_names"])
            if feature_names is None:
                feature_names = current_feature_names
            elif current_feature_names != feature_names:
                raise ValueError(f"{path}: feature_names do not match the first dataset.")
            features = np.asarray(dataset["features"], dtype=np.float32)
            targets = np.asarray(dataset["target_actions"], dtype=np.float32)
            if features.ndim != 2:
                raise ValueError(f"{path}: features must be rank 2.")
            if targets.shape != (features.shape[0], 3):
                raise ValueError(f"{path}: target_actions must have shape (N, 3).")
            labels = np.asarray(dataset.get("label_phase", np.full(len(features), ""))).astype(str)
            mask = np.ones(len(features), dtype=bool)
            if args.label_phase:
                allowed = set(str(value) for value in args.label_phase)
                mask &= np.asarray([label in allowed for label in labels], dtype=bool)
            if not np.any(mask):
                raise ValueError(f"{path}: no samples remain after filtering.")
            feature_parts.append(features[mask])
            target_parts.append(targets[mask])
            label_parts.append(labels[mask])
            source_parts.append(
                np.asarray(dataset.get("source_trace", np.full(len(features), str(path)))).astype(str)[mask]
            )
            episode_parts.append(
                np.asarray(dataset.get("episode", np.arange(len(features)))).astype(str)[mask]
            )
            seed_parts.append(
                np.asarray(dataset.get("seed", np.full(len(features), ""))).astype(str)[mask]
            )
            step_parts.append(
                np.asarray(dataset.get("step", np.full(len(features), ""))).astype(str)[mask]
            )

    if feature_names is None:
        raise ValueError("No datasets were provided.")
    return {
        "features": np.concatenate(feature_parts, axis=0),
        "targets": np.concatenate(target_parts, axis=0),
        "label_phase": np.concatenate(label_parts, axis=0),
        "source_trace": np.concatenate(source_parts, axis=0),
        "episode": np.concatenate(episode_parts, axis=0),
        "seed": np.concatenate(seed_parts, axis=0),
        "step": np.concatenate(step_parts, axis=0),
        "feature_names": np.asarray(feature_names),
    }


def make_splits(
    *,
    sample_count: int,
    source_trace: np.ndarray,
    episode: np.ndarray,
    seed: np.ndarray,
    validation_split: float,
    split_mode: str,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    indices = np.arange(sample_count)
    if sample_count <= 1 or validation_split <= 0.0:
        return indices, np.asarray([], dtype=np.int64), []
    if split_mode == "random":
        shuffled = rng.permutation(indices)
        val_count = max(1, min(int(sample_count * validation_split), sample_count - 1))
        return shuffled[val_count:], shuffled[:val_count], []

    group_keys = np.asarray(
        [
            f"{source_trace[i]}|{seed[i]}|{episode[i]}"
            for i in range(sample_count)
        ]
    )
    groups = np.unique(group_keys)
    if len(groups) <= 1:
        shuffled = rng.permutation(indices)
        val_count = max(1, min(int(sample_count * validation_split), sample_count - 1))
        return shuffled[val_count:], shuffled[:val_count], ["fallback_random_single_group"]
    shuffled_groups = rng.permutation(groups)
    val_group_count = max(1, min(int(len(groups) * validation_split), len(groups) - 1))
    val_groups = set(str(group) for group in shuffled_groups[:val_group_count])
    val_mask = np.asarray([str(group) in val_groups for group in group_keys], dtype=bool)
    val_indices = indices[val_mask]
    train_indices = indices[~val_mask]
    if len(train_indices) == 0 or len(val_indices) == 0:
        shuffled = rng.permutation(indices)
        val_count = max(1, min(int(sample_count * validation_split), sample_count - 1))
        return shuffled[val_count:], shuffled[:val_count], ["fallback_random_empty_split"]
    return train_indices, val_indices, sorted(val_groups)


def make_sample_weights(label_phase: np.ndarray, train_indices: np.ndarray, balance: bool) -> np.ndarray:
    weights = np.ones(len(label_phase), dtype=np.float32)
    if not balance:
        return weights
    train_labels = label_phase[train_indices]
    counts = Counter(str(label) for label in train_labels)
    for index, label in enumerate(label_phase):
        weights[index] = 1.0 / max(1, counts[str(label)])
    mean_weight = float(weights[train_indices].mean())
    if mean_weight > 0.0:
        weights /= mean_weight
    return weights.astype(np.float32)


def make_loader(
    features: np.ndarray,
    targets_scaled: np.ndarray,
    weights: np.ndarray,
    indices: np.ndarray,
    batch_size: int,
    shuffle: bool,
) -> DataLoader:
    dataset = TensorDataset(
        torch.as_tensor(features[indices], dtype=torch.float32),
        torch.as_tensor(targets_scaled[indices], dtype=torch.float32),
        torch.as_tensor(weights[indices], dtype=torch.float32),
    )
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)


def weighted_mse(pred: torch.Tensor, target: torch.Tensor, weights: torch.Tensor) -> torch.Tensor:
    per_sample = F.mse_loss(pred, target, reduction="none").mean(dim=1)
    return (per_sample * weights).mean()


def predict_array(
    net: FinalInsertAdapterNet,
    features: np.ndarray,
    device: torch.device,
) -> np.ndarray:
    net.eval()
    preds: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(features), 512):
            batch = torch.as_tensor(features[start : start + 512], dtype=torch.float32, device=device)
            preds.append(net(batch).detach().cpu().numpy())
    net.train()
    return np.concatenate(preds, axis=0) if preds else np.zeros((0, 3), dtype=np.float32)


def evaluate_split(
    net: FinalInsertAdapterNet,
    features: np.ndarray,
    targets_scaled: np.ndarray,
    indices: np.ndarray,
    device: torch.device,
    target_scale: float,
) -> dict[str, float]:
    if len(indices) == 0:
        return {
            "mse_scaled": float("nan"),
            "mae_mm": float("nan"),
            "mae_xy_mm": float("nan"),
            "mae_z_mm": float("nan"),
            "max_abs_mm": float("nan"),
        }
    pred_scaled = predict_array(net, features[indices], device)
    error_m = (pred_scaled - targets_scaled[indices]) / target_scale
    abs_error_mm = np.abs(error_m) * 1000.0
    return {
        "mse_scaled": float(np.mean((pred_scaled - targets_scaled[indices]) ** 2)),
        "mae_mm": float(np.mean(abs_error_mm)),
        "mae_xy_mm": float(np.mean(abs_error_mm[:, :2])),
        "mae_z_mm": float(np.mean(abs_error_mm[:, 2])),
        "max_abs_mm": float(np.max(abs_error_mm)),
    }


def count_dict(values: np.ndarray) -> dict[str, int]:
    return {str(key): int(value) for key, value in Counter(str(v) for v in values).items()}


def main() -> None:
    args = parse_args()
    if args.epochs <= 0:
        raise ValueError("--epochs must be positive.")
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be positive.")
    if not 0.0 <= args.validation_split < 1.0:
        raise ValueError("--validation-split must be in [0, 1).")
    if args.target_scale <= 0.0:
        raise ValueError("--target-scale must be positive.")
    if args.feature_clip <= 0.0:
        raise ValueError("--feature-clip must be positive.")
    if args.log_interval <= 0:
        raise ValueError("--log-interval must be positive.")

    rng = np.random.default_rng(args.seed)
    torch.manual_seed(args.seed)
    arrays = load_arrays(args)
    features_raw = np.asarray(arrays["features"], dtype=np.float32)
    targets = np.asarray(arrays["targets"], dtype=np.float32)
    label_phase = np.asarray(arrays["label_phase"]).astype(str)
    feature_names = tuple(str(name) for name in arrays["feature_names"])

    train_indices, val_indices, val_groups = make_splits(
        sample_count=len(features_raw),
        source_trace=np.asarray(arrays["source_trace"]).astype(str),
        episode=np.asarray(arrays["episode"]).astype(str),
        seed=np.asarray(arrays["seed"]).astype(str),
        validation_split=float(args.validation_split),
        split_mode=str(args.split_mode),
        rng=rng,
    )
    feature_mean = features_raw[train_indices].mean(axis=0).astype(np.float32)
    feature_std = features_raw[train_indices].std(axis=0).astype(np.float32)
    feature_std = np.maximum(feature_std, 1e-6).astype(np.float32)
    features = ((features_raw - feature_mean) / feature_std).astype(np.float32)
    features = np.clip(
        features,
        -float(args.feature_clip),
        float(args.feature_clip),
    ).astype(np.float32)
    targets_scaled = (targets * float(args.target_scale)).astype(np.float32)
    weights = make_sample_weights(label_phase, train_indices, args.balance_label_phases)

    device = torch.device(args.device)
    config = FinalInsertAdapterConfig(
        input_dim=int(features.shape[1]),
        hidden_dim=int(args.hidden_dim),
        num_hidden_layers=int(args.num_hidden_layers),
        target_scale=float(args.target_scale),
        feature_clip=float(args.feature_clip),
    )
    net = FinalInsertAdapterNet(config).to(device)
    optimizer = torch.optim.Adam(
        net.parameters(),
        lr=float(args.learning_rate),
        weight_decay=float(args.weight_decay),
    )
    train_loader = make_loader(
        features,
        targets_scaled,
        weights,
        train_indices,
        args.batch_size,
        shuffle=True,
    )

    history: list[dict[str, float]] = []
    for epoch in range(1, args.epochs + 1):
        batch_losses: list[float] = []
        net.train()
        for feature_batch, target_batch, weight_batch in train_loader:
            feature_batch = feature_batch.to(device)
            target_batch = target_batch.to(device)
            weight_batch = weight_batch.to(device)
            pred = net(feature_batch)
            loss = weighted_mse(pred, target_batch, weight_batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            batch_losses.append(float(loss.detach().cpu()))
        train_metrics = evaluate_split(
            net,
            features,
            targets_scaled,
            train_indices,
            device,
            args.target_scale,
        )
        val_metrics = evaluate_split(
            net,
            features,
            targets_scaled,
            val_indices,
            device,
            args.target_scale,
        )
        row = {
            "epoch": float(epoch),
            "train_loss": float(np.mean(batch_losses)),
            "train_mae_mm": train_metrics["mae_mm"],
            "val_mae_mm": val_metrics["mae_mm"],
            "val_mse_scaled": val_metrics["mse_scaled"],
        }
        history.append(row)
        if epoch == 1 or epoch == args.epochs or epoch % args.log_interval == 0:
            print(
                "epoch={epoch} train_loss={train_loss:.6f} "
                "train_mae_mm={train_mae_mm:.4f} val_mae_mm={val_mae_mm:.4f}".format(
                    **row
                )
            )

    final_train_metrics = evaluate_split(
        net,
        features,
        targets_scaled,
        train_indices,
        device,
        args.target_scale,
    )
    final_val_metrics = evaluate_split(
        net,
        features,
        targets_scaled,
        val_indices,
        device,
        args.target_scale,
    )
    metadata = {
        "dataset": str(args.dataset),
        "extra_datasets": [str(path) for path in args.extra_datasets],
        "samples": int(len(features)),
        "train_samples": int(len(train_indices)),
        "val_samples": int(len(val_indices)),
        "split_mode": str(args.split_mode),
        "validation_split": float(args.validation_split),
        "validation_groups": val_groups,
        "label_phase_filter": [str(value) for value in args.label_phase],
        "balance_label_phases": bool(args.balance_label_phases),
        "label_phase_counts": count_dict(label_phase),
        "train_label_phase_counts": count_dict(label_phase[train_indices]),
        "val_label_phase_counts": count_dict(label_phase[val_indices]),
        "feature_names": list(feature_names),
        "target_scale": float(args.target_scale),
        "feature_clip": float(args.feature_clip),
        "target_abs_mean_m": np.mean(np.abs(targets), axis=0).astype(float).tolist(),
        "target_abs_max_m": np.max(np.abs(targets), axis=0).astype(float).tolist(),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "learning_rate": float(args.learning_rate),
        "weight_decay": float(args.weight_decay),
        "hidden_dim": int(args.hidden_dim),
        "num_hidden_layers": int(args.num_hidden_layers),
        "train_metrics": final_train_metrics,
        "val_metrics": final_val_metrics,
        "history": history,
    }
    save_final_insert_adapter_checkpoint(
        path=args.output,
        net=net.cpu(),
        feature_mean=feature_mean,
        feature_std=feature_std,
        feature_names=feature_names,
        metadata=metadata,
    )
    metadata_path = args.metadata_output or args.output.with_suffix(args.output.suffix + ".json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved final-insert adapter to {args.output}")
    print(f"saved metadata to {metadata_path}")
    print(
        "final train/val mae: "
        f"{final_train_metrics['mae_mm']:.4f} mm / {final_val_metrics['mae_mm']:.4f} mm"
    )


if __name__ == "__main__":
    main()
