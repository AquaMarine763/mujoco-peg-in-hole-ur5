# Sim2Real Multi-Geometry v2 Visual-Yaw Align

This is the current active research branch for tightening visual yaw alignment
on top of the true-fixture v2 stack.

Status:

- branch: `feature/multigeom-v2-visual-yaw-align`
- stable sim-to-real mainline: `sim2real_multigeom_v1`
- underlying fixture branch: `feature/multigeom-v2-true-fixtures`

Use this file first for the active commands and decision gate.


## Current Per-Shape Runtime Defaults

Use the short wrappers for current visual-yaw alignment work:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 -Profile square_square -Seeds @(906500) -Episodes 5
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 -Profile triangle_triangle -Seeds @(906500) -Episodes 20
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 -Profile hex_hex -Seeds @(906500) -Episodes 20
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 -Profile rectangular_key -Seeds @(906500) -Episodes 20
.\scripts\sim2real\demo_multigeom_v2_visual_yaw_align.ps1 -Profile square_square -Seed 906500 -ResultDir results\square_v148_demos
.\scripts\sim2real\demo_multigeom_v2_visual_yaw_align.ps1 -Profile triangle_triangle -Seed 906504 -ResultDir results\triangle_wrist_safe_v3_demos
.\scripts\sim2real\demo_multigeom_v2_visual_yaw_align.ps1 -Profile hex_hex -Seed 906500 -ResultDir results\hex_early_approach_descent_demos
.\scripts\sim2real\demo_multigeom_v2_visual_yaw_align.ps1 -Profile rectangular_key -Seed 906500 -ResultDir results\rectangular_key_post_yaw_reapproach_demos
```

Current wrapper behavior:

- `square_square`: routes to the stable v148/v149 sim2real v1 stack by default through `configs\sim2real\multigeom_v1_eval.yaml`. Historical v148/v149 evidence is `720/720`, collision `0/720`, timeout `0/720`; current wrapper smoke `results\square_default_wrapper_verify_5ep` is `5/5`.
- `triangle_triangle`: enables the wrist-safe absolute shape-yaw target protocol by default. Latest broad gate: `results\triangle_wrist_safe_v3_gate_120ep`, `116/120`, collision `0/120`, timeout `4/120`, and no wrist-span outliers above `180 deg`.
- `hex_hex`: routes to the hex-only early-approach/descent config by default. Latest broad gate: `results\hex_early_approach_descent_gate_120ep`, `120/120`, collision `0/120`, timeout `0/120`.
- `rectangular_key`: routes to the post-yaw reapproach key candidate by default through `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_local_hold_stronger_brake_early_approach_post_yaw_reapproach_v1_eval.yaml`. Historical stronger-brake six-seed gate was `112/120`, collision `0/120`, timeout `8/120`; post-yaw reapproach fixed the seed `906500` check to `20/20`, collision `0/20`, timeout `0/20`, but the broader six-seed x five-episode gate is currently `29/30`, collision `1/30`, timeout `0/30`.
- Other profiles still use the generic multishape visual-yaw config unless `-Config` is provided explicitly.
- Current short-wrapper gate after routing is `results\visual_yaw_align_post_yaw_reapproach_default_20ep`: `square_square=20/20`, `triangle_triangle=20/20`, `hex_hex=20/20`, `rectangular_key=20/20`, all with zero collision and zero timeout. Treat this as a smoke gate only; the rectangular-key multi-seed gate below is the current blocker for promotion.

Current demos to inspect:

- Square: `results\square_v148_demos\demo_square_square_seed906500.gif`.
- Triangle: `results\triangle_wrist_safe_v3_demos\demo_triangle_triangle_seed906504.gif`, `907508.gif`, `908510.gif`, `910505.gif`, `910500.gif`, `910501.gif`.
- Hex: `results\hex_early_approach_descent_demos\demo_hex_hex_seed906500.gif`.
- Rectangular key: `results\rectangular_key_post_yaw_reapproach_demos\demo_rectangular_key_seed906500.gif`.

Decision rule: keep per-shape routing. This is not a single unified learned policy/controller configuration yet; it is a deployment routing layer that selects the best current runtime stack per shape. Do not force a unified multishape default while square, triangle, hex, and key still rely on different runtime assumptions.


## 2026-07-02 Rectangular-Key Estimator v2 Candidate

The current best rectangular-key candidate is now:

```yaml
configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_local_hold_stronger_brake_early_approach_post_yaw_reapproach_low_z_verifier_v3_estimator_v2_relaxed_rawnorm_v1_eval.yaml
```

What changed:

- kept the v3 controller logic, because v4/v5/v7 did not improve the remaining timeout and v6 regressed;
- trained estimator v2 from low-Z crop-high key data plus targeted seed `909502` and `911504` correction samples;
- relaxed only the primary visual-yaw raw-norm gate to `0.015`, because estimator v2 is accurate but lower-confidence around `170-180 deg` key-yaw states.

Evidence:

- offline seed `911504` targeted set: v1 `16.24 deg` mean / `22.11 deg` p95 / `49.4%` bad fraction; v2 `1.89 deg` mean / `5.09 deg` p95 / `0%` bad fraction;
- focused key gate `909500,911500`: `10/10`, collision `0/10`, timeout `0/10`;
- broad key gate `results
ectangular_key_low_z_verifier_v3_estimator_v2_relaxed_rawnorm_v1_6seed_5ep`: `30/30`, collision `0/30`, timeout `0/30`;
- triangle regression `results	riangle_wrist_safe_v3_estimator_v2_relaxed_rawnorm_v1_regression_3seed_5ep`: `15/15`, collision `0/15`, timeout `0/15`.

Next gate before promotion: route rectangular-key wrapper/demo to this candidate, generate a seed `911504` demo, then run the four-shape wrapper smoke gate.

## 2026-07-02 Rectangular-Key Post-Yaw Reapproach v1

The remaining rectangular-key failure after stronger-brake routing was not a low-Z jam. It was a high-Z/far-XY timeout after a large visual-yaw correction, where final-servo lateral drift left the peg far from the keyhole before descent.

The current key fix is default-off in the low-level CLI but enabled by the rectangular-key per-shape config:

- `--guard-visual-yaw-align-post-yaw-reapproach-allow-applied-trigger` allows reapproach immediately after a visual-yaw target is applied.
- The current key config is `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_local_hold_stronger_brake_early_approach_post_yaw_reapproach_v1_eval.yaml`.
- The demo config is `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_rectangular_key_stronger_brake_early_approach_post_yaw_reapproach_v1_demo.yaml`.

Validation so far:

- Direct key candidate: `results\rectangular_key_early_approach_post_yaw_reapproach_v1_20ep_seed906500`, `20/20`, collision `0/20`, timeout `0/20`.
- Current all-shape short-wrapper gate: `results\visual_yaw_align_post_yaw_reapproach_default_20ep`, `80/80` total across square/triangle/hex/key, collision `0/80`, timeout `0/80`.
- Rectangular-key six-seed x five-episode gate: `results\rectangular_key_post_yaw_reapproach_v1_6seed_5ep`, `29/30`, collision `1/30`, timeout `0/30`. The failure is seed `909502`, episode `2`.
- False-small analysis: `results\rectangular_key_post_yaw_reapproach_v1_6seed_5ep\false_small_analysis\visual_yaw_false_small_analysis.md`. It found `126` false-small rows (`pred<=4 deg`, truth `>=12 deg`), including `78` in the failed episode. The critical low-Z rows are the key issue: visual yaw predicts near-aligned while true yaw remains about `14-24 deg`, so descent proceeds into collision.
- Rejected diagnostics: the hold-descent variant and low-Z z-gate latch variant each converted the seed `909502` collision into a timeout in focused testing, but did not recover the episode. Do not promote either as default.
- This remains a useful key default candidate, but it is not ready for push/tag promotion as a release milestone until the low-Z false-small visual-yaw failure is addressed.

## Triangle Wrist-Rotation Status

The original triangle demo had a real-robot wrist-safety issue. On seed
`910500`, the pre-diagnostic trace showed `wrist_2` span about `322.9 deg`
overall and about `206 deg` during insertion/recovery. The root cause was
repeated relative visual-yaw correction on a 120-degree symmetric shape:
predictions can flip equivalent basins, and even same-basin corrections can
accumulate because each frame asks the arm to rotate relative to the current
pose.

Rejected default-off diagnostics:

```powershell
--guard-visual-yaw-align-equivalent-basin-latch-enabled
--guard-visual-yaw-align-hold-target-override-applied
```

Smoke results on seed `910500` rejected these variants:

- equivalent-basin latch only: collision, `wrist_2` span still about
  `310.7 deg`
- pre-active target hold: `wrist_2` span about `142.2 deg`, but timeout at
  high Z
- hard IK wrist target clipping: collision / XY excursions

Current triangle protocol:

- `set_pose_ik_target_to_nearest_shape_hole_yaw` chooses an absolute
  hole-frame shape-yaw target across symmetry-equivalent orientations using
  wrist/IK/joint-margin costs.
- The wrapper enables `--guard-visual-yaw-align-absolute-shape-target` only for
  `triangle_triangle`.
- `freeze-aligned-target-source` is `target`, not `current`, so we do not
  freeze a still-misaligned real pose.
- `--guard-visual-yaw-align-absolute-shape-target-descent-unlock` allows
  descent after the absolute target has been held near the hole. This handles
  the observed false-large visual-yaw pattern where true yaw was already about
  `0.6 deg` but the estimator kept predicting about `20 deg` and blocked
  descent.

Focused validation:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Profile triangle_triangle `
  -Seeds 910500 `
  -Episodes 10 `
  -ResultDir results\triangle_abs_shape_target_unlock_wrapper_10ep_v2
