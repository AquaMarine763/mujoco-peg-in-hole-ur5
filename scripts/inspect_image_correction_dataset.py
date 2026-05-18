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
    "desired_z",
    "step_id",
    "steps_to_end",
    "alignment_stable_steps",
    "dist_xy",
    "dist_z",
    "z_above_target",
    "policy_norm",
    "oracle_norm",
    "correction_norm",
    "correction_xy_norm",
    "action_cosine",
    "contact_recovery_z_max",
)

BOOL_KEYS = (
    "near_hole",
    "failure_window",
    "opposed_actions",
    "policy_down_or_oracle_up",
    "policy_down_oracle_less_down",
    "contact_recovery_window",
    "timeout_progress_window",
    "insert_drift_window",
    "insert_settle_window",
    "balanced_v4b_window",
    "approach_window",
    "fixture_wall_window",
    "ever_within_insert_xy",
    "drift_after_alignment",
    "descent_should_block",
    "oracle_lift_action",
    "oracle_down_action",
    "recovery_branch",
    "synthetic_recovery_state",
    "episode_success",
    "episode_collision",
    "episode_timeout",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect an image correction NPZ dataset.")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    return parser.parse_args()


def metadata_path_for(dataset_path: Path) -> Path:
    return dataset_path.with_suffix(dataset_path.suffix + ".json")


def load_metadata(dataset_path: Path) -> dict[str, Any]:
    metadata_path = metadata_path_for(dataset_path)
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


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


def format_float(value: Any) -> str:
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


def add_stats(rows: list[dict[str, Any]], name: str, values: np.ndarray) -> None:
    rows.append({"metric": name, **finite_stats(values)})


def bool_rate(values: np.ndarray) -> float:
    if values.size == 0:
        return float("nan")
    return float(np.mean(np.asarray(values, dtype=np.bool_)))


def value_counts(values: np.ndarray) -> dict[str, int]:
    if values.size == 0:
        return {}
    labels, counts = np.unique(values.astype(str), return_counts=True)
    return {str(label): int(count) for label, count in zip(labels, counts)}


def conditional_rate(mask: np.ndarray, values: np.ndarray) -> float:
    mask = np.asarray(mask, dtype=np.bool_)
    if mask.size == 0 or int(np.sum(mask)) == 0:
        return float("nan")
    return bool_rate(values[mask])


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
    summary: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Image Correction Dataset Inspection",
        "",
        f"- Dataset: `{dataset_path}`",
        f"- Metadata: `{metadata_path_for(dataset_path)}`",
        f"- Schema: `{metadata.get('dataset_schema_version', 'unknown')}`",
        f"- Samples: `{summary['samples']}`",
        f"- Unique source episodes: `{summary['unique_episodes']}`",
        f"- Episodes completed while collecting: `{metadata.get('episodes_completed', 'unknown')}`",
        f"- Selection: `{metadata.get('selection', 'unknown')}`",
        f"- Scenario preset: `{metadata.get('scenario_preset', 'unknown')}`",
        f"- Tier preset: `{metadata.get('tier_preset', 'unknown')}`",
        f"- Min correction norm: `{metadata.get('min_correction_norm', 'unknown')}`",
        f"- Has near-hole crops: `{'near_hole_crops' in arrays}`",
        f"- Has control state: `{'control_state' in arrays}`",
        "",
        "## Correction Signals",
        "",
        "| Signal | Rate |",
        "| --- | ---: |",
        f"| near hole | {format_float(summary['near_hole_rate'])} |",
        f"| failure window | {format_float(summary['failure_window_rate'])} |",
        f"| opposed actions | {format_float(summary['opposed_action_rate'])} |",
        f"| policy down or oracle up | {format_float(summary['policy_down_or_oracle_up_rate'])} |",
        f"| policy down and oracle less down | {format_float(summary['policy_down_oracle_less_down_rate'])} |",
        f"| opposed actions near hole | {format_float(summary['near_hole_opposed_action_rate'])} |",
        f"| contact recovery window | {format_float(summary['contact_recovery_window_rate'])} |",
        f"| timeout progress window | {format_float(summary['timeout_progress_window_rate'])} |",
        f"| insert drift window | {format_float(summary['insert_drift_window_rate'])} |",
        f"| insert settle window | {format_float(summary['insert_settle_window_rate'])} |",
        f"| balanced v4b window | {format_float(summary['balanced_v4b_window_rate'])} |",
        f"| approach window | {format_float(summary['approach_window_rate'])} |",
        f"| fixture wall window | {format_float(summary['fixture_wall_window_rate'])} |",
        f"| ever within insert xy | {format_float(summary['ever_within_insert_xy_rate'])} |",
        f"| drift after alignment | {format_float(summary['drift_after_alignment_rate'])} |",
        f"| descent should block | {format_float(summary['descent_should_block_rate'])} |",
        f"| oracle lift action | {format_float(summary['oracle_lift_action_rate'])} |",
        f"| oracle down action | {format_float(summary['oracle_down_action_rate'])} |",
        f"| recovery branch | {format_float(summary['recovery_branch_rate'])} |",
        f"| synthetic recovery state | {format_float(summary['synthetic_recovery_state_rate'])} |",
        "",
        "## Outcome Counts",
        "",
        "| Outcome | Samples |",
        "| --- | ---: |",
    ]
    for key, count in summary["outcome_counts"].items():
        lines.append(f"| {key} | {count} |")

    lines.extend(
        [
            "",
            "## Scenario Counts",
            "",
            "| Scenario | Samples |",
            "| --- | ---: |",
        ]
    )
    for key, count in summary["scenario_counts"].items():
        lines.append(f"| {key} | {count} |")

    lines.extend(
        [
            "",
            "## Tier Counts",
            "",
            "| Tier | Samples |",
            "| --- | ---: |",
        ]
    )
    for key, count in summary["tier_counts"].items():
        lines.append(f"| {key} | {count} |")

    if summary["recovery_phase_counts"]:
        lines.extend(
            [
                "",
                "## Recovery Phase Counts",
                "",
                "| Phase | Samples |",
                "| --- | ---: |",
            ]
        )
        for key, count in summary["recovery_phase_counts"].items():
            lines.append(f"| {key} | {count} |")

    lines.extend(
        [
            "",
            "## Arrays",
            "",
            "| Key | Shape | Dtype |",
            "| --- | --- | --- |",
        ]
    )
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


