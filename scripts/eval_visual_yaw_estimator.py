from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from peg_in_hole_mujoco.sim_config import parse_args_with_config
from train_visual_yaw_estimator import (
    VisualYawDataset,
    VisualYawEstimator,
    resolve_device,
    split_indices,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a visual yaw estimator and generate per-profile/yaw-bin diagnostics."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--worst-sheet", type=Path, default=None)
    parser.add_argument("--split", choices=("validation", "train", "full"), default="validation")
    parser.add_argument("--validation-split", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--bin-count", type=int, default=12)
    parser.add_argument("--bad-threshold-deg", type=float, default=15.0)
    parser.add_argument("--worst-count", type=int, default=24)
    parser.add_argument("--worst-cols", type=int, default=4)
    parser.add_argument("--worst-profiles", nargs="+", default=["rectangular_key"])
    args = parse_args_with_config(parser)
    normalize_args(args)
    return args


def normalize_args(args: argparse.Namespace) -> None:
    if args.output_md is None:
        args.output_md = args.checkpoint.with_name(f"{args.checkpoint.stem}_eval.md")
    if args.output_json is None:
        args.output_json = args.output_md.with_suffix(".json")
    if args.worst_sheet is None:
        args.worst_sheet = args.output_md.with_name(f"{args.output_md.stem}_worst.png")
    if args.bin_count <= 0:
        raise ValueError("--bin-count must be positive.")
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be positive.")
    if args.worst_count < 0:
        raise ValueError("--worst-count cannot be negative.")
    if args.worst_cols <= 0:
        raise ValueError("--worst-cols must be positive.")


def load_checkpoint(path: Path, device: torch.device) -> dict[str, Any]:
    try:
        checkpoint = torch.load(path, map_location=device, weights_only=False)
    except TypeError:
        checkpoint = torch.load(path, map_location=device)
    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise ValueError(f"unsupported visual yaw checkpoint: {path}")
    return checkpoint


def checkpoint_arg(checkpoint: dict[str, Any], key: str, default: Any) -> Any:
    args = checkpoint.get("args", {})
    if isinstance(args, dict) and key in args:
        return args[key]
    return default


def select_indices(
    dataset: VisualYawDataset,
    checkpoint: dict[str, Any],
    args: argparse.Namespace,
) -> np.ndarray:
    if args.split == "full":
        return np.arange(len(dataset), dtype=np.int64)

    validation_split = args.validation_split
    if validation_split is None:
        validation_split = float(checkpoint_arg(checkpoint, "validation_split", 0.2))
    seed = args.seed
    if seed is None:
        seed = int(checkpoint_arg(checkpoint, "seed", 907_000))
    train_indices, val_indices = split_indices(len(dataset), float(validation_split), int(seed))
    return val_indices if args.split == "validation" else train_indices


def load_model(
    dataset: VisualYawDataset,
    checkpoint: dict[str, Any],
    device: torch.device,
) -> VisualYawEstimator:
    metadata = checkpoint.get("metadata", {})
    include_profile_onehot = True
    if isinstance(metadata, dict) and "include_profile_onehot" in metadata:
        include_profile_onehot = bool(metadata["include_profile_onehot"])
    else:
        include_profile_onehot = not bool(checkpoint_arg(checkpoint, "no_profile_onehot", False))
    model = VisualYawEstimator(
        cam_channels=int(dataset.cam.shape[1]),
        crop_channels=int(dataset.crop.shape[1]),
        profile_count=len(dataset.profile_order),
        include_profile_onehot=include_profile_onehot,
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model


def evaluate_samples(
    model: VisualYawEstimator,
    dataset: VisualYawDataset,
    indices: np.ndarray,
    device: torch.device,
    batch_size: int,
) -> dict[str, np.ndarray]:
    preds: list[np.ndarray] = []
    errors: list[np.ndarray] = []
    signed_errors: list[np.ndarray] = []
    target_yaw_deg: list[np.ndarray] = []
    pred_yaw_deg: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(indices), batch_size):
            batch_indices = indices[start : start + batch_size]
            batch_tensor = torch.as_tensor(batch_indices, dtype=torch.long)
            cam = dataset.cam[batch_tensor].to(device)
            crop = dataset.crop[batch_tensor].to(device)
            profile_id = dataset.profile_id[batch_tensor].to(device)
            target = dataset.target[batch_tensor].to(device)
            period_deg = dataset.period_deg[batch_tensor].to(device)
            pred = model(cam, crop, profile_id)

            pred_angle = torch.atan2(pred[:, 0], pred[:, 1])
            target_angle = torch.atan2(target[:, 0], target[:, 1])
            phase_error = torch.atan2(torch.sin(pred_angle - target_angle), torch.cos(pred_angle - target_angle))
            signed_error = phase_error * period_deg / (2.0 * torch.pi)
            target_yaw = target_angle * period_deg / (2.0 * torch.pi)
            pred_yaw = pred_angle * period_deg / (2.0 * torch.pi)

            preds.append(pred.cpu().numpy())
            signed_np = signed_error.cpu().numpy()
            signed_errors.append(signed_np)
            errors.append(np.abs(signed_np))
            target_yaw_deg.append(target_yaw.cpu().numpy())
            pred_yaw_deg.append(pred_yaw.cpu().numpy())

    return {
        "index": indices.astype(np.int64),
        "profile_id": dataset.profile_id[indices].numpy().astype(np.int64),
        "period_deg": dataset.period_deg[indices].numpy().astype(np.float64),
        "pred_sin_cos": np.concatenate(preds, axis=0),
        "signed_error_deg": np.concatenate(signed_errors, axis=0).astype(np.float64),
        "abs_error_deg": np.concatenate(errors, axis=0).astype(np.float64),
        "target_yaw_deg": np.concatenate(target_yaw_deg, axis=0).astype(np.float64),
        "pred_yaw_deg": np.concatenate(pred_yaw_deg, axis=0).astype(np.float64),
    }


def finite_stats(values: np.ndarray, bad_threshold_deg: float) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {
            "samples": 0.0,
            "mean": float("nan"),
            "p50": float("nan"),
            "p90": float("nan"),
            "p95": float("nan"),
            "max": float("nan"),
            "bad_frac": float("nan"),
        }
    return {
        "samples": float(values.size),
        "mean": float(np.mean(values)),
        "p50": float(np.percentile(values, 50)),
        "p90": float(np.percentile(values, 90)),
        "p95": float(np.percentile(values, 95)),
        "max": float(np.max(values)),
        "bad_frac": float(np.mean(values > bad_threshold_deg)),
    }


def profile_summary(
    records: dict[str, np.ndarray],
    profile_order: tuple[str, ...],
    bad_threshold_deg: float,
) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for profile_id, profile in enumerate(profile_order):
        mask = records["profile_id"] == profile_id
        if not np.any(mask):
            continue
        summary[profile] = finite_stats(records["abs_error_deg"][mask], bad_threshold_deg)
    return summary


def yaw_bin_summary(
    records: dict[str, np.ndarray],
    profile_order: tuple[str, ...],
    bin_count: int,
    bad_threshold_deg: float,
) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for profile_id, profile in enumerate(profile_order):
        profile_mask = records["profile_id"] == profile_id
        if not np.any(profile_mask):
            continue
        period = float(np.nanmedian(records["period_deg"][profile_mask]))
        edges = np.linspace(-0.5 * period, 0.5 * period, bin_count + 1)
        yaw_values = records["target_yaw_deg"][profile_mask]
        error_values = records["abs_error_deg"][profile_mask]
        bin_ids = np.digitize(yaw_values, edges, right=False) - 1
        bin_ids = np.clip(bin_ids, 0, bin_count - 1)
        for bin_id in range(bin_count):
            mask = bin_ids == bin_id
            if not np.any(mask):
                continue
            stats = finite_stats(error_values[mask], bad_threshold_deg)
            rows.append(
                {
                    "profile": profile,
                    "bin_start_deg": float(edges[bin_id]),
                    "bin_end_deg": float(edges[bin_id + 1]),
                    **stats,
                }
            )
    return rows


def selected_worst_samples(
    records: dict[str, np.ndarray],
    profile_order: tuple[str, ...],
    worst_profiles: list[str],
    worst_count: int,
) -> list[dict[str, Any]]:
    if worst_count <= 0:
        return []
    profile_ids = {profile: index for index, profile in enumerate(profile_order)}
    selected_profile_ids = [
        profile_ids[profile]
        for profile in worst_profiles
        if profile in profile_ids and np.any(records["profile_id"] == profile_ids[profile])
    ]
    if selected_profile_ids:
        mask = np.isin(records["profile_id"], np.asarray(selected_profile_ids, dtype=np.int64))
    else:
        mask = np.ones_like(records["abs_error_deg"], dtype=bool)
    candidate_rows = np.flatnonzero(mask)
    order = candidate_rows[np.argsort(records["abs_error_deg"][candidate_rows])[::-1]]
    worst_rows: list[dict[str, Any]] = []
    for row in order[:worst_count]:
        profile = profile_order[int(records["profile_id"][row])]
        worst_rows.append(
            {
                "dataset_index": int(records["index"][row]),
                "profile": profile,
                "period_deg": float(records["period_deg"][row]),
                "target_yaw_deg": float(records["target_yaw_deg"][row]),
                "pred_yaw_deg": float(records["pred_yaw_deg"][row]),
                "signed_error_deg": float(records["signed_error_deg"][row]),
                "abs_error_deg": float(records["abs_error_deg"][row]),
            }
        )
    return worst_rows


def image_rgb(image: np.ndarray) -> np.ndarray:
    image = np.asarray(image)
    if image.ndim == 2:
        image = np.repeat(image[:, :, None], 3, axis=2)
    if image.shape[2] == 1:
        image = np.repeat(image, 3, axis=2)
    if image.shape[2] > 3:
        image = image[:, :, :3]
    return np.asarray(image, dtype=np.uint8)


def put_text(image: np.ndarray, text: str, x: int, y: int, scale: float = 0.38) -> None:
    cv2.putText(
        image,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (20, 20, 20),
        1,
        cv2.LINE_AA,
    )


def write_worst_sheet(
    path: Path,
    raw_data: np.lib.npyio.NpzFile,
    worst_samples: list[dict[str, Any]],
    *,
    cols: int,
) -> None:
    if not worst_samples:
        return
    tile_w = 242
    tile_h = 156
    image_h = 100
    rows = int(np.ceil(len(worst_samples) / cols))
    sheet = np.full((rows * tile_h, cols * tile_w, 3), 245, dtype=np.uint8)
    for sample_index, sample in enumerate(worst_samples):
        row = sample_index // cols
        col = sample_index % cols
        x0 = col * tile_w
        y0 = row * tile_h
        dataset_index = int(sample["dataset_index"])
        cam = image_rgb(raw_data["cam_image"][dataset_index])
        crop = image_rgb(raw_data["near_hole_crop"][dataset_index])
        cam = cv2.resize(cam, (image_h, image_h), interpolation=cv2.INTER_AREA)
        crop = cv2.resize(crop, (image_h, image_h), interpolation=cv2.INTER_NEAREST)
        sheet[y0 + 6 : y0 + 6 + image_h, x0 + 6 : x0 + 6 + image_h] = cam
        sheet[y0 + 6 : y0 + 6 + image_h, x0 + 116 : x0 + 116 + image_h] = crop
        put_text(sheet, sample["profile"], x0 + 6, y0 + 124, 0.36)
        put_text(
            sheet,
            f"err={sample['abs_error_deg']:.1f} pred={sample['pred_yaw_deg']:.1f}",
            x0 + 6,
            y0 + 140,
            0.34,
        )
        put_text(sheet, f"target={sample['target_yaw_deg']:.1f}", x0 + 116, y0 + 124, 0.34)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR))


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_markdown(
    path: Path,
    *,
    args: argparse.Namespace,
    checkpoint: dict[str, Any],
    selected_count: int,
    overall: dict[str, float],
    profiles: dict[str, dict[str, float]],
    bins: list[dict[str, float | str]],
    worst_samples: list[dict[str, Any]],
) -> None:
    metadata = checkpoint.get("metadata", {})
    best_epoch = metadata.get("best_epoch", "unknown") if isinstance(metadata, dict) else "unknown"
    lines = [
        "# Visual Yaw Estimator Eval",
        "",
        f"- Dataset: `{args.dataset}`",
        f"- Checkpoint: `{args.checkpoint}`",
        f"- Split: `{args.split}`",
        f"- Samples evaluated: `{selected_count}`",
        f"- Checkpoint best epoch: `{best_epoch}`",
        f"- Worst sheet: `{args.worst_sheet}`",
        f"- Bad threshold: `>{args.bad_threshold_deg:.1f} deg`",
        "",
        "## Overall",
        "",
        "| Samples | Mean deg | P50 deg | P90 deg | P95 deg | Max deg | Bad frac |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| {int(overall['samples'])} | {overall['mean']:.3f} | {overall['p50']:.3f} | "
            f"{overall['p90']:.3f} | {overall['p95']:.3f} | {overall['max']:.3f} | "
            f"{overall['bad_frac']:.3f} |"
        ),
        "",
        "## Per Profile",
        "",
        "| Profile | Samples | Mean deg | P50 deg | P90 deg | P95 deg | Max deg | Bad frac |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for profile, stats in profiles.items():
        lines.append(
            f"| `{profile}` | {int(stats['samples'])} | {stats['mean']:.3f} | {stats['p50']:.3f} | "
            f"{stats['p90']:.3f} | {stats['p95']:.3f} | {stats['max']:.3f} | {stats['bad_frac']:.3f} |"
        )

    worst_bins = sorted(
        bins,
        key=lambda row: (float(row["p95"]), float(row["mean"])),
        reverse=True,
    )[:24]
    lines.extend(
        [
            "",
            "## Worst Yaw Bins",
            "",
            "| Profile | Bin deg | Samples | Mean deg | P95 deg | Max deg | Bad frac |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in worst_bins:
        lines.append(
            f"| `{row['profile']}` | {float(row['bin_start_deg']):.1f}..{float(row['bin_end_deg']):.1f} | "
            f"{int(float(row['samples']))} | {float(row['mean']):.3f} | {float(row['p95']):.3f} | "
            f"{float(row['max']):.3f} | {float(row['bad_frac']):.3f} |"
        )

    lines.extend(
        [
            "",
            "## Worst Samples",
            "",
            "| Index | Profile | Target deg | Pred deg | Signed err deg | Abs err deg |",
            "| ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for sample in worst_samples[:24]:
        lines.append(
            f"| {sample['dataset_index']} | `{sample['profile']}` | {sample['target_yaw_deg']:.3f} | "
            f"{sample['pred_yaw_deg']:.3f} | {sample['signed_error_deg']:.3f} | "
            f"{sample['abs_error_deg']:.3f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    device = resolve_device(args.device)
    checkpoint = load_checkpoint(args.checkpoint, device)
    dataset = VisualYawDataset(args.dataset)
    selected_indices = select_indices(dataset, checkpoint, args)
    model = load_model(dataset, checkpoint, device)
    records = evaluate_samples(model, dataset, selected_indices, device, args.batch_size)
    raw_data = np.load(args.dataset, allow_pickle=False)

    overall = finite_stats(records["abs_error_deg"], args.bad_threshold_deg)
    profiles = profile_summary(records, dataset.profile_order, args.bad_threshold_deg)
    bins = yaw_bin_summary(records, dataset.profile_order, args.bin_count, args.bad_threshold_deg)
    worst_samples = selected_worst_samples(
        records,
        dataset.profile_order,
        args.worst_profiles,
        args.worst_count,
    )

    payload = {
        "dataset": str(args.dataset),
        "checkpoint": str(args.checkpoint),
        "split": args.split,
        "samples_evaluated": int(len(selected_indices)),
        "overall": overall,
        "per_profile": profiles,
        "yaw_bins": bins,
        "worst_profiles": list(args.worst_profiles),
        "worst_samples": worst_samples,
    }
    write_json(args.output_json, payload)
    write_markdown(
        args.output_md,
        args=args,
        checkpoint=checkpoint,
        selected_count=len(selected_indices),
        overall=overall,
        profiles=profiles,
        bins=bins,
        worst_samples=worst_samples,
    )
    write_worst_sheet(args.worst_sheet, raw_data, worst_samples, cols=args.worst_cols)
    print(json.dumps(payload["overall"], indent=2, sort_keys=True))
    print(f"saved eval report to {args.output_md}")
    print(f"saved eval json to {args.output_json}")
    if worst_samples:
        print(f"saved worst-case sheet to {args.worst_sheet}")


if __name__ == "__main__":
    main()
