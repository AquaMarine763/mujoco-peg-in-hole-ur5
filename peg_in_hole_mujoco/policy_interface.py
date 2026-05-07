from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from peg_in_hole_mujoco.envs.peg_in_hole_env import PegInHoleMujocoEnv


class PolicyAdapter(Protocol):
    def predict(self, observation: Any) -> np.ndarray:
        """Return a Cartesian delta action in meters."""


@dataclass(frozen=True)
class ActionTransformResult:
    action: np.ndarray
    diagnostics: dict[str, Any]


class ActionTransformer(Protocol):
    def reset(self) -> None:
        """Reset per-episode transformer state."""

    def transform(self, info: dict[str, Any], policy_action: np.ndarray) -> ActionTransformResult:
        """Return the pre-safety action and optional trace diagnostics."""


class ObservationProvider(Protocol):
    def reset(self, seed: int | None = None) -> tuple[Any, dict[str, Any]]:
        """Reset the data source and return the first policy observation."""


@dataclass(frozen=True)
class StepResult:
    observation: Any
    reward: float
    terminated: bool
    truncated: bool
    info: dict[str, Any]


class ActionExecutor(Protocol):
    def execute(self, action: np.ndarray) -> StepResult:
        """Execute a safe Cartesian delta action."""

    def close(self) -> None:
        """Release backend resources."""


@dataclass(frozen=True)
class SafetyConfig:
    max_action: float = 0.005
    workspace_low: tuple[float, float, float] = (0.30, -0.25, 0.55)
    workspace_high: tuple[float, float, float] = (0.75, 0.25, 0.85)
    action_filter_alpha: float = 1.0


@dataclass(frozen=True)
class SafeAction:
    raw_action: np.ndarray
    limited_action: np.ndarray
    filtered_action: np.ndarray
    safe_action: np.ndarray
    target_before_workspace_clip: np.ndarray
    target_after_workspace_clip: np.ndarray
    action_limited: bool
    workspace_limited: bool


@dataclass(frozen=True)
class EpisodeResult:
    episode: int
    success: bool
    collision: bool
    truncated: bool
    steps: int
    episode_return: float
    final_dist_xy: float
    final_dist_z: float


class SB3PolicyAdapter:
    def __init__(self, model: Any, deterministic: bool = True):
        self.model = model
        self.deterministic = deterministic

    def predict(self, observation: Any) -> np.ndarray:
        action, _ = self.model.predict(observation, deterministic=self.deterministic)
        return np.asarray(action, dtype=np.float64).reshape(3)


class SafetyFilter:
    def __init__(self, config: SafetyConfig):
        if config.max_action <= 0.0:
            raise ValueError("SafetyConfig.max_action must be positive.")
        if not 0.0 < config.action_filter_alpha <= 1.0:
            raise ValueError("SafetyConfig.action_filter_alpha must be in (0, 1].")
        self.config = config
        self.workspace_low = np.asarray(config.workspace_low, dtype=np.float64)
        self.workspace_high = np.asarray(config.workspace_high, dtype=np.float64)
        if self.workspace_low.shape != (3,) or self.workspace_high.shape != (3,):
            raise ValueError("Safety workspace bounds must be 3D.")
        if np.any(self.workspace_low >= self.workspace_high):
            raise ValueError("Safety workspace low bounds must be lower than high bounds.")
        self.previous_action = np.zeros(3, dtype=np.float64)

    def reset(self) -> None:
        self.previous_action = np.zeros(3, dtype=np.float64)

    def filter(self, raw_action: np.ndarray, current_tip_pos: np.ndarray) -> SafeAction:
        raw_action = np.asarray(raw_action, dtype=np.float64).reshape(3)
        current_tip_pos = np.asarray(current_tip_pos, dtype=np.float64).reshape(3)

        limited_action = np.clip(
            raw_action,
            -self.config.max_action,
            self.config.max_action,
        )
        alpha = self.config.action_filter_alpha
        filtered_action = alpha * limited_action + (1.0 - alpha) * self.previous_action
        target_before_clip = current_tip_pos + filtered_action
        target_after_clip = np.clip(target_before_clip, self.workspace_low, self.workspace_high)
        safe_action = target_after_clip - current_tip_pos
        self.previous_action = safe_action.copy()

        return SafeAction(
            raw_action=raw_action,
            limited_action=limited_action,
            filtered_action=filtered_action,
            safe_action=safe_action,
            target_before_workspace_clip=target_before_clip,
            target_after_workspace_clip=target_after_clip,
            action_limited=not np.allclose(raw_action, limited_action),
            workspace_limited=not np.allclose(target_before_clip, target_after_clip),
        )


class MujocoObservationProvider:
    def __init__(self, env: PegInHoleMujocoEnv):
        self.env = env

    def reset(self, seed: int | None = None) -> tuple[Any, dict[str, Any]]:
        return self.env.reset(seed=seed)


