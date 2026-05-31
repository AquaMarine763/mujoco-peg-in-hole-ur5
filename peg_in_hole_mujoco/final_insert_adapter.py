from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn


@dataclass(frozen=True)
class FinalInsertAdapterConfig:
    input_dim: int
    hidden_dim: int = 64
    num_hidden_layers: int = 2
    target_scale: float = 1000.0
    feature_clip: float = 10.0


class FinalInsertAdapterNet(nn.Module):
    """Small MLP for local final-insert correction from trace-derived state."""

    def __init__(self, config: FinalInsertAdapterConfig) -> None:
        super().__init__()
        self.config = config
        if config.input_dim <= 0:
            raise ValueError("input_dim must be positive.")
        if config.hidden_dim <= 0:
            raise ValueError("hidden_dim must be positive.")
        if config.num_hidden_layers <= 0:
            raise ValueError("num_hidden_layers must be positive.")
        if config.target_scale <= 0.0:
            raise ValueError("target_scale must be positive.")
        if config.feature_clip <= 0.0:
            raise ValueError("feature_clip must be positive.")

        layers: list[nn.Module] = []
        dim = config.input_dim
        for _ in range(config.num_hidden_layers):
            layers.append(nn.Linear(dim, config.hidden_dim))
            layers.append(nn.ReLU())
            dim = config.hidden_dim
        layers.append(nn.Linear(dim, 3))
        self.net = nn.Sequential(*layers)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features.float())


class FinalInsertAdapterPolicy:
    def __init__(
        self,
        *,
        net: FinalInsertAdapterNet,
        feature_mean: torch.Tensor,
        feature_std: torch.Tensor,
        feature_names: tuple[str, ...],
        device: torch.device,
    ) -> None:
        self.net = net.to(device)
        self.net.eval()
        self.feature_mean = feature_mean.to(device)
        self.feature_std = feature_std.to(device)
        self.feature_names = feature_names
        self.device = device

    @classmethod
    def load(
        cls,
        path: Path,
        device: str | torch.device = "cpu",
    ) -> "FinalInsertAdapterPolicy":
        torch_device = torch.device(device)
        try:
            checkpoint = torch.load(path, map_location=torch_device, weights_only=False)
        except TypeError:
            checkpoint = torch.load(path, map_location=torch_device)
        model_config = checkpoint["model_config"]
        config = FinalInsertAdapterConfig(
            input_dim=int(model_config["input_dim"]),
            hidden_dim=int(model_config.get("hidden_dim", 64)),
            num_hidden_layers=int(model_config.get("num_hidden_layers", 2)),
            target_scale=float(model_config.get("target_scale", 1000.0)),
            feature_clip=float(model_config.get("feature_clip", 10.0)),
        )
        net = FinalInsertAdapterNet(config)
        net.load_state_dict(checkpoint["state_dict"])
        feature_mean = torch.as_tensor(
            checkpoint["feature_mean"],
            dtype=torch.float32,
            device=torch_device,
        ).reshape(1, -1)
        feature_std = torch.as_tensor(
            checkpoint["feature_std"],
            dtype=torch.float32,
            device=torch_device,
        ).reshape(1, -1)
        feature_names = tuple(str(name) for name in checkpoint["feature_names"])
        if len(feature_names) != config.input_dim:
            raise ValueError("checkpoint feature_names length does not match input_dim.")
        return cls(
            net=net,
            feature_mean=feature_mean,
            feature_std=feature_std,
            feature_names=feature_names,
            device=torch_device,
        )

    def predict(self, features: np.ndarray | dict[str, Any]) -> np.ndarray:
        array = self._feature_array(features)
        tensor = torch.as_tensor(array, dtype=torch.float32, device=self.device)
        tensor = (tensor - self.feature_mean) / self.feature_std
        tensor = torch.clamp(
            tensor,
            min=-self.net.config.feature_clip,
            max=self.net.config.feature_clip,
        )
        with torch.no_grad():
            scaled_action = self.net(tensor)
        action = scaled_action.detach().cpu().numpy() / self.net.config.target_scale
        return action.reshape(-1, 3).astype(np.float32)

    def _feature_array(self, features: np.ndarray | dict[str, Any]) -> np.ndarray:
        if isinstance(features, dict):
            values = [float(features[name]) for name in self.feature_names]
            return np.asarray(values, dtype=np.float32).reshape(1, -1)
        array = np.asarray(features, dtype=np.float32)
        if array.ndim == 1:
            array = array.reshape(1, -1)
        if array.ndim != 2:
            raise ValueError(f"Expected feature array rank 1 or 2, got {array.shape}.")
        if array.shape[1] != len(self.feature_names):
            raise ValueError(
                f"Expected {len(self.feature_names)} features, got {array.shape[1]}."
            )
        return array


def save_final_insert_adapter_checkpoint(
    *,
    path: Path,
    net: FinalInsertAdapterNet,
    feature_mean: np.ndarray,
    feature_std: np.ndarray,
    feature_names: tuple[str, ...],
    metadata: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "state_dict": net.state_dict(),
        "model_config": {
            "input_dim": net.config.input_dim,
            "hidden_dim": net.config.hidden_dim,
            "num_hidden_layers": net.config.num_hidden_layers,
            "target_scale": net.config.target_scale,
            "feature_clip": net.config.feature_clip,
        },
        "feature_mean": np.asarray(feature_mean, dtype=np.float32),
        "feature_std": np.asarray(feature_std, dtype=np.float32),
        "feature_names": tuple(str(name) for name in feature_names),
        "metadata": metadata,
    }
    torch.save(checkpoint, path)
