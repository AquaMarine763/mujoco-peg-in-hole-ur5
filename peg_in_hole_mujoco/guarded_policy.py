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
    actual_tip_delta: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    approach_height: float = 0.08
    action_low: np.ndarray = field(default_factory=lambda: np.full(3, -0.005, dtype=np.float64))
    action_high: np.ndarray = field(default_factory=lambda: np.full(3, 0.005, dtype=np.float64))
    dist_xy: float | None = None
    hole_clearance: float | None = None

    def __post_init__(self) -> None:
        _as_vector3(self.peg_tip_pos, "peg_tip_pos")
        _as_vector3(self.target_pos, "target_pos")
        _as_vector3(self.applied_action, "applied_action")
        _as_vector3(self.actual_tip_delta, "actual_tip_delta")
        low = _as_vector3(self.action_low, "action_low")
        high = _as_vector3(self.action_high, "action_high")
        if self.approach_height < 0.0:
            raise ValueError("approach_height cannot be negative.")
        if np.any(low >= high):
            raise ValueError("action_low must be lower than action_high.")
        if self.dist_xy is not None and self.dist_xy < 0.0:
            raise ValueError("dist_xy cannot be negative.")
        if self.hole_clearance is not None and self.hole_clearance < 0.0:
            raise ValueError("hole_clearance cannot be negative.")

    @classmethod
    def from_info(
        cls,
        info: dict[str, Any],
        *,
        approach_height: float = 0.08,
        action_low: np.ndarray | tuple[float, float, float] = (-0.005, -0.005, -0.005),
        action_high: np.ndarray | tuple[float, float, float] = (0.005, 0.005, 0.005),
    ) -> "GuardedDeploymentState":
        hole_clearance = _hole_clearance_from_info(info)
        return cls(
            peg_tip_pos=np.asarray(info["peg_tip_pos"], dtype=np.float64),
            target_pos=np.asarray(info["target_pos"], dtype=np.float64),
            applied_action=np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64),
            actual_tip_delta=np.asarray(
                info.get("action_actual_tip_delta", np.zeros(3)),
                dtype=np.float64,
            ),
            approach_height=float(approach_height),
            action_low=np.asarray(action_low, dtype=np.float64),
            action_high=np.asarray(action_high, dtype=np.float64),
            dist_xy=float(info["dist_xy"]) if "dist_xy" in info else None,
            hole_clearance=hole_clearance,
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
    guard_retry_enabled: bool = False
    guard_retry_stall_steps: int = 80
    guard_retry_xy_tolerance: float = 0.015
    guard_retry_z_max: float = 0.060
    guard_retry_lift_height: float = 0.080
    guard_retry_release_xy: float = 0.005
    guard_retry_max_attempts: int = 2
    guard_retry_max_steps: int = 120
    guard_insert_latch_enabled: bool = False
    guard_insert_latch_xy_tolerance: float = 0.005
    guard_insert_latch_release_xy: float = 0.009
    guard_insert_latch_resume_xy: float = 0.005
    guard_insert_latch_recenter_height: float = 0.0
    guard_insert_latch_recenter_z_tolerance: float = 0.0
    guard_insert_latch_max_down_action: float = 0.0
    guard_hover_enabled: bool = False
    guard_hover_xy_tolerance: float = 0.004
    guard_hover_release_xy: float = 0.006
    guard_hover_height: float = 0.050
    guard_hover_z_tolerance: float = 0.010
    guard_hover_required_steps: int = 6
    guard_hover_max_down_action: float = 0.002
    guard_near_action_scale_enabled: bool = False
    guard_near_action_xy_tolerance: float = 0.020
    guard_near_action_z_threshold: float = 0.070
    guard_near_max_xy_action: float = 0.002
    guard_near_max_down_action: float = 0.0015
    guard_fixture_clearance_enabled: bool = False
    guard_fixture_clearance_xy_min: float = 0.020
    guard_fixture_clearance_xy_max: float = 0.090
    guard_fixture_clearance_z_max: float = 0.060
    guard_fixture_clearance_lift_height: float = 0.100
    guard_fixture_clearance_max_up_action: float = 0.005
    guard_fixture_clearance_realign_enabled: bool = False
    guard_fixture_clearance_realign_start_z: float = 0.0
    guard_fixture_clearance_realign_xy: float = 0.020
    guard_fixture_clearance_max_xy_action: float = 0.005
    guard_fixture_clearance_max_down_action: float = 0.0
    guard_fixture_clearance_max_steps: int = 240
    guard_preinsert_recenter_enabled: bool = False
    guard_preinsert_recenter_start_z: float = 0.025
    guard_preinsert_recenter_min_z: float = 0.0
    guard_preinsert_recenter_trigger_xy: float = 0.004
    guard_preinsert_recenter_stable_xy: float = 0.0035
    guard_preinsert_recenter_height: float = 0.025
    guard_preinsert_recenter_z_tolerance: float = 0.006
    guard_preinsert_recenter_stable_steps: int = 3
    guard_preinsert_recenter_max_steps: int = 80
    guard_preinsert_recenter_max_xy_action: float = 0.005
    guard_preinsert_recenter_max_up_action: float = 0.005
    guard_preinsert_recenter_lift_before_lateral: bool = False
    guard_approach_recenter_enabled: bool = False
    guard_approach_recenter_requires_stateful_recovery: bool = True
    guard_approach_recenter_start_z: float = 0.075
    guard_approach_recenter_min_z: float = 0.045
    guard_approach_recenter_trigger_xy: float = 0.010
    guard_approach_recenter_max_xy: float = 0.030
    guard_approach_recenter_stable_xy: float = 0.005
    guard_approach_recenter_height: float = 0.060
    guard_approach_recenter_z_tolerance: float = 0.012
    guard_approach_recenter_stable_steps: int = 2
    guard_approach_recenter_max_steps: int = 220
    guard_approach_recenter_max_xy_action: float = 0.005
    guard_approach_recenter_max_up_action: float = 0.005
    guard_approach_recenter_xy_bias: tuple[float, float] = (0.0, 0.0)
    guard_stateful_recovery_enabled: bool = False
    guard_stateful_recovery_trigger_xy_min: float = 0.006
    guard_stateful_recovery_trigger_xy_max: float = 0.030
    guard_stateful_recovery_trigger_z_max: float = 0.130
    guard_stateful_recovery_lift_height: float = 0.060
    guard_stateful_recovery_lift_z_tolerance: float = 0.006
    guard_stateful_recovery_release_xy: float = 0.0048
    guard_stateful_recovery_resume_xy: float = 0.0065
    guard_stateful_recovery_resume_z: float = 0.012
    guard_stateful_recovery_stable_steps: int = 4
    guard_stateful_recovery_stall_steps: int = 100
    guard_stateful_recovery_min_xy_progress: float = 0.00035
    guard_stateful_recovery_min_actual_xy_motion: float = 0.00012
    guard_stateful_recovery_min_command_xy: float = 0.0025
    guard_stateful_recovery_max_attempts: int = 1
    guard_stateful_recovery_max_steps: int = 220
    guard_stateful_recovery_max_xy_action: float = 0.005
    guard_stateful_recovery_max_down_action: float = 0.0015
    guard_stateful_recovery_max_up_action: float = 0.005
    guard_final_servo_enabled: bool = False
    guard_final_servo_start_xy: float = 0.012
    guard_final_servo_start_z: float = 0.070
    guard_final_servo_min_start_z: float = 0.010
    guard_final_servo_hover_height: float = 0.040
    guard_final_servo_hover_z_tolerance: float = 0.010
    guard_final_servo_stable_xy: float = 0.0045
    guard_final_servo_descent_start_xy: float = 0.0
    guard_final_servo_stable_steps: int = 6
    guard_final_servo_release_xy: float = 0.008
    guard_final_servo_max_xy_action: float = 0.0025
    guard_final_servo_max_down_action: float = 0.0015
    guard_final_servo_low_recenter_enabled: bool = False
    guard_final_servo_low_recenter_z_max: float = 0.012
    guard_final_servo_low_recenter_trigger_xy: float = 0.0065
    guard_final_servo_low_recenter_release_xy: float = 0.0055
    guard_final_servo_low_recenter_height: float = 0.010
    guard_final_servo_low_recenter_stable_steps: int = 2
    guard_final_servo_low_recenter_max_steps: int = 120
    guard_final_servo_low_recenter_max_up_action: float = 0.003
    guard_final_servo_low_recenter_stall_steps: int = 0
    guard_final_servo_low_recenter_min_xy_progress: float = 0.0001
    guard_final_servo_descend_xy_bias: tuple[float, float] = (0.0, 0.0)
    guard_final_servo_descend_xy_bias_max_clearance: float = float("inf")
    guard_final_servo_descend_xy_bias_requires_stateful_recovery: bool = False
    guard_final_servo_lift_height: float = 0.060
    guard_final_servo_stall_steps: int = 80
    guard_final_servo_min_z_progress: float = 0.002
    guard_final_servo_max_retries: int = 2
    guard_final_servo_max_recovery_steps: int = 160
    guard_final_servo_recovery_mode: str = "lift_recenter"
    guard_final_servo_soft_unjam_lift: float = 0.006
    guard_final_servo_soft_unjam_min_height: float = 0.012
    guard_final_servo_soft_unjam_z_tolerance: float = 0.001
    guard_final_servo_soft_unjam_hold_steps: int = 4
    guard_final_servo_soft_unjam_max_up_action: float = 0.002
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
        if self.guard_retry_stall_steps <= 0:
            raise ValueError("guard_retry_stall_steps must be positive.")
        if self.guard_retry_xy_tolerance <= 0.0:
            raise ValueError("guard_retry_xy_tolerance must be positive.")
        if self.guard_retry_z_max <= 0.0:
            raise ValueError("guard_retry_z_max must be positive.")
        if self.guard_retry_lift_height <= 0.0:
            raise ValueError("guard_retry_lift_height must be positive.")
        if self.guard_retry_release_xy <= 0.0:
            raise ValueError("guard_retry_release_xy must be positive.")
        if self.guard_retry_release_xy > self.guard_retry_xy_tolerance:
            raise ValueError("guard_retry_release_xy must be <= guard_retry_xy_tolerance.")
        if self.guard_retry_max_attempts < 0:
            raise ValueError("guard_retry_max_attempts cannot be negative.")
        if self.guard_retry_max_steps <= 0:
            raise ValueError("guard_retry_max_steps must be positive.")
        if self.guard_insert_latch_xy_tolerance <= 0.0:
            raise ValueError("guard_insert_latch_xy_tolerance must be positive.")
        if self.guard_insert_latch_release_xy <= 0.0:
            raise ValueError("guard_insert_latch_release_xy must be positive.")
        if self.guard_insert_latch_release_xy < self.guard_insert_latch_xy_tolerance:
            raise ValueError(
                "guard_insert_latch_release_xy must be >= guard_insert_latch_xy_tolerance."
            )
        if self.guard_insert_latch_resume_xy <= 0.0:
            raise ValueError("guard_insert_latch_resume_xy must be positive.")
        if self.guard_insert_latch_resume_xy > self.guard_insert_latch_release_xy:
            raise ValueError(
                "guard_insert_latch_resume_xy must be <= guard_insert_latch_release_xy."
            )
        if self.guard_insert_latch_recenter_height < 0.0:
            raise ValueError("guard_insert_latch_recenter_height cannot be negative.")
        if self.guard_insert_latch_recenter_z_tolerance < 0.0:
            raise ValueError("guard_insert_latch_recenter_z_tolerance cannot be negative.")
        if self.guard_insert_latch_max_down_action < 0.0:
            raise ValueError("guard_insert_latch_max_down_action cannot be negative.")
        if self.guard_hover_xy_tolerance <= 0.0:
            raise ValueError("guard_hover_xy_tolerance must be positive.")
        if self.guard_hover_release_xy < self.guard_hover_xy_tolerance:
            raise ValueError("guard_hover_release_xy must be >= guard_hover_xy_tolerance.")
        if self.guard_hover_height <= 0.0:
            raise ValueError("guard_hover_height must be positive.")
        if self.guard_hover_z_tolerance <= 0.0:
            raise ValueError("guard_hover_z_tolerance must be positive.")
        if self.guard_hover_required_steps <= 0:
            raise ValueError("guard_hover_required_steps must be positive.")
        if self.guard_hover_max_down_action < 0.0:
            raise ValueError("guard_hover_max_down_action cannot be negative.")
        if self.guard_near_action_xy_tolerance <= 0.0:
            raise ValueError("guard_near_action_xy_tolerance must be positive.")
        if self.guard_near_action_z_threshold <= 0.0:
            raise ValueError("guard_near_action_z_threshold must be positive.")
        if self.guard_near_max_xy_action <= 0.0:
            raise ValueError("guard_near_max_xy_action must be positive.")
        if self.guard_near_max_down_action < 0.0:
            raise ValueError("guard_near_max_down_action cannot be negative.")
        if self.guard_fixture_clearance_xy_min < 0.0:
            raise ValueError("guard_fixture_clearance_xy_min cannot be negative.")
        if self.guard_fixture_clearance_xy_max <= self.guard_fixture_clearance_xy_min:
            raise ValueError(
                "guard_fixture_clearance_xy_max must be greater than "
                "guard_fixture_clearance_xy_min."
            )
        if self.guard_fixture_clearance_z_max <= 0.0:
            raise ValueError("guard_fixture_clearance_z_max must be positive.")
        if self.guard_fixture_clearance_lift_height <= self.guard_fixture_clearance_z_max:
            raise ValueError(
                "guard_fixture_clearance_lift_height must be greater than "
                "guard_fixture_clearance_z_max."
            )
        if self.guard_fixture_clearance_max_up_action <= 0.0:
            raise ValueError("guard_fixture_clearance_max_up_action must be positive.")
        if self.guard_fixture_clearance_realign_start_z < 0.0:
            raise ValueError("guard_fixture_clearance_realign_start_z cannot be negative.")
        if self.guard_fixture_clearance_realign_xy <= 0.0:
            raise ValueError("guard_fixture_clearance_realign_xy must be positive.")
        if self.guard_fixture_clearance_max_xy_action <= 0.0:
            raise ValueError("guard_fixture_clearance_max_xy_action must be positive.")
        if self.guard_fixture_clearance_max_down_action < 0.0:
            raise ValueError("guard_fixture_clearance_max_down_action cannot be negative.")
        if self.guard_fixture_clearance_max_steps <= 0:
            raise ValueError("guard_fixture_clearance_max_steps must be positive.")
        if self.guard_preinsert_recenter_start_z <= 0.0:
            raise ValueError("guard_preinsert_recenter_start_z must be positive.")
        if self.guard_preinsert_recenter_min_z < 0.0:
            raise ValueError("guard_preinsert_recenter_min_z cannot be negative.")
        if self.guard_preinsert_recenter_min_z > self.guard_preinsert_recenter_start_z:
            raise ValueError(
                "guard_preinsert_recenter_min_z must be <= guard_preinsert_recenter_start_z."
            )
        if self.guard_preinsert_recenter_trigger_xy <= 0.0:
            raise ValueError("guard_preinsert_recenter_trigger_xy must be positive.")
        if self.guard_preinsert_recenter_stable_xy <= 0.0:
            raise ValueError("guard_preinsert_recenter_stable_xy must be positive.")
        if self.guard_preinsert_recenter_stable_xy > self.guard_preinsert_recenter_trigger_xy:
            raise ValueError(
                "guard_preinsert_recenter_stable_xy must be <= "
                "guard_preinsert_recenter_trigger_xy."
            )
        if self.guard_preinsert_recenter_height <= 0.0:
            raise ValueError("guard_preinsert_recenter_height must be positive.")
        if self.guard_preinsert_recenter_z_tolerance <= 0.0:
            raise ValueError("guard_preinsert_recenter_z_tolerance must be positive.")
        if self.guard_preinsert_recenter_stable_steps <= 0:
            raise ValueError("guard_preinsert_recenter_stable_steps must be positive.")
        if self.guard_preinsert_recenter_max_steps <= 0:
            raise ValueError("guard_preinsert_recenter_max_steps must be positive.")
        if self.guard_preinsert_recenter_max_xy_action <= 0.0:
            raise ValueError("guard_preinsert_recenter_max_xy_action must be positive.")
        if self.guard_preinsert_recenter_max_up_action <= 0.0:
            raise ValueError("guard_preinsert_recenter_max_up_action must be positive.")
        if self.guard_approach_recenter_start_z <= 0.0:
            raise ValueError("guard_approach_recenter_start_z must be positive.")
        if self.guard_approach_recenter_min_z < 0.0:
            raise ValueError("guard_approach_recenter_min_z cannot be negative.")
        if self.guard_approach_recenter_min_z > self.guard_approach_recenter_start_z:
            raise ValueError(
                "guard_approach_recenter_min_z must be <= guard_approach_recenter_start_z."
            )
        if self.guard_approach_recenter_trigger_xy <= 0.0:
            raise ValueError("guard_approach_recenter_trigger_xy must be positive.")
        if self.guard_approach_recenter_max_xy <= self.guard_approach_recenter_trigger_xy:
            raise ValueError(
                "guard_approach_recenter_max_xy must be greater than "
                "guard_approach_recenter_trigger_xy."
            )
        if self.guard_approach_recenter_stable_xy <= 0.0:
            raise ValueError("guard_approach_recenter_stable_xy must be positive.")
        if self.guard_approach_recenter_stable_xy > self.guard_approach_recenter_trigger_xy:
            raise ValueError(
                "guard_approach_recenter_stable_xy must be <= "
                "guard_approach_recenter_trigger_xy."
            )
        if self.guard_approach_recenter_height <= 0.0:
            raise ValueError("guard_approach_recenter_height must be positive.")
        if self.guard_approach_recenter_z_tolerance <= 0.0:
            raise ValueError("guard_approach_recenter_z_tolerance must be positive.")
        if self.guard_approach_recenter_stable_steps <= 0:
            raise ValueError("guard_approach_recenter_stable_steps must be positive.")
        if self.guard_approach_recenter_max_steps <= 0:
            raise ValueError("guard_approach_recenter_max_steps must be positive.")
        if self.guard_approach_recenter_max_xy_action <= 0.0:
            raise ValueError("guard_approach_recenter_max_xy_action must be positive.")
        if self.guard_approach_recenter_max_up_action <= 0.0:
            raise ValueError("guard_approach_recenter_max_up_action must be positive.")
        if len(self.guard_approach_recenter_xy_bias) != 2:
            raise ValueError("guard_approach_recenter_xy_bias must contain two values.")
        if self.guard_stateful_recovery_trigger_xy_min < 0.0:
            raise ValueError("guard_stateful_recovery_trigger_xy_min cannot be negative.")
        if self.guard_stateful_recovery_trigger_xy_max <= self.guard_stateful_recovery_trigger_xy_min:
            raise ValueError(
                "guard_stateful_recovery_trigger_xy_max must be greater than "
                "guard_stateful_recovery_trigger_xy_min."
            )
        if self.guard_stateful_recovery_trigger_z_max <= 0.0:
            raise ValueError("guard_stateful_recovery_trigger_z_max must be positive.")
        if self.guard_stateful_recovery_lift_height <= 0.0:
            raise ValueError("guard_stateful_recovery_lift_height must be positive.")
        if self.guard_stateful_recovery_lift_z_tolerance <= 0.0:
            raise ValueError("guard_stateful_recovery_lift_z_tolerance must be positive.")
        if self.guard_stateful_recovery_release_xy <= 0.0:
            raise ValueError("guard_stateful_recovery_release_xy must be positive.")
        if self.guard_stateful_recovery_resume_xy < self.guard_stateful_recovery_release_xy:
            raise ValueError(
                "guard_stateful_recovery_resume_xy must be >= "
                "guard_stateful_recovery_release_xy."
            )
        if self.guard_stateful_recovery_resume_z <= 0.0:
            raise ValueError("guard_stateful_recovery_resume_z must be positive.")
        if self.guard_stateful_recovery_stable_steps <= 0:
            raise ValueError("guard_stateful_recovery_stable_steps must be positive.")
        if self.guard_stateful_recovery_stall_steps <= 0:
            raise ValueError("guard_stateful_recovery_stall_steps must be positive.")
        if self.guard_stateful_recovery_min_xy_progress < 0.0:
            raise ValueError("guard_stateful_recovery_min_xy_progress cannot be negative.")
        if self.guard_stateful_recovery_min_actual_xy_motion < 0.0:
            raise ValueError(
                "guard_stateful_recovery_min_actual_xy_motion cannot be negative."
            )
        if self.guard_stateful_recovery_min_command_xy < 0.0:
            raise ValueError("guard_stateful_recovery_min_command_xy cannot be negative.")
        if self.guard_stateful_recovery_max_attempts < 0:
            raise ValueError("guard_stateful_recovery_max_attempts cannot be negative.")
        if self.guard_stateful_recovery_max_steps <= 0:
            raise ValueError("guard_stateful_recovery_max_steps must be positive.")
        if self.guard_stateful_recovery_max_xy_action <= 0.0:
            raise ValueError("guard_stateful_recovery_max_xy_action must be positive.")
        if self.guard_stateful_recovery_max_down_action < 0.0:
            raise ValueError("guard_stateful_recovery_max_down_action cannot be negative.")
        if self.guard_stateful_recovery_max_up_action <= 0.0:
            raise ValueError("guard_stateful_recovery_max_up_action must be positive.")
        if self.guard_final_servo_start_xy <= 0.0:
            raise ValueError("guard_final_servo_start_xy must be positive.")
        if self.guard_final_servo_start_z <= 0.0:
            raise ValueError("guard_final_servo_start_z must be positive.")
        if self.guard_final_servo_min_start_z < 0.0:
            raise ValueError("guard_final_servo_min_start_z cannot be negative.")
        if self.guard_final_servo_min_start_z > self.guard_final_servo_start_z:
            raise ValueError(
                "guard_final_servo_min_start_z must be <= guard_final_servo_start_z."
            )
        if self.guard_final_servo_hover_height <= 0.0:
            raise ValueError("guard_final_servo_hover_height must be positive.")
        if self.guard_final_servo_hover_z_tolerance <= 0.0:
            raise ValueError("guard_final_servo_hover_z_tolerance must be positive.")
        if self.guard_final_servo_stable_xy <= 0.0:
            raise ValueError("guard_final_servo_stable_xy must be positive.")
        if self.guard_final_servo_descent_start_xy < 0.0:
            raise ValueError("guard_final_servo_descent_start_xy cannot be negative.")
        if (
            self.guard_final_servo_descent_start_xy > 0.0
            and self.guard_final_servo_descent_start_xy < self.guard_final_servo_stable_xy
        ):
            raise ValueError(
                "guard_final_servo_descent_start_xy must be >= guard_final_servo_stable_xy."
            )
        if self.guard_final_servo_stable_steps <= 0:
            raise ValueError("guard_final_servo_stable_steps must be positive.")
        if self.guard_final_servo_release_xy < self.guard_final_servo_stable_xy:
            raise ValueError(
                "guard_final_servo_release_xy must be >= guard_final_servo_stable_xy."
            )
        if self.guard_final_servo_max_xy_action <= 0.0:
            raise ValueError("guard_final_servo_max_xy_action must be positive.")
        if self.guard_final_servo_max_down_action < 0.0:
            raise ValueError("guard_final_servo_max_down_action cannot be negative.")
        if self.guard_final_servo_low_recenter_z_max <= 0.0:
            raise ValueError("guard_final_servo_low_recenter_z_max must be positive.")
        if self.guard_final_servo_low_recenter_trigger_xy <= 0.0:
            raise ValueError(
                "guard_final_servo_low_recenter_trigger_xy must be positive."
            )
        if self.guard_final_servo_low_recenter_release_xy <= 0.0:
            raise ValueError(
                "guard_final_servo_low_recenter_release_xy must be positive."
            )
        if (
            self.guard_final_servo_low_recenter_trigger_xy
            < self.guard_final_servo_low_recenter_release_xy
        ):
            raise ValueError(
                "guard_final_servo_low_recenter_trigger_xy must be >= "
                "guard_final_servo_low_recenter_release_xy."
            )
        if self.guard_final_servo_low_recenter_trigger_xy > self.guard_final_servo_release_xy:
            raise ValueError(
                "guard_final_servo_low_recenter_trigger_xy must be <= "
                "guard_final_servo_release_xy."
            )
        if self.guard_final_servo_low_recenter_release_xy > self.guard_final_servo_release_xy:
            raise ValueError(
                "guard_final_servo_low_recenter_release_xy must be <= "
                "guard_final_servo_release_xy."
            )
        if self.guard_final_servo_low_recenter_height <= 0.0:
            raise ValueError("guard_final_servo_low_recenter_height must be positive.")
        if self.guard_final_servo_low_recenter_stable_steps <= 0:
            raise ValueError(
                "guard_final_servo_low_recenter_stable_steps must be positive."
            )
        if self.guard_final_servo_low_recenter_max_steps <= 0:
            raise ValueError("guard_final_servo_low_recenter_max_steps must be positive.")
        if self.guard_final_servo_low_recenter_max_up_action <= 0.0:
            raise ValueError(
                "guard_final_servo_low_recenter_max_up_action must be positive."
            )
        if self.guard_final_servo_low_recenter_stall_steps < 0:
            raise ValueError(
                "guard_final_servo_low_recenter_stall_steps cannot be negative."
            )
        if self.guard_final_servo_low_recenter_min_xy_progress < 0.0:
            raise ValueError(
                "guard_final_servo_low_recenter_min_xy_progress cannot be negative."
            )
        if len(self.guard_final_servo_descend_xy_bias) != 2:
            raise ValueError("guard_final_servo_descend_xy_bias must contain two values.")
        if self.guard_final_servo_descend_xy_bias_max_clearance < 0.0:
            raise ValueError(
                "guard_final_servo_descend_xy_bias_max_clearance cannot be negative."
            )
        if self.guard_final_servo_lift_height <= self.guard_final_servo_hover_height:
            raise ValueError(
                "guard_final_servo_lift_height must be greater than "
                "guard_final_servo_hover_height."
            )
        if self.guard_final_servo_stall_steps <= 0:
            raise ValueError("guard_final_servo_stall_steps must be positive.")
        if self.guard_final_servo_min_z_progress <= 0.0:
            raise ValueError("guard_final_servo_min_z_progress must be positive.")
        if self.guard_final_servo_max_retries < 0:
            raise ValueError("guard_final_servo_max_retries cannot be negative.")
        if self.guard_final_servo_max_recovery_steps <= 0:
            raise ValueError("guard_final_servo_max_recovery_steps must be positive.")
        if self.guard_final_servo_recovery_mode not in ("lift_recenter", "soft_unjam"):
            raise ValueError(
                "guard_final_servo_recovery_mode must be lift_recenter or soft_unjam."
            )
        if self.guard_final_servo_soft_unjam_lift <= 0.0:
            raise ValueError("guard_final_servo_soft_unjam_lift must be positive.")
        if self.guard_final_servo_soft_unjam_min_height < 0.0:
            raise ValueError("guard_final_servo_soft_unjam_min_height cannot be negative.")
        if self.guard_final_servo_soft_unjam_z_tolerance <= 0.0:
            raise ValueError("guard_final_servo_soft_unjam_z_tolerance must be positive.")
        if self.guard_final_servo_soft_unjam_hold_steps < 0:
            raise ValueError("guard_final_servo_soft_unjam_hold_steps cannot be negative.")
        if self.guard_final_servo_soft_unjam_max_up_action <= 0.0:
            raise ValueError("guard_final_servo_soft_unjam_max_up_action must be positive.")
        if self.oracle.mode not in (
            "guarded_two_stage",
            "high_start_two_phase",
            "contact_aware_recovery",
            "timeout_descent_progress",
        ):
            raise ValueError(
                "GuardedPolicyConfig.oracle must use guarded_two_stage, "
                "high_start_two_phase, contact_aware_recovery, or "
                "timeout_descent_progress mode."
            )
        if self.guard_retry_xy_tolerance <= self.oracle.guarded_insert_xy_tolerance:
            raise ValueError(
                "guard_retry_xy_tolerance must be greater than guarded_insert_xy_tolerance."
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
    guard_retry_active: bool = False
    guard_retry_triggered: bool = False
    guard_retry_count: int = 0
    guard_retry_stall_steps: int = 0
    guard_retry_active_steps: int = 0
    guard_insert_latched: bool = False
    guard_insert_latch_activated: bool = False
    guard_insert_latch_released: bool = False
    guard_insert_latch_steps: int = 0
    guard_insert_latch_descent_allowed: bool = False
    guard_hover_active: bool = False
    guard_hover_stable_steps: int = 0
    guard_hover_descent_allowed: bool = False
    guard_hover_descent_latched: bool = False
    guard_hover_down_blocked: bool = False
    guard_near_action_limited: bool = False
    guard_fixture_clearance_active: bool = False
    guard_fixture_clearance_triggered: bool = False
    guard_fixture_clearance_released: bool = False
    guard_fixture_clearance_phase: str = "none"
    guard_fixture_clearance_steps: int = 0
    guard_fixture_clearance_realign_steps: int = 0
    guard_preinsert_recenter_active: bool = False
    guard_preinsert_recenter_triggered: bool = False
    guard_preinsert_recenter_released: bool = False
    guard_preinsert_recenter_steps: int = 0
    guard_preinsert_recenter_stable_steps: int = 0
    guard_preinsert_recenter_down_blocked: bool = False
    guard_approach_recenter_active: bool = False
    guard_approach_recenter_triggered: bool = False
    guard_approach_recenter_released: bool = False
    guard_approach_recenter_steps: int = 0
    guard_approach_recenter_stable_steps: int = 0
    guard_approach_recenter_down_blocked: bool = False
    guard_stateful_recovery_active: bool = False
    guard_stateful_recovery_triggered: bool = False
    guard_stateful_recovery_released: bool = False
    guard_stateful_recovery_exhausted: bool = False
    guard_stateful_recovery_phase: str = "inactive"
    guard_stateful_recovery_phase_steps: int = 0
    guard_stateful_recovery_stall_steps: int = 0
    guard_stateful_recovery_stable_steps: int = 0
    guard_stateful_recovery_attempts: int = 0
    guard_stateful_recovery_down_blocked: bool = False
    guard_final_servo_active: bool = False
    guard_final_servo_triggered: bool = False
    guard_final_servo_recovery_triggered: bool = False
    guard_final_servo_exhausted: bool = False
    guard_final_servo_phase: str = "inactive"
    guard_final_servo_phase_steps: int = 0
    guard_final_servo_stable_steps: int = 0
    guard_final_servo_stall_steps: int = 0
    guard_final_servo_low_recenter_stall_steps: int = 0
    guard_final_servo_low_recenter_best_dist_xy: float = float("inf")
    guard_final_servo_retry_count: int = 0
    guard_final_servo_descent_allowed: bool = False
    guard_final_servo_down_blocked: bool = False


class GuardedPolicyController:
    def __init__(self, config: GuardedPolicyConfig) -> None:
        self.config = config
        self.guard_active = False
        self.guard_steps = 0
        self.steps_since_reset = 0
        self.guard_retry_active = False
        self.guard_retry_count = 0
        self.guard_retry_stall_steps = 0
        self.guard_retry_active_steps = 0
        self.guard_insert_latched = False
        self.guard_insert_latch_steps = 0
        self.guard_hover_stable_steps = 0
        self.guard_hover_descent_latched = False
        self.guard_fixture_clearance_active = False
        self.guard_fixture_clearance_phase = "none"
        self.guard_fixture_clearance_steps = 0
        self.guard_fixture_clearance_realign_steps = 0
        self.guard_preinsert_recenter_active = False
        self.guard_preinsert_recenter_steps = 0
        self.guard_preinsert_recenter_stable_steps = 0
        self.guard_approach_recenter_active = False
        self.guard_approach_recenter_steps = 0
        self.guard_approach_recenter_stable_steps = 0
        self.guard_stateful_recovery_phase = "inactive"
        self.guard_stateful_recovery_phase_steps = 0
        self.guard_stateful_recovery_stall_steps = 0
        self.guard_stateful_recovery_stable_steps = 0
        self.guard_stateful_recovery_attempts = 0
        self.guard_stateful_recovery_best_dist_xy = float("inf")
        self.guard_stateful_recovery_exhausted = False
        self.guard_final_servo_phase = "inactive"
        self.guard_final_servo_phase_steps = 0
        self.guard_final_servo_stable_steps = 0
        self.guard_final_servo_stall_steps = 0
        self.guard_final_servo_low_recenter_stall_steps = 0
        self.guard_final_servo_low_recenter_best_dist_xy = float("inf")
        self.guard_final_servo_retry_count = 0
        self.guard_final_servo_best_z_above = float("inf")
        self.guard_final_servo_recovery_start_z_above = 0.0
        self.guard_final_servo_recovery_target_z_above = 0.0
        self.guard_final_servo_exhausted = False

    def reset(self) -> None:
        self.guard_active = False
        self.guard_steps = 0
        self.steps_since_reset = 0
        self.guard_retry_active = False
        self.guard_retry_count = 0
        self.guard_retry_stall_steps = 0
        self.guard_retry_active_steps = 0
        self.guard_insert_latched = False
        self.guard_insert_latch_steps = 0
        self.guard_hover_stable_steps = 0
        self.guard_hover_descent_latched = False
        self.guard_fixture_clearance_active = False
        self.guard_fixture_clearance_phase = "none"
        self.guard_fixture_clearance_steps = 0
        self.guard_fixture_clearance_realign_steps = 0
        self.guard_preinsert_recenter_active = False
        self.guard_preinsert_recenter_steps = 0
        self.guard_preinsert_recenter_stable_steps = 0
        self.guard_approach_recenter_active = False
        self.guard_approach_recenter_steps = 0
        self.guard_approach_recenter_stable_steps = 0
        self.guard_stateful_recovery_phase = "inactive"
        self.guard_stateful_recovery_phase_steps = 0
        self.guard_stateful_recovery_stall_steps = 0
        self.guard_stateful_recovery_stable_steps = 0
        self.guard_stateful_recovery_attempts = 0
        self.guard_stateful_recovery_best_dist_xy = float("inf")
        self.guard_stateful_recovery_exhausted = False
        self.guard_final_servo_phase = "inactive"
        self.guard_final_servo_phase_steps = 0
        self.guard_final_servo_stable_steps = 0
        self.guard_final_servo_stall_steps = 0
        self.guard_final_servo_low_recenter_stall_steps = 0
        self.guard_final_servo_low_recenter_best_dist_xy = float("inf")
        self.guard_final_servo_retry_count = 0
        self.guard_final_servo_best_z_above = float("inf")
        self.guard_final_servo_recovery_start_z_above = 0.0
        self.guard_final_servo_recovery_target_z_above = 0.0
        self.guard_final_servo_exhausted = False

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
            self._reset_retry()
            self._reset_insert_latch()
            self._reset_hover()
            self._reset_fixture_clearance()
            self._reset_preinsert_recenter()
            self._reset_approach_recenter()
            self._reset_stateful_recovery()
            self._reset_final_servo()
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
                guard_retry_active=False,
                guard_retry_triggered=False,
                guard_retry_count=self.guard_retry_count,
                guard_retry_stall_steps=self.guard_retry_stall_steps,
                guard_retry_active_steps=self.guard_retry_active_steps,
                guard_insert_latched=False,
                guard_insert_latch_activated=False,
                guard_insert_latch_released=False,
                guard_insert_latch_steps=self.guard_insert_latch_steps,
                guard_insert_latch_descent_allowed=False,
                guard_hover_descent_latched=False,
            )
            self.steps_since_reset += 1
            return result

        fixture_active, fixture_triggered, fixture_released = (
            self._update_fixture_clearance_state(dist_xy, z_above_target)
        )
        if fixture_active:
            self._reset_retry()
            self._reset_insert_latch()
            self._reset_hover()
            self._reset_preinsert_recenter()
            self._reset_approach_recenter()
            self._reset_stateful_recovery()
            self._reset_final_servo()
            guarded_action = self._fixture_clearance_action_from_state(state)
            self.guard_fixture_clearance_steps += 1
            if self.guard_fixture_clearance_phase == "realign":
                self.guard_fixture_clearance_realign_steps += 1
            self.guard_steps += 1
            result = GuardedPolicyStep(
                action=guarded_action,
                guarded=True,
                guard_active=True,
                guard_enabled=True,
                guard_should_activate=should_activate,
                guard_can_activate=can_activate,
                guard_activated=False,
                guard_down_blocked=False,
                guard_steps_since_reset=step_index,
                guard_dist_xy=dist_xy,
                guard_z_above_target=z_above_target,
                policy_action=policy_action,
                guarded_action=guarded_action,
                guard_retry_count=self.guard_retry_count,
                guard_retry_stall_steps=self.guard_retry_stall_steps,
                guard_retry_active_steps=self.guard_retry_active_steps,
                guard_insert_latch_steps=self.guard_insert_latch_steps,
                guard_hover_descent_latched=self.guard_hover_descent_latched,
                guard_fixture_clearance_active=True,
                guard_fixture_clearance_triggered=fixture_triggered,
                guard_fixture_clearance_released=fixture_released,
                guard_fixture_clearance_phase=self.guard_fixture_clearance_phase,
                guard_fixture_clearance_steps=self.guard_fixture_clearance_steps,
                guard_fixture_clearance_realign_steps=self.guard_fixture_clearance_realign_steps,
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
                self._reset_retry()
                self._reset_insert_latch()
                self._reset_hover()
                self._reset_preinsert_recenter()
                self._reset_approach_recenter()
                self._reset_stateful_recovery()
                self._reset_final_servo()

        if not self.guard_active:
            self._reset_retry()
            self._reset_insert_latch()
            self._reset_hover()
            self._reset_preinsert_recenter()
            self._reset_approach_recenter()
            self._reset_stateful_recovery()
            self._reset_final_servo()
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
                guard_retry_active=False,
                guard_retry_triggered=False,
                guard_retry_count=self.guard_retry_count,
                guard_retry_stall_steps=self.guard_retry_stall_steps,
                guard_retry_active_steps=self.guard_retry_active_steps,
                guard_insert_latched=False,
                guard_insert_latch_activated=False,
                guard_insert_latch_released=False,
                guard_insert_latch_steps=self.guard_insert_latch_steps,
                guard_insert_latch_descent_allowed=False,
                guard_hover_descent_latched=False,
                guard_fixture_clearance_released=fixture_released,
                guard_fixture_clearance_steps=self.guard_fixture_clearance_steps,
                guard_fixture_clearance_realign_steps=self.guard_fixture_clearance_realign_steps,
            )
            self.steps_since_reset += 1
            return result

        recovery_active, recovery_triggered, recovery_released = (
            self._update_stateful_recovery_state(state, dist_xy, z_above_target)
        )
        if recovery_active:
            self._reset_retry()
            self._reset_insert_latch()
            self._reset_hover()
            self._reset_preinsert_recenter()
            self._reset_approach_recenter()
            self._reset_final_servo()
            guarded_action, recovery_down_blocked = (
                self._stateful_recovery_action_from_state(state)
            )
            self.guard_stateful_recovery_phase_steps += 1
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
                guard_down_blocked=down_blocked or recovery_down_blocked,
                guard_steps_since_reset=step_index,
                guard_dist_xy=dist_xy,
                guard_z_above_target=z_above_target,
                policy_action=policy_action,
                guarded_action=guarded_action,
                guard_retry_count=self.guard_retry_count,
                guard_retry_stall_steps=self.guard_retry_stall_steps,
                guard_retry_active_steps=self.guard_retry_active_steps,
                guard_insert_latch_steps=self.guard_insert_latch_steps,
                guard_hover_descent_latched=self.guard_hover_descent_latched,
                guard_fixture_clearance_released=fixture_released,
                guard_fixture_clearance_steps=self.guard_fixture_clearance_steps,
                guard_fixture_clearance_realign_steps=self.guard_fixture_clearance_realign_steps,
                guard_stateful_recovery_active=True,
                guard_stateful_recovery_triggered=recovery_triggered,
                guard_stateful_recovery_released=recovery_released,
                guard_stateful_recovery_exhausted=self.guard_stateful_recovery_exhausted,
                guard_stateful_recovery_phase=self.guard_stateful_recovery_phase,
                guard_stateful_recovery_phase_steps=(
                    self.guard_stateful_recovery_phase_steps
                ),
                guard_stateful_recovery_stall_steps=(
                    self.guard_stateful_recovery_stall_steps
                ),
                guard_stateful_recovery_stable_steps=(
                    self.guard_stateful_recovery_stable_steps
                ),
                guard_stateful_recovery_attempts=(
                    self.guard_stateful_recovery_attempts
                ),
                guard_stateful_recovery_down_blocked=recovery_down_blocked,
            )
            self.steps_since_reset += 1
            return result

        approach_active, approach_triggered, approach_released = (
            self._update_approach_recenter_state(dist_xy, z_above_target)
        )
        if approach_active:
            self._reset_retry()
            self._reset_insert_latch()
            self._reset_hover()
            self._reset_preinsert_recenter()
            self._reset_final_servo()
            guarded_action = self._approach_recenter_action_from_state(state)
            self.guard_approach_recenter_steps += 1
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
                guard_retry_count=self.guard_retry_count,
                guard_retry_stall_steps=self.guard_retry_stall_steps,
                guard_retry_active_steps=self.guard_retry_active_steps,
                guard_insert_latch_steps=self.guard_insert_latch_steps,
                guard_hover_descent_latched=self.guard_hover_descent_latched,
                guard_fixture_clearance_released=fixture_released,
                guard_fixture_clearance_steps=self.guard_fixture_clearance_steps,
                guard_fixture_clearance_realign_steps=self.guard_fixture_clearance_realign_steps,
                guard_approach_recenter_active=True,
                guard_approach_recenter_triggered=approach_triggered,
                guard_approach_recenter_released=approach_released,
                guard_approach_recenter_steps=self.guard_approach_recenter_steps,
                guard_approach_recenter_stable_steps=(
                    self.guard_approach_recenter_stable_steps
                ),
                guard_approach_recenter_down_blocked=down_blocked,
                guard_stateful_recovery_released=recovery_released,
                guard_stateful_recovery_exhausted=self.guard_stateful_recovery_exhausted,
                guard_stateful_recovery_phase=self.guard_stateful_recovery_phase,
                guard_stateful_recovery_stall_steps=(
                    self.guard_stateful_recovery_stall_steps
                ),
                guard_stateful_recovery_attempts=(
                    self.guard_stateful_recovery_attempts
                ),
            )
            self.steps_since_reset += 1
            return result

        preinsert_active, preinsert_triggered, preinsert_released = (
            self._update_preinsert_recenter_state(dist_xy, z_above_target)
        )
        if preinsert_active:
            self._reset_retry()
            self._reset_insert_latch()
            self._reset_hover()
            self._reset_final_servo()
            guarded_action = self._preinsert_recenter_action_from_state(state)
            self.guard_preinsert_recenter_steps += 1
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
                guard_retry_count=self.guard_retry_count,
                guard_retry_stall_steps=self.guard_retry_stall_steps,
                guard_retry_active_steps=self.guard_retry_active_steps,
                guard_insert_latch_steps=self.guard_insert_latch_steps,
                guard_hover_descent_latched=self.guard_hover_descent_latched,
                guard_fixture_clearance_released=fixture_released,
                guard_fixture_clearance_steps=self.guard_fixture_clearance_steps,
                guard_fixture_clearance_realign_steps=self.guard_fixture_clearance_realign_steps,
                guard_preinsert_recenter_active=True,
                guard_preinsert_recenter_triggered=preinsert_triggered,
                guard_preinsert_recenter_released=preinsert_released,
                guard_preinsert_recenter_steps=self.guard_preinsert_recenter_steps,
                guard_preinsert_recenter_stable_steps=(
                    self.guard_preinsert_recenter_stable_steps
                ),
                guard_preinsert_recenter_down_blocked=True,
                guard_approach_recenter_released=approach_released,
                guard_approach_recenter_steps=self.guard_approach_recenter_steps,
                guard_approach_recenter_stable_steps=(
                    self.guard_approach_recenter_stable_steps
                ),
                guard_stateful_recovery_released=recovery_released,
                guard_stateful_recovery_exhausted=self.guard_stateful_recovery_exhausted,
                guard_stateful_recovery_phase=self.guard_stateful_recovery_phase,
                guard_stateful_recovery_stall_steps=(
                    self.guard_stateful_recovery_stall_steps
                ),
                guard_stateful_recovery_attempts=(
                    self.guard_stateful_recovery_attempts
                ),
            )
            self.steps_since_reset += 1
            return result

        final_active, final_triggered, final_recovery_triggered = (
            self._update_final_servo_state(dist_xy, z_above_target)
        )
        if final_active:
            self._reset_retry()
            self._reset_insert_latch()
            self._reset_hover()
            guarded_action, final_descent_allowed, final_down_blocked = (
                self._final_servo_action_from_state(state, dist_xy)
            )
            self.guard_final_servo_phase_steps += 1
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
                guard_down_blocked=down_blocked or final_down_blocked,
                guard_steps_since_reset=step_index,
                guard_dist_xy=dist_xy,
                guard_z_above_target=z_above_target,
                policy_action=policy_action,
                guarded_action=guarded_action,
                guard_retry_count=self.guard_retry_count,
                guard_retry_stall_steps=self.guard_retry_stall_steps,
                guard_retry_active_steps=self.guard_retry_active_steps,
                guard_insert_latch_steps=self.guard_insert_latch_steps,
                guard_hover_descent_latched=self.guard_hover_descent_latched,
                guard_fixture_clearance_released=fixture_released,
                guard_fixture_clearance_steps=self.guard_fixture_clearance_steps,
                guard_fixture_clearance_realign_steps=self.guard_fixture_clearance_realign_steps,
                guard_preinsert_recenter_released=preinsert_released,
                guard_preinsert_recenter_steps=self.guard_preinsert_recenter_steps,
                guard_preinsert_recenter_stable_steps=(
                    self.guard_preinsert_recenter_stable_steps
                ),
                guard_approach_recenter_released=approach_released,
                guard_approach_recenter_steps=self.guard_approach_recenter_steps,
                guard_approach_recenter_stable_steps=(
                    self.guard_approach_recenter_stable_steps
                ),
                guard_stateful_recovery_released=recovery_released,
                guard_stateful_recovery_exhausted=self.guard_stateful_recovery_exhausted,
                guard_stateful_recovery_phase=self.guard_stateful_recovery_phase,
                guard_stateful_recovery_stall_steps=(
                    self.guard_stateful_recovery_stall_steps
                ),
                guard_stateful_recovery_attempts=(
                    self.guard_stateful_recovery_attempts
                ),
                guard_final_servo_active=True,
                guard_final_servo_triggered=final_triggered,
                guard_final_servo_recovery_triggered=final_recovery_triggered,
                guard_final_servo_exhausted=self.guard_final_servo_exhausted,
                guard_final_servo_phase=self.guard_final_servo_phase,
                guard_final_servo_phase_steps=self.guard_final_servo_phase_steps,
                guard_final_servo_stable_steps=self.guard_final_servo_stable_steps,
                guard_final_servo_stall_steps=self.guard_final_servo_stall_steps,
                guard_final_servo_low_recenter_stall_steps=(
                    self.guard_final_servo_low_recenter_stall_steps
                ),
                guard_final_servo_low_recenter_best_dist_xy=(
                    self.guard_final_servo_low_recenter_best_dist_xy
                ),
                guard_final_servo_retry_count=self.guard_final_servo_retry_count,
                guard_final_servo_descent_allowed=final_descent_allowed,
                guard_final_servo_down_blocked=final_down_blocked,
            )
            self.steps_since_reset += 1
            return result

        retry_triggered = self._update_retry_state(dist_xy, z_above_target)
        latch_active, latch_activated, latch_released = self._update_insert_latch(dist_xy)
        latch_descent_allowed = False
        hover_active = False
        hover_descent_allowed = False
        hover_down_blocked = False
        near_action_limited = False
        if self.guard_retry_active:
            self._reset_insert_latch()
            self._reset_hover()
            latch_active = False
            latch_activated = False
            latch_released = False
            guarded_action = self._retry_action_from_state(state)
        elif latch_active:
            self._reset_hover()
            guarded_action, latch_descent_allowed = self._latched_insert_action_from_state(state)
        else:
            hover_active, hover_descent_allowed = self._update_hover_state(
                dist_xy,
                z_above_target,
            )
            if hover_active and not hover_descent_allowed:
                guarded_action = self._hover_align_action_from_state(state)
                hover_down_blocked = True
            elif hover_active and hover_descent_allowed:
                guarded_action, hover_down_blocked = self._hover_descent_action_from_state(
                    state,
                    dist_xy,
                )
            else:
                guarded_action = oracle_action_from_state(
                    peg_tip_pos=_as_vector3(state.peg_tip_pos, "peg_tip_pos"),
                    target_pos=_as_vector3(state.target_pos, "target_pos"),
                    applied_action=_as_vector3(state.applied_action, "applied_action"),
                    approach_height=float(state.approach_height),
                    action_low=_as_vector3(state.action_low, "action_low"),
                    action_high=_as_vector3(state.action_high, "action_high"),
                    config=self.config.oracle,
                )
            guarded_action, near_action_limited = self._limit_near_action(
                guarded_action,
                dist_xy,
                z_above_target,
            )
        if self.guard_insert_latched:
            self.guard_insert_latch_steps += 1
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
            guard_retry_active=self.guard_retry_active,
            guard_retry_triggered=retry_triggered,
            guard_retry_count=self.guard_retry_count,
            guard_retry_stall_steps=self.guard_retry_stall_steps,
            guard_retry_active_steps=self.guard_retry_active_steps,
            guard_insert_latched=self.guard_insert_latched,
            guard_insert_latch_activated=latch_activated,
            guard_insert_latch_released=latch_released,
            guard_insert_latch_steps=self.guard_insert_latch_steps,
            guard_insert_latch_descent_allowed=latch_descent_allowed,
            guard_hover_active=hover_active,
            guard_hover_stable_steps=self.guard_hover_stable_steps,
            guard_hover_descent_allowed=hover_descent_allowed,
            guard_hover_descent_latched=self.guard_hover_descent_latched,
            guard_hover_down_blocked=hover_down_blocked,
            guard_near_action_limited=near_action_limited,
            guard_fixture_clearance_released=fixture_released,
            guard_fixture_clearance_steps=self.guard_fixture_clearance_steps,
            guard_fixture_clearance_realign_steps=self.guard_fixture_clearance_realign_steps,
            guard_preinsert_recenter_released=preinsert_released,
            guard_preinsert_recenter_steps=self.guard_preinsert_recenter_steps,
            guard_preinsert_recenter_stable_steps=self.guard_preinsert_recenter_stable_steps,
            guard_approach_recenter_released=approach_released,
            guard_approach_recenter_steps=self.guard_approach_recenter_steps,
            guard_approach_recenter_stable_steps=self.guard_approach_recenter_stable_steps,
            guard_stateful_recovery_released=recovery_released,
            guard_stateful_recovery_exhausted=self.guard_stateful_recovery_exhausted,
            guard_stateful_recovery_phase=self.guard_stateful_recovery_phase,
            guard_stateful_recovery_stall_steps=self.guard_stateful_recovery_stall_steps,
            guard_stateful_recovery_attempts=self.guard_stateful_recovery_attempts,
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

    def _reset_hover(self) -> None:
        self.guard_hover_stable_steps = 0
        self.guard_hover_descent_latched = False

    def _reset_fixture_clearance(self) -> None:
        self.guard_fixture_clearance_active = False
        self.guard_fixture_clearance_phase = "none"
        self.guard_fixture_clearance_steps = 0
        self.guard_fixture_clearance_realign_steps = 0

    def _reset_preinsert_recenter(self) -> None:
        self.guard_preinsert_recenter_active = False
        self.guard_preinsert_recenter_steps = 0
        self.guard_preinsert_recenter_stable_steps = 0

    def _reset_approach_recenter(self) -> None:
        self.guard_approach_recenter_active = False
        self.guard_approach_recenter_steps = 0
        self.guard_approach_recenter_stable_steps = 0

    def _reset_stateful_recovery(self, *, keep_attempts: bool = False) -> None:
        self.guard_stateful_recovery_phase = "inactive"
        self.guard_stateful_recovery_phase_steps = 0
        self.guard_stateful_recovery_stall_steps = 0
        self.guard_stateful_recovery_stable_steps = 0
        self.guard_stateful_recovery_best_dist_xy = float("inf")
        if not keep_attempts:
            self.guard_stateful_recovery_attempts = 0
            self.guard_stateful_recovery_exhausted = False

    def _reset_final_servo(self, *, keep_exhausted: bool = False) -> None:
        self.guard_final_servo_phase = "inactive"
        self.guard_final_servo_phase_steps = 0
        self.guard_final_servo_stable_steps = 0
        self.guard_final_servo_stall_steps = 0
        self.guard_final_servo_low_recenter_stall_steps = 0
        self.guard_final_servo_low_recenter_best_dist_xy = float("inf")
        self.guard_final_servo_best_z_above = float("inf")
        self.guard_final_servo_recovery_start_z_above = 0.0
        self.guard_final_servo_recovery_target_z_above = 0.0
        if not keep_exhausted:
            self.guard_final_servo_retry_count = 0
            self.guard_final_servo_exhausted = False

    def _reset_retry(self) -> None:
        self.guard_retry_active = False
        self.guard_retry_stall_steps = 0
        self.guard_retry_active_steps = 0

    def _reset_insert_latch(self) -> None:
        self.guard_insert_latched = False
        self.guard_insert_latch_steps = 0

    def _set_final_servo_phase(self, phase: str) -> None:
        self.guard_final_servo_phase = phase
        self.guard_final_servo_phase_steps = 0
        if phase != "low_recenter":
            self.guard_final_servo_low_recenter_stall_steps = 0
            self.guard_final_servo_low_recenter_best_dist_xy = float("inf")

    def _set_stateful_recovery_phase(self, phase: str) -> None:
        self.guard_stateful_recovery_phase = phase
        self.guard_stateful_recovery_phase_steps = 0

    def _update_stateful_recovery_state(
        self,
        state: GuardedDeploymentState,
        dist_xy: float,
        z_above_target: float,
    ) -> tuple[bool, bool, bool]:
        if not self.config.guard_stateful_recovery_enabled:
            self._reset_stateful_recovery()
            return False, False, False

        if self.guard_stateful_recovery_phase != "inactive":
            timed_out = (
                self.guard_stateful_recovery_phase_steps
                >= self.config.guard_stateful_recovery_max_steps
            )
            if timed_out:
                self.guard_stateful_recovery_exhausted = True
                self._reset_stateful_recovery(keep_attempts=True)
                return False, False, True

            if self.guard_stateful_recovery_phase == "lift":
                lifted_enough = z_above_target >= (
                    self.config.guard_stateful_recovery_lift_height
                    - self.config.guard_stateful_recovery_lift_z_tolerance
                )
                if lifted_enough:
                    self._set_stateful_recovery_phase("recenter")

            elif self.guard_stateful_recovery_phase == "recenter":
                if dist_xy <= self.config.guard_stateful_recovery_release_xy:
                    self.guard_stateful_recovery_stable_steps = 1
                    self._set_stateful_recovery_phase("settle")

            elif self.guard_stateful_recovery_phase == "settle":
                if dist_xy <= self.config.guard_stateful_recovery_release_xy:
                    self.guard_stateful_recovery_stable_steps += 1
                    if (
                        self.guard_stateful_recovery_stable_steps
                        >= self.config.guard_stateful_recovery_stable_steps
                    ):
                        self._set_stateful_recovery_phase("resume")
                elif dist_xy > self.config.guard_stateful_recovery_resume_xy:
                    self.guard_stateful_recovery_stable_steps = 0
                    self._set_stateful_recovery_phase("recenter")

            elif self.guard_stateful_recovery_phase == "resume":
                if dist_xy > self.config.guard_stateful_recovery_resume_xy:
                    self.guard_stateful_recovery_stable_steps = 0
                    lifted_enough = z_above_target >= (
                        self.config.guard_stateful_recovery_lift_height
                        - self.config.guard_stateful_recovery_lift_z_tolerance
                    )
                    self._set_stateful_recovery_phase("recenter" if lifted_enough else "lift")
                    return True, False, False
                if (
                    z_above_target <= self.config.guard_stateful_recovery_resume_z
                    and dist_xy <= self.config.guard_stateful_recovery_release_xy
                ):
                    self._reset_stateful_recovery(keep_attempts=True)
                    return False, False, True

            else:
                raise ValueError(
                    f"Unknown stateful recovery phase: {self.guard_stateful_recovery_phase}"
                )
            return True, False, False

        if self.guard_stateful_recovery_exhausted:
            outside_window = (
                dist_xy > self.config.guard_stateful_recovery_trigger_xy_max
                or z_above_target > self.config.guard_stateful_recovery_trigger_z_max
            )
            if outside_window:
                self._reset_stateful_recovery()
            else:
                return False, False, False

        in_trigger_window = (
            self.config.guard_stateful_recovery_trigger_xy_min
            <= dist_xy
            <= self.config.guard_stateful_recovery_trigger_xy_max
            and z_above_target <= self.config.guard_stateful_recovery_trigger_z_max
        )
        if not in_trigger_window:
            self.guard_stateful_recovery_stall_steps = 0
            self.guard_stateful_recovery_best_dist_xy = float("inf")
            return False, False, False

        if self.guard_stateful_recovery_attempts >= self.config.guard_stateful_recovery_max_attempts:
            return False, False, False

        applied_action = _as_vector3(state.applied_action, "applied_action")
        actual_tip_delta = _as_vector3(state.actual_tip_delta, "actual_tip_delta")
        commanded_xy = float(np.linalg.norm(applied_action[:2]))
        actual_xy = float(np.linalg.norm(actual_tip_delta[:2]))
        command_is_meaningful = commanded_xy >= self.config.guard_stateful_recovery_min_command_xy
        actual_motion_is_small = actual_xy <= self.config.guard_stateful_recovery_min_actual_xy_motion
        improved = dist_xy < (
            self.guard_stateful_recovery_best_dist_xy
            - self.config.guard_stateful_recovery_min_xy_progress
        )
        if improved:
            self.guard_stateful_recovery_best_dist_xy = dist_xy
            self.guard_stateful_recovery_stall_steps = 0
            return False, False, False
        self.guard_stateful_recovery_best_dist_xy = min(
            self.guard_stateful_recovery_best_dist_xy,
            dist_xy,
        )

        if command_is_meaningful and actual_motion_is_small:
            self.guard_stateful_recovery_stall_steps += 1
        else:
            self.guard_stateful_recovery_stall_steps = max(
                0,
                self.guard_stateful_recovery_stall_steps - 1,
            )

        if self.guard_stateful_recovery_stall_steps < self.config.guard_stateful_recovery_stall_steps:
            return False, False, False

        self.guard_stateful_recovery_attempts += 1
        self.guard_stateful_recovery_stall_steps = 0
        self.guard_stateful_recovery_stable_steps = 0
        self.guard_stateful_recovery_best_dist_xy = dist_xy
        lift_ready = z_above_target >= (
            self.config.guard_stateful_recovery_lift_height
            - self.config.guard_stateful_recovery_lift_z_tolerance
        )
        self._set_stateful_recovery_phase("recenter" if lift_ready else "lift")
        return True, True, False

    def _stateful_recovery_action_from_state(
        self,
        state: GuardedDeploymentState,
    ) -> tuple[np.ndarray, bool]:
        tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
        target = _as_vector3(state.target_pos, "target_pos")
        applied_action = _as_vector3(state.applied_action, "applied_action")
        control_tip = tip + float(self.config.oracle.guarded_prediction_steps) * applied_action
        lift_z = float(target[2] + self.config.guard_stateful_recovery_lift_height)
        phase = self.guard_stateful_recovery_phase
        if phase == "lift":
            desired = np.asarray([target[0], target[1], lift_z], dtype=np.float64)
            max_xy_action = self.config.guard_stateful_recovery_max_xy_action
            max_down_action = 0.0
        elif phase in ("recenter", "settle"):
            desired = np.asarray(
                [
                    target[0],
                    target[1],
                    max(float(control_tip[2]), lift_z),
                ],
                dtype=np.float64,
            )
            max_xy_action = self.config.guard_stateful_recovery_max_xy_action
            max_down_action = 0.0
        elif phase == "resume":
            dist_xy = (
                float(state.dist_xy)
                if state.dist_xy is not None
                else float(np.linalg.norm(tip[:2] - target[:2]))
            )
            desired = np.asarray(
                [
                    target[0],
                    target[1],
                    target[2] + self.config.guard_stateful_recovery_resume_z,
                ],
                dtype=np.float64,
            )
            max_xy_action = self.config.guard_stateful_recovery_max_xy_action
            max_down_action = (
                self.config.guard_stateful_recovery_max_down_action
                if dist_xy <= self.config.guard_stateful_recovery_resume_xy
                else 0.0
            )
        else:
            desired = control_tip
            max_xy_action = 0.0
            max_down_action = 0.0

        action = self.config.oracle.action_gain * (desired - control_tip)
        action = self._limit_xy_action(action, max_xy_action)
        action = self._limit_z_action(
            action,
            max_down_action=max_down_action,
            max_up_action=self.config.guard_stateful_recovery_max_up_action,
        )
        return np.clip(action, state.action_low, state.action_high).astype(np.float32), True

    def _update_approach_recenter_state(
        self,
        dist_xy: float,
        z_above_target: float,
    ) -> tuple[bool, bool, bool]:
        if not self.config.guard_approach_recenter_enabled:
            self._reset_approach_recenter()
            return False, False, False

        if self.guard_final_servo_phase != "inactive":
            self._reset_approach_recenter()
            return False, False, False

        if (
            self.config.guard_approach_recenter_requires_stateful_recovery
            and not self.guard_stateful_recovery_exhausted
        ):
            self._reset_approach_recenter()
            return False, False, False

        if self.guard_approach_recenter_active:
            height_ready = abs(
                z_above_target - self.config.guard_approach_recenter_height
            ) <= self.config.guard_approach_recenter_z_tolerance
            xy_ready = dist_xy <= self.config.guard_approach_recenter_stable_xy
            if height_ready and xy_ready:
                self.guard_approach_recenter_stable_steps += 1
            else:
                self.guard_approach_recenter_stable_steps = 0

            stable = (
                self.guard_approach_recenter_stable_steps
                >= self.config.guard_approach_recenter_stable_steps
            )
            timed_out = (
                self.guard_approach_recenter_steps
                >= self.config.guard_approach_recenter_max_steps
            )
            left_window = (
                dist_xy > self.config.guard_approach_recenter_max_xy
                or z_above_target > self.config.guard_approach_recenter_start_z
                or z_above_target < self.config.guard_approach_recenter_min_z
            )
            if stable or timed_out or left_window:
                self._reset_approach_recenter()
                return False, False, True
            return True, False, False

        in_approach_zone = (
            z_above_target <= self.config.guard_approach_recenter_start_z
            and z_above_target >= self.config.guard_approach_recenter_min_z
            and dist_xy > self.config.guard_approach_recenter_trigger_xy
            and dist_xy <= self.config.guard_approach_recenter_max_xy
        )
        if not in_approach_zone:
            return False, False, False

        self.guard_approach_recenter_active = True
        self.guard_approach_recenter_steps = 0
        self.guard_approach_recenter_stable_steps = 0
        return True, True, False

    def _approach_recenter_action_from_state(self, state: GuardedDeploymentState) -> np.ndarray:
        tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
        target = _as_vector3(state.target_pos, "target_pos")
        applied_action = _as_vector3(state.applied_action, "applied_action")
        control_tip = tip + float(self.config.oracle.guarded_prediction_steps) * applied_action
        bias = np.asarray(self.config.guard_approach_recenter_xy_bias, dtype=np.float64)
        recenter_z = float(target[2] + self.config.guard_approach_recenter_height)
        desired_z = max(float(control_tip[2]), recenter_z)
        desired = np.asarray(
            [
                target[0] + bias[0],
                target[1] + bias[1],
                desired_z,
            ],
            dtype=np.float64,
        )
        action = self.config.oracle.action_gain * (desired - control_tip)
        action = self._limit_xy_action(
            action,
            self.config.guard_approach_recenter_max_xy_action,
        )
        action = self._limit_z_action(
            action,
            max_down_action=0.0,
            max_up_action=self.config.guard_approach_recenter_max_up_action,
        )
        return np.clip(action, state.action_low, state.action_high).astype(np.float32)

    def _update_preinsert_recenter_state(
        self,
        dist_xy: float,
        z_above_target: float,
    ) -> tuple[bool, bool, bool]:
        if not self.config.guard_preinsert_recenter_enabled:
            self._reset_preinsert_recenter()
            return False, False, False

        if self.guard_preinsert_recenter_active:
            height_ready = z_above_target >= (
                self.config.guard_preinsert_recenter_height
                - self.config.guard_preinsert_recenter_z_tolerance
            )
            xy_ready = dist_xy <= self.config.guard_preinsert_recenter_stable_xy
            if height_ready and xy_ready:
                self.guard_preinsert_recenter_stable_steps += 1
            else:
                self.guard_preinsert_recenter_stable_steps = 0

            stable = (
                self.guard_preinsert_recenter_stable_steps
                >= self.config.guard_preinsert_recenter_stable_steps
            )
            timed_out = (
                self.guard_preinsert_recenter_steps
                >= self.config.guard_preinsert_recenter_max_steps
            )
            if stable or timed_out:
                self._reset_preinsert_recenter()
                return False, False, True
            return True, False, False

        in_preinsert_zone = (
            z_above_target <= self.config.guard_preinsert_recenter_start_z
            and z_above_target >= self.config.guard_preinsert_recenter_min_z
            and dist_xy > self.config.guard_preinsert_recenter_trigger_xy
        )
        if not in_preinsert_zone:
            return False, False, False

        self.guard_preinsert_recenter_active = True
        self.guard_preinsert_recenter_steps = 0
        self.guard_preinsert_recenter_stable_steps = 0
        return True, True, False

    def _preinsert_recenter_action_from_state(self, state: GuardedDeploymentState) -> np.ndarray:
        tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
        target = _as_vector3(state.target_pos, "target_pos")
        applied_action = _as_vector3(state.applied_action, "applied_action")
        control_tip = tip + float(self.config.oracle.guarded_prediction_steps) * applied_action
        recenter_z = float(target[2] + self.config.guard_preinsert_recenter_height)
        height_ready = control_tip[2] >= (
            recenter_z - self.config.guard_preinsert_recenter_z_tolerance
        )
        desired_xy = (
            control_tip[:2]
            if self.config.guard_preinsert_recenter_lift_before_lateral
            and not height_ready
            else target[:2]
        )
        desired_z = max(
            float(control_tip[2]),
            recenter_z,
        )
        desired = np.asarray([desired_xy[0], desired_xy[1], desired_z], dtype=np.float64)
        action = self.config.oracle.action_gain * (desired - control_tip)
        action = self._limit_xy_action(
            action,
            self.config.guard_preinsert_recenter_max_xy_action,
        )
        action = self._limit_z_action(
            action,
            max_down_action=0.0,
            max_up_action=self.config.guard_preinsert_recenter_max_up_action,
        )
        return np.clip(action, state.action_low, state.action_high).astype(np.float32)

    def _final_servo_in_hover_band(self, dist_xy: float, z_above_target: float) -> bool:
        descent_start_xy = self._final_servo_descent_start_xy()
        return (
            dist_xy <= descent_start_xy
            and abs(z_above_target - self.config.guard_final_servo_hover_height)
            <= self.config.guard_final_servo_hover_z_tolerance
        )

    def _final_servo_descent_start_xy(self) -> float:
        if self.config.guard_final_servo_descent_start_xy > 0.0:
            return max(
                self.config.guard_final_servo_stable_xy,
                self.config.guard_final_servo_descent_start_xy,
            )
        return self.config.guard_final_servo_stable_xy

    def _start_final_servo_recovery(self, z_above_target: float) -> bool:
        if self.guard_final_servo_retry_count >= self.config.guard_final_servo_max_retries:
            self.guard_final_servo_exhausted = True
            self._reset_final_servo(keep_exhausted=True)
            return True
        self.guard_final_servo_retry_count += 1
        self.guard_final_servo_stable_steps = 0
        self.guard_final_servo_stall_steps = 0
        self.guard_final_servo_best_z_above = float("inf")
        self.guard_final_servo_recovery_start_z_above = z_above_target
        soft_target_z = max(
            z_above_target + self.config.guard_final_servo_soft_unjam_lift,
            self.config.guard_final_servo_soft_unjam_min_height,
        )
        self.guard_final_servo_recovery_target_z_above = min(
            soft_target_z,
            self.config.guard_final_servo_lift_height,
        )
        if self.config.guard_final_servo_recovery_mode == "soft_unjam":
            self._set_final_servo_phase("recover_soft_unjam")
        else:
            self._set_final_servo_phase("recover_lift")
        return True

    def _update_final_servo_state(
        self,
        dist_xy: float,
        z_above_target: float,
    ) -> tuple[bool, bool, bool]:
        if not self.config.guard_final_servo_enabled:
            self._reset_final_servo()
            return False, False, False

        if self.guard_final_servo_exhausted:
            outside_start = (
                dist_xy > self.config.guard_final_servo_start_xy
                or z_above_target > self.config.guard_final_servo_start_z
            )
            if outside_start:
                self._reset_final_servo()
            else:
                return False, False, False

        triggered = False
        recovery_triggered = False
        if self.guard_final_servo_phase == "inactive":
            if (
                dist_xy <= self.config.guard_final_servo_start_xy
                and z_above_target >= self.config.guard_final_servo_min_start_z
                and z_above_target <= self.config.guard_final_servo_start_z
            ):
                self.guard_final_servo_retry_count = 0
                self.guard_final_servo_stable_steps = 0
                self.guard_final_servo_stall_steps = 0
                self.guard_final_servo_best_z_above = z_above_target
                self._set_final_servo_phase("align_hover")
                triggered = True
            else:
                return False, False, False

        if self.guard_final_servo_phase == "align_hover":
            if self._final_servo_in_hover_band(dist_xy, z_above_target):
                self.guard_final_servo_stable_steps = 1
                self._set_final_servo_phase("stable_confirm")
            else:
                self.guard_final_servo_stable_steps = 0

        elif self.guard_final_servo_phase == "stable_confirm":
            if self._final_servo_in_hover_band(dist_xy, z_above_target):
                self.guard_final_servo_stable_steps += 1
                if (
                    self.guard_final_servo_stable_steps
                    >= self.config.guard_final_servo_stable_steps
                ):
                    self.guard_final_servo_best_z_above = z_above_target
                    self.guard_final_servo_stall_steps = 0
                    self._set_final_servo_phase("descend")
            else:
                self.guard_final_servo_stable_steps = 0
                self._set_final_servo_phase("align_hover")

        elif self.guard_final_servo_phase == "descend":
            if dist_xy > self.config.guard_final_servo_release_xy:
                recovery_triggered = self._start_final_servo_recovery(z_above_target)
            elif (
                self.config.guard_final_servo_low_recenter_enabled
                and z_above_target <= self.config.guard_final_servo_low_recenter_z_max
                and dist_xy > self.config.guard_final_servo_low_recenter_trigger_xy
            ):
                self.guard_final_servo_stable_steps = 0
                self.guard_final_servo_stall_steps = 0
                self.guard_final_servo_low_recenter_stall_steps = 0
                self.guard_final_servo_low_recenter_best_dist_xy = dist_xy
                self._set_final_servo_phase("low_recenter")
            elif z_above_target < (
                self.guard_final_servo_best_z_above
                - self.config.guard_final_servo_min_z_progress
            ):
                self.guard_final_servo_best_z_above = z_above_target
                self.guard_final_servo_stall_steps = 0
            else:
                self.guard_final_servo_stall_steps += 1
                if (
                    self.guard_final_servo_stall_steps
                    >= self.config.guard_final_servo_stall_steps
                    and (
                        z_above_target > 0.010
                        or dist_xy > self.config.guard_final_servo_stable_xy
                    )
                ):
                    recovery_triggered = self._start_final_servo_recovery(z_above_target)

        elif self.guard_final_servo_phase == "low_recenter":
            if dist_xy <= self.config.guard_final_servo_low_recenter_release_xy:
                self.guard_final_servo_stable_steps += 1
                if (
                    self.guard_final_servo_stable_steps
                    >= self.config.guard_final_servo_low_recenter_stable_steps
                ):
                    self.guard_final_servo_best_z_above = z_above_target
                    self.guard_final_servo_stall_steps = 0
                    self._set_final_servo_phase("descend")
            else:
                self.guard_final_servo_stable_steps = 0
                improved = dist_xy < (
                    self.guard_final_servo_low_recenter_best_dist_xy
                    - self.config.guard_final_servo_low_recenter_min_xy_progress
                )
                if improved:
                    self.guard_final_servo_low_recenter_best_dist_xy = dist_xy
                    self.guard_final_servo_low_recenter_stall_steps = 0
                else:
                    self.guard_final_servo_low_recenter_best_dist_xy = min(
                        self.guard_final_servo_low_recenter_best_dist_xy,
                        dist_xy,
                    )
                    if self.config.guard_final_servo_low_recenter_stall_steps > 0:
                        self.guard_final_servo_low_recenter_stall_steps += 1
                timed_out = (
                    self.guard_final_servo_phase_steps
                    >= self.config.guard_final_servo_low_recenter_max_steps
                )
                stalled = (
                    self.config.guard_final_servo_low_recenter_stall_steps > 0
                    and self.guard_final_servo_low_recenter_stall_steps
                    >= self.config.guard_final_servo_low_recenter_stall_steps
                )
                if timed_out or stalled:
                    recovery_triggered = self._start_final_servo_recovery(z_above_target)

        elif self.guard_final_servo_phase == "recover_lift":
            lifted_enough = z_above_target >= (
                self.config.guard_final_servo_lift_height
                - 2.0 * self.config.oracle.guarded_max_up_action
            )
            timed_out = (
                self.guard_final_servo_phase_steps
                >= self.config.guard_final_servo_max_recovery_steps
            )
            if lifted_enough:
                self._set_final_servo_phase("recover_recenter")
            elif timed_out:
                self.guard_final_servo_exhausted = True
                self._reset_final_servo(keep_exhausted=True)
                recovery_triggered = True

        elif self.guard_final_servo_phase == "recover_soft_unjam":
            target_z = self.guard_final_servo_recovery_target_z_above
            lifted_enough = z_above_target >= (
                target_z - self.config.guard_final_servo_soft_unjam_z_tolerance
            )
            held_long_enough = (
                self.guard_final_servo_phase_steps
                >= self.config.guard_final_servo_soft_unjam_hold_steps
            )
            timed_out = (
                self.guard_final_servo_phase_steps
                >= self.config.guard_final_servo_max_recovery_steps
            )
            if lifted_enough and held_long_enough:
                self._set_final_servo_phase("recover_soft_recenter")
            elif timed_out:
                self.guard_final_servo_exhausted = True
                self._reset_final_servo(keep_exhausted=True)
                recovery_triggered = True

        elif self.guard_final_servo_phase == "recover_soft_recenter":
            if dist_xy <= self.config.guard_final_servo_stable_xy:
                self.guard_final_servo_best_z_above = z_above_target
                self.guard_final_servo_stall_steps = 0
                self.guard_final_servo_stable_steps = 0
                self._set_final_servo_phase("descend")
            elif (
                self.guard_final_servo_phase_steps
                >= self.config.guard_final_servo_max_recovery_steps
            ):
                self.guard_final_servo_exhausted = True
                self._reset_final_servo(keep_exhausted=True)
                recovery_triggered = True

        elif self.guard_final_servo_phase == "recover_recenter":
            if dist_xy <= self.config.guard_final_servo_stable_xy:
                self.guard_final_servo_stable_steps = 0
                self._set_final_servo_phase("align_hover")
            elif (
                self.guard_final_servo_phase_steps
                >= self.config.guard_final_servo_max_recovery_steps
            ):
                self.guard_final_servo_exhausted = True
                self._reset_final_servo(keep_exhausted=True)
                recovery_triggered = True

        else:
            raise ValueError(f"Unknown final servo phase: {self.guard_final_servo_phase}")

        return self.guard_final_servo_phase != "inactive", triggered, recovery_triggered

    def _final_servo_action_from_state(
        self,
        state: GuardedDeploymentState,
        dist_xy: float,
    ) -> tuple[np.ndarray, bool, bool]:
        tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
        target = _as_vector3(state.target_pos, "target_pos")
        applied_action = _as_vector3(state.applied_action, "applied_action")
        control_tip = tip + float(self.config.oracle.guarded_prediction_steps) * applied_action
        descend_xy_bias = self._effective_final_servo_descend_xy_bias(state)
        phase = self.guard_final_servo_phase
        descent_allowed = phase == "descend" and dist_xy <= self.config.guard_final_servo_release_xy
        down_blocked = False
        max_up_action = self.config.oracle.guarded_max_up_action

        if phase in ("align_hover", "stable_confirm"):
            xy_ready = dist_xy <= self._final_servo_descent_start_xy()
            hover_z = float(target[2] + self.config.guard_final_servo_hover_height)
            align_z = float(target[2] + self.config.guard_final_servo_start_z)
            desired_z = hover_z if xy_ready else max(float(control_tip[2]), align_z)
            desired = np.asarray(
                [
                    target[0],
                    target[1],
                    desired_z,
                ],
                dtype=np.float64,
            )
            max_xy_action = self.config.guard_final_servo_max_xy_action
            max_down_action = self.config.guard_final_servo_max_down_action if xy_ready else 0.0
            down_blocked = not xy_ready
        elif phase == "descend":
            desired = np.asarray(
                [
                    target[0] + descend_xy_bias[0],
                    target[1] + descend_xy_bias[1],
                    target[2],
                ],
                dtype=np.float64,
            )
            max_xy_action = self.config.guard_final_servo_max_xy_action
            max_down_action = (
                self.config.guard_final_servo_max_down_action if descent_allowed else 0.0
            )
            down_blocked = not descent_allowed
        elif phase == "low_recenter":
            desired = np.asarray(
                [
                    target[0] + descend_xy_bias[0],
                    target[1] + descend_xy_bias[1],
                    target[2] + self.config.guard_final_servo_low_recenter_height,
                ],
                dtype=np.float64,
            )
            max_xy_action = self.config.guard_final_servo_max_xy_action
            max_down_action = 0.0
            max_up_action = self.config.guard_final_servo_low_recenter_max_up_action
            down_blocked = True
        elif phase == "recover_lift":
            desired = np.asarray(
                [
                    control_tip[0],
                    control_tip[1],
                    target[2] + self.config.guard_final_servo_lift_height,
                ],
                dtype=np.float64,
            )
            max_xy_action = 0.0
            max_down_action = 0.0
            down_blocked = True
        elif phase == "recover_soft_unjam":
            desired = np.asarray(
                [
                    control_tip[0],
                    control_tip[1],
                    target[2] + self.guard_final_servo_recovery_target_z_above,
                ],
                dtype=np.float64,
            )
            max_xy_action = 0.0
            max_down_action = 0.0
            max_up_action = self.config.guard_final_servo_soft_unjam_max_up_action
            down_blocked = True
        elif phase == "recover_soft_recenter":
            desired = np.asarray(
                [
                    target[0],
                    target[1],
                    target[2] + self.guard_final_servo_recovery_target_z_above,
                ],
                dtype=np.float64,
            )
            max_xy_action = self.config.guard_final_servo_max_xy_action
            max_down_action = 0.0
            max_up_action = self.config.guard_final_servo_soft_unjam_max_up_action
            down_blocked = True
        elif phase == "recover_recenter":
            desired = np.asarray(
                [
                    target[0],
                    target[1],
                    target[2] + self.config.guard_final_servo_lift_height,
                ],
                dtype=np.float64,
            )
            max_xy_action = self.config.guard_final_servo_max_xy_action
            max_down_action = 0.0
            down_blocked = True
        else:
            desired = control_tip
            max_xy_action = 0.0
            max_down_action = 0.0
            down_blocked = True

        action = self.config.oracle.action_gain * (desired - control_tip)
        action = self._limit_xy_action(action, max_xy_action)
        action = self._limit_z_action(
            action,
            max_down_action=max_down_action,
            max_up_action=max_up_action,
        )
        return (
            np.clip(action, state.action_low, state.action_high).astype(np.float32),
            descent_allowed,
            down_blocked,
        )

    def _effective_final_servo_descend_xy_bias(
        self,
        state: GuardedDeploymentState,
    ) -> np.ndarray:
        bias = np.asarray(
            self.config.guard_final_servo_descend_xy_bias,
            dtype=np.float64,
        )
        max_clearance = self.config.guard_final_servo_descend_xy_bias_max_clearance
        if bias.shape != (2,):
            raise ValueError("guard_final_servo_descend_xy_bias must contain two values.")
        if not np.any(bias):
            return bias
        if np.isfinite(max_clearance):
            clearance = state.hole_clearance
            if clearance is None or not np.isfinite(clearance) or clearance > max_clearance:
                return np.zeros(2, dtype=np.float64)
        if (
            self.config.guard_final_servo_descend_xy_bias_requires_stateful_recovery
            and self.guard_stateful_recovery_attempts <= 0
        ):
            return np.zeros(2, dtype=np.float64)
        return bias

    def _update_insert_latch(self, dist_xy: float) -> tuple[bool, bool, bool]:
        if not self.config.guard_insert_latch_enabled:
            self._reset_insert_latch()
            return False, False, False

        if self.guard_insert_latched:
            if dist_xy > self.config.guard_insert_latch_release_xy:
                self.guard_insert_latched = False
                self.guard_insert_latch_steps = 0
                return False, False, True
            return True, False, False

        if dist_xy <= self.config.guard_insert_latch_xy_tolerance:
            self.guard_insert_latched = True
            self.guard_insert_latch_steps = 0
            return True, True, False
        return False, False, False

    def _update_hover_state(self, dist_xy: float, z_above_target: float) -> tuple[bool, bool]:
        if not self.config.guard_hover_enabled:
            self._reset_hover()
            return False, False

        active = (
            dist_xy <= self.config.oracle.guarded_align_xy_tolerance
            and z_above_target <= self.config.guard_start_z
        )
        if not active:
            self._reset_hover()
            return False, False

        if self.guard_hover_descent_latched:
            if dist_xy <= self.config.guard_hover_release_xy:
                return True, True
            self.guard_hover_descent_latched = False
            self.guard_hover_stable_steps = 0

        in_xy_band = dist_xy <= self.config.guard_hover_xy_tolerance
        in_z_band = (
            abs(z_above_target - self.config.guard_hover_height)
            <= self.config.guard_hover_z_tolerance
        )
        if in_xy_band and in_z_band:
            self.guard_hover_stable_steps += 1
        elif dist_xy > self.config.guard_hover_release_xy or not in_z_band:
            self.guard_hover_stable_steps = 0

        descent_allowed = self.guard_hover_stable_steps >= self.config.guard_hover_required_steps
        if descent_allowed:
            self.guard_hover_descent_latched = True
        return True, descent_allowed

    def _hover_align_action_from_state(self, state: GuardedDeploymentState) -> np.ndarray:
        tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
        target = _as_vector3(state.target_pos, "target_pos")
        applied_action = _as_vector3(state.applied_action, "applied_action")
        control_tip = tip + float(self.config.oracle.guarded_prediction_steps) * applied_action
        hover_z = float(target[2] + self.config.guard_hover_height)
        desired = np.asarray([target[0], target[1], hover_z], dtype=np.float64)
        action = self.config.oracle.action_gain * (desired - control_tip)
        action = self._limit_xy_action(action, self.config.oracle.guarded_max_xy_action)
        action = self._limit_z_action(
            action,
            max_down_action=self.config.guard_hover_max_down_action,
            max_up_action=self.config.oracle.guarded_max_up_action,
        )
        return np.clip(action, state.action_low, state.action_high).astype(np.float32)

    def _hover_descent_action_from_state(
        self,
        state: GuardedDeploymentState,
        dist_xy: float,
    ) -> tuple[np.ndarray, bool]:
        tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
        target = _as_vector3(state.target_pos, "target_pos")
        applied_action = _as_vector3(state.applied_action, "applied_action")
        control_tip = tip + float(self.config.oracle.guarded_prediction_steps) * applied_action
        xy_aligned = dist_xy <= self.config.guard_hover_xy_tolerance
        hover_z = float(target[2] + self.config.guard_hover_height)
        desired_z = float(target[2]) if xy_aligned else max(float(control_tip[2]), hover_z)
        desired_xy = target[:2]
        max_down_action = (
            self.config.guard_near_max_down_action
            if self.config.guard_near_action_scale_enabled
            else self.config.oracle.guarded_max_down_action
        )
        if not xy_aligned:
            max_down_action = 0.0
        desired = np.asarray([desired_xy[0], desired_xy[1], desired_z], dtype=np.float64)
        action = self.config.oracle.action_gain * (desired - control_tip)
        action = self._limit_xy_action(action, self.config.oracle.guarded_max_xy_action)
        action = self._limit_z_action(
            action,
            max_down_action=max_down_action,
            max_up_action=self.config.oracle.guarded_max_up_action,
        )
        return np.clip(action, state.action_low, state.action_high).astype(np.float32), not xy_aligned

    def _limit_near_action(
        self,
        action: np.ndarray,
        dist_xy: float,
        z_above_target: float,
    ) -> tuple[np.ndarray, bool]:
        if not self.config.guard_near_action_scale_enabled:
            return action, False
        if (
            dist_xy > self.config.guard_near_action_xy_tolerance
            or z_above_target > self.config.guard_near_action_z_threshold
        ):
            return action, False

        limited = self._limit_xy_action(action, self.config.guard_near_max_xy_action)
        limited = self._limit_z_action(
            limited,
            max_down_action=self.config.guard_near_max_down_action,
            max_up_action=self.config.oracle.guarded_max_up_action,
        )
        return limited.astype(np.float32), not np.allclose(action, limited)

    def _update_retry_state(self, dist_xy: float, z_above_target: float) -> bool:
        if not self.config.guard_retry_enabled:
            self._reset_retry()
            return False

        if self.guard_retry_active:
            self.guard_retry_active_steps += 1
            lift_release_z = max(
                0.0,
                self.config.guard_retry_lift_height
                - 2.0 * self.config.oracle.guarded_max_up_action,
            )
            lifted_enough = z_above_target >= lift_release_z
            aligned_enough = dist_xy <= self.config.guard_retry_release_xy
            timed_out = self.guard_retry_active_steps >= self.config.guard_retry_max_steps
            if (lifted_enough and aligned_enough) or timed_out:
                self.guard_retry_active = False
                self.guard_retry_stall_steps = 0
                self.guard_retry_active_steps = 0
            return False

        in_retry_band = (
            self.config.oracle.guarded_insert_xy_tolerance
            < dist_xy
            <= self.config.guard_retry_xy_tolerance
            and z_above_target <= self.config.guard_retry_z_max
        )
        if not in_retry_band:
            self.guard_retry_stall_steps = 0
            return False

        self.guard_retry_stall_steps += 1
        if self.guard_retry_count >= self.config.guard_retry_max_attempts:
            return False
        if self.guard_retry_stall_steps < self.config.guard_retry_stall_steps:
            return False

        self.guard_retry_active = True
        self.guard_retry_count += 1
        self.guard_retry_stall_steps = 0
        self.guard_retry_active_steps = 0
        return True

    def _retry_action_from_state(self, state: GuardedDeploymentState) -> np.ndarray:
        tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
        target = _as_vector3(state.target_pos, "target_pos")
        applied_action = _as_vector3(state.applied_action, "applied_action")
        control_tip = tip + float(self.config.oracle.guarded_prediction_steps) * applied_action
        desired = np.asarray(
            [
                target[0],
                target[1],
                max(control_tip[2], target[2] + self.config.guard_retry_lift_height),
            ],
            dtype=np.float64,
        )
        action = self.config.oracle.action_gain * (desired - control_tip)
        action = self._limit_xy_action(action, self.config.oracle.guarded_max_xy_action)
        action = self._limit_z_action(
            action,
            max_down_action=0.0,
            max_up_action=self.config.oracle.guarded_max_up_action,
        )
        return np.clip(action, state.action_low, state.action_high).astype(np.float32)

    def _update_fixture_clearance_state(
        self,
        dist_xy: float,
        z_above_target: float,
    ) -> tuple[bool, bool, bool]:
        if not self.config.guard_fixture_clearance_enabled:
            self._reset_fixture_clearance()
            return False, False, False

        if self.guard_fixture_clearance_active:
            aligned_enough = dist_xy <= self.config.guard_fixture_clearance_realign_xy
            timed_out = self.guard_fixture_clearance_steps >= self.config.guard_fixture_clearance_max_steps
            if aligned_enough or timed_out:
                self._reset_fixture_clearance()
                return False, False, True
            realign_start_z = (
                self.config.guard_fixture_clearance_realign_start_z
                if self.config.guard_fixture_clearance_realign_start_z > 0.0
                else self.config.guard_fixture_clearance_lift_height
            )
            lifted_enough = z_above_target >= realign_start_z
            if self.guard_fixture_clearance_phase == "lift" and lifted_enough:
                if self.config.guard_fixture_clearance_realign_enabled:
                    self.guard_fixture_clearance_phase = "realign"
                    return True, False, False
                self._reset_fixture_clearance()
                return False, False, True
            return True, False, False

        in_danger_band = (
            self.config.guard_fixture_clearance_xy_min
            <= dist_xy
            <= self.config.guard_fixture_clearance_xy_max
            and z_above_target <= self.config.guard_fixture_clearance_z_max
        )
        if not in_danger_band:
            return False, False, False

        self.guard_fixture_clearance_active = True
        self.guard_fixture_clearance_phase = "lift"
        self.guard_fixture_clearance_steps = 0
        self.guard_fixture_clearance_realign_steps = 0
        return True, True, False

    def _fixture_clearance_action_from_state(self, state: GuardedDeploymentState) -> np.ndarray:
        if self.guard_fixture_clearance_phase == "realign":
            tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
            target = _as_vector3(state.target_pos, "target_pos")
            applied_action = _as_vector3(state.applied_action, "applied_action")
            control_tip = tip + float(self.config.oracle.guarded_prediction_steps) * applied_action
            desired = np.asarray(
                [
                    target[0],
                    target[1],
                    target[2] + self.config.guard_fixture_clearance_lift_height,
                ],
                dtype=np.float64,
            )
            action = self.config.oracle.action_gain * (desired - control_tip)
            action = self._limit_xy_action(
                action,
                self.config.guard_fixture_clearance_max_xy_action,
            )
            action = self._limit_z_action(
                action,
                max_down_action=self.config.guard_fixture_clearance_max_down_action,
                max_up_action=self.config.guard_fixture_clearance_max_up_action,
            )
            return np.clip(action, state.action_low, state.action_high).astype(np.float32)

        action = np.zeros(3, dtype=np.float64)
        max_up_action = min(
            self.config.guard_fixture_clearance_max_up_action,
            max(0.0, float(state.action_high[2])),
        )
        action[2] = max_up_action
        return np.clip(action, state.action_low, state.action_high).astype(np.float32)

    def _latched_insert_action_from_state(
        self,
        state: GuardedDeploymentState,
    ) -> tuple[np.ndarray, bool]:
        tip = _as_vector3(state.peg_tip_pos, "peg_tip_pos")
        target = _as_vector3(state.target_pos, "target_pos")
        applied_action = _as_vector3(state.applied_action, "applied_action")
        control_tip = tip + float(self.config.oracle.guarded_prediction_steps) * applied_action
        dist_xy = (
            float(state.dist_xy)
            if state.dist_xy is not None
            else float(np.linalg.norm(tip[:2] - target[:2]))
        )
        descent_allowed = dist_xy <= self.config.guard_insert_latch_resume_xy
        if descent_allowed:
            desired_xy = target[:2]
            desired_z = float(target[2])
            max_down_action = (
                self.config.guard_insert_latch_max_down_action
                if self.config.guard_insert_latch_max_down_action > 0.0
                else self.config.oracle.guarded_max_down_action
            )
        else:
            desired_xy = target[:2]
            desired_z = float(control_tip[2])
            if self.config.guard_insert_latch_recenter_height > 0.0:
                lift_z = float(target[2] + self.config.guard_insert_latch_recenter_height)
                lift_ready = control_tip[2] >= (
                    lift_z - self.config.guard_insert_latch_recenter_z_tolerance
                )
                if not lift_ready:
                    desired_xy = control_tip[:2]
                    desired_z = lift_z
            max_down_action = 0.0
        desired = np.asarray([desired_xy[0], desired_xy[1], desired_z], dtype=np.float64)
        action = self.config.oracle.action_gain * (desired - control_tip)
        action = self._limit_xy_action(action, self.config.oracle.guarded_max_xy_action)
        action = self._limit_z_action(
            action,
            max_down_action=max_down_action,
            max_up_action=self.config.oracle.guarded_max_up_action,
        )
        return np.clip(action, state.action_low, state.action_high).astype(np.float32), descent_allowed

    @staticmethod
    def _limit_xy_action(action: np.ndarray, max_xy_action: float) -> np.ndarray:
        limited = action.copy()
        if max_xy_action <= 0.0:
            limited[:2] = 0.0
            return limited
        xy_norm = float(np.linalg.norm(limited[:2]))
        if xy_norm > max_xy_action:
            limited[:2] *= max_xy_action / xy_norm
        return limited

    @staticmethod
    def _limit_z_action(
        action: np.ndarray,
        *,
        max_down_action: float,
        max_up_action: float,
    ) -> np.ndarray:
        limited = action.copy()
        if limited[2] < 0.0:
            limited[2] = max(limited[2], -max(0.0, max_down_action))
        else:
            limited[2] = min(limited[2], max(0.0, max_up_action))
        return limited


def _as_vector3(value: Any, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64).reshape(-1)
    if array.size != 3:
        raise ValueError(f"{name} must contain exactly 3 values.")
    return array


def _hole_clearance_from_info(info: dict[str, Any]) -> float | None:
    if "hole_clearance" in info:
        clearance = float(info["hole_clearance"])
        return clearance if np.isfinite(clearance) else None
    if "hole_half_size" not in info or "peg_radius" not in info:
        return None
    clearance = float(info["hole_half_size"]) - float(info["peg_radius"])
    return clearance if np.isfinite(clearance) else None