```

Result: `10/10`, collision `0/10`, timeout `0/10`, final yaw
`0.58-0.71 deg`. This is a major improvement over the old wrist-overrotation
demo, but not a final safety proof. Most `wrist_2` spans are now
`104-125 deg`; outliers still reach about `193/213/226 deg`, and one episode
has large `wrist_1/wrist_3` spans around `165/177 deg`. Next checks: generate
the new triangle demo and run a broader multi-seed triangle gate before
promotion/tagging.

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

Current high-yaw-only re-acquire diagnostic:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_reacquire_high_yaw_action_selection_eval.yaml `
  -Profile rectangular_key `
  -Episodes 20 `
  -Seeds 906500,907500,908500,909500,910500,911500
```

Result: `112/120`, collision `0/120`, timeout `8/120`.
Reports:

- `results\visual_yaw_low_z_crop_high_high_yaw_120ep_summary.md`
- `results\visual_yaw_low_z_crop_high_high_yaw_failure_analysis.md`
- `results\visual_yaw_low_z_crop_high_reacquire_comparison.md`

This is the current best same-six-seed number, but the gain is only `+1/120`
and one seed regresses, so keep it diagnostic. The remaining `8/8` failures
still finish above `150 deg` yaw error.

Centered high-yaw crop15 diagnostic:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_reacquire_centered_high_yaw_eval.yaml `
  -Profile rectangular_key `
  -Episodes 20 `
  -Seeds 908500,911500
```

Result: `37/40`, collision `0/40`, timeout `3/40`.
Direct singleton probes rescued `911513`, but the batched `911500` sequence
regressed relative to the high-yaw-only control `38/40`, so do not promote.
Keep this branch diagnostic-only; it confirms that the residual issue is
state-specific reapply / target-retention coverage, not a need to lower the
global crop gate.

Centered high-yaw local reapply latch candidate:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_reapply_eval.yaml `
  -Profile rectangular_key `
  -Episodes 20 `
  -Seeds 908500,911500 `
  -ResultDir results\vy_low_z_crop_high_centered_high_yaw_reapply_seed908500_911500_40ep
```

This candidate keeps the global crop gate at `16.0`, uses local
`crop_std>=15.0` only after a near-centered high-yaw evidence trigger, latches
reapply for `80` steps, preserves the IK target on trigger, and keeps
re-acquire-local descent disabled. Focused result: singleton `911513` succeeds
with final yaw error `0.59 deg`; same-seed gate `908500,911500` is `38/40`,
collision `0/40`, timeout `2/40`, matching high-yaw-only and avoiding the
crop15 regression. Full six-seed result: `112/120`, collision `0/120`, timeout
`8/120`. It rescues the `911513` latch case but does not beat high-yaw-only,
because it fixes `908503` and `911513` while adding `910512` and `911517`. Keep
it diagnostic-only for now.

Centered high-yaw target-reset reapply diagnostic:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_reapply_reset_eval.yaml `
  -Profile rectangular_key `
  -Episodes 20 `
  -Seeds 906500,907500,908500,909500,910500,911500 `
  -ResultDir results\vy_low_z_crop_high_centered_high_yaw_reapply_reset_seed906500_911500_120ep
```

Result: `110/120`, collision `0/120`, timeout `10/120`. This confirms target
reset fixes some isolated regressions but does not improve the full gate. Keep
diagnostic-only. Report:
`results\visual_yaw_low_z_crop_high_centered_reapply_reset_diagnostic.md`.

Centered high-yaw local hold diagnostic:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_local_hold_eval.yaml `
  -Profile rectangular_key `
  -Episodes 20 `
  -Seeds 908500,911500 `
  -ResultDir results\vy_low_z_crop_high_centered_high_yaw_local_hold_seed908500_911500_40ep

.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_local_hold_eval.yaml `
  -Profile rectangular_key `
  -Episodes 20 `
  -Seeds 906500,907500,908500,909500,910500,911500 `
  -ResultDir results\vy_low_z_crop_high_centered_high_yaw_local_hold_seed906500_911500_120ep
```

Focused result: `39/40`, collision `0/40`, timeout `1/40`; local hold fired on
`908503` and `911513`. Full result: `111/120`, collision `1/120`, timeout
`8/120`. The mechanism is useful evidence, but it is not promotable because it
does not beat high-yaw-only and introduces one collision in the full gate.
Report: `results\visual_yaw_low_z_crop_high_centered_local_hold_diagnostic.md`.

Centered local hold plus stronger large-XY/low-Z brake diagnostic:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_local_hold_stronger_brake_eval.yaml `
  -Profile rectangular_key `
  -Episodes 20 `
  -Seeds 906500,907500,908500,909500,910500,911500 `
  -ResultDir results\vy_low_z_crop_high_centered_high_yaw_local_hold_stronger_brake_seed906500_911500_120ep
```

Full result: `112/120`, collision `0/120`, timeout `8/120`. Seed split:
`906500 18/20`, `907500 20/20`, `908500 20/20`, `909500 18/20`,
`910500 18/20`, `911500 18/20`. This ties the historical high-yaw-only
headline while removing the two collisions seen in the current-code high-yaw-only
rerun (`109/120`, collision `2/120`, timeout `9/120`). Treat it as the safer
current-code candidate, not as a real success-rate improvement. Reports:

- `results\visual_yaw_low_z_crop_high_centered_local_hold_stronger_brake_diagnostic.md`
- `results\visual_yaw_low_z_crop_high_centered_local_hold_stronger_brake_failure_analysis.md`
- `results\visual_yaw_low_z_crop_high_high_yaw_current_rerun_diagnostic.md`
- `results\visual_yaw_low_z_crop_high_high_yaw_current_failure_analysis.md`

Approach-adapter extension diagnostics:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_local_hold_stronger_brake_adapter_long_eval.yaml `
  -Profile rectangular_key `
  -Episodes 1 `
  -Seeds 906508,906510,909502,909513,910512,910513,911504,911517 `
  -ResultDir results\vy_low_z_crop_high_centered_high_yaw_local_hold_stronger_brake_adapter_long_known_failures_8ep

.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_centered_local_hold_stronger_brake_adapter_longer_eval.yaml `
  -Profile rectangular_key `
  -Episodes 1 `
  -Seeds 906508,909513,910513,911504 `
  -ResultDir results\vy_low_z_crop_high_centered_high_yaw_local_hold_stronger_brake_adapter_longer_remaining_failures_4ep
```

