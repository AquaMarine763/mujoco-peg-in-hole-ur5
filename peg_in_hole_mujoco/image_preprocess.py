from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ImagePreprocessConfig:
    width: int = 100
    height: int = 100
    crop_xywh: tuple[int, int, int, int] | None = None
    rotate_k: int = 0
    flip_horizontal: bool = False
    flip_vertical: bool = False


def load_image(path: Path) -> np.ndarray:
    try:
        import imageio.v2 as imageio
    except ImportError as exc:
        raise ImportError("Install imageio with `python -m pip install imageio` to load camera images.") from exc
    return np.asarray(imageio.imread(path))


def save_image(path: Path, image: np.ndarray) -> None:
    try:
        import imageio.v2 as imageio
    except ImportError as exc:
        raise ImportError("Install imageio with `python -m pip install imageio` to save images.") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, np.asarray(image))


def crop_xywh(image: np.ndarray, crop: tuple[int, int, int, int] | None) -> np.ndarray:
    if crop is None:
        return image
    x, y, width, height = crop
    if width <= 0 or height <= 0:
        raise ValueError("Crop width and height must be positive.")
    image_height, image_width = image.shape[:2]
    x0 = max(0, int(x))
    y0 = max(0, int(y))
    x1 = min(image_width, x0 + int(width))
    y1 = min(image_height, y0 + int(height))
    if x0 >= x1 or y0 >= y1:
        raise ValueError(f"Crop {crop} is outside image shape {image.shape}.")
    return image[y0:y1, x0:x1]


def orient_image(
    image: np.ndarray,
    rotate_k: int = 0,
    flip_horizontal: bool = False,
    flip_vertical: bool = False,
) -> np.ndarray:
    oriented = np.rot90(image, k=rotate_k % 4)
    if flip_horizontal:
        oriented = np.flip(oriented, axis=1)
    if flip_vertical:
        oriented = np.flip(oriented, axis=0)
    return oriented


def resize_nearest(image: np.ndarray, width: int, height: int) -> np.ndarray:
    if width <= 0 or height <= 0:
        raise ValueError("Image width and height must be positive.")
    if image.ndim < 2:
        raise ValueError("Image must have at least two dimensions.")
    source_height, source_width = image.shape[:2]
    y_idx = np.linspace(0, source_height - 1, height).round().astype(np.int64)
    x_idx = np.linspace(0, source_width - 1, width).round().astype(np.int64)
    return image[y_idx][:, x_idx]


def to_grayscale_uint8(image: np.ndarray) -> np.ndarray:
    image = np.asarray(image)
    if image.ndim == 2:
        gray = image.astype(np.float32)
    elif image.ndim == 3 and image.shape[2] >= 3:
        rgb = image[..., :3].astype(np.float32)
        gray = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    elif image.ndim == 3 and image.shape[2] == 1:
        gray = image[..., 0].astype(np.float32)
    else:
        raise ValueError(f"Unsupported image shape: {image.shape}.")
    return np.clip(gray, 0, 255).astype(np.uint8)


def preprocess_camera_image(
    image: np.ndarray,
    width: int = 100,
    height: int = 100,
    config: ImagePreprocessConfig | None = None,
) -> np.ndarray:
    if config is None:
        config = ImagePreprocessConfig(width=width, height=height)
    cropped = crop_xywh(image, config.crop_xywh)
    oriented = orient_image(
        cropped,
        rotate_k=config.rotate_k,
        flip_horizontal=config.flip_horizontal,
        flip_vertical=config.flip_vertical,
    )
    resized = resize_nearest(oriented, width=config.width, height=config.height)
    gray = to_grayscale_uint8(resized)
    return gray[..., None]


def image_stats(image: np.ndarray) -> dict[str, Any]:
    array = np.asarray(image)
    return {
        "shape": "x".join(str(value) for value in array.shape),
        "dtype": str(array.dtype),
        "min": float(array.min()) if array.size else float("nan"),
        "max": float(array.max()) if array.size else float("nan"),
        "mean": float(array.mean()) if array.size else float("nan"),
        "std": float(array.std()) if array.size else float("nan"),
    }


def write_stats_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
