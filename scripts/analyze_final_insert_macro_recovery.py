from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


CSV_FIELDS = (
    "source_episode_csv",
    "source_step_csv",
    "seed",
    "episode",
    "outcome",
    "classification",
    "steps",
    "macro_steps",
    "macro_triggers",
    "macro_abort_steps",
    "macro_final_servo_inactive_steps",
    "final_servo_steps",
    "final_servo_recovery_triggers",
    "final_xy_mm",
    "final_z_mm",
    "min_xy_mm",
    "min_z_mm",
    "max_step_xy_mm",
    "max_macro_xy_mm",
    "final_tilt_deg",
    "final_tilted_margin_mm",
    "macro_phase_counts",
    "final_servo_phase_counts",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify final-insert macro-recovery failures from guarded eval "
            "episode CSVs and matching step traces."
        )
    )
    parser.add_argument("--episode-csv", nargs="+", type=Path, required=True)
    parser.add_argument(
        "--step-csv",
        nargs="*",
        type=Path,
        default=None,
        help="Optional explicit step CSVs. Defaults to *_steps.csv inferred from each *_episodes.csv.",
    )
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--include-success", action="store_true")
    parser.add_argument("--divergence-xy-m", type=float, default=0.012)
    parser.add_argument("--near-xy-m", type=float, default=0.008)
    parser.add_argument("--stuck-z-m", type=float, default=0.025)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def infer_step_csv(path: Path) -> Path:
    name = path.name
    if name.endswith("_episodes.csv"):
        return path.with_name(name.removesuffix("_episodes.csv") + "_steps.csv")
    return path.with_name(path.stem + "_steps.csv")


def to_float(row: dict[str, str], key: str, default: float = math.nan) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def to_int(row: dict[str, str], key: str, default: int = 0) -> int:
    value = to_float(row, key, float(default))
    if not math.isfinite(value):
        return default
    return int(value)


def is_true(row: dict[str, str], key: str) -> bool:
    return row.get(key, "").lower() == "true"


