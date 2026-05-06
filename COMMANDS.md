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

## Robot Model Compatibility / UR5e Adapter

The default simulator still uses the simplified UR5-like model at
`assets\ur5_peg_in_hole.xml`. A lightweight UR5e adapter is available at
`assets\ur5e_adapter\ur5e_peg_in_hole.xml`. It is derived from the DeepMind
MuJoCo Menagerie UR5e model and keeps the UR5e joint chain, inertials,
actuator style, and simplified collision geoms without vendoring large visual
mesh assets.

Check that the default model exposes the task interface names used by the
environment:

```powershell
python scripts\inspect_robot_model.py --model-path assets\ur5_peg_in_hole.xml --output-md results\robot_model_current.md --fail-on-missing
```

Check the UR5e adapter:

```powershell
python scripts\inspect_robot_model.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-md results\robot_model_ur5e_adapter.md --fail-on-missing
```

Smoke-test the UR5e adapter through reset, IK, stepping, and rendering. Random
actions are not expected to succeed; use the oracle command to verify that the
model can complete the task:

```powershell
python scripts\random_rollout.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --observation-mode state --episodes 1
python scripts\random_rollout.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --observation-mode image --episodes 1
python scripts\oracle_rollout.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --observation-mode state --episodes 3
```

All main environment scripts accept the same override:

```powershell
--model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml
```

## UR5e Adapter Fixed-Camera Baselines

The usable UR5e adapter image baselines use the fixed wrist-camera pose
in `assets\ur5e_adapter\ur5e_peg_in_hole.xml` and trains from scratch. Starting
from the old side-camera policy was tested and gave poor clean performance
because it kept an early-descent bias.

Recommended 50k fixed-camera oracle dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz --samples 50000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --compressed
```

Train the recommended 50k scratch image BC model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz --output checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip --epochs 30 --batch-size 512 --learning-rate 0.0001 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render the recommended 50k model:

```powershell
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_50k_scratch.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_50k_scratch.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_fixedcam_50k_scratch_hd.gif --trajectory-output results\demo_ur5e_adapter_fixedcam_50k_scratch_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Fast 5k smoke dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_5k_oracle.npz --samples 5000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --compressed
```

Train the 5k smoke model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_5k_oracle.npz --output checkpoints_image_bc_ur5e_adapter_fixedcam_5k_scratch\sac_image_bc.zip --epochs 50 --batch-size 256 --learning-rate 0.0001 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render the 5k smoke model:

```powershell
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_5k_scratch\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_5k_scratch\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_fixedcam_5k_scratch_hd.gif --trajectory-output results\demo_ur5e_adapter_fixedcam_5k_scratch_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current UR5e fixedcam results:

| Model | Episodes | Success | Collision |
| --- | ---: | ---: | ---: |
| `checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip` | 100 clean eval_policy | 1.000 | 0.000 |
| `checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip` | 100 clean eval_matrix | 0.950 | 0.050 |
| `checkpoints_image_bc_ur5e_adapter_fixedcam_5k_scratch\sac_image_bc.zip` | 100 clean | 0.790 | 0.200 |

The 50k clean baseline is strong, but the same model is not yet robust to
visual/camera/control randomization. See
`results\eval_matrix_ur5e_adapter_fixedcam_50k_scratch.md`.

## UR5e Adapter Visual-Camera Baseline

The current recommended UR5e visual-camera baseline is trained on a mixed
dataset: 50k clean fixed-camera oracle samples plus 100k `visual_camera`
randomized oracle samples.

Current recommended model:

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip
```

Collect the visual-camera oracle dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_oracle.npz --samples 50000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera --compressed
```

Merge clean and visual-camera datasets:

```powershell
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle.npz --compressed
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle.npz --compressed
```

Train from the clean 50k model, then continue with a lower learning rate:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle\sac_image_bc.zip --epochs 20 --batch-size 512 --learning-rate 0.00003 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35\sac_image_bc.zip --epochs 15 --batch-size 512 --learning-rate 0.00001 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip --epochs 20 --batch-size 512 --learning-rate 0.00001 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render the visual-camera model:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_100k_e35_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_100k_e35_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_150k_e20_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_150k_e20_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current visual-camera result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean e35 | 0.960 | 0.040 |
| visual_camera e35 | 0.660 | 0.340 |
| visual_camera_control e35 | 0.440 | 0.560 |
| clean e20 | 0.960 | 0.040 |
| visual_camera e20 | 0.810 | 0.190 |
| visual_camera_control e20 | 0.480 | 0.520 |
| full_light_geometry e20 | 0.140 | 0.840 |
| full_contact_light e20 | 0.140 | 0.840 |

The next UR5e step should improve visual-camera robustness before moving to
control or contact randomization. The current failure mode is still collision
under image/camera perturbations.

## UR5e Adapter Mild Control Baseline

Default `visual_camera_control` data collection was tested first, but the
oracle only reached `0.910` success and `0.089` collision. For the first
control-stage baseline, use a milder control randomization range:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_mild_50k_oracle.npz --samples 50000 --seed 190000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 0.9 1.1 --control-action-noise-std-range 0 0.0004 --control-action-delay-range 0 1 --control-action-filter-alpha-range 0.75 1.0 --compressed
```

Merge clean, visual-camera, and mild-control data:

```powershell
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_mild_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle.npz --compressed
```

Continue from the 150k visual-camera model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip --epochs 20 --batch-size 512 --learning-rate 0.00001 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_control_mild_200k_e20_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_control_mild_200k_e20_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current mild-control result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 0.930 | 0.070 |
| visual_camera | 0.920 | 0.080 |
| visual_camera_control | 0.600 | 0.400 |
| full_light_geometry | 0.200 | 0.790 |
| full_contact_light | 0.200 | 0.770 |

This is a useful control-stage improvement, not the final control-robust
policy.

## UR5e Adapter Success-Only Control Baseline

The next control-stage baseline targets the default `visual_camera_control`
range directly. The key change is `--success-only`: failed/collision oracle
episodes are used for diagnostics but are not written into the BC dataset.

First confirm which control component is limiting the mild-control model:

```powershell
python scripts\scan_control_randomization.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip --output results\control_randomization_scan_ur5e_mild_200k_e20.csv --episodes 30 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

