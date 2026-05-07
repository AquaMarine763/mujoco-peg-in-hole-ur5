from __future__ import annotations

import csv
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


@dataclass(frozen=True)
class RealPoseSample:
    peg_tip_pos: tuple[float, float, float]
    target_pos: tuple[float, float, float]
    step: int | None = None
    timestamp: float | None = None
    pose_frame: str = "robot_base"
    target_source: str = "static"
    target_frame: str = "robot_base"
    target_timestamp: float | None = None
    tcp_pos: tuple[float, float, float] | None = None
    tcp_rotvec: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class RealTargetCalibration:
    target_pos: tuple[float, float, float]
    pose_frame: str = "robot_base"
    target_source: str = "calibration"
    target_id: str = "hole"
    timestamp: float | None = None

    @classmethod
    def from_file(cls, path: Path | str) -> "RealTargetCalibration":
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return cls.from_csv(path)
        if suffix in (".yaml", ".yml"):
            return cls.from_simple_yaml(path)
        raise ValueError("target calibration must be .csv, .yaml, or .yml")

    @classmethod
    def from_csv(cls, path: Path | str) -> "RealTargetCalibration":
        with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
            rows = list(csv.DictReader(file))
        if not rows:
            raise ValueError(f"target calibration is empty: {path}")
        row = rows[0]
        return cls(
            target_pos=(
                _required_float(row, ("target_x", "hole_x"), row_index=0),
                _required_float(row, ("target_y", "hole_y"), row_index=0),
                _required_float(row, ("target_z", "hole_z"), row_index=0),
            ),
            pose_frame=_first_text(row, ("target_frame", "pose_frame", "frame")) or "robot_base",
            target_source=_first_text(row, ("target_source", "source")) or "calibration_csv",
            target_id=_first_text(row, ("target_id", "hole_id", "id")) or "hole",
            timestamp=_optional_float(row, ("target_timestamp", "timestamp", "time")),
        )

    @classmethod
    def from_simple_yaml(cls, path: Path | str) -> "RealTargetCalibration":
        values = _load_simple_key_values(Path(path))
        target_pos = values.get("target_pos", values.get("hole_pos"))
        if target_pos is None:
            target_pos = [
                values.get("target_x", values.get("hole_x")),
                values.get("target_y", values.get("hole_y")),
                values.get("target_z", values.get("hole_z")),
            ]
        if target_pos is None or len(target_pos) != 3 or any(value is None for value in target_pos):
            raise ValueError("target calibration must define target_pos or target_x/y/z.")
        return cls(
            target_pos=tuple(float(value) for value in target_pos),
            pose_frame=str(values.get("target_frame", values.get("pose_frame", "robot_base"))),
            target_source=str(values.get("target_source", "calibration_yaml")),
            target_id=str(values.get("target_id", values.get("hole_id", "hole"))),
            timestamp=(
                None
                if values.get("target_timestamp", values.get("timestamp")) is None
                else float(values.get("target_timestamp", values.get("timestamp")))
            ),
        )


