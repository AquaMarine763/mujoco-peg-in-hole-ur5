# Full UR5e Simulation Configs

These flat YAML files run the same task interface on the full UR5e MuJoCo model:

```text
assets/ur5e_full/ur5e_peg_in_hole_full.xml
```

Current full UR5e task geometry:

- Debug visualization sites are hidden in the rendered scene.
- Peg radius is `0.012 m`, so peg diameter is about `24 mm`.
- Base hole opening is about `40 mm`.
- Geometry-randomized configs use `geometry_hole_half_size_range: [0.017, 0.021]`, so randomized opening is about `34 - 42 mm`.

Metrics collected before this geometry change used a wider hole and should be treated as pre-change baselines.

The current strongest guarded demo config uses `max_steps: 400` so the video is
less likely to stop during the final downward insertion phase.

After the hole was narrowed, the guarded insertion alignment threshold was
retuned from `0.025 m` to `0.020 m` in the full UR5e configs. A 30-episode
comparison on the adapted checkpoint showed `0.020 m` was the best current
tradeoff among `0.015`, `0.020`, and `0.025`. The guarded full UR5e configs
now use `guard_blend: 1.0`, which was better than the previous `0.75` on the
narrowed hole.

The current recommended narrowed-hole full UR5e policy is:

```text
checkpoints/ur5e_full/adapt/sac_image_bc_50k_narrow_hole_full_light_geometry.zip
```

It was fine-tuned from the pre-narrow full UR5e adapted checkpoint using:

```text
datasets/ur5e_full/adapt/image_expert_50k_narrow_hole_full_light_geometry.npz
```

The original adapter-trained policy remains useful only as an early starting point for full-model adaptation.

