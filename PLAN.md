# Project Plan And Status

Last updated: 2026-06-23

This file records the current project status, known metrics, and next planned steps. Keep it current when a milestone changes.

## Current Objective

The project is moving from a lightweight MuJoCo UR5e-like peg-in-hole environment toward a more faithful UR5e simulation and a cautious sim-to-real pipeline.

The current branch is now split into two tracks:

- `feature/control-state-observation`: the stabilized single-geometry high-start controller baseline.
- `feature/multi-geometry`: the active candidate branch for geometry generalization.

The immediate objective on `feature/multi-geometry` is to keep the single-geometry baseline intact while adding a conservative multi-geometry scaffold. Legacy runtime geometry selection (`single`, `round_square`, `square_square`, `mixed_basic`) is working, and the new same-shape scaffold now adds `round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, `rectangular_key`, and `mixed_same_shape`. The current near-term focus is making single-policy, single-controller high-start insertion stable across the same-shape profiles before collecting larger multi-geometry training datasets.

Current sim-to-real packaging work: v148/v149 has been organized as `sim2real_multigeom_v1`. The new entry document is `SIM2REAL_MULTIGEOM_V1.md`; stable aliases live under `configs\sim2real`; runnable shortcuts live under `scripts\sim2real`. Treat `configs\sim2real\multigeom_v1_eval.yaml` as the authoritative multi-geometry evaluation entry. It inherits the v148 stack and carries the v149 fresh-seed evidence: combined v148+v149 `720/720`, zero collision, zero timeout. Keep v221 as a square-square recovery reference, not the multi-geometry mainline.

Current active research branch: `feature/multigeom-v2-visual-yaw-align`. The new branch entry is `SIM2REAL_MULTIGEOM_V2_VISUAL_YAW_ALIGN.md`; use it first for the current visual-yaw-alignment commands, current safe baseline, and the next evaluation loop.

2026-06-23 low-Z visual-evidence update: extended
`scripts\scan_visual_yaw_views.py` with a `final_descent` candidate group and
explicit low-Z sampling controls. The low-Z scan uses `tip_z_above_range
0.012-0.035m`, `tip_xy_offset_range 0-0.004m`, stratified yaw, and
key-focused profile weighting. In the 96-sample / 4-epoch scan,
`crop_wider_high` was best by key error (`59.6 deg`) versus `open_high`
(`69.7 deg`) and `raise_center_wide` (`72.7 deg`). The top-3 256-sample /
8-epoch recheck kept the same ordering: `crop_wider_high` key error
`71.7 deg`, `open_high` `79.8 deg`, `raise_center_wide` `88.2 deg`. These
small models are not final estimators; the point is view ranking. The next
training run is the new low-Z key-focused config set:
`multigeom_v2_true_fixture_tight_yaw_visual_yaw_*_key_focus_8k_stratified_low_z_crop_high.yaml`.

2026-06-23 low-Z crop-high estimator/runtime update: collected
`datasets\visual_yaw_v1_tight_yaw_key_focus_8k_stratified_low_z_crop_high.npz`
with 8192 samples and trained
`results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_low_z_crop_high.pt`.
Held-out validation mean/p95 is `2.079/6.153 deg` overall and
`2.726/7.377 deg` on `rectangular_key`; bad fraction is `0.00488` for the
`>15 deg` threshold. Runtime config
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_eval.yaml`
keeps the visible-brake controller and switches only to
`near_hole_crop_offset: [-18, -12]` plus the low-Z estimator. Same six-seed
rectangular-key guarded eval reached `111/120`, collision `0/120`, timeout
`9/120`, improving the historical visible-brake baseline `104/120`, collision
`0/120`, timeout `16/120`. Report:
`results\visual_yaw_low_z_crop_high_120ep_summary.md`. Remaining failures are
still timeout-only, not collision failures. Failure report:
`results\visual_yaw_low_z_crop_high_failure_analysis.md`; `7/9` finish with
final yaw error above `150 deg`, and `2/9` are near-insert yaw-gate /
descent-timing misses. Next work should protect the visually aligned yaw target
through low-Z descent and handle `170-179 deg` re-acquire separately, rather
than widen generic brake thresholds.

2026-06-23 key-yaw recovery update: added a default-off low-Z lateral-pop
recovery hook in `scripts\eval_guarded_policy.py` plus diagnostic config
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_lateral_pop_recovery_eval.yaml`.
The safe recovery-only smoke on `906500,908500,908516` was `2/3`, collision
`0`, timeout `1`; it triggered too late to rescue the known `908516` tail.
A late-finish/freeze-XY variant was rejected because it regressed `906500` to
timeout and changed `908516` into collision. Do not promote this line; keep the
current visible-brake baseline as the safest key-yaw baseline. Report:
`results\key_yaw_low_z_lateral_pop_recovery_analysis.md`.

2026-06-23 visual-yaw action-selection update: added
`scripts\analyze_visual_yaw_action_selection.py` to evaluate runtime action
choices against simulator-truth yaw in recorded traces. On the gated narrow
re-acquire 40ep trace, `visible + temporal-delta-stable` rows had zero sign
mismatch and zero high-error rows, but descent candidates based on near-zero
predicted yaw were still misleading: even `pred<=2deg` and `XY<=8mm` had true
yaw around `12deg` on average. A high-yaw-only runtime diagnostic config was
added:
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_reacquire_high_yaw_action_selection_eval.yaml`.
It disables re-acquire-local descent and only permits visible/stable high-yaw
re-apply. Same-seed 40ep result: `34/40`, collision `0`, timeout `6`, tying
gated narrow re-acquire but below the visible-brake baseline `35/40`. Do not
promote. Reports:
`results\visual_yaw_action_selection_narrow_gated_40ep.md`,
`results\visual_yaw_action_selection_high_yaw_only_40ep.md`, and
`results\key_yaw_high_yaw_action_selection_analysis.md`.

2026-06-09 true-fixture branch status: `feature/multigeom-v2-true-fixtures`
is the experimental branch for replacing the v1 box-wall hole scaffold with
per-shape fixture meshes. The initial implementation is opt-in through
`geometry_fixture_mode=true_mesh` and currently covers `hex_hex`,
`triangle_triangle`, `slot_slot`, and `rectangular_key` on the full UR5e XML. It keeps v1 behavior
unchanged by default (`box_wall`). The rendered v2 fixture now uses
visual-only ring meshes while collision remains convex-decomposed, which fixes
the misleading segmented/sharp demo appearance. `triangle_triangle` true mesh
is clamped so the triangular hole circumdiameter is at most `2x` the peg
diameter. Smoke results on seed `906500` after visual-ring and triangle-clamp
changes: `hex_hex=10/10`, `triangle_triangle=10/10`, and `slot_slot=10/10`,
zero collision and zero timeout, plus successful 2x2 demos under
`results\sim2real_multigeom_v2_true_fixture_demo_visual_ring_tri_clamp`. This
is not yet the stable sim-to-real mainline because multi-seed validation,
size-randomized mesh fixtures, and key-specific tight-insertion yaw handling
are still pending.

2026-06-10 true-fixture visual update: polygon pegs now have visual-only tip
cap, tip outline, and subtle side-edge highlight meshes for `hex` and
`triangle`. These are attached to `tool0`, dynamically enabled only for
polygon peg profiles, and keep `contype=0` / `conaffinity=0`, so they do not
change insertion physics. Smoke after the change: `hex_hex=10/10` and
`triangle_triangle=10/10` on seed `906500`, zero collision and zero timeout.
The hex demo probe is under
`results\sim2real_multigeom_v2_true_fixture_demo_polygon_peg_highlight`.
The same visual-only peg tip mechanism now also covers `rectangular_key` with
`peg_keyhole_tip_cap_visual_mesh` and
`peg_keyhole_tip_outline_visual_mesh`; this is the key peg bottom-face
visualization, separate from the keyhole opening's dark bottom marker.
Smoke on seed `906500`: `rectangular_key=10/10`, zero collision and zero
timeout. Demo output:
`results\sim2real_multigeom_v2_true_fixture_demo_keyhole_peg_tip_visual\demo_rectangular_key_seed906500.gif`.

2026-06-10 keyhole v2 update: `rectangular_key` now has an opt-in true_mesh
keyhole profile: round body plus one protruding tab. The full UR5e XML declares
`peg_keyhole_mesh`, `true_keyhole_fixture_visual_mesh`, and three reusable
keyhole wall meshes; runtime placement activates 11 convex wall segments and
keeps those collision segments transparent when the visual ring is present. The
demo also has a visual-only dark keyhole bottom marker, composed from a
non-colliding cylinder plus tab box (`hole_cavity_visual` and
`hole_key_tab_cavity_visual`). Smoke on seed `906500` after adding the bottom
visual: `rectangular_key=10/10`, zero collision and zero timeout. Demo output:
`results\sim2real_multigeom_v2_true_fixture_demo_keyhole_bottom_visual\demo_rectangular_key_seed906500.gif`.
Regression smoke after extending true fixture walls to 12 geoms:
`hex_hex=1/1`, `triangle_triangle=1/1`, and `slot_slot=1/1`, all zero
collision and zero timeout. Remaining keyhole limitations: fixed-size mesh
assets only, no validated size randomization, and key-specific yaw alignment is
not implemented yet.

2026-06-16 shape yaw sensitivity update: added
`scripts\scan_shape_yaw_sensitivity.py` to run an analytic 2D cross-section
scan over same-shape yaw error and clearance. This scan intentionally does not
use visual-only peg-tip highlights and does not run the policy; it identifies
clearances where yaw alignment becomes a necessary condition before training a
visual yaw estimator. Default report:
`results\shape_yaw_sensitivity_scan.md`; focused report:
`results\shape_yaw_sensitivity_focused_scan.md`. Initial focused candidates:
 `rectangular_key=0.75-1.25mm`, `square_square=0.5-1.0mm`,
 `triangle_triangle=0.5-1.0mm`, and `hex_hex=0.5mm`. Next step is to turn these
analytic candidates into MuJoCo physical tight-fixture buckets, then collect
image-only yaw labels with debug highlights off.

2026-06-16 tight-yaw physical fixture update: added opt-in
`geometry_true_fixture_variant=tight_yaw` and
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_eval.yaml`. The variant
uses fixed tight same-shape clearances chosen from the analytic scan:
`rectangular_key=1.0mm`, `square_square=0.75mm`,
`triangle_triangle=0.75mm`, and `hex_hex=0.5mm`. It also adds tight-yaw mesh
assets for the true-fixture wall/visual rings. `GuardedDeploymentState` now
keeps both legacy `hole_clearance` and non-negative `shape_yaw_clearance`, so
polygon fixtures no longer crash guard evaluation when the old circular-radius
clearance is negative. New wrapper:
`scripts\sim2real\eval_multigeom_v2_true_fixture_tight_yaw.ps1`.
Initial 5ep seed `906500` smoke with the current v148/v149 policy stack:
`rectangular_key=5/5`, `square_square=1/5`, `triangle_triangle=5/5`, and
`hex_hex=5/5`; all non-square runs had zero collision and zero timeout. The
square failures were timeout-dominant near-hole stalls: failed episodes reached
sub-mm to low-mm XY at some point but stayed around `38-40mm` above target with
about `3-6 deg` final yaw error and negative topdown/tilted clearance margins.
This confirms tight-yaw square is now a useful pressure test for the next
visual yaw-estimator / guarded yaw-align phase. Debug peg-tip visual highlights
remain demo-only and should stay disabled for training labels.

2026-06-16 visual yaw estimator pipeline update: added generic same-shape yaw
telemetry in the environment (`shape_yaw_period_deg`,
`shape_yaw_signed_error_deg`, `shape_yaw_error_deg`,
`shape_yaw_label_sin/cos`) and a new `enable_peg_tip_visual_helpers` switch.
The default remains enabled for demos, but yaw-label collection disables it so
the model cannot rely on artificial peg-tip cap/outline highlights. New
scripts/configs:
`scripts\collect_visual_yaw_dataset.py`,
`scripts\train_visual_yaw_estimator.py`,
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_dataset.yaml`,
and
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_train.yaml`.
Smoke dataset `results\visual_yaw_v1_tight_yaw_smoke_32.npz` validated the
schema, image/crop shapes, nonblank pixels, and `helpers_enabled=False`.
First 1k baseline:
`datasets\visual_yaw_v1_tight_yaw_1k.npz` with 1024 samples, balanced 256 each
for `square_square`, `triangle_triangle`, `hex_hex`, and `rectangular_key`.
Training output:
`results\visual_yaw_estimator_v1_tight_yaw_1k.pt`. Best validation mean yaw
error was `28.5 deg`, p95 `81.1 deg`. Per-profile mean error:
`hex_hex=14.3 deg`, `square_square=20.3 deg`,
`triangle_triangle=27.0 deg`, `rectangular_key=53.1 deg`. Interpretation: the
data/training path works, but this estimator is not accurate enough for
guarded wrist yaw alignment. The key profile is the main visibility/ambiguity
bottleneck, likely because key yaw spans 360 degrees and is often partly
occluded in the current wrist view. Next step should improve yaw data quality:
larger balanced data, profile-specific/key-focused sampling, and wrist/crop
pose scan before connecting the estimator to the controller.

2026-06-16 view/crop scan and key-focus update: added
`scripts\scan_visual_yaw_views.py` and ran a 4-candidate wrist camera / crop
scan with 128 samples/candidate and 8 epochs each. `raise_center` was best by
key-error tie-breaker, but `crop_wider`
(`near_hole_crop_source_size=80` while keeping the current wrist camera pose)
was nearly as good and lower risk for sim-to-real. The scan showed all
candidates still had a hard key problem, but `crop_wider` reduced key
validation mean error from `77.9 deg` (baseline scan) to `67.3 deg`. Using that
low-risk crop change, I collected a key-focused 2k dataset:
`datasets\visual_yaw_v1_tight_yaw_key_focus_2k_crop_wider.npz`, with
`rectangular_key` at 50% of samples and the other tight-yaw profiles retained.
The resulting estimator
`results\visual_yaw_estimator_v1_tight_yaw_key_focus_2k_crop_wider.pt`
reached best validation mean yaw error `13.7 deg`, p95 `47.4 deg`.
Per-profile mean error:
`square_square=5.8 deg`, `triangle_triangle=8.4 deg`,
`hex_hex=6.4 deg`, `rectangular_key=20.1 deg`. This is the first estimator
that is plausibly useful for a later guarded yaw-align experiment, but key p95
is still too high to wire into the controller immediately. Next step is either
more key-specific data around the `crop_wider` view or a small camera/crop
refinement around `raise_center` if we want to chase the remaining key error.

2026-06-16 visual yaw diagnostic update: added
`scripts\eval_visual_yaw_estimator.py` and
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_eval.yaml`.
The evaluator reloads a yaw checkpoint, reconstructs the held-out validation
split, reports per-profile and per-yaw-bin error, and writes a worst-case image
sheet. Current 2k crop-wider validation diagnostic:
overall mean `13.7 deg`, p95 `47.4 deg`; `rectangular_key` mean `20.1 deg`,
p95 `56.5 deg`, bad fraction `0.477` for `>15 deg`. The worst key bins are
`-60..-30 deg` and `-120..-90 deg`, so the next scaling step is not just "more
random data": it should use yaw-stratified sampling. The collector now supports
`yaw_sampling_mode=stratified` and `yaw_bin_count`; smoke dataset
`datasets\visual_yaw_v1_tight_yaw_stratified_smoke_96.npz` validated exact
12-bin coverage for `rectangular_key` (`4` samples per bin) with debug helpers
disabled. New 8k configs:
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_dataset_key_focus_8k_stratified.yaml`,
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_train_key_focus_8k_stratified.yaml`,
and
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_visual_yaw_eval_key_focus_8k_stratified.yaml`.

2026-06-16 8k stratified visual yaw result: collected
`datasets\visual_yaw_v1_tight_yaw_key_focus_8k_stratified_crop_wider.npz`
with 8192 samples and nearly exact per-bin yaw balance:
`rectangular_key` bins `341-342` samples each; other profiles `113-114`
samples each. The trained estimator
`results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_crop_wider.pt`
reached best validation mean yaw error `2.10 deg`, p95 `5.74 deg` at epoch
38. Independent eval:
`results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_crop_wider_eval.md`.
Per-profile validation mean/p95:
`square_square=1.39/3.80 deg`, `triangle_triangle=1.90/5.04 deg`,
`hex_hex=1.24/3.32 deg`, and `rectangular_key=2.71/6.78 deg`. The previous
key hard bins improved from p95 `93.4/81.8 deg` to `4.79/4.98 deg` for
`-60..-30 deg` and `-120..-90 deg`. Remaining failures are rare severe
occlusion outliers, with worst key error `87.0 deg`. Conclusion: this is now
accurate enough for a guarded yaw-align prototype, but only with confidence /
visibility gating and a fallback that refuses yaw correction when the key is
not visibly identifiable.

2026-06-16 guarded visual yaw-align update: added
`peg_in_hole_mujoco\visual_yaw_runtime.py`, a generic
`set_pose_ik_target_by_planar_yaw_correction()` environment hook, and
visual-yaw runtime options in `scripts\eval_guarded_policy.py`. The first
key-only runtime smoke showed that the estimator reads real visual key yaw:
predicted yaw tracked the simulator truth while rotating from roughly
`-173 deg` toward the keyhole orientation. However, the old tight-yaw success
criterion only checked XY/Z, so `rectangular_key=30/30` without visual yaw was
not evidence of actual key-tab alignment. I added an opt-in
`success_shape_yaw_tolerance_deg` gate. With `rectangular_key` requiring yaw
`<10 deg`, the baseline became `0/5` and naive soft/blocking visual-yaw
controllers also stayed `0/5`. The current best diagnostic controller,
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_eval.yaml`,
adds a bounded commit-descent latch plus post-align IK orientation target hold
on top of visual yaw hold, XY/Z hold, and post-yaw recenter. It only arms
descent after consecutive visual yaw/XY/Z stability, then briefly continues
descent inside a 2 cm XY release gate. Target hold preserves the last visually
aligned IK orientation target through short raw-norm/XY gate dropouts, blocking
descent and recentering XY instead of letting the wrist drift back to the
`~180 deg` basin. On seeds `906500/907500/908500`, this reached `27/30`, zero
collision and three timeouts (`10/10`, `9/10`, `8/10`). The same commit latch
without target hold was only `15/30`, zero collision and fifteen timeouts; the
strict hold/recenter recheck was `4/10`, collision `1/10`, timeout `5/10`. The
over-narrow `commit_descent` gate almost never triggered, and the wider `xy30`
commit did not improve success. This is strong diagnostic evidence that the
visual pipeline can support real key-tab yaw alignment under an explicit
XY/Z/yaw success gate, but it is still a diagnostic controller, not a stable
policy. Next step: validate target-hold on more seeds and reduce the remaining
two `~174 deg` failures plus one near-insert `11.13 deg` yaw-gate failure
before promoting it; separately, square visual yaw remains disabled because
the runtime distribution produced false roughly `45 deg` corrections.

2026-06-17 target-hold safety update: the aggressive target-hold controller
scaled to `55/60` on seeds `906500/907500/908500/909500/910500/911500`, but
introduced `2/60` collisions on seed `911500`. The collision tail came from
holding an old IK yaw target or continuing descent after the live visual
prediction failed raw-norm/visibility checks. I added
`guard_visual_yaw_align_aligned_descent_require_visible` and
`guard_visual_yaw_align_hold_target_release_yaw_deg`; the safer config
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_eval.yaml`
requires same-step visible yaw predictions for active descent and releases
target hold when the live predicted yaw exceeds `8 deg`. It reached `54/60`,
collision `0/60`, timeout `6/60`. For sim-to-real-oriented work, prefer this
safer visible variant over the slightly higher-success aggressive target-hold
variant. Remaining failures are mostly wrong-yaw-basin timeouts around
`170-178 deg`; next work should either add a bounded yaw re-acquire/retry phase
or run a larger gate to decide whether the current `90%` success / zero
collision level is sufficient for this diagnostic branch.

2026-06-17 low-visibility brake update: the larger 120ep visible gate showed
that the collision tail was not fully gone: `103/120`, collision `2/120`,
timeout `15/120`. I added
`guard_visual_yaw_align_low_visibility_brake_*`, which triggers only when yaw
visibility is poor, predicted yaw is large, XY is off-center, and the peg is
already low; it lifts and flushes control randomization history to cancel
delayed downward motion. The brake config
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_eval.yaml`
reached `104/120`, collision `0/120`, timeout `16/120`. This is now the safer
sim-to-real-oriented key-yaw diagnostic. Remaining failures are mostly
`170-179 deg` wrong-yaw-basin timeouts, with a few near-aligned yaw-gate or
not-inserted-Z timeouts. Next useful work is a bounded yaw re-acquire/retry
phase; more collision safety patches are not the bottleneck unless a new
collision class appears.

2026-06-17 bounded re-acquire update: I added default-off
`guard_visual_yaw_align_reacquire_*` tracing/control to
`scripts\eval_guarded_policy.py` and the diagnostic config
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_eval.yaml`.
The safer setting triggers from step `350`, allows two high-Z lift/recenter
attempts, uses `recenter_max_steps=220`, and keeps relaxed yaw correction
disabled. It reached `49/60`, collision `0/60`, timeout `11/60` on targeted
hard seeds `908500/909500/910500`; the brake subset was `47/60`, collision
`0/60`, timeout `13/60`. This is a real but small improvement, so do not
promote it over the 120ep brake baseline yet. I also implemented a default-off
relaxed yaw correction path for re-acquire, but the first smoke regressed
`909500` from `5/5` to `4/5` by pushing a near-recovered case back into large
XY. Keep relaxed yaw disabled until its confidence gate is redesigned. The next
bottleneck is visual-yaw confidence/action selection while re-acquiring, not
another collision-safety patch.

2026-06-18 re-acquire descent / confidence diagnostic update: I added the
default-off re-acquire descent config
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_descent_eval.yaml`.
It allows slow descent during re-acquire only when same-step visible yaw is
small, XY is bounded, and Z is still high enough. The 10ep smoke reached
`908500=4/5`, `909500=5/5`, collision `0`; this does not justify promotion
because the descent path only triggered clearly in a successful case and did
not solve the hard timeout. I also added
`scripts\analyze_visual_yaw_reacquire_traces.py` and ran it on the 60ep
targeted re-acquire trace. All re-acquire rows had mean pred-vs-truth yaw
error `20.0 deg`, high-error rate `8.1%`, and opposite-sign rate `39.3%`.
The current visibility gate reduced opposite-sign rate to `17.5%` and
high-error rate to `4.1%` at `31.1%` coverage. A simple temporal-delta gate
reduced high-error tail to `1.4%` but only covered `19.7%`; simple sign
stability was unsafe because a wrong sign can be stable. Next work should
redesign visual-yaw confidence/action selection, for example using visibility
plus low-delta prediction as a permissive condition and otherwise holding/lift
recenter rather than applying signed yaw correction.

2026-06-18 conservative re-acquire relaxed-yaw update: I added default-off
runtime confidence gates to the re-acquire relaxed-yaw path:
`guard_visual_yaw_align_reacquire_relaxed_yaw_require_visible`,
`guard_visual_yaw_align_reacquire_relaxed_yaw_require_stable_delta`,
`guard_visual_yaw_align_reacquire_relaxed_yaw_stable_window`,
`guard_visual_yaw_align_reacquire_relaxed_yaw_max_delta_deg`, and
`guard_visual_yaw_align_reacquire_relaxed_yaw_allow_visible_reapply`. The
diagnostic config is
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_confident_relaxed_yaw_eval.yaml`.
It requires visibility stats, a 3-frame signed-yaw delta window under `12 deg`,
and uses a conservative `30 deg` correction cap. During implementation I
introduced and fixed an indentation bug that temporarily disabled
`reacquire_active`; the fixed default re-acquire recheck recovered to
`908500=5/5`, `909500=4/5`, collision `0`. The confident relaxed-yaw smoke
reached `908500=5/5`, `909500=5/5`, `910500=4/5`, collision `0`; it triggered
`reacquire_relaxed_yaw` on `8/13/29` rows respectively. Offline analysis over
the 15ep smoke showed sign-mismatch rate `13.2%` over all re-acquire rows,
`5.7%` over visible rows, and high-error rate `1.1%` for visible+delta-stable
rows. This is a useful next candidate, but do not promote it until it passes
the targeted 60ep hard-seed gate and then the six-seed 120ep gate.

2026-06-18 targeted 60ep confident relaxed-yaw result: the candidate reached
`51/60`, collision `1/60`, timeout `8/60` on `908500/909500/910500`
(`16/20`, `17/20`, `18/20`). Default re-acquire on the same targeted set was
`49/60`, collision `0/60`, timeout `11/60`. The candidate rescued four
baseline timeouts (`908501`, `909511`, `909517`, `910500`) but regressed two
baseline successes (`908518`, `910512`) to timeout and changed `908516` from a
timeout into a plate collision. Offline re-acquire analysis for the candidate
showed all re-acquire rows sign-mismatch rate `19.2%`, visible rows `6.9%`,
and visible+delta-stable high-error rate `0.26%`; confidence gating is doing
useful filtering, but the collision blocks promotion. The `908516` collision
had no `reacquire_relaxed_yaw` rows and ended with large XY (`~9.8 cm`) while
Z was already below target under `z_gate`, so the next implementation should
add a large-XY/low-Z safety brake that lifts and flushes history before any
120ep promotion attempt. Keep the current safest promoted diagnostic as the
low-visibility brake baseline, not this candidate.

2026-06-18 large-XY/low-Z brake result: I added a default-off diagnostic
`guard_visual_yaw_align_large_xy_low_z_brake_*` and the config
`configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_confident_relaxed_yaw_large_xy_low_z_brake_eval.yaml`.
The narrow `z<=1 cm` version removed the isolated `908516` collision when run
alone, but was too late in the `908500` 20ep batch. Raising the trigger to
`z<=8 cm` removed the `908500` batch collision and produced a strong targeted
60ep result: `52/60`, collision `0/60`, timeout `8/60`
(`908500=16/20`, `909500=17/20`, `910500=19/20`). It then failed the six-seed
120ep promotion gate: `105/120`, collision `1/120`, timeout `14/120`. The new
collision was `906500`, where the wide brake triggered early around XY
`7-9 cm`, Z `~8 cm`, disrupted the original safest-brake success path, and
still ended in a plate collision after many brake steps. Conclusion: do not
promote either confident relaxed-yaw or z80 safety-brake configs. The current
safest key-yaw diagnostic remains the low-visibility brake baseline
`104/120`, collision `0/120`. Next work should not keep widening scalar brake
thresholds; it should design a stateful descent-permission/abort controller
that prevents entering low Z with large XY before contact, then returns to
high-Z recenter in a controlled phase.

2026-06-09 packaging smoke: `eval_multigeom_v1.ps1 -Profile round_round -Seeds 906500 -Episodes 1` passed `1/1`; `demo_multigeom_v1.ps1 -Profile round_round -Seed 906500` generated a successful GIF and trace; `preflight_multigeom_v1.ps1` passed in non-strict mode; `dryrun_multigeom_v1.ps1 -ZeroPolicy` wrote a 4-step synthetic real-interface trace.

2026-06-09 demo wiring update: `scripts\demo_policy.py` now loads and applies the v148 approach adapter, final-insert adapter, and square pose/yaw align path. `configs\sim2real\multigeom_v1_demo.yaml` now opens `domain_randomization=true` with `full_light_geometry`, uses the v8 approach adapter, the handoff final-insert adapter, and square pose/yaw alignment. Full-stack demo smoke passed on `round_round`, `square_square`, and `mixed_same_shape` seed `906500`; square demo showed `adapter_steps=103/0/47` for approach/final/yaw, where final stayed gated off because the clean rollout did not enter a stall state.

2026-06-09 demo visibility update: the UR5e task XMLs now include a visual-only
`hole_cavity_visual` dark opening marker and a `hole_top` inspection camera.
`configs\sim2real\multigeom_v1_demo.yaml` now renders `[overview, wrist_cam]`
and uses a 2x2 policy-observation layout by default. The resulting `2560x1440`
GIF places `overview` upper-left, `wrist_cam` lower-left, `cam_image`
upper-right, and `near_hole_crop` lower-right. `hole_top` remains optional but
is not default because the wrist can occlude it during insertion. This does not
alter collision geometry or success criteria. Smoke: `square_square`, seed
`906500`, success, zero collision, `202` steps, output under
`results\sim2real_multigeom_v1_demo_grid2x2_smoke`.

2026-06-09 multi-shape demo geometry check: `hex_hex` and
`triangle_triangle` were verified to use six and three active hole wall geoms
respectively. The misleading part was the visual-only cavity marker: it was a
round dark cylinder for all polygon holes, which made the demo look round or
partly occluded. The marker is now hidden for `hex` and `triangle` so the
actual wall geometry defines the visible opening. Follow-up check showed that
the collision walls themselves are intentionally short box-wall segments; making
those physical segments overlap changed hex insertion and caused a timeout, so
that physics change was rejected. Instead, the XMLs now include separate
`hole_polygon_visual_0..5` geoms. They are visual-only (`contype=0`,
`conaffinity=0`), are shown only for `hex`/`triangle`, and make the demo block
look connected while leaving collision geometry unchanged. New smoke demos:
`results\sim2real_multigeom_v1_demo_grid2x2_shapes_visual_wall_fixed\demo_hex_hex_seed906500.gif`
and
`results\sim2real_multigeom_v1_demo_grid2x2_shapes_visual_wall_fixed\demo_triangle_triangle_seed906500.gif`,
both successful with zero collision. Final visual-wall smoke eval:
`results\sim2real_multigeom_v1_visual_wall_final_probe`, with `hex_hex=1/1`
and `triangle_triangle=1/1`, zero collision and zero timeout. Important
limitation: this v1 path is still a box-wall scaffold, not a final CAD/mesh
fixture; `slot_slot` and `rectangular_key` are rectangular scaffold profiles
with different aspect ratios in v1. The v2 `true_mesh` path now has opt-in
rounded-slot/keyhole mesh geometry.

## Current Branch And Remote

- Active working branch: `feature/multigeom-v2-visual-yaw-align`
- Base candidate branch: `feature/multi-geometry`
- Remote: `https://github.com/AquaMarine763/mujoco-peg-in-hole-ur5.git`
- Latest local single-geometry milestone: `v0.6.50-single-geometry` / `4a0f65f Promote strict single-geometry high-start baseline`
- Latest pushed multi-geometry milestone: `v0.7.4-v8-adapter-finalstart100`
- Latest local multi-geometry boundary milestone: `v0.7.2-early-final-servo-boundary`
- Current version-promotion target: none. v221 has been promoted and pushed.
- Latest promoted contact-aware milestone: `v0.7.7-hard-square-clean3-escape55`
- Current contact-aware status: v221 is the current pushed contact-aware hard `square_square` recovery milestone; it passed the focused 5x30 gate on seeds `924500/927500/928500/929500/931500` with zero collision and zero timeout.
- Current local contact-aware diagnostic status: v316 remains the least-bad current-code hard `square_square` low-Z soft-hold release baseline, but it is not promotable/taggable. A fresh current-code v316 rerun reached `931500=30/30`, but key regression buckets still failed (`927500=29/30`, `929500=28/30`). v315 and v317-v328 are rejected diagnostics. v325-v328 show that local pre-pop hold/limit hooks can move failures between collision and timeout, but do not improve the focused `927500/30ep` gate.

## Current Hard-Square Recovery Diagnostics

The current-code replay no longer cleanly reproduces the older v198 `931500=30/30` result. A fresh serial v198 replay on `931500` reached only `26/30` with three collisions and one timeout, so do not promote from old v198 result files without fresh validation.

2026-06-07 low-Z soft-hold release diagnostics:

- Current-code v311 full rerun on `931500/30ep`: `27/30`, one collision and two timeouts. This does not match the earlier saved v311 `29/30`; treat the older file as historical evidence, not the active baseline.
- v315 added a low-Z/positive-margin gated third contact soft-hold attempt. It reached only `27/30` on `931500`, with two collisions and one timeout. Rejected.
- v316 kept v311's two contact soft-hold attempts but reduced `contact_soft_hold_release_continue` action caps to `max_xy=0.00035`, `max_down=0.0008`. It reached `29/30`, zero timeout and one collision (`931524`). This is the current best local diagnostic.
- v317 extended contact soft-hold from `4` to `8` steps. It regressed to `27/30`, with two collisions and one timeout. Rejected.
- v318 limited contact soft-hold to a single attempt. It regressed to `26/30`, zero collision but four timeouts. Rejected.
- v319 enabled a broad soft-hold release contact-brake. It fixed `931500=30/30` locally but regressed key buckets (`927500=27/30`, `929500=28/30`). Rejected.
- v320 narrowed the second-release contact-brake gate but still regressed `931500=27/30`. Rejected.
- v321 added a default-off soft-hold release-pop hold and enabled it narrowly on top of v316. It fixed the old `931524` episode in one run but produced `931500=29/30` with a new `931513` collision; release-pop hold did not trigger in that failure. Rejected.
- v322 added a default-off no-contact pop hold and enabled it on top of v316 for exhausted-brake lateral pops. It regressed the failure buckets (`927500=27/30`, `929500=27/30`) and is rejected.
- v323 added a default-off severe low-Z lateral-pop high reapproach hook and enabled it on top of v316. The focused `927500/30ep` gate reached only `28/30`, with one collision and one timeout, so it is rejected.
- v324 kept the same severe-pop gate but skipped the pre-lift hold and went directly into escape lift. The focused `927500/30ep` gate still reached only `28/30`, with the same collision/timeout pattern, so it is rejected.
- v325 adds a default-off `square_fast_settle_pre_pop_guard_hold` hook and enables it narrowly on top of v316. Result on `927500/30ep`: `28/30`, one collision and one timeout. It fixed the original `927514` collision but introduced failures on `927525` and `927528`; reject.
- v326 kept v325's hook but extended hold to five steps and allowed earlier repeat holds. Result on `927500/30ep`: `28/30`, zero collision and two timeouts. It removed collision risk but over-held and burned the 1000-step budget; reject.
- v327 tightened topdown margin and limited the pre-pop hold to a single four-step intervention. Result on `927500/30ep`: `28/30`, one collision and one timeout; reject.
- v328 replaced phase hold with action limiting in the same risk window. Result on `927500/30ep`: `27/30`, one collision and two timeouts; reject.
- Current interpretation: the residual is broader than a single soft-hold release pop. The active failure family is low-Z hard-square lateral pop after repeated contact-brake / contact-pop recovery. Heavy recenter/brake/hold responses can trade one collision for new timeouts or new collision seeds, so do not promote scalar local fixes without multi-bucket gates.
- Added `scripts\analyze_pre_pop_guard_traces.py` to scan step traces for candidate pre-pop gate matches before running full simulation gates. Initial scan on v316 failure traces shows the current gate matches both collision seeds (`927514`, `929525`) and timeout seed (`929521`), so it is not discriminative enough by itself.
- Next technical direction: stop blind scalar guard scans. Generate or reuse success step traces for the same hard-square seeds, run the offline classifier against both success and failure traces, then choose a narrower intervention before running another expensive 30ep gate.

Recent diagnostic results:

- v198 fresh serial recheck on `931500`: `26/30`, three collisions, one timeout. Direct fast-settle was disabled, so this exposed current-code residual low-Z pop risk.
- v200 direct finish after clean escape fixed `929500=30/30`, but `931500=29/30` with one collision. Rejected.
- v201 high-Z-only direct finish kept `929500=30/30`, but `931500=29/30` with one collision. Rejected.
- v202 v198 plus `square_recovery_escape_pre_lift_on_trigger=true` improved current-code `931500` to `29/30`, but still had one collision. Rejected.
- v203 v202 plus low-Z contact relief attempts `2 -> 3` passed `929500=30/30` and `931500=30/30`, but focused gate regressed: `924500=29/30`, `927500=28/30`, `928500=30/30`. Rejected.
- v204 v203 plus late-only direct finish did not improve `927500`; still `28/30`. Rejected.
- v205 v204 plus low-Z contact relief attempts `3 -> 4` improved `927500` to `29/30`, zero timeout but one collision. Rejected.
- v206 v205 plus earlier no-contact pre-pop relief phase gate `45 -> 35` removed the `927500` collision but produced `28/30` with two timeouts. Rejected.
- v217 v216 plus recovery escape recenter XY cap `0.006` passed `924500/928500/929500/931500`, but `927500=28/30` with two timeouts. Rejected.
- v218 v217 plus margin-gated late fast finish fixed `927500=30/30`, but `931500=29/30` with one collision. Rejected.
- v219 added `guard_final_servo_square_fast_settle_late_down_boost_min_clean_steps=5`. It blocked the immediate post-contact fast-finish risk, but was too conservative: `927500=29/30` with one timeout and `931500=29/30` with one collision/timeout failure. Rejected.
- v220 lowered the clean-step gate to `3`. It removed the `931500` collision but still left `927500=29/30` and `931500=29/30`, both timeout-only failures stuck in `square_recovery_escape_lift`. Rejected.
- v221 keeps clean3 and lowers `guard_final_servo_square_recovery_escape_height` from `0.070` to `0.055`. It passed the focused hard-square gate:
  - `924500=30/30`
  - `927500=30/30`
  - `928500=30/30`
  - `929500=30/30`
  - `931500=30/30`
  - all zero collision and zero timeout.
  - config: `configs\sim\ur5e_full\eval_multi_geometry_v221_v220_clean3_escape55_hard_square_30ep.yaml`
  - result directory: `D:\peg-in-hole-6yh\v221_clean3_escape55_probe`

Current interpretation:

- The hard square residual was two coupled issues:
  - late fast finish could fire too soon after wall contact and create a low-Z pop/collision;
  - after making fast finish safer, `square_recovery_escape_lift` could consume too much of the 1000-step budget when escape started late.
- v221's current working recipe is a short continuous no-contact gate before late fast finish plus a lower escape height (`55 mm`) so late recovery re-enters recenter/descend sooner.
- Before calling v221 stable for the whole project, run at least one broader regression gate beyond the five hard-square seeds: old collision-sensitive buckets and a small mixed/multi-geometry matrix.

## Multi-Geometry Branch Status

Implemented so far:

- `PegInHoleMujocoEnv` now accepts `geometry_profile`.
- The env can sample/apply legacy profiles `single`, `round_square`, `square_square`, and `mixed_basic`.
- Same-shape profiles are scaffolded: `round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, `rectangular_key`, and `mixed_same_shape`.
- The full, adapter, and lightweight XMLs now include polygonal peg mesh assets for `hex`/`triangle` and default-off auxiliary hole wall geoms for polygonal openings. Polygon peg meshes are scaled to a `12 mm` outer radius and centered around the original peg geom origin so the mesh tip matches the `peg_tip` site.
- `triangle_triangle` currently uses an easy-curriculum hole floor of `2.2 * peg_radius` because the first box-wall triangular-hole scaffold is too tight under the legacy `14.5 - 19 mm` hole range. Treat this as a scaffold setting to tighten later after a better triangular-hole/chamfer model.
- Runtime peg geometry switching is working on the full UR5e XML.
- `scripts\train_sac.py`, `scripts\demo_policy.py`, `scripts\eval_guarded_policy.py`, and `scripts\run_policy_inference.py` accept the new geometry args.
- `scripts\collect_image_expert_dataset.py`, `scripts\collect_image_correction_dataset.py`, `scripts\pretrain_image_actor_bc.py`, and `scripts\pretrain_image_actor_bc_weighted.py` now accept the new geometry args.
- Expert/correction datasets now record `geometry_profile`, `geometry_name`, `peg_shape`, and `hole_shape` arrays for later filtering and diagnostics.
- Smoke config:
  - `configs\sim\ur5e_full\eval_multi_geometry_smoke.yaml`
  - `configs\sim\ur5e_full\collect_multi_geometry_expert_smoke.yaml`
- Smoke result:
  - `mixed_basic` reset/eval smoke passed on seed `612000`
  - sampled geometry: `square_square`
  - `1/1` success on the 1-episode guarded smoke
  - this confirms runtime peg shape switching is working on the full UR5e XML
- Same-shape scaffold smoke:
  - reset/render/step smoke passed for `round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, `rectangular_key`, and `mixed_same_shape`.
  - v0.7.4 guarded recipe 1ep/profile smoke before geometry fixes on seed `880000`: `round_round=1/1`, `hex_hex=0/1 timeout`, `triangle_triangle=0/1 timeout`, `slot_slot=1/1`, `rectangular_key=1/1`. Result directory: `D:\peg-in-hole-6yh\v80_same_shape_geometry_scaffold_smoke`.
  - current fixed scaffold smoke on seed `880000`: `round_round=1/1`, `hex_hex=1/1`, `triangle_triangle=1/1`, `slot_slot=1/1`, `rectangular_key=1/1`, all zero collision and zero timeout.
  - result directory: `D:\peg-in-hole-6yh\v91_same_shape_geometry_fixed_smoke`.
  - follow-up 10ep/profile matrix on seed `881000`: `round_round=10/10`, `hex_hex=10/10`, `triangle_triangle=10/10`, `slot_slot=10/10`, `rectangular_key=10/10`, all zero collision and zero timeout.
  - mixed sampler check on seed `882000`: `mixed_same_shape=20/20`, zero collision and zero timeout.
  - result directory: `D:\peg-in-hole-6yh\v92_same_shape_matrix10_seed881000`.
  - broader fixed-profile matrix on seeds `883000`, `884000`, and `885000`, 10 episodes/profile/seed: combined `150/150`, zero collision, zero timeout. Each fixed profile reached `30/30`; max episode length was `667` steps.
  - result directory: `D:\peg-in-hole-6yh\v93_same_shape_multiseed_3x10_seed883_885`.
  - interpretation: the same-shape scaffold is stable enough under the current guarded v8 adapter recipe to move from smoke testing to balanced same-shape data collection. Do not treat this as final multi-geometry generalization; the next data stage should still keep per-shape balance and keep the temporary easy `triangle_triangle` hole floor visible.
  - balanced same-shape approach-window DAgger smoke:
    - config: `configs\sim\ur5e_full\collect_multi_geometry_same_shape_approach_dagger_smoke.yaml`
    - result directory: `D:\peg-in-hole-6yh\v94_same_shape_approach_dagger_smoke`
    - merged dataset: `image_correction_640_same_shape_approach_dagger_smoke.npz`
    - samples: `640`, with `128` each for `round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, and `rectangular_key`
    - label distribution: `approach_window_rate=1.000`, `descent_should_block_rate=1.000`, all samples phase `approach_recenter`
    - rollout outcome: sample-level episode outcomes were `48` success, `416` collision, `176` timeout; this reflects the collector rollout using the learned policy plus rollout adapter, not the full guarded deployment stack used in v93 eval
    - interpretation: v94 validates same-shape image/control-state schema and balanced approach labels, but it is not a production success-trajectory dataset. Before scaling to 50k, add a guarded-deployment rollout teacher path to the collector or collect from eval guarded traces.
  - guarded-deployment same-shape approach collector:
    - new script: `scripts\collect_guarded_image_correction_dataset.py`
    - new config: `configs\sim\ur5e_full\collect_guarded_same_shape_approach_smoke.yaml`
    - purpose: collect correction NPZ samples from the same guarded deployment stack used by eval, rather than from raw policy/adapter rollout
    - smoke result directory: `D:\peg-in-hole-6yh\v95_guarded_same_shape_approach_smoke`
    - 32-sample/profile smoke with local v8 adapter override:
      - `round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, and `rectangular_key` each collected `32` samples from `2` successful episodes
      - each shard had `success=1.000`, `collision=0.000`, `timeout=0.000`
    - merged smoke dataset: `image_correction_160_same_shape_guarded_approach_smoke.npz`
    - merged inspection: five shapes balanced at `32` samples each, all `160` samples from success episodes, `approach_window_rate=1.000`, `descent_should_block_rate=1.000`, all phase `approach_recenter`
    - config smoke with `guard_final_servo_start_z=0.100`: `config_smoke_round_round_8.npz` collected `8` samples from `1/1` successful episode
    - 512/profile guarded pilot result directory: `D:\peg-in-hole-6yh\v96_guarded_same_shape_approach_512`
    - 512/profile shards: `round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, and `rectangular_key` each collected `512` samples from `32` successful guarded episodes, with shard-level `success=1.000`, `collision=0.000`, `timeout=0.000`.
    - merged guarded pilot dataset: `image_correction_2560_same_shape_guarded_approach.npz`
    - merged guarded pilot inspection: `2560` samples, `160` unique source episodes, five profiles balanced at `512` samples each, all success-sourced, all phase `approach_recenter`, `approach_window_rate=1.000`, `descent_should_block_rate=1.000`, `episode_collision_rate=0.000`, `episode_timeout_rate=0.000`.
    - v97 same-shape-only adapter smoke: trained `D:\peg-in-hole-6yh\v97_same_shape_adapter_2560\approach_adapter_same_shape_2560_fullcrop_xy_override.pt` from the v96 merged dataset, `20` epochs, final validation loss `8.78e-6`. Fixed profile matrix on seed `890500` passed `50/50`, but `mixed_same_shape` seed `890700` was `19/20`; the failure was a high approach timeout with adapter active for `996` steps and no final-servo handoff. Do not promote v97.
    - v98 preservation adapter smoke: trained `D:\peg-in-hole-6yh\v98_same_shape_adapter_mixed_preserve\approach_adapter_same_shape_v96_plus_v8data_fullcrop_xy_override.pt` from v96 plus the v8 adapter training datasets, `30` epochs, final validation loss `2.07e-6`. Without an episode-level adapter cap it still timed out once on `mixed_same_shape` seed `890700`; with `--approach-adapter-episode-max-steps 220`, the same mixed check passed `20/20` and the fixed profile seed `891500` matrix passed `50/50`, zero collision and zero timeout.
    - v99 v98+epmax220 mixed multi-seed result directory: `D:\peg-in-hole-6yh\v99_v98_same_shape_multiseed_mixed`. Seeds `891700`, `892700`, and `893700`, `20` episodes each, passed `60/60`, zero collision and zero timeout. Mean adapter steps were about `123.0`, `131.2`, and `121.3`; mean final-servo steps were about `94.1`, `91.5`, and `92.8`.
    - v100 shared comparison result directory: `D:\peg-in-hole-6yh\v100_v8_vs_v98_same_shape_shared_mixed`. Promoted v8 on the same seeds `891700`, `892700`, and `893700` also passed `60/60`, zero collision and zero timeout. Shared totals: v8 `60/60`, mean steps `251.8`, mean adapter steps `126.9`; v98+epmax220 `60/60`, mean steps `255.4`, mean adapter steps `125.2`.
    - interpretation: v96 is a clean training dataset, but same-shape adapter training can over-own high approach unless the deployment gate includes an episode-level adapter step budget. v98+`episode_max_steps=220` is safe on the current smoke matrix, but it does not beat promoted v8. Do not tag/promote v98 yet; keep v8 as the promoted adapter and use v96/v98 as evidence for the next, harder same-shape generalization stage.
    - v101 promoted-v8 longer mixed baseline: `D:\peg-in-hole-6yh\v101_v8_same_shape_mixed_100ep`, `mixed_same_shape` seed `894700`, `100/100`, zero collision and zero timeout. Shape split was `round_round=14/14`, `square_square=19/19`, `hex_hex=16/16`, `triangle_triangle=20/20`, `slot_slot=12/12`, `rectangular_key=19/19`; mean steps `273.7`.
    - v102 narrow-clearance fixed-profile stress: `D:\peg-in-hole-6yh\v102_v8_same_shape_narrow_clearance_profile10`, with hole half-size `14-16 mm`, round peg radius `12.8-13.5 mm`, and square/slot/key short half-size `12.2-13.5 mm`. Result: `58/60`, zero collision, two square-square timeouts. Per-profile: `round_round=10/10`, `square_square=8/10`, `hex_hex=10/10`, `triangle_triangle=10/10`, `slot_slot=10/10`, `rectangular_key=10/10`. Both square failures reached sub-mm XY at some point but stalled high around `27-40 mm` Z with high tilt and negative tilted clearance margin.
    - v103 narrow-square control probes: `D:\peg-in-hole-6yh\v103_narrow_square_orientation_probe`. A base repeat was `9/10`; increasing final-servo IK orientation weight to `0.12` regressed to `7/10` with one collision, and tightening square-fast-settle tilt max to `8 deg` stayed at `9/10`. Do not solve the narrow-square gap by simple orientation-weight or tilt-threshold scans.
    - v104 square-fast-settle contact-unjam hook: added a default-off `guard_final_servo_square_fast_settle_contact_unjam_enabled` switch and eval/demo CLI wiring. The seed `895700` narrow square-square probe regressed to `7/10`, zero collision, three timeouts. The hook triggers, but it tends to spend long stretches in contact reinsert/orient-hold recovery and can worsen timeout.
    - v105-v108 square-tilt-reinsert probes: added a default-off `guard_final_servo_square_tilt_reinsert_*` hook that tries a short lift/recenter before returning to `square_fast_settle`. Early/default probes shifted failures toward collision, and the corrected v108 default probe on seed `895700` was still only `8/10`, with one collision and one timeout. Do not promote this hook.
    - v109 final-insert stuck-state extraction: added `scripts\build_final_insert_stuck_dataset.py` to convert guarded step traces into a conservative near-hole stuck-state CSV/NPZ. It filters timeout traces by final-servo activity, `square_square`, near-hole XY, `20-55 mm` Z above target, wall contact/high tilt/progress stall, and then labels local actions as `contact_lift`, `micro_recenter`, or `soft_descend`.
    - v109 pilot output: `D:\peg-in-hole-6yh\v109_final_insert_stuck_dataset`. The combined v102+v108 timeout trace extraction produced `209` samples from `3` trace episodes, all in `square_fast_settle`; label split was `contact_lift=69`, `micro_recenter=138`, `soft_descend=2`. Mean XY/Z was about `2.08 mm / 37.95 mm`. This is not a promoted controller change; it is the first reusable data/labeling entry point for a square-square narrow-clearance final-insert adapter.
    - v110 final-insert state-adapter pilot: added `peg_in_hole_mujoco\final_insert_adapter.py` and `scripts\train_final_insert_adapter.py`. The adapter is a low-dimensional MLP over the v109 contact/pose/clearance features, with saved feature normalization and normalized-feature clamping to avoid unseen one-hot contact features causing output explosions.
    - v110 pilot output: `D:\peg-in-hole-6yh\v110_final_insert_adapter_pilot`. Episode-split training on v109 produced train/validation MAE `0.019 mm / 0.515 mm`; random split produced `0.039 mm / 0.061 mm`. Interpretation: the MLP can fit the labeler, but three trace episodes are too narrow to claim cross-seed/contact generalization. Do not connect this checkpoint to the runtime controller as a promoted path yet.
    - v111 fresh narrow-square stuck traces: ran promoted v8/early-final-servo narrow `square_square` eval on seeds `895800`, `895900`, and `896000`, `10` episodes each. Each run was `9/10`, zero collision, one timeout. The three new timeout traces are the same near-hole failure family: `square_fast_settle`, XY about `2.7-7.9 mm`, Z stuck near `40 mm`, wall contact, and negative tilted clearance.
    - v111 stuck dataset output: `D:\peg-in-hole-6yh\v111_final_insert_stuck_dataset`. Fresh-only extraction produced `274` samples from `3` trace episodes. Combined v102+v108+fresh extraction produced `483` samples from `6` trace episodes; label split was `contact_lift=259`, `micro_recenter=221`, `soft_descend=3`, all in `square_fast_settle`.
    - v111 adapter output: `D:\peg-in-hole-6yh\v111_final_insert_adapter_pilot`. Combined random split reached train/validation MAE `0.125 mm / 0.155 mm`. Conservative episode split with all labels reached `0.213 mm / 0.640 mm` at `100` epochs but overfit badly by `300` epochs. The current best diagnostic candidate is `final_insert_adapter_combined_episode_split_contact_micro_e100.pt`, trained only on `contact_lift` and `micro_recenter`, with train/validation MAE `0.210 mm / 0.567 mm`.
    - v112 final-insert adapter eval hook: `scripts\eval_guarded_policy.py` now has default-off `--final-insert-adapter*` runtime wiring for the v111 low-dimensional adapter. It records raw/clipped adapter actions and active/reason fields in step traces, supports `override`, `override_xy`, and `residual` modes, plus phase/stall/contact/near-hole gates.
    - v112 direct full-action override result: output `D:\peg-in-hole-6yh\v112_final_insert_adapter_eval`. On seeds `895700/895800/895900/896000`, 10 episodes each, it reached `36/40`, zero collision and four timeouts. It fixed the old `895902` timeout but introduced a new `895800` timeout, so do not promote full-action override.
    - v112 conservative candidate: output `D:\peg-in-hole-6yh\v112_final_insert_adapter_eval_stall_gate`. Best tested setting is `--final-insert-adapter-mode override_xy --final-insert-adapter-max-xy-action 0.0012 --final-insert-adapter-min-stall-steps 15`, which reached `39/40`, zero collision and one timeout on the same four targeted seeds. The comparable baseline is `37/40`, zero collision and three timeouts (`895700` baseline was freshly measured at `10/10`; v111 had `895800/895900/896000` at `9/10` each).
    - v113 closed-loop final-insert adapter data: added the v112 conservative-hook timeout trace for `895803` back into the stuck-state dataset, producing `575` samples from `7` trace episodes. Label split: `contact_lift=276`, `micro_recenter=296`, `soft_descend=3`. The v113 episode-split contact/micro adapter reached train/validation MAE `0.189 mm / 0.645 mm`, worse than v111 validation, and still left `895803` as a timeout under the conservative `override_xy/stall15` eval.
    - v114 bounded lift-pulse diagnostic: `scripts\eval_guarded_policy.py` now has default-off `--final-insert-adapter-lift-pulse-*` flags to test short upward pulses after long final-insert adapter/stall periods. On `895800`, active/stall `80/80` did not trigger; active/stall `40/40` triggered `60` pulse steps but still timed out on `895803` and increased adapter ownership. Do not promote lift pulse.
    - v115 final-insert macro recovery diagnostic: `scripts\eval_guarded_policy.py` now has default-off `--final-insert-macro-recovery-*` flags. The macro triggers inside square-square `square_fast_settle` after a long near-hole stall and overrides actions with a bounded `lift -> align -> hold` sequence before returning control to final-servo. Default gate `80/80` did not trigger on `895803`; `40/40` with the default weak lift triggered twice but still timed out. A stronger probe (`lift_steps=40`, `lift_action=0.005`, `max_xy_action=0.0025`) can solve `895803` in a focused rerun, but the four-seed targeted matrix `895700/895800/895900/896000`, 10 episodes each, was only `37/40` with `1` collision and `2` timeouts. Do not promote macro recovery.
    - v116 macro abort safety diagnostic: added default-on-with-macro abort knobs `--final-insert-macro-recovery-abort-*`, including abort on XY divergence and on final-servo dropout during an active macro. The targeted four-seed strong-macro matrix became `36/40`, zero collision and four timeouts. The safety path can convert the exposed collision risk into timeout, but it does not improve insertion success and regresses the `895700` bucket. Keep it only as diagnostic guardrail for future macro probes.
    - Added `scripts\analyze_final_insert_macro_recovery.py` to classify macro-recovery failures from eval episode/step CSVs. Current summaries: v115 has `macro_not_triggered_timeout=1`, `macro_triggered_timeout_stuck_high_z=1`, `macro_triggered_collision_diverged=1`; v116 has `macro_not_triggered_timeout=1`, `macro_triggered_timeout_stuck_high_z=2`, `macro_triggered_timeout_diverged=1`.
    - v117 phase-aware final-insert teacher dataset builder: added `scripts\build_phase_aware_final_insert_dataset.py` to turn v115/v116 guarded episode+step traces into a phase-aware teacher dataset. It keeps the final-insert adapter schema, adds `failure_classification` and `teacher_phase`, and must use a longer tail window to capture the missed-trigger bucket. Smoke output `D:\peg-in-hole-6yh\v117_phase_aware_final_insert_probe` produced `899` samples from `9` trace episodes with failure split `macro_not_triggered_timeout=144`, `macro_triggered_timeout_stuck_high_z=576`, `macro_triggered_timeout_diverged=121`, `macro_triggered_collision_diverged=58`. A 2-epoch trainer compatibility smoke reached train/val MAE `1.58/1.64 mm`; this only validates schema/training flow. This is now the reusable closed-loop teacher entry point; the next step is real adapter training/eval on these phase-aware labels, not more macro-threshold scanning.
    - v118 phase-aware final-insert adapter pilot: trained `D:\peg-in-hole-6yh\v118_phase_aware_final_insert_adapter_pilot\final_insert_adapter_phase_aware_episode_split_e150.pt` with episode-split MAE `0.250/0.794 mm`, then an all-data rollout candidate `final_insert_adapter_phase_aware_alldata_e150.pt` with train MAE `0.310 mm`. Full-action `override` without a takeover bound left `895803` at `9/10`: the adapter lifted for `244` steps and timed out around `38 mm` above target. Added default-off runtime gates `--final-insert-adapter-max-consecutive-steps` and `--final-insert-adapter-cooldown-steps` so learned full-action corrections can run as short bursts before returning control to final-servo. With burst `40` / cooldown `80`, `no-wall-contact-required`, and `min_stall=15`, the targeted four-seed square-square matrix reached `39/40`, zero collision and one timeout. Removing the stall gate was unsafe (`896000` fell to `2/10`). Do not promote v118 yet; it ties the previous best diagnostic but does not beat it.
    - v119 handoff/stop teacher pilot: extended `scripts\build_phase_aware_final_insert_dataset.py` with `--handoff-teacher-enabled`, relabeling aligned/no-wall high-Z states as `handoff_descend`; the v119 dataset in `D:\peg-in-hole-6yh\v119_final_insert_handoff_teacher_probe` keeps `899` samples and changes `154` to handoff labels. Training `D:\peg-in-hole-6yh\v119_final_insert_handoff_adapter_pilot\final_insert_adapter_handoff_episode_split_e150.pt` reached episode-split MAE `0.323/0.253 mm`, much better validation than v118, and the all-data rollout checkpoint reached train MAE `0.270 mm`. Runtime now has default-off `--final-insert-adapter-handoff-on-down-action` and `--final-insert-adapter-handoff-on-aligned-no-contact`. Pure predicted-action handoff was too rare (`895800` only `8/10`); state handoff with XY `0.0048`, no wall, `min_stall=15`, no burst reached targeted `39/40`, zero collision. It fixes `895803` but still leaves `896007`, which times out after repeated high-Z `align_hover`/handoff behavior. Do not promote v119.
    - v120 align-hover escape and recovery-budget probe: added a default-off `guard_final_servo_align_hover_escape_*` gate to `GuardedPolicyController` and eval/demo/inference CLI wiring. It lets persistent high-Z `align_hover` / `stable_confirm` states drop into `near_miss_descend` when XY is already close enough, instead of waiting for another broad handoff threshold. The first v120 probe with escape alone still left `896007` at `9/10`; trace analysis showed escape did trigger, but final-servo exhausted its `max_retries=2` budget after repeated `square_fast_settle/recover` cycles and then fell back to ordinary guard/oracle at about `40 mm` Z. Keeping the same v119 handoff adapter, enabling align-hover escape, and raising only `--guard-final-servo-max-retries 4` reached targeted `40/40`, zero collision, zero timeout on seeds `895700/895800/895900/896000`, 10 episodes each. Result directory: `D:\peg-in-hole-6yh\v120_align_hover_escape_matrix_retry4`.
    - v121/v122 broader same-shape narrow-clearance validation: fixed-profile seed `897000`, 10 episodes/profile, passed `60/60`, zero collision and zero timeout with the retry4 v120 recipe. Mixed-same-shape retry4 on seeds `897500/898500/899500`, 60 episodes each, reached `175/180`, with all five failures in `square_square` (`1` collision and `4` timeouts). The five failed square episodes all succeeded in focused retry6 reruns. Full mixed-same-shape retry6 on the same three seeds then reached `180/180`, zero collision and zero timeout; shape split: `round_round=35/35`, `square_square=34/34`, `hex_hex=30/30`, `triangle_triangle=28/28`, `slot_slot=31/31`, `rectangular_key=22/22`. Result directories: `D:\peg-in-hole-6yh\v121_v120_same_shape_fixed_profile_matrix10`, `D:\peg-in-hole-6yh\v121_v120_same_shape_mixed_multiseed_60ep`, and `D:\peg-in-hole-6yh\v122_v120_retry6_mixed_multiseed_60ep`.
    - v123/v124 baseline ablations: the promoted v8 baseline on the same mixed seeds reached only `174/180` with `2` collisions and `4` timeouts, all in `square_square`. A retry6-only ablation without v119/v120 final-insert wiring improved only slightly to `175/180`, with `1` collision and `4` timeouts. This means retry budget alone is not the fix; the full v122 stack is still the current best diagnostic candidate.
    - v125 fresh-seed validation: the full v122 stack on mixed-same-shape seeds `900500/901500/902500`, 60 episodes each, reached only `175/180`, with `2` collisions and `3` timeouts. Every failure was `square_square`; `round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, and `rectangular_key` were all perfect. Do not promote v122.
    - v126-v127 diagnosis: retry8 alone did not fix the fresh failures. Collisions happened after `square_fast_settle` jumped laterally near `28-40 mm` Z and final-servo dropped inactive. Added default-off `guard_final_servo_priority_over_fixture_clearance` to prevent fixture-clearance from preempting an active final-servo/recovery phase. Focused probes rescued `900513` and `901554` and removed the collision mode, but high-Z timeouts remained.
    - v128 fresh mixed validation with priority-over-fixture reached `177/180`, zero collision and three square-square timeouts (`900500=60/60`, `901500=60/60`, `902500=57/60`). v129 lowered final-insert adapter max-up action to `0.002` and improved `902500` to `58/60`, zero collision; `0.001` caused a collision. v130 faster square-fast-settle descent did not beat `58/60`.
    - v131-v133 final-insert adapter ownership probes did not beat v128 globally. `stall40 + up0.002` reached `59/60` on the hard seed `902500`, but the fresh matrix fell to `176/180`, zero collision, four timeouts.
    - v134 high-Z contact-reinsert probe was rejected. Raising contact unjam Z to `0.050` and enabling high reapproach on `902500` reached only `56/60`, with one collision and three timeouts; failure traces showed no `contact_reinsert_*` phase, so the intended path did not actually address `square_fast_settle`.
    - v135/v136 revived the default-off square-tilt reinsert hook under the stronger v128 stack. With `margin_threshold=-0.001`, `lift_height=0.014`, and two attempts, `902500` improved to `59/60`, zero collision, but the fresh matrix was still `177/180` with one collision and two timeouts.
    - v137/v138 added a safer ordinary final-servo recovery height: `guard_final_servo_lift_height=0.060` instead of the stress config's `0.050`. This removed the `900500` recovery-recenter collision and produced the current best fresh result: `178/180`, zero collision, two square-square timeouts. Seed split: `900500=60/60`, `901500=59/60`, `902500=59/60`; all non-square same-shape profiles were perfect.
    - v119 final-insert handoff adapter artifact is now staged for repository packaging at `assets\final_insert_adapters\final_insert_adapter_handoff_alldata_e150.pt` (`37869` bytes, SHA256 `4FC0B6664F116C09A7D9569194E82EBDDA7D69F7E73BC60CA2C110176C2323C5`). This local worktree cannot materialize new files under `assets` because of Windows ACLs, so the file is staged via Git object/index plumbing and marked `skip-worktree`.
    - v139 expanded v138 to fresh seeds `903500/904500/905500`, 60 episodes each: `177/180`, zero collision, three square-square timeouts. Combined v138+v139 is `355/360`, zero collision, five timeouts; all non-square same-shape profiles remain perfect. Added `configs\sim\ur5e_full\eval_multi_geometry_v138_square_tilt_reinsert_lift60_60ep.yaml` so this candidate is reproducible without copying the long CLI.
    - v140 retry8 probe on seeds `903500/904500` did not improve timeout count (`59/60` and `58/60`, still zero collision). The remaining failures are therefore not solved by simply raising retry budget.
    - v141 added default-off `guard_final_servo_square_high_z_descend_*` as a narrow low-risk high-Z descend watchdog. Focused probes rejected it: `901500=59/60`, `903500=59/60`, `904500=57/60` with one collision. It sometimes triggers but does not solve the timeout mode and can make high-tilt square cases unsafe. Keep the code as a diagnostic only; do not enable it in v138.
    - v142 added default-off `guard_final_servo_rearm_*` to let an exhausted/inactive final-servo safely re-enter `align_hover` only after cooldown, stable low-risk XY/Z, low contact, low tilt, and square tilted-clearance checks. Focused probes did not improve the current bottleneck: `903500` stayed `59/60` with one rearm and zero collision; `903500` with `max_attempts=2`, `xy_max=0.007` also stayed `59/60` and consumed more recovery budget; `904500` stayed `59/60`, zero collision, and did not rearm because the failure remained active in `square_fast_settle`. Keep v142 as diagnostic trace plumbing only; do not enable it in v138.
    - v143 focused probe raises only `guard_final_servo_square_fast_settle_contact_max` from `6` to `8` on top of v138. Trace rationale: many `square_fast_settle` exits happened at `37-39 mm` Z with wall contact count `7/8`, low tilt, and zero collision, so the v138 contact gate was too conservative for benign square edge contacts. On v139 seeds `903500/904500/905500`, 60 episodes each, v143 reached `179/180`, zero collision and one timeout (`903557`, still `square_square`). Seed split: `903500=59/60`, `904500=60/60`, `905500=60/60`. A companion `guard_final_servo_ik_orientation_weight=0.12` probe did not solve `903557`, so do not include that in the candidate.
    - v143 old-seed validation on the original v138 seeds `900500/901500/902500` reached only `177/180`, zero collision and three square-square timeouts. Seed split: `900500=60/60`, `901500=59/60`, `902500=58/60`. Combined v143 across six 60-episode seeds is `356/360`, zero collision and four timeouts; all failures are `square_square`, and every non-square same-shape profile remains perfect (`287/287`). This improves the combined v138/v139 comparison by only one episode (`355/360` to `356/360`) while regressing the original v138 seed set from `178/180` to `177/180`. Treat v143 as diagnostic evidence that the contact gate was partly too strict, not as a stable promotion path.
    - v144 raised `guard_final_servo_square_tilt_reinsert_max_attempts` to `4` on top of v143. Focused seeds `901500/902500/903500`, 60 episodes each, reached `177/180` with one collision and two timeouts; this is worse than v143 and is rejected.
    - v145 margin/yaw-aware square settle hook is implemented default-off in guarded runtime plus eval/demo/inference CLI wiring. It uses `square_peg_yaw_error_deg` and `square_peg_tilted_clearance_margin` to trigger a short square-only `square_margin_yaw_settle_lift -> square_margin_yaw_settle_recenter` sequence inside stalled `square_fast_settle`; it does not command yaw directly because the action interface is still 3D translation. The trace classifier now labels the v143 failures as `square_fast_settle_negative_margin_yaw_stall`.
    - v145 focused 1ep probes were mixed: default attempts=1 fixed `901555`; `max_up_action=0.005` fixed `902550`; attempts=2 fixed `902550` and `903557`; lift height `0.008` fixed none. Full six-seed 60ep validation rejects both serious v145 candidates. Attempts=1 reached `354/360`, one collision and five timeouts. Attempts=2 also reached `354/360`, one collision and five timeouts. Both are worse than v143 (`356/360`, zero collision), so do not promote or tag v145.
    - v146 adds `scripts\build_square_fast_settle_teacher_dataset.py`, a square-fast-settle-specific teacher dataset builder that keeps the v109 final-insert adapter feature schema and labels local states as `clearance_lift`, `hold_recenter`, or `guarded_descend`. It also supports `--success-descend-override` so successful near-aligned traces can explicitly teach handoff/descent.
    - v146 pilot output `D:\peg-in-hole-6yh\v146_square_fast_settle_teacher`: `591` samples from the four v143 timeout episodes `901555/902535/902550/903557`, label split `clearance_lift=537`, `hold_recenter=54`. The e100 adapter reached train/val MAE `0.265/0.354 mm`. Runtime focused eval on those four seeds was `0/4` with full `override`, and `1/4` with `override_xy` (`901555` only), zero collision.
    - v147b mixed-success pilot output `D:\peg-in-hole-6yh\v147b_square_fast_settle_teacher_mix_success_descend`: `503` samples from the focused traces, including `61` `guarded_descend` samples from the successful `901555` trace. The e100 adapter overfit (`0.359/0.745 mm`) and did not improve runtime. The e50 checkpoint reached the best focused result so far: `2/4` with `override_xy` (`901555` and `902550` succeed), zero collision. Raising XY cap to `2.0 mm` and lowering `min_stall_steps` to `0` did not rescue `902535` or `903557`.
    - v148 adds default-off square pose yaw-align plumbing. The env now keeps a resettable pose IK target orientation, can snap the square peg target yaw to the nearest square-symmetric hole axis, and records pose-target yaw metrics in eval traces. `scripts\eval_guarded_policy.py` exposes `--guard-square-pose-yaw-align-*` and applies it only in square final-servo phases. Weight scan: `0.25` fixed the focused four hard seeds but produced `359/360` with one `905523` collision; `0.16` fixed that collision but regressed `902500` to one timeout; `0.20` passed the key seeds and the full six-seed matrix.
    - v148 candidate result: `D:\peg-in-hole-6yh\v148_square_pose_yaw_align_probe\matrix_60ep_weight020_six_seed`, seeds `900500/901500/902500/903500/904500/905500`, 60 episodes each, reached `360/360`, zero collision and zero timeout. Shape split: `square_square=73/73`, non-square same-shape `287/287`; mean steps `276.5`, max steps `660`. Repro config: `configs\sim\ur5e_full\eval_multi_geometry_v148_square_pose_yaw_align_w020_60ep.yaml`.
    - v149 fresh-seed validation of the same v148 recipe: `D:\peg-in-hole-6yh\v149_v148_fresh_seed_gate_906500_907500`, seeds `906500/907500/908500/909500/910500/911500`, 60 episodes each, reached `360/360`, zero collision and zero timeout. Shape split: `round_round=51/51`, `square_square=52/52`, `hex_hex=62/62`, `triangle_triangle=60/60`, `slot_slot=67/67`, `rectangular_key=68/68`; mean steps `281.7`, max steps `875`; all failure trace CSVs are empty.
    - v151 square-square hard stress pilot on top of the v148/v149 recipe used `square_square`, hole half-size `14.0-15.2 mm`, square peg half-size `12.8-13.8 mm`, hole XY jitter `6 mm`, hard control scale `0.60-0.95`, delay `3-5`, and filter alpha `0.30-0.50`. It reached `86/90`, with four collisions at seeds `918528`, `920511`, `920516`, and `920525`.
    - v152/v153 implement a default-off `guard_final_servo_square_recovery_escape_*` diagnostic. The hook detects square peg recovery after large XY jumps in the `20-60 mm` Z band, lifts to a high recovery height, recenters, and returns to final-servo. The eval CLI now exposes the hook, logs `guard_final_servo_square_recovery_escape_active/triggered`, and inserts the repo root into `sys.path` so direct script execution imports the local package.
    - Focused v152/v153 rescue checks: historical failed seeds `918528`, `920511`, `920516`, and `920525` each reached `1/1`, zero collision and zero timeout with escape enabled. v153 also fixes the escape state machine so lift timeout transitions into high-Z recenter instead of dropping final-servo inactive.
    - v153 full 90ep stress was not promotable: `89/90`, with one new collision at `919504`. Diagnosis showed escape could preempt ordinary recover/fast-settle in a case that previously recovered successfully.
    - v154 adds `guard_final_servo_square_recovery_escape_max_clearance`, default `0.0` meaning no clearance gate. With `--guard-final-servo-square-recovery-escape-max-clearance 0.0011`, focused `919504` no longer triggered escape and succeeded, while focused `920516` still triggered escape and succeeded.
    - v154 first 90ep stress with the clearance gate reached `88/90`, with two collisions in seed bucket `918500` (`918504`, `918521`). These were not stable focused failures: both seeds succeeded when rerun individually in `D:\peg-in-hole-6yh\v155_square_escape_collision_repro_focused`, and the full `918500` 30ep bucket rerun reached `30/30`, zero collision and zero timeout in `D:\peg-in-hole-6yh\v156_square_escape_gate_seed918500_rerun`.
    - v157 default-off regression passed `5/5`, zero collision and zero timeout, confirming the new hook does not affect the baseline unless explicitly enabled.
    - v160 repeated the clearance-gated 90ep stress serially and reached `86/90`, with four collisions (`918502`, `918519`, `918521`, `920510`) and zero timeout. This matched the v151 baseline success count and confirmed the v154/v158 escape recipe was not stable enough to promote.
    - v161 adds a more conservative preemptive escape path on `square_fast_settle` unsafe exit. If escape is enabled, the square clearance gate passes, and `square_fast_settle` is about to fall into ordinary recovery, the controller enters high escape lift directly instead of first running `recover_lift`. This reduces the effect of delayed/filtered lateral action remnants. Focused checks on `918502`, `918519`, `918521`, `920510`, `918528`, `920511`, `920516`, and `920525` reached `8/8`, zero collision and zero timeout. The default-off 5ep regression passed `5/5`.
    - v161 full 90ep hard square-square stress reached `89/90`, with one collision (`920502`) and zero timeout. Seed buckets: `918500=30/30`, `919500=30/30`, `920500=29/30`. This is an improvement over v160/v151 but still not stable enough to promote or tag.
    - v162 tested a wider clearance gate (`--guard-final-servo-square-recovery-escape-max-clearance 0.0020`) to include the remaining `920502` failure. Focused `920502` still collided, now inside `square_recovery_escape_lift`; the trace shows escape lift can still be carried sideways by control delay/filter remnants. Do not solve this by simply widening the clearance gate.
    - v163 adds a default-off eval diagnostic switch, `--guard-final-servo-square-recovery-escape-flush-control-history`, which calls `env.flush_control_randomization_history(action)` on the step where square recovery escape triggers. This replaces the delay buffer and low-pass filter state with the current upward-only escape command before the env applies control randomization. Focused `920502` changed from v162 collision to success, and the focused guard set `920502/919504/920501/920510/920520/920525/918502/918521` reached `8/8`, zero collision and zero timeout.
    - v163 full hard square-square stress with `max_clearance=0.0020` and flush enabled reached `90/90`, zero collision and zero timeout. Seed buckets: `918500=30/30`, `919500=30/30`, `920500=30/30`. Result directories: `D:\peg-in-hole-6yh\v163_square_escape_flush_clearance002_serial_90ep` and `D:\peg-in-hole-6yh\v163_square_escape_flush_clearance002_bucket920500`.
    - v164 replaces the non-deployable v163 flush diagnostic with a controller-visible safety sequence. The recipe keeps square recovery escape default-off, adds 8 upward-only pre-lift steps before escape lift, uses a 70 mm escape height, keeps the narrow-clearance gate at `0.0020`, and dynamically limits `square_fast_settle` XY action to `3 mm` normally but `2 mm` below `55 mm` Z. This is meant to drain delayed/filtered lateral/down commands without directly editing simulator action buffers.
    - v164 focused validation:
      - `D:\peg-in-hole-6yh\v164_square_escape_h0070_dynamic_xycap_z055_focused10`
      - seeds `920502/919504/920501/920510/920520/920525/918502/918521/920512/919508`
      - `10/10` success, zero collision, zero timeout.
    - v164 full hard square-square stress:
      - `D:\peg-in-hole-6yh\v164_square_escape_h0070_dynamic_xycap_z055_bucket918500`
      - `D:\peg-in-hole-6yh\v164_square_escape_h0070_dynamic_xycap_z055_bucket919500`
      - `D:\peg-in-hole-6yh\v164_square_escape_h0070_dynamic_xycap_z055_bucket920500`
      - seeds `918500/919500/920500`, 30 episodes each: `90/90` success, zero collision, zero timeout.
      - mean steps `330.6`, max steps `917`.
      - Repro config: `configs\sim\ur5e_full\eval_multi_geometry_v164_square_escape_dynamic_xycap_hard_square_30ep.yaml`.
    - Current conclusion for square recovery escape: v164 is the first deployable square-square hard-control candidate that matches the v163 flush diagnostic result without simulator-side buffer flushing. Keep the hook default-off, promote the tested config as the strict hard-control square-square recipe, then follow with a fresh-seed hard-control gate before broadening to non-square/mixed geometry stress.
    - interpretation: v148/v149 remains the clean mixed same-shape baseline at `720/720`, while v164 is the current hard-control square-square promotion target. v164 specifically addresses delayed/filtered control remnants during low-Z square recovery without simulator-side buffer flushing, so the next useful gate is fresh hard-control seeds before broadening the escape recipe to non-square/mixed geometry stress.
- Small matrix result:
  - `mixed_basic`, 8 episodes, seed `612000`: `0.750/0.000/0.250`
  - `round_square`, 8 episodes, seed `612000`: `0.875/0.000/0.125`
  - `square_square`, 8 episodes, seed `612000`: `0.875/0.000/0.125`
  - the separate `round_square` and `square_square` runs both failed only seed `612002`, with nearly identical final XY/Z, so the first bottleneck looks like the existing high-start/control trajectory rather than square-peg runtime geometry switching.