class MujocoActionExecutor:
    def __init__(self, env: PegInHoleMujocoEnv):
        self.env = env

    def execute(self, action: np.ndarray) -> StepResult:
        observation, reward, terminated, truncated, info = self.env.step(action)
        return StepResult(
            observation=observation,
            reward=float(reward),
            terminated=bool(terminated),
            truncated=bool(truncated),
            info=info,
        )

    def close(self) -> None:
        self.env.close()


class PolicyInferenceSession:
    def __init__(
        self,
        observation_provider: ObservationProvider,
        action_executor: ActionExecutor,
        policy: PolicyAdapter,
        safety_filter: SafetyFilter,
        control_frequency_hz: float,
        action_transformer: ActionTransformer | None = None,
    ):
        if control_frequency_hz <= 0.0:
            raise ValueError("control_frequency_hz must be positive.")
        self.observation_provider = observation_provider
        self.action_executor = action_executor
        self.policy = policy
        self.safety_filter = safety_filter
        self.control_frequency_hz = float(control_frequency_hz)
        self.control_period_sec = 1.0 / self.control_frequency_hz
        self.action_transformer = action_transformer

    def run_episode(self, episode: int, seed: int) -> tuple[EpisodeResult, list[dict[str, Any]]]:
        self.safety_filter.reset()
        if self.action_transformer is not None:
            self.action_transformer.reset()
        obs, info = self.observation_provider.reset(seed=seed)
        initial_action_diagnostics = self._initial_action_diagnostics()
        episode_return = 0.0
        rows: list[dict[str, Any]] = [
            self._row(
                episode=episode,
                step=0,
                reward=0.0,
                episode_return=episode_return,
                raw_action=np.zeros(3, dtype=np.float64),
                policy_action=np.zeros(3, dtype=np.float64),
                action_diagnostics=initial_action_diagnostics,
                safe_action=zero_safe_action(info),
                info=info,
                terminated=False,
                truncated=False,
            )
        ]

        while True:
            policy_action = self.policy.predict(obs)
            raw_action = policy_action
            action_diagnostics: dict[str, Any] = {}
            if self.action_transformer is not None:
                transform = self.action_transformer.transform(info, policy_action)
                raw_action = transform.action
                action_diagnostics = transform.diagnostics
            safe_action = self.safety_filter.filter(raw_action, info["peg_tip_pos"])
            step_result = self.action_executor.execute(safe_action.safe_action)
            obs = step_result.observation
            info = step_result.info
            episode_return += step_result.reward
            rows.append(
                self._row(
                    episode=episode,
                    step=int(info["step_count"]),
                    reward=step_result.reward,
                    episode_return=episode_return,
                    raw_action=raw_action,
                    policy_action=policy_action,
                    action_diagnostics=action_diagnostics,
                    safe_action=safe_action,
                    info=info,
                    terminated=step_result.terminated,
                    truncated=step_result.truncated,
                )
            )
            if step_result.terminated or step_result.truncated:
                break

        result = EpisodeResult(
            episode=episode,
            success=bool(info["insertion_success"]),
            collision=bool(info["collision"]),
            truncated=bool(step_result.truncated),
            steps=int(info["step_count"]),
            episode_return=episode_return,
            final_dist_xy=float(info["dist_xy"]),
            final_dist_z=float(info["dist_z"]),
        )
        return result, rows

    def close(self) -> None:
        self.action_executor.close()

    def _initial_action_diagnostics(self) -> dict[str, Any]:
        if self.action_transformer is None:
            return {}
        initial_diagnostics = getattr(self.action_transformer, "initial_diagnostics", None)
        if callable(initial_diagnostics):
            return dict(initial_diagnostics())
        return {}

    def _row(
        self,
        *,
        episode: int,
        step: int,
        reward: float,
        episode_return: float,
        raw_action: np.ndarray,
        policy_action: np.ndarray,
        action_diagnostics: dict[str, Any],
        safe_action: SafeAction,
        info: dict[str, Any],
        terminated: bool,
        truncated: bool,
    ) -> dict[str, Any]:
        row: dict[str, Any] = {
            "episode": episode,
            "step": step,
            "control_period_sec": self.control_period_sec,
            "reward": float(reward),
            "episode_return": float(episode_return),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "success": bool(info.get("insertion_success", False)),
            "collision": bool(info.get("collision", False)),
            "dist_xy": float(info.get("dist_xy", float("nan"))),
            "dist_z": float(info.get("dist_z", float("nan"))),
            "shaped_distance": float(info.get("shaped_distance", float("nan"))),
            "desired_z": float(info.get("desired_z", float("nan"))),
            "guard_enabled": bool(action_diagnostics.get("guard_enabled", False)),
            "guard_active": bool(action_diagnostics.get("guard_active", False)),
            "guard_should_activate": bool(action_diagnostics.get("guard_should_activate", False)),
            "guard_can_activate": bool(action_diagnostics.get("guard_can_activate", False)),
            "guard_activated": bool(action_diagnostics.get("guard_activated", False)),
            "guard_down_blocked": bool(action_diagnostics.get("guard_down_blocked", False)),
            "guard_steps_since_reset": int(action_diagnostics.get("guard_steps_since_reset", -1)),
            "guard_min_policy_steps": int(action_diagnostics.get("guard_min_policy_steps", 0)),
            "guard_dist_xy": float(action_diagnostics.get("guard_dist_xy", float("nan"))),
            "guard_z_above_target": float(
                action_diagnostics.get("guard_z_above_target", float("nan"))
            ),
            "action_limited": safe_action.action_limited,
            "workspace_limited": safe_action.workspace_limited,
            "control_action_scale_multiplier": float(info.get("control_action_scale_multiplier", float("nan"))),
            "control_action_noise_std": float(info.get("control_action_noise_std", float("nan"))),
            "control_action_delay": int(info.get("control_action_delay", -1)),
            "control_action_filter_alpha": float(info.get("control_action_filter_alpha", float("nan"))),
            "pose_source": str(info.get("pose_source", "")),
            "pose_frame": str(info.get("pose_frame", "")),
            "pose_step": int(info.get("pose_step", -1)),
            "pose_timestamp": float(info.get("pose_timestamp", float("nan"))),
            "target_source": str(info.get("target_source", "")),
            "target_frame": str(info.get("target_frame", "")),
            "target_timestamp": float(info.get("target_timestamp", float("nan"))),
        }
        row.update(vector_fields("target", info.get("target_pos", (float("nan"),) * 3), 3))
        row.update(vector_fields("peg_tip", info.get("peg_tip_pos", (float("nan"),) * 3), 3))
        row.update(vector_fields("tcp_pos", info.get("tcp_pos"), 3))
        row.update(vector_fields("tcp_rotvec", info.get("tcp_rotvec"), 3))
        row.update(vector_fields("policy_action", action_diagnostics.get("policy_action", policy_action), 3))
        row.update(vector_fields("guarded_action", action_diagnostics.get("guarded_action"), 3))
        row.update(vector_fields("final_action", action_diagnostics.get("final_action", raw_action), 3))
        row.update(vector_fields("raw_action", raw_action, 3))
        row.update(vector_fields("limited_action", safe_action.limited_action, 3))
        row.update(vector_fields("filtered_action", safe_action.filtered_action, 3))
        row.update(vector_fields("safe_action", safe_action.safe_action, 3))
        row.update(vector_fields("env_commanded_action", info.get("commanded_action", (float("nan"),) * 3), 3))
        row.update(vector_fields("env_applied_action", info.get("applied_action", (float("nan"),) * 3), 3))
        row.update(vector_fields("safe_target_before_clip", safe_action.target_before_workspace_clip, 3))
        row.update(vector_fields("safe_target_after_clip", safe_action.target_after_workspace_clip, 3))
        return row


