"""Analyze visual-yaw reliability during guarded re-acquire traces.

This is an offline diagnostic. It compares runtime visual-yaw predictions with
sim truth that is already present in step traces, so the results must not be
used as deployment labels directly.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


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


def _bool(row: dict[str, str], key: str) -> bool:
    value = str(row.get(key, "")).strip().lower()
    return value in {"1", "1.0", "true", "yes"}


def _wrap_delta_deg(value: float, period_deg: float) -> float:
    if not math.isfinite(value) or not math.isfinite(period_deg) or period_deg <= 0.0:
        return float("nan")
    return (value + 0.5 * period_deg) % period_deg - 0.5 * period_deg


def _profile_period(row: dict[str, str]) -> float:
    profile = row.get("geometry_profile") or row.get("guard_visual_yaw_align_profile") or ""
    return PROFILE_PERIOD_DEG.get(profile, 360.0)


def _sign(value: float, min_abs: float) -> int:
    if not math.isfinite(value) or abs(value) < min_abs:
        return 0
    return 1 if value > 0.0 else -1


@dataclass(frozen=True)
class GateConfig:
    name: str
    require_active: bool = True
    require_reacquire: bool = True
    require_visible: bool = False
    require_temporal_delta: bool = False
    require_temporal_sign: bool = False


GATE_CONFIGS = (
    GateConfig("all_reacquire"),
    GateConfig("visible_reacquire", require_visible=True),
    GateConfig("visible_reacquire_pred_delta_stable", require_visible=True, require_temporal_delta=True),
    GateConfig("visible_reacquire_pred_sign_stable", require_visible=True, require_temporal_sign=True),
    GateConfig(
        "visible_reacquire_pred_delta_and_sign_stable",
        require_visible=True,
        require_temporal_delta=True,
        require_temporal_sign=True,
    ),
)


@dataclass
class EpisodeSummary:
    file: str
    seed: str
    episode: str
    outcome: str
    rows: int = 0
    reacquire_rows: int = 0
    visible_reacquire_rows: int = 0
    sign_mismatch_rows: int = 0
    high_error_rows: int = 0
    max_abs_error_deg: float = float("nan")
    first_reacquire_step: str = ""
    last_step: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--output-csv", type=Path)
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


def _gate_matches(
    gate: GateConfig,
    row: dict[str, str],
    args: argparse.Namespace,
    temporal_delta_stable: bool,
    temporal_sign_stable: bool,
) -> bool:
    if gate.require_active and not _bool(row, "guard_visual_yaw_align_active"):
        return False
    if gate.require_reacquire and not _bool(row, "guard_visual_yaw_align_reacquire_active"):
        return False
    if gate.require_visible and not _visible(row, args):
        return False
    if gate.require_temporal_delta and not temporal_delta_stable:
        return False
    if gate.require_temporal_sign and not temporal_sign_stable:
        return False
    return True


def _empty_gate_stats() -> dict[str, float]:
    return {
        "rows": 0.0,
        "bad_error_rows": 0.0,
        "high_error_rows": 0.0,
        "sign_mismatch_rows": 0.0,
        "abs_error_sum": 0.0,
        "abs_error_max": float("nan"),
        "true_abs_sum": 0.0,
        "pred_abs_sum": 0.0,
    }


def _update_gate_stats(stats: dict[str, float], abs_error: float, true_abs: float, pred_abs: float, sign_mismatch: bool, args: argparse.Namespace) -> None:
    stats["rows"] += 1.0
    stats["abs_error_sum"] += abs_error
    stats["true_abs_sum"] += true_abs
    stats["pred_abs_sum"] += pred_abs
    stats["abs_error_max"] = abs_error if not math.isfinite(stats["abs_error_max"]) else max(stats["abs_error_max"], abs_error)
    if abs_error > args.bad_error_deg:
        stats["bad_error_rows"] += 1.0
    if abs_error > args.high_error_deg:
        stats["high_error_rows"] += 1.0
    if sign_mismatch:
        stats["sign_mismatch_rows"] += 1.0


def analyze_trace(path: Path, args: argparse.Namespace) -> tuple[dict[str, dict[str, float]], dict[tuple[str, str, str], EpisodeSummary]]:
    gate_stats = {gate.name: _empty_gate_stats() for gate in GATE_CONFIGS}
    episodes: dict[tuple[str, str, str], EpisodeSummary] = {}
    pred_history: dict[tuple[str, str, str], deque[float]] = defaultdict(lambda: deque(maxlen=max(1, args.temporal_window)))

    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = (str(path), row.get("seed", ""), row.get("episode", ""))
            summary = episodes.setdefault(
                key,
                EpisodeSummary(
                    file=str(path),
                    seed=row.get("seed", ""),
                    episode=row.get("episode", ""),
                    outcome=row.get("episode_outcome", ""),
                ),
            )
            summary.rows += 1
            summary.outcome = row.get("episode_outcome", summary.outcome)
            summary.last_step = row.get("step", summary.last_step)

            pred_signed = _float(row, "guard_visual_yaw_align_pred_signed_error_deg")
            true_signed = _float(row, "shape_yaw_signed_error_deg")
            if not (math.isfinite(pred_signed) and math.isfinite(true_signed)):
                continue

            period_deg = _profile_period(row)
            history = pred_history[key]
            history.append(pred_signed)
            temporal_delta_stable = _stable_delta(history, args, period_deg)
            temporal_sign_stable = _stable_sign(history, args)

            abs_error = abs(_wrap_delta_deg(pred_signed - true_signed, period_deg))
            if not math.isfinite(abs_error):
                continue
            true_abs = abs(_wrap_delta_deg(true_signed, period_deg))
            pred_abs = abs(_wrap_delta_deg(pred_signed, period_deg))
            pred_sign = _sign(pred_signed, args.sign_min_abs_deg)
            true_sign = _sign(true_signed, args.sign_min_abs_deg)
            sign_mismatch = pred_sign != 0 and true_sign != 0 and pred_sign != true_sign

            if _bool(row, "guard_visual_yaw_align_reacquire_active"):
                summary.reacquire_rows += 1
                if not summary.first_reacquire_step:
                    summary.first_reacquire_step = row.get("step", "")
                summary.max_abs_error_deg = (
                    abs_error
                    if not math.isfinite(summary.max_abs_error_deg)
                    else max(summary.max_abs_error_deg, abs_error)
                )
                if _visible(row, args):
                    summary.visible_reacquire_rows += 1
                if abs_error > args.high_error_deg:
                    summary.high_error_rows += 1
                if sign_mismatch:
                    summary.sign_mismatch_rows += 1

            for gate in GATE_CONFIGS:
                if _gate_matches(gate, row, args, temporal_delta_stable, temporal_sign_stable):
                    _update_gate_stats(gate_stats[gate.name], abs_error, true_abs, pred_abs, sign_mismatch, args)

    return gate_stats, episodes


def _merge_gate_stats(stats_list: Iterable[dict[str, dict[str, float]]]) -> dict[str, dict[str, float]]:
    merged = {gate.name: _empty_gate_stats() for gate in GATE_CONFIGS}
    for stats_by_gate in stats_list:
        for name, stats in stats_by_gate.items():
            target = merged[name]
            for key, value in stats.items():
                if key == "abs_error_max":
                    if math.isfinite(value):
                        target[key] = value if not math.isfinite(target[key]) else max(target[key], value)
                else:
                    target[key] += value
    return merged


def _format_float(value: float, digits: int = 3) -> str:
    if not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _gate_rows(gate_stats: dict[str, dict[str, float]], total_reacquire_rows: float) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for gate in GATE_CONFIGS:
        stats = gate_stats[gate.name]
        count = stats["rows"]
        rows.append(
            {
                "gate": gate.name,
                "rows": int(count),
                "coverage": count / total_reacquire_rows if total_reacquire_rows > 0.0 else float("nan"),
                "mean_abs_error_deg": stats["abs_error_sum"] / count if count > 0.0 else float("nan"),
                "max_abs_error_deg": stats["abs_error_max"],
                "bad_error_rate": stats["bad_error_rows"] / count if count > 0.0 else float("nan"),
                "high_error_rate": stats["high_error_rows"] / count if count > 0.0 else float("nan"),
                "sign_mismatch_rate": stats["sign_mismatch_rows"] / count if count > 0.0 else float("nan"),
                "mean_true_abs_deg": stats["true_abs_sum"] / count if count > 0.0 else float("nan"),
                "mean_pred_abs_deg": stats["pred_abs_sum"] / count if count > 0.0 else float("nan"),
            }
        )
    return rows


def _worst_episode_rows(episodes: Iterable[EpisodeSummary], limit: int) -> list[EpisodeSummary]:
    candidates = [episode for episode in episodes if episode.reacquire_rows > 0]
    candidates.sort(
        key=lambda episode: (
            episode.outcome == "success",
            -episode.sign_mismatch_rows,
            -episode.high_error_rows,
            -episode.reacquire_rows,
            -episode.max_abs_error_deg if math.isfinite(episode.max_abs_error_deg) else 0.0,
        )
    )
    return candidates[: max(0, limit)]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["gate"])
        writer.writeheader()
        writer.writerows(rows)


def _write_md(
    path: Path,
    args: argparse.Namespace,
    gate_rows: list[dict[str, object]],
    episodes: list[EpisodeSummary],
    total_reacquire_rows: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Visual Yaw Re-acquire Trace Analysis",
        "",
        "Offline diagnostic only: this compares visual-yaw predictions with sim truth already recorded in traces.",
        "",
        f"- Traces: `{len(args.traces)}`",
        f"- Re-acquire rows: `{int(total_reacquire_rows)}`",
        f"- Visibility gate: raw_norm >= `{args.raw_norm_min}`, cam_std >= `{args.cam_std_min}`, crop_std >= `{args.crop_std_min}`",
        f"- Temporal gate: last `{args.temporal_window}` predictions, max adjacent delta <= `{args.temporal_delta_deg} deg`",
        f"- Sign mismatch ignores predictions/truth below `{args.sign_min_abs_deg} deg`",
        "",
        "## Gate Summary",
        "",
        "| gate | rows | coverage | mean abs err deg | max abs err deg | >bad err | >high err | sign mismatch | mean true abs | mean pred abs |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in gate_rows:
        lines.append(
            "| {gate} | {rows} | {coverage} | {mean_abs_error_deg} | {max_abs_error_deg} | {bad_error_rate} | {high_error_rate} | {sign_mismatch_rate} | {mean_true_abs_deg} | {mean_pred_abs_deg} |".format(
                gate=row["gate"],
                rows=row["rows"],
                coverage=_format_float(float(row["coverage"])),
                mean_abs_error_deg=_format_float(float(row["mean_abs_error_deg"])),
                max_abs_error_deg=_format_float(float(row["max_abs_error_deg"])),
                bad_error_rate=_format_float(float(row["bad_error_rate"])),
                high_error_rate=_format_float(float(row["high_error_rate"])),
                sign_mismatch_rate=_format_float(float(row["sign_mismatch_rate"])),
                mean_true_abs_deg=_format_float(float(row["mean_true_abs_deg"])),
                mean_pred_abs_deg=_format_float(float(row["mean_pred_abs_deg"])),
            )
        )

    lines.extend(
        [
            "",
            "## Worst Re-acquire Episodes",
            "",
            "| file | seed | episode | outcome | reacquire rows | visible rows | sign mismatch | high error | max abs err deg | first step | last step |",
            "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for episode in episodes:
        lines.append(
            "| {file} | {seed} | {episode} | {outcome} | {reacquire_rows} | {visible_rows} | {sign_mismatch_rows} | {high_error_rows} | {max_abs} | {first_step} | {last_step} |".format(
                file=Path(episode.file).name,
                seed=episode.seed,
                episode=episode.episode,
                outcome=episode.outcome,
                reacquire_rows=episode.reacquire_rows,
                visible_rows=episode.visible_reacquire_rows,
                sign_mismatch_rows=episode.sign_mismatch_rows,
                high_error_rows=episode.high_error_rows,
                max_abs=_format_float(episode.max_abs_error_deg),
                first_step=episode.first_reacquire_step,
                last_step=episode.last_step,
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    stats_list = []
    all_episodes: dict[tuple[str, str, str], EpisodeSummary] = {}
    for path in args.traces:
        stats, episodes = analyze_trace(path, args)
        stats_list.append(stats)
        all_episodes.update(episodes)

    merged = _merge_gate_stats(stats_list)
    total_reacquire_rows = merged["all_reacquire"]["rows"]
    gate_rows = _gate_rows(merged, total_reacquire_rows)
    worst = _worst_episode_rows(all_episodes.values(), args.worst_episodes)

    if args.output_csv:
        _write_csv(args.output_csv, gate_rows)
    if args.output_md:
        _write_md(args.output_md, args, gate_rows, worst, total_reacquire_rows)

    writer = csv.DictWriter(sys.stdout, fieldnames=list(gate_rows[0].keys()))
    writer.writeheader()
    writer.writerows(gate_rows)


if __name__ == "__main__":
    main()
