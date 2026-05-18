from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import mujoco
import numpy as np

from audit_visual_visibility import (
    center_crop_bounds,
    draw_circle,
    draw_rect,
    finite_float,
    point_in_crop,
    project_point,
    render_rgb,
    upscale_nearest,
)
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


@dataclass
class SubsetStats:
    rows: int = 0
    hole_in_image: int = 0
    peg_in_image: int = 0
    both_in_image: int = 0
    hole_in_crop: int = 0
    peg_in_crop: int = 0
    both_in_crop: int = 0
    projected_distance_sum: float = 0.0
    projected_distance_count: int = 0
    segmented_rows: int = 0
    hole_visible: int = 0
    peg_visible: int = 0
    both_visible: int = 0
    hole_crop_visible: int = 0
    peg_crop_visible: int = 0
    both_crop_visible: int = 0
    hole_pixels_sum: int = 0
    peg_pixels_sum: int = 0
    hole_crop_pixels_sum: int = 0
    peg_crop_pixels_sum: int = 0

    def add_projection(
        self,
        *,
        hole_in_image: bool,
        peg_in_image: bool,
        hole_in_crop: bool,
        peg_in_crop: bool,
        projected_distance: float,
    ) -> None:
        self.rows += 1
        self.hole_in_image += int(hole_in_image)
        self.peg_in_image += int(peg_in_image)
        self.both_in_image += int(hole_in_image and peg_in_image)
        self.hole_in_crop += int(hole_in_crop)
        self.peg_in_crop += int(peg_in_crop)
        self.both_in_crop += int(hole_in_crop and peg_in_crop)
        if np.isfinite(projected_distance):
            self.projected_distance_sum += float(projected_distance)
            self.projected_distance_count += 1

    def add_segmentation(
        self,
        *,
        hole_pixels: int,
        peg_pixels: int,
        hole_crop_pixels: int,
        peg_crop_pixels: int,
        min_hole_pixels: int,
        min_peg_pixels: int,
    ) -> None:
        self.segmented_rows += 1
        hole_visible = hole_pixels >= min_hole_pixels
        peg_visible = peg_pixels >= min_peg_pixels
        hole_crop_visible = hole_crop_pixels >= min_hole_pixels
        peg_crop_visible = peg_crop_pixels >= min_peg_pixels
        self.hole_visible += int(hole_visible)
        self.peg_visible += int(peg_visible)
        self.both_visible += int(hole_visible and peg_visible)
        self.hole_crop_visible += int(hole_crop_visible)
        self.peg_crop_visible += int(peg_crop_visible)
        self.both_crop_visible += int(hole_crop_visible and peg_crop_visible)
        self.hole_pixels_sum += int(hole_pixels)
        self.peg_pixels_sum += int(peg_pixels)
        self.hole_crop_pixels_sum += int(hole_crop_pixels)
        self.peg_crop_pixels_sum += int(peg_crop_pixels)

    def as_row(self, prefix: str) -> dict[str, Any]:
        return {
            f"{prefix}_rows": self.rows,
            f"{prefix}_segmented_rows": self.segmented_rows,
            f"{prefix}_hole_in_image_rate": rate(self.hole_in_image, self.rows),
            f"{prefix}_peg_in_image_rate": rate(self.peg_in_image, self.rows),
            f"{prefix}_both_in_image_rate": rate(self.both_in_image, self.rows),
            f"{prefix}_hole_in_crop_rate": rate(self.hole_in_crop, self.rows),
            f"{prefix}_peg_in_crop_rate": rate(self.peg_in_crop, self.rows),
            f"{prefix}_both_in_crop_rate": rate(self.both_in_crop, self.rows),
            f"{prefix}_mean_projected_distance_px": rate(
                self.projected_distance_sum,
                self.projected_distance_count,
            ),
            f"{prefix}_hole_visible_rate": rate(self.hole_visible, self.segmented_rows),
            f"{prefix}_peg_visible_rate": rate(self.peg_visible, self.segmented_rows),
            f"{prefix}_both_visible_rate": rate(self.both_visible, self.segmented_rows),
            f"{prefix}_hole_crop_visible_rate": rate(
                self.hole_crop_visible,
                self.segmented_rows,
            ),
            f"{prefix}_peg_crop_visible_rate": rate(
                self.peg_crop_visible,
                self.segmented_rows,
            ),
            f"{prefix}_both_crop_visible_rate": rate(
                self.both_crop_visible,
                self.segmented_rows,
            ),
            f"{prefix}_mean_hole_pixels": rate(self.hole_pixels_sum, self.segmented_rows),
            f"{prefix}_mean_peg_pixels": rate(self.peg_pixels_sum, self.segmented_rows),
            f"{prefix}_mean_hole_crop_pixels": rate(
                self.hole_crop_pixels_sum,
                self.segmented_rows,
            ),
            f"{prefix}_mean_peg_crop_pixels": rate(
                self.peg_crop_pixels_sum,
                self.segmented_rows,
            ),
        }


