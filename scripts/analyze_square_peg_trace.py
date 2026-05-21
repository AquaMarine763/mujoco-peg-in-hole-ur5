from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize square-peg orientation diagnostics from guarded eval step traces."
    )
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    return parser.parse_args()


def to_float(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "nan"))
    except ValueError:
        return math.nan


def finite(values: Iterable[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def min_f(rows: list[dict[str, str]], key: str) -> float:
    values = finite(to_float(row, key) for row in rows)
    return min(values) if values else math.nan


def max_f(rows: list[dict[str, str]], key: str) -> float:
    values = finite(to_float(row, key) for row in rows)
    return max(values) if values else math.nan


def last_f(rows: list[dict[str, str]], key: str) -> float:
    if not rows:
        return math.nan
    return to_float(rows[-1], key)


def summarize_trace(path: Path) -> dict[str, object]:
    with path.open(newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"empty trace: {path}")

    last = rows[-1]
    final_servo_rows = [
        row for row in rows if row.get("guard_final_servo_active") == "True"
    ]
    phases = Counter(
        row.get("guard_final_servo_phase", "")
        for row in final_servo_rows
        if row.get("guard_final_servo_phase", "")
    )
    phase_summary = ";".join(f"{phase}:{count}" for phase, count in sorted(phases.items()))

    return {
        "trace": str(path),
        "seed": last.get("seed", ""),
        "outcome": last.get("episode_outcome", ""),
        "steps": len(rows),
        "final_servo_steps": len(final_servo_rows),
        "min_xy_mm": min_f(rows, "post_dist_xy") * 1000.0,
        "final_xy_mm": last_f(rows, "post_dist_xy") * 1000.0,
        "min_z_mm": min_f(rows, "post_dist_z") * 1000.0,
        "final_z_mm": last_f(rows, "post_dist_z") * 1000.0,
        "max_tilt_deg": max_f(rows, "peg_tilt_angle_deg"),
        "final_tilt_deg": last_f(rows, "peg_tilt_angle_deg"),
        "max_yaw_error_deg": max_f(rows, "square_peg_yaw_error_deg"),
        "final_yaw_error_deg": last_f(rows, "square_peg_yaw_error_deg"),
        "min_topdown_margin_mm": min_f(
            rows, "square_peg_topdown_clearance_margin"
        )
        * 1000.0,
        "final_topdown_margin_mm": last_f(
            rows, "square_peg_topdown_clearance_margin"
        )
        * 1000.0,
        "min_tilted_margin_mm": min_f(
            rows, "square_peg_tilted_clearance_margin"
        )
        * 1000.0,
        "final_tilted_margin_mm": last_f(
            rows, "square_peg_tilted_clearance_margin"
        )
        * 1000.0,
        "final_servo_phase_counts": phase_summary,
    }


def fmt(value: object) -> str:
    if isinstance(value, float):
        if not math.isfinite(value):
            return "nan"
        return f"{value:.3f}"
    return str(value)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "seed",
        "outcome",
        "steps",
        "final_servo_steps",
        "min_xy_mm",
        "final_xy_mm",
        "min_z_mm",
        "final_z_mm",
        "max_tilt_deg",
        "final_tilt_deg",
        "final_yaw_error_deg",
        "final_topdown_margin_mm",
        "final_tilted_margin_mm",
        "final_servo_phase_counts",
    ]
    lines = [
        "# Square Peg Trace Summary",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row[column]) for column in columns) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = [summarize_trace(path) for path in args.input]
    if args.output_csv is not None:
        write_csv(args.output_csv, rows)
    if args.output_md is not None:
        write_markdown(args.output_md, rows)
    if args.output_csv is None and args.output_md is None:
        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
