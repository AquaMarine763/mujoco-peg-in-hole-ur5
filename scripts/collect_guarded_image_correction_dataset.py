from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from collect_image_correction_dataset import (
    ClearanceTier,
    append_samples,
    array_metadata,
    build_arrays,
    corrective_action_for_state,
    empty_buffers,
    make_oracle_config,
    make_sample,
    outcome,
    select_episode_samples,
    summarize_float_array,
    summarize_text_array,
)
from eval_guarded_policy import (
    AGENTS,
    CORE_SCENARIOS,
    ApproachAdapterPolicy,
    GuardedPolicyController,
    MujocoGuardStateProvider,
    apply_approach_adapter,
    apply_guard_near_ik_orientation_weight,
    build_parser as build_eval_parser,
    guard_near_control_active,
    make_env,
    make_guarded_config,
    make_hard_bucket_scenario,
    oracle_action_from_state,
    policy_observation,
)
from peg_in_hole_mujoco.sim_config import parse_args_with_config


DATASET_SCHEMA_VERSION = "image_correction_v11_guarded_rollout"


def add_collection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=10_000)
    parser.add_argument("--samples-per-config", type=int, default=None)
    parser.add_argument("--max-episodes-per-config", type=int, default=1000)
    parser.add_argument("--compressed", action="store_true")
    parser.add_argument(
        "--selection",
        choices=[
            "failure_window",
            "near_hole_failure_window",
            "near_hole",
            "failed_episode_near_hole",
            "failed_episode_all",
            "timeout_progress_window",
            "timeout_progress_failure_window",
            "insert_drift_window",
            "insert_drift_failure_window",
            "insert_settle_window",
            "insert_settle_failure_window",
            "balanced_v4b_window",
            "balanced_v4b_failure_window",
            "early_approach_assist_window",
            "early_approach_assist_failure_window",
            "approach_window",
            "approach_failure_window",
            "fixture_wall_window",
            "fixture_wall_failure_window",
        ],
        default="approach_window",
    )
    parser.add_argument(
        "--episode-outcome-filter",
        choices=["any", "collision", "timeout", "terminated_failure"],
        default="any",
    )
    parser.add_argument("--keep-success-episodes", action="store_true")
    parser.add_argument("--failure-window-steps", type=int, default=8)
    parser.add_argument("--near-hole-xy", type=float, default=0.03)
    parser.add_argument("--near-hole-z", type=float, default=0.10)
    parser.add_argument("--min-correction-norm", type=float, default=0.004)
    parser.add_argument("--max-samples-per-episode", type=int, default=8)

    parser.add_argument("--insert-drift-correction-labels", action="store_true")
    parser.add_argument("--insert-drift-window-xy-max", type=float, default=0.015)
    parser.add_argument("--insert-drift-window-z-max", type=float, default=0.038)
    parser.add_argument("--insert-drift-stable-xy", type=float, default=0.0045)
    parser.add_argument("--insert-drift-stable-steps", type=int, default=4)
    parser.add_argument("--insert-drift-correction-max-xy-action", type=float, default=0.003)
    parser.add_argument("--insert-drift-correction-max-down-action", type=float, default=0.001)
    parser.add_argument("--insert-settle-correction-labels", action="store_true")
    parser.add_argument("--insert-settle-window-xy-max", type=float, default=0.015)
    parser.add_argument("--insert-settle-window-z-max", type=float, default=0.045)
    parser.add_argument("--insert-settle-insert-xy", type=float, default=0.0065)
    parser.add_argument("--insert-settle-settle-xy", type=float, default=0.010)
    parser.add_argument("--insert-settle-stable-steps", type=int, default=2)
    parser.add_argument("--insert-settle-hover-height", type=float, default=0.030)
    parser.add_argument("--insert-settle-hover-z-tolerance", type=float, default=0.006)
    parser.add_argument("--insert-settle-lift-z-max", type=float, default=0.016)
    parser.add_argument("--insert-settle-max-xy-action", type=float, default=0.0025)
    parser.add_argument("--insert-settle-max-down-action", type=float, default=0.0015)

    parser.add_argument("--balanced-v4b-labels", action="store_true")
    parser.add_argument("--balanced-v4b-window-xy", type=float, default=0.020)
    parser.add_argument("--balanced-v4b-window-z-max", type=float, default=0.080)
    parser.add_argument("--balanced-v4b-stable-xy", type=float, default=0.0045)
    parser.add_argument("--balanced-v4b-stable-steps", type=int, default=4)
    parser.add_argument("--balanced-v4b-low-z", type=float, default=0.040)
    parser.add_argument("--balanced-v4b-hover-height", type=float, default=0.050)
    parser.add_argument("--balanced-v4b-hover-z-tolerance", type=float, default=0.010)
    parser.add_argument("--balanced-v4b-max-down-action", type=float, default=0.0012)

    parser.add_argument("--approach-correction-labels", action="store_true")
    parser.add_argument("--approach-window-xy-min", type=float, default=0.020)
    parser.add_argument("--approach-window-xy-max", type=float, default=0.160)
    parser.add_argument("--approach-window-z-min", type=float, default=0.060)
    parser.add_argument("--approach-window-z-max", type=float, default=0.180)
    parser.add_argument("--approach-correction-target-height", type=float, default=0.120)
    parser.add_argument("--approach-correction-max-down-action", type=float, default=0.0)
    parser.add_argument(
        "--approach-sample-sort-key",
        choices=["correction_norm", "dist_xy", "steps_to_end"],
        default="correction_norm",
    )

    parser.add_argument("--early-approach-assist-labels", action="store_true")
    parser.add_argument("--early-approach-assist-trigger-xy", type=float, default=0.100)
    parser.add_argument("--early-approach-assist-release-xy", type=float, default=0.060)
    parser.add_argument("--early-approach-assist-min-z", type=float, default=0.120)
    parser.add_argument("--early-approach-assist-max-z", type=float, default=0.270)
    parser.add_argument("--early-approach-assist-target-height", type=float, default=0.140)
    parser.add_argument("--early-approach-assist-max-xy-action", type=float, default=0.008)
    parser.add_argument("--early-approach-assist-max-up-action", type=float, default=0.005)
    parser.add_argument("--early-approach-assist-max-down-action", type=float, default=0.0035)
    parser.add_argument(
        "--early-approach-assist-window-mode",
        choices=["release_band", "trigger_only"],
        default="release_band",
    )

    parser.add_argument("--fixture-wall-correction-labels", action="store_true")
    parser.add_argument("--fixture-wall-window-xy-min", type=float, default=0.020)
    parser.add_argument("--fixture-wall-window-xy-max", type=float, default=0.090)
    parser.add_argument("--fixture-wall-window-z-min", type=float, default=0.040)
    parser.add_argument("--fixture-wall-window-z-max", type=float, default=0.080)
    parser.add_argument("--fixture-wall-correction-target-height", type=float, default=0.080)
    parser.add_argument("--fixture-wall-correction-max-xy-action", type=float, default=0.003)
    parser.add_argument("--fixture-wall-correction-max-down-action", type=float, default=0.0)


