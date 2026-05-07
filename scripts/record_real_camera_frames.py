from __future__ import annotations

import argparse
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from peg_in_hole_mujoco.image_preprocess import image_stats, save_image, write_stats_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record real camera frames for offline policy dry-run and camera preflight."
    )
    parser.add_argument("--source", default=None, help="OpenCV camera source, e.g. RTSP URL or video device path.")
    parser.add_argument("--device-index", type=int, default=0, help="OpenCV camera index when --source is omitted.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/real_camera_frames"))
    parser.add_argument("--stats-output", type=Path, default=Path("results/real_camera_frames_stats.csv"))
    parser.add_argument("--summary-md", type=Path, default=Path("results/real_camera_frames_summary.md"))
    parser.add_argument("--frames", type=int, default=20)
    parser.add_argument("--frequency-hz", type=float, default=5.0)
    parser.add_argument("--warmup-frames", type=int, default=10)
    parser.add_argument("--camera-width", type=int, default=None)
    parser.add_argument("--camera-height", type=int, default=None)
    parser.add_argument("--prefix", default="camera_frame")
    parser.add_argument("--session-id", default="", help="Optional capture session id written into the stats CSV.")
    parser.add_argument("--synthetic-smoke", action="store_true")
    return parser.parse_args()


class OpenCVCamera:
    def __init__(
        self,
        source: str | int,
        *,
        width: int | None,
        height: int | None,
    ) -> None:
        try:
            import cv2  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "Install OpenCV to record live camera frames: python -m pip install opencv-python"
            ) from exc
        self.cv2 = cv2
        self.capture = cv2.VideoCapture(source)
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open camera source: {source}")
        if width is not None:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
        if height is not None:
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))

    def read(self) -> np.ndarray:
        ok, frame = self.capture.read()
        if not ok or frame is None:
            raise RuntimeError("Could not read frame from camera.")
        if frame.ndim == 3 and frame.shape[2] >= 3:
            frame = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        return np.asarray(frame)

    def close(self) -> None:
        self.capture.release()


def synthetic_frame(index: int) -> np.ndarray:
    y = np.linspace(0, 255, 240, dtype=np.uint8)[:, None]
    x = np.linspace(0, 255, 320, dtype=np.uint8)[None, :]
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    image[..., 0] = x
    image[..., 1] = y
    image[..., 2] = 255 - x
    center_x = 140 + int(18 * math.sin(0.4 * index))
    center_y = 105 + int(12 * math.cos(0.35 * index))
    image[center_y:center_y + 28, center_x:center_x + 28] = np.asarray([255, 255, 255], dtype=np.uint8)
    image[40:200, 70 + index:75 + index] = np.asarray([20, 20, 20], dtype=np.uint8)
    return image


def frame_source_text(args: argparse.Namespace) -> str:
    if args.synthetic_smoke:
        return "synthetic_smoke"
    if args.source is not None:
        return str(args.source)
    return f"device_index:{args.device_index}"


def iso_utc(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def record_frames(args: argparse.Namespace) -> list[dict[str, Any]]:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    camera = None
    try:
        if not args.synthetic_smoke:
            source: str | int = args.source if args.source is not None else int(args.device_index)
            camera = OpenCVCamera(
                source,
                width=args.camera_width,
                height=args.camera_height,
            )
            for _ in range(args.warmup_frames):
                camera.read()

        period = 1.0 / float(args.frequency_hz)
        start = time.perf_counter()
        for index in range(args.frames):
            loop_start = time.perf_counter()
            wall_time_unix = time.time()
            frame = synthetic_frame(index) if args.synthetic_smoke else camera.read()
            timestamp = loop_start - start
            output_path = args.output_dir / f"{args.prefix}_{index:06d}.png"
            save_image(output_path, frame)
            row: dict[str, Any] = {
                "session_id": args.session_id,
                "frame_index": index,
                "timestamp": timestamp,
                "wall_time_unix": wall_time_unix,
                "wall_time_utc": iso_utc(wall_time_unix),
                "source": frame_source_text(args),
                "output": str(output_path),
            }
            row.update(image_stats(frame))
            rows.append(row)
            sleep_time = period - (time.perf_counter() - loop_start)
            if sleep_time > 0.0 and index + 1 < args.frames:
                time.sleep(sleep_time)
    finally:
        if camera is not None:
            camera.close()
    return rows


def mean(values: list[float]) -> float:
    if not values:
        return float("nan")
    return float(sum(values) / len(values))


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    means = [float(row["mean"]) for row in rows]
    stds = [float(row["std"]) for row in rows]
    timestamps = [float(row["timestamp"]) for row in rows]
    intervals = [
        timestamps[index] - timestamps[index - 1]
        for index in range(1, len(timestamps))
    ]
    return {
        "frames": len(rows),
        "mean_min": min(means) if means else float("nan"),
        "mean_max": max(means) if means else float("nan"),
        "mean_avg": mean(means),
        "std_min": min(stds) if stds else float("nan"),
        "std_max": max(stds) if stds else float("nan"),
        "std_avg": mean(stds),
        "interval_min": min(intervals) if intervals else float("nan"),
        "interval_max": max(intervals) if intervals else float("nan"),
        "interval_avg": mean(intervals),
    }


def render_summary(args: argparse.Namespace, rows: list[dict[str, Any]], metrics: dict[str, Any]) -> str:
    lines = [
        "# Real Camera Frame Recording Summary",
        "",
        f"- Source: `{frame_source_text(args)}`",
        f"- Output directory: `{args.output_dir}`",
        f"- Stats CSV: `{args.stats_output}`",
        f"- Frames: `{len(rows)}`",
        f"- Requested frequency: `{args.frequency_hz}` Hz",
        f"- Warmup frames: `{args.warmup_frames}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in sorted(metrics):
        value = metrics[key]
        if isinstance(value, float):
            value_text = "nan" if math.isnan(value) else f"{value:.9g}"
        else:
            value_text = str(value)
        lines.append(f"| `{key}` | {value_text} |")

    lines.extend(
        [
            "",
            "## Next Command",
            "",
            "```powershell",
            (
                "python scripts\\check_real_camera_preflight.py "
                f"--input {args.output_dir} "
                "--output-dir results\\real_camera_preflight_frames "
                "--stats-output results\\real_camera_preflight_stats.csv "
                "--summary-md results\\real_camera_preflight_summary.md "
                "--width 100 --height 100 --max-frames 20"
            ),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if args.frames <= 0:
        raise ValueError("--frames must be positive.")
    if args.frequency_hz <= 0.0:
        raise ValueError("--frequency-hz must be positive.")
    if args.warmup_frames < 0:
        raise ValueError("--warmup-frames cannot be negative.")
    if args.camera_width is not None and args.camera_width <= 0:
        raise ValueError("--camera-width must be positive.")
    if args.camera_height is not None and args.camera_height <= 0:
        raise ValueError("--camera-height must be positive.")

    rows = record_frames(args)
    write_stats_csv(args.stats_output, rows)
    metrics = summarize_rows(rows)
    args.summary_md.parent.mkdir(parents=True, exist_ok=True)
    args.summary_md.write_text(render_summary(args, rows, metrics), encoding="utf-8")
    print(f"saved_frames_to={args.output_dir}")
    print(f"saved_stats_to={args.stats_output}")
    print(f"saved_summary_to={args.summary_md}")
    print(f"frames={len(rows)}")


if __name__ == "__main__":
    main()
