# MuJoCo Peg-in-Hole UR5 Reproduction

This project is a MuJoCo/Gymnasium reproduction of the core design in
`DRL_Peg-in-Hole_UR5`.

The first version intentionally keeps the task loop simple and inspectable:

- MuJoCo scene with a UR5-like 6-DoF arm, a fixed peg, a table, a movable hole
  fixture, and an eye-in-hand camera.
- Gymnasium API compatible with Stable-Baselines3.
- Observation modes:
  - `image`: `Dict({"cam_image": uint8[100, 100, 1]})`, matching the original
    visual input style.
  - `state`: low-dimensional debug observation for validating control/reward
    before visual training. It includes the peg tip, hole target, relative
    error, staged Cartesian target, staged relative error, and six joint angles.
- Action: continuous Cartesian tool displacement in XYZ, shape `(3,)`,
  clipped to `[-0.005, 0.005]`.
- Control: action updates the desired peg-tip position; a damped Jacobian IK
  solver maps the Cartesian target to arm joint position targets.
- Reward: dense distance reward plus a success bonus, matching the original
  project's reward shape.

## Install

Create a Python environment, then install dependencies from this folder:

```bash
python -m pip install -r requirements.txt
```

For editable package imports:

```bash
python -m pip install -e .
```

## Repository Contents

The public repository keeps the source code, MuJoCo XML asset, training/eval
scripts, dataset metadata, and small demo GIFs. Large generated files are not
tracked in Git: checkpoints, TensorBoard logs, and `.npz` expert datasets can
be regenerated with the commands below. See `ARTIFACTS.md` for the full policy.

## Quick Check

Start with the low-dimensional state mode. This avoids camera-rendering issues
while validating MuJoCo, IK, reward, reset, and termination:

```bash
python scripts/random_rollout.py --observation-mode state --episodes 3
```

Check the visual observation path:

```bash
python scripts/random_rollout.py --observation-mode image --episodes 1
```

## Train

State-mode smoke training:

```bash
python scripts/train_sac.py --agent sac --observation-mode state --total-timesteps 10000
```

State-mode curriculum baseline used during tuning:

```bash
python scripts/train_sac.py \
  --agent sac \
  --observation-mode state \
  --total-timesteps 20000 \
  --save-freq 10000 \
  --eval-freq 2000 \
  --eval-episodes 30 \
  --log-dir logs_state_tuned \
  --checkpoint-dir checkpoints_state_tuned \
  --progress-reward-scale 20 \
  --distance-reward-scale 2 \
  --action-alignment-scale 2.0 \
  --success-bonus 80
```

For the current low-dimensional state baseline, the most reliable path is to
pretrain the SAC actor from the staged Cartesian oracle after the RL curriculum:

```bash
python scripts/pretrain_actor_bc.py \
  --model checkpoints_state_tuned_v16_mid_tolerance/sac_state_best.zip \
  --output checkpoints_state_tuned_v21_bc_mid/sac_state_bc.zip \
  --samples 30000 \
  --epochs 10 \
  --success-xy-tolerance 0.015 \
  --success-z-tolerance 0.045
```

This is intentionally a state-space debugging baseline. It verifies that the
MuJoCo task, IK, action interface, and staged insertion logic are solvable
before moving to image observations.

Image-mode training, closer to the original project:

```bash
python scripts/train_sac.py --agent sac --observation-mode image --total-timesteps 250000
```

The image baseline should not start from raw SAC. First collect wrist-camera
expert data and behavior-clone the image actor:

```bash
python scripts/collect_image_expert_dataset.py \
  --output datasets/image_expert_5k_sidecam_oracle.npz \
  --samples 5000 \
  --rollout-noise-std 0.0005 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01 \
  --compressed
```

```bash
python scripts/pretrain_image_actor_bc.py \
  --dataset datasets/image_expert_5k_sidecam_oracle.npz \
  --output checkpoints_image_bc_5k_sidecam_oracle/sac_image_bc.zip \
  --epochs 10 \
  --batch-size 128 \
  --learning-rate 0.0001 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01
```

If validation loss is still falling, continue from that image model:

```bash
python scripts/pretrain_image_actor_bc.py \
  --dataset datasets/image_expert_5k_sidecam_oracle.npz \
  --model checkpoints_image_bc_5k_sidecam_oracle/sac_image_bc.zip \
  --output checkpoints_image_bc_5k_sidecam_oracle_e30/sac_image_bc.zip \
  --epochs 20 \
  --batch-size 128 \
  --learning-rate 0.00005 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01
```