def build_summary(dataset: np.lib.npyio.NpzFile) -> dict[str, Any]:
    samples = int(dataset["actions"].shape[0]) if "actions" in dataset.files else 0
    near_hole = np.asarray(dataset["near_hole"], dtype=np.bool_) if "near_hole" in dataset.files else np.zeros(samples, dtype=np.bool_)
    opposed = (
        np.asarray(dataset["opposed_actions"], dtype=np.bool_)
        if "opposed_actions" in dataset.files
        else np.zeros(samples, dtype=np.bool_)
    )
    summary = {
        "samples": samples,
        "unique_episodes": int(np.unique(dataset["episode_id"]).size) if "episode_id" in dataset.files else 0,
        "near_hole_rate": bool_rate(near_hole),
        "failure_window_rate": bool_rate(dataset["failure_window"]) if "failure_window" in dataset.files else float("nan"),
        "opposed_action_rate": bool_rate(opposed),
        "policy_down_or_oracle_up_rate": (
            bool_rate(dataset["policy_down_or_oracle_up"])
            if "policy_down_or_oracle_up" in dataset.files
            else float("nan")
        ),
        "policy_down_oracle_less_down_rate": (
            bool_rate(dataset["policy_down_oracle_less_down"])
            if "policy_down_oracle_less_down" in dataset.files
            else float("nan")
        ),
        "near_hole_opposed_action_rate": conditional_rate(near_hole, opposed),
        "contact_recovery_window_rate": (
            bool_rate(dataset["contact_recovery_window"])
            if "contact_recovery_window" in dataset.files
            else float("nan")
        ),
        "timeout_progress_window_rate": (
            bool_rate(dataset["timeout_progress_window"])
            if "timeout_progress_window" in dataset.files
            else float("nan")
        ),
        "insert_drift_window_rate": (
            bool_rate(dataset["insert_drift_window"])
            if "insert_drift_window" in dataset.files
            else float("nan")
        ),
        "insert_settle_window_rate": (
            bool_rate(dataset["insert_settle_window"])
            if "insert_settle_window" in dataset.files
            else float("nan")
        ),
        "balanced_v4b_window_rate": (
            bool_rate(dataset["balanced_v4b_window"])
            if "balanced_v4b_window" in dataset.files
            else float("nan")
        ),
        "approach_window_rate": (
            bool_rate(dataset["approach_window"])
            if "approach_window" in dataset.files
            else float("nan")
        ),
        "fixture_wall_window_rate": (
            bool_rate(dataset["fixture_wall_window"])
            if "fixture_wall_window" in dataset.files
            else float("nan")
        ),
        "ever_within_insert_xy_rate": (
            bool_rate(dataset["ever_within_insert_xy"])
            if "ever_within_insert_xy" in dataset.files
            else float("nan")
        ),
        "drift_after_alignment_rate": (
            bool_rate(dataset["drift_after_alignment"])
            if "drift_after_alignment" in dataset.files
            else float("nan")
        ),
        "descent_should_block_rate": (
            bool_rate(dataset["descent_should_block"])
            if "descent_should_block" in dataset.files
            else float("nan")
        ),
        "oracle_lift_action_rate": (
            bool_rate(dataset["oracle_lift_action"])
            if "oracle_lift_action" in dataset.files
            else float("nan")
        ),
        "oracle_down_action_rate": (
            bool_rate(dataset["oracle_down_action"])
            if "oracle_down_action" in dataset.files
            else float("nan")
        ),
        "recovery_branch_rate": (
            bool_rate(dataset["recovery_branch"])
            if "recovery_branch" in dataset.files
            else float("nan")
        ),
        "synthetic_recovery_state_rate": (
            bool_rate(dataset["synthetic_recovery_state"])
            if "synthetic_recovery_state" in dataset.files
            else float("nan")
        ),
        "outcome_counts": value_counts(dataset["episode_outcome"]) if "episode_outcome" in dataset.files else {},
        "scenario_counts": value_counts(dataset["scenario"]) if "scenario" in dataset.files else {},
        "tier_counts": value_counts(dataset["tier"]) if "tier" in dataset.files else {},
        "recovery_phase_counts": (
            value_counts(dataset["recovery_phase"])
            if "recovery_phase" in dataset.files
            else {}
        ),
    }
    return summary


