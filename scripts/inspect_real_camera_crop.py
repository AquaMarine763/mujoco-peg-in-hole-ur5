from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from peg_in_hole_mujoco.image_preprocess import (
    ImagePreprocessConfig,
    crop_xywh,
    image_stats,
    load_image,
    preprocess_camera_image,
    resize_nearest,
    save_image,
)
from peg_in_hole_mujoco.real_backend import IMAGE_SUFFIXES


DEFAULT_CROP_FRACTIONS = (0.50, 0.65, 0.80)
DEFAULT_ROTATIONS = (0, 1, 2, 3)
SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    crop_xywh: tuple[int, int, int, int]
    rotate_k: int
    flip_horizontal: bool
    flip_vertical: bool


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    count: int = 1
    details: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate real camera crop/orientation previews for choosing "
            "crop_xywh, rotate_k, and flip settings before strict real preflight."
        )
    )
    parser.add_argument("--input", type=Path, default=None, help="Single image or directory of recorded camera frames.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/real_camera_crop_inspection"))
    parser.add_argument("--summary-md", type=Path, default=Path("results/real_camera_crop_inspection_summary.md"))
    parser.add_argument("--stats-output", type=Path, default=Path("results/real_camera_crop_inspection_stats.csv"))
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--max-frames", type=int, default=6)
    parser.add_argument("--sheet-columns", type=int, default=8)
    parser.add_argument("--crop-xywh", nargs=4, type=int, action="append", default=None)
    parser.add_argument("--auto-crop-fractions", nargs="*", type=float, default=list(DEFAULT_CROP_FRACTIONS))
    parser.add_argument(
        "--auto-offset-fraction",
        type=float,
        default=0.0,
        help="Add left/right/up/down crops offset by this fraction of crop size. Use 0.15 for a wider sweep.",
    )
    parser.add_argument("--rotations", nargs="*", type=int, default=list(DEFAULT_ROTATIONS))
    parser.add_argument("--include-flips", action="store_true")
    parser.add_argument("--max-combinations", type=int, default=128)
    parser.add_argument("--synthetic-smoke", action="store_true")
    parser.add_argument("--fail-on-warn", action="store_true")
    return parser.parse_args()


def resolve_inputs(path: Path | None, *, synthetic_smoke: bool, max_frames: int) -> list[Path]:
    if synthetic_smoke:
        return []
    if path is None:
        raise ValueError("Provide --input or use --synthetic-smoke.")
    if path.is_file():
        paths = [path]
    elif path.is_dir():
        paths = sorted(item for item in path.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES)
    else:
        raise FileNotFoundError(path)
    return paths[:max_frames]


def synthetic_image(index: int) -> np.ndarray:
    y = np.linspace(0, 255, 240, dtype=np.uint8)[:, None]
    x = np.linspace(0, 255, 320, dtype=np.uint8)[None, :]
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    image[..., 0] = x
    image[..., 1] = y
    image[..., 2] = 255 - x
    center_x = 150 + int(10 * math.sin(0.5 * index))
    center_y = 112 + int(8 * math.cos(0.4 * index))
    image[center_y:center_y + 24, center_x:center_x + 24] = np.asarray([255, 255, 255], dtype=np.uint8)
    image[50:200, 95 + index:100 + index] = np.asarray([20, 20, 20], dtype=np.uint8)
    return image


def load_images(args: argparse.Namespace) -> list[tuple[str, np.ndarray]]:
    if args.synthetic_smoke:
        return [(f"synthetic_smoke_{index:03d}.png", synthetic_image(index)) for index in range(args.max_frames)]
    paths = resolve_inputs(args.input, synthetic_smoke=args.synthetic_smoke, max_frames=args.max_frames)
    return [(path.name, load_image(path)) for path in paths]


def clamp_crop(
    *,
    center_x: float,
    center_y: float,
    size: int,
    image_width: int,
    image_height: int,
) -> tuple[int, int, int, int]:
    size = max(1, min(int(size), image_width, image_height))
    x = int(round(center_x - size / 2))
    y = int(round(center_y - size / 2))
    x = max(0, min(x, image_width - size))
    y = max(0, min(y, image_height - size))
    return x, y, size, size