`adapter_long` raises the approach adapter latch cap to `420` and the per-episode
budget to `700`; targeted known-failure result is `2/8`, collision `0/8`,
timeout `6/8`, rescuing `906510` and `910512`. `adapter_longer` raises the cap
again to `700` and episode budget to `900`; remaining-failure probe is `0/4`.
Do not promote either. They show that adapter duration helps a narrow subset,
but the hard failures remain high-Z/far-XY approach misses or far-XY yaw-basin
timeouts. Reports:

- `results\visual_yaw_low_z_crop_high_adapter_long_known_failures_diagnostic.md`
- `results\visual_yaw_low_z_crop_high_adapter_long_known_failures_analysis.md`
- `results\visual_yaw_low_z_crop_high_adapter_longer_remaining_failures_diagnostic.md`
- `results\visual_yaw_low_z_crop_high_adapter_longer_remaining_failures_analysis.md`

Keep these variants diagnostic-only:

- wrong-basin hold
- wrong-basin re-acquire
- low-Z lateral-pop recovery
- high-yaw-only action selection
- late-finish / XY-freeze variants

## Recommended Next Loop

1. Use the stronger-brake local-hold config as the current-code safety reference
   because it preserves `112/120` and removes current rerun collisions.
2. Treat z190 as diagnostic, not promoted. Its best success-rate run reached
   `117/120`, but still had a rectangular-key collision. Follow-up variants
   (`key_safety1`, `pop_safety1`, `lowz2`, `early_pop1`, `hold_brake1`,
   `no_reacq_descent1`) did not beat the zero-collision reference.
3. Do not keep widening low-Z brakes or pop recoveries. The repeated failure
   pattern is now clearer: `909506` reaches low altitude from `align_hover`
   while XY/yaw are still unsafe, so the large-XY/low-Z brake reacts too late.
4. Next controller work should target `align_hover` directly: before the
   low-Z window, cap downward motion and lateral motion for rectangular-key
   when XY is still large or visual yaw confidence is unreliable.
5. Treat pure adapter-duration increases as rejected after the `2/8` and `0/4`
   targeted probes. If approach remains a bottleneck later, train a better
   approach adapter rather than extending latch duration again.
6. Keep square visual yaw disabled until its false `~45 deg` runtime
   corrections are understood.

## 2026-06-25 z190 Diagnostic Outcome

The z190 line was checked as a possible improvement over the zero-collision
reference:

- `z190`: `117/120`, collision `1/120`, timeout `2/120`; not safe enough.
- `z190_pop_safety1`: `18/20` on `909500`, collision `0`, timeout `2`;
  safer than z190 on the targeted bucket but no success gain.
- `z190_pop_safety1_lowz2`: repeated `909500/20ep` deterministic checks were
  `18/20`, collision `2`; full `120ep` also had a `909506` collision.
- `z190_pop_safety1_early_pop1`: `18/20`, collision `1`, timeout `1`;
  allowing lateral-pop recovery to interrupt re-acquire destabilized `909502`.
- `z190_pop_safety1_hold_brake1`: `18/20`, collision `1`, timeout `1`;
  persistent low-Z brake still reacts too late for `909506`.
- `z190_pop_safety1_no_reacq_descent1`: `18/20`, collision `1`, timeout `1`;
  the early collision path is not primarily re-acquire descent.

Use these results as rejection evidence. The current safe baseline is still the
stronger-brake local-hold config, not z190.

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

Eval-backed visual-yaw demo:

```powershell
.\scripts\sim2real\demo_multigeom_v2_visual_yaw_align.ps1 `
  -Profile rectangular_key `
  -Seed 907500 `
  -ResultDir results\sim2real_multigeom_v2_visual_yaw_align_eval_demo
```

This creates a GIF with `overview`, `wrist_cam`, `cam_image`, and
`near_hole_crop`. The 2026-06-28 smoke output at
`results\sim2real_multigeom_v2_visual_yaw_align_eval_demo_smoke` succeeded
`1/1` with final true key yaw error about `0.32 deg`.

Multi-shape alignment demo directory:

`results\sim2real_multigeom_v2_visual_yaw_align_multishape_demo`

Generated successful demos:

- `demo_rectangular_key_seed907500.gif`: visual-yaw estimator active,
  success `1/1`, `427` steps, final yaw error `0.64 deg`, visual-yaw active
  rows `79`.
- `demo_triangle_triangle_seed910500.gif`: visual-yaw estimator active,
  success `1/1`, `432` steps, final yaw error `2.49 deg`, visual-yaw active
  rows `333`.
- `demo_hex_hex_seed907000.gif`: visual-yaw estimator active, success `1/1`,
  `208` steps, final yaw error `5.02 deg`, visual-yaw active rows `14`.
- `demo_square_square_pose_yaw_seed906500.gif`: square v148 pose-yaw align
  path, success `1/1`, `210` steps, final yaw error `0.46 deg`. This is not
  the same visual-yaw estimator route as key/triangle/hex.

Wrist-spin mitigation status:

- The older key demo
  `results\sim2real_multigeom_v2_wrist_reasonable_yaw_pose_init_w09_smoke\rectangular_key_seed907500.trace.csv`
  reached a `wrist_2` span of `153.48 deg` and a maximum yaw error of
  `174.92 deg`, which visually looked like an unnecessary near-full wrist
  rotation.
- The current official key demo uses key-only initial yaw hold, IK continuity
  weights, and a `rectangular_key:20.0 deg` visual correction cap. Its
  `wrist_2` span is `53.11 deg`, maximum yaw error is `57.08 deg`, and final
  yaw is `0.64 deg`.
- Do not enable a hard per-step wrist-target clip as the default. A `6 deg`
  cap was tested and caused rectangular-key timeout behavior. The current
  preferred demo fix is bounded correction plus key-only initial yaw hold.
- Triangle and hex demos are successful visual-yaw demonstrations, but they are
  not yet optimized for real-robot wrist travel. Triangle still shows a large
  `wrist_2` trace span because symmetric shapes can choose equivalent yaw
  representatives. Before real hardware, add equivalent-yaw shortest-path
  target selection and UR5e joint-limit / cable-wrap checks.

2026-06-28 follow-up: a diagnostic shortest-equivalent target switch was added
but is intentionally default-off:

```yaml
guard_visual_yaw_align_shortest_equivalent_target: false
```

The first online greedy version chooses the symmetry-equivalent target with the
smallest estimated wrist motion. It is useful for trace diagnostics, but it is
not safe enough to promote. On the same `triangle_triangle` seed `910500`, the
default-off route succeeds in `436` steps with final yaw `2.32 deg`, while
turning shortest-equivalent on collided at step `148` and increased `wrist_2`
span to `460.89 deg`. Keep it off for official demos. The next version should
be a gated offline candidate selector that rejects candidates with large XY/Z
drift, poor IK target error, joint-limit margin, or contact-risk indicators
before comparing wrist travel.

2026-06-28 wrist trace diagnostic:

```powershell
python scripts\analyze_wrist_trace.py `
  --output-dir results\sim2real_multigeom_v2_wrist_trace_diagnostics_20260628
```