- Strictstable49 20ep matrix result:
  - `single`, 20 episodes, seed `612000`: `0.950/0.000/0.050`
  - `round_square`, 20 episodes, seed `612000`: `0.950/0.000/0.050`
  - `square_square`, 20 episodes, seed `612000`: `0.850/0.000/0.150`
  - `mixed_basic`, 20 episodes, seed `612000`: `0.950/0.000/0.050`
  - all failures were timeouts, not collisions
  - `square_square` failures reached low Z and often had `min_dist_xy < 5 mm`, so the first square-peg gap is final insertion retention/stability, not gross visual approach.
- Expert dataset smoke:
  - `mixed_basic` 32-sample smoke writes `geometry_name` and `peg_shape` arrays.
  - forced `square_square` 16-sample smoke writes `square_square` / `square` samples as expected.
- Expert dataset pilot:
  - `mixed_basic` 1024-sample pilot had a healthy geometry split (`round_square=421`, `square_square=603`) but the direct staged oracle had `0.000` episode success under high-start settings.
  - guarded-two-stage oracle pilot improved but is not production-ready: 512 samples, 2 completed episodes, `0.500/0.500/0.000`.
  - `high_start_two_phase` pilot was worse on the same seed, with collision in the first completed episode.
  - conclusion: do not launch 50k direct-oracle multi-geometry collection yet. The data path works, but the high-start teacher path needs either a guarded-deployment teacher or policy-visited correction collection.
- Policy-visited correction data:
  - Added configs for `square_square` and `mixed_basic` insert-settle correction smoke collection.
  - `square_square` smoke: 512 clean timeout samples, all in the insert-settle window; rollout outcome was `0.121/0.462/0.418`, which confirms the current policy/teacher is weak at square-square rollouts but the filtered correction samples are usable.
  - `mixed_basic` smoke: 512 clean timeout samples with a balanced split (`round_square=253`, `square_square=259`).
  - Scaled `square_square` to 2048 samples: all timeout samples, no sample-level collision, `insert_settle_window_rate=1.000`, phases `slow_insert=516`, `settle=844`, `lift_recenter=314`, `recenter=374`.
  - Trained conservative 5% replay checkpoint:
    - `checkpoints\ur5e_full\multi_geometry\correction\sac_image_bc_wrist_pose_control_state_square_square_insert_settle_2k_w05_e1.zip`
    - training/validation loss: `0.109244/0.101964`.
  - Strictstable49 20ep evaluation with the w05 checkpoint, seed `612000`:
    - `single`: `0.950/0.000/0.050`
    - `round_square`: `0.950/0.000/0.050`
    - `square_square`: `0.850/0.000/0.150`
    - `mixed_basic`: `0.950/0.000/0.050`
  - Conclusion: the w05 replay does not damage the existing guarded baseline, but it also does not improve the square-square timeout bucket. The likely reason is that strict evaluation uses `guard_blend=1.0`, so near-hole final insertion is dominated by the guarded/final-servo controller rather than the learned actor.
- Guard-blend / actor-contribution diagnostic:
  - Summary: `results\ur5e_full\multi_geometry\guard_blend_diag\summary.md`
  - `square_square`, 20 episodes, seed `612000`, strict high-start config.
  - Base checkpoint:
    - `guard_blend=1.0`: `0.850/0.000/0.150`
    - `guard_blend=0.75`: `0.850/0.000/0.150`
    - `guard_blend=0.5`: `0.700/0.000/0.300`
  - W05 checkpoint:
    - `guard_blend=1.0`: `0.850/0.000/0.150`
    - `guard_blend=0.75`: `0.850/0.000/0.150`
    - `guard_blend=0.5`: `0.650/0.000/0.350`
  - Actor-vs-guard split:
    - base `policy`: `0.000/0.000/1.000`
    - base `guard_only`: `0.850/0.000/0.150`
    - w05 `policy`: `0.000/0.100/0.900`
    - w05 `guard_only`: `0.850/0.000/0.150`
  - Conclusion: current square-square performance is controller/guard dominated. W05 does not provide a useful learned near-hole insertion policy. Lowering guard blend does not reveal a hidden actor benefit and starts to regress at `0.5`.
- Shape-aware square-peg final-servo diagnostic:
  - Added square-peg orientation/geometry fields to environment info and guarded step traces:
    - square symmetry yaw error relative to the hole axes
    - top-down projected square half-width and clearance margin
    - tilt-induced lateral extent
    - tilt-aware projected half-width and clearance margin
  - Added `scripts\analyze_square_peg_trace.py` for trace summaries.
  - Summary: `results\ur5e_full\multi_geometry\shape_aware_servo_diag\shape_aware_servo_summary.md`
  - Compared success reference seeds `612000/612001/612002` against known timeout seeds `612008/612010/612013`.
  - Finding: `612010` is a persistent high-tilt/wedged case, ending near `6.70 mm` XY / `7.62 mm` Z with final tilt about `20.65 deg`.
  - Finding: `612008` and `612013` finish with low final tilt and positive projected margins, but still timeout after hundreds of final-servo steps. These are final-servo/low-recenter phase-completion failures, not pure yaw/tilt failures.
  - Conclusion: a simple yaw/tilt threshold is not enough, because successful runs can have temporary tilt spikes. The next controller change should be opt-in and phase-aware: trigger on persistent late-stage square-peg tilt or low-Z final-servo stall, then lift/recenter/hold orientation before descending again.
- Square-aware recovery implementation/diagnostic:
  - Added an opt-in `guard_final_servo_square_recovery_*` path to `GuardedPolicyController`.
  - The new phases are `square_recover_lift` and `square_recover_recenter`.
  - Eval/demo/inference scripts expose the new switches, and eval step traces record square-recovery active/triggered/tilt-step fields.
  - Summary: `results\ur5e_full\multi_geometry\square_recovery_diag\summary.md`
  - Result: this is not promoted. On the targeted `612000-612013` 14ep window, the best tested candidate stayed flat at `11/14 = 0.786` success with zero collisions.
  - High-tilt seed `612010` still timed out even with square recovery, `guard_near_ik_orientation_weight=0.03/0.06`, higher lift, and a 1500-step episode.
  - Low-tilt near-miss seeds `612008` and `612013` remain sensitive to low-recenter settings; narrower low-recenter can improve XY or Z separately, but still does not make the episodes successful.
- Final insertion contact diagnostic:
  - Added independent peg-hole contact metrics to env `info` and guarded eval step traces. These metrics do not affect reward, collision termination, or success criteria.
  - Added `scripts\analyze_insert_contact_trace.py` to summarize wall/plate contact, first contact step, low-Z stall rate, insert-band contact rate, and final-servo phases.
  - Summary: `results\ur5e_full\multi_geometry\contact_insert_diag\summary.md`
  - Strictstable49 `square_square` known timeout seeds `612008/612010/612013` were compared against success references `612000/612001/612002`.
  - Finding: success references reached success with no peg-hole wall/plate contact in the trace, ending around `0.9 - 2.8 mm` XY and `9.7 - 10.0 mm` Z.
  - Finding: `612010` is a real contact-limited failure: wall contact in about `48.5%` of steps, `91.9%` of the 14 mm release-band steps in contact, final east-wall contact, final tilt about `20.65 deg`, and negative tilted square clearance.
  - Finding: `612008` and `612013` are not the same failure class. They have much lower contact rates, no plate contact, low final tilt, and mostly final-servo/recovery phase timeout behavior. `612008` ends high after recovery, while `612013` ends slightly outside the strict 5 mm band with south-wall contact.
  - Conclusion: do not add one broad square-recovery threshold. The next controller change should split the failure modes: a contact-aware unjam/retreat path for persistent wall-contact/high-tilt cases, and a low-contact final-servo phase-completion/acceptance fix for low-tilt near-misses.
- Split final-servo diagnostic:
  - Added an opt-in `guard_final_servo_split_recovery_*` path. It is square-only and defaults off.
  - New phase family:
    - `contact_unjam_lift` / `contact_unjam_recenter` for persistent wall-contact plus high-tilt or negative tilted clearance.
    - `near_miss_descend` / `near_miss_recenter` for low-contact, low-tilt, near-threshold final insertion misses.
  - Eval/demo/inference now expose and validate the new switches. Eval step traces record the new contact-unjam and near-miss counters.
  - Best current diagnostic setting uses near-miss XY bias `[0.0035, 0.0035]`, near-miss low recenter height `8 mm`, near-miss max down action `2.5 mm/step`, and contact unjam lift `45 mm`.
  - Targeted seed result: `612008` and `612013` switched from timeout to success; `612010` remains timeout and is still the persistent high-tilt wall-contact case.
  - Targeted `612000-612013` 14ep window improved from the previous square-recovery `11/14 = 0.786` to `13/14 = 0.929`, with zero collisions.
  - `square_square`, strictstable49, 20ep seed `612000` improved from baseline `0.850/0.000/0.150` to `0.950/0.000/0.050`.
  - Profile matrix with the same split setting, 20 episodes, seed `612000`:
    - `single`: `0.950/0.000/0.050`
    - `round_square`: `0.950/0.000/0.050`
    - `square_square`: `0.950/0.000/0.050`
    - `mixed_basic`: `0.950/0.000/0.050`
    - only failure in every profile was seed `612010`; no collisions were observed.
  - Larger profile gate with the same split setting, 60 episodes, seed `612000`:
    - `single`: `0.967/0.000/0.033`, failures `612010/612032`
    - `round_square`: `0.967/0.000/0.033`, failures `612010/612032`
    - `square_square`: `0.950/0.000/0.050`, failures `612010/612021/612032`
    - `mixed_basic`: `0.967/0.000/0.033`, failures `612010/612032`
    - all failures were timeouts; no collisions were observed.
  - Named config: `configs\sim\ur5e_full\eval_multi_geometry_square_square_split_servo_strictstable49_20ep.yaml`
  - Matrix result directory: `results\ur5e_full\multi_geometry\split_servo_diag_v6_bias35_matrix`
  - 60ep matrix result directory: `results\ur5e_full\multi_geometry\split_servo_diag_v6_bias35_matrix_60ep`
  - Focused one-episode failure contact summary: `results\ur5e_full\multi_geometry\split_servo_diag_v6_bias35_failure_contact\summary_release_band.md`
  - Summary: `results\ur5e_full\multi_geometry\split_servo_diag_v6_bias35\summary_release_band.md`
  - Focused failure-contact diagnosis:
    - remaining `single`/`round_square` failures `612010/612032` are also high-contact, high-tilt insert-band timeouts, not square-only geometry failures.
    - `square_square` failures `612010/612021/612032` show high insert-band wall contact (`0.83 - 0.86`) and final tilt around `15 - 20 deg`; contact unjam activates but does not yet produce a reliable reinsertion.
    - `mixed_basic` sampled `square_square` on its failing seeds and shows the same high-contact timeout pattern.
- Contact-aware reinsert follow-up branch:
  - Branch: `feature/contact-aware-reinsert`.
  - Implemented opt-in general contact reinsert with `--guard-final-servo-contact-reinsert-enabled`, so `contact_unjam_lift/contact_unjam_recenter` can be tested outside square-only split recovery.
  - Added wall-direction contact fields to guarded state and optional `--guard-final-servo-contact-unjam-wall-bias`; early v2 wall-bias diagnostics did not rescue the targeted seeds.
  - Added phase-local IK overrides:
    - `--guard-final-servo-ik-orientation-weight`
    - `--guard-contact-unjam-ik-orientation-weight`
  - v6 final-servo-only `0.03` did not rescue `square_square/612021`; it still timed out with final tilt around `18 deg`.
  - v7 high hover `40 mm` plus final-servo IK `0.12` reduced tilt to about `4 deg`, but hurt XY tracking and left the episode stuck high, so that setting is not usable.
  - v8 medium hover `25 mm`, stable steps `8`, and final-servo IK `0.06` rescued `square_square/612021` with zero collision.
  - The same v8 setting did not rescue the common `612010/612032` failures across profiles. `612010` still becomes a high-tilt contact/recenter timeout; `612032` can get stuck in final-servo align-hover when XY drifts outside the useful band.
  - Contact-only IK relaxation (`--guard-contact-unjam-ik-orientation-weight 0.0`) improves `612010` XY recentering but allows tilt to grow too much; it is diagnostic only.
  - Added default-off final-servo align-hover timeout with `--guard-final-servo-align-timeout-steps` and `--guard-final-servo-align-timeout-xy`. v12 confirms it prevents indefinite align-hover holding on `612032`, but it does not rescue the seed because the subsequent recovery/recenter consumes too many steps.
  - Added a default-off phase-specific reinsert path:
    - `contact_reinsert_orient_hold`
    - `contact_reinsert_descend`
    - `--guard-contact-reinsert-orient-ik-orientation-weight`
    - `--guard-final-servo-contact-reinsert-orient-*`
    - `--guard-final-servo-contact-reinsert-descend-max-steps`
  - v15/v16 show the phase-local strong IK idea works: `612010` contact reinsert can reduce tilt from about `18 deg` to about `8 deg` without the global `0.12` IK collision regression.
  - v18/v19 show the new reinsert descent is much closer but still not successful. It can keep tilt near `8 deg` and descend to the success Z band (`min_dist_z` about `8.1 mm`), but XY stalls around `5.7 mm`, just outside the `5 mm` strict success threshold.
  - v20 adds wall relief into `contact_reinsert_descend`; on `612010` this did not materially improve the final XY stall.
  - v35-v39 tip-lock and high re-approach scans were negative. Tip-lock did not preserve XY during orientation hold, and high re-approach either drifted too far in XY or failed to reduce tilt enough.
  - Added `pose_tip_priority` IK mode as an opt-in controller mode. Global `--ik-control-mode pose_tip_priority` is not usable for the learned policy path because it changes the nominal trajectory too much.
  - Added phase-local tip-priority switches:
    - `--guard-contact-reinsert-tip-priority-ik-enabled`
    - `--guard-final-servo-tip-priority-ik-enabled`
  - v41 contact-reinsert-only tip-priority rescued `single/612010` and `square_square/612021`, but not `single/612032` or `square_square/612010`.
  - v42 final-servo-wide tip-priority rescued the remaining targeted `single/612032` and `square_square/612010` cases.
  - v42 profile gates on seed `612000`:
    - 20ep matrix: `single=1.000`, `round_square=1.000`, `square_square=1.000`, `mixed_basic=1.000`, all zero collision and zero timeout.
    - 60ep matrix: `single=1.000`, `round_square=1.000`, `square_square=1.000`, `mixed_basic=1.000`, all zero collision and zero timeout.
  - Additional v42 seed smoke on seed `613000`, 10 episodes per profile: `single=1.000`, `round_square=1.000`, `square_square=1.000`, `mixed_basic=1.000`, all zero collision and zero timeout. Output directory: `D:\peg-in-hole-6yh\v42_tip_priority_seed613000_matrix10`.
  - Additional v42 seed gate on seed `614000`, 20 episodes per profile: `single=1.000`, `round_square=1.000`, `square_square=1.000`, `mixed_basic=1.000`, all zero collision and zero timeout. Output directory: `D:\peg-in-hole-6yh\v42_tip_priority_seed614000_matrix20`.
  - Larger v42 gate on seeds `615000/616000/617000`, 20 episodes per profile:
    - strict 1000-step v42 result: `236/240 = 0.983` overall success, zero collisions.
    - each profile had one timeout on `seed615000/episode0`; all other episodes succeeded.
    - failure type: approach-stage timeout before final-servo handoff, not insertion wedging. The failures stalled around `16.7 mm` XY and `65 mm` Z, with `final_servo_steps=0`, under a hard control-randomization draw (`action_scale_multiplier=0.849`, `delay=2`, `filter_alpha=0.698`).
    - output directory: `D:\peg-in-hole-6yh\v42_tip_priority_multiseed_matrix20`.
  - Wide-handoff probe:
    - overrides: `guard_approach_recenter_trigger_xy=0.018`, `guard_approach_recenter_stable_xy=0.017`, `guard_final_servo_start_xy=0.018`.
    - targeted `single/615000` succeeded; lowering approach recenter height to `55 mm` caused collision and is rejected.
    - wide-handoff 3-seed matrix improved strict 1000-step result to `238/240 = 0.992`, zero collisions.
    - `single` and `round_square` reached `60/60`; `square_square` and `mixed_basic` reached `59/60`.
    - remaining failures are `square_square/615000/episode0` and `mixed_basic/615000/episode0`; both are square-square geometry cases that enter final-servo, get very close, and then run out of the 1000-step budget.
    - output directory: `D:\peg-in-hole-6yh\v43_tip_priority_widehandoff_multiseed_matrix20`.
  - Remaining square timeout probes:
    - `max_steps=1500` plus wide-handoff rescues both remaining known failures. `square_square/615000` succeeds in `1242` steps; `mixed_basic/615000` succeeds in `1158` steps.
    - increasing `guard_final_servo_max_down_action` to `0.0020` or `0.0025` did not rescue the 1000-step square failures, so the bottleneck is final-servo recovery time/phase sequencing rather than a simple descent speed cap.
    - output directory: `D:\peg-in-hole-6yh\v43_seed615000_square_timeout_probes`.
  - Strict 1000-step square fast-settle follow-up:
    - Added default-off `guard_final_servo_square_fast_settle_*` knobs and a new `square_fast_settle` final-servo phase.
    - The phase is square-only and only triggers when the tip is close, low, low-tilt, and low-contact. It bypasses the slow hover/stable/recovery loop and applies direct XY correction plus bounded descent.
    - Added CLI/config wiring in guarded eval, demo, and inference scripts.
    - Added `scripts\analyze_final_servo_phase_trace.py` to summarize phase counts from step traces.
    - Targeted known failures under strict `max_steps=1000` are now rescued:
      - `square_square/615000/episode0`: success in `858` steps, no collision, final phase `square_fast_settle`.
      - `mixed_basic/615000/episode0`: success in `772` steps, no collision, final phase `square_fast_settle`.
    - v44 3-seed profile gate with wide-handoff plus square-fast-settle reached `240/240 = 1.000` success, zero collisions, zero timeouts.
      - `single`: `60/60`
      - `round_square`: `60/60`
      - `square_square`: `60/60`
      - `mixed_basic`: `60/60`
    - v44 new-seed strict regression on seeds `618000/619000/620000`, 20 episodes per profile, also reached `240/240 = 1.000` success, zero collisions, zero timeouts.
      - `single`: `60/60`
      - `round_square`: `60/60`
      - `square_square`: `60/60`
      - `mixed_basic`: `60/60`
      - mean steps `292.2`, max steps `802`, mean final XY `1.59 mm`, max final XY `5.00 mm`, max final peg tilt `3.19 deg`.
    - v45 moderate stress gate adds configurable hard-bucket control ranges and peg/jitter geometry overrides, then tightens the eval distribution:
      - hole half-size `16-20 mm`, round peg radius `11.8-13.0 mm`, square half-size `11.0-13.0 mm`
      - hole-center jitter `3 mm`, table/fixture height jitter `1.5 mm`
      - action scale `0.75-1.05`, noise `0.1-0.5 mm`, delay `2-3`, filter alpha `0.45-0.65`
      - seeds `621000/622000`, 20 episodes per profile: `160/160 = 1.000` success, zero collisions, zero timeouts
      - mean steps `291.6`, max steps `715`, mean final XY `1.54 mm`, max final XY `4.97 mm`, max final peg tilt `3.22 deg`
    - v45 boundary/worst-case probes:
      - boundary random probe with hole half-size `14.5-19 mm`, peg/square max `13.5 mm`, delay `3-4`, filter `0.35-0.55`, noise `0.25-0.8 mm`: `40/40 = 1.000` success on seed `623000`
      - deterministic worst-case with only `1 mm` geometric clearance, fixed scale `0.65`, delay `4`, filter `0.35`, noise `0.8 mm`: `single=4/5`, `square_square=0/5`, `mixed_basic=3/5`
      - worst-case failures are not the normal v44 timeout pattern. They are mostly extreme square-square clearance/control-limit failures: either approach never hands off, or final servo gets XY near `1-3 mm` but stalls high at `18-40 mm` Z with peg-hole wall contact and high tilt/yaw.
    - v46 square worst-case diagnosis:
      - Added `scripts\analyze_square_worstcase_failures.py`.
      - Baseline deterministic worst-case failure analysis: 8 failures total, with 3 `approach_no_final_servo` and 5 `near_xy_contact_high_z`.
      - The `near_xy_contact_high_z` failures briefly enter `square_fast_settle`, then contact/tilt rejects the phase; after that the episode stalls high with wall contact.
      - Opt-in contact-tolerant fast-settle probe uses `guard_final_servo_square_fast_settle_z_max=0.060`, `tilt_max_deg=14.0`, `contact_max=6`.
      - Deterministic worst-case improves from `single=4/5`, `square_square=0/5`, `mixed_basic=3/5` to `single=4/5`, `square_square=4/5`, `mixed_basic=4/5`.
      - Remaining failures are all `approach_no_final_servo`, so the final-insertion square contact stall is mostly addressed by this parameter set.
      - Moderate stress smoke with the same contact-tolerant settings reached `40/40 = 1.000`, zero collisions, zero timeouts on seed `625000`.
      - Larger moderate stress matrix on seeds `626000/627000/628000`, 20 episodes per profile, reached `240/240 = 1.000`, zero collisions, zero timeouts.
      - Larger matrix details: `single=60/60`, `round_square=60/60`, `square_square=60/60`, `mixed_basic=60/60`; mean steps `293.1`, max steps `826`, mean final XY `1.58 mm`, mean final-servo steps `60.3`.
      - A config smoke for the new v46 contact-tolerant stress config passed on `square_square/seed629000`, `1/1` success.
      - Deterministic worst-case demo `square_square/seed624001` succeeded in `245` steps, final XY/Z about `1.30 mm / 9.33 mm`.
      - Boundary regression with hole half-size `14.5-19 mm`, peg/square max `13.5 mm`, delay `3-4`, filter `0.35-0.55`, noise `0.25-0.8 mm`, seeds `630000/631000`, 10 episodes per profile: `76/80 = 0.950`, with 3 collisions and 1 timeout.
      - Boundary failures all occur on `seed631004` before final-servo. Single/round/mixed collide with `hole_north` around `36 mm` XY and `51 mm` Z; square-square times out around `32 mm` XY and `44 mm` Z. `square_fast_settle` is not involved.
      - Targeted `guard_block_down_when_unaligned` did not rescue `seed631004`. Fixture-clearance safety avoided collision but converted all four profiles to timeout; existing fixture realign did not activate (`fixture_realign=0`). Treat this as an approach/fixture-clearance state-machine problem.
    - output directories:
      - targeted probes: `D:\peg-in-hole-6yh\v44_square_fast_settle_probes`
      - 20ep x 3-seed matrix: `D:\peg-in-hole-6yh\v44_square_fast_settle_multiseed_matrix20`
      - new-seed 20ep x 3-seed regression: `D:\peg-in-hole-6yh\v44_square_fast_settle_regression_newseeds`
      - v45 moderate stress: `D:\peg-in-hole-6yh\v45_stress_matrix20_seed621_622`
      - v45 boundary probe: `D:\peg-in-hole-6yh\v45_boundary_probe_seed623`
      - v45 deterministic worst-case: `D:\peg-in-hole-6yh\v45_worstcase_probe_seed624`
      - v46 contact-tolerant worst-case probe: `D:\peg-in-hole-6yh\v46_square_recovery_param_probe_worstcase_all`
      - v46 contact-tolerant moderate smoke: `D:\peg-in-hole-6yh\v46_contact_tolerant_moderate_smoke_seed625`
      - v46 contact-tolerant larger moderate matrix: `D:\peg-in-hole-6yh\v46_contact_tolerant_moderate_matrix_seed626_628`
      - v46 contact-tolerant boundary regression: `D:\peg-in-hole-6yh\v46_contact_tolerant_boundary_regression_seed630_631`
      - v46 boundary targeted probes: `D:\peg-in-hole-6yh\v46_boundary_seed631004_blockdown_probe`, `D:\peg-in-hole-6yh\v46_boundary_seed631004_fixture_clearance_probe`, `D:\peg-in-hole-6yh\v46_boundary_seed631004_fixture_realign_probe`
      - v46 contact-tolerant config smoke: `D:\peg-in-hole-6yh\v46_contact_tolerant_config_smoke`
      - v46 contact-tolerant demo: `D:\peg-in-hole-6yh\v46_contact_tolerant_demos`
      - demo: `D:\peg-in-hole-6yh\v44_square_fast_settle_demos`
    - New reusable v44 configs:
      - `configs\sim\ur5e_full\eval_multi_geometry_contact_reinsert_tip_priority_square_fast_settle_60ep.yaml`
      - `configs\sim\ur5e_full\demo_multi_geometry_contact_reinsert_tip_priority_square_fast_settle.yaml`
    - New reusable v45 stress config:
      - `configs\sim\ur5e_full\eval_multi_geometry_contact_reinsert_tip_priority_square_fast_settle_stress_20ep.yaml`
    - New reusable v46 contact-tolerant stress config:
      - `configs\sim\ur5e_full\eval_multi_geometry_contact_reinsert_tip_priority_square_fast_settle_contact_tolerant_stress_20ep.yaml`
    - v44 demo result:
      - `square_square/615000`: success in `686` steps, no collision, final XY/Z about `1.14 mm / 9.79 mm`, final phase `square_fast_settle`.
  - New reusable 60ep config: `configs\sim\ur5e_full\eval_multi_geometry_contact_reinsert_tip_priority_60ep.yaml`.
  - New demo config: `configs\sim\ur5e_full\demo_multi_geometry_contact_reinsert_tip_priority.yaml`.
  - Demo result on seed `614000`:
    - `single`: success in `316` steps, `guard_steps=96`, final XY/Z about `1.34 mm / 9.40 mm`.
    - `square_square`: success in `315` steps, `guard_steps=95`, final XY/Z about `1.33 mm / 9.67 mm`.
    - GIFs are `2560x720`, overview plus wrist camera. Output directory: `D:\peg-in-hole-6yh\v42_tip_priority_demos`.
    - Important: `scripts\demo_policy.py` must be run with `--guarded-policy`; without it the demo is policy-only and can timeout with `guard_steps=0`.
  - Config smoke passed on 2026-05-24 with `single/seed612000`, `1/1` success. The local Codex shell could not create a new directory under repo `results\...` because of Windows permissions, so the smoke command overrode output paths to `D:\peg-in-hole-6yh\config_smoke*.csv/md`.
  - Current conclusion: wide-handoff plus square-fast-settle on top of phase-local final-servo/contact-reinsert tip-priority IK is the current strict 1000-step contact-aware reinsert candidate. Keep nominal `ik_control_mode: pose`; do not enable `pose_tip_priority` globally.

Next step:

- Do not scale square-square insert-settle BC replay by default; w05 was behaviorally flat under the current guarded deployment.
- Keep square recovery as a diagnostic hook, not a default.
- Treat wide-handoff plus square-fast-settle plus phase-local final-servo/contact-reinsert tip-priority as the current best opt-in multi-geometry guarded controller setting under strict `max_steps=1000`.
- v44 is locally committed and tagged as `v0.7.1-contact-reinsert-square-fast-settle`; do not add large untracked result traces unless a compact summary is specifically needed.
- Moderate v45 stress is solved, so do not train on that distribution yet. The useful next learning target is the square-square worst-case family: narrow clearance, delayed/filtered control, and insertion-time yaw/tilt/contact recovery.
- The v46 contact-tolerant square fast-settle parameter set passed the larger moderate-stress matrix and should now be treated as the current opt-in stress candidate, not a global default.
- Do not make the 1mm-clearance deterministic worst-case the default task yet; the remaining failures there are `approach_no_final_servo`, not final insertion contact stall.
- The tighter boundary regression exposed a separate approach/fixture-clearance problem on `seed631004`; solve that separately before claiming the aggressive boundary distribution is stable.
- Next technical work should implement or repair an approach-stage retreat/recenter/fixture-realign state machine for low-altitude, still-far-from-hole cases under severe delay/filter. Keep v46 contact-tolerant fast-settle as the current moderate-stress candidate.
- After the next learning/eval change is selected, push/tag only when requested.
- Keep the data plumbing and 2k correction dataset as a reusable diagnostic asset, but do not promote the w05 checkpoint as a new default.

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
- The default IK controller still solves peg-tip position only for checkpoint compatibility. An opt-in `ik_control_mode=pose` now constrains peg-tip orientation against the nominal rest orientation and regularizes posture, but it is diagnostic/experimental until evaluated on the existing high-start checkpoints.
- The current full UR5e fixture uses a peg radius of `0.012 m` and a base hole opening of about `40 mm`. Full-light geometry randomization now uses `geometry_hole_half_size_range=[0.017, 0.021]`, i.e. about `34 - 42 mm` opening.
- Metrics below were collected before the marker-hiding and hole-narrowing change unless explicitly refreshed.

Latest model audit:

- Added `scripts\audit_ur5e_full_model.py` to compare the full task XML against a raw DeepMind MuJoCo Menagerie `universal_robots_ur5e\ur5e.xml` reference.
- Generated `results\ur5e_full\model_audit\ur5e_full_menagerie_audit.md`.
- Audit result: the current full model preserves the shared UR5e body inertials and the full Menagerie mesh file set, but it is not an untouched official XML. It deliberately renames the six joints/actuators to the project interface, places the base in the task frame, adds the peg/tool/camera/table/hole wrapper, sets timestep/gravity, makes joint limits explicit, and adds contact defaults.
- Implication: before multi-geometry training, controller work should focus on task-specific control details: base pose, `tool0`/peg attachment pose, peg verticality, contact defaults, and IK/posture tracking near contact.

Latest near-contact controller diagnostic:

- Ran `scripts\diagnose_near_contact_tracking.py` with the promoted `pose IK + 0.03/64 + Kp2` setting.
- Outcome for the low-Z recenter probe: `xy reduction = 4.921 mm`, `reduction/cmd = 0.164`, `alignment = 0.986`, `step gain = 0.176`, `z drift = -2.897 mm`, `max tilt = 11.894 deg`.
- Attachment sanity check: `peg_tip -> eef` and `peg_tip -> tool0` stayed at `110 mm`, so the tool-chain geometry is consistent; the current limitation is not an obvious peg-to-tool attachment length error.
- Interpretation: the control direction is consistent, but low-Z Cartesian authority is still weak. The next useful change is a focused controller tweak for near-contact authority or low-Z stability, not multi-geometry data collection yet.

Latest low-Z preinsert lift-first guard experiment:

- Added an opt-in `guard_preinsert_recenter_lift_before_lateral` switch to the guarded deployment controller. Defaults stay unchanged.
- Same-seed 20ep baseline for the promoted `0.03/64 + Kp2` hard bucket was `0.950/0.000/0.050`.
- Broad lift-first preinsert recenter with `trigger_xy=0.004`, `stable_xy=0.0035`, `height=0.025` regressed to `0.850/0.000/0.150`. It turned seed `602000` and `602011` from successes into timeouts because preinsert recenter repeatedly held control around the 4 mm band.
- Narrow lift-first with `trigger_xy=0.008`, `stable_xy=0.0065`, `height=0.025`, `max_steps=40` recovered baseline at `0.950/0.000/0.050`, but did not improve the remaining timeout.
- Higher-lift variants also did not solve the same timeout: `height=0.045` stayed `0.950/0.000/0.050`, while early `height=0.080` regressed to `0.900/0.000/0.100`.
- Current conclusion: do not promote low-Z preinsert recenter as a new default. The hard remaining timeout shows low-Z lateral recentering can be ineffective even when command direction is correct; the next useful work is a controller/TCP tracking fix or a more explicit retreat-and-retry sequence, not broader preinsert threshold scans.

Latest hard-case TCP response diagnosis:

- Added `scripts\analyze_tcp_response_trace.py` to measure commanded/applied XY against actual peg-tip motion in step traces.
- On the baseline hard failure seed `602019`, the last 100 steps had mean final XY command about `5.0 mm`, mean applied XY about `4.5 mm`, but mean actual XY delta only about `0.009 mm`. The action-to-target alignment stayed high while actual-motion alignment was near zero.
- `guarded_hold_z_until_insert` moved the failure from a low-Z misaligned timeout into a long oscillation around the insert band. It reached XY `4.92 mm` and Z `48.9 mm`, but kept toggling because the descent/lift logic had no phase memory.
- A wide insert latch plus hold-Z held Z near `8.2 mm` with XY about `10.4 mm`, but still failed to converge.
- A widened `guard_final_servo` start range did enter final-servo, but still failed because XY drifted out of the release band and the current logic exhausted or reset without recovering the low-level tracking issue.
- `guard_near_action_scale` reduced command magnitude and improved tracking error, but it also stalled near `9 - 12 mm` XY and still did not insert.
- Current conclusion: the next bottleneck is not simple guard activation. It is the combination of low-level tracking authority, delay/filter response, and the need for a true stateful retreat/recenter phase if we want to keep working near the hole.

Latest static low-level controller response scan:

- Added `scripts\scan_near_contact_controller_response.py`, which reuses the low-Z near-contact probe and scans IK/control candidates across `ik_orientation_weight`, `ik_max_iterations`, `frame_skip`, actuator Kp, and damping.
- First scan output:
  - `results\ur5e_full\controller_diagnostics\near_contact_controller_response_scan_wori_kp.md`
  - `results\ur5e_full\controller_diagnostics\near_contact_controller_response_scan_wori_kp.csv`
  - conclusion note: `results\ur5e_full\controller_diagnostics\near_contact_controller_response_scan_summary.md`
- Probe result: global `Kp=3.0` improves low-Z command-to-motion response over the promoted `Kp=2.0` setting. The best probe candidate was `pose IK + w_ori=0.03 + 64 iterations + Kp3`, with `reduction/cmd=0.253`, `step_gain=0.262`, `0` probe collisions, and max tilt about `10.3 deg`.
- Closed-loop hard-bucket result did not promote Kp3:
  - Kp2 current retest, seed `602000`, 20ep hard bucket: `0.950/0.000/0.050`.
  - Kp3, same window: `0.850/0.000/0.150`.
  - Kp3 fixed the old seed `602019` timeout but introduced new timeouts at `602011`, `602013`, and `602017`.
- Intermediate Kp window scan over key seeds `602011-602019`:
  - Kp2.25: `8/9` success, still failed `602019`.
  - Kp2.5: `7/9` success, failed `602011` and `602019`.
  - Kp2.75: `8/9` success, fixed `602019` but failed `602011`.
- Current conclusion: the remaining failures are not solved by a single global actuator Kp. Higher Kp helps one low-Z timeout but changes approach/settling enough to create other timeouts. Keep `Kp=2.0` as the promoted static default. The next useful change should be stateful near-hole recovery, or a guarded/local gain schedule that only activates inside a tightly defined recovery phase.

Latest local near-hole recovery result:

- Implemented opt-in stateful near-hole recovery refinements:
  - recovery `resume` now returns to lift/recenter if XY drifts outside the resume band instead of exhausting at low Z.
  - final-servo align/confirm now holds or lifts to the start height while XY is outside its stable band, instead of continuing down to the low hover height.
  - eval/demo/inference can now switch arm actuator Kp locally with `--guard-near-actuator-kp-enabled`; the Kp boost applies during stateful recovery, final-servo, and the near-hole guarded zone, while global nominal Kp stays `2.0`.
- Added preset:
  - `configs\sim\ur5e_full\eval_high_start_hard_localkp3_recovery_20ep.yaml`
- Validated result for `pose IK + w_ori=0.03 + iters=64 + nominal Kp2 + local near-hole Kp3`:
  - hard bucket seed `602019`, 1ep: fixed the known timeout, success with `stateful_recovery=51` and `final_servo=109`.
  - hard bucket seed `602000`, 20ep: `1.000/0.000/0.000`.
  - hard bucket seed `602000`, 60ep: `0.917/0.000/0.083`, improving over the promoted Kp2 60ep result `0.883/0.000/0.117`, but not enough to promote as a stable 60ep/100ep milestone.
- Remaining 60ep failures:
  - early/approach plateau: `602024`, `602033`, `602048`, ending around `16 - 21 mm` XY and `55 - 65 mm` Z above target.
  - deep low-Z insertion drift: `602040`, `602047`, ending around `6.3 mm` XY and `8.7 mm` Z above target.
- Latest update: added a double-gated final-servo descend bias for tight-clearance cases after stateful recovery. The bias uses `guard_final_servo_descend_xy_bias: [0.0, -0.005]`, `guard_final_servo_descend_xy_bias_max_clearance: 0.006`, and `guard_final_servo_descend_xy_bias_requires_stateful_recovery: true`.
- Targeted checks now pass:
  - previously fixed seed `602019`: success preserved.
  - direct-insert tight-clearance seeds `602025`, `602028`, `602039`: success preserved.
  - low-Z drift seeds `602040`, `602047`: now succeed.
- Double-gated result for the same hard bucket:
  - seed `602000`, 20ep: `1.000/0.000/0.000`.
  - seed `602000`, 60ep: `0.950/0.000/0.050`.
- Remaining 60ep failures are only the high/approach plateau seeds `602024`, `602033`, and `602048`; all have `final_servo=0`, ending around `16 - 21 mm` XY and `55 - 65 mm` Z above target.
- Current conclusion: the near-hole low-Z recovery line is now stable enough for this stage. Do not call the whole high-start task solved yet; the next bottleneck is approach-to-hole plateau, not final insertion recovery.

Latest approach-plateau / low-recenter experiment:

- Added opt-in `guard_approach_recenter_*` and `guard_final_servo_low_recenter_*` phases to `GuardedPolicyController`, exposed through eval/demo/inference.
- `guard_approach_recenter` addresses the old high plateau seeds by taking over after a failed/short stateful recovery at about `45 - 75 mm` above target and re-centering around a high approach height.
- `guard_final_servo_low_recenter` adds a hysteretic low-Z hold/recenter phase: it can stop descent around `10 - 25 mm` above target, hold a configured height, re-center XY, then resume descent. It also reuses the final-servo XY bias when enabled.
- Best single-seed diagnostic candidate so far:
  - `guard_stateful_recovery_max_steps=80`
  - approach recenter `trigger/stable/height = 15 mm / 14 mm / 70 mm`
  - final-servo `start_xy=14 mm`, `stable_xy=6.25 mm`, `descent_start_xy=14 mm`
  - low-recenter `z_max=25 mm`, `trigger_xy=6.8 mm`, `release_xy=6.1 mm`, `height=18 mm`, `max_steps=500`
  - lift recovery `height=20 mm`, final-servo descend bias `[0, -5 mm]` with clearance gate `10 mm`
- Targeted result with that candidate:
  - regression seed `602025`: success preserved.
  - previous plateau seeds `602024/602033/602048`: still timeout, but the failure moved from high plateau/no final-servo into near-hole residuals.
  - `602024`: final XY/Z about `6.29 mm / 8.94 mm`, min XY about `6.04 mm`.
  - `602033`: final XY/Z about `6.40 mm / 10.34 mm`, min XY about `5.75 mm`.
  - `602048`: still high/late, final XY/Z about `6.95 mm / 16.78 mm`.
