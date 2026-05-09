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

On the `feature/ur5e-mainline` branch, the default simulator uses the
lightweight UR5e adapter at `assets\ur5e_adapter\ur5e_peg_in_hole.xml`. It is
derived from the DeepMind MuJoCo Menagerie UR5e model and keeps the UR5e joint
chain, inertials, actuator style, and simplified collision geoms without
vendoring large visual mesh assets. The older simplified UR5-like model remains
available at `assets\ur5_peg_in_hole.xml` for regression checks.

Check that the default model exposes the task interface names used by the
environment:

```powershell
python scripts\inspect_robot_model.py --output-md results\ur5e\mainline\robot_model_default_ur5e.md --fail-on-missing
```

Check the legacy UR5-like model explicitly:

```powershell
python scripts\inspect_robot_model.py --model-path assets\ur5_peg_in_hole.xml --output-md results\ur5e\mainline\robot_model_legacy_ur5_like.md --fail-on-missing
```

Smoke-test the default UR5e adapter through reset, IK, stepping, and rendering.
Random actions are not expected to succeed; use the oracle command to verify
that the model can complete the task:

```powershell
python scripts\random_rollout.py --observation-mode state --episodes 1
python scripts\random_rollout.py --observation-mode image --episodes 1
python scripts\oracle_rollout.py --observation-mode state --episodes 3
```

All main environment scripts still accept an explicit model override:

```powershell
--model-path assets\ur5_peg_in_hole.xml
```

Use the full UR5e model when demo rendering should show the actual UR5e mesh
and Menagerie collision/inertial model. The branch default remains the lighter
adapter so older training/evaluation numbers stay comparable:

```powershell
python scripts\inspect_robot_model.py `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --output-md results\robot_model_ur5e_full.md `
  --output-json results\robot_model_ur5e_full.json `
  --fail-on-missing

python scripts\oracle_rollout.py `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --observation-mode state `
  --episodes 3 `
  --max-steps 120

python scripts\demo_policy.py `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --observation-mode image `
  --include-near-hole-crop `
  --episodes 1 `
  --max-steps 12 `
  --output results\ur5e_full_demo.gif `
  --render-width 1280 `
  --render-height 720 `
  --render-camera overview
```

Full UR5e short commands are also available through config files:

```powershell
python scripts\eval_matrix.py --config configs\sim\ur5e_full\eval_image_crop.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_guarded_image_crop.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_guarded_image_crop.yaml
```

Current full UR5e task geometry hides the debug `hole_site`, `eef_site`, and
`peg_tip` markers in rendered demos. The peg diameter is about `24 mm`; the
base hole opening is about `40 mm`; geometry-randomized full UR5e configs use
`geometry_hole_half_size_range: [0.017, 0.021]`, i.e. about `34 - 42 mm`
opening. Metrics collected before this change used a wider hole and should be
refreshed before comparison. The main guarded full UR5e demo now uses
`max_steps: 400` so it has time to show the final insertion instead of ending
mid-descent. Full UR5e guarded configs now use
`guarded_align_xy_tolerance: 0.020`, selected from a 30-episode narrow-hole
scan.

Full UR5e visual-adaptation smoke and 50k commands:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_image_expert_smoke.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_image_bc_smoke.yaml
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_image_expert_50k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_image_bc_50k.yaml
```

Current strongest full UR5e adapted commands:

```powershell
python scripts\eval_matrix.py --config configs\sim\ur5e_full\eval_image_narrow_50k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_guarded_narrow_50k_all.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_guarded_narrow_50k_all.yaml
```

Full UR5e narrowed-hole correction pass:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_correction_narrow_smoke.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_smoke.npz `
  --output-md results\ur5e_full\correction\image_correction_narrow_smoke_inspection.md `
  --output-csv results\ur5e_full\correction\image_correction_narrow_smoke_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_correction_narrow_smoke.yaml

python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_correction_narrow_8k.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_8k_min006.npz `
  --output-md results\ur5e_full\correction\image_correction_narrow_8k_inspection.md `
  --output-csv results\ur5e_full\correction\image_correction_narrow_8k_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_correction_narrow_8k_w10_e2.yaml
python scripts\eval_matrix.py --config configs\sim\ur5e_full\eval_image_narrow_correction_8k_w10_e2.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_guarded_narrow_correction_8k_w10_e2.yaml
```

The latest correction checkpoint is:

```text
checkpoints\ur5e_full\correction\sac_image_bc_50k_narrow_correction_8k_w10_e2.zip
```

It is a candidate checkpoint, not the current default, because its 100-episode
results were mostly flat versus the narrowed-hole adapted checkpoint.

Full UR5e narrow-hole guarded scans:

```powershell
python scripts\scan_guarded_policy_params.py --config configs\sim\ur5e_full\scan_guarded_narrow_hole_smoke.yaml
python scripts\scan_guarded_policy_params.py --config configs\sim\ur5e_full\scan_guarded_narrow_hole_focused.yaml
```

Full UR5e high-start visual-search smoke:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_smoke.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_smoke.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_guarded_smoke.yaml
```

Full UR5e high-start 50k curriculum stage:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_50k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_50k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_guarded_50k.yaml
```

The first 50k high-start run completed end to end but is not yet strong enough
to become the default policy. The checkpoint is:

```text
checkpoints\ur5e_full\high_start\sac_image_bc_50k_high_start_visual_camera.zip
```

Collection summary: `50000` samples from `225` successful episodes out of
`1044` attempted episodes, `0.216` oracle success, `0.552` collision. BC
summary: 10 epochs, final train loss `0.062912`, final validation loss
`0.066407`.

100-episode high-start guarded-all result with standard near-hole guard:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| high-start 50k guarded all | 0.190 | 0.240 | 0.180 | 0.170 | 0.220 | 0.150 |

The high-start demo from `demo_high_start_guarded_50k.yaml` timed out at
`1000` steps with final XY about `8.8 mm` and final Z about `47.6 mm`, so this
stage needs an easier curriculum or better high-start oracle before larger XY
randomization.

Full UR5e easy high-start curriculum:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_easy_smoke.yaml
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_easy_20k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_easy_20k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_easy_guarded_20k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_easy_guarded_20k.yaml

python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_easy_50k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_easy_50k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_easy_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_easy_guarded_50k.yaml
```

Current easy high-start checkpoint:

```text
checkpoints\ur5e_full\high_start\easy\sac_image_bc_50k_high_start_easy_visual_camera.zip
```

Easy reset range: `0.08 - 0.15 m` above the hole and `0.04 - 0.10 m` initial
XY offset. Easy 50k collection summary: `50000` samples, `377` episodes,
`0.647` oracle success, `0.119` collision. BC summary: 10 epochs, final train
loss `0.061749`, final validation loss `0.061968`.

Easy 50k 100-episode high-start guarded-all result:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| seed 542000 | 0.670 | 0.540 | 0.500 | 0.530 | 0.530 | 0.530 |
| seed 534000 | 0.620 | 0.630 | 0.590 | 0.580 | 0.540 | 0.480 |

Successful easy 50k demo:

```text
demos\ur5e_full\high_start\easy\demo_high_start_easy_50k_visual_camera_standard_guard_seed534000.gif
```

It inserted in `247` steps from about `6.9 cm` XY offset and `12.0 cm` above
the hole. The default demo seed `542000` timed out, so this checkpoint is a
curriculum stepping stone rather than a final high-start policy.

Full UR5e medium high-start curriculum:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_medium_smoke.yaml
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_medium_20k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_medium_20k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_medium_guarded_20k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_medium_guarded_20k.yaml

python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_medium_50k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_medium_50k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_medium_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_medium_guarded_50k.yaml
```