Report:
`results\sim2real_multigeom_v2_wrist_trace_diagnostics_20260628\wrist_trace_summary.md`.
The diagnostic compares the official key/triangle/hex/square demos with the
older key trace and triangle shortest-equivalent/temporal-smoothing probes.
Main findings:

- Current key demo `wrist_2` unwrapped span is `53.11 deg`, improved from the
  older key trace `153.48 deg`.
- Current triangle demo still has `wrist_2` unwrapped span `322.94 deg` and
  cumulative motion `443.54 deg`. The trace has zero wrap-like qpos jumps, so
  this is not just a `+/-180 deg` display artifact in the GIF.
- Current hex demo `wrist_2` unwrapped span is `137.23 deg`.
- Greedy shortest-equivalent remains rejected: triangle collided and increased
  `wrist_2` span to `460.89 deg`.
- Temporal equivalent smoothing makes correction targets more continuous but
  does not materially reduce triangle `wrist_2` qpos travel. The next fix
  should address IK branch / joint-objective behavior and real UR5e wrist-wrap
  limits, not only scalar yaw-correction smoothing.

Important caveat: enabling the current visual-yaw estimator route directly on
`square_square` caused failures in the seed scan, so square remains on the
v148 square pose-yaw route for now. `slot_slot` is not covered by the current
visual-yaw estimator checkpoint and needs a slot-inclusive yaw dataset/model
before it can have a comparable visual-yaw alignment demo.

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

Low-Z high-yaw-only re-acquire diagnostic:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_reacquire_high_yaw_action_selection_eval.yaml `
  -Profile rectangular_key `
  -Episodes 20 `
  -Seeds 906500,907500,908500,909500,910500,911500 `
  -ResultDir results\vy_low_z_crop_high_high_yaw_seed906500_911500_120ep
```

Tight-yaw smoke:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 -Profile rectangular_key -Episodes 5 -Seeds 906500
```

## 2026-06-29 Triangle Wrist Protocol

The previous successful triangle demo inserted, but `wrist_2` made a real
near-full turn: raw/unwrapped span `322.93 deg`, cumulative motion
`443.54 deg`, with zero wrap-like qpos jumps. This is not acceptable as a
real-robot motion plan even though the GIF succeeds.

Implemented a triangle-only protocol in the eval/demo wrappers:

- wrist-limited equivalent yaw target selection, scoped to `triangle_triangle`
- relaxed visual raw-norm gate only for triangle
- hold-XY and hold-target phases while yaw is being resolved
- freeze the current peg-tip orientation once visual yaw is stably small
- recenter in XY with descent blocked, then descend only after XY is close

Run:

```powershell
.\scripts\sim2real\demo_multigeom_v2_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_multishape_eval_demo.yaml `
  -Profile triangle_triangle `
  -Seed 910500 `
  -ResultDir results\sim2real_multigeom_v2_triangle_wrist_protocol_demo