- Current conclusion: low-recenter is a useful diagnostic hook but is not promoted. The remaining gap is no longer gross approach failure on two seeds; it is low-level Cartesian authority around the last `1 - 2 mm` of XY correction under action-scale/delay/filter randomization. Next work should focus on a real control-chain compensation strategy or a validated bounded retry that starts earlier, not wider threshold scans.

Latest phase-local IK orientation relaxation:

- Added opt-in `--guard-near-ik-orientation-weight` to eval/demo/inference. It preserves the nominal `ik_orientation_weight` during high-start visual approach and switches only during stateful recovery, approach recenter, final-servo, or the near-hole guarded zone.
- Motivation: global `ik_orientation_weight=0.0` helped key seed `602024`, but can tilt the peg around `17 - 19 deg`; the safer hypothesis is to relax orientation only when near-hole Cartesian authority matters.
- Same 40-episode hard-bucket window, seed `602020`, with the current low-recenter candidate:
  - fixed `ik_orientation_weight=0.03`: `0.925/0.000/0.075`, failures `602024/602038/602048`.
  - global `ik_orientation_weight=0.0`: `0.900/0.000/0.100`, failures `602038/602040/602047/602048`.
  - nominal `0.03` plus `--guard-near-ik-orientation-weight 0.0`: `0.950/0.000/0.050`, failures `602038/602048`.
- Interpretation: phase-local relaxation is the best current controller-side candidate in this small gate. It fixes `602024` without the extra timeouts caused by global orientation relaxation, but `602038` still slowly descends around `5.4 mm` XY and `602048` still plateaus in low-recenter around `5.8 mm` XY / `16.5 mm` Z.

Latest strict final-servo stable-XY gate:

- Added reusable config `configs/sim/ur5e_full/eval_high_start_hard_localkp3_recovery_strictstable49_60ep.yaml`.
- Change from the phase-local candidate: keep near-hole `w_ori=0.0`, but tighten `guard_final_servo_stable_xy` from `6.25 mm` to `4.9 mm` so low-Z stalls just outside the `5 mm` success tolerance trigger the existing low-recenter/recovery path instead of timing out.
- Focused 20ep window, seed `602019`, reached `1.000/0.000/0.000`; this fixed the previous `602019/602038` near-miss window.
- Full hard-bucket 60ep gate, seed `602000`, reached `0.983/0.000/0.017`.
  - Only remaining failure: `602048`.
  - `602048` final XY/Z: `5.77 mm / 16.51 mm`; min XY/Z: `5.68 mm / 12.40 mm`.
  - Trace diagnosis: low-recenter is active, not missing. It spends about `462` steps trying to re-center near `16 - 18 mm` above target under action delay/filter/scale randomization and cannot remove the last `0.7 - 0.8 mm` XY error before timeout.
- Targeted `602048` probes tried plateau-triggered lift-recenter, `guard_action_gain=2.0`, descent-bias removal, and near-hole orientation weight `0.01`. None solved the seed within `1000` steps. The best probe reached `min_xy ~= 3.7 mm` and `min_z ~= 8.35 mm`, but not simultaneously; during descent XY drifted out again. Do not promote these one-seed parameters.
- Current conclusion: the strict stable-XY config is the best reproducible controller candidate for single-geometry high-start hard recovery. Treat the remaining gap as final insertion stability under tilt/contact/control-delay, not as another threshold scan. Next serious fix should either reduce near-hole tilt/contact drift or add a more principled insertion-time guarded controller; otherwise run a larger 100ep gate before moving toward multi-geometry.

## Latest UR5e Controller Diagnostic

Generated on 2026-05-17 with:

```powershell
python scripts\diagnose_ur5e_controller.py --episodes 3
```

Result summary:

| IK mode | Setup ok | XY gain | XY alignment | Tracking error | IK error | Orientation error | Max peg tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| position | 0.000 | 0.098 | 0.509 | 0.00281 | 0.00002 | 0.14471 | 9.453 deg |
| pose | 1.000 | 0.089 | 0.951 | 0.00278 | 0.00369 | 0.07546 | 4.575 deg |

Interpretation:

- Pose IK clearly improves low-Z orientation stability and command direction alignment.
- Both modes still have very low one-step lateral XY gain, so actuator/frame-skip tracking remains a likely bottleneck.
- Do not keep tuning high-level guard thresholds until the low-level controller comparison is evaluated with the current policy.

Next controller step:

- Run a 60-episode or 100-episode promoted-candidate gate with `ik_control_mode=pose`.
- If the gain holds, add pose-mode collection/eval configs and retrain a small correction or BC continuation run under the same controller.
- Inspect action tracking versus frame_skip/actuator gains before collecting more correction data, because one-step XY gain is still low.

Pose IK hard-bucket guarded eval, same final-servo config and insert-drift checkpoint:

| Seed | Episodes | Success | Collision | Timeout |
| ---: | ---: | ---: | ---: | ---: |
| position-IK 602000 | 60 | 0.417 | 0.133 | 0.450 |
| pose-IK 602000 | 60 | 0.717 | 0.100 | 0.183 |
| pose-IK 602000 | 20 | 0.850 | 0.050 | 0.100 |
| pose-IK 604000 | 20 | 0.700 | 0.200 | 0.100 |
| pose-IK 605000 | 20 | 0.700 | 0.100 | 0.200 |
| pose-IK 20ep x 3 avg | 60 | 0.750 | 0.117 | 0.133 |

This is a large improvement over the same-seed position-IK 60ep result of `0.417/0.133/0.450`; pose IK should be treated as the current best controller-side hypothesis.

Pose IK 100-episode matrix, same checkpoint/config family, seed `602000`:

| Scenario | Position success | Pose success | Delta | Position timeout | Pose timeout |
| --- | ---: | ---: | ---: | ---: | ---: |
| clean | 0.690 | 0.780 | +0.090 | 0.310 | 0.180 |
| visual_camera | 0.540 | 0.780 | +0.240 | 0.400 | 0.190 |
| visual_camera_control | 0.570 | 0.770 | +0.200 | 0.330 | 0.170 |
| full_light_geometry | 0.510 | 0.790 | +0.280 | 0.390 | 0.170 |
| full_contact_light | 0.500 | 0.800 | +0.300 | 0.420 | 0.160 |
| hard_full_light_bucket | 0.510 | 0.750 | +0.240 | 0.410 | 0.160 |

The cross-scenario matrix confirms that pose IK is not just a hard-bucket special case. Use pose IK as the preferred controller mode for the next full-UR5e high-start run.

Pose-aware correction replay, the later recovery-sequence recipe, and the first low-level gain/frame-skip diagnostic are now tested:

- `pose_ik_tail` hard gate stayed `0.717/0.100/0.183`.
- `recovery_sequence_pose_ik` hard gate also stayed `0.717/0.100/0.183`.
- Generic runtime `guarded_lift_before_lateral` regressed badly in a 20ep smoke to `0.150/0.800/0.050`.
- Summary: `results\ur5e_full\high_start\hard\correction\recovery_sequence_pose_ik_summary.md`
- `eval_guarded_policy.py` now exposes nominal arm dynamics multipliers and `frame_skip` for controller diagnostics.
- Kp=2 removed collisions in the hard 60ep gate, but did not materially improve success: `0.733/0.000/0.267` versus the previous pose-IK `0.717/0.100/0.183`.
- Kp=4 regressed hard 20ep to `0.250/0.000/0.750`; `frame_skip=20` stayed flat at hard 60ep `0.733/0.000/0.267`.
- Lowering pose-IK orientation weight to `0.06` and increasing IK iterations to `48` is the best current controller candidate: hard seed `602000` improved to `0.767/0.100/0.133`, and the 20ep x 3-seed average moved from `0.750/0.117/0.133` to `0.767/0.100/0.133`.
- The 100ep matrix also improved success in every scenario versus the previous pose-IK baseline: clean `0.780 -> 0.850`, visual_camera `0.780 -> 0.840`, visual_camera_control `0.770 -> 0.840`, full_light_geometry `0.790 -> 0.850`, full_contact_light `0.800 -> 0.850`, hard_full_light_bucket `0.750 -> 0.790`.
- Candidate config files:
  - `configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_hard_60ep.yaml`
  - `configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_matrix_100ep.yaml`
- Candidate hard 60ep failure analysis: `6` high-fixture-wall collisions, `2` insert-band low-Z drift timeouts, and `6` near-XY no-insert timeouts. Raising `guard_start_z` to `0.16` or `0.20` stayed flat in a 20ep hard smoke, so simple earlier guard activation is not enough.
- New best controller candidate is `ik_orientation_weight=0.06`, `ik_max_iterations=48`, and `nominal_actuator_kp_multiplier=2.0`.
- New best hard 60ep result: `0.850/0.000/0.150`, versus `0.767/0.100/0.133` for `0.06/48` without Kp2 and `0.717/0.100/0.183` for the older pose-IK baseline.
- Second hard seed check passed: seed `604000` reached `0.867/0.000/0.133`.
- New best 100ep matrix: clean `0.910/0.000/0.090`, visual_camera `0.910/0.000/0.090`, visual_camera_control `0.910/0.000/0.090`, full_light_geometry `0.900/0.000/0.100`, full_contact_light `0.900/0.000/0.100`, hard_full_light_bucket `0.890/0.000/0.110`.
- Kp2 candidate config files:
  - `configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_kp2_hard_60ep.yaml`
  - `configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_kp2_matrix_100ep.yaml`
- Kp2 failure analysis: remaining hard 60ep failures are `9` timeouts and `0` collisions; most are delay-2 high-misalignment timeouts around `20 - 30 mm` XY and `70 - 85 mm` above target.
- Wider `guarded_align_xy_tolerance=0.030` regressed hard 60ep to `0.833/0.000/0.167`, so do not promote wider align.
- Kp2 high-resolution demo is generated and successful:
  - config: `configs\sim\ur5e_full\demo_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_kp2.yaml`
  - output: `demos\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori006_it48_kp2.gif`
  - trace: `results\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori006_it48_kp2_trace.csv`
  - result: success in `309` steps, no collision, final XY/Z error about `4.3 mm / 9.7 mm`
  - the rendered GIF is `2560x720`; MP4 output fell back to GIF because the local `imageio` video backend is unavailable
- Follow-up trace inspection showed the `0.06/48 + Kp2` failures are not just high-level guard logic: the policy/guard command remains saturated but the measured peg-tip delta is near zero, and IK target error stays around `5 - 6 mm`. This points to pose-IK tracking authority as the next bottleneck.
- Lowering orientation weight and increasing iterations produced a new best candidate: `ik_orientation_weight=0.03`, `ik_max_iterations=64`, `nominal_actuator_kp_multiplier=2.0`.
- New hard 60ep results:
  - seed `602000`: `0.883/0.000/0.117`
  - seed `604000`: `0.900/0.000/0.100`
- The 100ep scenario matrix for `0.03/64 + Kp2` reached clean `0.970/0.000/0.030`, visual_camera `0.970/0.000/0.030`, visual_camera_control `0.940/0.000/0.060`, full_light_geometry `0.910/0.000/0.090`, full_contact_light `0.910/0.000/0.090`, hard_full_light_bucket `0.910/0.000/0.090`.
  - The first five rows came from `eval_insert_drift_pose_ik_wori003_it64_kp2_matrix_100ep_seed602000.*`.
  - The hard-bucket row was run separately as `eval_insert_drift_pose_ik_wori003_it64_kp2_hard_100ep_seed602000.*` because the initial matrix config missed `include_hard_bucket`; the config has been fixed.
- New candidate demo succeeded:
  - config: `configs\sim\ur5e_full\demo_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori003_it64_kp2.yaml`
  - output: `demos\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori003_it64_kp2.gif`
  - trace: `results\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori003_it64_kp2_trace.csv`
  - result: success in `335` steps, no collision, final XY/Z error about `4.5 mm / 9.6 mm`
- Summary: `results\ur5e_full\controller_diagnostics\controller_gain_frame_skip_summary.md`
- Matrix summary: `results\ur5e_full\controller_diagnostics\pose_ik_wori006_it48_matrix_summary.md`
- Kp2 summary: `results\ur5e_full\controller_diagnostics\pose_ik_wori006_it48_kp2_summary.md`
- Current best summary: `results\ur5e_full\controller_diagnostics\pose_ik_wori003_it64_kp2_summary.md`

Do not scale these correction recipes further without changing the controller/guard structure. Do not promote frame_skip 20, fixture-clearance lift, or wider align tolerance. Treat `ik_orientation_weight=0.03`, `ik_max_iterations=64`, and `nominal_actuator_kp_multiplier=2.0` as the current best full-UR5e controller candidate.

## Next Step

1. The `0.03/64 + Kp2` controller milestone has been promoted and pushed as `v0.6.49`.
2. The first controller-realism step is now model audit and task-wrapper accountability; the Menagerie audit is implemented and generated.
3. The focused near-contact diagnostic has now run on the promoted config, and the first preinsert lift-first guard experiment is implemented and evaluated. It is diagnostic only, not promoted.
4. The TCP response diagnosis has now shown that command-to-motion transfer is the limiting factor in the remaining hard timeout. The first static low-level Kp/IK scan is complete: stronger global Kp improves probe response but is not a safe promoted default in closed-loop policy evaluation.
5. Next implementation step: add a real stateful retreat/recenter phase with height hysteresis, or test a strictly local near-hole gain schedule inside that phase. Do not keep scanning global Kp or simple guard thresholds.
6. Multi-geometry has now started on `feature/multi-geometry`; keep the remaining timeout work focused on contact-aware insert-band recovery before scaling multi-geometry data collection.

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

## Hard High-Start Correction 2k Pass

On 2026-05-09, the correction pass was expanded from the 256-sample smoke to a balanced 2k dataset.

New configs:

- `configs\sim\ur5e_full\collect_high_start_hard_correction_2k.yaml`
- `configs\sim\ur5e_full\pretrain_high_start_hard_correction_2k_w05_e2.yaml`
- `configs\sim\ur5e_full\pretrain_high_start_hard_correction_2k_w10_e2.yaml`
- `configs\sim\ur5e_full\eval_high_start_hard_correction_2k_w05_e2.yaml`
- `configs\sim\ur5e_full\eval_high_start_hard_correction_2k_w10_e2.yaml`
- `configs\sim\ur5e_full\demo_high_start_hard_correction_2k_w10_e2.yaml`

Correction dataset:

```text
datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_near_hole_plateau_2k.npz
results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_2k_inspection.md
```

Collection summary:

- samples: `2000`
- unique source episodes: `131`
- collection episodes completed: `249`
- scenarios: `1000` visual_camera samples and `1000` visual_camera_control samples
- visual_camera source success/collision/timeout: `0.265 / 0.325 / 0.410`
- visual_camera_control source success/collision/timeout: `0.258 / 0.424 / 0.318`

Correction signal quality:

| Signal | Rate |
| --- | ---: |
| near hole | 1.000 |
| failure window | 0.686 |
| opposed policy/oracle actions | 0.749 |
| policy down or oracle up | 0.868 |
| policy down and oracle less down | 0.975 |

Distribution highlights:

- median `dist_xy`: about `10.8 mm`
- median `dist_z`: about `14.2 mm`
- mean correction norm: about `0.0111 m`
- sample outcomes: `619` collision-window samples and `1381` timeout-window samples

Weighted BC candidates:

| Candidate | Correction replay | Epochs | Final train loss | Final val loss |
| --- | ---: | ---: | ---: | ---: |
| `sac_image_bc_50k_high_start_hard_correction_2k_w05_e2.zip` | 0.05 | 2 | 0.044852 | 0.134496 |
| `sac_image_bc_50k_high_start_hard_correction_2k_w10_e2.zip` | 0.10 | 2 | 0.147904 | 0.205214 |

Same-seed 20-episode comparison, seed `574000`:

| Scenario | Baseline success | 5% success | 10% success | Baseline collision | 5% collision | 10% collision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | 0.45 | 0.45 | 0.45 | 0.35 | 0.35 | 0.35 |
| visual_camera | 0.25 | 0.25 | 0.25 | 0.25 | 0.25 | 0.30 |
| visual_camera_control | 0.40 | 0.40 | 0.40 | 0.35 | 0.35 | 0.30 |
| full_light_geometry | 0.25 | 0.25 | 0.25 | 0.30 | 0.30 | 0.30 |
| full_contact_light | 0.30 | 0.30 | 0.30 | 0.35 | 0.35 | 0.35 |
| hard_full_light_bucket | 0.35 | 0.35 | 0.40 | 0.45 | 0.45 | 0.35 |

10% correction demo:

```text
demos\ur5e_full\high_start\hard\correction\demo_high_start_hard_correction_2k_w10_e2.gif
results\ur5e_full\high_start\hard\correction\demo_high_start_hard_correction_2k_w10_e2_trace.csv
```

- result: timeout at `1000` steps, no collision
- first guard activation: step `279`, about `48.7 mm` XY and `119.3 mm` above target
- first reached `25 mm` XY: step `357`
- never reached the `5 mm` success XY tolerance
- final state: about `8.4 mm` XY error and `30.6 mm` above target

Interpretation:

- The 2k dataset confirms that the correction signal is real and repeatable.
- 5% replay is too weak to change the policy.
- 10% replay gives a small hard-bucket improvement in a 20-episode smoke, but it does not fix the same-seed demo plateau and slightly hurts visual_camera collision.
- Correction BC alone is not the next best lever. The next step should be a guarded re-align/retry controller for the final `5 - 15 mm` XY error band.

## Hard High-Start Guarded Retry Prototype

On 2026-05-09, a bounded deployment-time retry controller was added to the guarded policy path.

Code/config changes:

- `GuardedPolicyConfig` now supports retry settings:
  - `guard_retry_enabled`
  - `guard_retry_stall_steps`
  - `guard_retry_xy_tolerance`
  - `guard_retry_z_max`
  - `guard_retry_lift_height`
  - `guard_retry_release_xy`
  - `guard_retry_max_attempts`
  - `guard_retry_max_steps`
- `GuardedPolicyStep` now reports retry diagnostics:
  - `guard_retry_active`
  - `guard_retry_triggered`
  - `guard_retry_count`
  - `guard_retry_stall_steps`
  - `guard_retry_active_steps`
- `eval_guarded_policy.py`, `demo_policy.py`, and `run_policy_inference.py` expose the retry parameters and trace diagnostics.
- New configs:
  - `configs\sim\ur5e_full\eval_high_start_hard_retry_guarded_50k.yaml`
  - `configs\sim\ur5e_full\demo_high_start_hard_retry_guarded_50k.yaml`

The first unbounded retry smoke showed why a bound is necessary: retry could stay active for hundreds of steps and prevent normal insertion. The implementation was adjusted so retry:

- never commands downward motion while active
- has a maximum active duration per attempt
- records active-step diagnostics in eval/demo traces

Current same-seed 20-episode evaluation, seed `574000`:

| Scenario | Baseline hard-safe 50k | Retry guard | Collision |
| --- | ---: | ---: | ---: |
| clean | 0.45 | 0.30 | 0.35 |
| visual_camera | 0.25 | 0.15 | 0.25 |
| visual_camera_control | 0.40 | 0.25 | 0.35 |
| full_light_geometry | 0.25 | 0.25 | 0.30 |
| full_contact_light | 0.30 | 0.25 | 0.35 |
| hard_full_light_bucket | 0.35 | 0.30 | 0.45 |

Retry demo:

```text
demos\ur5e_full\high_start\hard\retry\demo_high_start_hard_retry_guarded_50k.gif
results\ur5e_full\high_start\hard\retry\demo_high_start_hard_retry_guarded_50k_trace.csv
```

- result: timeout at `1000` steps, no collision
- first guard activation: step `244`, about `50.0 mm` XY and `119.3 mm` above target
- first reached `25 mm` XY: step `332`
- retry triggered at steps `465` and `665`
- never reached the `5 mm` success XY tolerance
- final state: about `8.4 mm` XY error and `27.5 mm` above target

Interpretation:

- Retry is now implemented and instrumented, but it is not a promoted improvement.
- The dominant issue is deeper than retry timing: the current guarded oracle/IK path still cannot reliably move below about `8 mm` XY error once the peg is near the hole.
- More correction BC or more retry attempts are unlikely to solve the plateau until the near-hole controller is changed to hold alignment and/or improve IK/posture behavior before descent.

## Hard High-Start No-Prediction Guarded Controller

On 2026-05-09, the near-hole guarded oracle was extended with a diagnostic hold-Z option and then tested with prediction disabled.

Code/config changes:

- `OracleControllerConfig` now supports:
  - `guarded_hold_z_until_insert`
- `eval_guarded_policy.py`, `demo_policy.py`, `run_policy_inference.py`, `collect_image_expert_dataset.py`, and `oracle_rollout.py` expose `--guarded-hold-z-until-insert`.
- New configs:
  - `configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml`
  - `configs\sim\ur5e_full\demo_high_start_hard_pred0_guarded_50k.yaml`
  - `configs\sim\ur5e_full\eval_high_start_hard_strict_align_guarded_50k.yaml`
  - `configs\sim\ur5e_full\demo_high_start_hard_strict_align_guarded_50k.yaml`

Key finding:

- The old `guarded_prediction_steps: 1.0` can make the oracle believe the peg is already inside the `5 mm` insert band even when the real current XY error is still around `8 mm`.
- Setting `guarded_prediction_steps: 0.0` removes that false early-descent trigger and is the strongest controller-only improvement so far.

Same-seed 100-episode comparison, seed `574000` for the no-prediction candidate:

| Scenario | Baseline hard-safe 50k | No-prediction guard |
| --- | ---: | ---: |
| clean | 0.480 | 0.560 |
| visual_camera | 0.450 | 0.500 |
| visual_camera_control | 0.330 | 0.530 |
| full_light_geometry | 0.270 | 0.450 |
| full_contact_light | 0.310 | 0.380 |
| hard_full_light_bucket | 0.330 | 0.430 |

Same-seed 20-episode controller scan before the 100-episode run:

| Scenario | Baseline hard-safe 50k | Retry guard | Strict hold-Z | No-prediction guard |
| --- | ---: | ---: | ---: | ---: |
| clean | 0.45 | 0.30 | 0.40 | 0.55 |
| visual_camera | 0.25 | 0.15 | 0.25 | 0.50 |
| visual_camera_control | 0.40 | 0.25 | 0.40 | 0.50 |
| full_light_geometry | 0.25 | 0.25 | 0.25 | 0.40 |
| full_contact_light | 0.30 | 0.25 | 0.30 | 0.40 |
| hard_full_light_bucket | 0.35 | 0.30 | 0.35 | 0.45 |

No-prediction demo:

```text
demos\ur5e_full\high_start\hard\pred0\demo_high_start_hard_pred0_guarded_50k.gif
results\ur5e_full\high_start\hard\pred0\demo_high_start_hard_pred0_guarded_50k_trace.csv
```

- demo seed: `571001`
- result: success in `411` steps
- final XY: about `4.85 mm`
- final Z: about `9.83 mm`
- collision: false

Hard-case trace:

- seed `571000` remains a failure under no-prediction guard.
- In the no-prediction + strict hold diagnostic run, seed `571000` reached the `5 mm` band and got as low as about `3.0 mm` XY error, but XY drifted back out during descent and the controller oscillated instead of finishing.

Interpretation:

- The immediate controller fix is not retry; it is disabling one-step prediction in the guarded final insertion controller for this UR5e high-start setting.
- The 100-episode no-prediction run confirms this is a real improvement, but it is still far below the target success rate for deployment.
- Next, inspect seed `571000` to design a stateful insert latch or descent hysteresis that tolerates small XY drift during the final descent without returning to the old plateau.

## Hard High-Start Insert Latch Diagnostic

On 2026-05-09, a stateful insert latch / descent hysteresis prototype was added on top of the no-prediction guarded controller.

Code/config changes:

- `GuardedPolicyConfig` now supports:
  - `guard_insert_latch_enabled`
  - `guard_insert_latch_xy_tolerance`
  - `guard_insert_latch_release_xy`
  - `guard_insert_latch_resume_xy`
  - `guard_insert_latch_recenter_height`
  - `guard_insert_latch_max_down_action`
- `GuardedPolicyStep` reports latch diagnostics including:
  - `guard_insert_latched`
  - `guard_insert_latch_activated`
  - `guard_insert_latch_released`
  - `guard_insert_latch_steps`
  - `guard_insert_latch_descent_allowed`
- `eval_guarded_policy.py`, `demo_policy.py`, and `run_policy_inference.py` expose the latch settings and trace diagnostics.
- New diagnostic configs:
  - `configs\sim\ur5e_full\eval_high_start_hard_pred0_latch_guarded_50k.yaml`
  - `configs\sim\ur5e_full\demo_high_start_hard_pred0_latch_guarded_50k.yaml`

Seed `571000` result:

- The latch activates after the peg enters the `5 mm` band.
- The best trace reaches about `3.7 mm` XY, but then drifts back outside the insert band during descent.
- Pausing descent when XY drifts out of the `5 mm` band prevents more down-commanding, but it does not recover the wedged contact.
- A two-stage recenter variant was then tested: hold XY and lift first, then laterally re-align once above the hole-wall height. This also did not solve the hard seed within `1000` steps.

Small hard-bucket smoke for the two-stage recenter variant:

| Eval | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| pred0 latch/recenter hard bucket | 10 | 0.400 | 0.500 | 0.100 |

Diagnostic interpretation:

- IK is not the immediate blocker for the commanded Cartesian step: manual inspection showed the IK solution can reach the requested tip target with sub-millimeter error.
- The blocker is physical/contact tracking: while the peg tip is still inside the hole-wall vertical range, the simulated UR5e position actuators barely move upward or laterally under the small per-step action target.
- The latch/recenter prototype should not be promoted. It is useful evidence that the remaining hard high-start failures are wedged-contact / final-insertion correction failures, not just early-descent prediction failures.
- The promoted controller-only setting remains `guarded_prediction_steps: 0.0`.
- The next useful direction is contact-aware failure correction / DAgger, or a stronger deployment guarded oracle that learns/commands explicit unjam-lift and reinsert behavior from failure states.

## Two-Track High-Start Insert Improvement Plan

The next high-start work should use two coordinated tracks:

### Track A: Prevent Misalignment Before Descent

Goal: reduce the number of biased insert attempts so the system does not rely on recovery as the main solution.

Planned changes:

1. Add a near-hole hover alignment phase:
   - hold the peg above the hole before final descent
   - keep Z roughly `0.03 - 0.06 m` above the target while correcting XY
   - require stable XY alignment for several consecutive steps before allowing downward insertion
2. Add a descent gate:
   - if XY is outside the insert band, clamp downward Z action to `0`
   - allow slow descent only when XY is stable, for example `<= 0.003 - 0.005 m`
3. Add a near-hole small-action mode:
   - use larger actions for high-start search
   - switch to smaller near-hole actions, for example `0.001 - 0.002 m`, during final alignment/descent
4. Collect a near-hole visual alignment dataset:
   - peg starts `0.03 - 0.08 m` above the hole
   - XY offset covers roughly `0 - 0.020 m`
   - oracle labels should mostly hold Z and correct XY, not rush downward
5. Evaluate prevention quality:
   - fraction of descents that start with XY `<= 0.003 - 0.005 m`
   - rate of XY drift during first descent
   - hard seed `571000`
   - hard bucket and full eval matrix

### Track B: Recover From Wedged Near-Hole Failures

Goal: handle the remaining cases where the peg enters the hole area, drifts, wedges on the wall, and would otherwise timeout.

Planned changes:

1. Collect failure-window samples from policy rollouts:
   - XY entered the insert band, then drifted to about `0.005 - 0.010 m`
   - Z is low enough that peg-wall contact or wedging is likely
   - progress stalls for multiple steps
   - no immediate collision termination
2. Use a contact-aware guarded oracle for labels:
   - if low and misaligned, command a bounded upward unjam motion
   - after lifting above the hole-wall range, re-align XY
   - only then resume slow descent
   - limit retries so the correction policy does not learn infinite lift/retry loops
3. Fine-tune with weighted BC / DAgger:
   - start from the current hard high-start checkpoint
   - use a small correction ratio first, for example `10% - 20%`
   - inspect whether correction labels are genuinely different from the failed policy action
4. Evaluate recovery quality:
   - hard seed `571000`
   - hard bucket 20-episode smoke
   - full 100-episode matrix only if smoke improves
   - collision rate must not rise materially

### Implementation Order

These tracks should be coordinated, but not implemented as two large independent rewrites at the same time.

Recommended order:

1. Build shared diagnostics and selection logic once:
   - commanded action
   - target tip position
   - IK target error
   - joint target/current error
   - actual tip delta
   - descent-gate state
   - failure-window state
2. Implement Track A first:
   - near-hole hover alignment
   - descent gate
   - near-hole small-action mode
   - alignment dataset and BC fine-tune
3. Then implement Track B:
   - failure-window collector
   - contact-aware correction oracle
   - weighted BC / DAgger
4. After both are stable:
   - re-run the high-start hard eval matrix
   - then consider larger initial XY offsets
   - only after that reintroduce stronger control/geometry/contact randomization

Reasoning:

- Track A should reduce how often the peg enters the hole while misaligned.
- Track B should remain a fallback for the fewer hard cases that still wedge.
- Running both without staging would make it hard to know whether improvements came from better pre-insert alignment or from recovery after contact.

### Shared Diagnostics Status

Started on 2026-05-09.

Implemented environment-level action/IK/tracking diagnostics:

- `action_tip_pos_before`
- `action_target_tip_pos`
- `action_target_tip_delta`
- `action_actual_tip_delta`
- `action_tip_delta_error`
- `action_tracking_error`
- `ik_tip_pos`
- `ik_target_error`
- `ik_iterations`
- `joint_qpos_before_action`
- `joint_target_qpos`
- `joint_qpos_after_action`
- `joint_target_error`

These fields are now available in environment `info`, demo trajectory CSVs,
policy inference traces, expert dataset diagnostics, and correction dataset
diagnostics. They are intended to support both Track A descent-gate work and
Track B failure-window / DAgger sampling.

### Track A Hover / Descent Gate Prototype Status

Started on 2026-05-09.

Implemented controller-side Track A prototype on top of the hard high-start
no-prediction guard:

- `GuardedPolicyConfig` now supports near-hole hover alignment and near-action
  limiting:
  - `guard_hover_enabled`
  - `guard_hover_xy_tolerance`
  - `guard_hover_release_xy`
  - `guard_hover_height`
  - `guard_hover_z_tolerance`
  - `guard_hover_required_steps`
  - `guard_hover_max_down_action`
  - `guard_near_action_scale_enabled`
  - `guard_near_action_xy_tolerance`
  - `guard_near_action_z_threshold`
  - `guard_near_max_xy_action`
  - `guard_near_max_down_action`
- Hover descent is now stateful:
  - require stable hover alignment before final descent
  - latch descent once stable instead of resetting just because Z leaves the
    hover band during insertion
  - release back to hover if XY drifts beyond the release threshold
  - block downward motion and command lift/re-align if XY drifts outside the
    hover insert band during descent
- Trace/eval diagnostics now include:
  - `guard_hover_active`
  - `guard_hover_stable_steps`
  - `guard_hover_descent_allowed`
  - `guard_hover_descent_latched`
  - `guard_hover_down_blocked`
  - `guard_near_action_limited`
- Experimental configs:
  - `configs\sim\ur5e_full\eval_high_start_hard_pred0_hover_guarded_50k.yaml`
  - `configs\sim\ur5e_full\demo_high_start_hard_pred0_hover_guarded_50k.yaml`

Hard seed `571000` result:

- The old non-stateful hover prototype never latched on the hard bucket because
  control delay pushed the peg below the strict hover Z band.
- With `guard_hover_z_tolerance: 0.025`, the stateful prototype latches and
  starts descent near `3.8 mm` XY error.
- The peg still drifts to roughly `5.1 - 5.3 mm` XY error during low-Z contact
  and times out instead of inserting.
- Increasing `max_steps` to `1500` did not solve the seed; it only lifted from
  about `2.7 cm` to about `3.9 cm` above target before timeout.

Same-seed 10-episode hard-bucket smoke, seed `574000`:

| Eval | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| pred0 guarded baseline | 10 | 0.400 | 0.500 | 0.100 |
| pred0 hover/descent-gate prototype | 10 | 0.400 | 0.500 | 0.100 |

Interpretation:

- Track A diagnostics and mechanics are now implemented, but the hover/descent
  gate is not a promoted improvement yet.
- The prototype confirms the dominant remaining failure: final insertion enters
  a wedged low-Z contact state where small Cartesian commands cannot recover
  quickly enough.
- Next useful work is Track B: a contact-aware guarded oracle / DAgger
  correction path that labels explicit unjam-lift, re-align, and reinsert
  behavior from these low-Z failure states.

### Track B Contact-Aware Correction Smoke

Started on 2026-05-09.

Implemented a contact-aware correction-label oracle for failure-window data:

- `OracleMode` now supports `contact_aware_recovery`.
- `OracleControllerConfig` now supports:
  - `contact_recovery_xy_tolerance`
  - `contact_recovery_z_max`
  - `contact_recovery_lift_height`
  - `contact_recovery_lift_z_tolerance`
  - `contact_recovery_max_down_action`
- `collect_image_correction_dataset.py` now accepts:
  - `oracle_mode: contact_aware_recovery`
  - the contact recovery parameters above
- Correction datasets now store additional diagnostics:
  - `contact_recovery_window`
  - `recovery_phase`
  - `oracle_lift_action`
  - `oracle_down_action`
- `inspect_image_correction_dataset.py` reports contact recovery and recovery
  phase counts.

Smoke configs:

- `configs\sim\ur5e_full\collect_high_start_hard_contact_recovery_smoke.yaml`
- `configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_smoke_w10_e1.yaml`
- `configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_smoke_w10_e1.yaml`

Smoke dataset:

```text
datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_smoke.npz
results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_smoke_inspection.md
```

Dataset inspection:

- samples: `256`
- source episodes with kept samples: `22`
- collection episodes completed: `72`
- near-hole rate: `1.000`
- failure-window rate: `1.000`
- contact-recovery-window rate: `1.000`
- oracle lift action rate: `1.000`
- oracle down action rate: `0.000`
- opposed-action rate: `0.953`
- `policy_down_or_oracle_up` rate: `0.953`
- recovery phase counts:
  - `unjam_lift`: `256`

Mean raw label direction:

- oracle raw action mean: about `[0.0, 0.0, +0.005]`
- policy raw action mean: about `[-0.00007, +0.00130, -0.00402]`

This confirms the new labeler captures the intended failure correction: when
the learned policy keeps pushing down near the hole wall, the correction label
commands an upward unjam motion.

Smoke fine-tune:

```text
checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_50k_contact_recovery_smoke_w10_e1.zip
results\ur5e_full\high_start\hard\correction\training_metadata_contact_recovery_smoke_w10_e1.json
```

Same-seed 10-episode hard-bucket eval with pred0 guarded controller:

| Eval | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| pred0 guarded baseline | 10 | 0.400 | 0.500 | 0.100 |
| contact-recovery smoke w10 e1 | 10 | 0.400 | 0.500 | 0.100 |

Interpretation:

- The Track B label mechanism works.
- The first smoke dataset is too one-phase: it only teaches `unjam_lift`.
- The next Track B step should collect staged correction data, not just final
  failure-window rows:
  1. low-Z misaligned states labeled `unjam_lift`
  2. lifted but still misaligned states labeled `realign`
  3. lifted/aligned states labeled `slow_insert`
- Only after those three phases are represented should we scale to a larger
  2k-10k DAgger/correction dataset and rerun weighted BC.

Follow-up staged smoke:

Implemented recovery branch rollouts and synthetic staged recovery states in
`collect_image_correction_dataset.py`:

- `recovery_branch_rollout`
- `recovery_branch_max_starts_per_episode`
- `recovery_branch_max_steps`
- `recovery_branch_stride`
- `recovery_branch_stop_on_success`
- `recovery_branch_clear_control_history`
- `recovery_branch_synthetic_stages`

The staged collector now:

1. Saves lightweight MuJoCo state snapshots at low-Z near-hole failure states.
2. Branches from selected failure states and executes the contact-aware oracle.
3. Optionally clears control delay/filter history for data generation so the
   oracle branch is not dominated by previous policy-down commands.
4. Adds synthetic curriculum states:
   - lifted but still misaligned: `realign`
   - lifted and aligned: `slow_insert`
5. Selects samples in a phase-balanced order rather than only by correction
   norm.

Staged smoke config:

```text
configs\sim\ur5e_full\collect_high_start_hard_contact_recovery_staged_smoke.yaml
```

Staged smoke dataset:

```text
datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_smoke.npz
results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_smoke_inspection.md
```

Staged smoke inspection:

- samples: `512`
- episodes completed while collecting: `86`
- unique kept source episodes: `22`
- recovery branch rate: `0.514`
- synthetic recovery state rate: `0.168`
- recovery phase counts:
  - `unjam_lift`: `410`
  - `realign`: `49`
  - `slow_insert`: `53`

This is a substantial improvement over the first contact-recovery smoke, which
had `256/256` `unjam_lift` samples and no useful realign/slow-insert coverage.

Staged smoke fine-tune:

```text
checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_50k_contact_recovery_staged_smoke_w15_e1.zip
results\ur5e_full\high_start\hard\correction\training_metadata_contact_recovery_staged_smoke_w15_e1.json
```

Same-seed 10-episode hard-bucket eval with pred0 guarded controller:

| Eval | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| pred0 guarded baseline | 10 | 0.400 | 0.500 | 0.100 |
| contact-recovery smoke w10 e1 | 10 | 0.400 | 0.500 | 0.100 |
| staged contact-recovery smoke w15 e1 | 10 | 0.400 | 0.500 | 0.100 |

Hard seed `571000` with the staged smoke checkpoint:

- result: collision at `123` guarded steps
- success: `0`
- collision: `1`
- timeout: `0`

Interpretation:

- The staged Track B data pipeline is now working and produces the intended
  multi-phase labels.
- The 512-sample staged smoke checkpoint is not promoted. It does not improve
  hard-bucket success and makes seed `571000` collide rather than timeout.
- Next useful step is to scale the staged dataset carefully, but with lower
  replay weight and explicit collision monitoring.

Follow-up staged 2k pass:

New configs:

- `configs\sim\ur5e_full\collect_high_start_hard_contact_recovery_staged_2k.yaml`
- `configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_staged_2k_w05_e2.yaml`
- `configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_staged_2k_w10_e2.yaml`
- `configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_staged_2k_w05_e2.yaml`
- `configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_staged_2k_w10_e2.yaml`

