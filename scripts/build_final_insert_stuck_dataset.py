from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np


WALL_FIELDS = (
    "peg_hole_contact_hole_north",
    "peg_hole_contact_hole_south",
    "peg_hole_contact_hole_east",
    "peg_hole_contact_hole_west",
)

FEATURE_NAMES = (
    "rel_x",
    "rel_y",
    "z_above_target",
    "dist_xy",
    "dist_z",
    "peg_tilt_angle_deg",
    "square_peg_yaw_error_deg",
    "square_peg_topdown_clearance_margin",
    "square_peg_tilted_clearance_margin",
    "peg_hole_contact_wall_count",
    "peg_hole_contact_plate_count",
    "wall_north",
    "wall_south",
    "wall_east",
    "wall_west",
    "z_progress_window",
    "xy_progress_window",
    "guard_final_servo_phase_steps",
    "guard_final_servo_stall_steps",
)

CSV_FIELDNAMES = (
    "source_trace",
    "episode",
    "seed",
    "episode_outcome",
    "step",
    "geometry_profile",
    "geometry_name",
    "peg_shape",
    "hole_shape",
    "guard_final_servo_phase",
    "stuck_reason",
    "label_phase",
    "label_action_x",
    "label_action_y",
    "label_action_z",
    *FEATURE_NAMES,
    "post_peg_tip_x",
    "post_peg_tip_y",
    "post_peg_tip_z",
    "post_target_x",
    "post_target_y",
    "post_target_z",
    "post_dist_xy",
    "post_z_above_target",
    "hole_half_size",
    "peg_radius",
    "hole_clearance",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract near-hole final-insert stuck states from guarded eval step "
            "traces and assign conservative local correction labels."
        )
    )
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-npz", type=Path, default=None)
    parser.add_argument(
        "--geometry-name",
        nargs="*",
        default=["square_square"],
        help="Geometry names to keep. Use 'any' to disable geometry filtering.",
    )
    parser.add_argument(
        "--outcome",
        nargs="*",
        default=["timeout"],
        help="Episode outcomes to keep. Use 'any' to disable outcome filtering.",
    )
    parser.add_argument("--max-xy-m", type=float, default=0.008)
    parser.add_argument("--min-z-m", type=float, default=0.020)
    parser.add_argument("--max-z-m", type=float, default=0.055)
    parser.add_argument("--tilt-deg", type=float, default=8.0)
    parser.add_argument("--tilted-margin-m", type=float, default=-0.001)
    parser.add_argument("--stall-window-steps", type=int, default=20)
    parser.add_argument("--stall-min-z-progress-m", type=float, default=0.0005)
    parser.add_argument("--stall-min-xy-progress-m", type=float, default=0.0002)
    parser.add_argument("--sample-stride", type=int, default=4)
    parser.add_argument("--max-samples-per-episode", type=int, default=256)
    parser.add_argument("--label-release-xy-m", type=float, default=0.0048)
    parser.add_argument("--label-max-xy-action-m", type=float, default=0.0020)
    parser.add_argument("--label-contact-max-xy-action-m", type=float, default=0.0012)
    parser.add_argument("--label-max-down-action-m", type=float, default=0.0008)
    parser.add_argument("--label-lift-action-m", type=float, default=0.0025)
    parser.add_argument("--label-wall-bias-m", type=float, default=0.0010)
    return parser.parse_args()


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