@dataclass(frozen=True)
class CameraCandidate:
    candidate_id: int
    pos_offset: tuple[float, float, float]
    rot_offset_deg: tuple[float, float, float]
    fovy: float
    crop_offset: tuple[int, int]
    crop_bounds: tuple[int, int, int, int]

    @property
    def pose_penalty(self) -> float:
        dx, dy, dz = self.pos_offset
        roll, pitch, yaw = self.rot_offset_deg
        return float(
            abs(dx) + abs(dy) + abs(dz)
            + 0.001 * (abs(roll) + abs(pitch) + abs(yaw))
            + 0.0005 * abs(self.fovy - 100.0)
            + 0.0002 * (abs(self.crop_offset[0]) + abs(self.crop_offset[1]))
        )


@dataclass
class CandidateStats:
    candidate: CameraCandidate
    subsets: dict[str, SubsetStats] = field(
        default_factory=lambda: {
            "all": SubsetStats(),
            "low_z": SubsetStats(),
            "near_xy": SubsetStats(),
            "insert_band": SubsetStats(),
        }
    )

    def as_row(self) -> dict[str, Any]:
        candidate = self.candidate
        row: dict[str, Any] = {
            "candidate_id": candidate.candidate_id,
            "pos_offset_x": candidate.pos_offset[0],
            "pos_offset_y": candidate.pos_offset[1],
            "pos_offset_z": candidate.pos_offset[2],
            "rot_offset_roll_deg": candidate.rot_offset_deg[0],
            "rot_offset_pitch_deg": candidate.rot_offset_deg[1],
            "rot_offset_yaw_deg": candidate.rot_offset_deg[2],
            "fovy": candidate.fovy,
            "crop_offset_x": candidate.crop_offset[0],
            "crop_offset_y": candidate.crop_offset[1],
            "crop_x0": candidate.crop_bounds[0],
            "crop_y0": candidate.crop_bounds[1],
            "crop_x1": candidate.crop_bounds[2],
            "crop_y1": candidate.crop_bounds[3],
            "pose_penalty": candidate.pose_penalty,
        }
        for name, stats in self.subsets.items():
            row.update(stats.as_row(name))
        return row