def finite(values: Iterable[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def max_f(rows: list[dict[str, str]], key: str) -> float:
    values = finite(to_float(row, key) for row in rows)
    return max(values) if values else math.nan


def phase_counts(rows: list[dict[str, str]], key: str) -> str:
    counts = Counter(row.get(key, "") for row in rows if row.get(key, ""))
    return ";".join(f"{phase}:{count}" for phase, count in sorted(counts.items()))


def row_key(row: dict[str, str]) -> tuple[str, str]:
    return (row.get("seed", ""), row.get("episode", ""))


def group_step_rows(paths: list[Path]) -> tuple[dict[tuple[str, str], list[dict[str, str]]], dict[tuple[str, str], Path]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    sources: dict[tuple[str, str], Path] = {}
    for path in paths:
        if not path.exists():
            continue
        for row in read_csv(path):
            key = row_key(row)
            grouped[key].append(row)
            sources[key] = path
    for rows in grouped.values():
        rows.sort(key=lambda row: to_int(row, "step"))
    return grouped, sources


def classify_failure(
    *,
    outcome: str,
    macro_triggers: int,
    final_xy: float,
    final_z: float,
    max_macro_xy: float,
    args: argparse.Namespace,
) -> str:
    if outcome == "success":
        return "success"
    if macro_triggers <= 0 and outcome == "timeout":
        return "macro_not_triggered_timeout"
    if outcome == "collision" and macro_triggers > 0:
        if max_macro_xy > args.divergence_xy_m or final_xy > args.divergence_xy_m:
            return "macro_triggered_collision_diverged"
        return "macro_triggered_collision"
    if outcome == "collision":
        return "collision_without_macro"
    if outcome == "timeout" and macro_triggers > 0:
        if max_macro_xy > args.divergence_xy_m or final_xy > args.divergence_xy_m:
            return "macro_triggered_timeout_diverged"
        if final_z > args.stuck_z_m and final_xy <= args.near_xy_m:
            return "macro_triggered_timeout_stuck_high_z"
        return "macro_triggered_timeout"
    return f"other_{outcome}"


def summarize_episode(
    *,
    episode_row: dict[str, str],
    source_episode_csv: Path,
    step_rows: list[dict[str, str]],
    source_step_csv: Path | None,
    args: argparse.Namespace,
) -> dict[str, object]:
    outcome = episode_row.get("outcome", "")
    macro_triggers = to_int(episode_row, "final_insert_macro_recovery_triggers")
    macro_steps = to_int(episode_row, "final_insert_macro_recovery_steps")
    final_xy = to_float(episode_row, "final_dist_xy")
    final_z = to_float(episode_row, "final_dist_z")
    max_step_xy = max_f(step_rows, "post_dist_xy")
    macro_rows = [
        row
        for row in step_rows
        if is_true(row, "final_insert_macro_recovery_active")
        or row.get("final_insert_macro_recovery_phase", "inactive") != "inactive"
    ]
    macro_abort_rows = [
        row for row in macro_rows if row.get("final_insert_macro_recovery_phase") == "abort_lift"
    ]
    macro_inactive_servo_rows = [
        row for row in macro_rows if not is_true(row, "guard_final_servo_active")
    ]
    final_servo_rows = [row for row in step_rows if is_true(row, "guard_final_servo_active")]
    max_macro_xy = max_f(macro_rows, "post_dist_xy")
    classification = classify_failure(
        outcome=outcome,
        macro_triggers=macro_triggers,
        final_xy=final_xy,
        final_z=final_z,
        max_macro_xy=max_macro_xy,
        args=args,
    )
    return {
        "source_episode_csv": str(source_episode_csv),
        "source_step_csv": "" if source_step_csv is None else str(source_step_csv),
        "seed": episode_row.get("seed", ""),
        "episode": episode_row.get("episode", ""),
        "outcome": outcome,
        "classification": classification,
        "steps": to_int(episode_row, "steps"),
        "macro_steps": macro_steps,
        "macro_triggers": macro_triggers,
        "macro_abort_steps": len(macro_abort_rows),
        "macro_final_servo_inactive_steps": len(macro_inactive_servo_rows),
        "final_servo_steps": to_int(episode_row, "final_servo_steps"),
        "final_servo_recovery_triggers": to_int(
            episode_row, "final_servo_recovery_triggers"
        ),
        "final_xy_mm": final_xy * 1000.0,
        "final_z_mm": final_z * 1000.0,
        "min_xy_mm": to_float(episode_row, "min_dist_xy") * 1000.0,
        "min_z_mm": to_float(episode_row, "min_dist_z") * 1000.0,
        "max_step_xy_mm": max_step_xy * 1000.0,
        "max_macro_xy_mm": max_macro_xy * 1000.0,
        "final_tilt_deg": to_float(episode_row, "final_peg_tilt_angle_deg"),
        "final_tilted_margin_mm": to_float(
            episode_row, "final_square_peg_tilted_clearance_margin"
        )
        * 1000.0,
        "macro_phase_counts": phase_counts(macro_rows, "final_insert_macro_recovery_phase"),
        "final_servo_phase_counts": phase_counts(final_servo_rows, "guard_final_servo_phase"),
    }


def fmt(value: object) -> str:
    if isinstance(value, float):
        if not math.isfinite(value):
            return "nan"
        return f"{value:.3f}"
    return str(value)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(CSV_FIELDS))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = (
        "seed",
        "episode",
        "outcome",
        "classification",
        "steps",
        "macro_steps",
        "macro_triggers",
        "macro_abort_steps",
        "macro_final_servo_inactive_steps",
        "final_xy_mm",
        "final_z_mm",
        "max_step_xy_mm",
        "final_tilt_deg",
        "final_tilted_margin_mm",
    )
    class_counts = Counter(str(row["classification"]) for row in rows)
    lines = [
        "# Final Insert Macro Recovery Summary",
        "",
        "## Classification Counts",
        "",
        "| Classification | Count |",
        "| --- | ---: |",
    ]
    for name, count in sorted(class_counts.items()):
        lines.append(f"| {name} | {count} |")
    lines.extend(
        [
            "",
            "## Episodes",
            "",
            "| " + " | ".join(columns) + " |",
            "| " + " | ".join("---" for _ in columns) + " |",
        ]
    )
    for row in rows:
        lines.append("| " + " | ".join(fmt(row[column]) for column in columns) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    step_paths = (
        list(args.step_csv)
        if args.step_csv is not None and len(args.step_csv) > 0
        else [infer_step_csv(path) for path in args.episode_csv]
    )
    grouped_steps, step_sources = group_step_rows(step_paths)
    summaries: list[dict[str, object]] = []
    for episode_csv in args.episode_csv:
        for episode_row in read_csv(episode_csv):
            if not args.include_success and episode_row.get("outcome") == "success":
                continue
            key = row_key(episode_row)
            summaries.append(
                summarize_episode(
                    episode_row=episode_row,
                    source_episode_csv=episode_csv,
                    step_rows=grouped_steps.get(key, []),
                    source_step_csv=step_sources.get(key),
                    args=args,
                )
            )

    if args.output_csv is not None:
        write_csv(args.output_csv, summaries)
    if args.output_md is not None:
        write_markdown(args.output_md, summaries)
    if args.output_csv is None and args.output_md is None:
        for row in summaries:
            print(row)


if __name__ == "__main__":
    main()
