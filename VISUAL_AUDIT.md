# Visual Contribution Audit

Last updated: 2026-05-12

This audit checks whether the hard high-start image policy is actually using
visual observations, and how much the privileged guard/oracle contributes to
success.

## Scope

Checkpoint:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip
```

Base config:

```text
configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml
```

Scenario:

```text
hard_full_light_bucket
```

Smoke size:

```text
10 episodes, seed 574000
```

This is a smoke audit, not a final statistical result. It is intended to catch
large failure modes before more training or camera changes.

## Added Audit Controls

`scripts\eval_guarded_policy.py` now supports:

- `--control-mode guarded`: learned policy plus guarded final insertion
- `--control-mode policy`: learned policy only, no guard
- `--control-mode guard_only`: privileged oracle/guard action only, no learned
  policy action
- `--image-ablation normal`: unchanged image observations
- `--image-ablation black`: all image observations replaced with zeros
- `--image-ablation noise`: all image observations replaced with random pixels
- `--image-ablation shuffle`: policy receives previous observations from other
  steps instead of the current observation

## Results

| Control | Image | Success | Collision | Timeout | Mean guarded steps | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy | normal | 0.100 | 0.700 | 0.200 | 0.0 | 0.02761 | 0.03800 |
| policy | black | 0.000 | 1.000 | 0.000 | 0.0 | 0.16070 | 0.01429 |
| policy | noise | 0.000 | 1.000 | 0.000 | 0.0 | 0.20742 | 0.02018 |
| policy | shuffle | 0.000 | 1.000 | 0.000 | 0.0 | 0.11630 | 0.01748 |
| guarded | normal | 0.400 | 0.500 | 0.100 | 212.0 | 0.02120 | 0.03086 |
| guarded | black | 0.100 | 0.900 | 0.000 | 13.6 | 0.15705 | 0.01032 |
| guarded | noise | 0.100 | 0.900 | 0.000 | 20.2 | 0.20237 | 0.01619 |
| guarded | shuffle | 0.100 | 0.900 | 0.000 | 15.5 | 0.11756 | 0.01084 |
| guard_only | normal | 0.500 | 0.300 | 0.200 | 456.2 | 0.01445 | 0.02286 |

Raw reports:

```text
results\ur5e_full\high_start\hard\visual_audit\
```

## Interpretation

The visual input is not irrelevant:

- policy-only normal image reaches `0.100` success, while black/noise/shuffle
  all drop to `0.000`.
- guarded normal image reaches `0.400`, while guarded black/noise/shuffle drop
  to `0.100`.
- corrupted images also prevent the learned policy from reaching the guard
  activation region: guarded steps drop from `212.0` to about `13.6 - 20.2`.

The privileged guard/oracle is still a major contributor:

- policy-only normal is only `0.100`.
- guarded normal is `0.400`.
- guard_only is `0.500`.

This means the current hard high-start success is not purely visual policy
success. The learned image policy helps approach the hole and activate the
guard, but the privileged guard/oracle still carries much of the final task.

## Risk For Sim-To-Real

The current guarded evaluation still uses MuJoCo truth through the guard state:

- peg tip position
- target/hole position
- true XY/Z distance
- applied action diagnostics

These are useful for diagnosis and data generation, but they are not directly
available on the real robot unless replaced by calibrated camera estimates,
TCP state, and possibly force/current/contact proxies.

The audit reduces one concern but confirms another:

- reduced concern: the image policy is not completely blind or purely memorized
  from action priors.
- confirmed concern: deployment success will be overestimated if the privileged
  guard is treated as a real-compatible controller.

## Key-Frame Visibility Audit

Added:

```text
scripts\audit_visual_visibility.py
```

This script rolls out the current checkpoint, writes a step-level visibility
CSV, and exports key-frame images:

- wrist RGB
- wrist RGB annotated with projected hole center and peg tip
- policy grayscale image
- near-hole crop
- overview camera

3-episode hard-bucket smoke:

```text
results\ur5e_full\high_start\hard\visual_audit\visibility_pred0_guarded_3ep.csv
results\ur5e_full\high_start\hard\visual_audit\visibility_pred0_guarded_3ep.md
results\ur5e_full\high_start\hard\visual_audit\frames_pred0_guarded_3ep\
```

Outcome:

- success: `0.667`
- collision: `0.000`
- timeout: `0.333`
- timeout case ended near the hole: final XY about `6.0 mm`, final Z about
  `21.8 mm`

Visibility metrics:

| Subset | Hole projected | Peg projected | Both in center crop | Hole crop visible | Peg crop visible |
| --- | ---: | ---: | ---: | ---: | ---: |
| all | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 |
| low_z | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 |
| near_xy | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 |
| insert_band | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 |

Interpretation:

- The full wrist image generally contains enough projection information: both
  the hole center and peg tip project into the `100x100` wrist frame.
- The current fixed center crop is poorly framed for final alignment: the hole
  geometry is visible in the crop, but the peg geometry is not visible in the
  crop in sampled segmentation frames.
- This weakens the current near-hole visual signal. The policy can see some
  hole/fixture appearance, but the crop does not reliably show the relative
  peg-tip-to-hole geometry needed for the final millimeters.
- This supports changing the camera/crop observation path before scaling more
  correction or DAgger data.

## Crop Offset Scan

Added:

```text
scripts\scan_visual_crop_offset.py
```

The environment now supports a configurable fixed crop offset:

```text
near_hole_crop_offset: [x_pixels, y_pixels]
```

The default is `[0, 0]`, so existing datasets, checkpoints, and configs remain
backward compatible.

3-episode hard-bucket crop scan:

```text
results\ur5e_full\high_start\hard\visual_audit\crop_offset_scan_pred0_guarded_3ep.csv
results\ur5e_full\high_start\hard\visual_audit\crop_offset_scan_pred0_guarded_3ep.md
```

Best visibility candidate:

```text
near_hole_crop_offset: [-18, 0]
```

This shifts the `64x64` crop from center bounds `18:18:82:82` to left bounds
`0:18:64:82`.

Comparison on the 3-episode smoke:

| Crop offset | Insert both projected in crop | Insert both visible in crop | Near-XY both projected in crop | Near-XY both visible in crop |
| --- | ---: | ---: | ---: | ---: |
| `[0, 0]` | 0.000 | 0.000 | 0.000 | 0.000 |
| `[-18, 0]` | 1.000 | 0.140 | 1.000 | 0.308 |

Interpretation:

- The crop framing problem is real and fixable: left-shifting the crop makes
  projected peg-tip-to-hole geometry fall inside the crop.
- The remaining low `both visible` rate is not only a crop issue. It also
  reflects physical occlusion / view geometry near insertion: when the peg is
  hidden in the full wrist image, a crop cannot recover it.
- Therefore the next data/training step should use the shifted crop, but the
  next camera-design step should still consider either a wrist camera pose
  change or a second view if final insertion remains occluded.

## Shifted-Crop Training Smoke

The first shifted-crop training smoke used `near_hole_crop_offset: [-18, 0]`.
Two variants were tried from the current hard high-start center-crop checkpoint:

| Model | Data | Epochs / LR | Clean | Visual camera | Visual camera control | Hard bucket |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| center-crop baseline | 50k center crop | existing | 0.600 | 0.700 | 0.500 | 0.400 |
| crop-left smoke | 1k crop-left | 2 / config LR | 0.500 | 0.400 | 0.300 | 0.300 |
| crop-left conservative | 10k crop-left | 1 / 0.000003 | 0.500 | 0.400 | 0.100 | 0.200 |

Artifacts:

```text
datasets\ur5e_full\high_start\hard\image_expert_1k_high_start_hard_safe_visual_camera_crop_left.npz
datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_safe_visual_camera_crop_left.npz
checkpoints\ur5e_full\high_start\hard\sac_image_bc_1k_high_start_hard_safe_visual_camera_crop_left.zip
checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_safe_visual_camera_crop_left_lr3e6_e1.zip
results\ur5e_full\high_start\hard\visual_audit\eval_center_baseline_50k_10ep.md
results\ur5e_full\high_start\hard\visual_audit\eval_crop_left_1k_e2_10ep.md
results\ur5e_full\high_start\hard\visual_audit\eval_crop_left_10k_lr3e6_e1_10ep.md
```

The shifted crop itself was validated with a 2-episode visibility audit:

```text
results\ur5e_full\high_start\hard\visual_audit\visibility_crop_left_10k_lr3e6_e1_2ep.md
results\ur5e_full\high_start\hard\visual_audit\frames_crop_left_10k_lr3e6_e1_2ep\
```

In that audit, `both in crop` reached `1.000` for all rows and insert-band
rows. That confirms the crop offset solves the geometric framing problem.
However, it does not by itself improve task success under short fine-tuning.

Interpretation:

- Do not promote the crop-left checkpoint as a better policy.
- The old model has likely adapted to the center-crop observation distribution;
  changing the crop location creates an observation shift that short BC
  fine-tuning does not absorb.
- The crop offset is still useful as evidence for observation redesign, but
  the next visual step should be either a camera-pose / second-view audit or a
  larger replay-style retrain designed around the new observation from the
  start.

## Wrist Camera Pose Scan

Added:

```text
scripts\scan_wrist_camera_pose.py
```

The scan rolls out the current baseline policy with the current baseline camera,
then temporarily applies candidate wrist camera local pose/FOV/crop settings at
sampled states. This keeps the policy rollout fixed while auditing whether a
different camera mounting pose would improve visibility.

Rotation/FOV/crop coarse scan:

```text
results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_rot_fov_crop_3ep.csv
results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_rot_fov_crop_3ep.md
```

Result: rotation/FOV alone helped only slightly. The best coarse candidate
improved insert-band crop visibility from about `0.149` to `0.161`, so the
remaining bottleneck is not solved by a small view rotation or FOV change.

Position/yaw/crop scan:

```text
results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_pos_yaw_crop_3ep.csv
results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_pos_yaw_crop_3ep.md
results\ur5e_full\high_start\hard\visual_audit\frames_wrist_camera_pose_scan_pos_yaw_crop_3ep\
```

Best smoke candidate:

```text
camera local pos_offset: [-0.04, -0.04, 0.00]
camera local rot_offset_deg: [0.0, 0.0, 0.0]
fovy: 100
near_hole_crop_offset: [-18, 0]
```

Same 3-episode sampled visibility comparison:

| Candidate | Insert both visible in crop | Insert both in crop | Near-XY both visible in crop | Near-XY both in crop | All both visible |
| --- | ---: | ---: | ---: | ---: | ---: |
| current pose + crop `[-18,0]` | 0.149 | 1.000 | 0.308 | 1.000 | 0.513 |
| pos `[-0.04,-0.04,0]` + crop `[-18,0]` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| pos `[0,-0.04,-0.04]` + crop `[-18,0]` | 0.966 | 1.000 | 0.972 | 1.000 | 0.980 |

Frame export for candidate `003` and current-pose shifted-crop candidate `027`
does not show an obvious invalid view in the sampled frames. Still, this is a
visibility result only: the current policy was not trained with this camera
mounting pose.

Interpretation:

- The better next step is not a second camera yet. A plausible wrist camera
  mounting shift already removes most sampled near-insertion occlusion.
- The next implementation step should add a configurable nominal wrist camera
  pose offset to the environment/configs, then collect and train with that pose
  from the start.
- Do not evaluate the old checkpoint with this new camera as a performance
  claim; it would be another observation-distribution shift.

## Wrist Pose Smoke Training

Implemented environment/config support for a nominal wrist camera pose:

```text
wrist_camera_pos_offset: [x, y, z]
wrist_camera_rot_offset_deg: [roll, pitch, yaw]
wrist_camera_fovy: optional_fovy
```

The default remains the original XML camera. When set, visual camera
randomization now jitters around the configured nominal pose.

Smoke configs:

```text
configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_smoke.yaml
configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_smoke.yaml
configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_smoke.yaml
```

Smoke artifacts:

```text
datasets\ur5e_full\high_start\hard\image_expert_1k_high_start_hard_wrist_pose_visual_camera.npz
checkpoints\ur5e_full\high_start\hard\sac_image_bc_1k_high_start_hard_wrist_pose_visual_camera.zip
results\ur5e_full\high_start\hard\visual_audit\image_expert_1k_wrist_pose_inspection.md
results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_1k_e2_10ep.md
```

Dataset collection completed, but the oracle rollout was weak for this smoke
seed: `0.214` success, `0.214` collision, `0.571` timeout over `14` episodes.
The saved dataset is still valid and success-only, but it contains only `3`
successful source episodes.

The 2-epoch BC smoke ran end-to-end, but should not be promoted:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.200 | 0.800 | 0.000 |
| visual_camera | 0.300 | 0.600 | 0.100 |
| visual_camera_control | 0.100 | 0.800 | 0.100 |
| full_light_geometry | 0.200 | 0.700 | 0.100 |
| full_contact_light | 0.100 | 0.900 | 0.000 |
| hard_full_light_bucket | 0.000 | 1.000 | 0.000 |

Interpretation:

- The selected wrist pose remains a strong visibility candidate.
- The smoke confirms the new camera path is wired through env/config/dataset
  metadata/training/eval.
- Short fine-tuning from the old center-camera checkpoint is not enough. The
  observation shift is larger than the earlier crop-only shift, and the smoke
  model collides before the guard can help in the hard bucket.
- Next training should use a larger replay/scratch run under the new camera
  pose, with stronger dataset coverage, rather than another tiny fine-tune.

## Wrist Pose 10k Scratch

Collected a larger wrist-pose dataset using the more stable `seed=564000`:

```text
datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_wrist_pose_visual_camera_seed564k.npz
results\ur5e_full\high_start\hard\visual_audit\image_expert_10k_wrist_pose_seed564k_inspection.md
```

Collection statistics matched the earlier hard high-start oracle difficulty:
`0.427` success, `0.122` collision over `82` episodes, with `success_only=true`.

Scratch BC was then run under the new camera observation instead of fine-tuning
from the old center-camera checkpoint:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_wrist_pose_visual_camera_scratch_e10.zip
checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_wrist_pose_visual_camera_scratch_e20.zip
```