def parse_args() -> argparse.Namespace:
    parser = build_eval_parser("Scan wrist camera pose, FOV, and crop candidates for visibility.")
    parser.add_argument(
        "--audit-scenario",
        choices=sorted(SCENARIOS.keys()),
        default="hard_full_light_bucket",
    )
    parser.add_argument("--sample-stride", type=int, default=10)
    parser.add_argument("--scan-pos-x-offsets", nargs="+", type=float, default=(0.0,))
    parser.add_argument("--scan-pos-y-offsets", nargs="+", type=float, default=(0.0,))
    parser.add_argument("--scan-pos-z-offsets", nargs="+", type=float, default=(0.0,))
    parser.add_argument("--scan-roll-deg", nargs="+", type=float, default=(0.0,))
    parser.add_argument("--scan-pitch-deg", nargs="+", type=float, default=(0.0,))
    parser.add_argument("--scan-yaw-deg", nargs="+", type=float, default=(0.0,))
    parser.add_argument("--scan-fovy", nargs="+", type=float, default=(100.0,))
    parser.add_argument("--scan-crop-x-offsets", nargs="+", type=int, default=(0, -18))
    parser.add_argument("--scan-crop-y-offsets", nargs="+", type=int, default=(0,))
    parser.add_argument("--low-z-threshold", type=float, default=0.060)
    parser.add_argument("--near-xy-threshold", type=float, default=0.030)
    parser.add_argument("--insertion-xy-threshold", type=float, default=0.012)
    parser.add_argument("--min-hole-pixels", type=int, default=5)
    parser.add_argument("--min-peg-pixels", type=int, default=5)
    parser.add_argument("--frame-dir", type=Path, default=None)
    parser.add_argument("--save-candidate-ids", nargs="*", type=int, default=())
    parser.add_argument("--max-saved-frames-per-candidate", type=int, default=8)
    parser.add_argument("--image-upscale", type=int, default=4)
    parser.add_argument(
        "--scan-output-csv",
        type=Path,
        default=Path("results/ur5e_full/high_start/hard/visual_audit/wrist_camera_pose_scan.csv"),
    )
    parser.add_argument(
        "--scan-output-md",
        type=Path,
        default=Path("results/ur5e_full/high_start/hard/visual_audit/wrist_camera_pose_scan.md"),
    )
    return parse_args_with_config(parser)


def rate(numerator: float, denominator: int) -> float:
    return float(numerator / denominator) if denominator > 0 else float("nan")


def subset_names(args: argparse.Namespace, info: dict[str, Any]) -> list[str]:
    names = ["all"]
    dist_xy = finite_float(info.get("dist_xy"))
    dist_z = finite_float(info.get("dist_z"))
    if dist_z <= args.low_z_threshold:
        names.append("low_z")
    if dist_xy <= args.near_xy_threshold:
        names.append("near_xy")
    if dist_xy <= args.insertion_xy_threshold and dist_z <= args.low_z_threshold:
        names.append("insert_band")
    return names


def projected_distance(hole_projection: dict[str, Any], peg_projection: dict[str, Any]) -> float:
    hole_u = finite_float(hole_projection["u"])
    hole_v = finite_float(hole_projection["v"])
    peg_u = finite_float(peg_projection["u"])
    peg_v = finite_float(peg_projection["v"])
    if not (
        np.isfinite(hole_u)
        and np.isfinite(hole_v)
        and np.isfinite(peg_u)
        and np.isfinite(peg_v)
    ):
        return float("nan")
    return float(np.hypot(hole_u - peg_u, hole_v - peg_v))


def visibility_masks(renderer: mujoco.Renderer, env: Any) -> tuple[np.ndarray, np.ndarray]:
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
    return hole_mask, peg_mask


def make_candidates(args: argparse.Namespace) -> list[CandidateStats]:
    candidates: list[CandidateStats] = []
    candidate_id = 0
    for pos_x in args.scan_pos_x_offsets:
        for pos_y in args.scan_pos_y_offsets:
            for pos_z in args.scan_pos_z_offsets:
                for roll in args.scan_roll_deg:
                    for pitch in args.scan_pitch_deg:
                        for yaw in args.scan_yaw_deg:
                            for fovy in args.scan_fovy:
                                for crop_y in args.scan_crop_y_offsets:
                                    for crop_x in args.scan_crop_x_offsets:
                                        candidate_id += 1
                                        candidates.append(
                                            CandidateStats(
                                                candidate=CameraCandidate(
                                                    candidate_id=candidate_id,
                                                    pos_offset=(float(pos_x), float(pos_y), float(pos_z)),
                                                    rot_offset_deg=(
                                                        float(roll),
                                                        float(pitch),
                                                        float(yaw),
                                                    ),
                                                    fovy=float(fovy),
                                                    crop_offset=(int(crop_x), int(crop_y)),
                                                    crop_bounds=center_crop_bounds(
                                                        args.width,
                                                        args.height,
                                                        args.near_hole_crop_size,
                                                        (int(crop_x), int(crop_y)),
                                                    ),
                                                )
                                            )
                                        )
    return candidates


