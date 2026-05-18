from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from stable_baselines3 import SAC

from peg_in_hole_mujoco import PegInHoleMujocoEnv
from peg_in_hole_mujoco.dataset_stacking import (
    CONTROL_STATE_DIM,
    maybe_stack_control_state,
    maybe_stack_image_array,
)
from peg_in_hole_mujoco.sim_config import parse_args_with_config


@dataclass
class LoadedDataset:
    path: Path
    images: np.ndarray
    near_hole_crops: np.ndarray | None
    control_states: np.ndarray | None
    actions: np.ndarray
    train_indices: np.ndarray
    val_indices: np.ndarray
    recovery_phase: np.ndarray | None
    train_phase_indices: dict[str, np.ndarray]
    val_phase_indices: dict[str, np.ndarray]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Behavior-clone an image SAC actor from weighted expert datasets."
    )
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--datasets", nargs="+", type=Path, required=True)
    parser.add_argument("--dataset-weights", nargs="+", type=float, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata-output", type=Path, default=None)
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--samples-per-epoch", type=int, default=300_000)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=5e-6)
    parser.add_argument("--validation-split", type=float, default=0.05)
    parser.add_argument("--validation-batches", type=int, default=20)
    parser.add_argument("--phase-balanced-recovery", action="store_true")
    parser.add_argument(
        "--recovery-phase-names",
        nargs="+",
        default=("unjam_lift", "realign", "slow_insert"),
    )
    parser.add_argument("--recovery-phase-weights", nargs="+", type=float, default=None)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=410_000)
    parser.add_argument("--image-width", type=int, default=100)
    parser.add_argument("--image-height", type=int, default=100)
    parser.add_argument("--include-near-hole-crop", action="store_true")
    parser.add_argument("--near-hole-crop-size", type=int, default=64)
    parser.add_argument("--near-hole-crop-offset", nargs=2, type=int, default=(0, 0))
    parser.add_argument("--include-control-state", action="store_true")
    parser.add_argument("--image-frame-stack", type=int, default=1)
    parser.add_argument("--wrist-camera-pos-offset", nargs=3, type=float, default=(0.0, 0.0, 0.0))
    parser.add_argument(
        "--wrist-camera-rot-offset-deg",
        nargs=3,
        type=float,
        default=(0.0, 0.0, 0.0),
    )
    parser.add_argument("--wrist-camera-fovy", type=float, default=None)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--target-low", nargs=3, type=float, default=(0.50, 0.00, 0.65))
    parser.add_argument("--target-high", nargs=3, type=float, default=(0.60, 0.10, 0.65))
    parser.add_argument(
        "--initialization-mode",
        choices=["fixed", "target_relative_high_start"],
        default="fixed",
    )
    parser.add_argument("--initial-tip-z-above-range", nargs=2, type=float, default=(0.15, 0.25))
    parser.add_argument("--initial-tip-xy-offset-range", nargs=2, type=float, default=(0.08, 0.16))
    parser.add_argument(
        "--initial-tip-xy-angle-range-deg",
        nargs=2,
        type=float,
        default=(0.0, 360.0),
    )
    parser.add_argument("--initial-ik-max-attempts", type=int, default=20)
    parser.add_argument("--ik-control-mode", choices=["position", "pose"], default="position")
    parser.add_argument("--ik-orientation-weight", type=float, default=0.12)
    parser.add_argument("--ik-posture-weight", type=float, default=0.01)
    parser.add_argument("--ik-step-limit", type=float, default=0.06)
    parser.add_argument("--ik-max-iterations", type=int, default=24)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--geometry-hole-half-size-range", nargs=2, type=float, default=(0.017, 0.021))
    parser.add_argument("--approach-xy-tolerance", type=float, default=0.06)
    parser.add_argument("--approach-height", type=float, default=0.08)
    parser.add_argument("--staged-xy-weight", type=float, default=2.0)
    parser.add_argument("--staged-z-weight", type=float, default=1.0)
    parser.add_argument("--success-bonus", type=float, default=120.0)
    parser.add_argument("--collision-penalty", type=float, default=300.0)
    parser.add_argument("--timeout-penalty", type=float, default=10.0)
    parser.add_argument("--progress-reward-scale", type=float, default=20.0)
    parser.add_argument("--distance-reward-scale", type=float, default=2.0)
    parser.add_argument("--action-penalty-scale", type=float, default=0.002)
    parser.add_argument("--action-alignment-scale", type=float, default=2.0)
    parser.add_argument("--buffer-size", type=int, default=100_000)
    parser.add_argument("--learning-starts", type=int, default=1_000)
    parser.add_argument("--ent-coef", default="auto_0.01")
    return parse_args_with_config(parser)


