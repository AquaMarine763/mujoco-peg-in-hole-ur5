from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco import PegInHoleMujocoEnv
from peg_in_hole_mujoco.sim_config import parse_args_with_config


AGENTS = {
    "sac": SAC,
    "ppo": PPO,
    "a2c": A2C,
}


CONTROL_RANGES = {
    "control_action_scale_range": (0.8, 1.2),
    "control_action_noise_std_range": (0.0, 0.0008),
    "control_action_delay_range": (0, 2),
    "control_action_filter_alpha_range": (0.55, 1.0),
}


CONTACT_LIGHT_RANGES = {
    "contact_friction_multiplier_range": (0.7, 1.3),
    "contact_solref_time_multiplier_range": (0.8, 1.25),
    "contact_solref_damping_multiplier_range": (0.8, 1.2),
    "contact_solimp_width_multiplier_range": (0.8, 1.2),
    "dynamics_joint_damping_multiplier_range": (0.8, 1.2),
    "dynamics_actuator_kp_multiplier_range": (0.8, 1.2),
}


@dataclass(frozen=True)
class Scenario:
    name: str
    level: str
    control_action_scale_range: tuple[float, float] = (1.0, 1.0)
    control_action_noise_std_range: tuple[float, float] = (0.0, 0.0)
    control_action_delay_range: tuple[int, int] = (0, 0)
    control_action_filter_alpha_range: tuple[float, float] = (1.0, 1.0)
    contact_friction_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solref_time_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solref_damping_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solimp_width_multiplier_range: tuple[float, float] = (1.0, 1.0)
    dynamics_joint_damping_multiplier_range: tuple[float, float] = (1.0, 1.0)
    dynamics_actuator_kp_multiplier_range: tuple[float, float] = (1.0, 1.0)
    geometry_hole_half_size_range: tuple[float, float] = (0.017, 0.021)


CORE_SCENARIOS = (
    Scenario("clean", "none"),
    Scenario("visual_camera", "visual_camera"),
    Scenario("visual_camera_control", "visual_camera_control", **CONTROL_RANGES),
    Scenario("full_light_geometry", "full_light_geometry", **CONTROL_RANGES),
    Scenario(
        "full_contact_light",
        "full_contact_light",
        **CONTROL_RANGES,
        **CONTACT_LIGHT_RANGES,
    ),
)


STRESS_SCENARIOS = (
    Scenario(
        "high_delay_0_3",
        "visual_camera_control",
        control_action_scale_range=(1.0, 1.0),
        control_action_noise_std_range=(0.0, 0.0),
        control_action_delay_range=(0, 3),
        control_action_filter_alpha_range=(1.0, 1.0),
    ),
    Scenario(
        "high_combined_control",
        "visual_camera_control",
        control_action_scale_range=(0.75, 1.25),
        control_action_noise_std_range=(0.0, 0.0015),
        control_action_delay_range=(0, 3),
        control_action_filter_alpha_range=(0.4, 1.0),
    ),
    Scenario(
        "high_full_contact_light",
        "full_contact_light",
        contact_friction_multiplier_range=(0.5, 1.5),
        contact_solref_time_multiplier_range=(0.6, 1.6),
        contact_solref_damping_multiplier_range=(0.6, 1.5),
        contact_solimp_width_multiplier_range=(0.5, 1.5),
        dynamics_joint_damping_multiplier_range=(0.6, 1.5),
        dynamics_actuator_kp_multiplier_range=(0.6, 1.4),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained policy across the standard environment matrix.")
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=90_000)
    parser.add_argument("--output-csv", type=Path, default=Path("results/eval_matrix_latest.csv"))
    parser.add_argument("--output-md", type=Path, default=Path("results/eval_matrix_latest.md"))
    parser.add_argument("--include-stress", action="store_true")
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument(
        "--initialization-mode",
        choices=["fixed", "target_relative_high_start"],
        default="fixed",
    )
    parser.add_argument("--initial-tip-z-above-range", nargs=2, type=float, default=(0.15, 0.25))
    parser.add_argument("--initial-tip-xy-offset-range", nargs=2, type=float, default=(0.08, 0.16))
    parser.add_argument("--initial-tip-xy-angle-range-deg", nargs=2, type=float, default=(0.0, 360.0))
    parser.add_argument("--initial-ik-max-attempts", type=int, default=20)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--geometry-hole-half-size-range", nargs=2, type=float, default=(0.017, 0.021))
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
    return parse_args_with_config(parser)


def make_env(args: argparse.Namespace, scenario: Scenario) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode=args.observation_mode,
        image_width=args.width,
        image_height=args.height,
        include_near_hole_crop=args.include_near_hole_crop,
        near_hole_crop_size=args.near_hole_crop_size,
        max_steps=args.max_steps,
        action_scale=args.action_scale,
        initialization_mode=args.initialization_mode,
        initial_tip_z_above_range=tuple(args.initial_tip_z_above_range),
        initial_tip_xy_offset_range=tuple(args.initial_tip_xy_offset_range),
        initial_tip_xy_angle_range_deg=tuple(args.initial_tip_xy_angle_range_deg),
        initial_ik_max_attempts=args.initial_ik_max_attempts,
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
        domain_randomization_level=scenario.level,
        control_action_scale_range=scenario.control_action_scale_range,
        control_action_noise_std_range=scenario.control_action_noise_std_range,
        control_action_delay_range=scenario.control_action_delay_range,
        control_action_filter_alpha_range=scenario.control_action_filter_alpha_range,
        geometry_hole_half_size_range=tuple(args.geometry_hole_half_size_range),
        contact_friction_multiplier_range=scenario.contact_friction_multiplier_range,
        contact_solref_time_multiplier_range=scenario.contact_solref_time_multiplier_range,
        contact_solref_damping_multiplier_range=scenario.contact_solref_damping_multiplier_range,
        contact_solimp_width_multiplier_range=scenario.contact_solimp_width_multiplier_range,
        dynamics_joint_damping_multiplier_range=scenario.dynamics_joint_damping_multiplier_range,
        dynamics_actuator_kp_multiplier_range=scenario.dynamics_actuator_kp_multiplier_range,
    )


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def range_text(values: tuple[Any, Any]) -> str:
    return f"{values[0]}:{values[1]}"


