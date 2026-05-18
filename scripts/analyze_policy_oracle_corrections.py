from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco import (
    OracleControllerConfig,
    PegInHoleMujocoEnv,
    oracle_action,
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


CLEARANCE_TIERS = {
    "wide_legacy": ClearanceTier("wide_legacy", (0.025, 0.029), (0.0115, 0.0125)),
    "medium": ClearanceTier("medium", (0.020, 0.024), (0.0115, 0.0125)),
    "narrow": ClearanceTier("narrow", (0.017, 0.021), (0.0115, 0.0125)),
    "tight": ClearanceTier("tight", (0.015, 0.018), (0.0115, 0.0125)),
}


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare learned policy actions against guarded-oracle corrective actions."
    )
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=970_000)
    parser.add_argument("--output-csv", type=Path, default=Path("results/policy_oracle_corrections_steps.csv"))
    parser.add_argument(
        "--episode-output-csv",
        type=Path,
        default=Path("results/policy_oracle_corrections_episodes.csv"),
    )
    parser.add_argument("--output-md", type=Path, default=Path("results/policy_oracle_corrections.md"))
    parser.add_argument(
        "--scenario-preset",
        choices=["geometry", "hard", "targeted", "contact"],
        default="targeted",
    )
    parser.add_argument(
        "--tier-preset",
        choices=["wide", "medium", "narrow", "tight", "wide_medium", "medium_narrow", "all"],
        default="wide_medium",
    )
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--near-hole-crop-offset", nargs=2, type=int, default=(0, 0))
    parser.add_argument("--wrist-camera-pos-offset", nargs=3, type=float, default=(0.0, 0.0, 0.0))
    parser.add_argument(
        "--wrist-camera-rot-offset-deg",
        nargs=3,
        type=float,
        default=(0.0, 0.0, 0.0),
    )
    parser.add_argument("--wrist-camera-fovy", type=float, default=None)
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
    parser.add_argument("--failure-window-steps", type=int, default=8)
    parser.add_argument("--near-hole-xy", type=float, default=0.03)
    parser.add_argument("--near-hole-z", type=float, default=0.10)
    parser.add_argument("--opposition-dot-threshold", type=float, default=0.0)
    parser.add_argument("--oracle-action-gain", type=float, default=1.0)
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
    if args.tier_preset == "wide":
        return [CLEARANCE_TIERS["wide_legacy"]]
    if args.tier_preset == "medium":
        return [CLEARANCE_TIERS["medium"]]
    if args.tier_preset == "narrow":
        return [CLEARANCE_TIERS["narrow"]]
    if args.tier_preset == "tight":
        return [CLEARANCE_TIERS["tight"]]
    if args.tier_preset == "wide_medium":
        return [CLEARANCE_TIERS["wide_legacy"], CLEARANCE_TIERS["medium"]]
    if args.tier_preset == "medium_narrow":
        return [CLEARANCE_TIERS["medium"], CLEARANCE_TIERS["narrow"]]
    return list(CLEARANCE_TIERS.values())


def scenarios_for_args(args: argparse.Namespace) -> list[Scenario]:
    if args.scenario_preset == "geometry":
        return [SCENARIOS["full_light_geometry"]]
    if args.scenario_preset == "hard":
        return [SCENARIOS["hard_full_light_bucket"]]
    if args.scenario_preset == "contact":
        return [SCENARIOS["full_light_geometry"], SCENARIOS["full_contact_light"]]
    return [SCENARIOS["full_light_geometry"], SCENARIOS["hard_full_light_bucket"]]


def make_env(args: argparse.Namespace, scenario: Scenario, tier: ClearanceTier) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode=args.observation_mode,
        image_width=args.width,
        image_height=args.height,
        include_near_hole_crop=args.include_near_hole_crop,
        near_hole_crop_size=args.near_hole_crop_size,
        near_hole_crop_offset=tuple(args.near_hole_crop_offset),
        wrist_camera_pos_offset=tuple(args.wrist_camera_pos_offset),
        wrist_camera_rot_offset_deg=tuple(args.wrist_camera_rot_offset_deg),
        wrist_camera_fovy=args.wrist_camera_fovy,
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


