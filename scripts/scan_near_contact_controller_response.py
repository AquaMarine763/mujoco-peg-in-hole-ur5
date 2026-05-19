from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from diagnose_near_contact_tracking import make_env, run_probe


@dataclass(frozen=True)
class ControllerCandidate:
    ik_control_mode: str
    ik_orientation_weight: float
    ik_max_iterations: int
    ik_step_limit: float
    frame_skip: int
    actuator_kp_multiplier: float
    joint_damping_multiplier: float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scan low-Z UR5e controller response candidates by reusing the "
            "near-contact recenter diagnostic."
        )
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=Path("assets/ur5e_full/ur5e_peg_in_hole_full.xml"),
    )
    parser.add_argument(
        "--ik-control-modes",
        nargs="+",
        choices=["position", "pose"],
        default=["pose"],
    )
    parser.add_argument("--ik-orientation-weights", nargs="+", type=float, default=(0.01, 0.02, 0.03))
    parser.add_argument("--ik-posture-weight", type=float, default=0.01)
    parser.add_argument("--ik-step-limits", nargs="+", type=float, default=(0.06,))
    parser.add_argument("--ik-max-iterations-list", nargs="+", type=int, default=(64, 96))
    parser.add_argument("--frame-skips", nargs="+", type=int, default=(10,))
    parser.add_argument("--actuator-kp-multipliers", nargs="+", type=float, default=(2.0, 3.0))
    parser.add_argument("--joint-damping-multipliers", nargs="+", type=float, default=(1.0,))
    parser.add_argument("--target-pos", nargs=3, type=float, default=(0.55, 0.05, 0.65))
    parser.add_argument("--xy-offsets-mm", nargs="+", type=float, default=(6.0, 10.0, 20.0))
    parser.add_argument("--z-above-mm", nargs="+", type=float, default=(8.0, 15.0, 30.0))
    parser.add_argument("--angles-deg", nargs="+", type=float, default=(0.0, 90.0, 180.0, 270.0))
    parser.add_argument("--recenter-steps", type=int, default=12)
    parser.add_argument("--max-xy-action", type=float, default=0.005)
    parser.add_argument("--z-action", type=float, default=0.0)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--settle-steps", type=int, default=40)
    parser.add_argument("--setup-tolerance", type=float, default=0.003)
    parser.add_argument("--seed", type=int, default=743_000)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/ur5e_full/controller_diagnostics/near_contact_controller_response_scan.csv"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("results/ur5e_full/controller_diagnostics/near_contact_controller_response_scan.md"),
    )
    return parser


def finite_mean(values: Iterable[float]) -> float:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=np.float64)
    return float(np.mean(finite)) if finite.size else float("nan")


def finite_max(values: Iterable[float]) -> float:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=np.float64)
    return float(np.max(finite)) if finite.size else float("nan")


def summarize_group(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)

    summaries: list[dict[str, Any]] = []
    for group_key, group_rows in groups.items():
        summary = {key: value for key, value in zip(keys, group_key)}
        collision_rate = float(np.mean([bool(row["collision"]) for row in group_rows]))
        setup_ok_rate = float(np.mean([bool(row["setup_ok"]) for row in group_rows]))
        setup_collision_rate = float(np.mean([bool(row["setup_collision"]) for row in group_rows]))
        max_tilt_deg = finite_max(float(row["max_tilt_deg"]) for row in group_rows)
        reduction_per_command = finite_mean(float(row["xy_reduction_per_command"]) for row in group_rows)
        mean_step_gain = finite_mean(float(row["mean_step_xy_gain"]) for row in group_rows)
        tilt_penalty = max(0.0, max_tilt_deg - 12.0) * 0.02 if np.isfinite(max_tilt_deg) else 0.0
        score = reduction_per_command + mean_step_gain - collision_rate * 0.5 - tilt_penalty
        summary.update(
            {
                "probes": len(group_rows),
                "setup_ok_rate": setup_ok_rate,
                "setup_collision_rate": setup_collision_rate,
                "collision_rate": collision_rate,
                "success_rate": float(np.mean([bool(row["final_success"]) for row in group_rows])),
                "mean_xy_reduction_mm": finite_mean(float(row["xy_reduction_mm"]) for row in group_rows),
                "mean_xy_reduction_per_command": reduction_per_command,
                "mean_total_xy_alignment": finite_mean(float(row["total_xy_alignment"]) for row in group_rows),
                "mean_step_xy_gain": mean_step_gain,
                "mean_z_drift_mm": finite_mean(float(row["z_drift_mm"]) for row in group_rows),
                "max_tilt_deg": max_tilt_deg,
                "mean_tracking_error_mm": finite_mean(
                    float(row["mean_tracking_error_mm"]) for row in group_rows
                ),
                "mean_ik_target_error_mm": finite_mean(
                    float(row["mean_ik_target_error_mm"]) for row in group_rows
                ),
                "score": score,
            }
        )
        summaries.append(summary)
    return summaries


