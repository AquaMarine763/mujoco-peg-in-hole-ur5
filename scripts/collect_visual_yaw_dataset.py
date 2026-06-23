from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import mujoco
except ImportError as exc:  # pragma: no cover - dependency check.
    raise ImportError(
        "mujoco is required. Install project dependencies with "
        "`python -m pip install -r requirements.txt`."
    ) from exc

from peg_in_hole_mujoco import PegInHoleMujocoEnv
from peg_in_hole_mujoco.sim_config import parse_args_with_config


DATASET_SCHEMA_VERSION = "visual_yaw_v1_near_hole_no_tip_highlight"
DEFAULT_PROFILES = (
    "square_square",
    "triangle_triangle",
    "hex_hex",
    "rectangular_key",
)
PROFILE_PERIOD_DEG = {
    "square_square": 90.0,
    "triangle_triangle": 120.0,
    "hex_hex": 60.0,
    "slot_slot": 180.0,
    "rectangular_key": 360.0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect near-hole wrist-camera observations with shape-yaw labels. "
            "This is for visual yaw-estimator training, not policy rollout."
        )
    )
    parser.add_argument("--model-path", type=Path, default=Path("assets/ur5e_full/ur5e_peg_in_hole_full.xml"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--samples", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=906_500)
    parser.add_argument("--geometry-profiles", nargs="+", default=list(DEFAULT_PROFILES))
    parser.add_argument("--geometry-fixture-mode", default="true_mesh")
    parser.add_argument("--geometry-true-fixture-variant", default="tight_yaw")
    parser.add_argument("--randomize-domain", action="store_true")
    parser.add_argument("--domain-randomization-level", default="visual_camera")
    parser.add_argument("--image-width", type=int, default=100)
    parser.add_argument("--image-height", type=int, default=100)
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--near-hole-crop-source-size", type=int, default=64)
    parser.add_argument("--near-hole-crop-offset", nargs=2, type=int, default=(-18, 0))
    parser.add_argument("--wrist-camera-pos-offset", nargs=3, type=float, default=(-0.04, -0.04, 0.0))
    parser.add_argument("--wrist-camera-rot-offset-deg", nargs=3, type=float, default=(0.0, 0.0, 0.0))
    parser.add_argument("--wrist-camera-fovy", type=float, default=100.0)
    parser.add_argument("--tip-z-above-range", nargs=2, type=float, default=(0.035, 0.080))
    parser.add_argument("--tip-xy-offset-range", nargs=2, type=float, default=(0.0, 0.006))
    parser.add_argument("--yaw-sampling-mode", choices=("uniform", "stratified"), default="uniform")
    parser.add_argument("--yaw-bin-count", type=int, default=12)
    parser.add_argument("--settle-steps", type=int, default=4)
    parser.add_argument("--max-ik-error", type=float, default=0.004)
    parser.add_argument("--max-attempts-multiplier", type=int, default=8)
    parser.add_argument("--enable-peg-tip-visual-helpers", action="store_true")
    parser.add_argument("--compressed", action="store_true")
    args = parse_args_with_config(parser)
    normalize_args(args)
    return args


def normalize_args(args: argparse.Namespace) -> None:
    args.geometry_profiles = [str(profile) for profile in args.geometry_profiles]
    if args.samples <= 0:
        raise ValueError("--samples must be positive.")
    if args.settle_steps < 0:
        raise ValueError("--settle-steps cannot be negative.")
    if args.max_attempts_multiplier < 1:
        raise ValueError("--max-attempts-multiplier must be at least 1.")
    if len(args.tip_z_above_range) != 2 or args.tip_z_above_range[0] > args.tip_z_above_range[1]:
        raise ValueError("--tip-z-above-range must be two increasing values.")
    if len(args.tip_xy_offset_range) != 2 or args.tip_xy_offset_range[0] > args.tip_xy_offset_range[1]:
        raise ValueError("--tip-xy-offset-range must be two increasing values.")
    if args.yaw_bin_count <= 0:
        raise ValueError("--yaw-bin-count must be positive.")
    unsupported = [profile for profile in args.geometry_profiles if profile not in PROFILE_PERIOD_DEG]
    if unsupported:
        raise ValueError(f"unsupported yaw-label geometry profile(s): {unsupported}")


def make_env(args: argparse.Namespace, profile: str) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode="image",
        image_width=args.image_width,
        image_height=args.image_height,
        include_near_hole_crop=True,
        near_hole_crop_size=args.near_hole_crop_size,
        near_hole_crop_source_size=args.near_hole_crop_source_size,
        near_hole_crop_offset=tuple(args.near_hole_crop_offset),
        include_control_state=False,
        image_frame_stack=1,
        randomize_domain=bool(args.randomize_domain),
        domain_randomization_level=args.domain_randomization_level,
        wrist_camera_pos_offset=tuple(args.wrist_camera_pos_offset),
        wrist_camera_rot_offset_deg=tuple(args.wrist_camera_rot_offset_deg),
        wrist_camera_fovy=args.wrist_camera_fovy,
        geometry_profile=profile,
        geometry_fixture_mode=args.geometry_fixture_mode,
        geometry_true_fixture_variant=args.geometry_true_fixture_variant,
        enable_peg_tip_visual_helpers=bool(args.enable_peg_tip_visual_helpers),
        ik_control_mode="pose_tip_priority",
        ik_orientation_weight=0.08,
        ik_posture_weight=0.01,
        ik_max_iterations=64,
        initialization_mode="target_relative_high_start",
    )


def target_xmat_for_yaw(env: PegInHoleMujocoEnv, yaw_deg: float) -> np.ndarray:
    hole_xmat = env._body_xmat(env.data, env.hole_body_id)
    hole_x_axis = hole_xmat @ np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
    hole_x_xy = env._project_unit_xy(hole_x_axis)
    if hole_x_xy is None:
        hole_x_xy = np.asarray([1.0, 0.0, 0.0], dtype=np.float64)
    yaw_rad = float(np.deg2rad(yaw_deg))
    c, s = float(np.cos(yaw_rad)), float(np.sin(yaw_rad))
    target_x_axis = np.asarray(
        [
            c * hole_x_xy[0] - s * hole_x_xy[1],
            s * hole_x_xy[0] + c * hole_x_xy[1],
            0.0,
        ],
        dtype=np.float64,
    )

    target_z_axis = env.default_pose_ik_target_xmat[:, 2].copy()
    target_z_norm = float(np.linalg.norm(target_z_axis))
    if target_z_norm <= 1e-9:
        target_z_axis = np.asarray([0.0, 0.0, 1.0], dtype=np.float64)
    else:
        target_z_axis = target_z_axis / target_z_norm

    target_x_axis = target_x_axis - target_z_axis * float(np.dot(target_x_axis, target_z_axis))
    target_x_axis = target_x_axis / max(float(np.linalg.norm(target_x_axis)), 1e-9)
    target_y_axis = np.cross(target_z_axis, target_x_axis)
    target_y_axis = target_y_axis / max(float(np.linalg.norm(target_y_axis)), 1e-9)
    return np.column_stack((target_x_axis, target_y_axis, target_z_axis))


def sample_tip_target(env: PegInHoleMujocoEnv, rng: np.random.Generator, args: argparse.Namespace) -> np.ndarray:
    radius = float(rng.uniform(args.tip_xy_offset_range[0], args.tip_xy_offset_range[1]))
    theta = float(rng.uniform(0.0, 2.0 * np.pi))
    z_above = float(rng.uniform(args.tip_z_above_range[0], args.tip_z_above_range[1]))
    return env.target_pos + np.asarray(
        [radius * np.cos(theta), radius * np.sin(theta), z_above],
        dtype=np.float64,
    )


def sample_target_yaw_deg(
    *,
    rng: np.random.Generator,
    args: argparse.Namespace,
    profile: str,
    period_deg: float,
    accepted_profile_counts: dict[str, int],
) -> float:
    if args.yaw_sampling_mode == "stratified":
        count = int(accepted_profile_counts.get(profile, 0))
        bin_id = count % int(args.yaw_bin_count)
        bin_width = float(period_deg) / float(args.yaw_bin_count)
        low = -0.5 * float(period_deg) + bin_width * bin_id
        high = low + bin_width
        return float(rng.uniform(low, high))
    return float(rng.uniform(-0.5 * period_deg, 0.5 * period_deg))


def place_tip_pose(
    env: PegInHoleMujocoEnv,
    target_pos: np.ndarray,
    target_xmat: np.ndarray,
    *,
    settle_steps: int,
) -> tuple[float, int]:
    env.set_pose_ik_target_xmat(target_xmat)
    qpos, achieved_tip, ik_error, iterations = env._solve_tip_priority_pose_ik_with_diagnostics(target_pos)
    del achieved_tip
    env._set_arm_qpos(env.data, qpos)
    env._set_arm_control(qpos)
    env.data.qvel[:] = 0.0
    mujoco.mj_forward(env.model, env.data)
    for _ in range(settle_steps):
        mujoco.mj_step(env.model, env.data)
    env.last_ik_tip_pos = env._site_xpos(env.data, env.peg_tip_site_id)
    env.last_ik_target_error = float(ik_error)
    env.last_ik_orientation_error = env._current_pose_ik_orientation_error(env.data)
    env.last_ik_iterations = int(iterations)
    env.last_joint_qpos_before_action = qpos.copy()
    env.last_joint_target_qpos = qpos.copy()
    env.last_joint_qpos_after_action = env.data.qpos[env.arm_qpos_ids].copy()
    env.last_joint_target_error = float(np.linalg.norm(env.last_joint_target_qpos - env.last_joint_qpos_after_action))
    env.last_peg_axis_world, env.last_peg_tilt_angle_deg = env._peg_axis_and_tilt(env.data)
    return float(ik_error), int(iterations)


def append_sample(
    buffers: dict[str, list[Any]],
    *,
    obs: dict[str, np.ndarray],
    info: dict[str, Any],
    profile: str,
    target_yaw_deg: float,
    target_tip_pos: np.ndarray,
    ik_error: float,
    ik_iterations: int,
) -> None:
    buffers["cam_image"].append(np.asarray(obs["cam_image"], dtype=np.uint8))
    buffers["near_hole_crop"].append(np.asarray(obs["near_hole_crop"], dtype=np.uint8))
    buffers["geometry_profile"].append(profile)
    buffers["geometry_name"].append(str(info.get("geometry_name", "")))
    buffers["peg_shape"].append(str(info.get("peg_shape", "")))
    buffers["hole_shape"].append(str(info.get("hole_shape", "")))
    buffers["target_yaw_deg"].append(float(target_yaw_deg))
    buffers["shape_yaw_period_deg"].append(float(info.get("shape_yaw_period_deg", np.nan)))
    buffers["shape_yaw_symmetry_order"].append(float(info.get("shape_yaw_symmetry_order", np.nan)))
    buffers["shape_yaw_raw_deg"].append(float(info.get("shape_yaw_raw_deg", np.nan)))
    buffers["shape_yaw_signed_error_deg"].append(float(info.get("shape_yaw_signed_error_deg", np.nan)))
    buffers["shape_yaw_error_deg"].append(float(info.get("shape_yaw_error_deg", np.nan)))
    buffers["shape_yaw_label_sin"].append(float(info.get("shape_yaw_label_sin", np.nan)))
    buffers["shape_yaw_label_cos"].append(float(info.get("shape_yaw_label_cos", np.nan)))
    buffers["shape_yaw_clearance"].append(float(info.get("shape_yaw_clearance", np.nan)))
    buffers["peg_tilt_angle_deg"].append(float(info.get("peg_tilt_angle_deg", np.nan)))
    buffers["dist_xy"].append(float(info.get("dist_xy", np.nan)))
    buffers["dist_z"].append(float(info.get("dist_z", np.nan)))
    buffers["ik_target_error"].append(float(ik_error))
    buffers["ik_iterations"].append(int(ik_iterations))
    buffers["target_tip_pos"].append(np.asarray(target_tip_pos, dtype=np.float32))
    buffers["peg_tip_pos"].append(np.asarray(info.get("peg_tip_pos", [np.nan, np.nan, np.nan]), dtype=np.float32))
    buffers["target_pos"].append(np.asarray(info.get("target_pos", [np.nan, np.nan, np.nan]), dtype=np.float32))


def empty_buffers() -> dict[str, list[Any]]:
    return {
        "cam_image": [],
        "near_hole_crop": [],
        "geometry_profile": [],
        "geometry_name": [],
        "peg_shape": [],
        "hole_shape": [],
        "target_yaw_deg": [],
        "shape_yaw_period_deg": [],
        "shape_yaw_symmetry_order": [],
        "shape_yaw_raw_deg": [],
        "shape_yaw_signed_error_deg": [],
        "shape_yaw_error_deg": [],
        "shape_yaw_label_sin": [],
        "shape_yaw_label_cos": [],
        "shape_yaw_clearance": [],
        "peg_tilt_angle_deg": [],
        "dist_xy": [],
        "dist_z": [],
        "ik_target_error": [],
        "ik_iterations": [],
        "target_tip_pos": [],
        "peg_tip_pos": [],
        "target_pos": [],
    }


def build_arrays(buffers: dict[str, list[Any]], metadata: dict[str, Any]) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {
        "cam_image": np.asarray(buffers["cam_image"], dtype=np.uint8),
        "near_hole_crop": np.asarray(buffers["near_hole_crop"], dtype=np.uint8),
        "geometry_profile": np.asarray(buffers["geometry_profile"]),
        "geometry_name": np.asarray(buffers["geometry_name"]),
        "peg_shape": np.asarray(buffers["peg_shape"]),
        "hole_shape": np.asarray(buffers["hole_shape"]),
        "target_tip_pos": np.asarray(buffers["target_tip_pos"], dtype=np.float32),
        "peg_tip_pos": np.asarray(buffers["peg_tip_pos"], dtype=np.float32),
        "target_pos": np.asarray(buffers["target_pos"], dtype=np.float32),
        "ik_iterations": np.asarray(buffers["ik_iterations"], dtype=np.int32),
        "metadata_json": np.asarray(json.dumps(metadata, indent=2, sort_keys=True, default=str)),
    }
    float_keys = (
        "target_yaw_deg",
        "shape_yaw_period_deg",
        "shape_yaw_symmetry_order",
        "shape_yaw_raw_deg",
        "shape_yaw_signed_error_deg",
        "shape_yaw_error_deg",
        "shape_yaw_label_sin",
        "shape_yaw_label_cos",
        "shape_yaw_clearance",
        "peg_tilt_angle_deg",
        "dist_xy",
        "dist_z",
        "ik_target_error",
    )
    for key in float_keys:
        arrays[key] = np.asarray(buffers[key], dtype=np.float32)
    return arrays


def summarize_arrays(arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    profiles, counts = np.unique(arrays["geometry_profile"].astype(str), return_counts=True)
    return {
        "samples": int(arrays["cam_image"].shape[0]),
        "profile_counts": {str(profile): int(count) for profile, count in zip(profiles, counts)},
        "mean_abs_yaw_error_deg": float(np.nanmean(arrays["shape_yaw_error_deg"])),
        "max_abs_yaw_error_deg": float(np.nanmax(arrays["shape_yaw_error_deg"])),
        "mean_ik_error": float(np.nanmean(arrays["ik_target_error"])),
        "max_ik_error": float(np.nanmax(arrays["ik_target_error"])),
        "cam_image_shape": list(arrays["cam_image"].shape),
        "near_hole_crop_shape": list(arrays["near_hole_crop"].shape),
    }


def write_report(path: Path, summary: dict[str, Any], args: argparse.Namespace) -> None:
    lines = [
        "# Visual Yaw Dataset",
        "",
        f"- Schema: `{DATASET_SCHEMA_VERSION}`",
        f"- Output: `{args.output}`",
        f"- Samples: `{summary['samples']}`",
        f"- Profiles: `{', '.join(args.geometry_profiles)}`",
        f"- Fixture mode / variant: `{args.geometry_fixture_mode}` / `{args.geometry_true_fixture_variant}`",
        f"- Peg-tip visual helpers enabled: `{bool(args.enable_peg_tip_visual_helpers)}`",
        f"- Domain randomization: `{bool(args.randomize_domain)}` / `{args.domain_randomization_level}`",
        f"- Yaw sampling: `{args.yaw_sampling_mode}` / bins `{args.yaw_bin_count}`",
        f"- Mean/max IK error: `{summary['mean_ik_error']:.6f}` / `{summary['max_ik_error']:.6f}`",
        f"- Mean/max abs yaw error deg: `{summary['mean_abs_yaw_error_deg']:.3f}` / `{summary['max_abs_yaw_error_deg']:.3f}`",
        "",
        "| Profile | Samples |",
        "| --- | ---: |",
    ]
    for profile, count in sorted(summary["profile_counts"].items()):
        lines.append(f"| `{profile}` | {count} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    buffers = empty_buffers()
    envs = {profile: make_env(args, profile) for profile in args.geometry_profiles}
    accepted_profile_counts = {profile: 0 for profile in set(args.geometry_profiles)}
    max_attempts = args.samples * args.max_attempts_multiplier
    attempts = 0

    try:
        while len(buffers["cam_image"]) < args.samples and attempts < max_attempts:
            index = len(buffers["cam_image"])
            profile = args.geometry_profiles[index % len(args.geometry_profiles)]
            env = envs[profile]
            period_deg = PROFILE_PERIOD_DEG[profile]
            sample_seed = int(args.seed + attempts)
            env.reset(seed=sample_seed)

            target_yaw_deg = sample_target_yaw_deg(
                rng=rng,
                args=args,
                profile=profile,
                period_deg=period_deg,
                accepted_profile_counts=accepted_profile_counts,
            )
            target_tip_pos = sample_tip_target(env, rng, args)
            target_xmat = target_xmat_for_yaw(env, target_yaw_deg)
            ik_error, ik_iterations = place_tip_pose(
                env,
                target_tip_pos,
                target_xmat,
                settle_steps=args.settle_steps,
            )
            attempts += 1
            env._clear_observation_history()
            obs = env._get_obs()
            info = env._get_info()
            if ik_error > args.max_ik_error:
                continue
            if not np.isfinite(float(info.get("shape_yaw_signed_error_deg", np.nan))):
                continue
            append_sample(
                buffers,
                obs=obs,
                info=info,
                profile=profile,
                target_yaw_deg=target_yaw_deg,
                target_tip_pos=target_tip_pos,
                ik_error=ik_error,
                ik_iterations=ik_iterations,
            )
            accepted_profile_counts[profile] = accepted_profile_counts.get(profile, 0) + 1
            if len(buffers["cam_image"]) % 100 == 0 or len(buffers["cam_image"]) == args.samples:
                print(f"collected {len(buffers['cam_image'])}/{args.samples} samples after {attempts} attempts")
    finally:
        for env in envs.values():
            env.close()

    if len(buffers["cam_image"]) < args.samples:
        raise RuntimeError(
            f"only collected {len(buffers['cam_image'])}/{args.samples} samples "
            f"after {attempts} attempts; relax --max-ik-error or increase attempts."
        )

    metadata = {
        "schema": DATASET_SCHEMA_VERSION,
        "args": dict(vars(args)),
        "attempts": attempts,
        "accepted_profile_counts": accepted_profile_counts,
    }
    arrays = build_arrays(buffers, metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.compressed:
        np.savez_compressed(args.output, **arrays)
    else:
        np.savez(args.output, **arrays)
    summary = summarize_arrays(arrays)
    report_path = args.output_md if args.output_md is not None else args.output.with_suffix(".md")
    write_report(report_path, summary, args)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"saved dataset to {args.output}")
    print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