def apply_candidate_camera(
    env: Any,
    candidate: CameraCandidate,
    *,
    base_pos: np.ndarray,
    base_quat: np.ndarray,
    base_fovy: float,
) -> None:
    camera_id = env.wrist_camera_id
    env.model.cam_pos[camera_id] = base_pos + np.asarray(candidate.pos_offset, dtype=np.float64)
    delta_quat = env._euler_xyz_to_quat(np.deg2rad(np.asarray(candidate.rot_offset_deg, dtype=np.float64)))
    camera_quat = env._quat_multiply(base_quat, delta_quat)
    env.model.cam_quat[camera_id] = camera_quat / np.linalg.norm(camera_quat)
    env.model.cam_fovy[camera_id] = candidate.fovy if np.isfinite(candidate.fovy) else base_fovy
    mujoco.mj_forward(env.model, env.data)


def restore_camera(
    env: Any,
    *,
    base_pos: np.ndarray,
    base_quat: np.ndarray,
    base_fovy: float,
) -> None:
    camera_id = env.wrist_camera_id
    env.model.cam_pos[camera_id] = base_pos
    env.model.cam_quat[camera_id] = base_quat
    env.model.cam_fovy[camera_id] = base_fovy
    mujoco.mj_forward(env.model, env.data)


def update_candidate(
    *,
    stats: CandidateStats,
    args: argparse.Namespace,
    info: dict[str, Any],
    hole_projection: dict[str, Any],
    peg_projection: dict[str, Any],
    hole_mask: np.ndarray,
    peg_mask: np.ndarray,
) -> None:
    names = subset_names(args, info)
    candidate = stats.candidate
    distance = projected_distance(hole_projection, peg_projection)
    hole_in_image = bool(hole_projection["in_frame"])
    peg_in_image = bool(peg_projection["in_frame"])
    hole_in_crop = point_in_crop(hole_projection, candidate.crop_bounds)
    peg_in_crop = point_in_crop(peg_projection, candidate.crop_bounds)
    x0, y0, x1, y1 = candidate.crop_bounds
    hole_pixels = int(hole_mask.sum())
    peg_pixels = int(peg_mask.sum())
    hole_crop_pixels = int(hole_mask[y0:y1, x0:x1].sum())
    peg_crop_pixels = int(peg_mask[y0:y1, x0:x1].sum())
    for name in names:
        stats.subsets[name].add_projection(
            hole_in_image=hole_in_image,
            peg_in_image=peg_in_image,
            hole_in_crop=hole_in_crop,
            peg_in_crop=peg_in_crop,
            projected_distance=distance,
        )
        stats.subsets[name].add_segmentation(
            hole_pixels=hole_pixels,
            peg_pixels=peg_pixels,
            hole_crop_pixels=hole_crop_pixels,
            peg_crop_pixels=peg_crop_pixels,
            min_hole_pixels=args.min_hole_pixels,
            min_peg_pixels=args.min_peg_pixels,
        )


def gray_from_rgb(image: np.ndarray) -> np.ndarray:
    rgb = np.asarray(image, dtype=np.float32)
    gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    return np.clip(gray, 0, 255).astype(np.uint8)