def main() -> None:
    args = parse_args()
    metadata = load_metadata(args.dataset)
    rows: list[dict[str, Any]] = []
    with np.load(args.dataset) as dataset:
        arrays = {
            key: {"shape": list(dataset[key].shape), "dtype": str(dataset[key].dtype)}
            for key in dataset.files
        }
        summary = build_summary(dataset)
        for key in SCALAR_KEYS:
            if key in dataset.files:
                add_stats(rows, key, dataset[key])
        for key in BOOL_KEYS:
            if key in dataset.files:
                add_stats(rows, f"{key}_rate", np.asarray(dataset[key], dtype=np.float32))
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
        if "policy_actions" in dataset.files:
            add_stats(rows, "policy_action_norm", np.linalg.norm(dataset["policy_actions"], axis=1))
        if "policy_raw_actions" in dataset.files:
            add_stats(rows, "policy_raw_action_norm", np.linalg.norm(dataset["policy_raw_actions"], axis=1))
        if "correction_raw_actions" in dataset.files:
            add_stats(rows, "correction_raw_action_norm", np.linalg.norm(dataset["correction_raw_actions"], axis=1))

    if args.output_csv is not None:
        write_csv(args.output_csv, rows)
        print(f"saved csv summary to {args.output_csv}")
    if args.output_md is not None:
        write_markdown(args.output_md, args.dataset, arrays, rows, metadata, summary)
        print(f"saved markdown summary to {args.output_md}")
    if args.output_csv is None and args.output_md is None:
        print(json.dumps({"arrays": arrays, "summary": summary, "stats": rows}, indent=2))


if __name__ == "__main__":
    main()
