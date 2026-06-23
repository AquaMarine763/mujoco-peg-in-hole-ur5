from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn


DEFAULT_PROFILE_ORDER = (
    "square_square",
    "triangle_triangle",
    "hex_hex",
    "rectangular_key",
)

PROFILE_PERIOD_DEG = {
    "square_square": 90.0,
    "triangle_triangle": 120.0,
    "hex_hex": 60.0,
    "slot_slot": 180.0,
    "rectangular_key": 360.0,
}


@dataclass(frozen=True)
class VisualYawPrediction:
    valid: bool
    reason: str
    profile: str = ""
    signed_error_deg: float = float("nan")
    abs_error_deg: float = float("nan")
    raw_norm: float = float("nan")
    cam_std: float = float("nan")
    crop_std: float = float("nan")


class ConvEncoder(nn.Module):
    def __init__(self, in_channels: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, 16, kernel_size=5, stride=2, padding=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 96, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
        )

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return self.net(image)


class VisualYawEstimator(nn.Module):
    def __init__(
        self,
        *,
        cam_channels: int,
        crop_channels: int,
        profile_count: int,
        include_profile_onehot: bool,
    ):
        super().__init__()
        self.include_profile_onehot = bool(include_profile_onehot)
        self.profile_count = int(profile_count)
        self.cam_encoder = ConvEncoder(cam_channels)
        self.crop_encoder = ConvEncoder(crop_channels)
        head_input = 96 + 96 + (profile_count if include_profile_onehot else 0)
        self.head = nn.Sequential(
            nn.Linear(head_input, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 2),
        )

    def raw_forward(
        self,
        cam: torch.Tensor,
        crop: torch.Tensor,
        profile_id: torch.Tensor,
    ) -> torch.Tensor:
        features = [self.cam_encoder(cam), self.crop_encoder(crop)]
        if self.include_profile_onehot:
            onehot = torch.nn.functional.one_hot(
                profile_id,
                num_classes=self.profile_count,
            ).float()
            features.append(onehot)
        return self.head(torch.cat(features, dim=1))

    def forward(
        self,
        cam: torch.Tensor,
        crop: torch.Tensor,
        profile_id: torch.Tensor,
    ) -> torch.Tensor:
        raw = self.raw_forward(cam, crop, profile_id)
        return raw / raw.norm(dim=1, keepdim=True).clamp_min(1e-6)


def resolve_device(device: str) -> torch.device:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device)


def _checkpoint_arg(checkpoint: dict[str, Any], key: str, default: Any) -> Any:
    args = checkpoint.get("args", {})
    if isinstance(args, dict) and key in args:
        return args[key]
    return default


class VisualYawRuntime:
    def __init__(self, checkpoint_path: Path, *, device: str = "auto"):
        self.checkpoint_path = Path(checkpoint_path)
        self.device = resolve_device(device)
        try:
            checkpoint = torch.load(
                self.checkpoint_path,
                map_location=self.device,
                weights_only=False,
            )
        except TypeError:
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
        if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
            raise ValueError(f"unsupported visual yaw checkpoint: {self.checkpoint_path}")

        metadata = checkpoint.get("metadata", {})
        self.profile_order = tuple(
            metadata.get("profile_order", DEFAULT_PROFILE_ORDER)
            if isinstance(metadata, dict)
            else DEFAULT_PROFILE_ORDER
        )
        self.profile_to_id = {
            profile: index for index, profile in enumerate(self.profile_order)
        }
        include_profile_onehot = True
        if isinstance(metadata, dict) and "include_profile_onehot" in metadata:
            include_profile_onehot = bool(metadata["include_profile_onehot"])
        else:
            include_profile_onehot = not bool(
                _checkpoint_arg(checkpoint, "no_profile_onehot", False)
            )

        cam_shape = metadata.get("cam_shape", [1, 100, 100]) if isinstance(metadata, dict) else [1, 100, 100]
        crop_shape = metadata.get("crop_shape", [1, 64, 64]) if isinstance(metadata, dict) else [1, 64, 64]
        self.cam_channels = int(cam_shape[0])
        self.crop_channels = int(crop_shape[0])
        self.model = VisualYawEstimator(
            cam_channels=self.cam_channels,
            crop_channels=self.crop_channels,
            profile_count=len(self.profile_order),
            include_profile_onehot=include_profile_onehot,
        ).to(self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

    @staticmethod
    def _prepare_image(
        value: np.ndarray,
        *,
        expected_channels: int,
    ) -> tuple[torch.Tensor, float]:
        image = np.asarray(value)
        if image.ndim == 2:
            image = image[:, :, None]
        if image.ndim != 3:
            raise ValueError(f"expected HWC image, got shape {image.shape}")
        if image.shape[2] < expected_channels:
            raise ValueError(
                f"expected at least {expected_channels} image channel(s), got {image.shape[2]}"
            )
        if image.shape[2] > expected_channels:
            image = image[:, :, -expected_channels:]
        std = float(np.std(image.astype(np.float32)))
        tensor = (
            torch.from_numpy(image.astype(np.float32) / 255.0)
            .permute(2, 0, 1)
            .unsqueeze(0)
            .contiguous()
        )
        return tensor, std

    def predict(
        self,
        obs: dict[str, np.ndarray],
        *,
        profile: str,
    ) -> VisualYawPrediction:
        if profile not in self.profile_to_id:
            return VisualYawPrediction(False, f"unsupported_profile:{profile}", profile=profile)
        if profile not in PROFILE_PERIOD_DEG:
            return VisualYawPrediction(False, f"missing_period:{profile}", profile=profile)
        if "cam_image" not in obs or "near_hole_crop" not in obs:
            return VisualYawPrediction(False, "missing_image_keys", profile=profile)

        try:
            cam, cam_std = self._prepare_image(
                obs["cam_image"],
                expected_channels=self.cam_channels,
            )
            crop, crop_std = self._prepare_image(
                obs["near_hole_crop"],
                expected_channels=self.crop_channels,
            )
        except ValueError as exc:
            return VisualYawPrediction(False, str(exc), profile=profile)

        profile_id = torch.tensor(
            [self.profile_to_id[profile]],
            dtype=torch.long,
            device=self.device,
        )
        with torch.no_grad():
            raw = self.model.raw_forward(
                cam.to(self.device),
                crop.to(self.device),
                profile_id,
            )
            raw_norm = raw.norm(dim=1).clamp_min(1e-6)
            pred = raw / raw_norm.unsqueeze(1)
            phase = torch.atan2(pred[:, 0], pred[:, 1])
            signed_error_deg = float(
                phase.item() * PROFILE_PERIOD_DEG[profile] / (2.0 * np.pi)
            )
        return VisualYawPrediction(
            True,
            "ok",
            profile=profile,
            signed_error_deg=signed_error_deg,
            abs_error_deg=abs(signed_error_deg),
            raw_norm=float(raw_norm.item()),
            cam_std=cam_std,
            crop_std=crop_std,
        )
