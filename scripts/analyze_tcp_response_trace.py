from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize how commanded/applied Cartesian actions translate into "
            "actual peg-tip motion in eval_guarded_policy step traces."
        )
    )
    parser.add_argument(
        "--trace",
        action="append",
        required=True,
        help="Trace spec in the form label=path.csv. Repeat for multiple traces.",
    )
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--success-xy", type=float, default=0.005)
    parser.add_argument("--near-xy", type=float, default=0.012)
    parser.add_argument("--low-z", type=float, default=0.020)
    parser.add_argument("--last-steps", type=int, default=100)
    return parser.parse_args()


def parse_trace_spec(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise ValueError(f"--trace must be label=path.csv, got: {spec}")
    label, path_text = spec.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"Empty trace label in: {spec}")
    return label, Path(path_text)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def to_float(row: dict[str, str], key: str, default: float = float("nan")) -> float:
    value = row.get(key, "")
    if value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def to_bool(row: dict[str, str], key: str) -> bool:
    return str(row.get(key, "")).lower() in ("1", "true", "yes")


def finite(values: list[float]) -> np.ndarray:
    if not values:
        return np.asarray([], dtype=np.float64)
    array = np.asarray(values, dtype=np.float64)
    return array[np.isfinite(array)]


def mean(values: list[float]) -> float:
    array = finite(values)
    return float(np.mean(array)) if array.size else float("nan")


def median(values: list[float]) -> float:
    array = finite(values)
    return float(np.median(array)) if array.size else float("nan")


def rate(values: list[bool]) -> float:
    if not values:
        return float("nan")
    return float(np.mean(np.asarray(values, dtype=np.bool_)))


def norm_xy(x: float, y: float) -> float:
    return float(np.linalg.norm([x, y]))


def safe_ratio(numerator: float, denominator: float) -> float:
    if not np.isfinite(numerator) or not np.isfinite(denominator) or abs(denominator) < 1e-9:
        return float("nan")
    return float(numerator / denominator)


def alignment(a: np.ndarray, b: np.ndarray) -> float:
    a_norm = float(np.linalg.norm(a))
    b_norm = float(np.linalg.norm(b))
    if a_norm < 1e-9 or b_norm < 1e-9:
        return float("nan")
    return float(np.dot(a, b) / (a_norm * b_norm))


