from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import mujoco
import numpy as np

from audit_visual_visibility import center_crop_bounds, finite_float, point_in_crop, project_point
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
    hole_in_crop: int = 0
    peg_in_crop: int = 0
    both_in_crop: int = 0
    projected_distance_sum: float = 0.0
    projected_distance_count: int = 0
    segmented_rows: int = 0
    hole_crop_visible: int = 0
    peg_crop_visible: int = 0
    both_crop_visible: int = 0
    hole_crop_pixels_sum: int = 0
    peg_crop_pixels_sum: int = 0

    def add_projection(
        self,
        *,
        hole_in_crop: bool,
        peg_in_crop: bool,
        projected_distance: float,
    ) -> None:
        self.rows += 1
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
        min_hole_pixels: int,
        min_peg_pixels: int,
    ) -> None:
        self.segmented_rows += 1
        hole_visible = hole_pixels >= min_hole_pixels
        peg_visible = peg_pixels >= min_peg_pixels
        self.hole_crop_visible += int(hole_visible)
        self.peg_crop_visible += int(peg_visible)
        self.both_crop_visible += int(hole_visible and peg_visible)
        self.hole_crop_pixels_sum += int(hole_pixels)
        self.peg_crop_pixels_sum += int(peg_pixels)

    def as_row(self, prefix: str) -> dict[str, Any]:
        return {
            f"{prefix}_rows": self.rows,
            f"{prefix}_segmented_rows": self.segmented_rows,
            f"{prefix}_hole_in_crop_rate": rate(self.hole_in_crop, self.rows),
            f"{prefix}_peg_in_crop_rate": rate(self.peg_in_crop, self.rows),
            f"{prefix}_both_in_crop_rate": rate(self.both_in_crop, self.rows),
            f"{prefix}_mean_projected_distance_px": rate(
                self.projected_distance_sum,
                self.projected_distance_count,
            ),
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
            f"{prefix}_mean_hole_crop_pixels": rate(
                self.hole_crop_pixels_sum,
                self.segmented_rows,
            ),
            f"{prefix}_mean_peg_crop_pixels": rate(
                self.peg_crop_pixels_sum,
                self.segmented_rows,
            ),
        }


@dataclass
class CandidateStats:
    offset_x: int
    offset_y: int
    bounds: tuple[int, int, int, int]
    subsets: dict[str, SubsetStats] = field(
        default_factory=lambda: {
            "all": SubsetStats(),
            "low_z": SubsetStats(),
            "near_xy": SubsetStats(),
            "insert_band": SubsetStats(),
        }
    )

    def as_row(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "crop_x0": self.bounds[0],
            "crop_y0": self.bounds[1],
            "crop_x1": self.bounds[2],
            "crop_y1": self.bounds[3],
        }
        for name, stats in self.subsets.items():
            row.update(stats.as_row(name))
        return row


