from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
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


@dataclass(frozen=True)
class BucketStats:
    key: str
    episodes: int
    successes: int
    collisions: int
    timeouts: int
    mean_steps: float
    mean_final_dist_xy: float
    mean_final_dist_z: float

    @property
    def success_rate(self) -> float:
        return self.successes / self.episodes if self.episodes else 0.0

    @property
    def collision_rate(self) -> float:
        return self.collisions / self.episodes if self.episodes else 0.0

    @property
    def timeout_rate(self) -> float:
        return self.timeouts / self.episodes if self.episodes else 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze control-randomization failure modes for a trained policy."
    )
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--episodes", type=int, default=200)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=150_000)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/control_failure_analysis_episodes.csv"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("results/control_failure_analysis.md"),
    )
    parser.add_argument(
        "--domain-randomization-level",
        choices=[
            "none",
            "visual",
            "visual_camera",
            "visual_camera_control",
            "full_light_geometry",
            "full_contact_light",
            "full",
        ],
        default="visual_camera_control",
    )
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--control-action-scale-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--control-action-noise-std-range", nargs=2, type=float, default=(0.0, 0.0008))
    parser.add_argument("--control-action-delay-range", nargs=2, type=int, default=(0, 2))
    parser.add_argument("--control-action-filter-alpha-range", nargs=2, type=float, default=(0.55, 1.0))
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--approach-xy-tolerance", type=float, default=0.06)
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
    )


def scale_bucket(value: float) -> str:
    if value < 0.9:
        return "low_<0.90"
    if value > 1.1:
        return "high_>1.10"
    return "mid_0.90_1.10"


def noise_bucket(value: float) -> str:
    if value < 0.00025:
        return "low_<0.00025"
    if value < 0.00055:
        return "mid_0.00025_0.00055"
    return "high_>=0.00055"


def filter_bucket(value: float) -> str:
    if value < 0.7:
        return "low_<0.70"
    if value < 0.85:
        return "mid_0.70_0.85"
    return "high_>=0.85"


def mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def evaluate_policy(args: argparse.Namespace) -> list[dict[str, Any]]:
    env = make_env(args)
    model = AGENTS[args.agent].load(args.model, env=env, device=args.device)
    rows: list[dict[str, Any]] = []

    try:
        for episode in range(args.episodes):
            episode_seed = args.seed + episode
            obs, info = env.reset(seed=episode_seed)
            episode_return = 0.0
            max_commanded_norm = 0.0
            max_applied_norm = 0.0
            mean_commanded_norms: list[float] = []
            mean_applied_norms: list[float] = []

            while True:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_return += float(reward)
                commanded = np.asarray(info.get("commanded_action", action), dtype=np.float64)
                applied = np.asarray(info.get("applied_action", action), dtype=np.float64)
                commanded_norm = float(np.linalg.norm(commanded / args.action_scale))
                applied_norm = float(np.linalg.norm(applied / args.action_scale))
                max_commanded_norm = max(max_commanded_norm, commanded_norm)
                max_applied_norm = max(max_applied_norm, applied_norm)
                mean_commanded_norms.append(commanded_norm)
                mean_applied_norms.append(applied_norm)
                if terminated or truncated:
                    break

            success = bool(info["insertion_success"])
            collision = bool(info["collision"])
            timeout = bool(truncated and not success)
            if success:
                outcome = "success"
            elif collision:
                outcome = "collision"
            elif timeout:
                outcome = "timeout"
            else:
                outcome = "terminated_failure"

            scale = float(info.get("control_action_scale_multiplier", 1.0))
            noise = float(info.get("control_action_noise_std", 0.0))
            delay = int(info.get("control_action_delay", 0))
            filter_alpha = float(info.get("control_action_filter_alpha", 1.0))
            rows.append(
                {
                    "episode": episode,
                    "seed": episode_seed,
                    "outcome": outcome,
                    "success": success,
                    "collision": collision,
                    "timeout": timeout,
                    "steps": int(info["step_count"]),
                    "episode_return": episode_return,
                    "final_dist_xy": float(info["dist_xy"]),
                    "final_dist_z": float(info["dist_z"]),
                    "control_action_scale_multiplier": scale,
                    "control_action_noise_std": noise,
                    "control_action_delay": delay,
                    "control_action_filter_alpha": filter_alpha,
                    "scale_bucket": scale_bucket(scale),
                    "noise_bucket": noise_bucket(noise),
                    "delay_bucket": f"delay_{delay}",
                    "filter_bucket": filter_bucket(filter_alpha),
                    "joint_bucket": (
                        f"delay_{delay}|{filter_bucket(filter_alpha)}|"
                        f"{scale_bucket(scale)}|{noise_bucket(noise)}"
                    ),
                    "max_commanded_action_norm": max_commanded_norm,
                    "max_applied_action_norm": max_applied_norm,
                    "mean_commanded_action_norm": mean(mean_commanded_norms),
                    "mean_applied_action_norm": mean(mean_applied_norms),
                }
            )
    finally:
        env.close()

    return rows