The scan shows that delay is the main weak point. Then scan oracle gains under
default control randomization:

```powershell
python scripts\scan_oracle_control_gain.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\oracle_control_gain_scan_ur5e_default_control.csv --output-md results\oracle_control_gain_scan_ur5e_default_control.md --episodes 100 --gains 1.0 0.7 0.5 0.35 0.25 0.18 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

For UR5e default control, `gain=1.0` remains best:

| Oracle gain | Success | Collision |
| ---: | ---: | ---: |
| 1.000 | 0.910 | 0.090 |
| 0.700 | 0.890 | 0.110 |
| 0.500 | 0.840 | 0.160 |
| 0.350 | 0.660 | 0.340 |
| 0.250 | 0.230 | 0.770 |
| 0.180 | 0.030 | 0.970 |

Collect default-control success-only data:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz --samples 50000 --seed 260000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --success-only --compressed
```

Merge clean, visual-camera, mild-control, and success-only default-control data:

```powershell
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_mild_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle.npz --compressed
```

Continue from the mild-control model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15\sac_image_bc.zip --epochs 15 --batch-size 512 --learning-rate 0.000008 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_control_success_250k_e15_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_control_success_250k_e15_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current success-only control result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 0.950 | 0.050 |
| visual_camera | 0.910 | 0.090 |
| visual_camera_control | 0.730 | 0.270 |
| full_light_geometry | 0.250 | 0.730 |
| full_contact_light | 0.270 | 0.690 |

This reaches the previous target of default `visual_camera_control >= 0.70`.

## UR5e Adapter Delay-Filter Success Baseline

The 250k success-only model still had a delay/filter weakness. Add one focused
success-only batch with scale and noise disabled, then add one more default
control success-only batch:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay_filter_success_50k_oracle.npz --samples 50000 --seed 310000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 2 --control-action-filter-alpha-range 0.55 1.0 --success-only --compressed
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay_filter_success_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle.npz --compressed
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle_e10\sac_image_bc.zip --epochs 10 --batch-size 512 --learning-rate 0.000006 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_seed330k_oracle.npz --samples 50000 --seed 330000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --success-only --compressed
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_seed330k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz --compressed
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle_e10\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --epochs 8 --batch-size 512 --learning-rate 0.000005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render the current recommended UR5e model:

```powershell
python scripts\scan_control_randomization.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --output results\control_randomization_scan_ur5e_delay_filter_success_350k_e8.csv --episodes 30 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_control_delay_filter_success_350k_e8_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_control_delay_filter_success_350k_e8_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current delay-filter success result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 0.990 | 0.010 |
| visual_camera | 0.930 | 0.070 |
| visual_camera_control | 0.860 | 0.140 |
| full_light_geometry | 0.290 | 0.670 |
| full_contact_light | 0.270 | 0.680 |

Analyze the remaining `visual_camera_control` failures before collecting the
next dataset:

```powershell
python scripts\analyze_control_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --episodes 200 --output-csv results\control_failure_analysis_ur5e_delay_filter_success_350k_e8.csv --output-md results\control_failure_analysis_ur5e_delay_filter_success_350k_e8.md --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Control failure analysis result:

| Bucket | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| overall | 200 | 0.830 | 0.165 | 0.005 |
| delay_2 | 72 | 0.764 | 0.236 | 0.000 |
| delay_1 | 63 | 0.794 | 0.190 | 0.016 |
| delay_0 | 65 | 0.938 | 0.062 | 0.000 |
| filter low <0.70 | 62 | 0.790 | 0.210 | 0.000 |
| scale low <0.90 | 43 | 0.721 | 0.279 | 0.000 |
| noise high >=0.00055 | 50 | 0.820 | 0.180 | 0.000 |

The next control dataset should bias toward `delay=2`, low filter alpha
`0.55-0.70`, low action scale `0.8-0.9`, and high noise
`0.00055-0.0008`. This is still a control-randomization problem; full
geometry/contact randomization should wait until default `visual_camera_control`
is closer to `0.90`.

## UR5e Adapter Hard-Control Weighted Baseline

Collect the hard-control success-only dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz --samples 50000 --seed 360000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 0.8 0.9 --control-action-noise-std-range 0.00055 0.0008 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --success-only --compressed
```

The hard-control oracle reached only `0.771` success and `0.229` collision, so
this data is useful as a targeted stress bucket, not as a standalone policy
distribution. First train a single-copy 400k model:

```powershell
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_success_400k_oracle.npz --compressed
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_success_400k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_success_400k_oracle_e6\sac_image_bc.zip --epochs 6 --batch-size 512 --learning-rate 0.000004 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Then train a hard-weighted 500k model by repeating the hard-control 50k dataset
three times:

```powershell
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle.npz --compressed
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_success_400k_oracle_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --epochs 5 --batch-size 512 --learning-rate 0.000003 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render the hard-weighted model:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\analyze_control_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --episodes 100 --output-csv results\control_failure_analysis_ur5e_hard_weighted_500k_e5_hard_control.csv --output-md results\control_failure_analysis_ur5e_hard_weighted_500k_e5_hard_control.md --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --control-action-scale-range 0.8 0.9 --control-action-noise-std-range 0.00055 0.0008 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70
python scripts\analyze_control_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --episodes 200 --output-csv results\control_failure_analysis_ur5e_hard_weighted_500k_e5.csv --output-md results\control_failure_analysis_ur5e_hard_weighted_500k_e5.md --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_control_hard_weighted_500k_e5_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_control_hard_weighted_500k_e5_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current hard-weighted result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 0.960 | 0.040 |
| visual_camera | 0.990 | 0.010 |
| visual_camera_control | 0.890 | 0.110 |
| hard-control fixed bucket | 0.770 | 0.230 |
| full_light_geometry | 0.300 | 0.660 |
| full_contact_light | 0.310 | 0.660 |

This version improves default control and hard-control robustness, but trades
off some clean performance compared with the 350k model. It is the current
control-robust recommendation; use the 350k model if the immediate goal is the
highest clean score.

## UR5e Adapter Balanced Weighted BC Trial

The 500k hard-weighted model improves control robustness but lowers clean
success to `0.960`. A balanced weighted BC trial can train from several source
datasets without materializing another merged `.npz`:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz --dataset-weights 0.55 0.18 0.12 0.05 0.10 --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_balanced_weighted_550k_oracle_e6\sac_image_bc.zip --epochs 6 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Balanced weighted result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 0.980 | 0.020 |
| visual_camera | 0.980 | 0.020 |
| visual_camera_control | 0.890 | 0.110 |
| hard-control fixed bucket | 0.740 | 0.260 |
| full_light_geometry | 0.310 | 0.660 |
| full_contact_light | 0.300 | 0.670 |

This trial recovers clean performance but does not improve default
`visual_camera_control` beyond the hard-weighted model. It is a useful
alternative if clean robustness matters more than the fixed hard-control bucket.

Safety filtering was also checked with the deployment-style inference path:

```powershell
python scripts\run_policy_inference.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --episodes 100 --output results\policy_inference_ur5e_hard_weighted_500k_e5_alpha08_trace.csv --device cpu --seed 90000 --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --safety-action-filter-alpha 0.8
python scripts\run_policy_inference.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --episodes 100 --output results\policy_inference_ur5e_hard_weighted_500k_e5_alpha06_trace.csv --device cpu --seed 90000 --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --safety-action-filter-alpha 0.6
```

The action filter did not improve success: `alpha=0.8` reached `0.870`, and
`alpha=0.6` reached `0.860`.

## Hole Geometry Curriculum Scan

Before collecting narrowed-hole data, scan the staged oracle over fixed hole
sizes:

```powershell
python scripts\scan_hole_geometry_oracle.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\hole_geometry_oracle_scan_ur5e_adapter.csv --output-md results\hole_geometry_oracle_scan_ur5e_adapter.md --episodes 50 --hole-half-sizes 0.045 0.029 0.025 0.020 0.017 0.015 --peg-radii 0.012 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\scan_hole_geometry_oracle.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\hole_geometry_oracle_scan_ur5e_adapter_approach02.csv --output-md results\hole_geometry_oracle_scan_ur5e_adapter_approach02.md --episodes 50 --hole-half-sizes 0.045 0.029 0.025 0.020 0.017 0.015 --peg-radii 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Default approach `0.06` is too aggressive for narrowed holes:

| Hole half-size | Clearance | Success | Collision |
| ---: | ---: | ---: | ---: |
| 0.045 | 0.033 | 1.000 | 0.000 |
| 0.029 | 0.017 | 0.860 | 0.120 |
| 0.025 | 0.013 | 0.800 | 0.200 |
| 0.020 | 0.008 | 0.720 | 0.280 |
| 0.017 | 0.005 | 0.640 | 0.320 |
| 0.015 | 0.003 | 0.500 | 0.480 |

With `approach_xy_tolerance=0.02`, the oracle becomes stable down to
hole half-size `0.020`:

| Hole half-size | Clearance | Success | Collision |
| ---: | ---: | ---: | ---: |
| 0.045 | 0.033 | 1.000 | 0.000 |
| 0.029 | 0.017 | 1.000 | 0.000 |
| 0.025 | 0.013 | 1.000 | 0.000 |
| 0.020 | 0.008 | 1.000 | 0.000 |
| 0.017 | 0.005 | 0.800 | 0.040 |
| 0.015 | 0.003 | 0.680 | 0.180 |

Recommended next geometry-curriculum range: start with
`geometry_hole_half_size_range 0.020 0.025`, `geometry_peg_radius_range 0.012
0.012`, and `approach_xy_tolerance 0.02`. Do not start at `0.017` or tighter
until the oracle itself is improved.

## Narrow Geometry Curriculum Attempt

Collect the first success-only narrowed-hole dataset. This keeps control
execution exact so the first geometry batch isolates hole-size difficulty:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --samples 50000 --seed 520000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.020 0.025 --geometry-peg-radius-range 0.012 0.012 --success-only --compressed
```

Observed oracle collection result:

| Samples | Episodes | Success | Collision |
| ---: | ---: | ---: | ---: |
| 50000 | 3474 | 0.996 | 0.004 |

Weighted continuation from the balanced model:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.45 0.12 0.10 0.05 0.08 0.20 --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_balanced_weighted_550k_oracle_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6\sac_image_bc.zip --epochs 6 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Narrow-only continuation used as an upper-bound diagnostic:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_balanced_weighted_550k_oracle_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_narrow_only_50k_oracle_e12\sac_image_bc.zip --epochs 12 --batch-size 512 --learning-rate 0.000002 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the weighted continuation on the standard matrix:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate the exact target narrow-geometry bucket:

```powershell
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6\sac_image_bc.zip --episodes 100 --device cpu --seed 610000 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.020 0.025 --geometry-peg-radius-range 0.012 0.012 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current result summary:

| Model | Target narrow geometry | Clean | Visual camera control | Full light geometry |
| --- | ---: | ---: | ---: | ---: |
| balanced 550k | 0.210 | 0.980 | 0.890 | 0.310 |
| weighted narrow 600k | 0.340 | 0.950 | 0.850 | 0.350 |
| narrow-only 50k | 0.450 | 0.820 | 0.580 | 0.360 |

The narrow data is useful, but this is not a new recommended policy yet. The
next iteration should add an intermediate geometry range and/or improve
near-hole visual alignment, instead of just increasing narrow-only BC weight.
Full details are in `results\geometry_curriculum_narrow_summary.md`.

## Resolution A/B For Intermediate Geometry

This test checks whether directly increasing the full wrist-camera image from
`100x100` to `128x128` helps near-hole geometry. It uses scratch BC models so
the input shapes are comparable without checkpoint migration.

Collect the 100x100 intermediate-geometry dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_20k_100_oracle.npz --samples 20000 --seed 630000 --image-width 100 --image-height 100 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --success-only --compressed
```

Collect the 128x128 intermediate-geometry dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_20k_128_oracle.npz --samples 20000 --seed 630001 --image-width 128 --image-height 128 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --success-only --compressed
```

Train the 100x100 scratch BC model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_20k_100_oracle.npz --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_20k_100_scratch_e30\sac_image_bc.zip --epochs 30 --batch-size 512 --learning-rate 0.0001 --image-width 100 --image-height 100 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Train the 128x128 scratch BC model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_20k_128_oracle.npz --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_20k_128_scratch_e30\sac_image_bc.zip --epochs 30 --batch-size 512 --learning-rate 0.0001 --image-width 128 --image-height 128 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the target intermediate geometry bucket:

```powershell
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_20k_100_scratch_e30\sac_image_bc.zip --episodes 100 --device cpu --seed 650000 --width 100 --height 100 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_20k_128_scratch_e30\sac_image_bc.zip --episodes 100 --device cpu --seed 650000 --width 128 --height 128 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current A/B result:

| Scenario | 100x100 | 128x128 |
| --- | ---: | ---: |
| BC final validation loss | 0.164 | 0.132 |
| Intermediate geometry success | 0.880 | 0.860 |
| Narrow geometry success | 0.750 | 0.720 |
| Clean success | 0.670 | 0.180 |

The lower 128x128 BC loss did not improve rollout success. Do not switch the
mainline to 128x128 yet; prefer staged geometry curriculum or a targeted
near-hole crop. Full details are in
`results\resolution_ab_intermediate_geometry_summary.md`.

## Staged Geometry Curriculum

Collect a 50k intermediate-geometry dataset at the current `100x100`
resolution:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz --samples 50000 --seed 680000 --image-width 100 --image-height 100 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --success-only --compressed
```

Observed collection result:

| Samples | Episodes | Oracle success | Oracle collision |
| ---: | ---: | ---: | ---: |
| 50000 | 3214 | 0.996 | 0.000 |

Stage 1: add intermediate geometry while replaying clean/control data:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz --dataset-weights 0.45 0.12 0.10 0.05 0.08 0.20 --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_balanced_weighted_550k_oracle_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_600k_oracle_e6\sac_image_bc.zip --epochs 6 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Stage 2: add low-weight narrow geometry on top of the intermediate model:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.42 0.12 0.10 0.05 0.08 0.15 0.08 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_600k_oracle_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip --epochs 5 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.0000015 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the staged model:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current staged curriculum result:

| Model | Intermediate bucket | Narrow bucket | Clean | Visual camera control | Full light geometry |
| --- | ---: | ---: | ---: | ---: | ---: |
| balanced 550k | 0.310 | 0.180 | 0.980 | 0.890 | 0.310 |
| intermediate 600k | 0.450 | 0.290 | 0.950 | 0.870 | 0.370 |
| staged intermediate+narrow 650k | 0.510 | 0.330 | 0.960 | 0.850 | 0.390 |

The staged model is the best geometry-curriculum candidate so far, but it is
not a replacement for the current control-focused model because default
`visual_camera_control` drops to `0.850`. Full details are in
`results\geometry_curriculum_staged_summary.md`.

## Near-Hole Crop Observation

The near-hole crop adds a second image key:

```text
cam_image: 100x100x1
near_hole_crop: 64x64x1
```

Existing `.npz` datasets can be reused. If `near_hole_crops` is not stored in a
dataset, the BC trainer derives it from `cam_images` when
`--include-near-hole-crop` is passed.

Analyze no-crop geometry failures:

```powershell
python scripts\analyze_geometry_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip --episodes 100 --seed 730000 --output-csv results\geometry_failure_analysis_staged_650k_intermediate.csv --output-md results\geometry_failure_analysis_staged_650k_intermediate.md --device cpu --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\analyze_geometry_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip --episodes 100 --seed 740000 --output-csv results\geometry_failure_analysis_staged_650k_narrow.csv --output-md results\geometry_failure_analysis_staged_650k_narrow.md --device cpu --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.020 0.025 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Train the crop model. The first low-learning-rate scratch run underfit, but it
is the checkpoint used by the continued `e16` run:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.40 0.12 0.08 0.05 0.08 0.15 0.12 --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e6\sac_image_bc.zip --epochs 6 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Continue with the effective higher learning rate:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.40 0.12 0.08 0.05 0.08 0.15 0.12 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --epochs 10 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.00005 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the crop model:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --episodes 100 --device cpu --seed 690000 --width 100 --height 100 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --episodes 100 --device cpu --seed 700000 --width 100 --height 100 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.020 0.025 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current crop result:

| Model | Crop | Intermediate bucket | Narrow bucket | Visual camera control | Full light geometry | Full contact light |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| staged 650k | no | 0.510 | 0.330 | 0.850 | 0.390 | 0.400 |
| staged crop 650k e16 | yes | 0.890 | 0.770 | 0.880 | 0.530 | 0.570 |

The crop model is the strongest geometry candidate so far. Full details are in
`results\near_hole_crop_summary.md`.

## Crop Control And Full-Light Replay

The crop model's remaining control failures were concentrated around delay 2,
low filter alpha, low action scale, and low noise:

```powershell
python scripts\analyze_control_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --episodes 200 --output-csv results\control_failure_analysis_ur5e_staged_crop_650k_e16.csv --output-md results\control_failure_analysis_ur5e_staged_crop_650k_e16.md --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Collect a hard control replay dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz --samples 50000 --seed 760000 --image-width 100 --image-height 100 --include-near-hole-crop --near-hole-crop-size 64 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 0.8 0.9 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --success-only --compressed
```

Observed collection result: `50000` samples, `2061` episodes, `0.799` oracle
success, `0.201` oracle collision.

Train the control replay model:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.35 0.14 0.15 0.06 0.04 0.10 0.10 0.06 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_control_replay_700k_oracle_e4\sac_image_bc.zip --epochs 4 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000005 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

The control replay model reaches `visual_camera_control=0.900`, but
`full_light_geometry` remains `0.520`, so add a combined geometry+control
dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz --samples 50000 --seed 780000 --image-width 100 --image-height 100 --include-near-hole-crop --near-hole-crop-size 64 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --success-only --compressed
```

Observed collection result: `50000` samples, `4003` episodes, `0.553` oracle
success, `0.445` oracle collision.

Train the final full-light replay model:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.30 0.12 0.10 0.15 0.06 0.04 0.08 0.10 0.05 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_control_replay_700k_oracle_e4\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --epochs 4 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000003 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the final crop replay model:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current result:

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| staged crop 650k e16 | 0.960 | 0.960 | 0.880 | 0.530 | 0.570 |
| crop control replay 700k e4 | 0.960 | 0.970 | 0.900 | 0.520 | 0.570 |
| crop full-light replay 750k e4 | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 |

The current strongest crop-enabled model is:

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip
```

Full details are in `results\crop_control_replay_summary.md`.

## Hard Full-Light Replay Attempt

Run combined full-light failure analysis on the current recommended crop model:

```powershell
python scripts\analyze_geometry_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 200 --seed 820000 --output-csv results\geometry_failure_analysis_staged_crop_full_light_replay_750k_e4_full_light.csv --output-md results\geometry_failure_analysis_staged_crop_full_light_replay_750k_e4_full_light.md --device cpu --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.2 --control-action-noise-std-range 0 0.0008 --control-action-delay-range 0 2 --control-action-filter-alpha-range 0.55 1.0 --geometry-hole-center-xy-jitter 0.002 0.002 --geometry-fixture-height-jitter 0.001 --geometry-table-height-jitter 0.001 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.0115 0.0125 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

The 200-episode analysis reached `0.650` success but still showed collision
concentration around `delay_2`, `low_<0.70` filter alpha, and low-noise
combined buckets.

Scan staged-oracle gain in the targeted hard full-light bucket:

```powershell
python scripts\scan_oracle_control_gain.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise.csv --output-md results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise.md --episodes 50 --seed 842000 --gains 1.0 0.7 0.5 0.35 0.25 0.18 --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Collect the hard full-light replay dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_gain05_success_50k_oracle.npz --samples 50000 --seed 845000 --image-width 100 --image-height 100 --include-near-hole-crop --near-hole-crop-size 64 --expert-action-gain 0.5 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --success-only --compressed
```

Observed collection result: `50000` samples, `7065` episodes, `0.267` oracle
success, `0.733` oracle collision.

Train the hard replay attempt:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_gain05_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.27 0.10 0.08 0.13 0.10 0.05 0.03 0.07 0.10 0.07 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_hard_full_light_replay_800k_oracle_e4\sac_image_bc.zip --epochs 4 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

This attempt is a negative result:

| Model | Standard full light | Full contact light | Hard full-light bucket |
| --- | ---: | ---: | ---: |
| crop full-light replay 750k e4 | 0.580 | 0.590 | 0.330 |
| hard full-light replay 800k e4 | 0.550 | 0.530 | 0.310 |

Do not promote the 800k hard replay model. Full details are in
`results\hard_full_light_replay_summary.md`.

## Guarded Two-Stage Oracle

The hard full-light bucket is limited by oracle/controller stability, not just
BC data volume. The selected guarded oracle improves the hard bucket before any
new policy training:

| Controller | Seed | Episodes | Success | Collision |
| --- | ---: | ---: | ---: | ---: |
| staged, gain 0.5 | 847000 | 100 | 0.280 | 0.720 |
| guarded_two_stage, gain 1.0 | 847000 | 100 | 0.440 | 0.560 |

Selected hard-bucket scan:

```powershell
python scripts\scan_oracle_control_gain.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise_guarded_selected_100ep.csv --output-md results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise_guarded_selected_100ep.md --episodes 100 --seed 847000 --gains 1.0 0.85 --oracle-mode guarded_two_stage --guarded-align-xy-tolerance 0.025 --guarded-insert-xy-tolerance 0.005 --guarded-retract-xy-tolerance 0.012 --guarded-preinsert-height 0.000 --guarded-max-xy-action 0.005 --guarded-max-down-action 0.0035 --guarded-max-up-action 0.005 --guarded-prediction-steps 1.0 --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Matching staged baseline:

```powershell
python scripts\scan_oracle_control_gain.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise_staged_selected_seed847k_100ep.csv --output-md results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise_staged_selected_seed847k_100ep.md --episodes 100 --seed 847000 --gains 1.0 0.7 0.5 --oracle-mode staged --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Next dataset collection candidate:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_guarded_success_50k_oracle.npz --samples 50000 --seed 848000 --image-width 100 --image-height 100 --include-near-hole-crop --near-hole-crop-size 64 --expert-action-gain 1.0 --oracle-mode guarded_two_stage --guarded-align-xy-tolerance 0.025 --guarded-insert-xy-tolerance 0.005 --guarded-retract-xy-tolerance 0.012 --guarded-preinsert-height 0.000 --guarded-max-xy-action 0.005 --guarded-max-down-action 0.0035 --guarded-max-up-action 0.005 --guarded-prediction-steps 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --success-only --compressed
```

Full details are in `results\guarded_oracle_summary.md`.

## Guarded Hard Replay Attempt

The guarded oracle was used to collect a 50k hard full-light success-only
dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_guarded_success_50k_oracle.npz --samples 50000 --seed 848000 --image-width 100 --image-height 100 --include-near-hole-crop --near-hole-crop-size 64 --expert-action-gain 1.0 --oracle-mode guarded_two_stage --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --success-only --compressed
```

Collection result: `50000` samples, `5127` episodes, `0.376` oracle success,
`0.608` oracle collision.

Two BC replay attempts were tested from the current 750k recommendation:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_guarded_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.29 0.10 0.08 0.13 0.08 0.05 0.03 0.07 0.10 0.07 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_guarded_hard_replay_800k_oracle_e4\sac_image_bc.zip --epochs 4 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_guarded_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.30 0.10 0.08 0.14 0.04 0.05 0.03 0.07 0.11 0.08 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_guarded_hard_replay_light_790k_oracle_e2\sac_image_bc.zip --epochs 2 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000001 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Result:

| Model | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 750k recommended | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 | 0.330 |
| guarded hard replay 800k e4 | 0.960 | 0.950 | 0.880 | 0.550 | 0.530 | 0.340 |
| guarded hard replay light 790k e2 | 0.980 | 0.980 | 0.910 | 0.550 | 0.580 | 0.340 |

Do not promote either guarded replay model. Full details are in
`results\guarded_hard_replay_summary.md`.

## Deployment-Time Guarded Insert

Evaluate the current recommended 750k visual policy without a guarded wrapper:

```powershell
python scripts\eval_guarded_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --seed 90000 --device cpu --output-csv results\eval_guarded_policy_matrix_750k_no_guard_core.csv --output-md results\eval_guarded_policy_matrix_750k_no_guard_core.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --guard-scenario-filter none --guard-start-xy 0.06 --guard-start-z 0.10 --guard-risk-xy 0.0 --guard-blend 1.0
```

Evaluate an aggressive wrapper that guards every scenario:

```powershell
python scripts\eval_guarded_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --seed 90000 --device cpu --include-hard-bucket --output-csv results\eval_guarded_policy_matrix_750k_override.csv --output-md results\eval_guarded_policy_matrix_750k_override.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --guard-scenario-filter all --guard-start-xy 0.06 --guard-start-z 0.10 --guard-risk-xy 0.0 --guard-blend 1.0
```

Evaluate the selected geometry/contact guarded wrapper:

```powershell
python scripts\eval_guarded_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --seed 90000 --device cpu --include-hard-bucket --output-csv results\eval_guarded_policy_matrix_750k_geometry_only_override.csv --output-md results\eval_guarded_policy_matrix_750k_geometry_only_override.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --guard-scenario-filter geometry --guard-start-xy 0.06 --guard-start-z 0.10 --guard-risk-xy 0.0 --guard-blend 1.0
```

Result:

| Configuration | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no guard | 0.980 | 0.980 | 0.910 | 0.580 | 0.580 | 0.330 |
| guard all scenarios | 1.000 | 1.000 | 0.830 | 0.690 | 0.660 | 0.480 |
| guard geometry/contact only | 0.980 | 0.980 | 0.920 | 0.690 | 0.660 | 0.480 |

The selected wrapper is a positive deployment-time result. It does not replace
the policy checkpoint; it wraps the current 750k policy during final insertion.
Full details are in `results\guarded_policy_summary.md`.

The wrapper is also available in `scripts\demo_policy.py` through
`--guarded-policy`. Demo trajectory CSVs include `guard_enabled`,
`guard_active`, `policy_action_*`, `guarded_action_*`, and `final_action_*`.
The checked demo files are:

| Demo | Seed | Result |
| --- | ---: | --- |
| `demos\guarded_policy_full_light_no_guard.gif` | 90000 | success, 12 steps |
| `demos\guarded_policy_full_light_guarded.gif` | 90000 | success, 11 steps, 11 guard rows |
| `demos\guarded_policy_hard_bucket_no_guard.gif` | 90005 | collision failure, 11 steps |
| `demos\guarded_policy_hard_bucket_guarded.gif` | 90005 | success, 20 steps, 20 guard rows |

Render the hard-bucket no-guard contrast episode:

```powershell
python scripts\demo_policy.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --output demos\guarded_policy_hard_bucket_no_guard.gif `
  --trajectory-output demos\guarded_policy_hard_bucket_no_guard_trajectory.csv `
  --episodes 1 `
  --seed 90005 `
  --device cpu `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --render-cameras overview wrist_cam `
  --render-width 640 `
  --render-height 480 `
  --fps 20 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02
```

Render the same episode with selective guarded insertion:

```powershell
python scripts\demo_policy.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --output demos\guarded_policy_hard_bucket_guarded.gif `
  --trajectory-output demos\guarded_policy_hard_bucket_guarded_trajectory.csv `
  --episodes 1 `
  --seed 90005 `
  --device cpu `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --render-cameras overview wrist_cam `
  --render-width 640 `
  --render-height 480 `
  --fps 20 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-name hard_full_light_bucket `
  --guard-start-xy 0.06 `
  --guard-start-z 0.10 `
  --guard-blend 1.0
```

Full demo details are in `results\guarded_demo_summary.md`.

## Guarded Parameter Scan

Run the focused one-at-a-time guarded parameter scan:

```powershell
python scripts\scan_guarded_policy_params.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --preset focused `
  --scenario-preset targeted `
  --episodes 30 `
  --seed 90000 `
  --device cpu `
  --output-csv results\guarded_policy_param_scan_focused.csv `
  --output-md results\guarded_policy_param_scan_focused.md `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guard-scenario-filter geometry
```

Validate the previous `blend=1.0` wrapper against the new `blend=0.75`
candidate on the full core matrix:

```powershell
python scripts\scan_guarded_policy_params.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --preset grid `
  --scenario-preset core `
  --episodes 100 `
  --seed 90000 `
  --device cpu `
  --output-csv results\guarded_policy_param_scan_blend_validation_100ep.csv `
  --output-md results\guarded_policy_param_scan_blend_validation_100ep.md `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guard-scenario-filter geometry `
  --guard-start-xy-values 0.06 `
  --guard-start-z-values 0.10 `
  --guard-blend-values 0.75 1.0 `
  --guarded-max-down-action-values 0.0035 `
  --guarded-align-xy-tolerance-values 0.025
```

Result:

| Configuration | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no guard | 0.980 | 0.980 | 0.910 | 0.580 | 0.600 | 0.320 |
| guard blend 0.75 | 0.980 | 0.980 | 0.900 | 0.710 | 0.650 | 0.530 |
| guard blend 1.0 | 0.980 | 0.980 | 0.910 | 0.690 | 0.660 | 0.480 |

Promote `guard_blend=0.75` as the next guarded deployment candidate. Full
details are in `results\guarded_policy_param_scan_summary.md`.

## Guarded Deployment Inference

Run a deployment-style smoke where geometry-only guard is available but should
not activate in the control-only scenario:

```powershell
python scripts\run_policy_inference.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 1 `
  --seed 90000 `
  --device cpu `
  --output results\policy_inference_visual_camera_control_guarded_smoke.csv `
  --domain-randomization-level visual_camera_control `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-blend 0.75
```

Run the hard-bucket no-guard deployment contrast:

```powershell
python scripts\run_policy_inference.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 1 `
  --seed 90005 `
  --device cpu `
  --output results\policy_inference_hard_bucket_no_guard_smoke.csv `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02
```

Run the same hard-bucket episode with guarded insertion:

```powershell
python scripts\run_policy_inference.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 1 `
  --seed 90005 `
  --device cpu `
  --output results\policy_inference_hard_bucket_guarded_blend075_smoke.csv `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-name hard_full_light_bucket `
  --guard-blend 0.75 `
  --guard-start-xy 0.06 `
  --guard-start-z 0.10
```

Result:

| Scenario | Configuration | Success | Collision | Steps | Guard steps |
| --- | --- | ---: | ---: | ---: | ---: |
| visual_camera_control | guarded geometry blend 0.75 | 1 | 0 | 10 | 0 |
| hard bucket | no guard | 0 | 1 | 11 | 0 |
| hard bucket | guarded geometry blend 0.75 | 1 | 0 | 34 | 34 |

Trace CSVs include `guard_enabled`, `guard_active`, `policy_action_*`,
`guarded_action_*`, `final_action_*`, `raw_action_*`, and `safe_action_*`.
Full details are in `results\policy_inference_guarded_summary.md`.

## Geometry Clearance Curriculum Scan

Run the targeted clearance scan over standard full-light geometry and the hard
delay/low-filter bucket:

```powershell
python scripts\scan_geometry_clearance.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --tier-preset all `
  --scenario-preset targeted `
  --episodes 30 `
  --seed 930000 `
  --device cpu `
  --output-csv results\geometry_clearance_scan_targeted_30ep.csv `
  --output-md results\geometry_clearance_scan_targeted_30ep.md `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02
```

Run the full-contact clearance scan:

```powershell
python scripts\scan_geometry_clearance.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --tier-preset all `
  --scenario-preset full_contact `
  --episodes 30 `
  --seed 930000 `
  --device cpu `
  --output-csv results\geometry_clearance_scan_full_contact_30ep.csv `
  --output-md results\geometry_clearance_scan_full_contact_30ep.md `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02
```

Guarded blend `0.75` result:

| Tier | Mean clearance | Full light | Hard bucket | Full contact |
| --- | ---: | ---: | ---: | ---: |
| wide_current | 14.9 mm | 0.600 | 0.400 | 0.633 |
| medium | 9.9 mm | 0.667 | 0.333 | 0.567 |
| narrow | 6.9 mm | 0.533 | 0.367 | 0.600 |
| tight | 4.4 mm | 0.467 | 0.267 | 0.533 |

