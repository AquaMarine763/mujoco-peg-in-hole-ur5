from __future__ import annotations

import argparse
import csv
import math
import statistics
import time
from pathlib import Path
from typing import Any


AXES = ("x", "y", "z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record read-only UR RTDE TCP samples as hole/target measurements. "
            "This script does not command robot motion."
        )
    )
    parser.add_argument("--host", default=None, help="UR controller IP address.")
    parser.add_argument("--output", type=Path, default=Path("results/real_hole_measurements.csv"))
    parser.add_argument("--summary-md", type=Path, default=Path("results/real_hole_measurements_summary.md"))
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--frequency-hz", type=float, default=5.0)
    parser.add_argument("--pose-frame", default="robot_base")
    parser.add_argument("--target-id", default="real_hole")
    parser.add_argument("--target-source", default="rtde_tcp_measurement")
    parser.add_argument(
        "--tcp-to-target-xyz",
        nargs=3,
        type=float,
        default=(0.0, 0.0, 0.0),
        help=(
            "Offset from the active TCP/tool frame to the measured target point, expressed in "
            "the TCP frame. Use 0 0 0 when the TCP is taught exactly at the hole target point."
        ),
    )
    parser.add_argument(
        "--synthetic-smoke",
        action="store_true",
        help="Write deterministic synthetic measurements without connecting to a UR controller.",
    )
    return parser.parse_args()


class URRTDETcpPoseReader:
    def __init__(self, host: str) -> None:
        try:
            import rtde_receive  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "Install ur-rtde to read UR TCP poses: python -m pip install ur-rtde"
            ) from exc
        self.receiver = rtde_receive.RTDEReceiveInterface(host)

    def read_tcp_pose(self) -> tuple[float, float, float, float, float, float]:
        pose = self.receiver.getActualTCPPose()
        if len(pose) != 6:
            raise RuntimeError(f"Expected 6 TCP pose values, got {len(pose)}.")
        return tuple(float(value) for value in pose)


def synthetic_tcp_pose(index: int) -> tuple[float, float, float, float, float, float]:
    phase = 0.55 * index
    return (
        0.5500 + 0.00018 * math.sin(phase),
        0.0500 + 0.00012 * math.cos(phase),
        0.6500 + 0.00008 * math.sin(0.7 * phase),
        0.0,
        0.0,
        0.0,
    )


def rotvec_to_matrix(rotvec: tuple[float, float, float]) -> tuple[tuple[float, float, float], ...]:
    rx, ry, rz = rotvec
    theta = math.sqrt(rx * rx + ry * ry + rz * rz)
    if theta < 1e-12:
        return (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        )
    kx, ky, kz = rx / theta, ry / theta, rz / theta
    c = math.cos(theta)
    s = math.sin(theta)
    v = 1.0 - c
    return (
        (kx * kx * v + c, kx * ky * v - kz * s, kx * kz * v + ky * s),
        (ky * kx * v + kz * s, ky * ky * v + c, ky * kz * v - kx * s),
        (kz * kx * v - ky * s, kz * ky * v + kx * s, kz * kz * v + c),
    )


def transform_offset(
    tcp_pos: tuple[float, float, float],
    tcp_rotvec: tuple[float, float, float],
    tcp_to_target_xyz: tuple[float, float, float],
) -> tuple[float, float, float]:
    rotation = rotvec_to_matrix(tcp_rotvec)
    rotated_offset = tuple(
        sum(rotation[row][col] * tcp_to_target_xyz[col] for col in range(3))
        for row in range(3)
    )
    return tuple(tcp_pos[index] + rotated_offset[index] for index in range(3))  # type: ignore[return-value]


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "step",
        "timestamp",
        "target_id",
        "target_source",
        "target_frame",
        "target_x",
        "target_y",
        "target_z",
        "tcp_x",
        "tcp_y",
        "tcp_z",
        "tcp_rx",
        "tcp_ry",
        "tcp_rz",
        "tcp_to_target_x",
        "tcp_to_target_y",
        "tcp_to_target_z",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def population_std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float(statistics.pstdev(values))


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for axis in AXES:
        values = [float(row[f"target_{axis}"]) for row in rows]
        metrics[f"{axis}_mean"] = float(statistics.fmean(values))
        metrics[f"{axis}_std"] = population_std(values)
        metrics[f"{axis}_min"] = min(values)
        metrics[f"{axis}_max"] = max(values)
        metrics[f"{axis}_range"] = max(values) - min(values)
    xy_mean = (metrics["x_mean"], metrics["y_mean"])
    xy_errors = [
        math.hypot(float(row["target_x"]) - xy_mean[0], float(row["target_y"]) - xy_mean[1])
        for row in rows
    ]
    metrics["xy_radial_error_max"] = max(xy_errors) if xy_errors else 0.0
    return metrics


