from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from peg_in_hole_mujoco.image_preprocess import (
    ImagePreprocessConfig,
    image_stats,
    load_image,
    preprocess_camera_image,
    save_image,
    write_stats_csv,
)
from peg_in_hole_mujoco.real_backend import IMAGE_SUFFIXES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess real camera frames to the policy image shape.")
    parser.add_argument("--input", type=Path, default=None, help="Single image file or directory of frames.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/preprocessed_camera_frames"))
    parser.add_argument("--stats-output", type=Path, default=Path("results/preprocessed_camera_frames_stats.csv"))
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=100)
    parser.add_argument("--crop-xywh", nargs=4, type=int, default=None)
    parser.add_argument("--rotate-k", type=int, default=0, help="Rotate by k * 90 degrees counterclockwise.")
    parser.add_argument("--flip-horizontal", action="store_true")
    parser.add_argument("--flip-vertical", action="store_true")
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--synthetic-smoke", action="store_true", help="Generate a synthetic test image when no camera frame is available.")
    return parser.parse_args()


def resolve_inputs(path: Path | None, synthetic_smoke: bool) -> list[Path]:
    if synthetic_smoke:
        return []
    if path is None:
        raise ValueError("Provide --input or use --synthetic-smoke.")
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(
            item for item in path.iterdir()
            if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES
        )
    raise FileNotFoundError(path)


def synthetic_image() -> np.ndarray:
    y = np.linspace(0, 255, 180, dtype=np.uint8)[:, None]
    x = np.linspace(0, 255, 240, dtype=np.uint8)[None, :]
    image = np.zeros((180, 240, 3), dtype=np.uint8)
    image[..., 0] = x
    image[..., 1] = y
    image[..., 2] = 255 - x
    image[80:100, 110:130] = np.asarray([255, 255, 255], dtype=np.uint8)
    return image


def process_image(
    name: str,
    image: np.ndarray,
    output_dir: Path,
    config: ImagePreprocessConfig,
) -> dict[str, object]:
    processed = preprocess_camera_image(image, config=config)
    output_path = output_dir / f"{Path(name).stem}_processed.png"
    save_image(output_path, processed[..., 0])
    row: dict[str, object] = {
        "input": name,
        "output": str(output_path),
        "crop_xywh": "" if config.crop_xywh is None else ",".join(str(value) for value in config.crop_xywh),
        "rotate_k": config.rotate_k,
        "flip_horizontal": config.flip_horizontal,
        "flip_vertical": config.flip_vertical,
    }
    row.update({f"input_{key}": value for key, value in image_stats(image).items()})
    row.update({f"processed_{key}": value for key, value in image_stats(processed).items()})
    return row


def main() -> None:
    args = parse_args()
    config = ImagePreprocessConfig(
        width=args.width,
        height=args.height,
        crop_xywh=None if args.crop_xywh is None else tuple(args.crop_xywh),
        rotate_k=args.rotate_k,
        flip_horizontal=args.flip_horizontal,
        flip_vertical=args.flip_vertical,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    input_paths = resolve_inputs(args.input, args.synthetic_smoke)
    if args.max_frames is not None:
        input_paths = input_paths[: args.max_frames]

    if args.synthetic_smoke:
        rows.append(process_image("synthetic_smoke.png", synthetic_image(), args.output_dir, config))
    else:
        for path in input_paths:
            rows.append(process_image(path.name, load_image(path), args.output_dir, config))

    write_stats_csv(args.stats_output, rows)
    print(f"processed_frames={len(rows)}")
    print(f"saved_processed_frames_to={args.output_dir}")
    print(f"saved_stats_to={args.stats_output}")


if __name__ == "__main__":
    main()
