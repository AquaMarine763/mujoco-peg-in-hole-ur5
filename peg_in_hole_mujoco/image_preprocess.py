from __future__ import annotations

from pathlib import Path

import numpy as np


def load_image(path: Path) -> np.ndarray:
    try:
        import imageio.v2 as imageio
    except ImportError as exc:
        raise ImportError("Install imageio with `python -m pip install imageio` to load camera images.") from exc
    return np.asarray(imageio.imread(path))


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


def preprocess_camera_image(image: np.ndarray, width: int = 100, height: int = 100) -> np.ndarray:
    resized = resize_nearest(image, width=width, height=height)
    gray = to_grayscale_uint8(resized)
    return gray[..., None]
