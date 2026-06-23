# Sim2Real Multi-Geometry v2 True Fixtures

This is the experimental branch for replacing box-wall scaffold holes with
per-shape convex mesh fixture pieces.

Current scope:

- Implemented true mesh fixture mode for `hex_hex`, `triangle_triangle`,
  `slot_slot`, and `rectangular_key`.
- The v2 collision pieces are convex mitered wall prisms.
- The demo/rendered fixture now uses a separate visual-only ring mesh for
  `hex_hex`, `triangle_triangle`, and `slot_slot`, so visible geometry is not
  the segmented collision decomposition.
- Polygon/key pegs now have visual-only tip helpers so demos show the actual
  peg cross section more clearly: `hex` and `triangle` use tip cap, tip
  outline, and subtle side-edge highlights; `rectangular_key` uses a keyhole
  tip cap and outline. These geoms have `contype=0` and `conaffinity=0`.
- The implementation is opt-in through `geometry_fixture_mode=true_mesh`.
- The default remains `box_wall`, so the stable v1 path is unchanged.
- `slot_slot` also has an opt-in slot peg mesh in `true_mesh` mode.
- `rectangular_key` now has an opt-in keyhole profile in `true_mesh` mode:
  round body plus one protruding tab. The default `box_wall` path still uses
  the old rectangular scaffold.
- `rectangular_key` also has a visual-only dark bottom marker for the keyhole
  opening. It is composed from a non-colliding cylinder plus tab box, so it is
  stable in demos and does not affect contact.
- `triangle_triangle` true fixture is clamped so the triangular hole
  circumdiameter is at most `2x` the peg diameter.
- Size randomization is temporarily fixed while collision scaling is validated.

Analytic yaw-sensitivity scan:

```powershell
python scripts\scan_shape_yaw_sensitivity.py --output-csv results\shape_yaw_sensitivity_scan.csv --output-md results\shape_yaw_sensitivity_scan.md
python scripts\scan_shape_yaw_sensitivity.py --yaw-deg 0,0.5,1,1.5,2,2.5,3,4,5,6,8,10 --clearance-mm 0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.5 --output-csv results\shape_yaw_sensitivity_focused_scan.csv --output-md results\shape_yaw_sensitivity_focused_scan.md
```

This is an analytic 2D precheck, not a policy rollout. It is used to choose
clearance buckets where yaw alignment becomes necessary before training the
visual yaw estimator / guarded yaw-align phase.

Tight-yaw physical fixture variant:

```powershell
.\scripts\sim2real\eval_multigeom_v2_true_fixture_tight_yaw.ps1 -Profile rectangular_key -Episodes 5 -Seeds 906500
.\scripts\sim2real\eval_multigeom_v2_true_fixture_tight_yaw.ps1 -Profile square_square -Episodes 5 -Seeds 906500
.\scripts\sim2real\eval_multigeom_v2_true_fixture_tight_yaw.ps1 -Profile triangle_triangle -Episodes 5 -Seeds 906500
.\scripts\sim2real\eval_multigeom_v2_true_fixture_tight_yaw.ps1 -Profile hex_hex -Episodes 5 -Seeds 906500
```

