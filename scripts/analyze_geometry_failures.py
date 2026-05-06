from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco import PegInHoleMujocoEnv


AGENTS = {
    "sac": SAC,
    "ppo": PPO,
    "a2c": A2C,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze geometry-randomization failure modes for a trained policy.")
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--episodes", type=int, default=200)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=720_000)
    parser.add_argument("--output-csv", type=Path, default=Path("results/geometry_failure_analysis_episodes.csv"))
    parser.add_argument("--output-md", type=Path, default=Path("results/geometry_failure_analysis.md"))
    parser.add_argument(
        "--domain-randomization-level",
        choices=["none", "visual", "visual_camera", "visual_camera_control", "full_light_geometry", "full_contact_light", "full"],
        default="full_light_geometry",
    )
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--control-action-scale-range", nargs=2, type=float, default=(1.0, 1.0))
    parser.add_argument("--control-action-noise-std-range", nargs=2, type=float, default=(0.0, 0.0))
    parser.add_argument("--control-action-delay-range", nargs=2, type=int, default=(0, 0))
    parser.add_argument("--control-action-filter-alpha-range", nargs=2, type=float, default=(1.0, 1.0))
    parser.add_argument("--geometry-hole-center-xy-jitter", nargs=2, type=float, default=(0.0, 0.0))
    parser.add_argument("--geometry-fixture-height-jitter", type=float, default=0.0)
    parser.add_argument("--geometry-table-height-jitter", type=float, default=0.0)
    parser.add_argument("--geometry-hole-half-size-range", nargs=2, type=float, default=(0.025, 0.029))
    parser.add_argument("--geometry-peg-radius-range", nargs=2, type=float, default=(0.012, 0.012))
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--approach-xy-tolerance", type=float, default=0.02)
    parser.add_argument("--approach-height", type=float, default=0.08)
    parser.add_argument("--staged-xy-weight", type=float, default=2.0)
    parser.add_argument("--staged-z-weight", type=float, default=1.0)
    parser.add_argument("--success-bonus", type=float, default=120.0)
    parser.add_argument("--collision-penalty", type=float, default=300.0)
    parser.add_argument("--timeout-penalty", type=float, default=10.0)
    parser.add_argument("--progress-reward-scale", type=float, default=20.0)
    parser.add_argument("--distance-reward-scale", type=float, default=2.0)
    parser.add_argument("--action-penalty-scale", type=float, default=0.002)
    parser.add_argument("--action-alignment-scale", type=float, default=2.0)
    return parser.parse_args()


def make_env(args: argparse.Namespace) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode=args.observation_mode,
        image_width=args.width,
        image_height=args.height,
        include_near_hole_crop=args.include_near_hole_crop,
        near_hole_crop_size=args.near_hole_crop_size,
        max_steps=args.max_steps,
        action_scale=args.action_scale,
        success_xy_tolerance=args.success_xy_tolerance,
        success_z_tolerance=args.success_z_tolerance,
        approach_xy_tolerance=args.approach_xy_tolerance,
        approach_height=args.approach_height,
        staged_xy_weight=args.staged_xy_weight,
        staged_z_weight=args.staged_z_weight,
        success_bonus=args.success_bonus,
        collision_penalty=args.collision_penalty,
        timeout_penalty=args.timeout_penalty,
        progress_reward_scale=args.progress_reward_scale,
        distance_reward_scale=args.distance_reward_scale,
        action_penalty_scale=args.action_penalty_scale,
        action_alignment_scale=args.action_alignment_scale,
        domain_randomization_level=args.domain_randomization_level,
        control_action_scale_range=tuple(args.control_action_scale_range),
        control_action_noise_std_range=tuple(args.control_action_noise_std_range),
        control_action_delay_range=tuple(args.control_action_delay_range),
        control_action_filter_alpha_range=tuple(args.control_action_filter_alpha_range),
        geometry_hole_center_xy_jitter=tuple(args.geometry_hole_center_xy_jitter),
        geometry_fixture_height_jitter=args.geometry_fixture_height_jitter,
        geometry_table_height_jitter=args.geometry_table_height_jitter,
        geometry_hole_half_size_range=tuple(args.geometry_hole_half_size_range),
        geometry_peg_radius_range=tuple(args.geometry_peg_radius_range),
    )


def outcome_from_info(info: dict[str, Any], truncated: bool) -> str:
    if bool(info["insertion_success"]):
        return "success"
    if bool(info["collision"]):
        return "collision"
    if truncated:
        return "timeout"
    return "terminated_failure"


def bucket_xy(dist_xy: float) -> str:
    if dist_xy < 0.005:
        return "aligned_<0.005"
    if dist_xy < 0.015:
        return "near_0.005_0.015"
    if dist_xy < 0.030:
        return "off_0.015_0.030"
    return "far_>=0.030"


