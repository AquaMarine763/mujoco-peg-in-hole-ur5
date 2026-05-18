from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import mujoco
import numpy as np

from peg_in_hole_mujoco import PegInHoleMujocoEnv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Probe UR5e peg-tip recenter authority from low-Z, off-center states "
            "near the fixture."
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
        default=["position", "pose"],
    )
    parser.add_argument("--target-pos", nargs=3, type=float, default=(0.55, 0.05, 0.65))
    parser.add_argument("--xy-offsets-mm", nargs="+", type=float, default=(6.0, 10.0, 20.0, 30.0))
    parser.add_argument("--z-above-mm", nargs="+", type=float, default=(8.0, 15.0, 30.0, 50.0))
    parser.add_argument("--angles-deg", nargs="+", type=float, default=(0.0, 90.0, 180.0, 270.0))
    parser.add_argument("--recenter-steps", type=int, default=12)
    parser.add_argument("--max-xy-action", type=float, default=0.005)
    parser.add_argument("--z-action", type=float, default=0.0)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--frame-skip", type=int, default=10)
    parser.add_argument("--settle-steps", type=int, default=40)
    parser.add_argument("--setup-tolerance", type=float, default=0.003)
    parser.add_argument("--ik-orientation-weight", type=float, default=0.12)
    parser.add_argument("--ik-posture-weight", type=float, default=0.01)
    parser.add_argument("--ik-step-limit", type=float, default=0.06)
    parser.add_argument("--ik-max-iterations", type=int, default=24)
    parser.add_argument("--actuator-kp-multipliers", nargs="+", type=float, default=(1.0,))
    parser.add_argument("--joint-damping-multipliers", nargs="+", type=float, default=(1.0,))
    parser.add_argument("--seed", type=int, default=742_000)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/ur5e_full/controller_diagnostics/near_contact_recenter_rows.csv"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("results/ur5e_full/controller_diagnostics/near_contact_recenter_summary.md"),
    )
    return parser


def make_env(args: argparse.Namespace, ik_control_mode: str) -> PegInHoleMujocoEnv:
    target_pos = tuple(float(value) for value in args.target_pos)
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode="state",
        max_steps=max(200, args.recenter_steps + 20),
        frame_skip=args.frame_skip,
        action_scale=args.action_scale,
        target_low=target_pos,
        target_high=target_pos,
        success_xy_tolerance=0.005,
        success_z_tolerance=0.010,
        approach_xy_tolerance=0.02,
        approach_height=0.12,
        initialization_mode="fixed",
        ik_control_mode=ik_control_mode,
        ik_orientation_weight=args.ik_orientation_weight,
        ik_posture_weight=args.ik_posture_weight,
        ik_step_limit=args.ik_step_limit,
        ik_max_iterations=args.ik_max_iterations,
    )


def apply_dynamics_multipliers(
    env: PegInHoleMujocoEnv,
    *,
    actuator_kp_multiplier: float,
    joint_damping_multiplier: float,
) -> None:
    env.model.dof_damping[env.arm_dof_ids] = (
        env.base_dof_damping[env.arm_dof_ids] * float(joint_damping_multiplier)
    )
    env.model.actuator_gainprm[env.arm_actuator_ids, 0] = (
        env.base_actuator_gainprm[env.arm_actuator_ids, 0] * float(actuator_kp_multiplier)
    )
    env.model.actuator_biasprm[env.arm_actuator_ids, 1] = (
        env.base_actuator_biasprm[env.arm_actuator_ids, 1] * float(actuator_kp_multiplier)
    )
    env.current_joint_damping_multiplier = float(joint_damping_multiplier)
    env.current_actuator_kp_multiplier = float(actuator_kp_multiplier)


def reset_action_tracking(env: PegInHoleMujocoEnv) -> None:
    env.previous_filtered_action = np.zeros(3, dtype=np.float64)
    env.last_commanded_action = np.zeros(3, dtype=np.float64)
    env.last_applied_action = np.zeros(3, dtype=np.float64)
    env.action_delay_buffer = [np.zeros(3, dtype=np.float64) for _ in range(env.current_action_delay)]
    env._reset_action_tracking_diagnostics()


