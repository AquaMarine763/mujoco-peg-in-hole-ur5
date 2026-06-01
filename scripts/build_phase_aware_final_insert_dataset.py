from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np

from build_final_insert_stuck_dataset import (
    FEATURE_NAMES,
    classify_stuck_reason,
    compute_window_progress,
    feature_values,
    finite_mean,
    is_true,
    label_action,
    limit_xy,
    row_vector,
    to_float,
    to_int,
    wall_relief_vector,
)


DEFAULT_FAILURE_CLASSES = (
    "macro_not_triggered_timeout",
    "macro_triggered_timeout_stuck_high_z",
    "macro_triggered_collision_diverged",
    "macro_triggered_timeout_diverged",
    "macro_triggered_collision",
    "macro_triggered_timeout",
    "collision_without_macro",
)

CSV_FIELDNAMES = (
    "source_episode_csv",
    "source_step_csv",
    "source_trace",
    "episode",
    "seed",
    "outcome",
    "failure_classification",
    "teacher_phase",
    "step",
    "geometry_profile",
    "geometry_name",
    "peg_shape",
    "hole_shape",
    "guard_final_servo_phase",
    "macro_active",
    "macro_phase",
    "macro_reason",
    "macro_attempt",
    "macro_steps_remaining",
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
            "Build a phase-aware final-insert correction dataset from guarded "
            "episode summaries and matching step traces. The output NPZ keeps "
            "the final-insert adapter schema while adding failure-class labels."
        )
    )
    parser.add_argument("--episode-csv", nargs="+", type=Path, required=True)
    parser.add_argument(
        "--step-csv",
        nargs="*",
        type=Path,
        default=None,
        help=(
            "Optional explicit step CSVs. If provided, the count must match "
            "--episode-csv. Otherwise *_steps.csv is inferred per episode file."
        ),
    )
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
        default=["timeout", "collision"],
        help="Episode outcomes to keep. Use 'any' to disable outcome filtering.",
    )
    parser.add_argument(
        "--failure-classification",
        nargs="*",
        default=list(DEFAULT_FAILURE_CLASSES),
        help="Failure classes to keep. Use 'any' to disable classification filtering.",
    )
    parser.add_argument("--max-xy-m", type=float, default=0.020)
    parser.add_argument("--min-z-m", type=float, default=0.005)
    parser.add_argument("--max-z-m", type=float, default=0.075)
    parser.add_argument(
        "--tail-window-steps",
        type=int,
        default=1000,
        help="Only sample rows within this many steps of episode end.",
    )
    parser.add_argument("--sample-stride", type=int, default=4)
    parser.add_argument("--max-samples-per-episode", type=int, default=256)
    parser.add_argument("--require-stuck-reason", action="store_true")
    parser.add_argument("--stall-window-steps", type=int, default=20)
    parser.add_argument("--stall-min-z-progress-m", type=float, default=0.0005)
    parser.add_argument("--stall-min-xy-progress-m", type=float, default=0.0002)
    parser.add_argument("--tilt-deg", type=float, default=8.0)
    parser.add_argument("--tilted-margin-m", type=float, default=-0.001)
    parser.add_argument("--label-release-xy-m", type=float, default=0.0048)
    parser.add_argument("--label-max-xy-action-m", type=float, default=0.0020)
    parser.add_argument("--label-contact-max-xy-action-m", type=float, default=0.0012)
    parser.add_argument("--label-max-down-action-m", type=float, default=0.0008)
    parser.add_argument("--label-lift-action-m", type=float, default=0.0025)
    parser.add_argument("--label-wall-bias-m", type=float, default=0.0010)
    parser.add_argument("--teacher-retreat-lift-action-m", type=float, default=0.0040)
    parser.add_argument("--teacher-safe-retreat-lift-action-m", type=float, default=0.0060)
    parser.add_argument("--teacher-retreat-max-xy-action-m", type=float, default=0.0012)
    parser.add_argument("--teacher-safe-retreat-max-xy-action-m", type=float, default=0.0008)
    parser.add_argument(
        "--handoff-teacher-enabled",
        action="store_true",
        help="Relabel aligned/no-wall high-Z states as handoff_descend instead of more retreat-lift.",
    )
    parser.add_argument("--handoff-xy-m", type=float, default=0.0020)
    parser.add_argument("--handoff-min-z-m", type=float, default=0.025)
    parser.add_argument("--handoff-max-z-m", type=float, default=0.060)
    parser.add_argument(
        "--handoff-failure-classification",
        nargs="*",
        default=["macro_not_triggered_timeout", "macro_triggered_timeout_stuck_high_z"],
        help="Failure classes where handoff teacher labels may be generated.",
    )
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


