from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from peg_in_hole_mujoco import PegInHoleMujocoEnv


@dataclass(frozen=True)
class HoleScanResult:
    hole_half_size: float
    peg_radius: float
    episodes: int
    successes: int
    collisions: int
    timeouts: int
    mean_steps: float
    mean_final_dist_xy: float
    mean_final_dist_z: float

    @property
    def success_rate(self) -> float:
        return self.successes / self.episodes

    @property
    def collision_rate(self) -> float:
        return self.collisions / self.episodes

    @property
    def timeout_rate(self) -> float:
        return self.timeouts / self.episodes

    @property
    def side_length(self) -> float:
        return 2.0 * self.hole_half_size

    @property
    def peg_diameter(self) -> float:
        return 2.0 * self.peg_radius

    @property
    def radial_clearance(self) -> float:
        return self.hole_half_size - self.peg_radius


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan staged-oracle success over fixed hole/peg sizes.")
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=Path("results/hole_geometry_oracle_scan.csv"))
    parser.add_argument("--output-md", type=Path, default=Path("results/hole_geometry_oracle_scan.md"))
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--seed", type=int, default=510_000)
    parser.add_argument("--hole-half-sizes", nargs="+", type=float, default=(0.045, 0.029, 0.025, 0.020, 0.017, 0.015))
    parser.add_argument("--peg-radii", nargs="+", type=float, default=(0.012,))
    parser.add_argument("--expert-action-gain", type=float, default=1.0)
    parser.add_argument("--observation-mode", choices=["state", "image"], default="state")
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--approach-xy-tolerance", type=float, default=0.06)
    parser.add_argument("--approach-height", type=float, default=0.08)
    parser.add_argument("--target-low", nargs=3, type=float, default=(0.50, 0.00, 0.65))
    parser.add_argument("--target-high", nargs=3, type=float, default=(0.60, 0.10, 0.65))
    parser.add_argument("--hole-center-xy-jitter", nargs=2, type=float, default=(0.0, 0.0))
    parser.add_argument("--fixture-height-jitter", type=float, default=0.0)
    parser.add_argument("--table-height-jitter", type=float, default=0.0)
    return parser.parse_args()


def make_env(args: argparse.Namespace, hole_half_size: float, peg_radius: float) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode=args.observation_mode,
        max_steps=args.max_steps,
        action_scale=args.action_scale,
        target_low=tuple(args.target_low),
        target_high=tuple(args.target_high),
        success_xy_tolerance=args.success_xy_tolerance,
        success_z_tolerance=args.success_z_tolerance,
        approach_xy_tolerance=args.approach_xy_tolerance,
        approach_height=args.approach_height,
        success_bonus=120.0,
        collision_penalty=300.0,
        progress_reward_scale=20.0,
        distance_reward_scale=2.0,
        action_alignment_scale=2.0,
        domain_randomization_level="full_light_geometry",
        control_action_scale_range=(1.0, 1.0),
        control_action_noise_std_range=(0.0, 0.0),
        control_action_delay_range=(0, 0),
        control_action_filter_alpha_range=(1.0, 1.0),
        geometry_hole_center_xy_jitter=tuple(args.hole_center_xy_jitter),
        geometry_fixture_height_jitter=args.fixture_height_jitter,
        geometry_table_height_jitter=args.table_height_jitter,
        geometry_hole_half_size_range=(hole_half_size, hole_half_size),
        geometry_peg_radius_range=(peg_radius, peg_radius),
    )


def oracle_action(env: PegInHoleMujocoEnv, info: dict[str, Any], action_gain: float) -> np.ndarray:
    tip = info["peg_tip_pos"].astype(np.float64)
    target = info["target_pos"].astype(np.float64)
    desired = np.asarray([target[0], target[1], info["desired_z"]], dtype=np.float64)
    action = action_gain * (desired - tip)
    return np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32)


def evaluate_size(args: argparse.Namespace, hole_half_size: float, peg_radius: float, seed_offset: int) -> HoleScanResult:
    env = make_env(args, hole_half_size, peg_radius)
    successes = 0
    collisions = 0
    timeouts = 0
    steps: list[float] = []
    final_dist_xy: list[float] = []
    final_dist_z: list[float] = []

    try:
        for episode in range(args.episodes):
            _, info = env.reset(seed=args.seed + seed_offset + episode)
            while True:
                action = oracle_action(env, info, args.expert_action_gain)
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

    return HoleScanResult(
        hole_half_size=hole_half_size,
        peg_radius=peg_radius,
        episodes=args.episodes,
        successes=successes,
        collisions=collisions,
        timeouts=timeouts,
        mean_steps=float(np.mean(steps)),
        mean_final_dist_xy=float(np.mean(final_dist_xy)),
        mean_final_dist_z=float(np.mean(final_dist_z)),
    )


def result_row(result: HoleScanResult) -> dict[str, Any]:
    return {
        "hole_half_size": result.hole_half_size,
        "hole_side_length": result.side_length,
        "peg_radius": result.peg_radius,
        "peg_diameter": result.peg_diameter,
        "radial_clearance": result.radial_clearance,
        "episodes": result.episodes,
        "success_rate": result.success_rate,
        "collision_rate": result.collision_rate,
        "timeout_rate": result.timeout_rate,
        "mean_steps": result.mean_steps,
        "mean_final_dist_xy": result.mean_final_dist_xy,
        "mean_final_dist_z": result.mean_final_dist_z,
    }


def write_csv(path: Path, results: list[HoleScanResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [result_row(result) for result in results]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved CSV report to {path}")


def write_markdown(path: Path, args: argparse.Namespace, results: list[HoleScanResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Hole Geometry Oracle Scan",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Observation mode: `{args.observation_mode}`",
        f"- Episodes per size: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Success tolerances: `xy={args.success_xy_tolerance}`, `z={args.success_z_tolerance}`",
        f"- Hole center jitter: `{args.hole_center_xy_jitter[0]}:{args.hole_center_xy_jitter[1]}`",
        f"- Fixture height jitter: `{args.fixture_height_jitter}`",
        f"- Table height jitter: `{args.table_height_jitter}`",
        "",
        "| Hole half-size | Hole side | Peg radius | Peg diameter | Clearance | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            "| {hole_half_size:.3f} | {hole_side_length:.3f} | {peg_radius:.3f} | "
            "{peg_diameter:.3f} | {radial_clearance:.3f} | {success_rate:.3f} | "
            "{collision_rate:.3f} | {timeout_rate:.3f} | {mean_steps:.1f} | "
            "{mean_final_dist_xy:.5f} | {mean_final_dist_z:.5f} |".format(**result_row(result))
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved Markdown report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")

    results = []
    seed_offset = 0
    for peg_radius in args.peg_radii:
        for hole_half_size in args.hole_half_sizes:
            result = evaluate_size(args, hole_half_size, peg_radius, seed_offset)
            results.append(result)
            seed_offset += args.episodes
            print(
                "hole_half={hole_half_size:.3f} peg_radius={peg_radius:.3f} "
                "clearance={radial_clearance:.3f} success={success_rate:.3f} "
                "collision={collision_rate:.3f} timeout={timeout_rate:.3f}".format(
                    **result_row(result)
                )
            )

    write_csv(args.output_csv, results)
    write_markdown(args.output_md, args, results)


if __name__ == "__main__":
    main()
