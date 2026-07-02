from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter a visual-yaw NPZ dataset by sample-wise metadata fields."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--outcome", default=None)
    parser.add_argument("--min-step", type=float, default=None)
    parser.add_argument("--max-step", type=float, default=None)
    parser.add_argument("--min-dist-xy", type=float, default=None)
    parser.add_argument("--max-dist-xy", type=float, default=None)
    parser.add_argument("--min-z-above", type=float, default=None)
    parser.add_argument("--max-z-above", type=float, default=None)
    parser.add_argument("--min-truth-yaw-deg", type=float, default=None)
    parser.add_argument("--max-truth-yaw-deg", type=float, default=None)
    parser.add_argument("--min-pred-yaw-deg", type=float, default=None)
    parser.add_argument("--max-pred-yaw-deg", type=float, default=None)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--compressed", action="store_true")
    return parser.parse_args()


def _sample_count(data: np.lib.npyio.NpzFile) -> int:
    if "cam_image" not in data.files:
        raise ValueError("dataset is missing cam_image")
    return int(data["cam_image"].shape[0])


def _samplewise_keys(data: np.lib.npyio.NpzFile, count: int) -> list[str]:
    return [
        key
        for key in data.files
        if data[key].ndim > 0 and int(data[key].shape[0]) == count
    ]


def _string_mask(data: np.lib.npyio.NpzFile, key: str, value: str | None, count: int) -> np.ndarray:
    if value is None:
        return np.ones(count, dtype=bool)
    if key not in data.files:
        raise ValueError(f"dataset is missing required filter key: {key}")
    return data[key].astype(str) == value


def _range_mask(
    data: np.lib.npyio.NpzFile,
    key: str,
    *,
    min_value: float | None,
    max_value: float | None,
    count: int,
) -> np.ndarray:
    if min_value is None and max_value is None:
        return np.ones(count, dtype=bool)
    if key not in data.files:
        raise ValueError(f"dataset is missing required filter key: {key}")
    values = data[key].astype(np.float64)
    mask = np.isfinite(values)
    if min_value is not None:
        mask &= values >= float(min_value)
    if max_value is not None:
        mask &= values <= float(max_value)
    return mask


def _metadata(args: argparse.Namespace, input_count: int, output_count: int) -> dict[str, Any]:
    return {
        "schema": "visual_yaw_dataset_filter_v1",
        "input": args.input.as_posix(),
        "output": args.output.as_posix(),
        "input_samples": int(input_count),
        "output_samples": int(output_count),
        "filters": {
            key: (str(value) if isinstance(value, Path) else value)
            for key, value in vars(args).items()
            if key not in {"input", "output", "compressed"}
        },
        "compressed": bool(args.compressed),
    }


def main() -> None:
    args = parse_args()
    if args.max_samples is not None and args.max_samples <= 0:
        raise ValueError("--max-samples must be positive when provided.")

    data = np.load(args.input, allow_pickle=False)
    try:
        count = _sample_count(data)
        mask = np.ones(count, dtype=bool)
        mask &= _string_mask(data, "geometry_profile", args.profile, count)
        mask &= _string_mask(data, "episode_outcome", args.outcome, count)
        mask &= _range_mask(data, "step", min_value=args.min_step, max_value=args.max_step, count=count)
        mask &= _range_mask(data, "dist_xy", min_value=args.min_dist_xy, max_value=args.max_dist_xy, count=count)
        mask &= _range_mask(data, "z_above_target", min_value=args.min_z_above, max_value=args.max_z_above, count=count)
        mask &= _range_mask(data, "shape_yaw_error_deg", min_value=args.min_truth_yaw_deg, max_value=args.max_truth_yaw_deg, count=count)
        mask &= _range_mask(data, "visual_yaw_pred_abs_error_deg", min_value=args.min_pred_yaw_deg, max_value=args.max_pred_yaw_deg, count=count)

        indices = np.flatnonzero(mask)
        if args.max_samples is not None and indices.size > args.max_samples:
            rng = np.random.default_rng(args.seed)
            indices = np.sort(rng.choice(indices, size=args.max_samples, replace=False))

        samplewise = _samplewise_keys(data, count)
        arrays: dict[str, np.ndarray] = {}
        for key in samplewise:
            arrays[key] = data[key][indices]
        arrays["metadata_json"] = np.asarray(
            json.dumps(_metadata(args, count, int(indices.size)), indent=2, sort_keys=True)
        )

        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.compressed:
            np.savez_compressed(args.output, **arrays)
        else:
            np.savez(args.output, **arrays)
        metadata_path = args.output.with_suffix(args.output.suffix + ".json")
        metadata_path.write_text(str(arrays["metadata_json"].item()) + "\n", encoding="utf-8")
        print(f"saved filtered visual-yaw dataset to {args.output}")
        print(f"saved metadata to {metadata_path}")
        print(f"input_samples={count}")
        print(f"output_samples={int(indices.size)}")
    finally:
        data.close()


if __name__ == "__main__":
    main()
