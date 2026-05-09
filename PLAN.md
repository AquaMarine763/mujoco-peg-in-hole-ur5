# Project Plan And Status

Last updated: 2026-05-09

This file records the current project status, known metrics, and next planned steps. Keep it current when a milestone changes.

## Current Objective

The project is moving from a lightweight MuJoCo UR5e-like peg-in-hole environment toward a more faithful UR5e simulation and a cautious sim-to-real pipeline.

The immediate objective is now to move from the near-hole narrowed full UR5e task to a high-start visual-search curriculum. The narrowed-hole correction pass has been validated, but it did not improve enough to replace the current default checkpoint.

## Current Branch And Remote

- Branch: `feature/ur5e-mainline`
- Remote: `https://github.com/AquaMarine763/mujoco-peg-in-hole-ur5.git`
- Latest known pushed milestone: `e602f34 Add full UR5e MuJoCo task model`

## Implemented So Far

- MuJoCo peg-in-hole task environment.
- State observation training path.
- Image observation training path.
- Side camera and near-hole crop support.
- Image expert dataset collection and BC pretraining.
- Visual domain randomization.
- Camera/control randomization.
- Guarded insertion wrapper for deployment-time correction.
- Geometry curriculum and harder tolerance evaluation.
- Demo generation with higher-resolution GIF output.
- Real UR5e read-only preparation tools and config templates.
- Lightweight UR5e adapter model:
  - `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Full UR5e MuJoCo task model:
  - `assets/ur5e_full/ur5e_peg_in_hole_full.xml`
- Full UR5e demo-facing cleanup:
  - hidden `hole_site`, `eef_site`, and `peg_tip` debug markers in rendered images
  - narrowed the full UR5e base hole opening from about `90 mm` to about `40 mm`
  - narrowed the standard geometry-randomized hole opening to about `34 - 42 mm`

## Full UR5e Model Status

The full UR5e model is based on DeepMind MuJoCo Menagerie `universal_robots_ur5e`.

It includes:

- UR5e visual meshes
- UR5e inertials
- UR5e collision geometry
- six UR5e joints
- six actuator controls
- existing task names preserved for environment compatibility:
  - `tool0`
  - `eef_site`
  - `peg_tip`
  - `wrist_cam`
  - `hole_body`
  - `hole_site`
  - `peg_geom`

Known validation already passed:

- model inspection compatible
- absolute path XML loading
- 3-episode oracle rollout succeeded
- high-resolution demo rendered with visible full UR5e mesh
- 100-episode policy-only and guarded evaluation completed on the full UR5e model

Important caveat:

- The model is not a byte-for-byte official UR5e XML. It keeps the Menagerie UR5e core assets and parameters, but the task XML adds the peg, camera, hole/table scene, task-facing names, and a custom reset/control setup.
- The environment currently resets to a custom `rest_qpos = [0.08, -1.2, 1.8, -0.6, 0.0, 0.0]` rather than the XML `home` keyframe.
- The IK controller solves peg-tip position only; it does not yet explicitly constrain tool orientation or regularize toward a preferred UR5e posture. This can make demo joint motion look unnatural.
- The current full UR5e fixture uses a peg radius of `0.012 m` and a base hole opening of about `40 mm`. Full-light geometry randomization now uses `geometry_hole_half_size_range=[0.017, 0.021]`, i.e. about `34 - 42 mm` opening.
- Metrics below were collected before the marker-hiding and hole-narrowing change unless explicitly refreshed.

## Recommended Policy Checkpoint

Current recommended image policy:

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip
```

This policy was trained on the lightweight UR5e adapter model. It may suffer visual distribution shift on the full UR5e mesh model.

Pre-narrow-hole full UR5e adapted image policy:

```text
checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip
```

Current recommended narrowed-hole full UR5e adapted image policy:

```text
checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip
```

Latest narrowed-hole correction candidate:

```text
checkpoints\ur5e_full\correction\sac_image_bc_50k_narrow_correction_8k_w10_e2.zip
```

This correction candidate is not the default because the 100-episode evaluation was mostly flat versus the adapted narrowed-hole checkpoint.

Latest high-start visual-search candidate:

```text
checkpoints\ur5e_full\high_start\sac_image_bc_50k_high_start_visual_camera.zip
```

This high-start candidate is also not the default yet. It proves the high-start data/training/eval path works, but the 100-episode high-start success rate is still only about `0.15 - 0.24` depending on the evaluation bucket.

Latest easy high-start visual-search candidate:

```text
checkpoints\ur5e_full\high_start\easy\sac_image_bc_50k_high_start_easy_visual_camera.zip
```

This is the current best high-start candidate for the easier `0.08 - 0.15 m` height and `0.04 - 0.10 m` XY-offset curriculum. It is not the general default yet because success is still about `0.50 - 0.67`, and the original harder high-start range is not solved.

Latest medium high-start visual-search candidate:

```text
checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip
```

This is the current best checkpoint for the medium `0.10 - 0.18 m` height and `0.06 - 0.12 m` XY-offset curriculum. It improves over medium 20k and produces a successful medium demo, but success is still only about `0.49 - 0.68` across buckets.

Latest hard-range high-start candidate:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip
```

This checkpoint is a hard-range candidate, not a promoted default. It reaches `0.45` on visual_camera but remains weak under control/geometry/contact buckets.

For full UR5e demo/deployment-style simulation on the narrowed-hole task, use:

```text
guard_scenario_filter=all
guarded_align_xy_tolerance=0.020
guard_blend=1.0
```

## Latest Known Adapter Metrics

Approximate latest known lightweight-adapter policy-only performance:

- clean: `0.980`
- visual: `0.980`
- visual_camera_control: `0.910 - 0.920`
- full light: about `0.580`
- full contact: about `0.590 - 0.600`

Approximate latest known guarded performance with blend `0.75`:

- clean: `0.980`
- visual: `0.980`
- visual_camera_control: `0.910 - 0.920`
- full light: about `0.710`
- full contact: about `0.640 - 0.650`
- hard bucket: about `0.530`

These numbers should be refreshed whenever a new checkpoint or environment version becomes the default.

## Full UR5e Metrics Before Adaptation

Generated on 2026-05-08 with:

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip
```

Model path:

```text
assets\ur5e_full\ur5e_peg_in_hole_full.xml
```

Policy-only, 100 episodes per scenario:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.080 | 0.220 | 0.700 |
| visual_camera | 0.260 | 0.210 | 0.530 |
| visual_camera_control | 0.250 | 0.220 | 0.530 |
| full_light_geometry | 0.140 | 0.590 | 0.270 |
| full_contact_light | 0.150 | 0.550 | 0.300 |

Guarded with `guard_scenario_filter=geometry`, `guard_blend=0.75`, 100 episodes per scenario:

| Scenario | Guard active | Success | Collision | Timeout |
| --- | --- | ---: | ---: | ---: |
| clean | no | 0.080 | 0.220 | 0.700 |
| visual_camera | no | 0.260 | 0.210 | 0.530 |
| visual_camera_control | no | 0.250 | 0.220 | 0.530 |
| full_light_geometry | yes | 0.620 | 0.280 | 0.100 |
| full_contact_light | yes | 0.650 | 0.290 | 0.060 |
| hard_full_light_bucket | yes | 0.590 | 0.280 | 0.130 |

Interpretation:

- The full UR5e model is structurally usable.
- The current image policy has a large visual distribution shift from lightweight adapter to full UR5e mesh.
- Guarded insertion still recovers many geometry-randomized cases once it is active.
- The full UR5e model should not become the default training/eval baseline until the policy is adapted to this visual distribution.

## Latest Full UR5e Adaptation Results

Generated on 2026-05-08 with:

```text
checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip
```

50k dataset:

- dataset: `datasets\ur5e_full\adapt\image_expert_50k_full_light_geometry.npz`
- samples: `50000`
- data collection episodes: `555`
- successful episodes kept: `472`
- collection success rate: `0.850`
- collection collision rate: `0.141`
- oracle mode: `guarded_two_stage`
- domain randomization level: `full_light_geometry`

BC fine-tuning:

- starting checkpoint: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- output checkpoint: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip`
- epochs: `10`
- final train loss: `0.044951`
- final validation loss: `0.046326`

Policy-only, 100 episodes per scenario:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.950 | 0.000 | 0.050 |
| visual_camera | 0.660 | 0.000 | 0.340 |
| visual_camera_control | 0.610 | 0.020 | 0.370 |
| full_light_geometry | 0.680 | 0.230 | 0.090 |
| full_contact_light | 0.650 | 0.240 | 0.110 |

Guarded with `guard_scenario_filter=geometry`, `guard_blend=0.75`, 100 episodes per scenario:

| Scenario | Guard active | Success | Collision | Timeout |
| --- | --- | ---: | ---: | ---: |
| clean | no | 0.950 | 0.000 | 0.050 |
| visual_camera | no | 0.660 | 0.000 | 0.340 |
| visual_camera_control | no | 0.610 | 0.020 | 0.370 |
| full_light_geometry | yes | 0.840 | 0.150 | 0.010 |
| full_contact_light | yes | 0.840 | 0.160 | 0.000 |
| hard_full_light_bucket | yes | 0.810 | 0.190 | 0.000 |

Guarded with `guard_scenario_filter=all`, `guard_blend=0.75`, 100 episodes per scenario:

| Scenario | Guard active | Success | Collision | Timeout |
| --- | --- | ---: | ---: | ---: |
| clean | yes | 0.990 | 0.000 | 0.010 |
| visual_camera | yes | 0.970 | 0.000 | 0.030 |
| visual_camera_control | yes | 0.950 | 0.020 | 0.030 |
| full_light_geometry | yes | 0.840 | 0.150 | 0.010 |
| full_contact_light | yes | 0.840 | 0.160 | 0.000 |
| hard_full_light_bucket | yes | 0.820 | 0.180 | 0.000 |

Demo:

- `demos\ur5e_full\adapt\demo_guarded_all_50k_full_light_geometry.gif`
- requested MP4 output fell back to GIF because the local `imageio` video backend is unavailable

## Full UR5e Config Status

Config-driven full UR5e workflows now live under:

```text
configs/sim/ur5e_full/
```

Implemented configs:

- `eval_image_crop.yaml`
- `eval_guarded_image_crop.yaml`
- `demo_guarded_image_crop.yaml`
- `eval_image_adapt_50k.yaml`
- `eval_guarded_adapt_50k_all.yaml`
- `demo_guarded_adapt_50k_all.yaml`
- `collect_high_start_smoke.yaml`
- `pretrain_high_start_smoke.yaml`
- `demo_high_start_guarded_smoke.yaml`
- `collect_high_start_50k.yaml`
- `pretrain_high_start_50k.yaml`
- `eval_high_start_guarded_adapt.yaml`
- `collect_image_expert_smoke.yaml`
- `collect_image_expert_50k.yaml`
- `pretrain_image_bc_smoke.yaml`
- `pretrain_image_bc_50k.yaml`

Smoke validation completed on 2026-05-08:

- `eval_matrix.py --config configs/sim/ur5e_full/eval_image_crop.yaml --episodes 1` passed
- `eval_guarded_policy.py --config configs/sim/ur5e_full/eval_guarded_image_crop.yaml --episodes 1` passed
- `demo_policy.py --config configs/sim/ur5e_full/demo_guarded_image_crop.yaml --max-steps 5` passed
- `collect_image_expert_dataset.py --config configs/sim/ur5e_full/collect_image_expert_smoke.yaml` passed with `success_rate=1.000`, `collision_rate=0.000`
- `pretrain_image_actor_bc.py --config configs/sim/ur5e_full/pretrain_image_bc_smoke.yaml` passed for 1 epoch
- adapted 50k eval, guarded eval, and demo configs passed short smoke checks

## High-Start Visual Curriculum Status

High-start reset is now implemented through:

```text
initialization_mode=target_relative_high_start
initial_tip_z_above_range=[0.15, 0.25]
initial_tip_xy_offset_range=[0.08, 0.16]
initial_tip_xy_angle_range_deg=[0.0, 360.0]
initial_ik_max_attempts=30
```

The default remains `initialization_mode=fixed`, so existing baselines are not changed.

Reset smoke confirmed the new mode starts substantially farther from the hole. Example range from local smoke:

- initial XY offset: about `0.09 - 0.16 m`
- initial Z above hole: about `0.15 - 0.24 m`
- IK error: below `0.0001 m` in sampled cases

High-start oracle findings:

- With `full_light_geometry` immediately enabled, the first smoke was too hard: `success_rate=0.143`, `collision_rate=0.571`.
- The first high-start curriculum stage was therefore changed to `visual_camera` only.
- `collect_high_start_smoke.yaml` now passes with `success_rate=1.000`, `collision_rate=0.000`.
- `pretrain_high_start_smoke.yaml` passes for 1 epoch.
- `demo_high_start_guarded_smoke.yaml` generated a 120-step GIF smoke from a high start. The trace starts around `8.5 cm` XY offset and `23.6 cm` above the hole.

Important interpretation:

- The current full UR5e adapted policy was not trained for high-start visual search.
- Standard near-hole guard activation does not help from high/far starts, because guard only activates near the hole.
- Wide guard/oracle smoke is useful for dataset validation, but high-start policy evaluation should keep guard activation near-hole so the learned policy must solve the search phase.

## High-Start Visual-Search 50k Stage

On 2026-05-08, the first full 50k high-start visual-search stage was run.

Dataset:

- config: `configs\sim\ur5e_full\collect_high_start_50k.yaml`
- dataset: `datasets\ur5e_full\high_start\image_expert_50k_high_start_visual_camera.npz`
- samples: `50000`
- high-start range: `0.15 - 0.25 m` above the hole
- initial XY offset range: `0.08 - 0.16 m`
- domain randomization level: `visual_camera`
- oracle mode: `guarded_two_stage`
- episodes completed: `1044`
- successful episodes kept: `225`
- collection success rate: `0.216`
- collection collision rate: `0.552`
- collection timeout rate: `0.233`

Dataset coverage:

- sample XY offset from hole:
  - median: about `0.038 m`
  - p95: about `0.110 m`
  - max: about `0.158 m`
- sample height above target:
  - median: about `0.075 m`
  - p95: about `0.195 m`
  - max: about `0.246 m`

BC fine-tune:

- config: `configs\sim\ur5e_full\pretrain_high_start_50k.yaml`
- starting checkpoint: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip`
- output checkpoint: `checkpoints\ur5e_full\high_start\sac_image_bc_50k_high_start_visual_camera.zip`
- epochs: `10`
- final train loss: `0.062912`
- final validation loss: `0.066407`