Training loss:

| Model | Train loss | Val loss |
| --- | ---: | ---: |
| scratch e10 | 0.126621 | 0.131496 |
| scratch e20 | 0.086670 | 0.091862 |

Same-seed 10-episode guarded eval:

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| old center-camera baseline | 0.600 | 0.700 | 0.500 | 0.400 | 0.500 | 0.400 |
| wrist pose 1k fine-tune | 0.200 | 0.300 | 0.100 | 0.200 | 0.100 | 0.000 |
| wrist pose 10k scratch e10 | 0.500 | 0.500 | 0.300 | 0.100 | 0.400 | 0.300 |
| wrist pose 10k scratch e20 | 0.500 | 0.500 | 0.400 | 0.100 | 0.400 | 0.300 |

Interpretation:

- Training from scratch under the new wrist-pose observation is much better than
  trying to fine-tune the old center-camera model on `1k` samples.
- The model now reaches the guarded near-hole region again: hard-bucket guard
  steps increased from `0.0` in the 1k fine-tune to `213.1` in e20.
- It is still below the old center-camera baseline, so this is not promoted.
- The next wrist-pose run should scale data, not just epochs: collect about
  `50k` successful wrist-pose expert samples, then run weighted/scratch BC with
  a larger sample budget.

## Wrist Pose 50k Scratch