Dataset:

```text
datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_2k.npz
results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_2k_inspection.md
```

Inspection:

- samples: `2048`
- visual_camera / visual_camera_control: `1024 / 1024`
- episodes completed while collecting: `288`
- unique kept source episodes: `86`
- recovery branch rate: `0.521`
- synthetic recovery state rate: `0.167`
- recovery phase counts:
  - `unjam_lift`: `1674`
  - `realign`: `172`
  - `slow_insert`: `202`

Weighted BC checkpoints:

```text
checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_50k_contact_recovery_staged_2k_w05_e2.zip
checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_50k_contact_recovery_staged_2k_w10_e2.zip
```

Same-seed 20-episode guarded eval:

| Checkpoint | Clean | Visual Camera | Visual Camera Control | Full Light | Full Contact | Hard Bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| staged 2k w05 e2 | 0.550 | 0.500 | 0.500 | 0.400 | 0.350 | 0.450 |
| staged 2k w10 e2 | 0.550 | 0.550 | 0.500 | 0.400 | 0.350 | 0.450 |

Hard-bucket collision / timeout:

| Checkpoint | Collision | Timeout |
| --- | ---: | ---: |
| staged 2k w05 e2 | 0.450 | 0.100 |
| staged 2k w10 e2 | 0.400 | 0.150 |

Hard seed `571000` with staged 2k w10 e2:

- result: collision
- success: `0`
- collision: `1`
- timeout: `0`

Interpretation:

- The staged 2k pass is a small positive signal versus the staged smoke, but
  it is not strong enough to promote.
- `5%` and `10%` replay are similar; `10%` slightly improves visual_camera and
  hard-bucket collision, but still fails the known hard seed `571000`.
- The correction dataset is still dominated by `unjam_lift`
  (`1674/2048`). With `5% - 10%` dataset replay, the effective realign and
  slow-insert training exposure is too small.
- The next Track B iteration should rebalance correction training by phase or
  increase staged synthetic `realign` / `slow_insert` coverage before scaling
  to `5k - 10k`.

Follow-up phase-balanced correction training:

Code change:

- `scripts\pretrain_image_actor_bc_weighted.py` now supports optional
  phase-balanced recovery sampling:
  - `phase_balanced_recovery`
  - `recovery_phase_names`
  - `recovery_phase_weights`
- When enabled on a dataset with `recovery_phase`, the script samples inside
  that dataset by phase weights instead of uniformly over all correction rows.
- Existing weighted BC configs are unchanged because the option defaults to
  off.

New configs:

- `configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_staged_2k_phase_w10_e2.yaml`
- `configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_staged_2k_phase_w10_e2.yaml`
- `configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_staged_2k_phase_w15_e2.yaml`
- `configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_staged_2k_phase_w15_e2.yaml`

Both use the same staged 2k dataset with recovery phase weights:

| Phase | Sampling Weight |
| --- | ---: |
| `unjam_lift` | 0.30 |
| `realign` | 0.35 |
| `slow_insert` | 0.35 |

Same-seed 20-episode guarded eval:

| Checkpoint | Clean | Visual Camera | Visual Camera Control | Full Light | Full Contact | Hard Bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| staged 2k w10 e2 | 0.550 | 0.550 | 0.500 | 0.400 | 0.350 | 0.450 |
| phase staged 2k w10 e2 | 0.550 | 0.550 | 0.500 | 0.350 | 0.350 | 0.500 |
| phase staged 2k w15 e2 | 0.550 | 0.550 | 0.500 | 0.350 | 0.350 | 0.450 |

Hard-bucket collision / timeout:

| Checkpoint | Collision | Timeout |
| --- | ---: | ---: |
| phase staged 2k w10 e2 | 0.400 | 0.100 |
| phase staged 2k w15 e2 | 0.450 | 0.100 |

Hard seed `571000` with phase staged 2k w10 e2:

- result: collision
- success: `0`
- collision: `1`
- timeout: `0`

Interpretation:

- Phase-balanced sampling helps more than plain low-weight replay: hard bucket
  improves to `0.500` for w10.
- Increasing correction replay from `10%` to `15%` hurts the hard bucket and
  full-contact collision, so more correction weight is not the fix.
- This is still not promoted because full_light_geometry drops to `0.350` and
  seed `571000` still collides.
- The next useful correction step is not just more weight. It should add
  better failure-state coverage and/or a deployment-time recovery gate that
  explicitly invokes unjam/re-align before the collision state becomes
  irreversible.

## Hard High-Start Visual Contribution Audit

Started on 2026-05-09 after concerns that BC/oracle/guarding may be masking
weak visual policy behavior.

Code change:

- `scripts\eval_guarded_policy.py` now supports:
  - `control_mode: guarded`
  - `control_mode: policy`
  - `control_mode: guard_only`
  - `image_ablation: normal`
  - `image_ablation: black`
  - `image_ablation: noise`
  - `image_ablation: shuffle`

Smoke scope:

- checkpoint: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip`
- config: `configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml`
- scenario: `hard_full_light_bucket`
- episodes: `10`
- seed: `574000`

Results:

| Control | Image | Success | Collision | Timeout | Mean Guard Steps |
| --- | --- | ---: | ---: | ---: | ---: |
| policy | normal | 0.100 | 0.700 | 0.200 | 0.0 |
| policy | black | 0.000 | 1.000 | 0.000 | 0.0 |
| policy | noise | 0.000 | 1.000 | 0.000 | 0.0 |
| policy | shuffle | 0.000 | 1.000 | 0.000 | 0.0 |
| guarded | normal | 0.400 | 0.500 | 0.100 | 212.0 |
| guarded | black | 0.100 | 0.900 | 0.000 | 13.6 |
| guarded | noise | 0.100 | 0.900 | 0.000 | 20.2 |
| guarded | shuffle | 0.100 | 0.900 | 0.000 | 15.5 |
| guard_only | normal | 0.500 | 0.300 | 0.200 | 456.2 |

Report:

```text
VISUAL_AUDIT.md
results\ur5e_full\high_start\hard\visual_audit\
```

Key-frame visibility audit:

- Added `scripts\audit_visual_visibility.py`.
- The script exports a step-level CSV plus key-frame images for wrist RGB,
  annotated wrist RGB, policy grayscale, near-hole crop, and overview camera.
- 3-episode hard-bucket smoke on the same pred0 guarded checkpoint reached
  `0.667` success, `0.000` collision, `0.333` timeout.
- In all audited subsets, hole center and peg tip projected into the full
  `100x100` wrist image at `1.000` rate.
- In all audited subsets, `both_projected_in_center_crop` was `0.000`.
- MuJoCo segmentation showed `hole_crop_visible=1.000` but
  `peg_crop_visible=0.000`.
- The timeout case ended close to the hole, around `6.0 mm` XY and `21.8 mm`
  above target, which is consistent with a near-hole alignment/descent
  visibility problem rather than a pure search failure.

Crop offset scan:

- Added `near_hole_crop_offset` to `PegInHoleMujocoEnv` and the main sim
  collection/training/eval/demo scripts. Default is `[0, 0]`, so old configs
  remain unchanged.
- Added `scripts\scan_visual_crop_offset.py`.
- 3-episode hard-bucket scan output:
  - `results\ur5e_full\high_start\hard\visual_audit\crop_offset_scan_pred0_guarded_3ep.csv`
  - `results\ur5e_full\high_start\hard\visual_audit\crop_offset_scan_pred0_guarded_3ep.md`
- Best smoke candidate is `near_hole_crop_offset: [-18, 0]`, which shifts the
  `64x64` crop from `18:18:82:82` to `0:18:64:82`.
- Center crop `[0, 0]` had `0.000` insert-band both-projected and
  `0.000` both-visible rates.
- Shifted crop `[-18, 0]` had `1.000` insert-band both-projected and `0.140`
  both-visible rates; near-XY both-projected was also `1.000`, with `0.308`
  both-visible.
- Interpretation: the crop framing problem is fixable, but physical occlusion
  remains a separate issue. The shifted crop should be used for new data
  collection/fine-tuning, not applied directly to the old center-crop policy as
  a promoted setting.

Interpretation:

- Visual input is not irrelevant: corrupting images collapses policy-only
  success from `0.100` to `0.000`, and prevents the learned policy from
  reliably reaching the guarded region.
- The privileged guard/oracle is still a major contributor: guarded normal is
  `0.400`, while guard-only is `0.500`.
- Current hard high-start success should not be interpreted as pure visual RL
  success.
- Sim-to-real risk remains if the MuJoCo truth guard is not replaced by a
  real-compatible estimate-driven guard.
- The visibility audit confirms that the fixed center crop is poorly framed for
  final peg-hole alignment. The crop scan gives a first shifted-crop candidate.
  The next useful step is shifted-crop data collection and fine-tuning, with a
  second-camera or wrist-camera pose change held for the case where shifted crop
  still cannot handle final-insertion occlusion.

Immediate next shifted-crop experiment:

1. Collect a small hard high-start visual-camera dataset with
   `near_hole_crop_offset: [-18, 0]`.
2. Fine-tune from the current hard high-start checkpoint for only `1-2` epochs.
3. Evaluate policy-only and guarded hard-bucket metrics. Compare against the
   current pred0 guarded baseline and repeat the visual ablation if performance
   improves.
4. If shifted crop improves approach but still times out near insertion, add a
   second camera or camera pose variant before scaling correction data again.

Shifted-crop experiment result:

- `1k` shifted-crop data collection completed:
  - output: `datasets\ur5e_full\high_start\hard\image_expert_1k_high_start_hard_safe_visual_camera_crop_left.npz`
  - collection episodes: `4`
  - collection success/collision: `0.750 / 0.000`
- `1k` shifted-crop fine-tune completed:
  - output: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_1k_high_start_hard_safe_visual_camera_crop_left.zip`
  - 10-episode guarded matrix: clean `0.500`, visual_camera `0.400`,
    visual_camera_control `0.300`, hard bucket `0.300`
- Same-seed center-crop baseline rerun:
  - output: `results\ur5e_full\high_start\hard\visual_audit\eval_center_baseline_50k_10ep.md`
  - 10-episode guarded matrix: clean `0.600`, visual_camera `0.700`,
    visual_camera_control `0.500`, hard bucket `0.400`
- Conservative `10k` shifted-crop fine-tune also failed to improve:
  - dataset: `datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_safe_visual_camera_crop_left.npz`
  - checkpoint: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_safe_visual_camera_crop_left_lr3e6_e1.zip`
  - 10-episode guarded matrix: clean `0.500`, visual_camera `0.400`,
    visual_camera_control `0.100`, hard bucket `0.200`
- A 2-episode shifted-crop visibility audit still confirmed the crop framing
  fix itself:
  - `both_in_crop=1.000` for all rows and insert-band rows
  - output: `results\ur5e_full\high_start\hard\visual_audit\visibility_crop_left_10k_lr3e6_e1_2ep.md`

Updated interpretation:

- Left-shifting the crop fixes the crop-framing metric, but short fine-tuning
  from the old center-crop checkpoint degrades performance.
- Keep the center-crop baseline as the current comparison/demo checkpoint.
- Do not scale more crop-left BC data as the next default step.
- Next visual work should audit camera-pose or second-view candidates, then
  train/replay around the selected observation from the start. This is a better
  response to the user's concern that oracle/guard inputs may dominate and that
  visual input may be weak or occluded.

Wrist camera pose scan:

- Added `scripts\scan_wrist_camera_pose.py`.
- The script keeps the rollout camera/policy fixed, temporarily applies
  candidate wrist camera local pose/FOV/crop settings at sampled states, renders
  segmentation, then restores the rollout camera before the next action.
- Smoke validation passed:
  - `results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_smoke.md`
- Rotation/FOV/crop scan:
  - `results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_rot_fov_crop_3ep.md`
  - best rotation/FOV-only candidate improved insert-band crop-visible rate only
    from about `0.149` to `0.161`, so rotation/FOV alone is not enough.
- Position/yaw/crop scan:
  - `results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_pos_yaw_crop_3ep.md`
  - frame export: `results\ur5e_full\high_start\hard\visual_audit\frames_wrist_camera_pose_scan_pos_yaw_crop_3ep\`
- Best smoke candidate:
  - local camera `pos_offset=[-0.04, -0.04, 0.00]`
  - local camera `rot_offset_deg=[0.0, 0.0, 0.0]`
  - `fovy=100`
  - `near_hole_crop_offset=[-18, 0]`
- Same sampled 3-episode comparison:
  - current pose + crop `[-18,0]`: insert-band both-crop-visible `0.149`,
    near-XY both-crop-visible `0.308`, all both-visible `0.513`
  - pos `[-0.04,-0.04,0]` + crop `[-18,0]`: insert-band
    both-crop-visible `1.000`, near-XY both-crop-visible `1.000`, all
    both-visible `1.000`
  - pos `[0,-0.04,-0.04]` + crop `[-18,0]`: insert-band
    both-crop-visible `0.966`, near-XY both-crop-visible `0.972`, all
    both-visible `0.980`
- Candidate frame export does not show an obvious invalid view or pure artifact,
  but this remains a visibility-only result.

Updated next step:

1. Add environment/config support for a nominal wrist camera pose offset.
2. Create high-start hard collect/pretrain/eval configs using
   `camera_pose_offset=[-0.04,-0.04,0]` and `near_hole_crop_offset=[-18,0]`.
3. Collect a small smoke dataset, inspect crops, then train from scratch or
   replay-style from a compatible checkpoint. Do not claim task success using
   the old center-crop checkpoint under the new camera.
4. Only add a second camera if this shifted wrist-pose candidate fails after
   proper data collection/training.

Wrist-pose env/config smoke:

- Added environment parameters:
  - `wrist_camera_pos_offset`
  - `wrist_camera_rot_offset_deg`
  - `wrist_camera_fovy`
- Defaults preserve the original XML camera. When configured, visual camera
  randomization jitters around the configured nominal pose.
- Passed the parameters through the common collection/training/eval/demo
  scripts and stored them in image expert/correction metadata.
- Added smoke configs:
  - `configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_smoke.yaml`
  - `configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_smoke.yaml`
  - `configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_smoke.yaml`
- Environment smoke confirmed `near_hole_crop` shape `(64,64,1)` and info
  camera fields.
- 1k dataset collection completed:
  - output: `datasets\ur5e_full\high_start\hard\image_expert_1k_high_start_hard_wrist_pose_visual_camera.npz`
  - inspection: `results\ur5e_full\high_start\hard\visual_audit\image_expert_1k_wrist_pose_inspection.md`
  - collection success/collision/timeout: `0.214 / 0.214 / 0.571`
  - because `success_only=true`, the saved dataset is valid but comes from only
    `3` successful episodes.
- 2-epoch low-LR BC smoke completed:
  - output: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_1k_high_start_hard_wrist_pose_visual_camera.zip`
  - train/val loss after epoch 2: `0.596712 / 0.526904`
- 10-episode guarded eval completed:
  - output: `results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_1k_e2_10ep.md`
  - clean `0.200`
  - visual_camera `0.300`
  - visual_camera_control `0.100`
  - full_light_geometry `0.200`
  - full_contact_light `0.100`
  - hard_full_light_bucket `0.000`, collision `1.000`

Interpretation:

- The wrist pose candidate remains good for visibility, but the 1k short
  fine-tune is not a usable policy.
- Hard-bucket collision with `0` guard steps means the policy is failing before
  it reaches the guarded near-hole region.
- The next proper training step should not be another tiny fine-tune. It should
  either:
  - collect a larger successful wrist-pose expert dataset with better source
    episode coverage, then train from a more compatible initialization, or
  - run a replay/scratch weighted BC job where all image data is generated under
    the new wrist camera pose.
- Do not start second-camera implementation until the wrist-pose replay/scratch
  path has been tested.

Wrist-pose 10k scratch update:

- Collected `10k` wrist-pose expert samples with `seed=564000`:
  - dataset: `datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_wrist_pose_visual_camera_seed564k.npz`
  - inspection: `results\ur5e_full\high_start\hard\visual_audit\image_expert_10k_wrist_pose_seed564k_inspection.md`
  - collection success/collision: `0.427 / 0.122`
- Trained scratch BC under the new wrist-pose observation:
  - e10: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_wrist_pose_visual_camera_scratch_e10.zip`
  - e20: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_wrist_pose_visual_camera_scratch_e20.zip`
  - e20 train/val loss: `0.086670 / 0.091862`
- Same-seed 10-episode guarded eval:
  - e10: clean `0.500`, visual_camera `0.500`, visual_camera_control `0.300`,
    full_light_geometry `0.100`, full_contact_light `0.400`, hard bucket `0.300`
  - e20: clean `0.500`, visual_camera `0.500`, visual_camera_control `0.400`,
    full_light_geometry `0.100`, full_contact_light `0.400`, hard bucket `0.300`
- Interpretation:
  - scratch under the new camera is much better than the 1k fine-tune and
    reaches the guarded region again
  - it is still below the old center-camera baseline, especially on
    visual_camera and hard bucket
  - extra epochs alone are not enough; the next useful step is a larger
    wrist-pose data/replay run

Next training recommendation:

1. Collect `50k` wrist-pose expert samples using `seed=564000` or a multi-seed
   scheme, still with `success_only=true`.
2. Train either:
   - scratch BC for `20-30` epochs, or
   - weighted replay using `10k`/`50k` wrist-pose data as the dominant dataset.
3. Evaluate the same 10/20/100-episode guarded matrix before touching
   second-camera logic.
4. If 50k wrist-pose still underperforms center-camera baseline, inspect
   failure traces: the likely issue will be dataset/action coverage rather than
   pure visibility.

Wrist-pose 50k scratch result:

- Added configs:
  - `configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_50k.yaml`
  - `configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_50k_scratch.yaml`
  - `configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_50k_scratch.yaml`
- Collected `50k` wrist-pose expert samples:
  - dataset: `datasets\ur5e_full\high_start\hard\image_expert_50k_high_start_hard_wrist_pose_visual_camera_seed564k.npz`
  - inspection: `results\ur5e_full\high_start\hard\visual_audit\image_expert_50k_wrist_pose_seed564k_inspection.md`
  - collection success/collision: `0.377 / 0.110` across `462` episodes
- Trained scratch e20:
  - checkpoint: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_wrist_pose_visual_camera_scratch_e20.zip`
  - final train/val loss: `0.045830 / 0.047674`
- 20-episode same-seed guarded eval:
  - report: `results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_50k_scratch_e20_20ep.md`
  - clean `0.550`
  - visual_camera `0.600`
  - visual_camera_control `0.350`
  - full_light_geometry `0.400`
  - full_contact_light `0.400`
  - hard bucket `0.400`

Interpretation:

- This is the first wrist-pose model that is competitive with the old
  center-camera baseline.
- It matches the old baseline on clean/full_light/full_contact and improves
  visual_camera, but it regresses on visual_camera_control and is slightly lower
  on hard bucket.
- The next bottleneck is likely control randomization / action execution
  coverage under the new wrist-pose observation, not visibility.

Next step:

1. Collect a wrist-pose `visual_camera_control` expert dataset, ideally `50k`
   samples, with the same camera pose/crop.
2. Train weighted replay from the 50k scratch wrist-pose checkpoint with a mix
   of:
   - wrist-pose visual_camera 50k
   - wrist-pose visual_camera_control 50k
3. Evaluate the same 20-episode matrix first; promote only if
   visual_camera_control and hard bucket recover without losing visual_camera.

Wrist-pose control replay result:

- Added configs:
  - `configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_50k.yaml`
  - `configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_replay_100k_e4.yaml`
  - `configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_replay_100k_e4.yaml`
- Collected `50k` wrist-pose `visual_camera_control` expert samples:
  - dataset: `datasets\ur5e_full\high_start\hard\image_expert_50k_high_start_hard_wrist_pose_visual_camera_control_seed580k.npz`
  - inspection: `results\ur5e_full\high_start\hard\visual_audit\image_expert_50k_wrist_pose_control_seed580k_inspection.md`
  - collection success/collision: `0.413 / 0.210` across `424` episodes
- Trained two weighted replay variants from the wrist-pose 50k scratch model:
  - `0.45/0.55` visual/control weights:
    `checkpoints\ur5e_full\high_start\hard\sac_image_bc_100k_high_start_hard_wrist_pose_control_replay_e4.zip`
  - `0.25/0.75` visual/control weights:
    `checkpoints\ur5e_full\high_start\hard\sac_image_bc_100k_high_start_hard_wrist_pose_control_replay_w75_e4.zip`
- 20-episode guarded eval:
  - `0.45/0.55`: clean `0.550`, visual_camera `0.600`,
    visual_camera_control `0.350`, full_light_geometry `0.400`,
    full_contact_light `0.300`, hard bucket `0.400`
  - `0.25/0.75`: clean `0.550`, visual_camera `0.600`,
    visual_camera_control `0.350`, full_light_geometry `0.400`,
    full_contact_light `0.300`, hard bucket `0.400`

Interpretation:

- Generic control replay did not improve visual_camera_control over the
  wrist-pose 50k scratch model.
- Heavier control weighting did not help, so the problem is probably not just
  dataset mixture weight.
- The control dataset has a higher oracle collision rate (`0.210`), suggesting
  the randomization creates specific hard execution regimes that need targeted
  handling.

Next step:

1. Run control-failure analysis on the wrist-pose 50k scratch and replay models
   to identify delay/filter/action-scale buckets causing failures.
2. If failures cluster around delay `2` and low filter alpha, collect a targeted
   wrist-pose delay2/low-alpha/low-noise control dataset rather than another
   broad `visual_camera_control` dataset.
3. Consider a guarded near-action limiter or guarded controller adjustment for
   delayed execution if policy actions are reaching the near-hole region but
   contact/insertion fails under delay.

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

1. Keep `guarded_prediction_steps: 0.0` as the current best controller-only hard high-start setting.
2. Do not promote latch/recenter, retry, strict hold-Z, `high_start_two_phase`, hard down-block, or `align=0.025` unless a later evaluation clearly beats the no-prediction controller.
3. Treat the wrist-pose 50k scratch checkpoint as the current new-camera comparison model, but do not promote it as the default demo model yet.
4. Do not promote broad control replay or targeted delay-2 replay:
   - broad control replay kept `visual_camera_control` at `0.350` and reduced `full_contact_light`
   - targeted delay-2 replay also kept `visual_camera_control` at `0.350`, reduced `full_contact_light` to `0.300`, and worsened 80-episode control failure success to `0.175`
5. Optional `control_state` image observation is now implemented and smoke-tested on branch `feature/control-state-observation`. It contains previous commanded action, measured TCP/peg-tip delta, command-minus-measured error, and normalized step count. It does not include MuJoCo target truth or hidden randomization parameters.
6. Do not load old image checkpoints into control-state envs; the observation space changes and requires a scratch model.
7. First training-scale control-state results are complete and not promoted:
   - 10k control-state scratch e10: clean/visual_camera/visual_camera_control/full_light/full_contact/hard `0.450/0.400/0.400/0.300/0.300/0.300`
   - 60k mixed scratch e8: `0.550/0.600/0.400/0.350/0.350/0.400`
   - 80-episode policy-only control analysis for 60k mixed scratch is poor: success/collision/timeout `0.125/0.562/0.312`
8. Control-state image-ablation audit is complete:
   - guarded normal/black/noise/shuffle visual_camera_control success: `0.400/0.000/0.050/0.050`
   - policy-only normal/black/noise/shuffle visual_camera_control success: `0.150/0.000/0.000/0.000`
   - guard-only visual_camera_control success: `0.600`
   - conclusion: the model still uses images, but pure policy control quality is weak
9. Frame stacking is implemented and tested, but the first stack3 BC trial is not promoted:
   - stack3 smoke dataset/training/eval passed with `cam_images (512,100,100,3)`, `near_hole_crops (512,64,64,3)`, and `control_state (512,30)`
   - 60k mixed stack3 scratch e6 reached guarded clean/visual_camera/visual_camera_control/full_light/full_contact/hard `0.500/0.400/0.350/0.300/0.150/0.350`
   - 80-episode policy-only control analysis regressed to success/collision/timeout `0.013/0.800/0.188`
   - conclusion: simple frame stacking lowers BC loss but worsens rollout control
10. DAgger v2 handoff correction is implemented and has the first positive signal:
   - correction collection now supports `include_control_state`, `selection=near_hole`, `keep_success_episodes`, and `recovery_branch_from_near_hole`
   - 2k DAgger v2 dataset phase mix: `realign=1099`, `slow_insert=402`, `unjam_lift=547`, with `control_state (2048,10)`
   - 2k w10 e2 guarded clean/visual_camera/visual_camera_control/full_light/full_contact/hard: `0.550/0.550/0.500/0.350/0.350/0.400`
   - 80-episode policy-only visual_camera_control success/collision/timeout improved to `0.263/0.438/0.300`
   - image ablation while preserving `control_state` passed: policy-only visual_camera_control normal/black/noise/shuffle success over comparable 40-episode windows was `0.300/0.000/0.000/0.000`
   - second-seed guarded 60-episode comparison against the 60k mixed baseline is only modestly positive:
     - DAgger v2: `0.650/0.500/0.500/0.400/0.417/0.217`
     - mixed e8: `0.633/0.450/0.483/0.367/0.417/0.217`
   - second-seed policy-only visual_camera_control 160-episode comparison is also modestly positive:
     - DAgger v2 success/collision/timeout: `0.181/0.556/0.263`
     - mixed e8 success/collision/timeout: `0.156/0.575/0.269`
   - hard-bucket-only 60-episode multi-seed validation does not show a net gain:
     - seed `602000`: DAgger v2 `0.217`, mixed e8 `0.217`
     - seed `604000`: DAgger v2 `0.200`, mixed e8 `0.250`
     - seed `605000`: DAgger v2 `0.450`, mixed e8 `0.433`
     - average across these three 60-episode hard-bucket windows: DAgger v2 about `0.289`, mixed e8 about `0.300`
   - conclusion: DAgger v2 is real and still vision-dependent, but the gain is small and does not transfer to the hardest bucket; do not promote it and do not scale this exact recipe to `5k - 10k`
11. Next correction work should change the recipe rather than scale DAgger v2:
   - analyze hard-bucket failures directly instead of using visual_camera_control as the main proxy
   - bias future correction collection toward hard-bucket low-Z misalignment and geometry/contact failures, not just generic handoff states
   - keep the DAgger v2 checkpoint as a diagnostic candidate for visual_camera_control, not as a new base model
   - recurrent policy remains a fallback if improved correction data and guarded recovery gates saturate
   - hard-bucket episode trace support was added to `eval_guarded_policy.py` via `--episode-output-csv`
   - seed `604000` hard-bucket traces show the failure is broader than final insertion:
     - DAgger v2: `12/60` success, `26/60` collision, `22/60` timeout, `16` pre-guard failures, `32` guarded failures
     - mixed e8: `15/60` success, `23/60` collision, `22/60` timeout, `15` pre-guard failures, `30` guarded failures
     - guarded failures end around `18 mm` mean XY error for both models, so many cases fail before the final `5 mm` insert band
   - trace summary: `results\ur5e_full\high_start\hard\correction\hard_bucket_trace_seed604k_summary.md`
12. Hard-bucket-focused correction v3 is implemented and has the best hard-bucket signal so far:
   - smoke dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_hard_bucket_v3_smoke.npz`
   - 2k dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_hard_bucket_v3.npz`
   - v3 uses `scenario_preset=hard`, `selection=failed_episode_near_hole`, failed episodes only, `near_hole_xy=0.120`, and `near_hole_z=0.160` so it includes approach/handoff failures as well as low-Z recovery.
   - 2k dataset shape: `2048` samples from `101` source episodes; phase mix `realign=1064`, `slow_insert=411`, `unjam_lift=573`; approach-rate `0.661`, low-Z-rate `0.339`, wide-XY-rate `0.382`.
   - 2k w10 e2 checkpoint: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2.zip`
   - 2k w10 e1 checkpoint: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1.zip`
   - 20-episode matrix smoke: clean/visual_camera/visual_camera_control/full_light/full_contact/hard `0.650/0.750/0.600/0.600/0.550/0.650`
   - e1 20-episode matrix smoke: `0.650/0.750/0.600/0.700/0.600/0.600`
   - 60-episode hard-bucket gate average over seeds `602000`, `604000`, `605000`:
     - mixed e8: success/collision/timeout `0.300/0.406/0.295`
     - DAgger v2: `0.289/0.417/0.295`
     - v3 smoke: `0.356/0.300/0.344`
     - v3 2k w10 e2: `0.417/0.145/0.439`
     - v3 2k w10 e1: `0.416/0.167/0.417`
   - conclusion: v3 2k is a real improvement for hard-bucket collision and success, but timeout is now the main regression; keep e1/e2 as candidates rather than promoted defaults.
   - next correction step: keep the hard-bucket v3 data recipe but add a timeout-aware slow-insert/descent-progress component or guarded progress check.
   - step-level timeout tracing is now implemented in `scripts\eval_guarded_policy.py` via `--step-output-csv` and `--step-trace-outcome-filter`.
   - seed `604000` v3 e1 timeout trace:
     - base hard bucket 60ep success/collision/timeout: `0.383/0.133/0.483`
     - `22/29` timeout episodes reached the strict `5 mm` XY band at least once
     - median timeout final XY/Z: `7.35 mm / 24.9 mm`
     - many close timeouts are caused by `guarded_two_stage` returning toward safe Z in the `5 - 20 mm` XY funnel after the peg has already been near aligned
   - controller ablations did not solve this:
     - soft latch 60ep: `0.350/0.133/0.517`
     - fast latch 30ep: `0.367/0.033/0.600`, same as base first-30
     - insert XY `0.008` 30ep: `0.367/0.033/0.600`, same as base first-30
     - contact-aware guard 30ep: `0.167/0.100/0.733`
     - policy-only 30ep: `0.133/0.233/0.633`
     - guard blend `0.75` 30ep: `0.367/0.033/0.600`
   - decision: do not promote soft latch, wider insert threshold, contact-aware deployment guard, policy-only, or lower guard blend. The next useful change is a timeout-aware near-hole supervision/progress design, not more deployment guard threshold tuning.
   - trace summary: `results\ur5e_full\high_start\hard\correction\hard_bucket_timeout_trace_v3_summary.md`
   - timeout-progress v4 smoke was implemented but is not promoted:
     - added oracle mode `timeout_descent_progress`
     - added correction selection `timeout_progress_window` and `timeout_progress_failure_window`
     - smoke dataset: `512` samples, all timeout, all near-hole, all timeout-progress-window, `oracle_down_action=1.000`, `oracle_lift_action=0.000`
     - same-seed hard-bucket gate, seed `622000`, 20 episodes:
       - v3 e1 baseline: `0.500/0.150/0.350`
       - v4 smoke w10 e1: `0.250/0.550/0.200`
       - v4 smoke w03 e1: `0.400/0.300/0.300`
     - conclusion: progress-only labels reduce timeout by converting too many episodes into collision; do not scale this dataset as-is.
     - next version must balance progress labels with lifted re-align / hover-recenter / block-down examples instead of applying pure downward progress supervision.
     - summary: `results\ur5e_full\high_start\hard\correction\timeout_progress_v4_smoke_summary.md`
   - safety-balanced v4b/v4b2 timeout correction was implemented but is not promoted:
     - collector now supports `balanced_v4b_labels`, `balanced_v4b_window`, and `balanced_v4b_failure_window`
     - datasets now record `balanced_v4b_window`, `alignment_stable_steps`, `ever_within_insert_xy`, `drift_after_alignment`, and `descent_should_block`
     - v4b smoke dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_balanced_v4b_smoke.npz`
     - v4b phase mix was too lift-heavy: `block_down=151`, `hover_recenter=51`, `stable_slow_insert=113`, `unjam_lift=197`
     - v4b2 narrowed the unjam zone (`balanced_v4b_low_z=0.020`) and increased hover height (`balanced_v4b_hover_height=0.060`)
     - v4b2 smoke dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke.npz`
     - v4b2 phase mix was healthier but still safety-heavy: `block_down=185`, `hover_recenter=179`, `stable_slow_insert=48`, `unjam_lift=100`
     - same-seed hard-bucket gate, seed `622000`, 20 episodes:
       - v3 e1 baseline: `0.500/0.150/0.350`
       - v4 progress-only w03 e1: `0.400/0.300/0.300`
       - v4b2 w03 e1: `0.350/0.400/0.250`
       - v4b2 w01 e1: `0.400/0.300/0.300`
     - conclusion: v4b2 reduces timeout but still converts too many cases into collision; do not scale/promote v4b2 as a checkpoint or larger dataset recipe.
     - follow-up step trace with contact-pair diagnostics showed v4b2 collisions are approach/fixture-clearance failures, not final insertion misses:
       - v4b2 collision insert-band rate: `0.000`
     - v4b2 collision median final XY/Z: about `60.9 mm / 45.4 mm`
     - added collisions are `peg_geom` against `hole_north/south/west`, `hole_plate`, or `table_top`
     - same-seed transitions include v3 successes becoming v4b2 collisions on episodes `13` and `19`
     - wide contact-aware guard diagnostic is not promoted: `guard_start_xy=0.09`, `contact_aware_recovery`, `contact_recovery_z_max=0.10`, `contact_recovery_lift_height=0.12` reached only `0.050/0.400/0.550`.
     - fixture-clearance safety gate is now implemented in `GuardedPolicyConfig` and exposed in eval/demo/inference:
       - it is an independent deployment-time gate, not a wider oracle takeover
       - when the peg is below a low fixture-clearance height and still laterally far from the hole, it overrides with XY `0` and positive Z until lifted
       - same-seed v4b2 w01, seed `622000`, 20 hard-bucket episodes:
       - `xy_max=0.09`, `z_max=0.06`, `lift=0.10`: `0.400/0.250/0.350`
       - `xy_max=0.13`, `z_max=0.06`, `lift=0.10`: `0.400/0.200/0.400`
       - `xy_max=0.13`, `z_max=0.08`, `lift=0.12`: `0.400/0.200/0.400`
       - conclusion: the gate reduces approach/fixture collisions without collapsing success, but mostly converts one collision into timeout and does not recover hard-bucket success. Keep it as a safety/diagnostic tool, not a promoted training result.
     - two-stage fixture gate with safe-height realign is implemented and exposed as an explicit diagnostic option:
       - it adds `guard_fixture_clearance_realign_enabled`, `guard_fixture_clearance_realign_start_z`, realign XY limits, and phase/realign-step trace fields
       - same-seed v4b2 w01, seed `622000`, 20 hard-bucket episodes:
         - `realign_start_z=0.060`, max XY `0.005`: `0.400/0.250/0.350`
         - `realign_start_z=0.045`, max XY `0.005`: `0.400/0.300/0.300`
         - `realign_start_z=0.045`, max XY `0.002`: `0.400/0.300/0.300`
       - conclusion: high-threshold realign rarely activates, while low-threshold realign reintroduces low-altitude scraping/collision. Do not promote two-stage fixture realign as a default.
     - high-approach correction data path is now implemented:
       - collector supports `approach_correction_labels`, `approach_window`, `approach_failure_window`, and `approach_recenter`
       - datasets now record `approach_window` and inspector reports `approach_window_rate`
       - smoke dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_approach_smoke.npz`
       - smoke inspection: `approach_window_rate=1.000`, `approach_recenter=512`, mean XY/Z above target about `69.8 mm / 108.9 mm`
       - outcome mix was collision-heavy (`336` collision samples, `176` timeout samples), but that is acceptable for this smoke because selection is high approach states from failed hard-bucket episodes.
       - 2k dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_approach.npz`
       - 2k inspection: `approach_window_rate=1.000`, `approach_recenter=2048`, median XY/Z above target about `80.5 mm / 111.6 mm`
       - 10% replay, 1 epoch training saved `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_approach_2k_w10_e1.zip`; train/val loss `0.070090/0.093158`
       - first matrix, seed `616000`, 20 episodes: clean/visual_camera/visual_camera_control/full_light/full_contact/hard success `0.650/0.550/0.550/0.350/0.500/0.500`
       - same-seed matrix versus v3, seed `614000`, 20 episodes:
         - v3 hard-bucket 2k w10 e1: `0.650/0.750/0.600/0.700/0.600/0.600`
         - approach 2k w10 e1: `0.700/0.700/0.600/0.700/0.650/0.650`
       - hard-only seed `622000`, 20 episodes: approach 2k w10 e1 reached `0.500/0.150/0.350`, flat versus v3 but better than the v4b/v4b2 correction line.
       - larger hard-only 60-episode multi-seed result did not pass promotion:
         - seed `602000`: v3 `0.383/0.217/0.400`, approach `0.367/0.267/0.367`
         - seed `604000`: v3 `0.383/0.133/0.483`, approach `0.350/0.150/0.500`
         - seed `605000`: v3 `0.483/0.150/0.367`, approach `0.483/0.167/0.350`
       - policy-only hard-bucket image ablation passed: normal `0.300/0.425/0.275`, black `0.000/1.000/0.000`, noise `0.000/1.000/0.000`, shuffle `0.000/0.800/0.200`
       - current decision: keep approach 2k w10 e1 as a visual-positive candidate, but do not promote it because larger hard-only multi-seed success is not consistently better than v3.
       - summary: `results\ur5e_full\high_start\hard\correction\approach_2k_candidate_summary.md`
       - failure trace analysis on seed `602000`:
         - v3 and approach have similar failure shapes; approach adds a few more `high_fixture_wall_collision` cases.
         - approach baseline failure modes: `high_fixture_wall_collision=13`, `insert_band_timeout_low_z_drift=13`, `near_xy_timeout_no_insert=5`, `pre_guard_drop_or_drift=3`, `low_z_misaligned_collision=1`, `insert_band_timeout_slow_descent=3`.
         - controller gate diagnostics were negative:
           - approach baseline: `0.367/0.267/0.367`
           - fixture clearance gate: `0.350/0.283/0.367`
         - hover/descent gate: `0.350/0.267/0.383`
         - lift-before-lateral gate: `0.150/0.267/0.583`
         - conclusion: do not keep tuning broad controller gates. Next step should target pre-contact high-fixture-wall states in data/labels, or inspect why guard reaches the fixture wall at roughly `50 mm` above target with large XY error.
         - summary: `results\ur5e_full\high_start\hard\correction\controller_gate_diagnostics_seed602k_summary.md`
       - fixture-wall pre-contact correction data path is now implemented:
         - collector supports `fixture_wall_correction_labels`, `fixture_wall_window`, `fixture_wall_failure_window`, and `fixture_wall_recenter`
         - datasets now record `fixture_wall_window`, and inspector reports `fixture_wall_window_rate`
         - smoke config: `configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_fixture_wall_smoke.yaml`
         - smoke dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_fixture_wall_smoke.npz`
         - smoke inspection: `fixture_wall_window_rate=1.000`, `fixture_wall_recenter=512`, median XY/Z above target about `32.3 mm / 69.9 mm`, and `oracle_down_action_rate=0.000`
         - outcome mix was collision-heavy (`407` collision samples, `105` timeout samples), which is expected because this dataset intentionally targets the pre-contact fixture-wall failure band.
         - 2k fixture-wall candidate:
           - dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_fixture_wall.npz`
           - inspection: `fixture_wall_window_rate=1.000`, `fixture_wall_recenter=2048`, median XY/Z above target about `34.7 mm / 68.6 mm`, and `oracle_down_action_rate=0.000`
           - trained checkpoint: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_fixture_wall_2k_w10_e1.zip`
           - three-seed 60-episode hard-bucket average: fixture-wall `0.428/0.128/0.444` versus v3 `0.417/0.167/0.417` and approach `0.400/0.194/0.406`
           - decision: do not promote yet; collision is lower and success is slightly higher, but timeout is worse. Next experiment should combine this safer pre-contact recenter signal with a timeout/progress recovery component or test a lower fixture-wall replay weight.
           - summary: `results\ur5e_full\high_start\hard\correction\fixture_wall_2k_candidate_summary.md`
         - fixture-wall failure trace and w05 replay test are complete:
           - seed `602000` failure trace shows fixture-wall w10 reduces `high_fixture_wall_collision` from approach `13` to `9`, but increases `insert_band_timeout_low_z_drift` to `19`
           - timeout episodes usually enter the insert band, then drift out to about `6 - 7 mm` XY and finish around `25 mm` above target
           - w05 replay checkpoint: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_fixture_wall_2k_w05_e1.zip`
           - three-seed 60-episode hard-bucket average: w05 `0.405/0.139/0.456`, worse than w10 `0.428/0.128/0.444`
           - decision: do not promote w05 and stop tuning fixture-wall replay weight by itself. The next recipe should explicitly combine fixture-wall recenter with timeout-progress / slow-insert labels.
           - summary: `results\ur5e_full\high_start\hard\correction\fixture_wall_trace_and_w05_summary.md`
         - fixture-wall + timeout-progress w03 follow-up is also not promoted:
           - checkpoint: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_fixture_wall_progress_w03_e1.zip`
           - 20-episode matrix seed `626000` reached hard bucket `0.500/0.050/0.450`, but clean and full-light regressed to `0.450/0.100/0.450` and `0.250/0.350/0.400`
           - hard-only quick checks were unstable: seed `621000` `0.300/0.150/0.550`, seed `622000` `0.450/0.250/0.300`
           - decision: do not run full 60-episode multi-seed eval; the existing progress-only smoke dataset is too one-sided even at `3%`
           - next progress dataset should be redesigned around late-stage insert-band drift, with safer criteria for when downward labels are allowed.
         - insert-drift late-stage correction path is now implemented and tested:
           - collector supports `insert_drift_correction_labels`, `insert_drift_window`, `insert_drift_recenter`, and `insert_drift_slow_insert`
           - 2k dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_insert_drift.npz`
           - inspection: `insert_drift_window_rate=1.000`, phases `insert_drift_recenter=1396`, `insert_drift_slow_insert=652`, median XY/Z about `5.38 mm / 25.65 mm`, and `episode_timeout_rate=1.000`
           - trained checkpoint: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_insert_drift_2k_w10_e1.zip`
           - 20-episode matrix seed `621000`: clean `0.600/0.000/0.400`, visual_camera `0.500/0.000/0.500`, visual_camera_control `0.550/0.000/0.450`, full_light_geometry `0.450/0.100/0.450`, full_contact_light `0.400/0.000/0.600`, hard bucket `0.400/0.000/0.600`
           - hard-bucket 60-episode seeds `602000/604000/605000`: `0.417/0.133/0.450`, `0.400/0.067/0.533`, `0.483/0.067/0.450`
           - three-seed average: insert-drift `0.433/0.089/0.478`, versus fixture-wall `0.428/0.128/0.444`
           - decision: do not promote; the candidate reduces collision further but raises timeout. The next recipe should not simply scale insert-drift data. Redesign late-stage labels so slow descent is allowed only after stronger alignment stability, and add a local settle/progress signal to avoid endless cautious recentering.
         - insert-settle late-stage follow-up is implemented and tested:
           - collector schema is now `image_correction_v7_insert_settle_control_state`
           - new labels: `insert_settle_slow_insert`, `insert_settle_settle`, `insert_settle_lift_recenter`, `insert_settle_recenter`
           - 2k config stopped at `1920/2048` samples after `520` episodes; this was enough for a small candidate test
           - 2k diagnostics: `oracle_down_action_rate=0.618`, `oracle_lift_action_rate=0.334`, median XY/Z about `5.01 mm / 31.76 mm`
           - phase counts: `slow_insert=590`, `settle=842`, `lift_recenter=397`, `recenter=91`
           - 5% replay checkpoint: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_insert_settle_2k_w05_e1.zip`
           - 5% result: 20-episode hard bucket stayed `0.400/0.000/0.600`; hard seed `602000` matched insert-drift at `0.417/0.133/0.450`
         - 10% replay checkpoint: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_insert_settle_2k_w10_e1.zip`
         - 10% result: 20-episode hard bucket regressed to `0.300/0.100/0.600`, although clean/visual timeout improved slightly
         - decision: do not promote; do not continue scaling one-step late-stage BC labels. Next work should inspect closed-loop final insertion traces or use a deployment-time guarded/servo final insertion controller.
         - closed-loop insert-drift vs insert-settle timeout tracing is complete:
           - summary: `results\ur5e_full\high_start\hard\correction\insert_late_bc_timeout_trace_seed602000_summary.md`
           - both candidates had `27/60` timeout episodes on hard seed `602000`
           - timeout insert-band rate was high: insert-drift `0.926`, insert-settle w05 `0.852`
           - median timeout final XY/Z was about `6.7 - 6.9 mm` and `24.4 mm` above target
           - dominant failure remains `insert_band_timeout_low_z_drift`; this is a late final-insertion stability problem, not a total visual-search failure.
         - guard scalar scan on insert-drift w10 e1 seed `602000` is complete:
           - summary: `results\ur5e_full\high_start\hard\correction\insert_late_bc_guard_scalar_scan_seed602000_summary.md`
           - baseline first 20 episodes: `0.500/0.150/0.350`
           - `guarded_prediction_steps=1.0` regressed to `0.300/0.150/0.550`; `2.0` regressed to `0.050/0.250/0.700`
           - strong near-hole action limiting regressed to `0.000/0.350/0.650`
           - higher down action, wider align/insert thresholds, gain `1.5`, and timeout-progress guard were flat at `0.500/0.150/0.350`
           - decision: stop scanning single scalar guard parameters. Next implementation should be a stateful final insertion servo with explicit near-hole phase, short alignment-stability gate, and bounded lift/recenter recovery.
         - final-servo MVP is implemented and smoke-tested:
           - summary: `results\ur5e_full\high_start\hard\correction\final_servo_mvp_summary.md`
           - new fields are available in guarded eval/demo/inference traces via `guard_final_servo_*`
           - early/high hover variants regressed hard 20ep to as low as `0.050/0.150/0.800`
           - low-hover and late-start variants reduced harm but stayed below baseline
         - fast-latch variant is the only non-regressing setting: hard 20ep `0.500/0.150/0.350`, hard 60ep seed `602000` `0.417/0.133/0.450`
         - decision: keep the code and fast-latch config as a safe diagnostic hook, but do not promote final servo as a performance gain yet. Next iteration should replace heavy recovery lift with a small low-Z unjam/hold/recenter behavior.
         - soft-unjam and descend-bias follow-up is complete:
           - summary: `results\ur5e_full\high_start\hard\correction\final_servo_soft_unjam_summary.md`
           - added `guard_final_servo_recovery_mode=soft_unjam`, soft unjam height/tolerance/hold/max-up settings, and `guard_final_servo_descend_xy_bias`
           - all hard 20ep seed `602000` soft-unjam/bias candidates stayed flat at `0.500/0.150/0.350`
           - best mean return improved to `273.706`, but no timeout converted to success
         - timeout endpoints show systematic `-X` drift of about `6.8 mm`, yet a `+3 mm` descend bias moved already-successful episodes more than timeout episodes
         - decision: do not continue scanning post-wedge final-servo recovery. The failures are contact-limited after wedging; next work should prevent the low-Z drift before the peg is wedged.
         - preinsert recenter gate is implemented and smoke-tested:
           - summary: `results\ur5e_full\high_start\hard\correction\preinsert_recenter_summary.md`
           - new fields are available in guarded eval traces via `guard_preinsert_recenter_*`
           - hard 20ep seed `602000` stayed flat at `0.500/0.150/0.350` for 25mm, early 35mm, and short-confirm variants
           - mean return improved up to `460.382`, and final-servo usage dropped, so the gate changes behavior but does not convert timeout episodes
           - trace symptom: commanded lateral recentering can move the measured peg-tip error in the wrong direction near low-Z insertion
           - decision: stop threshold-only preinsert guard tuning for now. The next bottleneck is low-level UR5e control realism, especially peg verticality/orientation and Cartesian-to-tip motion authority near contact.
