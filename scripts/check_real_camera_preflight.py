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
    image_stats,
    load_image,
    preprocess_camera_image,
    save_image,
)
from peg_in_hole_mujoco.real_backend import IMAGE_SUFFIXES


SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    count: int = 1
    details: str = ""


@dataclass(frozen=True)
class FrameResult:
    name: str
    output_path: str
    processed: np.ndarray | None
    row: dict[str, Any]
    error: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight-check real camera frames before policy dry-run."
    )
    parser.add_argument("--input", type=Path, default=None, help="Single image file or directory.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/real_camera_preflight_frames"))
    parser.add_argument("--stats-output", type=Path, default=Path("results/real_camera_preflight_stats.csv"))
    parser.add_argument("--summary-md", type=Path, default=Path("results/real_camera_preflight_summary.md"))
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
    parser.add_argument("--crop-xywh", nargs=4, type=int, default=None)
    parser.add_argument("--rotate-k", type=int, default=0)
    parser.add_argument("--flip-horizontal", action="store_true")
    parser.add_argument("--flip-vertical", action="store_true")
    parser.add_argument("--max-frames", type=int, default=20)
    parser.add_argument("--min-frames", type=int, default=1)
    parser.add_argument("--min-processed-mean", type=float, default=2.0)
    parser.add_argument("--max-processed-mean", type=float, default=253.0)
    parser.add_argument("--min-processed-std", type=float, default=2.0)
    parser.add_argument("--max-zero-fraction", type=float, default=0.98)
    parser.add_argument("--max-255-fraction", type=float, default=0.98)
    parser.add_argument("--min-frame-diff-mean", type=float, default=0.0)
    parser.add_argument("--allow-identical-frames", action="store_true")
    parser.add_argument("--fail-on-warn", action="store_true")
    parser.add_argument(
        "--synthetic-smoke",
        action="store_true",
        help="Generate deterministic synthetic frames without real camera input.",
    )
    parser.add_argument("--synthetic-frames", type=int, default=4)
    return parser.parse_args()


def resolve_inputs(path: Path | None, synthetic_smoke: bool, max_frames: int | None) -> list[Path]:
    if synthetic_smoke:
        return []
    if path is None:
        raise ValueError("Provide --input or use --synthetic-smoke.")
    if path.is_file():
        paths = [path]
    elif path.is_dir():
        paths = sorted(
            item for item in path.iterdir()
            if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES
        )
    else:
        raise FileNotFoundError(path)
    if max_frames is not None:
        paths = paths[:max_frames]
    return paths


def synthetic_image(index: int) -> np.ndarray:
    y = np.linspace(0, 255, 180, dtype=np.uint8)[:, None]
    x = np.linspace(0, 255, 240, dtype=np.uint8)[None, :]
    image = np.zeros((180, 240, 3), dtype=np.uint8)
    image[..., 0] = x
    image[..., 1] = y
    image[..., 2] = 255 - x
    center_x = 112 + 3 * index
    center_y = 86 + 2 * index
    image[center_y:center_y + 20, center_x:center_x + 20] = np.asarray([255, 255, 255], dtype=np.uint8)
    image[40:150, 40 + index:43 + index] = np.asarray([20, 20, 20], dtype=np.uint8)
    return image


def array_shape_text(image: np.ndarray | None) -> str:
    if image is None:
        return ""
    return "x".join(str(value) for value in image.shape)


def extended_stats(image: np.ndarray) -> dict[str, float]:
    array = np.asarray(image)
    if array.size == 0:
        return {
            "zero_fraction": float("nan"),
            "max_255_fraction": float("nan"),
            "finite_fraction": float("nan"),
            "p01": float("nan"),
            "p99": float("nan"),
        }
    numeric = array.astype(np.float64)
    return {
        "zero_fraction": float(np.mean(numeric <= 0.0)),
        "max_255_fraction": float(np.mean(numeric >= 255.0)),
        "finite_fraction": float(np.mean(np.isfinite(numeric))),
        "p01": float(np.percentile(numeric, 1.0)),
        "p99": float(np.percentile(numeric, 99.0)),
    }


