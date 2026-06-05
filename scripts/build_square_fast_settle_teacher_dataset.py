from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from peg_in_hole_mujoco.sim_config import parse_args_with_config

from build_final_insert_stuck_dataset import (
    CSV_FIELDNAMES,
    FEATURE_NAMES,
    compute_window_progress,
    feature_values,
    finite_mean,
    limit_xy,
    selected_row,
    to_float,
    to_int,
    wall_relief_vector,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a square_fast_settle teacher dataset from failed guarded step "
            "traces. The labels are conservative local corrections for the "
            "final-insert adapter schema."
        )
    )
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-npz", type=Path, default=None)
    parser.add_argument("--geometry-name", default="square_square")
    parser.add_argument("--phase", default="square_fast_settle")
    parser.add_argument(
        "--outcome",
        nargs="*",
        default=["timeout"],
        help="Episode outcomes to keep. Use 'any' to disable outcome filtering.",
    )
    parser.add_argument("--max-xy-m", type=float, default=0.008)
    parser.add_argument("--min-z-m", type=float, default=0.020)
    parser.add_argument("--max-z-m", type=float, default=0.055)
    parser.add_argument("--min-stall-steps", type=int, default=8)
    parser.add_argument("--progress-window-steps", type=int, default=20)
    parser.add_argument("--stall-min-z-progress-m", type=float, default=0.0005)
    parser.add_argument("--stall-min-xy-progress-m", type=float, default=0.0002)
    parser.add_argument("--yaw-error-deg", type=float, default=4.0)
    parser.add_argument("--bad-tilted-margin-m", type=float, default=-0.001)
    parser.add_argument("--soft-topdown-margin-m", type=float, default=0.0005)
    parser.add_argument("--sample-stride", type=int, default=3)
    parser.add_argument("--max-samples-per-episode", type=int, default=256)
    parser.add_argument("--label-release-xy-m", type=float, default=0.0048)
    parser.add_argument("--label-max-xy-action-m", type=float, default=0.0015)
    parser.add_argument("--label-contact-max-xy-action-m", type=float, default=0.0010)
    parser.add_argument("--label-max-down-action-m", type=float, default=0.0006)
    parser.add_argument("--label-lift-action-m", type=float, default=0.0025)
    parser.add_argument("--label-wall-bias-m", type=float, default=0.0010)
    parser.add_argument(
        "--include-safe-descend",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep safe square_fast_settle rows and label them as guarded_descend.",
    )
    parser.add_argument(
        "--success-descend-override",
        action="store_true",
        help=(
            "In successful traces, force near-aligned rows to guarded_descend "
            "even if square yaw/margin diagnostics are conservative."
        ),
    )
    parser.add_argument("--success-descend-max-xy-m", type=float, default=0.005)
    parser.add_argument("--success-descend-min-z-m", type=float, default=0.005)
    parser.add_argument("--success-descend-max-z-m", type=float, default=0.055)
    return parse_args_with_config(parser)


