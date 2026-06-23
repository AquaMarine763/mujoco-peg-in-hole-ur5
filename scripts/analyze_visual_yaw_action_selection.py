"""Analyze visual-yaw confidence gates for runtime action selection.

This is an offline diagnostic. It uses simulator-truth yaw columns already
recorded in step traces, so the report is for controller design only and must
not be treated as deploy-time feedback.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


PROFILE_PERIOD_DEG = {
    "round_round": 360.0,
    "square_square": 90.0,
    "triangle_triangle": 120.0,
    "hex_hex": 60.0,
    "slot_slot": 180.0,
    "rectangular_key": 360.0,
}


def _float(row: dict[str, str], key: str, default: float = float("nan")) -> float:
    try:
        return float(row.get(key, ""))
    except (TypeError, ValueError):
        return default


def _first_float(row: dict[str, str], keys: Iterable[str]) -> float:
    for key in keys:
        value = _float(row, key)
        if math.isfinite(value):
            return value
    return float("nan")


def _bool(row: dict[str, str], key: str) -> bool:
    value = str(row.get(key, "")).strip().lower()
    return value in {"1", "1.0", "true", "yes"}


def _wrap_delta_deg(value: float, period_deg: float) -> float:
    if not math.isfinite(value) or not math.isfinite(period_deg) or period_deg <= 0.0:
        return float("nan")
    return (value + 0.5 * period_deg) % period_deg - 0.5 * period_deg


def _profile(row: dict[str, str]) -> str:
    return row.get("geometry_profile") or row.get("guard_visual_yaw_align_profile") or ""


def _profile_period(row: dict[str, str]) -> float:
    return PROFILE_PERIOD_DEG.get(_profile(row), 360.0)


def _sign(value: float, min_abs: float) -> int:
    if not math.isfinite(value) or abs(value) < min_abs:
        return 0
    return 1 if value > 0.0 else -1


def _format_float(value: float, digits: int = 3) -> str:
    if not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


@dataclass(frozen=True)
class CandidateGate:
    name: str
    description: str
    predicate: Callable[["RowFeatures"], bool]


@dataclass
class RowFeatures:
    row: dict[str, str]
    visible: bool
    delta_stable: bool
    sign_stable: bool
    pred_signed: float
    true_signed: float
    pred_abs: float
    true_abs: float
    abs_error: float
    sign_mismatch: bool
    dist_xy: float
    z_above_target: float
    wall_contact: int
    action_bucket: str
    outcome: str
    scoped: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--episode-output-csv", type=Path)
    parser.add_argument(
        "--scope",
        choices=["reacquire", "visual_active"],
        default="reacquire",
        help="Rows to analyze. Default focuses on visual-yaw re-acquire.",
    )
    parser.add_argument("--raw-norm-min", type=float, default=0.08)
    parser.add_argument("--cam-std-min", type=float, default=18.0)
    parser.add_argument("--crop-std-min", type=float, default=16.0)
    parser.add_argument("--temporal-window", type=int, default=3)
    parser.add_argument("--temporal-delta-deg", type=float, default=12.0)
    parser.add_argument("--sign-min-abs-deg", type=float, default=15.0)
    parser.add_argument("--bad-error-deg", type=float, default=15.0)
    parser.add_argument("--high-error-deg", type=float, default=45.0)
    parser.add_argument("--worst-episodes", type=int, default=12)
    args = parser.parse_args()
    if args.temporal_window <= 0:
        raise ValueError("--temporal-window must be positive.")
    if args.temporal_delta_deg < 0.0:
        raise ValueError("--temporal-delta-deg must be non-negative.")
    if args.raw_norm_min < 0.0:
        raise ValueError("--raw-norm-min must be non-negative.")
    if args.cam_std_min < 0.0 or args.crop_std_min < 0.0:
        raise ValueError("--cam-std-min and --crop-std-min must be non-negative.")
    if args.sign_min_abs_deg < 0.0:
        raise ValueError("--sign-min-abs-deg must be non-negative.")
    return args


def _visible(row: dict[str, str], args: argparse.Namespace) -> bool:
    return (
        _float(row, "guard_visual_yaw_align_raw_norm") >= args.raw_norm_min
        and _float(row, "guard_visual_yaw_align_cam_std") >= args.cam_std_min
        and _float(row, "guard_visual_yaw_align_crop_std") >= args.crop_std_min
    )


def _stable_delta(history: deque[float], args: argparse.Namespace, period_deg: float) -> bool:
    if len(history) < args.temporal_window:
        return False
    values = list(history)[-args.temporal_window :]
    for previous, current in zip(values, values[1:]):
        if abs(_wrap_delta_deg(current - previous, period_deg)) > args.temporal_delta_deg:
            return False
    return True


def _stable_sign(history: deque[float], args: argparse.Namespace) -> bool:
    if len(history) < args.temporal_window:
        return False
    signs = [_sign(value, args.sign_min_abs_deg) for value in list(history)[-args.temporal_window :]]
    return signs[0] != 0 and all(sign == signs[0] for sign in signs)


def _action_bucket(reason: str) -> str:
    reason = str(reason)
    if "low_z_lateral_pop_recovery" in reason:
        return "low_z_lateral_pop_recovery"
    if "low_z_late_finish_descent" in reason:
        return "low_z_late_finish_descent"
    if "reacquire_relaxed_yaw" in reason:
        return "reacquire_relaxed_yaw"
    if reason.startswith("reacquire_descent"):
        return "reacquire_descent"
    if "large_xy_low_z_brake" in reason:
        return "large_xy_low_z_brake"
    if "low_visibility_brake" in reason:
        return "low_visibility_brake"
    if "aligned_descent" in reason:
        return "aligned_descent"
    if "xy_gate" in reason:
        return "xy_gate"
    if "raw_norm_gate" in reason:
        return "raw_norm_gate"
    if "cam_std_gate" in reason:
        return "cam_std_gate"
    if "crop_std_gate" in reason:
        return "crop_std_gate"
    if "deadband" in reason:
        return "deadband"
    if "yaw_ok_recenter" in reason:
        return "yaw_ok_recenter"
    if "applied" in reason:
        return "visual_yaw_applied"
    return reason or "unknown"


def _empty_stats() -> dict[str, float]:
    return {
        "rows": 0.0,
        "success_rows": 0.0,
        "timeout_rows": 0.0,
        "collision_rows": 0.0,
        "bad_error_rows": 0.0,
        "high_error_rows": 0.0,
        "sign_mismatch_rows": 0.0,
        "abs_error_sum": 0.0,
        "abs_error_max": float("nan"),
        "true_abs_sum": 0.0,
        "pred_abs_sum": 0.0,
        "dist_xy_sum": 0.0,
        "z_sum": 0.0,
        "down_action_rows": 0.0,
        "up_action_rows": 0.0,
    }


def _update_stats(stats: dict[str, float], feature: RowFeatures, args: argparse.Namespace) -> None:
    stats["rows"] += 1.0
    stats["abs_error_sum"] += feature.abs_error
    stats["true_abs_sum"] += feature.true_abs
    stats["pred_abs_sum"] += feature.pred_abs
    if math.isfinite(feature.dist_xy):
        stats["dist_xy_sum"] += feature.dist_xy
    if math.isfinite(feature.z_above_target):
        stats["z_sum"] += feature.z_above_target
    stats["abs_error_max"] = (
        feature.abs_error
        if not math.isfinite(stats["abs_error_max"])
        else max(stats["abs_error_max"], feature.abs_error)
    )
    outcome = feature.outcome.lower()
    if outcome == "success":
        stats["success_rows"] += 1.0
    elif outcome == "timeout":
        stats["timeout_rows"] += 1.0
    elif outcome == "collision":
        stats["collision_rows"] += 1.0
    if feature.abs_error > args.bad_error_deg:
        stats["bad_error_rows"] += 1.0
    if feature.abs_error > args.high_error_deg:
        stats["high_error_rows"] += 1.0
    if feature.sign_mismatch:
        stats["sign_mismatch_rows"] += 1.0
    final_z = _float(feature.row, "final_action_z")
    if math.isfinite(final_z):
        if final_z < 0.0:
            stats["down_action_rows"] += 1.0
        elif final_z > 0.0:
            stats["up_action_rows"] += 1.0


def _stats_rows(
    stats_by_name: dict[str, dict[str, float]],
    total_rows: float,
) -> list[dict[str, object]]:
    rows = []
    for name, stats in stats_by_name.items():
        count = stats["rows"]
        rows.append(
            {
                "name": name,
                "rows": int(count),
                "coverage": count / total_rows if total_rows > 0.0 else float("nan"),
                "success_row_rate": stats["success_rows"] / count if count else float("nan"),
                "timeout_row_rate": stats["timeout_rows"] / count if count else float("nan"),
                "collision_row_rate": stats["collision_rows"] / count if count else float("nan"),
                "mean_abs_error_deg": stats["abs_error_sum"] / count if count else float("nan"),
                "max_abs_error_deg": stats["abs_error_max"],
                "bad_error_rate": stats["bad_error_rows"] / count if count else float("nan"),
                "high_error_rate": stats["high_error_rows"] / count if count else float("nan"),
                "sign_mismatch_rate": stats["sign_mismatch_rows"] / count if count else float("nan"),
                "mean_true_abs_deg": stats["true_abs_sum"] / count if count else float("nan"),
                "mean_pred_abs_deg": stats["pred_abs_sum"] / count if count else float("nan"),
                "mean_xy": stats["dist_xy_sum"] / count if count else float("nan"),
                "mean_z": stats["z_sum"] / count if count else float("nan"),
                "down_action_rate": stats["down_action_rows"] / count if count else float("nan"),
                "up_action_rate": stats["up_action_rows"] / count if count else float("nan"),
            }
        )
    return rows


def _candidate_gates() -> list[CandidateGate]:
    return [
        CandidateGate("scoped_all", "All rows in the selected scope.", lambda f: f.scoped),
        CandidateGate("visible", "Visibility stats pass.", lambda f: f.scoped and f.visible),
        CandidateGate(
            "visible_delta_stable",
            "Visibility stats pass and last predictions are temporally stable.",
            lambda f: f.scoped and f.visible and f.delta_stable,
        ),
        CandidateGate(
            "yaw_reapply_mid_high",
            "Candidate for yaw correction: visible, delta-stable, pred yaw 30-90 deg, Z 50-130 mm.",
            lambda f: (
                f.scoped
                and f.visible
                and f.delta_stable
                and 30.0 <= f.pred_abs <= 90.0
                and 0.050 <= f.z_above_target <= 0.130
            ),
        ),
        CandidateGate(
            "yaw_reapply_high_only",
            "Candidate for high-yaw correction only: visible, delta-stable, pred yaw 60-120 deg, Z 50-130 mm.",
            lambda f: (
                f.scoped
                and f.visible
                and f.delta_stable
                and 60.0 <= f.pred_abs <= 120.0
                and 0.050 <= f.z_above_target <= 0.130
            ),
        ),
        CandidateGate(
            "descent_small_yaw_xy30",
            "Candidate for descent: visible, delta-stable, pred yaw <=8 deg, XY <=30 mm, Z 30-130 mm.",
            lambda f: (
                f.scoped
                and f.visible
                and f.delta_stable
                and f.pred_abs <= 8.0
                and f.dist_xy <= 0.030
                and 0.030 <= f.z_above_target <= 0.130
                and f.wall_contact <= 0
            ),
        ),
        CandidateGate(
            "descent_small_yaw_xy16",
            "Tighter descent candidate: visible, delta-stable, pred yaw <=8 deg, XY <=16 mm, Z 30-130 mm.",
            lambda f: (
                f.scoped
                and f.visible
                and f.delta_stable
                and f.pred_abs <= 8.0
                and f.dist_xy <= 0.016
                and 0.030 <= f.z_above_target <= 0.130
                and f.wall_contact <= 0
            ),
        ),
        CandidateGate(
            "descent_tiny_yaw_xy16",
            "Very conservative descent candidate: visible, delta-stable, pred yaw <=2 deg, XY <=16 mm, Z 30-130 mm.",
            lambda f: (
                f.scoped
                and f.visible
                and f.delta_stable
                and f.pred_abs <= 2.0
                and f.dist_xy <= 0.016
                and 0.030 <= f.z_above_target <= 0.130
                and f.wall_contact <= 0
            ),
        ),
        CandidateGate(
            "descent_tiny_yaw_xy8",
            "Very conservative descent candidate: visible, delta-stable, pred yaw <=2 deg, XY <=8 mm, Z 30-130 mm.",
            lambda f: (
                f.scoped
                and f.visible
                and f.delta_stable
                and f.pred_abs <= 2.0
                and f.dist_xy <= 0.008
                and 0.030 <= f.z_above_target <= 0.130
                and f.wall_contact <= 0
            ),
        ),
        CandidateGate(
            "descent_tiny_yaw_xy8_mid_z",
            "Tiny-yaw descent candidate away from final low-Z tail: pred yaw <=2 deg, XY <=8 mm, Z 45-130 mm.",
            lambda f: (
                f.scoped
                and f.visible
                and f.delta_stable
                and f.pred_abs <= 2.0
                and f.dist_xy <= 0.008
                and 0.045 <= f.z_above_target <= 0.130
                and f.wall_contact <= 0
            ),
        ),
        CandidateGate(
            "hold_recenter_only",
            "Rows that are scoped but fail both yaw-correction and descent candidates.",
            lambda f: (
                f.scoped
                and not (
                    f.visible
                    and f.delta_stable
                    and 30.0 <= f.pred_abs <= 90.0
                    and 0.050 <= f.z_above_target <= 0.130
                )
                and not (
                    f.visible
                    and f.delta_stable
                    and f.pred_abs <= 8.0
                    and f.dist_xy <= 0.030
                    and 0.030 <= f.z_above_target <= 0.130
                    and f.wall_contact <= 0
                )
            ),
        ),
    ]


@dataclass
class EpisodeSummary:
    file: str
    seed: str
    episode: str
    outcome: str
    scoped_rows: int = 0
    visible_delta_rows: int = 0
    yaw_candidate_rows: int = 0
    descent_candidate_rows: int = 0
    sign_mismatch_rows: int = 0
    high_error_rows: int = 0
    max_abs_error_deg: float = float("nan")
    first_scoped_step: str = ""
    last_step: str = ""


def _make_feature(
    row: dict[str, str],
    args: argparse.Namespace,
    delta_stable: bool,
    sign_stable: bool,
) -> RowFeatures | None:
    pred_signed = _float(row, "guard_visual_yaw_align_pred_signed_error_deg")
    true_signed = _float(row, "shape_yaw_signed_error_deg")
    if not (math.isfinite(pred_signed) and math.isfinite(true_signed)):
        return None
    period_deg = _profile_period(row)
    abs_error = abs(_wrap_delta_deg(pred_signed - true_signed, period_deg))
    if not math.isfinite(abs_error):
        return None
    pred_abs = abs(_wrap_delta_deg(pred_signed, period_deg))
    true_abs = abs(_wrap_delta_deg(true_signed, period_deg))
    pred_sign = _sign(pred_signed, args.sign_min_abs_deg)
    true_sign = _sign(true_signed, args.sign_min_abs_deg)
    scoped = (
        _bool(row, "guard_visual_yaw_align_reacquire_active")
        if args.scope == "reacquire"
        else _bool(row, "guard_visual_yaw_align_active")
    )
    return RowFeatures(
        row=row,
        visible=_visible(row, args),
        delta_stable=delta_stable,
        sign_stable=sign_stable,
        pred_signed=pred_signed,
        true_signed=true_signed,
        pred_abs=pred_abs,
        true_abs=true_abs,
        abs_error=abs_error,
        sign_mismatch=pred_sign != 0 and true_sign != 0 and pred_sign != true_sign,
        dist_xy=_first_float(row, ("pre_dist_xy", "dist_xy")),
        z_above_target=_first_float(row, ("pre_z_above_target", "z_above_target")),
        wall_contact=int(_float(row, "peg_hole_contact_wall_count", 0.0)),
        action_bucket=_action_bucket(row.get("guard_visual_yaw_align_reason", "")),
        outcome=row.get("episode_outcome", ""),
        scoped=scoped,
    )


def analyze_trace(
    path: Path,
    args: argparse.Namespace,
    gates: list[CandidateGate],
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]], dict[tuple[str, str, str], EpisodeSummary]]:
    gate_stats = {gate.name: _empty_stats() for gate in gates}
    action_stats: dict[str, dict[str, float]] = defaultdict(_empty_stats)
    episodes: dict[tuple[str, str, str], EpisodeSummary] = {}
    pred_history: dict[tuple[str, str, str], deque[float]] = defaultdict(
        lambda: deque(maxlen=max(1, args.temporal_window))
    )

    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = (str(path), row.get("seed", ""), row.get("episode", ""))
            period_deg = _profile_period(row)
            pred_signed = _float(row, "guard_visual_yaw_align_pred_signed_error_deg")
            history = pred_history[key]
            if math.isfinite(pred_signed):
                history.append(pred_signed)
            delta_stable = _stable_delta(history, args, period_deg)
            sign_stable = _stable_sign(history, args)
            feature = _make_feature(row, args, delta_stable, sign_stable)
            if feature is None or not feature.scoped:
                continue

            summary = episodes.setdefault(
                key,
                EpisodeSummary(
                    file=str(path),
                    seed=row.get("seed", ""),
                    episode=row.get("episode", ""),
                    outcome=row.get("episode_outcome", ""),
                ),
            )
            summary.scoped_rows += 1
            summary.outcome = row.get("episode_outcome", summary.outcome)
            summary.last_step = row.get("step", summary.last_step)
            if not summary.first_scoped_step:
                summary.first_scoped_step = row.get("step", "")
            if feature.visible and feature.delta_stable:
                summary.visible_delta_rows += 1
            if feature.abs_error > args.high_error_deg:
                summary.high_error_rows += 1
            if feature.sign_mismatch:
                summary.sign_mismatch_rows += 1
            summary.max_abs_error_deg = (
                feature.abs_error
                if not math.isfinite(summary.max_abs_error_deg)
                else max(summary.max_abs_error_deg, feature.abs_error)
            )

            _update_stats(action_stats[feature.action_bucket], feature, args)
            for gate in gates:
                if gate.predicate(feature):
                    _update_stats(gate_stats[gate.name], feature, args)
                    if gate.name == "yaw_reapply_mid_high":
                        summary.yaw_candidate_rows += 1
                    elif gate.name == "descent_small_yaw_xy30":
                        summary.descent_candidate_rows += 1

    return gate_stats, dict(action_stats), episodes


def _merge_stats(stats_list: Iterable[dict[str, dict[str, float]]], names: Iterable[str] | None = None) -> dict[str, dict[str, float]]:
    if names is None:
        names = sorted({name for stats in stats_list for name in stats})
    merged = {name: _empty_stats() for name in names}
    for stats_by_name in stats_list:
        for name, stats in stats_by_name.items():
            target = merged.setdefault(name, _empty_stats())
            for key, value in stats.items():
                if key == "abs_error_max":
                    if math.isfinite(value):
                        target[key] = value if not math.isfinite(target[key]) else max(target[key], value)
                else:
                    target[key] += value
    return merged


def _worst_episode_rows(episodes: Iterable[EpisodeSummary], limit: int) -> list[EpisodeSummary]:
    candidates = [episode for episode in episodes if episode.scoped_rows > 0]
    candidates.sort(
        key=lambda episode: (
            episode.outcome == "success",
            -episode.sign_mismatch_rows,
            -episode.high_error_rows,
            -episode.scoped_rows,
            -episode.max_abs_error_deg if math.isfinite(episode.max_abs_error_deg) else 0.0,
        )
    )
    return candidates[: max(0, limit)]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["name"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_episode_csv(path: Path, episodes: list[EpisodeSummary]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "file": episode.file,
            "seed": episode.seed,
            "episode": episode.episode,
            "outcome": episode.outcome,
            "scoped_rows": episode.scoped_rows,
            "visible_delta_rows": episode.visible_delta_rows,
            "yaw_candidate_rows": episode.yaw_candidate_rows,
            "descent_candidate_rows": episode.descent_candidate_rows,
            "sign_mismatch_rows": episode.sign_mismatch_rows,
            "high_error_rows": episode.high_error_rows,
            "max_abs_error_deg": _format_float(episode.max_abs_error_deg),
            "first_scoped_step": episode.first_scoped_step,
            "last_step": episode.last_step,
        }
        for episode in episodes
    ]
    _write_csv(path, rows)


def _append_stats_table(lines: list[str], title: str, rows: list[dict[str, object]]) -> None:
    lines.extend(
        [
            "",
            f"## {title}",
            "",
            "| name | rows | coverage | success rows | timeout rows | collision rows | mean err | max err | >bad | >high | sign mismatch | mean true | mean pred | mean XY | mean Z | down | up |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            "| {name} | {rows} | {coverage} | {success_row_rate} | {timeout_row_rate} | {collision_row_rate} | {mean_abs_error_deg} | {max_abs_error_deg} | {bad_error_rate} | {high_error_rate} | {sign_mismatch_rate} | {mean_true_abs_deg} | {mean_pred_abs_deg} | {mean_xy} | {mean_z} | {down_action_rate} | {up_action_rate} |".format(
                name=row["name"],
                rows=row["rows"],
                coverage=_format_float(float(row["coverage"])),
                success_row_rate=_format_float(float(row["success_row_rate"])),
                timeout_row_rate=_format_float(float(row["timeout_row_rate"])),
                collision_row_rate=_format_float(float(row["collision_row_rate"])),
                mean_abs_error_deg=_format_float(float(row["mean_abs_error_deg"])),
                max_abs_error_deg=_format_float(float(row["max_abs_error_deg"])),
                bad_error_rate=_format_float(float(row["bad_error_rate"])),
                high_error_rate=_format_float(float(row["high_error_rate"])),
                sign_mismatch_rate=_format_float(float(row["sign_mismatch_rate"])),
                mean_true_abs_deg=_format_float(float(row["mean_true_abs_deg"])),
                mean_pred_abs_deg=_format_float(float(row["mean_pred_abs_deg"])),
                mean_xy=_format_float(float(row["mean_xy"]), digits=4),
                mean_z=_format_float(float(row["mean_z"]), digits=4),
                down_action_rate=_format_float(float(row["down_action_rate"])),
                up_action_rate=_format_float(float(row["up_action_rate"])),
            )
        )


def _write_md(
    path: Path,
    args: argparse.Namespace,
    gates: list[CandidateGate],
    gate_rows: list[dict[str, object]],
    action_rows: list[dict[str, object]],
    episodes: list[EpisodeSummary],
    total_rows: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Visual Yaw Action-Selection Analysis",
        "",
        "Offline diagnostic only: this compares visual-yaw predictions with simulator truth recorded in traces.",
        "",
        f"- Traces: `{len(args.traces)}`",
        f"- Scope: `{args.scope}`",
        f"- Scoped rows: `{int(total_rows)}`",
        f"- Visibility gate: raw_norm >= `{args.raw_norm_min}`, cam_std >= `{args.cam_std_min}`, crop_std >= `{args.crop_std_min}`",
        f"- Temporal gate: last `{args.temporal_window}` predictions, max adjacent delta <= `{args.temporal_delta_deg} deg`",
        f"- Sign mismatch ignores predictions/truth below `{args.sign_min_abs_deg} deg`",
        "",
        "## Candidate Gates",
        "",
    ]
    for gate in gates:
        lines.append(f"- `{gate.name}`: {gate.description}")
    _append_stats_table(lines, "Gate Summary", gate_rows)
    _append_stats_table(lines, "Current Action Buckets", action_rows)
    lines.extend(
        [
            "",
            "## Worst Episodes",
            "",
            "| file | seed | episode | outcome | scoped rows | visible-delta rows | yaw cand | descent cand | sign mismatch | high error | max err | first step | last step |",
            "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for episode in episodes:
        lines.append(
            "| {file} | {seed} | {episode} | {outcome} | {scoped_rows} | {visible_delta_rows} | {yaw_candidate_rows} | {descent_candidate_rows} | {sign_mismatch_rows} | {high_error_rows} | {max_abs} | {first_step} | {last_step} |".format(
                file=Path(episode.file).name,
                seed=episode.seed,
                episode=episode.episode,
                outcome=episode.outcome,
                scoped_rows=episode.scoped_rows,
                visible_delta_rows=episode.visible_delta_rows,
                yaw_candidate_rows=episode.yaw_candidate_rows,
                descent_candidate_rows=episode.descent_candidate_rows,
                sign_mismatch_rows=episode.sign_mismatch_rows,
                high_error_rows=episode.high_error_rows,
                max_abs=_format_float(episode.max_abs_error_deg),
                first_step=episode.first_scoped_step,
                last_step=episode.last_step,
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    gates = _candidate_gates()
    gate_stats_list = []
    action_stats_list = []
    all_episodes: dict[tuple[str, str, str], EpisodeSummary] = {}
    for path in args.traces:
        gate_stats, action_stats, episodes = analyze_trace(path, args, gates)
        gate_stats_list.append(gate_stats)
        action_stats_list.append(action_stats)
        all_episodes.update(episodes)

    gate_stats = _merge_stats(gate_stats_list, names=[gate.name for gate in gates])
    action_stats = _merge_stats(action_stats_list)
    total_rows = gate_stats["scoped_all"]["rows"]
    gate_rows = _stats_rows(gate_stats, total_rows)
    action_rows = _stats_rows(action_stats, total_rows)
    action_rows.sort(key=lambda row: (-int(row["rows"]), str(row["name"])))
    worst = _worst_episode_rows(all_episodes.values(), args.worst_episodes)

    if args.output_csv:
        _write_csv(args.output_csv, gate_rows + action_rows)
    if args.episode_output_csv:
        _write_episode_csv(args.episode_output_csv, worst)
    if args.output_md:
        _write_md(args.output_md, args, gates, gate_rows, action_rows, worst, total_rows)

    writer = csv.DictWriter(sys.stdout, fieldnames=list((gate_rows + action_rows)[0].keys()))
    writer.writeheader()
    writer.writerows(gate_rows + action_rows)


if __name__ == "__main__":
    main()
