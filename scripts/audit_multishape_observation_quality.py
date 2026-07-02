from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mujoco
import numpy as np

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
for path in (str(SCRIPTS_DIR), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import collect_visual_yaw_dataset as collector
from audit_visual_visibility import (
    center_crop_bounds,
    draw_circle,
    draw_rect,
    project_point,
    render_rgb,
    upscale_nearest,
)


GEOM_OBJ_TYPE = int(mujoco.mjtObj.mjOBJ_GEOM)


DEFAULT_PROFILES = (
    "round_round",
    "slot_slot",
    "square_square",
    "triangle_triangle",
    "hex_hex",
    "rectangular_key",
)

PROFILE_PERIOD_DEG = {
    **collector.PROFILE_PERIOD_DEG,
    "round_round": 360.0,
}


@dataclass(frozen=True)
class ViewCandidate:
    name: str
    wrist_camera_pos_offset: tuple[float, float, float]
    wrist_camera_rot_offset_deg: tuple[float, float, float]
    wrist_camera_fovy: float
    near_hole_crop_source_size: int
    near_hole_crop_offset: tuple[int, int]


VIEW_CANDIDATES = (
    ViewCandidate(
        name="baseline",
        wrist_camera_pos_offset=(-0.04, -0.04, 0.0),
        wrist_camera_rot_offset_deg=(0.0, 0.0, 0.0),
        wrist_camera_fovy=100.0,
        near_hole_crop_source_size=80,
        near_hole_crop_offset=(-18, -12),
    ),
    ViewCandidate(
        name="centered_wide",
        wrist_camera_pos_offset=(-0.04, -0.04, 0.0),
        wrist_camera_rot_offset_deg=(0.0, 0.0, 0.0),
        wrist_camera_fovy=105.0,
        near_hole_crop_source_size=96,
        near_hole_crop_offset=(0, 0),
    ),
    ViewCandidate(
        name="raised_centered",
        wrist_camera_pos_offset=(-0.03, -0.04, 0.025),
        wrist_camera_rot_offset_deg=(0.0, 0.0, 0.0),
        wrist_camera_fovy=105.0,
        near_hole_crop_source_size=96,
        near_hole_crop_offset=(0, 0),
    ),
    ViewCandidate(
        name="open_high",
        wrist_camera_pos_offset=(-0.025, -0.045, 0.04),
        wrist_camera_rot_offset_deg=(0.0, 0.0, 0.0),
        wrist_camera_fovy=110.0,
        near_hole_crop_source_size=112,
        near_hole_crop_offset=(0, 0),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit whether the multishape learned-vision branch gives the policy "
            "usable cam_image and near_hole_crop observations."
        )
    )
    parser.add_argument("--model-path", type=Path, default=Path("assets/ur5e_full/ur5e_peg_in_hole_full.xml"))
    parser.add_argument("--output-root", type=Path, default=Path("results/sim2real_learned_vision/observation_quality_audit"))
    parser.add_argument("--profiles", nargs="+", default=list(DEFAULT_PROFILES))
    parser.add_argument("--candidate-names", nargs="+", default=[candidate.name for candidate in VIEW_CANDIDATES])
    parser.add_argument("--samples-per-profile", type=int, default=12)
    parser.add_argument("--seed", type=int, default=912_000)
    parser.add_argument("--image-width", type=int, default=100)
    parser.add_argument("--image-height", type=int, default=100)
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--tip-z-above-range", nargs=2, type=float, default=(0.010, 0.120))
    parser.add_argument("--tip-xy-offset-range", nargs=2, type=float, default=(0.0, 0.012))
    parser.add_argument("--yaw-bin-count", type=int, default=12)
    parser.add_argument("--settle-steps", type=int, default=4)
    parser.add_argument("--max-ik-error", type=float, default=0.006)
    parser.add_argument("--max-attempts-multiplier", type=int, default=10)
    parser.add_argument("--frame-samples-per-profile", type=int, default=4)
    parser.add_argument("--image-upscale", type=int, default=4)
    args = parser.parse_args()
    normalize_args(args)
    return args


def normalize_args(args: argparse.Namespace) -> None:
    args.profiles = [str(profile) for profile in args.profiles]
    unsupported = sorted(set(args.profiles) - set(PROFILE_PERIOD_DEG))
    if unsupported:
        raise ValueError(f"unsupported profile(s): {unsupported}")
    candidate_names = {candidate.name for candidate in VIEW_CANDIDATES}
    unsupported_candidates = sorted(set(args.candidate_names) - candidate_names)
    if unsupported_candidates:
        raise ValueError(f"unsupported candidate(s): {unsupported_candidates}")
    if args.samples_per_profile <= 0:
        raise ValueError("--samples-per-profile must be positive.")
    if args.frame_samples_per_profile < 0:
        raise ValueError("--frame-samples-per-profile cannot be negative.")
    if args.near_hole_crop_size <= 0:
        raise ValueError("--near-hole-crop-size must be positive.")
    if len(args.tip_z_above_range) != 2 or args.tip_z_above_range[0] > args.tip_z_above_range[1]:
        raise ValueError("--tip-z-above-range must contain two increasing values.")
    if len(args.tip_xy_offset_range) != 2 or args.tip_xy_offset_range[0] > args.tip_xy_offset_range[1]:
        raise ValueError("--tip-xy-offset-range must contain two increasing values.")


def candidate_by_name(name: str) -> ViewCandidate:
    for candidate in VIEW_CANDIDATES:
        if candidate.name == name:
            return candidate
    raise ValueError(f"unknown candidate: {name}")


def collect_args_for_candidate(args: argparse.Namespace, candidate: ViewCandidate) -> argparse.Namespace:
    return argparse.Namespace(
        model_path=args.model_path,
        geometry_fixture_mode="true_mesh",
        geometry_true_fixture_variant="tight_yaw",
        randomize_domain=False,
        domain_randomization_level="visual_camera",
        image_width=args.image_width,
        image_height=args.image_height,
        near_hole_crop_size=args.near_hole_crop_size,
        near_hole_crop_source_size=candidate.near_hole_crop_source_size,
        near_hole_crop_offset=list(candidate.near_hole_crop_offset),
        wrist_camera_pos_offset=list(candidate.wrist_camera_pos_offset),
        wrist_camera_rot_offset_deg=list(candidate.wrist_camera_rot_offset_deg),
        wrist_camera_fovy=candidate.wrist_camera_fovy,
        enable_peg_tip_visual_helpers=False,
        tip_z_above_range=tuple(args.tip_z_above_range),
        tip_xy_offset_range=tuple(args.tip_xy_offset_range),
        yaw_sampling_mode="stratified",
        yaw_bin_count=args.yaw_bin_count,
        settle_steps=args.settle_steps,
        max_ik_error=args.max_ik_error,
        max_attempts_multiplier=args.max_attempts_multiplier,
    )


def sample_target_yaw_deg(
    *,
    rng: np.random.Generator,
    profile: str,
    profile_count: int,
    yaw_bin_count: int,
) -> float:
    period_deg = float(PROFILE_PERIOD_DEG[profile])
    bin_id = int(profile_count) % int(yaw_bin_count)
    bin_width = period_deg / float(yaw_bin_count)
    low = -0.5 * period_deg + bin_width * bin_id
    high = low + bin_width
    return float(rng.uniform(low, high))


def finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def grayscale_stats(image: np.ndarray) -> tuple[float, float]:
    array = np.asarray(image, dtype=np.float32).squeeze()
    return float(np.mean(array)), float(np.std(array))


def projection_distance(projection: dict[str, Any], width: int, height: int) -> float:
    u = finite_float(projection.get("u"))
    v = finite_float(projection.get("v"))
    if not np.isfinite(u) or not np.isfinite(v):
        return float("nan")
    return float(math.hypot(u - width / 2.0, v - height / 2.0))


def border_distance(projection: dict[str, Any], width: int, height: int) -> float:
    u = finite_float(projection.get("u"))
    v = finite_float(projection.get("v"))
    if not np.isfinite(u) or not np.isfinite(v):
        return float("nan")
    return float(min(u, v, width - 1.0 - u, height - 1.0 - v))


def visibility_masks(renderer: mujoco.Renderer, env: Any) -> tuple[np.ndarray, np.ndarray]:
    renderer.update_scene(env.data, camera="wrist_cam")
    seg = renderer.render()
    object_ids = seg[:, :, 0]
    object_types = seg[:, :, 1]
    hole_geom_ids = {
        env._geom_id("hole_plate"),
        *env.hole_wall_geom_ids.values(),
        *env.true_fixture_wall_geom_ids.values(),
    }
    if env.true_fixture_visual_geom_id is not None:
        hole_geom_ids.add(env.true_fixture_visual_geom_id)
    if env.hole_cavity_visual_geom_id is not None:
        hole_geom_ids.add(env.hole_cavity_visual_geom_id)
    if env.hole_key_tab_cavity_visual_geom_id is not None:
        hole_geom_ids.add(env.hole_key_tab_cavity_visual_geom_id)
    hole_geom_ids.update(env.hole_polygon_visual_geom_ids.values())
    peg_geom_ids = {env.peg_geom_id}
    geom_mask = object_types == GEOM_OBJ_TYPE
    hole_mask = geom_mask & np.isin(object_ids, list(hole_geom_ids))
    peg_mask = geom_mask & np.isin(object_ids, list(peg_geom_ids))
    return hole_mask, peg_mask


def row_for_sample(
    *,
    args: argparse.Namespace,
    candidate: ViewCandidate,
    profile: str,
    sample_index: int,
    attempt_seed: int,
    env: Any,
    obs: dict[str, np.ndarray],
    info: dict[str, Any],
    ik_error: float,
    ik_iterations: int,
    target_yaw_deg: float,
    target_tip_pos: np.ndarray,
    hole_mask: np.ndarray,
    peg_mask: np.ndarray,
) -> dict[str, Any]:
    crop_bounds = center_crop_bounds(
        args.image_width,
        args.image_height,
        int(info.get("near_hole_crop_source_size", candidate.near_hole_crop_source_size)),
        tuple(int(v) for v in info.get("near_hole_crop_offset", candidate.near_hole_crop_offset)),
    )
    hole_projection = project_point(
        env,
        np.asarray(info["target_pos"], dtype=np.float64),
        camera_id=env.wrist_camera_id,
        width=args.image_width,
        height=args.image_height,
    )
    peg_projection = project_point(
        env,
        np.asarray(info["peg_tip_pos"], dtype=np.float64),
        camera_id=env.wrist_camera_id,
        width=args.image_width,
        height=args.image_height,
    )
    cam_mean, cam_std = grayscale_stats(obs["cam_image"])
    crop_mean, crop_std = grayscale_stats(obs["near_hole_crop"])
    hole_center_dist = projection_distance(hole_projection, args.image_width, args.image_height)
    peg_center_dist = projection_distance(peg_projection, args.image_width, args.image_height)
    hole_border_dist = border_distance(hole_projection, args.image_width, args.image_height)
    peg_border_dist = border_distance(peg_projection, args.image_width, args.image_height)
    hole_crop_x0, hole_crop_y0, hole_crop_x1, hole_crop_y1 = crop_bounds
    hole_crop_mask = hole_mask[hole_crop_y0:hole_crop_y1, hole_crop_x0:hole_crop_x1]
    peg_crop_mask = peg_mask[hole_crop_y0:hole_crop_y1, hole_crop_x0:hole_crop_x1]
    hole_pixels = int(hole_mask.sum())
    peg_pixels = int(peg_mask.sum())
    hole_crop_pixels = int(hole_crop_mask.sum())
    peg_crop_pixels = int(peg_crop_mask.sum())
    hole_in_crop = (
        bool(hole_projection["in_frame"])
        and hole_crop_x0 <= finite_float(hole_projection["u"]) < hole_crop_x1
        and hole_crop_y0 <= finite_float(hole_projection["v"]) < hole_crop_y1
    )
    peg_in_crop = (
        bool(peg_projection["in_frame"])
        and hole_crop_x0 <= finite_float(peg_projection["u"]) < hole_crop_x1
        and hole_crop_y0 <= finite_float(peg_projection["v"]) < hole_crop_y1
    )
    z_above_target = float(np.asarray(info["peg_tip_pos"])[2] - np.asarray(info["target_pos"])[2])
    return {
        "candidate": candidate.name,
        "profile": profile,
        "sample_index": sample_index,
        "attempt_seed": attempt_seed,
        "geometry_name": str(info.get("geometry_name", "")),
        "peg_shape": str(info.get("peg_shape", "")),
        "hole_shape": str(info.get("hole_shape", "")),
        "target_yaw_deg": float(target_yaw_deg),
        "shape_yaw_signed_error_deg": finite_float(info.get("shape_yaw_signed_error_deg")),
        "shape_yaw_error_deg": finite_float(info.get("shape_yaw_error_deg")),
        "shape_yaw_period_deg": finite_float(info.get("shape_yaw_period_deg")),
        "dist_xy": finite_float(info.get("dist_xy")),
        "dist_z": finite_float(info.get("dist_z")),
        "z_above_target": z_above_target,
        "ik_error": float(ik_error),
        "ik_iterations": int(ik_iterations),
        "target_tip_x": float(target_tip_pos[0]),
        "target_tip_y": float(target_tip_pos[1]),
        "target_tip_z": float(target_tip_pos[2]),
        "hole_u": finite_float(hole_projection.get("u")),
        "hole_v": finite_float(hole_projection.get("v")),
        "hole_depth": finite_float(hole_projection.get("depth")),
        "hole_in_frame": bool(hole_projection["in_frame"]),
        "hole_in_crop": bool(hole_in_crop),
        "hole_center_distance_px": hole_center_dist,
        "hole_border_distance_px": hole_border_dist,
        "peg_u": finite_float(peg_projection.get("u")),
        "peg_v": finite_float(peg_projection.get("v")),
        "peg_depth": finite_float(peg_projection.get("depth")),
        "peg_in_frame": bool(peg_projection["in_frame"]),
        "peg_in_crop": bool(peg_in_crop),
        "peg_center_distance_px": peg_center_dist,
        "peg_border_distance_px": peg_border_dist,
        "both_in_frame": bool(hole_projection["in_frame"] and peg_projection["in_frame"]),
        "both_in_crop": bool(hole_in_crop and peg_in_crop),
        "hole_pixels": hole_pixels,
        "peg_pixels": peg_pixels,
        "hole_crop_pixels": hole_crop_pixels,
        "peg_crop_pixels": peg_crop_pixels,
        "hole_visible": bool(hole_pixels >= 5),
        "peg_visible": bool(peg_pixels >= 5),
        "hole_crop_visible": bool(hole_crop_pixels >= 5),
        "peg_crop_visible": bool(peg_crop_pixels >= 5),
        "both_crop_visible": bool(hole_crop_pixels >= 5 and peg_crop_pixels >= 5),
        "hole_crop_pixel_ratio": float(hole_crop_pixels / max(1, hole_pixels)),
        "peg_crop_pixel_ratio": float(peg_crop_pixels / max(1, peg_pixels)),
        "crop_x0": int(hole_crop_x0),
        "crop_y0": int(hole_crop_y0),
        "crop_x1": int(hole_crop_x1),
        "crop_y1": int(hole_crop_y1),
        "near_hole_crop_source_size": int(info.get("near_hole_crop_source_size", candidate.near_hole_crop_source_size)),
        "near_hole_crop_offset_x": int(candidate.near_hole_crop_offset[0]),
        "near_hole_crop_offset_y": int(candidate.near_hole_crop_offset[1]),
        "cam_mean": cam_mean,
        "cam_std": cam_std,
        "crop_mean": crop_mean,
        "crop_std": crop_std,
        "wrist_camera_pos_offset_x": float(candidate.wrist_camera_pos_offset[0]),
        "wrist_camera_pos_offset_y": float(candidate.wrist_camera_pos_offset[1]),
        "wrist_camera_pos_offset_z": float(candidate.wrist_camera_pos_offset[2]),
        "wrist_camera_fovy": float(candidate.wrist_camera_fovy),
    }


def save_sample_frames(
    *,
    args: argparse.Namespace,
    candidate: ViewCandidate,
    profile: str,
    sample_index: int,
    env: Any,
    obs: dict[str, np.ndarray],
    row: dict[str, Any],
    frame_renderer: mujoco.Renderer,
) -> None:
    frame_dir = args.output_root / "frames" / candidate.name / profile
    frame_dir.mkdir(parents=True, exist_ok=True)
    stem = frame_dir / f"{sample_index:03d}_z{row['z_above_target']:.3f}_yaw{row['shape_yaw_signed_error_deg']:.1f}"

    wrist_rgb = render_rgb(frame_renderer, env, "wrist_cam")
    annotated = wrist_rgb.copy()
    draw_rect(annotated, (int(row["crop_x0"]), int(row["crop_y0"]), int(row["crop_x1"]), int(row["crop_y1"])), (0, 128, 255))
    draw_circle(annotated, row["hole_u"], row["hole_v"], (255, 0, 0), radius=3)
    draw_circle(annotated, row["peg_u"], row["peg_v"], (0, 255, 0), radius=3)
    cam = np.asarray(obs["cam_image"]).squeeze()
    crop = np.asarray(obs["near_hole_crop"]).squeeze()

    try:
        import imageio.v2 as imageio
    except ImportError:
        import imageio

    imageio.imwrite(stem.with_name(stem.name + "_wrist.png"), upscale_nearest(wrist_rgb, args.image_upscale))
    imageio.imwrite(stem.with_name(stem.name + "_wrist_annotated.png"), upscale_nearest(annotated, args.image_upscale))
    imageio.imwrite(stem.with_name(stem.name + "_cam_image.png"), upscale_nearest(cam, args.image_upscale))
    imageio.imwrite(stem.with_name(stem.name + "_near_hole_crop.png"), upscale_nearest(crop, args.image_upscale))


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["candidate"]), str(row["profile"])), []).append(row)

    summary_rows: list[dict[str, Any]] = []
    for (candidate, profile), group in sorted(grouped.items()):
        low_z = [row for row in group if finite_float(row["z_above_target"]) <= 0.035]
        def rate(key: str, subset: list[dict[str, Any]] = group) -> float:
            if not subset:
                return float("nan")
            return float(sum(bool(row[key]) for row in subset) / len(subset))

        def mean(key: str, subset: list[dict[str, Any]] = group) -> float:
            values = [finite_float(row[key]) for row in subset if np.isfinite(finite_float(row[key]))]
            if not values:
                return float("nan")
            return float(sum(values) / len(values))

        summary_rows.append(
            {
                "candidate": candidate,
                "profile": profile,
                "samples": len(group),
                "low_z_samples": len(low_z),
                "hole_in_frame_rate": rate("hole_in_frame"),
                "hole_in_crop_rate": rate("hole_in_crop"),
                "peg_in_crop_rate": rate("peg_in_crop"),
                "both_in_crop_rate": rate("both_in_crop"),
                "hole_crop_visible_rate": rate("hole_crop_visible"),
                "peg_crop_visible_rate": rate("peg_crop_visible"),
                "both_crop_visible_rate": rate("both_crop_visible"),
                "low_z_both_in_crop_rate": rate("both_in_crop", low_z),
                "low_z_both_crop_visible_rate": rate("both_crop_visible", low_z),
                "mean_hole_center_distance_px": mean("hole_center_distance_px"),
                "mean_hole_border_distance_px": mean("hole_border_distance_px"),
                "mean_hole_pixels": mean("hole_pixels"),
                "mean_peg_pixels": mean("peg_pixels"),
                "mean_hole_crop_pixels": mean("hole_crop_pixels"),
                "mean_peg_crop_pixels": mean("peg_crop_pixels"),
                "mean_cam_std": mean("cam_std"),
                "mean_crop_std": mean("crop_std"),
                "mean_abs_shape_yaw_error_deg": mean("shape_yaw_error_deg"),
                "mean_z_above_target": mean("z_above_target"),
            }
        )
    return summary_rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Candidate | Profile | Samples | Hole in crop | Both visible | Low-z visible | Hole crop px | Peg crop px | Hole center px | Hole border px | Crop std |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {candidate} | {profile} | {samples} | {hole:.1%} | {bothvis:.1%} | {lowzvis:.1%} | {holepx:.1f} | {pegpx:.1f} | {center:.1f} | {border:.1f} | {cropstd:.1f} |".format(
                candidate=row["candidate"],
                profile=row["profile"],
                samples=int(row["samples"]),
                hole=float(row["hole_in_crop_rate"]),
                bothvis=float(row["both_crop_visible_rate"]),
                lowzvis=float(row["low_z_both_crop_visible_rate"]) if np.isfinite(float(row["low_z_both_crop_visible_rate"])) else float("nan"),
                holepx=float(row["mean_hole_crop_pixels"]),
                pegpx=float(row["mean_peg_crop_pixels"]),
                center=float(row["mean_hole_center_distance_px"]),
                border=float(row["mean_hole_border_distance_px"]),
                cropstd=float(row["mean_crop_std"]),
            )
        )
    return lines