Current medium high-start checkpoint:

```text
checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip
```

Medium reset range: `0.10 - 0.18 m` above the hole and `0.06 - 0.12 m`
initial XY offset. Medium 50k collection summary: `50000` samples, `287`
episodes, `0.627` oracle success, `0.087` collision. BC summary: 10 epochs,
final train loss `0.045268`, final validation loss `0.044958`.

Medium 50k 100-episode high-start guarded-all result:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| medium 50k | 0.680 | 0.620 | 0.510 | 0.510 | 0.510 | 0.490 |

Successful medium 50k demo:

```text
demos\ur5e_full\high_start\medium\demo_high_start_medium_50k_visual_camera_standard_guard.gif
```

It inserted in `285` steps from about `8.65 cm` XY offset and `11.25 cm`
above the hole.

Full UR5e hard high-start re-test and safe-height curriculum:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_from_medium_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_from_medium_guarded_50k.yaml

python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_safe_smoke.yaml
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_safe_20k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_hard_safe_20k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_safe_20k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_safe_20k.yaml

python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_safe_50k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_hard_safe_50k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_safe_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_safe_50k.yaml
```

Current hard-range candidate:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip
```

Hard range: `0.15 - 0.25 m` above the hole and `0.08 - 0.16 m` initial XY
offset. Hard-safe uses `approach_height: 0.12` and `guard_start_z: 0.12`.

Hard-safe 20k result:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hard-safe 20k | 0.480 | 0.400 | 0.340 | 0.350 | 0.390 | 0.240 |

Hard-safe 50k result:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hard-safe 50k | 0.480 | 0.450 | 0.330 | 0.270 | 0.310 | 0.330 |

Successful hard demos:

```text
demos\ur5e_full\high_start\hard\demo_high_start_hard_from_medium_50k_standard_guard.gif
demos\ur5e_full\high_start\hard\demo_high_start_hard_safe_20k_visual_camera_standard_guard.gif
demos\ur5e_full\high_start\hard\demo_high_start_hard_safe_50k_visual_camera_standard_guard.gif
```

Hard-safe 50k did not clearly beat hard-safe 20k, so the next work should
improve the high-start controller/oracle and collect failure/correction data
instead of continuing to add more success-only hard data.

Two-phase hard high-start controller checks:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_twophase_smoke.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_twophase_hard_safe_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_twophase_hard_safe_50k.yaml
```

This uses `oracle_mode: high_start_two_phase` for collection and
`guarded_oracle_mode: high_start_two_phase` plus
`guard_block_down_when_unaligned: true` for guarded evaluation/demo. The first
100-episode result was mixed:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hard-safe 50k + two-phase guard | 0.490 | 0.340 | 0.320 | 0.350 | 0.350 | 0.270 |

It reduced some collision risk but increased timeout, so this should be tuned
before use as a default.

Hard high-start guard parameter scan and focused validation:

```powershell
python scripts\scan_guarded_policy_params.py --config configs\sim\ur5e_full\scan_high_start_hard_twophase_guarded_smoke.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_align025_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_align025_guarded_50k.yaml
```

The scan compares `guarded_two_stage` vs `high_start_two_phase`, align
thresholds `0.020/0.025/0.030`, and block-down false/true on the hard
high-start reset. The 5-episode smoke did not find a clear two-phase or
block-down improvement. The focused `align=0.025`, `guarded_two_stage`
100-episode result was:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hard-safe 50k + align 0.025 guard | 0.530 | 0.370 | 0.310 | 0.340 | 0.290 | 0.270 |

The corresponding demo timed out at `1000` steps with no collision, final XY
about `8.4 mm`, and final Z about `32.8 mm`. This is not a promoted default;
it points to near-hole plateau correction as the next step.

Hard high-start correction smoke:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_correction_smoke.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_near_hole_plateau_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_smoke_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_correction_smoke.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_correction_smoke.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_correction_smoke.yaml
```

The smoke collected `256` near-hole failure samples from `29` visual_camera
hard high-start episodes. It is high-signal data: `72.3%` opposed actions and
`86.7%` policy-down/oracle-up-or-less-down. The 1-epoch weighted BC smoke is
not a default checkpoint; same-seed 20-episode evaluation was mixed and the
demo still timed out near `8.4 mm` XY error.

Current narrowed-hole full UR5e adapted checkpoint:

```text
checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip
```

Pre-narrow-hole full UR5e adapted checkpoint:

```text
checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip
```

Checked full UR5e result before adaptation, using the adapter-trained image policy:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy only | 0.080 | 0.260 | 0.250 | 0.140 | 0.150 | - |
| guarded blend 0.75 | 0.080 | 0.260 | 0.250 | 0.620 | 0.650 | 0.590 |

Checked full UR5e result after 50k full-model BC adaptation, before the
narrow-hole geometry update:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy only | 0.950 | 0.660 | 0.610 | 0.680 | 0.650 | - |
| guarded geometry | 0.950 | 0.660 | 0.610 | 0.840 | 0.840 | 0.810 |
| guarded all | 0.990 | 0.970 | 0.950 | 0.840 | 0.840 | 0.820 |

Checked after hiding full UR5e debug markers and narrowing the hole to about
`40 mm` base opening, using the same adapted checkpoint and guarded-all mode:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| guarded all, 10 episodes | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.700 |
| guarded all, 30 episodes, align 0.025 | 0.800 | 0.800 | 0.800 | 0.767 | 0.767 | 0.667 |
| guarded all, 30 episodes, align 0.020, blend 1.0 | 0.933 | 0.900 | 0.833 | 0.867 | 0.867 | 0.800 |
| guarded all, 100 episodes, align 0.020, blend 1.0 | 0.970 | 0.910 | 0.860 | 0.830 | 0.830 | 0.770 |

Policy-only 100-episode narrowed-hole baseline:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact |
| --- | ---: | ---: | ---: | ---: | ---: |
| policy only | 0.750 | 0.690 | 0.640 | 0.600 | 0.620 |

After collecting and training the 50k narrowed-hole dataset:

```text
datasets\ur5e_full\adapt\image_expert_50k_narrow_hole_full_light_geometry.npz
checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip
```

Collection summary: `50000` samples, `545` episodes, `0.824` success, `0.154`
collision. BC summary: 10 epochs, final train loss `0.039346`, final validation
loss `0.041165`.

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy only, 100 episodes | 0.850 | 0.800 | 0.740 | 0.740 | 0.740 | - |
| guarded all, 100 episodes | 0.980 | 0.930 | 0.860 | 0.830 | 0.840 | 0.780 |

After the narrowed-hole correction pass:

```text
datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_8k_min006.npz
checkpoints\ur5e_full\correction\sac_image_bc_50k_narrow_correction_8k_w10_e2.zip
```

The command requested 8k correction samples, but the strict
`min_correction_norm=0.006` filter and `max_episodes_per_config=2000` cap
produced `1836` high-signal samples. Weighted BC used 90% narrowed-hole expert
replay and 10% correction replay for 2 epochs.

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| correction policy only, 100 episodes | 0.870 | 0.780 | 0.760 | 0.750 | 0.720 | - |
| correction guarded all, 100 episodes | 0.970 | 0.940 | 0.870 | 0.830 | 0.840 | 0.780 |

