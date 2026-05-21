from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Behavior-clone an image SAC actor from expert image/action data.")
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--validation-split", type=float, default=0.1)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=40_000)
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
    parser.add_argument("--initial-tip-xy-angle-range-deg", nargs=2, type=float, default=(0.0, 360.0))
    parser.add_argument("--initial-ik-max-attempts", type=int, default=20)
    parser.add_argument("--ik-control-mode", choices=["position", "pose"], default="position")
    parser.add_argument("--ik-orientation-weight", type=float, default=0.12)
    parser.add_argument("--ik-posture-weight", type=float, default=0.01)
    parser.add_argument("--ik-step-limit", type=float, default=0.06)
    parser.add_argument("--ik-max-iterations", type=int, default=24)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--geometry-hole-half-size-range", nargs=2, type=float, default=(0.017, 0.021))
    parser.add_argument("--geometry-peg-radius-range", nargs=2, type=float, default=(0.0115, 0.0125))
    parser.add_argument(
        "--geometry-profile",
        choices=["single", "round_square", "square_square", "mixed_basic"],
        default="single",
    )
    parser.add_argument("--geometry-square-peg-half-size-range", nargs=2, type=float, default=(0.0105, 0.0125))
    parser.add_argument("--geometry-mixed-square-probability", type=float, default=0.5)
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
        geometry_peg_radius_range=tuple(args.geometry_peg_radius_range),
        geometry_profile=args.geometry_profile,
        geometry_square_peg_half_size_range=tuple(args.geometry_square_peg_half_size_range),
        geometry_mixed_square_probability=args.geometry_mixed_square_probability,
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


def load_near_hole_crops(
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
    episode_ids = (
        np.asarray(dataset["episode_id"], dtype=np.int64)
        if "episode_id" in dataset
        else np.zeros(len(actions), dtype=np.int64)
    )
    step_ids = (
        np.asarray(dataset["step_id"], dtype=np.float32)
        if "step_id" in dataset
        else np.arange(len(actions), dtype=np.float32)
    )
    if "control_state" in dataset:
        control_state = np.asarray(dataset["control_state"], dtype=np.float32)
        return maybe_stack_control_state(
            control_state,
            frame_stack=frame_stack,
            episode_ids=episode_ids,
            step_ids=step_ids,
        )

    sample_count = len(actions)
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


def to_actor_obs(
    images: np.ndarray,
    near_hole_crops: np.ndarray | None,
    control_states: np.ndarray | None,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    tensor = torch.as_tensor(images, device=device)
    if tensor.ndim != 4 or tensor.shape[-1] <= 0:
        raise ValueError(f"Expected image batch shape (N, H, W, C), got {tuple(tensor.shape)}")
    obs = {"cam_image": tensor.permute(0, 3, 1, 2)}
    if near_hole_crops is not None:
        crop_tensor = torch.as_tensor(near_hole_crops, device=device)
        if crop_tensor.ndim != 4 or crop_tensor.shape[-1] <= 0:
            raise ValueError(
                f"Expected crop batch shape (N, H, W, C), got {tuple(crop_tensor.shape)}"
            )
        obs["near_hole_crop"] = crop_tensor.permute(0, 3, 1, 2)
    if control_states is not None:
        state_tensor = torch.as_tensor(control_states, dtype=torch.float32, device=device)
        if state_tensor.ndim != 2 or state_tensor.shape[1] % CONTROL_STATE_DIM != 0:
            raise ValueError(
                f"Expected control_state batch shape (N, {CONTROL_STATE_DIM} * K), got {tuple(state_tensor.shape)}"
            )
        obs["control_state"] = state_tensor
    return obs


def batch_loss(
    actor: torch.nn.Module,
    images: np.ndarray,
    near_hole_crops: np.ndarray | None,
    control_states: np.ndarray | None,
    actions: np.ndarray,
    indices: np.ndarray,
    device: torch.device,
) -> torch.Tensor:
    crop_batch = near_hole_crops[indices] if near_hole_crops is not None else None
    control_batch = control_states[indices] if control_states is not None else None
    obs = to_actor_obs(images[indices], crop_batch, control_batch, device)
    target = torch.as_tensor(actions[indices], dtype=torch.float32, device=device)
    pred = actor(obs, deterministic=True)
    return F.mse_loss(pred, target)


def mean_loss(
    actor: torch.nn.Module,
    images: np.ndarray,
    near_hole_crops: np.ndarray | None,
    control_states: np.ndarray | None,
    actions: np.ndarray,
    indices: np.ndarray,
    batch_size: int,
    device: torch.device,
) -> float:
    losses = []
    actor.eval()
    with torch.no_grad():
        for start in range(0, len(indices), batch_size):
            batch_indices = indices[start : start + batch_size]
            loss = batch_loss(actor, images, near_hole_crops, control_states, actions, batch_indices, device)
            losses.append(float(loss.detach().cpu()))
    actor.train()
    return float(np.mean(losses)) if losses else 0.0


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    dataset = np.load(args.dataset)
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
        frame_stack=args.image_frame_stack,
        episode_ids=episode_ids,
        step_ids=step_ids,
    )
    near_hole_crops = (
        load_near_hole_crops(
            dataset,
            images,
            args.near_hole_crop_size,
            tuple(args.near_hole_crop_offset),
            args.image_frame_stack,
            episode_ids,
            step_ids,
        )
        if args.include_near_hole_crop
        else None
    )
    actions = dataset["actions"].astype(np.float32)
    control_states = (
        derive_control_state(
            dataset,
            actions,
            args.action_scale,
            args.max_steps,
            args.image_frame_stack,
        )
        if args.include_control_state
        else None
    )
    if images.dtype != np.uint8:
        raise ValueError(f"Expected uint8 cam_images, got {images.dtype}")
    if actions.ndim != 2 or actions.shape[1] != 3:
        raise ValueError(f"Expected actions shape (N, 3), got {actions.shape}")

    env = make_env(args)
    model = load_or_create_model(args, env)
    actor = model.policy.actor
    device = model.device
    optimizer = torch.optim.Adam(actor.parameters(), lr=args.learning_rate)

    indices = rng.permutation(len(images))
    val_size = int(len(indices) * args.validation_split)
    val_indices = indices[:val_size]
    train_indices = indices[val_size:]
    if len(train_indices) == 0:
        raise ValueError("Training split is empty; reduce --validation-split or add samples.")

    actor.train()
    for epoch in range(args.epochs):
        epoch_indices = rng.permutation(train_indices)
        train_losses = []
        for start in range(0, len(epoch_indices), args.batch_size):
            batch_indices = epoch_indices[start : start + args.batch_size]
            loss = batch_loss(actor, images, near_hole_crops, control_states, actions, batch_indices, device)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.detach().cpu()))

        val_loss = mean_loss(
            actor,
            images,
            near_hole_crops,
            control_states,
            actions,
            val_indices,
            args.batch_size,
            device,
        )
        print(
            f"epoch={epoch + 1} "
            f"train_loss={np.mean(train_losses):.6f} "
            f"val_loss={val_loss:.6f}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    model.save(args.output)
    env.close()
    print(f"saved image behavior-cloned model to {args.output}")


if __name__ == "__main__":
    main()