```

Current result:

- Triangle demo seed `910500`: success `1/1`, collision `0`, timeout `0`,
  `250` trace rows, final yaw `2.16 deg`.
- `wrist_2` span improved from `322.93 deg` to `144.97 deg`.
- The trace shows `freeze_aligned_target_recenter_*` followed by
  `freeze_aligned_target_descent_*`, so the behavior is now visually:
  rotate/align, recenter, then insert.
- Wrapper rechecks kept non-triangle shapes on their default paths:
  `hex_hex` seed `907000` success `1/1`, final yaw `5.02 deg`;
  `rectangular_key` seed `907500` success `1/1`, final yaw `0.60 deg`.

The protocol is not a universal replacement. Earlier attempts to apply the
same full protocol globally caused hex timeout/collision and key collision.
Keep this path scoped to `triangle_triangle` until a broader wrist-aware IK
selector is implemented and validated across all shapes.

## 2026-06-29 Wrist-Gate Follow-Up

Added default-off wrist-aware diagnostics:

- `guard_visual_yaw_align_equivalent_wrist_target_jump_deg` trace field
- wrist-limited equivalent-target gates for max wrist delta, target jump,
  minimum improvement, and max equivalent correction
- `guard_visual_yaw_align_target_jump_gate_*` runtime gate

Smoke results:

- Default behavior after the code change remained successful:
  triangle seed `910500` success, final yaw `0.63 deg`; hex seed `907000`
  success, final yaw `4.41 deg`; rectangular-key seed `907500` success,
  final yaw `0.43 deg`.
- Wrist-limited selector without the triangle freeze/recenter protocol timed
  out on triangle seed `910500`; final XY was about `0.14 m` and yaw about
  `53.1 deg`.
- Extra wrist-limited gates inside the triangle protocol preserved success but
  worsened cumulative wrist/target motion and final yaw.
- Target-jump gate at `80 deg` preserved success and lowered max target jump,
  but increased qpos span/cumulative motion and worsened final yaw.
- Correction-slew diagnostics were also rejected. `slew20` preserved success
  but worsened final yaw (`6.11 deg`), cumulative `wrist_2` motion
  (`440.86 deg`), and target cumulative motion (`1166.40 deg`). `slew40`
  collided with final yaw `40.56 deg` and much larger wrist/target motion.

Decision: keep these controls as diagnostics only. They should not be enabled
in the official demo/config yet. The better next direction is a smoother target
generation or latch strategy that avoids oscillatory visual-yaw targets before
they become large jumps, instead of rejecting jumps after they appear.

## 2026-06-29 Target-Latch Diagnostic

Added a default-off visual-yaw target-latch diagnostic:

```powershell
--guard-visual-yaw-align-target-latch-enabled
--guard-visual-yaw-align-target-latch-profiles triangle_triangle
--guard-visual-yaw-align-target-latch-steps 60
--guard-visual-yaw-align-target-latch-arm-yaw-deg 65
--guard-visual-yaw-align-target-latch-release-yaw-deg 75
--guard-visual-yaw-align-target-latch-stable-window 2
--guard-visual-yaw-align-target-latch-max-delta-deg 45
```

This latch stores a recent visual-yaw IK target and reuses it briefly instead
of recomputing a new equivalent yaw target every frame. It is intentionally
off by default.

Result on `triangle_triangle`, seed `910500`:

- default-off recheck: success `1/1`, final yaw `3.95 deg`
- relaxed target-latch diagnostic: timeout, final XY `0.00016 m`, final yaw
  `30.34 deg`
- target-latch active rows: `915/1000`
- `wrist_2` cumulative motion dropped from `390.87 deg` to `290.83 deg`, but
  the robot froze a wrong yaw basin and never inserted

Decision: do not promote target latch. It proves that freezing a target can
reduce wrist motion, but it can also freeze an incorrect visual-yaw estimate.
The next useful direction is not a longer/stronger latch; it is confidence-aware
target generation that can continue correcting yaw while limiting jumps.

Stable-apply gate follow-up using the existing temporal action gate was also
rejected:

```powershell
--guard-visual-yaw-align-temporal-action-gate-enabled
--guard-visual-yaw-align-temporal-action-gate-profiles triangle_triangle
--guard-visual-yaw-align-temporal-action-gate-window 3
--guard-visual-yaw-align-temporal-action-gate-max-delta-deg 12
--guard-visual-yaw-align-temporal-action-gate-min-pred-yaw-deg 15
--guard-visual-yaw-align-temporal-action-gate-reset-target
--guard-visual-yaw-align-temporal-action-gate-block-descent
```

On the same triangle seed this timed out with final yaw `55.37 deg`. The gate
filtered early target updates too aggressively; once the peg descended below
the visual-yaw Z gate, the remaining yaw error could not be corrected. Keep the
temporal action gate diagnostic-only for triangle.

Target-jump soft-limit diagnostic was also rejected. A temporary controller
that scaled down the visual-yaw correction when the resulting wrist target jump
exceeded `80 deg` succeeded in the first triangle smoke, but final yaw worsened
to `8.80 deg`, `wrist_2` span rose to `173.71 deg`, cumulative `wrist_2`
motion rose to `498.99 deg`, and target jumps still reached `119.35 deg`.
Absolute-correction follow-ups collided and pushed the wrist farther from the
intended range. The soft-limit implementation has been removed from
`scripts\eval_guarded_policy.py`; do not re-add scalar target-jump shrinkage as
the next step. The next useful direction is confidence-aware target generation,
better triangle/hex yaw-estimator data under the exact wrist camera view, and
candidate target scoring against IK/wrist/contact risk before applying it.

2026-06-29 follow-up caveat: the triangle wrist-protocol demo is not yet a
stable evaluation result. With the same seed/config, the demo path can still
produce a successful GIF while the non-demo eval path collides. The traces show
the controller is on a numerical/visual-confidence boundary, not a clean policy
margin: in the failing eval path, freeze-aligned-target can arm while the true
shape yaw is still about `30 deg` because the visual estimator reports only
`1-3 deg` residual yaw at low `raw_norm` around `0.08`. Raising the freeze
raw-norm threshold avoids that collision in the tested seed, but turns into a
timeout around `32 deg` yaw because the view never regains reliable evidence.
Treat this as the active blocker for triangle: do not use the GIF alone as
proof of robust align-then-insert. The next controller needs a confidence-aware
re-acquire / target-generation phase, not another scalar post-hoc gate.

## 2026-06-29 High-Confidence Triangle Freeze13 Diagnostic

Follow-up experiments changed the diagnosis. Low-confidence re-acquire was
implemented as a default-off diagnostic and did prevent the hard collision on
`triangle_triangle`, seed `910500`, but it timed out. With `min-step=700` it
triggered too late; with `min-step=300` it repeatedly lifted/recentered and
spent the insertion budget.

Trace review showed the better promotion path: the current yaw estimator is
biased on triangle near insertion. Good true alignment often appears as
`11-13 deg` predicted residual with high `raw_norm`, while the dangerous false
alignment appears as `1-3 deg` with low `raw_norm`. A diagnostic run used:

```text
--guard-visual-yaw-align-min-raw-norm 0.12
--guard-visual-yaw-align-freeze-aligned-target-yaw-deg 13.0
--guard-visual-yaw-align-freeze-aligned-target-required-steps 3
```

Single-seed result:

- `triangle_triangle`, seed `910500`: success, `156` steps, final yaw
  `0.71 deg`, zero collision/timeout.

The follow-up six-seed matrix rejected promotion:

- `triangle_triangle`: `1/6`, zero collision, five timeouts.
- `hex_hex`: `3/6`, one collision, two timeouts.
- `rectangular_key`: `1/6`, zero collision, five timeouts.

Current guidance: do not promote freeze13 into the wrapper. The wrapper remains
on the previous triangle protocol. Keep both low-confidence re-acquire and
freeze13 as diagnostic tools until per-shape yaw estimation/target generation
is improved and validated on multiple seeds.

## 2026-06-29 Multishape Eval Entry Fix And Triangle XY Drift

The visual-yaw eval entry was corrected. The old
`multigeom_v2_true_fixture_tight_yaw_visual_yaw_align_eval.yaml` is
rectangular-key-only, so triangle/hex evaluations could silently report
`visual_yaw_align_steps=0`. Added:

- `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_multishape_eval.yaml`
- `scripts\analyze_visual_yaw_trace_summary.py`

Both visual-yaw eval wrappers now default to the multishape config, while the
demo wrapper already uses the multishape demo config. The new trace summary
script accepts individual traces, directories, or wildcard patterns and reports
whether visual yaw was actually active/applied.

Correct-entry smoke results:

- `triangle_triangle`, seed `910500`: success, final yaw `1.62 deg`,
  visual/applied `202/38`.
- `hex_hex`, seed `907000`: success, final yaw `5.02 deg`,
  visual/applied `14/14`.
- `rectangular_key`, seed `907500`: success, final yaw `0.47 deg`,
  visual/applied `78/78`.

Combined trace report:
`results\sim2real_multigeom_v2_multishape_eval_entry_smoke_summary\visual_yaw_trace_summary.md`.

The corrected six-seed triangle eval rejected promotion:

- `triangle_triangle`, seeds `906500/907500/908500/909500/910500/911500`:
  `1/6` success, `4/6` collision, `1/6` timeout.
- All six episodes had visual-yaw active and applied.
- Failures are not simply "visual yaw did not run." They are mostly post-yaw
  XY drift / premature descent failures: collision seeds often finish with
  final XY around `20-34 mm` while already below the hole plane.
- The first freeze-descent handoff often happens around `19-20 mm` XY and
  `64-95 mm` Z, so the risky state begins before low-Z collision.

Rejected follow-ups:

- strict freeze/hold XY gate (`descent_xy=6 mm`, `release_xy=12 mm`) turned
  the first two seeds into timeouts and still collided on the third. It blocks
  descent but does not create a strong enough recenter/re-approach path.
- low-Z `descent_abort` with lift/recenter triggered, but mostly at or below
  the hole plane and failed `0/3` (`1` timeout, `2` collisions). It is too late
  for this failure mode as configured.

Current diagnosis: triangle needs a stateful "after visual yaw, reset XY /
re-approach before descent" controller. The next useful change is not another
yaw threshold. It should explicitly hold the aligned yaw target, lift or stay
high enough, re-center XY to a tight band, then release descent only after
both visual yaw and XY are stable. Validate with the new trace summary first,
then only generate demos after a multi-seed eval is stable.

## 2026-06-30 Post-Yaw Reapproach Follow-Up

Post-yaw reapproach was implemented as a default-off diagnostic in
`scripts\eval_guarded_policy.py`, and the trace summary now reports
`post active:descent:release` counts.

The important finding is that triangle failures are not solved by merely
returning XY to the hole center. In the tested seeds, the controller can bring
XY near `5-6 mm`, but the visual-yaw estimate can remain biased or noisy while
the freeze-aligned descent chain later drives into a wrong yaw basin or low-Z
lateral pop.

Rejected diagnostics:

- `release-to-visual-realign` after recenter (`8 mm` XY, `55 mm` Z) produced
  `0/3` on seeds `906500/907500/908500`.
- `block-background-targets` during post-yaw reapproach also produced
  deterministic `0/3`.

Keep both switches default-off. The current triangle success path still relies
on the freeze/hold target chain; cutting it off is too destructive. The next
useful controller change should refine freeze descent itself: continue visual
yaw confidence checks during the frozen descent and slow or hold descent when
the prediction/confidence pattern looks like a wrong basin.

## 2026-06-30 Freeze-Descent Visual-Safety Gate

Implemented a default-off conservative gate for the next triangle diagnostic:

```powershell
--guard-visual-yaw-align-freeze-descent-visual-safety-enabled
--guard-visual-yaw-align-freeze-descent-visual-safety-profiles triangle_triangle
--guard-visual-yaw-align-freeze-descent-visual-safety-low-conf-max-raw-norm 0.12
--guard-visual-yaw-align-freeze-descent-visual-safety-low-conf-max-pred-yaw-deg 8.0
--guard-visual-yaw-align-freeze-descent-visual-safety-large-pred-yaw-deg 14.0
--guard-visual-yaw-align-freeze-descent-visual-safety-max-down-action 0.001
```

It only runs during `freeze_aligned_target_descent_*`. It keeps the frozen IK
target intact, continues XY hold/recenter, and only reduces the downward action
when visual evidence looks risky. This is intentionally less destructive than
`release-to-visual-realign` or `block-background-targets`, both of which were
rejected by deterministic smoke tests.

Validation order:

1. Run deterministic `906500/907500/908500` triangle smoke with post-yaw
   reapproach plus this gate.
2. Summarize with `scripts\analyze_visual_yaw_trace_summary.py`; require the
   new `freeze_descent_visual_safety` counts to explain any outcome change.
3. Only expand to the six-seed corrected triangle matrix if the 3-seed smoke
   beats or at least preserves the unstable `1/3` baseline without increasing
   collisions.

Validation result:

- Default thresholds reached `2/3`; `908500` still collided because safety
  fired only once.
- Relaxed thresholds (`raw<=0.155`, `pred<=11 deg`) with slow descent also
  reached `2/3`; `908500` fired safety for `74` rows but still collided.
- Relaxed thresholds with full Z block reached `2/3` and changed `908500` from
  collision to timeout. This is the safer diagnostic setting, but not a
  solution.
- `--guard-visual-yaw-align-freeze-descent-visual-safety-release-freeze`
  regressed to `1/3`: it broke `906500` and did not rescue `908500`. Keep it
  default-off and rejected unless a later target-generation change justifies
  retesting it.

Interpretation: this gate can reduce collision risk, but it does not recover a
wrong triangle yaw basin. The next controller or learning step should improve
triangle visual-yaw estimation/target generation at high Z, or add a deliberate
visual re-acquire phase before resuming descent.

## 2026-06-30 Rollout Distribution Mismatch

A triangle/hex wrong-basin visual-yaw estimator was trained on a focused
mid/high-Z dataset:

- Dataset: `datasets\visual_yaw_v1_tight_yaw_triangle_hex_wrong_basin_8k.npz`
- Checkpoint:
  `results\visual_yaw_estimator_v1_tight_yaw_triangle_hex_wrong_basin_8k.pt`
- Offline validation: overall mean/p95 `1.60/5.53 deg`, triangle
  `1.13/2.87 deg`, hex `1.19/3.24 deg`.

Despite the strong offline numbers, online triangle insertion did not improve.
The same critical seeds `906500/907500/908500` remained `0/3`, and a
NoTriangleWristProtocol plus wrist-limited/holdXY-only ablation also stayed
`0/3`.

To check whether this was control tuning or a vision distribution issue,
`scripts\eval_guarded_policy.py` now has a default-off rollout visual-yaw
snapshot path:

```powershell
--visual-yaw-rollout-dataset-output <file.npz>
--visual-yaw-rollout-dataset-csv <file.csv>
--visual-yaw-rollout-dataset-md <file.md>
--visual-yaw-rollout-dataset-outcome-filter failure
--visual-yaw-rollout-dataset-stride 2
```

The diagnostic run on `triangle_triangle`, seed `908500`, produced:

- NPZ: `datasets\visual_yaw_rollout_triangle_908500_wrist_holdxy_stride2.npz`
- CSV/MD:
  `results\visual_yaw_rollout_triangle_908500_wrist_holdxy_stride2.csv/.md`
- `500` failure rollout samples.
- Mean prediction-vs-label yaw error: `36.81 deg`.
- `193` samples where true yaw is `>=30 deg` but predicted yaw is `<=8 deg`.

Conclusion: the current visual-yaw estimator is not failing because the held-out
static dataset is too small; it is failing because the closed-loop rollout
images are off-distribution. The next robust step is failure-rollout data
augmentation/retraining, then re-running the same triangle three-seed online
test. Do not promote the triangle/hex wrong-basin estimator or tune more
freeze/descent constants until that online vision mismatch is addressed.

## 2026-06-30 Rollout-Augmented Triangle/Hex Regression

Merged rollout failure snapshots from triangle seeds `906500`, `907500`, and
`908500` with the static triangle/hex wrong-basin dataset:

- Static dataset:
  `datasets\visual_yaw_v1_tight_yaw_triangle_hex_wrong_basin_8k.npz`
- Rollout datasets:
  `datasets\visual_yaw_rollout_triangle_906500_rollout_aug_failure_stride2.npz`,
  `datasets\visual_yaw_rollout_triangle_907500_rollout_aug_failure_stride2.npz`,
  and `datasets\visual_yaw_rollout_triangle_908500_wrist_holdxy_stride2.npz`
- Merged dataset:
  `datasets\visual_yaw_v1_tight_yaw_triangle_hex_wrong_basin_8k_plus_rollout906500_907500_908500_balanced.npz`
- Checkpoint:
  `results\visual_yaw_estimator_v1_tight_yaw_triangle_hex_wrong_basin_8k_plus_rollout_balanced.pt`

Offline validation is strong overall: mean `1.219 deg`, p95 `3.686 deg`, bad
fraction `0.005`. Per-profile validation is also good on triangle/hex:
`triangle_triangle` mean/p95 `0.775/2.366 deg`, `hex_hex` `1.258/3.270 deg`.

The first online result exposed a wrapper issue. The triangle protocol injected
relaxed yaw thresholds (`freeze_aligned_target_yaw_deg=8`,
`freeze_aligned_target_release_yaw_deg=65`) and overrode stricter YAML
settings. Added `-NoTriangleProtocolYawOverrides` to both eval wrappers. With
that switch and the strict-yaw low-Z-abort config, the focused three-seed check
reached `3/3` on triangle:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Profile triangle_triangle `
  -Episodes 1 `
  -Seeds 906500,907500,908500 `
  -Config configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_hex_rollout_balanced_low_z_abort_strict_yaw_eval.yaml `
  -ResultDir results\sim2real_multigeom_v2_triangle_hex_rollout_balanced_low_z_abort_strict_yaw_no_override_triangle_3seed `
  -NoTriangleProtocolYawOverrides
