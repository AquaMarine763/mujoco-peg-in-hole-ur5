from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
for path in (str(SCRIPTS_DIR), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import collect_visual_yaw_dataset as collector
import train_visual_yaw_estimator as trainer


@dataclass(frozen=True)
class ViewCandidate:
    name: str
    wrist_camera_pos_offset: tuple[float, float, float]
    wrist_camera_rot_offset_deg: tuple[float, float, float]
    wrist_camera_fovy: float
    near_hole_crop_size: int
    near_hole_crop_source_size: int
    near_hole_crop_offset: tuple[int, int]


DEFAULT_CANDIDATES = (
    ViewCandidate(
        name="baseline",
        wrist_camera_pos_offset=(-0.04, -0.04, 0.0),
        wrist_camera_rot_offset_deg=(0.0, 0.0, 0.0),
        wrist_camera_fovy=100.0,
        near_hole_crop_size=64,
        near_hole_crop_source_size=64,
        near_hole_crop_offset=(-18, 0),
    ),
    ViewCandidate(
        name="crop_wider",
        wrist_camera_pos_offset=(-0.04, -0.04, 0.0),
        wrist_camera_rot_offset_deg=(0.0, 0.0, 0.0),
        wrist_camera_fovy=100.0,
        near_hole_crop_size=64,
        near_hole_crop_source_size=80,
        near_hole_crop_offset=(-18, 0),
    ),
    ViewCandidate(
        name="raise_center",
        wrist_camera_pos_offset=(-0.03, -0.04, 0.02),
        wrist_camera_rot_offset_deg=(0.0, 0.0, 0.0),
        wrist_camera_fovy=100.0,
        near_hole_crop_size=64,
        near_hole_crop_source_size=80,
        near_hole_crop_offset=(-14, 0),
    ),
    ViewCandidate(
        name="open_high",
        wrist_camera_pos_offset=(-0.025, -0.045, 0.04),
        wrist_camera_rot_offset_deg=(0.0, 0.0, 0.0),
        wrist_camera_fovy=110.0,
        near_hole_crop_size=64,
        near_hole_crop_source_size=96,
        near_hole_crop_offset=(-10, 0),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan wrist camera and near-hole crop settings for visual yaw estimation."
    )
    parser.add_argument("--output-root", type=Path, default=Path("results/visual_yaw_view_scan"))
    parser.add_argument("--dataset-root", type=Path, default=Path("datasets/visual_yaw_view_scan"))
    parser.add_argument("--samples-per-candidate", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--validation-split", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=908000)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument(
        "--candidate-names",
        nargs="+",
        default=[candidate.name for candidate in DEFAULT_CANDIDATES],
    )
    parser.add_argument("--compressed", action="store_true")
    return parser.parse_args()


def candidate_by_name(name: str) -> ViewCandidate:
    for candidate in DEFAULT_CANDIDATES:
        if candidate.name == name:
            return candidate
    raise ValueError(f"unknown candidate: {name}")


def build_collect_args(candidate: ViewCandidate, args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        model_path=Path("assets/ur5e_full/ur5e_peg_in_hole_full.xml"),
        output=Path("unused.npz"),
        output_md=None,
        samples=args.samples_per_candidate,
        seed=args.seed,
        geometry_profiles=list(collector.DEFAULT_PROFILES),
        geometry_fixture_mode="true_mesh",
        geometry_true_fixture_variant="tight_yaw",
        randomize_domain=False,
        domain_randomization_level="visual_camera",
        image_width=100,
        image_height=100,
        near_hole_crop_size=candidate.near_hole_crop_size,
        near_hole_crop_source_size=candidate.near_hole_crop_source_size,
        near_hole_crop_offset=list(candidate.near_hole_crop_offset),
        wrist_camera_pos_offset=list(candidate.wrist_camera_pos_offset),
        wrist_camera_rot_offset_deg=list(candidate.wrist_camera_rot_offset_deg),
        wrist_camera_fovy=candidate.wrist_camera_fovy,
        tip_z_above_range=(0.035, 0.080),
        tip_xy_offset_range=(0.0, 0.006),
        settle_steps=4,
        max_ik_error=0.004,
        enable_peg_tip_visual_helpers=False,
        compressed=args.compressed,
    )


def collect_candidate_dataset(candidate: ViewCandidate, args: argparse.Namespace) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    collect_args = build_collect_args(candidate, args)
    rng = np.random.default_rng(args.seed)
    buffers = collector.empty_buffers()
    envs = {profile: collector.make_env(collect_args, profile) for profile in collect_args.geometry_profiles}
    attempts = 0
    max_attempts = args.samples_per_candidate * 8

    try:
        while len(buffers["cam_image"]) < args.samples_per_candidate and attempts < max_attempts:
            index = len(buffers["cam_image"])
            profile = collect_args.geometry_profiles[index % len(collect_args.geometry_profiles)]
            env = envs[profile]
            period_deg = collector.PROFILE_PERIOD_DEG[profile]
            env.reset(seed=int(args.seed + attempts))
            target_yaw_deg = float(rng.uniform(-0.5 * period_deg, 0.5 * period_deg))
            target_tip_pos = collector.sample_tip_target(env, rng, collect_args)
            target_xmat = collector.target_xmat_for_yaw(env, target_yaw_deg)
            ik_error, ik_iterations = collector.place_tip_pose(
                env,
                target_tip_pos,
                target_xmat,
                settle_steps=collect_args.settle_steps,
            )
            attempts += 1
            env._clear_observation_history()
            obs = env._get_obs()
            info = env._get_info()
            if ik_error > collect_args.max_ik_error:
                continue
            if not np.isfinite(float(info.get("shape_yaw_signed_error_deg", np.nan))):
                continue
            collector.append_sample(
                buffers,
                obs=obs,
                info=info,
                profile=profile,
                target_yaw_deg=target_yaw_deg,
                target_tip_pos=target_tip_pos,
                ik_error=ik_error,
                ik_iterations=ik_iterations,
            )
    finally:
        for env in envs.values():
            env.close()

    if len(buffers["cam_image"]) < args.samples_per_candidate:
        raise RuntimeError(
            f"{candidate.name}: only collected {len(buffers['cam_image'])}/{args.samples_per_candidate} samples"
        )

    metadata = {
        "schema": collector.DATASET_SCHEMA_VERSION,
        "candidate": candidate.name,
        "args": {
            "seed": args.seed,
            "samples_per_candidate": args.samples_per_candidate,
            "wrist_camera_pos_offset": candidate.wrist_camera_pos_offset,
            "wrist_camera_rot_offset_deg": candidate.wrist_camera_rot_offset_deg,
            "wrist_camera_fovy": candidate.wrist_camera_fovy,
            "near_hole_crop_size": candidate.near_hole_crop_size,
            "near_hole_crop_source_size": candidate.near_hole_crop_source_size,
            "near_hole_crop_offset": candidate.near_hole_crop_offset,
        },
        "attempts": attempts,
    }
    arrays = collector.build_arrays(buffers, metadata)
    return arrays, metadata


def train_candidate(
    candidate: ViewCandidate,
    args: argparse.Namespace,
    dataset_path: Path,
    output_path: Path,
    report_path: Path,
) -> tuple[list[trainer.EpochMetrics], dict[str, Any]]:
    train_args = argparse.Namespace(
        dataset=dataset_path,
        output=output_path,
        output_md=report_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=1e-5,
        validation_split=args.validation_split,
        seed=args.seed,
        device=args.device,
        no_profile_onehot=False,
        num_workers=args.num_workers,
    )
    model, history, metadata = trainer.train(train_args)
    trainer.save_checkpoint(output_path, model, history, metadata, train_args)
    trainer.write_report(report_path, history, metadata, train_args)
    return history, metadata


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    args.dataset_root.mkdir(parents=True, exist_ok=True)

    candidate_rows: list[dict[str, Any]] = []
    for index, name in enumerate(args.candidate_names):
        candidate = candidate_by_name(name)
        candidate_seed = args.seed + 1000 * index
        candidate_args = argparse.Namespace(**vars(args))
        candidate_args.seed = candidate_seed

        dataset_path = args.dataset_root / f"{candidate.name}.npz"
        dataset_md = args.dataset_root / f"{candidate.name}.md"
        model_path = args.output_root / f"{candidate.name}.pt"
        report_path = args.output_root / f"{candidate.name}.md"

        arrays, metadata = collect_candidate_dataset(candidate, candidate_args)
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        if args.compressed:
            np.savez_compressed(dataset_path, **arrays)
        else:
            np.savez(dataset_path, **arrays)
        dataset_report_args = build_collect_args(candidate, candidate_args)
        dataset_report_args.output = dataset_path
        dataset_report_args.output_md = dataset_md
        collector.write_report(dataset_md, collector.summarize_arrays(arrays), dataset_report_args)

        history, train_metadata = train_candidate(
            candidate,
            candidate_args,
            dataset_path,
            model_path,
            report_path,
        )
        best = min(history, key=lambda metric: metric.val_mean_abs_yaw_error_deg)
        val_breakdown = train_metadata.get("val_profile_breakdown", {})
        key_error = float(val_breakdown.get("rectangular_key", {}).get("mean_abs_yaw_error_deg", float("inf")))
        candidate_rows.append(
            {
                "candidate": candidate.name,
                "seed": candidate_seed,
                "dataset": str(dataset_path),
                "model": str(model_path),
                "report": str(report_path),
                "cam_offset": candidate.wrist_camera_pos_offset,
                "crop_offset": candidate.near_hole_crop_offset,
                "crop_source_size": candidate.near_hole_crop_source_size,
                "fovy": candidate.wrist_camera_fovy,
                "samples": int(train_metadata["samples"]),
                "best_epoch": int(train_metadata["best_epoch"]),
                "best_val_mean_yaw_error_deg": float(train_metadata["best_val_mean_abs_yaw_error_deg"]),
                "best_val_p95_yaw_error_deg": float(best.val_p95_abs_yaw_error_deg),
                "key_val_mean_yaw_error_deg": key_error,
                "square_val_mean_yaw_error_deg": float(val_breakdown.get("square_square", {}).get("mean_abs_yaw_error_deg", float("inf"))),
                "triangle_val_mean_yaw_error_deg": float(val_breakdown.get("triangle_triangle", {}).get("mean_abs_yaw_error_deg", float("inf"))),
                "hex_val_mean_yaw_error_deg": float(val_breakdown.get("hex_hex", {}).get("mean_abs_yaw_error_deg", float("inf"))),
            }
        )
        print(
            f"candidate={candidate.name} best_val={train_metadata['best_val_mean_abs_yaw_error_deg']:.3f} "
            f"key_val={key_error:.3f}"
        )

    candidate_rows.sort(key=lambda row: (row["key_val_mean_yaw_error_deg"], row["best_val_mean_yaw_error_deg"]))
    summary_path = args.output_root / "view_scan_summary.md"
    summary_lines = [
        "# Visual Yaw View Scan",
        "",
        f"- Samples per candidate: `{args.samples_per_candidate}`",
        f"- Epochs: `{args.epochs}`",
        f"- Seed: `{args.seed}`",
        "",
        "| Candidate | Cam offset | Crop offset | Crop src | FOV | Best val yaw | Key val yaw | Square val yaw | Triangle val yaw | Hex val yaw |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in candidate_rows:
        summary_lines.append(
            f"| `{row['candidate']}` | `{row['cam_offset']}` | `{row['crop_offset']}` | "
            f"{row['crop_source_size']} | {row['fovy']} | {row['best_val_mean_yaw_error_deg']:.3f} | "
            f"{row['key_val_mean_yaw_error_deg']:.3f} | {row['square_val_mean_yaw_error_deg']:.3f} | "
            f"{row['triangle_val_mean_yaw_error_deg']:.3f} | {row['hex_val_mean_yaw_error_deg']:.3f} |"
        )
    summary_lines.extend(
        [
            "",
            f"Best candidate by key error: `{candidate_rows[0]['candidate']}`",
        ]
    )
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    json_path = args.output_root / "view_scan_summary.json"
    json_path.write_text(json.dumps(candidate_rows, indent=2, default=str), encoding="utf-8")
    print(f"saved summary to {summary_path}")
    print(f"saved json to {json_path}")


if __name__ == "__main__":
    main()
