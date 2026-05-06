from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np

from peg_in_hole_mujoco.oracle_controller import OracleControllerConfig, oracle_action


GuardScenarioFilter = Literal["none", "all", "geometry", "hard"]


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
        if self.oracle.mode != "guarded_two_stage":
            raise ValueError("GuardedPolicyConfig.oracle must use guarded_two_stage mode.")


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

    def should_activate(self, info: dict[str, Any]) -> bool:
        dist_xy, z_above_target = self.activation_metrics(info)
        return (
            self.config.guard_risk_xy <= dist_xy <= self.config.guard_start_xy
            and z_above_target <= self.config.guard_start_z
        )

    def activation_metrics(self, info: dict[str, Any]) -> tuple[float, float]:
        tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
        target = np.asarray(info["target_pos"], dtype=np.float64)
        dist_xy = float(info["dist_xy"])
        z_above_target = float(tip[2] - target[2])
        return dist_xy, z_above_target

    def step(
        self,
        env: Any,
        info: dict[str, Any],
        policy_action: np.ndarray,
        *,
        scenario_name: str,
        scenario_level: str,
    ) -> GuardedPolicyStep:
        policy_action = np.asarray(policy_action, dtype=np.float32)
        guarded_enabled = self.scenario_uses_guard(scenario_name, scenario_level)
        dist_xy, z_above_target = self.activation_metrics(info)
        should_activate = guarded_enabled and self.should_activate(info)
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
            tip = np.asarray(info["peg_tip_pos"], dtype=np.float64)
            target = np.asarray(info["target_pos"], dtype=np.float64)
            if float(tip[2] - target[2]) > self.config.guard_start_z:
                self.guard_active = False
                activated_this_step = False

        if not self.guard_active:
            result = GuardedPolicyStep(
                action=policy_action,
                guarded=False,
                guard_active=False,
                guard_enabled=True,
                guard_should_activate=should_activate,
                guard_can_activate=can_activate,
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

        guarded_action = oracle_action(env, info, self.config.oracle)
        blend = float(np.clip(self.config.guard_blend, 0.0, 1.0))
        action = (1.0 - blend) * policy_action + blend * guarded_action
        down_blocked = False
        if (
            self.config.guard_block_down_when_unaligned
            and dist_xy > self.config.oracle.guarded_align_xy_tolerance
            and action[2] < 0.0
        ):
            action[2] = 0.0
            down_blocked = True
        action = np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32)
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