def normalize_weights(weights: list[float], count: int) -> np.ndarray:
    if len(weights) != count:
        raise ValueError("--dataset-weights must match --datasets length.")
    array = np.asarray(weights, dtype=np.float64)
    if np.any(array < 0.0) or float(array.sum()) <= 0.0:
        raise ValueError("--dataset-weights must be non-negative and sum to a positive value.")
    return array / array.sum()


def normalize_named_weights(names: list[str], weights: list[float] | None) -> dict[str, float]:
    if not names:
        raise ValueError("--recovery-phase-names cannot be empty.")
    if weights is None:
        weights = [1.0] * len(names)
    if len(weights) != len(names):
        raise ValueError("--recovery-phase-weights must match --recovery-phase-names length.")
    array = np.asarray(weights, dtype=np.float64)
    if np.any(array < 0.0) or float(array.sum()) <= 0.0:
        raise ValueError("--recovery-phase-weights must be non-negative and sum to a positive value.")
    normalized = array / array.sum()
    return {str(name): float(weight) for name, weight in zip(names, normalized)}


def make_env(args: argparse.Namespace) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        model_path=args.model_path,
        observation_mode="image",
        image_width=args.image_width,
        image_height=args.image_height,
        include_near_hole_crop=args.include_near_hole_crop,
        near_hole_crop_size=args.near_hole_crop_size,
        near_hole_crop_offset=tuple(args.near_hole_crop_offset),
        include_control_state=args.include_control_state,
        image_frame_stack=args.image_frame_stack,
        wrist_camera_pos_offset=tuple(args.wrist_camera_pos_offset),
        wrist_camera_rot_offset_deg=tuple(args.wrist_camera_rot_offset_deg),
        wrist_camera_fovy=args.wrist_camera_fovy,
        max_steps=args.max_steps,
        action_scale=args.action_scale,
        target_low=tuple(args.target_low),
        target_high=tuple(args.target_high),
        initialization_mode=args.initialization_mode,
        initial_tip_z_above_range=tuple(args.initial_tip_z_above_range),
        initial_tip_xy_offset_range=tuple(args.initial_tip_xy_offset_range),
        initial_tip_xy_angle_range_deg=tuple(args.initial_tip_xy_angle_range_deg),
        initial_ik_max_attempts=args.initial_ik_max_attempts,
        ik_control_mode=args.ik_control_mode,
        ik_orientation_weight=args.ik_orientation_weight,
        ik_posture_weight=args.ik_posture_weight,
        ik_step_limit=args.ik_step_limit,
        ik_max_iterations=args.ik_max_iterations,
        success_xy_tolerance=args.success_xy_tolerance,
        success_z_tolerance=args.success_z_tolerance,
        geometry_hole_half_size_range=tuple(args.geometry_hole_half_size_range),
        approach_xy_tolerance=args.approach_xy_tolerance,
        approach_height=args.approach_height,
        staged_xy_weight=args.staged_xy_weight,
        staged_z_weight=args.staged_z_weight,
        success_bonus=args.success_bonus,
        collision_penalty=args.collision_penalty,
        timeout_penalty=args.timeout_penalty,
        progress_reward_scale=args.progress_reward_scale,
        distance_reward_scale=args.distance_reward_scale,
        action_penalty_scale=args.action_penalty_scale,
        action_alignment_scale=args.action_alignment_scale,
    )


def load_or_create_model(args: argparse.Namespace, env: PegInHoleMujocoEnv) -> SAC:
    if args.model is not None:
        return SAC.load(args.model, env=env, device=args.device)
    return SAC(
        "MultiInputPolicy",
        env,
        device=args.device,
        learning_rate=args.learning_rate,
        buffer_size=args.buffer_size,
        learning_starts=args.learning_starts,
        ent_coef=args.ent_coef,
        seed=args.seed,
        verbose=1,
    )