def save_candidate_frame(
    *,
    imageio: Any,
    frame_dir: Path,
    renderer: mujoco.Renderer,
    env: Any,
    args: argparse.Namespace,
    candidate: CameraCandidate,
    episode: int,
    step: int,
    tag: str,
    hole_projection: dict[str, Any],
    peg_projection: dict[str, Any],
) -> None:
    frame_dir.mkdir(parents=True, exist_ok=True)
    safe_tag = tag.replace(" ", "_").replace("/", "_")
    prefix = (
        frame_dir
        / f"candidate{candidate.candidate_id:03d}_ep{episode:03d}_step{step:04d}_{safe_tag}"
    )
    wrist_rgb = render_rgb(renderer, env, "wrist_cam")
    annotated = wrist_rgb.copy()
    draw_rect(annotated, candidate.crop_bounds, (0, 128, 255))
    draw_circle(annotated, hole_projection["u"], hole_projection["v"], (255, 0, 0), radius=3)
    draw_circle(annotated, peg_projection["u"], peg_projection["v"], (0, 255, 0), radius=3)
    gray = gray_from_rgb(wrist_rgb)
    x0, y0, x1, y1 = candidate.crop_bounds
    crop = gray[y0:y1, x0:x1]
    imageio.imwrite(
        prefix.with_name(prefix.name + "_wrist_annotated_x4.png"),
        upscale_nearest(annotated, args.image_upscale),
    )
    imageio.imwrite(
        prefix.with_name(prefix.name + "_near_crop_x4.png"),
        upscale_nearest(crop, args.image_upscale),
    )