def auto_crop_candidates(image_shape: tuple[int, ...], fractions: list[float], offset_fraction: float) -> list[tuple[int, int, int, int]]:
    image_height, image_width = image_shape[:2]
    side_base = min(image_width, image_height)
    offsets = [(0.0, 0.0)]
    if offset_fraction > 0.0:
        offsets.extend(
            [
                (-offset_fraction, 0.0),
                (offset_fraction, 0.0),
                (0.0, -offset_fraction),
                (0.0, offset_fraction),
            ]
        )
    crops: list[tuple[int, int, int, int]] = []
    seen: set[tuple[int, int, int, int]] = set()
    for fraction in fractions:
        if fraction <= 0.0:
            continue
        size = int(round(side_base * min(fraction, 1.0)))
        for dx, dy in offsets:
            crop = clamp_crop(
                center_x=image_width / 2 + dx * size,
                center_y=image_height / 2 + dy * size,
                size=size,
                image_width=image_width,
                image_height=image_height,
            )
            if crop not in seen:
                crops.append(crop)
                seen.add(crop)
    return crops


def flip_combinations(include_flips: bool) -> list[tuple[bool, bool]]:
    if not include_flips:
        return [(False, False)]
    return [(False, False), (True, False), (False, True), (True, True)]


def build_candidates(args: argparse.Namespace, image_shape: tuple[int, ...]) -> tuple[list[Candidate], list[Issue]]:
    issues: list[Issue] = []
    crops = [tuple(values) for values in args.crop_xywh] if args.crop_xywh else auto_crop_candidates(
        image_shape,
        [float(value) for value in args.auto_crop_fractions],
        float(args.auto_offset_fraction),
    )
    if not crops:
        raise ValueError("No crop candidates were generated.")

    candidates: list[Candidate] = []
    for crop in crops:
        for rotate_k in args.rotations:
            for flip_horizontal, flip_vertical in flip_combinations(args.include_flips):
                candidate_id = f"c{len(candidates):03d}"
                candidates.append(
                    Candidate(
                        candidate_id=candidate_id,
                        crop_xywh=tuple(int(value) for value in crop),
                        rotate_k=int(rotate_k) % 4,
                        flip_horizontal=bool(flip_horizontal),
                        flip_vertical=bool(flip_vertical),
                    )
                )
    if len(candidates) > args.max_combinations:
        issues.append(
            Issue(
                severity="WARN",
                code="candidate_limit_applied",
                message="Candidate combinations were truncated by --max-combinations.",
                count=len(candidates) - args.max_combinations,
                details=f"{len(candidates)} -> {args.max_combinations}",
            )
        )
        candidates = candidates[: args.max_combinations]
    return candidates, issues


