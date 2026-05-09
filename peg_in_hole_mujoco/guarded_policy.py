from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

import numpy as np

from peg_in_hole_mujoco.oracle_controller import (
    OracleControllerConfig,
    oracle_action_from_state,
)


GuardScenarioFilter = Literal["none", "all", "geometry", "hard"]


@dataclass(frozen=True)
class GuardedDeploymentState:
    """Backend-neutral state needed by the guarded final-insertion controller."""

    peg_tip_pos: np.ndarray
    target_pos: np.ndarray
    applied_action: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    approach_height: float = 0.08
    action_low: np.ndarray = field(default_factory=lambda: np.full(3, -0.005, dtype=np.float64))
    action_high: np.ndarray = field(default_factory=lambda: np.full(3, 0.005, dtype=np.float64))
    dist_xy: float | None = None

    def __post_init__(self) -> None:
        _as_vector3(self.peg_tip_pos, "peg_tip_pos")
        _as_vector3(self.target_pos, "target_pos")
        _as_vector3(self.applied_action, "applied_action")
        low = _as_vector3(self.action_low, "action_low")
        high = _as_vector3(self.action_high, "action_high")
        if self.approach_height < 0.0:
            raise ValueError("approach_height cannot be negative.")
        if np.any(low >= high):
            raise ValueError("action_low must be lower than action_high.")
        if self.dist_xy is not None and self.dist_xy < 0.0:
            raise ValueError("dist_xy cannot be negative.")

    @classmethod
    def from_info(
        cls,
        info: dict[str, Any],
        *,
        approach_height: float = 0.08,
        action_low: np.ndarray | tuple[float, float, float] = (-0.005, -0.005, -0.005),
        action_high: np.ndarray | tuple[float, float, float] = (0.005, 0.005, 0.005),
    ) -> "GuardedDeploymentState":
        return cls(
            peg_tip_pos=np.asarray(info["peg_tip_pos"], dtype=np.float64),
            target_pos=np.asarray(info["target_pos"], dtype=np.float64),
            applied_action=np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64),
            approach_height=float(approach_height),
            action_low=np.asarray(action_low, dtype=np.float64),
            action_high=np.asarray(action_high, dtype=np.float64),
            dist_xy=float(info["dist_xy"]) if "dist_xy" in info else None,
        )


class GuardStateProvider(Protocol):
    def state_from_info(self, info: dict[str, Any]) -> GuardedDeploymentState:
        """Convert backend-specific telemetry into guarded deployment state."""


class MujocoGuardStateProvider:
    def __init__(self, env: Any):
        self.env = env

    def state_from_info(self, info: dict[str, Any]) -> GuardedDeploymentState:
        return GuardedDeploymentState.from_info(
            info,
            approach_height=float(self.env.approach_height),
            action_low=np.asarray(self.env.action_space.low, dtype=np.float64),
            action_high=np.asarray(self.env.action_space.high, dtype=np.float64),
        )


class RealGuardStateProvider:
    """Adapter for real-robot telemetry shaped like the deployment trace info."""

    def __init__(
        self,
        *,
        approach_height: float = 0.08,
        action_limit: float = 0.005,
        action_low: np.ndarray | tuple[float, float, float] | None = None,
        action_high: np.ndarray | tuple[float, float, float] | None = None,
    ):
        if action_limit <= 0.0:
            raise ValueError("action_limit must be positive.")
        self.approach_height = float(approach_height)
        self.action_low = (
            np.asarray(action_low, dtype=np.float64)
            if action_low is not None
            else np.full(3, -float(action_limit), dtype=np.float64)
        )
        self.action_high = (
            np.asarray(action_high, dtype=np.float64)
            if action_high is not None
            else np.full(3, float(action_limit), dtype=np.float64)
        )

    def state_from_info(self, info: dict[str, Any]) -> GuardedDeploymentState:
        return GuardedDeploymentState.from_info(
            info,
            approach_height=self.approach_height,
            action_low=self.action_low,
            action_high=self.action_high,
        )