def summarize_bucket(rows: list[dict[str, Any]], key: str) -> list[BucketStats]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)

    stats = []
    for bucket, bucket_rows in grouped.items():
        stats.append(
            BucketStats(
                key=bucket,
                episodes=len(bucket_rows),
                successes=sum(int(row["success"]) for row in bucket_rows),
                collisions=sum(int(row["collision"]) for row in bucket_rows),
                timeouts=sum(int(row["timeout"]) for row in bucket_rows),
                mean_steps=mean([float(row["steps"]) for row in bucket_rows]),
                mean_final_dist_xy=mean([float(row["final_dist_xy"]) for row in bucket_rows]),
                mean_final_dist_z=mean([float(row["final_dist_z"]) for row in bucket_rows]),
            )
        )
    return sorted(stats, key=lambda item: (item.collision_rate, item.timeout_rate, item.episodes), reverse=True)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved episode failure analysis to {path}")


def bucket_table(title: str, stats: list[BucketStats], min_episodes: int = 1) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in stats:
        if item.episodes < min_episodes:
            continue
        lines.append(
            "| {key} | {episodes} | {success_rate:.3f} | {collision_rate:.3f} | "
            "{timeout_rate:.3f} | {mean_steps:.1f} | {mean_final_dist_xy:.5f} | "
            "{mean_final_dist_z:.5f} |".format(
                key=item.key,
                episodes=item.episodes,
                success_rate=item.success_rate,
                collision_rate=item.collision_rate,
                timeout_rate=item.timeout_rate,
                mean_steps=item.mean_steps,
                mean_final_dist_xy=item.mean_final_dist_xy,
                mean_final_dist_z=item.mean_final_dist_z,
            )
        )
    return lines


def write_markdown(path: Path, args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    episodes = len(rows)
    successes = sum(int(row["success"]) for row in rows)
    collisions = sum(int(row["collision"]) for row in rows)
    timeouts = sum(int(row["timeout"]) for row in rows)
    failures = [row for row in rows if not row["success"]]
    min_joint_bucket_episodes = max(3, episodes // 50)

    lines = [
        "# Control Failure Analysis",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Observation mode: `{args.observation_mode}`",
        f"- Domain randomization level: `{args.domain_randomization_level}`",
        f"- Episodes: `{episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Success tolerances: `xy={args.success_xy_tolerance}`, `z={args.success_z_tolerance}`",
        "",
        "## Overall",
        "",
        "| Episodes | Success | Collision | Timeout | Failures | Mean failure XY | Mean failure Z |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| {episodes} | {successes / episodes:.3f} | {collisions / episodes:.3f} | "
            f"{timeouts / episodes:.3f} | {len(failures)} | "
            f"{mean([float(row['final_dist_xy']) for row in failures]):.5f} | "
            f"{mean([float(row['final_dist_z']) for row in failures]):.5f} |"
        ),
        "",
    ]
    for title, key, min_episodes in (
        ("By Delay", "delay_bucket", 1),
        ("By Filter Alpha", "filter_bucket", 1),
        ("By Scale", "scale_bucket", 1),
        ("By Noise", "noise_bucket", 1),
        ("Worst Joint Buckets", "joint_bucket", min_joint_bucket_episodes),
    ):
        lines.extend(bucket_table(title, summarize_bucket(rows, key), min_episodes=min_episodes))
        lines.append("")

    lines.extend(
        [
            "## Suggested Next Data Bias",
            "",
            suggested_next_data_bias(rows),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"saved Markdown failure analysis to {path}")


def suggested_next_data_bias(rows: list[dict[str, Any]]) -> str:
    delay_stats = summarize_bucket(rows, "delay_bucket")
    filter_stats = summarize_bucket(rows, "filter_bucket")
    scale_stats = summarize_bucket(rows, "scale_bucket")
    noise_stats = summarize_bucket(rows, "noise_bucket")

    worst_delay = delay_stats[0]
    worst_filter = filter_stats[0]
    worst_scale = scale_stats[0]
    worst_noise = noise_stats[0]
    return (
        "Prioritize new success-only data around "
        f"`{worst_delay.key}`, `{worst_filter.key}`, `{worst_scale.key}`, and "
        f"`{worst_noise.key}`. These buckets currently have the highest collision/timeout "
        "rates in the evaluated control-randomization distribution."
    )


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")

    rows = evaluate_policy(args)
    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, args, rows)

    successes = sum(int(row["success"]) for row in rows)
    collisions = sum(int(row["collision"]) for row in rows)
    timeouts = sum(int(row["timeout"]) for row in rows)
    print(
        "episodes={episodes} success={success:.3f} collision={collision:.3f} "
        "timeout={timeout:.3f}".format(
            episodes=len(rows),
            success=successes / len(rows),
            collision=collisions / len(rows),
            timeout=timeouts / len(rows),
        )
    )


if __name__ == "__main__":
    main()
