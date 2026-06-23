"""Analyze rectangular-key tight-yaw failure modes from eval traces.

This is an offline sim diagnostic. It compares recorded visual-yaw predictions
with sim truth already present in step traces, so the output must not be used as
real-robot labels.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


def _float(row: dict[str, str], key: str, default: float = float("nan")) -> float:
    try:
        value = row.get(key, "")
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(row: dict[str, str], key: str, default: int = 0) -> int:
    try:
        value = row.get(key, "")
        if value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _bool(row: dict[str, str], key: str) -> bool:
    value = str(row.get(key, "")).strip().lower()
    return value in {"1", "1.0", "true", "yes"}


def _wrap_delta_deg(value: float, period_deg: float = 360.0) -> float:
    if not math.isfinite(value) or period_deg <= 0.0:
        return float("nan")
    return (value + 0.5 * period_deg) % period_deg - 0.5 * period_deg


def _fmt(value: float, digits: int = 3) -> str:
    if not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return float("nan")
    return float(numerator) / float(denominator)


@dataclass
class EpisodeRecord:
    run: str
    episode_file: str
    step_file: str
    seed: str
    episode: str
    outcome: str
    success: bool
    collision: bool
    timeout: bool
    steps: int
    final_dist_xy: float
    final_dist_z: float
    min_dist_xy: float
    min_dist_z: float
    final_shape_yaw_error_deg: float
    success_shape_yaw_error_deg: float
    success_shape_yaw_ok: bool
    final_peg_tilt_angle_deg: float
    low_z_steps: int
    low_z_misaligned_steps: int
    insert_band_steps: int
    insert_band_misaligned_steps: int
    visual_yaw_align_steps: int
    visual_yaw_align_blocked_steps: int
    final_servo_steps: int
    final_servo_descent_steps: int
    final_servo_recovery_triggers: int
    fixture_clearance_steps: int
    control_action_delay: int
    control_action_filter_alpha: float
    failure_mode: str = ""
    step_rows: int = 0
    last_step: str = ""
    last_pre_dist_xy: float = float("nan")
    last_pre_z_above_target: float = float("nan")
    last_true_signed_yaw_deg: float = float("nan")
    last_pred_signed_yaw_deg: float = float("nan")
    last_pred_abs_yaw_deg: float = float("nan")
    last_pose_ik_target_square_yaw_error_deg: float = float("nan")
    last_visual_yaw_reason: str = ""
    last_final_servo_phase: str = ""
    visual_yaw_reason_counts: Counter[str] = field(default_factory=Counter)
    temporal_gate_steps: int = 0
    low_visibility_brake_steps: int = 0
    target_hold_steps: int = 0
    aligned_descent_steps: int = 0
    blocked_down_rows: int = 0
    visible_prediction_rows: int = 0
    high_pred_rows: int = 0
    sign_mismatch_rows: int = 0
    high_error_rows: int = 0
    correct_high_yaw_visible_rows: int = 0
    correct_high_yaw_xy_gate_rows: int = 0
    correct_high_yaw_raw_norm_gate_rows: int = 0
    correct_high_yaw_inactive_rows: int = 0
    max_pred_abs_yaw_deg: float = float("nan")
    max_truth_abs_yaw_deg: float = float("nan")
    max_pred_truth_abs_error_deg: float = float("nan")
    final_window_pred_abs_mean_deg: float = float("nan")
    final_window_truth_abs_mean_deg: float = float("nan")
    final_window_pred_truth_abs_error_mean_deg: float = float("nan")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="Run label and directory as LABEL=PATH. May be repeated.",
    )
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--wrong-yaw-deg", type=float, default=90.0)
    parser.add_argument("--yaw-fail-deg", type=float, default=10.0)
    parser.add_argument("--near-xy-m", type=float, default=0.008)
    parser.add_argument("--far-xy-m", type=float, default=0.020)
    parser.add_argument("--low-z-m", type=float, default=0.030)
    parser.add_argument("--high-pred-deg", type=float, default=45.0)
    parser.add_argument("--sign-min-abs-deg", type=float, default=15.0)
    parser.add_argument("--pred-error-deg", type=float, default=30.0)
    parser.add_argument("--final-window", type=int, default=80)
    args = parser.parse_args()
    if args.final_window <= 0:
        raise ValueError("--final-window must be positive.")
    return args


def _parse_run_arg(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"--run must be LABEL=PATH, got: {value}")
    label, path = value.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"--run label is empty: {value}")
    return label, Path(path)


def _step_file_for_episode_csv(path: Path) -> Path:
    name = path.name
    if not name.endswith("_episodes.csv"):
        raise ValueError(f"Expected *_episodes.csv, got {path}")
    return path.with_name(name[: -len("_episodes.csv")] + "_steps.csv")


def _classify_failure(record: EpisodeRecord, args: argparse.Namespace) -> str:
    if record.success:
        return "success"
    if record.collision:
        return "collision"
    yaw = record.success_shape_yaw_error_deg
    if not math.isfinite(yaw):
        yaw = record.final_shape_yaw_error_deg
    if record.timeout and math.isfinite(yaw) and yaw >= args.wrong_yaw_deg:
        return "timeout_wrong_yaw_basin"
    if record.timeout and math.isfinite(yaw) and yaw > args.yaw_fail_deg:
        return "timeout_yaw_not_aligned"
    if record.timeout and record.min_dist_xy > args.near_xy_m:
        return "timeout_never_centered_xy"
    if record.timeout and record.min_dist_z > args.low_z_m:
        return "timeout_never_descended_low"
    if record.timeout and (record.low_z_misaligned_steps > 0 or record.insert_band_misaligned_steps > 0):
        return "timeout_low_z_or_insert_misaligned"
    if record.timeout and record.final_dist_xy > args.far_xy_m:
        return "timeout_recovery_drift"
    if record.timeout:
        return "timeout_other"
    return record.outcome or "unknown"


def _load_episode_records(run: str, run_dir: Path, args: argparse.Namespace) -> dict[tuple[str, str, str], EpisodeRecord]:
    records: dict[tuple[str, str, str], EpisodeRecord] = {}
    for episode_csv in sorted(run_dir.glob("*_episodes.csv")):
        step_csv = _step_file_for_episode_csv(episode_csv)
        with episode_csv.open(newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                seed = row.get("seed", "")
                episode = row.get("episode", "")
                record = EpisodeRecord(
                    run=run,
                    episode_file=str(episode_csv),
                    step_file=str(step_csv) if step_csv.exists() else "",
                    seed=seed,
                    episode=episode,
                    outcome=row.get("outcome", ""),
                    success=_bool(row, "success"),
                    collision=_bool(row, "collision"),
                    timeout=_bool(row, "timeout"),
                    steps=_int(row, "steps"),
                    final_dist_xy=_float(row, "final_dist_xy"),
                    final_dist_z=_float(row, "final_dist_z"),
                    min_dist_xy=_float(row, "min_dist_xy"),
                    min_dist_z=_float(row, "min_dist_z"),
                    final_shape_yaw_error_deg=_float(row, "final_shape_yaw_error_deg"),
                    success_shape_yaw_error_deg=_float(row, "success_shape_yaw_error_deg"),
                    success_shape_yaw_ok=_bool(row, "success_shape_yaw_ok"),
                    final_peg_tilt_angle_deg=_float(row, "final_peg_tilt_angle_deg"),
                    low_z_steps=_int(row, "low_z_steps"),
                    low_z_misaligned_steps=_int(row, "low_z_misaligned_steps"),
                    insert_band_steps=_int(row, "insert_band_steps"),
                    insert_band_misaligned_steps=_int(row, "insert_band_misaligned_steps"),
                    visual_yaw_align_steps=_int(row, "visual_yaw_align_steps"),
                    visual_yaw_align_blocked_steps=_int(row, "visual_yaw_align_blocked_steps"),
                    final_servo_steps=_int(row, "final_servo_steps"),
                    final_servo_descent_steps=_int(row, "final_servo_descent_steps"),
                    final_servo_recovery_triggers=_int(row, "final_servo_recovery_triggers"),
                    fixture_clearance_steps=_int(row, "fixture_clearance_steps"),
                    control_action_delay=_int(row, "control_action_delay"),
                    control_action_filter_alpha=_float(row, "control_action_filter_alpha"),
                )
                record.failure_mode = _classify_failure(record, args)
                records[(str(step_csv), seed, episode)] = record
    return records


def _sign(value: float, min_abs: float) -> int:
    if not math.isfinite(value) or abs(value) < min_abs:
        return 0
    return 1 if value > 0.0 else -1


def _update_max(current: float, value: float) -> float:
    if not math.isfinite(value):
        return current
    if not math.isfinite(current):
        return value
    return max(current, value)


def _analyze_step_files(records: dict[tuple[str, str, str], EpisodeRecord], args: argparse.Namespace) -> None:
    records_by_file: dict[str, dict[tuple[str, str], EpisodeRecord]] = defaultdict(dict)
    for (step_file, seed, episode), record in records.items():
        if step_file:
            records_by_file[step_file][(seed, episode)] = record

    final_windows: dict[tuple[str, str, str], deque[tuple[float, float, float]]] = defaultdict(
        lambda: deque(maxlen=args.final_window)
    )

    for step_file, records_for_file in sorted(records_by_file.items()):
        path = Path(step_file)
        if not path.exists():
            continue
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                key2 = (row.get("seed", ""), row.get("episode", ""))
                record = records_for_file.get(key2)
                if record is None:
                    continue
                key3 = (step_file, key2[0], key2[1])
                record.step_rows += 1
                record.last_step = row.get("step", record.last_step)
                record.last_pre_dist_xy = _float(row, "pre_dist_xy", record.last_pre_dist_xy)
                record.last_pre_z_above_target = _float(
                    row, "pre_z_above_target", record.last_pre_z_above_target
                )
                record.last_final_servo_phase = row.get(
                    "guard_final_servo_phase", record.last_final_servo_phase
                )

                reason = row.get("guard_visual_yaw_align_reason", "")
                if reason:
                    record.last_visual_yaw_reason = reason
                    record.visual_yaw_reason_counts[reason] += 1
                    if reason.startswith("temporal_action_gate"):
                        record.temporal_gate_steps += 1

                if _bool(row, "guard_visual_yaw_align_low_visibility_brake"):
                    record.low_visibility_brake_steps += 1
                if _bool(row, "guard_visual_yaw_align_target_hold"):
                    record.target_hold_steps += 1
                if _bool(row, "guard_visual_yaw_align_aligned_descent"):
                    record.aligned_descent_steps += 1
                if _bool(row, "guard_visual_yaw_align_blocked_down"):
                    record.blocked_down_rows += 1

                pred_signed = _float(row, "guard_visual_yaw_align_pred_signed_error_deg")
                pred_abs = _float(row, "guard_visual_yaw_align_pred_abs_error_deg")
                true_signed = _float(row, "shape_yaw_signed_error_deg")
                pose_target = _float(row, "pose_ik_target_square_yaw_error_deg")
                if math.isfinite(pred_signed):
                    record.last_pred_signed_yaw_deg = pred_signed
                    record.max_pred_abs_yaw_deg = _update_max(
                        record.max_pred_abs_yaw_deg, abs(_wrap_delta_deg(pred_signed))
                    )
                if math.isfinite(pred_abs):
                    record.last_pred_abs_yaw_deg = pred_abs
                    if pred_abs >= args.high_pred_deg:
                        record.high_pred_rows += 1
                if math.isfinite(true_signed):
                    record.last_true_signed_yaw_deg = true_signed
                    record.max_truth_abs_yaw_deg = _update_max(
                        record.max_truth_abs_yaw_deg, abs(_wrap_delta_deg(true_signed))
                    )
                if math.isfinite(pose_target):
                    record.last_pose_ik_target_square_yaw_error_deg = pose_target

                if math.isfinite(pred_signed) and math.isfinite(true_signed):
                    abs_error = abs(_wrap_delta_deg(pred_signed - true_signed))
                    true_abs = abs(_wrap_delta_deg(true_signed))
                    pred_abs_wrapped = abs(_wrap_delta_deg(pred_signed))
                    record.max_pred_truth_abs_error_deg = _update_max(
                        record.max_pred_truth_abs_error_deg, abs_error
                    )
                    final_windows[key3].append(
                        (
                            pred_abs_wrapped,
                            true_abs,
                            abs_error,
                        )
                    )
                    if abs_error >= args.pred_error_deg:
                        record.high_error_rows += 1
                    pred_sign = _sign(pred_signed, args.sign_min_abs_deg)
                    true_sign = _sign(true_signed, args.sign_min_abs_deg)
                    if pred_sign != 0 and true_sign != 0 and pred_sign != true_sign:
                        record.sign_mismatch_rows += 1
                    is_visible = (
                        _float(row, "guard_visual_yaw_align_raw_norm") >= 0.08
                        and _float(row, "guard_visual_yaw_align_cam_std") >= 18.0
                        and _float(row, "guard_visual_yaw_align_crop_std") >= 16.0
                    )
                    if (
                        is_visible
                        and true_abs >= args.wrong_yaw_deg
                        and pred_abs_wrapped >= args.high_pred_deg
                        and abs_error <= args.pred_error_deg
                    ):
                        record.correct_high_yaw_visible_rows += 1
                        if reason == "xy_gate":
                            record.correct_high_yaw_xy_gate_rows += 1
                        elif reason == "raw_norm_gate":
                            record.correct_high_yaw_raw_norm_gate_rows += 1
                        elif reason == "inactive_phase":
                            record.correct_high_yaw_inactive_rows += 1

                if (
                    _float(row, "guard_visual_yaw_align_raw_norm") >= 0.08
                    and _float(row, "guard_visual_yaw_align_cam_std") >= 18.0
                    and _float(row, "guard_visual_yaw_align_crop_std") >= 16.0
                ):
                    record.visible_prediction_rows += 1

    for key, window in final_windows.items():
        record = records.get(key)
        if record is None or not window:
            continue
        record.final_window_pred_abs_mean_deg = sum(item[0] for item in window) / len(window)
        record.final_window_truth_abs_mean_deg = sum(item[1] for item in window) / len(window)
        record.final_window_pred_truth_abs_error_mean_deg = sum(item[2] for item in window) / len(window)


def _episode_rows(records: Iterable[EpisodeRecord]) -> list[dict[str, object]]:
    rows = []
    for record in sorted(records, key=lambda item: (item.run, int(item.seed or 0), int(item.episode or 0))):
        top_reasons = ";".join(
            f"{reason}:{count}" for reason, count in record.visual_yaw_reason_counts.most_common(3)
        )
        rows.append(
            {
                "run": record.run,
                "seed": record.seed,
                "episode": record.episode,
                "outcome": record.outcome,
                "failure_mode": record.failure_mode,
                "steps": record.steps,
                "final_dist_xy": _fmt(record.final_dist_xy, 6),
                "final_dist_z": _fmt(record.final_dist_z, 6),
                "min_dist_xy": _fmt(record.min_dist_xy, 6),
                "min_dist_z": _fmt(record.min_dist_z, 6),
                "success_shape_yaw_error_deg": _fmt(record.success_shape_yaw_error_deg),
                "final_shape_yaw_error_deg": _fmt(record.final_shape_yaw_error_deg),
                "final_peg_tilt_angle_deg": _fmt(record.final_peg_tilt_angle_deg),
                "low_z_misaligned_steps": record.low_z_misaligned_steps,
                "insert_band_misaligned_steps": record.insert_band_misaligned_steps,
                "visual_yaw_align_steps": record.visual_yaw_align_steps,
                "visual_yaw_align_blocked_steps": record.visual_yaw_align_blocked_steps,
                "final_servo_descent_steps": record.final_servo_descent_steps,
                "final_servo_recovery_triggers": record.final_servo_recovery_triggers,
                "fixture_clearance_steps": record.fixture_clearance_steps,
                "last_pre_dist_xy": _fmt(record.last_pre_dist_xy, 6),
                "last_pre_z_above_target": _fmt(record.last_pre_z_above_target, 6),
                "last_true_signed_yaw_deg": _fmt(record.last_true_signed_yaw_deg),
                "last_pred_signed_yaw_deg": _fmt(record.last_pred_signed_yaw_deg),
                "last_pose_ik_target_square_yaw_error_deg": _fmt(
                    record.last_pose_ik_target_square_yaw_error_deg
                ),
                "last_final_servo_phase": record.last_final_servo_phase,
                "last_visual_yaw_reason": record.last_visual_yaw_reason,
                "top_visual_yaw_reasons": top_reasons,
                "temporal_gate_steps": record.temporal_gate_steps,
                "low_visibility_brake_steps": record.low_visibility_brake_steps,
                "target_hold_steps": record.target_hold_steps,
                "aligned_descent_steps": record.aligned_descent_steps,
                "blocked_down_rows": record.blocked_down_rows,
                "visible_prediction_rows": record.visible_prediction_rows,
                "high_pred_rows": record.high_pred_rows,
                "sign_mismatch_rows": record.sign_mismatch_rows,
                "high_error_rows": record.high_error_rows,
                "correct_high_yaw_visible_rows": record.correct_high_yaw_visible_rows,
                "correct_high_yaw_xy_gate_rows": record.correct_high_yaw_xy_gate_rows,
                "correct_high_yaw_raw_norm_gate_rows": record.correct_high_yaw_raw_norm_gate_rows,
                "correct_high_yaw_inactive_rows": record.correct_high_yaw_inactive_rows,
                "max_pred_abs_yaw_deg": _fmt(record.max_pred_abs_yaw_deg),
                "max_truth_abs_yaw_deg": _fmt(record.max_truth_abs_yaw_deg),
                "max_pred_truth_abs_error_deg": _fmt(record.max_pred_truth_abs_error_deg),
                "final_window_pred_abs_mean_deg": _fmt(record.final_window_pred_abs_mean_deg),
                "final_window_truth_abs_mean_deg": _fmt(record.final_window_truth_abs_mean_deg),
                "final_window_pred_truth_abs_error_mean_deg": _fmt(
                    record.final_window_pred_truth_abs_error_mean_deg
                ),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["run"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _mean(values: Iterable[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return float("nan")
    return sum(finite) / len(finite)


def _run_summary(records: list[EpisodeRecord]) -> list[dict[str, object]]:
    rows = []
    by_run: dict[str, list[EpisodeRecord]] = defaultdict(list)
    for record in records:
        by_run[record.run].append(record)
    for run, items in sorted(by_run.items()):
        failures = [item for item in items if not item.success]
        rows.append(
            {
                "run": run,
                "episodes": len(items),
                "success": sum(item.success for item in items),
                "success_rate": _ratio(sum(item.success for item in items), len(items)),
                "collision": sum(item.collision for item in items),
                "timeout": sum(item.timeout for item in items),
                "mean_steps": _mean(item.steps for item in items),
                "mean_failure_yaw_deg": _mean(
                    item.success_shape_yaw_error_deg for item in failures
                ),
                "mean_failure_min_xy_mm": 1000.0 * _mean(item.min_dist_xy for item in failures),
                "mean_failure_min_z_mm": 1000.0 * _mean(item.min_dist_z for item in failures),
                "mean_failure_final_xy_mm": 1000.0 * _mean(item.final_dist_xy for item in failures),
            }
        )
    return rows


def _failure_mode_summary(records: list[EpisodeRecord]) -> dict[str, Counter[str]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        counters[record.run][record.failure_mode] += 1
    return counters


def _opportunity_rows(records: list[EpisodeRecord]) -> list[dict[str, object]]:
    rows = []
    grouped: dict[tuple[str, str], list[EpisodeRecord]] = defaultdict(list)
    for record in records:
        outcome_group = "success" if record.success else "failure"
        grouped[(record.run, outcome_group)].append(record)
    for (run, outcome_group), items in sorted(grouped.items()):
        rows.append(
            {
                "run": run,
                "outcome_group": outcome_group,
                "episodes": len(items),
                "episodes_with_correct_high_yaw_visible": sum(
                    item.correct_high_yaw_visible_rows > 0 for item in items
                ),
                "correct_high_yaw_visible_rows": sum(
                    item.correct_high_yaw_visible_rows for item in items
                ),
                "correct_high_yaw_xy_gate_rows": sum(
                    item.correct_high_yaw_xy_gate_rows for item in items
                ),
                "correct_high_yaw_raw_norm_gate_rows": sum(
                    item.correct_high_yaw_raw_norm_gate_rows for item in items
                ),
                "correct_high_yaw_inactive_rows": sum(
                    item.correct_high_yaw_inactive_rows for item in items
                ),
            }
        )
    return rows


def _write_md(path: Path, args: argparse.Namespace, records: list[EpisodeRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    run_rows = _run_summary(records)
    mode_counts = _failure_mode_summary(records)
    failure_records = [record for record in records if not record.success]
    failure_records.sort(
        key=lambda item: (
            item.run,
            item.failure_mode,
            -item.success_shape_yaw_error_deg if math.isfinite(item.success_shape_yaw_error_deg) else 0.0,
            int(item.seed or 0),
        )
    )

    lines = [
        "# Key Yaw Failure Mode Analysis",
        "",
        "Offline sim diagnostic for rectangular-key tight-yaw traces.",
        "",
        f"- Wrong-yaw basin threshold: `{args.wrong_yaw_deg} deg`",
        f"- Yaw failure threshold: `{args.yaw_fail_deg} deg`",
        f"- Near XY threshold: `{1000.0 * args.near_xy_m:.1f} mm`",
        f"- Low-Z threshold: `{1000.0 * args.low_z_m:.1f} mm`",
        f"- Final prediction window: `{args.final_window}` steps",
        "",
        "## Run Summary",
        "",
        "| run | episodes | success | success rate | collision | timeout | mean steps | mean failure yaw deg | mean failure min XY mm | mean failure min Z mm | mean failure final XY mm |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in run_rows:
        lines.append(
            "| {run} | {episodes} | {success} | {success_rate} | {collision} | {timeout} | {mean_steps} | {mean_failure_yaw_deg} | {mean_failure_min_xy_mm} | {mean_failure_min_z_mm} | {mean_failure_final_xy_mm} |".format(
                run=row["run"],
                episodes=row["episodes"],
                success=row["success"],
                success_rate=_fmt(float(row["success_rate"])),
                collision=row["collision"],
                timeout=row["timeout"],
                mean_steps=_fmt(float(row["mean_steps"]), 1),
                mean_failure_yaw_deg=_fmt(float(row["mean_failure_yaw_deg"])),
                mean_failure_min_xy_mm=_fmt(float(row["mean_failure_min_xy_mm"]), 2),
                mean_failure_min_z_mm=_fmt(float(row["mean_failure_min_z_mm"]), 2),
                mean_failure_final_xy_mm=_fmt(float(row["mean_failure_final_xy_mm"]), 2),
            )
        )

    lines.extend(["", "## Failure Mode Breakdown", ""])
    for run in sorted(mode_counts):
        lines.append(f"### {run}")
        lines.append("")
        lines.append("| mode | episodes |")
        lines.append("| --- | ---: |")
        for mode, count in mode_counts[run].most_common():
            if mode == "success":
                continue
            lines.append(f"| {mode} | {count} |")
        lines.append("")

    lines.extend(
        [
            "## Correct High-Yaw Visual Evidence",
            "",
            "Rows counted here have visible observations, true key yaw in the wrong basin, predicted yaw also large, and prediction/truth error within the configured threshold.",
            "",
            "| run | outcome | episodes | episodes with evidence | evidence rows | xy-gate rows | raw-norm rows | inactive rows |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _opportunity_rows(records):
        lines.append(
            "| {run} | {outcome_group} | {episodes} | {episodes_with_correct_high_yaw_visible} | {correct_high_yaw_visible_rows} | {correct_high_yaw_xy_gate_rows} | {correct_high_yaw_raw_norm_gate_rows} | {correct_high_yaw_inactive_rows} |".format(
                **row
            )
        )
    lines.append("")

    lines.extend(
        [
            "## Failure Episodes",
            "",
            "| run | seed | ep | mode | yaw deg | min XY mm | min Z mm | final XY mm | final Z mm | low-Z mis | insert mis | VY steps/block | temp gate | low-vis brake | correct high-yaw evidence/xygate | last true/pred yaw | last phase | top VY reasons |",
            "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for record in failure_records:
        top_reasons = "; ".join(
            f"{reason}:{count}" for reason, count in record.visual_yaw_reason_counts.most_common(2)
        )
        yaw = record.success_shape_yaw_error_deg
        if not math.isfinite(yaw):
            yaw = record.final_shape_yaw_error_deg
        lines.append(
            "| {run} | {seed} | {episode} | {mode} | {yaw} | {min_xy} | {min_z} | {final_xy} | {final_z} | {low_z_mis} | {insert_mis} | {vy_steps}/{vy_block} | {temp_gate} | {low_vis} | {evidence}/{xygate} | {true_yaw}/{pred_yaw} | {phase} | {reasons} |".format(
                run=record.run,
                seed=record.seed,
                episode=record.episode,
                mode=record.failure_mode,
                yaw=_fmt(yaw),
                min_xy=_fmt(1000.0 * record.min_dist_xy, 2),
                min_z=_fmt(1000.0 * record.min_dist_z, 2),
                final_xy=_fmt(1000.0 * record.final_dist_xy, 2),
                final_z=_fmt(1000.0 * record.final_dist_z, 2),
                low_z_mis=record.low_z_misaligned_steps,
                insert_mis=record.insert_band_misaligned_steps,
                vy_steps=record.visual_yaw_align_steps,
                vy_block=record.visual_yaw_align_blocked_steps,
                temp_gate=record.temporal_gate_steps,
                low_vis=record.low_visibility_brake_steps,
                evidence=record.correct_high_yaw_visible_rows,
                xygate=record.correct_high_yaw_xy_gate_rows,
                true_yaw=_fmt(record.last_true_signed_yaw_deg),
                pred_yaw=_fmt(record.last_pred_signed_yaw_deg),
                phase=record.last_final_servo_phase,
                reasons=top_reasons,
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation Hints",
            "",
            "- `timeout_wrong_yaw_basin` means the final key yaw error is near a wrong asymmetric basin, usually around 180 deg for the key profile.",
            "- `timeout_yaw_not_aligned` means yaw is still outside the success tolerance but not in the fully flipped basin.",
            "- `timeout_low_z_or_insert_misaligned` means the episode reached low-Z or insertion-band states while still failing the yaw/XY success gates.",
            "- Large `low-vis brake` or `temporal gate` counts with no success usually means the current safety patch is converting risky descent into timeout rather than fixing yaw estimation.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    all_records: dict[tuple[str, str, str], EpisodeRecord] = {}
    for run_arg in args.run:
        label, path = _parse_run_arg(run_arg)
        records = _load_episode_records(label, path, args)
        all_records.update(records)

    _analyze_step_files(all_records, args)
    records = list(all_records.values())
    rows = _episode_rows(records)
    _write_csv(args.output_csv, rows)
    _write_md(args.output_md, args, records)

    for row in _run_summary(records):
        print(
            "{run}: {success}/{episodes} success, collision={collision}, timeout={timeout}".format(
                **row
            )
        )


if __name__ == "__main__":
    main()