Collected and trained the first larger wrist-pose model:

```text
datasets\ur5e_full\high_start\hard\image_expert_50k_high_start_hard_wrist_pose_visual_camera_seed564k.npz
checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_wrist_pose_visual_camera_scratch_e20.zip
results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_50k_scratch_e20_20ep.md
```

Dataset collection:

| Samples | Episodes | Success | Collision |
| ---: | ---: | ---: | ---: |
| 50k | 462 | 0.377 | 0.110 |

Training loss:

| Model | Train loss | Val loss |
| --- | ---: | ---: |
| wrist pose 50k scratch e20 | 0.045830 | 0.047674 |

Same-seed guarded eval:

| Model | Episodes | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| old center-camera baseline | 20 | 0.550 | 0.500 | 0.500 | 0.400 | 0.400 | 0.450 |
| wrist pose 10k scratch e20 | 10 | 0.500 | 0.500 | 0.400 | 0.100 | 0.400 | 0.300 |
| wrist pose 50k scratch e20 | 20 | 0.550 | 0.600 | 0.350 | 0.400 | 0.400 | 0.400 |

Interpretation:

- Scaling from 10k to 50k closed most of the gap. The new camera candidate now
  matches the old baseline on clean/full-light/full-contact and exceeds it on
  visual_camera.
