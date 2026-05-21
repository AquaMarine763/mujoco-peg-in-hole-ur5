# Agent Working Notes

Last updated: 2026-05-19

This file records the standing workflow, user preferences, safety rules, and project constraints for future Codex work in this repository. Read this file before making non-trivial changes.

## Project Goal

Build a MuJoCo peg-in-hole reproduction inspired by `DRL_Peg-in-Hole_UR5`, then evolve it into a UR5e sim-to-real pipeline.

The current focus is:

- Keep the existing lightweight UR5e adapter training pipeline usable.
- Add and validate a full UR5e MuJoCo task model.
- Improve robustness with image observations, near-hole crop, domain randomization, guarded insertion, and staged geometry curriculum.
- Prepare real UR5e deployment in read-only / dry-run form before enabling any real robot motion.

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

- Repo root: `D:\peg-in-hole-6yh\mujoco_peg_in_hole`
- Current experimental branch: `feature/multi-geometry`
- Stabilized single-geometry baseline branch: `feature/control-state-observation`
- Remote: `https://github.com/AquaMarine763/mujoco-peg-in-hole-ur5.git`
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
  - Supported profiles are `single`, `round_square`, `square_square`, and `mixed_basic`.
  - Keep `single` as the default path unless an experiment explicitly overrides it.
  - The new branch is for geometry generalization experiments, not a replacement for the stabilized single-geometry controller work.
  - Expert/correction dataset collection and BC pretraining scripts accept the same geometry args.
  - Dataset files now record `geometry_profile`, `geometry_name`, `peg_shape`, and `hole_shape`; use those arrays to debug multi-geometry balance.
  - Current strictstable49 20ep profile check: `single=0.95`, `round_square=0.95`, `square_square=0.85`, `mixed_basic=0.95`, all with zero collisions. Treat `square_square` final insertion stability as the first multi-geometry bottleneck.
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
    - results are summarized in `VISUAL_AUDIT.md`; do not scale to 50k control-state data or promote stack3. DAgger v2 is promising but must pass larger evals before promotion
  - keep correction BC as a supporting dataset path, but do not expand to 10k until the controller issue is addressed
  - introduce larger randomized initial XY offsets only after original hard high-start search is stable
  - then reintroduce control/geometry/contact randomization

## Editing Workflow

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
