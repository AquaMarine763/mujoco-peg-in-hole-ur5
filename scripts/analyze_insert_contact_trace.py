from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from pathlib import Path
from typing import Iterable


CONTACT_WALL_FIELDS = (
    "peg_hole_contact_hole_north",
    "peg_hole_contact_hole_south",
    "peg_hole_contact_hole_east",
    "peg_hole_contact_hole_west",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize peg-hole contact diagnostics from guarded eval step traces."
    )
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument(
        "--insert-xy-m",
        type=float,
        default=0.005,
        help="XY threshold used to count insert-band steps.",
    )
    parser.add_argument(
        "--low-z-m",
        type=float,
        default=0.025,
        help="Height above target used to count late low-Z steps.",
    )
    parser.add_argument(
        "--stall-z-delta-m",
        type=float,
        default=0.0002,
        help="Absolute per-step Z motion below this is counted as low-Z stall.",
    )
    return parser.parse_args()


def to_float(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "nan"))
    except ValueError:
        return math.nan


def to_int(row: dict[str, str], key: str) -> int:
    try:
        return int(float(row.get(key, "0")))
    except ValueError:
        return 0


def finite(values: Iterable[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def min_f(rows: list[dict[str, str]], key: str) -> float:
    values = finite(to_float(row, key) for row in rows)
    return min(values) if values else math.nan


def max_f(rows: list[dict[str, str]], key: str) -> float:
    values = finite(to_float(row, key) for row in rows)
    return max(values) if values else math.nan


def mean_f(values: Iterable[float]) -> float:
    finite_values = finite(values)
    return sum(finite_values) / len(finite_values) if finite_values else math.nan


def last_f(rows: list[dict[str, str]], key: str) -> float:
    if not rows:
        return math.nan
    return to_float(rows[-1], key)


def count_rows(rows: list[dict[str, str]], key: str, threshold: float) -> int:
    return sum(1 for row in rows if to_float(row, key) <= threshold)


def contact_rows(rows: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    return [row for row in rows if to_int(row, key) > 0]


def first_step(rows: list[dict[str, str]]) -> int:
    if not rows:
        return -1
    return to_int(rows[0], "step")


def wall_contact_name(field: str) -> str:
    return field.replace("peg_hole_contact_hole_", "")


def active_walls(row: dict[str, str]) -> str:
    walls = [
        wall_contact_name(field)
        for field in CONTACT_WALL_FIELDS
        if to_int(row, field) > 0
    ]
    return ",".join(walls) if walls else "none"


def summarize_pairs(rows: list[dict[str, str]]) -> str:
    counts: Counter[str] = Counter()
    for row in rows:
        for pair in row.get("peg_hole_contact_pairs", "").split(";"):
            pair = pair.strip()
            if pair:
                counts[pair] += 1
    return ";".join(f"{pair}:{count}" for pair, count in sorted(counts.items()))


def phase_summary(rows: list[dict[str, str]], field: str) -> str:
    counts = Counter(row.get(field, "") for row in rows if row.get(field, ""))
    return ";".join(f"{phase}:{count}" for phase, count in sorted(counts.items()))


def summarize_trace(
    path: Path,
    *,
    insert_xy_m: float,
    low_z_m: float,
    stall_z_delta_m: float,
) -> dict[str, object]:
    with path.open(newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"empty trace: {path}")

    last = rows[-1]
    steps = len(rows)
    peg_contact_rows = contact_rows(rows, "peg_hole_contact_count")
    wall_rows = contact_rows(rows, "peg_hole_contact_wall_count")
    plate_rows = contact_rows(rows, "peg_hole_contact_plate_count")
    final_servo_rows = [
        row for row in rows if row.get("guard_final_servo_active") == "True"
    ]
    low_z_rows = [
        row for row in rows if to_float(row, "post_z_above_target") <= low_z_m
    ]
    low_z_stall_rows = [
        row
        for row in low_z_rows
        if abs(to_float(row, "tip_z_delta")) <= stall_z_delta_m
    ]
    insert_band_rows = [
        row for row in rows if to_float(row, "post_dist_xy") <= insert_xy_m
    ]
    insert_contact_rows = [
        row
        for row in insert_band_rows
        if to_int(row, "peg_hole_contact_wall_count") > 0
        or to_int(row, "peg_hole_contact_plate_count") > 0
    ]

    final_contact_dist_values = [
        to_float(row, "peg_hole_contact_min_dist")
        for row in rows[-min(50, steps) :]
        if to_int(row, "peg_hole_contact_count") > 0
    ]

    return {
        "trace": str(path),
        "seed": last.get("seed", ""),
        "geometry_profile": last.get("geometry_profile", ""),
        "geometry_name": last.get("geometry_name", ""),
        "outcome": last.get("episode_outcome", ""),
        "steps": steps,
        "final_servo_steps": len(final_servo_rows),
        "contact_steps": len(peg_contact_rows),
        "contact_frac": len(peg_contact_rows) / steps,
        "wall_contact_steps": len(wall_rows),
        "wall_contact_frac": len(wall_rows) / steps,
        "plate_contact_steps": len(plate_rows),
        "plate_contact_frac": len(plate_rows) / steps,
        "first_contact_step": first_step(peg_contact_rows),
        "first_wall_contact_step": first_step(wall_rows),
        "insert_band_steps": len(insert_band_rows),
        "insert_band_contact_steps": len(insert_contact_rows),
        "insert_band_contact_frac": (
            len(insert_contact_rows) / len(insert_band_rows)
            if insert_band_rows
            else math.nan
        ),
        "low_z_steps": len(low_z_rows),
        "low_z_stall_steps": len(low_z_stall_rows),
        "low_z_stall_frac": len(low_z_stall_rows) / len(low_z_rows)
        if low_z_rows
        else math.nan,
        "final_contact_walls": active_walls(last),
        "final_contact_pairs": last.get("peg_hole_contact_pairs", ""),
        "pair_step_counts": summarize_pairs(rows),
        "min_contact_dist_mm": min_f(peg_contact_rows, "peg_hole_contact_min_dist")
        * 1000.0,
        "final_window_mean_contact_dist_mm": mean_f(final_contact_dist_values)
        * 1000.0,
        "min_xy_mm": min_f(rows, "post_dist_xy") * 1000.0,
        "final_xy_mm": last_f(rows, "post_dist_xy") * 1000.0,
        "min_z_mm": min_f(rows, "post_dist_z") * 1000.0,
        "final_z_mm": last_f(rows, "post_dist_z") * 1000.0,
        "final_z_above_target_mm": last_f(rows, "post_z_above_target") * 1000.0,
        "max_tilt_deg": max_f(rows, "peg_tilt_angle_deg"),
        "final_tilt_deg": last_f(rows, "peg_tilt_angle_deg"),
        "final_yaw_error_deg": last_f(rows, "square_peg_yaw_error_deg"),
        "final_tilted_margin_mm": last_f(
            rows, "square_peg_tilted_clearance_margin"
        )
        * 1000.0,
        "final_servo_phase_counts": phase_summary(
            final_servo_rows, "guard_final_servo_phase"
        ),
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
        "geometry_name",
        "outcome",
        "steps",
        "contact_frac",
        "wall_contact_frac",
        "plate_contact_frac",
        "first_wall_contact_step",
        "insert_band_steps",
        "insert_band_contact_frac",
        "low_z_stall_frac",
        "final_contact_walls",
        "min_contact_dist_mm",
        "final_xy_mm",
        "final_z_mm",
        "final_z_above_target_mm",
        "final_tilt_deg",
        "final_yaw_error_deg",
        "final_tilted_margin_mm",
        "final_servo_phase_counts",
    ]
    lines = [
        "# Final Insert Contact Trace Summary",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row[column]) for column in columns) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = [
        summarize_trace(
            path,
            insert_xy_m=args.insert_xy_m,
            low_z_m=args.low_z_m,
            stall_z_delta_m=args.stall_z_delta_m,
        )
        for path in args.input
    ]
    if args.output_csv is not None:
        write_csv(args.output_csv, rows)
    if args.output_md is not None:
        write_markdown(args.output_md, rows)
    if args.output_csv is None and args.output_md is None:
        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