def load_trace(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as file:
        rows = list(csv.DictReader(file))
    for row in rows:
        row["source_trace"] = str(path)
    return rows


def episode_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (row.get("source_trace", ""), row.get("seed", ""), row.get("episode", ""))


def group_by_episode(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[episode_key(row)].append(row)
    return dict(grouped)


def keep_outcome(row: dict[str, str], outcomes: set[str]) -> bool:
    return "any" in outcomes or row.get("episode_outcome", "") in outcomes


def row_vector(row: dict[str, str], prefix: str) -> np.ndarray:
    return np.asarray(
        [
            to_float(row, f"{prefix}_x"),
            to_float(row, f"{prefix}_y"),
            to_float(row, f"{prefix}_z"),
        ],
        dtype=np.float64,
    )


def classify_square_settle_state(
    row: dict[str, str],
    *,
    z_progress: float,
    xy_progress: float,
    args: argparse.Namespace,
) -> str | None:
    wall_count = to_int(row, "peg_hole_contact_wall_count")
    plate_count = to_int(row, "peg_hole_contact_plate_count")
    yaw_error = to_float(row, "square_peg_yaw_error_deg")
    tilted_margin = to_float(row, "square_peg_tilted_clearance_margin")
    topdown_margin = to_float(row, "square_peg_topdown_clearance_margin")
    stall_steps = to_int(row, "guard_final_servo_stall_steps")

    bad_yaw = math.isfinite(yaw_error) and yaw_error >= args.yaw_error_deg
    bad_tilted_margin = (
        math.isfinite(tilted_margin)
        and tilted_margin <= args.bad_tilted_margin_m
    )
    bad_topdown_margin = (
        math.isfinite(topdown_margin)
        and topdown_margin <= args.soft_topdown_margin_m
    )
    z_stalled = (
        math.isfinite(z_progress)
        and z_progress <= args.stall_min_z_progress_m
    )
    xy_stalled = (
        math.isfinite(xy_progress)
        and abs(xy_progress) <= args.stall_min_xy_progress_m
    )
    stalled = stall_steps >= args.min_stall_steps or (z_stalled and xy_stalled)

    reasons: list[str] = []
    if wall_count > 0:
        reasons.append("wall_contact")
    if plate_count > 0:
        reasons.append("plate_contact")
    if bad_yaw:
        reasons.append("bad_yaw")
    if bad_tilted_margin:
        reasons.append("negative_tilted_margin")
    if bad_topdown_margin:
        reasons.append("tight_topdown_margin")
    if stalled:
        reasons.append("progress_stall")
    if not reasons:
        return None
    return "+".join(reasons)


def label_square_action(
    row: dict[str, str],
    *,
    args: argparse.Namespace,
) -> tuple[str, np.ndarray]:
    tip = row_vector(row, "post_peg_tip")
    target = row_vector(row, "post_target")
    rel = target - tip
    dist_xy = float(np.linalg.norm(rel[:2]))

    wall_count = to_int(row, "peg_hole_contact_wall_count")
    plate_count = to_int(row, "peg_hole_contact_plate_count")
    yaw_error = to_float(row, "square_peg_yaw_error_deg")
    tilted_margin = to_float(row, "square_peg_tilted_clearance_margin")
    topdown_margin = to_float(row, "square_peg_topdown_clearance_margin")

    bad_yaw = math.isfinite(yaw_error) and yaw_error >= args.yaw_error_deg
    bad_tilted_margin = (
        math.isfinite(tilted_margin)
        and tilted_margin <= args.bad_tilted_margin_m
    )
    tight_topdown_margin = (
        math.isfinite(topdown_margin)
        and topdown_margin <= args.soft_topdown_margin_m
    )
    xy = rel[:2] + wall_relief_vector(row, args.label_wall_bias_m)

    if wall_count > 0 or plate_count > 0 or bad_tilted_margin:
        action = np.asarray([xy[0], xy[1], args.label_lift_action_m], dtype=np.float64)
        action = limit_xy(action, args.label_contact_max_xy_action_m)
        return "clearance_lift", action
    if bad_yaw or tight_topdown_margin or dist_xy > args.label_release_xy_m:
        action = np.asarray([xy[0], xy[1], 0.0], dtype=np.float64)
        action = limit_xy(action, args.label_max_xy_action_m)
        return "hold_recenter", action

    action = np.asarray(
        [rel[0], rel[1], -args.label_max_down_action_m],
        dtype=np.float64,
    )
    action = limit_xy(action, args.label_max_xy_action_m)
    return "guarded_descend", action


def success_descend_action(
    row: dict[str, str],
    *,
    args: argparse.Namespace,
) -> np.ndarray:
    tip = row_vector(row, "post_peg_tip")
    target = row_vector(row, "post_target")
    rel = target - tip
    action = np.asarray(
        [rel[0], rel[1], -args.label_max_down_action_m],
        dtype=np.float64,
    )
    return limit_xy(action, args.label_max_xy_action_m)


def should_force_success_descend(
    row: dict[str, str],
    *,
    args: argparse.Namespace,
) -> bool:
    if not args.success_descend_override:
        return False
    if row.get("episode_outcome", "") != "success":
        return False
    post_xy = to_float(row, "post_dist_xy")
    post_z = to_float(row, "post_z_above_target")
    return (
        post_xy <= args.success_descend_max_xy_m
        and args.success_descend_min_z_m
        <= post_z
        <= args.success_descend_max_z_m
    )


def row_is_in_gate(row: dict[str, str], args: argparse.Namespace, outcomes: set[str]) -> bool:
    if args.geometry_name != "any" and row.get("geometry_name", "") != args.geometry_name:
        return False
    if args.phase != "any" and row.get("guard_final_servo_phase", "") != args.phase:
        return False
    if not keep_outcome(row, outcomes):
        return False
    if row.get("guard_final_servo_active", "").lower() != "true":
        return False
    post_xy = to_float(row, "post_dist_xy")
    post_z = to_float(row, "post_z_above_target")
    return post_xy <= args.max_xy_m and args.min_z_m <= post_z <= args.max_z_m


def extract_rows(args: argparse.Namespace) -> list[dict[str, object]]:
    outcomes = {str(value).strip() for value in args.outcome}
    selected: list[dict[str, object]] = []
    for path in args.input:
        rows = load_trace(path)
        for episode_rows in group_by_episode(rows).values():
            episode_selected: list[dict[str, object]] = []
            for index, row in enumerate(episode_rows):
                if args.sample_stride > 1 and index % args.sample_stride != 0:
                    continue
                if not row_is_in_gate(row, args, outcomes):
                    continue
                z_progress, xy_progress = compute_window_progress(
                    episode_rows,
                    index,
                    args.progress_window_steps,
                )
                state_reason = classify_square_settle_state(
                    row,
                    z_progress=z_progress,
                    xy_progress=xy_progress,
                    args=args,
                )
                force_success_descend = should_force_success_descend(row, args=args)
                if force_success_descend:
                    state_reason = "success_descend_override"
                    label_phase = "guarded_descend"
                    label = success_descend_action(row, args=args)
                elif state_reason is None:
                    if not args.include_safe_descend:
                        continue
                    state_reason = "safe_descend"
                    label_phase, label = label_square_action(row, args=args)
                    if label_phase != "guarded_descend":
                        continue
                else:
                    label_phase, label = label_square_action(row, args=args)
                features = feature_values(
                    row,
                    z_progress=z_progress,
                    xy_progress=xy_progress,
                )
                episode_selected.append(
                    selected_row(
                        row,
                        source_trace=path,
                        stuck_reason=state_reason,
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


def mean_for(rows: list[dict[str, object]], key: str) -> float:
    return finite_mean(float(row[key]) for row in rows)


def write_markdown(path: Path, rows: list[dict[str, object]], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    label_counts = Counter(str(row["label_phase"]) for row in rows)
    reason_counts = Counter(str(row["stuck_reason"]) for row in rows)
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
        "# Square Fast Settle Teacher Dataset",
        "",
        "## Filters",
        "",
        f"- geometry/phase: `{args.geometry_name}` / `{args.phase}`",
        f"- outcome: `{', '.join(args.outcome)}`",
        f"- XY/Z window: `xy <= {args.max_xy_m:.4f} m`, "
        f"`{args.min_z_m:.4f} <= z <= {args.max_z_m:.4f} m`",
        f"- stall gate: `{args.min_stall_steps}` steps, window `{args.progress_window_steps}`",
        f"- yaw/bad tilted margin: `{args.yaw_error_deg:.1f} deg`, "
        f"`{args.bad_tilted_margin_m:.4f} m`",
        f"- success descend override: `{args.success_descend_override}` "
        f"`xy <= {args.success_descend_max_xy_m:.4f} m`, "
        f"`{args.success_descend_min_z_m:.4f} <= z <= "
        f"{args.success_descend_max_z_m:.4f} m`",
        "",
        "## Summary",
        "",
        f"- selected samples: `{len(rows)}`",
        f"- trace episodes: `{len(episode_counts)}`",
        f"- mean XY/Z: `{mean_for(rows, 'post_dist_xy') * 1000.0:.2f} mm` / "
        f"`{mean_for(rows, 'post_z_above_target') * 1000.0:.2f} mm`",
        f"- mean yaw error: `{mean_for(rows, 'square_peg_yaw_error_deg'):.2f} deg`",
        f"- mean tilted margin: "
        f"`{mean_for(rows, 'square_peg_tilted_clearance_margin') * 1000.0:.2f} mm`",
        "",
        "## Label Counts",
        "",
    ]
    for key, count in sorted(label_counts.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "## State Reason Counts", ""])
    for key, count in sorted(reason_counts.items()):
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
    if args.progress_window_steps <= 0:
        raise ValueError("--progress-window-steps must be positive.")
    if args.max_z_m <= args.min_z_m:
        raise ValueError("--max-z-m must exceed --min-z-m.")
    if args.success_descend_max_z_m <= args.success_descend_min_z_m:
        raise ValueError("--success-descend-max-z-m must exceed min Z.")
    rows = extract_rows(args)
    if not rows:
        raise RuntimeError("No rows selected. Relax filters or check inputs.")
    write_csv(args.output_csv, rows)
    if args.output_npz is not None:
        write_npz(args.output_npz, rows)
    if args.output_md is not None:
        write_markdown(args.output_md, rows, args)
    print(f"selected {len(rows)} square-fast-settle teacher states")
    print(f"wrote {args.output_csv}")
    if args.output_npz is not None:
        print(f"wrote {args.output_npz}")
    if args.output_md is not None:
        print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