@dataclass(frozen=True)
class GuardedPolicyConfig:
    scenario_filter: GuardScenarioFilter = "geometry"
    guard_start_xy: float = 0.06
    guard_start_z: float = 0.10
    guard_risk_xy: float = 0.0
    guard_blend: float = 1.0
    guard_min_policy_steps: int = 0
    guard_block_down_when_unaligned: bool = False
    guard_release_on_high: bool = False
    oracle: OracleControllerConfig = field(
        default_factory=lambda: OracleControllerConfig(mode="guarded_two_stage")
    )

    def __post_init__(self) -> None:
        if self.scenario_filter not in ("none", "all", "geometry", "hard"):
            raise ValueError("scenario_filter must be one of: none, all, geometry, hard.")
        if self.guard_start_xy <= 0.0:
            raise ValueError("guard_start_xy must be positive.")
        if self.guard_start_z <= 0.0:
            raise ValueError("guard_start_z must be positive.")
        if self.guard_risk_xy < 0.0:
            raise ValueError("guard_risk_xy cannot be negative.")
        if self.guard_risk_xy > self.guard_start_xy:
            raise ValueError("guard_risk_xy must be <= guard_start_xy.")
        if not 0.0 <= self.guard_blend <= 1.0:
            raise ValueError("guard_blend must be between 0 and 1.")
        if self.guard_min_policy_steps < 0:
            raise ValueError("guard_min_policy_steps cannot be negative.")
        if self.oracle.mode not in ("guarded_two_stage", "high_start_two_phase"):
            raise ValueError(
                "GuardedPolicyConfig.oracle must use guarded_two_stage or high_start_two_phase mode."
            )


@dataclass
class GuardedPolicyStep:
    action: np.ndarray
    guarded: bool
    guard_active: bool
    guard_enabled: bool
    guard_should_activate: bool
    guard_can_activate: bool
    guard_activated: bool
    guard_down_blocked: bool
    guard_steps_since_reset: int
    guard_dist_xy: float
    guard_z_above_target: float
    policy_action: np.ndarray
    guarded_action: np.ndarray | None