This uses `geometry_true_fixture_variant=tight_yaw` through
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_eval.yaml`. The fixed
clearances are `rectangular_key=1.0mm`, `square_square=0.75mm`,
`triangle_triangle=0.75mm`, and `hex_hex=0.5mm`. These are intended as a
pressure test where cross-section yaw alignment can matter; they are not yet
the default v2 evaluation.

Current 5-episode tight-yaw smoke on seed `906500` with the v148/v149 policy
stack:

- `rectangular_key`: `5/5`, collision `0`, timeout `0`
- `square_square`: `1/5`, collision `0`, timeout `4/5`
- `triangle_triangle`: `5/5`, collision `0`, timeout `0`
- `hex_hex`: `5/5`, collision `0`, timeout `0`

The square failures reached near-hole XY at some point but stayed around
`38-40mm` above target, with about `3-6 deg` final square yaw error and
negative clearance margins. This is the current evidence that tight-yaw square
needs an explicit yaw-estimation / yaw-align phase before descent.

Visual yaw-label dataset and estimator:

```powershell
python scripts\scan_visual_yaw_views.py --samples-per-candidate 128 --epochs 8 --batch-size 64 --seed 908000
python scripts\collect_visual_yaw_dataset.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_dataset.yaml --output datasets\visual_yaw_v1_tight_yaw_key_focus_2k_crop_wider.npz --output-md results\visual_yaw_v1_tight_yaw_key_focus_2k_crop_wider.md
python scripts\train_visual_yaw_estimator.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_train.yaml --output-md results\visual_yaw_estimator_v1_tight_yaw_key_focus_2k_crop_wider.md
```

The collector places the UR5e near the hole with controlled wrist-yaw offsets
and saves `cam_image`, `near_hole_crop`, and generic `shape_yaw_*` labels.
Peg-tip cap/outline helpers are disabled by default for this dataset, so the
estimator cannot learn from debug-only highlights.

The first 1k balanced estimator was only a pipeline baseline:

- overall best validation mean yaw error: `28.5 deg`, p95 `81.1 deg`
- `hex_hex`: mean `14.3 deg`, p95 `26.4 deg`
- `square_square`: mean `20.3 deg`, p95 `43.1 deg`
- `triangle_triangle`: mean `27.0 deg`, p95 `57.2 deg`
- `rectangular_key`: mean `53.1 deg`, p95 `127.9 deg`

The view/crop scan showed `crop_wider` is the best low-risk next setting:
it keeps the wrist camera pose and only changes `near_hole_crop_source_size`
from `64` to `80`. With a key-focused 2k dataset, the current estimator result
is:

- overall best validation mean yaw error: `13.7 deg`, p95 `47.4 deg`
- `hex_hex`: mean `6.4 deg`, p95 `16.9 deg`
- `square_square`: mean `5.8 deg`, p95 `16.2 deg`
- `triangle_triangle`: mean `8.4 deg`, p95 `16.0 deg`
- `rectangular_key`: mean `20.1 deg`, p95 `56.5 deg`

Interpretation: the training path and low-risk crop change help substantially,
but key yaw p95 is still too high for controller integration without more
data/view refinement.

Held-out yaw diagnostics:

```powershell
python scripts\eval_visual_yaw_estimator.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_eval.yaml
```

The diagnostic report is
`results\visual_yaw_estimator_v1_tight_yaw_key_focus_2k_crop_wider_eval.md`,
with worst-case key images in
`results\visual_yaw_estimator_v1_tight_yaw_key_focus_2k_crop_wider_eval_worst_key.png`.
It confirms that the remaining error is concentrated in `rectangular_key`,
especially the `-60..-30 deg` and `-120..-90 deg` target-yaw bins. This is why
the next larger dataset uses stratified yaw sampling.

Next key-focused stratified run:

```powershell
python scripts\collect_visual_yaw_dataset.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_dataset_key_focus_8k_stratified.yaml
python scripts\train_visual_yaw_estimator.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_train_key_focus_8k_stratified.yaml
python scripts\eval_visual_yaw_estimator.py --config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_eval_key_focus_8k_stratified.yaml
```

Current 8k stratified result:

- Dataset:
  `datasets\visual_yaw_v1_tight_yaw_key_focus_8k_stratified_crop_wider.npz`
- Model:
  `results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_crop_wider.pt`
- Eval:
  `results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_crop_wider_eval.md`
- Overall validation mean/p95: `2.10/5.74 deg`
- Per-profile mean/p95: `square_square=1.39/3.80 deg`,
  `triangle_triangle=1.90/5.04 deg`, `hex_hex=1.24/3.32 deg`,
  `rectangular_key=2.71/6.78 deg`
- The old key hard bins `-60..-30 deg` and `-120..-90 deg` now have p95
  `4.79 deg` and `4.98 deg`.

This is the first yaw estimator that is accurate enough to test in a guarded
yaw-align controller. Do not use it as an unconditional yaw command: worst-case
images still include rare severe occlusion outliers, so the controller should
gate on visibility/confidence and fall back to no yaw correction when the
visual estimate is unreliable.

Guarded visual yaw-align / yaw-sensitive key smoke:

```powershell
.\scripts\sim2real\eval_multigeom_v2_true_fixture_tight_yaw.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_eval.yaml `
  -Profile rectangular_key -Episodes 5 -Seeds 906500 `
  -ResultDir results\sim2real_multigeom_v2_true_fixture_tight_yaw_key_yaw_success_smoke

