# Commands

This file keeps the current recommended commands in one place. Run commands
from the repository root:

```powershell
cd D:\peg-in-hole-6yh\mujoco_peg_in_hole
```

## Install

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Quick Checks

State observation smoke test:

```powershell
python scripts\random_rollout.py --observation-mode state --episodes 3
```

Image observation smoke test:

```powershell
python scripts\random_rollout.py --observation-mode image --episodes 1
```

Current strongest randomized environment smoke test:

```powershell
python scripts\random_rollout.py --observation-mode state --episodes 1 --domain-randomization-level full_contact_light
```

## Current Best Model

```text
checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip
```

This is the delay-robust image BC model. It is currently the recommended model
for evaluation and demos.

## Reproduce Current Best Training

Collect the delay-robust expert dataset:

```powershell
python scripts\collect_image_expert_dataset.py --output datasets\image_expert_50k_sidecam_visual_camera_control_delay3_oracle.npz --samples 50000 --expert-action-gain 0.22 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 3 --control-action-filter-alpha-range 1 1 --compressed
```

Continue image actor behavior cloning:

```powershell
python scripts\pretrain_image_actor_bc.py --dataset datasets\image_expert_50k_sidecam_visual_camera_control_delay3_oracle.npz --model checkpoints_image_bc_50k_sidecam_visual_camera_control_oracle\sac_image_bc.zip --output checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --epochs 10 --batch-size 256 --learning-rate 0.000012 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

## Evaluate

Clean environment:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Default control randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control
```

High-delay control randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 3 --control-action-filter-alpha-range 1 1
```

High combined control randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 0.75 1.25 --control-action-noise-std-range 0 0.0015 --control-action-delay-range 0 3 --control-action-filter-alpha-range 0.4 1.0
```

Light geometry randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level full_light_geometry
```

Current strongest default full randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level full_contact_light
```

High contact/dynamics randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level full_contact_light --contact-friction-multiplier-range 0.5 1.5 --contact-solref-time-multiplier-range 0.6 1.6 --contact-solref-damping-multiplier-range 0.6 1.5 --contact-solimp-width-multiplier-range 0.5 1.5 --dynamics-joint-damping-multiplier-range 0.6 1.5 --dynamics-actuator-kp-multiplier-range 0.6 1.4
```

## Demo

`--width` and `--height` are the policy observation image size. Use
`--render-width` and `--render-height` to control the saved GIF resolution.
Use `--trajectory-output` to save per-step diagnostics as CSV. Use
`--render-cameras overview wrist_cam` to concatenate multiple camera views.

Recommended full-contact-light image demo:

```powershell
python scripts\demo_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --output demos\image_bc_sidecam_full_contact_light_hd.gif --width 100 --height 100 --render-width 640 --render-height 480 --fps 20 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level full_contact_light
```

Multi-camera diagnostic demo with trajectory CSV:

```powershell
python scripts\demo_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --output demos\image_bc_sidecam_full_contact_light_multicam_hd.gif --trajectory-output results\demo_full_contact_light_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level full_contact_light
```

High combined control demo:

```powershell
python scripts\demo_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --output demos\image_bc_sidecam_visual_camera_control_delay3_hd.gif --width 100 --height 100 --render-width 640 --render-height 480 --fps 20 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 0.75 1.25 --control-action-noise-std-range 0 0.0015 --control-action-delay-range 0 3 --control-action-filter-alpha-range 0.4 1.0
```

State baseline demo:

```powershell
python scripts\demo_policy.py --agent sac --observation-mode state --model checkpoints_state_tuned_v21_bc_mid\sac_state_bc.zip --output demos\state_bc_high_precision_hd.gif --render-width 640 --render-height 480 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

## Evaluation Matrix

Run the standard five-environment matrix:

```powershell
python scripts\eval_matrix.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_latest.csv --output-md results\eval_matrix_latest.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Include stress scenarios for high delay, combined control noise, and high
contact/dynamics randomization:

```powershell
python scripts\eval_matrix.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --include-stress --output-csv results\eval_matrix_stress_latest.csv --output-md results\eval_matrix_stress_latest.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

## Sensitivity Scans

Control randomization scan:

```powershell
python scripts\scan_control_randomization.py --model checkpoints_image_bc_50k_sidecam_visual_camera_control_oracle\sac_image_bc.zip --output results\control_randomization_scan.csv --episodes 50 --device cpu
```

Contact/dynamics scan:

```powershell
python scripts\scan_contact_randomization.py --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --output results\contact_randomization_scan.csv --episodes 50 --device cpu
```

## Reference Results

Current best model:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 1.000 | 0.000 |
| visual_camera_control | 0.980 | 0.010 |
| high_delay 0-3 | 0.950 | 0.020 |
| high combined control | 0.970 | 0.010 |
| full_light_geometry | 0.960 | 0.010 |
| full_contact_light | 0.970 | 0.010 |
| high full_contact_light | 0.970 | 0.010 |