def step_metrics(row: dict[str, str]) -> dict[str, float | bool | str]:
    pre_tip = np.asarray(
        [
            to_float(row, "pre_peg_tip_x"),
            to_float(row, "pre_peg_tip_y"),
            to_float(row, "pre_peg_tip_z"),
        ],
        dtype=np.float64,
    )
    post_tip = np.asarray(
        [
            to_float(row, "post_peg_tip_x"),
            to_float(row, "post_peg_tip_y"),
            to_float(row, "post_peg_tip_z"),
        ],
        dtype=np.float64,
    )
    target = np.asarray(
        [
            to_float(row, "pre_target_x"),
            to_float(row, "pre_target_y"),
            to_float(row, "pre_target_z"),
        ],
        dtype=np.float64,
    )
    actual_delta = post_tip - pre_tip
    target_delta_xy = target[:2] - pre_tip[:2]
    final_action_xy = np.asarray(
        [to_float(row, "final_action_x", 0.0), to_float(row, "final_action_y", 0.0)],
        dtype=np.float64,
    )
    applied_action_xy = np.asarray(
        [
            to_float(row, "applied_action_x", 0.0),
            to_float(row, "applied_action_y", 0.0),
        ],
        dtype=np.float64,
    )
    actual_delta_xy = actual_delta[:2]

    final_xy_norm = float(np.linalg.norm(final_action_xy))
    applied_xy_norm = float(np.linalg.norm(applied_action_xy))
    actual_xy_norm = float(np.linalg.norm(actual_delta_xy))
    xy_progress = to_float(row, "pre_dist_xy") - to_float(row, "post_dist_xy")
    final_z = to_float(row, "final_action_z", 0.0)
    applied_z = to_float(row, "applied_action_z", 0.0)
    actual_z = float(actual_delta[2])

    return {
        "outcome": str(row.get("episode_outcome", "")),
        "guarded": to_bool(row, "guarded"),
        "guard_active": to_bool(row, "guard_active"),
        "retry_active": to_bool(row, "guard_retry_active"),
        "preinsert_active": to_bool(row, "guard_preinsert_recenter_active"),
        "final_servo_active": to_bool(row, "guard_final_servo_active"),
        "low_z_misaligned": (
            to_float(row, "pre_z_above_target") <= args_low_z
            and to_float(row, "pre_dist_xy") > args_success_xy
        ),
        "near_xy_misaligned": (
            to_float(row, "pre_dist_xy") <= args_near_xy
            and to_float(row, "pre_dist_xy") > args_success_xy
        ),
        "pre_dist_xy": to_float(row, "pre_dist_xy"),
        "pre_z_above_target": to_float(row, "pre_z_above_target"),
        "xy_progress": xy_progress,
        "final_xy_norm": final_xy_norm,
        "applied_xy_norm": applied_xy_norm,
        "actual_xy_norm": actual_xy_norm,
        "xy_progress_per_final_cmd": safe_ratio(xy_progress, final_xy_norm),
        "xy_progress_per_applied_cmd": safe_ratio(xy_progress, applied_xy_norm),
        "actual_xy_per_applied_xy": safe_ratio(actual_xy_norm, applied_xy_norm),
        "final_action_target_alignment": alignment(final_action_xy, target_delta_xy),
        "applied_action_target_alignment": alignment(applied_action_xy, target_delta_xy),
        "actual_motion_target_alignment": alignment(actual_delta_xy, target_delta_xy),
        "final_z": final_z,
        "applied_z": applied_z,
        "actual_z": actual_z,
        "actual_z_per_applied_z": safe_ratio(actual_z, applied_z),
        "action_tracking_error": to_float(row, "action_tracking_error"),
        "ik_target_error": to_float(row, "ik_target_error"),
        "ik_orientation_error": to_float(row, "ik_orientation_error"),
        "peg_tilt_angle_deg": to_float(row, "peg_tilt_angle_deg"),
        "joint_margin": to_float(row, "joint_limit_min_normalized_margin"),
        "control_delay": to_float(row, "control_action_delay"),
        "control_filter_alpha": to_float(row, "control_action_filter_alpha"),
        "control_scale": to_float(row, "control_action_scale_multiplier"),
    }


def window_rows(rows: list[dict[str, str]], name: str) -> list[dict[str, str]]:
    if name == "all":
        return rows
    if name == "last":
        return rows[-args_last_steps:]
    metrics = [step_metrics(row) for row in rows]
    selected: list[dict[str, str]] = []
    for row, metric in zip(rows, metrics, strict=True):
        if name == "guarded" and bool(metric["guarded"]):
            selected.append(row)
        elif name == "low_z_misaligned" and bool(metric["low_z_misaligned"]):
            selected.append(row)
        elif name == "near_xy_misaligned" and bool(metric["near_xy_misaligned"]):
            selected.append(row)
        elif name == "retry" and bool(metric["retry_active"]):
            selected.append(row)
        elif name == "preinsert" and bool(metric["preinsert_active"]):
            selected.append(row)
        elif name == "final_servo" and bool(metric["final_servo_active"]):
            selected.append(row)
    return selected