def paired_paths(args: argparse.Namespace) -> list[tuple[Path, Path]]:
    if args.step_csv is None or len(args.step_csv) == 0:
        return [(path, infer_step_csv(path)) for path in args.episode_csv]
    if len(args.step_csv) != len(args.episode_csv):
        raise ValueError("--step-csv count must match --episode-csv count.")
    return list(zip(args.episode_csv, args.step_csv))


def row_key(row: dict[str, str]) -> tuple[str, str]:
    return (row.get("seed", ""), row.get("episode", ""))


def group_step_rows(path: Path) -> dict[tuple[str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    if not path.exists():
        return grouped
    for row in read_csv(path):
        grouped[row_key(row)].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda row: to_int(row, "step"))
    return dict(grouped)


def finite(values: Iterable[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def max_f(rows: list[dict[str, str]], key: str) -> float:
    values = finite(to_float(row, key) for row in rows)
    return max(values) if values else math.nan


def macro_is_active(row: dict[str, str]) -> bool:
    return is_true(row, "final_insert_macro_recovery_active") or (
        row.get("final_insert_macro_recovery_phase", "inactive") not in ("", "inactive")
    )


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


def keep_name(value: str, allowed: set[str]) -> bool:
    return "any" in allowed or value in allowed


def safe_retreat_action(
    row: dict[str, str],
    *,
    lift_action_m: float,
    max_xy_action_m: float,
    wall_bias_m: float,
) -> np.ndarray:
    tip = row_vector(row, "post_peg_tip")
    target = row_vector(row, "post_target")
    rel = target - tip
    xy = 0.5 * rel[:2] + wall_relief_vector(row, wall_bias_m)
    action = np.asarray([xy[0], xy[1], lift_action_m], dtype=np.float64)
    return limit_xy(action, max_xy_action_m)


def retreat_recenter_action(
    row: dict[str, str],
    *,
    lift_action_m: float,
    max_xy_action_m: float,
    wall_bias_m: float,
) -> np.ndarray:
    tip = row_vector(row, "post_peg_tip")
    target = row_vector(row, "post_target")
    rel = target - tip
    xy = rel[:2] + wall_relief_vector(row, wall_bias_m)
    action = np.asarray([xy[0], xy[1], lift_action_m], dtype=np.float64)
    return limit_xy(action, max_xy_action_m)


def handoff_descend_action(row: dict[str, str], *, max_down_action_m: float) -> np.ndarray:
    tip = row_vector(row, "post_peg_tip")
    target = row_vector(row, "post_target")
    rel = target - tip
    action = np.asarray([rel[0], rel[1], -max_down_action_m], dtype=np.float64)
    return limit_xy(action, max_norm=0.0)


def should_label_handoff(
    row: dict[str, str],
    *,
    failure_classification: str,
    args: argparse.Namespace,
) -> bool:
    if not args.handoff_teacher_enabled:
        return False
    allowed_classes = {name.strip() for name in args.handoff_failure_classification}
    if failure_classification not in allowed_classes:
        return False
    if to_int(row, "peg_hole_contact_wall_count") > 0:
        return False
    post_xy = to_float(row, "post_dist_xy")
    post_z = to_float(row, "post_z_above_target")
    return (
        post_xy <= args.handoff_xy_m
        and args.handoff_min_z_m <= post_z <= args.handoff_max_z_m
    )


def teacher_label(
    row: dict[str, str],
    *,
    failure_classification: str,
    stuck_reason: str,
    args: argparse.Namespace,
) -> tuple[str, str, np.ndarray]:
    base_phase, base_action = label_action(
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

    wall_contact = to_int(row, "peg_hole_contact_wall_count") > 0
    high_tilt = to_float(row, "peg_tilt_angle_deg") >= args.tilt_deg
    bad_margin = to_float(row, "square_peg_tilted_clearance_margin") <= args.tilted_margin_m
    progress_stall = "progress_stall" in stuck_reason

    if should_label_handoff(
        row,
        failure_classification=failure_classification,
        args=args,
    ):
        action = handoff_descend_action(
            row,
            max_down_action_m=args.label_max_down_action_m,
        )
        return "handoff_descend", f"{failure_classification}_handoff_descend", action

    if failure_classification in (
        "macro_triggered_collision_diverged",
        "macro_triggered_timeout_diverged",
        "collision_without_macro",
    ):
        action = safe_retreat_action(
            row,
            lift_action_m=args.teacher_safe_retreat_lift_action_m,
            max_xy_action_m=args.teacher_safe_retreat_max_xy_action_m,
            wall_bias_m=args.label_wall_bias_m,
        )
        return "safe_retreat", "divergence_safe_retreat", action

    if failure_classification == "macro_triggered_timeout_stuck_high_z":
        if wall_contact or high_tilt or bad_margin or progress_stall:
            action = retreat_recenter_action(
                row,
                lift_action_m=args.teacher_retreat_lift_action_m,
                max_xy_action_m=args.teacher_retreat_max_xy_action_m,
                wall_bias_m=args.label_wall_bias_m,
            )
            return "retreat_lift", "stuck_high_z_retreat_lift", action
        if to_float(row, "post_dist_xy") > args.label_release_xy_m:
            action = retreat_recenter_action(
                row,
                lift_action_m=0.0,
                max_xy_action_m=args.label_max_xy_action_m,
                wall_bias_m=args.label_wall_bias_m,
            )
            return "retreat_recenter", "stuck_high_z_recenter", action
        return base_phase, f"stuck_high_z_{base_phase}", base_action

    if failure_classification == "macro_not_triggered_timeout":
        return base_phase, f"missed_trigger_{base_phase}", base_action

    if failure_classification == "macro_triggered_collision":
        action = safe_retreat_action(
            row,
            lift_action_m=args.teacher_retreat_lift_action_m,
            max_xy_action_m=args.teacher_retreat_max_xy_action_m,
            wall_bias_m=args.label_wall_bias_m,
        )
        return "contact_lift", "macro_collision_contact_lift", action

    return base_phase, f"macro_timeout_{base_phase}", base_action


def selected_row(
    row: dict[str, str],
    *,
    source_episode_csv: Path,
    source_step_csv: Path,
    outcome: str,
    failure_classification: str,
    stuck_reason: str,
    label_phase: str,
    teacher_phase: str,
    label: np.ndarray,
    features: dict[str, float],
) -> dict[str, object]:
    return {
        "source_episode_csv": str(source_episode_csv),
        "source_step_csv": str(source_step_csv),
        "source_trace": str(source_step_csv),
        "episode": row.get("episode", ""),
        "seed": row.get("seed", ""),
        "outcome": outcome,
        "failure_classification": failure_classification,
        "teacher_phase": teacher_phase,
        "step": row.get("step", ""),
        "geometry_profile": row.get("geometry_profile", ""),
        "geometry_name": row.get("geometry_name", ""),
        "peg_shape": row.get("peg_shape", ""),
        "hole_shape": row.get("hole_shape", ""),
        "guard_final_servo_phase": row.get("guard_final_servo_phase", ""),
        "macro_active": macro_is_active(row),
        "macro_phase": row.get("final_insert_macro_recovery_phase", ""),
        "macro_reason": row.get("final_insert_macro_recovery_reason", ""),
        "macro_attempt": to_int(row, "final_insert_macro_recovery_attempt"),
        "macro_steps_remaining": to_int(row, "final_insert_macro_recovery_steps_remaining"),
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


def extract_episode_rows(
    *,
    episode_row: dict[str, str],
    step_rows: list[dict[str, str]],
    source_episode_csv: Path,
    source_step_csv: Path,
    failure_classification: str,
    args: argparse.Namespace,
) -> list[dict[str, object]]:
    if not step_rows:
        return []
    end_step = max(to_int(row, "step") for row in step_rows)
    min_step = max(0, end_step - args.tail_window_steps)
    outcome = episode_row.get("outcome", "")
    selected: list[dict[str, object]] = []
    for index, row in enumerate(step_rows):
        if args.sample_stride > 1 and index % args.sample_stride != 0:
            continue
        if to_int(row, "step") < min_step:
            continue
        if not (is_true(row, "guard_final_servo_active") or macro_is_active(row)):
            continue
        post_xy = to_float(row, "post_dist_xy")
        post_z = to_float(row, "post_z_above_target")
        if not (post_xy <= args.max_xy_m and args.min_z_m <= post_z <= args.max_z_m):
            continue
        z_progress, xy_progress = compute_window_progress(
            step_rows,
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
            if args.require_stuck_reason:
                continue
            stuck_reason = "failure_tail"
        label_phase, teacher_phase, label = teacher_label(
            row,
            failure_classification=failure_classification,
            stuck_reason=stuck_reason,
            args=args,
        )
        features = feature_values(
            row,
            z_progress=z_progress,
            xy_progress=xy_progress,
        )
        selected.append(
            selected_row(
                row,
                source_episode_csv=source_episode_csv,
                source_step_csv=source_step_csv,
                outcome=outcome,
                failure_classification=failure_classification,
                stuck_reason=stuck_reason,
                label_phase=label_phase,
                teacher_phase=teacher_phase,
                label=label,
                features=features,
            )
        )
        if len(selected) >= args.max_samples_per_episode:
            break
    return selected


def extract_rows(args: argparse.Namespace) -> list[dict[str, object]]:
    geometry_names = {name.strip() for name in args.geometry_name}
    outcomes = {name.strip() for name in args.outcome}
    failure_classes = {name.strip() for name in args.failure_classification}
    rows: list[dict[str, object]] = []

    for episode_csv, step_csv in paired_paths(args):
        step_groups = group_step_rows(step_csv)
        for episode_row in read_csv(episode_csv):
            outcome = episode_row.get("outcome", "")
            if not keep_name(outcome, outcomes):
                continue
            if not keep_name(episode_row.get("geometry_name", ""), geometry_names):
                continue
            key = row_key(episode_row)
            step_rows = step_groups.get(key, [])
            macro_rows = [row for row in step_rows if macro_is_active(row)]
            failure_classification = classify_failure(
                outcome=outcome,
                macro_triggers=to_int(episode_row, "final_insert_macro_recovery_triggers"),
                final_xy=to_float(episode_row, "final_dist_xy"),
                final_z=to_float(episode_row, "final_dist_z"),
                max_macro_xy=max_f(macro_rows, "post_dist_xy"),
                args=args,
            )
            if not keep_name(failure_classification, failure_classes):
                continue
            rows.extend(
                extract_episode_rows(
                    episode_row=episode_row,
                    step_rows=step_rows,
                    source_episode_csv=episode_csv,
                    source_step_csv=step_csv,
                    failure_classification=failure_classification,
                    args=args,
                )
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(CSV_FIELDNAMES))
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
        label_phase=np.asarray([str(row["label_phase"]) for row in rows]),
        teacher_phase=np.asarray([str(row["teacher_phase"]) for row in rows]),
        failure_classification=np.asarray(
            [str(row["failure_classification"]) for row in rows]
        ),
        stuck_reason=np.asarray([str(row["stuck_reason"]) for row in rows]),
        macro_phase=np.asarray([str(row["macro_phase"]) for row in rows]),
        geometry_name=np.asarray([str(row["geometry_name"]) for row in rows]),
        source_trace=np.asarray([str(row["source_trace"]) for row in rows]),
        episode=np.asarray([str(row["episode"]) for row in rows]),
        seed=np.asarray([str(row["seed"]) for row in rows]),
        step=np.asarray([str(row["step"]) for row in rows]),
    )


def fmt(value: object) -> str:
    if isinstance(value, float):
        if not math.isfinite(value):
            return "nan"
        return f"{value:.4f}"
    return str(value)


def mean_for(rows: list[dict[str, object]], key: str) -> float:
    return finite_mean(float(row[key]) for row in rows)


def write_count_table(lines: list[str], title: str, counts: Counter[str]) -> None:
    lines.extend(["", f"## {title}", "", "| Name | Count |", "| --- | ---: |"])
    for key, count in sorted(counts.items()):
        lines.append(f"| `{key}` | {count} |")


def write_markdown(path: Path, rows: list[dict[str, object]], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    class_counts = Counter(str(row["failure_classification"]) for row in rows)
    teacher_counts = Counter(str(row["teacher_phase"]) for row in rows)
    label_counts = Counter(str(row["label_phase"]) for row in rows)
    macro_counts = Counter(str(row["macro_phase"]) or "inactive" for row in rows)
    episode_counts = Counter(
        (
            Path(str(row["source_episode_csv"])).name,
            str(row["seed"]),
            str(row["episode"]),
            str(row["outcome"]),
            str(row["failure_classification"]),
        )
        for row in rows
    )
    lines = [
        "# Phase-Aware Final Insert Dataset Summary",
        "",
        "## Filters",
        "",
        f"- geometry_name: `{', '.join(args.geometry_name)}`",
        f"- outcome: `{', '.join(args.outcome)}`",
        f"- failure_classification: `{', '.join(args.failure_classification)}`",
        f"- XY/Z window: `xy <= {args.max_xy_m:.4f} m`, "
        f"`{args.min_z_m:.4f} <= z <= {args.max_z_m:.4f} m`",
        f"- tail window: `{args.tail_window_steps}` steps",
        "",
        "## Summary",
        "",
        f"- selected samples: `{len(rows)}`",
        f"- trace episodes: `{len(episode_counts)}`",
        f"- mean XY/Z: `{mean_for(rows, 'post_dist_xy') * 1000.0:.2f} mm` / "
        f"`{mean_for(rows, 'post_z_above_target') * 1000.0:.2f} mm`",
        f"- mean tilt: `{mean_for(rows, 'peg_tilt_angle_deg'):.2f} deg`",
        f"- mean action Z: `{mean_for(rows, 'label_action_z') * 1000.0:.2f} mm`",
    ]
    write_count_table(lines, "Failure Class Counts", class_counts)
    write_count_table(lines, "Teacher Phase Counts", teacher_counts)
    write_count_table(lines, "Label Phase Counts", label_counts)
    write_count_table(lines, "Macro Phase Counts", macro_counts)
    lines.extend(
        [
            "",
            "## Episode Counts",
            "",
            "| Trace | Seed | Episode | Outcome | Failure Class | Samples |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for (trace, seed, episode, outcome, failure_class), count in sorted(episode_counts.items()):
        lines.append(
            f"| {trace} | {seed} | {episode} | {outcome} | {failure_class} | {count} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.sample_stride <= 0:
        raise ValueError("--sample-stride must be positive.")
    if args.max_samples_per_episode <= 0:
        raise ValueError("--max-samples-per-episode must be positive.")
    if args.stall_window_steps <= 0:
        raise ValueError("--stall-window-steps must be positive.")
    if args.tail_window_steps <= 0:
        raise ValueError("--tail-window-steps must be positive.")

    rows = extract_rows(args)
    if not rows:
        raise RuntimeError("No phase-aware rows selected. Relax filters or check inputs.")
    write_csv(args.output_csv, rows)
    if args.output_npz is not None:
        write_npz(args.output_npz, rows)
    if args.output_md is not None:
        write_markdown(args.output_md, rows, args)
    print(f"selected {len(rows)} phase-aware final-insert states")
    print(f"wrote {args.output_csv}")
    if args.output_npz is not None:
        print(f"wrote {args.output_npz}")
    if args.output_md is not None:
        print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
