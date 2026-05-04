from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from stable_baselines3 import A2C, PPO, SAC
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import get_schedule_fn

from peg_in_hole_mujoco import PegInHoleMujocoEnv


AGENTS = {
    "sac": SAC,
    "ppo": PPO,
    "a2c": A2C,
}


MONITOR_INFO_KEYWORDS = (
    "insertion_success",
    "collision",
    "dist_xy",
    "dist_z",
)


class SuccessEvalCallback(BaseCallback):
    def __init__(
        self,
        eval_env: PegInHoleMujocoEnv,
        save_path: Path,
        eval_freq: int,
        n_eval_episodes: int,
        seed: int,
    ):
        super().__init__()
        self.eval_env = eval_env
        self.save_path = save_path
        self.eval_freq = int(eval_freq)
        self.n_eval_episodes = int(n_eval_episodes)
        self.seed = int(seed)
        self.best_success_rate = -1.0
        self.best_mean_return = -np.inf

    def _on_training_start(self) -> None:
        self._evaluate_and_save()

    def _on_step(self) -> bool:
        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            self._evaluate_and_save()
        return True

    def _on_training_end(self) -> None:
        self.eval_env.close()

    def _evaluate_and_save(self) -> None:
        successes = 0
        collisions = 0
        returns = []
        final_xy = []
        final_z = []

        for episode in range(self.n_eval_episodes):
            obs, _ = self.eval_env.reset(seed=self.seed + episode)
            episode_return = 0.0
            while True:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = self.eval_env.step(action)
                episode_return += reward
                if terminated or truncated:
                    break

            successes += int(info["insertion_success"])
            collisions += int(info["collision"])
            returns.append(episode_return)
            final_xy.append(info["dist_xy"])
            final_z.append(info["dist_z"])

        success_rate = successes / self.n_eval_episodes
        collision_rate = collisions / self.n_eval_episodes
        mean_return = float(np.mean(returns))
        mean_final_xy = float(np.mean(final_xy))
        mean_final_z = float(np.mean(final_z))

        print(
            "eval "
            f"timesteps={self.num_timesteps} "
            f"success_rate={success_rate:.3f} "
            f"collision_rate={collision_rate:.3f} "
            f"mean_return={mean_return:.3f} "
            f"mean_final_xy={mean_final_xy:.4f} "
            f"mean_final_z={mean_final_z:.4f}"
        )

        improved = (
            success_rate > self.best_success_rate
            or (
                success_rate == self.best_success_rate
                and mean_return > self.best_mean_return
            )
        )
        if improved:
            self.best_success_rate = success_rate
            self.best_mean_return = mean_return
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            self.model.save(self.save_path)
            print(f"saved new best model to {self.save_path}")


