from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from peg_in_hole_mujoco.real_backend import RealTargetCalibration


AXES = ("x", "y", "z")
POSITION_COLUMNS = (
    ("target_x", "hole_x", "x"),
    ("target_y", "hole_y", "y"),
    ("target_z", "hole_z", "z"),
)
SYNTHETIC_ROWS = (
    (0.5500, 0.0500, 0.6500),
    (0.5502, 0.0499, 0.6501),
    (0.5499, 0.0501, 0.6499),
    (0.5501, 0.0500, 0.6500),
)


@dataclass(frozen=True)
class CalibrationSample:
    target_pos: tuple[float, float, float]
    pose_frame: str
    timestamp: float | None


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and validate a real hole target calibration file."
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input-csv",
        type=Path,
        default=None,
        help="CSV with target_x/y/z or hole_x/y/z measurements in meters.",
    )
    input_group.add_argument("--target-pos", nargs=3, type=float, default=None)
    input_group.add_argument(
        "--synthetic-smoke",
        action="store_true",
        help="Generate a deterministic synthetic measurement set for smoke testing.",
    )
    parser.add_argument("--output", type=Path, default=Path("configs/real_hole_target_calibration.yaml"))
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=Path("results/real_target_calibration_builder_summary.md"),
    )
    parser.add_argument("--synthetic-input-output", type=Path, default=None)
    parser.add_argument("--target-id", default="real_hole")
    parser.add_argument("--target-source", default="fixture_calibration")
    parser.add_argument("--pose-frame", default="robot_base")
    parser.add_argument("--timestamp", type=float, default=None)
    parser.add_argument("--method", choices=["mean", "median", "first", "last"], default="mean")
    parser.add_argument("--max-xy-std", type=float, default=0.001)
    parser.add_argument("--max-z-std", type=float, default=0.001)
    parser.add_argument("--max-xy-range", type=float, default=0.003)
    parser.add_argument("--max-z-range", type=float, default=0.003)
    parser.add_argument("--fail-on-warn", action="store_true")
    return parser.parse_args()


def first_text(row: dict[str, str], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is not None and value.strip():
            return value.strip()
    return None


def required_float(row: dict[str, str], keys: tuple[str, ...], row_index: int) -> float:
    value = first_text(row, keys)
    if value is None:
        raise ValueError(f"row {row_index} is missing one of: {', '.join(keys)}")
    return float(value)


def optional_float(row: dict[str, str], keys: tuple[str, ...]) -> float | None:
    value = first_text(row, keys)
    return None if value is None else float(value)


def sample_from_row(row: dict[str, str], row_index: int, default_pose_frame: str) -> CalibrationSample:
    target_pos = tuple(
        required_float(row, aliases, row_index)
        for aliases in POSITION_COLUMNS
    )
    pose_frame = first_text(row, ("target_frame", "hole_frame", "pose_frame", "frame")) or default_pose_frame
    timestamp = optional_float(row, ("target_timestamp", "hole_timestamp", "timestamp", "time", "t"))
    return CalibrationSample(
        target_pos=target_pos,  # type: ignore[arg-type]
        pose_frame=pose_frame,
        timestamp=timestamp,
    )


def load_samples_from_csv(path: Path, default_pose_frame: str) -> list[CalibrationSample]:
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError(f"calibration measurement CSV is empty: {path}")
    return [
        sample_from_row(row, row_index=index, default_pose_frame=default_pose_frame)
        for index, row in enumerate(rows)
    ]


def synthetic_samples(default_pose_frame: str) -> list[CalibrationSample]:
    return [
        CalibrationSample(target_pos=row, pose_frame=default_pose_frame, timestamp=float(index) * 0.05)
        for index, row in enumerate(SYNTHETIC_ROWS)
    ]


def write_synthetic_input(path: Path, samples: list[CalibrationSample]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "step",
                "timestamp",
                "target_frame",
                "target_x",
                "target_y",
                "target_z",
            ],
        )
        writer.writeheader()
        for index, sample in enumerate(samples):
            writer.writerow(
                {
                    "step": index,
                    "timestamp": "" if sample.timestamp is None else sample.timestamp,
                    "target_frame": sample.pose_frame,
                    "target_x": sample.target_pos[0],
                    "target_y": sample.target_pos[1],
                    "target_z": sample.target_pos[2],
                }
            )