def center_crop_images(
    images: np.ndarray,
    crop_size: int,
    crop_offset: tuple[int, int] = (0, 0),
) -> np.ndarray:
    if crop_size <= 0:
        raise ValueError("crop_size must be positive.")
    if images.ndim != 4:
        raise ValueError(f"Expected image batch shape (N, H, W, C), got {images.shape}")
    height, width = images.shape[1:3]
    source_size = min(crop_size, height, width)
    offset_x, offset_y = crop_offset
    x0 = int(np.clip((width - source_size) // 2 + offset_x, 0, width - source_size))
    y0 = int(np.clip((height - source_size) // 2 + offset_y, 0, height - source_size))
    crop = images[:, y0 : y0 + source_size, x0 : x0 + source_size, :]
    if crop.shape[1] == crop_size and crop.shape[2] == crop_size:
        return np.ascontiguousarray(crop)
    y_idx = np.linspace(0, crop.shape[1] - 1, crop_size).round().astype(np.int64)
    x_idx = np.linspace(0, crop.shape[2] - 1, crop_size).round().astype(np.int64)
    return np.ascontiguousarray(crop[:, y_idx][:, :, x_idx, :])


def load_or_derive_crops(
    dataset: np.lib.npyio.NpzFile,
    images: np.ndarray,
    crop_size: int,
    crop_offset: tuple[int, int] = (0, 0),
    frame_stack: int = 1,
    episode_ids: np.ndarray | None = None,
    step_ids: np.ndarray | None = None,
) -> np.ndarray:
    if "near_hole_crops" in dataset:
        crops = dataset["near_hole_crops"]
        if crops.dtype != np.uint8:
            raise ValueError(f"Expected uint8 near_hole_crops, got {crops.dtype}")
        return maybe_stack_image_array(
            crops,
            frame_stack=frame_stack,
            episode_ids=episode_ids,
            step_ids=step_ids,
        )
    return center_crop_images(images, crop_size, crop_offset)


def derive_control_state(
    dataset: np.lib.npyio.NpzFile,
    actions: np.ndarray,
    action_scale: float,
    max_steps: int,
    frame_stack: int,
) -> np.ndarray:
    sample_count = len(actions)
    episode_ids = (
        np.asarray(dataset["episode_id"], dtype=np.int64)
        if "episode_id" in dataset
        else np.zeros(sample_count, dtype=np.int64)
    )
    step_ids = (
        np.asarray(dataset["step_id"], dtype=np.float32)
        if "step_id" in dataset
        else np.arange(sample_count, dtype=np.float32)
    )
    if "control_state" in dataset:
        control_state = np.asarray(dataset["control_state"], dtype=np.float32)
        return maybe_stack_control_state(
            control_state,
            frame_stack=frame_stack,
            episode_ids=episode_ids,
            step_ids=step_ids,
        )

    command_source = (
        np.asarray(dataset["raw_actions"], dtype=np.float32)
        if "raw_actions" in dataset
        else np.asarray(actions, dtype=np.float32) * float(action_scale)
    )
    actual_delta = (
        np.asarray(dataset["action_actual_tip_delta"], dtype=np.float32)
        if "action_actual_tip_delta" in dataset
        else np.zeros((sample_count, 3), dtype=np.float32)
    )
    previous_command = np.zeros((sample_count, 3), dtype=np.float32)
    last_command_by_episode: dict[int, np.ndarray] = {}
    for index, episode_id in enumerate(episode_ids):
        episode_key = int(episode_id)
        if float(step_ids[index]) > 0.0 and episode_key in last_command_by_episode:
            previous_command[index] = last_command_by_episode[episode_key]
        last_command_by_episode[episode_key] = command_source[index].astype(np.float32, copy=True)

    scale = max(float(action_scale), 1e-9)
    tracking_error = previous_command - actual_delta
    step_fraction = (step_ids.reshape(-1, 1) / max(float(max_steps), 1.0)).astype(np.float32)
    base_control_state = np.concatenate(
        [
            previous_command / scale,
            actual_delta / scale,
            tracking_error / scale,
            step_fraction,
        ],
        axis=1,
    ).astype(np.float32)
    return maybe_stack_control_state(
        base_control_state,
        frame_stack=frame_stack,
        episode_ids=episode_ids,
        step_ids=step_ids,
    )


def build_phase_indices(
    recovery_phase: np.ndarray | None,
    indices: np.ndarray,
) -> dict[str, np.ndarray]:
    if recovery_phase is None:
        return {}
    phase_indices: dict[str, np.ndarray] = {}
    for phase in np.unique(recovery_phase[indices]):
        phase_name = str(phase)
        phase_indices[phase_name] = indices[recovery_phase[indices] == phase]
    return phase_indices


def load_dataset(
    path: Path,
    rng: np.random.Generator,
    validation_split: float,
    include_near_hole_crop: bool,
    include_control_state: bool,
    near_hole_crop_size: int,
    near_hole_crop_offset: tuple[int, int] = (0, 0),
    action_scale: float = 0.005,
    max_steps: int = 200,
    frame_stack: int = 1,
) -> LoadedDataset:
    with np.load(path) as dataset:
        episode_ids = (
            np.asarray(dataset["episode_id"], dtype=np.int64)
            if "episode_id" in dataset
            else None
        )
        step_ids = (
            np.asarray(dataset["step_id"], dtype=np.float32)
            if "step_id" in dataset
            else None
        )
        images = maybe_stack_image_array(
            dataset["cam_images"],
            frame_stack=frame_stack,
            episode_ids=episode_ids,
            step_ids=step_ids,
        )
        near_hole_crops = (
            load_or_derive_crops(
                dataset,
                images,
                near_hole_crop_size,
                near_hole_crop_offset,
                frame_stack,
                episode_ids,
                step_ids,
            )
            if include_near_hole_crop
            else None
        )
        actions = np.asarray(dataset["actions"], dtype=np.float32)
        control_states = (
            derive_control_state(dataset, actions, action_scale, max_steps, frame_stack)
            if include_control_state
            else None
        )
        recovery_phase = (
            np.asarray(dataset["recovery_phase"])
            if "recovery_phase" in dataset
            else None
        )
    if images.ndim != 4 or images.shape[-1] <= 0:
        raise ValueError(f"{path}: expected cam_images shape (N, H, W, C), got {images.shape}")
    if actions.ndim != 2 or actions.shape[1] != 3:
        raise ValueError(f"{path}: expected actions shape (N, 3), got {actions.shape}")
    if control_states is not None and (
        control_states.ndim != 2 or control_states.shape[1] % CONTROL_STATE_DIM != 0
    ):
        raise ValueError(
            f"{path}: expected control_state shape (N, {CONTROL_STATE_DIM} * K), got {control_states.shape}"
        )

    indices = rng.permutation(len(images))
    val_size = int(len(indices) * validation_split)
    val_indices = indices[:val_size]
    train_indices = indices[val_size:]
    if len(train_indices) == 0:
        raise ValueError(f"{path}: training split is empty.")
    if len(val_indices) == 0:
        val_indices = train_indices
    return LoadedDataset(
        path,
        images,
        near_hole_crops,
        control_states,
        actions,
        train_indices,
        val_indices,
        recovery_phase,
        build_phase_indices(recovery_phase, train_indices),
        build_phase_indices(recovery_phase, val_indices),
    )


def to_actor_obs(
    images: np.ndarray,
    near_hole_crops: np.ndarray | None,
    control_states: np.ndarray | None,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    tensor = torch.as_tensor(images, device=device)
    obs = {"cam_image": tensor.permute(0, 3, 1, 2)}
    if near_hole_crops is not None:
        crop_tensor = torch.as_tensor(near_hole_crops, device=device)
        obs["near_hole_crop"] = crop_tensor.permute(0, 3, 1, 2)
    if control_states is not None:
        state_tensor = torch.as_tensor(control_states, dtype=torch.float32, device=device)
        obs["control_state"] = state_tensor
    return obs


def batch_loss(
    actor: torch.nn.Module,
    dataset: LoadedDataset,
    indices: np.ndarray,
    device: torch.device,
) -> torch.Tensor:
    crop_batch = (
        dataset.near_hole_crops[indices]
        if dataset.near_hole_crops is not None
        else None
    )
    control_batch = (
        dataset.control_states[indices]
        if dataset.control_states is not None
        else None
    )
    obs = to_actor_obs(dataset.images[indices], crop_batch, control_batch, device)
    target = torch.as_tensor(dataset.actions[indices], dtype=torch.float32, device=device)
    pred = actor(obs, deterministic=True)
    return F.mse_loss(pred, target)


def sample_dataset_indices(
    dataset: LoadedDataset,
    candidate_indices: np.ndarray,
    batch_size: int,
    rng: np.random.Generator,
    *,
    phase_balanced_recovery: bool,
    recovery_phase_weights: dict[str, float],
    validation: bool = False,
) -> np.ndarray:
    phase_indices = dataset.val_phase_indices if validation else dataset.train_phase_indices
    if not phase_balanced_recovery or not phase_indices:
        return rng.choice(candidate_indices, size=batch_size, replace=True)

    available_names: list[str] = []
    available_weights: list[float] = []
    for phase_name, phase_weight in recovery_phase_weights.items():
        indices = phase_indices.get(phase_name)
        if indices is not None and len(indices) > 0 and phase_weight > 0.0:
            available_names.append(phase_name)
            available_weights.append(float(phase_weight))
    if not available_names:
        return rng.choice(candidate_indices, size=batch_size, replace=True)

    weights = np.asarray(available_weights, dtype=np.float64)
    weights = weights / weights.sum()
    sampled_phases = rng.choice(available_names, size=batch_size, replace=True, p=weights)
    sampled_indices = np.empty(batch_size, dtype=np.int64)
    for phase_name in available_names:
        mask = sampled_phases == phase_name
        if not np.any(mask):
            continue
        sampled_indices[mask] = rng.choice(
            phase_indices[phase_name],
            size=int(np.sum(mask)),
            replace=True,
        )
    return sampled_indices


def weighted_validation_loss(
    actor: torch.nn.Module,
    datasets: list[LoadedDataset],
    dataset_weights: np.ndarray,
    batch_size: int,
    validation_batches: int,
    rng: np.random.Generator,
    device: torch.device,
    phase_balanced_recovery: bool,
    recovery_phase_weights: dict[str, float],
) -> float:
    losses: list[float] = []
    actor.eval()
    with torch.no_grad():
        for dataset, weight in zip(datasets, dataset_weights):
            dataset_losses = []
            for _ in range(validation_batches):
                indices = sample_dataset_indices(
                    dataset,
                    dataset.val_indices,
                    batch_size,
                    rng,
                    phase_balanced_recovery=phase_balanced_recovery,
                    recovery_phase_weights=recovery_phase_weights,
                    validation=True,
                )
                loss = batch_loss(actor, dataset, indices, device)
                dataset_losses.append(float(loss.detach().cpu()))
            losses.append(float(weight) * float(np.mean(dataset_losses)))
    actor.train()
    return float(np.sum(losses))


def dataset_summary(dataset: LoadedDataset, weight: float) -> dict[str, object]:
    summary: dict[str, object] = {
        "path": str(dataset.path),
        "samples": int(len(dataset.images)),
        "train_samples": int(len(dataset.train_indices)),
        "validation_samples": int(len(dataset.val_indices)),
        "weight": float(weight),
        "has_near_hole_crops": bool(dataset.near_hole_crops is not None),
        "has_control_state": bool(dataset.control_states is not None),
    }
    if dataset.recovery_phase is not None:
        phases, counts = np.unique(dataset.recovery_phase, return_counts=True)
        summary["recovery_phase_counts"] = {
            str(phase): int(count) for phase, count in zip(phases, counts)
        }
        summary["train_recovery_phase_counts"] = {
            str(phase): int(len(indices))
            for phase, indices in sorted(dataset.train_phase_indices.items())
        }
        summary["validation_recovery_phase_counts"] = {
            str(phase): int(len(indices))
            for phase, indices in sorted(dataset.val_phase_indices.items())
        }
    return summary


def main() -> None:
    args = parse_args()
    if args.epochs <= 0:
        raise ValueError("--epochs must be positive.")
    if args.samples_per_epoch <= 0:
        raise ValueError("--samples-per-epoch must be positive.")

    rng = np.random.default_rng(args.seed)
    weights = (
        normalize_weights(args.dataset_weights, len(args.datasets))
        if args.dataset_weights is not None
        else normalize_weights([1.0] * len(args.datasets), len(args.datasets))
    )
    phase_weights = normalize_named_weights(
        [str(name) for name in args.recovery_phase_names],
        args.recovery_phase_weights,
    )
    datasets = [
        load_dataset(
            path,
            rng,
            args.validation_split,
            args.include_near_hole_crop,
            args.include_control_state,
            args.near_hole_crop_size,
            tuple(args.near_hole_crop_offset),
            args.action_scale,
            args.max_steps,
            args.image_frame_stack,
        )
        for path in args.datasets
    ]
    for dataset, weight in zip(datasets, weights):
        print(
            f"dataset={dataset.path} samples={len(dataset.images)} "
            f"train={len(dataset.train_indices)} val={len(dataset.val_indices)} weight={weight:.3f}"
        )
        if args.phase_balanced_recovery and dataset.train_phase_indices:
            phase_summary = ", ".join(
                f"{phase}={len(indices)}"
                for phase, indices in sorted(dataset.train_phase_indices.items())
            )
            print(f"  phase-balanced recovery enabled for train phases: {phase_summary}")

    env = make_env(args)
    model = load_or_create_model(args, env)
    actor = model.policy.actor
    device = model.device
    optimizer = torch.optim.Adam(actor.parameters(), lr=args.learning_rate)
    batches_per_epoch = int(np.ceil(args.samples_per_epoch / args.batch_size))

    actor.train()
    epoch_history: list[dict[str, float | int]] = []
    for epoch in range(args.epochs):
        train_losses = []
        for _ in range(batches_per_epoch):
            dataset_index = int(rng.choice(len(datasets), p=weights))
            dataset = datasets[dataset_index]
            indices = sample_dataset_indices(
                dataset,
                dataset.train_indices,
                args.batch_size,
                rng,
                phase_balanced_recovery=args.phase_balanced_recovery,
                recovery_phase_weights=phase_weights,
            )
            loss = batch_loss(actor, dataset, indices, device)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.detach().cpu()))

        val_loss = weighted_validation_loss(
            actor,
            datasets,
            weights,
            args.batch_size,
            args.validation_batches,
            rng,
            device,
            args.phase_balanced_recovery,
            phase_weights,
        )
        mean_train_loss = float(np.mean(train_losses))
        epoch_history.append(
            {
                "epoch": int(epoch + 1),
                "train_loss": mean_train_loss,
                "val_loss": float(val_loss),
            }
        )
        print(
            f"epoch={epoch + 1} "
            f"train_loss={mean_train_loss:.6f} "
            f"val_loss={val_loss:.6f}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    model.save(args.output)
    metadata_path = (
        args.metadata_output
        if args.metadata_output is not None
        else args.output.with_suffix(args.output.suffix + ".json")
    )
    metadata = {
        "output": str(args.output),
        "base_model": str(args.model) if args.model is not None else None,
        "model_path": str(args.model_path) if args.model_path is not None else None,
        "datasets": [
            dataset_summary(dataset, float(weight))
            for dataset, weight in zip(datasets, weights)
        ],
        "epochs": int(args.epochs),
        "samples_per_epoch": int(args.samples_per_epoch),
        "batch_size": int(args.batch_size),
        "learning_rate": float(args.learning_rate),
        "validation_split": float(args.validation_split),
        "validation_batches": int(args.validation_batches),
        "phase_balanced_recovery": bool(args.phase_balanced_recovery),
        "recovery_phase_weights": phase_weights,
        "seed": int(args.seed),
        "device": str(model.device),
        "include_near_hole_crop": bool(args.include_near_hole_crop),
        "include_control_state": bool(args.include_control_state),
        "image_frame_stack": int(args.image_frame_stack),
        "near_hole_crop_size": int(args.near_hole_crop_size),
        "initialization_mode": args.initialization_mode,
        "initial_tip_z_above_range": [float(value) for value in args.initial_tip_z_above_range],
        "initial_tip_xy_offset_range": [float(value) for value in args.initial_tip_xy_offset_range],
        "initial_tip_xy_angle_range_deg": [
            float(value) for value in args.initial_tip_xy_angle_range_deg
        ],
        "initial_ik_max_attempts": int(args.initial_ik_max_attempts),
        "ik_control_mode": args.ik_control_mode,
        "ik_orientation_weight": float(args.ik_orientation_weight),
        "ik_posture_weight": float(args.ik_posture_weight),
        "ik_step_limit": float(args.ik_step_limit),
        "ik_max_iterations": int(args.ik_max_iterations),
        "success_xy_tolerance": float(args.success_xy_tolerance),
        "success_z_tolerance": float(args.success_z_tolerance),
        "approach_xy_tolerance": float(args.approach_xy_tolerance),
        "history": epoch_history,
        "final_train_loss": epoch_history[-1]["train_loss"],
        "final_val_loss": epoch_history[-1]["val_loss"],
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    env.close()
    print(f"saved weighted image behavior-cloned model to {args.output}")
    print(f"saved training metadata to {metadata_path}")


if __name__ == "__main__":
    main()