def get_tensorboard_log(log_dir: Path) -> str | None:
    try:
        import tensorboard  # noqa: F401
    except ImportError:
        print("TensorBoard is not installed; SB3 tensorboard logging is disabled.")
        print("Install it with `python -m pip install tensorboard` if you want TensorBoard logs.")
        return None
    return str(log_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train an SB3 agent on the MuJoCo peg-in-hole env.")
    parser.add_argument("--agent", choices=AGENTS.keys(), default="sac")
    parser.add_argument("--observation-mode", choices=["image", "state"], default="image")
    parser.add_argument("--total-timesteps", type=int, default=250_000)
    parser.add_argument("--save-freq", type=int, default=10_000)
    parser.add_argument("--log-dir", type=Path, default=Path("logs"))
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"))
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", type=Path, default=None)
    parser.add_argument("--warm-start-actor", type=Path, default=None)
    parser.add_argument("--domain-randomization", action="store_true")
    parser.add_argument(
        "--domain-randomization-level",
        choices=["none", "visual", "visual_camera", "visual_camera_control", "full"],
        default="none",
    )
    parser.add_argument("--eval-freq", type=int, default=5_000)
    parser.add_argument("--eval-episodes", type=int, default=20)
    parser.add_argument("--eval-seed", type=int, default=10_000)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--buffer-size", type=int, default=1_000_000)
    parser.add_argument("--learning-starts", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--train-freq", type=int, default=1)
    parser.add_argument("--gradient-steps", type=int, default=1)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--tau", type=float, default=0.005)
    parser.add_argument("--ent-coef", default="auto")
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--action-scale", type=float, default=0.005)
    parser.add_argument("--target-low", nargs=3, type=float, default=(0.50, 0.00, 0.65))
    parser.add_argument("--target-high", nargs=3, type=float, default=(0.60, 0.10, 0.65))
    parser.add_argument("--success-xy-tolerance", type=float, default=0.02)
    parser.add_argument("--success-z-tolerance", type=float, default=0.06)
    parser.add_argument("--approach-xy-tolerance", type=float, default=0.06)
    parser.add_argument("--approach-height", type=float, default=0.08)
    parser.add_argument("--staged-xy-weight", type=float, default=2.0)
    parser.add_argument("--staged-z-weight", type=float, default=1.0)
    parser.add_argument("--success-bonus", type=float, default=50.0)
    parser.add_argument("--collision-penalty", type=float, default=150.0)
    parser.add_argument("--timeout-penalty", type=float, default=10.0)
    parser.add_argument("--progress-reward-scale", type=float, default=10.0)
    parser.add_argument("--distance-reward-scale", type=float, default=1.0)
    parser.add_argument("--action-penalty-scale", type=float, default=0.002)
    parser.add_argument("--action-alignment-scale", type=float, default=0.5)
    return parser.parse_args()


def make_env(args: argparse.Namespace) -> PegInHoleMujocoEnv:
    return PegInHoleMujocoEnv(
        observation_mode=args.observation_mode,
        max_steps=args.max_steps,
        action_scale=args.action_scale,
        target_low=tuple(args.target_low),
        target_high=tuple(args.target_high),
        success_xy_tolerance=args.success_xy_tolerance,
        success_z_tolerance=args.success_z_tolerance,
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
        randomize_domain=args.domain_randomization,
        domain_randomization_level=args.domain_randomization_level,
    )


def make_model_kwargs(args: argparse.Namespace) -> dict:
    kwargs = {
        "verbose": 1,
        "device": args.device,
        "tensorboard_log": get_tensorboard_log(args.log_dir),
        "seed": args.seed,
        "learning_rate": args.learning_rate,
    }
    if args.agent == "sac":
        kwargs.update(
            {
                "buffer_size": args.buffer_size,
                "learning_starts": args.learning_starts,
                "batch_size": args.batch_size,
                "train_freq": args.train_freq,
                "gradient_steps": args.gradient_steps,
                "gamma": args.gamma,
                "tau": args.tau,
                "ent_coef": args.ent_coef,
            }
        )
    return kwargs


def main() -> None:
    args = parse_args()
    args.log_dir.mkdir(parents=True, exist_ok=True)
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    env = make_env(args)
    env = Monitor(
        env,
        str(args.log_dir / args.agent),
        info_keywords=MONITOR_INFO_KEYWORDS,
    )
    eval_env = make_env(args)

    model_class = AGENTS[args.agent]
    policy = "MultiInputPolicy" if args.observation_mode == "image" else "MlpPolicy"
    model_kwargs = make_model_kwargs(args)
    if args.resume is None:
        model = model_class(
            policy,
            env,
            **model_kwargs,
        )
        if args.warm_start_actor is not None:
            source_model = model_class.load(args.warm_start_actor, device=args.device)
            if not hasattr(model.policy, "actor") or not hasattr(source_model.policy, "actor"):
                raise ValueError("--warm-start-actor is only supported for actor-critic policies.")
            model.policy.actor.load_state_dict(source_model.policy.actor.state_dict())
            print(f"warm-started actor from {args.warm_start_actor}")
    else:
        if args.warm_start_actor is not None:
            raise ValueError("--resume and --warm-start-actor cannot be used together.")
        custom_objects = {
            "learning_rate": args.learning_rate,
            "lr_schedule": get_schedule_fn(args.learning_rate),
        }
        model = model_class.load(
            args.resume,
            env=env,
            device=args.device,
            tensorboard_log=model_kwargs["tensorboard_log"],
            custom_objects=custom_objects,
        )
        model.verbose = 1

    checkpoint_callback = CheckpointCallback(
        save_freq=args.save_freq,
        save_path=str(args.checkpoint_dir),
        name_prefix=f"{args.agent}_{args.observation_mode}_model",
    )
    success_eval_callback = SuccessEvalCallback(
        eval_env=eval_env,
        save_path=args.checkpoint_dir / f"{args.agent}_{args.observation_mode}_best",
        eval_freq=args.eval_freq,
        n_eval_episodes=args.eval_episodes,
        seed=args.eval_seed,
    )
    model.learn(
        total_timesteps=args.total_timesteps,
        callback=[checkpoint_callback, success_eval_callback],
        reset_num_timesteps=args.resume is None,
    )
    model.save(args.checkpoint_dir / f"{args.agent}_{args.observation_mode}_final")
    env.close()


if __name__ == "__main__":
    main()