.\scripts\sim2real\eval_multigeom_v2_true_fixture_tight_yaw_visual_yaw_align.ps1 `
  -Config configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_eval.yaml `
  -Profile rectangular_key -Episodes 10 -Seeds 906500,907500,908500,909500,910500,911500 `
  -ResultDir results\sim2real_multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_multiseed_60ep
```

The new `success_shape_yaw_tolerance_deg` environment option makes non-round
success require XY, Z, and shape yaw simultaneously. This matters because the
old tight-yaw smoke only checked XY/Z: `rectangular_key` could be `30/30`
without proving that the key tab was aligned to the keyhole. With
`rectangular_key` yaw tolerance set to `10 deg`, the no-visual-yaw baseline is
`0/5` on seed `906500`.

Runtime visual yaw-align status:

- Naive soft visual yaw correction: `0/5` under the yaw-sensitive gate.
- Hard block / hold variants confirmed the visual estimator can drive yaw
  close to `0 deg`, but XY drift and early release caused timeouts.
- Current strict hold/recenter recheck:
  `multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_strict_eval.yaml`
  reached `4/10`, collision `1/10`, timeout `5/10`.
- Bounded `commit_descent_latch` without target hold:
  `multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_eval.yaml`
  reached `15/30`, collision `0`, timeout `15/30` across seeds
  `906500/907500/908500`.
- Current best diagnostic:
  `multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_eval.yaml`
  reached `27/30`, collision `0`, timeout `3/30` across seeds
  `906500/907500/908500` (`10/10`, `9/10`, `8/10`). It only commits descent
  after consecutive visual yaw/XY/Z stability, uses a bounded 2 cm XY latch,
  and preserves the last visually aligned IK orientation target during short
  raw-norm/XY gate dropouts.
- Extended 60ep target-hold check reached `55/60`, but with `2/60`
  collisions. The sim-to-real-oriented safer diagnostic is now
  `multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_eval.yaml`:
  `54/60`, collision `0`, timeout `6/60` across
  `906500/907500/908500/909500/910500/911500`. It requires same-step visible
  yaw predictions for active descent and releases target hold when live
  predicted yaw error exceeds `8 deg`.
- The 120ep visible check exposed a delayed-action collision tail:
  `103/120`, collision `2/120`, timeout `15/120`. The current safest
  diagnostic is
  `multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_eval.yaml`:
  `104/120`, collision `0/120`, timeout `16/120`. It adds a low-visibility
  brake that lifts and flushes control history when yaw visibility is poor,
  predicted yaw is large, XY is off-center, and the peg is already low.
- A bounded re-acquire diagnostic is now available:
  `multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_eval.yaml`.
  It adds high-Z lift/recenter retry for wrong-yaw-basin timeouts. On targeted
  hard seeds `908500/909500/910500`, it reached `49/60`, collision `0/60`,
  timeout `11/60`, compared with `47/60`, collision `0/60`, timeout `13/60`
  for the brake subset. This is not yet promoted because the improvement is
  small and has not passed the full six-seed 120ep gate.
- A relaxed yaw-correction path inside re-acquire exists but is disabled in the
  diagnostic config. Its first 10ep smoke regressed `909500` from `5/5` to
  `4/5`, so it needs a better confidence gate before use.
- A re-acquire descent path exists as another default-off diagnostic:
  `multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_descent_eval.yaml`.
  It permits slow descent during re-acquire only with same-step visible yaw,
  small predicted yaw, bounded XY, and high enough Z. The 10ep smoke reached
  `908500=4/5`, `909500=5/5`, collision `0`; keep it diagnostic because it
  did not clearly improve the hard timeout set.
