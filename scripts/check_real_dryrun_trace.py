from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


AXES = ("x", "y", "z")
REQUIRED_COLUMNS = (
    "episode",
    "step",
    "dist_xy",
    "dist_z",
    "target_x",
    "target_y",
    "target_z",
    "peg_tip_x",
    "peg_tip_y",
    "peg_tip_z",
    "raw_action_x",
    "raw_action_y",
    "raw_action_z",
    "final_action_x",
    "final_action_y",
    "final_action_z",
    "safe_action_x",
    "safe_action_y",
    "safe_action_z",
    "action_limited",
    "workspace_limited",
)
ACTION_PREFIXES = (
    "policy_action",
    "guarded_action",
    "final_action",
    "raw_action",
    "limited_action",
    "filtered_action",
    "safe_action",
    "env_commanded_action",
    "env_applied_action",
)
STATIC_SOURCES = {"static", "constant", "manual"}
SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    count: int = 1
    details: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a real-robot dry-run trace before using it for deployment decisions."
    )
    parser.add_argument("--trace", type=Path, required=True, help="Dry-run CSV trace to inspect.")
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None, help="Optional issues CSV.")
    parser.add_argument("--max-safe-action", type=float, default=0.002)
    parser.add_argument("--max-safe-action-norm", type=float, default=None)
    parser.add_argument("--expected-pose-frame", default=None)
    parser.add_argument("--expected-target-frame", default=None)
    pose_source_group = parser.add_mutually_exclusive_group()
    pose_source_group.add_argument("--require-nonstatic-pose", action="store_true")
    pose_source_group.add_argument("--allow-static-pose", action="store_true")
    target_source_group = parser.add_mutually_exclusive_group()
    target_source_group.add_argument("--require-nonstatic-target", action="store_true")
    target_source_group.add_argument("--allow-static-target", action="store_true")
    parser.add_argument("--allow-action-limited", action="store_true")
    parser.add_argument("--allow-workspace-limited", action="store_true")
    parser.add_argument("--guard-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--down-action-epsilon", type=float, default=1e-9)
    parser.add_argument("--pose-consistency-tolerance", type=float, default=1e-6)
    parser.add_argument("--tcp-consistency-tolerance", type=float, default=1e-5)
    parser.add_argument(
        "--tcp-to-peg-tip-xyz",
        nargs=3,
        type=float,
        default=None,
        help="Optional TCP-frame peg-tip offset used to verify tcp_pos/tcp_rotvec rows.",
    )
    parser.add_argument("--fail-on-warn", action="store_true")
    return parser.parse_args()


def load_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = [dict(row) for row in reader]
        fieldnames = list(reader.fieldnames or [])
    return rows, fieldnames


def parse_float(value: Any) -> float:
    if value is None:
        return math.nan
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return math.nan
    try:
        return float(text)
    except ValueError:
        return math.nan


def parse_int(value: Any) -> int | None:
    number = parse_float(value)
    if not math.isfinite(number):
        return None
    return int(number)


def parse_bool(value: Any) -> bool | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def is_finite_vector(values: Iterable[float]) -> bool:
    return all(math.isfinite(value) for value in values)


def vector(row: dict[str, str], prefix: str) -> tuple[float, float, float] | None:
    keys = [f"{prefix}_{axis}" for axis in AXES]
    if not all(key in row for key in keys):
        return None
    return tuple(parse_float(row[key]) for key in keys)


def has_vector(fieldnames: Iterable[str], prefix: str) -> bool:
    fields = set(fieldnames)
    return all(f"{prefix}_{axis}" in fields for axis in AXES)


