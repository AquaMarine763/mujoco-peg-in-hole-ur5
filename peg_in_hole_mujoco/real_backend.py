from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from peg_in_hole_mujoco.image_preprocess import ImagePreprocessConfig, load_image, preprocess_camera_image
from peg_in_hole_mujoco.policy_interface import StepResult


IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff"}


@dataclass(frozen=True)
class RealCameraConfig:
    image_width: int = 100
    image_height: int = 100
    crop_xywh: tuple[int, int, int, int] | None = None
    rotate_k: int = 0
    flip_horizontal: bool = False
    flip_vertical: bool = False
    observation_key: str = "cam_image"
    peg_tip_pos: tuple[float, float, float] = (0.55, 0.05, 0.78)
    target_pos: tuple[float, float, float] = (0.55, 0.05, 0.65)

    def preprocess_config(self) -> ImagePreprocessConfig:
        return ImagePreprocessConfig(
            width=self.image_width,
            height=self.image_height,
            crop_xywh=self.crop_xywh,
            rotate_k=self.rotate_k,
            flip_horizontal=self.flip_horizontal,
            flip_vertical=self.flip_vertical,
        )


class ZeroPolicyAdapter:
    def predict(self, observation: Any) -> np.ndarray:
        del observation
        return np.zeros(3, dtype=np.float64)


class RealCameraObservationProvider:
    def __init__(
        self,
        config: RealCameraConfig,
        image_path: Path | None = None,
        image_dir: Path | None = None,
    ):
        self.config = config
        self.image_paths = self._resolve_image_paths(image_path, image_dir)
        self.frame_index = 0
        self.step_count = 0

    def reset(self, seed: int | None = None) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        del seed
        self.frame_index = 0
        self.step_count = 0
        return self.observe()

    def observe(self) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        image = self._next_image()
        observation = {self.config.observation_key: image}
        return observation, self.info()

    def info(self) -> dict[str, Any]:
        peg_tip = np.asarray(self.config.peg_tip_pos, dtype=np.float32)
        target = np.asarray(self.config.target_pos, dtype=np.float32)
        dist_xy = float(np.linalg.norm(peg_tip[:2] - target[:2]))
        dist_z = float(abs(peg_tip[2] - target[2]))
        return {
            "insertion_success": False,
            "collision": False,
            "step_count": self.step_count,
            "dist_xy": dist_xy,
            "dist_z": dist_z,
            "shaped_distance": float(2.0 * dist_xy + dist_z),
            "desired_z": float(target[2]),
            "target_pos": target,
            "peg_tip_pos": peg_tip,
            "commanded_action": np.zeros(3, dtype=np.float32),
            "applied_action": np.zeros(3, dtype=np.float32),
            "control_action_scale_multiplier": 1.0,
            "control_action_noise_std": 0.0,
            "control_action_delay": 0,
            "control_action_filter_alpha": 1.0,
        }

    def _next_image(self) -> np.ndarray:
        if not self.image_paths:
            return np.zeros(
                (self.config.image_height, self.config.image_width, 1),
                dtype=np.uint8,
            )
        path = self.image_paths[self.frame_index % len(self.image_paths)]
        self.frame_index += 1
        return preprocess_camera_image(
            load_image(path),
            config=self.config.preprocess_config(),
        )

    @staticmethod
    def _resolve_image_paths(image_path: Path | None, image_dir: Path | None) -> list[Path]:
        if image_path is not None and image_dir is not None:
            raise ValueError("Use either image_path or image_dir, not both.")
        if image_path is not None:
            return [Path(image_path)]
        if image_dir is None:
            return []
        directory = Path(image_dir)
        return sorted(
            path for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )


class DryRunUR5ActionExecutor:
    def __init__(self, observation_provider: RealCameraObservationProvider, max_steps: int = 50):
        if max_steps <= 0:
            raise ValueError("max_steps must be positive.")
        self.observation_provider = observation_provider
        self.max_steps = int(max_steps)
        self.actions: list[np.ndarray] = []

    def execute(self, action: np.ndarray) -> StepResult:
        action = np.asarray(action, dtype=np.float64).reshape(3)
        self.actions.append(action.copy())
        self.observation_provider.step_count += 1
        observation, info = self.observation_provider.observe()
        info["commanded_action"] = action.astype(np.float32)
        info["applied_action"] = action.astype(np.float32)
        return StepResult(
            observation=observation,
            reward=0.0,
            terminated=False,
            truncated=self.observation_provider.step_count >= self.max_steps,
            info=info,
        )

    def close(self) -> None:
        pass