def evaluate_scenario(args: argparse.Namespace, scenario: Scenario) -> dict[str, Any]:
    env = make_env(args, scenario)
    model = AGENTS[args.agent].load(args.model, env=env, device=args.device)
    successes = 0
    collisions = 0
    timeouts = 0
    returns: list[float] = []
    steps: list[float] = []
    final_dist_xy: list[float] = []
    final_dist_z: list[float] = []

    try:
        for episode in range(args.episodes):
            obs, _ = env.reset(seed=args.seed + episode)
            episode_return = 0.0
            while True:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_return += float(reward)
                if terminated or truncated:
                    break

            successes += int(info["insertion_success"])
            collisions += int(info["collision"])
            timeouts += int(truncated and not info["insertion_success"])
            returns.append(episode_return)
            steps.append(float(info["step_count"]))
            final_dist_xy.append(float(info["dist_xy"]))
            final_dist_z.append(float(info["dist_z"]))
    finally:
        env.close()

    return {
        "name": scenario.name,
        "level": scenario.level,
        "episodes": args.episodes,
        "success_rate": successes / args.episodes,
        "collision_rate": collisions / args.episodes,
        "timeout_rate": timeouts / args.episodes,
        "mean_return": mean(returns),
        "mean_steps": mean(steps),
        "mean_final_dist_xy": mean(final_dist_xy),
        "mean_final_dist_z": mean(final_dist_z),
        "control_scale_range": range_text(scenario.control_action_scale_range),
        "control_noise_std_range": range_text(scenario.control_action_noise_std_range),
        "control_delay_range": range_text(scenario.control_action_delay_range),
        "control_filter_alpha_range": range_text(scenario.control_action_filter_alpha_range),
        "contact_friction_range": range_text(scenario.contact_friction_multiplier_range),
        "contact_solref_time_range": range_text(scenario.contact_solref_time_multiplier_range),
        "contact_solref_damping_range": range_text(scenario.contact_solref_damping_multiplier_range),
        "contact_solimp_width_range": range_text(scenario.contact_solimp_width_multiplier_range),
        "joint_damping_range": range_text(scenario.dynamics_joint_damping_multiplier_range),
        "actuator_kp_range": range_text(scenario.dynamics_actuator_kp_multiplier_range),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved CSV report to {path}")


def write_markdown(path: Path, args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Evaluation Matrix",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Observation mode: `{args.observation_mode}`",
        f"- Episodes per scenario: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Success tolerances: `xy={args.success_xy_tolerance}`, `z={args.success_z_tolerance}`",
        "",
        "| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {name} | {level} | {success_rate:.3f} | {collision_rate:.3f} | "
            "{timeout_rate:.3f} | {mean_return:.3f} | {mean_steps:.1f} | "
            "{mean_final_dist_xy:.5f} | {mean_final_dist_z:.5f} |".format(**row)
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved Markdown report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")

    scenarios = list(CORE_SCENARIOS)
    if args.include_stress:
        scenarios.extend(STRESS_SCENARIOS)

    rows = []
    for scenario in scenarios:
        row = evaluate_scenario(args, scenario)
        rows.append(row)
        print(
            "{name}: success={success_rate:.3f} collision={collision_rate:.3f} "
            "timeout={timeout_rate:.3f} return={mean_return:.3f} "
            "steps={mean_steps:.1f} dist_xy={mean_final_dist_xy:.5f} "
            "dist_z={mean_final_dist_z:.5f}".format(**row)
        )

    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, args, rows)


if __name__ == "__main__":
    main()