def render_summary(
    *,
    args: argparse.Namespace,
    rows: list[dict[str, Any]],
    metrics: dict[str, float],
    synthetic: bool,
) -> str:
    target_mean = (metrics["x_mean"], metrics["y_mean"], metrics["z_mean"])
    lines = [
        "# UR RTDE Target Measurement Summary",
        "",
        f"- Output: `{args.output}`",
        f"- Samples: `{len(rows)}`",
        f"- Source: `{'synthetic_smoke' if synthetic else 'ur_rtde'}`",
        f"- Pose frame: `{args.pose_frame}`",
        f"- Target id: `{args.target_id}`",
        "- Mean target position: `[{:.9f}, {:.9f}, {:.9f}]`".format(*target_mean),
        "- TCP-to-target offset: `[{:.9f}, {:.9f}, {:.9f}]`".format(
            *tuple(float(value) for value in args.tcp_to_target_xyz)
        ),
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
            "## Next Command",
            "",
            "```powershell",
            (
                "python scripts\\make_real_target_calibration.py "
                f"--input-csv {args.output} "
                "--output configs\\real_hole_target_calibration.yaml "
                "--summary-md results\\real_target_calibration_builder_summary.md "
                f"--target-id {args.target_id} "
                "--target-source fixture_calibration "
                f"--pose-frame {args.pose_frame} "
                "--method mean"
            ),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if args.samples <= 0:
        raise ValueError("--samples must be positive.")
    if args.frequency_hz <= 0.0:
        raise ValueError("--frequency-hz must be positive.")
    if args.host is None and not args.synthetic_smoke:
        raise ValueError("Provide --host or use --synthetic-smoke.")

    tcp_to_target_xyz = tuple(float(value) for value in args.tcp_to_target_xyz)
    reader = None if args.synthetic_smoke else URRTDETcpPoseReader(str(args.host))
    period = 1.0 / float(args.frequency_hz)
    start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for step in range(args.samples):
        loop_start = time.perf_counter()
        pose = synthetic_tcp_pose(step) if reader is None else reader.read_tcp_pose()
        tcp_pos = pose[:3]
        tcp_rotvec = pose[3:]
        target_pos = transform_offset(tcp_pos, tcp_rotvec, tcp_to_target_xyz)
        rows.append(
            {
                "step": step,
                "timestamp": loop_start - start,
                "target_id": args.target_id,
                "target_source": args.target_source,
                "target_frame": args.pose_frame,
                "target_x": target_pos[0],
                "target_y": target_pos[1],
                "target_z": target_pos[2],
                "tcp_x": tcp_pos[0],
                "tcp_y": tcp_pos[1],
                "tcp_z": tcp_pos[2],
                "tcp_rx": tcp_rotvec[0],
                "tcp_ry": tcp_rotvec[1],
                "tcp_rz": tcp_rotvec[2],
                "tcp_to_target_x": tcp_to_target_xyz[0],
                "tcp_to_target_y": tcp_to_target_xyz[1],
                "tcp_to_target_z": tcp_to_target_xyz[2],
            }
        )
        sleep_time = period - (time.perf_counter() - loop_start)
        if sleep_time > 0.0 and step + 1 < args.samples:
            time.sleep(sleep_time)

    write_rows(args.output, rows)
    metrics = summarize_rows(rows)
    args.summary_md.parent.mkdir(parents=True, exist_ok=True)
    args.summary_md.write_text(
        render_summary(args=args, rows=rows, metrics=metrics, synthetic=args.synthetic_smoke),
        encoding="utf-8",
    )
    print(f"saved target measurements to {args.output}")
    print(f"saved summary to {args.summary_md}")
    print(f"samples={len(rows)}")
    print(
        "mean_target=[{:.9f}, {:.9f}, {:.9f}]".format(
            metrics["x_mean"],
            metrics["y_mean"],
            metrics["z_mean"],
        )
    )


if __name__ == "__main__":
    main()