```

Expanded validation rejected promotion:

- Triangle, strict-yaw low-Z-abort, no wrapper yaw overrides:
  `25/30`, collision `5/30`, timeout `0/30`.
- The five failures are all low-Z collisions, not timeouts. Trace review shows
  the controller can descend while true yaw is still about `18-22 deg`; the
  estimator reports only `1-3 deg`, then the prediction disappears under the
  z gate and the final steps collide.
- More aggressive low-Z abort v2 was worse on the focused fail-seed gate:
  `10/20`, collision `1/20`, timeout `9/20`.
- Narrow low-Z gate was safer but not better: `15/20`, collision `1/20`,
  timeout `4/20`. It mostly converts collisions into timeouts.
- Hex must not use the triangle strict-yaw config as a shared multishape
  default. On `hex_hex` six seeds x five episodes, that config reached only
  `14/30`, collision `2/30`, timeout `14/30`.

Current decision:

- Do not promote the rollout-balanced triangle/hex estimator stack yet.
- Keep `-NoTriangleProtocolYawOverrides` available and use it when a config
  intentionally sets strict triangle yaw thresholds.
- Keep the new low-Z gate and low-Z abort v2 strict configs as diagnostic-only:
  they are useful safety evidence but do not improve headline success.
- Split per-shape runtime configs. Triangle needs a controller/vision fix for
  low-Z false-small-yaw predictions; hex should keep its own thresholds rather
  than inheriting triangle strict descent settings.

Next technical step:

1. Add a trace-based false-small-yaw detector or training label for the low-Z
   triangle basin where true yaw is large but predicted yaw is small.
2. Prefer improving yaw target generation / estimator coverage over adding more
   lift-recenter attempts, because repeated aborts are already shown to trade
   collisions for timeouts.
3. Re-run triangle on at least `6x5` episodes and hex on a separate hex-safe
   config before any tag or promotion.

## 2026-06-30 False-Small-Yaw Trace Diagnostic

Added `scripts\analyze_visual_yaw_false_small.py` and ran it on the strict
triangle `6x5` regression:

```powershell
python scripts\analyze_visual_yaw_false_small.py `
  results\sim2real_multigeom_v2_rollout_balanced_strict_no_override_triangle_6seed_5ep `
  --output-dir results\sim2real_multigeom_v2_rollout_balanced_strict_no_override_triangle_6seed_5ep\false_small_analysis `
  --scope-profile triangle_triangle
```