def flatten_stats(prefix: str, stats: dict[str, Any]) -> dict[str, Any]:
    return {f"{prefix}_{key}": value for key, value in stats.items()}


def process_frame(
    *,
    name: str,
    image: np.ndarray,
    output_dir: Path,
    config: ImagePreprocessConfig,
) -> FrameResult:
    processed = preprocess_camera_image(image, config=config)
    output_path = output_dir / f"{Path(name).stem}_processed.png"
    save_image(output_path, processed[..., 0])
    row: dict[str, Any] = {
        "input": name,
        "output": str(output_path),
        "crop_xywh": "" if config.crop_xywh is None else ",".join(str(value) for value in config.crop_xywh),
        "rotate_k": config.rotate_k,
        "flip_horizontal": config.flip_horizontal,
        "flip_vertical": config.flip_vertical,
        "input_shape": array_shape_text(image),
        "processed_shape": array_shape_text(processed),
    }
    row.update(flatten_stats("input", image_stats(image)))
    row.update(flatten_stats("processed", image_stats(processed)))
    row.update(flatten_stats("processed", extended_stats(processed)))
    return FrameResult(
        name=name,
        output_path=str(output_path),
        processed=processed,
        row=row,
    )


def failed_frame_result(name: str, error: Exception) -> FrameResult:
    return FrameResult(
        name=name,
        output_path="",
        processed=None,
        error=str(error),
        row={
            "input": name,
            "output": "",
            "error": str(error),
        },
    )


def write_frame_stats_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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