High-start guarded-all 100-episode evaluation:

- config: `configs\sim\ur5e_full\eval_high_start_guarded_50k.yaml`
- guard start: `0.06 m` XY and `0.08 m` above target
- this uses the standard near-hole guard, not the wide oracle-style guard

| Scenario | Success | Collision | Timeout | Final XY | Final Z |
| --- | ---: | ---: | ---: | ---: | ---: |
| clean | 0.190 | 0.470 | 0.340 | 0.03117 | 0.03211 |
| visual_camera | 0.240 | 0.420 | 0.340 | 0.06557 | 0.04705 |
| visual_camera_control | 0.180 | 0.470 | 0.350 | 0.06743 | 0.05562 |
| full_light_geometry | 0.170 | 0.510 | 0.320 | 0.06076 | 0.04785 |
| full_contact_light | 0.220 | 0.500 | 0.280 | 0.05828 | 0.04202 |
| hard_full_light_bucket | 0.150 | 0.520 | 0.330 | 0.08274 | 0.06235 |

Demo:

- config: `configs\sim\ur5e_full\demo_high_start_guarded_50k.yaml`
- output: `demos\ur5e_full\high_start\demo_high_start_50k_visual_camera_standard_guard.gif`
- trace: `results\ur5e_full\high_start\demo_high_start_50k_visual_camera_standard_guard_trace.csv`
- result: not successful; timed out at `1000` steps with final XY about `0.00883 m` and final Z about `0.04759 m`
- MP4 output fell back to GIF because the local imageio video backend is not installed

Interpretation:

- The high-start data/training/eval/demo pipeline now works end to end.
- The first high-start policy does not yet solve visual hole search.
- The oracle itself is weak from the high-start distribution, with only `0.216` collection success and `0.552` collision, so more BC epochs alone are unlikely to be enough.
- Do not introduce larger randomized initial XY offsets yet. First improve the high-start curriculum and/or oracle/controller behavior.

## Easy High-Start Visual-Search Stage

On 2026-05-08, an easier high-start stage was added to bridge between the near-hole task and the original high-start range.

Easy reset range:

- height above hole: `0.08 - 0.15 m`
- initial XY offset: `0.04 - 0.10 m`
- approach safe height: `0.10 m`
- domain randomization level: `visual_camera`
- oracle mode: `guarded_two_stage`
- rollout noise: `0.0002`

20k easy dataset:

- config: `configs\sim\ur5e_full\collect_high_start_easy_20k.yaml`
- dataset: `datasets\ur5e_full\high_start\easy\image_expert_20k_high_start_easy_visual_camera.npz`
- samples: `20000`
- episodes completed: `161`
- successful episodes kept: `102`
- collection success rate: `0.634`
- collection collision rate: `0.186`
- collection timeout rate: `0.180`

20k easy BC:

- config: `configs\sim\ur5e_full\pretrain_high_start_easy_20k.yaml`
- output checkpoint: `checkpoints\ur5e_full\high_start\easy\sac_image_bc_20k_high_start_easy_visual_camera.zip`
- epochs: `10`
- final train loss: `0.070573`
- final validation loss: `0.070368`

20k easy guarded-all 100-episode evaluation:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.600 | 0.200 | 0.200 |
| visual_camera | 0.590 | 0.210 | 0.200 |
| visual_camera_control | 0.570 | 0.280 | 0.150 |
| full_light_geometry | 0.560 | 0.220 | 0.220 |
| full_contact_light | 0.530 | 0.220 | 0.250 |
| hard_full_light_bucket | 0.470 | 0.330 | 0.200 |

20k easy demo:

- config: `configs\sim\ur5e_full\demo_high_start_easy_guarded_20k.yaml`
- output: `demos\ur5e_full\high_start\easy\demo_high_start_easy_20k_visual_camera_standard_guard.gif`
- result: success in `251` steps, no collision

50k easy dataset:

- config: `configs\sim\ur5e_full\collect_high_start_easy_50k.yaml`
- dataset: `datasets\ur5e_full\high_start\easy\image_expert_50k_high_start_easy_visual_camera.npz`
- samples: `50000`
- episodes completed: `377`
- collection success rate: `0.647`
- collection collision rate: `0.119`

50k easy BC:

- config: `configs\sim\ur5e_full\pretrain_high_start_easy_50k.yaml`
- output checkpoint: `checkpoints\ur5e_full\high_start\easy\sac_image_bc_50k_high_start_easy_visual_camera.zip`
- epochs: `10`
- final train loss: `0.061749`
- final validation loss: `0.061968`

50k easy guarded-all 100-episode evaluation:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.670 | 0.120 | 0.210 |
| visual_camera | 0.540 | 0.180 | 0.280 |
| visual_camera_control | 0.500 | 0.270 | 0.230 |
| full_light_geometry | 0.530 | 0.270 | 0.200 |
| full_contact_light | 0.530 | 0.340 | 0.130 |
| hard_full_light_bucket | 0.530 | 0.260 | 0.210 |

Same-seed comparison against the 20k eval seed (`534000`) for the 50k checkpoint:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.620 | 0.150 | 0.230 |
| visual_camera | 0.630 | 0.170 | 0.200 |
| visual_camera_control | 0.590 | 0.260 | 0.150 |
| full_light_geometry | 0.580 | 0.210 | 0.210 |
| full_contact_light | 0.540 | 0.220 | 0.240 |
| hard_full_light_bucket | 0.480 | 0.300 | 0.220 |

50k easy demos:

- default seed `542000`: timed out at `800` steps, final XY about `0.00843 m`, final Z about `0.02102 m`
- seed `534000`: succeeded in `247` steps, initial XY about `0.069 m`, initial Z about `0.120 m`, no collision
- successful demo: `demos\ur5e_full\high_start\easy\demo_high_start_easy_50k_visual_camera_standard_guard_seed534000.gif`

Interpretation:

- Easier high-start is a real improvement over the original high-start stage.
- The original high-start 50k stage had only `0.15 - 0.24` success; easy 50k reaches about `0.50 - 0.67` depending on scenario and seed.
- The remaining failures are still substantial, especially collision and timeout under camera/control/geometry variation.
- Do not jump directly to larger initial XY offsets yet. The next curriculum should be a medium stage, not the full hard range.

## Medium High-Start Visual-Search Stage

On 2026-05-08, a medium high-start stage was added between easy and the original hard range.

Medium reset range:

- height above hole: `0.10 - 0.18 m`
- initial XY offset: `0.06 - 0.12 m`
- approach safe height: `0.12 m`
- domain randomization level: `visual_camera`
- oracle mode: `guarded_two_stage`
- rollout noise: `0.0002`

20k medium dataset:

- config: `configs\sim\ur5e_full\collect_high_start_medium_20k.yaml`
- dataset: `datasets\ur5e_full\high_start\medium\image_expert_20k_high_start_medium_visual_camera.npz`
- samples: `20000`
- episodes completed: `129`
- successful episodes kept: `74`
- collection success rate: `0.574`
- collection collision rate: `0.070`
- collection timeout rate: `0.357`

20k medium BC:

- config: `configs\sim\ur5e_full\pretrain_high_start_medium_20k.yaml`
- starting checkpoint: `checkpoints\ur5e_full\high_start\easy\sac_image_bc_50k_high_start_easy_visual_camera.zip`
- output checkpoint: `checkpoints\ur5e_full\high_start\medium\sac_image_bc_20k_high_start_medium_visual_camera.zip`
- epochs: `10`
- final train loss: `0.046298`
- final validation loss: `0.046241`

20k medium guarded-all 100-episode evaluation:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.560 | 0.220 | 0.220 |
| visual_camera | 0.530 | 0.250 | 0.220 |
| visual_camera_control | 0.540 | 0.250 | 0.210 |
| full_light_geometry | 0.520 | 0.220 | 0.260 |
| full_contact_light | 0.480 | 0.300 | 0.220 |
| hard_full_light_bucket | 0.440 | 0.330 | 0.230 |

20k medium demo:

- config: `configs\sim\ur5e_full\demo_high_start_medium_guarded_20k.yaml`
- output: `demos\ur5e_full\high_start\medium\demo_high_start_medium_20k_visual_camera_standard_guard.gif`
- result: collision at `107` steps; guard only active for `3` steps

50k medium dataset:

- config: `configs\sim\ur5e_full\collect_high_start_medium_50k.yaml`
- dataset: `datasets\ur5e_full\high_start\medium\image_expert_50k_high_start_medium_visual_camera.npz`
- samples: `50000`
- episodes completed: `287`
- successful episodes kept: `180`
- collection success rate: `0.627`
- collection collision rate: `0.087`
- collection timeout rate: `0.286`

50k medium BC:

- config: `configs\sim\ur5e_full\pretrain_high_start_medium_50k.yaml`
- starting checkpoint: `checkpoints\ur5e_full\high_start\easy\sac_image_bc_50k_high_start_easy_visual_camera.zip`
- output checkpoint: `checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip`
- epochs: `10`
- final train loss: `0.045268`
- final validation loss: `0.044958`

50k medium guarded-all 100-episode evaluation:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.680 | 0.060 | 0.260 |
| visual_camera | 0.620 | 0.140 | 0.240 |
| visual_camera_control | 0.510 | 0.210 | 0.280 |
| full_light_geometry | 0.510 | 0.230 | 0.260 |
| full_contact_light | 0.510 | 0.260 | 0.230 |
| hard_full_light_bucket | 0.490 | 0.250 | 0.260 |

50k medium demo:

- config: `configs\sim\ur5e_full\demo_high_start_medium_guarded_50k.yaml`
- output: `demos\ur5e_full\high_start\medium\demo_high_start_medium_50k_visual_camera_standard_guard.gif`
- result: success in `285` steps, no collision
- initial state: about `0.0865 m` XY offset and `0.1125 m` above the hole

Interpretation:

- Medium 50k is a useful curriculum step and clearly better than medium 20k.
- Compared with easy 50k, medium 50k handles a harder start range with similar overall success, but it still has high timeout and nontrivial collision under control/geometry/contact buckets.
- The original hard range should be re-tested from the medium 50k checkpoint next, but larger random XY offsets should still wait.

