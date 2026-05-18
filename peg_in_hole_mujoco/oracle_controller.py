from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np


OracleMode = Literal[
    "staged",
    "guarded_two_stage",
    "high_start_two_phase",
    "contact_aware_recovery",
    "timeout_descent_progress",
]


@dataclass(frozen=True)
class OracleControllerConfig:
    mode: OracleMode = "staged"
    action_gain: float = 1.0
    guarded_align_xy_tolerance: float = 0.025
    guarded_insert_xy_tolerance: float = 0.005
    guarded_retract_xy_tolerance: float = 0.012
    guarded_preinsert_height: float = 0.0
    guarded_max_xy_action: float = 0.005
    guarded_max_down_action: float = 0.0035
    guarded_max_up_action: float = 0.005
    guarded_prediction_steps: float = 1.0
    guarded_hold_z_until_insert: bool = False
    guarded_lift_before_lateral: bool = False
    guarded_lift_before_lateral_xy_tolerance: float = 0.020
    guarded_lift_before_lateral_z_margin: float = 0.010
    contact_recovery_xy_tolerance: float = 0.005
    contact_recovery_z_max: float = 0.050
    contact_recovery_lift_height: float = 0.060
    contact_recovery_lift_z_tolerance: float = 0.010
    contact_recovery_max_down_action: float = 0.001
    timeout_progress_xy_tolerance: float = 0.010
    timeout_progress_z_max: float = 0.060
    timeout_progress_max_down_action: float = 0.0015


def oracle_action(env: Any, info: dict[str, Any], config: OracleControllerConfig) -> np.ndarray:
    """Return a Cartesian displacement action for the current peg-in-hole state."""

    if config.mode == "staged":
        desired = _staged_desired_position(info)
        action = config.action_gain * (desired - _tip_pos(info))
        return _clip_to_action_space(env, action)
    if config.mode == "guarded_two_stage":
        return guarded_two_stage_oracle_action(env, info, config)
    if config.mode == "high_start_two_phase":
        return high_start_two_phase_oracle_action(env, info, config)
    if config.mode == "contact_aware_recovery":
        return contact_aware_recovery_oracle_action(env, info, config)
    if config.mode == "timeout_descent_progress":
        return timeout_descent_progress_oracle_action(env, info, config)
    raise ValueError(f"Unknown oracle mode: {config.mode}")


def guarded_two_stage_oracle_action(
    env: Any,
    info: dict[str, Any],
    config: OracleControllerConfig,
) -> np.ndarray:
    return guarded_two_stage_oracle_action_from_state(
        peg_tip_pos=_tip_pos(info),
        target_pos=_target_pos(info),
        applied_action=np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64),
        approach_height=float(env.approach_height),
        action_low=np.asarray(env.action_space.low, dtype=np.float64),
        action_high=np.asarray(env.action_space.high, dtype=np.float64),
        config=config,
    )


def high_start_two_phase_oracle_action(
    env: Any,
    info: dict[str, Any],
    config: OracleControllerConfig,
) -> np.ndarray:
    return high_start_two_phase_oracle_action_from_state(
        peg_tip_pos=_tip_pos(info),
        target_pos=_target_pos(info),
        applied_action=np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64),
        approach_height=float(env.approach_height),
        action_low=np.asarray(env.action_space.low, dtype=np.float64),
        action_high=np.asarray(env.action_space.high, dtype=np.float64),
        config=config,
    )


def contact_aware_recovery_oracle_action(
    env: Any,
    info: dict[str, Any],
    config: OracleControllerConfig,
) -> np.ndarray:
    return contact_aware_recovery_oracle_action_from_state(
        peg_tip_pos=_tip_pos(info),
        target_pos=_target_pos(info),
        applied_action=np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64),
        approach_height=float(env.approach_height),
        action_low=np.asarray(env.action_space.low, dtype=np.float64),
        action_high=np.asarray(env.action_space.high, dtype=np.float64),
        config=config,
    )


def timeout_descent_progress_oracle_action(
    env: Any,
    info: dict[str, Any],
    config: OracleControllerConfig,
) -> np.ndarray:
    return timeout_descent_progress_oracle_action_from_state(
        peg_tip_pos=_tip_pos(info),
        target_pos=_target_pos(info),
        applied_action=np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64),
        approach_height=float(env.approach_height),
        action_low=np.asarray(env.action_space.low, dtype=np.float64),
        action_high=np.asarray(env.action_space.high, dtype=np.float64),
        config=config,
    )