- The main remaining regression is `visual_camera_control`: `0.350` versus the
  old baseline's `0.500`.
- This suggests the visibility problem is largely addressed, and the next
  bottleneck is control randomization under the new observation distribution.
- Do not start second-camera work yet. The next useful run is wrist-pose
  control-randomized data/replay, not another camera redesign.

## Wrist Pose Control Replay

Collected wrist-pose `visual_camera_control` data:

```text
datasets\ur5e_full\high_start\hard\image_expert_50k_high_start_hard_wrist_pose_visual_camera_control_seed580k.npz
results\ur5e_full\high_start\hard\visual_audit\image_expert_50k_wrist_pose_control_seed580k_inspection.md
```

Collection statistics:

| Samples | Episodes | Success | Collision |
| ---: | ---: | ---: | ---: |
| 50k | 424 | 0.413 | 0.210 |

Two weighted replay variants were trained from the wrist-pose 50k scratch
checkpoint:

| Model | Visual data weight | Control data weight | Final val loss |
| --- | ---: | ---: | ---: |
| `control_replay_e4` | 0.45 | 0.55 | 0.067870 |
| `control_replay_w75_e4` | 0.25 | 0.75 | 0.067704 |

Same-seed 20-episode guarded eval:

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| wrist pose 50k scratch e20 | 0.550 | 0.600 | 0.350 | 0.400 | 0.400 | 0.400 |
| control replay 0.55 e4 | 0.550 | 0.600 | 0.350 | 0.400 | 0.300 | 0.400 |
| control replay 0.75 e4 | 0.550 | 0.600 | 0.350 | 0.400 | 0.300 | 0.400 |

Interpretation:

- Generic control-randomized replay did not recover `visual_camera_control`.
- Increasing the control-data weight from `0.55` to `0.75` did not change the
  control success rate and reduced `full_contact_light`.
- The next step should not be another blind replay-weight sweep. It should
  analyze control failures by delay/filter/action-scale buckets and collect
  targeted data for the failing subset, or adjust the guarded near-region logic
  to account for delayed/filtered execution.

## Targeted Delay-2 Control Replay

Control failure analysis on the wrist-pose 50k scratch checkpoint and the broad
control replay checkpoint showed the same weak buckets:

| Model | Episodes | Overall success | Collision | Timeout | delay=2 success | low-scale success | high-noise success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wrist pose 50k scratch e20 | 80 | 0.237 | 0.438 | 0.325 | 0.152 | 0.059 | 0.167 |
| broad control replay w75 e4 | 80 | 0.250 | 0.400 | 0.350 | 0.152 | 0.000 | 0.125 |

Collected targeted success-only control data for the hardest subset:

```text
datasets\ur5e_full\high_start\hard\image_expert_20k_high_start_hard_wrist_pose_control_targeted_delay2_seed585k.npz
```

Dataset statistics:

| Samples | Episodes | Success | Collision | Delay | Scale mean | Noise mean | Filter alpha mean |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20k | 308 | 0.234 | 0.419 | 2.0 | 0.874 | 0.000675 | 0.770 |

Trained weighted replay from the wrist-pose 50k scratch checkpoint:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_70k_high_start_hard_wrist_pose_control_targeted_delay2_w60_e4.zip
```

Training loss:

| Epoch | Train loss | Val loss |
| ---: | ---: | ---: |
| 1 | 0.075346 | 0.067638 |
| 2 | 0.066877 | 0.061551 |
| 3 | 0.063955 | 0.059776 |
| 4 | 0.061595 | 0.057895 |

Same-seed 20-episode guarded eval:

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| wrist pose 50k scratch e20 | 0.550 | 0.600 | 0.350 | 0.400 | 0.400 | 0.400 |
| targeted delay-2 replay w60 e4 | 0.550 | 0.600 | 0.350 | 0.400 | 0.300 | 0.400 |

The targeted replay checkpoint is not promoted. It preserves clean and
visual_camera performance, but does not improve `visual_camera_control` and
regresses `full_contact_light`.

An 80-episode control failure analysis of the targeted model was worse than the
source scratch model:

| Model | Overall success | Collision | Timeout | delay=2 success | mid-filter success | low-scale success | high-noise success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| targeted delay-2 replay w60 e4 | 0.175 | 0.475 | 0.350 | 0.121 | 0.062 | 0.000 | 0.125 |

Interpretation:

- More success-only BC on delayed/noisy executions is not enough.
- The current image observation is effectively single-frame and does not expose
  the hidden action delay/filter state.
- The labels are still current-state oracle actions, while the environment
  executes delayed/filtered/noisy actions. That makes delayed-control
  compensation hard to learn with a memoryless image policy.
- The next model-side fix should expose real-available robot/control history
  such as previous command and measured TCP delta, or use a recurrent/frame-stack
  policy. Do not keep scaling targeted BC without changing the observation or
  controller structure.

## Near-Region Action Limiter Check

Two guarded near-action limiter settings were tested on the wrist-pose 50k
scratch checkpoint:

| Setting | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket | Conclusion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| strong `xy=0.002`, down `0.0010` | 0.000 | 0.000 | 0.000 | 0.050 | 0.050 | 0.050 | Too restrictive; mostly timeout/collision |
| mild `xy=0.005`, down `0.0025` | 0.550 | 0.600 | 0.350 | 0.400 | 0.400 | 0.400 | Safe but flat |

The near limiter is not promoted. It can be revisited as part of a more
state-aware deployment controller, but threshold-only slowing did not recover
`visual_camera_control`.

## Control-State Observation Smoke

Created local branch:

```text
feature/control-state-observation
```

Added an optional image observation key:

```text
control_state: shape (10,), dtype float32
```

The vector is deliberately limited to real-available control/proprio history:

| Slice | Meaning |
| --- | --- |
| `0:3` | previous commanded Cartesian action, normalized by `action_scale` |
| `3:6` | previous measured TCP/peg-tip displacement, normalized by `action_scale` |
| `6:9` | previous command minus measured displacement, normalized by `action_scale` |
| `9` | `step_count / max_steps` |

It does not expose target pose, hole pose, MuJoCo randomization parameters, or
hidden action scale/noise/delay. The goal is to let the image policy compensate
for delayed/filtered execution using information a real UR controller and TCP
state estimate can provide.

Smoke dataset:

```text
datasets\ur5e_full\high_start\hard\image_expert_512_high_start_hard_wrist_pose_control_state_smoke.npz
results\ur5e_full\high_start\hard\visual_audit\image_expert_512_wrist_pose_control_state_smoke_inspection.md
```

Smoke collection statistics:

| Samples | Episodes | Success | Collision | Array check |
| ---: | ---: | ---: | ---: | --- |
| 512 | 4 | 0.750 | 0.250 | `control_state` = `[512, 10]` |

Smoke training:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_512_high_start_hard_wrist_pose_control_state_smoke.zip
checkpoints\ur5e_full\high_start\hard\sac_image_bc_512_high_start_hard_wrist_pose_control_state_weighted_smoke.zip
```

| Smoke | Epochs | Train loss | Val loss | Purpose |
| --- | ---: | ---: | ---: | --- |
| single-dataset scratch | 1 | 0.482062 | 0.490762 | model save/load with `control_state` |
| weighted scratch | 1 | 0.479151 | 0.475912 | weighted replay path with `control_state` |
| derived old-dataset weighted scratch | 1 | 0.519189 | 0.486645 | derives `control_state` from old data without a stored vector |

2-episode guarded rollout also ran end-to-end:

```text
results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_smoke_2ep.md
```

The smoke checkpoint is not a performance result and is not promoted. It mostly
collides because it was trained on only `512` samples for one epoch.

Important compatibility note:

- Adding `control_state` changes the SB3 observation space and actor feature
  extractor.