## Hard High-Start Re-Test And Safe-Height Stage

On 2026-05-08/2026-05-09, the original high-start range was re-tested after the easy and medium curriculum.

Original hard range:

- height above hole: `0.15 - 0.25 m`
- initial XY offset: `0.08 - 0.16 m`

Medium checkpoint direct hard-range re-test:

- config: `configs\sim\ur5e_full\eval_high_start_hard_from_medium_guarded_50k.yaml`
- checkpoint: `checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip`
- approach height / guard start Z: `0.12 m`

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.400 | 0.120 | 0.480 |
| visual_camera | 0.370 | 0.220 | 0.410 |
| visual_camera_control | 0.350 | 0.340 | 0.310 |
| full_light_geometry | 0.220 | 0.320 | 0.460 |
| full_contact_light | 0.340 | 0.300 | 0.360 |
| hard_full_light_bucket | 0.270 | 0.360 | 0.370 |

The direct hard-range demo from the medium checkpoint succeeded:

- config: `configs\sim\ur5e_full\demo_high_start_hard_from_medium_guarded_50k.yaml`
- output: `demos\ur5e_full\high_start\hard\demo_high_start_hard_from_medium_50k_standard_guard.gif`
- result: success in `224` steps

Hard-safe 20k dataset:

- config: `configs\sim\ur5e_full\collect_high_start_hard_safe_20k.yaml`
- dataset: `datasets\ur5e_full\high_start\hard\image_expert_20k_high_start_hard_safe_visual_camera.npz`
- samples: `20000`
- episodes completed: `146`
- successful episodes kept: `68`
- collection success rate: `0.466`
- collection collision rate: `0.116`
- collection timeout rate: `0.418`

Hard-safe 20k BC:

- config: `configs\sim\ur5e_full\pretrain_high_start_hard_safe_20k.yaml`
- starting checkpoint: `checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip`
- output checkpoint: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_20k_high_start_hard_safe_visual_camera.zip`
- epochs: `10`
- final train loss: `0.040639`
- final validation loss: `0.040242`

Hard-safe 20k guarded-all 100-episode evaluation:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.480 | 0.100 | 0.420 |
| visual_camera | 0.400 | 0.190 | 0.410 |
| visual_camera_control | 0.340 | 0.300 | 0.360 |
| full_light_geometry | 0.350 | 0.240 | 0.410 |
| full_contact_light | 0.390 | 0.290 | 0.320 |
| hard_full_light_bucket | 0.240 | 0.370 | 0.390 |

Hard-safe 20k demo:

- config: `configs\sim\ur5e_full\demo_high_start_hard_safe_20k.yaml`
- output: `demos\ur5e_full\high_start\hard\demo_high_start_hard_safe_20k_visual_camera_standard_guard.gif`
- result: success in `441` steps
- initial state: about `0.105 m` XY offset and `0.200 m` above the hole

Hard-safe 50k dataset:

- config: `configs\sim\ur5e_full\collect_high_start_hard_safe_50k.yaml`
- dataset: `datasets\ur5e_full\high_start\hard\image_expert_50k_high_start_hard_safe_visual_camera.npz`
- samples: `50000`
- episodes completed: `462`
- successful episodes kept: `174`
- collection success rate: `0.377`
- collection collision rate: `0.110`
- collection timeout rate: `0.513`

Hard-safe 50k BC:

- config: `configs\sim\ur5e_full\pretrain_high_start_hard_safe_50k.yaml`
- starting checkpoint: `checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip`
- output checkpoint: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip`
- epochs: `10`
- final train loss: `0.046788`
- final validation loss: `0.047316`

Hard-safe 50k guarded-all 100-episode evaluation:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.480 | 0.150 | 0.370 |
| visual_camera | 0.450 | 0.220 | 0.330 |
| visual_camera_control | 0.330 | 0.270 | 0.400 |
| full_light_geometry | 0.270 | 0.370 | 0.360 |
| full_contact_light | 0.310 | 0.370 | 0.320 |
| hard_full_light_bucket | 0.330 | 0.260 | 0.410 |

Hard-safe 50k demo:

- config: `configs\sim\ur5e_full\demo_high_start_hard_safe_50k.yaml`
- output: `demos\ur5e_full\high_start\hard\demo_high_start_hard_safe_50k_visual_camera_standard_guard.gif`
- result: success in `287` steps
- initial state: about `0.122 m` XY offset and `0.177 m` above the hole

Interpretation:

- The original hard range is partially learnable after the easy/medium curriculum and `0.12 m` safe approach height.
- Single demo rollouts can succeed from the hard range, but average success remains too low.
- Hard-safe 50k does not reliably beat hard-safe 20k; more of the same success-only BC data is unlikely to solve the problem alone.
- The main remaining bottleneck is high-start control quality: too many episodes timeout or collide before stable near-hole insertion.
- Next work should improve the high-start controller/oracle and add failure correction, not expand initial XY randomization.

## Two-Phase High-Start Controller

On 2026-05-09, the first high-start controller/oracle improvement was implemented.

Code changes:

- `OracleControllerConfig.mode` now supports `high_start_two_phase`.
- `oracle_action_from_state(...)` dispatches between `guarded_two_stage` and `high_start_two_phase` for deployment-style guarded policy use.
- `high_start_two_phase` holds the peg at its current height, or raises it back to the safe height, while XY is outside the alignment threshold. It only allows descent after XY is aligned.
- `guard_block_down_when_unaligned` now applies before guard activation as well as after guard activation.
- `demo_policy.py`, `eval_guarded_policy.py`, and `run_policy_inference.py` now accept `guarded_oracle_mode`.
- `collect_image_expert_dataset.py`, `oracle_rollout.py`, and `scan_oracle_control_gain.py` accept `oracle_mode=high_start_two_phase`.

Validation configs:

- `configs\sim\ur5e_full\collect_high_start_hard_twophase_smoke.yaml`
- `configs\sim\ur5e_full\eval_high_start_hard_twophase_hard_safe_50k.yaml`
- `configs\sim\ur5e_full\demo_high_start_hard_twophase_hard_safe_50k.yaml`