def finite_mean(values: Iterable[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else math.nan


def limit_xy(vector: np.ndarray, max_norm: float) -> np.ndarray:
    limited = np.asarray(vector, dtype=np.float64).copy()
    norm = float(np.linalg.norm(limited[:2]))
    if max_norm <= 0.0:
        limited[:2] = 0.0
    elif norm > max_norm:
        limited[:2] *= max_norm / norm
    return limited


def wall_relief_vector(row: dict[str, str], wall_bias_m: float) -> np.ndarray:
    relief = np.zeros(2, dtype=np.float64)
    if to_int(row, "peg_hole_contact_hole_east") > 0:
        relief[0] -= wall_bias_m
    if to_int(row, "peg_hole_contact_hole_west") > 0:
        relief[0] += wall_bias_m
    if to_int(row, "peg_hole_contact_hole_north") > 0:
        relief[1] -= wall_bias_m
    if to_int(row, "peg_hole_contact_hole_south") > 0:
        relief[1] += wall_bias_m
    return relief


def row_vector(row: dict[str, str], prefix: str) -> np.ndarray:
    return np.asarray(
        [
            to_float(row, f"{prefix}_x"),
            to_float(row, f"{prefix}_y"),
            to_float(row, f"{prefix}_z"),
        ],
        dtype=np.float64,
    )


def episode_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (row.get("source_trace", ""), row.get("episode", ""), row.get("seed", ""))


def compute_window_progress(
    rows: list[dict[str, str]],
    index: int,
    window_steps: int,
) -> tuple[float, float]:
    if index <= 0:
        return math.nan, math.nan
    start = max(0, index - window_steps)
    previous = rows[start]
    current = rows[index]
    z_progress = (
        to_float(previous, "post_z_above_target")
        - to_float(current, "post_z_above_target")
    )
    xy_progress = to_float(previous, "post_dist_xy") - to_float(current, "post_dist_xy")
    return z_progress, xy_progress


def keep_geometry(row: dict[str, str], geometry_names: set[str]) -> bool:
    return "any" in geometry_names or row.get("geometry_name", "") in geometry_names


def keep_outcome(row: dict[str, str], outcomes: set[str]) -> bool:
    return "any" in outcomes or row.get("episode_outcome", "") in outcomes


def classify_stuck_reason(
    row: dict[str, str],
    *,
    z_progress: float,
    xy_progress: float,
    tilt_deg: float,
    tilted_margin_m: float,
    stall_min_z_progress_m: float,
    stall_min_xy_progress_m: float,
) -> str | None:
    wall_contact = to_int(row, "peg_hole_contact_wall_count") > 0
    plate_contact = to_int(row, "peg_hole_contact_plate_count") > 0
    high_tilt = to_float(row, "peg_tilt_angle_deg") >= tilt_deg
    threshold = to_float(row, "stuck_tilted_margin_threshold", tilted_margin_m)
    negative_margin = to_float(row, "square_peg_tilted_clearance_margin") <= threshold
    z_stalled = math.isfinite(z_progress) and z_progress <= stall_min_z_progress_m
    xy_stalled = math.isfinite(xy_progress) and abs(xy_progress) <= stall_min_xy_progress_m

    reasons: list[str] = []
    if wall_contact:
        reasons.append("wall_contact")
    if plate_contact:
        reasons.append("plate_contact")
    if high_tilt:
        reasons.append("high_tilt")
    if z_stalled and xy_stalled:
        reasons.append("progress_stall")
    if not reasons:
        return None
    if negative_margin:
        reasons.append("negative_tilted_margin")
    return "+".join(reasons)


def label_action(
    row: dict[str, str],
    *,
    release_xy_m: float,
    max_xy_action_m: float,
    contact_max_xy_action_m: float,
    max_down_action_m: float,
    lift_action_m: float,
    wall_bias_m: float,
    tilt_deg: float,
    tilted_margin_m: float,
) -> tuple[str, np.ndarray]:
    tip = row_vector(row, "post_peg_tip")
    target = row_vector(row, "post_target")
    rel = target - tip
    dist_xy = float(np.linalg.norm(rel[:2]))
    wall_contact = to_int(row, "peg_hole_contact_wall_count") > 0
    high_tilt = to_float(row, "peg_tilt_angle_deg") >= tilt_deg
    bad_margin = to_float(row, "square_peg_tilted_clearance_margin") <= tilted_margin_m

    xy = rel[:2] + wall_relief_vector(row, wall_bias_m)
    if wall_contact and (high_tilt or bad_margin):
        action = np.asarray([xy[0], xy[1], lift_action_m], dtype=np.float64)
        action = limit_xy(action, contact_max_xy_action_m)
        return "contact_lift", action
    if dist_xy > release_xy_m or wall_contact:
        action = np.asarray([xy[0], xy[1], 0.0], dtype=np.float64)
        action = limit_xy(action, max_xy_action_m)
        return "micro_recenter", action
    action = np.asarray([rel[0], rel[1], -max_down_action_m], dtype=np.float64)
    action = limit_xy(action, max_xy_action_m)
    return "soft_descend", action


def feature_values(
    row: dict[str, str],
    *,
    z_progress: float,
    xy_progress: float,
) -> dict[str, float]:
    tip = row_vector(row, "post_peg_tip")
    target = row_vector(row, "post_target")
    rel = target - tip
    return {
        "rel_x": float(rel[0]),
        "rel_y": float(rel[1]),
        "z_above_target": to_float(row, "post_z_above_target"),
        "dist_xy": to_float(row, "post_dist_xy"),
        "dist_z": to_float(row, "post_dist_z"),
        "peg_tilt_angle_deg": to_float(row, "peg_tilt_angle_deg"),
        "square_peg_yaw_error_deg": to_float(row, "square_peg_yaw_error_deg"),
        "square_peg_topdown_clearance_margin": to_float(
            row, "square_peg_topdown_clearance_margin"
        ),
        "square_peg_tilted_clearance_margin": to_float(
            row, "square_peg_tilted_clearance_margin"
        ),
        "peg_hole_contact_wall_count": float(to_int(row, "peg_hole_contact_wall_count")),
        "peg_hole_contact_plate_count": float(to_int(row, "peg_hole_contact_plate_count")),
        "wall_north": float(to_int(row, "peg_hole_contact_hole_north") > 0),
        "wall_south": float(to_int(row, "peg_hole_contact_hole_south") > 0),
        "wall_east": float(to_int(row, "peg_hole_contact_hole_east") > 0),
        "wall_west": float(to_int(row, "peg_hole_contact_hole_west") > 0),
        "z_progress_window": z_progress,
        "xy_progress_window": xy_progress,
        "guard_final_servo_phase_steps": float(
            to_int(row, "guard_final_servo_phase_steps")
        ),
        "guard_final_servo_stall_steps": float(
            to_int(row, "guard_final_servo_stall_steps")
        ),
    }


def selected_row(
    row: dict[str, str],
    *,
    source_trace: Path,
    stuck_reason: str,
    label_phase: str,
    label: np.ndarray,
    features: dict[str, float],
) -> dict[str, object]:
    output: dict[str, object] = {
        "source_trace": str(source_trace),
        "episode": row.get("episode", ""),
        "seed": row.get("seed", ""),
        "episode_outcome": row.get("episode_outcome", ""),
        "step": row.get("step", ""),
        "geometry_profile": row.get("geometry_profile", ""),
        "geometry_name": row.get("geometry_name", ""),
        "peg_shape": row.get("peg_shape", ""),
        "hole_shape": row.get("hole_shape", ""),
        "guard_final_servo_phase": row.get("guard_final_servo_phase", ""),
        "stuck_reason": stuck_reason,
        "label_phase": label_phase,
        "label_action_x": float(label[0]),
        "label_action_y": float(label[1]),
        "label_action_z": float(label[2]),
        **features,
        "post_peg_tip_x": to_float(row, "post_peg_tip_x"),
        "post_peg_tip_y": to_float(row, "post_peg_tip_y"),
        "post_peg_tip_z": to_float(row, "post_peg_tip_z"),
        "post_target_x": to_float(row, "post_target_x"),
        "post_target_y": to_float(row, "post_target_y"),
        "post_target_z": to_float(row, "post_target_z"),
        "post_dist_xy": to_float(row, "post_dist_xy"),
        "post_z_above_target": to_float(row, "post_z_above_target"),
        "hole_half_size": to_float(row, "hole_half_size"),
        "peg_radius": to_float(row, "peg_radius"),
        "hole_clearance": to_float(row, "hole_clearance"),
    }
    return output


def load_trace(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as file:
        rows = list(csv.DictReader(file))
    for row in rows:
        row["source_trace"] = str(path)
    return rows


def group_by_episode(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[episode_key(row)].append(row)
    return dict(grouped)


def extract_rows(args: argparse.Namespace) -> list[dict[str, object]]:
    geometry_names = {name.strip() for name in args.geometry_name}
    outcomes = {name.strip() for name in args.outcome}
    selected: list[dict[str, object]] = []

    for path in args.input:
        rows = load_trace(path)
        for episode_rows in group_by_episode(rows).values():
            episode_selected: list[dict[str, object]] = []
            for index, row in enumerate(episode_rows):
                if args.sample_stride > 1 and index % args.sample_stride != 0:
                    continue
                if not keep_geometry(row, geometry_names):
                    continue
                if not keep_outcome(row, outcomes):
                    continue
                if not is_true(row, "guard_final_servo_active"):
                    continue
                post_xy = to_float(row, "post_dist_xy")
                post_z = to_float(row, "post_z_above_target")
                if not (
                    post_xy <= args.max_xy_m
                    and args.min_z_m <= post_z <= args.max_z_m
                ):
                    continue
                z_progress, xy_progress = compute_window_progress(
                    episode_rows,
                    index,
                    args.stall_window_steps,
                )
                row["stuck_tilted_margin_threshold"] = str(args.tilted_margin_m)
                stuck_reason = classify_stuck_reason(
                    row,
                    z_progress=z_progress,
                    xy_progress=xy_progress,
                    tilt_deg=args.tilt_deg,
                    tilted_margin_m=args.tilted_margin_m,
                    stall_min_z_progress_m=args.stall_min_z_progress_m,
                    stall_min_xy_progress_m=args.stall_min_xy_progress_m,
                )
                if stuck_reason is None:
                    continue
                label_phase, label = label_action(
                    row,
                    release_xy_m=args.label_release_xy_m,
                    max_xy_action_m=args.label_max_xy_action_m,
                    contact_max_xy_action_m=args.label_contact_max_xy_action_m,
                    max_down_action_m=args.label_max_down_action_m,
                    lift_action_m=args.label_lift_action_m,
                    wall_bias_m=args.label_wall_bias_m,
                    tilt_deg=args.tilt_deg,
                    tilted_margin_m=args.tilted_margin_m,
                )
                features = feature_values(
                    row,
                    z_progress=z_progress,
                    xy_progress=xy_progress,
                )
                episode_selected.append(
                    selected_row(
                        row,
                        source_trace=path,
                        stuck_reason=stuck_reason,
                        label_phase=label_phase,
                        label=label,
                        features=features,
                    )
                )
                if len(episode_selected) >= args.max_samples_per_episode:
                    break
            selected.extend(episode_selected)
    return selected


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_npz(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    features = np.asarray(
        [[float(row[name]) for name in FEATURE_NAMES] for row in rows],
        dtype=np.float32,
    )
    actions = np.asarray(
        [
            [
                float(row["label_action_x"]),
                float(row["label_action_y"]),
                float(row["label_action_z"]),
            ]
            for row in rows
        ],
        dtype=np.float32,
    )
    np.savez_compressed(
        path,
        features=features,
        target_actions=actions,
        feature_names=np.asarray(FEATURE_NAMES),
        label_phase=np.asarray([row["label_phase"] for row in rows]),
        stuck_reason=np.asarray([row["stuck_reason"] for row in rows]),
        geometry_name=np.asarray([row["geometry_name"] for row in rows]),
        source_trace=np.asarray([row["source_trace"] for row in rows]),
        episode=np.asarray([row["episode"] for row in rows]),
        seed=np.asarray([row["seed"] for row in rows]),
        step=np.asarray([row["step"] for row in rows]),
    )


def fmt(value: object) -> str:
    if isinstance(value, float):
        if not math.isfinite(value):
            return "nan"
        return f"{value:.4f}"
    return str(value)


def mean_for(rows: list[dict[str, object]], key: str) -> float:
    return finite_mean(float(row[key]) for row in rows)


def write_markdown(path: Path, rows: list[dict[str, object]], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    label_counts = Counter(str(row["label_phase"]) for row in rows)
    reason_counts = Counter(str(row["stuck_reason"]) for row in rows)
    phase_counts = Counter(str(row["guard_final_servo_phase"]) for row in rows)
    episode_counts = Counter(
        (
            Path(str(row["source_trace"])).name,
            str(row["seed"]),
            str(row["episode"]),
            str(row["episode_outcome"]),
        )
        for row in rows
    )

    lines = [
        "# Final Insert Stuck Dataset Summary",
        "",
        "## Filters",
        "",
        f"- geometry_name: `{', '.join(args.geometry_name)}`",
        f"- outcome: `{', '.join(args.outcome)}`",
        f"- XY/Z window: `xy <= {args.max_xy_m:.4f} m`, "
        f"`{args.min_z_m:.4f} <= z <= {args.max_z_m:.4f} m`",
        f"- tilt / tilted margin: `tilt >= {args.tilt_deg:.1f} deg`, "
        f"`tilted_margin <= {args.tilted_margin_m:.4f} m`",
        f"- stall window: `{args.stall_window_steps}` steps, "
        f"`z_progress <= {args.stall_min_z_progress_m:.4f} m`",
        "",
        "## Summary",
        "",
        f"- selected samples: `{len(rows)}`",
        f"- trace episodes: `{len(episode_counts)}`",
        f"- mean XY/Z: `{mean_for(rows, 'post_dist_xy') * 1000.0:.2f} mm` / "
        f"`{mean_for(rows, 'post_z_above_target') * 1000.0:.2f} mm`",
        f"- mean tilt: `{mean_for(rows, 'peg_tilt_angle_deg'):.2f} deg`",
        f"- mean tilted margin: "
        f"`{mean_for(rows, 'square_peg_tilted_clearance_margin') * 1000.0:.2f} mm`",
        "",
        "## Label Phase Counts",
        "",
    ]
    for key, count in sorted(label_counts.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "## Stuck Reason Counts", ""])
    for key, count in sorted(reason_counts.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "## Guard Phase Counts", ""])
    for key, count in sorted(phase_counts.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(
        [
            "",
            "## Episode Counts",
            "",
            "| Trace | Seed | Episode | Outcome | Samples |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for (trace, seed, episode, outcome), count in sorted(episode_counts.items()):
        lines.append(f"| {trace} | {seed} | {episode} | {outcome} | {count} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.sample_stride <= 0:
        raise ValueError("--sample-stride must be positive.")
    if args.max_samples_per_episode <= 0:
        raise ValueError("--max-samples-per-episode must be positive.")
    if args.stall_window_steps <= 0:
        raise ValueError("--stall-window-steps must be positive.")
    rows = extract_rows(args)
    if not rows:
        raise RuntimeError("No stuck-state rows selected. Relax filters or check inputs.")
    write_csv(args.output_csv, rows)
    if args.output_npz is not None:
        write_npz(args.output_npz, rows)
    if args.output_md is not None:
        write_markdown(args.output_md, rows, args)
    print(f"selected {len(rows)} stuck states")
    print(f"wrote {args.output_csv}")
    if args.output_npz is not None:
        print(f"wrote {args.output_npz}")
    if args.output_md is not None:
        print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
