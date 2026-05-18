from __future__ import annotations

import argparse
import csv
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import mujoco
import numpy as np

from eval_guarded_policy import (
    AGENTS,
    CORE_SCENARIOS,
    HARD_BUCKET_SCENARIO,
    build_parser as build_eval_parser,
    make_env,
    make_guarded_config,
    policy_observation,
)
from peg_in_hole_mujoco import (
    GuardedPolicyController,
    MujocoGuardStateProvider,
    oracle_action_from_state,
)
from peg_in_hole_mujoco.sim_config import parse_args_with_config


SCENARIOS = {scenario.name: scenario for scenario in (*CORE_SCENARIOS, HARD_BUCKET_SCENARIO)}
GEOM_OBJ_TYPE = int(mujoco.mjtObj.mjOBJ_GEOM)


def parse_args() -> argparse.Namespace:
    parser = build_eval_parser("Audit whether peg/hole geometry is visible to the wrist camera.")
    parser.add_argument(
        "--audit-scenario",
        choices=sorted(SCENARIOS.keys()),
        default="hard_full_light_bucket",
        help="Scenario to audit. Defaults to the hard high-start bucket.",
    )
    parser.add_argument(
        "--visibility-output-csv",
        type=Path,
        default=Path("results/ur5e_full/high_start/hard/visual_audit/visibility_trace.csv"),
    )
    parser.add_argument(
        "--visibility-output-md",
        type=Path,
        default=Path("results/ur5e_full/high_start/hard/visual_audit/visibility_audit.md"),
    )
    parser.add_argument(
        "--frame-dir",
        type=Path,
        default=Path("results/ur5e_full/high_start/hard/visual_audit/frames"),
    )
    parser.add_argument("--frame-stride", type=int, default=50)
    parser.add_argument("--segmentation-stride", type=int, default=5)
    parser.add_argument("--max-frames-per-episode", type=int, default=12)
    parser.add_argument("--low-z-threshold", type=float, default=0.060)
    parser.add_argument("--near-xy-threshold", type=float, default=0.030)
    parser.add_argument("--insertion-xy-threshold", type=float, default=0.012)
    parser.add_argument("--min-hole-pixels", type=int, default=5)
    parser.add_argument("--min-peg-pixels", type=int, default=5)
    parser.add_argument("--overview-width", type=int, default=960)
    parser.add_argument("--overview-height", type=int, default=720)
    parser.add_argument("--image-upscale", type=int, default=4)
    return parse_args_with_config(parser)


def finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def vector_fields(prefix: str, value: Any, size: int = 3) -> dict[str, float]:
    labels = ("x", "y", "z") if size == 3 else tuple(str(index) for index in range(size))
    if value is None:
        return {f"{prefix}_{label}": float("nan") for label in labels}
    array = np.asarray(value, dtype=np.float64).reshape(-1)
    return {
        f"{prefix}_{label}": float(array[index]) if index < array.size else float("nan")
        for index, label in enumerate(labels)
    }