def choose_position(samples: list[CalibrationSample], method: str) -> tuple[float, float, float]:
    values_by_axis = [[sample.target_pos[index] for sample in samples] for index in range(3)]
    if method == "first":
        return samples[0].target_pos
    if method == "last":
        return samples[-1].target_pos
    if method == "median":
        return tuple(float(statistics.median(values)) for values in values_by_axis)  # type: ignore[return-value]
    return tuple(float(statistics.fmean(values)) for values in values_by_axis)  # type: ignore[return-value]


def population_std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float(statistics.pstdev(values))


def axis_metrics(samples: list[CalibrationSample]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for index, axis in enumerate(AXES):
        values = [sample.target_pos[index] for sample in samples]
        metrics[f"{axis}_mean"] = float(statistics.fmean(values))
        metrics[f"{axis}_std"] = population_std(values)
        metrics[f"{axis}_min"] = min(values)
        metrics[f"{axis}_max"] = max(values)
        metrics[f"{axis}_range"] = max(values) - min(values)
    xy_positions = [(sample.target_pos[0], sample.target_pos[1]) for sample in samples]
    xy_mean = (metrics["x_mean"], metrics["y_mean"])
    xy_errors = [
        math.hypot(position[0] - xy_mean[0], position[1] - xy_mean[1])
        for position in xy_positions
    ]
    metrics["xy_radial_error_max"] = max(xy_errors) if xy_errors else 0.0
    return metrics


def collect_issues(
    samples: list[CalibrationSample],
    metrics: dict[str, float],
    args: argparse.Namespace,
) -> list[Issue]:
    issues: list[Issue] = []
    frames = sorted({sample.pose_frame for sample in samples})
    if len(frames) > 1:
        issues.append(
            Issue(
                severity="ERROR",
                code="mixed_pose_frames",
                message=f"Measurement rows use multiple frames: {', '.join(frames)}.",
            )
        )
    if frames and frames[0] != args.pose_frame:
        issues.append(
            Issue(
                severity="ERROR",
                code="pose_frame_differs_from_requested",
                message=(
                    f"Input frame is '{frames[0]}', output frame is '{args.pose_frame}', "
                    "and this script does not transform frames."
                ),
            )
        )
    xy_std = math.hypot(metrics["x_std"], metrics["y_std"])
    if xy_std > args.max_xy_std:
        issues.append(
            Issue(
                severity="WARN",
                code="xy_std_high",
                message=f"XY measurement std is {xy_std:.6g} m, above {args.max_xy_std:.6g} m.",
            )
        )
    if metrics["z_std"] > args.max_z_std:
        issues.append(
            Issue(
                severity="WARN",
                code="z_std_high",
                message=f"Z measurement std is {metrics['z_std']:.6g} m, above {args.max_z_std:.6g} m.",
            )
        )
    xy_range = math.hypot(metrics["x_range"], metrics["y_range"])
    if xy_range > args.max_xy_range:
        issues.append(
            Issue(
                severity="WARN",
                code="xy_range_high",
                message=f"XY measurement range is {xy_range:.6g} m, above {args.max_xy_range:.6g} m.",
            )
        )
    if metrics["z_range"] > args.max_z_range:
        issues.append(
            Issue(
                severity="WARN",
                code="z_range_high",
                message=f"Z measurement range is {metrics['z_range']:.6g} m, above {args.max_z_range:.6g} m.",
            )
        )
    return issues


def latest_timestamp(samples: list[CalibrationSample], override: float | None) -> float | None:
    if override is not None:
        return override
    timestamps = [sample.timestamp for sample in samples if sample.timestamp is not None]
    if not timestamps:
        return None
    return max(float(value) for value in timestamps)


def write_yaml(
    path: Path,
    *,
    target_id: str,
    target_source: str,
    pose_frame: str,
    target_pos: tuple[float, float, float],
    timestamp: float | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Fixed hole/fixture pose in the declared target frame.",
        f"target_id: {target_id}",
        f"target_source: {target_source}",
        f"pose_frame: {pose_frame}",
        "target_pos: [{:.9f}, {:.9f}, {:.9f}]".format(*target_pos),
    ]
    if timestamp is not None:
        lines.append(f"target_timestamp: {timestamp:.9f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verdict(issues: list[Issue], fail_on_warn: bool) -> str:
    if any(issue.severity == "ERROR" for issue in issues):
        return "FAIL"
    if any(issue.severity == "WARN" for issue in issues):
        return "FAIL" if fail_on_warn else "WARN"
    return "PASS"


def render_summary(
    *,
    input_description: str,
    output: Path,
    target_pos: tuple[float, float, float],
    metrics: dict[str, float],
    issues: list[Issue],
    samples: list[CalibrationSample],
    result: str,
    args: argparse.Namespace,
) -> str:
    frames = sorted({sample.pose_frame for sample in samples})
    lines = [
        "# Real Target Calibration Builder Summary",
        "",
        f"- Input: `{input_description}`",
        f"- Output: `{output}`",
        f"- Verdict: **{result}**",
        f"- Method: `{args.method}`",
        f"- Samples: `{len(samples)}`",
        f"- Pose frame: `{args.pose_frame}`",
        f"- Input frames: `{', '.join(frames) if frames else 'none'}`",
        "- Target position: `[{:.9f}, {:.9f}, {:.9f}]`".format(*target_pos),
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in sorted(metrics):
        lines.append(f"| `{key}` | {metrics[key]:.9g} |")
    lines.extend(
        [
            "",
            "## Issues",
            "",
            "| Severity | Code | Message |",
            "| --- | --- | --- |",
        ]
    )
    if not issues:
        lines.append("| INFO | `no_issues` | No issues detected. |")
    else:
        for issue in issues:
            lines.append(f"| {issue.severity} | `{issue.code}` | {issue.message} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    input_description = "direct target position"
    if args.synthetic_smoke:
        samples = synthetic_samples(args.pose_frame)
        input_description = "synthetic smoke measurements"
        if args.synthetic_input_output is not None:
            write_synthetic_input(args.synthetic_input_output, samples)
    elif args.target_pos is not None:
        samples = [
            CalibrationSample(
                target_pos=tuple(float(value) for value in args.target_pos),
                pose_frame=args.pose_frame,
                timestamp=args.timestamp,
            )
        ]
    else:
        samples = load_samples_from_csv(args.input_csv, args.pose_frame)
        input_description = str(args.input_csv)

    target_pos = choose_position(samples, args.method)
    metrics = axis_metrics(samples)
    issues = collect_issues(samples, metrics, args)
    timestamp = latest_timestamp(samples, args.timestamp)
    write_yaml(
        args.output,
        target_id=args.target_id,
        target_source=args.target_source,
        pose_frame=args.pose_frame,
        target_pos=target_pos,
        timestamp=timestamp,
    )
    loaded = RealTargetCalibration.from_file(args.output)
    roundtrip_error = math.sqrt(
        sum((loaded.target_pos[index] - target_pos[index]) ** 2 for index in range(3))
    )
    if roundtrip_error > 1e-9:
        issues.append(
            Issue(
                severity="ERROR",
                code="roundtrip_target_position_mismatch",
                message=(
                    "Generated calibration did not round-trip through RealTargetCalibration "
                    f"(error={roundtrip_error:.6g} m)."
                ),
            )
        )
    result = verdict(issues, args.fail_on_warn)
    args.summary_md.parent.mkdir(parents=True, exist_ok=True)
    args.summary_md.write_text(
        render_summary(
            input_description=input_description,
            output=args.output,
            target_pos=target_pos,
            metrics=metrics,
            issues=issues,
            samples=samples,
            result=result,
            args=args,
        ),
        encoding="utf-8",
    )

    print(f"saved target calibration to {args.output}")
    print(f"saved summary to {args.summary_md}")
    print(f"verdict={result}")
    if result == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
