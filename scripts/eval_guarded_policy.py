from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco import (
    GuardedPolicyConfig,
    GuardedPolicyController,
    MujocoGuardStateProvider,
    OracleControllerConfig,
    PegInHoleMujocoEnv,
)
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
    geometry_hole_center_xy_jitter: tuple[float, float] = (0.002, 0.002)
    geometry_fixture_height_jitter: float = 0.001
    geometry_table_height_jitter: float = 0.001
    geometry_hole_half_size_range: tuple[float, float] = (0.025, 0.029)
    geometry_peg_radius_range: tuple[float, float] = (0.0115, 0.0125)
    contact_friction_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solref_time_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solref_damping_multiplier_range: tuple[float, float] = (1.0, 1.0)
    contact_solimp_width_multiplier_range: tuple[float, float] = (1.0, 1.0)
    dynamics_joint_damping_multiplier_range: tuple[float, float] = (1.0, 1.0)
    dynamics_actuator_kp_multiplier_range: tuple[float, float] = (1.0, 1.0)


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


HARD_BUCKET_SCENARIO = Scenario(
    "hard_full_light_bucket",
    "full_light_geometry",
    control_action_scale_range=(0.8, 1.1),
    control_action_noise_std_range=(0.0, 0.00025),
    control_action_delay_range=(2, 2),
    control_action_filter_alpha_range=(0.55, 0.70),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a learned policy with deployment-time guarded insertion."
    )
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=90_000)
    parser.add_argument("--output-csv", type=Path, default=Path("results/eval_guarded_policy_latest.csv"))
    parser.add_argument("--output-md", type=Path, default=Path("results/eval_guarded_policy_latest.md"))
    parser.add_argument("--include-hard-bucket", action="store_true")
    parser.add_argument("--hard-bucket-only", action="store_true")
    parser.add_argument(
        "--guard-scenario-filter",
        choices=["none", "all", "geometry", "hard"],
        default="all",
        help="Limit guarded insertion to none, all, geometry/contact scenarios, or only the hard bucket.",
    )
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
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
    parser.add_argument("--guard-start-xy", type=float, default=0.060)
    parser.add_argument("--guard-start-z", type=float, default=0.100)
    parser.add_argument("--guard-risk-xy", type=float, default=0.0)
    parser.add_argument("--guard-blend", type=float, default=1.0)
    parser.add_argument("--guard-min-policy-steps", type=int, default=0)
    parser.add_argument("--guard-block-down-when-unaligned", action="store_true")
    parser.add_argument("--guard-release-on-high", action="store_true")
    parser.add_argument("--guard-action-gain", type=float, default=1.0)
    parser.add_argument("--guarded-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guarded-max-down-action", type=float, default=0.0035)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.005)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)
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
        geometry_hole_center_xy_jitter=scenario.geometry_hole_center_xy_jitter,
        geometry_fixture_height_jitter=scenario.geometry_fixture_height_jitter,
        geometry_table_height_jitter=scenario.geometry_table_height_jitter,
        geometry_hole_half_size_range=scenario.geometry_hole_half_size_range,
        geometry_peg_radius_range=scenario.geometry_peg_radius_range,
        contact_friction_multiplier_range=scenario.contact_friction_multiplier_range,
        contact_solref_time_multiplier_range=scenario.contact_solref_time_multiplier_range,
        contact_solref_damping_multiplier_range=scenario.contact_solref_damping_multiplier_range,
        contact_solimp_width_multiplier_range=scenario.contact_solimp_width_multiplier_range,
        dynamics_joint_damping_multiplier_range=scenario.dynamics_joint_damping_multiplier_range,
        dynamics_actuator_kp_multiplier_range=scenario.dynamics_actuator_kp_multiplier_range,
    )


def make_guarded_config(args: argparse.Namespace) -> GuardedPolicyConfig:
    return GuardedPolicyConfig(
        scenario_filter=args.guard_scenario_filter,
        guard_start_xy=args.guard_start_xy,
        guard_start_z=args.guard_start_z,
        guard_risk_xy=args.guard_risk_xy,
        guard_blend=args.guard_blend,
        guard_min_policy_steps=args.guard_min_policy_steps,
        guard_block_down_when_unaligned=args.guard_block_down_when_unaligned,
        guard_release_on_high=args.guard_release_on_high,
        oracle=OracleControllerConfig(
            mode="guarded_two_stage",
            action_gain=args.guard_action_gain,
            guarded_align_xy_tolerance=args.guarded_align_xy_tolerance,
            guarded_insert_xy_tolerance=args.guarded_insert_xy_tolerance,
            guarded_retract_xy_tolerance=args.guarded_retract_xy_tolerance,
            guarded_preinsert_height=args.guarded_preinsert_height,
            guarded_max_xy_action=args.guarded_max_xy_action,
            guarded_max_down_action=args.guarded_max_down_action,
            guarded_max_up_action=args.guarded_max_up_action,
            guarded_prediction_steps=args.guarded_prediction_steps,
        ),
    )


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def range_text(values: tuple[Any, Any]) -> str:
    return f"{values[0]}:{values[1]}"


