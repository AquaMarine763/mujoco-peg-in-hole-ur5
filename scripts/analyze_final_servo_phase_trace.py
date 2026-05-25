from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize guarded final-servo phase traces from eval step CSVs."
    )
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--success-xy", type=float, default=0.005)
    parser.add_argument("--success-z", type=float, default=0.010)
    return parser.parse_args()


def as_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def episode_key(row: dict[str, str], path: Path) -> tuple[str, str, str]:
    return (
        str(path),
        row.get("episode", ""),
        row.get("episode_outcome", ""),
    )


def summarize_episode(
    path: Path,
    rows: list[dict[str, str]],
    *,
    success_xy: float,
    success_z: float,
) -> dict[str, Any]:
    first = rows[0]
    last = rows[-1]
    phase_counts = Counter(row.get("guard_final_servo_phase", "missing") for row in rows)
    phase_transitions = 0
    previous_phase = None
    for row in rows:
        phase = row.get("guard_final_servo_phase", "missing")
        if previous_phase is not None and phase != previous_phase:
            phase_transitions += 1
        previous_phase = phase

    final_servo_rows = [
        row for row in rows if row.get("guard_final_servo_active", "False") == "True"
    ]
    success_band_rows = [
        row
        for row in rows
        if as_float(row, "post_dist_xy", float("inf")) <= success_xy
        and as_float(row, "post_dist_z", float("inf")) <= success_z
    ]
    near_square_rows = [
        row
        for row in rows
        if row.get("peg_shape", "") == "square"
        and as_float(row, "post_dist_xy", float("inf")) <= 0.008
        and as_float(row, "post_dist_z", float("inf")) <= 0.040
        and as_float(row, "peg_hole_contact_wall_count", float("inf")) <= 0
        and as_float(row, "peg_tilt_angle_deg", float("inf")) <= 8.0
    ]

    min_xy = min(as_float(row, "post_dist_xy", float("inf")) for row in rows)
    min_z = min(as_float(row, "post_dist_z", float("inf")) for row in rows)

    summary: dict[str, Any] = {
        "source": str(path),
        "episode": first.get("episode", ""),
        "seed": first.get("seed", ""),
        "outcome": first.get("episode_outcome", ""),
        "steps": len(rows),
        "final_servo_steps": len(final_servo_rows),
        "phase_transitions": phase_transitions,
        "final_phase": last.get("guard_final_servo_phase", ""),
        "final_xy": as_float(last, "post_dist_xy", float("nan")),
        "final_z": as_float(last, "post_dist_z", float("nan")),
        "min_xy": min_xy,
        "min_z": min_z,
        "success_band_rows": len(success_band_rows),
        "near_square_fast_settle_rows": len(near_square_rows),
        "final_retry_count": last.get("guard_final_servo_retry_count", ""),
        "final_tilt_deg": as_float(last, "peg_tilt_angle_deg", float("nan")),
        "final_wall_contacts": last.get("peg_hole_contact_wall_count", ""),
    }
    for phase, count in sorted(phase_counts.items()):
        summary[f"phase_{phase}"] = count
    return summary


def load_summaries(paths: list[Path], success_xy: float, success_z: float) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            groups: dict[tuple[str, str, str], list[dict[str, str]]] = {}
            for row in reader:
                groups.setdefault(episode_key(row, path), []).append(row)
        for rows in groups.values():
            if rows:
                summaries.append(
                    summarize_episode(
                        path,
                        rows,
                        success_xy=success_xy,
                        success_z=success_z,
                    )
                )
    return summaries


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
    lines = ["# Final Servo Phase Trace Summary", ""]
    for row in rows:
        lines.extend(
            [
                f"## {Path(str(row['source'])).name} episode {row['episode']}",
                "",
                f"- outcome: `{row['outcome']}`",
                f"- steps/final-servo steps: `{row['steps']}/{row['final_servo_steps']}`",
                f"- final phase/retry: `{row['final_phase']}/{row['final_retry_count']}`",
                f"- final XY/Z: `{row['final_xy']:.6f}/{row['final_z']:.6f}`",
                f"- min XY/Z: `{row['min_xy']:.6f}/{row['min_z']:.6f}`",
                f"- success-band rows: `{row['success_band_rows']}`",
                f"- near square-fast-settle candidate rows: `{row['near_square_fast_settle_rows']}`",
                f"- final tilt/wall contacts: `{row['final_tilt_deg']:.3f}/{row['final_wall_contacts']}`",
                "",
            ]
        )
        phase_items = sorted(
            (key.replace("phase_", ""), value)
            for key, value in row.items()
            if key.startswith("phase_")
        )
        lines.append("| Phase | Steps |")
        lines.append("| --- | ---: |")
        for phase, count in phase_items:
            lines.append(f"| `{phase}` | {count} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    summaries = load_summaries(args.input, args.success_xy, args.success_z)
    if args.output_csv is not None:
        write_csv(args.output_csv, summaries)
    if args.output_md is not None:
        write_md(args.output_md, summaries)
    if args.output_csv is None and args.output_md is None:
        for row in summaries:
            print(
                f"{Path(str(row['source'])).name} episode={row['episode']} "
                f"outcome={row['outcome']} final={row['final_xy']:.4f}/{row['final_z']:.4f} "
                f"final_servo_steps={row['final_servo_steps']} "
                f"near_fast_settle={row['near_square_fast_settle_rows']}"
            )


if __name__ == "__main__":
    main()