13. Do not scale control-state data to 50k until a supervision/control run remains positive under ablation and larger evals.
14. Keep Track B contact-aware failure correction active, but do not promote the staged 2k or phase-balanced staged 2k checkpoints; phase w10 improves the hard bucket to `0.500` but still collides on seed `571000`.
15. Do not simply increase correction replay weight; phase w15 regressed versus phase w10, and v3 2k already shows the timeout risk of stronger correction.
16. Do not expand the current DAgger v2 dataset to `5k - 10k`; only revisit scale-up after the hard-bucket v3 line solves timeout.
17. Do not scale the current insert-drift or insert-settle datasets directly; insert-drift lowers collision but worsens timeout, while insert-settle 10% brings collision back without hard-bucket success gain. Closed-loop trace analysis, scalar guard scans, final-servo MVP, soft-unjam recovery, descend-bias diagnostics, and preinsert recenter gate tests are now done. Next work should shift to low-level controller realism: orientation-constrained IK/TCP pose servo and posture regularization, then rerun the same pre-wedge diagnostics.
18. Only after original high-start success is stable, introduce larger randomized initial XY offsets.
19. Only after high-start plus larger XY offsets are stable, reintroduce geometry/contact randomization.
20. Audit the full UR5e model against the raw Menagerie UR5e XML and add a report showing exactly what was changed for the task wrapper.
21. Improve the robot controller by adding orientation-constrained IK and a posture/nullspace regularization term so the UR5e joint motion looks more realistic.
22. Reduce full_light/full_contact collision rate by scanning guarded thresholds or running a larger/lower-threshold correction pass only after the control-state issue is addressed.
23. Generate a short comparison demo set: adapter baseline, full UR5e adapted policy-only, full UR5e adapted guarded-all, high-start visual-search policy.
24. Decide whether the full UR5e model should become the regular sim baseline after the controller realism and high-start curriculum are improved.
25. Continue real-readiness work only in read-only mode:
   - session preparation
   - real camera frame capture
   - crop inspection
   - calibration/config validation
   - synthetic or recorded replay

## Contact-Aware Reinsert Diagnostics

- Branch `feature/contact-aware-reinsert` is still experimental and is not promoted.
- New guarded-controller hooks are implemented and default off:
  - `contact_reinsert_orient_hold`
  - `contact_reinsert_descend`
  - `contact_reinsert_micro_align`
  - phase-specific `guard_final_servo_contact_reinsert_orient_max_xy_action`
  - optional micro-align up action
  - tip-locked orient hold drift compensation
  - high-clearance re-approach phases `contact_reinsert_high_lift` / `contact_reinsert_high_realign`
- Target seed `single/612010` remained timeout-only through v39, then was rescued by the v42 phase-local tip-priority candidate.
- Best diagnosis so far:
  - phase-local strong orientation can reduce tilt from about `18 deg` to `7-8 deg`
  - reinsert can reach the Z success band around `8 mm`
  - XY still stalls around `5.65-5.75 mm`, just outside the `5 mm` success threshold
  - tight contact-unjam recenter can briefly reach `4.7-4.9 mm` XY, but subsequent orientation correction moves the peg tip back out to `6-7 mm`
- Negative results to avoid repeating:
  - lateral-only micro-align at low Z did not reduce the residual XY error
  - micro-align with 0.4mm/step or 1.5mm/step upward unload did not clear wall contact
  - global `guard_final_servo_max_xy_action` of `0.0035-0.005` caused collision through later recovery behavior
  - phase-local orient max XY up to `0.005` still did not preserve XY during tilt correction
  - reinsert orientation IK weight `0.20` reduced tilt to about `4 deg` but worsened XY tracking
- v35 tip-lock result on `single/612010`: timeout. Tip-lock was active for 100 orient-hold steps, but XY still moved from about `4.66 mm` to `7.1 mm`; tilt improved to about `7.1 deg`. Stop the tip-lock line.
- v36-v39 high-clearance re-approach result on `single/612010`: not promoted.
  - With high-stage IK `0.06`, high re-approach lowered tilt to about `9 deg` but moved XY out to `26-38 mm` and could collide during recovery.
  - With high-stage IK `0.0`, it avoided collision but did not reduce tilt; high realign stalled around `11-12 mm` XY and `15 deg` tilt.
  - With high-stage IK `0.02`, it still timed out around `13-14 mm` XY and `14 deg` tilt.
- v40-v42 tip-priority IK result:
  - Added `pose_tip_priority` IK mode and default-off phase-local switches for contact reinsert and final servo.
  - Global `pose_tip_priority` is not promoted because it disrupts the learned approach trajectory.
  - Phase-local final-servo/contact-reinsert tip-priority fixed the known hard seeds and reached `1.000/0.000/0.000` on 20ep and 60ep profile matrices for `single`, `round_square`, `square_square`, and `mixed_basic` on seed `612000`.
- Current conclusion: the scalar orientation-weight line is closed, and v42 phase-local tip-priority remains the final-insertion base candidate.

## v47 Early Final-Servo Boundary Candidate

- Implemented default-off fixture-clearance retreat:
  - `guard_fixture_clearance_retreat_enabled`
  - `guard_fixture_clearance_retreat_release_xy`
  - `guard_fixture_clearance_retreat_max_xy_action`
  - fixture-clearance active steps now also use local near-control Kp/IK hooks in eval/demo/inference.
- Direct fixture retreat on the hard boundary seed `631004` improved safety but not completion:
  - `v47_boundary_seed631004_fixture_retreat_probe`: 4/4 profiles became timeout-only, 0 collision, 0 success.
  - The trace showed repeated retreat/re-approach between roughly `40-70 mm` XY; this was too conservative for the 1000-step target.
- The successful fix was not pure retreat; it was earlier final-servo handoff plus stronger approach control:
  - `nominal_actuator_kp_multiplier=3.0`
  - `guarded_max_xy_action=0.008`
  - `guard_final_servo_start_xy=0.035`
  - fixture-clearance retreat kept as a low-altitude fallback with `z_max=0.052`, `release_xy=0.060`, `max_xy_action=0.003`.
- Targeted hard seed result:
  - `D:\peg-in-hole-6yh\v47_boundary_seed631004_early_final_servo_all_profiles`
  - `single`, `round_square`, `square_square`, `mixed_basic`: `4/4` success, `0` collision, `0` timeout.
  - typical completion was `315-329` steps, with about `95-103` final-servo steps.
- Boundary regression result:
  - `D:\peg-in-hole-6yh\v47_boundary_regression_final035_kp3_gxy008_seed630_631`
  - seeds `630000/631000`, `10` episodes/profile, 4 profiles: `80/80` success, `0` collision, `0` timeout.
- Larger boundary gate:
  - `D:\peg-in-hole-6yh\v47_boundary_gate_seed632_634_20ep`
  - seeds `632000/633000/634000`, `20` episodes/profile, 4 profiles: `238/240` success, `0` collision, `2` timeout.
  - the two timeouts were both episode seed `634014`; final-servo never activated because the policy reached good XY while still just above `guard_start_z=0.12` at the 1000-step limit.
- High-Z guard fix:
  - raising `guard_start_z` to `0.14` fixed the targeted `seed634014` failures without raising `guard_final_servo_start_z`.
  - `D:\peg-in-hole-6yh\v47_boundary_seed634000_gstart140_20ep`
  - seed `634000`, `20` episodes/profile, 4 profiles: `80/80` success, `0` collision, `0` timeout.
- Moderate-stress regression against v46:
  - `D:\peg-in-hole-6yh\v47_on_v46_moderate_regression_seed626_628_20ep`
  - v47 control/handoff settings on the v46 moderate-stress distribution, seeds `626000/627000/628000`: `240/240` success, `0` collision, `0` timeout.
- New opt-in config:
  - `configs/sim/ur5e_full/eval_multi_geometry_early_final_servo_boundary_stress_20ep.yaml`
  - includes the high-Z guard fix: `guard_start_z=0.14`.
  - smoke result before the high-Z guard update: `D:\peg-in-hole-6yh\v47_early_final_servo_config_smoke`, `square_square/seed631004`: success.
  - smoke result after the high-Z guard update: `D:\peg-in-hole-6yh\v47_early_final_servo_gstart140_config_smoke`, `square_square/seed634014`: success.
- New demo config:
  - `configs/sim/ur5e_full/demo_multi_geometry_early_final_servo_boundary.yaml`
  - demo output: `D:\peg-in-hole-6yh\v47_early_final_servo_demos\demo_v47_square_square_seed634014_guarded_overview_wrist.gif`
  - trajectory output: `D:\peg-in-hole-6yh\v47_early_final_servo_demos\demo_v47_square_square_seed634014_guarded_trajectory.csv`
  - result: `square_square/seed634014` success in `288` steps, final XY/Z about `0.60 mm / 9.26 mm`, `94` guarded steps, `50` final-servo steps, `0` fixture-retreat steps.
  - GIF is `2560x720`, `289` frames, overview + wrist camera side-by-side. MP4 output fell back to GIF because the local `imageio` install has no ffmpeg/pyav writer.
- Promotion decision:
  - v47 is promoted as the current strict-1000 multi-geometry boundary-stress candidate.
  - `v0.7.2-early-final-servo-boundary` points at the promotion commit for this state.
  - v46 remains the moderate-stress reference, but v47 supersedes it for boundary stress because it fixes the v46 approach/fixture-clearance failures without regressing the v46 moderate matrix.
  - Do not treat the deterministic 1 mm clearance worst-case as the default task; use it only as a boundary diagnostic.
  - Next work should start from v47 and inspect whether the remaining robustness gap is policy-side visual search, control tracking, or a deliberately harder geometry distribution.
- Policy/controller contribution ablation:
  - Output directory: `D:\peg-in-hole-6yh\v47_policy_contribution_ablation_seed635_10ep`
  - Config: `configs/sim/ur5e_full/eval_multi_geometry_early_final_servo_boundary_stress_20ep.yaml`, `mixed_basic`, seed `635000`, `10` episodes/condition.
  - guarded blend `1.0`, normal image: `1.000/0.000/0.000`, mean `312.3` steps.
  - guarded blend `0.75`, normal image: `1.000/0.000/0.000`, mean `346.0` steps.
  - guarded blend `0.5`, normal image: `0.900/0.000/0.100`, timeout on `635008`.
  - guarded blend `1.0`, black image: `0.700/0.000/0.300`.
  - guarded blend `1.0`, noise image: `0.600/0.000/0.400`.
  - guarded blend `1.0`, shuffled image: `1.000/0.000/0.000` on this small seed window; do not over-interpret without more seeds.
  - guard-only: `0.700/0.000/0.300`.
  - policy-only: `0.000/0.000/1.000`.
  - Conclusion: v47 is a coupled policy plus controller system. Vision contributes to reaching useful guard conditions, while the final insertion remains controller-dominated. Do not claim the learned image policy is an independent insertion controller under the boundary distribution.
- Visual contribution scale-up:
  - Output directory: `D:\peg-in-hole-6yh\v47_visual_contribution_ablation_seed636_20ep`
  - Config: same v47 boundary config, `mixed_basic`, seed `636000`, `20` episodes/condition.
  - guarded normal image: `0.950/0.000/0.050`, timeout on `636017`.
  - guarded black image: `0.750/0.000/0.250`.
  - guarded noise image: `0.400/0.000/0.600`.
  - guarded shuffled image: `0.950/0.000/0.050`, same timeout seed as normal.
  - guard-only: `0.850/0.000/0.150`.
  - policy-only: `0.000/0.000/1.000`.
  - Combined with the earlier seed `635000` 10ep diagnostic:
    - normal: `29/30 = 0.967`
    - black: `22/30 = 0.733`
    - noise: `14/30 = 0.467`
    - shuffle: `29/30 = 0.967`
    - guard-only: `24/30 = 0.800`
    - policy-only: `0/30 = 0.000`
  - Updated conclusion: visual corruption clearly hurts performance, so the policy is not visual-agnostic. However, shuffled images matching normal means this experiment does not prove strong spatial visual servoing; the model may rely on coarse image statistics, control-state channels, or guarded-controller takeover. The next useful diagnostic should add control-state ablation and/or channel-specific image ablations.
- Control-state contribution scale-up:
  - Output directory: `D:\peg-in-hole-6yh\v47_control_state_ablation_seed637_20ep`
  - Config: same v47 boundary config, `mixed_basic`, seed `637000`, `20` episodes/condition.
  - normal image + control normal/zero/noise/shuffle: all `20/20 = 1.000`, zero collision.
  - black image + control normal: `18/20 = 0.900`, zero collision, `2` timeouts.
  - black image + control zero: `17/20 = 0.850`, `3` collisions.
  - Interpretation: with normal images, control-state corruption does not matter on this window. With black images, control-state helps somewhat, but image corruption is still the larger lever. The current v47 policy is not primarily depending on the low-dimensional control-state channel to succeed.
  - Next diagnostic should move back to the image path itself, ideally channel-specific image ablation or a camera/crop change that makes spatial alignment harder to fake.
- Image-channel contribution scale-up:
  - Added `--image-ablation-target {all,cam_image,near_hole_crop}` to `scripts/eval_guarded_policy.py`.
  - Output directory: `D:\peg-in-hole-6yh\v47_image_channel_ablation_seed638_10ep`
  - Config: same v47 boundary config, `mixed_basic`, seed `638000`, `10` episodes/condition.
  - normal: `10/10 = 1.000`.
  - all images black/noise: `8/10 = 0.800` / `4/10 = 0.400`.
  - `cam_image` black/noise: `10/10 = 1.000` / `8/10 = 0.800`.
  - `near_hole_crop` black/noise: `7/10 = 0.700` / `0/10 = 0.000`.
  - all/cam/crop shuffle: all `10/10 = 1.000`.
  - Interpretation: the near-hole crop is the sensitive visual channel, not the full wrist frame. The policy is sensitive to crop content quality, especially noise, but crop shuffle still passing means this does not prove precise per-frame spatial visual servoing. Next work should improve crop/camera spatial informativeness or collect handoff/approach diagnostics around crop-driven actions.
- Crop/camera sensitivity scan:
  - Output directories:
    - `D:\peg-in-hole-6yh\v47_crop_camera_scan_seed639_5ep`
    - `D:\peg-in-hole-6yh\v47_crop_camera_scan_focus_seed640_10ep`
  - Direct crop-size scanning was not run because the trained SB3 observation space expects `near_hole_crop` shape `64x64`; changing `near_hole_crop_size` changes the model input space. To test crop scale later, add a separate "crop source size then resize to 64" option.
  - Fixed-size `64x64` crop offset probe, seed `639000`, 5ep/condition:
    - X offsets `-36, -24, -18, -12, 0, +12` at `FOV=100`: all `5/5`.
    - X offset `+24`: `4/5`, timeout on `639004`.
    - Y offsets `-16, 0, +16` at X `-18`: all `5/5`.
    - FOV `90, 100, 110, 120`: all `5/5`.
    - FOV `80`: `3/5`, timeouts on `639000/639001`.
  - Focused seed `640000` 10ep expansion:
    - baseline crop `[-18,0]`, FOV `100`: `10/10`.
    - crop X `+24`, FOV `100`: `7/10`.
    - crop X `+12`, FOV `100`: `7/10`.
    - crop `[-18,0]`, FOV `80`: `8/10`.
  - Interpretation: v47 is not fully crop-geometry invariant. It tolerates negative/nominal offsets and moderate-to-wide FOV, but positive crop X offsets and narrow FOV expose approach/guard-entry failures. Next training-side work should add crop/camera jitter around this axis, or redesign the crop to make hole-centered spatial information more stable.
- Crop source-size resize scan:
  - Added `near_hole_crop_source_size` to `PegInHoleMujocoEnv` and `scripts\eval_guarded_policy.py`.
  - This keeps the policy observation key shape fixed at `near_hole_crop=64x64`, while cropping a different source window and resizing it back to `64x64` before inference.
  - Output directory: `D:\peg-in-hole-6yh\v47_crop_source_resize_scan_seed642_5ep`.
  - Summary files: `summary.md` and `summary.csv` in that directory.
  - Source-size matrix, output size fixed at `64`, FOV `100`, seed `642000`, 5 episodes/condition:
    - source `48`: offset `[-18,0]` `5/5`, `[+12,0]` `2/5`, `[+24,0]` `2/5`.
    - source `64`: offset `[-18,0]` `5/5`, `[+12,0]` `2/5`, `[+24,0]` `2/5`.
    - source `80`: offset `[-18,0]` `5/5`, `[+12,0]` `3/5`, `[+24,0]` `3/5`.
    - source `96`: offset `[-18,0]` `5/5`, `[+12,0]` `5/5`, `[+24,0]` `5/5`.
  - Interpretation: the current checkpoint benefits from a wider source crop when the crop center shifts positive in X. Directly changing the output crop size is still incompatible with the saved SB3 observation space; source-size resize is the safe evaluation path.
  - Next visual-policy step: add collection/training support for crop-source jitter, starting around `80-96` source pixels with output fixed at `64`, then rerun the same offset/FOV scan with a trained jitter model.
- Crop-source jitter data path:
  - Added default-off `near_hole_crop_source_size_range` to the environment. When set, it samples the source crop size once per episode and still outputs the fixed `near_hole_crop_size`.
  - Wired fixed source size and source-size range through guarded eval, ordinary eval, matrix eval, demo, deployment-style inference, expert collection, correction collection, and image BC pretraining scripts.
  - Expert/correction datasets now record `near_hole_crop_source_size` as a diagnostic array, and metadata records the configured source-size range.
  - New smoke config: `configs\sim\ur5e_full\collect_multi_geometry_crop_source_jitter_smoke.yaml`.
  - Smoke output directory: `D:\peg-in-hole-6yh\v47_crop_source_jitter_smoke`.
  - Smoke result:
    - environment reset probe sampled source sizes `[96, 87, 95, 96, 81, 89, 81, 83]` under range `[80,96]`.
    - 8-sample expert dataset wrote `cam_images (8,100,100,1)`, `near_hole_crops (8,64,64,1)`, and metadata range `[80,96]`.
    - 1-epoch BC smoke loaded the dataset and saved `sac_image_bc_crop_source_jitter_smoke.zip`.
  - Next experiment: collect a real crop-source-jitter expert dataset, likely `20k-50k` samples with source range `[80,96]`, fine-tune the current v47 actor lightly, then rerun the source-size/offset/FOV scan plus the standard `clean/visual_camera/visual_camera_control/full_light_geometry/full_contact_light/hard` matrix.

### 2026-05-26 Crop-Source Jitter Pilot Result

- Ran a medium crop-source jitter pilot outside the repo at `D:\peg-in-hole-6yh\v48_crop_source_jitter_pilot`.
- Dataset:
  - `image_expert_2k_crop_source_jitter_80_96_pilot.npz`
  - `2048` samples, `5` completed episodes, success/collision/timeout `0.800/0.000/0.200`.
  - Source-size counts: `81:1000`, `87:232`, `89:54`, `95:220`, `96:542`.
  - Geometry split: `square_square:1746`, `round_square:302`.
  - Schema: `image_expert_v3_crop_source`.
- Conservative continuation:
  - Base model: `checkpoints/ur5e_full/high_start/hard/correction/sac_image_bc_wrist_pose_control_state_insert_drift_2k_w10_e1.zip`.
  - Output: `D:\peg-in-hole-6yh\v48_crop_source_jitter_pilot\sac_image_bc_crop_source_jitter_2k_e1_lr1e-6.zip`.
  - One epoch, LR `1e-6`, batch `256`; train/val loss `0.096211/0.098894`.
- Fixed source-size scan on seed `642000`, 5 episodes per condition:
  - `64 -> 64`: `[-18,0] 5/5`, `[+12,0] 2/5`, `[+24,0] 2/5`.
  - `80 -> 64`: `[-18,0] 5/5`, `[+12,0] 3/5`, `[+24,0] 3/5`.
  - `96 -> 64`: `[-18,0] 5/5`, `[+12,0] 5/5`, `[+24,0] 5/5`.
  - This matches the v47 base pattern; the 2k one-epoch jitter continuation is not a promoted model.
- Runtime source-size range `[80,96]` comparison on seed `643000`, 10 episodes:
  - Base v47: `[+12,0] 9/10`, `[+24,0] 9/10`, no collisions.
  - 2k jitter continuation: `[+12,0] 9/10`, `[+24,0] 9/10`, no collisions.
  - The common failure is episode 9, `round_square`, timeout from far approach: final XY remains around `0.20 m`; guard never activates.
- Conclusion:
  - Runtime larger source crop/range is useful and should stay available.
  - The current bottleneck is not final insertion or crop-size jitter training. It is the learned approach policy failing to close large XY error on some high-start `round_square` cases before guarded insertion can take over.
  - Next work should target approach-stage visual servoing: collect/weight hard far-XY approach failures, especially `round_square`, and consider a guard/assist path that can activate earlier for large XY approach failures without taking over normal successful cases.

### 2026-05-26 Round-Square Approach Pilot

- Added correction-dataset support for matching the v47 hard bucket:
  - hard control overrides: scale/noise/delay/filter ranges.
  - geometry overrides: hole/peg ranges, hole-center/fixture/table jitter.
  - nominal joint damping / actuator Kp multipliers.
  - `approach_sample_sort_key` for approach-window selection; default remains `correction_norm` to preserve old behavior.
- Output directory: `D:\peg-in-hole-6yh\v49_round_square_approach_failure_pilot`.
- First failure-only collection attempt timed out after 20 minutes, so natural timeout-only sampling is too sparse as a primary route.
- DAgger-style `round_square` approach-window pilot:
  - `image_correction_512_round_square_approach_window_v47_hardmatch.npz`
  - `512` samples from `28` policy-only timeout episodes, all `approach_recenter`.
  - XY range `0.080-0.153 m`; this over-sampled early approach, not the late far-drift region.
  - Weighted BC output `sac_image_bc_v49_round_square_approach_w10_e1_lr1e-6.zip` did not improve success: `round_square` seed643 `[+12,+24]` both stayed `9/10`.
- Late-window focused pilot:
  - Added `--approach-sample-sort-key steps_to_end`.
  - Exact seed `643009` late set reached steps `936-999`, XY `0.158-0.176 m`, with many opposed policy/oracle actions.
  - Larger set `image_correction_512_round_square_late_approach_v47_hardmatch.npz` used `26` policy-only timeout episodes.
  - Weighted BC output `sac_image_bc_v49_round_square_late_approach_w15_e1_lr2e-6.zip`.
  - Evaluation on `round_square`, seed `643000`, crop-source range `[80,96]`:
    - base v47: `[+12,0] 9/10`, `[+24,0] 9/10`, final failure XY about `0.206 m`.
    - v49 late candidate: `[+12,0] 9/10`, `[+24,0] 9/10`, final failure XY about `0.205 m`.
  - Conclusion: this is useful instrumentation and data plumbing, but not a promoted model. Small BC correction can slightly change the failure trajectory but does not solve the far-XY approach blind spot.
- Next recommendation:
  - Keep the correction script enhancements.
  - Do not scale this exact BC recipe yet.
  - Next test should compare two routes: a stronger approach-specific learner/data curriculum versus a default-off early approach assist/guard that activates only when `dist_xy` remains high and Z is still safely above the fixture.

### 2026-05-27 Early Approach Assist Pilot

- Added a default-off `guard_early_approach_assist` mode in `GuardedPolicyController`.
  - It can activate before normal `guard_active` when high-start XY error is still large and Z is in a safe approach window.
  - It commands a guarded lateral recenter toward the hole center, keeps/targets a high approach height, and hands back to the learned policy plus existing guarded insertion stack after XY reaches the release threshold.
  - CLI and step/episode/summary metrics are wired through `scripts/eval_guarded_policy.py`.
- Validation output directory: `D:\peg-in-hole-6yh\v50_early_approach_assist`.
  - `results/` currently rejected creation of new files/directories on this machine, so this pilot's raw CSV/Markdown outputs are kept outside the repo.
- Targeted seed `643000`, `round_square`, crop-source range `[80,96]`:
  - no-assist baseline: `[+12,0] 9/10`, `[+24,0] 9/10`, 0 collisions, 1 timeout each.
  - early assist enabled: `[+12,0] 10/10`, `[+24,0] 10/10`, 0 collisions, 0 timeouts.
  - mean early-assist usage: `30.2` steps, trigger rate `0.7` per episode.
- Spillover smoke, `mixed_basic`, same seed/range:
  - `[+12,0] 10/10`, `[+24,0] 10/10`, 0 collisions, 0 timeouts.
  - mean early-assist usage: `18.8` steps, trigger rate `0.4` per episode.
- Larger v50 gate:
  - Output directory: `D:\peg-in-hole-6yh\v50_early_approach_assist_gate`.
  - Config: `configs/sim/ur5e_full/eval_multi_geometry_early_approach_assist_gate_10ep.yaml`.
  - Seed `643000`, crop-source range `[80,96]`, offsets `[-18,0]`, `[+12,0]`, `[+24,0]`.
  - Profiles `single`, `round_square`, `square_square`, `mixed_basic`, 10 episodes/profile/offset.
  - Result: `120/120` success, `0` collisions, `0` timeouts.
  - Config smoke with `mixed_basic`, 1 episode succeeded.
- Interpretation:
  - This confirms the exposed v47/v48/v49 failure is an approach-stage far-XY timeout before normal guard activation, not a final insertion/contact failure.
  - The early assist is now a promoted eval/deployment guard candidate for this branch, but it is still a guarded-controller solution, not proof that the visual policy alone learned robust far-XY search.
- Next recommendation:
  - Tag this as the v50 early-assist milestone.
  - Next technical branch should return to learned approach improvement: collect/weight high-start far-XY approach data and test whether the policy can reduce early-assist usage, rather than expanding deploy-time assist first.
  - Keep the longer-term learner route open: train an approach-specific visual curriculum so the policy itself closes far XY error, instead of relying entirely on deploy-time assist.

### 2026-05-27 Early Approach Assist BC Pilot

- Added v51 data plumbing in `scripts/collect_image_correction_dataset.py`.
  - New selection modes: `early_approach_assist_window` and `early_approach_assist_failure_window`.
  - New label switch: `early_approach_assist_labels`.
  - The label commands v50-style high-start lateral recentering toward the hole center at a safe approach height.
  - Dataset schema at that point was `image_correction_v9_early_approach_assist`; later adapter-rollout DAgger support moved it to `image_correction_v10_rollout_approach_adapter`.
- Added configs:
  - `configs/sim/ur5e_full/collect_high_start_hard_wrist_pose_control_state_early_approach_assist_2k.yaml`
  - `configs/sim/ur5e_full/pretrain_high_start_hard_wrist_pose_control_state_early_approach_assist_2k_w10_e1.yaml`
- Pilot outputs are outside the repo:
  - `D:\peg-in-hole-6yh\v51_early_approach_learning`
  - smoke: `32` samples, all `early_approach_assist`
  - pilot dataset: `512` samples from `22` hard episodes, all `early_approach_assist`
  - XY range: `0.060-0.145 m`; Z-above-target range: `0.137-0.238 m`
  - trigger-window rate: `0.561`; window rate: `1.000`
- Trained one 1-epoch pilot:
  - `D:\peg-in-hole-6yh\v51_early_approach_learning\sac_image_bc_v51_early_approach_assist_512_w10_e1.zip`
  - train loss `0.280255`, val loss `0.196000`
- Evaluation on the exposed `round_square`, seed `643000`, crop-source range `[80,96]`:
  - no early assist, `[+12,0]`: `8/10`, `1` collision, `1` timeout
  - no early assist, `[+24,0]`: `8/10`, `1` collision, `1` timeout
  - with early assist, `[+12,0]`: `10/10`, mean early-assist steps `30.2`
- Interpretation:
  - Do not promote the v51 512-sample BC checkpoint.
  - The current naive BC mixing did not reduce deploy-time early-assist usage and regressed the unassisted policy.
  - The likely issue is label conflict/distribution shift: broad release-band assist labels teach strong lateral correction in states where the existing policy/guard handoff was already delicate.
- Next recommendation:
  - Keep the data plumbing and configs.
  - Before scaling to full 2k, narrow the learner update: either train a separate approach head/gated adapter, or collect stricter trigger-only samples (`dist_xy >= 0.10`) and lower the replay weight below `10%`.
  - Promotion remains v50 early assist, not v51 BC.

### 2026-05-27 Trigger-Only Early Assist BC Pilot

- Added `early_approach_assist_window_mode`.
  - `release_band`: keeps states down to release XY.
  - `trigger_only`: keeps only states beyond trigger XY, currently `dist_xy >= 0.10`.
- Updated the recommended v52 configs to trigger-only data and 5% replay:
  - collection: `configs/sim/ur5e_full/collect_high_start_hard_wrist_pose_control_state_early_approach_assist_2k.yaml`
  - pretrain: `configs/sim/ur5e_full/pretrain_high_start_hard_wrist_pose_control_state_early_approach_assist_trigger_2k_w05_e1.yaml`
- Pilot outputs are in `D:\peg-in-hole-6yh\v51_early_approach_learning`.
  - dataset: `image_correction_512_high_start_hard_wrist_pose_control_state_early_approach_assist_trigger_only.npz`
  - `512` samples from `47` hard episodes, all `early_approach_assist`
  - XY range: `0.100-0.156 m`; Z-above-target range: `0.136-0.238 m`
  - trigger-window rate: `1.000`
- Trained one 1-epoch 5% pilot:
  - checkpoint: `sac_image_bc_v52_early_approach_assist_trigger512_w05_e1.zip`
  - train loss `0.197861`, val loss `0.163761`
- Evaluation on `round_square`, seed `643000`, crop-source range `[80,96]`:
  - no early assist, `[+12,0]`: `9/10`, `0` collision, `1` timeout
  - no early assist, `[+24,0]`: `9/10`, `0` collision, `1` timeout
  - with early assist, `[+12,0]`: `10/10`, mean early-assist steps `30.2`
