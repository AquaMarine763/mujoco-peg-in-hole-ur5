from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np


SCALAR_KEYS = (
    "hole_half_size",
    "peg_radius",
    "hole_clearance",
    "control_action_scale_multiplier",
    "control_action_noise_std",
    "control_action_delay",
    "control_action_filter_alpha",
    "fixture_height_offset",
    "table_height_offset",
    "contact_friction_multiplier",
    "contact_solref_time_multiplier",
    "contact_solref_damping_multiplier",
    "contact_solimp_width_multiplier",
    "joint_damping_multiplier",
    "actuator_kp_multiplier",
    "desired_z",
    "step_id",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect an image expert NPZ dataset.")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    return parser.parse_args()


def finite_stats(values: np.ndarray) -> dict[str, float]:
    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    finite = flat[np.isfinite(flat)]
    if finite.size == 0:
        return {
            "count": 0.0,
            "mean": float("nan"),
            "std": float("nan"),
            "min": float("nan"),
            "p05": float("nan"),
            "p50": float("nan"),
            "p95": float("nan"),
            "max": float("nan"),
        }
    return {
        "count": float(finite.size),
        "mean": float(np.mean(finite)),
        "std": float(np.std(finite)),
        "min": float(np.min(finite)),
        "p05": float(np.percentile(finite, 5)),
        "p50": float(np.percentile(finite, 50)),
        "p95": float(np.percentile(finite, 95)),
        "max": float(np.max(finite)),
    }


def add_stats(rows: list[dict[str, Any]], name: str, values: np.ndarray) -> None:
    stats = finite_stats(values)
    rows.append({"metric": name, **stats})


def format_float(value: Any) -> str:
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if np.isnan(number):
        return "nan"
    if abs(number) >= 1000:
        return f"{number:.1f}"
    if abs(number) >= 1:
        return f"{number:.4f}"
    return f"{number:.6f}"


def metadata_path_for(dataset_path: Path) -> Path:
    return dataset_path.with_suffix(dataset_path.suffix + ".json")


def load_metadata(dataset_path: Path) -> dict[str, Any]:
    metadata_path = metadata_path_for(dataset_path)
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["metric", "count", "mean", "std", "min", "p05", "p50", "p95", "max"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_markdown(
    path: Path,
    dataset_path: Path,
    arrays: dict[str, dict[str, Any]],
    rows: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Image Expert Dataset Inspection",
        "",
        f"- Dataset: `{dataset_path}`",
        f"- Metadata: `{metadata_path_for(dataset_path)}`",
        f"- Schema: `{metadata.get('dataset_schema_version', 'unknown')}`",
        f"- Samples: `{arrays.get('actions', {}).get('shape', ['unknown'])[0]}`",
        f"- Episodes completed: `{metadata.get('episodes_completed', 'unknown')}`",
        f"- Success rate: `{metadata.get('success_rate', 'unknown')}`",
        f"- Collision rate: `{metadata.get('collision_rate', 'unknown')}`",
        f"- Success-only: `{metadata.get('success_only', 'unknown')}`",
        f"- Has near-hole crops: `{'near_hole_crops' in arrays}`",
        f"- Image frame stack: `{metadata.get('image_frame_stack', 'unknown')}`",
        f"- Control state dim: `{arrays.get('control_state', {}).get('shape', ['none', 'none'])[1]}`",
        "",
        "## Arrays",
        "",
        "| Key | Shape | Dtype |",
        "| --- | --- | --- |",
    ]
    for key, info in sorted(arrays.items()):
        lines.append(f"| `{key}` | `{info['shape']}` | `{info['dtype']}` |")

    lines.extend(
        [
            "",
            "## Distributions",
            "",
            "| Metric | Count | Mean | Std | Min | P05 | P50 | P95 | Max |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            "| {metric} | {count} | {mean} | {std} | {min} | {p05} | {p50} | {p95} | {max} |".format(
                metric=row["metric"],
                count=format_float(row.get("count")),
                mean=format_float(row.get("mean")),
                std=format_float(row.get("std")),
                min=format_float(row.get("min")),
                p05=format_float(row.get("p05")),
                p50=format_float(row.get("p50")),
                p95=format_float(row.get("p95")),
                max=format_float(row.get("max")),
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    metadata = load_metadata(args.dataset)
    rows: list[dict[str, Any]] = []
    with np.load(args.dataset) as dataset:
        arrays = {
            key: {"shape": list(dataset[key].shape), "dtype": str(dataset[key].dtype)}
            for key in dataset.files
        }
        for key in SCALAR_KEYS:
            if key in dataset.files:
                add_stats(rows, key, dataset[key])
        if "hole_center_offset" in dataset.files:
            offsets = dataset["hole_center_offset"]
            if offsets.ndim == 2 and offsets.shape[1] == 2:
                add_stats(rows, "hole_center_offset_x", offsets[:, 0])
                add_stats(rows, "hole_center_offset_y", offsets[:, 1])
                add_stats(rows, "hole_center_offset_norm", np.linalg.norm(offsets, axis=1))
        if "actions" in dataset.files:
            add_stats(rows, "action_norm", np.linalg.norm(dataset["actions"], axis=1))
        if "raw_actions" in dataset.files:
            add_stats(rows, "raw_action_norm", np.linalg.norm(dataset["raw_actions"], axis=1))
        if "control_state" in dataset.files:
            control_state = dataset["control_state"]
            if control_state.ndim == 2:
                names = (
                    "prev_cmd_x",
                    "prev_cmd_y",
                    "prev_cmd_z",
                    "actual_delta_x",
                    "actual_delta_y",
                    "actual_delta_z",
                    "tracking_error_x",
                    "tracking_error_y",
                    "tracking_error_z",
                    "step_fraction",
                )
                for index in range(min(control_state.shape[1], len(names))):
                    add_stats(rows, f"control_state_{names[index]}", control_state[:, index])
        if "episode_id" in dataset.files:
            unique_episodes = np.unique(dataset["episode_id"]).size
            rows.append(
                {
                    "metric": "unique_episode_id_count",
                    "count": float(unique_episodes),
                    "mean": float(unique_episodes),
                    "std": 0.0,
                    "min": float(unique_episodes),
                    "p05": float(unique_episodes),
                    "p50": float(unique_episodes),
                    "p95": float(unique_episodes),
                    "max": float(unique_episodes),
                }
            )

    if args.output_csv is not None:
        write_csv(args.output_csv, rows)
        print(f"saved csv summary to {args.output_csv}")
    if args.output_md is not None:
        write_markdown(args.output_md, args.dataset, arrays, rows, metadata)
        print(f"saved markdown summary to {args.output_md}")
    if args.output_csv is None and args.output_md is None:
        print(json.dumps({"arrays": arrays, "stats": rows}, indent=2))


if __name__ == "__main__":
    main()
