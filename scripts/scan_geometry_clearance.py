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
    OracleControllerConfig,
    PegInHoleMujocoEnv,
)


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
class ClearanceTier:
    name: str
    hole_half_size_range: tuple[float, float]
    peg_radius_range: tuple[float, float]

    @property
    def min_clearance(self) -> float:
        return self.hole_half_size_range[0] - self.peg_radius_range[1]

    @property
    def max_clearance(self) -> float:
        return self.hole_half_size_range[1] - self.peg_radius_range[0]


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


@dataclass(frozen=True)
class GuardMode:
    name: str
    scenario_filter: str
    guard_blend: float = 0.75


CLEARANCE_TIERS = (
    ClearanceTier("wide_legacy", (0.025, 0.029), (0.0115, 0.0125)),
    ClearanceTier("medium", (0.020, 0.024), (0.0115, 0.0125)),
    ClearanceTier("narrow", (0.017, 0.021), (0.0115, 0.0125)),
    ClearanceTier("tight", (0.015, 0.018), (0.0115, 0.0125)),
)


SCENARIOS = {
    "full_light_geometry": Scenario("full_light_geometry", "full_light_geometry", **CONTROL_RANGES),
    "hard_full_light_bucket": Scenario(
        "hard_full_light_bucket",
        "full_light_geometry",
        control_action_scale_range=(0.8, 1.1),
        control_action_noise_std_range=(0.0, 0.00025),
        control_action_delay_range=(2, 2),
        control_action_filter_alpha_range=(0.55, 0.70),
    ),
    "full_contact_light": Scenario(
        "full_contact_light",
        "full_contact_light",
        **CONTROL_RANGES,
        **CONTACT_LIGHT_RANGES,
    ),
}


GUARD_MODES = (
    GuardMode("no_guard", "none", 0.0),
    GuardMode("guard_blend_075", "geometry", 0.75),
    GuardMode("guard_blend_100", "geometry", 1.0),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan hole/peg clearance curriculum difficulty for a trained policy."
    )
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=930_000)
    parser.add_argument("--output-csv", type=Path, default=Path("results/geometry_clearance_scan.csv"))
    parser.add_argument("--output-md", type=Path, default=Path("results/geometry_clearance_scan.md"))
    parser.add_argument(
        "--scenario-preset",
        choices=["geometry", "targeted", "full_contact", "contact"],
        default="targeted",
    )
    parser.add_argument("--tier-preset", choices=["wide_medium", "all"], default="all")
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
    parser.add_argument("--guard-action-gain", type=float, default=1.0)
    parser.add_argument("--guarded-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guarded-max-down-action", type=float, default=0.0035)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.005)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)
    return parser.parse_args()


def tiers_for_args(args: argparse.Namespace) -> list[ClearanceTier]:
    if args.tier_preset == "wide_medium":
        return list(CLEARANCE_TIERS[:2])
    return list(CLEARANCE_TIERS)


def scenarios_for_args(args: argparse.Namespace) -> list[Scenario]:
    if args.scenario_preset == "geometry":
        return [SCENARIOS["full_light_geometry"]]
    if args.scenario_preset == "full_contact":
        return [SCENARIOS["full_contact_light"]]
    if args.scenario_preset == "contact":
        return [
            SCENARIOS["full_light_geometry"],
            SCENARIOS["hard_full_light_bucket"],
            SCENARIOS["full_contact_light"],
        ]
    return [
        SCENARIOS["full_light_geometry"],
        SCENARIOS["hard_full_light_bucket"],
    ]


def make_env(args: argparse.Namespace, scenario: Scenario, tier: ClearanceTier) -> PegInHoleMujocoEnv:
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
        geometry_hole_center_xy_jitter=(0.002, 0.002),
        geometry_fixture_height_jitter=0.001,
        geometry_table_height_jitter=0.001,
        geometry_hole_half_size_range=tier.hole_half_size_range,
        geometry_peg_radius_range=tier.peg_radius_range,
        contact_friction_multiplier_range=scenario.contact_friction_multiplier_range,
        contact_solref_time_multiplier_range=scenario.contact_solref_time_multiplier_range,
        contact_solref_damping_multiplier_range=scenario.contact_solref_damping_multiplier_range,
        contact_solimp_width_multiplier_range=scenario.contact_solimp_width_multiplier_range,
        dynamics_joint_damping_multiplier_range=scenario.dynamics_joint_damping_multiplier_range,
        dynamics_actuator_kp_multiplier_range=scenario.dynamics_actuator_kp_multiplier_range,
    )