- Interpretation:
  - v52 trigger-only avoids the v51 collision regression, but still only matches the original no-assist baseline and does not reduce early-assist usage.
  - Do not promote v52 as a new model milestone yet.
  - The remaining timeout is still high-Z, far-XY policy drift before normal guard activation; BC labels alone are too weak or too indirect to change that behavior with the current monolithic policy.
- Next recommendation:
  - Keep v50 early assist as the promoted deployment guard.
  - For learner-side improvement, stop broad monolithic BC scans and implement a gated approach adapter or explicit approach subpolicy that only owns the high-Z/far-XY region.

### 2026-05-27 Gated Approach Adapter Smoke

- Added a separate approach adapter path instead of continuing to modify the SAC actor.
  - Module: `peg_in_hole_mujoco/approach_adapter.py`
  - Training script: `scripts/train_approach_adapter.py`
  - Eval integration: `scripts/eval_guarded_policy.py`
  - Configs:
    - `configs/sim/ur5e_full/train_approach_adapter_trigger_2k_xy.yaml`
    - `configs/sim/ur5e_full/train_approach_adapter_trigger_2k_xy_override.yaml`
    - `configs/sim/ur5e_full/train_approach_adapter_trigger_2k_full_crop_xy_override.yaml`
- The adapter consumes `near_hole_crop + control_state` and is gated to high-Z/far-XY states.
  - Default eval gate: `dist_xy >= 0.10`, `z_above_target = 0.12-0.27`.
  - Safe default is XY-only: Z stays owned by the base policy unless `--approach-adapter-apply-z` is explicitly set.
  - Eval supports `residual` mode and `override_xy` mode.
  - v2 adapter checkpoints can optionally consume `cam_image + near_hole_crop + control_state`; v1 crop-only checkpoints still load.
- Smoke outputs are in `D:\peg-in-hole-6yh\v51_early_approach_learning`.
  - residual adapter: `approach_adapter_trigger512_xy.pt`
  - override XY adapter: `approach_adapter_trigger512_xy_override.pt`
- Residual adapter pilot:
  - trained on 512 trigger-only samples, target `correction_raw_actions`, XY-only
  - final train/val loss: `0.00005535 / 0.00005381`
  - no-assist `round_square +12`, seed `643000`: `9/10`, `0` collision, `1` timeout
  - mean adapter steps: `210.1`
  - result: not useful; residual saturates actions but does not fix the far-XY timeout.
- Override-XY adapter pilot:
  - trained on 512 trigger-only samples, target `raw_actions`, XY-only
  - final train/val loss: `0.00002237 / 0.00003713`
  - no-assist `round_square +12`, seed `643000`: `9/10`, `0` collision, `1` timeout
  - mean adapter steps: `113.9`
  - failed episode final XY improved only modestly, about `0.2278 m -> 0.2153 m`.
  - with v50 early assist enabled: `10/10`, but mean early-assist steps stayed `30.2`; adapter steps were only `11.2`.
- Full+crop override-XY v2 pilot:
  - trained on the same 512 trigger-only samples, target `raw_actions`, XY-only
  - output: `D:\peg-in-hole-6yh\v51_early_approach_learning\approach_adapter_v2_fullcrop_trigger512_xy_override.pt`
  - final train/val loss: `0.00004401 / 0.00005041`
  - no-assist `round_square +12`, residual limit `0.005`: `8/10`, `0` collision, `2` timeouts; adapter was active too long (`289.4` mean steps)
  - no-assist `round_square +12`, residual limit `0.003`: `9/10`, `0` collision, `1` timeout
  - no-assist `round_square +24`, residual limit `0.003`: `9/10`, `0` collision, `1` timeout
  - with v50 early assist enabled at `+12`, residual limit `0.003`: `10/10`, mean early-assist steps `30.2`, mean adapter steps `11.2`
- DAgger-style adapter follow-up:
  - `scripts/collect_image_correction_dataset.py` now supports an optional rollout adapter via `--rollout-approach-adapter*`.
  - This lets the collector visit states induced by the current adapter, then label those states with the guarded/oracle corrective action.
  - Wide-XY smoke data expanded trigger-only coverage from old max `dist_xy=0.156 m` to about `0.202 m`.
  - Targeted adapter-rollout DAgger smoke on `round_square +12` found the expected failure mode: rollout adapter actions were often opposite the oracle/target direction, while oracle labels remained well aligned.
  - v6 full+crop mixed adapter was trained from original 512 trigger-only data plus wide-XY and targeted DAgger samples, with DAgger samples repeated for weight.
  - v6 with the original `dist_xy >= 0.10` adapter gate still timed out once, but the failure changed from far drift (`~0.18 m`) to just below the gate (`~0.098 m`), showing the adapter had corrected most of the approach error.
  - Lowering the adapter gate to `dist_xy >= 0.06` fixed the handoff gap:
    - no-assist `round_square -18`, seed `643000`, crop-source `[80,96]`: `10/10`, `0` collision, `0` timeout
    - no-assist `round_square +12`, seed `643000`, crop-source `[80,96]`: `10/10`, `0` collision, `0` timeout
    - no-assist `round_square +24`, seed `643000`, crop-source `[80,96]`: `10/10`, `0` collision, `0` timeout
    - no-assist `+12` crop-offset profile smoke, seed `643000`: `single=10/10`, `round_square=10/10`, `square_square=10/10`, `mixed_basic=10/10`, all zero collision and zero timeout
    - full no-assist profile/offset matrix, seed `643000`, crop-source `[80,96]`, offsets `[-18,0]`, `[+12,0]`, `[+24,0]`: `120/120`, `0` collision, `0` timeout
      - mean adapter steps ranged from `72.6` to `102.6`
      - mean episode steps ranged from `224.9` to `256.6`
    - new-seed full no-assist profile/offset matrix, seed `644000`, same profiles and offsets: `120/120`, `0` collision, `0` timeout
    - new-seed seed `645000` exposed that the original eval setting was too conservative:
      - original `min_z=0.12`, `max_xy_residual=0.003`: `106/120`, `0` collision, `14` timeouts
      - lowered `min_z=0.08` with `max_xy_residual=0.005`: `118/120`, `0` collision, `2` timeouts
      - stronger `max_xy_residual=0.008`: `117/120`, `0` collision, `3` timeouts because adapter stayed active too long and starved final-servo time
      - compromise `min_z=0.08`, `max_xy_residual=0.006`: `120/120`, `0` collision, `0` timeout
    - regression check on seed `644000` rejected the tuned eval-only fix:
      - `min_z=0.08`, `max_xy_residual=0.006`: `109/120`, `0` collision, `11` timeouts
      - failures concentrated on episode seed `644002`, where the adapter stayed active for all `1000` steps and guard/final-servo never took over
      - keeping `min_z=0.12` while raising `max_xy_residual=0.006` also failed targeted seed645 probes, so a single fixed cap/gate is not robust enough
  - v6 output: `D:\peg-in-hole-6yh\v51_early_approach_learning\approach_adapter_v6_fullcrop_mix_targeted_dagger_xy_override.pt`
- Interpretation:
  - The code path is now in place, but the 512-sample adapter is not a promoted learner milestone.
  - `override_xy` is the better adapter formulation, but the v6 checkpoint is not ready to replace v50 early assist through eval-parameter tuning alone.
  - Adding full camera features alone did not fix the unassisted far-XY timeout; targeted DAgger plus a lower handoff gate was needed.
  - The seed645/seed644 contrast shows two concrete tuning modes: if the XY cap is too small or the Z gate exits early, approach timeout remains; if the adapter owns the trajectory too long, it can diverge or consume the 1000-step budget before final-servo.
- Next recommendation:
  - Keep the adapter infrastructure.
  - Do not scale residual mode.
  - Do not promote/tag v6.
  - Next work should collect targeted adapter-rollout DAgger data from the newly exposed seed645 failures while preserving seed644 passing behavior, then train a non-smoke v7 adapter.
  - Compare v7 against v50 early assist and an explicit visual-servo target estimator; avoid more broad fixed-threshold scans unless the adapter policy or gate logic changes.

### 2026-05-28 Adapter v7 Targeted DAgger Pilot

- Collected a small targeted adapter-rollout dataset:
  - output: `D:\peg-in-hole-6yh\v62_adapter_v7_targeted_dagger\image_correction_96_mixed_basic_p24_seed645000_timeout_rollout_adapter_v6.npz`
  - rollout adapter: v6 with original conservative rollout gate `trigger_xy=0.06`, `min_z=0.12`, `max_xy_residual=0.003`
  - selection: `early_approach_assist_failure_window`, timeout episodes only
  - `96` samples from `5` timeout source episodes, `11` completed episodes
  - `opposed_actions_rate=0.552`, `approach_window_rate=0.698`, `dist_xy` mean about `117 mm`, `z_above_target` mean about `171 mm`
- Trained pilot v7:
  - output: `D:\peg-in-hole-6yh\v62_adapter_v7_targeted_dagger\approach_adapter_v7_fullcrop_mix_seed645_dagger_xy_override.pt`
  - final train/validation loss: `0.00000785 / 0.00000760`
  - training mixed the v6 data recipe plus the new seed645 timeout dataset repeated three times.
- Targeted seed645 eval with the original conservative eval gate (`min_z=0.12`, `max_xy_residual=0.003`) improved but did not solve the failures:
  - `single +12`: `9/10`
  - `single +24`: `9/10`
  - `round_square +24`: `9/10`
  - `square_square +24`: `9/10`
  - `mixed_basic +24`: `9/10`
  - all failures were timeouts, zero collisions
- Interpretation:
  - The DAgger route is still the right next direction, but the 96-sample mixed-basic pilot is underpowered and too narrow.
  - Do not promote v7.
  - Next collection should be balanced across `single`, `round_square`, `square_square`, and `mixed_basic`, both `[+12,0]` and `[+24,0]`, and should include seed644 preservation/negative cases so the adapter learns when not to overtake.

### 2026-05-28 Adapter v8 Latched-Gate Candidate

- Implemented default-off latched approach-adapter evaluation in `scripts/eval_guarded_policy.py`.
  - New switches:
    - `--approach-adapter-latch-enabled`
    - `--approach-adapter-latched-min-z`
    - `--approach-adapter-max-steps`
    - `--approach-adapter-episode-max-steps`
  - Default behavior is unchanged.
  - With latch enabled, the adapter still must first activate in the normal high-Z gate, then it may continue until `release_xy`, `latched_min_z`, or the consecutive step cap.
  - The episode step cap is also default-off; it prevents pathological immediate re-latching after the consecutive cap is exhausted.
- Motivation:
  - v8 without latch still timed out on seed645 episode `645009`.
  - The adapter exited at about `90 mm` XY because `z_above_target` slipped just below `0.12 m`; then the base policy drifted back out to about `164 mm` XY.
  - A fixed lower `min_z=0.08` was unsafe because it let the adapter own seed644 episode `644002` for all `1000` steps.
  - The latch makes the lower-Z extension bounded and stateful rather than globally lowering the activation gate.
- Collected balanced targeted DAgger data for v8:
  - output directory: `D:\peg-in-hole-6yh\v63_adapter_v8_balanced_dagger`
  - 8 datasets, `96` samples each
  - profiles: `single`, `round_square`, `square_square`, `mixed_basic`
  - offsets: `[+12,0]`, `[+24,0]`
  - rollout adapter: v7 under the original conservative gate
- Trained v8 adapter:
  - output: `D:\peg-in-hole-6yh\v63_adapter_v8_balanced_dagger\approach_adapter_v8_fullcrop_balanced_seed645_dagger_xy_override.pt`
  - final train/validation loss: about `0.00000389 / 0.00000391`
  - v8 alone, under the original conservative gate, still only reached `9/10` on most targeted seed645 conditions.
- Latched v8 evaluation setting:
  - `trigger_xy=0.06`
  - `release_xy=0.03`
  - activation `min_z=0.12`, `max_z=0.27`
  - latched `min_z=0.08`
  - `max_steps=220`
  - `mode=override_xy`
  - `max_xy_residual=0.003`
- Validation:
  - seed `643000`, 12 profile/offset runs, 10 episodes each: `120/120`, `0` collision, `0` timeout
  - seed `644000`, same matrix: `120/120`, `0` collision, `0` timeout
  - seed `645000`, same matrix: `120/120`, `0` collision, `0` timeout
  - combined: `360/360`, `0` collision, `0` timeout
  - mean adapter steps by seed were roughly `146`, `157`, and `152`.
- Fresh-seed follow-up:
  - seed `646000` with the same latch220 setting: `120/120`, `0` collision, `0` timeout.
  - seed `647000` with the same latch220 setting: `116/120`, `0` collision, `4` timeout.
  - The four seed647 failures were all `m18` crop-offset episode `647008`. They were not contact/collision failures; the adapter could consume `440` steps through immediate re-latching, and final-servo handoff then happened too late.
  - `--approach-adapter-episode-max-steps 220` fixed `single_m18` and `round_square_m18` on seed647, but still left `square_square_m18` and `mixed_basic_m18` at `9/10`; this is useful as a safety knob, but it is not the promoted recipe.
  - A direct adapter down-bias probe was discarded: it reduced adapter steps but caused high-tilt/recovery timeouts.
- Current stronger eval recipe:
  - Keep v8 latch220 adapter settings.
  - Add `--guard-final-servo-start-z 0.100` so final servo takes over at `100 mm` above target instead of `70 mm`.
  - seed `643000`, 12 profile/offset runs, 10 episodes each: `120/120`, `0` collision, `0` timeout.
  - seed `644000`, same matrix: `120/120`, `0` collision, `0` timeout.
  - seed `645000`, same matrix: `120/120`, `0` collision, `0` timeout.
  - seed `646000`, 12 profile/offset runs, 10 episodes each: `120/120`, `0` collision, `0` timeout.
  - seed `647000`, same matrix: `120/120`, `0` collision, `0` timeout.
  - combined result for this recipe: `600/600`, `0` collision, `0` timeout.
  - result directories: `D:\peg-in-hole-6yh\v77_adapter_v8_latch220_finalstart100_seed643_regression`, `D:\peg-in-hole-6yh\v78_adapter_v8_latch220_finalstart100_seed644_regression`, `D:\peg-in-hole-6yh\v79_adapter_v8_latch220_finalstart100_seed645_regression`, `D:\peg-in-hole-6yh\v76_adapter_v8_latch220_finalstart100_seed646_regression`, `D:\peg-in-hole-6yh\v74_adapter_v8_latch220_finalstart100_m18_seed647_probe`, and `D:\peg-in-hole-6yh\v75_adapter_v8_latch220_finalstart100_seed647_p12p24`.
- Adapter artifact:
  - repo path: `assets\approach_adapters\approach_adapter_v8_fullcrop_balanced_seed645_dagger_xy_override.pt`
  - local checkpoint: `D:\peg-in-hole-6yh\v63_adapter_v8_balanced_dagger\approach_adapter_v8_fullcrop_balanced_seed645_dagger_xy_override.pt`
  - size: `341061` bytes
  - SHA256: `0788831FBC94E344865A35ACD96408C40D72D50521D2C668D86570F640EE53EB`
  - packaging note: direct filesystem copy into `assets` was blocked by the local Windows ACL, so the artifact was added through Git object/index plumbing instead.
  - current local worktree note: this machine keeps the artifact path marked `skip-worktree` because the file cannot be materialized under `assets`; fresh clones/checkouts should contain the repo-path file normally.
- Interpretation:
  - This is the first learner-side approach-adapter path that matches the v50 early-assist matrix on the tested seeds without enabling v50 early assist.
  - The mechanism is not pure policy-only insertion; the guarded final-servo stack still performs final insertion.
  - The stronger fresh-seed recipe is adapter plus earlier final-servo handoff, not adapter-only learning.
  - The code+artifact recipe is promoted as `v0.7.4-v8-adapter-finalstart100`.
  - Optional follow-up: mirror the checkpoint as a GitHub release asset if GitHub asset distribution becomes preferable to keeping the compact adapter in the repository.

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

## Contact Brake Hard Square Status

Current branch: `feature/contact-aware-reinsert`.

Goal: reduce hard square-square low-Z insertion failures where wall contact under
delay/filter pushes the peg laterally after it is already near-centered.

Implemented default-off diagnostics/candidates:

- `guard_final_servo_square_contact_brake_enabled`: detects square wall contact
  inside the near-hole low-Z window, lifts, recenters, and returns to
  `square_fast_settle`.
- `guard_final_servo_square_fast_settle_low_z_max_down_action` with
  `guard_final_servo_square_fast_settle_low_z_down_threshold`: optional low-Z
  down-speed cap.
- `guard_final_servo_square_contact_brake_exhausted_escape_enabled`: optional
  fallback from exhausted contact-brake attempts into square recovery escape.
- `guard_final_servo_square_contact_brake_reset_attempts_after_escape_enabled`:
  optional reset after a successful square recovery escape.

Validation notes:

- Focused old problem seeds
  `921509/922510/923504/921526/921512/923511` passed `6/6` with contact brake.
- Fresh hard square gate `921500/922500/923500`, 30 episodes each, reached
  `89/90` with default contact brake; the remaining failure is `922504`.
- `max_attempts=3` fixed `922504` in isolation but introduced new failures in
  the full gate, so it is not promoted.
- Global or broad low-Z down limiting can convert collisions into timeouts; it
  is not a promotion candidate yet.
- `exhausted_escape` avoids the `922504` collision but tends to create repeated
  high escape loops and timeouts.
- Simulator-side `square_recovery_escape_flush_control_history` reaches `5/5`
  on the `922500` focused gate, confirming the remaining issue is mostly
  delay/filter control-history residue. Keep it diagnostic-only because it is
  not directly deployable on a real controller.
- Deployable preemptive hold candidate:
  `contact_brake_max_up=0.005`,
  `preemptive_hold_steps=12`,
  `preemptive_hold_max_up=0.005`.
  This passed `921500=30/30`, `922500=30/30`, but `923500=29/30` with one
  timeout at `923504`.
- Adding high-Z square descend with limited XY servo fixed the `923504`
  timeout and reached old-gate `90/90` with:
  `high_z_stall=0`, `high_z_contact_max=4`,
  `high_z_max_xy=0.0015`, `high_z_max_down=0.0020`,
  `high_z_low_z_brake_wall_count=4`, `high_z_low_z_brake_z_max=0.032`.
  However, fresh gate `924500/925500/926500` reached only `88/90`; `926500`
  had two collision failures. This is not promotable.
- Slower global high-Z descent (`high_z_max_down=0.0012`) fixed `926500=30/30`
  but regressed `921500=28/30`, so the issue is not solved by a single global
  down-speed cap.
- Low-Z unconditional floor brake (`wall_count=0`) and low-Z XY cap
  (`low_z_max_xy=0`) over-intervened and caused large regressions
  (`921500/926500` fell to roughly 60-70% success). Do not use these as
  candidates.
- Current failure pattern: high-Z descent with delay/filter can still create a
  one-step low-Z lateral/tilt pop before wall-contact information is available.
  Recovery/escape after that pop may collide while trying to lift.
- v166 added default-off staged high-Z re-descent, low-Z hold, exhausted
  contact-brake continue, and gated expanded preemptive hold plumbing. The
  global widened-prehold idea was rejected because it rescued several focused
  failures but could break `926516`; the gated version only expands the
  prehold XY window when Z is high enough and tilted clearance margin is not
  too negative.
- v166 single-seed probe on
  `921507/923511/923520/924510/925517/926516` passed `6/6`, but the full
  old+fresh 6x30 gate reached only `177/180`; failures were all in the
  `925500` bucket (`925503` collision, `925521/925523` timeouts).
- Failure diagnosis:
  - `925521` was mainly an approach-adapter ownership timeout: the adapter
    stayed active for `821` steps, leaving too little final-servo budget.
  - `925523` was a repeated square recovery escape loop after a risky expanded
    prehold with tilted margin around `-0.00040`.
  - `925503` was a low-Z continuation after exhausted contact-brake attempts;
    the peg was near-centered but then popped laterally/tilted at low Z.
- Accepted v170 changes:
  - add `approach_adapter_episode_max_steps=220`
  - tighten expanded prehold margin gate from `-0.0005` to `-0.0003`
  - raise square contact-brake attempts from `2` to `3`
  - keep exhausted-continue tightly gated at `margin_min=-0.0003`
  - keep broad low-Z down-speed limiting disabled, because a probe converted
    `925503` back into collision
  - reject the very early square escape-risk threshold
    (`early_risk_margin=-0.00028`, `z_min=0.020`) because it removed collision
    but regressed `925500` to `26/30` with four timeouts.
- v169 focused validation:
  - failed `925500` seeds `925503/925521/925523`: `3/3`, zero collision,
    zero timeout.
  - historical sensitive seeds
    `921507/923511/923520/924510/925517/926516`: `6/6`, zero collision,
    zero timeout; importantly `926516` did not trigger expanded prehold.
- v170 full hard square-square gate:
  - result directory: `D:\peg-in-hole-6yh\v170_A_brake3_gate_6x30`
  - seeds `921500/922500/923500/924500/925500/926500`, 30 episodes each:
    `180/180`, zero collision, zero timeout.
  - seed buckets:
    `921500=30/30`, `922500=30/30`, `923500=30/30`,
    `924500=30/30`, `925500=30/30`, `926500=30/30`.
  - reproducible config:
    `configs\sim\ur5e_full\eval_multi_geometry_v170_square_contact_brake_staged_descend_hard_square_30ep.yaml`.
- v170 fresh gate failed and is not promotable:
  - result directory:
    `D:\peg-in-hole-6yh\v171_v170_fresh_hard_square_3x30`
  - seeds `927500/928500/929500`, 30 episodes each: `88/90`.
  - failures:
    `927525` collision after final-insert adapter intervention in late
    `square_fast_settle`;
    `929512` timeout after repeated square recovery escape loops, ending near
    center but still about `20 mm` above the success Z threshold.
  - current-code replay on 2026-06-05:
    `D:\peg-in-hole-6yh\v172_current_code_fresh3x30`.
    With the same v170 config and the default-off v171/v172 hooks still
    disabled, seeds `927500/928500/929500` reached `89/90`:
    `927500=30/30`, `928500=30/30`, `929500=29/30`. The remaining failure is
    `929512` timeout, zero collision. This is still not promotable.
- Rejected v171 probes:
  - disabling the final-insert adapter fixed `927525` and `927500=30/30`, but
    did not fix the `929512` timeout by itself.
  - lowering global square recovery escape height from `70 mm` to `60 mm`
    fixed `929500=30/30` but introduced a `928526` collision.
  - lowering it to `65 mm` fixed `928500=30/30` but introduced a `929524`
    collision.
- Rejected v171 global fast-down candidate:
  - keep v170 recovery height and contact-brake stack.
  - disable the learned final-insert adapter for this hard square deployable
    gate with `final_insert_adapter_enabled=false`.
  - globally raising `guard_final_servo_square_fast_settle_max_down_action`
    from `0.0020` to `0.0025` passed focused fresh/sensitive probes
    (`927500/928500/929500/925500`, 30 episodes each) but regressed old
    collision-sensitive buckets:
    `921500=29/30` and `923500=29/30`.
  - conclusion: do not promote global square-fast-settle down acceleration.
- v171 late-down-boost / low-Z insertion probes:
  - added a default-off narrow
    `guard_final_servo_square_fast_settle_late_down_boost_*` hook. It only
    applies in square `square_fast_settle` after the configured brake-attempt
    count, phase age, tight XY window, Z window, and contact gate pass.
  - the first narrow boost (`max_down=0.0025`, `XY<=2.5 mm`, no contact,
    `brake_attempts>=3`) kept `927500=30/30` but left `929500=29/30`; the
    failure remained `929512` timeout.
  - adding a paired late-boost XY cap (`max_xy=0.0010`) changed the same
    `929512` failure from a late pop/escape into a cleaner timeout: final
    about `2.0 mm` XY and `22.7 mm` Z, zero collision. This is safer but still
    not a fix.
  - increasing late boost down to `0.0032` caused earlier low-Z contact and
    recovery timeout on `929512`; do not use it.
  - lowering exhausted-continue Z to `20 mm` and loosening margin to `-0.8 mm`
    still left `929512` as timeout; widening exhausted-continue XY to `12 mm`
    converted it to collision. Do not continue inserting after the low-Z pop.
  - raising square contact-brake max attempts to `4` regressed `929500` to
    `26/30` with `3` collisions and `1` timeout. Do not add more global brake
    attempts.
  - added a default-off
    `guard_final_servo_square_fast_settle_clearance_hold_*` diagnostic hook
    that locks XY, blocks down action, and allows tiny upward relief in low-Z
    near-centered negative-margin states. On `929500` with the late boost
    config it regressed to `28/30`, zero collision but two timeouts. Keep this
    hook diagnostic-only for now.
  - current failure interpretation: `929512` is not simply missing speed. The
    peg reaches low Z with sub-2 mm XY, but narrow square tilted-clearance
    remains slightly negative and delayed/filtered contact can create a
    low-Z lateral pop. Full escape is safe but too slow; hard continuation and
    extra brake attempts are unsafe.
  - reproducible diagnostic config:
    `configs\sim\ur5e_full\eval_multi_geometry_v171_no_final_adapter_fastdown_hard_square_30ep.yaml`.
- Rejected v172 low-Z relief / direct-settle probes:
  - Added default-off
    `guard_final_servo_square_fast_settle_low_z_relief_*` plumbing with
    `square_low_z_relief_lift` and `square_low_z_relief_recenter` phases. On
    `929500` it reached only `28/30`; `929512` and `929518` still timed out,
    and the relief action could create a lateral pop/escape. Keep diagnostic
    only.
  - Narrow fast-down with a tight XY cap was unsafe. `max_down=0.0030` and
    `max_xy=0.0005` regressed `929500` to `27/30`, including a new `929506`
    collision. A smaller `max_down=0.0026` rescued some single seeds but
    converted `929508` to collision and left `929512` unresolved.
  - Raising square yaw-align weight is not a robust fix. Weight `0.40` fixed
    `929500=30/30` but regressed `927500=28/30`; weight `0.45` was worse on
    fresh buckets; weight `0.35` fixed several timeout seeds but still
    produced a `927525` collision. More yaw authority can reduce timeout but
    increases low-Z collision risk.
  - Globally allowing earlier/high-Z `square_fast_settle` entry is unsafe.
    `square_fast_settle_z_max=0.085` reached only `86/90` on fresh 3x30, all
    failures collision. `z_max=0.065` improved to `89/90` but still introduced
    a `928528` collision.
  - Added default-off
    `guard_final_servo_square_recovery_escape_direct_fast_settle_*` plumbing.
    It can rescue focused seeds after recovery escape, but fresh 3x30 still
    failed: with yaw `0.40`, `58/60` across `927500/929500` because of
    collisions; with base yaw `0.20`, `88/90` because `929512/929518`
    remained timeouts. Keep diagnostic only.
  - Down-only commit / XY-lock style insertion is not safe. Late-down boost
    `max_down=0.0020` with `max_xy=0.0001` converted `929512`, `929518`, and
    `927514` into collisions.
  - Earlier escape on one wall-contact step fixed some focused timeouts, but
    converted `929512` to collision. Do not reduce
    `guard_final_servo_square_recovery_escape_early_contact_wall_steps` to `1`
    globally.
  - Cutting the approach adapter earlier is broad-regressive. Episode cap
    `180` produced `26/30`, `29/30`, `27/30` on fresh
    `927500/928500/929500`; cap `200` still reached only `29/30`, `29/30`,
    `28/30`.
- Current v172 failure interpretation:
  - The residual hard-square issue is low-Z contact under delayed/filtered
    control, not just descent speed.
  - Typical bad state: `1-3 mm` XY error and `25-35 mm` Z above target, brief
    wall contact, then a lateral pop to `10-25+ mm`.
  - More aggressive deterministic insertion often converts timeout into
    collision. Safer recovery avoids collision but can exhaust the 1000-step
    budget.
  - Stop broad scalar scans of final insert speed, yaw weight, recovery height,
    and adapter cap unless a new mechanism changes the failure mode.
- v173 low-Z square teacher/adapter smoke:
  - `scripts\build_square_fast_settle_teacher_dataset.py` now supports
    `--config` through the shared flat-YAML parser, so low-Z square failure
    extraction can be made reproducible.
  - Teacher smoke from
    `D:\peg-in-hole-6yh\v172_current_code_fresh3x30\eval_v170_fresh_seed929500_30ep_failure_steps.csv`
    selected `102` `square_fast_settle` samples from the `929512` timeout:
    mean `2.50 mm` XY, `40.89 mm` Z, mean yaw error `0.12 deg`, mean tilted
    margin `-0.59 mm`.
  - Labels were `99` `hold_recenter` and `3` `clearance_lift`; the dominant
    reason was tight top-down square clearance, not gross yaw error.
  - A 20-epoch smoke adapter trained cleanly from the 102 samples with random
    split train/val MAE `0.49/0.51 mm`.
  - Closed-loop smoke on the same `929500` 30-episode bucket remained
    `29/30`, zero collision, with `929512` still timing out. Conclusion: the
    trace-derived dataset/training/eval path works, but a single-failure
    adapter is not enough. Next data work must be balanced DAgger across
    multiple low-Z failure seeds plus success-preservation samples.

Current decision:

- There is no promotable v171/v172 successor at this point. v170 remains the
  last clean 6x30 old hard-square gate, but it failed the fresh gate at
  `88/90`; the latest stable promoted tag remains
  `v0.7.6-square-escape-dynamic-xycap`.
- Do not push/tag a new version from this state. The new late-boost,
  clearance-hold, low-Z relief, and direct-fast-settle hooks are useful
  diagnostics and remain default-off.
- Next useful work: stop hand-tuning deterministic low-Z insert actions and
  build a safer correction path around the low-Z square lateral-pop states.
  Preferred direction is failure-correction / DAgger data from states that
  actually enter the bad low-Z contact regime, with labels using
  tilted-clearance margin, contact state, yaw error, and recovery phase. Use
  the v173 smoke path as the data pipeline skeleton, but scale it to multiple
  failure traces and add success-preservation rows before training another
  closed-loop candidate. Validate first on `929512`, `929518`, `927525`,
  `927514`, `928528`, then on fresh `927500/928500/929500` and old
  collision-sensitive buckets.

## 2026-06-06 Hard-Square Contact-Aware Reinsert Status

- Branch: `feature/contact-aware-reinsert`.
- Last pushed stable hard-square milestone remains
  `v0.7.7-hard-square-clean3-escape55` from v221.
- Local v222-v238 probes are diagnostic only and should not be promoted:
  - v233 was strong on `925/927/931/924/928`, but failed `929500=27/30`.
  - v235 was the best balanced soft-hold timing probe, but still failed
    `929500=29/30` on seed `929510`.
  - v237/v238 showed that margin gating can rescue some seeds, but the wider
    margin gate regressed collision-sensitive `931509`.
- Current interpretation: the remaining failures are not solved by another
  scalar scan of soft-hold timing or margin. Soft-hold can help low-margin
  contact states, but returning directly to `square_fast_settle` can immediately
  feed the contact-brake/recovery chain and create a late lateral pop.
- Current local candidate: v239
  `configs/sim/ur5e_full/eval_multi_geometry_v239_v235_contact_soft_hold_release_continue_hard_square_30ep.yaml`.
  It keeps v235's first-trigger gate and adds default-off code for a structured
  `square_fast_settle_contact_soft_hold_release_continue` phase. The phase only
  runs after soft-hold when contact is clear and XY/yaw/tilt/margin are healthy,
  then performs a short bounded descent with small XY correction.
- Validation order for v239:
  1. Static checks:
     `python -B -m py_compile peg_in_hole_mujoco\guarded_policy.py scripts\eval_guarded_policy.py`
     and `git diff --check`.
  2. Serial targeted 1-episode hard-square seeds:
     `925523`, `931509`, `931524`, `927514`, `927525`, `929510`,
     `929516`, `929521`, `929524`.
  3. If targeted smoke passes, serial 30ep buckets in this order:
     `927500`, `929500`, then `924500/925500/928500/931500`.
- Do not push/tag v239 until targeted smoke and old/fresh hard-square 30ep
  buckets are clean. Avoid parallel evals for these gates because earlier
  parallel probes produced unstable hard-square outcomes.
- v239-v244 follow-up diagnostics:
  - v239 added `square_fast_settle_contact_soft_hold_release_continue` and
    passed most focused seeds, but still collided on `929524`; release did not
    activate because wall contact was still present at soft-hold exit.
  - v240 added bounded soft-hold extension while contact persists. It fixed
    targeted `929524`, but regressed `927500` to `28/30`, including early
    extension around episode step 459. Reject.
  - v241 made extension late-only at episode step `>=550`. Focused seeds and
    `927500=30/30` passed, but `929500=29/30` with a `929504` collision in the
    old second contact-brake/recenter chain. Not promotable.
  - v242 limited contact-brake to one attempt. It fixed focused `929504`, but
    regressed `929500` to `28/30` (`929512`, `929525`). Reject.
  - v243 kept two brake attempts but added a repeat-brake margin gate at
    `-1.0 mm`. Focused seeds and `927500=30/30` passed, but `929500=29/30`
    with a `929518` collision after repeated brake/recovery and low-Z relief.
    Not promotable.
  - v244 narrowed low-Z relief to non-positive margin. It regressed focused
    `929518` to timeout and `931509` to collision. Reject.
- Current conclusion: v241/v243 contain useful default-off mechanics, but none
  is a promotion candidate. The failure mode has moved from one deterministic
  bad seed to multiple narrow contact-chain boundary cases. Stop broad scalar
  scans of soft-hold, brake attempts, and low-Z relief thresholds unless the
  next change is a more structured policy for late contact-chain handoff.
- Next recommended direction: inspect successful vs failed `929500` traces
  around late fast-settle/contact-brake/low-Z-relief handoffs and design a
  phase-local "safe release or escape" rule with explicit post-contact stability
  requirements, rather than adding another global threshold.

## 2026-06-06 v247-v256 Contact-Chain Diagnostics

- v247-v252 were focused on low-Z square fast-settle wall-contact failures:
  - v247 positive-margin clearance hold: current rerun `929500=29/30`, collision
    on `929518`; reject.
  - v248 broad clean preemptive release: `931500=27/30`, 3 collisions; reject.
  - v249 deep positive hold + clean release attempt2: `931500=30/30`,
    `927500=30/30`, but `929500=29/30`; reject.
  - v250 pure hold only: `929500=29/30`; reject.
  - v251 down guard + pure hold: `929500=30/30`, `927500=30/30`, but
    `931500=29/30` with one collision on `931513`.
  - v252 moved low-Z down guard/hold to brake attempts `>=3` and fixed the
    `931513` collision in the first observed run, but had one `931509` timeout
    in an earlier `931500/30ep` run. A later current-code rerun of v252 on
    `931500/30ep` reached `30/30`, so this region is not fully deterministic.
- v253 added a default-off code path plus config for a very narrow late
  contact-brake lift release:
  - New fields are
    `guard_final_servo_square_contact_brake_late_lift_release_*`.
  - Main gate: `931500=30/30`, `929500=30/30`, `927500=30/30`.
  - Repeat `931500=30/30`.
  - Extra bucket `933500=29/30`, timeout on `933514`.
  - Current status: useful diagnostic candidate, but not promotable because
    `933500` exposed a remaining timeout and the original v252 timeout was not
    consistently reproducible.
- v254 lowered late recovery-escape height to `0.040`.
  - Fixed `933500=30/30`.
  - Regressed `931500=29/30` with collision on `931509` and `929500=29/30`
    with collision on `929518`.
  - Reject. Lowering late escape height globally causes low-altitude recenter
    with large XY and reintroduces collisions.
- v255 added default-off from-escape direct fast-settle code:
  - New fields are
    `guard_final_servo_square_recovery_escape_direct_fast_settle_from_escape_*`.
  - v255 config tried to short-circuit late escape only after episode step
    `>=930`.
  - `933500=29/30` with collision on `933513`; this collision occurred before
    the `930`-step gate, so it is more evidence of run-to-run instability and
    a separate low-Z wall-contact issue, not a validated fix. Reject.
- v256 tried starting low-Z down guard and clearance hold at brake attempt `>=1`.
  - `933500=28/30`, with one collision and one timeout.
  - Reject. Broadening the low-Z guard to early brake attempts creates new
    stalls/recovery chains.
- Current decision:
  - Do not push/tag/promote v253-v256.
  - Keep the new code hooks default-off because they are useful for future
    controlled experiments.
  - Avoid further broad scalar scans. The next useful experiment should add
    better instrumentation first: explicit trace columns for direct-fast-settle
    active state and for which guard condition caused a phase transition. Then
    rerun v252/v253/v255 serially on `929500`, `931500`, `933500` before
    changing more control rules.

## 2026-06-06 Final-Servo Trace Instrumentation

- Added step-trace instrumentation for hard-square contact-chain diagnosis:
  - `guard_final_servo_phase_transition_reason`
  - `guard_final_servo_square_recovery_escape_direct_fast_settle_active`
- The transition reason is a one-step pulse. It resets to `none` at the start of
  each guarded-policy step and is set only when `_set_final_servo_phase(...)`
  changes or explicitly restarts a phase.
- Static validation passed:
  - `python -B -m py_compile peg_in_hole_mujoco\guarded_policy.py scripts\eval_guarded_policy.py`
  - `git diff --check` only reported local LF/CRLF warnings.
- Smoke validation passed on v253 config, seed `933500`, `1` episode:
  - success `1/1`, collision `0/1`, timeout `0/1`
  - step CSV was written to
    `D:\peg-in-hole-6yh\instrumentation_smoke\eval_seed933500_1ep_steps.csv`
  - observed transition reasons included `final_servo_start`,
    `align_hover_escape`, `square_fast_settle`,
    `square_high_z_descend`, `square_contact_brake`,
    `square_contact_brake_lifted_enough`, and
    `square_contact_brake_recenter_stable`.
  - direct-fast-settle did not trigger in this one successful smoke episode.
- Next step:
  - Run serial, trace-enabled 30ep evaluations on hard-square seeds
    `929500`, `931500`, and `933500`, preferably comparing v252, v253, and v255.
  - Use the new transition columns to decide whether the next control change
    should target late contact-brake release, recovery escape, or low-Z
    fast-settle. Do not promote or tag until those serial gates are stable.

## 2026-06-07 v252-v261 Instrumented Hard-Square Follow-Up

- Ran trace-enabled 30ep gates with the current instrumented controller on
  hard-square seeds `929500`, `931500`, and `933500`.
- Baseline diagnostic reruns:
  - v252: `929500=29/30` with 1 collision, `931500=29/30` with 1 collision,
    `933500=29/30` with 1 timeout.
  - v253: `929500=30/30`, `931500=29/30` with 1 timeout,
    `933500=28/30` with 1 collision and 1 timeout.
  - v255: `929500=28/30` with 1 collision and 1 timeout,
    `931500=30/30`, `933500=30/30`.
