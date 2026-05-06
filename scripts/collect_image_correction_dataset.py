from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import A2C, PPO, SAC

from peg_in_hole_mujoco import OracleControllerConfig, PegInHoleMujocoEnv, oracle_action


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
    "wide_current": ClearanceTier("wide_current", (0.025, 0.029), (0.0115, 0.0125)),
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


SCALAR_DIAGNOSTIC_KEYS = (
    "hole_half_size",
    "peg_radius",
    "hole_clearance",
    "control_action_scale_multiplier",
    "control_action_noise_std",
    "control_action_delay",
    "control_action_filter_alpha",
    "fixture_height_offset",
    "table_height_offset",
    "contact_friction_multiplier",
    "contact_solref_time_multiplier",
    "contact_solref_damping_multiplier",
    "contact_solimp_width_multiplier",
    "joint_damping_multiplier",
    "actuator_kp_multiplier",
)
VECTOR_DIAGNOSTIC_KEYS = ("hole_center_offset",)
DATASET_SCHEMA_VERSION = "image_correction_v1_policy_failure_window"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect image corrective samples from policy-visited failure windows."
    )
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=10_000)
    parser.add_argument("--samples-per-config", type=int, default=None)
    parser.add_argument("--max-episodes-per-config", type=int, default=1000)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=990_000)
    parser.add_argument("--compressed", action="store_true")
    parser.add_argument(
        "--scenario-preset",
        choices=["geometry", "hard", "targeted", "contact"],
        default="targeted",
    )
    parser.add_argument(
        "--tier-preset",
        choices=["wide", "medium", "wide_medium", "all"],
        default="medium",
    )
    parser.add_argument(
        "--selection",
        choices=[
            "failure_window",
            "near_hole_failure_window",
            "failed_episode_near_hole",
            "failed_episode_all",
        ],
        default="failure_window",
    )
    parser.add_argument(
        "--episode-outcome-filter",
        choices=["any", "collision", "timeout", "terminated_failure"],
        default="any",
        help="Keep corrective samples only from episodes with this final outcome.",
    )
    parser.add_argument("--failure-window-steps", type=int, default=8)
    parser.add_argument("--near-hole-xy", type=float, default=0.03)
    parser.add_argument("--near-hole-z", type=float, default=0.10)
    parser.add_argument("--min-correction-norm", type=float, default=0.004)
    parser.add_argument("--max-samples-per-episode", type=int, default=8)
    parser.add_argument("--image-width", type=int, default=100)
    parser.add_argument("--image-height", type=int, default=100)
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
        return [CLEARANCE_TIERS["wide_current"]]
    if args.tier_preset == "medium":
        return [CLEARANCE_TIERS["medium"]]
    if args.tier_preset == "wide_medium":
        return [CLEARANCE_TIERS["wide_current"], CLEARANCE_TIERS["medium"]]
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
        observation_mode="image",
        image_width=args.image_width,
        image_height=args.image_height,
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


def action_cosine(a: np.ndarray, b: np.ndarray) -> float:
    a_norm = float(np.linalg.norm(a))
    b_norm = float(np.linalg.norm(b))
    if a_norm <= 1e-12 or b_norm <= 1e-12:
        return float("nan")
    return float(np.dot(a, b) / (a_norm * b_norm))


def read_diagnostics(info: dict[str, Any]) -> dict[str, float | np.ndarray]:
    hole_half_size = float(info.get("hole_half_size", np.nan))
    peg_radius = float(info.get("peg_radius", np.nan))
    hole_center_offset = np.asarray(
        info.get("hole_center_offset", [np.nan, np.nan]),
        dtype=np.float32,
    )
    if hole_center_offset.shape != (2,):
        hole_center_offset = np.full(2, np.nan, dtype=np.float32)
    return {
        "hole_half_size": hole_half_size,
        "peg_radius": peg_radius,
        "hole_clearance": hole_half_size - peg_radius,
        "control_action_scale_multiplier": float(
            info.get("control_action_scale_multiplier", np.nan)
        ),
        "control_action_noise_std": float(info.get("control_action_noise_std", np.nan)),
        "control_action_delay": float(info.get("control_action_delay", -1)),
        "control_action_filter_alpha": float(info.get("control_action_filter_alpha", np.nan)),
        "fixture_height_offset": float(info.get("fixture_height_offset", np.nan)),
        "table_height_offset": float(info.get("table_height_offset", np.nan)),
        "contact_friction_multiplier": float(info.get("contact_friction_multiplier", np.nan)),
        "contact_solref_time_multiplier": float(info.get("contact_solref_time_multiplier", np.nan)),
        "contact_solref_damping_multiplier": float(
            info.get("contact_solref_damping_multiplier", np.nan)
        ),
        "contact_solimp_width_multiplier": float(
            info.get("contact_solimp_width_multiplier", np.nan)
        ),
        "joint_damping_multiplier": float(info.get("joint_damping_multiplier", np.nan)),
        "actuator_kp_multiplier": float(info.get("actuator_kp_multiplier", np.nan)),
        "hole_center_offset": hole_center_offset.astype(np.float32, copy=True),
    }