def vector_norm(values: tuple[float, float, float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def max_abs_component(values: tuple[float, float, float]) -> float:
    return max(abs(value) for value in values)


def row_label(row: dict[str, str]) -> str:
    episode = row.get("episode", "?")
    step = row.get("step", "?")
    return f"episode={episode}, step={step}"


def unique_values(rows: list[dict[str, str]], column: str) -> list[str]:
    values = sorted({row.get(column, "").strip() for row in rows if row.get(column, "").strip()})
    return values


def count_bool(rows: list[dict[str, str]], column: str, expected: bool = True) -> int:
    return sum(1 for row in rows if parse_bool(row.get(column)) is expected)


def severity_for_static_source(require_nonstatic: bool, allow_static: bool) -> str:
    if require_nonstatic:
        return "ERROR"
    if allow_static:
        return "INFO"
    return "WARN"


def rotation_matrix_from_rotvec(rotvec: tuple[float, float, float]) -> tuple[tuple[float, float, float], ...]:
    rx, ry, rz = rotvec
    theta = vector_norm(rotvec)
    if theta < 1e-12:
        return (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        )
    kx, ky, kz = rx / theta, ry / theta, rz / theta
    c = math.cos(theta)
    s = math.sin(theta)
    v = 1.0 - c
    return (
        (kx * kx * v + c, kx * ky * v - kz * s, kx * kz * v + ky * s),
        (ky * kx * v + kz * s, ky * ky * v + c, ky * kz * v - kx * s),
        (kz * kx * v - ky * s, kz * ky * v + kx * s, kz * kz * v + c),
    )


def matvec(
    matrix: tuple[tuple[float, float, float], ...],
    values: tuple[float, float, float],
) -> tuple[float, float, float]:
    return tuple(sum(matrix[row][col] * values[col] for col in range(3)) for row in range(3))  # type: ignore[return-value]


def add_vectors(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> tuple[float, float, float]:
    return tuple(left[index] + right[index] for index in range(3))  # type: ignore[return-value]


def sub_vectors(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> tuple[float, float, float]:
    return tuple(left[index] - right[index] for index in range(3))  # type: ignore[return-value]


def check_required_columns(fieldnames: list[str]) -> list[Issue]:
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if not missing:
        return []
    return [
        Issue(
            severity="ERROR",
            code="missing_required_columns",
            message="Trace is missing required dry-run columns.",
            count=len(missing),
            details=", ".join(missing),
        )
    ]


def analyze_frames(
    rows: list[dict[str, str]],
    fieldnames: list[str],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[Issue]]:
    metrics: dict[str, Any] = {}
    issues: list[Issue] = []

    if "pose_frame" in fieldnames:
        pose_frames = unique_values(rows, "pose_frame")
        metrics["pose_frames"] = ", ".join(pose_frames) if pose_frames else "none"
        if args.expected_pose_frame is not None:
            mismatches = [
                row
                for row in rows
                if row.get("pose_frame", "").strip()
                and row.get("pose_frame", "").strip() != args.expected_pose_frame
            ]
            if mismatches:
                issues.append(
                    Issue(
                        severity="ERROR",
                        code="pose_frame_mismatch",
                        message=f"pose_frame differs from expected frame '{args.expected_pose_frame}'.",
                        count=len(mismatches),
                        details=row_label(mismatches[0]),
                    )
                )
    elif args.expected_pose_frame is not None:
        issues.append(
            Issue(
                severity="ERROR",
                code="missing_pose_frame",
                message="Trace does not contain pose_frame.",
            )
        )

    if "target_frame" in fieldnames:
        target_frames = unique_values(rows, "target_frame")
        metrics["target_frames"] = ", ".join(target_frames) if target_frames else "none"
        if args.expected_target_frame is not None:
            mismatches = [
                row
                for row in rows
                if row.get("target_frame", "").strip()
                and row.get("target_frame", "").strip() != args.expected_target_frame
            ]
            if mismatches:
                issues.append(
                    Issue(
                        severity="ERROR",
                        code="target_frame_mismatch",
                        message=f"target_frame differs from expected frame '{args.expected_target_frame}'.",
                        count=len(mismatches),
                        details=row_label(mismatches[0]),
                    )
                )
    elif args.expected_target_frame is not None:
        issues.append(
            Issue(
                severity="ERROR",
                code="missing_target_frame",
                message="Trace does not contain target_frame.",
            )
        )

    if "pose_frame" in fieldnames and "target_frame" in fieldnames:
        mismatches = [
            row
            for row in rows
            if row.get("pose_frame", "").strip()
            and row.get("target_frame", "").strip()
            and row.get("pose_frame", "").strip() != row.get("target_frame", "").strip()
        ]
        if mismatches:
            issues.append(
                Issue(
                    severity="WARN",
                    code="pose_target_frame_mismatch",
                    message="pose_frame and target_frame differ in the same trace row.",
                    count=len(mismatches),
                    details=row_label(mismatches[0]),
                )
            )

    return metrics, issues


def analyze_sources(
    rows: list[dict[str, str]],
    fieldnames: list[str],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[Issue]]:
    metrics: dict[str, Any] = {}
    issues: list[Issue] = []

    source_specs = (
        (
            "pose_source",
            args.require_nonstatic_pose,
            args.allow_static_pose,
            "missing_pose_source",
            "static_pose_source",
        ),
        (
            "target_source",
            args.require_nonstatic_target,
            args.allow_static_target,
            "missing_target_source",
            "static_target_source",
        ),
    )
    for column, require_nonstatic, allow_static, missing_code, static_code in source_specs:
        if column not in fieldnames:
            if require_nonstatic:
                issues.append(
                    Issue(
                        severity="ERROR",
                        code=missing_code,
                        message=f"Trace does not contain {column}; cannot verify non-static source.",
                    )
                )
            continue

        values = unique_values(rows, column)
        metrics[f"{column}s"] = ", ".join(values) if values else "none"
        static_rows = [
            row for row in rows if row.get(column, "").strip().lower() in STATIC_SOURCES
        ]
        if static_rows:
            severity = severity_for_static_source(require_nonstatic, allow_static)
            issues.append(
                Issue(
                    severity=severity,
                    code=static_code,
                    message=f"{column} is static in part of the trace.",
                    count=len(static_rows),
                    details=row_label(static_rows[0]),
                )
            )

    return metrics, issues


def analyze_actions(
    rows: list[dict[str, str]],
    fieldnames: list[str],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[Issue]]:
    metrics: dict[str, Any] = {}
    issues: list[Issue] = []
    max_safe_action_norm = args.max_safe_action_norm
    if max_safe_action_norm is None and args.max_safe_action is not None:
        max_safe_action_norm = math.sqrt(3.0) * float(args.max_safe_action)

    for prefix in ACTION_PREFIXES:
        if not has_vector(fieldnames, prefix):
            continue
        finite_vectors = [
            (row, current)
            for row in rows
            if (current := vector(row, prefix)) is not None and is_finite_vector(current)
        ]
        if not finite_vectors:
            metrics[f"{prefix}_finite_rows"] = 0
            continue
        max_component_row, max_component_vector = max(
            finite_vectors, key=lambda item: max_abs_component(item[1])
        )
        max_norm_row, max_norm_vector = max(finite_vectors, key=lambda item: vector_norm(item[1]))
        metrics[f"{prefix}_finite_rows"] = len(finite_vectors)
        metrics[f"{prefix}_max_abs_component"] = max_abs_component(max_component_vector)
        metrics[f"{prefix}_max_abs_component_at"] = row_label(max_component_row)
        metrics[f"{prefix}_max_norm"] = vector_norm(max_norm_vector)
        metrics[f"{prefix}_max_norm_at"] = row_label(max_norm_row)

    if has_vector(fieldnames, "safe_action"):
        component_violations = []
        norm_violations = []
        for row in rows:
            current = vector(row, "safe_action")
            if current is None or not is_finite_vector(current):
                continue
            if max_abs_component(current) > args.max_safe_action + 1e-12:
                component_violations.append(row)
            if max_safe_action_norm is not None and vector_norm(current) > max_safe_action_norm + 1e-12:
                norm_violations.append(row)
        if component_violations:
            issues.append(
                Issue(
                    severity="ERROR",
                    code="safe_action_component_limit_exceeded",
                    message=f"safe_action component exceeds {args.max_safe_action:g} m.",
                    count=len(component_violations),
                    details=row_label(component_violations[0]),
                )
            )
        if norm_violations:
            issues.append(
                Issue(
                    severity="ERROR",
                    code="safe_action_norm_limit_exceeded",
                    message=f"safe_action norm exceeds {max_safe_action_norm:g} m.",
                    count=len(norm_violations),
                    details=row_label(norm_violations[0]),
                )
            )

    if "workspace_limited" in fieldnames:
        limited_count = count_bool(rows, "workspace_limited", True)
        metrics["workspace_limited_rows"] = limited_count
        if limited_count:
            severity = "INFO" if args.allow_workspace_limited else "ERROR"
            issues.append(
                Issue(
                    severity=severity,
                    code="workspace_limited",
                    message="Safety workspace clipping occurred.",
                    count=limited_count,
                    details="Use --allow-workspace-limited only for intentional boundary tests.",
                )
            )

    if "action_limited" in fieldnames:
        limited_count = count_bool(rows, "action_limited", True)
        metrics["action_limited_rows"] = limited_count
        if limited_count:
            severity = "INFO" if args.allow_action_limited else "WARN"
            issues.append(
                Issue(
                    severity=severity,
                    code="action_limited",
                    message="Raw or transformed action was clipped by the safety action limit.",
                    count=limited_count,
                )
            )

    return metrics, issues


def analyze_guard(
    rows: list[dict[str, str]],
    fieldnames: list[str],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[Issue]]:
    metrics: dict[str, Any] = {}
    issues: list[Issue] = []
    if "guard_enabled" not in fieldnames:
        return metrics, issues

    guard_enabled_rows = [row for row in rows if parse_bool(row.get("guard_enabled")) is True]
    guard_active_rows = [row for row in rows if parse_bool(row.get("guard_active")) is True]
    guard_activated_rows = [row for row in rows if parse_bool(row.get("guard_activated")) is True]
    guard_down_blocked_count = count_bool(rows, "guard_down_blocked", True) if "guard_down_blocked" in fieldnames else 0
    metrics["guard_enabled_rows"] = len(guard_enabled_rows)
    metrics["guard_active_rows"] = len(guard_active_rows)
    metrics["guard_activated_rows"] = len(guard_activated_rows)
    metrics["guard_down_blocked_rows"] = guard_down_blocked_count

    if guard_enabled_rows and not guard_active_rows:
        issues.append(
            Issue(
                severity="WARN",
                code="guard_never_active",
                message="Guard was enabled but never became active.",
            )
        )

    first_guard_row = guard_active_rows[0] if guard_active_rows else None
    if first_guard_row is not None:
        metrics["first_guard_active_at"] = row_label(first_guard_row)
        metrics["first_guard_z_above_target"] = parse_float(first_guard_row.get("guard_z_above_target"))
        metrics["first_guard_dist_xy"] = parse_float(first_guard_row.get("guard_dist_xy"))

    if guard_down_blocked_count:
        issues.append(
            Issue(
                severity="INFO",
                code="guard_down_blocked",
                message="Guard blocked downward action while XY alignment was outside tolerance.",
                count=guard_down_blocked_count,
            )
        )

    if not has_vector(fieldnames, "safe_action"):
        return metrics, issues

    first_guard_index = rows.index(first_guard_row) if first_guard_row is not None else None
    down_before_guard = []
    down_while_unaligned = []
    active_unaligned = []
    for index, row in enumerate(rows):
        current_safe = vector(row, "safe_action")
        if current_safe is None or not is_finite_vector(current_safe):
            continue
        safe_z = current_safe[2]
        guard_active = parse_bool(row.get("guard_active")) is True
        guard_dist_xy = parse_float(row.get("guard_dist_xy"))
        if (
            guard_enabled_rows
            and first_guard_index is not None
            and index < first_guard_index
            and safe_z < -args.down_action_epsilon
        ):
            down_before_guard.append(row)
        if guard_active and math.isfinite(guard_dist_xy) and guard_dist_xy > args.guard_align_xy_tolerance:
            active_unaligned.append(row)
            if safe_z < -args.down_action_epsilon:
                down_while_unaligned.append(row)

    metrics["guard_active_unaligned_rows"] = len(active_unaligned)
    metrics["down_before_guard_rows"] = len(down_before_guard)
    metrics["down_while_guard_unaligned_rows"] = len(down_while_unaligned)

    if active_unaligned:
        issues.append(
            Issue(
                severity="INFO",
                code="guard_active_while_unaligned",
                message=(
                    "Guard was active while guard_dist_xy exceeded the configured alignment tolerance."
                ),
                count=len(active_unaligned),
                details=row_label(active_unaligned[0]),
            )
        )
    if down_before_guard:
        issues.append(
            Issue(
                severity="WARN",
                code="down_before_guard_active",
                message="safe_action_z moved downward before the guard first became active.",
                count=len(down_before_guard),
                details=row_label(down_before_guard[0]),
            )
        )
    if down_while_unaligned:
        issues.append(
            Issue(
                severity="WARN",
                code="down_while_guard_unaligned",
                message=(
                    "safe_action_z moved downward while guard_dist_xy exceeded the alignment tolerance."
                ),
                count=len(down_while_unaligned),
                details=row_label(down_while_unaligned[0]),
            )
        )

    return metrics, issues


def analyze_pose_consistency(
    rows: list[dict[str, str]],
    fieldnames: list[str],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[Issue]]:
    metrics: dict[str, Any] = {}
    issues: list[Issue] = []

    needed = {"dist_xy", "dist_z", "target_x", "target_y", "target_z", "peg_tip_x", "peg_tip_y", "peg_tip_z"}
    if needed.issubset(set(fieldnames)):
        xy_mismatches = []
        z_mismatches = []
        max_xy_error = 0.0
        max_z_error = 0.0
        for row in rows:
            target = vector(row, "target")
            peg_tip = vector(row, "peg_tip")
            if target is None or peg_tip is None or not is_finite_vector(target) or not is_finite_vector(peg_tip):
                continue
            expected_xy = math.hypot(peg_tip[0] - target[0], peg_tip[1] - target[1])
            expected_z = abs(peg_tip[2] - target[2])
            xy_error = abs(parse_float(row.get("dist_xy")) - expected_xy)
            z_error = abs(parse_float(row.get("dist_z")) - expected_z)
            if math.isfinite(xy_error):
                max_xy_error = max(max_xy_error, xy_error)
                if xy_error > args.pose_consistency_tolerance:
                    xy_mismatches.append(row)
            if math.isfinite(z_error):
                max_z_error = max(max_z_error, z_error)
                if z_error > args.pose_consistency_tolerance:
                    z_mismatches.append(row)
        metrics["dist_xy_max_consistency_error"] = max_xy_error
        metrics["dist_z_max_consistency_error"] = max_z_error
        if xy_mismatches:
            issues.append(
                Issue(
                    severity="ERROR",
                    code="dist_xy_inconsistent",
                    message="dist_xy does not match norm(peg_tip_xy - target_xy).",
                    count=len(xy_mismatches),
                    details=row_label(xy_mismatches[0]),
                )
            )
        if z_mismatches:
            issues.append(
                Issue(
                    severity="ERROR",
                    code="dist_z_inconsistent",
                    message="dist_z does not match abs(peg_tip_z - target_z).",
                    count=len(z_mismatches),
                    details=row_label(z_mismatches[0]),
                )
            )

    monotonic_specs = (
        ("step", "step_not_monotonic"),
        ("pose_step", "pose_step_not_monotonic"),
        ("pose_timestamp", "pose_timestamp_not_monotonic"),
    )
    for column, code in monotonic_specs:
        if column not in fieldnames:
            continue
        mismatches = []
        previous_by_episode: dict[str, float] = {}
        for row in rows:
            episode = row.get("episode", "")
            value = parse_float(row.get(column))
            if not math.isfinite(value):
                continue
            previous = previous_by_episode.get(episode)
            if previous is not None and value < previous:
                mismatches.append(row)
            previous_by_episode[episode] = value
        if mismatches:
            issues.append(
                Issue(
                    severity="ERROR",
                    code=code,
                    message=f"{column} is not monotonic nondecreasing within an episode.",
                    count=len(mismatches),
                    details=row_label(mismatches[0]),
                )
            )

    return metrics, issues


def analyze_tcp_consistency(
    rows: list[dict[str, str]],
    fieldnames: list[str],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[Issue]]:
    metrics: dict[str, Any] = {}
    issues: list[Issue] = []
    fields = set(fieldnames)
    tcp_pos_fields = {f"tcp_pos_{axis}" for axis in AXES}
    tcp_rotvec_fields = {f"tcp_rotvec_{axis}" for axis in AXES}
    has_any_tcp = bool(fields & tcp_pos_fields) or bool(fields & tcp_rotvec_fields)
    has_all_tcp = tcp_pos_fields.issubset(fields) and tcp_rotvec_fields.issubset(fields)

    if not has_any_tcp:
        if "pose_source" in fieldnames and any(
            "tcp" in row.get("pose_source", "").strip().lower() for row in rows
        ):
            issues.append(
                Issue(
                    severity="WARN",
                    code="tcp_source_without_tcp_columns",
                    message="pose_source mentions TCP, but tcp_pos/tcp_rotvec columns are missing.",
                )
            )
        return metrics, issues

    if not has_all_tcp:
        missing = sorted((tcp_pos_fields | tcp_rotvec_fields) - fields)
        issues.append(
            Issue(
                severity="WARN",
                code="partial_tcp_columns",
                message="Trace has only part of the TCP pose columns.",
                count=len(missing),
                details=", ".join(missing),
            )
        )
        return metrics, issues

    finite_tcp_rows = [
        row
        for row in rows
        if (tcp_pos := vector(row, "tcp_pos")) is not None
        and (tcp_rotvec := vector(row, "tcp_rotvec")) is not None
        and is_finite_vector(tcp_pos)
        and is_finite_vector(tcp_rotvec)
    ]
    metrics["tcp_finite_rows"] = len(finite_tcp_rows)
    if not finite_tcp_rows:
        issues.append(
            Issue(
                severity="WARN",
                code="no_finite_tcp_rows",
                message="TCP columns exist, but no row has a finite TCP pose.",
            )
        )
        return metrics, issues

    if args.tcp_to_peg_tip_xyz is None:
        issues.append(
            Issue(
                severity="INFO",
                code="tcp_offset_check_skipped",
                message="Pass --tcp-to-peg-tip-xyz to verify TCP-to-peg-tip conversion.",
            )
        )
        return metrics, issues

    offset = tuple(float(value) for value in args.tcp_to_peg_tip_xyz)
    mismatches = []
    max_error = 0.0
    for row in finite_tcp_rows:
        tcp_pos = vector(row, "tcp_pos")
        tcp_rotvec = vector(row, "tcp_rotvec")
        peg_tip = vector(row, "peg_tip")
        if (
            tcp_pos is None
            or tcp_rotvec is None
            or peg_tip is None
            or not is_finite_vector(peg_tip)
        ):
            continue
        expected_peg_tip = add_vectors(tcp_pos, matvec(rotation_matrix_from_rotvec(tcp_rotvec), offset))
        error = vector_norm(sub_vectors(peg_tip, expected_peg_tip))
        max_error = max(max_error, error)
        if error > args.tcp_consistency_tolerance:
            mismatches.append(row)
    metrics["tcp_to_peg_tip_max_error"] = max_error
    if mismatches:
        issues.append(
            Issue(
                severity="ERROR",
                code="tcp_to_peg_tip_inconsistent",
                message="peg_tip_pos does not match tcp_pos + R(tcp_rotvec) * tcp_to_peg_tip_xyz.",
                count=len(mismatches),
                details=row_label(mismatches[0]),
            )
        )

    return metrics, issues


def analyze_trace(
    rows: list[dict[str, str]],
    fieldnames: list[str],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[Issue]]:
    metrics: dict[str, Any] = {
        "rows": len(rows),
        "columns": len(fieldnames),
        "episodes": len({row.get("episode", "") for row in rows if row.get("episode", "")}),
    }
    issues = check_required_columns(fieldnames)
    if not rows:
        issues.append(
            Issue(
                severity="ERROR",
                code="empty_trace",
                message="Trace contains no data rows.",
            )
        )
        return metrics, issues

    for analyzer in (
        analyze_frames,
        analyze_sources,
        analyze_actions,
        analyze_guard,
        analyze_pose_consistency,
        analyze_tcp_consistency,
    ):
        analyzer_metrics, analyzer_issues = analyzer(rows, fieldnames, args)
        metrics.update(analyzer_metrics)
        issues.extend(analyzer_issues)

    return metrics, sorted(issues, key=lambda issue: (SEVERITY_ORDER[issue.severity], issue.code))


def verdict(issues: list[Issue], fail_on_warn: bool) -> str:
    if any(issue.severity == "ERROR" for issue in issues):
        return "FAIL"
    if any(issue.severity == "WARN" for issue in issues):
        return "FAIL" if fail_on_warn else "WARN"
    return "PASS"


def format_value(value: Any) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.9g}"
    return str(value)


def render_markdown(trace: Path, metrics: dict[str, Any], issues: list[Issue], result: str) -> str:
    lines = [
        "# Real Dry-run Trace Check",
        "",
        f"- Trace: `{trace}`",
        f"- Verdict: **{result}**",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in sorted(metrics):
        lines.append(f"| `{key}` | {format_value(metrics[key])} |")

    lines.extend(
        [
            "",
            "## Issues",
            "",
            "| Severity | Code | Count | Details |",
            "| --- | --- | ---: | --- |",
        ]
    )
    if not issues:
        lines.append("| INFO | no_issues | 0 | No issues detected. |")
    else:
        for issue in issues:
            detail = issue.details or issue.message
            lines.append(f"| {issue.severity} | `{issue.code}` | {issue.count} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def write_issue_csv(path: Path, issues: list[Issue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["severity", "code", "message", "count", "details"])
        writer.writeheader()
        for issue in issues:
            writer.writerow(asdict(issue))


def main() -> None:
    args = parse_args()
    rows, fieldnames = load_rows(args.trace)
    metrics, issues = analyze_trace(rows, fieldnames, args)
    result = verdict(issues, args.fail_on_warn)

    if args.output_md is not None:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(args.trace, metrics, issues, result), encoding="utf-8")
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "trace": str(args.trace),
            "verdict": result,
            "metrics": metrics,
            "issues": [asdict(issue) for issue in issues],
        }
        args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.output_csv is not None:
        write_issue_csv(args.output_csv, issues)

    print(f"trace={args.trace}")
    print(f"verdict={result}")
    print(f"rows={metrics.get('rows', 0)} issues={len(issues)}")
    for issue in issues:
        print(f"{issue.severity}: {issue.code} ({issue.count}) {issue.message}")

    if result == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