- Old image checkpoints cannot be fine-tuned directly into this observation
  space.
- The next meaningful run should train a new scratch control-aware image model,
  or use datasets where `control_state` can be derived from recorded previous
  action and measured TCP displacement.

## Control-State 10k And Mixed 60k Results

Collected a first training-scale control-state dataset:

```text
datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_wrist_pose_control_state_visual_camera_control_seed590k.npz
results\ur5e_full\high_start\hard\visual_audit\image_expert_10k_wrist_pose_control_state_visual_camera_control_seed590k_inspection.md
```

Collection statistics:

| Samples | Episodes | Success | Collision | Notes |
| ---: | ---: | ---: | ---: | --- |
| 10k | 94 | 0.394 | 0.170 | `visual_camera_control`, `include_control_state=true` |

Scratch 10k training:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_wrist_pose_control_state_visual_camera_control_scratch_e10.zip
```

Training loss:

| Model | Final train loss | Final val loss |
| --- | ---: | ---: |
| control-state 10k scratch e10 | 0.049103 | 0.056419 |

Same-seed 20-episode guarded eval:

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| wrist pose 50k scratch e20 | 0.550 | 0.600 | 0.350 | 0.400 | 0.400 | 0.400 |
| control-state 10k scratch e10 | 0.450 | 0.400 | 0.400 | 0.300 | 0.300 | 0.300 |

Interpretation:

- `control_state` gave a small `visual_camera_control` bump in guarded eval, but
  the model lost too much clean and visual_camera performance.
- Training only on control-randomized data is not enough; it shifts the
  observation/action distribution away from the stronger visual-camera model.

Then trained a mixed scratch model using the original wrist-pose 50k visual
dataset plus the new 10k control-state dataset:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_60k_high_start_hard_wrist_pose_control_state_mix_scratch_e8.zip
results\ur5e_full\high_start\hard\visual_audit\training_metadata_wrist_pose_control_state_mix_60k_scratch_e8.json
```

The 50k visual dataset does not store `control_state`; the weighted training
script derived it from previous recorded action, measured action delta, and
step index. The 10k control dataset uses the stored `control_state`.

Training loss:

| Model | Final train loss | Final val loss |
| --- | ---: | ---: |
| control-state mixed 60k scratch e8 | 0.028147 | 0.026645 |

Same-seed 20-episode guarded eval:

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| wrist pose 50k scratch e20 | 0.550 | 0.600 | 0.350 | 0.400 | 0.400 | 0.400 |
| control-state 10k scratch e10 | 0.450 | 0.400 | 0.400 | 0.300 | 0.300 | 0.300 |
| control-state mixed 60k scratch e8 | 0.550 | 0.600 | 0.400 | 0.350 | 0.350 | 0.400 |

The mixed model is not promoted yet. It restores clean/visual_camera and nudges
`visual_camera_control` from `0.350` to `0.400`, but this is not a large enough
improvement.

Policy-only control failure analysis is negative:

```text
results\ur5e_full\high_start\hard\visual_audit\control_failure_wrist_pose_control_state_mix_60k_scratch_e8_80ep.md
```

| Model | Episodes | Policy-only success | Collision | Timeout | low-scale success |
| --- | ---: | ---: | ---: | ---: | ---: |
| wrist pose 50k scratch e20 | 80 | 0.237 | 0.438 | 0.325 | 0.059 |
| broad control replay w75 e4 | 80 | 0.250 | 0.400 | 0.350 | 0.000 |
| targeted delay-2 replay w60 e4 | 80 | 0.175 | 0.475 | 0.350 | 0.000 |
| control-state mixed 60k scratch e8 | 80 | 0.125 | 0.562 | 0.312 | 0.000 |

Interpretation:

- The control-state observation path is technically working.
- The current mixed BC model improves guarded `visual_camera_control` only
  slightly and worsens policy-only robustness.
- Do not promote or push this as a version tag.
- Before scaling to 50k more control-state data, run visual ablations that keep
  `control_state` intact. If the model relies too much on `control_state` and
  not enough on image geometry, use frame stacking/recurrent policy or a
  different dataset balance/loss before collecting more data.

## Control-State Image Ablation

Ran image ablations on the mixed 60k control-state checkpoint while preserving
the non-image `control_state` vector. This tests whether the model still uses
visual geometry, or whether `control_state` became a shortcut.