def evaluate_scenario(args: argparse.Namespace, scenario: Scenario) -> dict[str, Any]:
    env = make_env(args, scenario)
    model = AGENTS[args.agent].load(args.model, env=env, device=args.device)
    guarded_controller = GuardedPolicyController(make_guarded_config(args))
    guard_state_provider = MujocoGuardStateProvider(env)
    guard_enabled = guarded_controller.scenario_uses_guard(scenario.name, scenario.level)
    successes = 0
    collisions = 0
    timeouts = 0
    guarded_episodes = 0
    returns: list[float] = []
    steps: list[float] = []
    guarded_steps: list[float] = []
    final_dist_xy: list[float] = []
    final_dist_z: list[float] = []

    try:
        for episode in range(args.episodes):
            obs, info = env.reset(seed=args.seed + episode)
            guarded_controller.reset()
            episode_return = 0.0
            episode_guard_steps = 0
            while True:
                policy_action, _ = model.predict(obs, deterministic=True)
                step = guarded_controller.step_with_provider(
                    guard_state_provider,
                    info,
                    policy_action,
                    scenario_name=scenario.name,
                    scenario_level=scenario.level,
                )
                action = step.action
                guarded = step.guarded
                episode_guard_steps += int(guarded)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_return += float(reward)
                if terminated or truncated:
                    break

            successes += int(info["insertion_success"])
            collisions += int(info["collision"])
            timeouts += int(truncated and not info["insertion_success"])
            guarded_episodes += int(episode_guard_steps > 0)
            returns.append(episode_return)
            steps.append(float(info["step_count"]))
            guarded_steps.append(float(episode_guard_steps))
            final_dist_xy.append(float(info["dist_xy"]))
            final_dist_z.append(float(info["dist_z"]))
    finally:
        env.close()

    mean_steps = mean(steps)
    mean_guarded_steps = mean(guarded_steps)
    return {
        "name": scenario.name,
        "level": scenario.level,
        "episodes": args.episodes,
        "success_rate": successes / args.episodes,
        "collision_rate": collisions / args.episodes,
        "timeout_rate": timeouts / args.episodes,
        "mean_return": mean(returns),
        "mean_steps": mean_steps,
        "mean_guarded_steps": mean_guarded_steps,
        "mean_guarded_step_fraction": mean_guarded_steps / max(mean_steps, 1e-9),
        "guarded_episode_rate": guarded_episodes / args.episodes,
        "guard_enabled": guard_enabled,
        "mean_final_dist_xy": mean(final_dist_xy),
        "mean_final_dist_z": mean(final_dist_z),
        "control_scale_range": range_text(scenario.control_action_scale_range),
        "control_noise_std_range": range_text(scenario.control_action_noise_std_range),
        "control_delay_range": range_text(scenario.control_action_delay_range),
        "control_filter_alpha_range": range_text(scenario.control_action_filter_alpha_range),
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
        "# Guarded Policy Evaluation",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Observation mode: `{args.observation_mode}`",
        f"- Episodes per scenario: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Guard start XY: `{args.guard_start_xy}`",
        f"- Guard start Z above target: `{args.guard_start_z}`",
        f"- Guard risk XY: `{args.guard_risk_xy}`",
        f"- Guard scenario filter: `{args.guard_scenario_filter}`",
        f"- Guard blend: `{args.guard_blend}`",
        f"- Guard min policy steps: `{args.guard_min_policy_steps}`",
        f"- Guard block down when unaligned: `{args.guard_block_down_when_unaligned}`",
        f"- Guarded align/insert XY: `{args.guarded_align_xy_tolerance}/{args.guarded_insert_xy_tolerance}`",
        f"- Guarded max XY/down/up action: `{args.guarded_max_xy_action}/{args.guarded_max_down_action}/{args.guarded_max_up_action}`",
        f"- Guarded prediction steps: `{args.guarded_prediction_steps}`",
        "",
        "| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {name} | {level} | {guard_enabled} | {success_rate:.3f} | {collision_rate:.3f} | "
            "{timeout_rate:.3f} | {mean_return:.3f} | {mean_steps:.1f} | "
            "{mean_guarded_steps:.1f} ({mean_guarded_step_fraction:.2f}) | "
            "{guarded_episode_rate:.3f} | {mean_final_dist_xy:.5f} | "
            "{mean_final_dist_z:.5f} |".format(**row)
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved Markdown report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")
    if args.guard_start_xy <= 0.0 or args.guard_start_z <= 0.0:
        raise ValueError("--guard-start-xy and --guard-start-z must be positive.")
    if args.guard_risk_xy < 0.0 or args.guard_risk_xy > args.guard_start_xy:
        raise ValueError("--guard-risk-xy must be between 0 and --guard-start-xy.")

    scenarios = [HARD_BUCKET_SCENARIO] if args.hard_bucket_only else list(CORE_SCENARIOS)
    if args.include_hard_bucket and not args.hard_bucket_only:
        scenarios.append(HARD_BUCKET_SCENARIO)

    rows = []
    for scenario in scenarios:
        row = evaluate_scenario(args, scenario)
        rows.append(row)
        print(
            "{name}: success={success_rate:.3f} collision={collision_rate:.3f} "
            "timeout={timeout_rate:.3f} guard_steps={mean_guarded_steps:.1f} "
            "guard_ep={guarded_episode_rate:.3f} return={mean_return:.3f}".format(**row)
        )

    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, args, rows)


if __name__ == "__main__":
    main()
