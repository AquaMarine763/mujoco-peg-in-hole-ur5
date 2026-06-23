# Sim2Real Multi-Geometry v2 Visual-Yaw Align

This is the current active research branch for tightening visual yaw alignment
on top of the true-fixture v2 stack.

Status:

- branch: `feature/multigeom-v2-visual-yaw-align`
- stable sim-to-real mainline: `sim2real_multigeom_v1`
- underlying fixture branch: `feature/multigeom-v2-true-fixtures`

Use this file first for the active commands and decision gate.

## Current Safe Baseline

The baseline to recheck is the rectangular-key visible-brake configuration:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_eval.yaml `
  -Profile rectangular_key `
  -Episodes 120 `
  -Seeds 906500,907500,908500,909500,910500,911500
```

Current result: `104/120`, collision `0/120`, timeout `16/120`.

## Current Low-Z Crop-High Candidate

The refined final-descent visual input keeps the wrist camera pose unchanged
and only shifts the policy crop upward:

```yaml
near_hole_crop_offset: [-18, -12]
guard_visual_yaw_align_model: results/visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_low_z_crop_high.pt
```

Use:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_eval.yaml `
  -Profile rectangular_key `
  -Episodes 20 `
  -Seeds 906500,907500,908500,909500,910500,911500 `
  -ResultDir results\vy_visible_brake_low_z_crop_high_seed906500_911500_120ep
```

Current six-seed result: `111/120`, collision `0/120`, timeout `9/120`.
Report: `results\visual_yaw_low_z_crop_high_120ep_summary.md`.
Failure analysis: `results\visual_yaw_low_z_crop_high_failure_analysis.md`.

This is a real improvement over the visible-brake baseline, but not a final
promotion target yet. The residual failures are timeout / wrong-yaw-basin
cases rather than collision cases: `7/9` finish with final yaw error above
`150 deg`, while `2/9` are near-insert yaw-gate / descent-timing misses.

Keep these variants diagnostic-only:

- wrong-basin hold
- wrong-basin re-acquire
- low-Z lateral-pop recovery
- high-yaw-only action selection
- late-finish / XY-freeze variants

## Recommended Next Loop

1. Analyze the nine low-Z crop-high timeouts and separate wrong-yaw-basin
   failures from not-descended / not-inserted failures.
2. Avoid broadening scalar brake thresholds unless a new collision class
   appears; the current low-Z candidate already has zero collision.
3. If the timeouts are visual ambiguity dominated, try a second visual cue
   near final descent instead of another wide crop scan.
4. Keep square visual yaw disabled until its false `~45 deg` runtime
   corrections are understood.

The current best runtime yaw estimator for the low-Z key line is the 8k
stratified low-Z crop-high model. Held-out validation mean/p95 is
`2.079/6.153 deg` overall and `2.726/7.377 deg` on `rectangular_key`. It is
accurate enough for gated runtime use, but not enough to remove
visibility/confidence checks.

Low-Z view scan result:

- `crop_wider_high` is the best current low-Z candidate.
- It beat `open_high` and both `raise_center` variants on key error in the
  96x4 and 256x8 scans.
- The remaining low-Z errors are still large, so the next useful move is a
  low-Z key-focused dataset rather than another broad camera sweep.

## Short Commands

Visual-yaw view scan:

```powershell
python scripts\scan_visual_yaw_views.py --samples-per-candidate 128 --epochs 8 --batch-size 64 --seed 908000
```

Key-focused yaw dataset:

```powershell
python scripts\collect_visual_yaw_dataset.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_dataset_key_focus_8k_stratified.yaml
```

Key-focused yaw estimator:

```powershell
python scripts\train_visual_yaw_estimator.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_train_key_focus_8k_stratified.yaml
python scripts\eval_visual_yaw_estimator.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_eval_key_focus_8k_stratified.yaml
```

Low-Z key-focused yaw estimator:

```powershell
python scripts\collect_visual_yaw_dataset.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_dataset_key_focus_8k_stratified_low_z_crop_high.yaml
python scripts\train_visual_yaw_estimator.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_train_key_focus_8k_stratified_low_z_crop_high.yaml
python scripts\eval_visual_yaw_estimator.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_eval_key_focus_8k_stratified_low_z_crop_high.yaml
```

Low-Z guarded runtime eval:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_eval.yaml `
  -Profile rectangular_key `
  -Episodes 20 `
  -Seeds 906500,907500,908500,909500,910500,911500 `
  -ResultDir results\vy_visible_brake_low_z_crop_high_seed906500_911500_120ep
```

Tight-yaw smoke:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 -Profile rectangular_key -Episodes 5 -Seeds 906500
```