- Over-narrow `commit_descent` almost never triggered, while the wider `xy30`
  variant did not improve success and can enter the wrong yaw basin.

Interpretation: the visual stack can now contribute to true key-tab yaw
alignment under an explicit XY/Z/yaw success gate. Target hold fixed the main
observed failure mode where the key reached near-zero true yaw and then drifted
back to the `~180 deg` basin after visual control gated out. This is still a
diagnostic state machine. For sim-to-real-oriented work prefer the brake
variant because it removes the observed collision tail while preserving roughly
the same success level. The bounded re-acquire diagnostic gives a small
targeted gain but is not yet a new default. The next work is improving
visual-yaw confidence/action selection during re-acquire. Square visual yaw remains
disabled because the current runtime distribution produced false roughly
`45 deg` predictions on square.

Offline confidence analysis with `scripts\analyze_visual_yaw_reacquire_traces.py`
on the targeted 60ep re-acquire run shows why the next step should be confidence
and action selection rather than more retry/descent logic: all re-acquire rows
had mean pred-vs-truth yaw error `20.0 deg` and opposite-sign rate `39.3%`.
The existing visibility gate improved this to `17.5%` opposite-sign at `31.1%`
coverage, and a temporal-delta-stable gate reduced high-error tail to `1.4%`
at `19.7%` coverage. Simple predicted-sign stability is not enough, because it
can keep a stable but wrong sign.

Conservative relaxed-yaw diagnostic:
`multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_confident_relaxed_yaw_eval.yaml`
adds default-off runtime confidence gates for re-acquire relaxed yaw. It
requires visible prediction stats, a 3-frame signed-yaw delta window under
`12 deg`, allows visible re-apply, and caps correction at `30 deg`. Fixed
15ep smoke on `908500/909500/910500` reached `14/15`, collision `0`; the
matching default re-acquire recheck on `908500/909500` was `9/10`, collision
`0`. The smoke triggered `reacquire_relaxed_yaw` on `8/13/29` rows by seed.
This is promising but remains diagnostic-only until it passes the targeted
60ep hard-seed gate and then the six-seed 120ep gate.

Targeted 60ep result for the same candidate: `51/60`, collision `1/60`,
timeout `8/60` (`908500=16/20`, `909500=17/20`, `910500=18/20`). The default
bounded re-acquire targeted run was `49/60`, collision `0/60`, timeout
`11/60`. The candidate rescued four baseline timeouts but regressed two
baseline successes and changed `908516` from timeout into a plate collision.
The collision had no `reacquire_relaxed_yaw` rows and ended at large XY under
`z_gate`, so this candidate is not promoted. The next step is a large-XY/low-Z
safety brake before any further 120ep promotion attempt.

Large-XY/low-Z brake diagnostic:
`multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_confident_relaxed_yaw_large_xy_low_z_brake_eval.yaml`
adds a default-off brake that lifts/flushes when XY is large and Z is already
near the hole. The broad `z<=8 cm` setting passed the targeted hard 60ep set
with `52/60`, collision `0/60`, timeout `8/60`, but failed the six-seed 120ep
gate with `105/120`, collision `1/120`, timeout `14/120`. It disrupted
`906500`, where the current low-visibility brake baseline succeeds. This
confirms that scalar brake widening is not enough; the next design should be a
stateful descent-permission/abort controller. Current safest key-yaw baseline
remains `104/120`, collision `0/120`.

Stateful descent-abort diagnostic:

- Runtime support is implemented as default-off
  `guard_visual_yaw_align_descent_abort_*` controls in
  `scripts\eval_guarded_policy.py`. The phase can trigger on late low-Z /
  off-center keyhole states, reset the pose IK yaw target while active, lift,
  recenter, flush delayed control history, and records per-step trace fields:
  `guard_visual_yaw_align_descent_abort_active`, `triggered`, `phase`, and
  `attempts`.