Key outputs:

- `visual_yaw_false_small_analysis.md`
- `visual_yaw_false_small_episodes.csv`
- `visual_yaw_false_small_events.csv`
- `visual_yaw_false_small_gates.csv`
- `visual_yaw_observable_proxy_gates.csv`
- `visual_yaw_observable_proxy_episodes.csv`

The simulator-truth diagnostic confirms the failure mechanism:

- false-small condition: predicted yaw `<=4 deg`, true yaw `>=12 deg`
- false-small rows: `743`
- failed episodes hit: `5/5`
- success episodes: only `4` false-small rows
- `freeze_low_z_near_xy_false_small` hits `5/5` failed and `0/25` success

But the deployable proxy check rejects a simple runtime gate. Without using
sim-truth yaw, `freeze_low_z_near_xy_pred_small` hits all `30/30` episodes:

- failed rows: `254`
- success rows: `1104`
- success episodes hit: `25/25`
- failure max-run: only `4-5`, while success max-run reaches `22`
- mean raw norm is almost identical for success and collision (`0.1775` vs
  `0.1768`)

Decision: do not add a control gate based only on small predicted yaw, frozen
descent, low Z, and near XY. It would block normal successful insertion. The
truth-only false-small pattern is real, but it is not observable with the
current trace fields without also knowing the true yaw. Next work should improve
the visual yaw estimator/data distribution for low-Z occluded rollout states,
not add another descent blocker.

## 2026-06-30 Strict-Failseed v2 And Per-Profile Routing

Collected five strict triangle low-Z collision failseeds as rollout visual-yaw
datasets:

- `906501`
- `907502`
- `910503`
- `910504`
- `911501`

Merged them with
`datasets\visual_yaw_v1_tight_yaw_triangle_hex_wrong_basin_8k_plus_rollout906500_907500_908500_balanced.npz`
to create:

- `datasets\visual_yaw_v1_tight_yaw_triangle_hex_wrong_basin_8k_plus_rollout_balanced_plus_strict_failseeds_v2.npz`
- `results\visual_yaw_estimator_v1_tight_yaw_triangle_hex_wrong_basin_8k_plus_rollout_balanced_plus_strict_failseeds_v2.pt`

Offline validation for v2 is good but not clearly better globally:

- overall mean/p95/bad fraction: `1.075 / 3.816 / 0.004`
- triangle mean/p95: `0.749 / 2.510 deg`
- hex mean/p95: `1.585 / 4.194 deg`

Online results are shape-dependent:

- Triangle strict failseed smoke: `5/5`, converting all five previous
  collision failseeds to success.
- Triangle six seeds x five episodes with strict low-Z abort:
  `29/30`, collision `0/30`, timeout `1/30`.
- Hex with the same shared v2 checkpoint:
  `1/30`, collision `18/30`, timeout `11/30`.

Decision: v2 is a triangle-only candidate. It must not replace the shared
triangle/hex estimator.

Implemented profile-specific visual-yaw checkpoint routing in
`scripts\eval_guarded_policy.py`:

```powershell
--guard-visual-yaw-align-profile-models `
  triangle_triangle:results/visual_yaw_estimator_v1_tight_yaw_triangle_hex_wrong_basin_8k_plus_rollout_balanced_plus_strict_failseeds_v2.pt
```

The runtime now uses the profile-specific checkpoint when one is configured and
falls back to `--guard-visual-yaw-align-model` for other profiles. New configs:

- `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_strict_failseeds_v2_eval.yaml`
- `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_hex_per_profile_v2_eval.yaml`

Validation:

- Triangle-only strict config smoke on `906501`: `1/1`, visual active/applied,
  final yaw `0.80 deg`.
- Per-profile hex fallback config on six seeds x five episodes:
  `14/30`, collision `2/30`, timeout `14/30`, visual active/applied in
  `26/30`.

Interpretation: per-profile routing prevents the shared v2 checkpoint from
destroying hex performance, but hex is still weak. The next useful path is a
hex-specific rollout dataset and hex-specific visual-yaw estimator, then route
triangle to v2 and hex to the hex-only checkpoint.

## 2026-06-30 Hex Failure-Rollout v1

Collected hex failure rollout visual-yaw datasets from the per-profile fallback
hex regression. The collection covered `16` failed episodes; `908503` had no
valid visual-yaw predictions and was left out of the first merged training set.
Most usable failure rollouts showed mean prediction-vs-label yaw error around
`12-22 deg`, confirming that hex failures are also a closed-loop distribution
shift, not merely a controller threshold issue.

Merged dataset:

- `datasets\visual_yaw_v1_tight_yaw_triangle_hex_wrong_basin_8k_plus_rollout_balanced_plus_hex_failures_v1.npz`
- output samples: `27059`

Trained checkpoint:

- `results\visual_yaw_estimator_v1_tight_yaw_triangle_hex_wrong_basin_8k_plus_rollout_balanced_plus_hex_failures_v1.pt`

Offline validation:

- overall mean/p95/bad fraction: `0.691 / 2.481 / 0.002`
- `hex_hex` mean/p95/bad fraction: `0.460 / 1.378 / 0.003`
- `triangle_triangle` mean/p95: `0.647 / 2.134 deg`

Online hex result with
`configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_v2_hex_failures_v1_eval.yaml`:

- `hex_hex`, six seeds x five episodes: `29/30`, collision `0/30`,
  timeout `1/30`
- the only timeout is `908503`, which was already the visual-inactive outlier
  in the failure-rollout collection.

Triangle compatibility check:

- `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_v2_hex_failures_v1_eval.yaml`
  inherited the non-strict triangle yaw release settings and produced
  `29/30` with one collision on `909502`; this is not the desired triangle
  entry.
- `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_strict_v2_hex_failures_v1_eval.yaml`
  restores strict triangle settings but reached `28/30`, collision `0/30`,
  timeout `2/30` (`908503`, `909502`).

Current decision: keep the strongest entries per shape instead of promoting a
single default:

- Triangle: use
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_strict_failseeds_v2_eval.yaml`
  (`29/30`, collision `0`, timeout `1`).
- Hex: use
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_v2_hex_failures_v1_eval.yaml`
  for `hex_hex` (`29/30`, collision `0`, timeout `1`) until the
  early-approach/descent follow-up below is validated.

Next work should target the remaining visual-inactive / high-yaw timeout seeds,
especially triangle `908503` and hex `908503`, before promoting a unified
multishape default.

## 2026-07-01 Hex Early-Approach Descent v1

Hex `908503` was diagnosed as a runtime approach/descent issue, not a
visual-yaw estimator issue.

Baseline trace:

- Config:
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_v2_hex_failures_v1_eval.yaml`
- Result: `29/30`, collision `0/30`, timeout `1/30`
- The only timeout was `908503`.
- For `908503`, visual yaw was never active/applied (`0/0`), final-servo stayed
  inactive for all `1000` rows, closest XY was about `43 mm`, and Z stayed high
  around `0.10-0.22 m`.

First follow-up:

- Config:
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_v2_hex_failures_v1_hex_early_approach_v1_eval.yaml`
- Adds a hex-only high-Z/far-XY early approach assist.
- `908503` then entered final-servo and reached good XY/yaw alignment, but
  still timed out at about `6-8 cm` above the fixture because target-hold/crop
  gates blocked descent after alignment.

Current hex entry:

```powershell
.\scripts\sim2real\eval_multigeom_v2_visual_yaw_align.ps1 `
  -Profile hex_hex `
  -Episodes 5 `
  -Seeds 906500,907500,908500,909500,910500,911500 `
  -Config configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_v2_hex_failures_v1_hex_early_approach_descent_v1_eval.yaml `
  -ResultDir results\sim2real_multigeom_v2_hex_early_approach_descent_v1_hex_6seed_5ep

python scripts\analyze_visual_yaw_trace_summary.py `
  results\sim2real_multigeom_v2_hex_early_approach_descent_v1_hex_6seed_5ep `
  --output-dir results\sim2real_multigeom_v2_hex_early_approach_descent_v1_hex_6seed_5ep\trace_summary
```

Config:

- `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_v2_hex_failures_v1_hex_early_approach_descent_v1_eval.yaml`
- hex-only `guard_visual_yaw_align_profiles: [hex_hex]`
- hex-only route to
  `results\visual_yaw_estimator_v1_tight_yaw_triangle_hex_wrong_basin_8k_plus_rollout_balanced_plus_hex_failures_v1.pt`
- high-Z/far-XY early approach assist
- target-hold descent blocking disabled after alignment
- aligned/near-miss descent slightly strengthened

Result:

- `hex_hex`, six seeds x five episodes: `30/30`
- collision `0/30`
- timeout `0/30`
- trace summary:
  `results\sim2real_multigeom_v2_hex_early_approach_descent_v1_hex_6seed_5ep\trace_summary\visual_yaw_trace_summary.md`

The focused `908503` smoke succeeds in `616` rows, reaches final Z about
`9.3 mm`, final yaw about `0.18 deg`, and has zero collision. This confirms the
fix is "approach into guard zone, then allow aligned descent through crop
dropouts," not new yaw-estimator training.

Updated per-shape recommendation:

- Triangle: keep
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_strict_failseeds_v2_eval.yaml`
  with `-NoTriangleProtocolYawOverrides` (`29/30`, timeout-only).
- Hex: use
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_v2_hex_failures_v1_hex_early_approach_descent_v1_eval.yaml`
  (`30/30`, zero collision/timeout).

Do not promote a unified multishape default yet. Triangle `908503/909502` are
different failures: low-Z visibility/target-maintenance after visual yaw has
already run, not the hex high-Z guard-activation problem.

## 2026-07-01 Triangle Low-Z Pop Recovery v12-v16

Hard smoke used `triangle_triangle`, seed `909500`, 3 episodes, with
`-NoTriangleProtocolYawOverrides`.

Baseline around this failure family:

- v10 pre-pop guard: `2/3`, collision `0`, timeout `1`.
- v11 longer pre-pop hold: `2/3`, collision `0`, timeout `1`.
- v11 failure: episode `909502` is centered near the hole, then jumps from
  about `3.4 mm` to `13 mm` XY near the hole plane. Generic recovery then
  lifts/recenters too broadly and times out.

New diagnostic runtime hook:

- Added default-off
  `guard_visual_yaw_align_pre_pop_near_plane_brake_*` controls and trace
  fields in `scripts\eval_guarded_policy.py`.
- Scope: only active inside visual-yaw pre-pop guard, default off.
- Intended effect: short near-plane Z brake while XY is still small, before
  the lateral pop.

Tested candidates:

- v12 local post-pop recovery:
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_strict_failseeds_v2_low_z_reacquire_v12_local_pop_recovery_eval.yaml`
  -> `2/3`, collision `1`, timeout `0`.
- v13 short near-plane brake:
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_strict_failseeds_v2_low_z_reacquire_v13_pre_pop_near_plane_brake_eval.yaml`
  -> `2/3`, collision `1`, timeout `0`; first gate was too narrow.
- v14 wider zero-XY brake:
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_strict_failseeds_v2_low_z_reacquire_v14_pre_pop_near_plane_zero_xy_brake_eval.yaml`
  -> `2/3`, collision `1`, timeout `0`; brake triggered but did not stop the
  lateral pop.
- v15 sustained stronger brake:
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_strict_failseeds_v2_low_z_reacquire_v15_pre_pop_near_plane_sustained_hold_eval.yaml`
  -> `2/3`, collision `0`, timeout `1`; safer, but still falls into broad
  recovery and times out.
- v16 sustained brake plus local pop recovery:
  `configs\sim2real\multigeom_v2_true_fixture_visual_yaw_align_triangle_strict_failseeds_v2_low_z_reacquire_v16_hold_plus_local_pop_recovery_eval.yaml`
  -> `2/3`, collision `1`, timeout `0`.

Conclusion:

- Do not promote v12-v16.
- Pure action-layer near-plane braking is not enough. The pop happens even
  when commanded XY is zero; the likely cause is contact/tilt/control-lag
  coupling around the hole plane.
- Local post-pop lift can reduce timeout but reintroduces collision risk.
- Best safe behavior in this family remains v11/v15 style: no collision, but
  timeout on the hard episode.

Next useful direction:

- Replace the generic high recover/reacquire after low-Z pop with a bounded
  local recovery state that preserves the final-servo target, caps tilt, and
  releases only after XY is locally stable.
- Alternatively improve the final insertion model/contact tuning for triangle
  near-hole contact before adding more runtime gates.

## 2026-07-02 Triangle Wrist-Safe Absolute Target v3

The previous absolute-shape-target protocol solved the original near-360-degree visual-yaw spinning failure, but the 120 episode gate still had `54/120` episodes with some wrist span above `180 deg`. Trace inspection showed many outliers started from a high-start IK wrist basin far from rest before visual yaw alignment activated.

Implemented v3:

- Absolute shape target candidates are normalized through nearest wrist-equivalent selection before scoring.
- Candidate scoring now heavily penalizes wrist target jump, wrist delta, and distance from rest.
- Added `--guard-visual-yaw-align-absolute-shape-target-max-rest-delta-deg`.
- Added `--initial-shape-yaw-max-wrist-rest-delta-deg` to bias high-start yaw initialization toward wrist-safe equivalent poses.
- Triangle wrapper defaults now use:
  - `--guard-visual-yaw-align-absolute-shape-target-max-abs-deg 160`
  - `--guard-visual-yaw-align-absolute-shape-target-max-delta-deg 95`
  - `--guard-visual-yaw-align-absolute-shape-target-max-target-jump-deg 70`
  - `--guard-visual-yaw-align-absolute-shape-target-max-rest-delta-deg 130`
  - `--ik-nearest-wrist-target-equivalent`
  - `--ik-max-wrist-target-delta-deg 8`
  - `--initial-shape-yaw-max-wrist-rest-delta-deg 130`
  - `--initial-ik-max-attempts 80`

Validation:

- Targeted hard seeds: `906504, 907508, 908510, 910505, 910500, 910501` -> `6/6`, collision `0`, timeout `0`.
- Full 120 episode gate:
  - directory: `results\triangle_wrist_safe_v3_gate_120ep`
  - success: `116/120` (`96.67%`)
  - collision: `0/120`
  - timeout: `4/120`
  - wrist outliers above `180 deg`: `0/120`
  - wrist_1 span mean/median/p95/max: `29.4 / 28.8 / 40.3 / 47.3 deg`
  - wrist_2 span mean/median/p95/max: `114.0 / 115.3 / 125.7 / 129.4 deg`
  - wrist_3 span mean/median/p95/max: `20.4 / 20.5 / 22.7 / 23.2 deg`

Conclusion: v3 should replace the earlier triangle wrist protocol for demos/eval. It is not yet a final all-shape sim-to-real release because timeout is still `4/120`, but the wrist over-rotation failure is now effectively gated out in this 120 episode test.