def center_crop_gray(image: np.ndarray, size: int) -> np.ndarray:
    if size <= 0:
        raise ValueError("--near-hole-crop-size must be positive.")
    array = np.asarray(image)
    if array.ndim == 3 and array.shape[-1] == 1:
        gray = array[:, :, 0]
    elif array.ndim == 2:
        gray = array
    else:
        raise ValueError(f"Expected grayscale image, got {array.shape}.")
    height, width = gray.shape[:2]
    crop_size = min(size, height, width)
    y0 = max(0, (height - crop_size) // 2)
    x0 = max(0, (width - crop_size) // 2)
    crop = gray[y0:y0 + crop_size, x0:x0 + crop_size]
    if crop.shape != (size, size):
        crop = resize_nearest(crop, width=size, height=size)
    return crop.astype(np.uint8, copy=False)


def as_gray2d(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image)
    if array.ndim == 3 and array.shape[-1] == 1:
        return array[:, :, 0]
    if array.ndim == 2:
        return array
    raise ValueError(f"Expected grayscale image, got {array.shape}.")


def preview_panel(processed: np.ndarray, near_crop: np.ndarray) -> np.ndarray:
    left = as_gray2d(processed)
    right = resize_nearest(near_crop, width=left.shape[1], height=left.shape[0])
    gutter = np.full((left.shape[0], 6), 180, dtype=np.uint8)
    return np.concatenate([left, gutter, right], axis=1)


def image_to_rgb(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image)
    if array.ndim == 2:
        return np.repeat(array[:, :, None], 3, axis=2)
    if array.ndim == 3 and array.shape[-1] == 1:
        return np.repeat(array, 3, axis=2)
    if array.ndim == 3 and array.shape[-1] >= 3:
        return array[:, :, :3]
    raise ValueError(f"Unsupported image shape for sheet: {array.shape}.")


def make_sheet(images: list[np.ndarray], *, columns: int, pad: int = 8) -> np.ndarray:
    if not images:
        return np.zeros((1, 1), dtype=np.uint8)
    columns = max(1, int(columns))
    rgb_images = [image_to_rgb(image).astype(np.uint8, copy=False) for image in images]
    tile_height = max(image.shape[0] for image in rgb_images)
    tile_width = max(image.shape[1] for image in rgb_images)
    rows = int(math.ceil(len(rgb_images) / columns))
    sheet_height = rows * tile_height + (rows + 1) * pad
    sheet_width = columns * tile_width + (columns + 1) * pad
    sheet = np.full((sheet_height, sheet_width, 3), 235, dtype=np.uint8)
    for index, image in enumerate(rgb_images):
        row = index // columns
        col = index % columns
        y0 = pad + row * (tile_height + pad)
        x0 = pad + col * (tile_width + pad)
        sheet[y0:y0 + image.shape[0], x0:x0 + image.shape[1]] = image
    return sheet


def extended_stats(image: np.ndarray) -> dict[str, float]:
    array = np.asarray(image).astype(np.float64)
    if array.size == 0:
        return {
            "zero_fraction": float("nan"),
            "max_255_fraction": float("nan"),
            "p01": float("nan"),
            "p99": float("nan"),
        }
    return {
        "zero_fraction": float(np.mean(array <= 0.0)),
        "max_255_fraction": float(np.mean(array >= 255.0)),
        "p01": float(np.percentile(array, 1.0)),
        "p99": float(np.percentile(array, 99.0)),
    }


def prefixed(prefix: str, values: dict[str, Any]) -> dict[str, Any]:
    return {f"{prefix}_{key}": value for key, value in values.items()}


def crop_preview(image: np.ndarray, crop: tuple[int, int, int, int]) -> np.ndarray:
    cropped = crop_xywh(image, crop)
    height = 120
    width = max(1, int(round(cropped.shape[1] * height / max(1, cropped.shape[0]))))
    return resize_nearest(cropped, width=width, height=height)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def process_candidates(
    *,
    images: list[tuple[str, np.ndarray]],
    candidates: list[Candidate],
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], dict[str, list[np.ndarray]], list[Issue]]:
    rows: list[dict[str, Any]] = []
    candidate_panels: dict[str, list[np.ndarray]] = {candidate.candidate_id: [] for candidate in candidates}
    issues: list[Issue] = []
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for candidate in candidates:
        config = ImagePreprocessConfig(
            width=args.width,
            height=args.height,
            crop_xywh=candidate.crop_xywh,
            rotate_k=candidate.rotate_k,
            flip_horizontal=candidate.flip_horizontal,
            flip_vertical=candidate.flip_vertical,
        )
        candidate_dir = args.output_dir / candidate.candidate_id
        candidate_dir.mkdir(parents=True, exist_ok=True)
        for frame_index, (name, image) in enumerate(images):
            row: dict[str, Any] = {
                "candidate_id": candidate.candidate_id,
                "frame_index": frame_index,
                "input": name,
                "crop_xywh": ",".join(str(value) for value in candidate.crop_xywh),
                "rotate_k": candidate.rotate_k,
                "flip_horizontal": candidate.flip_horizontal,
                "flip_vertical": candidate.flip_vertical,
            }
            try:
                processed = preprocess_camera_image(image, config=config)
                near_crop = center_crop_gray(processed, args.near_hole_crop_size)
                panel = preview_panel(processed, near_crop)
                panel_path = candidate_dir / f"frame_{frame_index:03d}_panel.png"
                processed_path = candidate_dir / f"frame_{frame_index:03d}_cam_image.png"
                near_path = candidate_dir / f"frame_{frame_index:03d}_near_hole_crop.png"
                save_image(panel_path, panel)
                save_image(processed_path, as_gray2d(processed))
                save_image(near_path, near_crop)
                candidate_panels[candidate.candidate_id].append(panel)
                row.update(
                    {
                        "panel_output": str(panel_path),
                        "cam_image_output": str(processed_path),
                        "near_hole_crop_output": str(near_path),
                        "input_shape": "x".join(str(value) for value in np.asarray(image).shape),
                        "processed_shape": "x".join(str(value) for value in processed.shape),
                        "near_hole_crop_shape": "x".join(str(value) for value in near_crop.shape),
                    }
                )
                row.update(prefixed("input", image_stats(image)))
                row.update(prefixed("processed", image_stats(processed)))
                row.update(prefixed("processed", extended_stats(processed)))
                row.update(prefixed("near_hole_crop", image_stats(near_crop)))
                row.update(prefixed("near_hole_crop", extended_stats(near_crop)))
            except Exception as exc:
                issues.append(
                    Issue(
                        severity="ERROR",
                        code="candidate_processing_failed",
                        message="A crop/orientation candidate failed to process.",
                        details=f"{candidate.candidate_id} {name}: {exc}",
                    )
                )
                row["error"] = str(exc)
            rows.append(row)
    return rows, candidate_panels, issues


def parse_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return math.nan
    return number if math.isfinite(number) else math.nan


def mean(values: list[float]) -> float:
    values = [value for value in values if math.isfinite(value)]
    if not values:
        return float("nan")
    return float(sum(values) / len(values))


def aggregate_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_candidate.setdefault(str(row["candidate_id"]), []).append(row)
    summaries: list[dict[str, Any]] = []
    for candidate_id, candidate_rows in sorted(by_candidate.items()):
        ok_rows = [row for row in candidate_rows if not row.get("error")]
        means = [parse_float(row.get("processed_mean")) for row in ok_rows]
        stds = [parse_float(row.get("processed_std")) for row in ok_rows]
        near_stds = [parse_float(row.get("near_hole_crop_std")) for row in ok_rows]
        zero_fractions = [parse_float(row.get("processed_zero_fraction")) for row in ok_rows]
        max_fractions = [parse_float(row.get("processed_max_255_fraction")) for row in ok_rows]
        template = candidate_rows[0]
        summaries.append(
            {
                "candidate_id": candidate_id,
                "crop_xywh": template.get("crop_xywh", ""),
                "rotate_k": template.get("rotate_k", ""),
                "flip_horizontal": template.get("flip_horizontal", ""),
                "flip_vertical": template.get("flip_vertical", ""),
                "frames_ok": len(ok_rows),
                "frames_failed": len(candidate_rows) - len(ok_rows),
                "processed_mean_avg": mean(means),
                "processed_std_avg": mean(stds),
                "near_hole_crop_std_avg": mean(near_stds),
                "processed_zero_fraction_max": max(zero_fractions) if zero_fractions else float("nan"),
                "processed_255_fraction_max": max(max_fractions) if max_fractions else float("nan"),
            }
        )
    return summaries


def save_preview_sheets(
    *,
    images: list[tuple[str, np.ndarray]],
    candidates: list[Candidate],
    candidate_panels: dict[str, list[np.ndarray]],
    args: argparse.Namespace,
) -> dict[str, str]:
    sheet_paths: dict[str, str] = {}
    if images:
        first_frame_crops = [crop_preview(images[0][1], candidate.crop_xywh) for candidate in candidates]
        crop_sheet_path = args.output_dir / "crop_candidates_first_frame_sheet.png"
        save_image(crop_sheet_path, make_sheet(first_frame_crops, columns=args.sheet_columns))
        sheet_paths["crop_candidates_first_frame_sheet"] = str(crop_sheet_path)

        first_panels = [
            panels[0]
            for panels in (candidate_panels[candidate.candidate_id] for candidate in candidates)
            if panels
        ]
        first_processed_sheet_path = args.output_dir / "processed_candidates_first_frame_sheet.png"
        save_image(first_processed_sheet_path, make_sheet(first_panels, columns=args.sheet_columns))
        sheet_paths["processed_candidates_first_frame_sheet"] = str(first_processed_sheet_path)

    for candidate in candidates:
        panels = candidate_panels.get(candidate.candidate_id, [])
        if not panels:
            continue
        sheet_path = args.output_dir / candidate.candidate_id / "frames_sheet.png"
        save_image(sheet_path, make_sheet(panels, columns=min(args.sheet_columns, max(1, len(panels)))))
        sheet_paths[f"{candidate.candidate_id}_frames_sheet"] = str(sheet_path)
    return sheet_paths


def collect_issues(
    *,
    images: list[tuple[str, np.ndarray]],
    candidates: list[Candidate],
    candidate_summaries: list[dict[str, Any]],
    existing_issues: list[Issue],
    args: argparse.Namespace,
) -> list[Issue]:
    issues = list(existing_issues)
    if not images:
        issues.append(Issue("ERROR", "no_input_frames", "No input frames were loaded."))
    if not candidates:
        issues.append(Issue("ERROR", "no_candidates", "No crop/orientation candidates were generated."))
    failed_candidates = [summary for summary in candidate_summaries if int(summary.get("frames_failed", 0)) > 0]
    if failed_candidates:
        issues.append(
            Issue(
                "ERROR",
                "candidate_failures",
                "At least one candidate failed on one or more frames.",
                count=len(failed_candidates),
                details=str(failed_candidates[0].get("candidate_id")),
            )
        )
    saturated = [
        summary
        for summary in candidate_summaries
        if parse_float(summary.get("processed_zero_fraction_max")) > 0.98
        or parse_float(summary.get("processed_255_fraction_max")) > 0.98
    ]
    if saturated:
        issues.append(
            Issue(
                "WARN",
                "saturated_candidates",
                "Some candidates are almost fully black or white after preprocessing.",
                count=len(saturated),
                details=str(saturated[0].get("candidate_id")),
            )
        )
    low_contrast = [
        summary
        for summary in candidate_summaries
        if parse_float(summary.get("processed_std_avg")) < 2.0
    ]
    if low_contrast:
        issues.append(
            Issue(
                "WARN",
                "low_contrast_candidates",
                "Some candidates have very low processed image contrast.",
                count=len(low_contrast),
                details=str(low_contrast[0].get("candidate_id")),
            )
        )
    return sorted(issues, key=lambda issue: (SEVERITY_ORDER[issue.severity], issue.code))


def verdict(issues: list[Issue], fail_on_warn: bool) -> str:
    if any(issue.severity == "ERROR" for issue in issues):
        return "FAIL"
    if any(issue.severity == "WARN" for issue in issues):
        return "FAIL" if fail_on_warn else "WARN"
    return "PASS"


def format_value(value: Any) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.9g}"
    return str(value)