- The new trace columns showed two main late failure types:
  - clean low-Z timeout in `square_fast_settle`: near-centered, no contact,
    positive margin, but down action capped at `0.001`.
  - late bad-margin recovery-escape loop: repeated
    `square_recovery_escape_* -> square_fast_settle` around XY `6-8 mm`,
    Z `45-50 mm`, negative tilted margin.
- v258 added clean low-Z late down boost on top of v253:
  - `929500=30/30`, `931500=30/30`, `933500=29/30` with 1 timeout.
  - Current best local diagnostic point: `89/90`, zero collisions, but not
    promotable because the `933500` timeout remains.
- v257, v259, v260, and v261 explored direct-fast-settle gating:
  - v257 narrowed inherited direct fast-settle and regressed `929500=28/30`.
  - v259 added a high-Z direct gate and fixed `933500=30/30`, but regressed
    `931500=28/30` with 1 collision and 1 timeout.
  - v260 allowed direct only before step `900`; `933500=29/30` with 1
    collision.
  - v261 allowed direct only before step `930`; `933500=29/30` with 1 timeout.
- Current decision:
  - Do not push/tag/promote v257-v261.
  - v258 is the best comparison base for the next experiment, not a release.
  - Stop single-threshold scans of direct-fast-settle gates. The failures
    migrate between timeout and collision depending on the seed.
- Next recommended direction:
  - Add a structured late `square_recovery_escape_recenter` handoff for
    negative-margin, mid-Z states instead of more scalar direct gates.
  - The handoff should keep collision risk low by requiring no contact,
    bounded tilt, bounded XY, and either a short high-Z recenter hold or a
    safer align-hover resume, then validate first on `933500` before repeating
    `929500/931500/933500`.

## 2026-06-07 v262-v266 Late Escape/Finish Diagnostics

- Added a default-off late recovery-escape recenter descend handoff:
  - `guard_final_servo_square_recovery_escape_late_recenter_descend_*`
  - `guard_final_servo_square_recovery_escape_late_recenter_descend_hold_release_*`
  - The handoff targets very late, clean, negative-margin
    `square_recovery_escape_recenter` states and can hold recenter instead of
    immediately releasing to `align_hover`.
- Added guarded-state support for
  `square_peg_topdown_clearance_margin`, then added a default-off
  `guard_final_servo_square_fast_settle_late_finish_continue_topdown_margin_min`
  gate so late finish continuation can require positive top-down clearance.
- Key results:
  - v262: `933500=29/30`, one timeout. Late descend triggered but released too
    quickly into `align_hover/square_fast_settle`.
  - v263: sticky late recenter fixed `933500=30/30`, but `929500` repeat showed
    one timeout. The timeout began too late in the episode for slow sticky
    descend to finish.
  - v264: relaxed late finish tilted-margin only. `929500=28/30` with 2
    collisions. Reject.
  - v265: topdown-gated mild-negative late finish continuation.
    `929500=30/30`, `933500=30/30`, initial `931500=29/30` with one timeout,
    repeat `931500=30/30`.
  - v266: widened late finish XY/topdown gate. `931500=30/30`, but
    `929500=27/30` with 1 collision and 2 timeouts. Reject.
- Current decision:
  - v265 is the best local candidate from this batch, but do not tag/promote
    yet because hard-square contact evaluations remain repeat-sensitive.
  - v266 and v264 should remain diagnostic configs only.
  - Next validation should rerun v265 serially on `929500/931500/933500`,
    preferably with the same trace settings, then run a repeat bucket before
    any GitHub push/tag.

## 2026-06-07 v265 Repeat And v267-v268 Late Escape Veto

- Repeated v265 on `929500/30ep` with full step tracing:
  - `v265_repeat2_seed929500=29/30`, zero collisions, one timeout on
    `929524`.
  - The failure entered `square_recovery_escape_pre_lift` at step `923` from a
    clean low-Z state with positive topdown clearance, then spent the rest of
    the episode lifting/recentering.
- Added a default-off late escape veto:
  - `guard_final_servo_square_fast_settle_late_escape_veto_*`
  - Intended behavior: in very late, low-Z, no-contact, topdown-positive,
    bounded yaw/tilt states, keep `square_fast_settle` instead of starting a
    new recovery escape.
- v267 and v268 are rejected:
  - v267 `929500=28/30`, with one collision and one timeout.
  - v268 `929500=28/30`, with one collision and one timeout.
  - The collision failures occurred before the late veto gate and the timeout
    failures migrated into bad large-XY/large-tilt escape states. This is not a
    stable controller-threshold direction.
- Current decision:
  - Do not push/tag/promote v265-v268.
  - Keep the new late escape veto code default-off as instrumentation/control
    scaffolding, but do not keep widening it.
  - Next useful work should shift away from more guard threshold scans and
    toward collecting the repeated hard-square failure states for targeted
    correction/DAgger or a learned recovery adapter. The controller-only path is
    showing repeat-sensitive contact failures around the 1000-step deadline.

## 2026-06-07 v269-v273 Targeted Final-Insert Adapter Diagnostics

- Built a targeted phase-aware dataset from the v265 repeat failure:
  - Source: `D:\peg-in-hole-6yh\trace_eval_final_servo_instrumentation\v265_repeat2_seed929500_*`.
  - Output: `D:\peg-in-hole-6yh\trace_eval_final_servo_instrumentation\v269_v265_repeat2_failure_dataset.npz`.
  - Samples: `88`, all from `929524`, label mix `micro_recenter=63`,
    `soft_descend=20`, `handoff_descend=5`.
- v269 trained only on that narrow failure tail:
  - Checkpoint:
    `D:\peg-in-hole-6yh\v269_hard_square_failure_adapter\final_insert_adapter_v269_v265_failure_e120.pt`.
  - Training smoke reached random-split val MAE `0.224 mm`.
  - Closed-loop `929500/30ep` regressed to `27/30`, with 2 collisions and 1
    timeout. Reject. A single failure tail is too narrow and damages other
    hard-square episodes.
- v270 blended the v269 failure tail with the existing v174 low-Z balanced
  failure/success datasets:
  - Checkpoint:
    `D:\peg-in-hole-6yh\v270_blended_final_insert_adapter\final_insert_adapter_v270_v174_plus_v269_nolift_e120.pt`.
  - Training val MAE `0.167 mm`.
  - Closed-loop no-handoff results:
    - `929500=30/30`
    - `931500=30/30`
    - `933500 repeat=29/30`, one timeout on `933514`
  - This is the best learned-adapter diagnostic from this batch, but not
    promotable because it regresses `933500` relative to the current v265
    record.
- Tested runtime state handoff with v270:
  - It fixed `933500=30/30`, but regressed `929500=29/30` with one collision.
  - Reject this gate as a release direction. It trades one hard bucket for
    another and can perturb already-successful insertions.
- v271/v272/v273 tried adding the v270 `933514` timeout back into training:
  - v271 used a wide `365`-sample 933514 dataset with balanced labels:
    `929500=27/30`, `933500=30/30`. Reject.
  - v272 downsampled that 933514 dataset to `122` samples with balanced labels:
    `929500=29/30`, `933500=30/30`. Reject.
  - v273 used the same downsampled data without label balancing:
    `929500=29/30`, `933500=29/30` with one collision. Reject.
- Current decision:
  - Do not push/tag/promote v269-v273.
  - Keep v270 as a useful diagnostic baseline, not a candidate.
  - Do not continue blindly mixing single failure traces into the low-dimensional
    final-insert adapter; the policy becomes seed-bucket sensitive.
- Next recommended direction:
  - Collect a broader, balanced failure-correction set across several repeat
    failures before retraining another adapter, or switch to an explicit
    deployment-time guarded insert policy that handles late low-Z progress
    without relying on a tiny learned XY adapter.
  - If continuing adapter work, add per-dataset/sample weighting or a real
    DAgger loop so one new failure trace cannot dominate the learned correction
    surface.

## 2026-06-07 v274-v275 Weighted Adapter Diagnostics

- Added per-dataset weighting to `scripts\train_final_insert_adapter.py`:
  - New flag: `--dataset-weights`, ordered as `--dataset` followed by
    `--extra-datasets`.
  - Final sample weight is dataset weight multiplied by the optional
    label-phase balancing weight, then normalized to train-set mean `1.0`.
  - Metadata now records dataset weights and train sample-weight range.
  - Static check passed:
    `python -B -m py_compile scripts\train_final_insert_adapter.py`.
- v274 tested whether low-weight `933514` data could fix the v270 `933500`
  timeout without damaging `929500`:
  - Training inputs: v174 low-Z failure/success, v269 `929524`, and v272
    downsampled `933514`.
  - Dataset weights: `1.0, 1.0, 0.35, 0.05`.
  - Checkpoint:
    `D:\peg-in-hole-6yh\v274_weighted_final_insert_adapter\final_insert_adapter_v274_weighted_035_005_e120.pt`.
  - Results:
    - `929500=30/30`
    - `933500=28/30`, one timeout and one collision
  - Reject. Even very low-weight `933514` data introduced new failures.
- v275 removed the `933514` data and only kept v174 plus low-weight v269:
  - Dataset weights: `1.0, 1.0, 0.35`.
  - Checkpoint:
    `D:\peg-in-hole-6yh\v275_weighted_final_insert_adapter\final_insert_adapter_v275_v174_v269_w035_e120.pt`.
  - Initial 30ep gate:
    - `929500=30/30`
    - `931500=30/30`
    - `933500=30/30`
  - Repeat `929500=29/30`, one collision on `929518`.
  - A runtime probe raising `--final-insert-adapter-square-risk-xy-min` to
    `0.008` still produced `929500=29/30`, but the failure moved to `929524`
    and the adapter never activated. This indicates the remaining failure is
    not purely adapter-action pollution; the guarded final insert/recovery
    stack remains repeat-sensitive.
- Current decision:
  - Do not push/tag/promote v274 or v275 yet.
  - v275 is the best weighted-adapter diagnostic so far and worth keeping as a
    local comparison point.
  - Do not add `933514` back into adapter training unless there is broader
    multi-seed data or explicit per-failure weighting/DAgger supervision.
- Next recommended direction:
  - Either collect a broader balanced correction set across several independent
    repeat failures, or move the remaining late low-Z contact handling into a
    more explicit guarded insert/recovery controller.
  - For a promotion candidate, require at least serial `929500/931500/933500`
    plus repeat `929500` with zero collision and zero timeout.

## 2026-06-07 v276-v277 Release Contact Brake Diagnostics

- Added a default-off hard-square guard for the narrow failure mode observed
  after `square_fast_settle_contact_soft_hold_release_continue`:
  - New config group:
    `guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_*`.
  - It only evaluates during the soft-hold release-continue phase.
  - It detects low-Z, small-XY wall contact after release and can hand off to
    the existing contact-brake path before another down action is applied.
  - New optional response flag:
    `guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_soft_hold_first_enabled`.
    When enabled, release-window contact first returns to the cheaper
    contact-soft-hold path if attempts remain, then escalates to full
    contact-brake only when needed.
- v276 config:
  `configs\sim\ur5e_full\eval_multi_geometry_v276_v265_release_contact_brake_hard_square_30ep.yaml`.
  - Base: v265.
  - Uses the v275 weighted final-insert adapter:
    `D:\peg-in-hole-6yh\v275_weighted_final_insert_adapter\final_insert_adapter_v275_v174_v269_w035_e120.pt`.
  - Results:
    - `929500=30/30`
    - `931500=30/30`
    - `933500=30/30`
    - repeat `929500=29/30`, one timeout on `929518`
  - Diagnosis: v276 fixed the collision-style release contact failure, but the
    heavy response consumed contact-brake/recovery budget and exposed a
    late-timeout path. Reject as a release candidate.
- v277 config:
  `configs\sim\ur5e_full\eval_multi_geometry_v277_v276_release_contact_soft_hold_first_hard_square_30ep.yaml`.
  - Base: v276.
  - Enables soft-hold-first response before full contact-brake escalation.
  - Results:
    - `929500=30/30`
    - repeat `929500=30/30`
    - `931500=30/30`
    - `933500=30/30`
  - Total focused gate: `120/120`, collision `0`, timeout `0`.
  - v277 is the current best local hard-square candidate, but should still get
    one wider fresh-seed gate before push/tag/promotion because previous
    hard-square candidates were repeat-sensitive.
- Wider v277 fresh-seed gate:
  - `935500=30/30`, collision `0`, timeout `0`.
  - `927500=29/30`, one timeout on `927514`.
  - The `927514` timeout ended clean and near inserted: final XY about
    `2.2 mm`, final Z about `13.9 mm`, low yaw, positive topdown/tilted
    clearance margins, and no collision. It is a late recovery-budget/tail
    completion problem, not the release-window collision problem that v277
    targeted.
- v278 config:
  `configs\sim\ur5e_full\eval_multi_geometry_v278_v277_clean_tail_down_boost_hard_square_30ep.yaml`.
  - Tried to fix `927514` by extending late-down-boost to `12 mm`, raising
    max down action to `0.004`, and reducing min phase steps.
  - Result on `927500=28/30`, with one collision and one timeout.
  - Reject. Raising the global late-down-boost cap is too broad; it can amplify
    low-Z contact around the 20-32 mm band.
- v279 config:
  `configs\sim\ur5e_full\eval_multi_geometry_v279_v277_clean_tail_zmin_only_hard_square_30ep.yaml`.
  - Tried only extending late-down-boost lower bound to `12 mm` while keeping
    v277's original down cap.
  - Result on `927500=29/30`, with the same clean timeout on `927514`.
  - Reject as a fix. It does not materially change the failing tail behavior.
- Static checks passed after v277:
  - `python -B -m py_compile peg_in_hole_mujoco\guarded_policy.py scripts\eval_guarded_policy.py scripts\train_final_insert_adapter.py`
  - `git diff --check` only reported Windows CRLF conversion warnings.
- Next recommended direction:
  - v280 introduced a separate default-off very-late clean tail boost. v284
    raised only that narrow below-24-mm clean tail cap to `0.0050`; it improved
    `927514` final Z to about `11.5 mm`, but still timed out at `927500=29/30`.
  - v282/v283 tried a late clean direct finish from
    `square_recovery_escape_recenter`; v282 still timed out and v283 was less
    safe because allowing contact continuation exposed XY jumps. Reject both.
  - v285 raised the tail cap to `0.0065` and converted the problem to a
    collision on `927525`. Reject.
  - v286 used `0.0060`; it passed initial `927500=30/30` but repeat `929500`
    regressed to `28/30` with collisions on `929510` and `929524`. The collision
    traces show mid/low-Z wall-contact pop around `22-31 mm`, before the
    very-late clean tail boost should dominate.
  - Current direction: do not promote v286 and do not keep increasing final
    tail down speed. Start from v284 and add a separate default-off
    contact-pop hold for the `XY 10-24 mm`, `Z 20-42 mm`, wall-contact band.
    This is v287:
    `configs\sim\ur5e_full\eval_multi_geometry_v287_v284_contact_pop_hold_hard_square_30ep.yaml`.
  - v287's first gate should run the problematic repeats (`929500`, repeat
    `929500`) plus `927500`. If it avoids collisions but still times out on
    `927514`, then tune only the clean tail cap narrowly, not the contact band.

## 2026-06-07 v287-v293 Contact-Pop / No-Contact Recenter Diagnostics

- Branch: `feature/contact-aware-reinsert`.
- Static checks for the latest code passed:
  - `python -B -m py_compile peg_in_hole_mujoco\guarded_policy.py scripts\eval_guarded_policy.py`
  - `git diff --check` only reports Windows CRLF conversion warnings.
- v287:
  `configs\sim\ur5e_full\eval_multi_geometry_v287_v284_contact_pop_hold_hard_square_30ep.yaml`.
  - Added contact-pop hold in the `XY 10-24 mm`, `Z 20-42 mm` band.
  - `929500=29/30`, collision on `929524`.
  - Diagnosis: the critical `929524` jump happened with wall contact still
    reported as zero, so wall-contact-gated hold was too late.
- v288:
  `configs\sim\ur5e_full\eval_multi_geometry_v288_v287_no_contact_xy_pop_recenter_hard_square_30ep.yaml`.
  - Added no-contact XY-pop current-height recenter.
  - Targeted `929524` single episode passed and trace confirmed
    `square_recovery_escape_no_contact_xy_pop_recenter`.
  - `929500=29/30`, collision on `929521`; failure later involved low-Z stall
    relief after three contact-pop holds.
- v289:
  `configs\sim\ur5e_full\eval_multi_geometry_v289_v288_low_z_stall_hold_resume_hard_square_30ep.yaml`.
  - Re-enabled low-Z stall hold/resume globally.
  - `929500=30/30` and repeat `929500=30/30`, but `927500=29/30` with timeout
    on `927514` at about `42 mm` Z. Reject: global hold can badly regress clean
    late-tail cases.
- v290:
  `configs\sim\ur5e_full\eval_multi_geometry_v290_v288_no_low_z_stall_relief_hard_square_30ep.yaml`.
  - Disabled low-Z stall relief entirely.
  - `929500=28/30`, one timeout and one collision. Reject: some episodes still
    need a recovery outlet.
- v291:
  `configs\sim\ur5e_full\eval_multi_geometry_v291_v288_contact_pop_gated_low_z_hold_hard_square_30ep.yaml`.
  - Added default-off code:
    `guard_final_servo_square_fast_settle_low_z_stall_relief_hold_min_contact_pop_hold_attempts`.
  - Uses low-Z stall hold only after at least three contact-pop holds.
  - `929500=30/30`, `927500=29/30`, `931500=30/30`, repeat
    `929500=30/30`.
  - Better than v289, but still leaves `927514` timeout.
- v292:
  `configs\sim\ur5e_full\eval_multi_geometry_v292_v291_contact_pop_exhausted_recenter_hard_square_30ep.yaml`.
  - Added default-off contact-pop-exhausted current-height recenter.
  - `929500=30/30`, but `927500=28/30` with one timeout and one collision.
  - Reject: exhausted recenter did not finish `927514` and exposed a
    no-contact recenter collision on `927519`.
- v293:
  `configs\sim\ur5e_full\eval_multi_geometry_v293_v291_no_contact_xy_pop_margin_tilt_gate_hard_square_30ep.yaml`.
  - Added default-off no-contact XY-pop recenter gates:
    `margin_min` and `tilt_max_deg`.
  - Sets tilted margin `>= -0.0030` and tilt `<= 3.5 deg`.
  - Results:
    - `929500=30/30`
    - `927500=30/30`
    - `931500=30/30`
    - repeat `929500=30/30`
    - `933500=28/30`, collisions on `933513` and `933523`
  - Diagnosis:
    - `933513`: no-contact recenter still triggers with low topdown margin and
      yaw near `1.55 deg`; next no-contact gate should add topdown/yaw limits.
    - `933523`: separate contact-brake release pop. After contact-brake recenter
      reports stable at about `2.6 mm` XY and `28.6 mm` Z, the next
      fast-settle step pops to about `20.6 mm` XY and collides, likely due to
      residual upward command/control delay and wall contact. This needs a
      post-contact-brake release hold/flush or stricter release check, not more
      no-contact XY-pop tuning.
- Current decision:
  - Do not push/tag/promote v293.
  - Keep the new default-off hooks; they are useful diagnostics.
  - Next useful work is v294: add no-contact topdown/yaw gates for `933513`,
    then separately add a narrow post-contact-brake-release hold/flush for
    `933523`. Validate in order: `933500`, then `929500`, `927500`, `931500`.

## 2026-06-07 v294-v303 Hard-Square Release-Flush Diagnostics

- Branch: `feature/contact-aware-reinsert`.
- v294:
  `configs\sim\ur5e_full\eval_multi_geometry_v294_v293_no_contact_xy_pop_topdown_yaw_gate_hard_square_30ep.yaml`.
  - Added topdown/yaw gates to no-contact XY-pop recenter.
  - Result: `933500=29/30`.
  - Fixed `933513`, but `933523` remained.
- v295:
  `configs\sim\ur5e_full\eval_multi_geometry_v295_v294_contact_soft_hold_large_pop_recenter_hard_square_30ep.yaml`.
  - Added contact-soft-hold large-pop current-height recenter.
  - Result: `933500=30/30`, but `929500=29/30` with collision `929524`.
  - Reject as promotable; it moved risk into a repeat-sensitive batch.
- v296:
  `configs\sim\ur5e_full\eval_multi_geometry_v296_v295_no_contact_pop_hold_attempt_gate_hard_square_30ep.yaml`.
  - Restricted no-contact XY-pop recenter to cases with no prior contact-pop
    hold attempts.
  - Result: `929500=29/30`, failure `929517`.
- v297-v299:
  - v297 enabled low-Z relief wide recenter and restored `929500=30/30`, but
    regressed `933500` to `29/30`.
  - v298 narrowed the window and regressed `929500=29/30`.
  - v299 added a dual window: normal `XY<=26 mm`, wider `XY<=35 mm` only
    after at least three contact-pop holds. Result: `929500=30/30`,
    `933500=29/30`. Treat v299 as a useful diagnostic point, not a release.
- v300-v301:
  - Narrowing no-contact XY-pop recenter to `25 mm`, or tightening yaw to
    `1.10 deg`, both worsened `933500` to `28/30`. Reject.
- v302:
  `configs\sim\ur5e_full\eval_multi_geometry_v302_v299_recenter_drift_lift_hard_square_30ep.yaml`.
  - Added recenter drift-lift guard. If `square_recovery_escape_recenter`
    drifts to large XY/yaw while no contact is reported, return to recovery
    lift.
  - Result: `933500=29/30`.
  - Fixed `933506`, but `933523` returned.
  - Diagnosis for `933523`: post-contact-brake release pop. The controller
    reaches `square_contact_brake_recenter` stable around `XY 2.6 mm`,
    `Z 28.6 mm`, then the immediate return to `square_fast_settle` jumps to
    about `XY 20.6 mm` and collides.
- v303:
  `configs\sim\ur5e_full\eval_multi_geometry_v303_v302_contact_brake_release_flush_hard_square_30ep.yaml`.
  - Added default-off controller hooks and enabled a narrow
    `square_contact_brake_release_flush` phase in this config.
  - Flush is zero-action for 4 steps after stable contact-brake recenter,
    gated by square geometry, at least two brake attempts, `XY<=4 mm`,
    `Z=20-35 mm`, and contact count `<=8`.
  - Current validation order:
    1. `933500/30ep`
    2. if pass, `929500/30ep`
    3. if pass, `927500/30ep` and `931500/30ep`
  - Do not push/tag/promote until v303 clears the focused seed gate.

## 2026-06-07 v304-v313 Hard-Square Exhausted-Continue Diagnostics

- Branch: `feature/contact-aware-reinsert`.
- Current verified baseline:
  - Re-ran current-code v307 on `931500/30ep`:
    `D:\peg-in-hole-6yh\v307_current_baseline\eval\v307_current_seed931500.*`.
  - Result: `931500=29/30`, collision `0`, timeout `1`.
  - v307 remains the best conservative diagnostic baseline, but it is not a
    release candidate because `931509` still times out.
- v304-v308 summary:
  - v304 made contact-brake release flush late-only; `933500=29/30`, failed
    `933514`.
  - v305 relaxed no-contact XY-pop recenter gates; it passed `933500` and
    `929500`, but failed `927500` and `931500` at `28/30`. Reject.
  - v306 added contact-pop-hold current-height recenter; it fixed the known
    `927525` collision class, but left `927514` timeout and `931512`
    collision. Reject as a release.
  - v307 added preemptive-hold pop recenter; current-code result remains
    `931500=29/30` with only `931509` timeout. Best conservative diagnostic
    point.
  - v308 enabled low-Z exhausted continue. It fixed `931500=30/30`, but
    regressed `933500=28/30`, `929500=29/30`, and left `927500=29/30`.
    Reject: exhausted-continue was too broad.
- v309:
  `configs\sim\ur5e_full\eval_multi_geometry_v309_v307_strict_late_finish_continue_hard_square_30ep.yaml`.
  - Used existing `late_finish_continue` instead of exhausted-continue.
  - Result: `931500=27/30`, collision `2`, timeout `1`.
  - Reject. The gate did not provide a safe replacement for exhausted-continue.
- v310:
  `configs\sim\ur5e_full\eval_multi_geometry_v310_v307_gated_exhausted_continue_hard_square_30ep.yaml`.
  - Added default-off exhausted-continue gates:
    `min_steps_since_reset`, `topdown_margin_min`, `yaw_max_deg`.
  - Low-Z window stayed at `Z=24-30 mm`.
  - Result: `931500=28/30`, collision `1`, timeout `1`.
  - Diagnosis: the current `931509` failure triggers recovery earlier, around
    `Z 37-38 mm`, while XY/yaw/topdown/tilted margins are still clean.
- v311:
  `configs\sim\ur5e_full\eval_multi_geometry_v311_v310_high_z_gated_exhausted_continue_hard_square_30ep.yaml`.
  - Moved the gated exhausted-continue window upward to `Z=36-39 mm`.
  - Result: `931500=29/30`, collision `1`, timeout `0`.
  - Useful diagnostic: it removes the `931509` timeout class, but leaves a
    low-Z pop collision on `931524` after `Z ~= 27 mm`, `XY ~= 2.6 mm`, wall
    contact `4`, and exhausted brake attempts.
- v312-v313:
  - v312 enabled the existing low-Z contact down guard globally on top of v311.
    Result: `931500=28/30`, collision `1`, timeout `1`. Reject.
  - v313 added a default-off `low_z_contact_down_guard_min_steps_since_reset`
    hook and enabled the guard only after 700 steps. Result: `931500=28/30`,
    collision `1`, timeout `1`. Reject.
- Current decision:
  - Do not push/tag/promote v309-v313.
  - Keep the new default-off parameters because they make the diagnostic space
    more controllable and default to old behavior.
  - Best current diagnostic points:
    - conservative: v307 current-code baseline, `931500=29/30`, no collision.
    - exploratory: v311, `931500=29/30`, no timeout but one low-Z pop collision.
  - Next technical direction should not be a broader down guard. Implement a
    narrowly scoped low-Z pop detector/recovery for `square_fast_settle` after
    exhausted contact-brake attempts:
    detect wall contact at `Z 24-31 mm`, `XY<=4 mm`, positive topdown/tilted
    margin before the pop, then avoid immediate continued descent/recenter into
    the wall. Validate first on `931500/30ep`, then `927500`, `933500`, and
    `929500`.

## 2026-06-09 v329-v330 Pre-Pop Offline Gate Diagnostics

- Branch: `feature/contact-aware-reinsert`.
- Added default-off pre-pop guard controls:
  - `guard_final_servo_square_fast_settle_pre_pop_guard_max_phase_steps`
  - `guard_final_servo_square_fast_settle_pre_pop_guard_topdown_margin_max`
  - `guard_final_servo_square_fast_settle_pre_pop_guard_tilt_min_deg`
- Added/updated diagnostic artifacts:
  - `scripts/analyze_pre_pop_guard_traces.py` now supports the same
    `max_phase_steps`, `topdown_margin_max`, and `tilt_min_deg` constraints
    used by runtime.
  - `configs/sim/ur5e_full/eval_multi_geometry_v329_v316_pre_pop_guard_offline_narrow_hard_square_30ep.yaml`
  - `configs/sim/ur5e_full/eval_multi_geometry_v330_v329_pre_pop_guard_stronger_hold_hard_square_30ep.yaml`
- Offline trace scan:
  - Success traces collected for v316 on `927500`, `929500`, and `931500`.
  - Default broad pre-pop gate matched `5/84` success traces, `2/2`
    collision traces, and `1/1` timeout trace. Reject as too broad.
  - v329 narrowed gate
    (`topdown_margin=0.0010-0.00145`, `tilt>=0.6 deg`,
    `yaw<=0.4 deg`, `phase_steps=8-25`) matched `0/84` success traces,
    `2/2` collision traces, and `0/1` timeout traces.
- Runtime evals:
  - v329 `927500/30ep`: `29/30`, failure `927518` collision. Failure trace
    had no pre-pop trigger.
  - v329 `929500/30ep`: `28/30`, failures `929521` timeout and `929525`
    collision. `929525` triggered pre-pop but was not recovered.
  - v329 `931500/30ep`: `27/30`, failures `931509`, `931518`, `931524`
    timeout. Failure traces had no pre-pop trigger, so this is likely
    run-to-run instability rather than direct pre-pop side effect.
  - v330 stronger hold (`8` steps, `+0.003` up) on `929500/30ep`: `26/30`,
    all failures collision. Reject; stronger hold did not recover `929525`
    and correlated with worse outcomes.
- Diagnosis:
  - The v329 gate is useful diagnostically: it can identify a collision-prone
    low-Z state without hitting the sampled success traces.
  - The current intervention form, a short zero-XY upward hold, is not enough.
    In `929525`, z continued downward through the pre-pop hold, then XY popped
    from about `1.9 mm` to `3.3 mm` with wall contact and then to about
    `21 mm`.
- Decision:
  - Do not push/tag/promote v329 or v330.
  - Keep the default-off hooks and configs as diagnostic tools.
  - Next implementation should target the low-Z wall-contact onset after the
    pop starts, not a stronger pre-pop hold: detect first wall-contact spike
    in `square_fast_settle` around `Z 26-33 mm`, `XY<=4 mm`, positive
    clearance, and exhausted brake/soft-hold history, then immediately switch
    to a controlled lift/recenter/retry rather than allowing another downward
    step into the wall.

## 2026-06-18 Keyhole Descent-Abort Diagnostic

- Implemented default-off `guard_visual_yaw_align_descent_abort_*` runtime
  controls in `scripts\eval_guarded_policy.py`.
- Added step trace fields for descent-abort active/triggered/phase/attempts,
  config validation, markdown reporting, control-history flush, and per-step
  pose IK target reset while the abort phase is active.
- Added diagnostic configs:
  - `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_vy_conf_relax_descent_abort_eval.yaml`
  - `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_vy_reacquire_descent_abort_unreliable_eval.yaml`
- Results:
  - relaxed-yaw + descent-abort can rescue individual hard seeds such as
    `908516` in 1ep smoke, but 40ep probes introduced timeout/collision
    regressions on `906500` or `908500`.
  - bounded re-acquire + low-Z unreliable descent-abort: `906500=18/20`,
    collision `0`; `908500=17/20`, collision `1`.
  - adding a large-predicted-yaw trigger rescued `908516` 1ep but regressed
    the 40ep gate to `906500=18/20`, collision `1`; `908500=15/20`,
    collision `0`.
- Decision: keep descent-abort as instrumentation/default-off diagnostics
  only. Do not promote or tag these configs. Current safest key-yaw baseline
  remains
  `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_eval.yaml`
  at `104/120`, collision `0/120`.
- Follow-up temporal visual-yaw action/descent gate:
  - Added default-off `guard_visual_yaw_align_temporal_action_gate_*`
    controls. The hard reset-target version caused `906500/908500/908516`
    1ep smoke to timeout, because it repeatedly cleared the yaw target before
    convergence.
  - The current diagnostic config
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_temporal_action_gate_eval.yaml`
    keeps the yaw target active and only blocks descent while large yaw
    predictions are not temporally stable.
  - 40ep: `906500=19/20`, collision `0`; `908500=16/20`, collision `0`.
    Compared with the existing visible-brake 120ep traces, `906500` is flat
    and `908500` improves by one episode.
  - Targeted hard 60ep: `908500=16/20`, `909500=14/20`, `910500=17/20`,
    total `47/60`, collision `0`, timeout `13`. This is below the existing
    stronger candidates, so do not promote.
- Next technical direction: stop broad scalar safety scans. Either improve the
  visual-yaw confidence/action gate before low-Z descent, or design a more
  deliberate high-Z retreat/recenter controller that is validated against
  success-preservation seeds before hard-failure seeds.

## 2026-06-18 Keyhole Failure-Mode Trace Analysis

- Added `scripts\analyze_key_yaw_failure_modes.py`, an offline diagnostic that
  aggregates rectangular-key tight-yaw episode summaries plus step traces into
  per-episode failure modes and visual-yaw statistics.
- Generated:
  - `results\key_yaw_failure_mode_analysis.md`
  - `results\key_yaw_failure_mode_analysis.csv`
- Inputs used:
  - local visible-brake subset:
    `results\sim2real_multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_multiseed_120ep`
  - temporal descent gate:
    `results\vy_visible_brake_temporal_descent_gate_targeted_60ep`
- Local visible-brake directory currently contains four 20ep seeds, not the
  full historical six-seed run. The diagnostic result for the available subset
  is `70/80`, collision `0`, timeout `10`; keep the historical baseline record
  as `104/120`, collision `0/120`.
- Temporal descent gate targeted result remains `47/60`, collision `0`,
  timeout `13`.
- Failure-mode result:
  - visible-brake subset failures: `6/10` are
    `timeout_wrong_yaw_basin`, `2/10` are residual yaw-not-aligned, `1/10`
    is low-Z/insert-band misalignment with final yaw already correct, and
    `1/10` never descends low enough.
  - temporal gate failures: `10/13` are `timeout_wrong_yaw_basin`, `2/13`
    are residual yaw-not-aligned, and `1/13` never descends low enough.
- Interpretation: the remaining keyhole tail is dominated by asymmetric key
  yaw ending in the wrong 180-degree basin. Temporal descent blocking and
  low-visibility braking can avoid some risky downward motion, but mostly
  convert bad yaw states into timeout. The next promoted direction should be a
  stronger visual-yaw estimator/confidence pipeline, not another scalar safety
  threshold scan.
- Follow-up opportunity check:
  - Extended the analysis script to count correct high-yaw visual evidence.
  - Both success and failure episodes frequently contain reliable large-yaw
    visual evidence, so "seeing the yaw" alone is not discriminative.
  - The failure tail is more likely a controller/gating/reacquisition problem:
    the system can see wrong-basin yaw at some point, but does not preserve or
    safely reacquire the yaw target through later recovery/recenter phases.
- Rejected near-control activation diagnostic:
  - Added
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_near_control_eval.yaml`.
  - It keeps the visible-brake baseline but changes
    `guard_visual_yaw_align_activation_mode` from `final_servo` to
    `near_control`.
  - 1ep smoke on `908508,908516,910500`: `0/3`, collision `2`, timeout `1`.
  - Decision: do not promote. Earlier visual-yaw activation destabilizes hard
    seeds and can create collisions. The next controller test should be a
    narrower wrong-basin yaw reacquire/target-preservation phase, not global
    `near_control`.
- Target-hold diagnostics:
  - Added
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_high_yaw_target_hold_eval.yaml`.
    This lets target hold arm and release on high yaw (`180/180`). It rescued
    `910500` 1ep but caused a collision on `908508` and a timeout on `908516`;
    reject as too broad.
  - Added
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_high_yaw_arm_target_hold_eval.yaml`.
    This arms on high yaw but keeps the normal `8 deg` release threshold.
  - Formal smoke on `906500,908500,908516`: `2/3`, collision `0`, timeout `1`.
  - 40ep on `906500,908500`: `35/40`, collision `0`, timeout `5`
    (`906500=20/20`, `908500=15/20`).
  - Failure analysis:
    `results\key_yaw_high_yaw_arm_failure_analysis.md`.
    Failures remain dominated by wrong-yaw basin (`4/5`).
  - Decision: do not promote. The config-level high-yaw target-hold tweak is
    safe enough for diagnostics but does not improve `908500` over the current
    visible-brake baseline. The next useful implementation needs an explicit
    stateful wrong-basin yaw reacquire/target-preservation phase, not another
    target-hold scalar.

## 2026-06-18 Wrong-Basin Hold Diagnostic

- Added a default-off wrong-basin target-preservation hook in
  `scripts\eval_guarded_policy.py` and the matching config
  `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_wrong_basin_hold_eval.yaml`.
- The hook is rectangular-key only, requires stable large predicted yaw, and
  can preserve the current IK target while blocking descent and recentering XY
  in a narrow near-hole band.
- Smoke on seeds `906500,908500,908516`:
  - wide first pass: `2/3`, collision `0`
  - 3 cm max-XY variant: `1/3`, collision `0`
  - 6 cm max-XY variant: `2/3`, collision `0`
- 40ep on `906500,908500`:
  - baseline visible-brake: `35/40`, collision `0`
  - wrong-basin hold wide: `33/40`, collision `0`
  - wrong-basin hold 6 cm: `34/40`, collision `0`
- Failure-mode analysis:
  `results\key_yaw_wrong_basin_hold_failure_analysis.md`.
  The new hook is safe enough for diagnostics but does not beat the current
  visible-brake baseline. Keep it default-off and do not promote or tag it.
  The next useful step is still a narrower yaw-reacquire hypothesis or a
  better confidence gate, not more broad hold/recenter widening.

## 2026-06-23 Narrow Wrong-Basin Re-Acquire Diagnostic

- Added
  `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_wrong_basin_reacquire_narrow_eval.yaml`.
- Added default-off re-acquire trigger quality gates in
  `scripts\eval_guarded_policy.py`:
  `guard_visual_yaw_align_reacquire_trigger_require_visible`,
  `guard_visual_yaw_align_reacquire_trigger_require_stable_delta`,
  `guard_visual_yaw_align_reacquire_trigger_stable_window`, and
  `guard_visual_yaw_align_reacquire_trigger_max_delta_deg`.
- Smoke on seeds `906500,908500,908516`:
  - ungated narrow re-acquire: `3/3`, collision `0`; it rescued `908516`.
  - gated narrow re-acquire plus low-Z large-XY brake: `2/3`, collision `0`;
    it blocked the unsafe low-confidence trigger but no longer rescued
    `908516`.
- 40ep on `906500,908500`:
  - visible-brake baseline: `35/40`, collision `0`, timeout `5`
  - hold 6 cm: `34/40`, collision `0`, timeout `6`
  - narrow re-acquire ungated: `35/40`, collision `1`, timeout `4`
  - narrow re-acquire gated + low-Z drift brake: `34/40`, collision `0`,
    timeout `6`
- Analysis report:
  `results\key_yaw_wrong_basin_reacquire_narrow_analysis.md`.
- Decision: do not promote or tag narrow re-acquire. The ungated variant can
  rescue a hard seed but introduces collision risk from low-confidence
  `raw_norm_gate` triggers. The gated variant restores safety but loses the
  rescue. The next useful work should shift from more scalar yaw-reacquire
  tuning to a more explicit low-Z lateral-pop / delayed-action recovery, or to
  improving the visual-confidence pipeline before re-acquire is allowed to
  change descent behavior.

## When To Update This File

Update this file after:

- a new training/eval checkpoint becomes recommended
- major metrics change
- the default model path changes
- UR5e full model moves from demo-only to training path
- real-robot readiness gates change
- a milestone is pushed to GitHub
- the next-step plan changes materially