def center_crop_bounds(
    width: int,
    height: int,
    crop_size: int,
    offset: tuple[int, int] = (0, 0),
) -> tuple[int, int, int, int]:
    crop = min(int(crop_size), int(width), int(height))
    offset_x, offset_y = offset
    x0 = int(np.clip((int(width) - crop) // 2 + int(offset_x), 0, int(width) - crop))
    y0 = int(np.clip((int(height) - crop) // 2 + int(offset_y), 0, int(height) - crop))
    return x0, y0, x0 + crop, y0 + crop


def project_point(
    env: Any,
    point: np.ndarray,
    *,
    camera_id: int,
    width: int,
    height: int,
) -> dict[str, Any]:
    camera_pos = env.data.cam_xpos[camera_id].copy()
    camera_mat = env.data.cam_xmat[camera_id].reshape(3, 3).copy()
    rel = np.asarray(point, dtype=np.float64).reshape(3) - camera_pos
    camera_frame = camera_mat.T @ rel
    depth = -float(camera_frame[2])
    if depth <= 1e-9:
        return {
            "u": float("nan"),
            "v": float("nan"),
            "depth": depth,
            "in_front": False,
            "in_frame": False,
        }

    fovy_rad = math.radians(float(env.model.cam_fovy[camera_id]))
    focal = 0.5 * float(height) / math.tan(0.5 * fovy_rad)
    u = 0.5 * float(width) + focal * float(camera_frame[0]) / depth
    v = 0.5 * float(height) - focal * float(camera_frame[1]) / depth
    return {
        "u": u,
        "v": v,
        "depth": depth,
        "in_front": True,
        "in_frame": bool(0.0 <= u < width and 0.0 <= v < height),
    }


def point_in_crop(projection: dict[str, Any], crop_bounds: tuple[int, int, int, int]) -> bool:
    if not projection["in_frame"]:
        return False
    x0, y0, x1, y1 = crop_bounds
    return bool(x0 <= projection["u"] < x1 and y0 <= projection["v"] < y1)


def render_rgb(renderer: mujoco.Renderer, env: Any, camera_name: str) -> np.ndarray:
    renderer.update_scene(env.data, camera=camera_name)
    return renderer.render().copy()


def segmentation_counts(
    renderer: mujoco.Renderer,
    env: Any,
    *,
    crop_bounds: tuple[int, int, int, int],
) -> dict[str, Any]:
    renderer.update_scene(env.data, camera="wrist_cam")
    seg = renderer.render()
    object_ids = seg[:, :, 0]
    object_types = seg[:, :, 1]

    hole_geom_ids = {
        env._geom_id("hole_plate"),
        *env.hole_wall_geom_ids.values(),
    }
    peg_geom_ids = {env.peg_geom_id}
    geom_mask = object_types == GEOM_OBJ_TYPE
    hole_mask = geom_mask & np.isin(object_ids, list(hole_geom_ids))
    peg_mask = geom_mask & np.isin(object_ids, list(peg_geom_ids))
    x0, y0, x1, y1 = crop_bounds
    hole_crop = hole_mask[y0:y1, x0:x1]
    peg_crop = peg_mask[y0:y1, x0:x1]
    return {
        "segmentation_sampled": True,
        "hole_pixels": int(hole_mask.sum()),
        "peg_pixels": int(peg_mask.sum()),
        "hole_crop_pixels": int(hole_crop.sum()),
        "peg_crop_pixels": int(peg_crop.sum()),
        "image_pixels": int(hole_mask.size),
        "crop_pixels": int(hole_crop.size),
    }


def empty_segmentation_counts() -> dict[str, Any]:
    return {
        "segmentation_sampled": False,
        "hole_pixels": -1,
        "peg_pixels": -1,
        "hole_crop_pixels": -1,
        "peg_crop_pixels": -1,
        "image_pixels": -1,
        "crop_pixels": -1,
    }


def draw_circle(image: np.ndarray, u: float, v: float, color: tuple[int, int, int], radius: int) -> None:
    if not np.isfinite(u) or not np.isfinite(v):
        return
    height, width = image.shape[:2]
    cx = int(round(u))
    cy = int(round(v))
    for y in range(max(0, cy - radius), min(height, cy + radius + 1)):
        for x in range(max(0, cx - radius), min(width, cx + radius + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius**2:
                image[y, x, :] = color


def draw_rect(image: np.ndarray, bounds: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = bounds
    image[y0:y1, x0 : min(x0 + 1, x1), :] = color
    image[y0:y1, max(x0, x1 - 1) : x1, :] = color
    image[y0 : min(y0 + 1, y1), x0:x1, :] = color
    image[max(y0, y1 - 1) : y1, x0:x1, :] = color


def upscale_nearest(image: np.ndarray, scale: int) -> np.ndarray:
    scale = max(1, int(scale))
    if image.ndim == 2:
        image = image[:, :, None]
    if image.shape[2] == 1:
        image = np.repeat(image, 3, axis=2)
    return np.repeat(np.repeat(image, scale, axis=0), scale, axis=1)


def save_key_frame(
    *,
    imageio: Any,
    args: argparse.Namespace,
    env: Any,
    wrist_renderer: mujoco.Renderer,
    overview_renderer: mujoco.Renderer,
    obs: Any,
    episode: int,
    step: int,
    tag: str,
    hole_projection: dict[str, Any],
    peg_projection: dict[str, Any],
    crop_bounds: tuple[int, int, int, int],
) -> list[Path]:
    safe_tag = tag.replace(" ", "_").replace("/", "_")
    prefix = args.frame_dir / f"ep{episode:03d}_step{step:04d}_{safe_tag}"
    prefix.parent.mkdir(parents=True, exist_ok=True)

    wrist_rgb = render_rgb(wrist_renderer, env, "wrist_cam")
    annotated = wrist_rgb.copy()
    draw_rect(annotated, crop_bounds, (0, 128, 255))
    draw_circle(annotated, hole_projection["u"], hole_projection["v"], (255, 0, 0), radius=3)
    draw_circle(annotated, peg_projection["u"], peg_projection["v"], (0, 255, 0), radius=3)

    if isinstance(obs, dict) and "cam_image" in obs:
        policy_gray = np.asarray(obs["cam_image"]).squeeze()
    else:
        policy_gray = np.zeros((args.height, args.width), dtype=np.uint8)
    if isinstance(obs, dict) and "near_hole_crop" in obs:
        near_crop = np.asarray(obs["near_hole_crop"]).squeeze()
    else:
        x0, y0, x1, y1 = crop_bounds
        near_crop = policy_gray[y0:y1, x0:x1]

    overview = render_rgb(overview_renderer, env, "overview")
    paths = [
        prefix.with_name(prefix.name + "_wrist_rgb_x4.png"),
        prefix.with_name(prefix.name + "_wrist_annotated_x4.png"),
        prefix.with_name(prefix.name + "_policy_gray_x4.png"),
        prefix.with_name(prefix.name + "_near_crop_x4.png"),
        prefix.with_name(prefix.name + "_overview.png"),
    ]
    imageio.imwrite(paths[0], upscale_nearest(wrist_rgb, args.image_upscale))
    imageio.imwrite(paths[1], upscale_nearest(annotated, args.image_upscale))
    imageio.imwrite(paths[2], upscale_nearest(policy_gray, args.image_upscale))
    imageio.imwrite(paths[3], upscale_nearest(near_crop, args.image_upscale))
    imageio.imwrite(paths[4], overview)
    return paths


def should_save_frame(
    *,
    args: argparse.Namespace,
    step: int,
    info: dict[str, Any],
    guard_activated: bool,
    terminated: bool,
    truncated: bool,
    seen_tags: set[str],
    saved_count: int,
) -> str | None:
    tags: list[str] = []
    dist_xy = finite_float(info.get("dist_xy"))
    dist_z = finite_float(info.get("dist_z"))
    if step == 0:
        tags.append("reset")
    if guard_activated:
        tags.append("guard_activation")
    if dist_z <= args.low_z_threshold:
        tags.append("low_z")
    if dist_xy <= args.near_xy_threshold:
        tags.append("near_xy")
    if dist_xy <= args.insertion_xy_threshold and dist_z <= args.low_z_threshold:
        tags.append("insert_band")
    if info.get("insertion_success", False):
        tags.append("success")
    if info.get("collision", False):
        tags.append("collision")
    if truncated and not info.get("insertion_success", False):
        tags.append("timeout")
    if terminated or truncated:
        tags.append("final")

    for tag in tags:
        if tag not in seen_tags:
            return tag

    near_enough_for_sampling = dist_z <= 0.080 or dist_xy <= 0.040
    if (
        saved_count < args.max_frames_per_episode
        and args.frame_stride > 0
        and step > 0
        and step % args.frame_stride == 0
        and near_enough_for_sampling
    ):
        return f"sample_{step:04d}"
    return None


def build_visibility_row(
    *,
    args: argparse.Namespace,
    episode: int,
    step: int,
    scenario_name: str,
    scenario_level: str,
    info: dict[str, Any],
    reward: float,
    episode_return: float,
    policy_action: np.ndarray,
    final_action: np.ndarray,
    guarded_action: np.ndarray | None,
    guard_info: dict[str, Any],
    terminated: bool,
    truncated: bool,
    crop_bounds: tuple[int, int, int, int],
    hole_projection: dict[str, Any],
    peg_projection: dict[str, Any],
    segmentation: dict[str, Any],
    frame_tag: str | None,
) -> dict[str, Any]:
    hole_u = finite_float(hole_projection["u"])
    hole_v = finite_float(hole_projection["v"])
    peg_u = finite_float(peg_projection["u"])
    peg_v = finite_float(peg_projection["v"])
    projected_distance = (
        float(math.hypot(hole_u - peg_u, hole_v - peg_v))
        if np.isfinite(hole_u) and np.isfinite(hole_v) and np.isfinite(peg_u) and np.isfinite(peg_v)
        else float("nan")
    )
    z_above_target = finite_float(np.asarray(info.get("peg_tip_pos", [np.nan] * 3))[2]) - finite_float(
        np.asarray(info.get("target_pos", [np.nan] * 3))[2]
    )
    row: dict[str, Any] = {
        "episode": episode,
        "step": step,
        "scenario": scenario_name,
        "scenario_level": scenario_level,
        "control_mode": args.control_mode,
        "image_ablation": args.image_ablation,
        "reward": float(reward),
        "episode_return": float(episode_return),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": bool(info.get("insertion_success", False)),
        "collision": bool(info.get("collision", False)),
        "frame_tag": frame_tag or "",
        "dist_xy": finite_float(info.get("dist_xy")),
        "dist_z": finite_float(info.get("dist_z")),
        "z_above_target": float(z_above_target),
        "desired_z": finite_float(info.get("desired_z")),
        "hole_u": hole_u,
        "hole_v": hole_v,
        "hole_depth": finite_float(hole_projection["depth"]),
        "hole_in_front": bool(hole_projection["in_front"]),
        "hole_in_frame": bool(hole_projection["in_frame"]),
        "hole_in_center_crop": point_in_crop(hole_projection, crop_bounds),
        "peg_u": peg_u,
        "peg_v": peg_v,
        "peg_depth": finite_float(peg_projection["depth"]),
        "peg_in_front": bool(peg_projection["in_front"]),
        "peg_in_frame": bool(peg_projection["in_frame"]),
        "peg_in_center_crop": point_in_crop(peg_projection, crop_bounds),
        "hole_peg_projected_distance_px": projected_distance,
        "both_projected_in_frame": bool(hole_projection["in_frame"] and peg_projection["in_frame"]),
        "both_projected_in_center_crop": bool(
            point_in_crop(hole_projection, crop_bounds) and point_in_crop(peg_projection, crop_bounds)
        ),
        "crop_x0": crop_bounds[0],
        "crop_y0": crop_bounds[1],
        "crop_x1": crop_bounds[2],
        "crop_y1": crop_bounds[3],
        "hole_visible": bool(segmentation["hole_pixels"] >= args.min_hole_pixels),
        "peg_visible": bool(segmentation["peg_pixels"] >= args.min_peg_pixels),
        "hole_crop_visible": bool(segmentation["hole_crop_pixels"] >= args.min_hole_pixels),
        "peg_crop_visible": bool(segmentation["peg_crop_pixels"] >= args.min_peg_pixels),
    }
    row.update(segmentation)
    row.update(vector_fields("target", info.get("target_pos", (float("nan"),) * 3), 3))
    row.update(vector_fields("peg_tip", info.get("peg_tip_pos", (float("nan"),) * 3), 3))
    row.update(vector_fields("policy_action", policy_action, 3))
    row.update(vector_fields("final_action", final_action, 3))
    row.update(vector_fields("guarded_action", guarded_action, 3))
    row.update(
        {
            "guard_enabled": bool(guard_info.get("guard_enabled", False)),
            "guard_active": bool(guard_info.get("guard_active", False)),
            "guard_activated": bool(guard_info.get("guard_activated", False)),
            "guard_should_activate": bool(guard_info.get("guard_should_activate", False)),
            "guard_can_activate": bool(guard_info.get("guard_can_activate", False)),
            "guard_dist_xy": finite_float(guard_info.get("guard_dist_xy")),
            "guard_z_above_target": finite_float(guard_info.get("guard_z_above_target")),
        }
    )
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved visibility trace to {path}")


def mean(values: list[float]) -> float:
    if not values:
        return float("nan")
    return float(sum(values) / len(values))


def bool_rate(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return float("nan")
    return float(sum(bool(row[key]) for row in rows) / len(rows))


def metric_rows(rows: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    subsets = [
        ("all", rows),
        ("low_z", [row for row in rows if finite_float(row["dist_z"]) <= args.low_z_threshold]),
        ("near_xy", [row for row in rows if finite_float(row["dist_xy"]) <= args.near_xy_threshold]),
        (
            "insert_band",
            [
                row
                for row in rows
                if finite_float(row["dist_xy"]) <= args.insertion_xy_threshold
                and finite_float(row["dist_z"]) <= args.low_z_threshold
            ],
        ),
    ]
    metrics = []
    for name, subset in subsets:
        segmented = [row for row in subset if bool(row["segmentation_sampled"])]
        distances = [
            finite_float(row["hole_peg_projected_distance_px"])
            for row in subset
            if np.isfinite(finite_float(row["hole_peg_projected_distance_px"]))
        ]
        metrics.append(
            {
                "subset": name,
                "rows": len(subset),
                "segmented_rows": len(segmented),
                "hole_in_frame": bool_rate(subset, "hole_in_frame"),
                "peg_in_frame": bool_rate(subset, "peg_in_frame"),
                "both_in_frame": bool_rate(subset, "both_projected_in_frame"),
                "both_in_crop": bool_rate(subset, "both_projected_in_center_crop"),
                "mean_projected_distance_px": mean(distances),
                "hole_visible": bool_rate(segmented, "hole_visible"),
                "peg_visible": bool_rate(segmented, "peg_visible"),
                "hole_crop_visible": bool_rate(segmented, "hole_crop_visible"),
                "peg_crop_visible": bool_rate(segmented, "peg_crop_visible"),
            }
        )
    return metrics


def write_markdown(
    path: Path,
    args: argparse.Namespace,
    *,
    scenario_name: str,
    scenario_level: str,
    episode_summaries: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    saved_frame_paths: list[Path],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    successes = sum(int(summary["success"]) for summary in episode_summaries)
    collisions = sum(int(summary["collision"]) for summary in episode_summaries)
    timeouts = sum(int(summary["timeout"]) for summary in episode_summaries)
    metrics = metric_rows(rows, args)
    lines = [
        "# Visual Visibility Audit",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Scenario: `{scenario_name}` / `{scenario_level}`",
        f"- Control mode: `{args.control_mode}`",
        f"- Image ablation: `{args.image_ablation}`",
        f"- Episodes: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Policy image size: `{args.width}x{args.height}`",
        f"- Center crop size: `{args.near_hole_crop_size}`",
        f"- Center crop offset: `{tuple(args.near_hole_crop_offset)}`",
        f"- Segmentation stride: `{args.segmentation_stride}`",
        f"- Frame directory: `{args.frame_dir}`",
        "",
        "## Rollout Outcome",
        "",
        f"- Success rate: `{successes / max(args.episodes, 1):.3f}`",
        f"- Collision rate: `{collisions / max(args.episodes, 1):.3f}`",
        f"- Timeout rate: `{timeouts / max(args.episodes, 1):.3f}`",
        f"- Saved key-frame images: `{len(saved_frame_paths)}`",
        "",
        "## Visibility Metrics",
        "",
        "| Subset | Rows | Seg rows | Hole projected | Peg projected | Both projected | Both in crop | Mean px gap | Hole visible | Peg visible | Hole crop visible | Peg crop visible |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for metric in metrics:
        lines.append(
            "| {subset} | {rows} | {segmented_rows} | {hole_in_frame:.3f} | {peg_in_frame:.3f} | "
            "{both_in_frame:.3f} | {both_in_crop:.3f} | {mean_projected_distance_px:.2f} | "
            "{hole_visible:.3f} | {peg_visible:.3f} | {hole_crop_visible:.3f} | "
            "{peg_crop_visible:.3f} |".format(**metric)
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `projected` means the 3D point projects inside the wrist camera image.",
            "- `visible` means MuJoCo segmentation found enough rendered pixels for the corresponding geometry.",
            "- The red marker in annotated wrist frames is the projected hole center; the green marker is the peg tip; the blue box is the policy center crop.",
        ]
    )
    if saved_frame_paths:
        lines.extend(["", "## Example Frames", ""])
        for path_item in saved_frame_paths[:20]:
            lines.append(f"- `{path_item}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved visibility report to {path}")


def guard_info_from_step(step: Any, guard_enabled: bool) -> dict[str, Any]:
    if step is None:
        return {
            "guard_enabled": guard_enabled,
            "guard_active": False,
            "guard_activated": False,
            "guard_should_activate": False,
            "guard_can_activate": False,
            "guard_dist_xy": float("nan"),
            "guard_z_above_target": float("nan"),
        }
    return {
        "guard_enabled": step.guard_enabled,
        "guard_active": step.guarded,
        "guard_activated": step.guard_activated,
        "guard_should_activate": step.guard_should_activate,
        "guard_can_activate": step.guard_can_activate,
        "guard_dist_xy": step.guard_dist_xy,
        "guard_z_above_target": step.guard_z_above_target,
    }


def main() -> None:
    try:
        import imageio.v2 as imageio
    except ImportError as exc:
        raise ImportError("Install imageio with `python -m pip install imageio` to save audit frames.") from exc

    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")
    if args.frame_stride <= 0:
        raise ValueError("--frame-stride must be positive.")
    if args.segmentation_stride <= 0:
        raise ValueError("--segmentation-stride must be positive.")
    if args.max_frames_per_episode <= 0:
        raise ValueError("--max-frames-per-episode must be positive.")
    if args.observation_mode != "image":
        raise ValueError("Visibility audit requires --observation-mode image.")

    scenario = SCENARIOS[args.audit_scenario]
    env = make_env(args, scenario)
    model = (
        None
        if args.control_mode == "guard_only"
        else AGENTS[args.agent].load(args.model, env=env, device=args.device)
    )
    guarded_config = make_guarded_config(args)
    guarded_controller = GuardedPolicyController(guarded_config)
    guard_state_provider = MujocoGuardStateProvider(env)
    guard_enabled = (
        args.control_mode == "guard_only"
        or (
            args.control_mode == "guarded"
            and guarded_controller.scenario_uses_guard(scenario.name, scenario.level)
        )
    )
    wrist_renderer = mujoco.Renderer(env.model, height=args.height, width=args.width)
    segmentation_renderer = mujoco.Renderer(env.model, height=args.height, width=args.width)
    segmentation_renderer.enable_segmentation_rendering()
    overview_renderer = mujoco.Renderer(
        env.model,
        height=args.overview_height,
        width=args.overview_width,
    )
    crop_bounds = center_crop_bounds(
        args.width,
        args.height,
        args.near_hole_crop_size,
        tuple(args.near_hole_crop_offset),
    )
    ablation_rng = np.random.default_rng(args.seed + 1_000_003)
    shuffle_bank: list[Any] = []

    rows: list[dict[str, Any]] = []
    episode_summaries: list[dict[str, Any]] = []
    saved_frame_paths: list[Path] = []

    try:
        for episode in range(args.episodes):
            obs, info = env.reset(seed=args.seed + episode)
            guarded_controller.reset()
            episode_return = 0.0
            saved_tags: set[str] = set()
            saved_count = 0

            policy_action = np.zeros(3, dtype=np.float32)
            final_action = np.zeros(3, dtype=np.float32)
            guarded_action = None
            guard_info = guard_info_from_step(None, guard_enabled)
            for step_index, reward, terminated, truncated in [(0, 0.0, False, False)]:
                del step_index
                hole_projection = project_point(
                    env,
                    np.asarray(info["target_pos"], dtype=np.float64),
                    camera_id=env.wrist_camera_id,
                    width=args.width,
                    height=args.height,
                )
                peg_projection = project_point(
                    env,
                    np.asarray(info["peg_tip_pos"], dtype=np.float64),
                    camera_id=env.wrist_camera_id,
                    width=args.width,
                    height=args.height,
                )
                segmentation = segmentation_counts(
                    segmentation_renderer,
                    env,
                    crop_bounds=crop_bounds,
                )
                frame_tag = should_save_frame(
                    args=args,
                    step=0,
                    info=info,
                    guard_activated=False,
                    terminated=False,
                    truncated=False,
                    seen_tags=saved_tags,
                    saved_count=saved_count,
                )
                if frame_tag is not None:
                    saved_tags.add(frame_tag)
                    saved_count += 1
                    saved_frame_paths.extend(
                        save_key_frame(
                            imageio=imageio,
                            args=args,
                            env=env,
                            wrist_renderer=wrist_renderer,
                            overview_renderer=overview_renderer,
                            obs=obs,
                            episode=episode + 1,
                            step=0,
                            tag=frame_tag,
                            hole_projection=hole_projection,
                            peg_projection=peg_projection,
                            crop_bounds=crop_bounds,
                        )
                    )
                rows.append(
                    build_visibility_row(
                        args=args,
                        episode=episode + 1,
                        step=0,
                        scenario_name=scenario.name,
                        scenario_level=scenario.level,
                        info=info,
                        reward=reward,
                        episode_return=episode_return,
                        policy_action=policy_action,
                        final_action=final_action,
                        guarded_action=guarded_action,
                        guard_info=guard_info,
                        terminated=terminated,
                        truncated=truncated,
                        crop_bounds=crop_bounds,
                        hole_projection=hole_projection,
                        peg_projection=peg_projection,
                        segmentation=segmentation,
                        frame_tag=frame_tag,
                    )
                )

            while True:
                if args.control_mode == "guard_only":
                    state = guard_state_provider.state_from_info(info)
                    policy_action = np.zeros(3, dtype=np.float32)
                    final_action = oracle_action_from_state(
                        peg_tip_pos=state.peg_tip_pos,
                        target_pos=state.target_pos,
                        applied_action=state.applied_action,
                        approach_height=state.approach_height,
                        action_low=state.action_low,
                        action_high=state.action_high,
                        config=guarded_config.oracle,
                    )
                    guarded_action = final_action
                    guard_step = None
                    guard_info = {
                        "guard_enabled": True,
                        "guard_active": True,
                        "guard_activated": False,
                        "guard_should_activate": True,
                        "guard_can_activate": True,
                        "guard_dist_xy": finite_float(info.get("dist_xy")),
                        "guard_z_above_target": finite_float(info.get("peg_tip_pos")[2])
                        - finite_float(info.get("target_pos")[2]),
                    }
                else:
                    assert model is not None
                    model_obs = policy_observation(
                        obs,
                        mode=args.image_ablation,
                        rng=ablation_rng,
                        shuffle_bank=shuffle_bank,
                    )
                    policy_action, _ = model.predict(model_obs, deterministic=True)
                    policy_action = np.asarray(policy_action, dtype=np.float32)
                    if args.control_mode == "policy":
                        final_action = policy_action
                        guarded_action = None
                        guard_step = None
                        guard_info = guard_info_from_step(None, guard_enabled=False)
                    else:
                        guard_step = guarded_controller.step_with_provider(
                            guard_state_provider,
                            info,
                            policy_action,
                            scenario_name=scenario.name,
                            scenario_level=scenario.level,
                        )
                        final_action = guard_step.action
                        guarded_action = guard_step.guarded_action
                        guard_info = guard_info_from_step(guard_step, guard_enabled)

                obs, reward, terminated, truncated, info = env.step(final_action)
                episode_return += float(reward)
                step = int(info["step_count"])
                hole_projection = project_point(
                    env,
                    np.asarray(info["target_pos"], dtype=np.float64),
                    camera_id=env.wrist_camera_id,
                    width=args.width,
                    height=args.height,
                )
                peg_projection = project_point(
                    env,
                    np.asarray(info["peg_tip_pos"], dtype=np.float64),
                    camera_id=env.wrist_camera_id,
                    width=args.width,
                    height=args.height,
                )
                frame_tag = should_save_frame(
                    args=args,
                    step=step,
                    info=info,
                    guard_activated=bool(guard_info.get("guard_activated", False)),
                    terminated=terminated,
                    truncated=truncated,
                    seen_tags=saved_tags,
                    saved_count=saved_count,
                )
                must_segment = (
                    step % args.segmentation_stride == 0
                    or frame_tag is not None
                    or terminated
                    or truncated
                )
                segmentation = (
                    segmentation_counts(segmentation_renderer, env, crop_bounds=crop_bounds)
                    if must_segment
                    else empty_segmentation_counts()
                )
                if frame_tag is not None:
                    saved_tags.add(frame_tag)
                    saved_count += 1
                    saved_frame_paths.extend(
                        save_key_frame(
                            imageio=imageio,
                            args=args,
                            env=env,
                            wrist_renderer=wrist_renderer,
                            overview_renderer=overview_renderer,
                            obs=obs,
                            episode=episode + 1,
                            step=step,
                            tag=frame_tag,
                            hole_projection=hole_projection,
                            peg_projection=peg_projection,
                            crop_bounds=crop_bounds,
                        )
                    )
                rows.append(
                    build_visibility_row(
                        args=args,
                        episode=episode + 1,
                        step=step,
                        scenario_name=scenario.name,
                        scenario_level=scenario.level,
                        info=info,
                        reward=float(reward),
                        episode_return=episode_return,
                        policy_action=policy_action,
                        final_action=np.asarray(final_action, dtype=np.float64),
                        guarded_action=guarded_action,
                        guard_info=guard_info,
                        terminated=terminated,
                        truncated=truncated,
                        crop_bounds=crop_bounds,
                        hole_projection=hole_projection,
                        peg_projection=peg_projection,
                        segmentation=segmentation,
                        frame_tag=frame_tag,
                    )
                )

                if terminated or truncated:
                    episode_summaries.append(
                        {
                            "episode": episode + 1,
                            "success": bool(info["insertion_success"]),
                            "collision": bool(info["collision"]),
                            "timeout": bool(truncated and not info["insertion_success"]),
                            "steps": step,
                            "return": episode_return,
                            "final_dist_xy": finite_float(info["dist_xy"]),
                            "final_dist_z": finite_float(info["dist_z"]),
                        }
                    )
                    print(
                        "episode {episode}: success={success} collision={collision} "
                        "timeout={timeout} steps={steps} final_xy={final_dist_xy:.5f} "
                        "final_z={final_dist_z:.5f}".format(**episode_summaries[-1])
                    )
                    break
    finally:
        wrist_renderer.close()
        segmentation_renderer.close()
        overview_renderer.close()
        env.close()

    write_csv(args.visibility_output_csv, rows)
    write_markdown(
        args.visibility_output_md,
        args,
        scenario_name=scenario.name,
        scenario_level=scenario.level,
        episode_summaries=episode_summaries,
        rows=rows,
        saved_frame_paths=saved_frame_paths,
    )


if __name__ == "__main__":
    main()