def place_tip(
    env: PegInHoleMujocoEnv,
    target_tip_pos: np.ndarray,
    args: argparse.Namespace,
) -> dict[str, Any]:
    q_target, achieved_tip, ik_error, ik_iterations = env._solve_ik_with_diagnostics(target_tip_pos)
    env._set_arm_qpos(env.data, q_target)
    env._set_arm_control(q_target)
    env.data.qvel[:] = 0.0
    mujoco.mj_forward(env.model, env.data)
    for _ in range(args.settle_steps):
        mujoco.mj_step(env.model, env.data)
    reset_action_tracking(env)
    info = env._get_info()
    setup_error = float(np.linalg.norm(np.asarray(info["peg_tip_pos"]) - target_tip_pos))
    return {
        "setup_ok": bool(setup_error <= args.setup_tolerance),
        "setup_error": setup_error,
        "setup_ik_error": float(ik_error),
        "setup_ik_iterations": int(ik_iterations),
        "setup_achieved_x": float(achieved_tip[0]),
        "setup_achieved_y": float(achieved_tip[1]),
        "setup_achieved_z": float(achieved_tip[2]),
        "setup_collision": bool(env._check_collision()),
        "setup_collision_pairs": ";".join(env._collision_contact_pairs()[:8]),
    }


def clipped_recenter_action(
    tip: np.ndarray,
    target: np.ndarray,
    *,
    max_xy_action: float,
    z_action: float,
    action_low: np.ndarray,
    action_high: np.ndarray,
) -> np.ndarray:
    delta_xy = target[:2] - tip[:2]
    xy_norm = float(np.linalg.norm(delta_xy))
    action = np.zeros(3, dtype=np.float64)
    if xy_norm > 1e-9:
        action[:2] = delta_xy * min(1.0, max_xy_action / xy_norm)
    action[2] = float(z_action)
    return np.clip(action, action_low, action_high).astype(np.float32)


def finite_mean(values: list[float]) -> float:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=np.float64)
    return float(np.mean(finite)) if finite.size else float("nan")


def finite_max(values: list[float]) -> float:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=np.float64)
    return float(np.max(finite)) if finite.size else float("nan")


def finite_min(values: list[float]) -> float:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=np.float64)
    return float(np.min(finite)) if finite.size else float("nan")