def oracle_action_from_state(
    *,
    peg_tip_pos: np.ndarray,
    target_pos: np.ndarray,
    applied_action: np.ndarray,
    approach_height: float,
    action_low: np.ndarray,
    action_high: np.ndarray,
    config: OracleControllerConfig,
) -> np.ndarray:
    if config.mode == "guarded_two_stage":
        return guarded_two_stage_oracle_action_from_state(
            peg_tip_pos=peg_tip_pos,
            target_pos=target_pos,
            applied_action=applied_action,
            approach_height=approach_height,
            action_low=action_low,
            action_high=action_high,
            config=config,
        )
    if config.mode == "high_start_two_phase":
        return high_start_two_phase_oracle_action_from_state(
            peg_tip_pos=peg_tip_pos,
            target_pos=target_pos,
            applied_action=applied_action,
            approach_height=approach_height,
            action_low=action_low,
            action_high=action_high,
            config=config,
        )
    if config.mode == "contact_aware_recovery":
        return contact_aware_recovery_oracle_action_from_state(
            peg_tip_pos=peg_tip_pos,
            target_pos=target_pos,
            applied_action=applied_action,
            approach_height=approach_height,
            action_low=action_low,
            action_high=action_high,
            config=config,
        )
    if config.mode == "timeout_descent_progress":
        return timeout_descent_progress_oracle_action_from_state(
            peg_tip_pos=peg_tip_pos,
            target_pos=target_pos,
            applied_action=applied_action,
            approach_height=approach_height,
            action_low=action_low,
            action_high=action_high,
            config=config,
        )
    raise ValueError(f"Unsupported deployment oracle mode: {config.mode}")


def guarded_two_stage_oracle_action_from_state(
    *,
    peg_tip_pos: np.ndarray,
    target_pos: np.ndarray,
    applied_action: np.ndarray,
    approach_height: float,
    action_low: np.ndarray,
    action_high: np.ndarray,
    config: OracleControllerConfig,
) -> np.ndarray:
    tip = np.asarray(peg_tip_pos, dtype=np.float64).reshape(3)
    target = np.asarray(target_pos, dtype=np.float64).reshape(3)
    applied_action = np.asarray(applied_action, dtype=np.float64).reshape(3)
    control_tip = _predicted_tip_pos_from_action(
        tip,
        applied_action,
        config.guarded_prediction_steps,
    )
    dist_xy = float(np.linalg.norm(control_tip[:2] - target[:2]))

    safe_z = float(target[2] + approach_height)
    preinsert_z = float(target[2] + config.guarded_preinsert_height)
    lift_before_lateral = (
        config.guarded_lift_before_lateral
        and dist_xy > config.guarded_lift_before_lateral_xy_tolerance
        and float(control_tip[2]) < safe_z - config.guarded_lift_before_lateral_z_margin
    )
    desired_z = _guarded_desired_z(
        tip_z=float(control_tip[2]),
        target_z=float(target[2]),
        safe_z=safe_z,
        preinsert_z=preinsert_z,
        dist_xy=dist_xy,
        config=config,
    )
    desired_xy = control_tip[:2] if lift_before_lateral else target[:2]
    desired = np.asarray([desired_xy[0], desired_xy[1], desired_z], dtype=np.float64)
    action = config.action_gain * (desired - control_tip)
    action = _limit_xy_action(action, config.guarded_max_xy_action)
    action = _limit_z_action(
        action,
        max_down_action=config.guarded_max_down_action,
        max_up_action=config.guarded_max_up_action,
    )
    return _clip_to_bounds(action, action_low, action_high)