def process_inputs(args: argparse.Namespace, config: ImagePreprocessConfig) -> list[FrameResult]:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results: list[FrameResult] = []
    if args.synthetic_smoke:
        for index in range(args.synthetic_frames):
            name = f"synthetic_smoke_{index:03d}.png"
            try:
                results.append(
                    process_frame(
                        name=name,
                        image=synthetic_image(index),
                        output_dir=args.output_dir,
                        config=config,
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive report path
                results.append(failed_frame_result(name, exc))
        return results

    paths = resolve_inputs(args.input, args.synthetic_smoke, args.max_frames)
    for path in paths:
        try:
            results.append(
                process_frame(
                    name=path.name,
                    image=load_image(path),
                    output_dir=args.output_dir,
                    config=config,
                )
            )
        except Exception as exc:
            results.append(failed_frame_result(str(path), exc))
    return results


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def finite_results(results: list[FrameResult]) -> list[FrameResult]:
    return [result for result in results if result.processed is not None and result.error is None]


def mean_abs_diff(left: np.ndarray, right: np.ndarray) -> float:
    left_array = left.astype(np.float32)
    right_array = right.astype(np.float32)
    if left_array.shape != right_array.shape:
        return float("nan")
    return float(np.mean(np.abs(left_array - right_array)))


def summarize_results(results: list[FrameResult], args: argparse.Namespace) -> dict[str, Any]:
    ok_results = finite_results(results)
    metrics: dict[str, Any] = {
        "frames_total": len(results),
        "frames_ok": len(ok_results),
        "frames_failed": len(results) - len(ok_results),
        "expected_processed_shape": f"{args.height}x{args.width}x1",
    }
    if ok_results:
        means = [parse_float(result.row.get("processed_mean")) for result in ok_results]
        stds = [parse_float(result.row.get("processed_std")) for result in ok_results]
        zero_fractions = [parse_float(result.row.get("processed_zero_fraction")) for result in ok_results]
        max_fractions = [parse_float(result.row.get("processed_max_255_fraction")) for result in ok_results]
        metrics.update(
            {
                "processed_mean_min": float(np.nanmin(means)),
                "processed_mean_max": float(np.nanmax(means)),
                "processed_mean_avg": float(np.nanmean(means)),
                "processed_std_min": float(np.nanmin(stds)),
                "processed_std_max": float(np.nanmax(stds)),
                "processed_std_avg": float(np.nanmean(stds)),
                "processed_zero_fraction_max": float(np.nanmax(zero_fractions)),
                "processed_255_fraction_max": float(np.nanmax(max_fractions)),
            }
        )
    diffs: list[float] = []
    for left, right in zip(ok_results, ok_results[1:]):
        if left.processed is not None and right.processed is not None:
            diffs.append(mean_abs_diff(left.processed, right.processed))
    if diffs:
        metrics["frame_diff_mean_min"] = float(np.nanmin(diffs))
        metrics["frame_diff_mean_max"] = float(np.nanmax(diffs))
        metrics["frame_diff_mean_avg"] = float(np.nanmean(diffs))
        metrics["identical_adjacent_pairs"] = int(sum(diff == 0.0 for diff in diffs))
    else:
        metrics["identical_adjacent_pairs"] = 0
    return metrics


def collect_issues(
    results: list[FrameResult],
    metrics: dict[str, Any],
    args: argparse.Namespace,
) -> list[Issue]:
    issues: list[Issue] = []
    ok_results = finite_results(results)
    if len(results) < args.min_frames:
        issues.append(
            Issue(
                severity="ERROR",
                code="too_few_input_frames",
                message=f"Only {len(results)} frame(s) were found, below --min-frames {args.min_frames}.",
            )
        )
    if len(ok_results) < args.min_frames:
        issues.append(
            Issue(
                severity="ERROR",
                code="too_few_valid_frames",
                message=f"Only {len(ok_results)} frame(s) were processed successfully.",
            )
        )
    failed = [result for result in results if result.error is not None]
    if failed:
        issues.append(
            Issue(
                severity="ERROR",
                code="frame_processing_failed",
                message="At least one frame could not be loaded or preprocessed.",
                count=len(failed),
                details=f"{failed[0].name}: {failed[0].error}",
            )
        )

    expected_shape = f"{args.height}x{args.width}x1"
    bad_shape = [
        result
        for result in ok_results
        if str(result.row.get("processed_shape", "")) != expected_shape
    ]
    if bad_shape:
        issues.append(
            Issue(
                severity="ERROR",
                code="processed_shape_mismatch",
                message=f"Processed image shape differs from expected {expected_shape}.",
                count=len(bad_shape),
                details=bad_shape[0].name,
            )
        )

    low_std = [
        result for result in ok_results
        if parse_float(result.row.get("processed_std")) < args.min_processed_std
    ]
    if low_std:
        issues.append(
            Issue(
                severity="ERROR",
                code="processed_contrast_too_low",
                message=f"Processed image std is below {args.min_processed_std:g}.",
                count=len(low_std),
                details=low_std[0].name,
            )
        )

    low_mean = [
        result for result in ok_results
        if parse_float(result.row.get("processed_mean")) < args.min_processed_mean
    ]
    high_mean = [
        result for result in ok_results
        if parse_float(result.row.get("processed_mean")) > args.max_processed_mean
    ]
    if low_mean:
        issues.append(
            Issue(
                severity="WARN",
                code="processed_mean_low",
                message=f"Processed image mean is below {args.min_processed_mean:g}.",
                count=len(low_mean),
                details=low_mean[0].name,
            )
        )
    if high_mean:
        issues.append(
            Issue(
                severity="WARN",
                code="processed_mean_high",
                message=f"Processed image mean is above {args.max_processed_mean:g}.",
                count=len(high_mean),
                details=high_mean[0].name,
            )
        )

    high_zero = [
        result for result in ok_results
        if parse_float(result.row.get("processed_zero_fraction")) > args.max_zero_fraction
    ]
    high_255 = [
        result for result in ok_results
        if parse_float(result.row.get("processed_max_255_fraction")) > args.max_255_fraction
    ]
    if high_zero:
        issues.append(
            Issue(
                severity="WARN",
                code="processed_zero_fraction_high",
                message=f"More than {args.max_zero_fraction:g} of pixels are zero.",
                count=len(high_zero),
                details=high_zero[0].name,
            )
        )
    if high_255:
        issues.append(
            Issue(
                severity="WARN",
                code="processed_255_fraction_high",
                message=f"More than {args.max_255_fraction:g} of pixels are 255.",
                count=len(high_255),
                details=high_255[0].name,
            )
        )

    identical_pairs = int(metrics.get("identical_adjacent_pairs", 0))
    if identical_pairs and not args.allow_identical_frames:
        issues.append(
            Issue(
                severity="WARN",
                code="identical_adjacent_frames",
                message="Adjacent processed frames are identical.",
                count=identical_pairs,
            )
        )

    min_diff = parse_float(metrics.get("frame_diff_mean_min"))
    if math.isfinite(min_diff) and min_diff < args.min_frame_diff_mean:
        issues.append(
            Issue(
                severity="WARN",
                code="frame_diff_below_threshold",
                message=f"Minimum adjacent frame mean absolute difference is below {args.min_frame_diff_mean:g}.",
                details=f"{min_diff:.6g}",
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


def render_markdown(
    *,
    args: argparse.Namespace,
    metrics: dict[str, Any],
    issues: list[Issue],
    result: str,
) -> str:
    lines = [
        "# Real Camera Preflight Summary",
        "",
        f"- Verdict: **{result}**",
        f"- Input: `{args.input if args.input is not None else 'synthetic_smoke'}`",
        f"- Output frames: `{args.output_dir}`",
        f"- Stats CSV: `{args.stats_output}`",
        f"- Image size: `{args.width}x{args.height}`",
        f"- Crop: `{args.crop_xywh}`",
        f"- Rotate k: `{args.rotate_k}`",
        f"- Flip horizontal: `{args.flip_horizontal}`",
        f"- Flip vertical: `{args.flip_vertical}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in sorted(metrics):
        lines.append(f"| `{key}` | {format_value(metrics[key])} |")

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
            details = issue.details or issue.message
            lines.append(f"| {issue.severity} | `{issue.code}` | {issue.count} | {details} |")
    lines.append("")
    return "\n".join(lines)


def write_issues_json(path: Path, result: str, metrics: dict[str, Any], issues: list[Issue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "verdict": result,
        "metrics": metrics,
        "issues": [asdict(issue) for issue in issues],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.width <= 0 or args.height <= 0:
        raise ValueError("--width and --height must be positive.")
    if args.max_frames is not None and args.max_frames <= 0:
        raise ValueError("--max-frames must be positive.")
    if args.min_frames <= 0:
        raise ValueError("--min-frames must be positive.")
    if args.synthetic_smoke and args.synthetic_frames <= 0:
        raise ValueError("--synthetic-frames must be positive.")

    config = ImagePreprocessConfig(
        width=args.width,
        height=args.height,
        crop_xywh=None if args.crop_xywh is None else tuple(args.crop_xywh),
        rotate_k=args.rotate_k,
        flip_horizontal=args.flip_horizontal,
        flip_vertical=args.flip_vertical,
    )
    results = process_inputs(args, config)
    rows = [result.row for result in results]
    if rows:
        write_frame_stats_csv(args.stats_output, rows)
    metrics = summarize_results(results, args)
    issues = collect_issues(results, metrics, args)
    result = verdict(issues, args.fail_on_warn)

    args.summary_md.parent.mkdir(parents=True, exist_ok=True)
    args.summary_md.write_text(
        render_markdown(args=args, metrics=metrics, issues=issues, result=result),
        encoding="utf-8",
    )
    if args.output_json is not None:
        write_issues_json(args.output_json, result, metrics, issues)

    print(f"verdict={result}")
    print(f"processed_frames={metrics.get('frames_ok', 0)}")
    print(f"failed_frames={metrics.get('frames_failed', 0)}")
    print(f"saved_processed_frames_to={args.output_dir}")
    print(f"saved_stats_to={args.stats_output}")
    print(f"saved_summary_to={args.summary_md}")
    for issue in issues:
        print(f"{issue.severity}: {issue.code} ({issue.count}) {issue.message}")
    if result == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