Checkpoint:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_60k_high_start_hard_wrist_pose_control_state_mix_scratch_e8.zip
```

Guarded 20-episode eval:

| Image input | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| normal | 0.550 | 0.600 | 0.400 | 0.350 | 0.350 | 0.400 |
| black | 0.250 | 0.000 | 0.000 | 0.000 | 0.050 | 0.000 |
| noise | 0.250 | 0.100 | 0.050 | 0.000 | 0.050 | 0.000 |
| shuffle | 0.000 | 0.050 | 0.050 | 0.000 | 0.000 | 0.100 |

Policy-only 20-episode eval:

| Image input | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| normal | 0.250 | 0.050 | 0.150 | 0.150 | 0.200 | 0.250 |
| black | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| noise | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shuffle | 0.000 | 0.050 | 0.000 | 0.000 | 0.000 | 0.000 |

Guard-only 20-episode ceiling:

| Mode | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| guard-only | 0.650 | 0.650 | 0.600 | 0.450 | 0.400 | 0.550 |

Interpretation:

- The model is not ignoring images. With `control_state` preserved, corrupting
  images still collapses success from `0.400 - 0.600` to about `0.000 - 0.100`
  in most guarded scenarios.
- Policy-only also depends on images, but its absolute performance is poor:
  `visual_camera_control` is only `0.150` in the 20-episode matrix and `0.125`
  in the 80-episode control failure analysis.
- Guard-only is much stronger than policy-only, especially on
  `visual_camera_control` (`0.600` vs `0.150`). The remaining bottleneck is not
  visual contribution; it is policy control quality and handoff/near-hole
  robustness.
- Do not treat `control_state` as solved. It is a useful input path, but this
  BC model still needs a better temporal/control strategy.

## Frame Stacking Trial

Implemented optional `image_frame_stack` for image observations:

- `cam_image`: `(H, W, K)`
- `near_hole_crop`: `(crop, crop, K)`
- `control_state`: `10 * K`

Default `K=1` preserves old checkpoints/configs. The dataset/training/eval/demo
path now supports `K=3`, including deriving stacks from older single-frame
datasets using `episode_id` and `step_id`.

Smoke result:

```text
datasets\ur5e_full\high_start\hard\image_expert_512_high_start_hard_wrist_pose_control_state_stack3_smoke.npz
checkpoints\ur5e_full\high_start\hard\sac_image_bc_512_high_start_hard_wrist_pose_control_state_stack3_smoke.zip
```

Dataset shapes:

| Array | Shape |
| --- | --- |
| cam_images | `(512, 100, 100, 3)` |
| near_hole_crops | `(512, 64, 64, 3)` |
| control_state | `(512, 30)` |

Training-scale stack3 run:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_60k_high_start_hard_wrist_pose_control_state_mix_stack3_scratch_e6.zip
results\ur5e_full\high_start\hard\visual_audit\training_metadata_wrist_pose_control_state_mix_stack3_scratch_e6.json
```

Training loss:

| Model | Final train loss | Final val loss |
| --- | ---: | ---: |
| control-state mixed 60k stack3 scratch e6 | 0.019360 | 0.021006 |

Same-seed 20-episode guarded eval:

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| control-state mixed 60k scratch e8 | 0.550 | 0.600 | 0.400 | 0.350 | 0.350 | 0.400 |
| control-state mixed 60k stack3 scratch e6 | 0.500 | 0.400 | 0.350 | 0.300 | 0.150 | 0.350 |

Policy-only 80-episode control analysis:

| Model | Episodes | Policy-only success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| control-state mixed 60k scratch e8 | 80 | 0.125 | 0.562 | 0.312 |
| control-state mixed 60k stack3 scratch e6 | 80 | 0.013 | 0.800 | 0.188 |

Interpretation:

- Frame stacking is wired correctly, but this simple `K=3` BC run is not a
  performance improvement.
- The lower validation loss did not translate to better rollout control.
- Do not promote the stack3 checkpoint or push a version tag for it.
- The next attempt should not be "more of the same stack3 BC". It should change
  the supervision/rollout strategy: DAgger-style failure correction,
  phase-aware near-hole labels, or a recurrent/closed-loop policy that is
  evaluated for policy-only robustness early.

## DAgger V2 Handoff Correction

Implemented a DAgger-style correction path for the wrist-pose + `control_state`
model. The key change versus earlier contact-recovery data is that sampling now
starts before the terminal failure window:

- correction collection can run with `include_control_state`
- `selection=near_hole` keeps handoff-region states, not just the final few
  failure steps
- `keep_success_episodes=true` allows useful near-hole corrections from
  successful policy rollouts
- `recovery_branch_from_near_hole=true` can branch from the wider guard handoff
  region, instead of only from low-Z contact-recovery states

2k dataset:

```text
datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_dagger_v2.npz
```

Dataset shape and phase mix:

| Item | Value |
| --- | ---: |
| samples | 2048 |
| control_state shape | `(2048, 10)` |
| visual_camera samples | 1024 |
| visual_camera_control samples | 1024 |
| realign | 1099 |
| slow_insert | 402 |
| unjam_lift | 547 |
| source success/collision/timeout samples | 617 / 831 / 600 |
| recovery branch rate | 0.151 |
| contact recovery window rate | 0.267 |

The phase mix is healthier than the previous staged contact-recovery data:
`realign` and `slow_insert` are no longer drowned by `unjam_lift`.

Training:

```text
checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_dagger_v2_2k_w10_e2.zip
```

This fine-tunes the 60k control-state mixed checkpoint with 10% DAgger v2
correction replay for 2 epochs.