class GuardedPolicyController:
    def __init__(self, config: GuardedPolicyConfig) -> None:
        self.config = config
        self.guard_active = False
        self.guard_steps = 0
        self.steps_since_reset = 0

    def reset(self) -> None:
        self.guard_active = False
        self.guard_steps = 0
        self.steps_since_reset = 0

    def scenario_uses_guard(self, scenario_name: str, scenario_level: str) -> bool:
        if self.config.scenario_filter == "none":
            return False
        if self.config.scenario_filter == "all":
            return True
        if self.config.scenario_filter == "hard":
            return scenario_name == "hard_full_light_bucket"
        return scenario_level in ("full_light_geometry", "full_contact_light", "full")

    def should_activate(self, state: GuardedDeploymentState) -> bool:
        dist_xy, z_above_target = self.activation_metrics(state)
        return (
            self.config.guard_risk_xy <= dist_xy <= self.config.guard_start_xy
            and z_above_target <= self.config.guard_start_z
        )

    def activation_metrics(self, state: GuardedDeploymentState) -> tuple[float, float]:
        tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
        target = _as_vector3(state.target_pos, "target_pos")
        dist_xy = (
            float(state.dist_xy)
            if state.dist_xy is not None
            else float(np.linalg.norm(tip[:2] - target[:2]))
        )
        z_above_target = float(tip[2] - target[2])
        return dist_xy, z_above_target

    def step_from_state(
        self,
        state: GuardedDeploymentState,
        policy_action: np.ndarray,
        *,
        scenario_name: str,
        scenario_level: str,
    ) -> GuardedPolicyStep:
        policy_action = np.asarray(policy_action, dtype=np.float32)
        guarded_enabled = self.scenario_uses_guard(scenario_name, scenario_level)
        dist_xy, z_above_target = self.activation_metrics(state)
        should_activate = guarded_enabled and self.should_activate(state)
        can_activate = self.steps_since_reset >= self.config.guard_min_policy_steps
        step_index = self.steps_since_reset
        if not guarded_enabled:
            result = GuardedPolicyStep(
                action=policy_action,
                guarded=False,
                guard_active=False,
                guard_enabled=False,
                guard_should_activate=False,
                guard_can_activate=False,
                guard_activated=False,
                guard_down_blocked=False,
                guard_steps_since_reset=step_index,
                guard_dist_xy=dist_xy,
                guard_z_above_target=z_above_target,
                policy_action=policy_action,
                guarded_action=None,
            )
            self.steps_since_reset += 1
            return result

        activated_this_step = False
        if not self.guard_active and can_activate and should_activate:
            self.guard_active = True
            activated_this_step = True
        if self.config.guard_release_on_high and self.guard_active:
            tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
            target = _as_vector3(state.target_pos, "target_pos")
            if float(tip[2] - target[2]) > self.config.guard_start_z:
                self.guard_active = False
                activated_this_step = False

        if not self.guard_active:
            action = policy_action.copy()
            down_blocked = self._block_down_if_unaligned(action, dist_xy)
            result = GuardedPolicyStep(
                action=action.astype(np.float32),
                guarded=False,
                guard_active=False,
                guard_enabled=True,
                guard_should_activate=should_activate,
                guard_can_activate=can_activate,
                guard_activated=False,
                guard_down_blocked=down_blocked,
                guard_steps_since_reset=step_index,
                guard_dist_xy=dist_xy,
                guard_z_above_target=z_above_target,
                policy_action=policy_action,
                guarded_action=None,
            )
            self.steps_since_reset += 1
            return result

        guarded_action = oracle_action_from_state(
            peg_tip_pos=_as_vector3(state.peg_tip_pos, "peg_tip_pos"),
            target_pos=_as_vector3(state.target_pos, "target_pos"),
            applied_action=_as_vector3(state.applied_action, "applied_action"),
            approach_height=float(state.approach_height),
            action_low=_as_vector3(state.action_low, "action_low"),
            action_high=_as_vector3(state.action_high, "action_high"),
            config=self.config.oracle,
        )
        blend = float(np.clip(self.config.guard_blend, 0.0, 1.0))
        action = (1.0 - blend) * policy_action + blend * guarded_action
        down_blocked = self._block_down_if_unaligned(action, dist_xy)
        action = np.clip(action, state.action_low, state.action_high).astype(np.float32)
        self.guard_steps += 1
        result = GuardedPolicyStep(
            action=action,
            guarded=True,
            guard_active=True,
            guard_enabled=True,
            guard_should_activate=should_activate,
            guard_can_activate=can_activate,
            guard_activated=activated_this_step,
            guard_down_blocked=down_blocked,
            guard_steps_since_reset=step_index,
            guard_dist_xy=dist_xy,
            guard_z_above_target=z_above_target,
            policy_action=policy_action,
            guarded_action=guarded_action,
        )
        self.steps_since_reset += 1
        return result

    def step_with_provider(
        self,
        provider: GuardStateProvider,
        info: dict[str, Any],
        policy_action: np.ndarray,
        *,
        scenario_name: str,
        scenario_level: str,
    ) -> GuardedPolicyStep:
        return self.step_from_state(
            provider.state_from_info(info),
            policy_action,
            scenario_name=scenario_name,
            scenario_level=scenario_level,
        )

    def step(
        self,
        env: Any,
        info: dict[str, Any],
        policy_action: np.ndarray,
        *,
        scenario_name: str,
        scenario_level: str,
    ) -> GuardedPolicyStep:
        return self.step_with_provider(
            MujocoGuardStateProvider(env),
            info,
            policy_action,
            scenario_name=scenario_name,
            scenario_level=scenario_level,
        )

    def _block_down_if_unaligned(self, action: np.ndarray, dist_xy: float) -> bool:
        if (
            self.config.guard_block_down_when_unaligned
            and dist_xy > self.config.oracle.guarded_align_xy_tolerance
            and action[2] < 0.0
        ):
            action[2] = 0.0
            return True
        return False


def _as_vector3(value: Any, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64).reshape(-1)
    if array.size != 3:
        raise ValueError(f"{name} must contain exactly 3 values.")
    return array