def parse_args() -> argparse.Namespace:
    parser = build_eval_parser("Scan fixed near-hole crop offsets for peg/hole visibility.")
    parser.add_argument(
        "--audit-scenario",
        choices=sorted(SCENARIOS.keys()),
        default="hard_full_light_bucket",
    )
    parser.add_argument(
        "--scan-x-offsets",
        nargs="+",
        type=int,
        default=(-32, -24, -18, -12, -6, 0, 6, 12),
    )
    parser.add_argument(
        "--scan-y-offsets",
        nargs="+",
        type=int,
        default=(-24, -16, -8, 0, 8, 16, 24),
    )
    parser.add_argument("--segmentation-stride", type=int, default=10)
    parser.add_argument("--low-z-threshold", type=float, default=0.060)
    parser.add_argument("--near-xy-threshold", type=float, default=0.030)
    parser.add_argument("--insertion-xy-threshold", type=float, default=0.012)
    parser.add_argument("--min-hole-pixels", type=int, default=5)
    parser.add_argument("--min-peg-pixels", type=int, default=5)
    parser.add_argument(
        "--scan-output-csv",
        type=Path,
        default=Path("results/ur5e_full/high_start/hard/visual_audit/crop_offset_scan.csv"),
    )
    parser.add_argument(
        "--scan-output-md",
        type=Path,
        default=Path("results/ur5e_full/high_start/hard/visual_audit/crop_offset_scan.md"),
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


def update_candidates(
    *,
    candidates: list[CandidateStats],
    args: argparse.Namespace,
    info: dict[str, Any],
    hole_projection: dict[str, Any],
    peg_projection: dict[str, Any],
    hole_mask: np.ndarray | None,
    peg_mask: np.ndarray | None,
) -> None:
    names = subset_names(args, info)
    distance = projected_distance(hole_projection, peg_projection)
    for candidate in candidates:
        hole_in_crop = point_in_crop(hole_projection, candidate.bounds)
        peg_in_crop = point_in_crop(peg_projection, candidate.bounds)
        for name in names:
            candidate.subsets[name].add_projection(
                hole_in_crop=hole_in_crop,
                peg_in_crop=peg_in_crop,
                projected_distance=distance,
            )
        if hole_mask is None or peg_mask is None:
            continue
        x0, y0, x1, y1 = candidate.bounds
        hole_pixels = int(hole_mask[y0:y1, x0:x1].sum())
        peg_pixels = int(peg_mask[y0:y1, x0:x1].sum())
        for name in names:
            candidate.subsets[name].add_segmentation(
                hole_pixels=hole_pixels,
                peg_pixels=peg_pixels,
                min_hole_pixels=args.min_hole_pixels,
                min_peg_pixels=args.min_peg_pixels,
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
    print(f"saved crop offset scan CSV to {path}")


def sort_key(row: dict[str, Any]) -> tuple[float, float, float, float]:
    return (
        finite_float(row.get("insert_band_both_crop_visible_rate"), -1.0),
        finite_float(row.get("insert_band_both_in_crop_rate"), -1.0),
        finite_float(row.get("near_xy_both_crop_visible_rate"), -1.0),
        -abs(float(row["offset_x"])) - 0.1 * abs(float(row["offset_y"])),
    )


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
        "# Crop Offset Visibility Scan",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Model: `{args.model}`",
        f"- MuJoCo model path: `{args.model_path or 'default'}`",
        f"- Scenario: `{scenario_name}` / `{scenario_level}`",
        f"- Episodes: `{args.episodes}`",
        f"- Seed: `{args.seed}`",
        f"- Current env crop offset during rollout: `{tuple(args.near_hole_crop_offset)}`",
        f"- Scanned X offsets: `{list(args.scan_x_offsets)}`",
        f"- Scanned Y offsets: `{list(args.scan_y_offsets)}`",
        f"- Segmentation stride: `{args.segmentation_stride}`",
        "",
        "## Rollout Outcome",
        "",
        f"- Success rate: `{successes / max(args.episodes, 1):.3f}`",
        f"- Collision rate: `{collisions / max(args.episodes, 1):.3f}`",
        f"- Timeout rate: `{timeouts / max(args.episodes, 1):.3f}`",
        "",
        "## Top Crop Offsets",
        "",
        "| Rank | Offset | Bounds | Insert both visible | Insert both projected | Near both visible | Near both projected | All both projected |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, row in enumerate(sorted_rows[:12], start=1):
        lines.append(
            "| {rank} | ({offset_x}, {offset_y}) | {crop_x0}:{crop_y0}:{crop_x1}:{crop_y1} | "
            "{insert_band_both_crop_visible_rate:.3f} | {insert_band_both_in_crop_rate:.3f} | "
            "{near_xy_both_crop_visible_rate:.3f} | {near_xy_both_in_crop_rate:.3f} | "
            "{all_both_in_crop_rate:.3f} |".format(rank=rank, **row)
        )
    if sorted_rows:
        best = sorted_rows[0]
        lines.extend(
            [
                "",
                "## Recommendation",
                "",
                f"- Best smoke candidate: `near_hole_crop_offset: [{best['offset_x']}, {best['offset_y']}]`",
                "- Treat this as a visibility candidate only. A policy trained on the center crop should not be promoted with this offset until data collection and BC/RL fine-tuning use the same offset.",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved crop offset scan report to {path}")


def main() -> None:
    args = parse_args()
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive.")
    if args.segmentation_stride <= 0:
        raise ValueError("--segmentation-stride must be positive.")
    if args.observation_mode != "image":
        raise ValueError("Crop visibility scan requires --observation-mode image.")

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
    segmentation_renderer = mujoco.Renderer(env.model, height=args.height, width=args.width)
    segmentation_renderer.enable_segmentation_rendering()
    candidates = [
        CandidateStats(
            offset_x=int(offset_x),
            offset_y=int(offset_y),
            bounds=center_crop_bounds(
                args.width,
                args.height,
                args.near_hole_crop_size,
                (int(offset_x), int(offset_y)),
            ),
        )
        for offset_y in args.scan_y_offsets
        for offset_x in args.scan_x_offsets
    ]
    ablation_rng = np.random.default_rng(args.seed + 1_000_003)
    shuffle_bank: list[Any] = []
    episode_summaries: list[dict[str, Any]] = []

    try:
        for episode in range(args.episodes):
            obs, info = env.reset(seed=args.seed + episode)
            guarded_controller.reset()
            episode_return = 0.0
            for step in range(args.max_steps + 1):
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
                sample_segmentation = step % args.segmentation_stride == 0
                hole_mask = peg_mask = None
                if sample_segmentation:
                    hole_mask, peg_mask = visibility_masks(segmentation_renderer, env)
                update_candidates(
                    candidates=candidates,
                    args=args,
                    info=info,
                    hole_projection=hole_projection,
                    peg_projection=peg_projection,
                    hole_mask=hole_mask,
                    peg_mask=peg_mask,
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
