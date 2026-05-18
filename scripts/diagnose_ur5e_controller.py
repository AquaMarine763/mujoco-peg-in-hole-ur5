from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np
import mujoco

from peg_in_hole_mujoco import PegInHoleMujocoEnv


DIRECTIONS = (
    ("x_plus", np.asarray([1.0, 0.0, 0.0], dtype=np.float64)),
    ("x_minus", np.asarray([-1.0, 0.0, 0.0], dtype=np.float64)),
    ("y_plus", np.asarray([0.0, 1.0, 0.0], dtype=np.float64)),
    ("y_minus", np.asarray([0.0, -1.0, 0.0], dtype=np.float64)),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diagnose UR5e Cartesian low-level control tracking near the hole."
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
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--seed", type=int, default=720_000)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--lateral-action", type=float, default=0.003)
    parser.add_argument("--steps-per-direction", type=int, default=8)
    parser.add_argument(
        "--setup-mode",
        choices=["ik_settle", "closed_loop"],
        default="ik_settle",
        help="Place the tip at the low-Z probe point directly, or approach it through env.step.",
    )
    parser.add_argument("--settle-steps", type=int, default=80)
    parser.add_argument("--approach-max-steps", type=int, default=180)
    parser.add_argument("--approach-tolerance", type=float, default=0.003)
    parser.add_argument("--low-z-above-target", type=float, default=0.030)
    parser.add_argument("--target-pos", nargs=3, type=float, default=(0.55, 0.05, 0.65))
    parser.add_argument(
        "--initialization-mode",
        choices=["fixed", "target_relative_high_start"],
        default="target_relative_high_start",
    )
    parser.add_argument("--initial-tip-z-above-range", nargs=2, type=float, default=(0.15, 0.20))
    parser.add_argument("--initial-tip-xy-offset-range", nargs=2, type=float, default=(0.08, 0.12))
    parser.add_argument("--ik-orientation-weight", type=float, default=0.12)
    parser.add_argument("--ik-posture-weight", type=float, default=0.01)
    parser.add_argument("--ik-step-limit", type=float, default=0.06)
    parser.add_argument("--ik-max-iterations", type=int, default=24)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/ur5e_full/controller_diagnostics/ur5e_controller_direction_rows.csv"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("results/ur5e_full/controller_diagnostics/ur5e_controller_summary.md"),
    )
    return parser


def make_env(args: argparse.Namespace, ik_control_mode: str) -> PegInHoleMujocoEnv:
    target_pos = tuple(float(value) for value in args.target_pos)
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode="state",
        image_width=160,
        image_height=120,
        max_steps=max(
            400,
            args.approach_max_steps + len(DIRECTIONS) * args.steps_per_direction + 20,
        ),
        action_scale=args.action_scale,
        target_low=target_pos,
        target_high=target_pos,
        initialization_mode=args.initialization_mode,
        initial_tip_z_above_range=tuple(args.initial_tip_z_above_range),
        initial_tip_xy_offset_range=tuple(args.initial_tip_xy_offset_range),
        success_xy_tolerance=0.005,
        success_z_tolerance=0.006,
        ik_control_mode=ik_control_mode,
        ik_orientation_weight=args.ik_orientation_weight,
        ik_posture_weight=args.ik_posture_weight,
        ik_step_limit=args.ik_step_limit,
        ik_max_iterations=args.ik_max_iterations,
    )


def clip_action(delta: np.ndarray, action_scale: float) -> np.ndarray:
    return np.clip(delta, -action_scale, action_scale).astype(np.float32)


