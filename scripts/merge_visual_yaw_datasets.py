from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


REQUIRED_KEYS = (
    "cam_image",
    "near_hole_crop",
    "geometry_profile",
    "shape_yaw_label_sin",
    "shape_yaw_label_cos",
    "shape_yaw_period_deg",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge visual-yaw NPZ datasets by concatenating common sample-wise arrays. "
            "Inputs can be repeated to upweight small rollout datasets."
        )
    )
    parser.add_argument("--inputs", nargs="+", type=Path, required=True)
    parser.add_argument(
        "--repeats",
        nargs="+",
        type=int,
        default=None,
        help="Repeat count per input. Defaults to 1 for every input.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compressed", action="store_true")
    parser.add_argument(
        "--add-source-fields",
        action="store_true",
        help="Add source_dataset/source_sample_index/source_repeat_index arrays for diagnostics.",
    )
    return parser.parse_args()


def sample_count(data: np.lib.npyio.NpzFile, path: Path) -> int:
    missing = [key for key in REQUIRED_KEYS if key not in data.files]
    if missing:
        raise ValueError(f"{path} is missing required visual-yaw keys: {missing}")
    count = int(data["cam_image"].shape[0])
    for key in REQUIRED_KEYS:
        array = data[key]
        if array.ndim == 0 or int(array.shape[0]) != count:
            raise ValueError(f"{path}:{key} is not sample-wise with count {count}; shape={array.shape}")
    return count


def common_samplewise_keys(
    loaded: list[np.lib.npyio.NpzFile],
    counts: list[int],
) -> list[str]:
    keys = set(loaded[0].files)
    for data in loaded[1:]:
        keys &= set(data.files)

    samplewise: list[str] = []
    for key in sorted(keys):
        ok = True
        trailing_shape: tuple[int, ...] | None = None
        for data, count in zip(loaded, counts):
            array = data[key]
            if array.ndim == 0 or int(array.shape[0]) != count:
                ok = False
                break
            if trailing_shape is None:
                trailing_shape = tuple(array.shape[1:])
            elif tuple(array.shape[1:]) != trailing_shape:
                ok = False
                break
        if ok:
            samplewise.append(key)

    missing_required = [key for key in REQUIRED_KEYS if key not in samplewise]
    if missing_required:
        raise ValueError(f"common sample-wise keys are missing required fields: {missing_required}")
    return samplewise


def repeat_array(array: np.ndarray, repeat: int) -> np.ndarray:
    if repeat == 1:
        return array
    chunks = [array] * repeat
    return np.concatenate(chunks, axis=0)


def build_arrays(
    loaded: list[np.lib.npyio.NpzFile],
    paths: list[Path],
    counts: list[int],
    repeats: list[int],
    keys: list[str],
    *,
    add_source_fields: bool,
) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for key in keys:
        chunks: list[np.ndarray] = []
        dtype = loaded[0][key].dtype
        for data, repeat in zip(loaded, repeats):
            chunk = repeat_array(data[key], repeat)
            if chunk.dtype != dtype:
                chunk = chunk.astype(dtype)
            chunks.append(chunk)
        arrays[key] = np.concatenate(chunks, axis=0)

    if add_source_fields:
        source_names: list[np.ndarray] = []
        source_indices: list[np.ndarray] = []
        source_repeats: list[np.ndarray] = []
        for path, count, repeat in zip(paths, counts, repeats):
            base_indices = np.arange(count, dtype=np.int32)
            for repeat_index in range(repeat):
                source_names.append(np.full(count, path.as_posix(), dtype=f"<U{max(1, len(path.as_posix()))}"))
                source_indices.append(base_indices)
                source_repeats.append(np.full(count, repeat_index, dtype=np.int32))
        arrays["source_dataset"] = np.concatenate(source_names, axis=0)
        arrays["source_sample_index"] = np.concatenate(source_indices, axis=0)
        arrays["source_repeat_index"] = np.concatenate(source_repeats, axis=0)

    return arrays


def metadata(
    paths: list[Path],
    counts: list[int],
    repeats: list[int],
    keys: list[str],
    arrays: dict[str, np.ndarray],
    *,
    compressed: bool,
    add_source_fields: bool,
) -> dict[str, Any]:
    return {
        "schema": "visual_yaw_dataset_merge_v1",
        "inputs": [path.as_posix() for path in paths],
        "input_samples": counts,
        "input_repeats": repeats,
        "effective_input_samples": [count * repeat for count, repeat in zip(counts, repeats)],
        "output_samples": int(arrays["cam_image"].shape[0]),
        "merged_samplewise_keys": keys,
        "compressed": bool(compressed),
        "add_source_fields": bool(add_source_fields),
    }


def main() -> None:
    args = parse_args()
    if len(args.inputs) < 2:
        raise ValueError("At least two input datasets are required.")
    repeats = args.repeats if args.repeats is not None else [1] * len(args.inputs)
    if len(repeats) != len(args.inputs):
        raise ValueError("--repeats must have the same length as --inputs.")
    if any(repeat <= 0 for repeat in repeats):
        raise ValueError("--repeats must be positive integers.")

    loaded = [np.load(path, allow_pickle=False) for path in args.inputs]
    try:
        counts = [sample_count(data, path) for data, path in zip(loaded, args.inputs)]
        keys = common_samplewise_keys(loaded, counts)
        arrays = build_arrays(
            loaded,
            args.inputs,
            counts,
            repeats,
            keys,
            add_source_fields=bool(args.add_source_fields),
        )
        arrays["metadata_json"] = np.asarray(
            json.dumps(
                metadata(
                    args.inputs,
                    counts,
                    repeats,
                    keys,
                    arrays,
                    compressed=bool(args.compressed),
                    add_source_fields=bool(args.add_source_fields),
                ),
                indent=2,
            )
        )

        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.compressed:
            np.savez_compressed(args.output, **arrays)
        else:
            np.savez(args.output, **arrays)

        metadata_path = args.output.with_suffix(args.output.suffix + ".json")
        metadata_path.write_text(str(arrays["metadata_json"].item()) + "\n", encoding="utf-8")
        print(f"saved merged visual-yaw dataset to {args.output}")
        print(f"saved metadata to {metadata_path}")
        print(f"output_samples={int(arrays['cam_image'].shape[0])}")
        print(f"merged_keys={len(keys)}")
    finally:
        for data in loaded:
            data.close()


if __name__ == "__main__":
    main()
