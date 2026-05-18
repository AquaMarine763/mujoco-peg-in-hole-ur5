from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize eval_guarded_policy step traces by failure mode."
    )
    parser.add_argument(
        "--trace",
        action="append",
        required=True,
        help="Trace spec in the form label=path.csv. Repeat for multiple models.",
    )
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--near-xy", type=float, default=0.010)
    parser.add_argument("--far-xy", type=float, default=0.030)
    parser.add_argument("--low-z", type=float, default=0.020)
    parser.add_argument("--window-steps", type=int, default=20)
    return parser.parse_args()


def parse_trace_spec(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise ValueError(f"--trace must be label=path.csv, got: {spec}")
    label, path = spec.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"Empty trace label in: {spec}")
    return label, Path(path)


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


def bool_rate(values: list[bool]) -> float:
    if not values:
        return float("nan")
    return float(np.mean(np.asarray(values, dtype=np.bool_)))


def finite_mean(values: list[float]) -> float:
    if not values:
        return float("nan")
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    return float(np.mean(array)) if array.size else float("nan")


def finite_median(values: list[float]) -> float:
    if not values:
        return float("nan")
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    return float(np.median(array)) if array.size else float("nan")


def classify_failure_mode(
    *,
    outcome: str,
    guard_steps: int,
    final_xy: float,
    final_z: float,
    min_xy: float,
    ever_insert_band: bool,
    ever_low_z: bool,
    low_z_misaligned_steps: int,
    near_xy: float,
    far_xy: float,
    low_z: float,
) -> str:
    if outcome == "success":
        return "success"
    if guard_steps <= 0:
        if final_z <= 0.0 or final_xy >= far_xy:
            return "pre_guard_drop_or_drift"
        return "pre_guard_failure"
    if outcome == "collision":
        if ever_insert_band:
            return "insert_band_collision"
        if ever_low_z and final_xy > near_xy:
            return "low_z_misaligned_collision"
        return "high_fixture_wall_collision"
    if outcome == "timeout":
        if ever_insert_band:
            if low_z_misaligned_steps > 0:
                return "insert_band_timeout_low_z_drift"
            return "insert_band_timeout_slow_descent"
        if min_xy <= near_xy:
            return "near_xy_timeout_no_insert"
        if final_z <= low_z and final_xy > near_xy:
            return "low_z_misaligned_timeout"
        return "misaligned_timeout"
    return "other_failure"