Current image BC baseline:

- Clean model: `checkpoints_image_bc_50k_sidecam_oracle/sac_image_bc.zip`
- Clean dataset: `datasets/image_expert_50k_sidecam_oracle.npz`
- Basic visual DR model:
  `checkpoints_image_bc_50k_sidecam_dr_oracle/sac_image_bc.zip`
- Basic visual DR dataset:
  `datasets/image_expert_50k_sidecam_dr_oracle.npz`
- Visual+camera DR model:
  `checkpoints_image_bc_50k_sidecam_visual_camera_oracle_e20/sac_image_bc.zip`
- Visual+camera DR dataset:
  `datasets/image_expert_50k_sidecam_visual_camera_oracle.npz`
- Visual+camera+control DR model:
  `checkpoints_image_bc_50k_sidecam_visual_camera_control_oracle/sac_image_bc.zip`
- Visual+camera+control DR dataset:
  `datasets/image_expert_50k_sidecam_visual_camera_control_oracle.npz`
- Delay-robust visual+camera+control DR model:
  `checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle/sac_image_bc.zip`
- Delay-robust visual+camera+control DR dataset:
  `datasets/image_expert_50k_sidecam_visual_camera_control_delay3_oracle.npz`
- Wrist camera: side-mounted `100x100` grayscale view.
- Evaluation threshold: `success_xy_tolerance=0.005`,
  `success_z_tolerance=0.01`
- Clean model, clean env, 100 evaluation episodes:
  `1.000` success rate, `0.000` collision rate.
- Basic visual DR model, clean env, 100 evaluation episodes:
  `1.000` success rate, `0.000` collision rate.
- Basic visual DR model, basic visual DR env, 100 evaluation episodes:
  `0.940` success rate, `0.030` collision rate.
- Basic visual DR model, visual+camera DR env, 100 evaluation episodes:
  `0.540` success rate, `0.060` collision rate.
- Visual+camera DR model, clean env, 100 evaluation episodes:
  `1.000` success rate, `0.000` collision rate.
- Visual+camera DR model, visual+camera DR env, 100 evaluation episodes:
  `0.950` success rate, `0.030` collision rate.
- Visual+camera DR model, visual+camera+control DR env, 100 evaluation episodes:
  `0.670` success rate, `0.100` collision rate.
- Visual+camera+control DR model, clean env, 100 evaluation episodes:
  `1.000` success rate, `0.000` collision rate.
- Visual+camera+control DR model, visual DR env, 100 evaluation episodes:
  `0.980` success rate, `0.010` collision rate.
- Visual+camera+control DR model, visual+camera DR env, 100 evaluation episodes:
  `0.970` success rate, `0.010` collision rate.
- Visual+camera+control DR model, visual+camera+control DR env,
  100 evaluation episodes: `0.920` success rate, `0.020` collision rate.
- Delay-robust model, clean env, 100 evaluation episodes:
  `1.000` success rate, `0.000` collision rate.
- Delay-robust model, default visual+camera+control DR env,
  100 evaluation episodes: `0.980` success rate, `0.010` collision rate.
- Delay-robust model, high-delay `0-3` env, 100 evaluation episodes:
  `0.950` success rate, `0.020` collision rate.
- Delay-robust model, high combined control DR env, 100 evaluation episodes:
  `0.970` success rate, `0.010` collision rate.

Domain randomization levels:

- `none`: deterministic visual/camera setup.
- `visual`: randomizes table, peg, hole colors, and light diffuse color.
- `visual_camera`: `visual` plus wrist-camera pose jitter and image brightness,
  contrast, and Gaussian noise.
- `visual_camera_control`: `visual_camera` plus per-episode action scale jitter,
  action execution noise, 0-2 step action delay, and low-pass action filtering.
- `full`: reserved for adding dynamics and contact randomization.

Train the domain-randomized image BC baseline:

```bash
python scripts/collect_image_expert_dataset.py \
  --output datasets/image_expert_50k_sidecam_dr_oracle.npz \
  --samples 50000 \
  --rollout-noise-std 0.0005 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01 \
  --domain-randomization \
  --compressed
```

```bash
python scripts/pretrain_image_actor_bc.py \
  --dataset datasets/image_expert_50k_sidecam_dr_oracle.npz \
  --model checkpoints_image_bc_50k_sidecam_oracle/sac_image_bc.zip \
  --output checkpoints_image_bc_50k_sidecam_dr_oracle/sac_image_bc.zip \
  --epochs 10 \
  --batch-size 256 \
  --learning-rate 0.00003 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01
```