def make_guarded_config(args: argparse.Namespace, guard_mode: GuardMode) -> GuardedPolicyConfig:
    return GuardedPolicyConfig(
        scenario_filter=guard_mode.scenario_filter,
        guard_start_xy=args.guard_start_xy,
        guard_start_z=args.guard_start_z,
        guard_risk_xy=args.guard_risk_xy,
        guard_blend=guard_mode.guard_blend,
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


def clearance_mm(value: float) -> float:
    return value * 1000.0


def evaluate_config(
    args: argparse.Namespace,
    tier: ClearanceTier,
    scenario: Scenario,
    guard_mode: GuardMode,
) -> dict[str, Any]:
    env = make_env(args, scenario, tier)
    model = AGENTS[args.agent].load(args.model, env=env, device=args.device)
    guarded_controller = GuardedPolicyController(make_guarded_config(args, guard_mode))
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
    clearances: list[float] = []
    hole_half_sizes: list[float] = []
    peg_radii: list[float] = []

    try:
        for episode in range(args.episodes):
            obs, info = env.reset(seed=args.seed + episode)
            guarded_controller.reset()
            episode_return = 0.0
            episode_guard_steps = 0
            while True:
                policy_action, _ = model.predict(obs, deterministic=True)
                guarded_step = guarded_controller.step(
                    env,
                    info,
                    policy_action,
                    scenario_name=scenario.name,
                    scenario_level=scenario.level,
                )
                obs, reward, terminated, truncated, info = env.step(guarded_step.action)
                episode_return += float(reward)
                episode_guard_steps += int(guarded_step.guarded)
                if terminated or truncated:
                    break

            hole_half_size = float(info.get("hole_half_size", tier.hole_half_size_range[0]))
            peg_radius = float(info.get("peg_radius", tier.peg_radius_range[0]))
            successes += int(info["insertion_success"])
            collisions += int(info["collision"])
            timeouts += int(truncated and not info["insertion_success"])
            guarded_episodes += int(episode_guard_steps > 0)
            returns.append(episode_return)
            steps.append(float(info["step_count"]))
            guarded_steps.append(float(episode_guard_steps))
            final_dist_xy.append(float(info["dist_xy"]))
            final_dist_z.append(float(info["dist_z"]))
            clearances.append(hole_half_size - peg_radius)
            hole_half_sizes.append(hole_half_size)
            peg_radii.append(peg_radius)
    finally:
        env.close()

    mean_steps = mean(steps)
    mean_guarded_steps = mean(guarded_steps)
    return {
        "tier": tier.name,
        "scenario": scenario.name,
        "guard_mode": guard_mode.name,
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
        "mean_hole_half_size": mean(hole_half_sizes),
        "mean_peg_radius": mean(peg_radii),
        "mean_clearance": mean(clearances),
        "min_clearance": min(clearances),
        "max_clearance": max(clearances),
        "tier_min_clearance": tier.min_clearance,
        "tier_max_clearance": tier.max_clearance,
        "mean_clearance_mm": clearance_mm(mean(clearances)),
        "tier_min_clearance_mm": clearance_mm(tier.min_clearance),
        "tier_max_clearance_mm": clearance_mm(tier.max_clearance),
        "hole_half_size_range": range_text(tier.hole_half_size_range),
        "peg_radius_range": range_text(tier.peg_radius_range),
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
    tiers = list(dict.fromkeys(str(row["tier"]) for row in rows))
    scenarios = list(dict.fromkeys(str(row["scenario"]) for row in rows))
    guard_modes = list(dict.fromkeys(str(row["guard_mode"]) for row in rows))
    lines = [
        "# Geometry Clearance Scan",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Episodes per combination: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Scenario preset: `{args.scenario_preset}`",
        f"- Tier preset: `{args.tier_preset}`",
        f"- Success tolerances: `xy={args.success_xy_tolerance}`, `z={args.success_z_tolerance}`",
        "",
        "## Tier Summary",
        "",
        "| Tier | Hole half size | Peg radius | Clearance range |",
        "| --- | ---: | ---: | ---: |",
    ]
    for tier in tiers:
        row = next(item for item in rows if item["tier"] == tier)
        lines.append(
            "| {tier} | {hole_half_size_range} | {peg_radius_range} | "
            "{tier_min_clearance_mm:.1f}-{tier_max_clearance_mm:.1f} mm |".format(**row)
        )

    lines.extend(["", "## Success Matrix", ""])
    for scenario in scenarios:
        lines.extend(
            [
                f"### {scenario}",
                "",
                "| Tier | no guard | guard blend 0.75 | guard blend 1.0 |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for tier in tiers:
            values = {}
            for guard_mode in guard_modes:
                row = next(
                    item
                    for item in rows
                    if item["tier"] == tier
                    and item["scenario"] == scenario
                    and item["guard_mode"] == guard_mode
                )
                values[guard_mode] = float(row["success_rate"])
            lines.append(
                "| {tier} | {no_guard:.3f} | {guard075:.3f} | {guard100:.3f} |".format(
                    tier=tier,
                    no_guard=values.get("no_guard", float("nan")),
                    guard075=values.get("guard_blend_075", float("nan")),
                    guard100=values.get("guard_blend_100", float("nan")),
                )
            )
        lines.append("")

    lines.extend(
        [
            "## Detailed Rows",
            "",
            "| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            "| {tier} | {scenario} | {guard_mode} | {success_rate:.3f} | "
            "{collision_rate:.3f} | {timeout_rate:.3f} | {mean_return:.3f} | "
            "{mean_steps:.1f} | {mean_guarded_steps:.1f} | "
            "{mean_final_dist_xy:.5f} | {mean_final_dist_z:.5f} | "
            "{mean_clearance_mm:.1f} mm |".format(**row)
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved Markdown report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")

    rows: list[dict[str, Any]] = []
    for tier in tiers_for_args(args):
        for scenario in scenarios_for_args(args):
            for guard_mode in GUARD_MODES:
                row = evaluate_config(args, tier, scenario, guard_mode)
                rows.append(row)
                print(
                    "{tier} / {scenario} / {guard_mode}: success={success_rate:.3f} "
                    "collision={collision_rate:.3f} timeout={timeout_rate:.3f} "
                    "guard_steps={mean_guarded_steps:.1f} clearance={mean_clearance_mm:.1f}mm".format(
                        **row
                    )
                )

    write_csv(args.output_csv, rows)
    write_markdown(args.output_md, args, rows)


if __name__ == "__main__":
    main()