def summarize_episode(
    label: str,
    episode: str,
    rows: list[dict[str, str]],
    *,
    success_xy_tolerance: float,
    near_xy: float,
    far_xy: float,
    low_z: float,
    window_steps: int,
) -> dict[str, Any]:
    rows = sorted(rows, key=lambda row: int(float(row.get("step", "0") or 0)))
    first = rows[0]
    last = rows[-1]
    recent = rows[-window_steps:]

    pre_xy = [to_float(row, "pre_dist_xy") for row in rows]
    pre_z = [to_float(row, "pre_z_above_target") for row in rows]
    post_xy = [to_float(row, "post_dist_xy") for row in rows]
    post_z = [to_float(row, "post_z_above_target") for row in rows]
    final_action_z = [to_float(row, "final_action_z") for row in rows]
    applied_action_z = [to_float(row, "applied_action_z") for row in rows]
    peg_tilt_angles = [to_float(row, "peg_tilt_angle_deg") for row in rows]
    ik_orientation_errors = [to_float(row, "ik_orientation_error") for row in rows]
    ik_target_errors = [to_float(row, "ik_target_error") for row in rows]
    joint_limit_margins = [
        to_float(row, "joint_limit_min_normalized_margin") for row in rows
    ]

    guard_steps = [row for row in rows if to_bool(row, "guard_active")]
    guarded_steps = [row for row in rows if to_bool(row, "guarded")]
    near_steps = [row for row in rows if to_float(row, "pre_dist_xy") <= near_xy]
    insert_steps = [
        row for row in rows if to_float(row, "pre_dist_xy") <= success_xy_tolerance
    ]
    low_z_steps = [row for row in rows if to_float(row, "pre_z_above_target") <= low_z]
    low_z_misaligned_steps = [
        row
        for row in low_z_steps
        if to_float(row, "pre_dist_xy") > success_xy_tolerance
    ]
    recent_down = [to_float(row, "final_action_z") < -1e-6 for row in recent]
    recent_policy_down = [to_float(row, "policy_action_z") < -1e-6 for row in recent]
    recent_guarded_down = [
        to_float(row, "guarded_action_z") < -1e-6
        for row in recent
        if row.get("guarded_action_z", "") != ""
    ]

    final_pre_xy = to_float(last, "pre_dist_xy")
    final_pre_z = to_float(last, "pre_z_above_target")
    final_action_xy = float(
        np.linalg.norm(
            [
                to_float(last, "final_action_x", 0.0),
                to_float(last, "final_action_y", 0.0),
            ]
        )
    )
    min_xy = float(np.nanmin(np.asarray(pre_xy, dtype=np.float64))) if pre_xy else float("nan")
    min_z = float(np.nanmin(np.asarray(pre_z, dtype=np.float64))) if pre_z else float("nan")
    min_xy_at_low_z = (
        float(
            np.nanmin(
                np.asarray([to_float(row, "pre_dist_xy") for row in low_z_steps], dtype=np.float64)
            )
        )
        if low_z_steps
        else float("nan")
    )

    result = {
        "label": label,
        "episode": episode,
        "seed": first.get("seed", ""),
        "outcome": first.get("episode_outcome", ""),
        "steps": len(rows),
        "final_step": int(float(last.get("post_step_count", "0") or 0)),
        "guard_steps": len(guard_steps),
        "guarded_steps": len(guarded_steps),
        "first_guard_step": int(float(guard_steps[0].get("step", "0"))) if guard_steps else -1,
        "min_xy": min_xy,
        "min_z": min_z,
        "min_xy_at_low_z": min_xy_at_low_z,
        "final_pre_xy": final_pre_xy,
        "final_pre_z": final_pre_z,
        "final_post_xy": to_float(last, "post_dist_xy"),
        "final_post_z": to_float(last, "post_z_above_target"),
        "final_action_xy_norm": final_action_xy,
        "final_action_z": to_float(last, "final_action_z"),
        "final_policy_action_z": to_float(last, "policy_action_z"),
        "final_guarded_action_z": to_float(last, "guarded_action_z"),
        "final_applied_action_z": to_float(last, "applied_action_z"),
        "final_collision_contact_count": int(
            float(last.get("collision_contact_count", "0") or 0)
        ),
        "final_collision_contact_pairs": last.get("collision_contact_pairs", ""),
        "ever_insert_band": bool(insert_steps),
        "ever_near_xy": bool(near_steps),
        "ever_low_z": bool(low_z_steps),
        "low_z_steps": len(low_z_steps),
        "low_z_misaligned_steps": len(low_z_misaligned_steps),
        "insert_band_steps": len(insert_steps),
        "near_xy_steps": len(near_steps),
        "recent_down_rate": bool_rate(recent_down),
        "recent_policy_down_rate": bool_rate(recent_policy_down),
        "recent_guarded_down_rate": bool_rate(recent_guarded_down),
        "mean_recent_final_action_z": finite_mean(
            [to_float(row, "final_action_z") for row in recent]
        ),
        "mean_recent_applied_action_z": finite_mean(
            [to_float(row, "applied_action_z") for row in recent]
        ),
        "mean_action_tracking_error": finite_mean(
            [to_float(row, "action_tracking_error") for row in rows]
        ),
        "mean_peg_tilt_angle_deg": finite_mean(peg_tilt_angles),
        "max_peg_tilt_angle_deg": (
            float(np.nanmax(np.asarray(peg_tilt_angles, dtype=np.float64)))
            if peg_tilt_angles
            else float("nan")
        ),
        "mean_ik_orientation_error": finite_mean(ik_orientation_errors),
        "mean_ik_target_error": finite_mean(ik_target_errors),
        "min_joint_limit_normalized_margin": (
            float(np.nanmin(np.asarray(joint_limit_margins, dtype=np.float64)))
            if joint_limit_margins
            else float("nan")
        ),
        "control_delay": int(float(last.get("control_action_delay", "0") or 0)),
        "control_scale": to_float(last, "control_action_scale_multiplier"),
        "control_filter_alpha": to_float(last, "control_action_filter_alpha"),
        "hole_clearance": to_float(last, "hole_clearance"),
    }
    result["failure_mode"] = classify_failure_mode(
        outcome=str(result["outcome"]),
        guard_steps=int(result["guard_steps"]),
        final_xy=float(result["final_pre_xy"]),
        final_z=float(result["final_pre_z"]),
        min_xy=float(result["min_xy"]),
        ever_insert_band=bool(result["ever_insert_band"]),
        ever_low_z=bool(result["ever_low_z"]),
        low_z_misaligned_steps=int(result["low_z_misaligned_steps"]),
        near_xy=near_xy,
        far_xy=far_xy,
        low_z=low_z,
    )
    return result


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["label"]), str(row["outcome"]))].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (label, outcome), group in sorted(grouped.items()):
        summary_rows.append(
            {
                "label": label,
                "outcome": outcome,
                "episodes": len(group),
                "ever_insert_band_rate": bool_rate([bool(row["ever_insert_band"]) for row in group]),
                "ever_low_z_rate": bool_rate([bool(row["ever_low_z"]) for row in group]),
                "median_min_xy_mm": finite_median([1000.0 * float(row["min_xy"]) for row in group]),
                "median_final_xy_mm": finite_median(
                    [1000.0 * float(row["final_pre_xy"]) for row in group]
                ),
                "median_final_z_mm": finite_median(
                    [1000.0 * float(row["final_pre_z"]) for row in group]
                ),
                "mean_low_z_misaligned_steps": finite_mean(
                    [float(row["low_z_misaligned_steps"]) for row in group]
                ),
                "mean_recent_down_rate": finite_mean(
                    [float(row["recent_down_rate"]) for row in group]
                ),
                "mean_recent_action_z_mm": finite_mean(
                    [1000.0 * float(row["mean_recent_final_action_z"]) for row in group]
                ),
                "mean_guard_steps": finite_mean([float(row["guard_steps"]) for row in group]),
                "mean_tracking_error_mm": finite_mean(
                    [1000.0 * float(row["mean_action_tracking_error"]) for row in group]
                ),
                "mean_peg_tilt_deg": finite_mean(
                    [float(row["mean_peg_tilt_angle_deg"]) for row in group]
                ),
                "max_peg_tilt_deg": (
                    float(np.nanmax([float(row["max_peg_tilt_angle_deg"]) for row in group]))
                    if group
                    else float("nan")
                ),
                "mean_ik_orientation_error": finite_mean(
                    [float(row["mean_ik_orientation_error"]) for row in group]
                ),
                "mean_ik_target_error_mm": finite_mean(
                    [1000.0 * float(row["mean_ik_target_error"]) for row in group]
                ),
            }
        )
    return summary_rows