- Confident relaxed-yaw plus descent-abort:
  `multigeom_v2_true_fixture_tight_yaw_key_vy_conf_relax_descent_abort_eval.yaml`.
  It can rescue individual collision seeds such as `908516` in 1ep smoke, but
  the 40ep gate on `906500/908500` was not safe. Variants tested during tuning
  either caused `906500` timeout/collision or left `908500` with a collision.
  Do not promote.
- Bounded re-acquire plus conservative descent-abort:
  `multigeom_v2_true_fixture_tight_yaw_key_vy_reacquire_descent_abort_unreliable_eval.yaml`.
  Low-Z unreliable-only trigger turned `908516` from collision to timeout and
  preserved `906500/908500` 1ep smoke, but 40ep was `906500=18/20` collision
  `0`, `908500=17/20` collision `1`. Adding a large-predicted-yaw trigger
  rescued `908516` 1ep but 40ep became `906500=18/20` collision `1` and
  `908500=15/20` collision `0`.
- Conclusion: descent-abort is useful as instrumentation and a default-off
  diagnostic hook, but the current trigger/intervention is not a promotion
  candidate. For sim-to-real safety, keep the visible-brake baseline as the
  current best key-yaw candidate and shift the next work away from scalar
  threshold scanning toward a better learned/estimated yaw-confidence gate or
  a more deliberate high-Z retreat/recenter controller.

Temporal visual-yaw action/descent gate diagnostic:

- Runtime support is implemented as default-off
  `guard_visual_yaw_align_temporal_action_gate_*` controls. The gate can watch
  recent signed-yaw predictions, require temporal stability for large yaw
  predictions, optionally restore the previous IK target, and/or block descent.
- Config:
  `multigeom_v2_true_fixture_tight_yaw_key_visible_brake_temporal_action_gate_eval.yaml`.
- Hard reset-target smoke regressed `906500`, `908500`, and `908516` to
  timeout because yaw convergence repeatedly lost its target.
- The softer descent-only version kept the yaw target active and only blocked
  downward motion during unstable large-yaw predictions. It passed basic smoke
  and gave `906500=19/20`, collision `0`; `908500=16/20`, collision `0` on
  the 40ep check, but targeted hard 60ep was only `47/60`, collision `0`,
  timeout `13` (`908500=16/20`, `909500=14/20`, `910500=17/20`).
- Decision: keep this as diagnostic evidence only. Delaying descent on
  unstable visual-yaw predictions does not solve the wrong-yaw-basin timeout
  tail and is not a promotion candidate.

Failure-mode trace analysis on 2026-06-18:

- Added `scripts\analyze_key_yaw_failure_modes.py` to classify rectangular-key
  tight-yaw failures from existing episode/step CSVs.
- Generated `results\key_yaw_failure_mode_analysis.md` and
  `results\key_yaw_failure_mode_analysis.csv`.
- The locally available visible-brake subset contains four 20ep seeds:
  `70/80`, collision `0`, timeout `10`. This is a subset of the historical
  `104/120`, collision `0/120` record.
- Temporal descent gate targeted set remains `47/60`, collision `0`,
  timeout `13`.
- The dominant residual class is `timeout_wrong_yaw_basin`: `6/10` local
  visible-brake failures and `10/13` temporal-gate failures finish with key yaw
  near the wrong asymmetric 180-degree basin.
- Follow-up opportunity counting shows that reliable large-yaw visual evidence
  appears in both successes and failures. The remaining problem is therefore
  not simply "the camera cannot see yaw"; it is that yaw correction is not
  safely preserved/reacquired through recovery and recenter phases.
- Rejected diagnostic:
  `multigeom_v2_true_fixture_tight_yaw_key_visible_brake_near_control_eval.yaml`
  switches visual-yaw activation from `final_servo` to `near_control`. It got
  `0/3` on seeds `908508,908516,910500`, with two collisions. Do not promote.
