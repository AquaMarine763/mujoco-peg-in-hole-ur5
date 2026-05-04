from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from stable_baselines3 import SAC

from peg_in_hole_mujoco import PegInHoleMujocoEnv


@dataclass(frozen=True)
class ContactScanConfig:
    name: str
    level: str = "full_contact_light"
    friction_range: tuple[float, float] = (1.0, 1.0)
    solref_time_range: tuple[float, float] = (1.0, 1.0)
    solref_damping_range: tuple[float, float] = (1.0, 1.0)
    solimp_width_range: tuple[float, float] = (1.0, 1.0)
    joint_damping_range: tuple[float, float] = (1.0, 1.0)
    actuator_kp_range: tuple[float, float] = (1.0, 1.0)


CONTACT_SCAN_CONFIGS = (
    ContactScanConfig("full_light_geometry_reference", level="full_light_geometry"),
    ContactScanConfig("friction_only", friction_range=(0.7, 1.3)),
    ContactScanConfig("solref_time_only", solref_time_range=(0.8, 1.25)),
    ContactScanConfig("solref_damping_only", solref_damping_range=(0.8, 1.2)),
    ContactScanConfig("solimp_width_only", solimp_width_range=(0.8, 1.2)),
    ContactScanConfig("joint_damping_only", joint_damping_range=(0.8, 1.2)),
    ContactScanConfig("actuator_kp_only", actuator_kp_range=(0.8, 1.2)),
    ContactScanConfig(
        "default_contact_light",
        friction_range=(0.7, 1.3),
        solref_time_range=(0.8, 1.25),
        solref_damping_range=(0.8, 1.2),
        solimp_width_range=(0.8, 1.2),
        joint_damping_range=(0.8, 1.2),
        actuator_kp_range=(0.8, 1.2),
    ),
    ContactScanConfig(
        "high_contact_light",
        friction_range=(0.5, 1.5),
        solref_time_range=(0.6, 1.6),
        solref_damping_range=(0.6, 1.5),
        solimp_width_range=(0.5, 1.5),
        joint_damping_range=(0.6, 1.5),
        actuator_kp_range=(0.6, 1.4),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan contact/dynamics randomization sensitivity.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/contact_randomization_scan.csv"))
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=80_000)
    parser.add_argument("--success-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--success-z-tolerance", type=float, default=0.01)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    return parser.parse_args()


def make_env(args: argparse.Namespace, config: ContactScanConfig) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        observation_mode="image",
        max_steps=args.max_steps,
        action_scale=args.action_scale,
        success_xy_tolerance=args.success_xy_tolerance,
        success_z_tolerance=args.success_z_tolerance,
        success_bonus=120.0,
        collision_penalty=300.0,
        progress_reward_scale=20.0,
        distance_reward_scale=2.0,
        action_alignment_scale=2.0,
        domain_randomization_level=config.level,
        contact_friction_multiplier_range=config.friction_range,
        contact_solref_time_multiplier_range=config.solref_time_range,
        contact_solref_damping_multiplier_range=config.solref_damping_range,
        contact_solimp_width_multiplier_range=config.solimp_width_range,
        dynamics_joint_damping_multiplier_range=config.joint_damping_range,
        dynamics_actuator_kp_multiplier_range=config.actuator_kp_range,
    )


def evaluate_config(args: argparse.Namespace, config: ContactScanConfig) -> dict[str, object]:
    env = make_env(args, config)
    model = SAC.load(args.model, env=env, device=args.device)
    successes = 0
    collisions = 0
    timeouts = 0
    returns: list[float] = []
    steps: list[int] = []

    try:
        for episode in range(args.episodes):
            obs, _ = env.reset(seed=args.seed + episode)
            episode_return = 0.0
            while True:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_return += reward
                if terminated or truncated:
                    break
            successes += int(info["insertion_success"])
            collisions += int(info["collision"])
            timeouts += int(truncated and not info["insertion_success"])
            returns.append(episode_return)
            steps.append(int(info["step_count"]))
    finally:
        env.close()

    return {
        "name": config.name,
        "level": config.level,
        "episodes": args.episodes,
        "success_rate": successes / args.episodes,
        "collision_rate": collisions / args.episodes,
        "timeout_rate": timeouts / args.episodes,
        "mean_return": sum(returns) / len(returns),
        "mean_steps": sum(steps) / len(steps),
        "friction_range": f"{config.friction_range[0]}:{config.friction_range[1]}",
        "solref_time_range": f"{config.solref_time_range[0]}:{config.solref_time_range[1]}",
        "solref_damping_range": f"{config.solref_damping_range[0]}:{config.solref_damping_range[1]}",
        "solimp_width_range": f"{config.solimp_width_range[0]}:{config.solimp_width_range[1]}",
        "joint_damping_range": f"{config.joint_damping_range[0]}:{config.joint_damping_range[1]}",
        "actuator_kp_range": f"{config.actuator_kp_range[0]}:{config.actuator_kp_range[1]}",
    }


def main() -> None:
    args = parse_args()
    rows = []
    for config in CONTACT_SCAN_CONFIGS:
        row = evaluate_config(args, config)
        rows.append(row)
        print(
            "{name}: success={success_rate:.3f} collision={collision_rate:.3f} "
            "timeout={timeout_rate:.3f} return={mean_return:.3f} steps={mean_steps:.1f}".format(
                **row
            )
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved scan results to {args.output}")


if __name__ == "__main__":
    main()