Training loss:

| Model | Final train loss | Final val loss |
| --- | ---: | ---: |
| DAgger v2 2k w10 e2 | 0.047296 | 0.091466 |

Same-seed 20-episode guarded eval:

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| control-state mixed 60k scratch e8 | 0.550 | 0.600 | 0.400 | 0.350 | 0.350 | 0.400 |
| DAgger v2 2k w10 e2 | 0.550 | 0.550 | 0.500 | 0.350 | 0.350 | 0.400 |

80-episode policy-only `visual_camera_control` analysis:

| Model | Episodes | Policy-only success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| control-state mixed 60k scratch e8 | 80 | 0.125 | 0.562 | 0.312 |
| stack3 mixed 60k scratch e6 | 80 | 0.013 | 0.800 | 0.188 |
| DAgger v2 2k w10 e2 | 80 | 0.263 | 0.438 | 0.300 |

Image ablation while preserving `control_state`:

| Mode | Image input | Episodes | visual_camera_control success | Collision | Timeout |
| --- | --- | ---: | ---: | ---: | ---: |
| guarded | normal | 20 | 0.500 | 0.300 | 0.200 |
| guarded | black | 20 | 0.000 | 0.950 | 0.050 |
| guarded | noise | 20 | 0.050 | 0.950 | 0.000 |
| guarded | shuffle | 20 | 0.100 | 0.850 | 0.050 |
| policy-only | normal | 40 | 0.300 | 0.400 | 0.300 |
| policy-only | black | 40 | 0.000 | 1.000 | 0.000 |
| policy-only | noise | 40 | 0.000 | 1.000 | 0.000 |
| policy-only | shuffle | 40 | 0.000 | 0.950 | 0.050 |

Larger validation:

| Check | DAgger v2 | Mixed e8 baseline | Interpretation |
| --- | ---: | ---: | --- |
| guarded 60ep clean, seed 602000 | 0.650 | 0.633 | small positive |
| guarded 60ep visual_camera, seed 602000 | 0.500 | 0.450 | small positive |
| guarded 60ep visual_camera_control, seed 602000 | 0.500 | 0.483 | small positive |
| guarded 60ep full_light_geometry, seed 602000 | 0.400 | 0.367 | small positive |
| guarded 60ep full_contact_light, seed 602000 | 0.417 | 0.417 | flat |
| guarded 60ep hard bucket, seed 602000 | 0.217 | 0.217 | flat |
| policy-only visual_camera_control 160ep, seed 603000 | 0.181 | 0.156 | small positive |
| hard bucket 60ep, seed 604000 | 0.200 | 0.250 | worse |
| hard bucket 60ep, seed 605000 | 0.450 | 0.433 | tiny positive |

Interpretation:

- This is the first post-control-state change that improves policy-only control
  robustness instead of only changing guarded behavior.
- Guarded `visual_camera_control` improves from `0.400` to `0.500`, while clean
  stays flat at `0.550`.
- Collision drops in both guarded `visual_camera_control` and policy-only
  control analysis.
- Image ablation confirms the DAgger v2 checkpoint still depends on visual
  geometry. With `control_state` intact, black/noise/shuffle images collapse
  policy-only success to `0.000`.
- It is still not a final model. Larger-seed validation shows a modest
  visual_camera_control gain, but the hard bucket has no net improvement across
  seeds `602000`, `604000`, and `605000`.

## Next Recommendation

Do not keep scaling correction or targeted control BC blindly yet.

Next work should make the visual/deployment path less privileged and better
framed:

1. Keep the wrist-pose 50k scratch checkpoint as the current new-camera
   comparison model, but do not promote it over the old center-camera demo
   baseline yet.
2. The real-available control/proprio observation path now exists and has passed
   smoke tests.
3. A `10k` control-state run and mixed `60k` scratch run are complete. They are
   not promoted.
4. Image contribution is confirmed. Frame stacking is implemented but the first
   stack3 run regressed.
5. Do not scale the current DAgger v2 recipe to `5k - 10k`; change the
   correction distribution first.
6. Only collect larger `50k` control-state data after DAgger v2 or another
   supervision/control run remains positive under ablation and larger evals.
7. Bias the next correction dataset toward hard-bucket low-Z misalignment and
   geometry/contact failures, then re-run the same image-ablation and
   hard-bucket multi-seed checks.
8. Hard-bucket-focused v3 correction completed this next-step test:
   - 2k v3 data covers both approach/handoff and low-Z states
   - hard-bucket gate average improved to about `0.416 - 0.417` success
   - collision dropped sharply to about `0.145 - 0.167`
   - timeout rose to about `0.417 - 0.439`, so the next bottleneck is
     timeout/descent progress rather than collision
9. Add a real-compatible guard path whose inputs come from estimated visual
   target pose and robot TCP state, not MuJoCo truth.
10. Keep reporting policy-only, guarded, guard-only, and image-ablation metrics
   for every major checkpoint.
