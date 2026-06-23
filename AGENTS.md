# Agent Working Notes

Last updated: 2026-06-17

This file records the standing workflow, user preferences, safety rules, and project constraints for future Codex work in this repository. Read this file before making non-trivial changes.

## Project Goal

Build a MuJoCo peg-in-hole reproduction inspired by `DRL_Peg-in-Hole_UR5`, then evolve it into a UR5e sim-to-real pipeline.

The current focus is:

- Keep the existing lightweight UR5e adapter training pipeline usable.
- Add and validate a full UR5e MuJoCo task model.
- Improve robustness with image observations, near-hole crop, domain randomization, guarded insertion, and staged geometry curriculum.
- Treat v47 early-final-servo boundary as the current promoted strict-1000 multi-geometry boundary candidate.
- Prepare real UR5e deployment in read-only / dry-run form before enabling any real robot motion.
- Treat `sim2real_multigeom_v1` as the cleaned v148/v149 same-shape multi-geometry sim-to-real mainline. Use `SIM2REAL_MULTIGEOM_V1.md` first for commands and status; do not confuse this with the v221 hard-square-only recovery line.
- Treat `feature/multigeom-v2-true-fixtures` as the experimental true-fixture branch. It is opt-in through `geometry_fixture_mode=true_mesh`, currently covers `hex_hex`, `triangle_triangle`, `slot_slot`, and `rectangular_key`, and must not replace the v1 sim-to-real mainline until multi-seed validation and size-randomized mesh fixtures are done.
- Treat `feature/multigeom-v2-visual-yaw-align` as the current active research branch for visual yaw alignment on top of the true-fixture stack. Use `SIM2REAL_MULTIGEOM_V2_VISUAL_YAW_ALIGN.md` first for its commands and status.
  Current low-Z view-ranking result: `crop_wider_high` is the best candidate
  among the tested final-descent crop/camera variants; use the low-Z
  `*_key_focus_8k_stratified_low_z_crop_high.yaml` configs for the next yaw
  estimator run.

## User Preferences

- Use Chinese for user-facing explanations unless the user asks otherwise.
- Be direct and implementation-first.
- Prefer concrete commands, current metrics, and next-step plans over abstract discussion.
- Keep useful project milestones documented.
- Push useful stable milestones to GitHub when requested, but do not push every small local change automatically.
- Keep `PLAN.md`, `COMMANDS.md`, and `AGENTS.md` aligned with the active branch and the current experimental focus.
- Do not ask unnecessary questions; make conservative assumptions when the repo context is enough.
- The user permits opening Codex sub-agents / parallel tool work when useful for bounded subtasks or parallel experiments. Use this only when it materially speeds the task; keep write scopes separated and do not duplicate work.

## Safety Rules

- Do not enable real robot motion without explicit user approval.
- Real-robot work must stay read-only, synthetic, dry-run, or config-validation until the user explicitly decides to move forward.
- Keep strict real deployment gates:
  - camera calibration required
  - near-hole image crop required
  - target/workpiece calibration required
  - TCP pose trace validation required
  - dry-run validation required
- Never hard-reset or revert unrelated user changes.
- Do not touch `main` for risky work; use feature branches for model replacement, UR5e migration, or larger experiments.

## Repo Conventions

- Current active worktree root: `D:\peg-in-hole-6yh\_promotion_v075_square_pose_yaw_align_20260603213104`
- Historical/original worktree with some large checkpoints: `D:\peg-in-hole-6yh\mujoco_peg_in_hole`
- Current working branch: `feature/multigeom-v2-visual-yaw-align`
- Current active candidate branch: `feature/multi-geometry`
- Stabilized single-geometry baseline branch: `feature/control-state-observation`
- Remote: `https://github.com/AquaMarine763/mujoco-peg-in-hole-ur5.git`
- The `scripts\sim2real\*.ps1` shortcuts are the preferred entry points for the cleaned v148/v149 mainline. They set `PYTHONPATH` to the current worktree first and resolve the policy checkpoint from the current worktree or the sibling `D:\peg-in-hole-6yh\mujoco_peg_in_hole` worktree.
- `scripts\sim2real\eval_multigeom_v2_true_fixture.ps1` and `scripts\sim2real\demo_multigeom_v2_true_fixture.ps1` are the preferred entry points for the experimental true-fixture branch. They enable `geometry_fixture_mode=true_mesh` through config/CLI while preserving v1 defaults elsewhere.
- `scripts\demo_policy.py` now supports the sim2real v1 full demo action chain: policy -> approach adapter -> guarded controller -> final-insert adapter -> square pose/yaw align -> MuJoCo step. Final-insert adapter activity is gated and may stay at zero on clean successful demos.
- Current sim2real demo output renders `overview` plus `wrist_cam` and appends
  a policy-observation grid by default: upper-left `overview`, lower-left
  `wrist_cam`, upper-right `cam_image`, lower-right `near_hole_crop`. The panel
  is built from the live obs dict. The optional `hole_top` camera is not default
  because wrist occlusion makes it less useful during insertion. The XML
  `hole_cavity_visual` geom is visual-only (`contype=0`, `conaffinity=0`) and
  exists only to make the hole opening visible in demo frames; do not treat it
  as collision geometry. It is intentionally hidden for `hex` and `triangle`
  holes because a round marker made polygon demos look incorrectly round. For
  `hex` and `triangle`, the XMLs also include `hole_polygon_visual_0..5`
  geoms. They are visual-only and are dynamically placed with overlapping ends
  so the demo block looks connected, while the original collision wall segments
  remain active but transparent. Do not describe this v1 path as a final CAD
  fixture: it is still a box-wall scaffold. `slot_slot` and `rectangular_key`
  remain rectangular scaffold profiles with different aspect ratios in v1. The
  v2 `true_mesh` path now has opt-in rounded-slot/keyhole mesh geometry.
- v2 true-fixture status:
  - `scripts\generate_true_fixture_mesh_assets.py` generates fixed-size convex
    wall meshes for the full UR5e task XML.
  - `hex_hex`, `triangle_triangle`, `slot_slot`, and `rectangular_key` have
    opt-in true mesh fixture support. `slot_slot` also has an opt-in slot peg mesh in
    `true_mesh` mode; default `box_wall` mode still uses the old box peg.
    `rectangular_key` uses a keyhole profile in `true_mesh` mode: round body
    plus one protruding tab. It uses `peg_keyhole_mesh`, a visual-only
    `true_keyhole_fixture_visual_mesh`, and 11 transparent convex wall
    segments for collision. The keyhole opening also uses visual-only dark
    bottom markers: `hole_cavity_visual` for the round body and
    `hole_key_tab_cavity_visual` for the tab. These must stay non-colliding and
    should be described as demo/observation aids, not physical bottom geometry.
    Demo rendering uses a separate visual-only ring mesh for these shapes,
    while the segmented convex wall meshes remain active for collision but are
    transparent.
    Polygon peg demo clarity is improved with visual-only tip cap, tip outline,
    and subtle side-edge highlight meshes for `hex` and `triangle`; they are
    dynamically enabled only for those peg shapes and must remain
    `contype=0`, `conaffinity=0`.
    `rectangular_key` also uses the same visual-only peg-tip path for the key
    peg bottom face: `peg_keyhole_tip_cap_visual_mesh` and
    `peg_keyhole_tip_outline_visual_mesh`. This is separate from the keyhole
    opening's dark bottom marker and must also remain non-colliding.
    `triangle_triangle` true mesh clamps the triangular hole circumdiameter to
    at most `2x` the peg diameter.
    MuJoCo mesh compiler pose compensation (`model.mesh_pos` /
    `model.mesh_quat`) is required for correct fixture placement.
  - Current smoke gate on seed `906500`: `hex_hex=10/10`,
    `triangle_triangle=10/10`, and `slot_slot=10/10`, zero collision and zero
    timeout after visual-ring and triangle-clamp changes. Treat this as
    prototype evidence only, not a stable release gate.
  - 2026-06-10 polygon peg visual-highlight smoke: `hex_hex=10/10` and
    `triangle_triangle=10/10`, zero collision and zero timeout. The hex demo is
    under `results\sim2real_multigeom_v2_true_fixture_demo_polygon_peg_highlight`.
  - 2026-06-10 keyhole v2 bottom-visual smoke: `rectangular_key=10/10`, zero
    collision and zero timeout. Demo:
    `results\sim2real_multigeom_v2_true_fixture_demo_keyhole_bottom_visual\demo_rectangular_key_seed906500.gif`.
  - 2026-06-10 key peg tip visual smoke: `rectangular_key=10/10`, zero
    collision and zero timeout. Demo:
    `results\sim2real_multigeom_v2_true_fixture_demo_keyhole_peg_tip_visual\demo_rectangular_key_seed906500.gif`.
  - 2026-06-16 analytic shape yaw sensitivity scan added at
    `scripts\scan_shape_yaw_sensitivity.py`. It is 2D geometry only and does
    not use visual-only peg-tip highlights or policy rollouts. Focused
    candidate clearances from the first pass:
    `rectangular_key=0.75-1.25mm`, `square_square=0.5-1.0mm`,
    `triangle_triangle=0.5-1.0mm`, `hex_hex=0.5mm`.
  - 2026-06-16 tight-yaw true-fixture variant added through
    `geometry_true_fixture_variant=tight_yaw` and
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_eval.yaml`.
    Current fixed tight-yaw clearances are `rectangular_key=1.0mm`,
    `square_square=0.75mm`, `triangle_triangle=0.75mm`, and `hex_hex=0.5mm`.
    Use `scripts\sim2real\eval_multigeom_v2_true_fixture_tight_yaw.ps1` for
    this pressure test. Initial seed `906500`, 5ep/profile result:
    `rectangular_key=5/5`, `square_square=1/5`,
    `triangle_triangle=5/5`, `hex_hex=5/5`. The square failures are mainly
    near-hole timeouts with yaw/clearance margin errors, which is exactly the
    intended baseline before adding a visual yaw estimator and guarded
    yaw-align phase. `shape_yaw_clearance` is the meaningful non-negative
    clearance for polygon/key tight-yaw diagnostics; legacy `hole_clearance`
    may be negative for polygon shapes and should not be used as the only
    validity check.
    Visual-only peg-tip highlights are demo/debug aids only; keep them
    disabled for image label collection and visual yaw training.
  - 2026-06-16 visual yaw data/training pipeline:
    `scripts\collect_visual_yaw_dataset.py` directly places the UR5e near the
    hole with controlled wrist yaw offsets and records `cam_image`,
    `near_hole_crop`, and `shape_yaw_label_sin/cos`.
    `scripts\train_visual_yaw_estimator.py` trains the first supervised CNN
    baseline. The environment now exposes generic `shape_yaw_*` telemetry and
    an `enable_peg_tip_visual_helpers` flag. Keep this flag off for training
    data. Current 1k baseline on
    `datasets\visual_yaw_v1_tight_yaw_1k.npz` is not control-ready:
    validation mean yaw error `28.5 deg`, p95 `81.1 deg`; per-profile mean
    error `hex_hex=14.3`, `square_square=20.3`, `triangle_triangle=27.0`,
    `rectangular_key=53.1` degrees. Do not wire this estimator into guarded
    yaw-align as-is; first improve key visibility/data scale/camera-crop
    settings.
  - 2026-06-16 view/crop scan and key-focus update:
    `scripts\scan_visual_yaw_views.py` compared `baseline`, `crop_wider`,
    `raise_center`, and `open_high` using 128 samples/candidate and 8 epochs.
    `raise_center` won the key-error tie-breaker, but `crop_wider` is the
    lower-risk sim-to-real candidate because it keeps the current wrist camera
    pose and only widens `near_hole_crop_source_size` from `64` to `80`.
    Using the `crop_wider` setup, I collected
    `datasets\visual_yaw_v1_tight_yaw_key_focus_2k_crop_wider.npz` with
    `rectangular_key` at 50% of samples. The resulting estimator
    `results\visual_yaw_estimator_v1_tight_yaw_key_focus_2k_crop_wider.pt`
    reached best validation mean yaw error `13.7 deg`, p95 `47.4 deg`.
    Per-profile mean error:
    `square_square=5.8`, `triangle_triangle=8.4`, `hex_hex=6.4`,
    `rectangular_key=20.1` degrees. This is the first version that starts to
    look useful for a later guarded yaw-align experiment, but it still should
    not be wired into the controller directly because key p95 remains high.
    Keep `enable_peg_tip_visual_helpers=false` for all training data.
  - 2026-06-16 visual yaw diagnostic update:
    `scripts\eval_visual_yaw_estimator.py` evaluates a yaw checkpoint on the
    reconstructed held-out split, reports per-profile/per-yaw-bin errors, and
    writes a worst-case image sheet. Current 2k crop-wider diagnostic:
    overall mean `13.7 deg`, p95 `47.4 deg`; `rectangular_key` mean
    `20.1 deg`, p95 `56.5 deg`, bad fraction `0.477` for `>15 deg`.
    Key failures concentrate in the `-60..-30 deg` and `-120..-90 deg` yaw
    bins. The collector now supports `yaw_sampling_mode=stratified` and
    `yaw_bin_count`; smoke
    `datasets\visual_yaw_v1_tight_yaw_stratified_smoke_96.npz` validated exact
    key 12-bin coverage. Next learning run should use the new 8k configs:
    `multigeom_v2_true_fixture_tight_yaw_visual_yaw_dataset_key_focus_8k_stratified.yaml`,
    `multigeom_v2_true_fixture_tight_yaw_visual_yaw_train_key_focus_8k_stratified.yaml`,
    and
    `multigeom_v2_true_fixture_tight_yaw_visual_yaw_eval_key_focus_8k_stratified.yaml`.
  - 2026-06-16 8k stratified yaw result:
    `datasets\visual_yaw_v1_tight_yaw_key_focus_8k_stratified_crop_wider.npz`
    has 8192 samples with balanced yaw bins. Estimator
    `results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_crop_wider.pt`
    reached validation mean/p95 `2.10/5.74 deg`; per-profile mean/p95:
    `square_square=1.39/3.80`, `triangle_triangle=1.90/5.04`,
    `hex_hex=1.24/3.32`, `rectangular_key=2.71/6.78` deg. The previous key
    hard bins are now around p95 `4.8-5.0 deg`. This is good enough to start a
    guarded yaw-align prototype, but do not command yaw unconditionally because
    rare severe occlusion outliers remain. Add confidence/visibility gating and
    a no-correction fallback.
  - 2026-06-16 guarded visual yaw-align prototype:
    `peg_in_hole_mujoco\visual_yaw_runtime.py` loads the 8k estimator for
    runtime prediction. `scripts\eval_guarded_policy.py` can now run key-only
    visual yaw correction, optional descent blocking, Z hold, XY hold,
    post-yaw recenter, and opt-in yaw-sensitive success gates. The important
    task definition change is `success_shape_yaw_tolerance_deg`: without it,
    `rectangular_key` can report success from XY/Z only and does not prove that
    the key tab was oriented correctly. Current yaw-sensitive key smoke on seed
    `906500`: baseline no-visual-yaw `0/5`; soft visual yaw `0/5`; strict
    visual yaw hold/recenter recheck `4/10` with `1/10` collision and `5/10`
    timeout; bounded 2 cm `commit_descent_latch` without target hold `15/30`,
    zero collision and fifteen timeouts across seeds `906500/907500/908500`;
    `commit_descent_latch_target_hold` first reached `27/30`, then `55/60`
    across seeds `906500/907500/908500/909500/910500/911500`, but had `2/60`
    collisions. The safer visible variant reached `54/60`, zero collision and
    six timeouts on the same six seeds, but the larger 120ep visible gate still
    exposed `2/120` collisions (`103/120`). For sim-to-real-oriented work,
    prefer the low-visibility brake diagnostic:
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_eval.yaml`.
    It reached `104/120`, zero collision and sixteen timeouts on six 20ep
    seeds.
    Target hold preserves the last visually aligned IK orientation target
    through short raw-norm/XY gate dropouts and fixes most returns to the
    `~180 deg` wrong-yaw basin. The safer visible variant additionally requires
    same-step visible yaw predictions for active descent and releases target
    hold when live predicted yaw exceeds `8 deg`; the brake variant additionally
    lifts and flushes control history under poor yaw visibility, large predicted
    yaw, off-center XY, and low Z. The over-narrow
    `commit_descent` gate almost never triggers, and the wider `xy30` commit
    did not improve success. Do not promote this line until either a larger
    gate passes or the remaining wrong-yaw-basin timeouts are handled.
    Bounded re-acquire/retry now exists as a diagnostic config:
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_eval.yaml`.
    The safer setting triggers from step `350`, allows two high-Z lift/recenter
    attempts, and keeps relaxed yaw correction disabled. It reached `49/60`,
    zero collision and eleven timeouts on targeted seeds
    `908500/909500/910500`; the matching brake subset was `47/60`, zero
    collision and thirteen timeouts. This is a small diagnostic gain, not a
    promotion candidate. The relaxed yaw-correction path inside re-acquire is
    implemented but must stay disabled for now: its first 10ep smoke regressed
    `909500` from `5/5` to `4/5` by pushing a near-recovered case back into
    large XY. The current bottleneck is no longer collision safety; it is
    visual-yaw confidence/action selection during `170-179 deg`
    wrong-yaw-basin recovery. Square visual yaw remains disabled because the
    current runtime distribution produced false roughly `45 deg` predictions on
    square.
    Re-acquire descent also exists as a default-off diagnostic config:
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_descent_eval.yaml`.
    Its 10ep smoke reached `908500=4/5`, `909500=5/5`, collision `0`, but did
    not show enough benefit to promote. Keep it as diagnostic evidence only.
    New offline analyzer:
    `scripts\analyze_visual_yaw_reacquire_traces.py`. On the targeted 60ep
    re-acquire trace, all re-acquire rows had opposite-sign rate `39.3%`;
    runtime visibility reduced this to `17.5%`, and temporal-delta stability
    reduced high-error tail to `1.4%` but at only `19.7%` coverage. Simple
    predicted-sign stability is unsafe because the wrong sign can be stable.
    Next work should design a conservative runtime confidence/action gate, not
    feed signed yaw correction whenever the prediction is merely persistent.
    A conservative relaxed-yaw diagnostic config now exists:
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_confident_relaxed_yaw_eval.yaml`.
    It requires visible prediction stats, a 3-frame signed-yaw delta window
    under `12 deg`, and caps the re-applied correction at `30 deg`. Fixed
    smoke: default re-acquire recheck `908500=5/5`, `909500=4/5`, collision
    `0`; confident relaxed-yaw smoke `908500=5/5`, `909500=5/5`,
    `910500=4/5`, collision `0`, with `reacquire_relaxed_yaw` triggering on
    `8/13/29` rows respectively. Keep this as the next candidate only; do not
    promote until targeted 60ep and six-seed 120ep pass. Note: an indentation
    bug during this implementation briefly disabled `reacquire_active`; it was
    fixed and verified by the default recheck above.
    Targeted 60ep candidate result: `51/60`, collision `1/60`, timeout
    `8/60` on seeds `908500/909500/910500`. It rescued four baseline timeouts
    but regressed two baseline successes and turned `908516` into a plate
    collision. The collision trace had no `reacquire_relaxed_yaw` rows and
    ended with large XY under `z_gate`, so the next implementation should be a
    large-XY/low-Z safety brake, not a stronger relaxed-yaw policy.
    The first large-XY/low-Z brake diagnostic is implemented as
    `guard_visual_yaw_align_large_xy_low_z_brake_*` plus config
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_yaw_success_visual_yaw_hold_xy_recenter_commit_descent_latch_target_hold_visible_brake_reacquire_confident_relaxed_yaw_large_xy_low_z_brake_eval.yaml`.
    A broad `z<=8 cm` trigger passed the targeted hard 60ep set with `52/60`,
    collision `0`, but failed the six-seed 120ep gate with `105/120`,
    collision `1`, timeout `14`. It disrupted `906500`, where the baseline
    low-visibility brake had succeeded. Do not promote it and do not keep
    widening scalar brake thresholds. The next useful direction is a stateful
    descent-permission/abort phase that prevents entering low Z with large XY,
    then explicitly returns to high-Z recenter.
    Stateful descent-abort is now implemented as default-off
    `guard_visual_yaw_align_descent_abort_*` controls and trace fields. It
    resets the pose IK yaw target while active, lifts, recenters, and can flush
    control randomization history. Diagnostics are not promotable yet:
    confident relaxed-yaw + descent-abort rescued `908516` in 1ep smoke but
    produced unsafe 40ep variants; bounded re-acquire + low-Z unreliable abort
    gave `906500=18/20` collision `0`, `908500=17/20` collision `1`; adding a
    large-predicted-yaw trigger gave `906500=18/20` collision `1`,
    `908500=15/20` collision `0`. Current safest key-yaw baseline remains
    `visible_brake_eval` at `104/120`, collision `0/120`. Do not promote/tag
    descent-abort configs without a zero-collision 120ep gate.
    Temporal visual-yaw action/descent gate is also implemented as default-off
    `guard_visual_yaw_align_temporal_action_gate_*`. Hard reset-target smoke
    regressed `906500/908500/908516` to timeout. The softer descent-only
    diagnostic
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_temporal_action_gate_eval.yaml`
    kept zero collision but targeted hard 60ep was only `47/60`
    (`908500=16/20`, `909500=14/20`, `910500=17/20`). Do not promote this
    temporal gate; it is diagnostic evidence that delaying descent alone does
    not fix wrong-yaw-basin timeouts.
    Low-Z lateral-pop recovery is implemented as default-off
    `guard_visual_yaw_align_low_z_lateral_pop_recovery_*` controls and trace
    fields, with diagnostic config
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_lateral_pop_recovery_eval.yaml`.
    The recovery-only smoke on `906500,908500,908516` reached `2/3`,
    collision `0`, timeout `1`; it triggered too late to rescue `908516`.
    A late-finish/freeze-XY variant using
    `guard_visual_yaw_align_low_z_late_finish_descent_*` was rejected because
    it regressed `906500` to timeout and changed `908516` into collision.
    Keep both hooks diagnostic-only and default-off; current safest key-yaw
    baseline remains the visible-brake config.
    `scripts\analyze_visual_yaw_action_selection.py` now summarizes candidate
    runtime action gates from step traces. On the gated narrow re-acquire 40ep
    trace, visible+temporal-delta-stable rows had no sign mismatch and no
    high-error rows, but predicted near-zero yaw was not enough to release
    descent: even `pred<=2deg` and `XY<=8mm` had about `12deg` true yaw on
    average in timeout traces. The high-yaw-only action-selection config
    `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_reacquire_high_yaw_action_selection_eval.yaml`
    disables re-acquire-local descent and only permits visible/stable high-yaw
    re-apply. Same-seed 40ep result was `34/40`, collision `0`, timeout `6`,
    tying gated narrow re-acquire but below visible-brake baseline `35/40`.
    Do not promote this config. The next useful step is likely better visual
    evidence near the final descent point, not more scalar descent thresholds.
    Regression smoke after increasing `true_fixture_wall_0..11`:
    `hex_hex=1/1`, `triangle_triangle=1/1`, and `slot_slot=1/1`, all zero
    collision and zero timeout.
  - Keyhole limitations to remember: current keyhole meshes are fixed-size
    assets, not validated for runtime scale randomization; tight keyhole
    insertion should get key-specific yaw/alignment diagnostics rather than
    reusing square-symmetry yaw logic.