def make_oracle_config(args: argparse.Namespace) -> OracleControllerConfig:
    return OracleControllerConfig(
        mode="guarded_two_stage",
        action_gain=args.oracle_action_gain,
        guarded_align_xy_tolerance=args.guarded_align_xy_tolerance,
        guarded_insert_xy_tolerance=args.guarded_insert_xy_tolerance,
        guarded_retract_xy_tolerance=args.guarded_retract_xy_tolerance,
        guarded_preinsert_height=args.guarded_preinsert_height,
        guarded_max_xy_action=args.guarded_max_xy_action,
        guarded_max_down_action=args.guarded_max_down_action,
        guarded_max_up_action=args.guarded_max_up_action,
        guarded_prediction_steps=args.guarded_prediction_steps,
    )


def vector_fields(prefix: str, values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64).reshape(3)
    return {
        f"{prefix}_x": float(values[0]),
        f"{prefix}_y": float(values[1]),
        f"{prefix}_z": float(values[2]),
    }


def action_cosine(a: np.ndarray, b: np.ndarray) -> float:
    a_norm = float(np.linalg.norm(a))
    b_norm = float(np.linalg.norm(b))
    if a_norm <= 1e-12 or b_norm <= 1e-12:
        return float("nan")
    return float(np.dot(a, b) / (a_norm * b_norm))


def outcome(info: dict[str, Any], truncated: bool) -> str:
    if bool(info["insertion_success"]):
        return "success"
    if bool(info["collision"]):
        return "collision"
    if truncated:
        return "timeout"
    return "terminated_failure"


def scalar_info(info: dict[str, Any], key: str, default: float = float("nan")) -> float:
    return float(info.get(key, default))