Train the stronger visual+camera DR baseline:

```bash
python scripts/collect_image_expert_dataset.py \
  --output datasets/image_expert_50k_sidecam_visual_camera_oracle.npz \
  --samples 50000 \
  --rollout-noise-std 0.0005 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01 \
  --domain-randomization-level visual_camera \
  --compressed
```

```bash
python scripts/pretrain_image_actor_bc.py \
  --dataset datasets/image_expert_50k_sidecam_visual_camera_oracle.npz \
  --model checkpoints_image_bc_50k_sidecam_dr_oracle/sac_image_bc.zip \
  --output checkpoints_image_bc_50k_sidecam_visual_camera_oracle/sac_image_bc.zip \
  --epochs 10 \
  --batch-size 256 \
  --learning-rate 0.00003 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01
```

If validation loss is still falling, continue with a smaller learning rate:

```bash
python scripts/pretrain_image_actor_bc.py \
  --dataset datasets/image_expert_50k_sidecam_visual_camera_oracle.npz \
  --model checkpoints_image_bc_50k_sidecam_visual_camera_oracle/sac_image_bc.zip \
  --output checkpoints_image_bc_50k_sidecam_visual_camera_oracle_e20/sac_image_bc.zip \
  --epochs 10 \
  --batch-size 256 \
  --learning-rate 0.000015 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01
```

Evaluate the visual+camera randomized baseline:

```bash
python scripts/eval_policy.py \
  --agent sac \
  --observation-mode image \
  --model checkpoints_image_bc_50k_sidecam_visual_camera_oracle_e20/sac_image_bc.zip \
  --episodes 100 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01 \
  --domain-randomization-level visual_camera
```

Train the visual+camera+control DR baseline:

```bash
python scripts/collect_image_expert_dataset.py \
  --output datasets/image_expert_50k_sidecam_visual_camera_control_oracle.npz \
  --samples 50000 \
  --expert-action-gain 0.25 \
  --rollout-noise-std 0.0005 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01 \
  --domain-randomization-level visual_camera_control \
  --compressed
```

```bash
python scripts/pretrain_image_actor_bc.py \
  --dataset datasets/image_expert_50k_sidecam_visual_camera_control_oracle.npz \
  --model checkpoints_image_bc_50k_sidecam_visual_camera_oracle_e20/sac_image_bc.zip \
  --output checkpoints_image_bc_50k_sidecam_visual_camera_control_oracle/sac_image_bc.zip \
  --epochs 10 \
  --batch-size 256 \
  --learning-rate 0.000015 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01
```

Evaluate the control-randomized baseline:

```bash
python scripts/eval_policy.py \
  --agent sac \
  --observation-mode image \
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_oracle/sac_image_bc.zip \
  --episodes 100 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01 \
  --domain-randomization-level visual_camera_control
```

Train the delay-robust control baseline:

```bash
python scripts/collect_image_expert_dataset.py \
  --output datasets/image_expert_50k_sidecam_visual_camera_control_delay3_oracle.npz \
  --samples 50000 \
  --expert-action-gain 0.22 \
  --rollout-noise-std 0.0005 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01 \
  --domain-randomization-level visual_camera_control \
  --control-action-scale-range 1 1 \
  --control-action-noise-std-range 0 0 \
  --control-action-delay-range 0 3 \
  --control-action-filter-alpha-range 1 1 \
  --compressed
```

```bash
python scripts/pretrain_image_actor_bc.py \
  --dataset datasets/image_expert_50k_sidecam_visual_camera_control_delay3_oracle.npz \
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_oracle/sac_image_bc.zip \
  --output checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle/sac_image_bc.zip \
  --epochs 10 \
  --batch-size 256 \
  --learning-rate 0.000012 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01
```

Evaluate the delay-robust model under high combined control randomization:

```bash
python scripts/eval_policy.py \
  --agent sac \
  --observation-mode image \
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle/sac_image_bc.zip \
  --episodes 100 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01 \
  --domain-randomization-level visual_camera_control \
  --control-action-scale-range 0.75 1.25 \
  --control-action-noise-std-range 0 0.0015 \
  --control-action-delay-range 0 3 \
  --control-action-filter-alpha-range 0.4 1.0
```

Run the control-randomization sensitivity scan:

```bash
python scripts/scan_control_randomization.py \
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_oracle/sac_image_bc.zip \
  --output results/control_randomization_scan.csv \
  --episodes 50 \
  --device cpu
```

