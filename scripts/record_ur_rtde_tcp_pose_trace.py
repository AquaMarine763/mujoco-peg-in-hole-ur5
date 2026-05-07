from __future__ import annotations

import argparse
import csv
import math
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record a read-only UR RTDE TCP pose trace for real dry-run replay."
    )
    parser.add_argument("--host", default=None, help="UR controller IP address.")
    parser.add_argument("--output", type=Path, default=Path("results/ur_rtde_tcp_pose_trace.csv"))
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--frequency-hz", type=float, default=20.0)
    parser.add_argument("--pose-frame", default="robot_base")
    parser.add_argument("--target-pos", nargs=3, type=float, default=(0.55, 0.05, 0.65))
    parser.add_argument(
        "--synthetic-smoke",
        action="store_true",
        help="Write deterministic synthetic TCP poses without connecting to a UR controller.",
    )
    parser.add_argument(
        "--no-target-columns",
        action="store_true",
        help="Omit target_x/y/z columns so downstream calibration can supply the target separately.",
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
    phase = 0.2 * index
    return (
        0.55 + 0.001 * math.sin(phase),
        0.05 + 0.001 * math.cos(phase),
        0.83 - 0.0005 * index,
        0.0,
        0.0,
        0.0,
    )


def write_rows(path: Path, rows: list[dict[str, Any]], *, include_target_columns: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "step",
        "timestamp",
        "pose_frame",
        "tcp_x",
        "tcp_y",
        "tcp_z",
        "tcp_rx",
        "tcp_ry",
        "tcp_rz",
    ]
    if include_target_columns:
        fieldnames.extend(["target_x", "target_y", "target_z"])
    else:
        for row in rows:
            row.pop("target_x", None)
            row.pop("target_y", None)
            row.pop("target_z", None)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    if args.samples <= 0:
        raise ValueError("--samples must be positive.")
    if args.frequency_hz <= 0.0:
        raise ValueError("--frequency-hz must be positive.")
    if args.host is None and not args.synthetic_smoke:
        raise ValueError("Provide --host or use --synthetic-smoke.")

    reader = None if args.synthetic_smoke else URRTDETcpPoseReader(str(args.host))
    period = 1.0 / float(args.frequency_hz)
    start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for step in range(args.samples):
        loop_start = time.perf_counter()
        pose = synthetic_tcp_pose(step) if reader is None else reader.read_tcp_pose()
        rows.append(
            {
                "step": step,
                "timestamp": loop_start - start,
                "pose_frame": args.pose_frame,
                "tcp_x": pose[0],
                "tcp_y": pose[1],
                "tcp_z": pose[2],
                "tcp_rx": pose[3],
                "tcp_ry": pose[4],
                "tcp_rz": pose[5],
                "target_x": args.target_pos[0],
                "target_y": args.target_pos[1],
                "target_z": args.target_pos[2],
            }
        )
        sleep_time = period - (time.perf_counter() - loop_start)
        if sleep_time > 0.0 and step + 1 < args.samples:
            time.sleep(sleep_time)

    write_rows(args.output, rows, include_target_columns=not args.no_target_columns)
    print(f"saved TCP pose trace to {args.output}")
    print(f"samples={len(rows)}")
    print(f"target_columns={'included' if not args.no_target_columns else 'omitted'}")


if __name__ == "__main__":
    main()