The refreshed demo with `guarded_align_xy_tolerance=0.020` and
`guard_blend=1.0` succeeded in `91` steps and was written to:

```text
demos\ur5e_full\adapt\demo_guarded_all_50k_narrow_hole_full_light_geometry.gif
```

The current best full UR5e demo/deployment-style simulation is the adapted
checkpoint `checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip`
with `guard_scenario_filter=all`, `guarded_align_xy_tolerance=0.020`, and
`guard_blend=1.0`. The remaining weakness is the `0.13 - 0.18` collision rate
under visual_camera_control/full/hard conditions.

Checked high-start smoke:

| Stage | Domain | Result |
| --- | --- | --- |
| reset | high-start | starts about `0.15 - 0.25 m` above and `0.08 - 0.16 m` away in XY |
| oracle smoke | visual_camera | `1.000` success, `0.000` collision |
| oracle smoke | full_light_geometry | too hard for first stage: `0.143` success, `0.571` collision |
| BC smoke | visual_camera | 1 epoch completed |

Use `visual_camera` as the first high-start curriculum stage. Add control and
geometry randomization only after high-start search works reliably.

UR5e mainline branch verification:

```powershell
python scripts\eval_matrix.py --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\ur5e\mainline\eval_matrix_default_ur5e_750k_crop.csv --output-md results\ur5e\mainline\eval_matrix_default_ur5e_750k_crop.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_guarded_policy.py --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --seed 90000 --device cpu --include-hard-bucket --output-csv results\ur5e\mainline\eval_guarded_default_ur5e_750k_blend075.csv --output-md results\ur5e\mainline\eval_guarded_default_ur5e_750k_blend075.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --guard-scenario-filter geometry --guard-start-xy 0.06 --guard-start-z 0.08 --guard-risk-xy 0.0 --guard-blend 0.75 --guard-min-policy-steps 0
```

The same UR5e mainline commands are now available as config-driven short
commands. These use the branch-default UR5e model and the recommended
near-hole crop policy:

```powershell
python scripts\eval_matrix.py --config configs\sim\ur5e\eval_image_crop.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e\eval_guarded_image_crop.yaml
python scripts\demo_policy.py --config configs\sim\ur5e\demo_guarded_image_crop.yaml
python scripts\scan_guarded_policy_params.py --config configs\sim\ur5e\scan_guarded_policy_focused.yaml
```

Structured-layout smoke for future UR5e data and BC experiments:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e\collect_image_expert_smoke.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e\pretrain_image_bc_smoke.yaml
```

For MP4 demo output, install the current dependency set:

```powershell
python -m pip install -r requirements.txt
```

If the MP4 backend is still unavailable, `demo_policy.py` automatically saves a
same-stem GIF fallback.

Checked UR5e mainline result:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy only | 0.980 | 0.980 | 0.920 | 0.580 | 0.600 | - |
| guarded blend 0.75 | 0.980 | 0.980 | 0.910 | 0.710 | 0.640 | 0.530 |

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

Late-activation follow-up:

```powershell
python scripts\scan_guarded_policy_params.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 100 `
  --seed 90000 `
  --device cpu `
  --preset grid `
  --scenario-preset core `
  --guard-scenario-filter geometry `
  --guard-start-xy-values 0.03 0.06 `
  --guard-start-z-values 0.08 0.10 `
  --guard-blend-values 0.75 `
  --guard-min-policy-step-values 0 `
  --guarded-max-down-action-values 0.0035 `
  --guarded-align-xy-tolerance-values 0.025 `
  --output-csv results\guarded_policy_late_activation_validation_100ep.csv `
  --output-md results\guarded_policy_late_activation_validation_100ep.md `
  --approach-xy-tolerance 0.02 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01
```

Current guarded deployment recommendation:

```text
guard_scenario_filter = geometry
guard_start_xy = 0.06
guard_start_z = 0.08
guard_blend = 0.75
guard_min_policy_steps = 0
```

`guard_min_policy_steps` is available in `eval_guarded_policy.py`,
`run_policy_inference.py`, and `scan_guarded_policy_params.py`, but keep it at
`0` for the current policy. Delaying guard activation reduced guard steps but
lost hard-bucket recovery. Full details are in
`results\guarded_late_activation_summary.md`.

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
  --guard-blend 0.75 `
  --guard-start-z 0.08 `
  --guard-min-policy-steps 0
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
  --guard-start-z 0.08 `
  --guard-min-policy-steps 0
```

Result:

| Scenario | Configuration | Success | Collision | Steps | Guard steps |
| --- | --- | ---: | ---: | ---: | ---: |
| visual_camera_control | guarded geometry blend 0.75 | 1 | 0 | 10 | 0 |
| hard bucket | no guard | 0 | 1 | 11 | 0 |
| hard bucket | guarded geometry blend 0.75 | 1 | 0 | 34 | 34 |

Trace CSVs include `guard_enabled`, `guard_active`, `policy_action_*`,
`guard_should_activate`, `guard_can_activate`, `guard_activated`,
`guard_down_blocked`, `guard_dist_xy`, `guard_z_above_target`,
`guarded_action_*`, `final_action_*`, `raw_action_*`, and `safe_action_*`.
Full details are in `results\policy_inference_guarded_summary.md`.

Run the matching HD deployment demos:

```powershell
python scripts\demo_policy.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --seed 90005 `
  --device cpu `
  --output demos\guarded_deployment_hard_bucket_no_guard_z08_hd.gif `
  --trajectory-output demos\guarded_deployment_hard_bucket_no_guard_z08_trajectory.csv `
  --width 100 `
  --height 100 `
  --render-width 640 `
  --render-height 480 `
  --render-cameras overview wrist_cam `
  --fps 20 `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02
```

```powershell
python scripts\demo_policy.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --seed 90005 `
  --device cpu `
  --output demos\guarded_deployment_hard_bucket_guarded_z08_hd.gif `
  --trajectory-output demos\guarded_deployment_hard_bucket_guarded_z08_trajectory.csv `
  --width 100 `
  --height 100 `
  --render-width 640 `
  --render-height 480 `
  --render-cameras overview wrist_cam `
  --fps 20 `
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
  --guard-start-z 0.08 `
  --guard-min-policy-steps 0
```

```powershell
python scripts\demo_policy.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --seed 90000 `
  --device cpu `
  --output demos\guarded_deployment_full_light_guarded_z08_hd.gif `
  --trajectory-output demos\guarded_deployment_full_light_guarded_z08_trajectory.csv `
  --width 100 `
  --height 100 `
  --render-width 640 `
  --render-height 480 `
  --render-cameras overview wrist_cam `
  --fps 20 `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.2 `
  --control-action-noise-std-range 0 0.0008 `
  --control-action-delay-range 0 2 `
  --control-action-filter-alpha-range 0.55 1.0 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-name full_light_geometry `
  --guard-blend 0.75 `
  --guard-start-xy 0.06 `
  --guard-start-z 0.08 `
  --guard-min-policy-steps 0
