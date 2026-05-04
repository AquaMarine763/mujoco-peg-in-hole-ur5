# Artifact Policy

This repository tracks the reproducible MuJoCo environment, scripts, assets,
documentation, small metadata files, and demo GIFs.

Large generated artifacts are intentionally not committed:

- `checkpoints*/`: Stable-Baselines3 model checkpoints and cloned actor models.
- `logs*/`: TensorBoard and training logs.
- `datasets/*.npz`: image expert datasets, including 50k-sample runs.
- `debug/`, `.tmp/`, `.deps/`: local scratch and dependency caches.

The JSON files under `datasets/` are small run metadata records and are kept so
the dataset settings remain inspectable.

To reproduce the current strongest image baseline, regenerate the
visual+camera+control dataset and behavior-cloned model:

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