@dataclass(frozen=True)
class RealPoseTrace:
    samples: tuple[RealPoseSample, ...]

    @classmethod
    def from_csv(cls, path: Path | str, *, default_pose_frame: str = "robot_base") -> "RealPoseTrace":
        with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
            rows = list(csv.DictReader(file))
        if not rows:
            raise ValueError(f"pose trace is empty: {path}")
        samples = tuple(
            _pose_sample_from_row(row, row_index=index, default_pose_frame=default_pose_frame)
            for index, row in enumerate(rows)
        )
        return cls(samples=samples)

    @classmethod
    def from_tcp_csv(
        cls,
        path: Path | str,
        *,
        target_pos: tuple[float, float, float],
        default_target_source: str,
        default_target_frame: str,
        default_target_timestamp: float | None,
        tcp_to_peg_tip_xyz: tuple[float, float, float],
        default_pose_frame: str = "robot_base",
    ) -> "RealPoseTrace":
        with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
            rows = list(csv.DictReader(file))
        if not rows:
            raise ValueError(f"TCP pose trace is empty: {path}")
        samples = tuple(
            _pose_sample_from_tcp_row(
                row,
                row_index=index,
                default_target_pos=target_pos,
                default_target_source=default_target_source,
                default_target_frame=default_target_frame,
                default_target_timestamp=default_target_timestamp,
                tcp_to_peg_tip_xyz=tcp_to_peg_tip_xyz,
                default_pose_frame=default_pose_frame,
            )
            for index, row in enumerate(rows)
        )
        return cls(samples=samples)

    def sample_for_step(self, step_count: int) -> RealPoseSample:
        if step_count < 0:
            raise ValueError("step_count cannot be negative.")
        if not self.samples:
            raise ValueError("pose trace has no samples.")
        return self.samples[min(step_count, len(self.samples) - 1)]


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
        pose_trace_path: Path | str | None = None,
        tcp_pose_trace_path: Path | str | None = None,
        target_calibration: RealTargetCalibration | None = None,
        pose_frame: str = "robot_base",
        tcp_to_peg_tip_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        if pose_trace_path is not None and tcp_pose_trace_path is not None:
            raise ValueError("Use either pose_trace_path or tcp_pose_trace_path, not both.")
        self.config = config
        self.image_paths = self._resolve_image_paths(image_path, image_dir)
        self.target_calibration = target_calibration or RealTargetCalibration(
            target_pos=tuple(float(value) for value in config.target_pos),
            pose_frame=pose_frame,
            target_source="static",
        )
        self.pose_trace: RealPoseTrace | None = None
        self.pose_source = "static"
        if pose_trace_path is not None:
            self.pose_trace = RealPoseTrace.from_csv(
                pose_trace_path,
                default_pose_frame=pose_frame,
            )
            self.pose_source = "csv"
        if tcp_pose_trace_path is not None:
            self.pose_trace = RealPoseTrace.from_tcp_csv(
                tcp_pose_trace_path,
                target_pos=self.target_calibration.target_pos,
                default_target_source=self.target_calibration.target_source,
                default_target_frame=self.target_calibration.pose_frame,
                default_target_timestamp=self.target_calibration.timestamp,
                tcp_to_peg_tip_xyz=tuple(float(value) for value in tcp_to_peg_tip_xyz),
                default_pose_frame=pose_frame,
            )
            self.pose_source = "tcp_csv"
        self.pose_frame = pose_frame
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
        pose_sample = self._pose_sample()
        peg_tip = np.asarray(pose_sample.peg_tip_pos, dtype=np.float32)
        target = np.asarray(pose_sample.target_pos, dtype=np.float32)
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
            "pose_source": self.pose_source,
            "pose_frame": pose_sample.pose_frame,
            "pose_step": self.step_count if pose_sample.step is None else pose_sample.step,
            "pose_timestamp": (
                float("nan") if pose_sample.timestamp is None else float(pose_sample.timestamp)
            ),
            "target_source": pose_sample.target_source,
            "target_frame": pose_sample.target_frame,
            "target_timestamp": (
                float("nan")
                if pose_sample.target_timestamp is None
                else float(pose_sample.target_timestamp)
            ),
            "tcp_pos": (
                np.full(3, np.nan, dtype=np.float32)
                if pose_sample.tcp_pos is None
                else np.asarray(pose_sample.tcp_pos, dtype=np.float32)
            ),
            "tcp_rotvec": (
                np.full(3, np.nan, dtype=np.float32)
                if pose_sample.tcp_rotvec is None
                else np.asarray(pose_sample.tcp_rotvec, dtype=np.float32)
            ),
        }

    def _pose_sample(self) -> RealPoseSample:
        if self.pose_trace is not None:
            return self.pose_trace.sample_for_step(self.step_count)
        return RealPoseSample(
            peg_tip_pos=tuple(float(value) for value in self.config.peg_tip_pos),
            target_pos=self.target_calibration.target_pos,
            step=self.step_count,
            pose_frame=self.pose_frame,
            target_source=self.target_calibration.target_source,
            target_frame=self.target_calibration.pose_frame,
            target_timestamp=self.target_calibration.timestamp,
        )

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


def _pose_sample_from_row(
    row: dict[str, str],
    *,
    row_index: int,
    default_pose_frame: str,
) -> RealPoseSample:
    step = _optional_int(row, ("step", "pose_step"))
    timestamp = _optional_float(row, ("timestamp", "time", "t"))
    pose_frame = _first_text(row, ("pose_frame", "frame", "reference_frame")) or default_pose_frame
    return RealPoseSample(
        peg_tip_pos=(
            _required_float(row, ("peg_tip_x", "tcp_x", "tool_x"), row_index=row_index),
            _required_float(row, ("peg_tip_y", "tcp_y", "tool_y"), row_index=row_index),
            _required_float(row, ("peg_tip_z", "tcp_z", "tool_z"), row_index=row_index),
        ),
        target_pos=(
            _required_float(row, ("target_x", "hole_x"), row_index=row_index),
            _required_float(row, ("target_y", "hole_y"), row_index=row_index),
            _required_float(row, ("target_z", "hole_z"), row_index=row_index),
        ),
        step=step,
        timestamp=timestamp,
        pose_frame=pose_frame,
        target_source="pose_csv",
        target_frame=_first_text(row, ("target_frame", "hole_frame")) or pose_frame,
        target_timestamp=_optional_float(row, ("target_timestamp", "hole_timestamp")),
    )