Two-phase oracle smoke:

- dataset: `datasets\ur5e_full\high_start\hard\image_expert_high_start_hard_twophase_smoke.npz`
- episodes completed: `3`
- success rate: `0.667`
- collision rate: `0.000`

Hard-safe 50k policy evaluated with two-phase guard and pre-guard down-block:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.490 | 0.100 | 0.410 |
| visual_camera | 0.340 | 0.190 | 0.470 |
| visual_camera_control | 0.320 | 0.260 | 0.420 |
| full_light_geometry | 0.350 | 0.260 | 0.390 |
| full_contact_light | 0.350 | 0.300 | 0.350 |
| hard_full_light_bucket | 0.270 | 0.340 | 0.390 |

Two-phase hard demo:

- config: `configs\sim\ur5e_full\demo_high_start_hard_twophase_hard_safe_50k.yaml`
- output: `demos\ur5e_full\high_start\hard\demo_high_start_hard_twophase_hard_safe_50k_visual_camera_standard_guard.gif`
- result: timeout at `1000` steps, no collision
- final state: about `0.0081 m` XY error and `0.0345 m` above target

Interpretation:

- The two-phase oracle and pre-guard down-block are implemented and usable.
- The first hard-range evaluation reduced some collision risk but increased timeout; it is not a drop-in default.
- The demo failure is informative: it reached near-hole alignment but stayed too high/slow and timed out.
- Next tuning should make the down-block less conservative, or release it sooner near the hole, instead of adding more success-only hard data.

## Hard High-Start Guard Parameter Scan

On 2026-05-09, `scan_guarded_policy_params.py` was extended so high-start scans can cover:

- `initialization_mode=target_relative_high_start`
- high-start height/XY reset ranges
- narrowed-hole geometry ranges
- `guarded_oracle_mode` values: `guarded_two_stage` and `high_start_two_phase`
- `guard_block_down_when_unaligned` false/true in the same grid

Smoke scan config:

```text
configs\sim\ur5e_full\scan_high_start_hard_twophase_guarded_smoke.yaml
```

5-episode targeted scan output:

```text
results\ur5e_full\high_start\hard\scan_high_start_hard_twophase_guarded_smoke.md
```

Key scan findings:

- All guarded candidates averaged `0.300` success across visual_camera_control, full_light_geometry, full_contact_light, and hard bucket; no-guard averaged `0.200`.
- `high_start_two_phase` was effectively tied with `guarded_two_stage`.
- Block-down false/true was also effectively tied in this setup.
- `align=0.020` was better on visual_camera_control in the 5-episode smoke (`0.600`) but weaker on hard bucket (`0.200`).
- `align=0.025` and `align=0.030` were better on hard bucket in the smoke (`0.400`) but did not solve full_light_geometry, which stayed at `0.000`.

Focused 100-episode validation for the `align=0.025`, `guarded_two_stage`, no-block candidate:

```text
configs\sim\ur5e_full\eval_high_start_hard_align025_guarded_50k.yaml
results\ur5e_full\high_start\hard\eval_high_start_hard_align025_guarded_50k.md
```

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.530 | 0.050 | 0.420 |
| visual_camera | 0.370 | 0.170 | 0.460 |
| visual_camera_control | 0.310 | 0.330 | 0.360 |
| full_light_geometry | 0.340 | 0.280 | 0.380 |
| full_contact_light | 0.290 | 0.320 | 0.390 |
| hard_full_light_bucket | 0.270 | 0.340 | 0.390 |

Focused demo:

```text
configs\sim\ur5e_full\demo_high_start_hard_align025_guarded_50k.yaml
demos\ur5e_full\high_start\hard\demo_high_start_hard_align025_50k_visual_camera_standard_guard.gif
results\ur5e_full\high_start\hard\demo_high_start_hard_align025_50k_visual_camera_standard_guard_trace.csv
```

Demo result:

- timeout at `1000` steps
- no collision
- initial state: about `110.5 mm` XY offset and `235.0 mm` above target
- guard first activated at step `244`
- first reached `25 mm` XY alignment at step `332`
- never reached the `5 mm` success XY tolerance
- final state: about `8.4 mm` XY error and `32.8 mm` above target

Interpretation:

- `align=0.025` is not a new default; it improves clean success versus the previous hard-safe table but does not improve the hard/contact buckets enough.
- The dominant failure is now a near-hole plateau: the policy/guard combination often gets close to the hole, then stalls around `5 - 15 mm` XY error and times out or collides.
- The next useful work is a DAgger-style hard high-start correction pass or a guarded re-align/retry controller for the final `5 - 15 mm` XY band, not more success-only hard-range BC.

## Hard High-Start Correction Smoke

On 2026-05-09, the first targeted failure-correction smoke was added and run.

Code/config changes:

- `collect_image_correction_dataset.py` now supports high-start reset arguments.
- The correction collector now has visual/high-start scenario presets:
  - `visual`
  - `visual_control`
  - `high_start_targeted`
- New configs:
  - `configs\sim\ur5e_full\collect_high_start_hard_correction_smoke.yaml`
  - `configs\sim\ur5e_full\pretrain_high_start_hard_correction_smoke.yaml`
  - `configs\sim\ur5e_full\eval_high_start_hard_correction_smoke.yaml`
  - `configs\sim\ur5e_full\demo_high_start_hard_correction_smoke.yaml`

Correction dataset:

```text
datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_near_hole_plateau_smoke.npz
results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_smoke_inspection.md
```

Collection settings:

- source checkpoint: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip`
- scenario: `visual_camera`
- hard high-start range: `0.15 - 0.25 m` height, `0.08 - 0.16 m` XY offset
- selection: `failed_episode_near_hole`
- near-hole window: `dist_xy <= 0.060 m`, `z_above_target <= 0.140 m`
- samples: `256`
- source episodes completed: `29`
- unique source episodes in dataset: `18`
- collection success rate: `0.172`
- collection collision rate: `0.448`
- collection timeout rate: `0.379`

Correction signal quality:

| Signal | Rate |
| --- | ---: |
| near hole | 1.000 |
| failure window | 0.645 |
| opposed policy/oracle actions | 0.723 |
| policy down or oracle up | 0.867 |
| policy down and oracle less down | 1.000 |

Distribution highlights:

- median `dist_xy`: about `10.7 mm`
- median `dist_z`: about `26.3 mm`
- mean correction norm: about `0.0105 m`
- sample outcomes: `96` collision-window samples and `160` timeout-window samples

Weighted BC smoke:

```text
checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_50k_high_start_hard_correction_smoke.zip
results\ur5e_full\high_start\hard\correction\training_metadata_high_start_hard_correction_smoke.json
```

- replay mix: `85%` hard-safe 50k expert data, `15%` correction smoke data
- epochs: `1`
- samples per epoch: `4096`
- final train loss: `0.422022`
- final validation loss: `0.230001`

Same-seed 20-episode comparison against hard-safe 50k baseline, seed `574000`:

| Scenario | Baseline success | Correction success | Baseline collision | Correction collision |
| --- | ---: | ---: | ---: | ---: |
| clean | 0.450 | 0.500 | 0.350 | 0.300 |
| visual_camera | 0.250 | 0.250 | 0.250 | 0.300 |
| visual_camera_control | 0.400 | 0.400 | 0.350 | 0.300 |
| full_light_geometry | 0.250 | 0.300 | 0.300 | 0.200 |
| full_contact_light | 0.300 | 0.250 | 0.350 | 0.400 |
| hard_full_light_bucket | 0.350 | 0.350 | 0.450 | 0.400 |

Correction smoke demo:

```text
demos\ur5e_full\high_start\hard\correction\demo_high_start_hard_correction_smoke.gif
results\ur5e_full\high_start\hard\correction\demo_high_start_hard_correction_smoke_trace.csv
```

- result: timeout at `1000` steps, no collision
- first guard activation: step `283`, about `34.2 mm` XY and `119.3 mm` above target
- first reached `25 mm` XY: step `315`
- never reached `5 mm` success XY tolerance
- final state: about `8.4 mm` XY error and `31.3 mm` above target

Interpretation:

- The correction collector is now targeting the right distribution and the samples are clearly high-signal.
- The 256-sample, 1-epoch correction smoke is not enough to promote a new checkpoint.
- The next correction pass should increase sample count to `2k - 10k`, include `visual_camera_control`, and tune dataset weight/epochs so correction improves plateau behavior without hurting visual_camera.

## Narrow-Hole Demo Update

On 2026-05-08 the full UR5e demo fixture was updated to hide debug markers and narrow the hole:

- hidden rendered sites: `hole_site`, `eef_site`, `peg_tip`
- peg radius: `0.012 m`, about `24 mm` diameter
- base hole opening: about `40 mm`
- randomized hole opening: about `34 - 42 mm`

Validation after the change:

- model compatibility check passed with no missing task names
- 3-episode guarded oracle smoke: `0.667` success, `0.333` collision
- 10-episode guarded-all adapted policy smoke:
  - clean: `0.800` success, `0.200` collision
  - visual_camera: `0.800` success, `0.200` collision
  - visual_camera_control: `0.800` success, `0.200` collision
  - full_light_geometry: `0.800` success, `0.200` collision
  - full_contact_light: `0.800` success, `0.200` collision
  - hard_full_light_bucket: `0.700` success, `0.300` collision
- guarded alignment threshold scan:
  - old `0.025 m` align threshold, 30 episodes: clean `0.800`, visual_camera `0.800`, visual_camera_control `0.800`, full_light `0.767`, full_contact `0.767`, hard `0.667`
  - `0.015 m` align threshold, 30 episodes: clean `0.833`, visual_camera `0.867`, visual_camera_control `0.833`, full_light `0.800`, full_contact `0.800`, hard `0.767`
  - `0.020 m` align threshold with `guard_blend=1.0`, 30 episodes: clean `0.933`, visual_camera `0.900`, visual_camera_control `0.833`, full_light `0.867`, full_contact `0.867`, hard `0.800`
- refreshed demo succeeded:
  - `demos\ur5e_full\adapt\demo_guarded_all_50k_full_light_geometry.gif`
  - trajectory: `results\ur5e_full\adapt\demo_guarded_all_50k_full_light_geometry_trace.csv`
- 100-episode narrowed-hole policy-only baseline:
  - clean `0.750`, visual_camera `0.690`, visual_camera_control `0.640`, full_light_geometry `0.600`, full_contact_light `0.620`
- 100-episode narrowed-hole guarded-all baseline with `guarded_align_xy_tolerance=0.020` and `guard_blend=1.0`:
  - clean `0.970` success, `0.020` collision
  - visual_camera `0.910` success, `0.080` collision
  - visual_camera_control `0.860` success, `0.140` collision
  - full_light_geometry `0.830` success, `0.150` collision
  - full_contact_light `0.830` success, `0.150` collision
  - hard_full_light_bucket `0.770` success, `0.180` collision
- 50k narrowed-hole dataset:
  - dataset: `datasets\ur5e_full\adapt\image_expert_50k_narrow_hole_full_light_geometry.npz`
  - samples: `50000`
  - data collection episodes: `545`
  - collection success rate: `0.824`
  - collection collision rate: `0.154`
- 50k narrowed-hole BC fine-tune:
  - starting checkpoint: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip`
  - output checkpoint: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip`
  - epochs: `10`
  - final train loss: `0.039346`
  - final validation loss: `0.041165`
- 100-episode narrowed-hole policy-only after fine-tune:
  - clean `0.850`, visual_camera `0.800`, visual_camera_control `0.740`, full_light_geometry `0.740`, full_contact_light `0.740`
- 100-episode narrowed-hole guarded-all after fine-tune:
  - clean `0.980` success, `0.020` collision
  - visual_camera `0.930` success, `0.070` collision
  - visual_camera_control `0.860` success, `0.140` collision
  - full_light_geometry `0.830` success, `0.130` collision
  - full_contact_light `0.840` success, `0.140` collision
  - hard_full_light_bucket `0.780` success, `0.180` collision
- narrowed-hole fine-tuned demo:
  - `demos\ur5e_full\adapt\demo_guarded_all_50k_narrow_hole_full_light_geometry.gif`
  - inserted successfully in `91` steps

Interpretation:

- The demo is visually cleaner and no longer shows the red/green debug points.
- The main demo config now uses `max_steps: 400`, `guarded_align_xy_tolerance=0.020`, and `guard_blend=1.0`; the refreshed demo inserted successfully in `91` steps.
- Narrowing the hole is a real difficulty increase. The narrowed-hole fine-tune improves policy-only performance substantially, but guarded hard/full collision is still about `0.13 - 0.18`.

## Narrow-Hole Correction Pass

On 2026-05-08, a DAgger-style near-contact correction pass was run before starting the high-start curriculum.

Smoke validation:

- dataset: `datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_smoke.npz`
- samples: `256`
- source episodes: `42`
- collection episodes: `270`
- selection: `near_hole_failure_window`
- near-hole rate: `1.000`
- failure-window rate: `1.000`
- collision samples: `191`
- timeout samples: `65`
- smoke weighted BC passed for 1 epoch

Main correction dataset:

- dataset: `datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_8k_min006.npz`
- requested samples: `8000`
- collected samples: `1836`
- collection episodes: `4000`
- source episodes: `383`
- reason for shortfall: `min_correction_norm=0.006` plus `max_episodes_per_config=2000` filtered out many failures
- near-hole rate: `1.000`
- failure-window rate: `1.000`
- opposed policy/oracle action rate: `0.522`
- policy down while oracle asks up/less down rate: `0.951`

Weighted BC:

- starting checkpoint: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip`
- output checkpoint: `checkpoints\ur5e_full\correction\sac_image_bc_50k_narrow_correction_8k_w10_e2.zip`
- datasets: 90% narrowed-hole expert replay, 10% correction replay
- epochs: `2`
- final train loss: `0.094687`
- final validation loss: `0.090112`