def write_report(path: Path, args: argparse.Namespace, summary_rows: list[dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    metadata = {
        "profiles": args.profiles,
        "candidate_names": args.candidate_names,
        "samples_per_profile": args.samples_per_profile,
        "seed": args.seed,
        "image_shape": [args.image_height, args.image_width],
        "near_hole_crop_size": args.near_hole_crop_size,
        "tip_z_above_range": args.tip_z_above_range,
        "tip_xy_offset_range": args.tip_xy_offset_range,
    }
    lines = [
        "# Multishape Observation Quality Audit",
        "",
        "This audit checks whether `cam_image` and `near_hole_crop` are plausible policy inputs for learned visual alignment.",
        "",
        "## Setup",
        "",
        "```json",
        json.dumps(metadata, indent=2, sort_keys=True),
        "```",
        "",
        "## Summary",
        "",
        *markdown_table(summary_rows),
        "",
        "## Interpretation",
        "",
        "- `hole_in_crop` diagnoses whether the projected hole center is inside `near_hole_crop`.",
        "- `both_visible` uses MuJoCo segmentation pixels, so it is stricter than projected target-point visibility.",
        "- `low_z_visible` is the stricter near-insertion visibility check.",
        "- Low `hole_border_px` means the hole is near the image edge and likely fragile for sim-to-real.",
        "- `cam_std` and `crop_std` are simple contrast proxies; very low values indicate weak visual signal.",
        "",
        f"- Raw CSV: `{args.output_root / 'observation_quality_samples.csv'}`",
        f"- Summary CSV: `{args.output_root / 'observation_quality_summary.csv'}`",
        f"- Sample frames: `{args.output_root / 'frames'}`",
        "",
        f"Total accepted samples: `{len(rows)}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    all_rows: list[dict[str, Any]] = []
    args.output_root.mkdir(parents=True, exist_ok=True)

    for candidate_name in args.candidate_names:
        candidate = candidate_by_name(candidate_name)
        collect_args = collect_args_for_candidate(args, candidate)
        envs = {profile: collector.make_env(collect_args, profile) for profile in args.profiles}
        frame_renderers = {
            profile: mujoco.Renderer(env.model, height=args.image_height, width=args.image_width)
            for profile, env in envs.items()
        }
        segmentation_renderers = {
            profile: mujoco.Renderer(env.model, height=args.image_height, width=args.image_width)
            for profile, env in envs.items()
        }
        for renderer in segmentation_renderers.values():
            renderer.enable_segmentation_rendering()
        accepted_counts = {profile: 0 for profile in args.profiles}
        attempts = {profile: 0 for profile in args.profiles}
        max_attempts = args.samples_per_profile * int(args.max_attempts_multiplier)

        try:
            for profile in args.profiles:
                env = envs[profile]
                while accepted_counts[profile] < args.samples_per_profile and attempts[profile] < max_attempts:
                    attempt_seed = int(args.seed + len(all_rows) * 997 + attempts[profile])
                    env.reset(seed=attempt_seed)
                    period_deg = float(PROFILE_PERIOD_DEG[profile])
                    target_yaw_deg = sample_target_yaw_deg(
                        rng=rng,
                        profile=profile,
                        profile_count=accepted_counts[profile],
                        yaw_bin_count=args.yaw_bin_count,
                    )
                    target_tip_pos = collector.sample_tip_target(env, rng, collect_args)
                    target_xmat = collector.target_xmat_for_yaw(env, target_yaw_deg)
                    ik_error, ik_iterations = collector.place_tip_pose(
                        env,
                        target_tip_pos,
                        target_xmat,
                        settle_steps=args.settle_steps,
                    )
                    attempts[profile] += 1
                    env._clear_observation_history()
                    obs = env._get_obs()
                    info = env._get_info()
                    if ik_error > args.max_ik_error:
                        continue
                    hole_mask, peg_mask = visibility_masks(segmentation_renderers[profile], env)
                    row = row_for_sample(
                        args=args,
                        candidate=candidate,
                        profile=profile,
                        sample_index=accepted_counts[profile],
                        attempt_seed=attempt_seed,
                        env=env,
                        obs=obs,
                        info=info,
                        ik_error=ik_error,
                        ik_iterations=ik_iterations,
                        target_yaw_deg=target_yaw_deg,
                        target_tip_pos=target_tip_pos,
                        hole_mask=hole_mask,
                        peg_mask=peg_mask,
                    )
                    all_rows.append(row)
                    if accepted_counts[profile] < args.frame_samples_per_profile:
                        save_sample_frames(
                            args=args,
                            candidate=candidate,
                            profile=profile,
                            sample_index=accepted_counts[profile],
                            env=env,
                            obs=obs,
                            row=row,
                            frame_renderer=frame_renderers[profile],
                        )
                    accepted_counts[profile] += 1
                if accepted_counts[profile] < args.samples_per_profile:
                    raise RuntimeError(
                        f"{candidate.name}/{profile}: accepted {accepted_counts[profile]}/"
                        f"{args.samples_per_profile} after {attempts[profile]} attempts"
                    )
                print(f"{candidate.name}/{profile}: accepted {accepted_counts[profile]} samples")
        finally:
            for renderer in frame_renderers.values():
                renderer.close()
            for renderer in segmentation_renderers.values():
                renderer.close()
            for env in envs.values():
                env.close()

    summary_rows = summarize(all_rows)
    raw_csv = args.output_root / "observation_quality_samples.csv"
    summary_csv = args.output_root / "observation_quality_summary.csv"
    report_md = args.output_root / "observation_quality_audit.md"
    write_csv(raw_csv, all_rows)
    write_csv(summary_csv, summary_rows)
    write_report(report_md, args, summary_rows, all_rows)
    print(f"saved raw samples to {raw_csv}")
    print(f"saved summary to {summary_csv}")
    print(f"saved report to {report_md}")


if __name__ == "__main__":
    main()