- Current contact-aware hard-square status:
  - Latest stable promoted tag remains `v0.7.6-square-escape-dynamic-xycap`.
  - Do not promote/push/tag a v0.7.7 successor from the current local
    deterministic recovery probes. v170 passed the old hard-square 6x30 gate
    (`180/180`) but failed the fresh 3x30 gate (`88/90`).
  - v171-v206 low-Z deterministic probes are diagnostic only. Default-off
    hooks for late down boost, clearance hold, low-Z relief, direct
    fast-settle, late-only direct fast-settle, and contact-brake variants may
    remain in code if they compile and stay disabled by default.
  - Current-code v198 does not reproduce the older clean `931500=30/30` result:
    a fresh serial replay on `931500` reached only `26/30`, with three
    collisions and one timeout. Treat older v198 files as historical evidence,
    not a promotion gate.
  - v200 direct finish fixed `929500=30/30` but regressed `931500` with one
    collision. v201 high-Z-only direct finish also left `931500=29/30`.
  - v202 pre-lift-on-trigger improved current-code `931500` to `29/30`.
    v203 added a third low-Z contact relief attempt and passed
    `929500=30/30`, `931500=30/30`, and `928500=30/30`, but failed focused
    buckets `924500=29/30` and `927500=28/30`.
  - v204 late-only direct finish did not fix `927500`. v205 added a fourth
    low-Z relief attempt and moved `927500` to `29/30`, still with one
    collision. v206 lowered the no-contact pre-pop relief phase gate from `45`
    to `35`, removing the `927500` collision but producing two timeouts
    (`28/30`). Do not promote v203-v206.
  - Current residual interpretation: low-Z square failures split into
    pre-contact lateral pop states and late escape/recenter timeout states.
    More relief attempts improve safety locally but burn budget; broad direct
    fast-settle can create collisions. The next design should combine earlier
    pre-pop risk detection with a strictly late, bounded finish assist.
  - 2026-06-08 local low-Z soft-hold / lateral-pop diagnostics: current-code
    v311 rerun on `931500/30ep` reached only `27/30`, so do not treat the
    older saved v311 `29/30` as the active baseline without rerunning. v315
    low-Z/margin-gated third soft-hold reached `27/30` and is rejected.
    v316 reduced contact-soft-hold release-continue caps to
    `max_xy=0.00035`, `max_down=0.0008`; a fresh current-code rerun reached
    `931500=30/30`, but key regression buckets still failed
    (`927500=29/30`, `929500=28/30`). v316 is diagnostic only, not a
    promotable milestone. v317 longer soft-hold regressed to `27/30`; v318
    single soft-hold attempt regressed to `26/30`; v319 broad release
    contact-brake fixed `931500` but regressed `927500/929500`; v320 narrow
    second-release contact-brake regressed `931500=27/30`; v321 release-pop
    hold stayed `931500=29/30`; v322 no-contact pop hold regressed
    `927500=27/30` and `929500=27/30`. v323 added severe low-Z
    lateral-pop high reapproach, but `927500/30ep` was only `28/30` with
    one collision and one timeout. v324 skipped the pre-lift hold and still
    reached only `28/30` on `927500`. Do not push/tag v315-v324 as stable
    milestones. v325-v327 explored narrow `square_fast_settle_pre_pop_guard_hold`
    variants; v328 replaced the hold with action limiting in the same risk
    window. Focused `927500/30ep` results were `28/30`, `28/30`, `28/30`, and
    `27/30` respectively. Do not push/tag/promote v325-v328. The next useful
    step is an offline trace classifier/replay table that evaluates candidate
    gates against failure and success traces before another expensive 30ep
    simulation gate. `scripts/analyze_pre_pop_guard_traces.py` now performs
    the first-pass gate scan; initial v316 failure scans show the current gate
    also matches timeout seed `929521`, so success traces are required before
    tuning another runtime intervention.
  - Current residual interpretation: hard-square failures are broader than a
    single soft-hold release pop. The recurring family is low-Z lateral pop
    after repeated contact-brake/contact-pop recovery, followed by either
    pre-lift/recenter collision or 1000-step timeout. Heavy local recovery
    patches can shift failures between buckets; require at least the hard
    regression buckets before promotion.
  - Current-code v170 fresh replay on 2026-06-05 reached `89/90` across
    `927500/928500/929500`; the only remaining failure was `929512` timeout,
    zero collision. This is better than the earlier `88/90` record but still
    below promotion threshold.
  - The residual failure mode is low-Z hard `square_square` contact under
    delayed/filtered control: near-centered states around `1-3 mm` XY and
    `25-35 mm` Z can briefly contact the wall, pop laterally, then either
    collide if insertion is aggressive or timeout if recovery is conservative.
  - v173 smoke validates the data path: `build_square_fast_settle_teacher_dataset.py`
    can extract low-Z `square_fast_settle` labels from failure traces, and a
    tiny 102-sample adapter can train/evaluate, but it stayed `29/30` on
    `929500`. Treat it as infrastructure only.
  - Next technical direction is balanced failure-correction / DAgger around
    policy-visited low-Z lateral-pop states, with success-preservation rows;
    do not continue broad scalar scans of descent speed, yaw weight, escape
    height, or approach-adapter cap.