def aggregate_failure_modes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["label"]), str(row["failure_mode"]))].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (label, failure_mode), group in sorted(grouped.items()):
        summary_rows.append(
            {
                "label": label,
                "failure_mode": failure_mode,
                "episodes": len(group),
                "collision_rate": bool_rate([str(row["outcome"]) == "collision" for row in group]),
                "timeout_rate": bool_rate([str(row["outcome"]) == "timeout" for row in group]),
                "ever_insert_band_rate": bool_rate([bool(row["ever_insert_band"]) for row in group]),
                "median_min_xy_mm": finite_median([1000.0 * float(row["min_xy"]) for row in group]),
                "median_final_xy_mm": finite_median(
                    [1000.0 * float(row["final_pre_xy"]) for row in group]
                ),
                "median_final_z_mm": finite_median(
                    [1000.0 * float(row["final_pre_z"]) for row in group]
                ),
                "mean_low_z_misaligned_steps": finite_mean(
                    [float(row["low_z_misaligned_steps"]) for row in group]
                ),
                "mean_guard_steps": finite_mean([float(row["guard_steps"]) for row in group]),
                "mean_peg_tilt_deg": finite_mean(
                    [float(row["mean_peg_tilt_angle_deg"]) for row in group]
                ),
                "max_peg_tilt_deg": (
                    float(np.nanmax([float(row["max_peg_tilt_angle_deg"]) for row in group]))
                    if group
                    else float("nan")
                ),
                "mean_ik_orientation_error": finite_mean(
                    [float(row["mean_ik_orientation_error"]) for row in group]
                ),
            }
        )
    return summary_rows


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


