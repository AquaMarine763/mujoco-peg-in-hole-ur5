from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np


OracleMode = Literal["staged", "guarded_two_stage"]


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


def oracle_action(env: Any, info: dict[str, Any], config: OracleControllerConfig) -> np.ndarray:
    """Return a Cartesian displacement action for the current peg-in-hole state."""

    if config.mode == "staged":
        desired = _staged_desired_position(info)
        action = config.action_gain * (desired - _tip_pos(info))
        return _clip_to_action_space(env, action)
    if config.mode == "guarded_two_stage":
        return guarded_two_stage_oracle_action(env, info, config)
    raise ValueError(f"Unknown oracle mode: {config.mode}")


def guarded_two_stage_oracle_action(
    env: Any,
    info: dict[str, Any],
    config: OracleControllerConfig,
) -> np.ndarray:
    tip = _tip_pos(info)
    control_tip = _predicted_tip_pos(tip, info, config.guarded_prediction_steps)
    target = _target_pos(info)
    dist_xy = float(np.linalg.norm(control_tip[:2] - target[:2]))

    safe_z = float(target[2] + env.approach_height)
    preinsert_z = float(target[2] + config.guarded_preinsert_height)
    desired_z = _guarded_desired_z(
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
    return _clip_to_action_space(env, action)


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

    if dist_xy > insert_tol:
        progress = (align_tol - dist_xy) / (align_tol - insert_tol)
        return float(safe_z + progress * (preinsert_z - safe_z))

    if dist_xy > config.guarded_retract_xy_tolerance and tip_z < preinsert_z:
        return preinsert_z

    return target_z


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
    if prediction_steps <= 0.0:
        return tip
    applied_action = np.asarray(info.get("applied_action", np.zeros(3)), dtype=np.float64)
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
    return np.clip(action, env.action_space.low, env.action_space.high).astype(np.float32)