Policy-only 100-episode evaluation after correction:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.870 | 0.130 | 0.000 |
| visual_camera | 0.780 | 0.140 | 0.080 |
| visual_camera_control | 0.760 | 0.200 | 0.040 |
| full_light_geometry | 0.750 | 0.180 | 0.070 |
| full_contact_light | 0.720 | 0.210 | 0.070 |

Guarded-all 100-episode evaluation after correction:

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.970 | 0.020 | 0.010 |
| visual_camera | 0.940 | 0.050 | 0.010 |
| visual_camera_control | 0.870 | 0.130 | 0.000 |
| full_light_geometry | 0.830 | 0.130 | 0.040 |
| full_contact_light | 0.840 | 0.140 | 0.020 |
| hard_full_light_bucket | 0.780 | 0.180 | 0.040 |

Interpretation:

- The correction data quality is good: every selected sample is a near-hole failure-window correction.
- The correction pass only gives marginal policy-only gains on `visual_camera_control` and `full_light_geometry`, and it slightly hurts `visual_camera` and `full_contact_light`.
- Guarded-all performance is effectively flat versus the narrowed-hole adapted checkpoint.
- Do not promote the correction checkpoint as the default unless a later larger/lower-threshold correction pass clearly improves the full-contact and hard buckets.

## Next Steps

1. Expand hard high-start correction from smoke to a `2k - 10k` sample dataset, including both `visual_camera` and `visual_camera_control`.
2. Tune correction replay weight and epochs. The 256-sample smoke used `15%` correction for `1` epoch and was mixed; next try lower weights such as `5% - 10%` and `2 - 3` epochs.
3. Re-evaluate correction candidates against hard-safe 50k, two-phase, and `align=0.025` on a shared seed set.
4. Prototype a guarded re-align/retry behavior for episodes that stall near the hole before final insertion.
5. Keep `high_start_two_phase`, hard down-block, `align=0.025`, and the correction-smoke checkpoint as candidates, not defaults, until they clearly beat the hard-safe baseline.
6. Only after original high-start success is stable, introduce larger randomized initial XY offsets.
7. Only after high-start plus larger XY offsets are stable, reintroduce control/geometry/contact randomization.
8. Audit the full UR5e model against the raw Menagerie UR5e XML and add a report showing exactly what was changed for the task wrapper.
9. Improve the robot controller by adding orientation-constrained IK and a posture/nullspace regularization term so the UR5e joint motion looks more realistic.
10. Reduce full_light/full_contact collision rate from about `0.13 - 0.18` by scanning guarded thresholds or running a larger/lower-threshold correction pass if needed.
11. Generate a short comparison demo set: adapter baseline, full UR5e adapted policy-only, full UR5e adapted guarded-all, high-start visual-search policy.
12. Decide whether the full UR5e model should become the regular sim baseline after the controller realism and high-start curriculum are improved.
13. Continue real-readiness work only in read-only mode:
   - session preparation
   - real camera frame capture
   - crop inspection
   - calibration/config validation
   - synthetic or recorded replay

## Key Commands

Full UR5e model check:

```powershell
python scripts\inspect_robot_model.py --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml --output-md results\robot_model_ur5e_full.md --fail-on-missing
```

Full UR5e oracle smoke test:

```powershell
python scripts\oracle_rollout.py --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml --observation-mode state --episodes 3 --max-steps 120
```

Full UR5e demo:

```powershell
python scripts\demo_policy.py `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --observation-mode image `
  --include-near-hole-crop `
  --episodes 1 `
  --output results\ur5e_full_demo.gif `
  --render-width 1280 `
  --render-height 720
```

Full UR5e image eval matrix:

```powershell
python scripts\eval_matrix.py `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 100 `
  --device cpu `
  --output-csv results\ur5e_full_eval_matrix.csv `
  --output-md results\ur5e_full_eval_matrix.md `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01
```

Full UR5e guarded eval:

```powershell
python scripts\eval_guarded_policy.py `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 100 `
  --seed 90000 `
  --device cpu `
  --include-hard-bucket `
  --output-csv results\ur5e_full_eval_guarded.csv `
  --output-md results\ur5e_full_eval_guarded.md `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --guard-scenario-filter geometry `
  --guard-start-xy 0.06 `
  --guard-start-z 0.08 `
  --guard-risk-xy 0.0 `
  --guard-blend 0.75 `
  --guard-min-policy-steps 0
```

## When To Update This File

Update this file after:

- a new training/eval checkpoint becomes recommended
- major metrics change
- the default model path changes
- UR5e full model moves from demo-only to training path
- real-robot readiness gates change
- a milestone is pushed to GitHub
- the next-step plan changes materially