- Target-hold diagnostics:
  - `multigeom_v2_true_fixture_tight_yaw_key_visible_brake_high_yaw_target_hold_eval.yaml`
    was too broad: it rescued `910500` 1ep but caused a collision on `908508`.
  - `multigeom_v2_true_fixture_tight_yaw_key_visible_brake_high_yaw_arm_target_hold_eval.yaml`
    was safer: formal smoke `2/3`, collision `0`; 40ep on `906500,908500`
    was `35/40`, collision `0`, timeout `5`. This does not improve the
    `908500` tail over the visible-brake baseline, so do not promote.
- Wrong-basin hold diagnostic:
  - Added a default-off hook in `scripts\eval_guarded_policy.py` and config
    `multigeom_v2_true_fixture_tight_yaw_key_visible_brake_wrong_basin_hold_eval.yaml`.
  - Same-seed 40ep comparison on `906500,908500`: visible-brake baseline
    `35/40`, wide hold `33/40`, 6 cm max-XY hold `34/40`, all collision `0`.
  - Report: `results\key_yaw_wrong_basin_hold_failure_analysis.md`.
    Keep this hook diagnostic-only; it does not beat the current baseline.
- Narrow wrong-basin re-acquire diagnostic:
  - Added
    `multigeom_v2_true_fixture_tight_yaw_key_visible_brake_wrong_basin_reacquire_narrow_eval.yaml`.
  - Added default-off visible/stable trigger gates for the generic re-acquire
    path in `scripts\eval_guarded_policy.py`.
  - Smoke on `906500,908500,908516`: ungated narrow re-acquire reached `3/3`
    and rescued `908516`; gated + low-Z large-XY brake reached `2/3`.
  - Same-seed 40ep: visible-brake baseline `35/40`, hold 6 cm `34/40`,
    ungated narrow re-acquire `35/40` with `1` collision, gated narrow
    re-acquire `34/40` with collision `0`.
  - Report: `results\key_yaw_wrong_basin_reacquire_narrow_analysis.md`.
    Do not promote; the safety gate removes the useful rescue signal, while
    the unsafe version introduces collision risk.
- Low-Z lateral-pop recovery diagnostic:
  - Added default-off
    `guard_visual_yaw_align_low_z_lateral_pop_recovery_*` controls plus the
    diagnostic config
    `multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_lateral_pop_recovery_eval.yaml`.
  - Safe recovery-only smoke on `906500,908500,908516`: `2/3`, collision `0`,
    timeout `1`. It triggers too late to rescue the known `908516` tail.
  - A late-finish/freeze-XY variant was rejected because it regressed
    `906500` to timeout and turned `908516` into collision.
  - Report: `results\key_yaw_low_z_lateral_pop_recovery_analysis.md`.
    Keep both hooks diagnostic-only and default-off.
- Visual-yaw action-selection diagnostic:
  - Added `scripts\analyze_visual_yaw_action_selection.py` to summarize
    candidate runtime gates from step traces.
  - On the gated narrow re-acquire 40ep trace, `visible +
    temporal-delta-stable` rows had zero sign mismatch and zero high-error
    rows, but near-zero predicted yaw still did not imply true near-zero yaw.
    Even a very conservative `pred<=2deg` and `XY<=8mm` descent candidate had
    about `12deg` true yaw on average in the timeout traces.
  - Added
    `multigeom_v2_true_fixture_tight_yaw_key_visible_brake_reacquire_high_yaw_action_selection_eval.yaml`
    as a diagnostic that disables re-acquire-local descent and only allows
    visible/stable high-yaw re-apply. Same-seed 40ep result:
    `34/40`, collision `0`, timeout `6`. This ties gated narrow re-acquire
    but is below the visible-brake baseline `35/40`.
  - Reports:
    `results\visual_yaw_action_selection_narrow_gated_40ep.md`,
    `results\visual_yaw_action_selection_high_yaw_only_40ep.md`, and
    `results\key_yaw_high_yaw_action_selection_analysis.md`.
  - Do not promote. The next useful direction is better visual evidence near
    the final descent point, not more scalar descent thresholds.
