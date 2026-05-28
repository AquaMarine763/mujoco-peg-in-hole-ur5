from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn


@dataclass(frozen=True)
class ApproachAdapterConfig:
    crop_channels: int
    control_dim: int
    hidden_dim: int = 128
    image_channels: int = 0
    use_full_image: bool = False


class ApproachAdapterNet(nn.Module):
    def __init__(self, config: ApproachAdapterConfig) -> None:
        super().__init__()
        self.config = config
        if config.crop_channels <= 0:
            raise ValueError("crop_channels must be positive.")
        if config.use_full_image and config.image_channels <= 0:
            raise ValueError("image_channels must be positive when use_full_image is enabled.")
        # Keep this module name for compatibility with v1 crop-only checkpoints.
        self.image_encoder = _make_image_encoder(config.crop_channels)
        self.full_image_encoder = (
            _make_image_encoder(config.image_channels) if config.use_full_image else None
        )
        visual_dim = 64 + (64 if config.use_full_image else 0)
        self.head = nn.Sequential(
            nn.Linear(visual_dim + config.control_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, 3),
        )

    def forward(
        self,
        crop: torch.Tensor,
        control_state: torch.Tensor,
        image: torch.Tensor | None = None,
    ) -> torch.Tensor:
        crop_features = self.image_encoder(_normalize_image_tensor(crop))
        features = [crop_features]
        if self.config.use_full_image:
            if image is None:
                raise ValueError("Full-image approach adapter requires image input.")
            if self.full_image_encoder is None:
                raise RuntimeError("full_image_encoder is not initialized.")
            features.insert(0, self.full_image_encoder(_normalize_image_tensor(image)))
        features.append(control_state.float())
        return self.head(torch.cat(features, dim=1))


class ApproachAdapterPolicy:
    def __init__(
        self,
        *,
        net: ApproachAdapterNet,
        control_mean: torch.Tensor,
        control_std: torch.Tensor,
        device: torch.device,
    ) -> None:
        self.net = net.to(device)
        self.net.eval()
        self.control_mean = control_mean.to(device)
        self.control_std = control_std.to(device)
        self.device = device

    @classmethod
    def load(cls, path: Path, device: str | torch.device = "cpu") -> "ApproachAdapterPolicy":
        torch_device = torch.device(device)
        try:
            checkpoint = torch.load(path, map_location=torch_device, weights_only=False)
        except TypeError:
            checkpoint = torch.load(path, map_location=torch_device)
        model_config = checkpoint["model_config"]
        config = ApproachAdapterConfig(
            crop_channels=int(model_config["crop_channels"]),
            control_dim=int(model_config["control_dim"]),
            hidden_dim=int(model_config.get("hidden_dim", 128)),
            image_channels=int(model_config.get("image_channels", 0)),
            use_full_image=bool(model_config.get("use_full_image", False)),
        )
        net = ApproachAdapterNet(config)
        net.load_state_dict(checkpoint["state_dict"])
        control_mean = torch.as_tensor(
            checkpoint["control_mean"],
            dtype=torch.float32,
            device=torch_device,
        ).reshape(1, -1)
        control_std = torch.as_tensor(
            checkpoint["control_std"],
            dtype=torch.float32,
            device=torch_device,
        ).reshape(1, -1)
        return cls(
            net=net,
            control_mean=control_mean,
            control_std=control_std,
            device=torch_device,
        )

    @property
    def control_dim(self) -> int:
        return int(self.control_mean.shape[1])

    def predict(self, obs: dict[str, Any]) -> np.ndarray:
        crop_source = obs.get("near_hole_crop", obs.get("cam_image"))
        if crop_source is None:
            raise KeyError("approach adapter requires near_hole_crop or cam_image in obs.")
        crop = _image_to_tensor(crop_source, self.device)
        image = None
        if self.net.config.use_full_image:
            image_source = obs.get("cam_image")
            if image_source is None:
                raise KeyError("full-image approach adapter requires cam_image in obs.")
            image = _image_to_tensor(image_source, self.device)
        control_state = _control_to_tensor(
            obs.get("control_state"),
            self.control_dim,
            self.device,
        )
        control_state = (control_state - self.control_mean) / self.control_std
        with torch.no_grad():
            residual = self.net(crop, control_state, image=image)
        return residual.detach().cpu().numpy().reshape(3).astype(np.float32)


def save_adapter_checkpoint(
    *,
    path: Path,
    net: ApproachAdapterNet,
    control_mean: np.ndarray,
    control_std: np.ndarray,
    metadata: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "state_dict": net.state_dict(),
        "model_config": {
            "crop_channels": net.config.crop_channels,
            "image_channels": net.config.image_channels,
            "control_dim": net.config.control_dim,
            "hidden_dim": net.config.hidden_dim,
            "use_full_image": net.config.use_full_image,
        },
        "control_mean": np.asarray(control_mean, dtype=np.float32),
        "control_std": np.asarray(control_std, dtype=np.float32),
        "metadata": metadata,
    }
    torch.save(checkpoint, path)


def _make_image_encoder(channels: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(channels, 16, kernel_size=5, stride=2, padding=2),
        nn.ReLU(),
        nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
        nn.ReLU(),
        nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
        nn.ReLU(),
        nn.AdaptiveAvgPool2d((1, 1)),
        nn.Flatten(),
    )


def _normalize_image_tensor(image: torch.Tensor) -> torch.Tensor:
    if image.dtype == torch.uint8:
        return image.float() / 255.0
    normalized = image.float()
    if normalized.numel() and float(normalized.detach().max()) > 2.0:
        normalized = normalized / 255.0
    return normalized


def _image_to_tensor(image: Any, device: torch.device) -> torch.Tensor:
    array = np.asarray(image)
    if array.ndim == 3:
        if array.shape[0] in (1, 3, 4) and array.shape[-1] not in (1, 3, 4):
            chw = array
        else:
            chw = np.transpose(array, (2, 0, 1))
        array = chw[None, ...]
    elif array.ndim == 4:
        if array.shape[1] in (1, 3, 4):
            pass
        else:
            array = np.transpose(array, (0, 3, 1, 2))
    else:
        raise ValueError(f"Expected image rank 3 or 4, got {array.shape}.")
    return torch.as_tensor(array, device=device)


def _control_to_tensor(
    control_state: Any,
    expected_dim: int,
    device: torch.device,
) -> torch.Tensor:
    if control_state is None:
        array = np.zeros((1, expected_dim), dtype=np.float32)
    else:
        array = np.asarray(control_state, dtype=np.float32).reshape(1, -1)
    if array.shape[1] != expected_dim:
        raise ValueError(
            f"Expected control_state dim {expected_dim}, got {array.shape[1]}."
        )
    return torch.as_tensor(array, dtype=torch.float32, device=device)