```

The saved GIFs are `1280x480` because two `640x480` camera views are
concatenated. The summarized demo outcomes are in
`results\guarded_deployment_demo_summary.md`.

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
| wide_legacy | 14.9 mm | 0.600 | 0.400 | 0.633 |
| medium | 9.9 mm | 0.667 | 0.333 | 0.567 |
| narrow | 6.9 mm | 0.533 | 0.367 | 0.600 |
| tight | 4.4 mm | 0.467 | 0.267 | 0.533 |

Use `medium` as the next curriculum target, mixed with current wide clearance.
Do not jump directly to narrow/tight as the default distribution; hard-control
success is still too low. Full details are in
`results\geometry_clearance_scan_summary.md`.

## Medium Clearance Dataset Diagnostics

Expert collection now writes v2 diagnostic arrays into new `.npz` files:
`hole_half_size`, `peg_radius`, `hole_clearance`, `hole_center_offset`,
control scale/noise/delay/filter values, fixture/table height offsets, and
contact/dynamics multipliers. Metadata also records success, collision,
timeout, kept-episode rates, array shapes, and summary diagnostics.

Inspect any image expert dataset:

```powershell
python scripts\inspect_image_expert_dataset.py `
  --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_smoke_oracle.npz `
  --output-md results\image_expert_medium_guarded_success_smoke_inspection.md `
  --output-csv results\image_expert_medium_guarded_success_smoke_inspection.csv
```

Medium clearance guarded smoke:

```powershell
python scripts\collect_image_expert_dataset.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_smoke_oracle.npz `
  --samples 500 `
  --seed 940000 `
  --image-width 100 `
  --image-height 100 `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --expert-action-gain 1.0 `
  --oracle-mode guarded_two_stage `
  --guarded-align-xy-tolerance 0.025 `
  --guarded-insert-xy-tolerance 0.005 `
  --guarded-retract-xy-tolerance 0.012 `
  --guarded-preinsert-height 0.000 `
  --guarded-max-xy-action 0.005 `
  --guarded-max-down-action 0.0035 `
  --guarded-max-up-action 0.005 `
  --guarded-prediction-steps 1.0 `
  --rollout-noise-std 0.0005 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --domain-randomization-level full_light_geometry `
  --geometry-hole-half-size-range 0.020 0.024 `
  --geometry-peg-radius-range 0.0115 0.0125 `
  --success-only `
  --compressed
```

Medium clearance hard-control guarded smoke:

```powershell
python scripts\collect_image_expert_dataset.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_smoke_oracle.npz `
  --samples 500 `
  --seed 941000 `
  --image-width 100 `
  --image-height 100 `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --expert-action-gain 1.0 `
  --oracle-mode guarded_two_stage `
  --guarded-align-xy-tolerance 0.025 `
  --guarded-insert-xy-tolerance 0.005 `
  --guarded-retract-xy-tolerance 0.012 `
  --guarded-preinsert-height 0.000 `
  --guarded-max-xy-action 0.005 `
  --guarded-max-down-action 0.0035 `
  --guarded-max-up-action 0.005 `
  --guarded-prediction-steps 1.0 `
  --rollout-noise-std 0.0005 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --domain-randomization-level full_light_geometry `
  --geometry-hole-half-size-range 0.020 0.024 `
  --geometry-peg-radius-range 0.0115 0.0125 `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --success-only `
  --compressed
```

Checked 500-sample smoke result:

| Dataset | Episodes | Success | Collision | Mean clearance | Mean delay | Mean alpha |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| medium guarded success | 58 | 0.603 | 0.345 | 9.93 mm | 1.11 | 0.777 |
| medium hard guarded success | 87 | 0.299 | 0.701 | 10.36 mm | 2.00 | 0.627 |

Full 50k checked result:

| Dataset | Episodes | Success | Collision | Mean clearance | Mean delay | Mean alpha |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| medium guarded success 50k | 5142 | 0.579 | 0.385 | 10.05 mm | 0.88 | 0.785 |
| medium hard guarded success 50k | 8096 | 0.345 | 0.647 | 10.11 mm | 2.00 | 0.628 |

The full datasets are:

```text
datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_50k_oracle.npz
datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_50k_oracle.npz
```

Inspect the full datasets:

```powershell
python scripts\inspect_image_expert_dataset.py --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_50k_oracle.npz --output-md results\image_expert_medium_guarded_success_50k_inspection.md --output-csv results\image_expert_medium_guarded_success_50k_inspection.csv
python scripts\inspect_image_expert_dataset.py --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_50k_oracle.npz --output-md results\image_expert_medium_hard_guarded_success_50k_inspection.md --output-csv results\image_expert_medium_hard_guarded_success_50k_inspection.csv
```

Medium replay continuation from the current 750k crop model:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_50k_oracle.npz --dataset-weights 0.255 0.102 0.085 0.128 0.051 0.034 0.068 0.085 0.042 0.100 0.050 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2\sac_image_bc.zip --epochs 2 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000001 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the medium replay candidate:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\scan_geometry_clearance.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2\sac_image_bc.zip --tier-preset wide_medium --scenario-preset targeted --episodes 30 --seed 960000 --device cpu --output-csv results\geometry_clearance_scan_medium_replay_light_850k_targeted_30ep.csv --output-md results\geometry_clearance_scan_medium_replay_light_850k_targeted_30ep.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02
```

Medium replay result:

| Model | Clean | Visual camera | Visual camera control | Full light | Full contact |
| --- | ---: | ---: | ---: | ---: | ---: |
| medium replay e4 | 0.960 | 0.970 | 0.860 | 0.540 | 0.570 |
| medium replay light e2 | 0.970 | 0.980 | 0.900 | 0.550 | 0.660 |

Do not promote either medium replay as the current recommendation. The light
replay improves `full_contact_light`, but `full_light_geometry` remains below
the current 750k baseline. The next iteration should add near-failure
correction/DAgger-style data instead of only raising medium success-only replay
weight.

## Policy vs Oracle Correction Analysis

Use this analysis before collecting corrective data. It executes the learned
policy, queries the guarded two-stage oracle on the same pre-step state, and
logs the policy action, oracle action, correction vector, near-hole flag, and
whether the row falls in the last few steps before a collision or timeout.

```powershell
python scripts\analyze_policy_oracle_corrections.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 50 `
  --device cpu `
  --seed 980000 `
  --scenario-preset targeted `
  --tier-preset wide_medium `
  --output-csv results\policy_oracle_corrections_750k_targeted_50ep_steps.csv `
  --episode-output-csv results\policy_oracle_corrections_750k_targeted_50ep_episodes.csv `
  --output-md results\policy_oracle_corrections_750k_targeted_50ep.md
```

Checked result:

| Tier | Scenario | Success | Collision | Failure corr | Failure opposed | Policy down / oracle up |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| wide_legacy | full_light_geometry | 0.640 | 0.360 | 0.005 | 0.035 | 0.065 |
| wide_legacy | hard_full_light_bucket | 0.320 | 0.680 | 0.004 | 0.007 | 0.070 |
| medium | full_light_geometry | 0.660 | 0.300 | 0.005 | 0.189 | 0.125 |
| medium | hard_full_light_bucket | 0.400 | 0.560 | 0.004 | 0.076 | 0.059 |

The main signal is medium `full_light_geometry`: in the failure window,
policy-vs-oracle action opposition is much higher than wide
`full_light_geometry`. The next data collection pass should target rows with
`failure_window=True`, high `correction_norm`, and preferably `near_hole=True`
as DAgger-style corrective samples.

## Near-Hole Correction Dataset

Collect focused DAgger-style corrective samples from policy-visited failure
windows. This pass keeps only medium-clearance near-hole rows with
`correction_norm >= 0.006`.