def parse_args() -> argparse.Namespace:
    parser = build_eval_parser(
        "Collect correction samples from the same guarded deployment rollout used by eval."
    )
    add_collection_args(parser)
    args = parse_args_with_config(parser)
    normalize_args(args)
    return args


def normalize_args(args: argparse.Namespace) -> None:
    args.image_width = args.width
    args.image_height = args.height
    args.oracle_mode = args.guarded_oracle_mode
    args.oracle_action_gain = args.guard_action_gain


def scenarios_for_args(args: argparse.Namespace) -> list[Any]:
    hard_bucket = make_hard_bucket_scenario(args)
    scenarios = [hard_bucket] if args.hard_bucket_only else list(CORE_SCENARIOS)
    if args.include_hard_bucket and not args.hard_bucket_only:
        scenarios.append(hard_bucket)
    return scenarios


def make_collection_tier(args: argparse.Namespace) -> ClearanceTier:
    return ClearanceTier(
        "eval_config",
        tuple(args.geometry_hole_half_size_range),
        tuple(args.geometry_peg_radius_range),
    )


def run_guarded_episode(
    env: Any,
    model: Any,
    guarded_controller: GuardedPolicyController,
    guard_state_provider: MujocoGuardStateProvider,
    rollout_adapter: ApproachAdapterPolicy | None,
    oracle_config: Any,
    *,
    args: argparse.Namespace,
    tier: ClearanceTier,
    scenario: Any,
    episode_id: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    env.set_ik_control_mode(args.ik_control_mode)
    env.set_ik_orientation_weight(args.ik_orientation_weight)
    obs, info = env.reset(seed=seed)
    guarded_controller.reset()

    episode_base_actuator_kp_multiplier = float(
        info.get("actuator_kp_multiplier", args.nominal_actuator_kp_multiplier)
    )
    ablation_rng = np.random.default_rng(seed + 1_000_003)
    image_shuffle_bank: list[Any] = []
    control_state_shuffle_bank: list[np.ndarray] = []
    rows: list[dict[str, Any]] = []
    episode_return = 0.0
    alignment_stable_steps = 0
    ever_within_insert_xy = False
    approach_adapter_latched = False
    approach_adapter_latch_steps = 0
    approach_adapter_episode_steps = 0

    while True:
        current_dist_xy = float(info["dist_xy"])
        if current_dist_xy <= args.balanced_v4b_stable_xy:
            alignment_stable_steps += 1
        else:
            alignment_stable_steps = 0
        ever_within_insert_xy = bool(
            ever_within_insert_xy
            or current_dist_xy <= args.guarded_insert_xy_tolerance
        )

        if args.control_mode == "guard_only":
            state = guard_state_provider.state_from_info(info)
            base_policy_action = np.zeros(3, dtype=np.float32)
            policy_action = base_policy_action.copy()
            adapter_residual = np.zeros(3, dtype=np.float32)
            adapter_active = False
            final_action = oracle_action_from_state(
                peg_tip_pos=state.peg_tip_pos,
                target_pos=state.target_pos,
                applied_action=state.applied_action,
                approach_height=state.approach_height,
                action_low=state.action_low,
                action_high=state.action_high,
                config=make_guarded_config(args).oracle,
            )
            guard_step = None
        else:
            if model is None:
                raise ValueError("guarded/policy rollout requires a loaded model.")
            model_obs = policy_observation(
                obs,
                image_ablation=args.image_ablation,
                image_ablation_target=args.image_ablation_target,
                control_state_ablation=args.control_state_ablation,
                rng=ablation_rng,
                image_shuffle_bank=image_shuffle_bank,
                control_state_shuffle_bank=control_state_shuffle_bank,
            )
            base_policy_action, _ = model.predict(model_obs, deterministic=True)
            base_policy_action = np.asarray(base_policy_action, dtype=np.float32).reshape(3)
            (
                policy_action,
                adapter_residual,
                adapter_active,
            ) = apply_approach_adapter(
                adapter=rollout_adapter,
                args=args,
                obs=model_obs,
                info=info,
                policy_action=base_policy_action,
                action_low=np.asarray(env.action_space.low, dtype=np.float64),
                action_high=np.asarray(env.action_space.high, dtype=np.float64),
                latched=approach_adapter_latched,
                latch_steps=approach_adapter_latch_steps,
                episode_steps=approach_adapter_episode_steps,
            )
            if args.approach_adapter_latch_enabled:
                if adapter_active:
                    approach_adapter_latched = True
                    approach_adapter_latch_steps += 1
                    approach_adapter_episode_steps += 1
                else:
                    approach_adapter_latched = False
                    approach_adapter_latch_steps = 0
            elif adapter_active:
                approach_adapter_episode_steps += 1

            if args.control_mode == "policy":
                final_action = policy_action
                guard_step = None
            else:
                guard_step = guarded_controller.step_with_provider(
                    guard_state_provider,
                    info,
                    policy_action,
                    scenario_name=scenario.name,
                    scenario_level=scenario.level,
                )
                final_action = guard_step.action

        (
            corrective_action,
            phase_override,
            drift_after_alignment,
            descent_should_block,
        ) = corrective_action_for_state(
            env,
            info,
            oracle_config,
            args=args,
            alignment_stable_steps=alignment_stable_steps,
            ever_within_insert_xy=ever_within_insert_xy,
        )
        rows.append(
            make_sample(
                env,
                obs,
                info,
                policy_action,
                corrective_action,
                args=args,
                tier=tier,
                scenario=scenario,
                episode_id=episode_id,
                seed=seed,
                base_policy_action=base_policy_action,
                rollout_approach_adapter_residual=adapter_residual,
                rollout_approach_adapter_active=adapter_active,
                phase_override=phase_override,
                alignment_stable_steps=alignment_stable_steps,
                ever_within_insert_xy=ever_within_insert_xy,
                drift_after_alignment=drift_after_alignment,
                descent_should_block=descent_should_block,
            )
        )

        near_control_active = guard_near_control_active(guard_step, args)
        if args.guard_near_actuator_kp_enabled:
            env.set_arm_actuator_kp_multiplier(
                args.guard_near_actuator_kp_multiplier
                if near_control_active
                else episode_base_actuator_kp_multiplier
            )
        apply_guard_near_ik_orientation_weight(env, guard_step, args)

        obs, reward, terminated, truncated, info = env.step(
            np.asarray(final_action, dtype=np.float32)
        )
        episode_return += float(reward)
        if terminated or truncated:
            break

    final_step = int(info["step_count"])
    episode_outcome = outcome(info, truncated)
    for sample in rows:
        sample["episode_outcome"] = episode_outcome
        sample["episode_success"] = bool(info["insertion_success"])
        sample["episode_collision"] = bool(info["collision"])
        sample["episode_timeout"] = bool(truncated and not info["insertion_success"])
        sample["final_step"] = final_step
        sample["steps_to_end"] = final_step - int(sample["step_id"])
        sample["failure_window"] = bool(
            not info["insertion_success"]
            and int(sample["steps_to_end"]) <= args.failure_window_steps
        )

    return rows, {
        "episode_id": episode_id,
        "seed": seed,
        "scenario": scenario.name,
        "success": bool(info["insertion_success"]),
        "collision": bool(info["collision"]),
        "timeout": bool(truncated and not info["insertion_success"]),
        "episode_outcome": episode_outcome,
        "return": episode_return,
        "final_step": final_step,
        "final_dist_xy": float(info["dist_xy"]),
        "final_dist_z": float(info["dist_z"]),
    }


def save_dataset(
    *,
    args: argparse.Namespace,
    arrays: dict[str, np.ndarray],
    config_summaries: list[dict[str, Any]],
    episode_summaries: list[dict[str, Any]],
    target_per_config: int,
) -> None:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.compressed:
        np.savez_compressed(args.output, **arrays)
    else:
        np.savez(args.output, **arrays)

    metadata = {
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "samples": int(arrays["actions"].shape[0]),
        "model": str(args.model),
        "model_path": str(args.model_path) if args.model_path is not None else "default",
        "control_mode": args.control_mode,
        "samples_per_config": target_per_config,
        "max_episodes_per_config": args.max_episodes_per_config,
        "episodes_completed": len(episode_summaries),
        "config_summaries": config_summaries,
        "selection": args.selection,
        "episode_outcome_filter": args.episode_outcome_filter,
        "keep_success_episodes": args.keep_success_episodes,
        "min_correction_norm": args.min_correction_norm,
        "max_samples_per_episode": args.max_samples_per_episode,
        "geometry_profile": args.geometry_profile,
        "approach_adapter_enabled": args.approach_adapter_enabled,
        "approach_adapter": str(args.approach_adapter)
        if args.approach_adapter is not None
        else None,
        "approach_adapter_latch_enabled": args.approach_adapter_latch_enabled,
        "approach_adapter_latched_min_z": args.approach_adapter_latched_min_z,
        "approach_adapter_max_steps": args.approach_adapter_max_steps,
        "guard_start_xy": args.guard_start_xy,
        "guard_start_z": args.guard_start_z,
        "guard_final_servo_enabled": args.guard_final_servo_enabled,
        "guard_final_servo_start_xy": args.guard_final_servo_start_xy,
        "guard_final_servo_start_z": args.guard_final_servo_start_z,
        "array_metadata": array_metadata(arrays),
        "diagnostics": {
            "correction_norm": summarize_float_array(arrays["correction_norm"]),
            "action_cosine": summarize_float_array(arrays["action_cosine"]),
            "geometry_name": summarize_text_array(arrays["geometry_name"]),
            "peg_shape": summarize_text_array(arrays["peg_shape"]),
            "recovery_phase": summarize_text_array(arrays["recovery_phase"]),
            "episode_outcome": summarize_text_array(arrays["episode_outcome"]),
            "approach_window_rate": float(np.mean(arrays["approach_window"]))
            if arrays["approach_window"].size
            else 0.0,
            "descent_should_block_rate": float(np.mean(arrays["descent_should_block"]))
            if arrays["descent_should_block"].size
            else 0.0,
            "episode_success_rate": float(np.mean(arrays["episode_success"]))
            if arrays["episode_success"].size
            else 0.0,
            "episode_collision_rate": float(np.mean(arrays["episode_collision"]))
            if arrays["episode_collision"].size
            else 0.0,
            "episode_timeout_rate": float(np.mean(arrays["episode_timeout"]))
            if arrays["episode_timeout"].size
            else 0.0,
        },
    }
    metadata_path = args.output.with_suffix(args.output.suffix + ".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved guarded correction dataset to {args.output}")
    print(f"saved metadata to {metadata_path}")
    print(
        f"samples={arrays['actions'].shape[0]} "
        f"episodes_completed={len(episode_summaries)}"
    )


def main() -> None:
    args = parse_args()
    if args.observation_mode != "image":
        raise ValueError("guarded image correction collection requires image observations.")
    if args.samples <= 0:
        raise ValueError("--samples must be positive.")
    if args.max_episodes_per_config <= 0:
        raise ValueError("--max-episodes-per-config must be positive.")

    scenarios = scenarios_for_args(args)
    target_per_config = (
        args.samples_per_config
        if args.samples_per_config is not None
        else int(np.ceil(args.samples / len(scenarios)))
    )
    tier = make_collection_tier(args)
    oracle_config = make_oracle_config(args)
    rollout_adapter = (
        ApproachAdapterPolicy.load(args.approach_adapter, device=args.device)
        if args.approach_adapter_enabled and args.approach_adapter is not None
        else None
    )

    buffers = empty_buffers()
    episode_summaries: list[dict[str, Any]] = []
    config_summaries: list[dict[str, Any]] = []
    global_episode_id = 0

    for config_index, scenario in enumerate(scenarios):
        env = make_env(args, scenario)
        model = (
            None
            if args.control_mode == "guard_only"
            else AGENTS[args.agent].load(args.model, env=env, device=args.device)
        )
        guarded_controller = GuardedPolicyController(make_guarded_config(args))
        guard_state_provider = MujocoGuardStateProvider(env)
        config_samples = 0
        config_episodes = 0
        config_successes = 0
        config_collisions = 0
        config_timeouts = 0
        try:
            while (
                config_samples < target_per_config
                and config_episodes < args.max_episodes_per_config
                and len(buffers["cam_images"]) < args.samples
            ):
                seed = args.seed + config_index * args.max_episodes_per_config + config_episodes
                rows, summary = run_guarded_episode(
                    env,
                    model,
                    guarded_controller,
                    guard_state_provider,
                    rollout_adapter,
                    oracle_config,
                    args=args,
                    tier=tier,
                    scenario=scenario,
                    episode_id=global_episode_id,
                    seed=seed,
                )
                global_episode_id += 1
                config_episodes += 1
                config_successes += int(summary["success"])
                config_collisions += int(summary["collision"])
                config_timeouts += int(summary["timeout"])
                episode_summaries.append(summary)
                selected = select_episode_samples(rows, args)
                kept = append_samples(
                    buffers,
                    selected,
                    min(
                        args.samples - len(buffers["cam_images"]),
                        target_per_config - config_samples,
                    ),
                )
                config_samples += kept
        finally:
            env.close()

        config_summary = {
            "scenario": scenario.name,
            "episodes_completed": config_episodes,
            "samples": config_samples,
            "success_rate": config_successes / max(config_episodes, 1),
            "collision_rate": config_collisions / max(config_episodes, 1),
            "timeout_rate": config_timeouts / max(config_episodes, 1),
        }
        config_summaries.append(config_summary)
        print(
            "{scenario}: samples={samples} episodes={episodes} "
            "success={success:.3f} collision={collision:.3f} timeout={timeout:.3f}".format(
                scenario=scenario.name,
                samples=config_samples,
                episodes=config_episodes,
                success=config_summary["success_rate"],
                collision=config_summary["collision_rate"],
                timeout=config_summary["timeout_rate"],
            )
        )

    arrays = build_arrays(
        buffers,
        args.include_near_hole_crop,
        args.include_control_state,
    )
    save_dataset(
        args=args,
        arrays=arrays,
        config_summaries=config_summaries,
        episode_summaries=episode_summaries,
        target_per_config=target_per_config,
    )


if __name__ == "__main__":
    main()