Current scan summary:

- Default control randomization, 100 episodes: `0.920` success rate,
  `0.020` collision rate.
- High delay only, `0-3` control steps, 100 episodes: `0.850` success rate,
  `0.020` collision rate.
- High combined control randomization, 100 episodes: `0.820` success rate,
  `0.080` collision rate.
- Main bottleneck: action delay. See `results/control_randomization_scan.md`.
- After delay-robust BC, high-delay `0-3` improves from `0.850` to `0.950`
  success rate, and high combined control randomization improves from `0.820`
  to `0.970` success rate.

Enable basic visual domain randomization for sim-to-real experiments:

```bash
python scripts/train_sac.py --agent sac --observation-mode image --domain-randomization-level visual
```

## Evaluate

```bash
python scripts/eval_policy.py \
  --agent sac \
  --observation-mode state \
  --model checkpoints_state_tuned_v21_bc_mid/sac_state_bc.zip \
  --episodes 100 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01
```

Render a policy demo:

```bash
python scripts/demo_policy.py \
  --agent sac \
  --observation-mode state \
  --model checkpoints_state_tuned_v21_bc_mid/sac_state_bc.zip \
  --output demos/state_bc_high_precision.gif \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01
```

For an image policy, keep the demo observation size at the model's training
size, currently `100x100`:

```bash
python scripts/demo_policy.py \
  --agent sac \
  --observation-mode image \
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle/sac_image_bc.zip \
  --output demos/image_bc_sidecam_visual_camera_control_delay3.gif \
  --width 100 \
  --height 100 \
  --success-xy-tolerance 0.005 \
  --success-z-tolerance 0.01 \
  --domain-randomization-level visual_camera_control \
  --control-action-scale-range 0.75 1.25 \
  --control-action-noise-std-range 0 0.0015 \
  --control-action-delay-range 0 3 \
  --control-action-filter-alpha-range 0.4 1.0
```

Current checked result for the state behavior-cloned baseline:

- `success_xy_tolerance=0.005`, `success_z_tolerance=0.01`
- 100 evaluation episodes
- Success rate: `1.000`
- Collision rate: `0.000`

Current checked result for the visual+camera image BC baseline:

- `success_xy_tolerance=0.005`, `success_z_tolerance=0.01`
- 100 clean evaluation episodes: `1.000` success rate, `0.000` collision rate.
- 100 `visual_camera` evaluation episodes: `0.950` success rate,
  `0.030` collision rate.

Current checked result for the visual+camera+control image BC baseline:

- Dataset collection with `expert_action_gain=0.25`: `0.998` success rate,
  `0.002` collision rate across 2062 expert episodes.
- 100 clean evaluation episodes: `1.000` success rate, `0.000` collision rate.
- 100 `visual` evaluation episodes: `0.980` success rate,
  `0.010` collision rate.
- 100 `visual_camera` evaluation episodes: `0.970` success rate,
  `0.010` collision rate.
- 100 `visual_camera_control` evaluation episodes: `0.920` success rate,
  `0.020` collision rate.

Current checked result for the delay-robust visual+camera+control baseline:

- Dataset collection with `expert_action_gain=0.22` and `delay=0-3`:
  `0.993` success rate, `0.007` collision rate across 1977 expert episodes.
- 100 clean evaluation episodes: `1.000` success rate, `0.000` collision rate.
- 100 default `visual_camera_control` episodes: `0.980` success rate,
  `0.010` collision rate.
- 100 high-delay `0-3` episodes: `0.950` success rate,
  `0.020` collision rate.
- 100 high combined control randomization episodes: `0.970` success rate,
  `0.010` collision rate.

## Important Design Notes

This is a reproducible MuJoCo baseline, not yet a high-fidelity UR5 digital
twin. The included MJCF uses primitive geometry and approximate UR5 kinematics
so the RL task can run independently from PyBullet/CoppeliaSim assets.

For sim-to-real work, the next steps should be:

1. Replace `assets/ur5_peg_in_hole.xml` with a calibrated UR5 MJCF.
2. Match the real end-effector frame, peg length/radius, camera intrinsics, and
   camera-to-tool transform.
3. Use the same action interface in sim and real: small Cartesian displacement
   or Cartesian velocity commands.
4. Expand domain randomization: lighting, textures, camera pose/noise, peg/hole
   tolerance, friction, joint damping, latency, and controller gains.
5. Tighten success detection from point-distance to insertion depth, peg axis
   alignment, and contact state.
