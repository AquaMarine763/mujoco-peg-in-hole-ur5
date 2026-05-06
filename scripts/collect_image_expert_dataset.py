from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from stable_baselines3 import SAC

from peg_in_hole_mujoco import OracleControllerConfig, PegInHoleMujocoEnv, oracle_action


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
DATASET_SCHEMA_VERSION = "image_expert_v2_diagnostics"


def new_diagnostic_buffers() -> dict[str, list[float | np.ndarray]]:
    return {key: [] for key in (*SCALAR_DIAGNOSTIC_KEYS, *VECTOR_DIAGNOSTIC_KEYS)}


def read_sample_diagnostics(info: dict) -> dict[str, float | np.ndarray]:
    hole_half_size = float(info.get("hole_half_size", np.nan))
    peg_radius = float(info.get("peg_radius", np.nan))
    if np.isfinite(hole_half_size) and np.isfinite(peg_radius):
        hole_clearance = hole_half_size - peg_radius
    else:
        hole_clearance = np.nan

    hole_center_offset = np.asarray(
        info.get("hole_center_offset", [np.nan, np.nan]),
        dtype=np.float32,
    )
    if hole_center_offset.shape != (2,):
        hole_center_offset = np.full(2, np.nan, dtype=np.float32)

    return {
        "hole_half_size": hole_half_size,
        "peg_radius": peg_radius,
        "hole_clearance": float(hole_clearance),
        "control_action_scale_multiplier": float(
            info.get("control_action_scale_multiplier", np.nan)
        ),
        "control_action_noise_std": float(info.get("control_action_noise_std", np.nan)),
        "control_action_delay": float(info.get("control_action_delay", -1)),
        "control_action_filter_alpha": float(
            info.get("control_action_filter_alpha", np.nan)
        ),
        "fixture_height_offset": float(info.get("fixture_height_offset", np.nan)),
        "table_height_offset": float(info.get("table_height_offset", np.nan)),
        "contact_friction_multiplier": float(
            info.get("contact_friction_multiplier", np.nan)
        ),
        "contact_solref_time_multiplier": float(
            info.get("contact_solref_time_multiplier", np.nan)
        ),
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


def append_diagnostics(
    buffers: dict[str, list[float | np.ndarray]],
    sample: dict[str, float | np.ndarray],
) -> None:
    for key, value in sample.items():
        buffers[key].append(value)


def extend_diagnostics(
    destination: dict[str, list[float | np.ndarray]],
    source: dict[str, list[float | np.ndarray]],
    keep: int,
) -> None:
    for key in destination:
        destination[key].extend(source[key][:keep])


def add_diagnostic_arrays(
    arrays: dict[str, np.ndarray],
    diagnostics: dict[str, list[float | np.ndarray]],
) -> None:
    for key in SCALAR_DIAGNOSTIC_KEYS:
        dtype = np.int32 if key == "control_action_delay" else np.float32
        arrays[key] = np.asarray(diagnostics[key], dtype=dtype)
    for key in VECTOR_DIAGNOSTIC_KEYS:
        arrays[key] = np.asarray(diagnostics[key], dtype=np.float32)


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


def array_metadata(arrays: dict[str, np.ndarray]) -> dict[str, dict[str, object]]:
    return {
        key: {"shape": list(value.shape), "dtype": str(value.dtype)}
        for key, value in sorted(arrays.items())
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect wrist-camera images with expert Cartesian actions.")
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=50_000)
    parser.add_argument("--expert-model", type=Path, default=None)
    parser.add_argument("--expert-action-gain", type=float, default=1.0)
    parser.add_argument("--oracle-mode", choices=["staged", "guarded_two_stage"], default="staged")
    parser.add_argument("--guarded-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.005)
    parser.add_argument("--guarded-max-down-action", type=float, default=0.0035)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.005)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)
    parser.add_argument("--rollout-noise-std", type=float, default=0.0005)
    parser.add_argument("--seed", type=int, default=30_000)
    parser.add_argument(
        "--success-only",
        action="store_true",
        help="Keep samples only from episodes that terminate with insertion success.",
    )
    parser.add_argument("--compressed", action="store_true")
    parser.add_argument("--domain-randomization", action="store_true")
    parser.add_argument(
        "--domain-randomization-level",
        choices=["none", "visual", "visual_camera", "visual_camera_control", "full_light_geometry", "full_contact_light", "full"],
        default="none",
    )
    parser.add_argument("--image-width", type=int, default=100)
    parser.add_argument("--image-height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--control-action-scale-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument(
        "--control-action-noise-std-range",
        nargs=2,
        type=float,
        default=(0.0, 0.0008),
    )
    parser.add_argument("--control-action-delay-range", nargs=2, type=int, default=(0, 2))
    parser.add_argument(
        "--control-action-filter-alpha-range",
        nargs=2,
        type=float,
        default=(0.55, 1.0),
    )
    parser.add_argument("--geometry-hole-center-xy-jitter", nargs=2, type=float, default=(0.002, 0.002))
    parser.add_argument("--geometry-fixture-height-jitter", type=float, default=0.001)
    parser.add_argument("--geometry-table-height-jitter", type=float, default=0.001)
    parser.add_argument("--geometry-hole-half-size-range", nargs=2, type=float, default=(0.025, 0.029))
    parser.add_argument("--geometry-peg-radius-range", nargs=2, type=float, default=(0.0115, 0.0125))
    parser.add_argument("--contact-friction-multiplier-range", nargs=2, type=float, default=(0.7, 1.3))
    parser.add_argument("--contact-solref-time-multiplier-range", nargs=2, type=float, default=(0.8, 1.25))
    parser.add_argument("--contact-solref-damping-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--contact-solimp-width-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--dynamics-joint-damping-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--dynamics-actuator-kp-multiplier-range", nargs=2, type=float, default=(0.8, 1.2))
    parser.add_argument("--target-low", nargs=3, type=float, default=(0.50, 0.00, 0.65))
    parser.add_argument("--target-high", nargs=3, type=float, default=(0.60, 0.10, 0.65))
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
        observation_mode="image",
        image_width=args.image_width,
        image_height=args.image_height,
        include_near_hole_crop=args.include_near_hole_crop,
        near_hole_crop_size=args.near_hole_crop_size,
        max_steps=args.max_steps,
        action_scale=args.action_scale,
        target_low=tuple(args.target_low),
        target_high=tuple(args.target_high),
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
        randomize_domain=args.domain_randomization,
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
        contact_friction_multiplier_range=tuple(args.contact_friction_multiplier_range),
        contact_solref_time_multiplier_range=tuple(args.contact_solref_time_multiplier_range),
        contact_solref_damping_multiplier_range=tuple(args.contact_solref_damping_multiplier_range),
        contact_solimp_width_multiplier_range=tuple(args.contact_solimp_width_multiplier_range),
        dynamics_joint_damping_multiplier_range=tuple(args.dynamics_joint_damping_multiplier_range),
        dynamics_actuator_kp_multiplier_range=tuple(args.dynamics_actuator_kp_multiplier_range),
    )