- Conclusion: the next v2 keyhole work should not be another broad hold,
  re-acquire, descent/brake scalar scan, or late-finish XY-freeze variant. The
  remaining useful branch is to improve visual evidence near the final descent
  point, for example a second/cavity-facing view or a specifically collected
  near-zero-yaw re-acquire dataset. Otherwise keep the current visible-brake
  baseline for safety.

Quick smoke:

```powershell
.\scripts\sim2real\eval_multigeom_v2_true_fixture.ps1 -Profile hex_hex -Episodes 1
.\scripts\sim2real\eval_multigeom_v2_true_fixture.ps1 -Profile triangle_triangle -Episodes 1
.\scripts\sim2real\eval_multigeom_v2_true_fixture.ps1 -Profile slot_slot -Episodes 1
.\scripts\sim2real\eval_multigeom_v2_true_fixture.ps1 -Profile rectangular_key -Episodes 1
```

Current 10-episode smoke:

```powershell
.\scripts\sim2real\eval_multigeom_v2_true_fixture.ps1 -Profile hex_hex -Episodes 10 -Seeds 906500 -ResultDir results\sim2real_multigeom_v2_true_fixture_10ep_probe_visual_ring_tri_clamp
.\scripts\sim2real\eval_multigeom_v2_true_fixture.ps1 -Profile triangle_triangle -Episodes 10 -Seeds 906500 -ResultDir results\sim2real_multigeom_v2_true_fixture_10ep_probe_visual_ring_tri_clamp
.\scripts\sim2real\eval_multigeom_v2_true_fixture.ps1 -Profile slot_slot -Episodes 10 -Seeds 906500 -ResultDir results\sim2real_multigeom_v2_true_fixture_10ep_probe_visual_ring_tri_clamp
.\scripts\sim2real\eval_multigeom_v2_true_fixture.ps1 -Profile rectangular_key -Episodes 10 -Seeds 906500 -ResultDir results\sim2real_multigeom_v2_true_fixture_10ep_keyhole_peg_tip_visual
```

Current 10-episode smoke results on seed `906500`:

- `hex_hex`: `10/10`, collision `0`, timeout `0`
- `triangle_triangle`: `10/10`, collision `0`, timeout `0`
- `slot_slot`: `10/10`, collision `0`, timeout `0`
- `rectangular_key` keyhole v2 with key peg tip visual: `10/10`,
  collision `0`, timeout `0`

Polygon peg visual-highlight smoke on 2026-06-10:

- `hex_hex`: `10/10`, collision `0`, timeout `0`
- `triangle_triangle`: `10/10`, collision `0`, timeout `0`
- demos:
  `results\sim2real_multigeom_v2_true_fixture_demo_polygon_peg_highlight\demo_hex_hex_seed906500.gif`,
  `results\sim2real_multigeom_v2_true_fixture_demo_polygon_peg_highlight\demo_triangle_triangle_seed906500.gif`
- frame probes:
  `results\sim2real_multigeom_v2_true_fixture_probe\polygon_peg_highlight`

Key peg tip visual smoke on 2026-06-10:

- `rectangular_key`: `10/10`, collision `0`, timeout `0`
- demo:
  `results\sim2real_multigeom_v2_true_fixture_demo_keyhole_peg_tip_visual\demo_rectangular_key_seed906500.gif`
- frame probes:
  `results\sim2real_multigeom_v2_true_fixture_probe\keyhole_peg_tip_visual`

Demo:

```powershell
.\scripts\sim2real\demo_multigeom_v2_true_fixture.ps1 -Profile hex_hex -Seed 906500 -Episodes 1 -ResultDir results\sim2real_multigeom_v2_true_fixture_demo_visual_ring_tri_clamp
.\scripts\sim2real\demo_multigeom_v2_true_fixture.ps1 -Profile triangle_triangle -Seed 906500 -Episodes 1 -ResultDir results\sim2real_multigeom_v2_true_fixture_demo_visual_ring_tri_clamp
.\scripts\sim2real\demo_multigeom_v2_true_fixture.ps1 -Profile slot_slot -Seed 906500 -Episodes 1 -ResultDir results\sim2real_multigeom_v2_true_fixture_demo_visual_ring_tri_clamp
.\scripts\sim2real\demo_multigeom_v2_true_fixture.ps1 -Profile rectangular_key -Seed 906500 -Episodes 1 -ResultDir results\sim2real_multigeom_v2_true_fixture_demo_keyhole_peg_tip_visual
```

