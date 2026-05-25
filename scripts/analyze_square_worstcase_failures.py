from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze square-square narrow-clearance final insertion failures."
    )
    parser.add_argument("--steps", nargs="+", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--success-xy", type=float, default=0.005)
    parser.add_argument("--success-z", type=float, default=0.010)
    parser.add_argument("--near-xy", type=float, default=0.008)
    parser.add_argument("--near-z", type=float, default=0.040)
    parser.add_argument("--tilt-limit-deg", type=float, default=8.0)
    return parser.parse_args()


def to_float(row: dict[str, str], key: str, default: float = float("nan")) -> float:
    value = row.get(key, "")
    if value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def to_int(row: dict[str, str], key: str, default: int = 0) -> int:
    value = row.get(key, "")
    if value == "":
        return default
    try:
        return int(float(value))
    except ValueError:
        return default


def to_bool(row: dict[str, str], key: str) -> bool:
    return row.get(key, "").lower() == "true"


def finite_min(values: list[float]) -> float:
    finite = [value for value in values if value == value]
    return min(finite) if finite else float("nan")


def finite_max(values: list[float]) -> float:
    finite = [value for value in values if value == value]
    return max(finite) if finite else float("nan")


def episode_key(path: Path, row: dict[str, str]) -> tuple[str, str]:
    return (str(path), row.get("episode", ""))


def classify_episode(
    rows: list[dict[str, str]],
    *,
    success_xy: float,
    success_z: float,
    near_xy: float,
    near_z: float,
) -> str:
    last = rows[-1]
    if to_bool(last, "success"):
        return "success"
    final_servo_rows = [
        row for row in rows if row.get("guard_final_servo_active") == "True"
    ]
    if not final_servo_rows:
        return "approach_no_final_servo"
    near_rows = [
        row
        for row in rows
        if to_float(row, "post_dist_xy", float("inf")) <= near_xy
        and to_float(row, "post_dist_z", float("inf")) <= near_z
    ]
    success_band_rows = [
        row
        for row in rows
        if to_float(row, "post_dist_xy", float("inf")) <= success_xy
        and to_float(row, "post_dist_z", float("inf")) <= success_z
    ]
    contact_near_rows = [
        row for row in near_rows if to_int(row, "peg_hole_contact_wall_count") > 0
    ]
    if success_band_rows:
        return "success_band_not_terminated"
    if contact_near_rows:
        return "near_xy_contact_high_z"
    if near_rows:
        return "near_xy_high_z_no_contact"
    return "approach_or_alignment_timeout"


def phase_transitions(rows: list[dict[str, str]]) -> list[tuple[str, str, float, float, float, int]]:
    transitions: list[tuple[str, str, float, float, float, int]] = []
    previous = None
    for row in rows:
        phase = row.get("guard_final_servo_phase", "")
        if phase != previous:
            transitions.append(
                (
                    row.get("step", ""),
                    phase,
                    to_float(row, "post_dist_xy") * 1000.0,
                    to_float(row, "post_dist_z") * 1000.0,
                    to_float(row, "peg_tilt_angle_deg"),
                    to_int(row, "peg_hole_contact_wall_count"),
                )
            )
            previous = phase
    return transitions


def summarize_episode(
    path: Path,
    rows: list[dict[str, str]],
    *,
    success_xy: float,
    success_z: float,
    near_xy: float,
    near_z: float,
    tilt_limit_deg: float,
) -> dict[str, Any]:
    first = rows[0]
    last = rows[-1]
    phases = Counter(row.get("guard_final_servo_phase", "") for row in rows)
    final_servo_rows = [
        row for row in rows if row.get("guard_final_servo_active") == "True"
    ]
    fast_rows = [
        row for row in rows if row.get("guard_final_servo_phase") == "square_fast_settle"
    ]
    near_rows = [
        row
        for row in rows
        if to_float(row, "post_dist_xy", float("inf")) <= near_xy
        and to_float(row, "post_dist_z", float("inf")) <= near_z
    ]
    near_contact_rows = [
        row for row in near_rows if to_int(row, "peg_hole_contact_wall_count") > 0
    ]
    fast_rejected_by_contact_or_tilt = [
        row
        for row in rows
        if row.get("peg_shape") == "square"
        and to_float(row, "post_dist_xy", float("inf")) <= near_xy
        and to_float(row, "post_dist_z", float("inf")) <= near_z
        and (
            to_int(row, "peg_hole_contact_wall_count")
            + to_int(row, "peg_hole_contact_plate_count")
            > 0
            or to_float(row, "peg_tilt_angle_deg", 0.0) > tilt_limit_deg
        )
    ]

    transitions = phase_transitions(rows)
    non_inactive_transitions = [
        f"{step}:{phase}@xy={xy_mm:.1f},z={z_mm:.1f},tilt={tilt:.1f},wall={wall}"
        for step, phase, xy_mm, z_mm, tilt, wall in transitions
        if phase != "inactive"
    ]
    row: dict[str, Any] = {
        "source": str(path),
        "episode": first.get("episode", ""),
        "seed": first.get("seed", ""),
        "outcome": last.get("episode_outcome", ""),
        "classification": classify_episode(
            rows,
            success_xy=success_xy,
            success_z=success_z,
            near_xy=near_xy,
            near_z=near_z,
        ),
        "steps": len(rows),
        "final_servo_steps": len(final_servo_rows),
        "square_fast_settle_steps": len(fast_rows),
        "near_xy_high_z_steps": len(near_rows),
        "near_xy_contact_high_z_steps": len(near_contact_rows),
        "fast_settle_rejected_by_contact_or_tilt_steps": len(
            fast_rejected_by_contact_or_tilt
        ),
        "final_phase": last.get("guard_final_servo_phase", ""),
        "final_xy_mm": to_float(last, "post_dist_xy") * 1000.0,
        "final_z_mm": to_float(last, "post_dist_z") * 1000.0,
        "min_xy_mm": finite_min([to_float(row, "post_dist_xy") for row in rows]) * 1000.0,
        "min_z_mm": finite_min([to_float(row, "post_dist_z") for row in rows]) * 1000.0,
        "final_tilt_deg": to_float(last, "peg_tilt_angle_deg"),
        "max_tilt_deg": finite_max([to_float(row, "peg_tilt_angle_deg") for row in rows]),
        "final_yaw_error_deg": to_float(last, "square_peg_yaw_error_deg"),
        "max_abs_yaw_error_deg": finite_max(
            [abs(to_float(row, "square_peg_yaw_error_deg")) for row in rows]
        ),
        "final_wall_contacts": to_int(last, "peg_hole_contact_wall_count"),
        "max_wall_contacts": max(to_int(row, "peg_hole_contact_wall_count") for row in rows),
        "min_tilted_clearance_margin_mm": finite_min(
            [to_float(row, "square_peg_tilted_clearance_margin") for row in rows]
        )
        * 1000.0,
        "final_tilted_clearance_margin_mm": to_float(
            last,
            "square_peg_tilted_clearance_margin",
        )
        * 1000.0,
        "hole_clearance_mm": to_float(last, "hole_clearance") * 1000.0,
        "control_scale": to_float(last, "control_action_scale_multiplier"),
        "control_noise_mm": to_float(last, "control_action_noise_std") * 1000.0,
        "control_delay": to_int(last, "control_action_delay"),
        "control_filter_alpha": to_float(last, "control_action_filter_alpha"),
        "phase_transitions": " | ".join(non_inactive_transitions),
    }
    for phase, count in sorted(phases.items()):
        row[f"phase_{phase}"] = count
    return row


def load_summaries(args: argparse.Namespace) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    paths: dict[tuple[str, str], Path] = {}
    for path in args.steps:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                key = episode_key(path, row)
                groups.setdefault(key, []).append(row)
                paths[key] = path
    return [
        summarize_episode(
            paths[key],
            rows,
            success_xy=args.success_xy,
            success_z=args.success_z,
            near_xy=args.near_xy,
            near_z=args.near_z,
            tilt_limit_deg=args.tilt_limit_deg,
        )
        for key, rows in sorted(groups.items())
        if rows
    ]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    class_counts = Counter(row["classification"] for row in rows)
    outcome_counts = Counter(row["outcome"] for row in rows)
    lines = [
        "# Square Worst-Case Failure Analysis",
        "",
        "## Aggregate",
        "",
        f"- episodes: `{len(rows)}`",
        f"- outcomes: `{dict(outcome_counts)}`",
        f"- classifications: `{dict(class_counts)}`",
        "",
        "| Source | Ep | Outcome | Class | Final XY/Z mm | Min XY/Z mm | Tilt/Yaw deg | Wall | Fast/Near/Rejected Steps |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{Path(str(row['source'])).name}` | {row['episode']} | "
            f"`{row['outcome']}` | `{row['classification']}` | "
            f"{row['final_xy_mm']:.2f}/{row['final_z_mm']:.2f} | "
            f"{row['min_xy_mm']:.2f}/{row['min_z_mm']:.2f} | "
            f"{row['final_tilt_deg']:.2f}/{row['final_yaw_error_deg']:.2f} | "
            f"{row['final_wall_contacts']} | "
            f"{row['square_fast_settle_steps']}/"
            f"{row['near_xy_contact_high_z_steps']}/"
            f"{row['fast_settle_rejected_by_contact_or_tilt_steps']} |"
        )
    lines.append("")
    lines.append("## Episode Details")
    lines.append("")
    for row in rows:
        lines.extend(
            [
                f"### {Path(str(row['source'])).name} episode {row['episode']}",
                "",
                f"- outcome/class: `{row['outcome']}` / `{row['classification']}`",
                f"- final XY/Z: `{row['final_xy_mm']:.2f} mm / {row['final_z_mm']:.2f} mm`",
                f"- min XY/Z: `{row['min_xy_mm']:.2f} mm / {row['min_z_mm']:.2f} mm`",
                f"- final tilt/yaw: `{row['final_tilt_deg']:.2f} deg / {row['final_yaw_error_deg']:.2f} deg`",
                f"- clearance/final tilted margin: `{row['hole_clearance_mm']:.2f} mm / {row['final_tilted_clearance_margin_mm']:.2f} mm`",
                f"- final/max wall contacts: `{row['final_wall_contacts']}/{row['max_wall_contacts']}`",
                f"- control scale/noise/delay/filter: `{row['control_scale']:.3f}/{row['control_noise_mm']:.3f} mm/{row['control_delay']}/{row['control_filter_alpha']:.3f}`",
                f"- phase transitions: `{row['phase_transitions']}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = load_summaries(args)
    if args.output_csv is not None:
        write_csv(args.output_csv, rows)
    if args.output_md is not None:
        write_md(args.output_md, rows)
    if args.output_csv is None and args.output_md is None:
        for row in rows:
            print(
                f"{Path(str(row['source'])).name} ep={row['episode']} "
                f"{row['outcome']} {row['classification']} "
                f"final={row['final_xy_mm']:.2f}/{row['final_z_mm']:.2f}mm"
            )


if __name__ == "__main__":
    main()