def high_start_two_phase_oracle_action_from_state(
    *,
    peg_tip_pos: np.ndarray,
    target_pos: np.ndarray,
    applied_action: np.ndarray,
    approach_height: float,
    action_low: np.ndarray,
    action_high: np.ndarray,
    config: OracleControllerConfig,
) -> np.ndarray:
    tip = np.asarray(peg_tip_pos, dtype=np.float64).reshape(3)
    target = np.asarray(target_pos, dtype=np.float64).reshape(3)
    applied_action = np.asarray(applied_action, dtype=np.float64).reshape(3)
    control_tip = _predicted_tip_pos_from_action(
        tip,
        applied_action,
        config.guarded_prediction_steps,
    )
    dist_xy = float(np.linalg.norm(control_tip[:2] - target[:2]))

    safe_z = float(target[2] + approach_height)
    preinsert_z = float(target[2] + config.guarded_preinsert_height)
    desired_z = _high_start_two_phase_desired_z(
        tip_z=float(control_tip[2]),
        target_z=float(target[2]),
        safe_z=safe_z,
        preinsert_z=preinsert_z,
        dist_xy=dist_xy,
        config=config,
    )
    desired = np.asarray([target[0], target[1], desired_z], dtype=np.float64)
    action = config.action_gain * (desired - control_tip)
    action = _limit_xy_action(action, config.guarded_max_xy_action)
    action = _limit_z_action(
        action,
        max_down_action=config.guarded_max_down_action,
        max_up_action=config.guarded_max_up_action,
    )
    return _clip_to_bounds(action, action_low, action_high)


def contact_aware_recovery_oracle_action_from_state(
    *,
    peg_tip_pos: np.ndarray,
    target_pos: np.ndarray,
    applied_action: np.ndarray,
    approach_height: float,
    action_low: np.ndarray,
    action_high: np.ndarray,
    config: OracleControllerConfig,
) -> np.ndarray:
    tip = np.asarray(peg_tip_pos, dtype=np.float64).reshape(3)
    target = np.asarray(target_pos, dtype=np.float64).reshape(3)
    applied_action = np.asarray(applied_action, dtype=np.float64).reshape(3)
    control_tip = _predicted_tip_pos_from_action(
        tip,
        applied_action,
        config.guarded_prediction_steps,
    )
    dist_xy = float(np.linalg.norm(control_tip[:2] - target[:2]))
    z_above_target = float(control_tip[2] - target[2])

    recovery_lift_z = float(target[2] + config.contact_recovery_lift_height)
    in_low_misaligned_contact = (
        dist_xy > config.contact_recovery_xy_tolerance
        and z_above_target <= config.contact_recovery_z_max
    )
    if in_low_misaligned_contact:
        desired_xy = control_tip[:2]
        desired = np.asarray([desired_xy[0], desired_xy[1], recovery_lift_z], dtype=np.float64)
        action = config.action_gain * (desired - control_tip)
        action = _limit_xy_action(action, config.guarded_max_xy_action)
        action = _limit_z_action(
            action,
            max_down_action=0.0,
            max_up_action=config.guarded_max_up_action,
        )
        return _clip_to_bounds(action, action_low, action_high)

    in_recovery_realign_band = (
        dist_xy > config.guarded_insert_xy_tolerance
        and z_above_target <= config.contact_recovery_lift_height
        + config.contact_recovery_lift_z_tolerance
    )
    if in_recovery_realign_band:
        desired = np.asarray([target[0], target[1], recovery_lift_z], dtype=np.float64)
        action = config.action_gain * (desired - control_tip)
        action = _limit_xy_action(action, config.guarded_max_xy_action)
        action = _limit_z_action(
            action,
            max_down_action=0.0,
            max_up_action=config.guarded_max_up_action,
        )
        return _clip_to_bounds(action, action_low, action_high)

    if dist_xy <= config.guarded_insert_xy_tolerance:
        desired = np.asarray([target[0], target[1], target[2]], dtype=np.float64)
        action = config.action_gain * (desired - control_tip)
        action = _limit_xy_action(action, config.guarded_max_xy_action)
        action = _limit_z_action(
            action,
            max_down_action=config.contact_recovery_max_down_action,
            max_up_action=config.guarded_max_up_action,
        )
        return _clip_to_bounds(action, action_low, action_high)

    return guarded_two_stage_oracle_action_from_state(
        peg_tip_pos=peg_tip_pos,
        target_pos=target_pos,
        applied_action=applied_action,
        approach_height=approach_height,
        action_low=action_low,
        action_high=action_high,
        config=config,
    )