Recommended adapter-trained starting policy:

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip
```

Common commands:

```powershell
python scripts/eval_matrix.py --config configs/sim/ur5e_full/eval_image_crop.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_guarded_image_crop.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_guarded_image_crop.yaml
```

Current strongest adapted full UR5e commands:

```powershell
python scripts/eval_matrix.py --config configs/sim/ur5e_full/eval_image_narrow_50k.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_guarded_narrow_50k_all.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_guarded_narrow_50k_all.yaml
```

Narrow-hole near-contact correction commands:

```powershell
python scripts/collect_image_correction_dataset.py --config configs/sim/ur5e_full/collect_correction_narrow_smoke.yaml
python scripts/pretrain_image_actor_bc_weighted.py --config configs/sim/ur5e_full/pretrain_correction_narrow_smoke.yaml
python scripts/collect_image_correction_dataset.py --config configs/sim/ur5e_full/collect_correction_narrow_8k.yaml
python scripts/pretrain_image_actor_bc_weighted.py --config configs/sim/ur5e_full/pretrain_correction_narrow_8k_w10_e2.yaml
python scripts/eval_matrix.py --config configs/sim/ur5e_full/eval_image_narrow_correction_8k_w10_e2.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_guarded_narrow_correction_8k_w10_e2.yaml
```

The first correction pass produced a valid high-signal correction dataset, but
it did not become the default policy. The strict 8k config collected `1836`
samples before hitting the episode cap. The resulting checkpoint is:

```text
checkpoints/ur5e_full/correction/sac_image_bc_50k_narrow_correction_8k_w10_e2.zip
```

100-episode guarded-all metrics were effectively flat versus the narrowed-hole
adapted checkpoint: clean `0.970`, visual_camera `0.940`,
visual_camera_control `0.870`, full_light_geometry `0.830`,
full_contact_light `0.840`, hard_full_light_bucket `0.780`.

Narrow-hole guarded scan commands:

```powershell
python scripts/scan_guarded_policy_params.py --config configs/sim/ur5e_full/scan_guarded_narrow_hole_smoke.yaml
python scripts/scan_guarded_policy_params.py --config configs/sim/ur5e_full/scan_guarded_narrow_hole_focused.yaml
```

Adaptation smoke commands:

```powershell
python scripts/collect_image_expert_dataset.py --config configs/sim/ur5e_full/collect_image_expert_smoke.yaml
python scripts/pretrain_image_actor_bc.py --config configs/sim/ur5e_full/pretrain_image_bc_smoke.yaml
python scripts/collect_image_expert_dataset.py --config configs/sim/ur5e_full/collect_high_start_smoke.yaml
python scripts/pretrain_image_actor_bc.py --config configs/sim/ur5e_full/pretrain_high_start_smoke.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_guarded_smoke.yaml
```

Adaptation run commands:

```powershell
python scripts/collect_image_expert_dataset.py --config configs/sim/ur5e_full/collect_image_expert_50k.yaml
python scripts/pretrain_image_actor_bc.py --config configs/sim/ur5e_full/pretrain_image_bc_50k.yaml
python scripts/collect_image_expert_dataset.py --config configs/sim/ur5e_full/collect_high_start_50k.yaml
python scripts/pretrain_image_actor_bc.py --config configs/sim/ur5e_full/pretrain_high_start_50k.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_guarded_50k.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_guarded_50k.yaml
```

High-start configs deliberately use `visual_camera` for the first curriculum
stage. A direct high-start `full_light_geometry` smoke was too hard for the
current oracle and produced high collision, so geometry/control/contact
randomization should be added only after high-start visual search is stable.

The first full 50k high-start stage completed, but it is not yet a successful
policy. It collected `50000` samples from `225` successful episodes out of
`1044` attempts. Collection success was `0.216`, collision was `0.552`. The
resulting checkpoint is:

```text
checkpoints/ur5e_full/high_start/sac_image_bc_50k_high_start_visual_camera.zip
```

100-episode guarded-all high-start success was: clean `0.190`,
visual_camera `0.240`, visual_camera_control `0.180`, full_light_geometry
`0.170`, full_contact_light `0.220`, hard_full_light_bucket `0.150`. The demo
timed out at `1000` steps with final XY about `8.8 mm` and final Z about
`47.6 mm`.

The easy high-start stage bridges the gap between near-hole insertion and the
original high-start range:

```powershell
python scripts/collect_image_expert_dataset.py --config configs/sim/ur5e_full/collect_high_start_easy_50k.yaml
python scripts/pretrain_image_actor_bc.py --config configs/sim/ur5e_full/pretrain_high_start_easy_50k.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_easy_guarded_50k.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_easy_guarded_50k.yaml
```

Easy high-start uses `0.08 - 0.15 m` height and `0.04 - 0.10 m` XY offset.
The current easy 50k checkpoint is:

```text
checkpoints/ur5e_full/high_start/easy/sac_image_bc_50k_high_start_easy_visual_camera.zip
```

Easy 50k collection: `50000` samples, `0.647` oracle success, `0.119`
collision. Same-seed 100-episode high-start guarded-all evaluation with seed
`534000`: clean `0.620`, visual_camera `0.630`, visual_camera_control
`0.590`, full_light_geometry `0.580`, full_contact_light `0.540`,
hard_full_light_bucket `0.480`. A seed `534000` demo inserted in `247` steps;
the default seed `542000` demo timed out, so this checkpoint is not a final
high-start solution.

The medium high-start stage uses `0.10 - 0.18 m` height and `0.06 - 0.12 m`
XY offset:

```powershell
python scripts/collect_image_expert_dataset.py --config configs/sim/ur5e_full/collect_high_start_medium_50k.yaml
python scripts/pretrain_image_actor_bc.py --config configs/sim/ur5e_full/pretrain_high_start_medium_50k.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_medium_guarded_50k.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_medium_guarded_50k.yaml
```

The current medium 50k checkpoint is:

```text
checkpoints/ur5e_full/high_start/medium/sac_image_bc_50k_high_start_medium_visual_camera.zip
```

Medium 50k collection: `50000` samples, `0.627` oracle success, `0.087`
collision. 100-episode high-start guarded-all evaluation: clean `0.680`,
visual_camera `0.620`, visual_camera_control `0.510`, full_light_geometry
`0.510`, full_contact_light `0.510`, hard_full_light_bucket `0.490`. The
medium 50k demo inserted in `285` steps from about `8.65 cm` XY offset and
`11.25 cm` height.

The original hard high-start range was re-tested from the medium checkpoint
and then trained with a safer `0.12 m` approach height:

```powershell
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_from_medium_guarded_50k.yaml
python scripts/collect_image_expert_dataset.py --config configs/sim/ur5e_full/collect_high_start_hard_safe_50k.yaml
python scripts/pretrain_image_actor_bc.py --config configs/sim/ur5e_full/pretrain_high_start_hard_safe_50k.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_safe_50k.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_hard_safe_50k.yaml
```

The current hard-range candidate is:

```text
checkpoints/ur5e_full/high_start/hard/sac_image_bc_50k_high_start_hard_safe_visual_camera.zip
```

Hard-safe 50k collection: `50000` samples, `0.377` oracle success, `0.110`
collision. 100-episode hard-range guarded-all evaluation: clean `0.480`,
visual_camera `0.450`, visual_camera_control `0.330`, full_light_geometry
`0.270`, full_contact_light `0.310`, hard_full_light_bucket `0.330`.
Hard-range demos can succeed, but the average success rate is still too low
for this to be a default policy.

The first two-phase high-start controller pass added:

- `oracle_mode: high_start_two_phase` for expert collection.
- `guarded_oracle_mode: high_start_two_phase` for guarded evaluation/demo.
- pre-guard `guard_block_down_when_unaligned`, so downward policy actions can
  be blocked before the near-hole guard activates.

```powershell
python scripts/collect_image_expert_dataset.py --config configs/sim/ur5e_full/collect_high_start_hard_twophase_smoke.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_twophase_hard_safe_50k.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_hard_twophase_hard_safe_50k.yaml
```

The first hard-range two-phase guarded result was mixed: clean `0.490`,
visual_camera `0.340`, visual_camera_control `0.320`, full_light_geometry
`0.350`, full_contact_light `0.350`, hard_full_light_bucket `0.270`. It reduced
some collision risk but increased timeout, so it needs parameter tuning before
it should become a default.

Hard high-start guarded parameter scan:

```powershell
python scripts/scan_guarded_policy_params.py --config configs/sim/ur5e_full/scan_high_start_hard_twophase_guarded_smoke.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_align025_guarded_50k.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_hard_align025_guarded_50k.yaml
```

The scan covers `guarded_two_stage` vs `high_start_two_phase`,
`guarded_align_xy_tolerance` values `0.020/0.025/0.030`, and block-down
false/true. The 5-episode smoke did not show a clear two-phase or block-down
benefit. The focused `align=0.025`, `guarded_two_stage` 100-episode result was:
clean `0.530`, visual_camera `0.370`, visual_camera_control `0.310`,
full_light_geometry `0.340`, full_contact_light `0.290`,
hard_full_light_bucket `0.270`.

The focused demo timed out at `1000` steps without collision, ending near
`8.4 mm` XY error and `32.8 mm` above target. Treat this as evidence for
near-hole plateau correction, not as a new default guarded setting.

Hard high-start correction smoke:

```powershell
python scripts/collect_image_correction_dataset.py --config configs/sim/ur5e_full/collect_high_start_hard_correction_smoke.yaml
python scripts/inspect_image_correction_dataset.py --dataset datasets/ur5e_full/high_start/hard/correction/image_correction_high_start_hard_near_hole_plateau_smoke.npz --output-md results/ur5e_full/high_start/hard/correction/image_correction_high_start_hard_smoke_inspection.md --output-csv results/ur5e_full/high_start/hard/correction/image_correction_high_start_hard_smoke_inspection.csv
python scripts/pretrain_image_actor_bc_weighted.py --config configs/sim/ur5e_full/pretrain_high_start_hard_correction_smoke.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_correction_smoke.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_hard_correction_smoke.yaml
```

This smoke collected `256` visual_camera hard high-start near-hole failure
samples from `29` policy episodes. The data is high-signal: `72.3%` opposed
policy/oracle actions and `86.7%` policy-down/oracle-up-or-less-down. The
1-epoch weighted BC checkpoint is not a default because 20-episode same-seed
evaluation was mixed and the demo still timed out near `8.4 mm` XY error.

Hard high-start correction 2k pass:

```powershell
python scripts/collect_image_correction_dataset.py --config configs/sim/ur5e_full/collect_high_start_hard_correction_2k.yaml
python scripts/inspect_image_correction_dataset.py --dataset datasets/ur5e_full/high_start/hard/correction/image_correction_high_start_hard_near_hole_plateau_2k.npz --output-md results/ur5e_full/high_start/hard/correction/image_correction_high_start_hard_2k_inspection.md --output-csv results/ur5e_full/high_start/hard/correction/image_correction_high_start_hard_2k_inspection.csv
python scripts/pretrain_image_actor_bc_weighted.py --config configs/sim/ur5e_full/pretrain_high_start_hard_correction_2k_w05_e2.yaml
python scripts/pretrain_image_actor_bc_weighted.py --config configs/sim/ur5e_full/pretrain_high_start_hard_correction_2k_w10_e2.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_correction_2k_w05_e2.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_correction_2k_w10_e2.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_hard_correction_2k_w10_e2.yaml
```

This pass collected `2000` samples: `1000` visual_camera and `1000`
visual_camera_control. The signal stayed strong: `74.9%` opposed actions and
`86.8%` policy-down/oracle-up. Same-seed 20-episode evaluation showed the 5%
replay candidate was effectively baseline, while the 10% replay candidate only
improved hard bucket from `0.35` to `0.40`. The 10% demo still timed out near
`8.4 mm` XY error and `30.6 mm` above target.

Hard high-start bounded retry prototype:

```powershell
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_retry_guarded_50k.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_hard_retry_guarded_50k.yaml
```

The prototype adds retry diagnostics and bounds each retry attempt to avoid a
long-lived controller takeover. The current result is negative, not promoted:
same-seed 20-episode success was clean `0.300`, visual_camera `0.150`,
visual_camera_control `0.250`, full_light_geometry `0.250`,
full_contact_light `0.250`, hard_full_light_bucket `0.300`. The demo still
timed out near `8.4 mm` XY error and `27.5 mm` above target after two retry
attempts.

Hard high-start no-prediction guarded controller:

```powershell
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_pred0_guarded_50k.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_hard_pred0_guarded_50k.yaml
```

This is now the strongest controller-only hard high-start result. It sets
`guarded_prediction_steps: 0.0` while leaving the guarded controller otherwise
close to the hard-safe baseline. Same-seed 100-episode success improved to:
clean `0.560`, visual_camera `0.500`, visual_camera_control `0.530`,
full_light_geometry `0.450`, full_contact_light `0.380`,
hard_full_light_bucket `0.430`. The demo seed `571001` inserted in `411`
steps. The neighboring seed `571000` still times out near the old `8 mm`
plateau and should remain a hard-case diagnostic.

Strict hold-Z diagnostic:

```powershell
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_strict_align_guarded_50k.yaml
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_hard_strict_align_guarded_50k.yaml
```

`guarded_hold_z_until_insert: true` with the old prediction setting was mostly
flat versus baseline: clean `0.400`, visual_camera `0.250`,
visual_camera_control `0.400`, full_light_geometry `0.250`,
full_contact_light `0.300`, hard_full_light_bucket `0.350`. With prediction
disabled, the same failed demo seed can enter the `5 mm` band, but it tends to
oscillate when XY drifts back out during descent. Do not promote strict hold-Z
yet.

Hard high-start insert latch / descent hysteresis diagnostic:

```powershell
python scripts/eval_guarded_policy.py --config configs/sim/ur5e_full/eval_high_start_hard_pred0_latch_guarded_50k.yaml --hard-bucket-only --episodes 10
python scripts/demo_policy.py --config configs/sim/ur5e_full/demo_high_start_hard_pred0_latch_guarded_50k.yaml
```

This config adds a stateful insert latch on top of
`guarded_prediction_steps: 0.0`. It can pause descent after entering the `5 mm`
insert band and includes a diagnostic two-stage recenter mode: lift first, then
move laterally. It is not promoted. A 10-episode hard-bucket smoke reached only
`0.400` success with `0.500` collision, and the hard demo seed `571000` still
failed. The trace shows the peg can enter the `5 mm` band, but once it drifts
and wedges inside the hole-wall height range, physical tracking becomes too
slow for the latch/recenter controller to recover reliably.

Next planned sequence:

1. Keep no-prediction guarded insertion as the current best controller-only hard high-start setting.
2. Treat latch/recenter, retry, strict hold-Z, and two-phase guard as diagnostics until they clearly beat no-prediction guarded insertion.
3. Add persistent action-tracking diagnostics if continuing controller work.
4. Move the next learning iteration to contact-aware failure correction / DAgger for wedged near-hole states.
5. Add larger randomized initial XY offsets only after hard high-start search works.
6. Reintroduce control/geometry/contact randomization after the search stage is stable.
