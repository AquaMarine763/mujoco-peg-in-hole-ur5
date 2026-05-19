# Project Plan And Status

Last updated: 2026-05-19

This file records the current project status, known metrics, and next planned steps. Keep it current when a milestone changes.

## Current Objective

The project is moving from a lightweight MuJoCo UR5e-like peg-in-hole environment toward a more faithful UR5e simulation and a cautious sim-to-real pipeline.

The current branch is now split into two tracks:

- `feature/control-state-observation`: the stabilized single-geometry high-start controller baseline.
- `feature/multi-geometry`: the new experimental branch for geometry generalization.

The immediate objective on `feature/multi-geometry` is to keep the single-geometry baseline intact while adding a conservative multi-geometry scaffold. The first stage is runtime geometry selection (`single`, `round_square`, `square_square`, `mixed_basic`) with no change to the default `single` path. The next stage is to evaluate whether the new geometry profile actually trains and evaluates cleanly before collecting any larger multi-geometry dataset.

## Current Branch And Remote

- Branch: `feature/multi-geometry`
- Remote: `https://github.com/AquaMarine763/mujoco-peg-in-hole-ur5.git`
- Latest local single-geometry milestone: `v0.6.50-single-geometry` / `4a0f65f Promote strict single-geometry high-start baseline`

## Multi-Geometry Branch Status

Implemented so far:

- `PegInHoleMujocoEnv` now accepts `geometry_profile`.
- The env can sample/apply `single`, `round_square`, `square_square`, and `mixed_basic`.
- Runtime peg geometry switching is working on the full UR5e XML.
- `scripts\train_sac.py`, `scripts\demo_policy.py`, `scripts\eval_guarded_policy.py`, and `scripts\run_policy_inference.py` accept the new geometry args.
- Smoke config:
  - `configs\sim\ur5e_full\eval_multi_geometry_smoke.yaml`
- Smoke result:
  - `mixed_basic` reset/eval smoke passed on seed `612000`
  - sampled geometry: `square_square`
  - `1/1` success on the 1-episode guarded smoke
  - this confirms runtime peg shape switching is working on the full UR5e XML

Next step:

- Run a small multi-geometry matrix and check whether `square_square` stays stable across more than one seed.
- If that stays stable, add a small multi-geometry training/eval matrix before any larger dataset collection.

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
6. Start multi-geometry only after the low-Z recenter and near-hole timeout cases stop looking like control-layer issues.

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