```powershell
python scripts\collect_image_correction_dataset.py `
  --agent sac `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --output datasets\image_correction_ur5e_adapter_medium_targeted_near_hole_failure_window_10k_min006_oracle.npz `
  --samples 10000 `
  --max-episodes-per-config 9000 `
  --scenario-preset targeted `
  --tier-preset medium `
  --selection near_hole_failure_window `
  --failure-window-steps 10 `
  --near-hole-xy 0.03 `
  --near-hole-z 0.10 `
  --min-correction-norm 0.006 `
  --max-samples-per-episode 6 `
  --include-near-hole-crop `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --compressed
```

Inspect correction-specific signals:

```powershell
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\image_correction_ur5e_adapter_medium_targeted_near_hole_failure_window_10k_min006_oracle.npz `
  --output-md results\image_correction_medium_targeted_near_hole_failure_window_10k_min006_correction_inspection.md `
  --output-csv results\image_correction_medium_targeted_near_hole_failure_window_10k_min006_correction_inspection.csv
```

Actual collected dataset: `8405` samples from `16003` policy episodes. It is
more focused than the first 2k correction pass: near-hole rate `1.000`,
opposed-action rate `0.470`, mean correction norm `0.00960`.

The best correction candidate so far is the 8% correction, 1 epoch variant:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz datasets\image_correction_ur5e_adapter_medium_targeted_near_hole_failure_window_10k_min006_oracle.npz `
  --dataset-weights 0.276 0.110 0.092 0.138 0.055 0.037 0.074 0.092 0.046 0.080 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1\sac_image_bc.zip `
  --metadata-output results\training_metadata_correction_nearhole_8k_w08_replay_858k_oracle_e1.json `
  --epochs 1 `
  --samples-per-epoch 200000 `
  --batch-size 512 `
  --learning-rate 0.0000008 `
  --validation-batches 20 `
  --approach-xy-tolerance 0.02 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --device cpu
```

Evaluate it:

```powershell
python scripts\eval_matrix.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1\sac_image_bc.zip `
  --episodes 100 `
  --seed 90000 `
  --device cpu `
  --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1.csv `
  --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1.md `
  --approach-xy-tolerance 0.02 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01
```

Correction experiment result:

| Model | Clean | Visual camera | Control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| 750k baseline | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 |
| correction 8k w08 e1 | 0.980 | 0.980 | 0.900 | 0.590 | 0.630 |
| correction 8k w05 e2 | 0.980 | 0.970 | 0.930 | 0.570 | 0.630 |
| correction 8k w08 e2 | 0.960 | 0.950 | 0.910 | 0.590 | 0.630 |

Do not promote the correction models yet. The e1 variant is a useful candidate,
but the gain is modest and not consistent across the medium/hard geometry scan.
Full details are in `results\correction_nearhole_8k_experiment_summary.md`.

Outcome-specific correction collection is supported with
`--episode-outcome-filter`. This is useful for diagnostics because collision
and timeout failure windows have different action-disagreement profiles:

```powershell
python scripts\collect_image_correction_dataset.py `
  --agent sac `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --output datasets\image_correction_ur5e_adapter_wide_medium_targeted_near_hole_collision_window_4k_min006_oracle.npz `
  --samples 4000 `
  --max-episodes-per-config 5000 `
  --scenario-preset targeted `
  --tier-preset wide_medium `
  --selection near_hole_failure_window `
  --episode-outcome-filter collision `
  --failure-window-steps 10 `
  --near-hole-xy 0.03 `
  --near-hole-z 0.10 `
  --min-correction-norm 0.006 `
  --max-samples-per-episode 6 `
  --include-near-hole-crop `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --compressed
```

```powershell
python scripts\collect_image_correction_dataset.py `
  --agent sac `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --output datasets\image_correction_ur5e_adapter_wide_medium_targeted_near_hole_timeout_window_4k_min006_oracle.npz `
  --samples 4000 `
  --max-episodes-per-config 5000 `
  --scenario-preset targeted `
  --tier-preset wide_medium `
  --selection near_hole_failure_window `
  --episode-outcome-filter timeout `
  --failure-window-steps 10 `
  --near-hole-xy 0.03 `
  --near-hole-z 0.10 `
  --min-correction-norm 0.006 `
  --max-samples-per-episode 6 `
  --include-near-hole-crop `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --compressed
```

Outcome-split result:

| Model | Clean | Visual camera | Control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| 750k baseline | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 |
| outcome split w04w04 e1 | 0.980 | 0.980 | 0.910 | 0.560 | 0.600 |
| outcome split w06w02 e1 | 0.980 | 0.980 | 0.900 | 0.580 | 0.590 |

Do not promote outcome-split correction models. Timeout correction rows are
diagnostically strong but conflict with success-replay BC when oversampled.
Full details are in `results\correction_outcome_split_6k_experiment_summary.md`.

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
Guarded deployment now follows the same adapter structure:
`MujocoGuardStateProvider` converts MuJoCo telemetry into
`GuardedDeploymentState`, while `RealGuardStateProvider` does the same for
real-robot dry-run telemetry.

Use a smoother action safety layer:

```powershell
python scripts\run_policy_inference.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 1 --output results\policy_inference_trace_smooth.csv --device cpu --domain-randomization-level full_contact_light --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --safety-action-filter-alpha 0.6
```

## Real Backend Dry Run

UR5e branch note: the current recommended real dry-run config lives under
`configs\real\ur5e\`. It enables `include_near_hole_crop: true`, because the
current recommended UR5e image policy expects both `cam_image` and
`near_hole_crop`.

Prepare an ignored local real-data read-only session:

```powershell
python scripts\prepare_real_ur5e_session.py `
  --session-id real_ur5e_YYYYMMDD `
  --ur-host <UR5E_IP> `
  --camera-device-index 0 `
  --overwrite
```

This writes:

- `configs\real\ur5e\real_ur5e_YYYYMMDD_local.yaml`
- `results\real\ur5e\real_ur5e_YYYYMMDD\COMMANDS.md`

Edit the local YAML before running the generated commands. The strict real
preflight now requires measured `crop_xywh`, camera intrinsics, and
`tool0_to_camera_*` values:

Tune camera crop and orientation from recorded frames:

```powershell
python scripts\inspect_real_camera_crop.py `
  --input results\real\ur5e\real_ur5e_YYYYMMDD\camera_tuning_frames `
  --output-dir results\real\ur5e\real_ur5e_YYYYMMDD\crop_inspection `
  --summary-md results\real\ur5e\real_ur5e_YYYYMMDD\crop_inspection_summary.md `
  --stats-output results\real\ur5e\real_ur5e_YYYYMMDD\crop_inspection_stats.csv `
  --output-json results\real\ur5e\real_ur5e_YYYYMMDD\crop_inspection_summary.json `
  --auto-crop-fractions 0.50 0.65 0.80 `
  --auto-offset-fraction 0.15 `
  --include-flips `
  --max-combinations 240
```

Use the top-ranked candidate only as a starting point. Inspect the preview
sheets before copying the config snippet.

```powershell
python scripts\check_real_deployment_config.py `
  --config configs\real\ur5e\real_ur5e_YYYYMMDD_local.yaml `
  --target-calibration results\real\ur5e\real_ur5e_YYYYMMDD\target_calibration.yaml `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --require-camera-calibration `
  --require-image-crop `
  --fail-on-warn `
  --output-md results\real\ur5e\real_ur5e_YYYYMMDD\config_check.md `
  --output-json results\real\ur5e\real_ur5e_YYYYMMDD\config_check.json