def timeout_descent_progress_oracle_action_from_state(
    *,
    peg_tip_pos: np.ndarray,
    target_pos: np.ndarray,
    applied_action: np.ndarray,
    approach_height: float,
    action_low: np.ndarray,
    action_high: np.ndarray,
    config: OracleControllerConfig,
) -> np.ndarray:
    tip = np.asarray(peg_tip_pos, dtype=np.float64).reshape(3)
    target = np.asarray(target_pos, dtype=np.float64).reshape(3)
    applied_action = np.asarray(applied_action, dtype=np.float64).reshape(3)
    control_tip = _predicted_tip_pos_from_action(
        tip,
        applied_action,
        config.guarded_prediction_steps,
    )
    dist_xy = float(np.linalg.norm(control_tip[:2] - target[:2]))
    z_above_target = float(control_tip[2] - target[2])

    in_progress_band = (
        dist_xy <= config.timeout_progress_xy_tolerance
        and z_above_target <= config.timeout_progress_z_max
    )
    if in_progress_band:
        desired = np.asarray([target[0], target[1], target[2]], dtype=np.float64)
        action = config.action_gain * (desired - control_tip)
        action = _limit_xy_action(action, config.guarded_max_xy_action)
        action = _limit_z_action(
            action,
            max_down_action=config.timeout_progress_max_down_action,
            max_up_action=config.guarded_max_up_action,
        )
        return _clip_to_bounds(action, action_low, action_high)

    return guarded_two_stage_oracle_action_from_state(
        peg_tip_pos=peg_tip_pos,
        target_pos=target_pos,
        applied_action=applied_action,
        approach_height=approach_height,
        action_low=action_low,
        action_high=action_high,
        config=config,
    )


def _guarded_desired_z(
    *,
    tip_z: float,
    target_z: float,
    safe_z: float,
    preinsert_z: float,
    dist_xy: float,
    config: OracleControllerConfig,
) -> float:
    align_tol = config.guarded_align_xy_tolerance
    insert_tol = config.guarded_insert_xy_tolerance
    if insert_tol >= align_tol:
        raise ValueError("guarded_insert_xy_tolerance must be smaller than guarded_align_xy_tolerance.")

    if dist_xy > align_tol:
        return safe_z

    if config.guarded_hold_z_until_insert and dist_xy > insert_tol:
        return safe_z

    if dist_xy > insert_tol:
        progress = (align_tol - dist_xy) / (align_tol - insert_tol)
        return float(safe_z + progress * (preinsert_z - safe_z))

    if dist_xy > config.guarded_retract_xy_tolerance and tip_z < preinsert_z:
        return preinsert_z

    return target_z


def _high_start_two_phase_desired_z(
    *,
    tip_z: float,
    target_z: float,
    safe_z: float,
    preinsert_z: float,
    dist_xy: float,
    config: OracleControllerConfig,
) -> float:
    if dist_xy > config.guarded_align_xy_tolerance:
        return max(float(tip_z), float(safe_z))

    return _guarded_desired_z(
        tip_z=tip_z,
        target_z=target_z,
        safe_z=safe_z,
        preinsert_z=preinsert_z,
        dist_xy=dist_xy,
        config=config,
    )


def _staged_desired_position(info: dict[str, Any]) -> np.ndarray:
    target = _target_pos(info)
    return np.asarray([target[0], target[1], info["desired_z"]], dtype=np.float64)


def _tip_pos(info: dict[str, Any]) -> np.ndarray:
    return np.asarray(info["peg_tip_pos"], dtype=np.float64)


def _target_pos(info: dict[str, Any]) -> np.ndarray:
    return np.asarray(info["target_pos"], dtype=np.float64)


def _predicted_tip_pos(
    tip: np.ndarray,
    info: dict[str, Any],
    prediction_steps: float,
) -> np.ndarray:
    applied_action = np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64)
    return _predicted_tip_pos_from_action(tip, applied_action, prediction_steps)


def _predicted_tip_pos_from_action(
    tip: np.ndarray,
    applied_action: np.ndarray,
    prediction_steps: float,
) -> np.ndarray:
    if prediction_steps <= 0.0:
        return tip
    return tip + float(prediction_steps) * applied_action


def _limit_xy_action(action: np.ndarray, max_xy_action: float) -> np.ndarray:
    limited = action.copy()
    if max_xy_action <= 0.0:
        limited[:2] = 0.0
        return limited

    xy_norm = float(np.linalg.norm(limited[:2]))
    if xy_norm > max_xy_action:
        limited[:2] *= max_xy_action / xy_norm
    return limited


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


def _clip_to_action_space(env: Any, action: np.ndarray) -> np.ndarray:
    return _clip_to_bounds(action, env.action_space.low, env.action_space.high)


def _clip_to_bounds(
    action: np.ndarray,
    action_low: np.ndarray,
    action_high: np.ndarray,
) -> np.ndarray:
    return np.clip(action, action_low, action_high).astype(np.float32)