def drive_to_target(
    env: PegInHoleMujocoEnv,
    target_tip_pos: np.ndarray,
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    step_infos: list[dict[str, Any]] = []
    info = env._get_info()  # Diagnostic script; avoid changing env state.
    ok = False
    for _ in range(args.approach_max_steps):
        tip_pos = np.asarray(info["peg_tip_pos"], dtype=np.float64)
        delta = target_tip_pos - tip_pos
        if float(np.linalg.norm(delta)) <= args.approach_tolerance:
            ok = True
            break
        _, _, terminated, truncated, info = env.step(clip_action(delta, args.action_scale))
        step_infos.append(info)
        if terminated or truncated:
            break
    return info, step_infos, ok


def place_tip_at_target(
    env: PegInHoleMujocoEnv,
    target_tip_pos: np.ndarray,
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    q_target, achieved_tip, ik_error, ik_iterations = env._solve_ik_with_diagnostics(
        target_tip_pos
    )
    env._set_arm_qpos(env.data, q_target)
    env._set_arm_control(q_target)
    env.data.qvel[:] = 0.0
    mujoco.mj_forward(env.model, env.data)
    for _ in range(args.settle_steps):
        mujoco.mj_step(env.model, env.data)
    env._reset_action_tracking_diagnostics()
    info = env._get_info()
    setup_error = float(np.linalg.norm(np.asarray(info["peg_tip_pos"]) - target_tip_pos))
    info["setup_ik_target_error"] = float(ik_error)
    info["setup_ik_iterations"] = int(ik_iterations)
    info["setup_achieved_tip"] = achieved_tip.astype(np.float32)
    return info, [info], setup_error <= args.approach_tolerance


def setup_probe_pose(
    env: PegInHoleMujocoEnv,
    target_tip_pos: np.ndarray,
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    if args.setup_mode == "closed_loop":
        return drive_to_target(env, target_tip_pos, args)
    return place_tip_at_target(env, target_tip_pos, args)


def run_direction(
    env: PegInHoleMujocoEnv,
    direction_name: str,
    direction: np.ndarray,
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    start_info = env._get_info()
    start_tip = np.asarray(start_info["peg_tip_pos"], dtype=np.float64)
    action = (direction * args.lateral_action).astype(np.float32)
    step_infos: list[dict[str, Any]] = []
    info = start_info

    terminated = False
    truncated = False
    for _ in range(args.steps_per_direction):
        _, _, terminated, truncated, info = env.step(action)
        step_infos.append(info)
        if terminated or truncated:
            break

    end_tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    commanded_delta = direction * args.lateral_action * len(step_infos)
    actual_delta = end_tip - start_tip
    commanded_norm = float(np.linalg.norm(commanded_delta[:2]))
    actual_norm = float(np.linalg.norm(actual_delta[:2]))
    alignment = 0.0
    if commanded_norm > 1e-9 and actual_norm > 1e-9:
        alignment = float(
            np.dot(commanded_delta[:2], actual_delta[:2])
            / (commanded_norm * actual_norm)
        )

    tracking_errors = [float(step_info["action_tracking_error"]) for step_info in step_infos]
    ik_errors = [float(step_info["ik_target_error"]) for step_info in step_infos]
    orientation_errors = [
        float(step_info.get("ik_orientation_error", np.nan)) for step_info in step_infos
    ]
    tilt_angles = [
        float(step_info.get("peg_tilt_angle_deg", np.nan)) for step_info in step_infos
    ]
    limit_margins = [
        float(step_info.get("joint_limit_min_normalized_margin", np.nan))
        for step_info in step_infos
    ]

    row = {
        "direction": direction_name,
        "steps_executed": len(step_infos),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "commanded_dx": float(commanded_delta[0]),
        "commanded_dy": float(commanded_delta[1]),
        "commanded_dz": float(commanded_delta[2]),
        "actual_dx": float(actual_delta[0]),
        "actual_dy": float(actual_delta[1]),
        "actual_dz": float(actual_delta[2]),
        "xy_gain": actual_norm / max(commanded_norm, 1e-9),
        "xy_alignment": alignment,
        "mean_action_tracking_error": float(np.mean(tracking_errors)) if tracking_errors else np.nan,
        "mean_ik_target_error": float(np.mean(ik_errors)) if ik_errors else np.nan,
        "mean_ik_orientation_error": (
            float(np.nanmean(orientation_errors)) if orientation_errors else np.nan
        ),
        "max_peg_tilt_angle_deg": float(np.nanmax(tilt_angles)) if tilt_angles else np.nan,
        "min_joint_limit_normalized_margin": (
            float(np.nanmin(limit_margins)) if limit_margins else np.nan
        ),
        "final_collision": bool(info.get("collision", False)),
        "final_success": bool(info.get("insertion_success", False)),
    }
    return row, step_infos


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    modes = sorted({str(row["ik_control_mode"]) for row in rows})
    for mode in modes:
        mode_rows = [row for row in rows if row["ik_control_mode"] == mode]
        summaries.append(
            {
                "ik_control_mode": mode,
                "rows": len(mode_rows),
                "setup_ok_rate": float(np.mean([row["setup_ok"] for row in mode_rows])),
                "mean_xy_gain": float(np.mean([row["xy_gain"] for row in mode_rows])),
                "mean_xy_alignment": float(np.mean([row["xy_alignment"] for row in mode_rows])),
                "mean_action_tracking_error": float(
                    np.mean([row["mean_action_tracking_error"] for row in mode_rows])
                ),
                "mean_ik_target_error": float(
                    np.mean([row["mean_ik_target_error"] for row in mode_rows])
                ),
                "mean_ik_orientation_error": float(
                    np.mean([row["mean_ik_orientation_error"] for row in mode_rows])
                ),
                "max_peg_tilt_angle_deg": float(
                    np.max([row["max_peg_tilt_angle_deg"] for row in mode_rows])
                ),
                "min_joint_limit_normalized_margin": float(
                    np.min([row["min_joint_limit_normalized_margin"] for row in mode_rows])
                ),
            }
        )
    return summaries


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, summaries: list[dict[str, Any]], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# UR5e controller diagnostic summary",
        "",
        f"- Model path: `{args.model_path}`",
        f"- Episodes per mode: `{args.episodes}`",
        f"- Setup mode: `{args.setup_mode}`",
        f"- Low-Z target: `target_z + {args.low_z_above_target:.3f} m`",
        f"- Lateral probe: `{args.steps_per_direction}` steps x `{args.lateral_action:.4f} m`",
        "",
        "| ik mode | rows | setup ok | xy gain | xy alignment | tracking err | ik err | ori err | max tilt deg | min joint margin |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summaries:
        lines.append(
            "| {ik_control_mode} | {rows} | {setup_ok_rate:.3f} | {mean_xy_gain:.3f} | "
            "{mean_xy_alignment:.3f} | {mean_action_tracking_error:.5f} | "
            "{mean_ik_target_error:.5f} | {mean_ik_orientation_error:.5f} | "
            "{max_peg_tilt_angle_deg:.3f} | {min_joint_limit_normalized_margin:.3f} |".format(
                **row
            )
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    rows: list[dict[str, Any]] = []

    for mode in args.ik_control_modes:
        env = make_env(args, mode)
        try:
            for episode in range(args.episodes):
                seed = args.seed + episode
                _, info = env.reset(seed=seed)
                target_pos = np.asarray(info["target_pos"], dtype=np.float64)
                low_target = target_pos + np.asarray(
                    [0.0, 0.0, args.low_z_above_target],
                    dtype=np.float64,
                )
                setup_info, _, setup_ok = setup_probe_pose(env, low_target, args)
                for direction_name, direction in DIRECTIONS:
                    row, _ = run_direction(env, direction_name, direction, args)
                    row.update(
                        {
                            "ik_control_mode": mode,
                            "episode": episode,
                            "seed": seed,
                            "setup_mode": args.setup_mode,
                            "setup_ok": bool(setup_ok),
                            "setup_final_dist_xy": float(setup_info["dist_xy"]),
                            "setup_final_dist_z": float(setup_info["dist_z"]),
                            "setup_ik_target_error": float(
                                setup_info.get("setup_ik_target_error", np.nan)
                            ),
                            "setup_ik_iterations": int(
                                setup_info.get("setup_ik_iterations", 0)
                            ),
                        }
                    )
                    rows.append(row)
        finally:
            env.close()

    summaries = summarize(rows)
    write_csv(args.output_csv, rows)
    write_summary(args.output_md, summaries, args)

    for row in summaries:
        print(
            "{ik_control_mode}: setup_ok={setup_ok_rate:.3f}, "
            "xy_gain={mean_xy_gain:.3f}, alignment={mean_xy_alignment:.3f}, "
            "tracking={mean_action_tracking_error:.5f}, tilt_max={max_peg_tilt_angle_deg:.3f}".format(
                **row
            )
        )
    print(f"Wrote {args.output_csv}")
    print(f"Wrote {args.output_md}")


if __name__ == "__main__":
    main()