def summarize_window(
    *,
    label: str,
    episode: str,
    rows: list[dict[str, str]],
    window: str,
) -> dict[str, Any] | None:
    selected = window_rows(rows, window)
    if not selected:
        return None
    metrics = [step_metrics(row) for row in selected]
    first = selected[0]
    last = selected[-1]
    return {
        "label": label,
        "episode": int(float(episode)),
        "seed": first.get("seed", ""),
        "outcome": first.get("episode_outcome", ""),
        "window": window,
        "steps": len(selected),
        "start_step": int(float(first.get("step", "0") or 0)),
        "end_step": int(float(last.get("step", "0") or 0)),
        "start_xy_mm": 1000.0 * to_float(first, "pre_dist_xy"),
        "end_xy_mm": 1000.0 * to_float(last, "post_dist_xy"),
        "start_z_mm": 1000.0 * to_float(first, "pre_z_above_target"),
        "end_z_mm": 1000.0 * to_float(last, "post_z_above_target"),
        "mean_final_xy_cmd_mm": 1000.0 * mean([float(m["final_xy_norm"]) for m in metrics]),
        "mean_applied_xy_cmd_mm": 1000.0 * mean([float(m["applied_xy_norm"]) for m in metrics]),
        "mean_actual_xy_delta_mm": 1000.0 * mean([float(m["actual_xy_norm"]) for m in metrics]),
        "median_xy_progress_um": 1_000_000.0 * median([float(m["xy_progress"]) for m in metrics]),
        "mean_xy_progress_um": 1_000_000.0 * mean([float(m["xy_progress"]) for m in metrics]),
        "mean_progress_per_final_cmd": mean(
            [float(m["xy_progress_per_final_cmd"]) for m in metrics]
        ),
        "mean_progress_per_applied_cmd": mean(
            [float(m["xy_progress_per_applied_cmd"]) for m in metrics]
        ),
        "mean_actual_xy_per_applied_xy": mean(
            [float(m["actual_xy_per_applied_xy"]) for m in metrics]
        ),
        "mean_final_target_alignment": mean(
            [float(m["final_action_target_alignment"]) for m in metrics]
        ),
        "mean_actual_target_alignment": mean(
            [float(m["actual_motion_target_alignment"]) for m in metrics]
        ),
        "mean_final_z_cmd_mm": 1000.0 * mean([float(m["final_z"]) for m in metrics]),
        "mean_applied_z_cmd_mm": 1000.0 * mean([float(m["applied_z"]) for m in metrics]),
        "mean_actual_z_delta_um": 1_000_000.0 * mean([float(m["actual_z"]) for m in metrics]),
        "mean_actual_z_per_applied_z": mean(
            [float(m["actual_z_per_applied_z"]) for m in metrics]
        ),
        "guarded_rate": rate([bool(m["guarded"]) for m in metrics]),
        "retry_rate": rate([bool(m["retry_active"]) for m in metrics]),
        "preinsert_rate": rate([bool(m["preinsert_active"]) for m in metrics]),
        "final_servo_rate": rate([bool(m["final_servo_active"]) for m in metrics]),
        "mean_tracking_error_mm": 1000.0
        * mean([float(m["action_tracking_error"]) for m in metrics]),
        "mean_ik_target_error_mm": 1000.0 * mean([float(m["ik_target_error"]) for m in metrics]),
        "mean_ik_orientation_error": mean([float(m["ik_orientation_error"]) for m in metrics]),
        "mean_tilt_deg": mean([float(m["peg_tilt_angle_deg"]) for m in metrics]),
        "min_joint_margin": float(np.min(finite([float(m["joint_margin"]) for m in metrics]))),
        "control_delay": to_float(last, "control_action_delay"),
        "control_filter_alpha": to_float(last, "control_action_filter_alpha"),
        "control_scale": to_float(last, "control_action_scale_multiplier"),
    }