Use `medium` as the next curriculum target, mixed with current wide clearance.
Do not jump directly to narrow/tight as the default distribution; hard-control
success is still too low. Full details are in
`results\geometry_clearance_scan_summary.md`.

## Current Recommended UR5e Model

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip
```

This is the current recommended crop-enabled UR5e adapter model. Use
`--include-near-hole-crop --near-hole-crop-size 64` for training, evaluation,
demo, and deployment-style inference with this checkpoint.

## Current Best Simplified Sidecam Model

```text
checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip
```

This is the delay-robust image BC model for the older simplified sidecam setup.

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

## Policy Inference Interface

Run the current best policy through the deployment-style MuJoCo inference
interface with action limiting, workspace limiting, and per-step CSV logging:

```powershell
python scripts\run_policy_inference.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 1 --output results\policy_inference_trace.csv --device cpu --domain-randomization-level full_contact_light --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

The default `--control-frequency-hz 50` matches the current MuJoCo control
period of `0.02 s`. Use an explicit value such as `20` when prototyping a real
robot dry-run loop.
Internally this path uses `PolicyInferenceSession` plus
`MujocoObservationProvider` and `MujocoActionExecutor`; real hardware should
replace only the provider/executor layer.

Use a smoother action safety layer:

```powershell
python scripts\run_policy_inference.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 1 --output results\policy_inference_trace_smooth.csv --device cpu --domain-randomization-level full_contact_light --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --safety-action-filter-alpha 0.6
```

## Real Backend Dry Run

Validate the real-robot provider/executor path without loading a model or moving
hardware:

```powershell
python scripts\run_real_policy_dryrun.py --zero-policy --episodes 1 --max-steps 5 --output results\real_policy_dryrun_zero_trace.csv
```

Run the trained image policy against a real-camera image or image folder while
still using a dry-run UR5 executor:

```powershell
python scripts\run_real_policy_dryrun.py --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --image-dir path\to\camera_frames --episodes 1 --output results\real_policy_dryrun_trace.csv
```

Preview preprocessing for a real camera frame directory:

```powershell
python scripts\preprocess_camera_frames.py --input path\to\camera_frames --output-dir results\preprocessed_camera_frames --stats-output results\preprocessed_camera_frames_stats.csv --width 100 --height 100 --crop-xywh 0 0 640 480 --rotate-k 0
```

Smoke-test preprocessing without camera frames:

```powershell
python scripts\preprocess_camera_frames.py --synthetic-smoke --output-dir results\preprocessed_camera_frames_smoke --stats-output results\preprocessed_camera_frames_smoke_stats.csv --crop-xywh 20 10 160 120 --rotate-k 1 --flip-horizontal
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

UR5e adapter fixedcam models:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean fixedcam 50k scratch eval_policy | 1.000 | 0.000 |
| clean fixedcam 50k scratch eval_matrix | 0.950 | 0.050 |
| visual_camera fixedcam 50k scratch | 0.040 | 0.850 |
| visual_camera_control fixedcam 50k scratch | 0.070 | 0.840 |
| clean clean+visual_camera 100k e35 | 0.960 | 0.040 |
| visual_camera clean+visual_camera 100k e35 | 0.660 | 0.340 |
| visual_camera_control clean+visual_camera 100k e35 | 0.440 | 0.560 |
| clean clean+visual_camera 150k e20 | 0.960 | 0.040 |
| visual_camera clean+visual_camera 150k e20 | 0.810 | 0.190 |
| visual_camera_control clean+visual_camera 150k e20 | 0.480 | 0.520 |
| clean mild-control 200k e20 | 0.930 | 0.070 |
| visual_camera mild-control 200k e20 | 0.920 | 0.080 |
| visual_camera_control mild-control 200k e20 | 0.600 | 0.400 |
| clean success-only control 250k e15 | 0.950 | 0.050 |
| visual_camera success-only control 250k e15 | 0.910 | 0.090 |
| visual_camera_control success-only control 250k e15 | 0.730 | 0.270 |
| full_light_geometry success-only control 250k e15 | 0.250 | 0.730 |
| full_contact_light success-only control 250k e15 | 0.270 | 0.690 |
| clean delay-filter success 300k e10 | 0.970 | 0.030 |
| visual_camera delay-filter success 300k e10 | 0.940 | 0.060 |
| visual_camera_control delay-filter success 300k e10 | 0.780 | 0.220 |
| clean delay-filter success 350k e8 | 0.990 | 0.010 |
| visual_camera delay-filter success 350k e8 | 0.930 | 0.070 |
| visual_camera_control delay-filter success 350k e8 | 0.860 | 0.140 |
| full_light_geometry delay-filter success 350k e8 | 0.290 | 0.670 |
| full_contact_light delay-filter success 350k e8 | 0.270 | 0.680 |
| clean hard-control 400k e6 | 0.980 | 0.020 |
| visual_camera hard-control 400k e6 | 0.960 | 0.040 |
| visual_camera_control hard-control 400k e6 | 0.880 | 0.120 |
| hard-control fixed bucket hard-control 400k e6 | 0.700 | 0.300 |
| clean hard-weighted 500k e5 | 0.960 | 0.040 |
| visual_camera hard-weighted 500k e5 | 0.990 | 0.010 |
| visual_camera_control hard-weighted 500k e5 | 0.890 | 0.110 |
| hard-control fixed bucket hard-weighted 500k e5 | 0.770 | 0.230 |
| full_light_geometry hard-weighted 500k e5 | 0.300 | 0.660 |
| full_contact_light hard-weighted 500k e5 | 0.310 | 0.660 |
| clean fixedcam 5k scratch | 0.790 | 0.200 |