def iter_candidates(args: argparse.Namespace) -> Iterable[ControllerCandidate]:
    for ik_control_mode in args.ik_control_modes:
        for orientation_weight in args.ik_orientation_weights:
            for max_iterations in args.ik_max_iterations_list:
                for ik_step_limit in args.ik_step_limits:
                    for frame_skip in args.frame_skips:
                        for actuator_kp in args.actuator_kp_multipliers:
                            for joint_damping in args.joint_damping_multipliers:
                                yield ControllerCandidate(
                                    ik_control_mode=ik_control_mode,
                                    ik_orientation_weight=float(orientation_weight),
                                    ik_max_iterations=int(max_iterations),
                                    ik_step_limit=float(ik_step_limit),
                                    frame_skip=int(frame_skip),
                                    actuator_kp_multiplier=float(actuator_kp),
                                    joint_damping_multiplier=float(joint_damping),
                                )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    candidate_keys = (
        "ik_control_mode",
        "ik_orientation_weight",
        "ik_max_iterations",
        "ik_step_limit",
        "frame_skip",
        "actuator_kp_multiplier",
        "joint_damping_multiplier",
    )
    by_candidate = summarize_group(rows, candidate_keys)
    by_candidate.sort(
        key=lambda row: (
            -float(row["score"]),
            float(row["collision_rate"]),
            -float(row["mean_xy_reduction_per_command"]),
        )
    )
    best_keys = candidate_keys
    top_candidate = {key: by_candidate[0][key] for key in best_keys} if by_candidate else {}
    top_rows = [
        row
        for row in rows
        if all(row[key] == value for key, value in top_candidate.items())
    ]
    top_by_z = summarize_group(top_rows, ("z_above_mm",))
    top_by_offset = summarize_group(top_rows, ("xy_offset_mm",))

    lines = [
        "# Near-Contact Controller Response Scan",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model path: `{args.model_path}`",
        f"- Seed: `{args.seed}`",
        f"- Probe grid: XY offsets `{list(args.xy_offsets_mm)}` mm, Z `{list(args.z_above_mm)}` mm, angles `{list(args.angles_deg)}` deg",
        f"- Recenter steps / max XY action / Z action: `{args.recenter_steps}` / `{args.max_xy_action}` / `{args.z_action}`",
        "",
        "## Ranked Candidates",
        "",
        "| rank | mode | w_ori | iters | step limit | frame skip | Kp | damping | probes | setup ok | setup coll | coll | xy reduction mm | reduction/cmd | step gain | alignment | z drift mm | max tilt | track err mm | ik err mm | score |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, row in enumerate(by_candidate, start=1):
        lines.append(
            "| {rank} | {ik_control_mode} | {ik_orientation_weight:.4f} | {ik_max_iterations} | "
            "{ik_step_limit:.3f} | {frame_skip} | {actuator_kp_multiplier:.2f} | "
            "{joint_damping_multiplier:.2f} | {probes} | {setup_ok_rate:.3f} | "
            "{setup_collision_rate:.3f} | {collision_rate:.3f} | {mean_xy_reduction_mm:.3f} | "
            "{mean_xy_reduction_per_command:.3f} | {mean_step_xy_gain:.3f} | "
            "{mean_total_xy_alignment:.3f} | {mean_z_drift_mm:.3f} | {max_tilt_deg:.3f} | "
            "{mean_tracking_error_mm:.3f} | {mean_ik_target_error_mm:.3f} | {score:.3f} |".format(
                rank=rank,
                **row,
            )
        )

    if top_candidate:
        lines.extend(
            [
                "",
                "## Top Candidate Breakdown",
                "",
                f"- Candidate: `{top_candidate}`",
                "",
                "### By Z Height",
                "",
                "| z mm | probes | coll | xy reduction mm | reduction/cmd | step gain | z drift mm | max tilt |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in sorted(top_by_z, key=lambda item: float(item["z_above_mm"])):
            lines.append(
                "| {z_above_mm:.1f} | {probes} | {collision_rate:.3f} | "
                "{mean_xy_reduction_mm:.3f} | {mean_xy_reduction_per_command:.3f} | "
                "{mean_step_xy_gain:.3f} | {mean_z_drift_mm:.3f} | {max_tilt_deg:.3f} |".format(**row)
            )
        lines.extend(
            [
                "",
                "### By XY Offset",
                "",
                "| offset mm | probes | coll | xy reduction mm | reduction/cmd | step gain | z drift mm | max tilt |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in sorted(top_by_offset, key=lambda item: float(item["xy_offset_mm"])):
            lines.append(
                "| {xy_offset_mm:.1f} | {probes} | {collision_rate:.3f} | "
                "{mean_xy_reduction_mm:.3f} | {mean_xy_reduction_per_command:.3f} | "
                "{mean_step_xy_gain:.3f} | {mean_z_drift_mm:.3f} | {max_tilt_deg:.3f} |".format(**row)
            )

    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    if args.recenter_steps <= 0:
        raise ValueError("--recenter-steps must be positive.")
    if args.max_xy_action <= 0.0:
        raise ValueError("--max-xy-action must be positive.")

    rows: list[dict[str, Any]] = []
    probe_id = 0
    candidates = list(iter_candidates(args))
    for candidate_id, candidate in enumerate(candidates, start=1):
        probe_args = argparse.Namespace(**vars(args))
        probe_args.ik_orientation_weight = candidate.ik_orientation_weight
        probe_args.ik_max_iterations = candidate.ik_max_iterations
        probe_args.ik_step_limit = candidate.ik_step_limit
        probe_args.frame_skip = candidate.frame_skip
        print(
            "candidate {}/{}: mode={} w_ori={} iters={} step_limit={} frame_skip={} kp={} damping={}".format(
                candidate_id,
                len(candidates),
                candidate.ik_control_mode,
                candidate.ik_orientation_weight,
                candidate.ik_max_iterations,
                candidate.ik_step_limit,
                candidate.frame_skip,
                candidate.actuator_kp_multiplier,
                candidate.joint_damping_multiplier,
            )
        )
        env = make_env(probe_args, candidate.ik_control_mode)
        try:
            for z_mm in args.z_above_mm:
                for offset_mm in args.xy_offsets_mm:
                    for angle_deg in args.angles_deg:
                        row = run_probe(
                            env,
                            probe_args,
                            ik_control_mode=candidate.ik_control_mode,
                            actuator_kp_multiplier=candidate.actuator_kp_multiplier,
                            joint_damping_multiplier=candidate.joint_damping_multiplier,
                            xy_offset_m=float(offset_mm) / 1000.0,
                            z_above_m=float(z_mm) / 1000.0,
                            angle_deg=float(angle_deg),
                            probe_id=probe_id,
                        )
                        row.update(
                            {
                                "candidate_id": candidate_id,
                                "ik_orientation_weight": candidate.ik_orientation_weight,
                                "ik_posture_weight": float(args.ik_posture_weight),
                                "ik_step_limit": candidate.ik_step_limit,
                                "ik_max_iterations": candidate.ik_max_iterations,
                                "frame_skip": candidate.frame_skip,
                            }
                        )
                        rows.append(row)
                        probe_id += 1
        finally:
            env.close()

    write_csv(args.output_csv, rows)
    write_summary(args.output_md, rows, args)
    ranked = summarize_group(
        rows,
        (
            "ik_control_mode",
            "ik_orientation_weight",
            "ik_max_iterations",
            "ik_step_limit",
            "frame_skip",
            "actuator_kp_multiplier",
            "joint_damping_multiplier",
        ),
    )
    ranked.sort(key=lambda row: -float(row["score"]))
    best = ranked[0]
    print(
        "best: mode={ik_control_mode} w_ori={ik_orientation_weight:.4f} iters={ik_max_iterations} "
        "frame_skip={frame_skip} kp={actuator_kp_multiplier:.2f} damping={joint_damping_multiplier:.2f} "
        "coll={collision_rate:.3f} reduction/cmd={mean_xy_reduction_per_command:.3f} "
        "step_gain={mean_step_xy_gain:.3f} tilt={max_tilt_deg:.2f} score={score:.3f}".format(**best)
    )
    print(f"Wrote {args.output_csv}")
    print(f"Wrote {args.output_md}")


if __name__ == "__main__":
    main()