def format_value(value: Any) -> str:
    if isinstance(value, (bool, np.bool_)):
        return "true" if value else "false"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not np.isfinite(number):
        return "nan"
    if abs(number) >= 100:
        return f"{number:.1f}"
    if abs(number) >= 10:
        return f"{number:.2f}"
    if abs(number) >= 1:
        return f"{number:.3f}"
    return f"{number:.6f}"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]], specs: list[tuple[str, Path]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TCP Response Trace Analysis",
        "",
        "## Inputs",
        "",
    ]
    for label, trace_path in specs:
        lines.append(f"- `{label}`: `{trace_path}`")
    lines.extend(
        [
            "",
            "## Episode Windows",
            "",
            "| Label | Ep | Outcome | Window | Steps | XY start/end mm | Z start/end mm | Final XY cmd mm | Applied XY cmd mm | Actual XY delta mm | Progress um | Progress/final | Actual/applied XY | Final align | Actual align | Final Z cmd mm | Actual Z um | Z/applied | Guard | Retry | Preinsert | Final servo | IK target mm | Tracking mm | Tilt deg | Delay/filter/scale |",
            "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {label} | {episode} | {outcome} | {window} | {steps} | {xy} | {z} | {final_xy} | {applied_xy} | {actual_xy} | {progress} | {progress_ratio} | {actual_ratio} | {final_align} | {actual_align} | {final_z} | {actual_z} | {z_ratio} | {guard} | {retry} | {preinsert} | {final_servo} | {ik_target} | {tracking} | {tilt} | {control} |".format(
                label=row["label"],
                episode=row["episode"],
                outcome=row["outcome"],
                window=row["window"],
                steps=row["steps"],
                xy=(
                    f"{format_value(row['start_xy_mm'])}/"
                    f"{format_value(row['end_xy_mm'])}"
                ),
                z=(
                    f"{format_value(row['start_z_mm'])}/"
                    f"{format_value(row['end_z_mm'])}"
                ),
                final_xy=format_value(row["mean_final_xy_cmd_mm"]),
                applied_xy=format_value(row["mean_applied_xy_cmd_mm"]),
                actual_xy=format_value(row["mean_actual_xy_delta_mm"]),
                progress=format_value(row["mean_xy_progress_um"]),
                progress_ratio=format_value(row["mean_progress_per_final_cmd"]),
                actual_ratio=format_value(row["mean_actual_xy_per_applied_xy"]),
                final_align=format_value(row["mean_final_target_alignment"]),
                actual_align=format_value(row["mean_actual_target_alignment"]),
                final_z=format_value(row["mean_final_z_cmd_mm"]),
                actual_z=format_value(row["mean_actual_z_delta_um"]),
                z_ratio=format_value(row["mean_actual_z_per_applied_z"]),
                guard=format_value(row["guarded_rate"]),
                retry=format_value(row["retry_rate"]),
                preinsert=format_value(row["preinsert_rate"]),
                final_servo=format_value(row["final_servo_rate"]),
                ik_target=format_value(row["mean_ik_target_error_mm"]),
                tracking=format_value(row["mean_tracking_error_mm"]),
                tilt=format_value(row["mean_tilt_deg"]),
                control=(
                    f"{format_value(row['control_delay'])}/"
                    f"{format_value(row['control_filter_alpha'])}/"
                    f"{format_value(row['control_scale'])}"
                ),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


args_success_xy = 0.005
args_near_xy = 0.012
args_low_z = 0.020
args_last_steps = 100


def main() -> None:
    global args_success_xy, args_near_xy, args_low_z, args_last_steps
    args = parse_args()
    args_success_xy = args.success_xy
    args_near_xy = args.near_xy
    args_low_z = args.low_z
    args_last_steps = args.last_steps

    specs = [parse_trace_spec(spec) for spec in args.trace]
    output_rows: list[dict[str, Any]] = []
    windows = (
        "all",
        "last",
        "guarded",
        "low_z_misaligned",
        "near_xy_misaligned",
        "retry",
        "preinsert",
        "final_servo",
    )
    for label, trace_path in specs:
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in read_rows(trace_path):
            grouped[str(row["episode"])].append(row)
        for episode, rows in grouped.items():
            rows = sorted(rows, key=lambda row: int(float(row.get("step", "0") or 0)))
            for window in windows:
                summary = summarize_window(
                    label=label,
                    episode=episode,
                    rows=rows,
                    window=window,
                )
                if summary is not None:
                    output_rows.append(summary)

    output_rows.sort(
        key=lambda row: (
            str(row["label"]),
            int(row["episode"]),
            (
                "all",
                "last",
                "guarded",
                "low_z_misaligned",
                "near_xy_misaligned",
                "retry",
                "preinsert",
                "final_servo",
            ).index(str(row["window"])),
        )
    )
    write_markdown(args.output_md, output_rows, specs)
    print(f"saved markdown summary to {args.output_md}")
    if args.output_csv is not None:
        write_csv(args.output_csv, output_rows)
        print(f"saved csv summary to {args.output_csv}")


if __name__ == "__main__":
    main()