class MujocoPolicySession(PolicyInferenceSession):
    def __init__(
        self,
        env: PegInHoleMujocoEnv,
        policy: PolicyAdapter,
        safety_filter: SafetyFilter,
        control_frequency_hz: float,
        action_transformer: ActionTransformer | None = None,
    ):
        super().__init__(
            observation_provider=MujocoObservationProvider(env),
            action_executor=MujocoActionExecutor(env),
            policy=policy,
            safety_filter=safety_filter,
            control_frequency_hz=control_frequency_hz,
            action_transformer=action_transformer,
        )


def zero_safe_action(info: dict[str, Any]) -> SafeAction:
    peg_tip_pos = np.asarray(info["peg_tip_pos"], dtype=np.float64)
    zeros = np.zeros(3, dtype=np.float64)
    return SafeAction(
        raw_action=zeros,
        limited_action=zeros,
        filtered_action=zeros,
        safe_action=zeros,
        target_before_workspace_clip=peg_tip_pos,
        target_after_workspace_clip=peg_tip_pos,
        action_limited=False,
        workspace_limited=False,
    )


def vector_fields(prefix: str, value: Any, size: int) -> dict[str, float]:
    labels = ("x", "y", "z") if size == 3 else tuple(str(index) for index in range(size))
    if value is None:
        return {f"{prefix}_{label}": float("nan") for label in labels}
    array = np.asarray(value, dtype=np.float64).reshape(-1)
    return {
        f"{prefix}_{label}": float(array[index]) if index < array.size else float("nan")
        for index, label in enumerate(labels)
    }


def write_trace_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
