"""Analyze false-small visual-yaw predictions in eval step traces.

This is an offline sim diagnostic. It compares visual-yaw predictions with
simulator-truth yaw columns recorded in traces. Do not use the truth columns as
real-robot feedback; use this only to design deployable confidence gates.
"""

from __future__ import annotations

import argparse
import csv
import glob
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable


def _float(row: dict[str, str], key: str, default: float = float("nan")) -> float:
    try:
        value = row.get(key, "")
        if value == "":
            return default
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def _bool(row: dict[str, str], key: str) -> bool:
    return str(row.get(key, "")).strip().lower() in {"1", "1.0", "true", "yes", "y"}


def _fmt(value: float, digits: int = 3) -> str:
    if not math.isfinite(value):
        return ""
    return f"{value:.{digits}f}"


def _ratio(num: int | float, den: int | float) -> float:
    return float(num) / float(den) if den else float("nan")


def _mean(values: Iterable[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else float("nan")


def _min(values: Iterable[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return min(finite) if finite else float("nan")


def _max(values: Iterable[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return max(finite) if finite else float("nan")


def _bucket(value: float, edges: list[float], labels: list[str]) -> str:
    if not math.isfinite(value):
        return "nan"
    for edge, label in zip(edges, labels):
        if value < edge:
            return label
    return labels[-1]


def _z_bucket_m(value_m: float) -> str:
    return _bucket(
        1000.0 * value_m,
        [0.0, 5.0, 10.0, 20.0, 35.0, 60.0],
        ["<0", "0-5", "5-10", "10-20", "20-35", "35-60"],
    )


def _xy_bucket_m(value_m: float) -> str:
    return _bucket(
        1000.0 * value_m,
        [1.0, 2.0, 3.0, 5.0, 10.0, 20.0],
        ["0-1", "1-2", "2-3", "3-5", "5-10", "10-20"],
    )


def _reason_bucket(reason: str) -> str:
    reason = str(reason)
    if reason.startswith("freeze_aligned_target_descent_"):
        return "freeze_descent"
    if reason.startswith("freeze_aligned_target_recenter_"):
        return "freeze_recenter"
    if "descent_abort" in reason:
        return "descent_abort"
    if "target_hold_z_gate" in reason:
        return "target_hold_z_gate"
    if reason == "z_gate" or reason.endswith("_z_gate"):
        return "z_gate"
    if "applied" in reason:
        return "applied"
    if "deadband" in reason:
        return "deadband"
    if "inactive" in reason:
        return "inactive"
    if "xy_gate" in reason:
        return "xy_gate"
    if "raw_norm_gate" in reason:
        return "raw_norm_gate"
    if "crop_std_gate" in reason:
        return "crop_std_gate"
    if "cam_std_gate" in reason:
        return "cam_std_gate"
    return reason or "unknown"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expand_inputs(inputs: list[str]) -> list[Path]:
    traces: list[Path] = []
    for item in inputs:
        matches = [Path(path) for path in glob.glob(item)]
        if not matches:
            matches = [Path(item)]
        for path in matches:
            if path.is_dir():
                traces.extend(sorted(path.rglob("*_steps.csv")))
            elif path.exists():
                traces.append(path)
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in traces:
        key = str(path.resolve())
        if key not in seen:
            seen.add(key)
            deduped.append(path)
    return deduped


def _episode_rows(rows: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row.get("episode", "0"), row.get("seed", ""))].append(row)
    return [
        sorted(group, key=lambda row: _float(row, "step", 0.0))
        for _, group in sorted(groups.items(), key=lambda item: (item[0][1], item[0][0]))
    ]


def _outcome(last: dict[str, str]) -> str:
    if _bool(last, "success"):
        return "success"
    if _bool(last, "collision"):
        return "collision"
    if _bool(last, "timeout"):
        return "timeout"
    return last.get("episode_outcome", "") or "unknown"


def _is_freeze_descent(row: dict[str, str]) -> bool:
    reason = row.get("guard_visual_yaw_align_reason", "")
    return reason.startswith("freeze_aligned_target_descent_")


def _has_prediction(row: dict[str, str]) -> bool:
    return math.isfinite(_float(row, "guard_visual_yaw_align_pred_abs_error_deg"))


def _row_features(row: dict[str, str]) -> dict[str, float | str | bool]:
    pred_abs = _float(row, "guard_visual_yaw_align_pred_abs_error_deg")
    true_abs = _float(row, "shape_yaw_error_deg")
    return {
        "pred_abs": pred_abs,
        "true_abs": true_abs,
        "raw_norm": _float(row, "guard_visual_yaw_align_raw_norm"),
        "cam_std": _float(row, "guard_visual_yaw_align_cam_std"),
        "crop_std": _float(row, "guard_visual_yaw_align_crop_std"),
        "xy": _float(row, "post_dist_xy", _float(row, "pre_dist_xy")),
        "z": _float(row, "post_z_above_target", _float(row, "pre_z_above_target")),
        "reason": row.get("guard_visual_yaw_align_reason", ""),
        "reason_bucket": _reason_bucket(row.get("guard_visual_yaw_align_reason", "")),
        "freeze_descent": _is_freeze_descent(row),
        "active": _bool(row, "guard_visual_yaw_align_active")
        or _bool(row, "guard_visual_yaw_align_applied"),
        "blocked_down": _bool(row, "guard_visual_yaw_align_blocked_down"),
        "down_action": _float(row, "final_action_z") < 0.0,
        "has_prediction": math.isfinite(pred_abs),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="Trace CSVs, directories, or glob patterns.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/visual_yaw_false_small_analysis"))
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--pred-small-deg", type=float, default=4.0)
    parser.add_argument("--truth-large-deg", type=float, default=12.0)
    parser.add_argument("--truth-critical-deg", type=float, default=18.0)
    parser.add_argument("--low-z-max", type=float, default=0.035)
    parser.add_argument("--near-xy-max", type=float, default=0.005)
    parser.add_argument("--scope-profile", default="", help="Optional geometry profile filter.")
    args = parser.parse_args()
    if args.pred_small_deg < 0.0:
        raise ValueError("--pred-small-deg must be non-negative")
    if args.truth_large_deg < 0.0 or args.truth_critical_deg < 0.0:
        raise ValueError("--truth thresholds must be non-negative")
    if args.low_z_max < 0.0 or args.near_xy_max < 0.0:
        raise ValueError("--low-z-max and --near-xy-max must be non-negative")
    return args


def analyze_trace(path: Path, args: argparse.Namespace) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    episode_summaries: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    for rows in _episode_rows(_read_csv(path)):
        if not rows:
            continue
        first = rows[0]
        last = rows[-1]
        profile = (
            last.get("geometry_profile")
            or last.get("guard_visual_yaw_align_profile")
            or first.get("geometry_profile", "")
        )
        if args.scope_profile and profile != args.scope_profile:
            continue
        outcome = _outcome(last)
        features = [_row_features(row) for row in rows]
        active = [feat for feat in features if bool(feat["active"])]
        pred_rows = [feat for feat in active if bool(feat["has_prediction"])]
        false_small = [
            feat
            for feat in pred_rows
            if float(feat["pred_abs"]) <= args.pred_small_deg
            and float(feat["true_abs"]) >= args.truth_large_deg
        ]
        critical_false_small = [
            feat for feat in false_small if float(feat["true_abs"]) >= args.truth_critical_deg
        ]
        freeze_false_small = [
            feat for feat in false_small if bool(feat["freeze_descent"])
        ]
        low_z_false_small = [
            feat
            for feat in false_small
            if math.isfinite(float(feat["z"])) and float(feat["z"]) <= args.low_z_max
        ]
        near_false_small = [
            feat
            for feat in false_small
            if math.isfinite(float(feat["xy"])) and float(feat["xy"]) <= args.near_xy_max
        ]
        z_gate_after_false_small = 0
        if false_small:
            first_false_index = min(i for i, feat in enumerate(features) if feat in false_small)
            z_gate_after_false_small = sum(
                1
                for feat in features[first_false_index:]
                if feat["reason_bucket"] in {"z_gate", "target_hold_z_gate"}
            )
        first_false = false_small[0] if false_small else None
        max_true_false = _max(float(feat["true_abs"]) for feat in false_small)
        row_summary = {
            "trace": str(path),
            "label": path.parent.name,
            "file": path.name,
            "episode": first.get("episode", "0"),
            "seed": first.get("seed", ""),
            "profile": profile,
            "outcome": outcome,
            "steps": int(_float(last, "post_step_count", _float(last, "step", 0.0))),
            "success": outcome == "success",
            "collision": outcome == "collision",
            "timeout": outcome == "timeout",
            "active_rows": len(active),
            "prediction_rows": len(pred_rows),
            "false_small_rows": len(false_small),
            "critical_false_small_rows": len(critical_false_small),
            "freeze_false_small_rows": len(freeze_false_small),
            "low_z_false_small_rows": len(low_z_false_small),
            "near_xy_false_small_rows": len(near_false_small),
            "z_gate_after_false_small_rows": z_gate_after_false_small,
            "first_false_small_step": (
                _float(rows[features.index(first_false)], "step") if first_false else float("nan")
            ),
            "first_false_small_z_mm": 1000.0 * float(first_false["z"]) if first_false else float("nan"),
            "first_false_small_xy_mm": 1000.0 * float(first_false["xy"]) if first_false else float("nan"),
            "first_false_small_pred_deg": float(first_false["pred_abs"]) if first_false else float("nan"),
            "first_false_small_true_deg": float(first_false["true_abs"]) if first_false else float("nan"),
            "max_true_deg_during_false_small": max_true_false,
            "final_yaw_deg": _float(last, "shape_yaw_error_deg"),
            "final_xy_mm": 1000.0 * _float(last, "post_dist_xy"),
            "final_z_mm": 1000.0 * _float(last, "post_z_above_target"),
        }
        episode_summaries.append(row_summary)
        for index, feat in enumerate(features):
            if feat in false_small:
                row = rows[index]
                event_rows.append(
                    {
                        "trace": str(path),
                        "label": path.parent.name,
                        "file": path.name,
                        "episode": row.get("episode", "0"),
                        "seed": row.get("seed", ""),
                        "profile": profile,
                        "outcome": outcome,
                        "step": row.get("step", ""),
                        "pred_abs_deg": feat["pred_abs"],
                        "true_abs_deg": feat["true_abs"],
                        "raw_norm": feat["raw_norm"],
                        "cam_std": feat["cam_std"],
                        "crop_std": feat["crop_std"],
                        "xy_mm": 1000.0 * float(feat["xy"]),
                        "z_mm": 1000.0 * float(feat["z"]),
                        "z_bucket": _z_bucket_m(float(feat["z"])),
                        "xy_bucket": _xy_bucket_m(float(feat["xy"])),
                        "reason_bucket": feat["reason_bucket"],
                        "reason": feat["reason"],
                        "freeze_descent": feat["freeze_descent"],
                        "blocked_down": feat["blocked_down"],
                        "down_action": feat["down_action"],
                    }
                )
    return episode_summaries, event_rows


def _write_csv(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _count_by(rows: list[dict[str, object]], key: str) -> Counter[str]:
    return Counter(str(row.get(key, "")) for row in rows)


def _gate_table(events: list[dict[str, object]], episodes: list[dict[str, object]]) -> list[dict[str, object]]:
    failed_seed_eps = {
        (row["trace"], row["episode"], row["seed"])
        for row in episodes
        if not bool(row["success"])
    }
    success_seed_eps = {
        (row["trace"], row["episode"], row["seed"])
        for row in episodes
        if bool(row["success"])
    }
    gates = {
        "all_false_small": lambda row: True,
        "freeze_false_small": lambda row: str(row["freeze_descent"]) == "True" or row["freeze_descent"] is True,
        "low_z_false_small": lambda row: _float_obj(row["z_mm"]) <= 35.0,
        "near_xy_false_small": lambda row: _float_obj(row["xy_mm"]) <= 5.0,
        "low_z_near_xy_false_small": lambda row: _float_obj(row["z_mm"]) <= 35.0 and _float_obj(row["xy_mm"]) <= 5.0,
        "freeze_low_z_false_small": lambda row: (str(row["freeze_descent"]) == "True" or row["freeze_descent"] is True)
        and _float_obj(row["z_mm"]) <= 35.0,
        "freeze_low_z_near_xy_false_small": lambda row: (str(row["freeze_descent"]) == "True" or row["freeze_descent"] is True)
        and _float_obj(row["z_mm"]) <= 35.0
        and _float_obj(row["xy_mm"]) <= 5.0,
    }
    table: list[dict[str, object]] = []
    for name, predicate in gates.items():
        matched = [row for row in events if predicate(row)]
        matched_eps = {(row["trace"], row["episode"], row["seed"]) for row in matched}
        table.append(
            {
                "gate": name,
                "rows": len(matched),
                "episodes": len(matched_eps),
                "failed_episodes_hit": len(matched_eps & failed_seed_eps),
                "success_episodes_hit": len(matched_eps & success_seed_eps),
                "mean_true_deg": _mean(_float_obj(row["true_abs_deg"]) for row in matched),
                "mean_pred_deg": _mean(_float_obj(row["pred_abs_deg"]) for row in matched),
                "mean_z_mm": _mean(_float_obj(row["z_mm"]) for row in matched),
                "mean_xy_mm": _mean(_float_obj(row["xy_mm"]) for row in matched),
            }
        )
    return table


def _proxy_event_candidates(
    rows: list[dict[str, str]],
    args: argparse.Namespace,
) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for row in rows:
        feat = _row_features(row)
        if not bool(feat["active"]) or not bool(feat["has_prediction"]):
            continue
        pred_abs = float(feat["pred_abs"])
        if not math.isfinite(pred_abs) or pred_abs > args.pred_small_deg:
            continue
        events.append(
            {
                "pred_abs_deg": pred_abs,
                "true_abs_deg": float(feat["true_abs"]),
                "raw_norm": feat["raw_norm"],
                "cam_std": feat["cam_std"],
                "crop_std": feat["crop_std"],
                "xy_mm": 1000.0 * float(feat["xy"]),
                "z_mm": 1000.0 * float(feat["z"]),
                "reason_bucket": feat["reason_bucket"],
                "reason": feat["reason"],
                "freeze_descent": feat["freeze_descent"],
                "blocked_down": feat["blocked_down"],
                "down_action": feat["down_action"],
            }
        )
    return events


def _proxy_predicates() -> dict[str, Callable[[dict[str, object]], bool]]:
    return {
        "pred_small": lambda row: True,
        "freeze_pred_small": lambda row: _bool_obj(row["freeze_descent"]),
        "low_z_pred_small": lambda row: _float_obj(row["z_mm"]) <= 35.0,
        "near_xy_pred_small": lambda row: _float_obj(row["xy_mm"]) <= 5.0,
        "low_z_near_xy_pred_small": lambda row: _float_obj(row["z_mm"]) <= 35.0
        and _float_obj(row["xy_mm"]) <= 5.0,
        "freeze_low_z_pred_small": lambda row: _bool_obj(row["freeze_descent"])
        and _float_obj(row["z_mm"]) <= 35.0,
        "freeze_near_xy_pred_small": lambda row: _bool_obj(row["freeze_descent"])
        and _float_obj(row["xy_mm"]) <= 5.0,
        "freeze_low_z_near_xy_pred_small": lambda row: _bool_obj(row["freeze_descent"])
        and _float_obj(row["z_mm"]) <= 35.0
        and _float_obj(row["xy_mm"]) <= 5.0,
        "freeze_low_z_near_xy_down_pred_small": lambda row: _bool_obj(row["freeze_descent"])
        and _float_obj(row["z_mm"]) <= 35.0
        and _float_obj(row["xy_mm"]) <= 5.0
        and _bool_obj(row["down_action"]),
    }


def _proxy_gate_table(traces: list[Path], args: argparse.Namespace) -> list[dict[str, object]]:
    gates = _proxy_predicates()
    rows_by_episode: list[dict[str, object]] = []
    for trace in traces:
        for episode_rows in _episode_rows(_read_csv(trace)):
            if not episode_rows:
                continue
            first = episode_rows[0]
            last = episode_rows[-1]
            profile = (
                last.get("geometry_profile")
                or last.get("guard_visual_yaw_align_profile")
                or first.get("geometry_profile", "")
            )
            if args.scope_profile and profile != args.scope_profile:
                continue
            outcome = _outcome(last)
            proxy_events = _proxy_event_candidates(episode_rows, args)
            for event in proxy_events:
                rows_by_episode.append(
                    {
                        "trace": str(trace),
                        "episode": first.get("episode", "0"),
                        "seed": first.get("seed", ""),
                        "profile": profile,
                        "outcome": outcome,
                        "success": outcome == "success",
                        **event,
                    }
                )

    failed_seed_eps = {
        (row["trace"], row["episode"], row["seed"])
        for row in rows_by_episode
        if not bool(row["success"])
    }
    success_seed_eps = {
        (row["trace"], row["episode"], row["seed"])
        for row in rows_by_episode
        if bool(row["success"])
    }
    table: list[dict[str, object]] = []
    for name, predicate in gates.items():
        matched = [row for row in rows_by_episode if predicate(row)]
        matched_eps = {(row["trace"], row["episode"], row["seed"]) for row in matched}
        success_rows = [row for row in matched if bool(row["success"])]
        failed_rows = [row for row in matched if not bool(row["success"])]
        table.append(
            {
                "gate": name,
                "rows": len(matched),
                "episodes": len(matched_eps),
                "failed_episodes_hit": len(matched_eps & failed_seed_eps),
                "success_episodes_hit": len(matched_eps & success_seed_eps),
                "failed_rows": len(failed_rows),
                "success_rows": len(success_rows),
                "mean_true_deg": _mean(_float_obj(row["true_abs_deg"]) for row in matched),
                "mean_pred_deg": _mean(_float_obj(row["pred_abs_deg"]) for row in matched),
                "mean_z_mm": _mean(_float_obj(row["z_mm"]) for row in matched),
                "mean_xy_mm": _mean(_float_obj(row["xy_mm"]) for row in matched),
            }
        )
    return table


def _max_run(matches: list[bool]) -> int:
    longest = 0
    current = 0
    for matched in matches:
        if matched:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _first_matched(events: list[dict[str, object]], matches: list[bool]) -> dict[str, object] | None:
    for event, matched in zip(events, matches):
        if matched:
            return event
    return None


def _proxy_episode_table(traces: list[Path], args: argparse.Namespace) -> list[dict[str, object]]:
    gates = _proxy_predicates()
    rows_out: list[dict[str, object]] = []
    focused_gates = [
        "pred_small",
        "freeze_pred_small",
        "freeze_low_z_near_xy_pred_small",
    ]
    for trace in traces:
        for episode_rows in _episode_rows(_read_csv(trace)):
            if not episode_rows:
                continue
            first = episode_rows[0]
            last = episode_rows[-1]
            profile = (
                last.get("geometry_profile")
                or last.get("guard_visual_yaw_align_profile")
                or first.get("geometry_profile", "")
            )
            if args.scope_profile and profile != args.scope_profile:
                continue
            outcome = _outcome(last)
            proxy_events = _proxy_event_candidates(episode_rows, args)
            summary: dict[str, object] = {
                "trace": str(trace),
                "file": trace.name,
                "episode": first.get("episode", "0"),
                "seed": first.get("seed", ""),
                "profile": profile,
                "outcome": outcome,
                "success": outcome == "success",
                "collision": outcome == "collision",
                "timeout": outcome == "timeout",
                "steps": int(_float(last, "post_step_count", _float(last, "step", 0.0))),
                "final_true_yaw_deg": _float(last, "shape_yaw_error_deg"),
                "final_xy_mm": 1000.0 * _float(last, "post_dist_xy"),
                "final_z_mm": 1000.0 * _float(last, "post_z_above_target"),
            }
            for gate, predicate in gates.items():
                matches = [bool(predicate(event)) for event in proxy_events]
                matched_events = [
                    event for event, matched in zip(proxy_events, matches) if matched
                ]
                first_matched = _first_matched(proxy_events, matches)
                summary[f"{gate}_rows"] = len(matched_events)
                summary[f"{gate}_max_run"] = _max_run(matches)
                summary[f"{gate}_mean_pred_deg"] = _mean(
                    _float_obj(event["pred_abs_deg"]) for event in matched_events
                )
                summary[f"{gate}_mean_true_deg"] = _mean(
                    _float_obj(event["true_abs_deg"]) for event in matched_events
                )
                summary[f"{gate}_mean_raw_norm"] = _mean(
                    _float_obj(event["raw_norm"]) for event in matched_events
                )
                summary[f"{gate}_mean_cam_std"] = _mean(
                    _float_obj(event["cam_std"]) for event in matched_events
                )
                summary[f"{gate}_mean_crop_std"] = _mean(
                    _float_obj(event["crop_std"]) for event in matched_events
                )
                if gate in focused_gates:
                    summary[f"{gate}_first_z_mm"] = (
                        _float_obj(first_matched["z_mm"])
                        if first_matched is not None
                        else float("nan")
                    )
                    summary[f"{gate}_first_xy_mm"] = (
                        _float_obj(first_matched["xy_mm"])
                        if first_matched is not None
                        else float("nan")
                    )
                    summary[f"{gate}_first_true_deg"] = (
                        _float_obj(first_matched["true_abs_deg"])
                        if first_matched is not None
                        else float("nan")
                    )
            rows_out.append(summary)
    return rows_out


def _float_obj(value: object, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def _bool_obj(value: object) -> bool:
    return str(value).strip().lower() in {"1", "1.0", "true", "yes", "y"}


def _write_markdown(
    episodes: list[dict[str, object]],
    events: list[dict[str, object]],
    gates: list[dict[str, object]],
    proxy_gates: list[dict[str, object]],
    proxy_episodes: list[dict[str, object]],
    traces: list[Path],
    path: Path,
    args: argparse.Namespace,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    success = sum(1 for row in episodes if bool(row["success"]))
    collision = sum(1 for row in episodes if bool(row["collision"]))
    timeout = sum(1 for row in episodes if bool(row["timeout"]))
    failed_events = [row for row in events if row["outcome"] != "success"]
    success_events = [row for row in events if row["outcome"] == "success"]
    lines = [
        "# Visual-Yaw False-Small Analysis",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Traces: `{len(traces)}`",
        f"- Episodes: `{len(episodes)}`",
        f"- Outcomes: success `{success}`, collision `{collision}`, timeout `{timeout}`",
        f"- False-small condition: pred `<= {args.pred_small_deg:g} deg`, truth `>= {args.truth_large_deg:g} deg`",
        f"- Critical truth threshold: `>= {args.truth_critical_deg:g} deg`",
        "",
        "## Inputs",
        "",
    ]
    for trace in traces:
        lines.append(f"- `{trace}`")
    lines.extend(
        [
            "",
            "## Event Summary",
            "",
            f"- False-small rows: `{len(events)}`",
            f"- In success episodes: `{len(success_events)}` rows",
            f"- In failed episodes: `{len(failed_events)}` rows",
            f"- Mean true yaw on false-small rows: `{_fmt(_mean(_float_obj(row['true_abs_deg']) for row in events))} deg`",
            f"- Mean predicted yaw on false-small rows: `{_fmt(_mean(_float_obj(row['pred_abs_deg']) for row in events))} deg`",
            "",
            "## Gate Coverage",
            "",
            "| Gate | Rows | Episodes | Failed ep hit | Success ep hit | Mean true | Mean pred | Mean Z mm | Mean XY mm |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in gates:
        lines.append(
            "| {gate} | {rows} | {episodes} | {failed_episodes_hit} | {success_episodes_hit} | {mean_true_deg} | {mean_pred_deg} | {mean_z_mm} | {mean_xy_mm} |".format(
                gate=row["gate"],
                rows=row["rows"],
                episodes=row["episodes"],
                failed_episodes_hit=row["failed_episodes_hit"],
                success_episodes_hit=row["success_episodes_hit"],
                mean_true_deg=_fmt(_float_obj(row["mean_true_deg"])),
                mean_pred_deg=_fmt(_float_obj(row["mean_pred_deg"])),
                mean_z_mm=_fmt(_float_obj(row["mean_z_mm"])),
                mean_xy_mm=_fmt(_float_obj(row["mean_xy_mm"])),
            )
        )
    lines.extend(
        [
            "",
            "## Observable Proxy Coverage",
            "",
            "These gates do not use simulator-truth yaw. They only use the predicted yaw, phase, XY, Z, and action fields available at runtime.",
            "",
            "| Gate | Rows | Episodes | Failed ep hit | Success ep hit | Failed rows | Success rows | Mean true | Mean pred | Mean Z mm | Mean XY mm |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in proxy_gates:
        lines.append(
            "| {gate} | {rows} | {episodes} | {failed_episodes_hit} | {success_episodes_hit} | {failed_rows} | {success_rows} | {mean_true_deg} | {mean_pred_deg} | {mean_z_mm} | {mean_xy_mm} |".format(
                gate=row["gate"],
                rows=row["rows"],
                episodes=row["episodes"],
                failed_episodes_hit=row["failed_episodes_hit"],
                success_episodes_hit=row["success_episodes_hit"],
                failed_rows=row["failed_rows"],
                success_rows=row["success_rows"],
                mean_true_deg=_fmt(_float_obj(row["mean_true_deg"])),
                mean_pred_deg=_fmt(_float_obj(row["mean_pred_deg"])),
                mean_z_mm=_fmt(_float_obj(row["mean_z_mm"])),
                mean_xy_mm=_fmt(_float_obj(row["mean_xy_mm"])),
            )
        )
    lines.extend(
        [
            "",
            "## Observable Proxy Episode Summary",
            "",
            "The key deployable proxy below is `freeze_low_z_near_xy_pred_small`: frozen-target descent, predicted yaw below the small threshold, Z <= 35 mm, and XY <= 5 mm.",
            "",
            "| Seed | Ep | Outcome | Proxy rows | Max run | Mean pred | Mean true | Mean raw | First Z mm | First XY mm | Final true |",
            "| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in sorted(
        proxy_episodes,
        key=lambda item: (
            0 if item["outcome"] != "success" else 1,
            str(item["seed"]),
            str(item["episode"]),
        ),
    ):
        gate = "freeze_low_z_near_xy_pred_small"
        lines.append(
            "| {seed} | {episode} | {outcome} | {rows} | {max_run} | {mean_pred} | {mean_true} | {mean_raw} | {first_z} | {first_xy} | {final_true} |".format(
                seed=row["seed"],
                episode=row["episode"],
                outcome=row["outcome"],
                rows=row[f"{gate}_rows"],
                max_run=row[f"{gate}_max_run"],
                mean_pred=_fmt(_float_obj(row[f"{gate}_mean_pred_deg"])),
                mean_true=_fmt(_float_obj(row[f"{gate}_mean_true_deg"])),
                mean_raw=_fmt(_float_obj(row[f"{gate}_mean_raw_norm"])),
                first_z=_fmt(_float_obj(row[f"{gate}_first_z_mm"])),
                first_xy=_fmt(_float_obj(row[f"{gate}_first_xy_mm"])),
                final_true=_fmt(_float_obj(row["final_true_yaw_deg"])),
            )
        )
    lines.extend(
        [
            "",
            "## False-Small Buckets",
            "",
            "### By Outcome",
            "",
        ]
    )
    for key, count in _count_by(events, "outcome").most_common():
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "### By Z Bucket", ""])
    for key, count in _count_by(events, "z_bucket").most_common():
        lines.append(f"- `{key} mm`: `{count}`")
    lines.extend(["", "### By XY Bucket", ""])
    for key, count in _count_by(events, "xy_bucket").most_common():
        lines.append(f"- `{key} mm`: `{count}`")
    lines.extend(["", "### By Reason Bucket", ""])
    for key, count in _count_by(events, "reason_bucket").most_common(12):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(
        [
            "",
            "## Episodes",
            "",
            "| Seed | Ep | Outcome | False-small | Critical | Freeze | Low-Z | Near-XY | Z-gate after | First step | First Z mm | First XY mm | First pred | First true | Final yaw |",
            "| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in sorted(
        episodes,
        key=lambda item: (
            0 if item["outcome"] != "success" else 1,
            str(item["seed"]),
            str(item["episode"]),
        ),
    ):
        lines.append(
            "| {seed} | {episode} | {outcome} | {false_small_rows} | {critical_false_small_rows} | {freeze_false_small_rows} | {low_z_false_small_rows} | {near_xy_false_small_rows} | {z_gate_after_false_small_rows} | {first_step} | {first_z} | {first_xy} | {first_pred} | {first_true} | {final_yaw} |".format(
                seed=row["seed"],
                episode=row["episode"],
                outcome=row["outcome"],
                false_small_rows=row["false_small_rows"],
                critical_false_small_rows=row["critical_false_small_rows"],
                freeze_false_small_rows=row["freeze_false_small_rows"],
                low_z_false_small_rows=row["low_z_false_small_rows"],
                near_xy_false_small_rows=row["near_xy_false_small_rows"],
                z_gate_after_false_small_rows=row["z_gate_after_false_small_rows"],
                first_step=_fmt(_float_obj(row["first_false_small_step"]), 0),
                first_z=_fmt(_float_obj(row["first_false_small_z_mm"])),
                first_xy=_fmt(_float_obj(row["first_false_small_xy_mm"])),
                first_pred=_fmt(_float_obj(row["first_false_small_pred_deg"])),
                first_true=_fmt(_float_obj(row["first_false_small_true_deg"])),
                final_yaw=_fmt(_float_obj(row["final_yaw_deg"])),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    traces = _expand_inputs(args.inputs)
    if not traces:
        raise FileNotFoundError("No step traces matched the provided inputs.")
    episode_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    for trace in traces:
        episodes, events = analyze_trace(trace, args)
        episode_rows.extend(episodes)
        event_rows.extend(events)
    gates = _gate_table(event_rows, episode_rows)
    proxy_gates = _proxy_gate_table(traces, args)
    proxy_episodes = _proxy_episode_table(traces, args)
    output_dir = args.output_dir
    output_csv = args.output_csv or output_dir / "visual_yaw_false_small_episodes.csv"
    output_events_csv = output_dir / "visual_yaw_false_small_events.csv"
    output_gates_csv = output_dir / "visual_yaw_false_small_gates.csv"
    output_proxy_gates_csv = output_dir / "visual_yaw_observable_proxy_gates.csv"
    output_proxy_episodes_csv = output_dir / "visual_yaw_observable_proxy_episodes.csv"
    output_md = args.output_md or output_dir / "visual_yaw_false_small_analysis.md"
    _write_csv(episode_rows, output_csv)
    _write_csv(event_rows, output_events_csv)
    _write_csv(gates, output_gates_csv)
    _write_csv(proxy_gates, output_proxy_gates_csv)
    _write_csv(proxy_episodes, output_proxy_episodes_csv)
    _write_markdown(
        episode_rows,
        event_rows,
        gates,
        proxy_gates,
        proxy_episodes,
        traces,
        output_md,
        args,
    )
    print(f"Wrote {output_csv}")
    print(f"Wrote {output_events_csv}")
    print(f"Wrote {output_gates_csv}")
    print(f"Wrote {output_proxy_gates_csv}")
    print(f"Wrote {output_proxy_episodes_csv}")
    print(f"Wrote {output_md}")


if __name__ == "__main__":
    main()
