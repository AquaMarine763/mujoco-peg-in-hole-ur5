from __future__ import annotations

import numpy as np


CONTROL_STATE_DIM = 10


def stack_sequence_array(
    values: np.ndarray,
    *,
    frame_stack: int,
    episode_ids: np.ndarray | None = None,
    step_ids: np.ndarray | None = None,
) -> np.ndarray:
    """Stack current and recent same-episode samples along the last axis."""

    if frame_stack <= 0:
        raise ValueError("frame_stack must be positive.")
    if frame_stack == 1:
        return np.ascontiguousarray(values)
    if values.ndim < 2:
        raise ValueError(f"Expected values with sample and feature axes, got {values.shape}")

    sample_count = int(values.shape[0])
    if episode_ids is None:
        episode_ids = np.zeros(sample_count, dtype=np.int64)
    if step_ids is None:
        step_ids = np.arange(sample_count, dtype=np.int64)
    if len(episode_ids) != sample_count or len(step_ids) != sample_count:
        raise ValueError("episode_ids and step_ids must match the sample count.")

    stacked = np.empty((*values.shape[:-1], values.shape[-1] * frame_stack), dtype=values.dtype)
    history_by_episode: dict[int, list[int]] = {}

    for index in range(sample_count):
        episode_key = int(episode_ids[index])
        step = int(step_ids[index])
        if step <= 0 or episode_key not in history_by_episode:
            history_by_episode[episode_key] = []

        history = history_by_episode[episode_key]
        source_indices = [*history, index]
        if not history:
            source_indices = [index] * frame_stack
        elif len(source_indices) < frame_stack:
            source_indices = [source_indices[0]] * (frame_stack - len(source_indices)) + source_indices
        else:
            source_indices = source_indices[-frame_stack:]

        stacked[index] = np.concatenate([values[source_index] for source_index in source_indices], axis=-1)
        history.append(index)
        if len(history) > frame_stack - 1:
            del history[: len(history) - (frame_stack - 1)]

    return np.ascontiguousarray(stacked)


def maybe_stack_image_array(
    values: np.ndarray,
    *,
    frame_stack: int,
    episode_ids: np.ndarray | None = None,
    step_ids: np.ndarray | None = None,
) -> np.ndarray:
    if values.ndim != 4:
        raise ValueError(f"Expected image array shape (N, H, W, C), got {values.shape}")
    if frame_stack <= 0:
        raise ValueError("frame_stack must be positive.")
    if values.shape[-1] == frame_stack:
        return np.ascontiguousarray(values)
    if values.shape[-1] != 1:
        raise ValueError(
            f"Cannot derive frame stack {frame_stack} from image channels {values.shape[-1]}."
        )
    return stack_sequence_array(
        values,
        frame_stack=frame_stack,
        episode_ids=episode_ids,
        step_ids=step_ids,
    )


def maybe_stack_control_state(
    control_state: np.ndarray,
    *,
    frame_stack: int,
    episode_ids: np.ndarray | None = None,
    step_ids: np.ndarray | None = None,
) -> np.ndarray:
    if control_state.ndim != 2:
        raise ValueError(f"Expected control_state shape (N, D), got {control_state.shape}")
    expected_dim = CONTROL_STATE_DIM * frame_stack
    if control_state.shape[1] == expected_dim:
        return np.ascontiguousarray(control_state, dtype=np.float32)
    if control_state.shape[1] != CONTROL_STATE_DIM:
        raise ValueError(
            f"Cannot derive control_state stack {frame_stack} from dim {control_state.shape[1]}."
        )
    return stack_sequence_array(
        control_state,
        frame_stack=frame_stack,
        episode_ids=episode_ids,
        step_ids=step_ids,
    ).astype(np.float32, copy=False)
