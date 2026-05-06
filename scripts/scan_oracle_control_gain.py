from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from peg_in_hole_mujoco import OracleControllerConfig, PegInHoleMujocoEnv, oracle_action


@dataclass(frozen=True)
class GainResult:
    gain: float
    episodes: int
    success_rate: float
    collision_rate: float
    timeout_rate: float
    mean_steps: float
    mean_final_dist_xy: float
    mean_final_dist_z: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan staged-oracle action gains under control randomization."
    )
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=Path("results/oracle_control_gain_scan.csv"))
    parser.add_argument("--output-md", type=Path, default=Path("results/oracle_control_gain_scan.md"))
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed", type=int, default=120_000)
    parser.add_argument("--gains", nargs="+", type=float, default=(1.0, 0.7, 0.5, 0.35, 0.25))
    parser.add_argument("--oracle-mode", choices=["staged", "guarded_two_stage"], default="staged")
    parser.add_argument("--guarded-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guarded-max-down-action", type=float, default=0.0035)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.005)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)
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
    parser.add_argument("--control-action-scale-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--control-action-noise-std-range", nargs=2, type=float, default=(0.0, 0.0008))
    parser.add_argument("--control-action-delay-range", nargs=2, type=int, default=(0, 2))
    parser.add_argument("--control-action-filter-alpha-range", nargs=2, type=float, default=(0.55, 1.0))
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
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
        observation_mode="state",
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

def evaluate_gain(args: argparse.Namespace, gain: float) -> GainResult:
    env = make_env(args)
    oracle_config = OracleControllerConfig(
        mode=args.oracle_mode,
        action_gain=gain,
        guarded_align_xy_tolerance=args.guarded_align_xy_tolerance,
        guarded_insert_xy_tolerance=args.guarded_insert_xy_tolerance,
        guarded_retract_xy_tolerance=args.guarded_retract_xy_tolerance,
        guarded_preinsert_height=args.guarded_preinsert_height,
        guarded_max_xy_action=args.guarded_max_xy_action,
        guarded_max_down_action=args.guarded_max_down_action,
        guarded_max_up_action=args.guarded_max_up_action,
        guarded_prediction_steps=args.guarded_prediction_steps,
    )
    successes = 0
    collisions = 0
    timeouts = 0
    steps: list[float] = []
    final_dist_xy: list[float] = []
    final_dist_z: list[float] = []

    try:
        for episode in range(args.episodes):
            _, info = env.reset(seed=args.seed + episode)
            while True:
                action = oracle_action(env, info, oracle_config)
                _, _, terminated, truncated, info = env.step(action)
                if terminated or truncated:
                    break

            successes += int(info["insertion_success"])
            collisions += int(info["collision"])
            timeouts += int(truncated and not info["insertion_success"])
            steps.append(float(info["step_count"]))
            final_dist_xy.append(float(info["dist_xy"]))
            final_dist_z.append(float(info["dist_z"]))
    finally:
        env.close()

    return GainResult(
        gain=gain,
        episodes=args.episodes,
        success_rate=successes / args.episodes,
        collision_rate=collisions / args.episodes,
        timeout_rate=timeouts / args.episodes,
        mean_steps=float(np.mean(steps)),
        mean_final_dist_xy=float(np.mean(final_dist_xy)),
        mean_final_dist_z=float(np.mean(final_dist_z)),
    )


def result_to_row(result: GainResult) -> dict[str, Any]:
    return {
        "gain": result.gain,
        "episodes": result.episodes,
        "success_rate": result.success_rate,
        "collision_rate": result.collision_rate,
        "timeout_rate": result.timeout_rate,
        "mean_steps": result.mean_steps,
        "mean_final_dist_xy": result.mean_final_dist_xy,
        "mean_final_dist_z": result.mean_final_dist_z,
    }


def write_csv(path: Path, results: list[GainResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [result_to_row(result) for result in results]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved CSV report to {path}")


def write_markdown(path: Path, args: argparse.Namespace, results: list[GainResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Oracle Control Gain Scan",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Domain randomization level: `{args.domain_randomization_level}`",
        f"- Oracle mode: `{args.oracle_mode}`",
        f"- Episodes per gain: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Control scale range: `{args.control_action_scale_range[0]}:{args.control_action_scale_range[1]}`",
        f"- Control noise std range: `{args.control_action_noise_std_range[0]}:{args.control_action_noise_std_range[1]}`",
        f"- Control delay range: `{args.control_action_delay_range[0]}:{args.control_action_delay_range[1]}`",
        f"- Control filter alpha range: `{args.control_action_filter_alpha_range[0]}:{args.control_action_filter_alpha_range[1]}`",
    ]
    if args.oracle_mode == "guarded_two_stage":
        lines.extend(
            [
                f"- Guarded align XY tolerance: `{args.guarded_align_xy_tolerance}`",
                f"- Guarded insert XY tolerance: `{args.guarded_insert_xy_tolerance}`",
                f"- Guarded preinsert height: `{args.guarded_preinsert_height}`",
                f"- Guarded max XY/down/up action: `{args.guarded_max_xy_action}/{args.guarded_max_down_action}/{args.guarded_max_up_action}`",
                f"- Guarded prediction steps: `{args.guarded_prediction_steps}`",
            ]
        )
    lines.extend(
        [
            "",
            "| Gain | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for result in results:
        lines.append(
            "| {gain:.3f} | {success_rate:.3f} | {collision_rate:.3f} | "
            "{timeout_rate:.3f} | {mean_steps:.1f} | {mean_final_dist_xy:.5f} | "
            "{mean_final_dist_z:.5f} |".format(**result_to_row(result))
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved Markdown report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")
    if not args.gains:
        raise ValueError("--gains must contain at least one value.")

    results = []
    for gain in args.gains:
        result = evaluate_gain(args, gain)
        results.append(result)
        print(
            "gain={gain:.3f} success={success_rate:.3f} collision={collision_rate:.3f} "
            "timeout={timeout_rate:.3f} steps={mean_steps:.1f}".format(
                **result_to_row(result)
            )
        )

    write_csv(args.output_csv, results)
    write_markdown(args.output_md, args, results)


if __name__ == "__main__":
    main()