Generated demos:

- `results\sim2real_multigeom_v2_true_fixture_demo_visual_ring_tri_clamp\demo_hex_hex_seed906500.gif`
- `results\sim2real_multigeom_v2_true_fixture_demo_visual_ring_tri_clamp\demo_triangle_triangle_seed906500.gif`
- `results\sim2real_multigeom_v2_true_fixture_demo_visual_ring_tri_clamp\demo_slot_slot_seed906500.gif`
- `results\sim2real_multigeom_v2_true_fixture_demo_keyhole_peg_tip_visual\demo_rectangular_key_seed906500.gif`

Implementation notes:

- Mesh assets live under `assets\ur5e_full\assets`.
- The full UR5e XML declares `true_hex_wall_mesh`,
  `true_triangle_wall_mesh`, `true_slot_side_wall_mesh`,
  `true_slot_arc_wall_mesh`, `true_keyhole_tab_side_wall_mesh`,
  `true_keyhole_tab_front_wall_mesh`, `true_keyhole_arc_wall_mesh`,
  `peg_slot_mesh`, `peg_keyhole_mesh`,
  `true_hex_fixture_visual_mesh`, `true_triangle_fixture_visual_mesh`, and
  `true_slot_fixture_visual_mesh`, `true_keyhole_fixture_visual_mesh`, plus
  reusable `true_fixture_wall_0..11`
  collision geoms and one visual-only `true_fixture_visual` geom.
- Keyhole bottom visualization reuses `hole_cavity_visual` as the circular
  dark bottom and `hole_key_tab_cavity_visual` as the protruding tab bottom.
  Both are visual-only.
- The full UR5e XML also declares polygon peg visual-only helper meshes:
  `peg_hex_tip_cap_visual_mesh`, `peg_hex_tip_outline_visual_mesh`,
  `peg_hex_side_edge_visual_mesh`, `peg_triangle_tip_cap_visual_mesh`,
  `peg_triangle_tip_outline_visual_mesh`, and
  `peg_triangle_side_edge_visual_mesh`, plus key peg tip helpers
  `peg_keyhole_tip_cap_visual_mesh` and
  `peg_keyhole_tip_outline_visual_mesh`.
- The tight-yaw variant adds separate fixed-size true-fixture wall/visual mesh
  assets for `hex`, `triangle`, and keyhole profiles. `shape_yaw_clearance` is
  the useful non-negative clearance metric for these shapes; the legacy
  circular `hole_clearance` can be negative for polygon holes and should not be
  used as a validity check.
- MuJoCo compiles OBJ meshes with internal `mesh_pos` / `mesh_quat`; runtime
  placement compensates those values before assigning wall geom pose.
- Unsupported shapes fall back to v1 `box_wall` fixture behavior.

Next work:

- Scale and improve the visual yaw-label dataset before controller integration:
  collect more key-focused data around the `crop_wider` setting and refine
  camera/crop only if key p95 does not improve.
- Train a stronger image-based yaw estimator over wrist camera / near-hole
  crop observations, using each shape's symmetry period (`key=360`,
  `square=90`, `triangle=120`, `hex=60`, `slot=180`).
- Add a guarded yaw-align phase only after the estimator reaches a much lower
  validation error, then rerun the tight-yaw matrix.
- Add size-bucketed or validated runtime-scaled mesh variants after yaw
  alignment works on fixed tight buckets.
- Run a larger multi-seed gate before considering v2 for the sim-to-real
  mainline.

Important limitation: this is a prototype. The v1 `sim2real_multigeom_v1`
baseline remains the stable multi-geometry sim-to-real baseline until v2 passes
multi-seed evaluation and size-randomized mesh fixtures are validated.