def guard_info_from_step(step: Any, guard_enabled: bool) -> dict[str, Any]:
    if step is None:
        return {"guard_active": False, "guard_activated": False, "guard_enabled": guard_enabled}
    return {
        "guard_active": step.guarded,
        "guard_activated": step.guard_activated,
        "guard_enabled": step.guard_enabled,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved wrist camera pose scan CSV to {path}")


def sort_key(row: dict[str, Any]) -> tuple[float, float, float, float, float]:
    return (
        finite_float(row.get("insert_band_both_crop_visible_rate"), -1.0),
        finite_float(row.get("insert_band_both_in_crop_rate"), -1.0),
        finite_float(row.get("near_xy_both_crop_visible_rate"), -1.0),
        finite_float(row.get("all_both_visible_rate"), -1.0),
        -finite_float(row.get("pose_penalty"), 1e9),
    )


def format_float(value: Any, digits: int = 3) -> str:
    number = finite_float(value)
    if not np.isfinite(number):
        return "nan"
    return f"{number:.{digits}f}"


def write_markdown(
    path: Path,
    args: argparse.Namespace,
    *,
    scenario_name: str,
    scenario_level: str,
    episode_summaries: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sorted_rows = sorted(rows, key=sort_key, reverse=True)
    successes = sum(int(row["success"]) for row in episode_summaries)
    collisions = sum(int(row["collision"]) for row in episode_summaries)
    timeouts = sum(int(row["timeout"]) for row in episode_summaries)
    lines = [
        "# Wrist Camera Pose Visibility Scan",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Scenario: `{scenario_name}` / `{scenario_level}`",
        f"- Episodes: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Rollout control mode: `{args.control_mode}`",
        f"- Rollout env crop offset: `{tuple(args.near_hole_crop_offset)}`",
        f"- Candidate count: `{len(rows)}`",
        f"- Sample stride: `{args.sample_stride}`",
        f"- Position X offsets: `{list(args.scan_pos_x_offsets)}`",
        f"- Position Y offsets: `{list(args.scan_pos_y_offsets)}`",
        f"- Position Z offsets: `{list(args.scan_pos_z_offsets)}`",
        f"- Roll / pitch / yaw offsets: `{list(args.scan_roll_deg)}` / `{list(args.scan_pitch_deg)}` / `{list(args.scan_yaw_deg)}`",
        f"- FOV values: `{list(args.scan_fovy)}`",
        f"- Crop X/Y offsets: `{list(args.scan_crop_x_offsets)}` / `{list(args.scan_crop_y_offsets)}`",
        "",
        "## Rollout Outcome",
        "",
        f"- Success rate: `{successes / max(args.episodes, 1):.3f}`",
        f"- Collision rate: `{collisions / max(args.episodes, 1):.3f}`",
        f"- Timeout rate: `{timeouts / max(args.episodes, 1):.3f}`",
        "",
        "## Top Candidates",
        "",
        "| Rank | ID | Pos dxyz | Rot rpy deg | FOV | Crop | Insert both visible | Insert both in crop | Near both visible | Near both in crop | All both visible |",
        "| ---: | ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, row in enumerate(sorted_rows[:15], start=1):
        lines.append(
            "| {rank} | {candidate_id} | ({pos_offset_x:.3f}, {pos_offset_y:.3f}, {pos_offset_z:.3f}) | "
            "({rot_offset_roll_deg:.1f}, {rot_offset_pitch_deg:.1f}, {rot_offset_yaw_deg:.1f}) | "
            "{fovy:.1f} | ({crop_offset_x}, {crop_offset_y}) | "
            "{insert_visible} | {insert_crop} | {near_visible} | {near_crop} | {all_visible} |".format(
                rank=rank,
                candidate_id=int(row["candidate_id"]),
                pos_offset_x=float(row["pos_offset_x"]),
                pos_offset_y=float(row["pos_offset_y"]),
                pos_offset_z=float(row["pos_offset_z"]),
                rot_offset_roll_deg=float(row["rot_offset_roll_deg"]),
                rot_offset_pitch_deg=float(row["rot_offset_pitch_deg"]),
                rot_offset_yaw_deg=float(row["rot_offset_yaw_deg"]),
                fovy=float(row["fovy"]),
                crop_offset_x=int(row["crop_offset_x"]),
                crop_offset_y=int(row["crop_offset_y"]),
                insert_visible=format_float(row.get("insert_band_both_crop_visible_rate")),
                insert_crop=format_float(row.get("insert_band_both_in_crop_rate")),
                near_visible=format_float(row.get("near_xy_both_crop_visible_rate")),
                near_crop=format_float(row.get("near_xy_both_in_crop_rate")),
                all_visible=format_float(row.get("all_both_visible_rate")),
            )
        )
    if sorted_rows:
        best = sorted_rows[0]
        lines.extend(
            [
                "",
                "## Recommendation",
                "",
                "- Treat this as a visibility candidate, not a trained policy setting.",
                "- If the candidate requires changing camera pose/FOV, collect data and retrain with that observation before evaluating task success.",
                (
                    "- Best smoke candidate: "
                    f"`pos_offset=({best['pos_offset_x']:.3f}, {best['pos_offset_y']:.3f}, {best['pos_offset_z']:.3f})`, "
                    f"`rot_offset_deg=({best['rot_offset_roll_deg']:.1f}, {best['rot_offset_pitch_deg']:.1f}, {best['rot_offset_yaw_deg']:.1f})`, "
                    f"`fovy={best['fovy']:.1f}`, "
                    f"`near_hole_crop_offset=[{best['crop_offset_x']}, {best['crop_offset_y']}]`."
                ),
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved wrist camera pose scan report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")
    if args.sample_stride <= 0:
        raise ValueError("--sample-stride must be positive.")
    if args.observation_mode != "image":
        raise ValueError("Wrist camera pose scan requires --observation-mode image.")

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
    candidates = make_candidates(args)
    if not candidates:
        raise ValueError("No camera candidates to scan.")
    segmentation_renderer = mujoco.Renderer(env.model, height=args.height, width=args.width)
    segmentation_renderer.enable_segmentation_rendering()
    frame_renderer: mujoco.Renderer | None = None
    imageio = None
    save_candidate_ids = set(int(value) for value in args.save_candidate_ids)
    saved_frame_counts = {candidate_id: 0 for candidate_id in save_candidate_ids}
    if args.frame_dir is not None and save_candidate_ids:
        import imageio.v2 as imageio_module

        imageio = imageio_module
        frame_renderer = mujoco.Renderer(env.model, height=args.height, width=args.width)
    ablation_rng = np.random.default_rng(args.seed + 1_000_003)
    shuffle_bank: list[Any] = []
    episode_summaries: list[dict[str, Any]] = []

    try:
        for episode in range(args.episodes):
            obs, info = env.reset(seed=args.seed + episode)
            guarded_controller.reset()
            episode_return = 0.0
            for step in range(args.max_steps + 1):
                if step % args.sample_stride == 0:
                    base_pos = env.model.cam_pos[env.wrist_camera_id].copy()
                    base_quat = env.model.cam_quat[env.wrist_camera_id].copy()
                    base_fovy = float(env.model.cam_fovy[env.wrist_camera_id])
                    try:
                        for candidate_stats in candidates:
                            apply_candidate_camera(
                                env,
                                candidate_stats.candidate,
                                base_pos=base_pos,
                                base_quat=base_quat,
                                base_fovy=base_fovy,
                            )
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
                            hole_mask, peg_mask = visibility_masks(segmentation_renderer, env)
                            update_candidate(
                                stats=candidate_stats,
                                args=args,
                                info=info,
                                hole_projection=hole_projection,
                                peg_projection=peg_projection,
                                hole_mask=hole_mask,
                                peg_mask=peg_mask,
                            )
                            candidate_id = candidate_stats.candidate.candidate_id
                            if (
                                frame_renderer is not None
                                and imageio is not None
                                and args.frame_dir is not None
                                and candidate_id in save_candidate_ids
                                and saved_frame_counts[candidate_id]
                                < args.max_saved_frames_per_candidate
                            ):
                                names = subset_names(args, info)
                                tag = "insert_band" if "insert_band" in names else (
                                    "near_xy" if "near_xy" in names else "sample"
                                )
                                if tag != "sample" or saved_frame_counts[candidate_id] == 0:
                                    save_candidate_frame(
                                        imageio=imageio,
                                        frame_dir=args.frame_dir,
                                        renderer=frame_renderer,
                                        env=env,
                                        args=args,
                                        candidate=candidate_stats.candidate,
                                        episode=episode + 1,
                                        step=step,
                                        tag=tag,
                                        hole_projection=hole_projection,
                                        peg_projection=peg_projection,
                                    )
                                    saved_frame_counts[candidate_id] += 1
                    finally:
                        restore_camera(
                            env,
                            base_pos=base_pos,
                            base_quat=base_quat,
                            base_fovy=base_fovy,
                        )

                if step >= args.max_steps:
                    break
                if args.control_mode == "guard_only":
                    state = guard_state_provider.state_from_info(info)
                    action = oracle_action_from_state(
                        peg_tip_pos=state.peg_tip_pos,
                        target_pos=state.target_pos,
                        applied_action=state.applied_action,
                        approach_height=state.approach_height,
                        action_low=state.action_low,
                        action_high=state.action_high,
                        config=guarded_config.oracle,
                    )
                    guard_info = {
                        "guard_active": True,
                        "guard_activated": False,
                        "guard_enabled": True,
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
                    if args.control_mode == "policy":
                        action = policy_action
                        guard_info = guard_info_from_step(None, False)
                    else:
                        guarded_step = guarded_controller.step_with_provider(
                            guard_state_provider,
                            info,
                            np.asarray(policy_action, dtype=np.float32),
                            scenario_name=scenario.name,
                            scenario_level=scenario.level,
                        )
                        action = guarded_step.action
                        guard_info = guard_info_from_step(guarded_step, guard_enabled)
                obs, reward, terminated, truncated, info = env.step(action)
                del guard_info
                episode_return += float(reward)
                if terminated or truncated:
                    episode_summaries.append(
                        {
                            "episode": episode + 1,
                            "success": bool(info["insertion_success"]),
                            "collision": bool(info["collision"]),
                            "timeout": bool(truncated and not info["insertion_success"]),
                            "steps": int(info["step_count"]),
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
        segmentation_renderer.close()
        if frame_renderer is not None:
            frame_renderer.close()
        env.close()

    rows = [candidate.as_row() for candidate in candidates]
    write_csv(args.scan_output_csv, rows)
    write_markdown(
        args.scan_output_md,
        args,
        scenario_name=scenario.name,
        scenario_level=scenario.level,
        episode_summaries=episode_summaries,
        rows=rows,
    )


if __name__ == "__main__":
    main()