def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    env = make_env(args)
    expert = SAC.load(args.expert_model, device="cpu") if args.expert_model is not None else None
    oracle_config = OracleControllerConfig(
        mode=args.oracle_mode,
        action_gain=args.expert_action_gain,
        guarded_align_xy_tolerance=args.guarded_align_xy_tolerance,
        guarded_insert_xy_tolerance=args.guarded_insert_xy_tolerance,
        guarded_retract_xy_tolerance=args.guarded_retract_xy_tolerance,
        guarded_preinsert_height=args.guarded_preinsert_height,
        guarded_max_xy_action=args.guarded_max_xy_action,
        guarded_max_down_action=args.guarded_max_down_action,
        guarded_max_up_action=args.guarded_max_up_action,
        guarded_prediction_steps=args.guarded_prediction_steps,
    )

    images: list[np.ndarray] = []
    near_hole_crops: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    raw_actions: list[np.ndarray] = []
    target_positions: list[np.ndarray] = []
    peg_tip_positions: list[np.ndarray] = []
    desired_zs: list[float] = []
    episode_ids: list[int] = []
    step_ids: list[int] = []
    diagnostics = new_diagnostic_buffers()
    successes = 0
    collisions = 0
    timeouts = 0
    episodes = 0
    episodes_kept = 0
    episode_images: list[np.ndarray] = []
    episode_near_hole_crops: list[np.ndarray] = []
    episode_actions: list[np.ndarray] = []
    episode_raw_actions: list[np.ndarray] = []
    episode_target_positions: list[np.ndarray] = []
    episode_peg_tip_positions: list[np.ndarray] = []
    episode_desired_zs: list[float] = []
    episode_ids_buffer: list[int] = []
    episode_step_ids: list[int] = []
    episode_diagnostics = new_diagnostic_buffers()

    obs, info = env.reset(seed=args.seed)
    try:
        while len(images) < args.samples:
            if expert is None:
                action = oracle_action(env, info, oracle_config)
            else:
                state_obs = env._get_state_obs()
                action, _ = expert.predict(state_obs, deterministic=True)
                action = np.asarray(action, dtype=np.float32)

            sample_image = obs["cam_image"].copy()
            sample_near_hole_crop = (
                obs["near_hole_crop"].copy() if args.include_near_hole_crop else None
            )
            sample_raw_action = action.copy()
            sample_action = (action / env.action_scale).astype(np.float32)
            sample_target_pos = info["target_pos"].copy()
            sample_peg_tip_pos = info["peg_tip_pos"].copy()
            sample_desired_z = float(info["desired_z"])
            sample_episode_id = episodes_kept if args.success_only else episodes
            sample_step_id = int(info["step_count"])
            sample_diagnostics = read_sample_diagnostics(info)

            if args.success_only:
                episode_images.append(sample_image)
                if sample_near_hole_crop is not None:
                    episode_near_hole_crops.append(sample_near_hole_crop)
                episode_raw_actions.append(sample_raw_action)
                episode_actions.append(sample_action)
                episode_target_positions.append(sample_target_pos)
                episode_peg_tip_positions.append(sample_peg_tip_pos)
                episode_desired_zs.append(sample_desired_z)
                episode_ids_buffer.append(sample_episode_id)
                episode_step_ids.append(sample_step_id)
                append_diagnostics(episode_diagnostics, sample_diagnostics)
            else:
                images.append(sample_image)
                if sample_near_hole_crop is not None:
                    near_hole_crops.append(sample_near_hole_crop)
                raw_actions.append(sample_raw_action)
                actions.append(sample_action)
                target_positions.append(sample_target_pos)
                peg_tip_positions.append(sample_peg_tip_pos)
                desired_zs.append(sample_desired_z)
                episode_ids.append(sample_episode_id)
                step_ids.append(sample_step_id)
                append_diagnostics(diagnostics, sample_diagnostics)

            rollout_action = action + rng.normal(0.0, args.rollout_noise_std, size=action.shape)
            rollout_action = np.clip(rollout_action, env.action_space.low, env.action_space.high)
            obs, _, terminated, truncated, info = env.step(rollout_action.astype(np.float32))

            if terminated or truncated:
                success = bool(info["insertion_success"])
                successes += int(success)
                collisions += int(info["collision"])
                timeouts += int(truncated and not success)
                episodes += 1
                if args.success_only and success:
                    keep = min(args.samples - len(images), len(episode_images))
                    images.extend(episode_images[:keep])
                    if args.include_near_hole_crop:
                        near_hole_crops.extend(episode_near_hole_crops[:keep])
                    raw_actions.extend(episode_raw_actions[:keep])
                    actions.extend(episode_actions[:keep])
                    target_positions.extend(episode_target_positions[:keep])
                    peg_tip_positions.extend(episode_peg_tip_positions[:keep])
                    desired_zs.extend(episode_desired_zs[:keep])
                    episode_ids.extend(episode_ids_buffer[:keep])
                    step_ids.extend(episode_step_ids[:keep])
                    extend_diagnostics(diagnostics, episode_diagnostics, keep)
                    episodes_kept += 1
                episode_images = []
                episode_near_hole_crops = []
                episode_actions = []
                episode_raw_actions = []
                episode_target_positions = []
                episode_peg_tip_positions = []
                episode_desired_zs = []
                episode_ids_buffer = []
                episode_step_ids = []
                episode_diagnostics = new_diagnostic_buffers()
                obs, info = env.reset(seed=args.seed + episodes)
    finally:
        env.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    arrays = {
        "cam_images": np.asarray(images, dtype=np.uint8),
        "actions": np.asarray(actions, dtype=np.float32),
        "raw_actions": np.asarray(raw_actions, dtype=np.float32),
        "target_pos": np.asarray(target_positions, dtype=np.float32),
        "peg_tip_pos": np.asarray(peg_tip_positions, dtype=np.float32),
        "desired_z": np.asarray(desired_zs, dtype=np.float32),
        "episode_id": np.asarray(episode_ids, dtype=np.int32),
        "step_id": np.asarray(step_ids, dtype=np.int32),
    }
    if args.include_near_hole_crop:
        arrays["near_hole_crops"] = np.asarray(near_hole_crops, dtype=np.uint8)
    add_diagnostic_arrays(arrays, diagnostics)
    if args.compressed:
        np.savez_compressed(args.output, **arrays)
    else:
        np.savez(args.output, **arrays)

    metadata = {
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "samples": len(images),
        "model_path": str(args.model_path) if args.model_path is not None else "default",
        "episodes_completed": episodes,
        "episodes_kept": episodes_kept if args.success_only else episodes,
        "successes": successes,
        "collisions": collisions,
        "timeouts": timeouts,
        "success_rate": successes / max(episodes, 1),
        "collision_rate": collisions / max(episodes, 1),
        "timeout_rate": timeouts / max(episodes, 1),
        "episodes_kept_rate": (
            (episodes_kept if args.success_only else episodes) / max(episodes, 1)
        ),
        "expert": "oracle" if expert is None else str(args.expert_model),
        "expert_action_gain": args.expert_action_gain,
        "oracle_mode": args.oracle_mode if expert is None else "expert_model",
        "guarded_align_xy_tolerance": args.guarded_align_xy_tolerance,
        "guarded_insert_xy_tolerance": args.guarded_insert_xy_tolerance,
        "guarded_retract_xy_tolerance": args.guarded_retract_xy_tolerance,
        "guarded_preinsert_height": args.guarded_preinsert_height,
        "guarded_max_xy_action": args.guarded_max_xy_action,
        "guarded_max_down_action": args.guarded_max_down_action,
        "guarded_max_up_action": args.guarded_max_up_action,
        "guarded_prediction_steps": args.guarded_prediction_steps,
        "rollout_noise_std": args.rollout_noise_std,
        "success_only": args.success_only,
        "success_xy_tolerance": args.success_xy_tolerance,
        "success_z_tolerance": args.success_z_tolerance,
        "domain_randomization": args.domain_randomization,
        "domain_randomization_level": args.domain_randomization_level,
        "domain_randomization_active": (
            args.domain_randomization or args.domain_randomization_level != "none"
        ),
        "image_width": args.image_width,
        "image_height": args.image_height,
        "include_near_hole_crop": args.include_near_hole_crop,
        "near_hole_crop_size": args.near_hole_crop_size,
        "control_action_scale_range": list(args.control_action_scale_range),
        "control_action_noise_std_range": list(args.control_action_noise_std_range),
        "control_action_delay_range": list(args.control_action_delay_range),
        "control_action_filter_alpha_range": list(args.control_action_filter_alpha_range),
        "geometry_hole_center_xy_jitter": list(args.geometry_hole_center_xy_jitter),
        "geometry_fixture_height_jitter": args.geometry_fixture_height_jitter,
        "geometry_table_height_jitter": args.geometry_table_height_jitter,
        "geometry_hole_half_size_range": list(args.geometry_hole_half_size_range),
        "geometry_peg_radius_range": list(args.geometry_peg_radius_range),
        "contact_friction_multiplier_range": list(args.contact_friction_multiplier_range),
        "contact_solref_time_multiplier_range": list(args.contact_solref_time_multiplier_range),
        "contact_solref_damping_multiplier_range": list(args.contact_solref_damping_multiplier_range),
        "contact_solimp_width_multiplier_range": list(args.contact_solimp_width_multiplier_range),
        "dynamics_joint_damping_multiplier_range": list(args.dynamics_joint_damping_multiplier_range),
        "dynamics_actuator_kp_multiplier_range": list(args.dynamics_actuator_kp_multiplier_range),
        "target_low": list(args.target_low),
        "target_high": list(args.target_high),
        "array_metadata": array_metadata(arrays),
        "diagnostics": {
            "hole_clearance": summarize_float_array(arrays["hole_clearance"]),
            "hole_half_size": summarize_float_array(arrays["hole_half_size"]),
            "peg_radius": summarize_float_array(arrays["peg_radius"]),
            "control_action_scale_multiplier": summarize_float_array(
                arrays["control_action_scale_multiplier"]
            ),
            "control_action_noise_std": summarize_float_array(
                arrays["control_action_noise_std"]
            ),
            "control_action_delay": summarize_float_array(
                arrays["control_action_delay"].astype(np.float32)
            ),
            "control_action_filter_alpha": summarize_float_array(
                arrays["control_action_filter_alpha"]
            ),
        },
    }
    metadata_path = args.output.with_suffix(args.output.suffix + ".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved dataset to {args.output}")
    print(f"saved metadata to {metadata_path}")
    print(
        "episodes_completed={episodes} success_rate={success_rate:.3f} "
        "collision_rate={collision_rate:.3f}".format(
            episodes=episodes,
            success_rate=successes / max(episodes, 1),
            collision_rate=collisions / max(episodes, 1),
        )
    )


if __name__ == "__main__":
    main()