```

UR5e read-only software gate smoke:

```powershell
python scripts\check_real_deployment_config.py `
  --config configs\real\ur5e\synthetic_smoke.yaml `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --output-md results\real\ur5e\smoke\config_check.md `
  --output-json results\real\ur5e\smoke\config_check.json

python scripts\run_real_dryrun_preflight.py `
  --config configs\real\ur5e\synthetic_smoke.yaml `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --max-steps 4 `
  --trace-output results\real\ur5e\smoke\dryrun_trace.csv `
  --check-output-md results\real\ur5e\smoke\dryrun_check.md `
  --check-output-json results\real\ur5e\smoke\dryrun_check.json `
  --summary-md results\real\ur5e\smoke\dryrun_summary.md `
  --allow-action-limited

python scripts\check_real_motion_readiness.py `
  --bundle-summary-json results\real\ur5e\smoke\capture_bundle_summary.json `
  --allow-synthetic `
  --allow-smoke-paths `
  --output-md results\real\ur5e\smoke\motion_readiness_synthetic_allowed.md `
  --output-json results\real\ur5e\smoke\motion_readiness_synthetic_allowed.json

python scripts\inspect_real_camera_crop.py `
  --synthetic-smoke `
  --output-dir results\real\ur5e\smoke\crop_inspection `
  --stats-output results\real\ur5e\smoke\crop_inspection_stats.csv `
  --summary-md results\real\ur5e\smoke\crop_inspection_summary.md `
  --output-json results\real\ur5e\smoke\crop_inspection_summary.json `
  --max-frames 3 `
  --auto-crop-fractions 0.60 0.80 `
  --auto-offset-fraction 0.10 `
  --include-flips `
  --max-combinations 160
```

Checked UR5e real smoke outputs:

| Gate | Result | Summary |
| --- | --- | --- |
| config check | PASS | `results\real\ur5e\smoke\config_check.md` |
| dry-run preflight | PASS | `results\real\ur5e\smoke\dryrun_summary.md` |
| crop/orientation inspection | PASS | `results\real\ur5e\smoke\crop_inspection_summary.md` |
| synthetic capture bundle | PASS | `results\real\ur5e\smoke\capture_bundle_summary.md` |
| readiness with synthetic allowed | PASS | `results\real\ur5e\smoke\motion_readiness_synthetic_allowed.md` |
| readiness default synthetic gate | FAIL expected | `results\real\ur5e\smoke\motion_readiness_synthetic_expected_fail.md` |

Check the static real deployment configuration before recording real camera or
UR TCP data. This does not connect to hardware:

```powershell
python scripts\check_real_deployment_config.py `
  --config configs\real_ur5_dryrun.yaml `
  --target-calibration configs\real_hole_target_calibration.yaml `
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip `
  --expected-pose-frame robot_base `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --output-md results\real_deployment_config_check.md `
  --output-json results\real_deployment_config_check.json
```

Smoke-test the static configuration checker without hardware:

```powershell
python scripts\check_real_deployment_config.py `
  --config configs\real_ur5_dryrun.yaml `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --output-md results\real_deployment_config_check_synthetic_smoke.md `
  --output-json results\real_deployment_config_check_synthetic_smoke.json
```

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

Run the real dry-run path with guarded final insertion enabled. This still does
not move hardware; it only checks the provider, policy/zero-policy, safety
filter, guarded controller, and trace logging path:

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 2 `
  --peg-tip-pos 0.55 0.05 0.72 `
  --target-pos 0.55 0.05 0.65 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_guarded_smoke.csv
```

Guarded interface refactor details and smoke results are in
`results\guarded_deployment_interface_refactor_summary.md`.

Run the same guarded dry-run path with a per-step pose CSV instead of static
`--peg-tip-pos` and `--target-pos` values:

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --pose-trace configs\real_pose_trace_smoke.csv `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_pose_trace_guarded_smoke.csv
```

Pose trace CSVs should provide `peg_tip_x/y/z` and `target_x/y/z` in meters in
the same frame. `tcp_x/y/z` and `hole_x/y/z` are accepted aliases. The trace
output includes `pose_source`, `pose_frame`, `pose_step`, and `pose_timestamp`.
Details are in `results\real_pose_trace_dryrun_summary.md`.

Run the dry-run path with UR-style TCP pose traces. `tcp_rx/ry/rz` are UR
rotation-vector values in radians, and `--tcp-to-peg-tip-xyz` is the measured
offset from the active TCP/tool frame to the peg tip:

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-pose-trace configs\real_tcp_pose_trace_smoke.csv `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_tcp_pose_guarded_smoke.csv
```

Run TCP trace replay with a separate fixed hole/fixture calibration file. This
is the preferred dry-run structure when TCP pose comes from UR RTDE and target
pose comes from fixture registration or hand-eye calibration:

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-pose-trace configs\real_tcp_pose_trace_no_target_smoke.csv `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_target_calibration_guarded_smoke.csv
```

The output trace includes `target_source`, `target_frame`, and
`target_timestamp`. Details are in
`results\real_target_calibration_dryrun_summary.md`.

Check a dry-run trace before using it for real deployment decisions. The
checker validates required trace columns, pose/target frames and sources,
safe-action limits, workspace clipping, guard activation behavior, distance
consistency, and optional TCP-to-peg-tip conversion:

```powershell
python scripts\check_real_dryrun_trace.py `
  --trace results\real_policy_dryrun_target_calibration_guarded_smoke.csv `
  --output-md results\real_dryrun_trace_check_target_calibration_smoke.md `
  --max-safe-action 0.002 `
  --expected-pose-frame robot_base `
  --require-nonstatic-target `
  --tcp-to-peg-tip-xyz 0 0 -0.11
```

For older TCP-pose and direct pose-trace smoke files:

```powershell
python scripts\check_real_dryrun_trace.py `
  --trace results\real_policy_dryrun_tcp_pose_guarded_smoke.csv `
  --output-md results\real_dryrun_trace_check_tcp_pose_smoke.md `
  --max-safe-action 0.002 `
  --expected-pose-frame robot_base `
  --tcp-to-peg-tip-xyz 0 0 -0.11

python scripts\check_real_dryrun_trace.py `
  --trace results\real_policy_dryrun_pose_trace_guarded_smoke.csv `
  --output-md results\real_dryrun_trace_check_pose_trace_smoke.md `
  --max-safe-action 0.002 `
  --expected-pose-frame robot_base
```

The current checker smoke summary is in
`results\real_dryrun_trace_checker_summary.md`.

Build a fixed hole/fixture target calibration file from repeated target
measurements. The measurement CSV should contain `target_x/y/z` or `hole_x/y/z`
in meters, plus an optional frame column such as `target_frame` or
`pose_frame`:

Record repeated hole/target measurements from UR RTDE. This is read-only: move
the robot manually or by teach pendant so that the active TCP is at the measured
hole target point, then record samples. If the active TCP is not exactly the
target point, provide the measured TCP-frame offset with `--tcp-to-target-xyz`:

```powershell
python scripts\record_ur_rtde_target_measurements.py `
  --host 192.168.0.10 `
  --samples 20 `
  --frequency-hz 5 `
  --pose-frame robot_base `
  --target-id real_hole `
  --tcp-to-target-xyz 0 0 0 `
  --output results\real_hole_measurements.csv `
  --summary-md results\real_hole_measurements_summary.md
