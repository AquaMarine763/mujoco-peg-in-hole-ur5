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

Keep these variants diagnostic-only:

- wrong-basin hold
- wrong-basin re-acquire
- low-Z lateral-pop recovery
- high-yaw-only action selection
- late-finish / XY-freeze variants

## Recommended Next Loop

1. Run `scan_visual_yaw_views.py` and compare wrist / crop variants.
2. Collect a new key-focused yaw dataset with the best view.
3. Train `train_visual_yaw_estimator.py`.
4. Run `eval_visual_yaw_estimator.py`.
5. Recheck the visible-brake guarded baseline.

The current best yaw estimator is the 8k stratified crop-wider model with
overall validation mean/p95 `2.10/5.74 deg`. It is accurate enough to test
inside a gated controller, but not enough to remove visibility/confidence
checks.

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

Tight-yaw smoke:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 -Profile rectangular_key -Episodes 5 -Seeds 906500
```