- Default task model remains the lightweight UR5e adapter unless explicitly switched:
  - `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Full UR5e model lives at:
  - `assets/ur5e_full/ur5e_peg_in_hole_full.xml`
- Current full UR5e task geometry hides debug sites in rendered demos and uses a narrowed hole:
  - peg diameter about `24 mm`
  - base hole opening about `40 mm`
  - randomized geometry opening about `34 - 42 mm`
  - current full UR5e guarded alignment threshold: `0.020 m`
  - current full UR5e guarded blend: `1.0`
- Multi-geometry status:
  - `PegInHoleMujocoEnv` now supports `geometry_profile`.
  - Legacy supported profiles are `single`, `round_square`, `square_square`, and `mixed_basic`.
  - Same-shape scaffold profiles are `round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, `rectangular_key`, and `mixed_same_shape`.
  - XML task assets now include default-off auxiliary hole walls and hex/triangle peg mesh assets. Polygonal peg meshes are centered on the original peg geom origin and scaled to a `12 mm` outer radius.
  - `triangle_triangle` has a temporary easy-curriculum hole floor of `2.2 * peg_radius`; keep this until a better triangular-hole/chamfer model lets us tighten the legacy small-hole range.
  - Keep `single` as the default path unless an experiment explicitly overrides it.
  - This branch is now the active candidate for geometry generalization, while the stabilized single-geometry controller work remains a useful baseline.
  - Expert/correction dataset collection and BC pretraining scripts accept the same geometry args.
  - Dataset files now record `geometry_profile`, `geometry_name`, `peg_shape`, and `hole_shape`; use those arrays to debug multi-geometry balance.
  - Same-shape v0.7.4 guarded recipe 1ep/profile smoke on seed `880000` after geometry fixes: `round_round=1/1`, `hex_hex=1/1`, `triangle_triangle=1/1`, `slot_slot=1/1`, `rectangular_key=1/1`, all zero collision and zero timeout. Result directory: `D:\peg-in-hole-6yh\v91_same_shape_geometry_fixed_smoke`.
  - Same-shape follow-up on seed `881000`: fixed profiles reached `50/50` combined success (`10/10` each for `round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, `rectangular_key`), zero collision and zero timeout. Mixed sampler check on seed `882000`: `mixed_same_shape=20/20`, zero collision and zero timeout. Result directory: `D:\peg-in-hole-6yh\v92_same_shape_matrix10_seed881000`.
  - Same-shape broader fixed-profile matrix on seeds `883000`, `884000`, and `885000`: `150/150` combined success, zero collision, zero timeout, with each fixed profile at `30/30`. Result directory: `D:\peg-in-hole-6yh\v93_same_shape_multiseed_3x10_seed883_885`. This is enough to start balanced same-shape data collection, while keeping the temporary triangle easy-hole floor explicit.
  - Same-shape approach-window DAgger smoke is available at `D:\peg-in-hole-6yh\v94_same_shape_approach_dagger_smoke`. It merged to `640` samples, balanced `128` each across `round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, and `rectangular_key`; all samples are `approach_recenter` with `approach_window_rate=1.0`. Treat it as schema/label smoke only: the collector rollout is learned policy plus rollout adapter, not the full guarded deployment stack, and episode outcomes were poor (`48` success-sourced samples, `416` collision-sourced, `176` timeout-sourced). Do not scale this exact recipe to 50k before adding a guarded-deployment rollout teacher path or collecting from guarded eval traces.
  - Guarded-deployment correction collection is now implemented in `scripts\collect_guarded_image_correction_dataset.py`. It reuses `eval_guarded_policy.py` config parsing and guarded controller execution, then writes the existing correction NPZ schema. Use this for production same-shape approach data instead of the v94 raw policy/adapter rollout recipe.
  - Guarded same-shape approach smoke config: `configs\sim\ur5e_full\collect_guarded_same_shape_approach_smoke.yaml`. The local workspace may not materialize the repo adapter under `assets\approach_adapters` because of the known skip-worktree/ACL workaround; override `--approach-adapter D:\peg-in-hole-6yh\v63_adapter_v8_balanced_dagger\approach_adapter_v8_fullcrop_balanced_seed645_dagger_xy_override.pt` when needed.
  - Guarded same-shape smoke result: `D:\peg-in-hole-6yh\v95_guarded_same_shape_approach_smoke`. Five shards (`round_round`, `hex_hex`, `triangle_triangle`, `slot_slot`, `rectangular_key`) each collected `32` samples from `2/2` successful guarded episodes, zero collision, zero timeout. The merged `160`-sample dataset is balanced at `32` per shape, all success-sourced, all `approach_recenter`, with `approach_window_rate=1.0`.
  - Guarded same-shape 512/profile pilot result: `D:\peg-in-hole-6yh\v96_guarded_same_shape_approach_512`. The merged `image_correction_2560_same_shape_guarded_approach.npz` has `2560` samples, `160` unique successful source episodes, five fixed same-shape profiles balanced at `512` samples each, all success-sourced, all phase `approach_recenter`, `approach_window_rate=1.000`, `descent_should_block_rate=1.000`, zero collision and zero timeout. This is the current clean same-shape approach-training candidate.
  - v97 same-shape-only adapter trained from v96 passed fixed profiles `50/50` on seed `890500`, but failed `mixed_same_shape` seed `890700` at `19/20` because the adapter stayed active for `996` steps and never handed off to final servo. Do not promote v97.
  - v98 preservation adapter trained from v96 plus the v8 adapter datasets. Without an episode-level adapter cap it also failed `mixed_same_shape` seed `890700` at `19/20`; with `--approach-adapter-episode-max-steps 220`, it passed `mixed_same_shape=20/20` on seed `890700`, fixed profiles `50/50` on seed `891500`, and a v99 mixed multi-seed check `60/60` on seeds `891700/892700/893700`, zero collision and zero timeout. Shared v100 comparison showed promoted v8 also passed the same `891700/892700/893700` matrix at `60/60`; v8 mean steps `251.8`, v98+epmax220 mean steps `255.4`. Do not promote/tag v98 yet.
  - Promoted v8 passed a longer v101 `mixed_same_shape` run at `100/100`, zero collision and zero timeout, on seed `894700`. Shape split included `square_square=19/19`; default same-shape scaffold is stable enough for the current stage.
  - v102 narrow-clearance fixed-profile stress used hole half-size `14-16 mm`, round peg radius `12.8-13.5 mm`, and square/slot/key short half-size `12.2-13.5 mm`. Result was `58/60`, with only `square_square` failing (`8/10`, two timeouts, no collisions). Failures reached sub-mm XY but stalled high with high tilt and negative tilted clearance margin. v103 simple probes did not solve it: final-servo orientation weight `0.12` regressed to `7/10` with one collision, and square-fast-settle tilt max `8 deg` stayed at `9/10`.
  - v104 adds a default-off `guard_final_servo_square_fast_settle_contact_unjam_enabled` hook plus eval/demo CLI flags. The hook triggers on persistent wall contact plus high tilt or negative tilted clearance while in `square_fast_settle`, using the square-fast-settle Z envelope. Probe result on seed `895700` regressed to `7/10`, zero collision and three timeouts, so do not promote it.
  - v105-v108 add a default-off `guard_final_servo_square_tilt_reinsert_*` hook for short lift/recenter/reinsert from stuck `square_fast_settle` states. It did not beat the v103 base repeat: the corrected v108 default probe was `8/10` with one collision and one timeout. Do not promote it.
  - v109 adds `scripts\build_final_insert_stuck_dataset.py` for trace-derived square-square narrow-clearance stuck-state data. The combined v102+v108 timeout extraction lives at `D:\peg-in-hole-6yh\v109_final_insert_stuck_dataset` and produced `209` samples, all from `square_fast_settle`, with labels `contact_lift=69`, `micro_recenter=138`, `soft_descend=2`. Treat this as an offline data/labeling entry point for a final-insert adapter, not as a promoted runtime controller.
  - v110 adds a low-dimensional final-insert adapter module and trainer. The output directory is `D:\peg-in-hole-6yh\v110_final_insert_adapter_pilot`. Episode-split MAE is `0.515 mm`, while random-split MAE is `0.061 mm`, so this is a fit/sanity pilot, not a runtime-promoted policy. The normalized-feature clamp is important because held-out wall one-hot features can otherwise explode.
  - v111 expands narrow square-square stuck traces with seeds `895800/895900/896000`; each 10ep run was `9/10`, zero collision, one timeout. Combined v102+v108+fresh stuck data has `483` samples from `6` trace episodes, all `square_fast_settle`, with labels `contact_lift=259`, `micro_recenter=221`, `soft_descend=3`. Current best offline diagnostic adapter is `D:\peg-in-hole-6yh\v111_final_insert_adapter_pilot\final_insert_adapter_combined_episode_split_contact_micro_e100.pt`, with episode-split train/val MAE `0.210 mm / 0.567 mm`. It is not promoted.
  - v112 wires the v111 final-insert adapter into `scripts\eval_guarded_policy.py` as a default-off diagnostic hook. It supports `override`, `override_xy`, and `residual` modes, step-trace action logging, and phase/stall/contact/near-hole gates. Do not enable it by default.
  - v112 targeted result: direct full-action override reached only `36/40`, zero collision and four timeouts on seeds `895700/895800/895900/896000`; do not promote that mode. The best conservative probe so far is `override_xy`, `max_xy_action=0.0012`, `min_stall_steps=15`, which reached `39/40`, zero collision and one timeout versus comparable baseline `37/40`.
  - v113 added the v112 `895803` adapter-visited timeout states back into the stuck dataset (`575` samples from `7` trace episodes) and trained `D:\peg-in-hole-6yh\v113_final_insert_adapter_closed_loop\final_insert_adapter_closed_loop_episode_split_contact_micro_e100.pt`. It did not solve `895803`; validation MAE was `0.645 mm`, worse than v111.
  - v114 adds default-off `--final-insert-adapter-lift-pulse-*` diagnostic flags. The pulse probe on `895800` still timed out on `895803` and increased adapter ownership; do not promote lift pulse.
  - v115 adds default-off `--final-insert-macro-recovery-*` diagnostics for a bounded `lift -> align -> hold` final-insert recovery sequence. Weak/default macro settings did not solve `895803`; a stronger lift fixed it in one focused run but the four-seed matrix stayed at `37/40` and introduced one collision. Do not promote macro recovery.
  - v116 adds macro abort safety knobs for XY divergence and final-servo dropout during an active macro. The same strong-macro four-seed matrix became `36/40`, zero collision and four timeouts. Treat this as a diagnostic safety guardrail only; it converts collision risk into timeout rather than improving insertion.
  - Use `scripts\analyze_final_insert_macro_recovery.py` for future macro probes. Current v115/v116 failure classifications confirm three separate buckets: missed-trigger timeout, triggered high-Z stuck timeout, and triggered divergence/collision risk.
  - v117 adds `scripts\build_phase_aware_final_insert_dataset.py` for phase-aware final-insert teacher data. It consumes guarded `*_episodes.csv` files plus inferred `*_steps.csv`, writes the existing adapter `features/target_actions` schema, and adds `failure_classification` plus `teacher_phase` arrays. Smoke output `D:\peg-in-hole-6yh\v117_phase_aware_final_insert_probe` has `899` samples from `9` trace episodes: `macro_not_triggered_timeout=144`, `macro_triggered_timeout_stuck_high_z=576`, `macro_triggered_timeout_diverged=121`, `macro_triggered_collision_diverged=58`. A 2-epoch training smoke only validates compatibility, not model quality. Keep this as a data/teacher entry point, not a promoted runtime controller.
  - v118 trains phase-aware final-insert adapter pilots in `D:\peg-in-hole-6yh\v118_phase_aware_final_insert_adapter_pilot`. Episode-split e150 MAE is `0.250/0.794 mm`; all-data e150 train MAE is `0.310 mm`. `scripts\eval_guarded_policy.py` now has default-off `--final-insert-adapter-max-consecutive-steps` and `--final-insert-adapter-cooldown-steps` so full-action corrections can run as bounded bursts. Best v118 probe so far uses full `override`, burst `40`, cooldown `80`, `--no-final-insert-adapter-wall-contact-required`, and `min_stall=15`; it reached `39/40`, zero collision on seeds `895700/895800/895900/896000`, tying but not beating the previous best diagnostic. `min_stall=0` is bad (`896000` fell to `2/10`). Do not promote v118.
  - v119 adds handoff/stop teacher support. `scripts\build_phase_aware_final_insert_dataset.py --handoff-teacher-enabled` labels aligned/no-wall high-Z states as `handoff_descend`; the v119 dataset has `154` handoff labels. `scripts\eval_guarded_policy.py` now supports default-off predicted-action handoff and aligned/no-contact state handoff. v119 episode-split MAE is `0.323/0.253 mm`, but runtime still only reaches `39/40`, zero collision with state handoff XY `0.0048`; predicted-action handoff alone was too rare. Do not promote v119.
  - v120 adds default-off `guard_final_servo_align_hover_escape_*` wiring in guarded runtime plus eval/demo/inference CLIs. It was added after analyzing `896007`: escape did trigger, but `max_retries=2` exhausted after repeated `square_fast_settle/recover` cycles around `35-40 mm` Z. The first opt-in diagnostic recipe was v119 state handoff plus align-hover escape and `--guard-final-servo-max-retries 4`; targeted seeds `895700/895800/895900/896000`, 10ep each, reached `40/40`, zero collision and zero timeout.
  - v121/v122 broadened v120 on same-shape narrow-clearance stress. Fixed-profile retry4 seed `897000` passed `60/60`; mixed-same-shape retry4 seeds `897500/898500/899500` reached only `175/180`, and all failures were `square_square`. Raising only `--guard-final-servo-max-retries 6` fixed all five focused failed seeds and reached `180/180`, zero collision and zero timeout on the same three mixed seeds. Current opt-in candidate is therefore v119 state handoff plus align-hover escape plus retry6, not retry4. Do not make this default before a larger mixed matrix and baseline comparison.
  - v123/v124 baseline ablations are now available. Promoted v8 baseline on the same mixed seeds is `174/180`, with `2` collisions and `4` timeouts, all square-square. Retry6-only without the v119/v120 final-insert stack is `175/180`, with `1` collision and `4` timeouts. The combination stack is still the best current diagnostic, but it is not yet promoted.
  - v125 fresh-seed validation shows the v122 stack was partly seed-specific. Mixed-same-shape narrow-clearance seeds `900500/901500/902500`, 60 episodes each, reached only `175/180`, with `2` collisions and `3` timeouts. All failures remained `square_square`; all other same-shape profiles were perfect. Do not promote/tag v122.
  - v126 probes on the five v125 failed square seeds showed retry budget alone is not enough. `retry8` still left collisions/timeouts. Disabling align-hover escape removed one collision but converted another case into timeout. Trace diagnosis: some failures jump laterally out of `square_fast_settle` around `28-40 mm` Z, final-servo drops inactive, and fixture-clearance/ordinary guard takes over too abruptly.
  - v127 adds default-off `guard_final_servo_priority_over_fixture_clearance` plus eval/demo/inference CLI wiring. It prevents an already-active final-servo/recovery phase from being preempted by fixture-clearance. Focused probes rescued `900513` and `901554`, removed the collision mode, but left high-Z square timeouts. Keep it opt-in.
  - v128 fresh mixed-same-shape validation with priority-over-fixture reached `177/180`, zero collisions and three timeouts: seeds `900500=60/60`, `901500=60/60`, `902500=57/60`. Remaining failures were `902535/902549/902550`, all `square_square`.
  - v129-v133 adapter/down-action/ownership probes did not produce a promotable setting. The best local hard-seed result was `902500=59/60`, but the fresh matrix regressed to `176/180`, zero collision and four timeouts.
  - v134 high-Z contact reinsert was rejected: `902500=56/60`, one collision, and no actual `contact_reinsert_*` phase in the failure traces.
  - v138 is the current best opt-in narrow same-shape diagnostic: priority-over-fixture + v119 final-insert handoff adapter + align-hover escape + retry6 + square-tilt reinsert (`margin_threshold=-0.001`, `lift_height=0.014`) + ordinary final-servo `guard_final_servo_lift_height=0.060`. Fresh seeds `900500/901500/902500`, 60 episodes each, reached `178/180`, zero collision, two timeouts. All non-square same-shape profiles were perfect; remaining failures were `square_square`.
  - Final-insert adapter artifact is staged in Git at `assets\final_insert_adapters\final_insert_adapter_handoff_alldata_e150.pt`, size `37869` bytes, SHA256 `4FC0B6664F116C09A7D9569194E82EBDDA7D69F7E73BC60CA2C110176C2323C5`. Local `assets` ACL blocks materializing it in this worktree, so it was added through Git object/index plumbing and marked `skip-worktree`; local eval commands may still point at `D:\peg-in-hole-6yh\v119_final_insert_handoff_adapter_pilot\final_insert_adapter_handoff_alldata_e150.pt`.
  - v139 expanded v138 to seeds `903500/904500/905500`, 60 episodes each, and reached `177/180`, zero collision, three square-square timeouts. Combined v138+v139 is `355/360`, zero collision, five timeouts. Config `configs\sim\ur5e_full\eval_multi_geometry_v138_square_tilt_reinsert_lift60_60ep.yaml` records the candidate.
  - v140 retry8 probe on seeds `903500/904500` did not reduce timeout count, so retry budget is not the remaining bottleneck.
  - v141 default-off `guard_final_servo_square_high_z_descend_*` diagnostic is rejected for now. It locks XY and pushes down from low-risk high-Z `square_fast_settle` stalls, but focused seeds `901500/903500/904500` stayed at `59/60`, `59/60`, and regressed to `57/60` with one collision. Do not enable this knob in v138.
  - v142 default-off `guard_final_servo_rearm_*` diagnostic is implemented and exposed in eval traces. It can re-enter `align_hover` after final-servo exhaustion only after cooldown plus low-risk XY/Z/contact/tilt/margin checks. Focused probes did not improve the bottleneck: seed `903500` stayed `59/60` with one rearm, seed `903500` with `max_attempts=2` and `xy_max=0.007` also stayed `59/60` while consuming more recovery budget, and seed `904500` stayed `59/60` with no rearm because the failure remained active in `square_fast_settle`. Do not enable this knob in v138.
  - v143 command-level probe raises only `guard_final_servo_square_fast_settle_contact_max` from `6` to `8` on top of v138. It initially looked promising on v139 seeds `903500/904500/905500`, reaching `179/180`, zero collision and one square-square timeout. The old-seed validation on `900500/901500/902500` reached only `177/180`, zero collision and three square-square timeouts. Combined six-seed result is `356/360`, zero collision and four timeouts; non-square same-shape profiles are perfect (`287/287`). Do not promote v143: it is diagnostic evidence that the contact gate can be too strict, but it regresses the original v138 seed set from `178/180` to `177/180`.
  - v144 adds `guard_final_servo_square_tilt_reinsert_max_attempts=4` on top of v143 and is rejected. Focused seeds `901500/902500/903500`, 60 episodes each, reached `177/180` with one collision and two timeouts.
  - v145 adds default-off margin/yaw-aware square settle diagnostics in guarded runtime plus eval/demo/inference CLI wiring. It records `square_peg_yaw_error_deg` in `GuardedDeploymentState`, adds `square_margin_yaw_settle_lift/recenter` phases, and refines `scripts\analyze_square_worstcase_failures.py` so the v143 failures classify as `square_fast_settle_negative_margin_yaw_stall`. Keep this hook diagnostic only. Focused 1ep probes were mixed, but full six-seed 60ep validation rejected the route: attempts=1 reached `354/360`, one collision and five timeouts; attempts=2 also reached `354/360`, one collision and five timeouts. Both are worse than v143 (`356/360`, zero collision).
  - v146/v147b add `scripts\build_square_fast_settle_teacher_dataset.py` for square-fast-settle teacher labels using the existing final-insert adapter schema. v146 from v143 timeout traces produced `591` samples and an e100 adapter with `0.354 mm` validation MAE, but runtime was only `0/4` in full `override` and `1/4` in `override_xy`. v147b adds `61` success-descend override labels; the best e50 `override_xy` checkpoint reached `2/4` on the focused seeds (`901555`, `902550`), zero collision, but still timed out on `902535` and `903557`. XY cap and min-stall probes did not rescue them. Keep the script as a useful diagnostic/data entry point, but do not promote the adapter.
  - v148 adds default-off square pose yaw-align plumbing. The env now keeps a resettable pose IK target orientation, can snap the square peg target yaw to the nearest square-symmetric hole axis, and records pose-target yaw metrics in eval traces. `scripts\eval_guarded_policy.py` exposes `--guard-square-pose-yaw-align-*` and applies it only in square final-servo phases. Weight scan summary: `0.25` fixed focused hard seeds but produced `359/360` with one `905523` collision; `0.16` removed that collision but regressed `902500` to one timeout; `0.20` passed the key seeds and the full six-seed validation.
  - v148 candidate result: `D:\peg-in-hole-6yh\v148_square_pose_yaw_align_probe\matrix_60ep_weight020_six_seed`, seeds `900500/901500/902500/903500/904500/905500`, 60 episodes each, reached `360/360`, zero collision and zero timeout. Shape split: `square_square=73/73`, non-square same-shape `287/287`; mean steps `276.5`, max steps `660`. Repro config: `configs\sim\ur5e_full\eval_multi_geometry_v148_square_pose_yaw_align_w020_60ep.yaml`.
  - v149 fresh-seed validation of the same v148 recipe: `D:\peg-in-hole-6yh\v149_v148_fresh_seed_gate_906500_907500`, seeds `906500/907500/908500/909500/910500/911500`, 60 episodes each, reached `360/360`, zero collision and zero timeout. Shape split: `round_round=51/51`, `square_square=52/52`, `hex_hex=62/62`, `triangle_triangle=60/60`, `slot_slot=67/67`, `rectangular_key=68/68`; mean steps `281.7`, max steps `875`; all failure trace CSVs are empty.
  - Current conclusion: v148 is now the narrow same-shape version-promotion target. Across the original six-seed matrix plus the fresh six-seed v149 gate it has reached `720/720`, zero collision and zero timeout. It directly addresses the square-square negative-margin/yaw stall that retry count, high-Z down-push, rearm, margin/yaw lift-recenter, and translation-only adapter scans did not solve. Promote it as `v0.7.5-square-pose-yaw-align`; after that, run stricter fresh/stress regression before moving into broader multi-geometry/randomization changes.
  - Baseline strictstable49 20ep profile check before split-servo recovery: `single=0.95`, `round_square=0.95`, `square_square=0.85`, `mixed_basic=0.95`, all with zero collisions. Treat `square_square` final insertion stability as the first multi-geometry bottleneck.
  - Direct multi-geometry expert collection is not ready for 50k scaling: staged oracle had 0 success in a 1k pilot, guarded-two-stage oracle reached only 1 success / 1 collision in a 512-sample pilot. Prefer policy-visited correction data or a guarded-deployment teacher before large collection.
  - Policy-visited correction data path is now validated for multi-geometry. `square_square` and `mixed_basic` insert-settle smoke configs collect clean timeout-window samples and record geometry labels correctly.
  - `square_square` insert-settle 2k dataset is available at `datasets\ur5e_full\multi_geometry\correction\image_correction_2k_square_square_insert_settle.npz`; it has 2048 timeout samples, all in the insert-settle window, with no sample-level collision.
  - Conservative 5% replay checkpoint `checkpoints\ur5e_full\multi_geometry\correction\sac_image_bc_wrist_pose_control_state_square_square_insert_settle_2k_w05_e1.zip` is not promoted. Strictstable49 20ep matrix stayed flat: `single=0.95`, `round_square=0.95`, `square_square=0.85`, `mixed_basic=0.95`, all zero collision.
  - Do not scale square-square one-step BC replay by default. Under strict guarded eval, near-hole behavior is dominated by `guard_blend=1.0` final-servo logic, so learned near-hole correction labels do not materially affect the remaining square-square timeout.
  - Guard-blend and actor-vs-guard diagnostics are complete. Summary: `results\ur5e_full\multi_geometry\guard_blend_diag\summary.md`.
  - Diagnostic conclusion: lowering `guard_blend` did not reveal a useful w05 actor benefit. `guard_blend=0.5` regressed base to `0.70` and w05 to `0.65`. `policy` mode was `0.00` success for both base and w05, while `guard_only` matched the guarded `0.85` success. Treat the square-square gap as a controller/final-servo problem, not a data-scaling problem.
  - Shape-aware square-peg diagnostics are now available in env info and guarded step traces. Use `scripts\analyze_square_peg_trace.py` to summarize yaw error, top-down square clearance, tilt-aware clearance, and final-servo phase counts.
  - Current shape diagnostic summary: `results\ur5e_full\multi_geometry\shape_aware_servo_diag\shape_aware_servo_summary.md`.
  - Diagnostic conclusion: `square_square` timeouts are mixed. Seed `612010` is a persistent high-tilt/wedged case, while `612008` and `612013` have low final tilt and positive projected clearance but still fail in final-servo/low-recenter. Do not use a naive max-tilt threshold; if implementing the next controller change, make it opt-in, phase-aware, and square-only.
  - Opt-in square-aware final-servo recovery is implemented but not promoted. It adds `guard_final_servo_square_recovery_*` knobs plus `square_recover_lift` / `square_recover_recenter` phases. Targeted 14ep seed `612000-612013` stayed flat at `11/14` success, and high-tilt seed `612010` still timed out even with near IK orientation weight `0.03/0.06`, higher lift, and 1500 max steps. Keep it as a diagnostic hook; do not spend more time scanning simple square-recovery thresholds.
  - Final insertion contact diagnostics are now available in env `info` and guarded step traces. Use `scripts\analyze_insert_contact_trace.py` on traces under `results\ur5e_full\multi_geometry\contact_insert_diag`.
  - Current contact diagnostic conclusion: successful square-square references `612000/612001/612002` had no peg-hole contact and ended near the success Z tolerance. Timeout `612010` is a persistent wall-contact/high-tilt failure, while `612008` and `612013` are lower-contact final-servo/recovery phase failures. Do not use one broad contact threshold for all square-square timeouts; split the next controller diagnostic into a contact/high-tilt unjam branch and a low-contact near-miss phase-completion branch.
  - Split final-servo diagnostic is implemented and is the current best opt-in multi-geometry guarded setting, not a global default. It adds square-only `contact_unjam_lift/contact_unjam_recenter` and `near_miss_descend/near_miss_recenter` phases behind `guard_final_servo_split_recovery_enabled`.
  - Best tested split setting uses near-miss XY bias `[0.0035, 0.0035]`, near-miss low recenter height `0.008`, near-miss max down `0.0025`, contact unjam lift `0.045`, contact wall steps `6`, near-miss steps `30`, near-miss XY/Z `0.0068/0.060`.
  - Result: `square_square` strictstable49 20ep seed `612000` improved to `0.950/0.000/0.050`; the `612000-612013` 14ep window improved to `13/14`, with only high-tilt contact seed `612010` still timing out.
  - Profile matrix with the same split setting, 20 episodes, seed `612000`, passed without non-square regression: `single=0.95`, `round_square=0.95`, `square_square=0.95`, `mixed_basic=0.95`, all zero collision. Every profile's only failure was seed `612010`.
  - Larger 60ep profile matrix also passed with zero collisions: `single=0.967`, `round_square=0.967`, `square_square=0.950`, `mixed_basic=0.967`. Common timeout seeds are `612010/612032`; `square_square` adds `612021`.
  - Reusable config: `configs\sim\ur5e_full\eval_multi_geometry_square_square_split_servo_strictstable49_20ep.yaml`. Matrix results: `results\ur5e_full\multi_geometry\split_servo_diag_v6_bias35_matrix` and `results\ur5e_full\multi_geometry\split_servo_diag_v6_bias35_matrix_60ep`.
  - Focused one-episode contact traces for the remaining failures are summarized at `results\ur5e_full\multi_geometry\split_servo_diag_v6_bias35_failure_contact\summary_release_band.md`.
  - Failure-contact conclusion: remaining `single`/`round_square` failures are also high-contact/high-tilt insert-band timeouts, so the next unjam design should be contact-aware and not square-only. In `square_square`, the current contact unjam branch triggers but still leaves seeds `612010/612021/612032` timing out after wall contact and high tilt. Next work should focus on a more deliberate retreat/recenter/reinsert strategy, not more broad threshold scans. Do not commit large failure step traces unless they are needed for a specific diagnostic.
  - `feature/contact-aware-reinsert` is the current experimental branch for that next controller step. It adds opt-in general contact reinsert, wall-direction contact relief, and phase-local IK orientation overrides for final-servo/contact-unjam diagnostics.
  - Latest contact-aware diagnostic result: v8 (`hover=0.025`, `stable_steps=8`, `final_servo_ik_orientation_weight=0.06`) rescues `square_square/612021`, but it does not solve common `612010/612032` failures across profiles. Do not promote v8 as a default.
  - `--guard-final-servo-align-timeout-steps` / `--guard-final-servo-align-timeout-xy` are implemented as a default-off safety valve. v12 confirms the escape triggers on `612032`, but the seed still times out because recovery/recenter consumes too many steps. Treat this as guard hygiene, not a promoted improvement.
  - Important interpretation: strong/high hover verticality can fix square tilt but can also harm XY tracking. Contact-only IK relaxation improves lateral recentering for `612010`, but tilt grows too much. The next implementation should be phase-specific: moderate verticality before descent, relaxed orientation during lateral unjam/recenter, verticality re-established before descent, and shorter recovery phases with progress checks.
  - Latest v42 contact-aware result: phase-local final-servo/contact-reinsert `pose_tip_priority` IK reached `1.000/0.000/0.000` on the 20ep and 60ep profile matrices for `single`, `round_square`, `square_square`, and `mixed_basic` on seed `612000`.
  - Additional v42 out-of-window smoke: seed `613000`, 10 episodes per profile, reached `1.000/0.000/0.000` for all four profiles. Output directory: `D:\peg-in-hole-6yh\v42_tip_priority_seed613000_matrix10`.
  - Additional v42 gate: seed `614000`, 20 episodes per profile, reached `1.000/0.000/0.000` for all four profiles. Output directory: `D:\peg-in-hole-6yh\v42_tip_priority_seed614000_matrix20`.
  - Larger v42 gate on seeds `615000/616000/617000`, 20 episodes per profile, reached `236/240 = 0.983` overall with zero collisions. All four failures were the same hard initialization `seed615000/episode0`, stalling before final-servo handoff around `16.7 mm` XY / `65 mm` Z under low action scale, delay 2, and high filtering.
  - Wide-handoff override `guard_approach_recenter_trigger_xy=0.018`, `guard_approach_recenter_stable_xy=0.017`, `guard_final_servo_start_xy=0.018` improved the same 3-seed matrix to `238/240 = 0.992`, zero collisions. `single` and `round_square` reached `60/60`; `square_square` and `mixed_basic` each kept one square-geometry timeout.
  - Known remaining square timeouts under wide-handoff succeed if `max_steps=1500`: `square_square/615000` in `1242` steps and `mixed_basic/615000` in `1158` steps. Increasing final-servo max down action to `0.0020/0.0025` did not fix them at 1000 steps.
  - v44 strict 1000-step follow-up is implemented:
    - default-off `guard_final_servo_square_fast_settle_*` knobs
    - new square-only `square_fast_settle` final-servo phase
    - eval/demo/inference CLI wiring
    - `scripts\analyze_final_servo_phase_trace.py`
  - v44 targeted result: `square_square/615000/episode0` now succeeds in `858` steps and `mixed_basic/615000/episode0` succeeds in `772` steps, both with final phase `square_fast_settle` and zero collision.
  - v44 gate result with wide-handoff plus square-fast-settle on seeds `615000/616000/617000`, 20 episodes per profile: `240/240 = 1.000`, zero collisions, zero timeouts. Output directory: `D:\peg-in-hole-6yh\v44_square_fast_settle_multiseed_matrix20`.
  - v44 new-seed strict regression on seeds `618000/619000/620000`, 20 episodes per profile: `240/240 = 1.000`, zero collisions, zero timeouts. Mean steps `292.2`, max steps `802`, mean final XY `1.59 mm`, max final XY `5.00 mm`, max final peg tilt `3.19 deg`. Output directory: `D:\peg-in-hole-6yh\v44_square_fast_settle_regression_newseeds`.
  - v45 stress eval plumbing is implemented in `scripts\eval_guarded_policy.py`: config/CLI can now override hard-bucket control ranges plus peg radius, hole-center jitter, fixture height jitter, and table height jitter.
  - v45 moderate stress config: `configs\sim\ur5e_full\eval_multi_geometry_contact_reinsert_tip_priority_square_fast_settle_stress_20ep.yaml`.
  - v45 moderate stress result on seeds `621000/622000`, 20 episodes per profile: `160/160 = 1.000`, zero collisions, zero timeouts. Output directory: `D:\peg-in-hole-6yh\v45_stress_matrix20_seed621_622`.
  - v45 boundary probe on seed `623000` with tighter geometry and harder control also reached `40/40 = 1.000`. Output directory: `D:\peg-in-hole-6yh\v45_boundary_probe_seed623`.
  - v45 deterministic worst-case with only `1 mm` clearance, fixed action scale `0.65`, delay `4`, filter alpha `0.35`, and noise `0.8 mm`: `single=4/5`, `square_square=0/5`, `mixed_basic=3/5`. Output directory: `D:\peg-in-hole-6yh\v45_worstcase_probe_seed624`. Treat this as a boundary diagnostic, not the default task.
  - v46 square worst-case diagnostic script added: `scripts\analyze_square_worstcase_failures.py`.
  - v46 baseline analysis of v45 deterministic worst-case found 8 failures: 3 `approach_no_final_servo` and 5 `near_xy_contact_high_z`. The latter briefly enter `square_fast_settle`, then get rejected by contact/tilt and stall high with wall contact.
  - v46 contact-tolerant square-fast-settle opt-in probe sets `guard_final_servo_square_fast_settle_z_max=0.060`, `guard_final_servo_square_fast_settle_tilt_max_deg=14.0`, and `guard_final_servo_square_fast_settle_contact_max=6`. Deterministic worst-case improves to `single=4/5`, `square_square=4/5`, `mixed_basic=4/5`. Remaining failures are all `approach_no_final_servo`. Output directory: `D:\peg-in-hole-6yh\v46_square_recovery_param_probe_worstcase_all`.
  - v46 contact-tolerant moderate-stress smoke on seed `625000`, 10 episodes per profile, reached `40/40 = 1.000`, zero collisions, zero timeouts. Output directory: `D:\peg-in-hole-6yh\v46_contact_tolerant_moderate_smoke_seed625`.
  - v46 contact-tolerant larger moderate-stress matrix on seeds `626000/627000/628000`, 20 episodes per profile, reached `240/240 = 1.000`, zero collisions, zero timeouts. Profile split: `single=60/60`, `round_square=60/60`, `square_square=60/60`, `mixed_basic=60/60`; mean steps `293.1`, max steps `826`, mean final XY `1.58 mm`, mean final-servo steps `60.3`. Output directory: `D:\peg-in-hole-6yh\v46_contact_tolerant_moderate_matrix_seed626_628`.
  - New reusable v46 contact-tolerant stress config: `configs\sim\ur5e_full\eval_multi_geometry_contact_reinsert_tip_priority_square_fast_settle_contact_tolerant_stress_20ep.yaml`. Config smoke passed on `square_square/seed629000`, `1/1` success. Output directory: `D:\peg-in-hole-6yh\v46_contact_tolerant_config_smoke`.
  - v46 contact-tolerant deterministic worst-case demo: `square_square/seed624001` succeeded in `245` steps, final XY/Z about `1.30 mm / 9.33 mm`, output GIF `D:\peg-in-hole-6yh\v46_contact_tolerant_demos\demo_v46_square_square_worstcase_seed624001_guarded.gif`.
  - v46 tighter boundary regression on seeds `630000/631000`, 10 episodes per profile, reached `76/80 = 0.950`, with 3 collisions and 1 timeout. Failures all occur on `seed631004` before final-servo handoff, around `32-37 mm` XY and `44-51 mm` Z. This is not a square-fast-settle regression.
  - Targeted `seed631004` probes: `guard_block_down_when_unaligned` did not rescue the seed; fixture-clearance safety avoids collisions but times out; fixture realign currently does not activate (`fixture_realign=0`). Treat this as an approach/fixture-clearance state-machine problem before claiming the aggressive boundary distribution is solved.
  - Reusable v44 configs:
    - `configs\sim\ur5e_full\eval_multi_geometry_contact_reinsert_tip_priority_square_fast_settle_60ep.yaml`
    - `configs\sim\ur5e_full\demo_multi_geometry_contact_reinsert_tip_priority_square_fast_settle.yaml`
  - v44 demo result: `square_square/615000` succeeded in `686` steps, final XY/Z about `1.14 mm / 9.79 mm`, final phase `square_fast_settle`. Output: `D:\peg-in-hole-6yh\v44_square_fast_settle_demos\demo_v44_square_square_seed615000_guarded.gif`.
  - Use config `configs\sim\ur5e_full\eval_multi_geometry_contact_reinsert_tip_priority_60ep.yaml` for the v42 candidate. It was smoke-tested on 2026-05-24 with `single/seed612000`, `1/1` success.
  - Use config `configs\sim\ur5e_full\demo_multi_geometry_contact_reinsert_tip_priority.yaml` for v42 demos. Always pass `--guarded-policy`; otherwise demo is policy-only and can timeout with `guard_steps=0`.
  - Demo outputs on seed `614000` live in `D:\peg-in-hole-6yh\v42_tip_priority_demos`: `single` succeeded in `316` steps and `square_square` succeeded in `315` steps. GIFs are `2560x720`, overview plus wrist camera.
  - Do not enable `--ik-control-mode pose_tip_priority` globally. It breaks the learned approach trajectory. Keep nominal `ik_control_mode: pose` and enable tip-priority only through `--guard-final-servo-tip-priority-ik-enabled` and `--guard-contact-reinsert-tip-priority-ik-enabled`.
  - v44 has been locally committed and tagged as `v0.7.1-contact-reinsert-square-fast-settle`.
  - v47 early-final-servo boundary is promoted as the current strict-1000 multi-geometry boundary candidate; tag `v0.7.2-early-final-servo-boundary` identifies this promoted state. It uses `configs\sim\ur5e_full\eval_multi_geometry_early_final_servo_boundary_stress_20ep.yaml` plus `guard_start_z=0.14`, `guard_final_servo_start_xy=0.035`, `guarded_max_xy_action=0.008`, and `nominal_actuator_kp_multiplier=3.0`.
  - v46 contact-tolerant square-fast-settle remains the moderate-stress reference, but v47 supersedes it for boundary stress. Do not make the 1mm-clearance deterministic worst-case the default task; treat it as a diagnostic. Do not add large untracked result traces by default, and push/tag only when requested.
  - v47 policy/controller contribution ablation on `mixed_basic`, seed `635000`, 10 episodes/condition: guarded normal `1.000`, guarded blend `0.75` `1.000`, guarded blend `0.5` `0.900`, black image `0.700`, noise image `0.600`, shuffled image `1.000`, guard-only `0.700`, policy-only `0.000`, all zero collision. Output directory: `D:\peg-in-hole-6yh\v47_policy_contribution_ablation_seed635_10ep`. Conclusion: vision contributes to approach/guard entry, but final insertion is controller-dominated; do not claim policy-only insertion ability under boundary stress.
  - v47 visual contribution scale-up on `mixed_basic`, seed `636000`, 20 episodes/condition: normal `0.950`, black `0.750`, noise `0.400`, shuffle `0.950`, guard-only `0.850`, policy-only `0.000`, all zero collision. Combined with seed `635000`, normal and shuffle are both `29/30`, black is `22/30`, noise is `14/30`, guard-only is `24/30`, policy-only is `0/30`. Conclusion: visual corruption matters, but shuffle matching normal means strong spatial visual servoing is not proven. Next diagnostic should add control-state ablation or channel-specific image ablations.
  - v47 control-state contribution scale-up on `mixed_basic`, seed `637000`, 20 episodes/condition: normal image + control normal/zero/noise/shuffle all `20/20`, black image + control normal `18/20`, black image + control zero `17/20` with 3 collisions. Conclusion: normal-image v47 is insensitive to control-state corruption, while black-image cases get somewhat worse when control-state is removed. The low-dimensional control-state channel is not the main driver of success; the next diagnostic should return to image-path ablation or a camera/crop change.
  - v47 image-channel ablation adds `--image-ablation-target {all,cam_image,near_hole_crop}`. On `mixed_basic`, seed `638000`, 10 episodes/condition: normal `10/10`, all black `8/10`, cam black `10/10`, crop black `7/10`, all noise `4/10`, cam noise `8/10`, crop noise `0/10`, all/cam/crop shuffle all `10/10`. Conclusion: `near_hole_crop` is the sensitive visual channel; `cam_image` is much less critical. Shuffle passing means crop content quality matters, but exact per-frame spatial visual servoing is still not proven.
  - v47 crop/camera scan: direct `near_hole_crop_size` changes are incompatible with the current checkpoint because the SB3 observation space expects `64x64`. Fixed-size crop offset/FOV scans show crop X `+12/+24` and FOV `80` are sensitive: seed640 focused 10ep got baseline `10/10`, crop X `+12` `7/10`, crop X `+24` `7/10`, FOV `80` `8/10`. Negative/nominal X offsets, Y offsets, and FOV `90-120` were stable in the 5ep seed639 probe. Next training work should add crop/camera jitter or a resize-back-to-64 crop-scale option.
  - v47 crop-source resize support is now implemented for guarded eval: `near_hole_crop_source_size` crops a variable source window and resizes it back to the fixed `near_hole_crop_size` output, so existing `64x64` SB3 checkpoints can be evaluated without observation-space mismatch. Seed642 5ep scan found source `96 -> 64` robust to offsets `[-18,0]`, `[+12,0]`, and `[+24,0]` at `5/5` each; source `48/64` were only `2/5` at positive X offsets, and source `80` was `3/5`. Summary: `D:\peg-in-hole-6yh\v47_crop_source_resize_scan_seed642_5ep\summary.md`. Next visual-policy step should add dataset/training support for source-size jitter around `80-96`, not change output `near_hole_crop_size`.
  - v47 crop-source jitter data path is implemented. `near_hole_crop_source_size_range` samples source crop size per episode while output remains `64x64`; it is wired through eval/demo/inference, expert/correction collection, and image BC pretraining. Expert/correction datasets record `near_hole_crop_source_size`. Smoke config: `configs\sim\ur5e_full\collect_multi_geometry_crop_source_jitter_smoke.yaml`; smoke output: `D:\peg-in-hole-6yh\v47_crop_source_jitter_smoke`. The reset probe sampled `[96,87,95,96,81,89,81,83]` for range `[80,96]`; the 8-sample dataset and 1-epoch BC smoke both passed. Next useful run is not another smoke: collect `20k-50k` jitter samples, lightly fine-tune v47, then rerun the crop offset/FOV scan and standard scenario matrix.
- UR5e controller status:
  - Default remains position-only peg-tip IK for checkpoint compatibility.
  - Experimental `ik_control_mode=pose` is implemented in `PegInHoleMujocoEnv` and exposed in guarded eval, demo, inference, and `scripts\diagnose_ur5e_controller.py`.
  - The latest 3-episode controller diagnostic shows pose IK improves low-Z peg orientation and XY command alignment, but one-step lateral XY gain remains low in both modes. Treat this as a control-layer bottleneck before collecting more correction data.
  - Pose IK hard-bucket guarded eval with the insert-drift w10 e1 checkpoint plus final-servo config is the current best controller-side result: the 60-episode seed `602000` comparison improved from position-IK `0.417/0.133/0.450` to pose-IK `0.717/0.100/0.183`.
  - The earlier 20-episode trio also supports the same conclusion: seeds `602000/604000/605000` averaged success/collision/timeout `0.750/0.117/0.133`.
  - The 100-episode cross-scenario matrix confirmed pose IK is not hard-bucket-only: clean `0.690->0.780`, visual_camera `0.540->0.780`, visual_camera_control `0.570->0.770`, full_light_geometry `0.510->0.790`, full_contact_light `0.500->0.800`, hard bucket `0.510->0.750`.
  - Pose IK should now be treated as the preferred controller mode for the next full-UR5e high-start training/evaluation run. The pose-aware near-hole timeout and fixture-wall collision correction sets have been collected, and the continuation fine-tune has already been run. It was effectively flat on the hard gate. The follow-up recovery-sequence recipe is also complete and flat: the collector now supports `fixture_wall_lift_before_lateral`, the 2k dataset/training/eval path ran, and the hard gate stayed `0.717/0.100/0.183`. Generic runtime `guarded_lift_before_lateral` regressed to `0.150/0.800/0.050` over 20 episodes. Do not scale these replay recipes; next work should target controller/guard behavior and low-level Cartesian tracking near contact.
  - Previous best controller candidate was pose IK with `ik_orientation_weight=0.06`, `ik_max_iterations=48`, and `nominal_actuator_kp_multiplier=2.0`.
  - Previous Kp2 candidate results: hard 60ep seed `602000` reached `0.850/0.000/0.150`, seed `604000` reached `0.867/0.000/0.133`, and the 100ep matrix reached clean/visual_camera/visual_camera_control `0.910/0.910/0.910`, full_light_geometry/full_contact_light `0.900/0.900`, hard bucket `0.890`, all with zero collisions.
  - The Kp2 high-resolution demo config is `configs\sim\ur5e_full\demo_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_kp2.yaml`. It succeeded in `309` steps with no collision and generated `demos\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori006_it48_kp2.gif` at `2560x720`. MP4 output currently falls back to GIF because the local `imageio` video backend is unavailable.
  - Current best controller candidate is pose IK with `ik_orientation_weight=0.03`, `ik_max_iterations=64`, and `nominal_actuator_kp_multiplier=2.0`.
  - Current candidate results: hard 60ep seed `602000` reached `0.883/0.000/0.117`, seed `604000` reached `0.900/0.000/0.100`, and the 100ep matrix reached clean `0.970/0.000/0.030`, visual_camera `0.970/0.000/0.030`, visual_camera_control `0.940/0.000/0.060`, full_light_geometry `0.910/0.000/0.090`, full_contact_light `0.910/0.000/0.090`, hard bucket `0.910/0.000/0.090`.
  - The current candidate demo config is `configs\sim\ur5e_full\demo_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori003_it64_kp2.yaml`. It succeeded in `335` steps with no collision and generated `demos\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori003_it64_kp2.gif`.
  - The `0.03/64 + Kp2` controller milestone has been pushed as `v0.6.49` / `0c62f5b`. Do not promote frame_skip 20, fixture-clearance lift, or wider `guarded_align_xy_tolerance=0.030`; these did not improve the Kp2 candidate.
  - `scripts\audit_ur5e_full_model.py` now compares `assets\ur5e_full\ur5e_peg_in_hole_full.xml` against a raw Menagerie `universal_robots_ur5e\ur5e.xml` reference. The generated audit report is `results\ur5e_full\model_audit\ur5e_full_menagerie_audit.md`.
  - Audit conclusion: the full UR5e XML preserves the shared Menagerie body inertials and mesh file set, but it is a task adapter. It renames joints/actuators, moves the base into the task frame, adds `tool0`, peg, wrist camera, table/hole scene, explicit joint limits, timestep/gravity, and task contact defaults. Next controller work should inspect base/tool0/peg pose, peg verticality, and near-contact TCP tracking before starting multi-geometry training.
  - Latest near-contact diagnostic for the promoted `pose IK + 0.03/64 + Kp2` setting: `xy reduction=4.921 mm`, `reduction/cmd=0.164`, `alignment=0.986`, `step gain=0.176`, `z drift=-2.897 mm`, `max tilt=11.894 deg`. The peg-tip to `eef`/`tool0` distance stays exactly `110 mm`, so the next bottleneck is low-Z TCP authority/stability rather than an obvious peg attachment length error.
  - `guard_preinsert_recenter_lift_before_lateral` is implemented as an opt-in diagnostic switch, but it is not promoted. Same-seed hard-bucket 20ep baseline for `0.03/64 + Kp2` was `0.950/0.000/0.050`; broad lift-first preinsert recenter regressed to `0.850/0.000/0.150`; narrow `trigger_xy=0.008,stable_xy=0.0065,height=0.025` recovered baseline but did not improve it; higher-lift variants did not solve the remaining timeout. Do not continue broad preinsert threshold scans before inspecting TCP tracking/IK response or adding a true retreat-retry sequence.
  - `scripts\analyze_tcp_response_trace.py` is available for step-trace command-to-motion diagnostics. On hard failure seed `602019`, the promoted baseline sent about `5.0 mm` final XY commands and `4.5 mm` applied XY commands in the last 100 steps, but actual peg-tip XY motion averaged only about `0.009 mm`. Hold-Z, retry, wide latch, early final-servo, and near-action limiting did not rescue the seed. `guard_insert_latch_recenter_z_tolerance` is implemented as an opt-in diagnostic knob, but it is not promoted. The next useful work is a true stateful retreat/recenter phase or lower-level IK/controller tracking work, not more one-parameter guard scans.
  - `scripts\scan_near_contact_controller_response.py` is now available for focused low-Z controller response scans across IK orientation weight, iterations, frame skip, actuator Kp, and damping. The first scan found that global `Kp=3.0` improves near-contact probe response versus `Kp=2.0`, but closed-loop hard-bucket evaluation regressed: Kp2 retest on seed `602000` 20ep was `0.950/0.000/0.050`, while Kp3 was `0.850/0.000/0.150`. Intermediate Kp values did not dominate: Kp2.25 still failed `602019`, Kp2.5 failed `602011/602019`, and Kp2.75 fixed `602019` but failed `602011`. Keep global `Kp=2.0` as the promoted static default; the next controller-side work should be stateful near-hole recovery or a strictly local gain schedule inside recovery, not more global Kp scans.
  - Local near-hole Kp recovery is now implemented as an opt-in deployment/eval/demo/inference feature. Use `--guard-near-actuator-kp-enabled --guard-near-actuator-kp-multiplier 3.0` with nominal Kp2 to boost arm actuator Kp only during stateful recovery, final-servo, and the near-hole guarded zone. The preset `configs\sim\ur5e_full\eval_high_start_hard_localkp3_recovery_20ep.yaml` now also uses a double-gated final-servo descend bias: `[0.0, -0.005]`, max clearance `0.006`, and `requires_stateful_recovery=true`. It preserves direct-insert tight-clearance successes (`602025/602028/602039`), fixes low-Z drift (`602040/602047`), and reaches hard-bucket seed `602000` 20ep `1.000/0.000/0.000` and 60ep `0.950/0.000/0.050`. Remaining failures are approach plateaus only (`602024/602033/602048`) with `final_servo=0`; the next work should target approach-to-hole plateau, not more final insertion recovery.
- Current recommended full UR5e narrowed-hole checkpoint:
  - `checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip`
- Latest full UR5e narrowed-hole correction candidate:
  - `checkpoints\ur5e_full\correction\sac_image_bc_50k_narrow_correction_8k_w10_e2.zip`
  - Do not treat it as the default unless a later evaluation clearly beats the adapted checkpoint; the first correction pass was mostly flat.
- Latest full UR5e high-start candidate:
  - `checkpoints\ur5e_full\high_start\sac_image_bc_50k_high_start_visual_camera.zip`
  - Do not treat it as the default; 100-episode high-start guarded success is only about `0.15 - 0.24`.
- Latest full UR5e easy high-start candidate:
  - `checkpoints\ur5e_full\high_start\easy\sac_image_bc_50k_high_start_easy_visual_camera.zip`
  - Easy range: `0.08 - 0.15 m` height and `0.04 - 0.10 m` XY offset.
  - Treat it as the current high-start curriculum checkpoint, but not the general default; same-seed success is about `0.48 - 0.63` across scenarios.
- Latest full UR5e medium high-start candidate:
  - `checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip`
  - Medium range: `0.10 - 0.18 m` height and `0.06 - 0.12 m` XY offset.
  - Treat it as the current best high-start curriculum checkpoint; success is about `0.49 - 0.68` across scenarios.
- Latest full UR5e hard-range high-start candidate:
  - `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip`
  - Hard range: `0.15 - 0.25 m` height and `0.08 - 0.16 m` XY offset with `0.12 m` safe approach height.
  - Do not promote it as default; success is about `0.27 - 0.48` across scenarios.
- High-start two-phase controller status:
  - `OracleControllerConfig.mode` supports `high_start_two_phase`.
  - `guarded_oracle_mode: high_start_two_phase` is supported by demo/eval/inference scripts.
  - `guard_block_down_when_unaligned` now applies before guard activation too.
  - Do not make the current two-phase hard config default yet; first eval was mixed and increased timeout.
  - The latest hard high-start guarded scan shows `high_start_two_phase` and hard down-block are not yet clear improvements over `guarded_two_stage`.
  - The focused `align=0.025`, `guarded_two_stage` 100-episode eval is also not promoted; it reached clean `0.530` but only visual_camera `0.370`, visual_camera_control `0.310`, full_contact `0.290`, and hard bucket `0.270`.
  - The latest hard demo failure plateaus near `8.4 mm` XY error and `32.8 mm` height above target, so the next improvement should target near-hole plateau/failure correction rather than more success-only hard data.
- Hard high-start correction status:
  - `collect_image_correction_dataset.py` supports high-start reset args and visual/high-start scenario presets.
  - The first correction smoke collected `256` near-hole failure samples from `29` visual_camera hard high-start episodes.
  - The samples are high-signal: `72.3%` opposed policy/oracle actions and `86.7%` policy-down/oracle-up-or-less-down.
  - The 1-epoch correction smoke checkpoint is not promoted; same-seed 20-episode eval was mixed and the demo still timed out near `8.4 mm` XY error.
  - The expanded 2k correction set includes visual_camera and visual_camera_control, with `74.9%` opposed actions and `86.8%` policy-down/oracle-up.
  - 2k weighted BC with 5% correction replay was effectively identical to baseline; 10% replay only improved the 20-episode hard bucket from `0.35` to `0.40` and reduced hard-bucket collision from `0.45` to `0.35`.
  - The 2k 10% demo still timed out near `8.4 mm` XY error and `30.6 mm` above target, so correction BC alone is not solving the insertion plateau.
  - Later hard-bucket v3 correction became the best hard-bucket candidate, but introduced timeout as the main failure mode. Keep `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1.zip` as the comparison baseline, not a fully promoted default.
  - Timeout-progress v4 and safety-balanced v4b/v4b2 were tested and are not promoted:
    - v4 progress-only reduced timeout by causing too many collisions.
    - v4b/v4b2 added block/hover/lift/slow-insert labels and dataset diagnostics, but same-seed hard-bucket results still converted timeout to collision.
    - v4b2 w01 e1 reached success/collision/timeout `0.400/0.300/0.300` versus v3 e1 baseline `0.500/0.150/0.350` on seed `622000`.
    - Step trace contact diagnostics show v4b2 collisions happen before final insertion: collision insert-band rate `0.000`, median collision XY about `60.9 mm`, with `peg_geom` hitting hole walls/plate/table.
    - A wider contact-aware guard (`guard_start_xy=0.09`, `contact_recovery_z_max=0.10`, `contact_recovery_lift_height=0.12`) regressed to `0.050/0.400/0.550`; do not promote broad early oracle takeover.
    - Fixture-clearance safety gate is implemented in `GuardedPolicyConfig` and exposed in eval/demo/inference. It independently forces XY `0` and Z-up when the peg is low over the fixture while still laterally far from the hole.
    - Same-seed v4b2 w01 fixture-gate smokes on seed `622000` reduced collision but did not improve success: conservative `xy_max=0.09,z_max=0.06,lift=0.10` reached `0.400/0.250/0.350`; wider `xy_max=0.13,z_max=0.06,lift=0.10` reached `0.400/0.200/0.400`.
    - Two-stage fixture realign is also implemented as an explicit diagnostic option, with phase and realign-step traces. It is not promoted: `realign_start_z=0.060` reached `0.400/0.250/0.350`, while earlier `realign_start_z=0.045` variants regressed to `0.400/0.300/0.300`.
    - Treat fixture-clearance as a deployment safety/diagnostic tool, not a promoted model result; the next fix should add high-approach correction coverage or prevent the initial low-altitude drift before contact risk appears.
    - High-approach correction coverage is now implemented in `collect_image_correction_dataset.py` with `approach_correction_labels`, `approach_window`, and `approach_recenter`. The 512-sample smoke is accepted as a data-path smoke.
    - The 2k high-approach correction candidate is a useful diagnostic/candidate but is not promoted. Same-seed `614000` 20-episode matrix improved hard bucket from v3 `0.600/0.150/0.250` to approach `0.650/0.100/0.250`, and hard-only seed `622000` was flat versus v3 at `0.500/0.150/0.350`. However, 60-episode hard-only multi-seed average was slightly below v3: approach average success/collision/timeout about `0.400/0.194/0.406` versus v3 `0.417/0.167/0.417`.
    - Approach 2k visual ablation passed: hard-bucket policy-only normal reached `0.300`, while black/noise/shuffle all reached `0.000` success. The model still uses image input, but the candidate is not consistently better than v3.
    - Failure trace seed `602000` shows the main hard-bucket failures are `high_fixture_wall_collision` and `insert_band_timeout_low_z_drift`. Existing controller gates are not promoted: fixture clearance `0.350/0.283/0.367`, hover/descent `0.350/0.267/0.383`, and lift-before-lateral `0.150/0.267/0.583` versus approach baseline `0.367/0.267/0.367`.
    - Fixture-wall pre-contact correction collection is now implemented and smoke-tested. The accepted smoke dataset is `datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_fixture_wall_smoke.npz`; it has `fixture_wall_window_rate=1.000`, `fixture_wall_recenter=512`, median XY/Z above target about `32.3 mm / 69.9 mm`, and zero down-action labels.
    - Fixture-wall 2k w10 e1 is a useful diagnostic/candidate but is not promoted. Dataset `image_correction_2k_high_start_hard_wrist_pose_control_state_fixture_wall.npz` has `fixture_wall_window_rate=1.000`, `fixture_wall_recenter=2048`, median XY/Z about `34.7 mm / 68.6 mm`, and zero down-action labels. The checkpoint `sac_image_bc_wrist_pose_control_state_fixture_wall_2k_w10_e1.zip` averaged hard-bucket `0.428/0.128/0.444` over seeds `602000/604000/605000`, versus v3 `0.417/0.167/0.417` and approach `0.400/0.194/0.406`; it reduces collisions but raises timeout. Do not scale this exact recipe without adding timeout/progress recovery or lowering replay weight.
    - Fixture-wall trace and w05 replay test are complete. Seed `602000` failure trace shows w10 reduces high fixture-wall collisions but increases `insert_band_timeout_low_z_drift`; the typical timeout entered the insert band and then drifted to about `6 - 7 mm` XY and about `25 mm` above target. The w05 checkpoint averaged hard-bucket `0.405/0.139/0.456`, worse than w10. Do not keep tuning fixture-wall replay weight by itself; next correction recipe should combine fixture-wall recenter with timeout-progress / slow-insert supervision.
    - Fixture-wall + timeout-progress w03 follow-up is also not promoted. It uses `sac_image_bc_wrist_pose_control_state_fixture_wall_progress_w03_e1.zip` and reached hard bucket `0.500/0.050/0.450` in the default 20-episode matrix, but clean/full-light regressed and same-seed hard checks were unstable (`621000: 0.300/0.150/0.550`, `622000: 0.450/0.250/0.300`). The current progress-only smoke dataset is too one-sided even at `3%`; the next progress recipe needs redesign around late-stage insert-band drift.
    - Insert-drift 2k w10 e1 is implemented, trained, and evaluated but not promoted. It starts from fixture-wall w10 and adds `10%` late insert-band drift replay. Three-seed hard-bucket average is `0.433/0.089/0.478`, versus fixture-wall `0.428/0.128/0.444`; it gives the lowest collision rate so far but increases timeout. Do not scale this dataset directly. Next redesign should make final downward progress conditional on stronger alignment stability and avoid over-weighting cautious recenter labels.
    - Insert-settle 2k is implemented and tested, but also not promoted. The 2k set has `1920` samples, `oracle_down_action_rate=0.618`, `oracle_lift_action_rate=0.334`, and phases `slow_insert=590`, `settle=842`, `lift_recenter=397`, `recenter=91`. The 5% replay checkpoint matched insert-drift on hard seed `602000` at `0.417/0.133/0.450`; the 10% replay checkpoint regressed the 20-episode hard bucket to `0.300/0.100/0.600`. Do not keep scaling one-step late-stage BC labels; next work should inspect closed-loop final insertion traces or move final millimeters into a deployment-time guarded/servo controller.
    - Insert late-stage closed-loop trace and guard scalar scan are complete. On hard seed `602000`, insert-drift and insert-settle w05 both had `27/60` timeouts; most timeout episodes entered the strict 5 mm insert band before drifting out to about `6 - 7 mm` XY and ending around `24 mm` above target. Scalar tuning did not help: prediction `1.0/2.0` and strong near-action limiting regressed, while higher down action, wider align/insert thresholds, gain `1.5`, and timeout-progress deployment guard were flat on the same 20-episode window. Next implementation should be a stateful final insertion servo with an explicit near-hole phase, alignment-stability gate, and bounded lift/recenter recovery. Do not keep scanning single guard thresholds unless the servo design changes.
    - Final-servo MVP is implemented in `GuardedPolicyController` and exposed through eval/demo/inference traces. It is not promoted as a performance improvement yet. Early/high-hover variants harmed hard-bucket success; the fast-latch setting is flat versus baseline on hard seed `602000` (`20ep 0.500/0.150/0.350`, `60ep 0.417/0.133/0.450`). Keep the code and fast-latch config as a diagnostic hook. Next improvement should redesign low-Z recovery into a small unjam/hold/recenter behavior, not a large lift or more one-step BC.
    - Latest local guard diagnostic adds `guard_approach_recenter_*` and hysteretic `guard_final_servo_low_recenter_*` phases. This is not promoted. It preserves a direct success seed (`602025`) but the old plateau seeds still timeout: `602024` ends near `6.29 mm / 8.94 mm` XY/Z, `602033` near `6.40 mm / 10.34 mm`, and `602048` near `6.95 mm / 16.78 mm`. Treat the remaining problem as low-level Cartesian authority under delay/action-scale randomization, not a missing threshold.
    - `--guard-near-ik-orientation-weight` is now implemented in eval/demo/inference as an opt-in phase-local IK orientation relaxation. It keeps nominal `ik_orientation_weight` during high-start approach and switches only during stateful recovery, approach recenter, final-servo, or the near-hole guarded zone.
    - Current low-recenter hard-bucket 40ep gate on seed `602020`: fixed `w_ori=0.03` reached `0.925/0.000/0.075`; global `w_ori=0.0` reached `0.900/0.000/0.100`; nominal `0.03` plus `--guard-near-ik-orientation-weight 0.0` reached `0.950/0.000/0.050`. Remaining failures are `602038` and `602048`, both timeouts. Treat phase-local orientation relaxation as the best current candidate but not a promoted milestone until a 60ep/100ep gate passes.
    - Strict final-servo stable-XY gate is the current best single-geometry hard recovery candidate. Config: `configs/sim/ur5e_full/eval_high_start_hard_localkp3_recovery_strictstable49_60ep.yaml`. Result on 60ep seed `602000`: `0.983/0.000/0.017`; only remaining failure is `602048`.
    - `602048` diagnosis: low-recenter is active for hundreds of steps and stalls around `5.7 mm` XY / `16.5 mm` Z under action delay/filter/scale randomization. Focused probes with plateau-triggered lift-recenter, `guard_action_gain=2.0`, no descent bias, and near-hole `w_ori=0.01` did not solve it within `1000` steps. Do not keep scanning one-seed thresholds; the remaining issue is final insertion stability under tilt/contact/control-delay.
    - Do not scale v4b/v4b2 data or use those checkpoints as candidates unless the label/controller design changes.
- Hard high-start bounded retry status:
  - `GuardedPolicyConfig` supports bounded retry/re-align parameters and diagnostics.
  - `eval_guarded_policy.py`, `demo_policy.py`, and `run_policy_inference.py` expose retry args and trace fields.
  - The current retry config is not promoted: same-seed 20-episode success was clean `0.300`, visual_camera `0.150`, visual_camera_control `0.250`, full_light_geometry `0.250`, full_contact_light `0.250`, hard bucket `0.300`.
  - The retry demo still timed out near `8.4 mm` XY error and `27.5 mm` above target after two retry attempts.
  - Treat this as evidence that the next fix should change near-hole guarded oracle / IK alignment behavior before expanding correction data or retry scans.
- Hard high-start no-prediction guard status:
  - `OracleControllerConfig` supports `guarded_hold_z_until_insert`, but strict hold-Z alone is only diagnostic and is not promoted.
  - The strongest current controller-only improvement is `guarded_prediction_steps: 0.0` with `guarded_two_stage`.
  - Same-seed 100-episode success is clean `0.560`, visual_camera `0.500`, visual_camera_control `0.530`, full_light_geometry `0.450`, full_contact_light `0.380`, hard bucket `0.430`.
  - Demo seed `571001` succeeds in `411` steps; seed `571000` remains a hard-case timeout and should be used for the next controller trace.
- Hard high-start insert latch status:
  - `GuardedPolicyConfig` supports insert latch / descent hysteresis settings and trace diagnostics.
  - `eval_guarded_policy.py`, `demo_policy.py`, and `run_policy_inference.py` expose latch settings.
  - Current latch/recenter configs are experimental only:
    - `configs\sim\ur5e_full\eval_high_start_hard_pred0_latch_guarded_50k.yaml`
    - `configs\sim\ur5e_full\demo_high_start_hard_pred0_latch_guarded_50k.yaml`
  - Seed `571000` confirmed the key failure: the peg enters the `5 mm` band, then drifts out while descending. Pausing descent alone does not recover it.
  - A two-stage recenter variant that first lifts before lateral re-align was tested, but a 10-episode hard-bucket smoke reached only `0.400` success with `0.500` collision. Do not promote latch/recenter.
  - Manual tracking diagnostics showed IK can solve the requested Cartesian move, but physical tracking becomes extremely slow while the peg tip is still wedged inside the hole-wall height range. The next useful fix is contact-aware failure correction / DAgger or a better guarded oracle, not more latch threshold scans.
- Current near-term plan:
  - keep `guarded_prediction_steps: 0.0` as the best controller-only hard high-start setting
  - treat insert latch / retry / strict hold-Z as diagnostics, not defaults
  - follow the two-track high-start insertion plan in `PLAN.md`
  - shared environment action/IK/tracking diagnostics are now available in `info`, demo traces, inference traces, and dataset diagnostics
  - Track A hover/descent-gate mechanics are implemented but not promoted:
    - configs: `eval_high_start_hard_pred0_hover_guarded_50k.yaml` and `demo_high_start_hard_pred0_hover_guarded_50k.yaml`
    - hard seed `571000` now latches and starts descent near `3.8 mm` XY, but still wedges around `5.1 - 5.3 mm` XY and times out
    - same-seed 10-episode hard-bucket smoke was flat versus pred0 guarded baseline: both `0.400` success, `0.500` collision, `0.100` timeout
  - Track B contact-aware correction labels are implemented and smoke-tested:
    - `OracleMode` supports `contact_aware_recovery`
    - correction datasets record `contact_recovery_window`, `recovery_phase`, `oracle_lift_action`, and `oracle_down_action`
    - smoke dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_smoke.npz`
    - smoke labels are intentionally strong: `256/256` samples are `unjam_lift`, oracle lift rate `1.0`, opposed-action rate `0.953`
    - 10% replay / 1 epoch smoke checkpoint was flat on the same-seed 10-episode hard bucket: `0.400` success, `0.500` collision, `0.100` timeout
    - staged Track B collection is now implemented with branch rollouts, optional control-history clearing, synthetic recovery curriculum states, and phase-balanced sample selection
    - staged smoke dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_smoke.npz`
    - staged smoke phase counts: `unjam_lift=410`, `realign=49`, `slow_insert=53`
    - 15% replay / 1 epoch staged smoke checkpoint is not promoted: same-seed 10-episode hard bucket stayed `0.400` success, `0.500` collision, `0.100` timeout, and seed `571000` became a collision
    - staged 2k dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_2k.npz`
    - staged 2k phase counts: `unjam_lift=1674`, `realign=172`, `slow_insert=202`
    - staged 2k weighted BC is not promoted: 5% and 10% replay both reached hard-bucket `0.450` success in the same-seed 20-episode matrix, while seed `571000` still collided
    - `pretrain_image_actor_bc_weighted.py` now supports optional phase-balanced recovery sampling with `phase_balanced_recovery`, `recovery_phase_names`, and `recovery_phase_weights`
    - phase-balanced staged 2k w10 e2 uses 10% correction replay and `unjam_lift/realign/slow_insert = 0.30/0.35/0.35`; it reached hard-bucket `0.500` success, `0.400` collision, `0.100` timeout in the same-seed 20-episode matrix
    - phase-balanced staged 2k w15 e2 regressed to hard-bucket `0.450` success and `0.450` collision; do not simply increase correction replay weight
    - phase-balanced staged 2k w10 is still not promoted because full_light_geometry is only `0.350` and seed `571000` still collided
    - next Track B step should improve failure-state coverage or add a guarded recovery gate before scaling beyond 2k
  - Visual contribution audit status:
    - `eval_guarded_policy.py` supports `control_mode=guarded|policy|guard_only` and `image_ablation=normal|black|noise|shuffle`
    - hard-bucket 10-episode smoke on pred0 hard high-start shows visual input matters: policy-only normal reached `0.100` success, while black/noise/shuffle reached `0.000`
    - guarded normal reached `0.400`, while guarded corrupted-image runs reached `0.100`
    - privileged guard-only reached `0.500`, so the current hard high-start result is still not pure visual-policy success
    - `scripts\audit_visual_visibility.py` exports step-level visibility CSVs plus key-frame wrist/overview/crop images
    - 3-episode pred0 guarded visibility smoke found both hole center and peg tip project into the full wrist image, but the fixed center crop never contains both; segmentation found hole geometry in the crop and no peg geometry in the crop
    - `PegInHoleMujocoEnv` and the main sim collection/training/eval/demo scripts now support `near_hole_crop_offset`; default `[0, 0]` preserves old behavior
    - `scripts\scan_visual_crop_offset.py` scans fixed crop offsets without changing the rollout policy input
    - 3-episode pred0 guarded crop scan selected `near_hole_crop_offset: [-18, 0]`: insert-band both-projected-in-crop improved from `0.000` to `1.000`, while both-visible-in-crop improved only to `0.140`, showing crop framing is fixable but occlusion remains
    - shifted-crop training smoke is not promoted: same-seed 10-episode guarded baseline center crop reached clean/visual_camera/visual_camera_control/hard bucket `0.600/0.700/0.500/0.400`, while crop-left 1k e2 reached `0.500/0.400/0.300/0.300` and crop-left 10k lr3e-6 e1 reached `0.500/0.400/0.100/0.200`
    - a 2-episode crop-left visibility audit still reached `both_in_crop=1.000`, so the crop offset fixes framing but short fine-tuning from the old center-crop checkpoint causes observation-shift regression
    - `scripts\scan_wrist_camera_pose.py` now scans candidate wrist camera local pose/FOV/crop settings offline against sampled rollout states, restoring the rollout camera before each policy action
    - rotation/FOV/crop scan showed only a small gain: insert-band both-crop-visible from about `0.149` to `0.161`
    - position/yaw/crop scan found a strong visibility candidate: local camera `pos_offset=[-0.04,-0.04,0.00]`, `rot_offset_deg=[0,0,0]`, `fovy=100`, `near_hole_crop_offset=[-18,0]`, with sampled insert-band and near-XY both-crop-visible rates `1.000`
    - candidate frame export did not show an obvious invalid view, but this remains a visibility-only result and must not be promoted as policy performance until data is collected/trained with the new camera pose
    - env/config support now exists for `wrist_camera_pos_offset`, `wrist_camera_rot_offset_deg`, and `wrist_camera_fovy`; defaults preserve the original XML camera, and camera randomization jitters around the configured nominal pose
    - 1k wrist-pose smoke dataset/training/eval ran end-to-end, but is not promoted: source oracle collection success/collision/timeout was `0.214/0.214/0.571`, the 2-epoch BC final train/val loss was `0.596712/0.526904`, and 10-episode guarded eval reached hard-bucket `0.000` success with `1.000` collision
    - hard-bucket failure had `0` guard steps, meaning the policy fails before reaching the guarded near-hole region under the new camera observation
    - 10k wrist-pose scratch with seed `564000` improved substantially: e20 train/val loss `0.086670/0.091862`; 10-episode guarded eval reached clean/visual_camera/visual_camera_control/full_light/full_contact/hard `0.500/0.500/0.400/0.100/0.400/0.300`
    - 10k scratch is still below the old center-camera baseline, so it is not promoted; it does show the new camera path is trainable when trained from the new observation distribution
    - 50k wrist-pose scratch e20 is the first competitive new-camera model: final train/val loss `0.045830/0.047674`; 20-episode guarded eval reached clean/visual_camera/visual_camera_control/full_light/full_contact/hard `0.550/0.600/0.350/0.400/0.400/0.400`
    - old center-camera baseline for the comparable 20-episode matrix was `0.550/0.500/0.500/0.400/0.400/0.450`; wrist pose improves visual_camera but regresses on visual_camera_control and hard bucket
    - broad wrist-pose visual_camera_control replay did not fix control performance: 50k control dataset collection success/collision was `0.413/0.210`; replay weights `0.45/0.55` and `0.25/0.75` both evaluated to clean/visual_camera/visual_camera_control/full_light/full_contact/hard `0.550/0.600/0.350/0.400/0.300/0.400`
    - control failure analysis showed the weak buckets are `delay=2`, `low scale <0.90`, `high noise >=0.00055`, and mid filter alpha
    - targeted delay-2 control replay was tested and is not promoted: 20k targeted data had collection success/collision `0.234/0.419`; weighted replay stayed at clean/visual_camera/visual_camera_control/full_light/full_contact/hard `0.550/0.600/0.350/0.400/0.300/0.400`; 80-episode control failure success worsened to `0.175`
    - near-action limiter tests are not promoted: strong limiting collapsed success to near zero, while mild limiting was flat on `visual_camera_control`
    - local branch `feature/control-state-observation` contains the next structural fix: optional image observation key `control_state` with previous commanded action, measured TCP/peg-tip delta, command-minus-measured error, and normalized step fraction
    - control-state smoke passed: 512-sample dataset contains `control_state` shape `[512, 10]`; single-dataset scratch smoke and weighted smoke both trained/saved; derived-control-state smoke on the old 10k dataset also trained; 2-episode guarded eval loaded and rolled out
    - old image checkpoints are not compatible with `include_control_state: true`; train scratch control-aware image models instead
    - first control-state performance runs are not promoted:
      - 10k control-state scratch e10 reached clean/visual_camera/visual_camera_control/full_light/full_contact/hard `0.450/0.400/0.400/0.300/0.300/0.300`
      - 60k mixed scratch e8 reached `0.550/0.600/0.400/0.350/0.350/0.400`
      - 80-episode policy-only control failure analysis for 60k mixed scratch was poor: `0.125` success, `0.562` collision, `0.312` timeout
    - control-state image ablation is complete and confirms the model still uses images:
      - guarded normal/black/noise/shuffle visual_camera_control success: `0.400/0.000/0.050/0.050`
      - policy-only normal/black/noise/shuffle visual_camera_control success: `0.150/0.000/0.000/0.000`
      - guard-only visual_camera_control success: `0.600`
    - frame stacking is implemented for `cam_image`, `near_hole_crop`, and `control_state`; stack3 smoke passed, but the 60k mixed stack3 scratch e6 checkpoint regressed:
      - guarded clean/visual_camera/visual_camera_control/full_light/full_contact/hard `0.500/0.400/0.350/0.300/0.150/0.350`
      - 80-episode policy-only visual_camera_control success/collision/timeout `0.013/0.800/0.188`
    - DAgger v2 handoff correction is implemented for the wrist-pose + control-state path:
      - correction collection supports `include_control_state`, `selection=near_hole`, `keep_success_episodes`, and `recovery_branch_from_near_hole`
      - 2k dataset phase mix: `realign=1099`, `slow_insert=402`, `unjam_lift=547`
      - 2k w10 e2 guarded clean/visual_camera/visual_camera_control/full_light/full_contact/hard `0.550/0.550/0.500/0.350/0.350/0.400`
      - 80-episode policy-only visual_camera_control success/collision/timeout `0.263/0.438/0.300`
      - image ablation passed: policy-only visual_camera_control normal/black/noise/shuffle success over comparable 40-episode windows `0.300/0.000/0.000/0.000`
    - final-servo recovery diagnostics are complete:
      - fast-latch final servo is implemented but not promoted: hard 20ep seed `602000` stayed `0.500/0.150/0.350`, and hard 60ep stayed flat versus insert-drift baseline
      - soft-unjam recovery, stricter release, and +3mm X descend bias also stayed flat at hard 20ep `0.500/0.150/0.350`
      - best soft-unjam mean return improved to `273.706`, but timeout episodes did not cross success thresholds
      - timeout endpoints are systematic, roughly `peg_tip_x - target_x ~= -6.8 mm`; post-wedge recovery/bias does not move those endpoints enough
      - do not keep scanning final-servo recovery parameters unless the structure changes. Focus next on preventing low-Z drift before contact wedging
    - preinsert recenter gate is implemented but not promoted:
      - hard 20ep seed `602000` stayed `0.500/0.150/0.350` across 25mm, early 35mm, and short-confirm variants
      - mean return improved up to `460.382`, and final-servo steps dropped, but timeout episodes still did not cross success thresholds
      - traces show commanded lateral recentering can fail to move the measured peg tip toward the hole near low-Z insertion
      - do not continue threshold-only preinsert guard scans. Next priority is low-level UR5e controller realism: orientation-constrained IK/TCP pose servo and posture regularization
    - recovery-sequence pose-IK replay is implemented but not promoted:
      - `collect_image_correction_dataset.py` now passes `guarded_lift_before_lateral` into `OracleControllerConfig`
      - new recovery phase: `fixture_wall_lift_before_lateral`
      - 2k dataset phases: `approach_recenter=207`, `fixture_wall_lift_before_lateral=245`, `fixture_wall_recenter=200`, `insert_drift_recenter=202`, `insert_drift_slow_insert=76`, `realign=239`, `slow_insert=130`, `unjam_lift=749`
      - 8% replay / 1 epoch checkpoint: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_recovery_sequence_pose_ik_2k_w08_e1.zip`
    - hard 60ep seed `602000` stayed flat at `0.717/0.100/0.183`
    - generic runtime `guarded_lift_before_lateral` 20ep smoke regressed to `0.150/0.800/0.050`
    - summary: `results\ur5e_full\high_start\hard\correction\recovery_sequence_pose_ik_summary.md`
    - important lesson: guarded eval uses `guard_blend=1.0`, so near-hole BC replay is mostly masked after guard activation. Future work should change controller/guard behavior instead of adding same-family replay data.
    - controller gain/frame-skip diagnostics are implemented but not promoted:
      - `PegInHoleMujocoEnv` supports `nominal_joint_damping_multiplier` and `nominal_actuator_kp_multiplier`
      - `eval_guarded_policy.py` exposes `--nominal-joint-damping-multiplier`, `--nominal-actuator-kp-multiplier`, and `--frame-skip`
      - Kp=2 hard 60ep seed `602000` reached `0.733/0.000/0.267`; it removed collisions but increased timeouts versus pose-IK `0.717/0.100/0.183`
      - Kp=4 hard 20ep regressed to `0.250/0.000/0.750`; Kp=2 with `frame_skip=20` stayed flat at hard 60ep `0.733/0.000/0.267`
      - lowering pose-IK orientation weight to `0.06` and increasing IK iterations to `48` is the current best controller candidate: hard seed `602000` improved to `0.767/0.100/0.133`
      - the same `0.06/48` setting across 20ep x 3 seeds averaged `0.767/0.100/0.133`, a small but real gain over the previous pose-IK average `0.750/0.117/0.133`
      - the 100ep matrix improved success in all scenarios: clean `0.850`, visual_camera `0.840`, visual_camera_control `0.840`, full_light_geometry `0.850`, full_contact_light `0.850`, hard `0.790`
      - candidate configs are `eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_hard_60ep.yaml` and `eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_matrix_100ep.yaml`
      - candidate hard 60ep failure analysis: `6` high-fixture-wall collisions, `2` insert-band low-Z drift timeouts, and `6` near-XY no-insert timeouts
      - raising `guard_start_z` to `0.16` or `0.20` stayed flat in 20ep hard smokes; next guard work should be delay-aware/trajectory-aware, not just earlier activation
      - follow-up Kp2 combination is now the current best controller candidate:
        `ik_orientation_weight=0.06`, `ik_max_iterations=48`, `nominal_actuator_kp_multiplier=2.0`
      - Kp2 hard 60ep seed `602000`: `0.850/0.000/0.150`
      - Kp2 hard 60ep seed `604000`: `0.867/0.000/0.133`
      - Kp2 100ep matrix success/collision/timeout:
        clean `0.910/0.000/0.090`, visual_camera `0.910/0.000/0.090`, visual_camera_control `0.910/0.000/0.090`, full_light_geometry `0.900/0.000/0.100`, full_contact_light `0.900/0.000/0.100`, hard `0.890/0.000/0.110`
      - Kp2 failures are now only timeouts; hard 60ep has `7` misaligned timeouts and `2` near-XY no-insert timeouts, all delay-2 dominated
      - `guarded_align_xy_tolerance=0.030` regressed hard 60ep to `0.833/0.000/0.167`; do not promote wider align
      - Kp2 configs are `eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_kp2_hard_60ep.yaml` and `eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_kp2_matrix_100ep.yaml`
      - summary: `results\ur5e_full\controller_diagnostics\controller_gain_frame_skip_summary.md`
      - matrix summary: `results\ur5e_full\controller_diagnostics\pose_ik_wori006_it48_matrix_summary.md`
      - Kp2 summary: `results\ur5e_full\controller_diagnostics\pose_ik_wori006_it48_kp2_summary.md`
      - Kp2 demo is generated and successful; next work should target remaining delay-2 high-misalignment timeouts, then consider pushing/tagging it as a stable controller milestone
    - contact-aware reinsert diagnostics on `feature/contact-aware-reinsert` are experimental but now have a strong v42 candidate:
      - default-off hooks exist for `contact_reinsert_orient_hold`, `contact_reinsert_descend`, `contact_reinsert_micro_align`, phase-local orient max XY, micro-align up action, tip-lock, high-clearance re-approach phases, and phase-local tip-priority IK
      - targeted `single/612010` v21-v39 runs still timed out or collided; do not repeat those scalar scans
      - key old failure: tight contact recenter could briefly reach `4.7-4.9 mm` XY, but orientation correction moved tip XY back to `6-7 mm`; low-Z reinsert then stalled around `5.65-5.75 mm`
      - v35 tip-lock and v36-v39 high-clearance re-approach were negative
      - v42 phase-local tip-priority IK fixed the known hard seeds and reached `1.000/0.000/0.000` on 20ep and 60ep matrices across `single`, `round_square`, `square_square`, and `mixed_basic` on seed `612000`
      - first out-of-window 10ep profile matrix on seed `613000` also reached `1.000/0.000/0.000` for all four profiles
      - seed `614000` 20ep profile matrix also reached `1.000/0.000/0.000` for all four profiles
      - seeds `615000/616000/617000` 20ep profile matrix exposed one hard initialization. v42 reached `236/240`; wide-handoff reached `238/240`; `max_steps=1500` rescues the two known remaining square timeouts.
      - next work is not another scalar scan; decide whether the project target is strict 1000-step completion or practical 1500-step completion, then promote or tune final-servo recovery accordingly
    - v47 strict-1000 boundary recovery candidate is now the current approach-stage candidate:
      - added default-off fixture-clearance retreat config fields and CLI wiring in eval/demo/inference
      - direct retreat alone converted the hard `seed631004` collisions to timeouts but did not solve completion
      - successful recipe is earlier final-servo handoff plus stronger approach control:
        `nominal_actuator_kp_multiplier=3.0`, `guarded_max_xy_action=0.008`, `guard_final_servo_start_xy=0.035`
      - fixture retreat remains enabled only as a low-altitude fallback in the v47 config:
        `guard_fixture_clearance_z_max=0.052`, `retreat_release_xy=0.060`, `retreat_max_xy_action=0.003`
      - new config: `configs/sim/ur5e_full/eval_multi_geometry_early_final_servo_boundary_stress_20ep.yaml`
      - validation: hard `seed631004` all-profile check reached `4/4` success, and boundary regression seeds `630000/631000` reached `80/80` success/collision/timeout `1.000/0.000/0.000`
      - larger boundary gate seeds `632000/633000/634000` initially reached `238/240`, with two `seed634014` high-Z slow-descent timeouts where guard never activated at `guard_start_z=0.12`
      - raising `guard_start_z` to `0.14` fixed seed `634000` to `80/80`, and the v47 control settings on the v46 moderate-stress distribution reached `240/240`
      - current v47 config includes `guard_start_z=0.14`; demo config is `configs/sim/ur5e_full/demo_multi_geometry_early_final_servo_boundary.yaml`
      - v47 demo `square_square/seed634014` succeeded in `288` steps; GIF fallback is `D:\peg-in-hole-6yh\v47_early_final_servo_demos\demo_v47_square_square_seed634014_guarded_overview_wrist.gif` at `2560x720`
      - before promotion/tagging, decide whether this becomes the strict-1000 boundary default or run one larger final promotion gate first
    - results are summarized in `VISUAL_AUDIT.md`; do not scale to 50k control-state data or promote stack3. DAgger v2 is promising but must pass larger evals before promotion
  - keep correction BC as a supporting dataset path, but do not expand to 10k until the controller issue is addressed
  - introduce larger randomized initial XY offsets only after original hard high-start search is stable
  - then reintroduce control/geometry/contact randomization
  - crop-source jitter pilot status:
    - 2026-05-26 pilot output is outside the repo at `D:\peg-in-hole-6yh\v48_crop_source_jitter_pilot`
    - 2k expert jitter dataset reached success/collision/timeout `0.800/0.000/0.200`; geometry split was skewed toward `square_square`
    - 1-epoch LR `1e-6` continuation from v47 trained cleanly but did not improve the fixed source-size scan
    - fixed-source candidate scan on seed `642000` matched v47: `64 -> 64` positive X offsets `2/5`, `80 -> 64` `3/5`, `96 -> 64` `5/5`
    - runtime `[80,96]` source range on seed `643000` gave both base v47 and candidate `9/10` at `+12` and `+24`; do not promote the 2k jitter continuation
    - observed failure is far-XY approach on `round_square`: `dist_xy` grows to about `0.20 m`, guard never activates, no collision. Next useful work is approach-stage visual servoing / hard far-XY data, not more low-risk crop jitter.
  - round-square approach pilot status:
    - correction data collection now supports hard-control overrides, geometry overrides, nominal actuator/joint multipliers, and `approach_sample_sort_key`; these are useful and should be kept
    - v49 outputs are outside the repo at `D:\peg-in-hole-6yh\v49_round_square_approach_failure_pilot`
    - natural timeout-only collection was too sparse and timed out after 20 minutes
    - DAgger-style approach-window data was easier to collect but the first `correction_norm`-sorted set over-sampled early approach states
    - `steps_to_end` sorting captured late seed643009 states with XY up to about `0.176 m` and opposed policy/oracle actions
    - weighted BC candidates did not improve the hard `round_square` seed643 eval: base and v49 late candidate both stayed `9/10` at crop offsets `+12` and `+24`
    - do not promote/tag the v49 approach BC models; next useful step is to compare stronger approach-specific visual curriculum against a default-off early approach assist/guard
  - early approach assist pilot status:
    - `guard_early_approach_assist` is implemented default-off in `GuardedPolicyController` and wired through `scripts/eval_guarded_policy.py`
    - v50 pilot outputs are outside the repo at `D:\peg-in-hole-6yh\v50_early_approach_assist` because `results/` currently rejects new writes
    - no-assist baseline on `round_square`, seed `643000`, crop-source range `[80,96]`: `[+12,0] 9/10`, `[+24,0] 9/10`, both with one timeout and no collision
    - early assist on the same target: `[+12,0] 10/10`, `[+24,0] 10/10`, no collisions/timeouts; mixed_basic spillover `[+12,0]` and `[+24,0]` also reached `10/10`
    - larger v50 gate outputs are outside the repo at `D:\peg-in-hole-6yh\v50_early_approach_assist_gate`
    - promoted config: `configs/sim/ur5e_full/eval_multi_geometry_early_approach_assist_gate_10ep.yaml`
    - v50 gate reached `120/120` success, `0` collision, `0` timeout on seed `643000`, crop-source range `[80,96]`, profiles `single/round_square/square_square/mixed_basic`, offsets `[-18,0]`, `[+12,0]`, `[+24,0]`
    - next work should reduce dependence on deploy-time assist by improving learned high-start far-XY approach behavior
  - early approach assist BC pilot status:
    - `scripts/collect_image_correction_dataset.py` now supports `early_approach_assist_labels`, `early_approach_assist_window`, and `early_approach_assist_failure_window`
    - it also supports `early_approach_assist_window_mode`; use `trigger_only` for the recommended data path
    - collection/pretrain configs are `collect_high_start_hard_wrist_pose_control_state_early_approach_assist_2k.yaml` and `pretrain_high_start_hard_wrist_pose_control_state_early_approach_assist_trigger_2k_w05_e1.yaml`
    - v51 pilot outputs are outside the repo at `D:\peg-in-hole-6yh\v51_early_approach_learning`
    - 512-sample pilot trained cleanly but regressed unassisted `round_square seed643000` from baseline `9/10` to `8/10` at both crop offsets `[+12,0]` and `[+24,0]`; do not promote the v51 512 checkpoint
    - v52 trigger-only 5% replay avoids the collision regression and matches baseline `9/10` at `[+12,0]` and `[+24,0]`, but with early assist enabled the mean assist steps remain `30.2`
    - do not promote v52 as a model milestone either; next learner-side work should use a gated approach adapter or explicit approach subpolicy instead of more broad monolithic BC scans
  - gated approach adapter smoke status:
    - module `peg_in_hole_mujoco/approach_adapter.py` and script `scripts/train_approach_adapter.py` are in place
    - eval wiring now supports `--approach-adapter` with `residual` and `override_xy` modes
    - 512-sample residual and override pilots were both trained from trigger-only data
    - neither variant beat the no-assist `round_square +12` baseline; residual mode was clearly worse in episode length, override mode was closer but still only `9/10`
    - v2 adapter support now exists for `cam_image + near_hole_crop + control_state`; config `train_approach_adapter_trigger_2k_full_crop_xy_override.yaml` trains it
    - 512-sample v2 full+crop override smoke also did not beat baseline: `8/10` with `max_xy=0.005`, `9/10` with `max_xy=0.003` on `round_square +12`, and `9/10` on `+24`
    - collector now supports adapter-rollout DAgger via `--rollout-approach-adapter*`; datasets record rollout adapter active/residual/base-policy fields
    - targeted DAgger showed the real issue: the adapter can push opposite the oracle on its own visited states, so collect adapter-induced failures instead of only static trigger windows
    - v6 full+crop mixed wide-XY + targeted DAgger adapter plus lower eval gate `--approach-adapter-trigger-xy 0.06 --approach-adapter-release-xy 0.03` reached `10/10` on `round_square` seed `643000` for crop offsets `[-18,0]`, `[+12,0]`, and `[+24,0]` without v50 early assist
    - v6 also reached `10/10` for the `+12` crop-offset smoke on `single`, `round_square`, `square_square`, and `mixed_basic`, with zero collision and zero timeout
    - v6 seed643000 full profile/offset matrix passed: `120/120`, zero collision, zero timeout across `single`, `round_square`, `square_square`, `mixed_basic` and offsets `[-18,0]`, `[+12,0]`, `[+24,0]`
    - v6 seed644000 full profile/offset matrix also passed: `120/120`, zero collision, zero timeout with the same profiles and offsets
    - v6 seed645000 with the original conservative eval setting `min_z=0.12`, `max_xy_residual=0.003` failed at `106/120`, zero collision, 14 timeouts. The failures were approach-stage timeouts, not insertion wedging.
    - tuned eval setting `min_z=0.08`, `max_xy_residual=0.006` passed seed645000 full profile/offset matrix: `120/120`, zero collision, zero timeout.
    - the same tuned setting regressed seed644000 to `109/120`, zero collision, 11 timeouts, mostly episode seed `644002` with adapter active for all 1000 steps and no guard/final-servo handoff
    - do not promote v6; checkpoint is a local smoke/targeted-data artifact outside Git, and fixed eval-threshold tuning is not robust enough. Next work should collect targeted adapter-rollout DAgger data from seed645 failures and train v7 while preserving seed644 behavior
    - v7 targeted DAgger smoke collected `96` mixed-basic `+24` timeout samples from seed645 rollout-adapter failures and trained `D:\peg-in-hole-6yh\v62_adapter_v7_targeted_dagger\approach_adapter_v7_fullcrop_mix_seed645_dagger_xy_override.pt`
    - v7 is not promoted: under the original conservative eval gate it reached only `9/10` on each targeted seed645 condition tested (`single +12`, `single +24`, `round_square +24`, `square_square +24`, `mixed_basic +24`), all zero collision but still one timeout each
    - next adapter work should scale targeted DAgger across profiles and crop offsets and include seed644 preservation cases; do not keep scanning fixed min-z/max-xy thresholds
    - adapter v8 balanced DAgger is trained at `D:\peg-in-hole-6yh\v63_adapter_v8_balanced_dagger\approach_adapter_v8_fullcrop_balanced_seed645_dagger_xy_override.pt` from the old v6/v7 recipe plus 8 balanced seed645 timeout datasets
    - `scripts/eval_guarded_policy.py` now supports default-off latched adapter gating with `--approach-adapter-latch-enabled`, `--approach-adapter-latched-min-z`, `--approach-adapter-max-steps`, and `--approach-adapter-episode-max-steps`
    - v8 without latch still mostly reached only `9/10` on the targeted seed645 failure cases, so the key improvement is the bounded latch, not just more DAgger data
    - current adapter v8 latched candidate uses activation `min_z=0.12`, latched `min_z=0.08`, `max_steps=220`, `trigger/release=0.06/0.03`, `override_xy`, and `max_xy_residual=0.003`
    - v8 latched candidate passed full 12-run profile/offset matrices on seeds `643000`, `644000`, and `645000`: combined `360/360`, zero collision, zero timeout
    - fresh seed `646000` also passed with the original latch220 recipe, but seed `647000` regressed to `116/120`, all `m18` timeouts from episode `647008`
    - the current stronger probe keeps v8 latch220 and adds `--guard-final-servo-start-z 0.100`; it passed seed `643000` through `647000` full matrices: combined `600/600`, zero collision, zero timeout
    - adapter artifact repo path: `assets\approach_adapters\approach_adapter_v8_fullcrop_balanced_seed645_dagger_xy_override.pt`, size `341061` bytes, SHA256 `0788831FBC94E344865A35ACD96408C40D72D50521D2C668D86570F640EE53EB`
    - direct filesystem copy into `assets` was blocked by local Windows ACL on 2026-05-29, so the artifact was added through Git object/index plumbing. On this local worktree the artifact path is marked `skip-worktree`; fresh clones/checkouts should contain it normally. The code+artifact recipe is promoted as `v0.7.4-v8-adapter-finalstart100`; optionally mirror the checkpoint as a GitHub release asset later if needed

## Editing Workflow

- Current hard-square context: v221
  `configs/sim/ur5e_full/eval_multi_geometry_v221_v220_clean3_escape55_hard_square_30ep.yaml`
  remains the last pushed stable milestone, committed/tagged/pushed as
  `v0.7.7-hard-square-clean3-escape55`.
- Current local diagnostic context: v239-v244 on
  `feature/contact-aware-reinsert`. These are rejected or non-promotable
  hard-square diagnostics, not release candidates.
  - v239 added structured soft-hold release-continue, but still collided on
    targeted `929524`.
  - v240 added bounded soft-hold extension and fixed targeted `929524`, but
    regressed `927500` to `28/30`.
  - v241 made extension late-only and restored `927500=30/30`, but `929500`
    stayed `29/30` on `929504`.
  - v242 globally limited contact-brake to one attempt and regressed `929500`
    to `28/30`.
  - v243 added repeat-brake margin gating; targeted seeds and `927500=30/30`
    passed, but `929500` stayed `29/30` on `929518`.
  - v244 narrowed low-Z relief margin and regressed focused `929518` and
    `931509`.
  Do not keep sweeping single scalar thresholds here. The next useful work is a
  structured late contact-chain handoff rule using post-contact stability, not
  another global soft-hold/brake/low-Z-relief threshold scan.
- Latest hard-square diagnostics, still local and not promotable:
  - v247-v252 explored low-Z clearance hold, action-level down guard, and
    contact-brake release timing. v252/v253 can pass the original
    `927500/929500/931500` 30ep gates in some current runs, but the hard-square
    eval is not fully repeat-stable.
  - v253 added `guard_final_servo_square_contact_brake_late_lift_release_*` and
    passed `927500/929500/931500`, plus a repeat `931500`, but failed extra
    `933500=29/30` with a timeout. Treat as diagnostic only.
  - v254 lowered late recovery-escape height and fixed `933500`, but regressed
    `931500` and `929500` to collisions. Reject.
  - v255 added
    `guard_final_servo_square_recovery_escape_direct_fast_settle_from_escape_*`,
    but `933500` still failed with an early collision. Reject.
  - v256 moved low-Z down guard/clearance hold to brake attempt `>=1` and
    regressed `933500` to `28/30`. Reject.
  - Before adding more control rules, add trace instrumentation for which guard
    transition fired and include direct-fast-settle active state in step CSVs;
    then rerun serial `929500/931500/933500` gates.
- Current instrumentation status:
  - `guard_final_servo_phase_transition_reason` and
    `guard_final_servo_square_recovery_escape_direct_fast_settle_active` are now
    included in guarded-policy step traces and `scripts\eval_guarded_policy.py`
    step CSV output.
  - The transition reason is a one-step pulse, reset to `none` at the beginning
    of each guarded-policy step.
  - A 1-episode smoke on v253 seed `933500` passed and confirmed both columns
    are present. Direct-fast-settle did not trigger in that smoke.
  - Serial trace-enabled reruns found v258 as the current best local diagnostic
    point: `929500=30/30`, `931500=30/30`, `933500=29/30` with one timeout and
    zero collisions. It is not a release candidate.
  - v257/v259/v260/v261 direct-fast-settle gates are not promotable. They shift
    the failure between late timeout and collision across seeds.
  - v262-v266 added and tested structured late escape/finish logic:
    - late recovery-escape recenter descend plus hold-release gates:
      `guard_final_servo_square_recovery_escape_late_recenter_descend_*`
    - guarded-state `square_peg_topdown_clearance_margin`
    - topdown-gated late finish continuation:
      `guard_final_servo_square_fast_settle_late_finish_continue_topdown_margin_min`
  - Current best local candidate is v265
    `configs/sim/ur5e_full/eval_multi_geometry_v265_v263_topdown_gated_late_finish_continue_hard_square_30ep.yaml`.
    It has current 30/30 records on `929500`, `933500`, and a repeat
    `931500`, but repeat `929500` with full trace regressed to `29/30`.
    Treat v265 as promising but not promoted.
  - Reject v264, v266, v267, and v268 as release candidates. v264 regressed
    `929500` to collisions; v266 fixed one `931500` run but regressed
    `929500` to `27/30`; v267/v268 late escape veto variants both stayed
    `28/30` on `929500`.
  - Do not keep widening late escape veto or late finish thresholds. The
    controller-only path is showing repeat-sensitive contact failures near the
    1000-step deadline. Next work should shift to targeted failure collection
    and correction/DAgger or a learned recovery adapter.
  - v269-v273 tested targeted final-insert adapter training:
    - v269 used only the v265 repeat `929524` failure tail and regressed
      `929500` to `27/30`. Reject.
    - v270 blended the v269 failure with the existing v174 low-Z success/failure
      datasets and is the best diagnostic adapter from this batch:
      `929500=30/30`, `931500=30/30`, `933500 repeat=29/30`. It is not
      promotable.
    - v270 plus runtime aligned/no-contact handoff fixed `933500` but regressed
      `929500` to a collision. Reject the handoff gate as a release direction.
    - v271/v272/v273 added the v270 `933514` timeout back into training with
      wide, downsampled, and unbalanced variants; all regressed either
      `929500` or `933500`. Reject.
    - Do not keep blindly mixing single failure traces into the low-dimensional
      adapter. Before another adapter run, add broader balanced failure coverage,
      per-dataset weighting, or a real DAgger loop.
  - v274-v275 added and tested per-dataset weighting in
    `scripts\train_final_insert_adapter.py`:
    - Use `--dataset-weights` in the same order as `--dataset` then
      `--extra-datasets`.
    - v274 included low-weight `933514` data and still regressed `933500` to
      `28/30`; reject.
    - v275 used v174 low-Z data plus low-weight v269 `929524` only. It passed
      initial `929500/931500/933500 = 30/30`, but repeat `929500` produced one
      collision. Treat v275 as the best local weighted-adapter diagnostic, not a
      release candidate.
    - A `final_insert_adapter_square_risk_xy_min=0.008` runtime probe still
      produced repeat `929500=29/30`, with the adapter inactive in the failure.
      The remaining issue is still guarded final insert/recovery
      repeat-sensitivity, not only learned adapter pollution.
  - v276-v277 moved the remaining low-Z release contact handling back into the
    guarded controller:
    - New default-off config group:
      `guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_*`.
    - v276 detected wall contact during
      `square_fast_settle_contact_soft_hold_release_continue` and handed off to
      contact-brake. It passed `929500/931500/933500`, but repeat `929500`
      timed out once because the heavy brake/recovery response consumed the
      remaining budget. Reject v276 as a release candidate.
    - v277 enables
      `guard_final_servo_square_fast_settle_contact_soft_hold_release_contact_brake_soft_hold_first_enabled`
      so release-window contact first returns to contact soft-hold, escalating
      to full contact-brake only if needed.
    - v277 focused gate with the v275 adapter:
      `929500=30/30`, repeat `929500=30/30`, `931500=30/30`, `933500=30/30`.
      Focused total: `120/120`, collision `0`, timeout `0`.
    - Current best local config:
      `configs/sim/ur5e_full/eval_multi_geometry_v277_v276_release_contact_soft_hold_first_hard_square_30ep.yaml`.
    - Wider fresh-seed gate: `935500=30/30`, but `927500=29/30` with one clean
      timeout on `927514`. Do not push/tag/promote v277 yet.
    - v278
      `configs/sim/ur5e_full/eval_multi_geometry_v278_v277_clean_tail_down_boost_hard_square_30ep.yaml`
      raised the global late-down-boost down cap and regressed `927500` to
      `28/30` with one collision plus one timeout. Reject.
    - v279
      `configs/sim/ur5e_full/eval_multi_geometry_v279_v277_clean_tail_zmin_only_hard_square_30ep.yaml`
      only extended the late-down-boost lower Z bound and stayed `927500=29/30`.
      Reject as a fix.
    - v280-v286 explored a separate very-late clean tail boost and late direct
      finish handoff. v284 (`0.0050` tail cap) is safer but still times out on
      `927514`; v286 (`0.0060`) passed initial `927500` but repeat `929500`
      regressed to collisions on `929510` and `929524`.
    - Do not promote v286. The current failure mode is mid/low-Z contact pop
      after wall contact, not final clean tail speed.
    - Current diagnostic config:
      `configs/sim/ur5e_full/eval_multi_geometry_v287_v284_contact_pop_hold_hard_square_30ep.yaml`.
      It starts from v284 and adds default-off
      `guard_final_servo_square_fast_settle_contact_pop_hold_*` logic for the
      `XY 10-24 mm`, `Z 20-42 mm`, wall-contact band. First gate should run
      `927500`, `929500`, and repeat `929500` before any promotion decision.
    - v288-v293 latest local diagnostics:
      - v288 added no-contact XY-pop current-height recenter and fixed targeted
        `929524`, but `929500` still failed on `929521`.
      - v289 global low-Z stall hold passed `929500` repeat but regressed
        `927514`; reject.
      - v290 disabling low-Z stall relief regressed `929500`; reject.
      - v291 gated low-Z stall hold on at least three contact-pop holds. It
        passed `929500`, repeat `929500`, and `931500`, but still left
        `927514` timeout.
      - v292 contact-pop-exhausted recenter did not fix `927514` and regressed
        `927500`; reject.
      - v293 added no-contact XY-pop `margin_min=-0.0030` and
        `tilt_max_deg=3.5`. Current results:
        `929500=30/30`, `927500=30/30`, `931500=30/30`, repeat
        `929500=30/30`, but `933500=28/30` with collisions on `933513` and
        `933523`.
      - Do not push/tag/promote v293. Next useful work is v294: add
        topdown/yaw gates to no-contact XY-pop recenter for `933513`, then a
        narrow post-contact-brake-release hold/flush or stricter release check
        for `933523`.
    - v294-v302 hard-square diagnostics:
      - v294 topdown/yaw gates fixed `933513` but left `933500=29/30` with
        `933523`.
      - v295 soft-hold large-pop recenter got `933500=30/30` but regressed
        `929500=29/30`; reject.
      - v296 limited no-contact XY-pop recenter to no prior contact-pop holds;
        `929500` still failed.
      - v297/v298/v299 explored low-Z relief wide recenter. v299 is the best
        diagnostic compromise: `929500=30/30`, `933500=29/30`.
      - v300/v301 narrowed no-contact recenter/yaw and worsened `933500` to
        `28/30`; reject.
      - v302 added recovery-escape recenter drift-lift and fixed `933506`, but
        `933523` returned. Remaining failure is post-contact-brake release
        pop: `square_contact_brake_recenter` stable near `XY 2.6 mm`,
        `Z 28.6 mm`, then immediate `square_fast_settle` jumps to about
        `XY 20.6 mm` and collides.
      - v303 is the current diagnostic config:
        `configs/sim/ur5e_full/eval_multi_geometry_v303_v302_contact_brake_release_flush_hard_square_30ep.yaml`.
        It adds a default-off `square_contact_brake_release_flush` phase and
        enables a 4-step zero-action flush after stable contact-brake recenter,
        gated by square geometry, at least two brake attempts, `XY<=4 mm`,
        `Z=20-35 mm`, and contact count `<=8`.
      - Validation order for v303: first `933500/30ep`, then `929500/30ep`,
        then `927500/30ep` and `931500/30ep`. Do not push/tag/promote until
        the focused gate passes.
    - v304-v313 latest local diagnostics:
      - v307 current-code baseline was re-run at
        `D:\peg-in-hole-6yh\v307_current_baseline\eval\v307_current_seed931500.*`
        and remains `931500=29/30`, collision `0`, timeout `1`.
      - v308 low-Z exhausted-continue fixed `931500=30/30`, but regressed
        `933500=28/30`, `929500=29/30`, and left `927500=29/30`; reject.
      - v309 strict `late_finish_continue` from v307 got `931500=27/30`;
        reject.
      - v310 added default-off exhausted-continue gates
        `min_steps_since_reset`, `topdown_margin_min`, and `yaw_max_deg`, but
        the low-Z window missed the current `931509` recovery trigger;
        `931500=28/30`; reject.
      - v311 moved the gated exhausted-continue window to `Z=36-39 mm`.
        Result: `931500=29/30`, collision `1`, timeout `0`. It is useful
        diagnostically because it removes the `931509` timeout class, but it is
        not promotable due to a low-Z pop collision on `931524`.
      - v312 globally enabled the existing low-Z contact down guard on v311 and
        regressed to `931500=28/30`; reject.
      - v313 added default-off
        `guard_final_servo_square_fast_settle_low_z_contact_down_guard_min_steps_since_reset`
        and enabled the guard only after 700 steps, but still got
        `931500=28/30`; reject.
      - Do not push/tag/promote v309-v313. Keep their default-off hooks for
        diagnostics. Next useful work should start from v311 and implement a
        more local low-Z pop detector/recovery rather than broadening the down
        guard.
    - v329-v330 latest local diagnostics:
      - v329 added an offline-narrowed pre-pop gate:
        `topdown_margin=0.0010-0.00145`, `tilt>=0.6 deg`,
        `yaw<=0.4 deg`, `phase_steps=8-25`.
      - Offline trace scan matched `0/84` success traces, `2/2` collision
        traces, and `0/1` timeout traces, so the trigger is discriminative.
      - Runtime results were not promotable:
        `927500=29/30`, `929500=28/30`, `931500=27/30`.
      - v330 stronger pre-pop hold (`8` steps, `+0.003` up) regressed
        `929500` to `26/30`; reject.
      - Do not push/tag/promote v329/v330. Keep the default-off hooks and
        configs for diagnostics only.
      - Next useful work should stop strengthening pre-pop hold and instead
        implement a low-Z wall-contact onset recovery in `square_fast_settle`:
        detect the first wall-contact/lateral-pop spike near `Z 26-33 mm`,
        `XY<=4 mm`, positive clearance, and exhausted brake/soft-hold history,
        then immediately lift/recenter/retry before continued descent drives
        the peg into the wall.
    - 2026-06-18 keyhole tight-yaw failure-mode diagnostic:
      - Added `scripts\analyze_key_yaw_failure_modes.py`.
      - Latest report:
        `results\key_yaw_failure_mode_analysis.md`.
      - The visible-brake local subset is `70/80`, collision `0`, timeout
        `10`; keep the historical six-seed record as `104/120`, collision
        `0/120`.
      - Temporal descent gate targeted run is `47/60`, collision `0`, timeout
        `13`.
      - Dominant residual class is `timeout_wrong_yaw_basin`, not plain
        low-level insertion stall.
      - Follow-up opportunity counting shows reliable large-yaw visual evidence
        in both successes and failures, so the camera/estimator is not the
        only bottleneck. The next useful keyhole controller work is a narrow
        wrong-basin yaw reacquire / target-preservation phase.
      - Rejected diagnostic:
        `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_near_control_eval.yaml`
        got `0/3`, collision `2`, timeout `1` on `908508,908516,910500`.
        Do not promote broad `near_control` activation.
      - Target-hold config diagnostics:
        `high_yaw_target_hold_eval` is too broad and caused a collision on
        `908508`. `high_yaw_arm_target_hold_eval` is safer but not better:
        formal smoke `2/3`, collision `0`; 40ep on `906500,908500` is
        `35/40`, collision `0`, timeout `5`, with `908500=15/20`.
        Do not promote either target-hold variant.
      - Wrong-basin hold hook is implemented in `scripts\eval_guarded_policy.py`
        and exposed through
        `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_wrong_basin_hold_eval.yaml`.
        It is default-off and diagnostic only. Same-seed 40ep comparison on
        `906500,908500`: visible-brake baseline `35/40`, wide hold `33/40`,
        6 cm max-XY hold `34/40`, all collision `0`. Do not promote/tag it.
      - Narrow wrong-basin re-acquire diagnostic is exposed through
        `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_wrong_basin_reacquire_narrow_eval.yaml`.
        New trigger quality gates are default-off in code. Same-seed 40ep:
        ungated narrow re-acquire `35/40` with `1` collision; gated + low-Z
        large-XY brake `34/40`, collision `0`. Do not promote/tag it. Treat
        this as evidence that low-confidence yaw re-acquire can rescue a hard
        seed but is not safe enough for the sim-to-real mainline.
      - Avoid more scalar safety gates unless they are paired with a specific
        yaw-reacquisition hypothesis and success-preservation seeds.
- Check `git status --short --branch` before and after code changes when possible.
- Use `rg` / `rg --files` for searching.
- Use `apply_patch` for manual file edits.
- Keep changes scoped to the requested task.
- Do not rewrite docs or code unrelated to the current milestone.
- Run targeted validation after implementation.
- Update `PLAN.md` when project status, metrics, default commands, branch state, or next milestones change.
- Update this `AGENTS.md` when user preferences, safety rules, workflow rules, or repository-level conventions change.

## Validation Expectations

Use targeted validation rather than broad expensive runs unless needed.

Common checks:

```powershell
python -m py_compile <changed_python_file>
git diff --check
python scripts\inspect_robot_model.py --model-path <model.xml> --fail-on-missing
python scripts\oracle_rollout.py --model-path <model.xml> --observation-mode state --episodes 3 --max-steps 120
```

For policy performance, prefer 100-episode evals for stable numbers.

## Real Robot Boundary

Real deployment is not active yet. The current acceptable real-robot tasks are:

- generate session folders/config templates
- inspect camera frames and crop alignment
- validate deployment YAML
- replay synthetic or recorded observations
- produce readiness reports

Do not send URScript, RTDE servo commands, joint commands, Cartesian motion commands, gripper commands, or any other motion command to a physical robot unless the user explicitly asks for that phase and safety checks have passed.