```

Smoke-test the target measurement recorder without hardware:

```powershell
python scripts\record_ur_rtde_target_measurements.py `
  --synthetic-smoke `
  --samples 6 `
  --frequency-hz 100 `
  --output results\real_hole_measurements_synthetic_smoke.csv `
  --summary-md results\real_hole_measurements_synthetic_smoke_summary.md
```

Convert the recorded measurement CSV into the fixed target calibration consumed
by the real dry-run and preflight scripts:

```powershell
python scripts\make_real_target_calibration.py `
  --input-csv results\real_hole_measurements.csv `
  --output configs\real_hole_target_calibration.yaml `
  --summary-md results\real_target_calibration_builder_summary.md `
  --target-id real_hole `
  --target-source fixture_calibration `
  --pose-frame robot_base `
  --method mean
```

If you already have one trusted measured target position:

```powershell
python scripts\make_real_target_calibration.py `
  --target-pos 0.550 0.050 0.650 `
  --output configs\real_hole_target_calibration.yaml `
  --summary-md results\real_target_calibration_builder_summary.md
```

Smoke-test the builder without hardware:

```powershell
python scripts\make_real_target_calibration.py `
  --synthetic-smoke `
  --synthetic-input-output results\real_target_calibration_builder_synthetic_input.csv `
  --output configs\real_hole_target_calibration_generated_smoke.yaml `
  --summary-md results\real_target_calibration_builder_smoke_summary.md
```

Run the complete real dry-run preflight gate. This wrapper first runs
`run_real_policy_dryrun.py`, then runs `check_real_dryrun_trace.py`, and finally
writes a compact summary. It still does not command robot motion:

```powershell
python scripts\run_real_dryrun_preflight.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-pose-trace configs\real_tcp_pose_trace_no_target_smoke.csv `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --trace-output results\real_policy_dryrun_preflight_target_calibration_smoke.csv `
  --check-output-md results\real_dryrun_preflight_target_calibration_check.md `
  --summary-md results\real_dryrun_preflight_target_calibration_summary.md
```

For a real preflight, replace the smoke TCP CSV with a trace recorded from UR
RTDE and replace the target calibration file with the measured fixture/hole
calibration. The default preflight requires non-static pose and target sources,
uses guarded final insertion, and fails on checker errors.

Record a read-only UR RTDE TCP pose trace for later dry-run replay. This script
does not command robot motion:

```powershell
python scripts\record_ur_rtde_tcp_pose_trace.py `
  --host 192.168.0.10 `
  --samples 200 `
  --frequency-hz 20 `
  --pose-frame robot_base `
  --target-pos 0.55 0.05 0.65 `
  --output results\ur_rtde_tcp_pose_trace.csv
```

When the hole target comes from a separate fixture calibration, omit embedded
target columns so the dry-run path uses `--target-calibration` instead of a
target pose inside the TCP trace:

```powershell
python scripts\record_ur_rtde_tcp_pose_trace.py `
  --host 192.168.0.10 `
  --samples 200 `
  --frequency-hz 20 `
  --pose-frame robot_base `
  --no-target-columns `
  --output results\ur_rtde_tcp_pose_trace.csv
```

Smoke-test the recorder without a robot:

```powershell
python scripts\record_ur_rtde_tcp_pose_trace.py `
  --synthetic-smoke `
  --samples 4 `
  --frequency-hz 100 `
  --output results\ur_rtde_tcp_pose_trace_synthetic_smoke.csv
```

Record raw frames from a real USB/RTSP camera before running the camera
preflight. Live recording uses OpenCV; install it if needed with
`python -m pip install opencv-python`:

```powershell
python scripts\record_real_camera_frames.py `
  --device-index 0 `
  --frames 20 `
  --frequency-hz 5 `
  --warmup-frames 10 `
  --output-dir results\real_camera_frames `
  --stats-output results\real_camera_frames_stats.csv `
  --summary-md results\real_camera_frames_summary.md
```

For an RTSP or other OpenCV source, replace `--device-index 0` with:

```powershell
--source rtsp://user:password@camera-host/stream
```

Smoke-test the frame recorder without a camera:

```powershell
python scripts\record_real_camera_frames.py `
  --synthetic-smoke `
  --frames 4 `
  --frequency-hz 100 `
  --output-dir results\real_camera_frames_synthetic_smoke `
  --stats-output results\real_camera_frames_synthetic_smoke_stats.csv `
  --summary-md results\real_camera_frames_synthetic_smoke_summary.md
```

Preview preprocessing for a real camera frame directory:

```powershell
python scripts\preprocess_camera_frames.py --input path\to\camera_frames --output-dir results\preprocessed_camera_frames --stats-output results\preprocessed_camera_frames_stats.csv --width 100 --height 100 --crop-xywh 0 0 640 480 --rotate-k 0
```

Run the real camera preflight before feeding images to the policy. This checks
that frames are readable, preprocessing produces the expected `100x100x1`
policy input, images are not blank or saturated, and adjacent frames are not
unexpectedly identical:

```powershell
python scripts\check_real_camera_preflight.py `
  --input path\to\camera_frames `
  --output-dir results\real_camera_preflight_frames `
  --stats-output results\real_camera_preflight_stats.csv `
  --summary-md results\real_camera_preflight_summary.md `
  --width 100 `
  --height 100 `
  --crop-xywh 0 0 640 480 `
  --rotate-k 0 `
  --max-frames 20
```

Smoke-test the camera preflight without real frames:

```powershell
python scripts\check_real_camera_preflight.py `
  --synthetic-smoke `
  --synthetic-frames 4 `
  --output-dir results\real_camera_preflight_synthetic_smoke_frames `
  --stats-output results\real_camera_preflight_synthetic_smoke_stats.csv `
  --summary-md results\real_camera_preflight_synthetic_smoke_summary.md `
  --output-json results\real_camera_preflight_synthetic_smoke_summary.json `
  --crop-xywh 20 10 160 120 `
  --rotate-k 1 `
  --flip-horizontal
```

Smoke-test preprocessing without camera frames:

```powershell
python scripts\preprocess_camera_frames.py --synthetic-smoke --output-dir results\preprocessed_camera_frames_smoke --stats-output results\preprocessed_camera_frames_smoke_stats.csv --crop-xywh 20 10 160 120 --rotate-k 1 --flip-horizontal
```

Run the combined real camera + policy dry-run preflight gate. This first checks
the camera frames and preprocessing, then feeds the same frames into the real
policy dry-run preflight with TCP pose trace and target calibration checks. It
still does not command robot motion:

```powershell
python scripts\run_real_camera_policy_preflight.py `
  --image-input path\to\camera_frames `
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip `
  --episodes 1 `
  --max-steps 20 `
  --tcp-pose-trace results\ur_rtde_tcp_pose_trace.csv `
  --target-calibration configs\real_hole_target_calibration.yaml `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --camera-crop-xywh 0 0 640 480 `
  --camera-rotate-k 0 `
  --expected-pose-frame robot_base `
  --summary-md results\real_camera_policy_preflight_summary.md `
  --output-json results\real_camera_policy_preflight_summary.json