def outcome(info: dict[str, Any], truncated: bool) -> str:
    if bool(info["insertion_success"]):
        return "success"
    if bool(info["collision"]):
        return "collision"
    if truncated:
        return "timeout"
    return "terminated_failure"


def should_keep_sample(sample: dict[str, Any], args: argparse.Namespace) -> bool:
    if float(sample["correction_norm"]) < args.min_correction_norm:
        return False
    if (
        args.episode_outcome_filter != "any"
        and sample["episode_outcome"] != args.episode_outcome_filter
    ):
        return False
    if args.selection == "failed_episode_all":
        return True
    if args.selection == "failed_episode_near_hole":
        return bool(sample["near_hole"])
    if args.selection == "near_hole_failure_window":
        return bool(sample["failure_window"] and sample["near_hole"])
    return bool(sample["failure_window"])


def run_episode(
    env: PegInHoleMujocoEnv,
    model: Any,
    oracle_config: OracleControllerConfig,
    *,
    args: argparse.Namespace,
    tier: ClearanceTier,
    scenario: Scenario,
    episode_id: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    obs, info = env.reset(seed=seed)
    rows: list[dict[str, Any]] = []
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
        sample = {
            "cam_image": obs["cam_image"].copy(),
            "near_hole_crop": (
                obs["near_hole_crop"].copy() if args.include_near_hole_crop else None
            ),
            "raw_action": corrective_action.astype(np.float32),
            "action": (corrective_action / env.action_scale).astype(np.float32),
            "policy_raw_action": policy_action.astype(np.float32),
            "policy_action": (policy_action / env.action_scale).astype(np.float32),
            "correction_raw_action": correction.astype(np.float32),
            "target_pos": target.astype(np.float32),
            "peg_tip_pos": tip.astype(np.float32),
            "desired_z": float(info["desired_z"]),
            "tier": tier.name,
            "scenario": scenario.name,
            "episode_id": episode_id,
            "seed": seed,
            "step_id": int(info["step_count"]),
            "dist_xy": dist_xy,
            "dist_z": float(info["dist_z"]),
            "z_above_target": z_above_target,
            "near_hole": bool(near_hole),
            "policy_norm": float(np.linalg.norm(policy_action)),
            "oracle_norm": float(np.linalg.norm(corrective_action)),
            "correction_norm": float(np.linalg.norm(correction)),
            "correction_xy_norm": float(np.linalg.norm(correction[:2])),
            "action_cosine": action_cosine(policy_action, corrective_action),
            "opposed_actions": bool(action_cosine(policy_action, corrective_action) < 0.0),
            "policy_down_or_oracle_up": bool(policy_action[2] < 0.0 and corrective_action[2] > 0.0),
            "policy_down_oracle_less_down": bool(policy_action[2] < corrective_action[2]),
            "diagnostics": read_diagnostics(info),
        }
        rows.append(sample)

        obs, reward, terminated, truncated, info = env.step(policy_action.astype(np.float32))
        episode_return += float(reward)
        if terminated or truncated:
            break

    final_step = int(info["step_count"])
    episode_outcome = outcome(info, truncated)
    for sample in rows:
        sample["episode_outcome"] = episode_outcome
        sample["episode_success"] = bool(info["insertion_success"])
        sample["episode_collision"] = bool(info["collision"])
        sample["episode_timeout"] = bool(truncated and not info["insertion_success"])
        sample["final_step"] = final_step
        sample["steps_to_end"] = final_step - int(sample["step_id"])
        sample["failure_window"] = bool(
            not info["insertion_success"]
            and int(sample["steps_to_end"]) <= args.failure_window_steps
        )

    episode_summary = {
        "tier": tier.name,
        "scenario": scenario.name,
        "episode_id": episode_id,
        "seed": seed,
        "outcome": episode_outcome,
        "success": bool(info["insertion_success"]),
        "collision": bool(info["collision"]),
        "timeout": bool(truncated and not info["insertion_success"]),
        "steps": final_step,
        "episode_return": float(episode_return),
        "final_dist_xy": float(info["dist_xy"]),
        "final_dist_z": float(info["dist_z"]),
        "hole_clearance": float(info.get("hole_half_size", np.nan) - info.get("peg_radius", np.nan)),
    }
    return rows, episode_summary


def select_episode_samples(rows: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    if rows and rows[-1]["episode_success"]:
        return []
    candidates = [sample for sample in rows if should_keep_sample(sample, args)]
    candidates.sort(key=lambda item: float(item["correction_norm"]), reverse=True)
    return candidates[: args.max_samples_per_episode]


def append_samples(
    buffers: dict[str, list[Any]],
    selected: list[dict[str, Any]],
    remaining: int,
) -> int:
    keep = min(remaining, len(selected))
    for sample in selected[:keep]:
        buffers["cam_images"].append(sample["cam_image"])
        if sample["near_hole_crop"] is not None:
            buffers["near_hole_crops"].append(sample["near_hole_crop"])
        for key in (
            "action",
            "raw_action",
            "policy_action",
            "policy_raw_action",
            "correction_raw_action",
            "target_pos",
            "peg_tip_pos",
        ):
            buffers[key].append(sample[key])
        for key in (
            "desired_z",
            "episode_id",
            "seed",
            "step_id",
            "dist_xy",
            "dist_z",
            "z_above_target",
            "near_hole",
            "policy_norm",
            "oracle_norm",
            "correction_norm",
            "correction_xy_norm",
            "action_cosine",
            "opposed_actions",
            "policy_down_or_oracle_up",
            "policy_down_oracle_less_down",
            "final_step",
            "steps_to_end",
            "failure_window",
            "episode_success",
            "episode_collision",
            "episode_timeout",
        ):
            buffers[key].append(sample[key])
        buffers["tier"].append(sample["tier"])
        buffers["scenario"].append(sample["scenario"])
        buffers["episode_outcome"].append(sample["episode_outcome"])
        for key, value in sample["diagnostics"].items():
            buffers[key].append(value)
    return keep


def empty_buffers() -> dict[str, list[Any]]:
    keys = [
        "cam_images",
        "near_hole_crops",
        "action",
        "raw_action",
        "policy_action",
        "policy_raw_action",
        "correction_raw_action",
        "target_pos",
        "peg_tip_pos",
        "desired_z",
        "episode_id",
        "seed",
        "step_id",
        "dist_xy",
        "dist_z",
        "z_above_target",
        "near_hole",
        "policy_norm",
        "oracle_norm",
        "correction_norm",
        "correction_xy_norm",
        "action_cosine",
        "opposed_actions",
        "policy_down_or_oracle_up",
        "policy_down_oracle_less_down",
        "final_step",
        "steps_to_end",
        "failure_window",
        "episode_success",
        "episode_collision",
        "episode_timeout",
        "tier",
        "scenario",
        "episode_outcome",
        *SCALAR_DIAGNOSTIC_KEYS,
        *VECTOR_DIAGNOSTIC_KEYS,
    ]
    return {key: [] for key in keys}


def summarize_float_array(values: np.ndarray) -> dict[str, float]:
    if values.size == 0:
        return {"mean": float("nan"), "min": float("nan"), "max": float("nan")}
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {"mean": float("nan"), "min": float("nan"), "max": float("nan")}
    return {
        "mean": float(np.mean(finite)),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
    }


def build_arrays(buffers: dict[str, list[Any]], include_near_hole_crop: bool) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {
        "cam_images": np.asarray(buffers["cam_images"], dtype=np.uint8),
        "actions": np.asarray(buffers["action"], dtype=np.float32),
        "raw_actions": np.asarray(buffers["raw_action"], dtype=np.float32),
        "policy_actions": np.asarray(buffers["policy_action"], dtype=np.float32),
        "policy_raw_actions": np.asarray(buffers["policy_raw_action"], dtype=np.float32),
        "correction_raw_actions": np.asarray(buffers["correction_raw_action"], dtype=np.float32),
        "target_pos": np.asarray(buffers["target_pos"], dtype=np.float32),
        "peg_tip_pos": np.asarray(buffers["peg_tip_pos"], dtype=np.float32),
        "desired_z": np.asarray(buffers["desired_z"], dtype=np.float32),
        "episode_id": np.asarray(buffers["episode_id"], dtype=np.int32),
        "seed": np.asarray(buffers["seed"], dtype=np.int32),
        "step_id": np.asarray(buffers["step_id"], dtype=np.int32),
        "dist_xy": np.asarray(buffers["dist_xy"], dtype=np.float32),
        "dist_z": np.asarray(buffers["dist_z"], dtype=np.float32),
        "z_above_target": np.asarray(buffers["z_above_target"], dtype=np.float32),
        "near_hole": np.asarray(buffers["near_hole"], dtype=np.bool_),
        "policy_norm": np.asarray(buffers["policy_norm"], dtype=np.float32),
        "oracle_norm": np.asarray(buffers["oracle_norm"], dtype=np.float32),
        "correction_norm": np.asarray(buffers["correction_norm"], dtype=np.float32),
        "correction_xy_norm": np.asarray(buffers["correction_xy_norm"], dtype=np.float32),
        "action_cosine": np.asarray(buffers["action_cosine"], dtype=np.float32),
        "opposed_actions": np.asarray(buffers["opposed_actions"], dtype=np.bool_),
        "policy_down_or_oracle_up": np.asarray(buffers["policy_down_or_oracle_up"], dtype=np.bool_),
        "policy_down_oracle_less_down": np.asarray(
            buffers["policy_down_oracle_less_down"],
            dtype=np.bool_,
        ),
        "final_step": np.asarray(buffers["final_step"], dtype=np.int32),
        "steps_to_end": np.asarray(buffers["steps_to_end"], dtype=np.int32),
        "failure_window": np.asarray(buffers["failure_window"], dtype=np.bool_),
        "episode_success": np.asarray(buffers["episode_success"], dtype=np.bool_),
        "episode_collision": np.asarray(buffers["episode_collision"], dtype=np.bool_),
        "episode_timeout": np.asarray(buffers["episode_timeout"], dtype=np.bool_),
        "tier": np.asarray(buffers["tier"]),
        "scenario": np.asarray(buffers["scenario"]),
        "episode_outcome": np.asarray(buffers["episode_outcome"]),
    }
    if include_near_hole_crop:
        arrays["near_hole_crops"] = np.asarray(buffers["near_hole_crops"], dtype=np.uint8)
    for key in SCALAR_DIAGNOSTIC_KEYS:
        dtype = np.int32 if key == "control_action_delay" else np.float32
        arrays[key] = np.asarray(buffers[key], dtype=dtype)
    for key in VECTOR_DIAGNOSTIC_KEYS:
        arrays[key] = np.asarray(buffers[key], dtype=np.float32)
    return arrays


def array_metadata(arrays: dict[str, np.ndarray]) -> dict[str, dict[str, object]]:
    return {
        key: {"shape": list(value.shape), "dtype": str(value.dtype)}
        for key, value in sorted(arrays.items())
    }


def main() -> None:
    args = parse_args()
    if args.samples <= 0:
        raise ValueError("--samples must be positive.")
    if args.max_samples_per_episode <= 0:
        raise ValueError("--max-samples-per-episode must be positive.")
    if args.failure_window_steps <= 0:
        raise ValueError("--failure-window-steps must be positive.")

    configs = [(tier, scenario) for tier in tiers_for_args(args) for scenario in scenarios_for_args(args)]
    target_per_config = (
        args.samples_per_config
        if args.samples_per_config is not None
        else int(np.ceil(args.samples / len(configs)))
    )
    oracle_config = make_oracle_config(args)
    buffers = empty_buffers()
    episode_summaries: list[dict[str, Any]] = []
    config_summaries: list[dict[str, Any]] = []
    global_episode_id = 0

    for config_index, (tier, scenario) in enumerate(configs):
        env = make_env(args, scenario, tier)
        model = AGENTS[args.agent].load(args.model, env=env, device=args.device)
        config_samples = 0
        config_episodes = 0
        config_successes = 0
        config_collisions = 0
        config_timeouts = 0
        try:
            while (
                config_samples < target_per_config
                and config_episodes < args.max_episodes_per_config
                and len(buffers["cam_images"]) < args.samples
            ):
                seed = args.seed + config_index * args.max_episodes_per_config + config_episodes
                episode_rows, episode_summary = run_episode(
                    env,
                    model,
                    oracle_config,
                    args=args,
                    tier=tier,
                    scenario=scenario,
                    episode_id=global_episode_id,
                    seed=seed,
                )
                global_episode_id += 1
                config_episodes += 1
                config_successes += int(episode_summary["success"])
                config_collisions += int(episode_summary["collision"])
                config_timeouts += int(episode_summary["timeout"])
                episode_summaries.append(episode_summary)
                selected = select_episode_samples(episode_rows, args)
                kept = append_samples(
                    buffers,
                    selected,
                    min(args.samples - len(buffers["cam_images"]), target_per_config - config_samples),
                )
                config_samples += kept
        finally:
            env.close()

        config_summaries.append(
            {
                "tier": tier.name,
                "scenario": scenario.name,
                "episodes_completed": config_episodes,
                "samples": config_samples,
                "success_rate": config_successes / max(config_episodes, 1),
                "collision_rate": config_collisions / max(config_episodes, 1),
                "timeout_rate": config_timeouts / max(config_episodes, 1),
            }
        )
        print(
            "{tier}/{scenario}: samples={samples} episodes={episodes} "
            "success={success:.3f} collision={collision:.3f}".format(
                tier=tier.name,
                scenario=scenario.name,
                samples=config_samples,
                episodes=config_episodes,
                success=config_summaries[-1]["success_rate"],
                collision=config_summaries[-1]["collision_rate"],
            )
        )

    arrays = build_arrays(buffers, args.include_near_hole_crop)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.compressed:
        np.savez_compressed(args.output, **arrays)
    else:
        np.savez(args.output, **arrays)

    metadata = {
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "samples": int(arrays["actions"].shape[0]),
        "model": str(args.model),
        "model_path": str(args.model_path) if args.model_path is not None else "default",
        "scenario_preset": args.scenario_preset,
        "tier_preset": args.tier_preset,
        "selection": args.selection,
        "episode_outcome_filter": args.episode_outcome_filter,
        "failure_window_steps": args.failure_window_steps,
        "near_hole_xy": args.near_hole_xy,
        "near_hole_z": args.near_hole_z,
        "min_correction_norm": args.min_correction_norm,
        "max_samples_per_episode": args.max_samples_per_episode,
        "samples_per_config": target_per_config,
        "max_episodes_per_config": args.max_episodes_per_config,
        "episodes_completed": len(episode_summaries),
        "config_summaries": config_summaries,
        "image_width": args.image_width,
        "image_height": args.image_height,
        "include_near_hole_crop": args.include_near_hole_crop,
        "near_hole_crop_size": args.near_hole_crop_size,
        "success_xy_tolerance": args.success_xy_tolerance,
        "success_z_tolerance": args.success_z_tolerance,
        "approach_xy_tolerance": args.approach_xy_tolerance,
        "oracle_mode": "guarded_two_stage",
        "oracle_action_gain": args.oracle_action_gain,
        "array_metadata": array_metadata(arrays),
        "diagnostics": {
            "correction_norm": summarize_float_array(arrays["correction_norm"]),
            "action_cosine": summarize_float_array(arrays["action_cosine"]),
            "hole_clearance": summarize_float_array(arrays["hole_clearance"]),
            "control_action_delay": summarize_float_array(
                arrays["control_action_delay"].astype(np.float32)
            ),
            "control_action_filter_alpha": summarize_float_array(
                arrays["control_action_filter_alpha"]
            ),
            "near_hole_rate": float(np.mean(arrays["near_hole"])) if arrays["near_hole"].size else 0.0,
            "opposed_action_rate": float(np.mean(arrays["opposed_actions"]))
            if arrays["opposed_actions"].size
            else 0.0,
            "policy_down_or_oracle_up_rate": float(
                np.mean(arrays["policy_down_or_oracle_up"])
            )
            if arrays["policy_down_or_oracle_up"].size
            else 0.0,
        },
    }
    metadata_path = args.output.with_suffix(args.output.suffix + ".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved correction dataset to {args.output}")
    print(f"saved metadata to {metadata_path}")
    print(f"samples={arrays['actions'].shape[0]} episodes_completed={len(episode_summaries)}")


if __name__ == "__main__":
    main()