def write_markdown(
    path: Path,
    episode_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    failure_mode_rows: list[dict[str, Any]],
    trace_specs: list[tuple[str, Path]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Step Trace Failure Analysis",
        "",
        "## Inputs",
        "",
    ]
    for label, trace_path in trace_specs:
        lines.append(f"- `{label}`: `{trace_path}`")

    lines.extend(
        [
            "",
            "## Aggregate By Outcome",
            "",
            "| Label | Outcome | Episodes | Insert-band rate | Low-Z rate | Median min XY mm | Median final XY mm | Median final Z mm | Low-Z misaligned steps | Recent down rate | Recent action Z mm | Guard steps | Tracking error mm | Mean tilt deg | Max tilt deg | IK ori err | IK target err mm |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary_rows:
        lines.append(
            "| {label} | {outcome} | {episodes} | {ever_insert_band_rate} | {ever_low_z_rate} | {median_min_xy_mm} | {median_final_xy_mm} | {median_final_z_mm} | {mean_low_z_misaligned_steps} | {mean_recent_down_rate} | {mean_recent_action_z_mm} | {mean_guard_steps} | {mean_tracking_error_mm} | {mean_peg_tilt_deg} | {max_peg_tilt_deg} | {mean_ik_orientation_error} | {mean_ik_target_error_mm} |".format(
                **{key: format_value(value) for key, value in row.items()}
            )
        )

    lines.extend(
        [
            "",
            "## Failure Modes",
            "",
            "| Label | Failure mode | Episodes | Collision rate | Timeout rate | Insert-band rate | Median min XY mm | Median final XY mm | Median final Z mm | Low-Z misaligned steps | Guard steps | Mean tilt deg | Max tilt deg | IK ori err |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in failure_mode_rows:
        lines.append(
            "| {label} | {failure_mode} | {episodes} | {collision_rate} | {timeout_rate} | {ever_insert_band_rate} | {median_min_xy_mm} | {median_final_xy_mm} | {median_final_z_mm} | {mean_low_z_misaligned_steps} | {mean_guard_steps} | {mean_peg_tilt_deg} | {max_peg_tilt_deg} | {mean_ik_orientation_error} |".format(
                **{key: format_value(value) for key, value in row.items()}
            )
        )

    lines.extend(
        [
            "",
            "## Episode Details",
            "",
            "| Label | Ep | Outcome | Failure mode | Steps | Final XY mm | Final Z mm | Min XY mm | Min XY low-Z mm | Insert-band | Low-Z misaligned steps | Recent down rate | Final action Z mm | Guard steps | Mean tilt deg | Max tilt deg | IK ori err | Delay | Clearance mm | Contact pairs |",
            "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in sorted(
        episode_rows,
        key=lambda item: (str(item["label"]), str(item["outcome"]), int(item["episode"])),
    ):
        lines.append(
            "| {label} | {episode} | {outcome} | {failure_mode} | {steps} | {final_pre_xy} | {final_pre_z} | {min_xy} | {min_xy_at_low_z} | {ever_insert_band} | {low_z_misaligned_steps} | {recent_down_rate} | {final_action_z} | {guard_steps} | {mean_peg_tilt_angle_deg} | {max_peg_tilt_angle_deg} | {mean_ik_orientation_error} | {control_delay} | {hole_clearance} | `{contact_pairs}` |".format(
                label=row["label"],
                episode=row["episode"],
                outcome=row["outcome"],
                failure_mode=row["failure_mode"],
                steps=row["steps"],
                final_pre_xy=format_value(1000.0 * float(row["final_pre_xy"])),
                final_pre_z=format_value(1000.0 * float(row["final_pre_z"])),
                min_xy=format_value(1000.0 * float(row["min_xy"])),
                min_xy_at_low_z=format_value(1000.0 * float(row["min_xy_at_low_z"])),
                ever_insert_band=format_value(row["ever_insert_band"]),
                low_z_misaligned_steps=format_value(row["low_z_misaligned_steps"]),
                recent_down_rate=format_value(row["recent_down_rate"]),
                final_action_z=format_value(1000.0 * float(row["final_action_z"])),
                guard_steps=format_value(row["guard_steps"]),
                mean_peg_tilt_angle_deg=format_value(row["mean_peg_tilt_angle_deg"]),
                max_peg_tilt_angle_deg=format_value(row["max_peg_tilt_angle_deg"]),
                mean_ik_orientation_error=format_value(row["mean_ik_orientation_error"]),
                control_delay=format_value(row["control_delay"]),
                hole_clearance=format_value(1000.0 * float(row["hole_clearance"])),
                contact_pairs=str(row.get("final_collision_contact_pairs", "")).replace("|", "/"),
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    trace_specs = [parse_trace_spec(spec) for spec in args.trace]
    episode_rows: list[dict[str, Any]] = []
    for label, path in trace_specs:
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in read_rows(path):
            grouped[str(row["episode"])].append(row)
        for episode, rows in grouped.items():
            episode_rows.append(
                summarize_episode(
                    label,
                    episode,
                    rows,
                    success_xy_tolerance=args.success_xy_tolerance,
                    near_xy=args.near_xy,
                    far_xy=args.far_xy,
                    low_z=args.low_z,
                    window_steps=args.window_steps,
                )
            )

    summary_rows = aggregate(episode_rows)
    failure_mode_rows = aggregate_failure_modes(episode_rows)
    write_markdown(args.output_md, episode_rows, summary_rows, failure_mode_rows, trace_specs)
    if args.output_csv is not None:
        write_csv(args.output_csv, episode_rows)
    print(f"saved markdown summary to {args.output_md}")
    if args.output_csv is not None:
        print(f"saved episode csv to {args.output_csv}")


if __name__ == "__main__":
    main()