def run_probe(
    env: PegInHoleMujocoEnv,
    args: argparse.Namespace,
    *,
    ik_control_mode: str,
    actuator_kp_multiplier: float,
    joint_damping_multiplier: float,
    xy_offset_m: float,
    z_above_m: float,
    angle_deg: float,
    probe_id: int,
) -> dict[str, Any]:
    obs, info = env.reset(seed=args.seed + probe_id)
    del obs
    apply_dynamics_multipliers(
        env,
        actuator_kp_multiplier=actuator_kp_multiplier,
        joint_damping_multiplier=joint_damping_multiplier,
    )
    target = np.asarray(info["target_pos"], dtype=np.float64)
    angle_rad = math.radians(float(angle_deg))
    offset_vec = np.asarray(
        [math.cos(angle_rad) * xy_offset_m, math.sin(angle_rad) * xy_offset_m, z_above_m],
        dtype=np.float64,
    )
    target_tip_pos = target + offset_vec
    setup = place_tip(env, target_tip_pos, args)

    start_info = env._get_info()
    start_tip = np.asarray(start_info["peg_tip_pos"], dtype=np.float64)
    start_dist_xy = float(np.linalg.norm(start_tip[:2] - target[:2]))
    start_z_above = float(start_tip[2] - target[2])
    start_tilt = float(start_info.get("peg_tilt_angle_deg", np.nan))

    tracking_errors: list[float] = []
    ik_errors: list[float] = []
    orientation_errors: list[float] = []
    tilt_angles: list[float] = []
    joint_target_errors: list[float] = []
    joint_limit_margins: list[float] = []
    actual_delta_xy_norms: list[float] = []
    command_delta_xy_norms: list[float] = []
    step_alignments: list[float] = []
    collision_step = -1
    terminated = False
    truncated = False
    final_info = start_info

    for step_id in range(args.recenter_steps):
        pre_tip = np.asarray(env._get_info()["peg_tip_pos"], dtype=np.float64)
        action = clipped_recenter_action(
            pre_tip,
            target,
            max_xy_action=args.max_xy_action,
            z_action=args.z_action,
            action_low=np.asarray(env.action_space.low, dtype=np.float64),
            action_high=np.asarray(env.action_space.high, dtype=np.float64),
        )
        _, _, terminated, truncated, final_info = env.step(action)
        actual_delta = np.asarray(final_info["action_actual_tip_delta"], dtype=np.float64)
        target_delta = np.asarray(final_info["action_target_tip_delta"], dtype=np.float64)
        command_norm = float(np.linalg.norm(target_delta[:2]))
        actual_norm = float(np.linalg.norm(actual_delta[:2]))
        if command_norm > 1e-9 and actual_norm > 1e-9:
            step_alignments.append(float(np.dot(target_delta[:2], actual_delta[:2]) / (command_norm * actual_norm)))
        actual_delta_xy_norms.append(actual_norm)
        command_delta_xy_norms.append(command_norm)
        tracking_errors.append(float(final_info["action_tracking_error"]))
        ik_errors.append(float(final_info["ik_target_error"]))
        orientation_errors.append(float(final_info.get("ik_orientation_error", np.nan)))
        tilt_angles.append(float(final_info.get("peg_tilt_angle_deg", np.nan)))
        joint_target_errors.append(float(final_info.get("joint_target_error", np.nan)))
        joint_limit_margins.append(float(final_info.get("joint_limit_min_normalized_margin", np.nan)))
        if bool(final_info.get("collision", False)) and collision_step < 0:
            collision_step = step_id + 1
        if terminated or truncated:
            break

    end_tip = np.asarray(final_info["peg_tip_pos"], dtype=np.float64)
    end_dist_xy = float(np.linalg.norm(end_tip[:2] - target[:2]))
    end_z_above = float(end_tip[2] - target[2])
    total_actual_delta = end_tip - start_tip
    desired_total = np.asarray([target[0] - start_tip[0], target[1] - start_tip[1]], dtype=np.float64)
    desired_norm = float(np.linalg.norm(desired_total))
    actual_xy_norm = float(np.linalg.norm(total_actual_delta[:2]))
    total_alignment = float("nan")
    if desired_norm > 1e-9 and actual_xy_norm > 1e-9:
        total_alignment = float(np.dot(desired_total, total_actual_delta[:2]) / (desired_norm * actual_xy_norm))
    commanded_xy = float(np.sum(command_delta_xy_norms))
    xy_reduction = start_dist_xy - end_dist_xy

    return {
        "probe_id": probe_id,
        "ik_control_mode": ik_control_mode,
        "actuator_kp_multiplier": float(actuator_kp_multiplier),
        "joint_damping_multiplier": float(joint_damping_multiplier),
        "xy_offset_mm": float(xy_offset_m * 1000.0),
        "z_above_mm": float(z_above_m * 1000.0),
        "angle_deg": float(angle_deg),
        **setup,
        "steps_executed": len(tracking_errors),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "collision": bool(final_info.get("collision", False)),
        "collision_step": int(collision_step),
        "collision_pairs": str(final_info.get("collision_contact_pairs", "")),
        "start_dist_xy_mm": start_dist_xy * 1000.0,
        "end_dist_xy_mm": end_dist_xy * 1000.0,
        "xy_reduction_mm": xy_reduction * 1000.0,
        "xy_reduction_per_command": xy_reduction / max(commanded_xy, 1e-9),
        "total_xy_alignment": total_alignment,
        "mean_step_xy_alignment": finite_mean(step_alignments),
        "mean_step_xy_gain": (
            float(np.sum(actual_delta_xy_norms) / max(np.sum(command_delta_xy_norms), 1e-9))
            if command_delta_xy_norms
            else float("nan")
        ),
        "start_z_above_mm": start_z_above * 1000.0,
        "end_z_above_mm": end_z_above * 1000.0,
        "z_drift_mm": (end_z_above - start_z_above) * 1000.0,
        "start_tilt_deg": start_tilt,
        "max_tilt_deg": finite_max(tilt_angles),
        "mean_tracking_error_mm": finite_mean(tracking_errors) * 1000.0,
        "mean_ik_target_error_mm": finite_mean(ik_errors) * 1000.0,
        "mean_ik_orientation_error": finite_mean(orientation_errors),
        "mean_joint_target_error": finite_mean(joint_target_errors),
        "min_joint_limit_normalized_margin": finite_min(joint_limit_margins),
        "final_success": bool(final_info.get("insertion_success", False)),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize_group(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(tuple(row[key] for key in keys), []).append(row)

    summaries: list[dict[str, Any]] = []
    for group_key, group_rows in sorted(groups.items(), key=lambda item: item[0]):
        summary = {key: value for key, value in zip(keys, group_key)}
        summary.update(
            {
                "probes": len(group_rows),
                "setup_ok_rate": float(np.mean([bool(row["setup_ok"]) for row in group_rows])),
                "setup_collision_rate": float(np.mean([bool(row["setup_collision"]) for row in group_rows])),
                "collision_rate": float(np.mean([bool(row["collision"]) for row in group_rows])),
                "success_rate": float(np.mean([bool(row["final_success"]) for row in group_rows])),
                "mean_xy_reduction_mm": finite_mean([float(row["xy_reduction_mm"]) for row in group_rows]),
                "mean_xy_reduction_per_command": finite_mean(
                    [float(row["xy_reduction_per_command"]) for row in group_rows]
                ),
                "mean_total_xy_alignment": finite_mean([float(row["total_xy_alignment"]) for row in group_rows]),
                "mean_step_xy_gain": finite_mean([float(row["mean_step_xy_gain"]) for row in group_rows]),
                "mean_z_drift_mm": finite_mean([float(row["z_drift_mm"]) for row in group_rows]),
                "max_tilt_deg": finite_max([float(row["max_tilt_deg"]) for row in group_rows]),
                "mean_tracking_error_mm": finite_mean(
                    [float(row["mean_tracking_error_mm"]) for row in group_rows]
                ),
                "mean_ik_target_error_mm": finite_mean(
                    [float(row["mean_ik_target_error_mm"]) for row in group_rows]
                ),
            }
        )
        summaries.append(summary)
    return summaries


def write_summary(path: Path, rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_mode = summarize_group(rows, ("ik_control_mode",))
    by_mode_dynamics = summarize_group(
        rows,
        ("ik_control_mode", "actuator_kp_multiplier", "joint_damping_multiplier"),
    )
    by_mode_z = summarize_group(rows, ("ik_control_mode", "z_above_mm"))
    by_mode_offset = summarize_group(rows, ("ik_control_mode", "xy_offset_mm"))
    lines = [
        "# Near-Contact Recenter Diagnostic",
        "",
        f"- Model path: `{args.model_path}`",
        f"- Recenter steps: `{args.recenter_steps}`",
        f"- Max XY action: `{args.max_xy_action:.4f} m`",
        f"- Z action: `{args.z_action:.4f} m`",
        f"- XY offsets mm: `{list(args.xy_offsets_mm)}`",
        f"- Z-above mm: `{list(args.z_above_mm)}`",
        f"- Angles deg: `{list(args.angles_deg)}`",
        "",
        "## By IK Mode",
        "",
        "| mode | probes | setup ok | setup coll | coll | success | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm | ik err mm |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in by_mode:
        lines.append(
            "| {ik_control_mode} | {probes} | {setup_ok_rate:.3f} | {setup_collision_rate:.3f} | "
            "{collision_rate:.3f} | {success_rate:.3f} | {mean_xy_reduction_mm:.3f} | "
            "{mean_xy_reduction_per_command:.3f} | {mean_total_xy_alignment:.3f} | "
            "{mean_step_xy_gain:.3f} | {mean_z_drift_mm:.3f} | {max_tilt_deg:.3f} | "
            "{mean_tracking_error_mm:.3f} | {mean_ik_target_error_mm:.3f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## By IK Mode And Dynamics",
            "",
            "| mode | kp | damping | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in by_mode_dynamics:
        lines.append(
            "| {ik_control_mode} | {actuator_kp_multiplier:.2f} | {joint_damping_multiplier:.2f} | "
            "{probes} | {collision_rate:.3f} | {mean_xy_reduction_mm:.3f} | "
            "{mean_xy_reduction_per_command:.3f} | {mean_total_xy_alignment:.3f} | "
            "{mean_step_xy_gain:.3f} | {mean_z_drift_mm:.3f} | {max_tilt_deg:.3f} | "
            "{mean_tracking_error_mm:.3f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## By IK Mode And Z",
            "",
            "| mode | z mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in by_mode_z:
        lines.append(
            "| {ik_control_mode} | {z_above_mm:.1f} | {probes} | {collision_rate:.3f} | "
            "{mean_xy_reduction_mm:.3f} | {mean_xy_reduction_per_command:.3f} | "
            "{mean_total_xy_alignment:.3f} | {mean_step_xy_gain:.3f} | "
            "{mean_z_drift_mm:.3f} | {max_tilt_deg:.3f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## By IK Mode And XY Offset",
            "",
            "| mode | offset mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in by_mode_offset:
        lines.append(
            "| {ik_control_mode} | {xy_offset_mm:.1f} | {probes} | {collision_rate:.3f} | "
            "{mean_xy_reduction_mm:.3f} | {mean_xy_reduction_per_command:.3f} | "
            "{mean_total_xy_alignment:.3f} | {mean_step_xy_gain:.3f} | "
            "{mean_z_drift_mm:.3f} | {max_tilt_deg:.3f} |".format(**row)
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    if args.recenter_steps <= 0:
        raise ValueError("--recenter-steps must be positive.")
    if args.max_xy_action <= 0.0:
        raise ValueError("--max-xy-action must be positive.")
    rows: list[dict[str, Any]] = []
    probe_id = 0
    for ik_control_mode in args.ik_control_modes:
        env = make_env(args, ik_control_mode)
        try:
            for kp_multiplier in args.actuator_kp_multipliers:
                for damping_multiplier in args.joint_damping_multipliers:
                    for z_mm in args.z_above_mm:
                        for offset_mm in args.xy_offsets_mm:
                            for angle_deg in args.angles_deg:
                                row = run_probe(
                                    env,
                                    args,
                                    ik_control_mode=ik_control_mode,
                                    actuator_kp_multiplier=float(kp_multiplier),
                                    joint_damping_multiplier=float(damping_multiplier),
                                    xy_offset_m=float(offset_mm) / 1000.0,
                                    z_above_m=float(z_mm) / 1000.0,
                                    angle_deg=float(angle_deg),
                                    probe_id=probe_id,
                                )
                                rows.append(row)
                                probe_id += 1
        finally:
            env.close()

    write_csv(args.output_csv, rows)
    write_summary(args.output_md, rows, args)
    for row in summarize_group(rows, ("ik_control_mode",)):
        print(
            "{ik_control_mode}: probes={probes}, coll={collision_rate:.3f}, "
            "xy_reduction={mean_xy_reduction_mm:.2f}mm, reduction/cmd={mean_xy_reduction_per_command:.3f}, "
            "alignment={mean_total_xy_alignment:.3f}, z_drift={mean_z_drift_mm:.2f}mm, "
            "tilt_max={max_tilt_deg:.2f}".format(**row)
        )
    print(f"Wrote {args.output_csv}")
    print(f"Wrote {args.output_md}")


if __name__ == "__main__":
    main()