```

Smoke-test the combined preflight without real hardware or live camera input:

```powershell
python scripts\run_real_camera_policy_preflight.py `
  --image-input results\real_camera_frames_synthetic_smoke `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-pose-trace configs\real_tcp_pose_trace_no_target_smoke.csv `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --camera-max-frames 4 `
  --camera-output-dir results\real_camera_policy_preflight_synthetic_smoke_camera_frames `
  --camera-stats-output results\real_camera_policy_preflight_synthetic_smoke_camera_stats.csv `
  --camera-summary-md results\real_camera_policy_preflight_synthetic_smoke_camera_summary.md `
  --camera-output-json results\real_camera_policy_preflight_synthetic_smoke_camera_summary.json `
  --dryrun-trace-output results\real_policy_dryrun_camera_policy_preflight_synthetic_smoke_trace.csv `
  --dryrun-check-output-md results\real_dryrun_camera_policy_preflight_synthetic_smoke_check.md `
  --dryrun-check-output-json results\real_dryrun_camera_policy_preflight_synthetic_smoke_check.json `
  --dryrun-summary-md results\real_dryrun_camera_policy_preflight_synthetic_smoke_summary.md `
  --summary-md results\real_camera_policy_preflight_synthetic_smoke_summary.md `
  --output-json results\real_camera_policy_preflight_synthetic_smoke_summary.json
```

Run a read-only capture bundle and preflight it in one command. The bundle now
runs `check_real_deployment_config.py` first, then records camera frames and UR
TCP poses in parallel, and finally runs `run_real_camera_policy_preflight.py`.
If the config check fails, it skips recorder startup and still writes a summary.
Arguments not recognized by the bundle script, such as `--model`,
`--zero-policy`, `--tcp-to-peg-tip-xyz`, and camera preprocessing flags, are
forwarded to the combined preflight. The bundle generates one session id and
writes it into both recorder CSVs; pass `--session-id` only when you want a
specific id in the logs:

```powershell
python scripts\run_real_capture_bundle.py `
  --config configs\real_ur5_dryrun.yaml `
  --config-check-output-md results\real_capture_bundle_config_check.md `
  --config-check-output-json results\real_capture_bundle_config_check.json `
  --record-camera-device-index 0 `
  --record-camera-frames 20 `
  --record-camera-frequency-hz 5 `
  --record-camera-warmup-frames 10 `
  --record-tcp-host 192.168.0.10 `
  --record-tcp-samples 20 `
  --record-tcp-frequency-hz 20 `
  --record-tcp-pose-frame robot_base `
  --target-calibration configs\real_hole_target_calibration.yaml `
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip `
  --episodes 1 `
  --max-steps 20 `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --camera-crop-xywh 0 0 640 480 `
  --camera-rotate-k 0 `
  --expected-pose-frame robot_base `
  --summary-md results\real_capture_bundle_summary.md `
  --preflight-summary-md results\real_capture_bundle_preflight_summary.md `
  --preflight-output-json results\real_capture_bundle_preflight_summary.json
```

Smoke-test the capture bundle without a robot or live camera:

```powershell
python scripts\run_real_capture_bundle.py `
  --session-id synthetic_config_gate_smoke `
  --config configs\real_ur5_dryrun.yaml `
  --config-check-output-md results\real_capture_bundle_config_gate_synthetic_smoke_config_check.md `
  --config-check-output-json results\real_capture_bundle_config_gate_synthetic_smoke_config_check.json `
  --record-camera-synthetic-smoke `
  --record-camera-frames 4 `
  --record-camera-frequency-hz 100 `
  --record-camera-output-dir results\real_capture_bundle_config_gate_synthetic_smoke_camera_frames `
  --record-camera-stats-output results\real_capture_bundle_config_gate_synthetic_smoke_camera_stats.csv `
  --record-camera-summary-md results\real_capture_bundle_config_gate_synthetic_smoke_camera_record_summary.md `
  --record-tcp-synthetic-smoke `
  --record-tcp-samples 4 `
  --record-tcp-frequency-hz 100 `
  --record-tcp-output results\real_capture_bundle_config_gate_synthetic_smoke_tcp_pose_trace.csv `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --camera-max-frames 4 `
  --camera-output-dir results\real_capture_bundle_config_gate_synthetic_smoke_preflight_camera_frames `
  --camera-stats-output results\real_capture_bundle_config_gate_synthetic_smoke_preflight_camera_stats.csv `
  --camera-summary-md results\real_capture_bundle_config_gate_synthetic_smoke_preflight_camera_summary.md `
  --camera-output-json results\real_capture_bundle_config_gate_synthetic_smoke_preflight_camera_summary.json `
  --dryrun-trace-output results\real_capture_bundle_config_gate_synthetic_smoke_policy_trace.csv `
  --dryrun-check-output-md results\real_capture_bundle_config_gate_synthetic_smoke_dryrun_check.md `
  --dryrun-check-output-json results\real_capture_bundle_config_gate_synthetic_smoke_dryrun_check.json `
  --dryrun-summary-md results\real_capture_bundle_config_gate_synthetic_smoke_dryrun_summary.md `
  --summary-md results\real_capture_bundle_config_gate_synthetic_smoke_summary.md `
  --output-json results\real_capture_bundle_config_gate_synthetic_smoke_summary.json `
  --preflight-summary-md results\real_capture_bundle_config_gate_synthetic_smoke_preflight_summary.md `
  --preflight-output-json results\real_capture_bundle_config_gate_synthetic_smoke_preflight_summary.json
```

Checked gate smoke outputs:

| Scenario | Expected exit | Summary |
| --- | ---: | --- |
| config pass | 0 | `results\real_capture_bundle_config_gate_synthetic_smoke_summary.md` |
| missing config | 1 | `results\real_capture_bundle_config_gate_failure_smoke_summary.md` |

After a real read-only capture bundle passes, run the real motion readiness
gate before allowing any robot motion. This still only reads the bundle summary
and generated preflight reports; it does not connect to the robot:

```powershell
python scripts\check_real_motion_readiness.py `
  --bundle-summary-json results\real_capture_bundle_summary.json `
  --output-md results\real_motion_readiness_check.md `
  --output-json results\real_motion_readiness_check.json `
  --min-camera-frames 20 `
  --min-tcp-samples 20 `
  --min-dryrun-rows 2 `
  --expected-pose-frame robot_base `
  --expected-target-source fixture_calibration `
  --expected-guard-blend 0.75 `
  --max-safe-action 0.002
```

The readiness checker intentionally fails synthetic/zero-policy bundles unless
they are explicitly allowed. Smoke-test that behavior:

```powershell
python scripts\check_real_motion_readiness.py `
  --bundle-summary-json results\real_capture_bundle_config_gate_synthetic_smoke_summary.json `
  --output-md results\real_motion_readiness_synthetic_expected_fail.md `
  --output-json results\real_motion_readiness_synthetic_expected_fail.json
```

Smoke-test the checker itself by explicitly allowing synthetic inputs:

```powershell
python scripts\check_real_motion_readiness.py `
  --bundle-summary-json results\real_capture_bundle_config_gate_synthetic_smoke_summary.json `
  --allow-synthetic `
  --allow-zero-policy `
  --allow-smoke-paths `
  --min-camera-frames 4 `
  --min-tcp-samples 4 `
  --min-dryrun-rows 4 `
  --output-md results\real_motion_readiness_synthetic_smoke.md `
  --output-json results\real_motion_readiness_synthetic_smoke.json
```

Checked readiness smoke outputs:

| Scenario | Expected exit | Summary |
| --- | ---: | --- |
| synthetic default gate | 1 | `results\real_motion_readiness_synthetic_expected_fail.md` |
| synthetic explicitly allowed | 0 | `results\real_motion_readiness_synthetic_smoke.md` |

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