def run_config(
    args: argparse.Namespace,
    scenario: Scenario,
    tier: ClearanceTier,
    oracle_config: OracleControllerConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    env = make_env(args, scenario, tier)
    model = AGENTS[args.agent].load(args.model, env=env, device=args.device)
    step_rows: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []

    try:
        for episode in range(args.episodes):
            seed = args.seed + episode
            obs, info = env.reset(seed=seed)
            episode_step_rows: list[dict[str, Any]] = []
            episode_return = 0.0
            terminated = False
            truncated = False

            while True:
                policy_action, _ = model.predict(obs, deterministic=True)
                policy_action = np.asarray(policy_action, dtype=np.float64).reshape(3)
                corrective_action = oracle_action(env, info, oracle_config).astype(np.float64)
                correction = corrective_action - policy_action
                tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
                target = np.asarray(info["target_pos"], dtype=np.float64)
                z_above_target = float(tip[2] - target[2])
                dist_xy = float(info["dist_xy"])
                near_hole = dist_xy <= args.near_hole_xy and z_above_target <= args.near_hole_z
                cosine = action_cosine(policy_action, corrective_action)
                opposed = bool(np.isfinite(cosine) and cosine < args.opposition_dot_threshold)

                obs, reward, terminated, truncated, next_info = env.step(policy_action.astype(np.float32))
                episode_return += float(reward)
                row: dict[str, Any] = {
                    "tier": tier.name,
                    "scenario": scenario.name,
                    "scenario_level": scenario.level,
                    "episode": episode,
                    "seed": seed,
                    "step_before": int(info["step_count"]),
                    "step_after": int(next_info["step_count"]),
                    "reward": float(reward),
                    "episode_return": episode_return,
                    "terminated_after": bool(terminated),
                    "truncated_after": bool(truncated),
                    "success_after": bool(next_info["insertion_success"]),
                    "collision_after": bool(next_info["collision"]),
                    "dist_xy": dist_xy,
                    "dist_z": float(info["dist_z"]),
                    "next_dist_xy": float(next_info["dist_xy"]),
                    "next_dist_z": float(next_info["dist_z"]),
                    "z_above_target": z_above_target,
                    "near_hole": bool(near_hole),
                    "policy_norm": float(np.linalg.norm(policy_action)),
                    "policy_xy_norm": float(np.linalg.norm(policy_action[:2])),
                    "oracle_norm": float(np.linalg.norm(corrective_action)),
                    "oracle_xy_norm": float(np.linalg.norm(corrective_action[:2])),
                    "correction_norm": float(np.linalg.norm(correction)),
                    "correction_xy_norm": float(np.linalg.norm(correction[:2])),
                    "action_cosine": cosine,
                    "opposed_actions": opposed,
                    "policy_down_or_oracle_up": bool(policy_action[2] < 0.0 and corrective_action[2] > 0.0),
                    "policy_down_oracle_less_down": bool(policy_action[2] < corrective_action[2]),
                    "hole_half_size": scalar_info(info, "hole_half_size"),
                    "peg_radius": scalar_info(info, "peg_radius"),
                    "hole_clearance": scalar_info(info, "hole_half_size") - scalar_info(info, "peg_radius"),
                    "control_action_scale_multiplier": scalar_info(info, "control_action_scale_multiplier"),
                    "control_action_noise_std": scalar_info(info, "control_action_noise_std"),
                    "control_action_delay": int(info.get("control_action_delay", -1)),
                    "control_action_filter_alpha": scalar_info(info, "control_action_filter_alpha"),
                }
                row.update(vector_fields("target", target))
                row.update(vector_fields("peg_tip", tip))
                row.update(vector_fields("policy_action", policy_action))
                row.update(vector_fields("oracle_action", corrective_action))
                row.update(vector_fields("correction", correction))
                episode_step_rows.append(row)
                info = next_info

                if terminated or truncated:
                    break

            episode_outcome = outcome(info, truncated)
            final_step = int(info["step_count"])
            for row in episode_step_rows:
                row["episode_outcome"] = episode_outcome
                row["episode_success"] = bool(info["insertion_success"])
                row["episode_collision"] = bool(info["collision"])
                row["episode_timeout"] = bool(truncated and not info["insertion_success"])
                row["final_step"] = final_step
                row["steps_to_end"] = final_step - int(row["step_after"])
                row["failure_window"] = bool(
                    not info["insertion_success"]
                    and row["steps_to_end"] < args.failure_window_steps
                )

            step_rows.extend(episode_step_rows)
            episode_rows.append(summarize_episode(tier, scenario, episode, seed, info, truncated, episode_return, episode_step_rows))
    finally:
        env.close()

    return step_rows, episode_rows


def mean_value(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return float("nan")
    values = np.asarray([float(row[key]) for row in rows], dtype=np.float64)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return float("nan")
    return float(np.mean(finite))


def rate_value(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return float("nan")
    return float(np.mean([bool(row[key]) for row in rows]))


def summarize_episode(
    tier: ClearanceTier,
    scenario: Scenario,
    episode: int,
    seed: int,
    info: dict[str, Any],
    truncated: bool,
    episode_return: float,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    near_rows = [row for row in rows if row["near_hole"]]
    failure_window_rows = [row for row in rows if row["failure_window"]]
    return {
        "tier": tier.name,
        "scenario": scenario.name,
        "scenario_level": scenario.level,
        "episode": episode,
        "seed": seed,
        "outcome": outcome(info, truncated),
        "success": bool(info["insertion_success"]),
        "collision": bool(info["collision"]),
        "timeout": bool(truncated and not info["insertion_success"]),
        "steps": int(info["step_count"]),
        "episode_return": float(episode_return),
        "final_dist_xy": float(info["dist_xy"]),
        "final_dist_z": float(info["dist_z"]),
        "min_dist_xy": min(float(row["dist_xy"]) for row in rows),
        "mean_correction_norm": mean_value(rows, "correction_norm"),
        "mean_near_correction_norm": mean_value(near_rows, "correction_norm"),
        "mean_failure_window_correction_norm": mean_value(failure_window_rows, "correction_norm"),
        "near_hole_step_rate": rate_value(rows, "near_hole"),
        "opposed_action_rate": rate_value(rows, "opposed_actions"),
        "failure_window_opposed_action_rate": rate_value(failure_window_rows, "opposed_actions"),
        "failure_window_policy_down_or_oracle_up_rate": rate_value(
            failure_window_rows,
            "policy_down_or_oracle_up",
        ),
        "control_action_scale_multiplier": scalar_info(info, "control_action_scale_multiplier"),
        "control_action_noise_std": scalar_info(info, "control_action_noise_std"),
        "control_action_delay": int(info.get("control_action_delay", -1)),
        "control_action_filter_alpha": scalar_info(info, "control_action_filter_alpha"),
        "hole_half_size": scalar_info(info, "hole_half_size"),
        "peg_radius": scalar_info(info, "peg_radius"),
        "hole_clearance": scalar_info(info, "hole_half_size") - scalar_info(info, "peg_radius"),
    }


def summarize_group(rows: list[dict[str, Any]], tier: str, scenario: str) -> dict[str, Any]:
    selected = [row for row in rows if row["tier"] == tier and row["scenario"] == scenario]
    failures = [row for row in selected if not row["success"]]
    return {
        "tier": tier,
        "scenario": scenario,
        "episodes": len(selected),
        "success_rate": rate_value(selected, "success"),
        "collision_rate": rate_value(selected, "collision"),
        "timeout_rate": rate_value(selected, "timeout"),
        "mean_steps": mean_value(selected, "steps"),
        "mean_final_dist_xy": mean_value(selected, "final_dist_xy"),
        "mean_clearance_mm": 1000.0 * mean_value(selected, "hole_clearance"),
        "mean_correction_norm": mean_value(selected, "mean_correction_norm"),
        "mean_near_correction_norm": mean_value(selected, "mean_near_correction_norm"),
        "mean_failure_window_correction_norm": mean_value(
            failures,
            "mean_failure_window_correction_norm",
        ),
        "failure_opposed_action_rate": mean_value(failures, "failure_window_opposed_action_rate"),
        "failure_policy_down_or_oracle_up_rate": mean_value(
            failures,
            "failure_window_policy_down_or_oracle_up_rate",
        ),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved CSV report to {path}")


def fmt(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if np.isnan(number):
        return "nan"
    return f"{number:.3f}"


def write_markdown(
    path: Path,
    args: argparse.Namespace,
    step_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tiers = list(dict.fromkeys(row["tier"] for row in episode_rows))
    scenarios = list(dict.fromkeys(row["scenario"] for row in episode_rows))
    group_rows = [
        summarize_group(episode_rows, tier, scenario)
        for tier in tiers
        for scenario in scenarios
        if any(row["tier"] == tier and row["scenario"] == scenario for row in episode_rows)
    ]
    failure_steps = [row for row in step_rows if row["failure_window"]]
    top_failure_steps = sorted(
        failure_steps,
        key=lambda row: float(row["correction_norm"]),
        reverse=True,
    )[:12]

    lines = [
        "# Policy vs Oracle Correction Analysis",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Episodes per tier/scenario: `{args.episodes}`",
        f"- Scenario preset: `{args.scenario_preset}`",
        f"- Tier preset: `{args.tier_preset}`",
        f"- Failure window steps: `{args.failure_window_steps}`",
        f"- Near-hole window: `xy<={args.near_hole_xy}`, `z_above_target<={args.near_hole_z}`",
        "",
        "## Summary",
        "",
        "| Tier | Scenario | Episodes | Success | Collision | Mean steps | Mean clearance | Mean corr | Near corr | Failure corr | Failure opposed | Failure policy down / oracle up |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in group_rows:
        lines.append(
            "| {tier} | {scenario} | {episodes} | {success_rate} | {collision_rate} | "
            "{mean_steps} | {mean_clearance_mm} mm | {mean_correction_norm} | "
            "{mean_near_correction_norm} | {mean_failure_window_correction_norm} | "
            "{failure_opposed_action_rate} | {failure_policy_down_or_oracle_up_rate} |".format(
                tier=row["tier"],
                scenario=row["scenario"],
                episodes=row["episodes"],
                success_rate=fmt(row["success_rate"]),
                collision_rate=fmt(row["collision_rate"]),
                mean_steps=fmt(row["mean_steps"]),
                mean_clearance_mm=fmt(row["mean_clearance_mm"]),
                mean_correction_norm=fmt(row["mean_correction_norm"]),
                mean_near_correction_norm=fmt(row["mean_near_correction_norm"]),
                mean_failure_window_correction_norm=fmt(row["mean_failure_window_correction_norm"]),
                failure_opposed_action_rate=fmt(row["failure_opposed_action_rate"]),
                failure_policy_down_or_oracle_up_rate=fmt(row["failure_policy_down_or_oracle_up_rate"]),
            )
        )

    lines.extend(
        [
            "",
            "## Largest Failure-Window Corrections",
            "",
            "| Tier | Scenario | Episode | Step | Outcome | Dist XY | Z above target | Policy z | Oracle z | Correction norm | Cosine |",
            "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in top_failure_steps:
        lines.append(
            "| {tier} | {scenario} | {episode} | {step} | {outcome} | {dist_xy} | "
            "{z_above} | {policy_z} | {oracle_z} | {correction} | {cosine} |".format(
                tier=row["tier"],
                scenario=row["scenario"],
                episode=row["episode"],
                step=row["step_after"],
                outcome=row["episode_outcome"],
                dist_xy=fmt(row["dist_xy"]),
                z_above=fmt(row["z_above_target"]),
                policy_z=fmt(row["policy_action_z"]),
                oracle_z=fmt(row["oracle_action_z"]),
                correction=fmt(row["correction_norm"]),
                cosine=fmt(row["action_cosine"]),
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The step CSV is the primary artifact for corrective-data collection. Rows with "
            "`failure_window=True`, high `correction_norm`, and `near_hole=True` are the "
            "first candidates for DAgger-style relabeling because they show states that "
            "the learned policy actually visits shortly before collision or timeout.",
            "",
            "If `failure_policy_down_or_oracle_up_rate` is high, the policy is descending "
            "while the guarded oracle would retract or slow insertion. If "
            "`failure_opposed_action_rate` is high, the XY/Z action direction is often "
            "opposite to the corrective action, which indicates that success-only BC is "
            "missing recovery examples rather than only needing more samples.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved Markdown report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")
    if args.failure_window_steps <= 0:
        raise ValueError("--failure-window-steps must be positive.")

    oracle_config = make_oracle_config(args)
    all_step_rows: list[dict[str, Any]] = []
    all_episode_rows: list[dict[str, Any]] = []
    for tier in tiers_for_args(args):
        for scenario in scenarios_for_args(args):
            step_rows, episode_rows = run_config(args, scenario, tier, oracle_config)
            all_step_rows.extend(step_rows)
            all_episode_rows.extend(episode_rows)
            group = summarize_group(episode_rows, tier.name, scenario.name)
            print(
                "{tier} / {scenario}: success={success:.3f} collision={collision:.3f} "
                "failure_corr={failure_corr:.5f} opposed={opposed:.3f}".format(
                    tier=tier.name,
                    scenario=scenario.name,
                    success=group["success_rate"],
                    collision=group["collision_rate"],
                    failure_corr=group["mean_failure_window_correction_norm"],
                    opposed=group["failure_opposed_action_rate"],
                )
            )

    write_csv(args.output_csv, all_step_rows)
    write_csv(args.episode_output_csv, all_episode_rows)
    write_markdown(args.output_md, args, all_step_rows, all_episode_rows)


if __name__ == "__main__":
    main()