def evaluate(args: argparse.Namespace) -> list[dict[str, Any]]:
    env = make_env(args)
    model = AGENTS[args.agent].load(args.model, env=env, device=args.device)
    rows: list[dict[str, Any]] = []

    try:
        for episode in range(args.episodes):
            seed = args.seed + episode
            obs, info = env.reset(seed=seed)
            episode_return = 0.0
            min_dist_xy = float(info["dist_xy"])
            min_dist_z = float(info["dist_z"])
            mean_action_z: list[float] = []
            mean_action_xy_norm: list[float] = []
            last_action = np.zeros(3, dtype=np.float64)
            truncated = False

            while True:
                action, _ = model.predict(obs, deterministic=True)
                last_action = np.asarray(action, dtype=np.float64)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_return += float(reward)
                min_dist_xy = min(min_dist_xy, float(info["dist_xy"]))
                min_dist_z = min(min_dist_z, float(info["dist_z"]))
                mean_action_z.append(float(last_action[2]))
                mean_action_xy_norm.append(float(np.linalg.norm(last_action[:2])))
                if terminated or truncated:
                    break

            final_dist_xy = float(info["dist_xy"])
            final_dist_z = float(info["dist_z"])
            rows.append(
                {
                    "episode": episode,
                    "seed": seed,
                    "outcome": outcome_from_info(info, truncated),
                    "success": bool(info["insertion_success"]),
                    "collision": bool(info["collision"]),
                    "timeout": bool(truncated and not info["insertion_success"]),
                    "steps": int(info["step_count"]),
                    "episode_return": episode_return,
                    "final_dist_xy": final_dist_xy,
                    "final_dist_z": final_dist_z,
                    "min_dist_xy": min_dist_xy,
                    "min_dist_z": min_dist_z,
                    "final_xy_bucket": bucket_xy(final_dist_xy),
                    "min_xy_bucket": bucket_xy(min_dist_xy),
                    "mean_action_z": float(np.mean(mean_action_z)),
                    "mean_action_xy_norm": float(np.mean(mean_action_xy_norm)),
                    "last_action_x": float(last_action[0]),
                    "last_action_y": float(last_action[1]),
                    "last_action_z": float(last_action[2]),
                    "hole_half_size": float(info.get("hole_half_size", np.nan)),
                    "peg_radius": float(info.get("peg_radius", np.nan)),
                    "hole_clearance": float(info.get("hole_half_size", np.nan) - info.get("peg_radius", np.nan)),
                }
            )
    finally:
        env.close()

    return rows


def mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return float(np.mean(values)) if values else 0.0


def rate(rows: list[dict[str, Any]], key: str) -> float:
    return sum(int(row[key]) for row in rows) / len(rows) if rows else 0.0


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved CSV report to {path}")


def write_markdown(path: Path, args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failures = [row for row in rows if not row["success"]]
    collisions = [row for row in rows if row["collision"]]
    timeouts = [row for row in rows if row["timeout"]]

    lines = [
        "# Geometry Failure Analysis",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Domain randomization level: `{args.domain_randomization_level}`",
        f"- Episodes: `{len(rows)}`",
        f"- Seed: `{args.seed}`",
        f"- Image size: `{args.width}x{args.height}`",
        f"- Near-hole crop: `{args.include_near_hole_crop}`",
        f"- Hole half-size range: `{args.geometry_hole_half_size_range[0]}:{args.geometry_hole_half_size_range[1]}`",
        f"- Peg radius range: `{args.geometry_peg_radius_range[0]}:{args.geometry_peg_radius_range[1]}`",
        "",
        "## Overall",
        "",
        "| Episodes | Success | Collision | Timeout | Mean final XY | Mean final Z | Mean failure XY | Mean failure Z |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| {len(rows)} | {rate(rows, 'success'):.3f} | {rate(rows, 'collision'):.3f} | "
            f"{rate(rows, 'timeout'):.3f} | {mean(rows, 'final_dist_xy'):.5f} | "
            f"{mean(rows, 'final_dist_z'):.5f} | {mean(failures, 'final_dist_xy'):.5f} | "
            f"{mean(failures, 'final_dist_z'):.5f} |"
        ),
        "",
        "## Failure Subset",
        "",
        "| Subset | Episodes | Mean final XY | Mean min XY | Mean final Z | Mean action Z | Mean action XY norm |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| collisions | {len(collisions)} | {mean(collisions, 'final_dist_xy'):.5f} | "
            f"{mean(collisions, 'min_dist_xy'):.5f} | {mean(collisions, 'final_dist_z'):.5f} | "
            f"{mean(collisions, 'mean_action_z'):.5f} | {mean(collisions, 'mean_action_xy_norm'):.5f} |"
        ),
        (
            f"| timeouts | {len(timeouts)} | {mean(timeouts, 'final_dist_xy'):.5f} | "
            f"{mean(timeouts, 'min_dist_xy'):.5f} | {mean(timeouts, 'final_dist_z'):.5f} | "
            f"{mean(timeouts, 'mean_action_z'):.5f} | {mean(timeouts, 'mean_action_xy_norm'):.5f} |"
        ),
        "",
        "## Failure XY Buckets",
        "",
        "| Final XY bucket | Episodes | Success | Collision | Timeout |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for bucket in ("aligned_<0.005", "near_0.005_0.015", "off_0.015_0.030", "far_>=0.030"):
        bucket_rows = [row for row in rows if row["final_xy_bucket"] == bucket]
        if not bucket_rows:
            continue
        lines.append(
            f"| {bucket} | {len(bucket_rows)} | {rate(bucket_rows, 'success'):.3f} | "
            f"{rate(bucket_rows, 'collision'):.3f} | {rate(bucket_rows, 'timeout'):.3f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "If most collisions have non-trivial final or minimum XY error, the policy is descending or contacting before lateral alignment is robust. That is the target failure mode for a near-hole crop or a two-stage approach/insert controller.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved Markdown report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")
    rows = evaluate(args)
    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, args, rows)
    print(
        "episodes={episodes} success_rate={success:.3f} collision_rate={collision:.3f} timeout_rate={timeout:.3f}".format(
            episodes=len(rows),
            success=rate(rows, "success"),
            collision=rate(rows, "collision"),
            timeout=rate(rows, "timeout"),
        )
    )


if __name__ == "__main__":
    main()