def render_summary(
    *,
    args: argparse.Namespace,
    result: str,
    images: list[tuple[str, np.ndarray]],
    candidates: list[Candidate],
    candidate_summaries: list[dict[str, Any]],
    sheet_paths: dict[str, str],
    issues: list[Issue],
) -> str:
    ranked = sorted(
        candidate_summaries,
        key=lambda row: parse_float(row.get("near_hole_crop_std_avg")),
        reverse=True,
    )
    lines = [
        "# Real Camera Crop Inspection",
        "",
        f"- Verdict: **{result}**",
        f"- Input: `{args.input if args.input is not None else 'synthetic_smoke'}`",
        f"- Frames loaded: `{len(images)}`",
        f"- Candidates: `{len(candidates)}`",
        f"- Output dir: `{args.output_dir}`",
        f"- Stats CSV: `{args.stats_output}`",
        f"- Policy image size: `{args.width}x{args.height}`",
        f"- Near-hole crop size: `{args.near_hole_crop_size}`",
        "",
        "## Preview Sheets",
        "",
    ]
    for key in sorted(sheet_paths):
        if not key.endswith("_frames_sheet"):
            lines.append(f"- `{key}`: `{sheet_paths[key]}`")
    lines.append("- Per-candidate frame sheets are saved under each `cNNN` output directory.")

    lines.extend(
        [
            "",
            "## Candidate Ranking",
            "",
            "Rank is only a heuristic based on near-hole crop contrast. Pick the final config by inspecting the preview sheets.",
            "",
            "| Rank | Candidate | crop_xywh | rotate_k | flip_h | flip_v | mean | std | near_std | sheet |",
            "| ---: | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for rank, row in enumerate(ranked[:20], start=1):
        candidate_id = str(row["candidate_id"])
        sheet = sheet_paths.get(f"{candidate_id}_frames_sheet", "")
        lines.append(
            "| {} | `{}` | `{}` | {} | {} | {} | {} | {} | {} | `{}` |".format(
                rank,
                candidate_id,
                row.get("crop_xywh", ""),
                row.get("rotate_k", ""),
                row.get("flip_horizontal", ""),
                row.get("flip_vertical", ""),
                format_value(parse_float(row.get("processed_mean_avg"))),
                format_value(parse_float(row.get("processed_std_avg"))),
                format_value(parse_float(row.get("near_hole_crop_std_avg"))),
                sheet,
            )
        )

    if ranked:
        top = ranked[0]
        lines.extend(
            [
                "",
                "## Config Snippet",
                "",
                "Copy these values only after visual inspection confirms the candidate is correct:",
                "",
                "```yaml",
                f"crop_xywh: [{top.get('crop_xywh', '').replace(',', ', ')}]",
                f"rotate_k: {top.get('rotate_k', 0)}",
                f"flip_horizontal: {str(top.get('flip_horizontal', False)).lower()}",
                f"flip_vertical: {str(top.get('flip_vertical', False)).lower()}",
                "include_near_hole_crop: true",
                f"near_hole_crop_size: {args.near_hole_crop_size}",
                "```",
            ]
        )

    lines.extend(
        [
            "",
            "## Issues",
            "",
            "| Severity | Code | Count | Details |",
            "| --- | --- | ---: | --- |",
        ]
    )
    if not issues:
        lines.append("| INFO | `no_issues` | 0 | No issues detected. |")
    else:
        for issue in issues:
            lines.append(f"| {issue.severity} | `{issue.code}` | {issue.count} | {issue.details or issue.message} |")
    lines.append("")
    return "\n".join(lines)


def write_json_summary(
    path: Path,
    *,
    result: str,
    candidates: list[Candidate],
    candidate_summaries: list[dict[str, Any]],
    sheet_paths: dict[str, str],
    issues: list[Issue],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "verdict": result,
        "candidates": [asdict(candidate) for candidate in candidates],
        "candidate_summaries": candidate_summaries,
        "sheet_paths": sheet_paths,
        "issues": [asdict(issue) for issue in issues],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.width <= 0 or args.height <= 0:
        raise ValueError("--width and --height must be positive.")
    if args.near_hole_crop_size <= 0:
        raise ValueError("--near-hole-crop-size must be positive.")
    if args.max_frames <= 0:
        raise ValueError("--max-frames must be positive.")
    if args.sheet_columns <= 0:
        raise ValueError("--sheet-columns must be positive.")
    if args.max_combinations <= 0:
        raise ValueError("--max-combinations must be positive.")

    images = load_images(args)
    if not images:
        raise ValueError("No input images were loaded.")
    candidates, candidate_issues = build_candidates(args, images[0][1].shape)
    rows, candidate_panels, processing_issues = process_candidates(images=images, candidates=candidates, args=args)
    write_csv(args.stats_output, rows)
    candidate_summaries = aggregate_candidates(rows)
    sheet_paths = save_preview_sheets(images=images, candidates=candidates, candidate_panels=candidate_panels, args=args)
    issues = collect_issues(
        images=images,
        candidates=candidates,
        candidate_summaries=candidate_summaries,
        existing_issues=candidate_issues + processing_issues,
        args=args,
    )
    result = verdict(issues, args.fail_on_warn)

    args.summary_md.parent.mkdir(parents=True, exist_ok=True)
    args.summary_md.write_text(
        render_summary(
            args=args,
            result=result,
            images=images,
            candidates=candidates,
            candidate_summaries=candidate_summaries,
            sheet_paths=sheet_paths,
            issues=issues,
        ),
        encoding="utf-8",
    )
    if args.output_json is not None:
        write_json_summary(
            args.output_json,
            result=result,
            candidates=candidates,
            candidate_summaries=candidate_summaries,
            sheet_paths=sheet_paths,
            issues=issues,
        )

    print(f"verdict={result}")
    print(f"frames={len(images)}")
    print(f"candidates={len(candidates)}")
    print(f"saved_output_dir={args.output_dir}")
    print(f"saved_summary_to={args.summary_md}")
    print(f"saved_stats_to={args.stats_output}")
    for issue in issues:
        print(f"{issue.severity}: {issue.code} ({issue.count}) {issue.message}")
    if result == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