def _pose_sample_from_tcp_row(
    row: dict[str, str],
    *,
    row_index: int,
    default_target_pos: tuple[float, float, float],
    default_target_source: str,
    default_target_frame: str,
    default_target_timestamp: float | None,
    tcp_to_peg_tip_xyz: tuple[float, float, float],
    default_pose_frame: str,
) -> RealPoseSample:
    step = _optional_int(row, ("step", "pose_step"))
    timestamp = _optional_float(row, ("timestamp", "time", "t"))
    pose_frame = _first_text(row, ("pose_frame", "frame", "reference_frame")) or default_pose_frame
    tcp_pos = (
        _required_float(row, ("tcp_x", "tool0_x", "tool_x"), row_index=row_index),
        _required_float(row, ("tcp_y", "tool0_y", "tool_y"), row_index=row_index),
        _required_float(row, ("tcp_z", "tool0_z", "tool_z"), row_index=row_index),
    )
    tcp_rotvec = (
        _required_float(row, ("tcp_rx", "tool0_rx", "rx"), row_index=row_index),
        _required_float(row, ("tcp_ry", "tool0_ry", "ry"), row_index=row_index),
        _required_float(row, ("tcp_rz", "tool0_rz", "rz"), row_index=row_index),
    )
    target_pos = (
        _optional_float(row, ("target_x", "hole_x")),
        _optional_float(row, ("target_y", "hole_y")),
        _optional_float(row, ("target_z", "hole_z")),
    )
    row_has_target = any(value is not None for value in target_pos)
    resolved_target = tuple(
        float(default_value if value is None else value)
        for value, default_value in zip(target_pos, default_target_pos)
    )
    peg_tip = _tcp_pose_to_peg_tip(
        tcp_pos=tcp_pos,
        tcp_rotvec=tcp_rotvec,
        tcp_to_peg_tip_xyz=tcp_to_peg_tip_xyz,
    )
    return RealPoseSample(
        peg_tip_pos=peg_tip,
        target_pos=resolved_target,
        step=step,
        timestamp=timestamp,
        pose_frame=pose_frame,
        target_source=(
            _first_text(row, ("target_source", "hole_source"))
            or ("tcp_csv" if row_has_target else default_target_source)
        ),
        target_frame=(
            _first_text(row, ("target_frame", "hole_frame"))
            or (pose_frame if row_has_target else default_target_frame)
        ),
        target_timestamp=(
            _optional_float(row, ("target_timestamp", "hole_timestamp"))
            if row_has_target
            else default_target_timestamp
        ),
        tcp_pos=tcp_pos,
        tcp_rotvec=tcp_rotvec,
    )


def _tcp_pose_to_peg_tip(
    *,
    tcp_pos: tuple[float, float, float],
    tcp_rotvec: tuple[float, float, float],
    tcp_to_peg_tip_xyz: tuple[float, float, float],
) -> tuple[float, float, float]:
    position = np.asarray(tcp_pos, dtype=np.float64).reshape(3)
    rotation = _rotvec_to_matrix(np.asarray(tcp_rotvec, dtype=np.float64).reshape(3))
    offset = np.asarray(tcp_to_peg_tip_xyz, dtype=np.float64).reshape(3)
    peg_tip = position + rotation @ offset
    return tuple(float(value) for value in peg_tip)


def _rotvec_to_matrix(rotvec: np.ndarray) -> np.ndarray:
    theta = float(np.linalg.norm(rotvec))
    if theta < 1e-12:
        return np.eye(3, dtype=np.float64)
    axis = rotvec / theta
    x, y, z = axis
    cross = np.asarray(
        [
            [0.0, -z, y],
            [z, 0.0, -x],
            [-y, x, 0.0],
        ],
        dtype=np.float64,
    )
    return (
        np.eye(3, dtype=np.float64)
        + np.sin(theta) * cross
        + (1.0 - np.cos(theta)) * (cross @ cross)
    )


def _required_float(
    row: dict[str, str],
    keys: tuple[str, ...],
    *,
    row_index: int,
) -> float:
    value = _first_text(row, keys)
    if value is None:
        raise ValueError(f"pose trace row {row_index} is missing one of: {', '.join(keys)}")
    return float(value)


def _optional_float(row: dict[str, str], keys: tuple[str, ...]) -> float | None:
    value = _first_text(row, keys)
    return None if value is None else float(value)


def _optional_int(row: dict[str, str], keys: tuple[str, ...]) -> int | None:
    value = _first_text(row, keys)
    return None if value is None else int(value)


def _first_text(row: dict[str, str], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is not None and value.strip():
            return value.strip()
    return None


def _load_simple_key_values(path: Path) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = _parse_simple_value(value.strip())
    return values


def _parse_simple_value(text: str) -> Any:
    if not text:
        return ""
    lower = text.lower()
    if lower in ("none", "null"):
        return None
    if lower == "true":
        return True
    if lower == "false":
        return False
    if text.startswith("[") and text.endswith("]"):
        content = text[1:-1].strip()
        if not content:
            return []
        return [_parse_simple_value(part.strip()) for part in content.split(",")]
    try:
        if any(char in lower for char in (".", "e")):
            return float(text)
        return int(text)
    except ValueError:
        return text.strip("'\"")
