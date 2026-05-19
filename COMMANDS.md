# Commands

This file keeps the current recommended commands in one place. Run commands
from the repository root:

```powershell
cd D:\peg-in-hole-6yh\mujoco_peg_in_hole
```

## Install

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Quick Checks

State observation smoke test:

```powershell
python scripts\random_rollout.py --observation-mode state --episodes 3
```

Image observation smoke test:

```powershell
python scripts\random_rollout.py --observation-mode image --episodes 1
```

Current strongest randomized environment smoke test:

```powershell
python scripts\random_rollout.py --observation-mode state --episodes 1 --domain-randomization-level full_contact_light
```

## Multi-Geometry Smoke

The `feature/multi-geometry` branch keeps `geometry_profile=single` as the
default. Use these checks to verify the experimental geometry scaffold.

Direct environment reset with mixed geometry:

```powershell
python -c "from peg_in_hole_mujoco import PegInHoleMujocoEnv; env=PegInHoleMujocoEnv(model_path='assets/ur5e_full/ur5e_peg_in_hole_full.xml', geometry_profile='mixed_basic', domain_randomization_level='full_light_geometry'); obs, info = env.reset(seed=1); print(info['geometry_profile'], info['geometry_name'], info['peg_shape'], info['hole_shape'], info['hole_half_size'], info['peg_radius'], info['hole_clearance']); env.close()"
```

Force the square-peg/square-hole profile:

```powershell
python -c "from peg_in_hole_mujoco import PegInHoleMujocoEnv; env=PegInHoleMujocoEnv(model_path='assets/ur5e_full/ur5e_peg_in_hole_full.xml', geometry_profile='square_square'); obs, info = env.reset(seed=2); print(info['geometry_name'], info['peg_shape'], info['peg_half_extents']); env.close()"
```

Guarded policy smoke on the experimental mixed profile:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_multi_geometry_smoke.yaml
```

## Robot Model Compatibility / UR5e Adapter

On the `feature/ur5e-mainline` branch, the default simulator uses the
lightweight UR5e adapter at `assets\ur5e_adapter\ur5e_peg_in_hole.xml`. It is
derived from the DeepMind MuJoCo Menagerie UR5e model and keeps the UR5e joint
chain, inertials, actuator style, and simplified collision geoms without
vendoring large visual mesh assets. The older simplified UR5-like model remains
available at `assets\ur5_peg_in_hole.xml` for regression checks.

Check that the default model exposes the task interface names used by the
environment:

```powershell
python scripts\inspect_robot_model.py --output-md results\ur5e\mainline\robot_model_default_ur5e.md --fail-on-missing
```

Check the legacy UR5-like model explicitly:

```powershell
python scripts\inspect_robot_model.py --model-path assets\ur5_peg_in_hole.xml --output-md results\ur5e\mainline\robot_model_legacy_ur5_like.md --fail-on-missing
```

Smoke-test the default UR5e adapter through reset, IK, stepping, and rendering.
Random actions are not expected to succeed; use the oracle command to verify
that the model can complete the task:

```powershell
python scripts\random_rollout.py --observation-mode state --episodes 1
python scripts\random_rollout.py --observation-mode image --episodes 1
python scripts\oracle_rollout.py --observation-mode state --episodes 3
```

All main environment scripts still accept an explicit model override:

```powershell
--model-path assets\ur5_peg_in_hole.xml
```

Use the full UR5e model when demo rendering should show the actual UR5e mesh
and Menagerie collision/inertial model. The branch default remains the lighter
adapter so older training/evaluation numbers stay comparable:

```powershell
python scripts\inspect_robot_model.py `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --output-md results\robot_model_ur5e_full.md `
  --output-json results\robot_model_ur5e_full.json `
  --fail-on-missing

python scripts\oracle_rollout.py `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --observation-mode state `
  --episodes 3 `
  --max-steps 120

python scripts\audit_ur5e_full_model.py `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --reference-model-path ..\_menagerie_ur5e.xml `
  --output-md results\ur5e_full\model_audit\ur5e_full_menagerie_audit.md `
  --output-json results\ur5e_full\model_audit\ur5e_full_menagerie_audit.json

python scripts\demo_policy.py `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --observation-mode image `
  --include-near-hole-crop `
  --episodes 1 `
  --max-steps 12 `
  --output results\ur5e_full_demo.gif `
  --render-width 1280 `
  --render-height 720 `
  --render-camera overview
```

Full UR5e short commands are also available through config files:

```powershell
python scripts\eval_matrix.py --config configs\sim\ur5e_full\eval_image_crop.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_guarded_image_crop.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_guarded_image_crop.yaml
```

Full UR5e low-level controller diagnostics:

```powershell
python scripts\diagnose_ur5e_controller.py --episodes 3

python scripts\diagnose_near_contact_tracking.py `
  --ik-control-modes pose `
  --ik-orientation-weight 0.03 `
  --ik-max-iterations 64 `
  --actuator-kp-multipliers 2.0 `
  --joint-damping-multipliers 1.0 `
  --output-csv results\ur5e_full\controller_diagnostics\near_contact_recenter_pose_003_064_kp2_rows.csv `
  --output-md results\ur5e_full\controller_diagnostics\near_contact_recenter_pose_003_064_kp2_summary.md
```

Focused static controller-response scan. This is diagnostic only; the first
scan showed global Kp3 improves low-Z probe response but regresses closed-loop
hard-bucket success, so do not promote it without a new gate result:

```powershell
python scripts\scan_near_contact_controller_response.py `
  --ik-control-modes pose `
  --ik-orientation-weights 0.0 0.01 0.02 0.03 `
  --ik-max-iterations-list 64 96 `
  --ik-step-limits 0.06 `
  --frame-skips 10 `
  --actuator-kp-multipliers 2.0 3.0 `
  --joint-damping-multipliers 1.0 `
  --xy-offsets-mm 6 10 20 `
  --z-above-mm 8 15 30 `
  --angles-deg 0 90 180 270 `
  --recenter-steps 12 `
  --output-csv results\ur5e_full\controller_diagnostics\near_contact_controller_response_scan_wori_kp.csv `
  --output-md results\ur5e_full\controller_diagnostics\near_contact_controller_response_scan_wori_kp.md
```

Closed-loop Kp comparison for the current hard-bucket controller:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori003_it64_kp2_hard_60ep.yaml `
  --episodes 20 `
  --nominal-actuator-kp-multiplier 2.0 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_hard_20ep_retest_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_hard_20ep_retest_seed602000.md
```

Local near-hole Kp recovery candidate. This keeps global nominal Kp at `2.0`
and boosts to Kp3 only while stateful recovery/final-servo/near-hole guarded
control is active. The current preset also applies a small final-servo descend
bias only after stateful recovery in tight-clearance cases:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_localkp3_recovery_20ep.yaml

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_localkp3_recovery_20ep.yaml `
  --episodes 60 `
  --output-csv results\ur5e_full\high_start\hard\recovery\eval_doublegate_bias_hard_60ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\recovery\eval_doublegate_bias_hard_60ep_seed602000.md `
  --episode-output-csv results\ur5e_full\high_start\hard\recovery\eval_doublegate_bias_hard_episodes_60ep_seed602000.csv `
  --step-output-csv results\ur5e_full\high_start\hard\recovery\eval_doublegate_bias_hard_failure_step_trace_60ep_seed602000.csv `
  --step-trace-outcome-filter failure
```

Current result: hard bucket seed `602000` reached `1.000/0.000/0.000` over
20 episodes and `0.950/0.000/0.050` over 60 episodes. The remaining 60ep
failures are high approach plateaus (`602024/602033/602048`) with no final-servo
entry, so the next work is approach-to-hole recovery rather than near-hole
insertion recovery.

Experimental approach + low-recenter diagnostic for one hard seed. This is not
promoted; use it to inspect the current 6 mm residual failure mode:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_localkp3_recovery_20ep.yaml `
  --episodes 1 `
  --seed 602024 `
  --guard-stateful-recovery-max-steps 80 `
  --guard-approach-recenter-trigger-xy 0.015 `
  --guard-approach-recenter-stable-xy 0.014 `
  --guard-approach-recenter-height 0.070 `
  --guard-approach-recenter-max-xy-action 0.008 `
  --guard-approach-recenter-xy-bias 0.0 0.0 `
  --guard-final-servo-start-xy 0.014 `
  --guard-final-servo-start-z 0.070 `
  --guard-final-servo-stable-xy 0.00625 `
  --guard-final-servo-descent-start-xy 0.014 `
  --guard-final-servo-release-xy 0.014 `
  --guard-final-servo-max-xy-action 0.008 `
  --guard-final-servo-max-down-action 0.0015 `
  --guard-final-servo-low-recenter-enabled `
  --guard-final-servo-low-recenter-z-max 0.025 `
  --guard-final-servo-low-recenter-trigger-xy 0.0068 `
  --guard-final-servo-low-recenter-release-xy 0.0061 `
  --guard-final-servo-low-recenter-height 0.018 `
  --guard-final-servo-low-recenter-stable-steps 1 `
  --guard-final-servo-low-recenter-max-steps 500 `
  --guard-final-servo-low-recenter-max-up-action 0.005 `
  --guard-final-servo-descend-xy-bias 0.0 -0.005 `
  --guard-final-servo-descend-xy-bias-max-clearance 0.010 `
  --guard-final-servo-stall-steps 25 `
  --guard-final-servo-max-retries 2 `
  --guard-final-servo-max-recovery-steps 320 `
  --guard-final-servo-recovery-mode lift_recenter `
  --guard-final-servo-lift-height 0.020 `
  --output-csv results\tmp_lowrec_hyst_state80_seed602024.csv `
  --output-md results\tmp_lowrec_hyst_state80_seed602024.md `
  --episode-output-csv results\tmp_lowrec_hyst_state80_seed602024_episodes.csv `
  --step-output-csv results\tmp_lowrec_hyst_state80_seed602024_steps.csv `
  --step-trace-outcome-filter any
```

The diagnostic compares the default position-only IK against the experimental
pose IK. It first places the peg tip near the hole with `ik_settle`, then
probes low-Z `+X/-X/+Y/-Y` tracking. Outputs:

```text
results\ur5e_full\controller_diagnostics\ur5e_controller_direction_rows.csv
results\ur5e_full\controller_diagnostics\ur5e_controller_summary.md
```

Phase-local IK orientation relaxation candidate. This keeps nominal pose IK
orientation weight at `0.03` during the high-start approach, but switches to
`0.0` only inside stateful recovery / approach recenter / final-servo / near-hole
guarded control. Latest 40ep hard-bucket gate on seed `602020` reached
`0.950/0.000/0.050`; remaining failures were `602038` and `602048` timeouts:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_localkp3_recovery_20ep.yaml `
  --episodes 40 `
  --seed 602020 `
  --ik-orientation-weight 0.03 `
  --guard-near-ik-orientation-weight 0.0 `
  --guard-stateful-recovery-max-steps 80 `
  --guard-approach-recenter-trigger-xy 0.015 `
  --guard-approach-recenter-stable-xy 0.014 `
  --guard-approach-recenter-height 0.070 `
  --guard-approach-recenter-max-xy-action 0.008 `
  --guard-approach-recenter-xy-bias 0.0 0.0 `
  --guard-final-servo-start-xy 0.014 `
  --guard-final-servo-start-z 0.070 `
  --guard-final-servo-stable-xy 0.00625 `
  --guard-final-servo-descent-start-xy 0.014 `
  --guard-final-servo-release-xy 0.014 `
  --guard-final-servo-max-xy-action 0.008 `
  --guard-final-servo-max-down-action 0.0015 `
  --guard-final-servo-low-recenter-enabled `
  --guard-final-servo-low-recenter-z-max 0.025 `
  --guard-final-servo-low-recenter-trigger-xy 0.0065 `
  --guard-final-servo-low-recenter-release-xy 0.0049 `
  --guard-final-servo-low-recenter-height 0.018 `
  --guard-final-servo-low-recenter-stable-steps 1 `
  --guard-final-servo-low-recenter-max-steps 500 `
  --guard-final-servo-low-recenter-max-up-action 0.005 `
  --guard-final-servo-low-recenter-stall-steps 0 `
  --guard-final-servo-descend-xy-bias 0.0 -0.005 `
  --guard-final-servo-descend-xy-bias-max-clearance 0.010 `
  --guard-final-servo-stall-steps 25 `
  --guard-final-servo-max-retries 2 `
  --guard-final-servo-max-recovery-steps 320 `
  --guard-final-servo-recovery-mode lift_recenter `
  --guard-final-servo-lift-height 0.020 `
  --output-csv results\ur5e_full\high_start\hard\recovery\eval_lowrec_near_wori000_40ep_seed602020.csv `
  --output-md results\ur5e_full\high_start\hard\recovery\eval_lowrec_near_wori000_40ep_seed602020.md `
  --episode-output-csv results\ur5e_full\high_start\hard\recovery\eval_lowrec_near_wori000_episodes_40ep_seed602020.csv `
  --step-output-csv results\ur5e_full\high_start\hard\recovery\eval_lowrec_near_wori000_failure_step_trace_40ep_seed602020.csv `
  --step-trace-outcome-filter failure
```

Current strict stable-XY 60ep gate. This is the best reproducible
single-geometry high-start hard recovery candidate as of 2026-05-19:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_localkp3_recovery_strictstable49_60ep.yaml
```

Checked result:

```text
results\ur5e_full\high_start\hard\recovery\eval_lowrec_near_wori000_strictstable49_60ep_seed602000.md
success/collision/timeout = 0.983/0.000/0.017
only remaining timeout = seed 602048
```

Notes:

- Tightening `guard_final_servo_stable_xy` to `0.0049` fixed the previous
  `602019/602038` near-miss timeout window.
- `602048` is a true final-insertion stability residual: low-recenter is active
  but stalls near `5.7 mm` XY and `16.5 mm` Z. Plateau-triggered lift-recenter,
  `guard_action_gain=2.0`, no descent bias, and near-hole orientation weight
  `0.01` were tested as one-seed probes but are not promoted.

Use pose IK in guarded evaluation or demos with:

```powershell
--ik-control-mode pose `
--ik-orientation-weight 0.03 `
--ik-posture-weight 0.01 `
--ik-step-limit 0.06 `
--ik-max-iterations 64 `
--nominal-actuator-kp-multiplier 2.0
```

Current pose-IK hard-bucket check:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_20ep.yaml `
  --ik-control-mode pose `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_pose_ik_20ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_pose_ik_20ep_seed602000.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_pose_ik_episodes_20ep_seed602000.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_pose_ik_failure_step_trace_20ep_seed602000.csv
```

Current pose-IK 60ep gate:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_hard_60ep.yaml
```

Position-IK 60ep comparison:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_hard_60ep.yaml --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_hard_60ep_position_seed602000.csv --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_hard_60ep_position_seed602000.md
```

Current pose-IK 100ep matrix:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_matrix_100ep.yaml
```

Position-IK 100ep matrix comparison:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_matrix_100ep.yaml --ik-control-mode position --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_position_ik_matrix_100ep_seed602000.csv --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_position_ik_matrix_100ep_seed602000.md
```

Pose-IK tail correction collection and weighted BC:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_near_hole_pose_ik_2k.yaml
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_fixture_wall_pose_ik_2k.yaml
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_pose_ik_tail_2k_w10_e1.yaml
```

The expected output checkpoint for this pass is:

```text
checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_pose_ik_tail_2k_w10_e1.zip
```

Post-retrain evaluation:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_pose_ik_tail_2k_w10_e1_final_servo_pose_ik_hard_60ep.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_pose_ik_tail_2k_w10_e1_final_servo_pose_ik_matrix_100ep.yaml
```

Current full UR5e task geometry hides the debug `hole_site`, `eef_site`, and
`peg_tip` markers in rendered demos. The peg diameter is about `24 mm`; the
base hole opening is about `40 mm`; geometry-randomized full UR5e configs use
`geometry_hole_half_size_range: [0.017, 0.021]`, i.e. about `34 - 42 mm`
opening. Metrics collected before this change used a wider hole and should be
refreshed before comparison. The main guarded full UR5e demo now uses
`max_steps: 400` so it has time to show the final insertion instead of ending
mid-descent. Full UR5e guarded configs now use
`guarded_align_xy_tolerance: 0.020`, selected from a 30-episode narrow-hole
scan.

Full UR5e visual-adaptation smoke and 50k commands:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_image_expert_smoke.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_image_bc_smoke.yaml
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_image_expert_50k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_image_bc_50k.yaml
```

Current strongest full UR5e adapted commands:

```powershell
python scripts\eval_matrix.py --config configs\sim\ur5e_full\eval_image_narrow_50k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_guarded_narrow_50k_all.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_guarded_narrow_50k_all.yaml
```

Full UR5e narrowed-hole correction pass:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_correction_narrow_smoke.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_smoke.npz `
  --output-md results\ur5e_full\correction\image_correction_narrow_smoke_inspection.md `
  --output-csv results\ur5e_full\correction\image_correction_narrow_smoke_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_correction_narrow_smoke.yaml

python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_correction_narrow_8k.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_8k_min006.npz `
  --output-md results\ur5e_full\correction\image_correction_narrow_8k_inspection.md `
  --output-csv results\ur5e_full\correction\image_correction_narrow_8k_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_correction_narrow_8k_w10_e2.yaml
python scripts\eval_matrix.py --config configs\sim\ur5e_full\eval_image_narrow_correction_8k_w10_e2.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_guarded_narrow_correction_8k_w10_e2.yaml
```

The latest correction checkpoint is:

```text
checkpoints\ur5e_full\correction\sac_image_bc_50k_narrow_correction_8k_w10_e2.zip
```

It is a candidate checkpoint, not the current default, because its 100-episode
results were mostly flat versus the narrowed-hole adapted checkpoint.

Full UR5e narrow-hole guarded scans:

```powershell
python scripts\scan_guarded_policy_params.py --config configs\sim\ur5e_full\scan_guarded_narrow_hole_smoke.yaml
python scripts\scan_guarded_policy_params.py --config configs\sim\ur5e_full\scan_guarded_narrow_hole_focused.yaml
```

Full UR5e high-start visual-search smoke:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_smoke.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_smoke.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_guarded_smoke.yaml
```

Full UR5e high-start 50k curriculum stage:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_50k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_50k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_guarded_50k.yaml
```

The first 50k high-start run completed end to end but is not yet strong enough
to become the default policy. The checkpoint is:

```text
checkpoints\ur5e_full\high_start\sac_image_bc_50k_high_start_visual_camera.zip
```

Collection summary: `50000` samples from `225` successful episodes out of
`1044` attempted episodes, `0.216` oracle success, `0.552` collision. BC
summary: 10 epochs, final train loss `0.062912`, final validation loss
`0.066407`.

100-episode high-start guarded-all result with standard near-hole guard:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| high-start 50k guarded all | 0.190 | 0.240 | 0.180 | 0.170 | 0.220 | 0.150 |

The high-start demo from `demo_high_start_guarded_50k.yaml` timed out at
`1000` steps with final XY about `8.8 mm` and final Z about `47.6 mm`, so this
stage needs an easier curriculum or better high-start oracle before larger XY
randomization.

Full UR5e easy high-start curriculum:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_easy_smoke.yaml
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_easy_20k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_easy_20k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_easy_guarded_20k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_easy_guarded_20k.yaml

python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_easy_50k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_easy_50k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_easy_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_easy_guarded_50k.yaml
```

Current easy high-start checkpoint:

```text
checkpoints\ur5e_full\high_start\easy\sac_image_bc_50k_high_start_easy_visual_camera.zip
```

Easy reset range: `0.08 - 0.15 m` above the hole and `0.04 - 0.10 m` initial
XY offset. Easy 50k collection summary: `50000` samples, `377` episodes,
`0.647` oracle success, `0.119` collision. BC summary: 10 epochs, final train
loss `0.061749`, final validation loss `0.061968`.

Easy 50k 100-episode high-start guarded-all result:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| seed 542000 | 0.670 | 0.540 | 0.500 | 0.530 | 0.530 | 0.530 |
| seed 534000 | 0.620 | 0.630 | 0.590 | 0.580 | 0.540 | 0.480 |

Successful easy 50k demo:

```text
demos\ur5e_full\high_start\easy\demo_high_start_easy_50k_visual_camera_standard_guard_seed534000.gif
```

It inserted in `247` steps from about `6.9 cm` XY offset and `12.0 cm` above
the hole. The default demo seed `542000` timed out, so this checkpoint is a
curriculum stepping stone rather than a final high-start policy.

Full UR5e medium high-start curriculum:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_medium_smoke.yaml
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_medium_20k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_medium_20k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_medium_guarded_20k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_medium_guarded_20k.yaml

python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_medium_50k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_medium_50k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_medium_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_medium_guarded_50k.yaml
```

Current medium high-start checkpoint:

```text
checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip
```

Medium reset range: `0.10 - 0.18 m` above the hole and `0.06 - 0.12 m`
initial XY offset. Medium 50k collection summary: `50000` samples, `287`
episodes, `0.627` oracle success, `0.087` collision. BC summary: 10 epochs,
final train loss `0.045268`, final validation loss `0.044958`.

Medium 50k 100-episode high-start guarded-all result:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| medium 50k | 0.680 | 0.620 | 0.510 | 0.510 | 0.510 | 0.490 |

Successful medium 50k demo:

```text
demos\ur5e_full\high_start\medium\demo_high_start_medium_50k_visual_camera_standard_guard.gif
```

It inserted in `285` steps from about `8.65 cm` XY offset and `11.25 cm`
above the hole.

Full UR5e hard high-start re-test and safe-height curriculum:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_from_medium_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_from_medium_guarded_50k.yaml

python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_safe_smoke.yaml
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_safe_20k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_hard_safe_20k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_safe_20k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_safe_20k.yaml

python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_safe_50k.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_hard_safe_50k.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_safe_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_safe_50k.yaml
```

Current hard-range candidate:

```text
checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip
```

Hard range: `0.15 - 0.25 m` above the hole and `0.08 - 0.16 m` initial XY
offset. Hard-safe uses `approach_height: 0.12` and `guard_start_z: 0.12`.

Hard-safe 20k result:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hard-safe 20k | 0.480 | 0.400 | 0.340 | 0.350 | 0.390 | 0.240 |

Hard-safe 50k result:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hard-safe 50k | 0.480 | 0.450 | 0.330 | 0.270 | 0.310 | 0.330 |

Successful hard demos:

```text
demos\ur5e_full\high_start\hard\demo_high_start_hard_from_medium_50k_standard_guard.gif
demos\ur5e_full\high_start\hard\demo_high_start_hard_safe_20k_visual_camera_standard_guard.gif
demos\ur5e_full\high_start\hard\demo_high_start_hard_safe_50k_visual_camera_standard_guard.gif
```

Hard-safe 50k did not clearly beat hard-safe 20k, so the next work should
improve the high-start controller/oracle and collect failure/correction data
instead of continuing to add more success-only hard data.

Two-phase hard high-start controller checks:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_twophase_smoke.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_twophase_hard_safe_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_twophase_hard_safe_50k.yaml
```

This uses `oracle_mode: high_start_two_phase` for collection and
`guarded_oracle_mode: high_start_two_phase` plus
`guard_block_down_when_unaligned: true` for guarded evaluation/demo. The first
100-episode result was mixed:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hard-safe 50k + two-phase guard | 0.490 | 0.340 | 0.320 | 0.350 | 0.350 | 0.270 |

It reduced some collision risk but increased timeout, so this should be tuned
before use as a default.

Hard high-start guard parameter scan and focused validation:

```powershell
python scripts\scan_guarded_policy_params.py --config configs\sim\ur5e_full\scan_high_start_hard_twophase_guarded_smoke.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_align025_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_align025_guarded_50k.yaml
```

The scan compares `guarded_two_stage` vs `high_start_two_phase`, align
thresholds `0.020/0.025/0.030`, and block-down false/true on the hard
high-start reset. The 5-episode smoke did not find a clear two-phase or
block-down improvement. The focused `align=0.025`, `guarded_two_stage`
100-episode result was:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hard-safe 50k + align 0.025 guard | 0.530 | 0.370 | 0.310 | 0.340 | 0.290 | 0.270 |

The corresponding demo timed out at `1000` steps with no collision, final XY
about `8.4 mm`, and final Z about `32.8 mm`. This is not a promoted default;
it points to near-hole plateau correction as the next step.

Hard high-start correction smoke:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_correction_smoke.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_near_hole_plateau_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_smoke_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_correction_smoke.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_correction_smoke.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_correction_smoke.yaml
```

The smoke collected `256` near-hole failure samples from `29` visual_camera
hard high-start episodes. It is high-signal data: `72.3%` opposed actions and
`86.7%` policy-down/oracle-up-or-less-down. The 1-epoch weighted BC smoke is
not a default checkpoint; same-seed 20-episode evaluation was mixed and the
demo still timed out near `8.4 mm` XY error.

Hard high-start correction 2k pass:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_correction_2k.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_near_hole_plateau_2k.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_2k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_2k_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_correction_2k_w05_e2.yaml
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_correction_2k_w10_e2.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_correction_2k_w05_e2.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_correction_2k_w10_e2.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_correction_2k_w10_e2.yaml
```

The 2k dataset balances `1000` visual_camera and `1000` visual_camera_control
samples. It keeps strong correction signal: `74.9%` opposed actions and
`86.8%` policy-down/oracle-up. In same-seed 20-episode eval, 5% replay was
effectively baseline, while 10% replay only improved hard bucket from `0.35`
to `0.40` and reduced hard-bucket collision from `0.45` to `0.35`. The demo
still timed out near `8.4 mm` XY error, so this is not a promoted checkpoint.

Hard high-start guarded retry prototype:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_retry_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_retry_guarded_50k.yaml
```

This adds deployment-time retry diagnostics and a bounded re-align/retry state
machine. It is not promoted: same-seed 20-episode evaluation was mostly worse
than the hard-safe 50k baseline (`clean 0.300`, `visual_camera 0.150`,
`visual_camera_control 0.250`, `full_light_geometry 0.250`,
`full_contact_light 0.250`, `hard_full_light_bucket 0.300`). The demo still
timed out near `8.4 mm` XY error. Treat this as evidence that the next fix
should be guarded oracle / IK near-hole alignment behavior, not more retry
attempts with the current controller.

Hard high-start no-prediction guarded controller:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_pred0_guarded_50k.yaml
```

This is the strongest current controller-only improvement for the hard
high-start checkpoint. It keeps `guarded_two_stage` but sets
`guarded_prediction_steps: 0.0`, avoiding the old one-step prediction that
could falsely assume the peg had already entered the `5 mm` insert band. In
same-seed 100-episode evaluation it improved success to clean `0.560`,
visual_camera `0.500`, visual_camera_control `0.530`, full_light_geometry
`0.450`, full_contact_light `0.380`, hard bucket `0.430`. The demo seed
`571001` inserts in `411` steps. Seed `571000` remains a useful failure case.

Hard high-start strict-align hold-Z check:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_strict_align_guarded_50k.yaml
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_strict_align_guarded_50k.yaml
```

`guarded_hold_z_until_insert: true` alone was not enough. With the old
prediction setting it still timed out near `8.4 mm`; with prediction disabled
it can enter the `5 mm` band but tends to oscillate if XY drifts back out
during descent. Keep it as diagnostic evidence, not as the default.

Hard high-start insert latch / descent hysteresis diagnostic:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_pred0_latch_guarded_50k.yaml --hard-bucket-only --episodes 10
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_pred0_latch_guarded_50k.yaml
```

This is experimental only. It adds a stateful latch after the peg enters the
`5 mm` insert band, pauses descent when XY drifts back out, and can run a
two-stage recenter attempt that lifts before lateral re-alignment. The current
hard-bucket smoke is not good enough to promote: `10` episodes, success
`0.400`, collision `0.500`, timeout `0.100`. The hard seed `571000` still
fails, and diagnostics show the peg becomes wedged inside the hole-wall height
range where physical tracking is extremely slow. The next learning step should
be contact-aware failure correction / DAgger, not more latch threshold tuning.

Hard high-start Track A hover / descent-gate diagnostic:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_pred0_hover_guarded_50k.yaml --hard-bucket-only --episodes 10
python scripts\demo_policy.py --config configs\sim\ur5e_full\demo_high_start_hard_pred0_hover_guarded_50k.yaml
```

This is also experimental only. It adds near-hole hover alignment, stateful
descent release, descent blocking when XY drifts out, and near-hole action
limiting. Same-seed 10-episode hard-bucket smoke was flat versus pred0 guarded
baseline: both reached success `0.400`, collision `0.500`, timeout `0.100`.
Seed `571000` now latches and starts descent near `3.8 mm` XY, but still
wedges around `5.1 - 5.3 mm` and times out. Treat this as support for the next
Track B step: contact-aware unjam / DAgger labels.

Hard high-start Track B contact-aware correction smoke:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_contact_recovery_smoke.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_smoke_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_smoke_w10_e1.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_smoke_w10_e1.yaml --hard-bucket-only --episodes 10
```

This smoke verifies the Track B label path. The dataset has `256` samples, all
from near-hole timeout windows. It is deliberately strong: `oracle_lift_action`
rate is `1.000`, `opposed_actions` is `0.953`, and every sample is labeled as
`unjam_lift`. The 10% replay / 1 epoch checkpoint is not promoted: hard-bucket
10-episode success stayed flat at `0.400`. The next Track B data pass should
include three phases: low-Z `unjam_lift`, lifted `realign`, and aligned
`slow_insert`.

Hard high-start Track B staged correction smoke:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_contact_recovery_staged_smoke.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_smoke_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_staged_smoke_w15_e1.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_staged_smoke_w15_e1.yaml --hard-bucket-only --episodes 10
```

This is the current Track B data-pipeline smoke. It adds branch rollouts from
failed low-Z states plus synthetic recovery curriculum states. Latest staged
smoke phase counts: `unjam_lift=410`, `realign=49`, `slow_insert=53`. The
staged smoke checkpoint is not promoted: hard-bucket 10-episode success
remained `0.400`, and seed `571000` collided. Scale staged data cautiously
with lower replay weight before treating it as a training candidate.

Hard high-start Track B staged correction 2k pass:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_contact_recovery_staged_2k.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_2k.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_2k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_contact_recovery_staged_2k_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_staged_2k_w05_e2.yaml
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_staged_2k_w10_e2.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_staged_2k_w05_e2.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_staged_2k_w10_e2.yaml
```

Use this as the next Track B scale-up, not as a promoted model. The first
acceptance check is a same-seed 20-episode matrix: success must beat the
current pred0 guarded baseline or clearly lower hard-bucket collisions without
hurting clean/visual_camera too much.

Checked staged 2k pass:

- dataset: `2048` samples, balanced as `1024` visual_camera and `1024`
  visual_camera_control
- recovery branch rate: `0.521`
- synthetic recovery state rate: `0.167`
- phase counts: `unjam_lift=1674`, `realign=172`, `slow_insert=202`

Same-seed 20-episode guarded eval:

| Checkpoint | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| staged 2k w05 e2 | 0.550 | 0.500 | 0.500 | 0.400 | 0.350 | 0.450 |
| staged 2k w10 e2 | 0.550 | 0.550 | 0.500 | 0.400 | 0.350 | 0.450 |

The staged 2k checkpoints are not promoted. They give only a small hard-bucket
signal, and the known hard seed `571000` still collides with the 10% replay
checkpoint. Next Track B work should rebalance or oversample `realign` and
`slow_insert` labels before scaling to a larger dataset.

Hard high-start Track B phase-balanced staged correction:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_staged_2k_phase_w10_e2.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_staged_2k_phase_w10_e2.yaml
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_staged_2k_phase_w10_e2.yaml `
  --hard-bucket-only `
  --episodes 1 `
  --seed 571000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_high_start_hard_contact_recovery_staged_2k_phase_w10_e2_seed571000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_high_start_hard_contact_recovery_staged_2k_phase_w10_e2_seed571000.md
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_contact_recovery_staged_2k_phase_w15_e2.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_contact_recovery_staged_2k_phase_w15_e2.yaml
```

This keeps the staged 2k dataset fixed but changes correction sampling. Inside
the correction dataset, batches use `unjam_lift/realign/slow_insert =
0.30/0.35/0.35` instead of the raw dataset ratio `1674/172/202`.

Same-seed 20-episode guarded eval:

| Checkpoint | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| staged 2k w10 e2 | 0.550 | 0.550 | 0.500 | 0.400 | 0.350 | 0.450 |
| phase staged 2k w10 e2 | 0.550 | 0.550 | 0.500 | 0.350 | 0.350 | 0.500 |
| phase staged 2k w15 e2 | 0.550 | 0.550 | 0.500 | 0.350 | 0.350 | 0.450 |

The phase-balanced w10 checkpoint is the best Track B signal so far, but it is
not promoted: `full_light_geometry` drops to `0.350`, and hard seed `571000`
still collides. The w15 run regressed, so the next step is better
failure-state coverage or a guarded recovery gate, not higher correction
weight.

Hard-bucket v3 timeout trace diagnosis:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1.yaml `
  --hard-bucket-only `
  --episodes 60 `
  --seed 604000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_step_trace_60ep_seed604k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_step_trace_60ep_seed604k.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_episode_trace_60ep_seed604k.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_step_trace_timeout_60ep_seed604k.csv `
  --step-trace-outcome-filter timeout
```

This is the current diagnostic for the v3 hard-bucket timeout bottleneck. The
seed `604000` 60-episode run produced success/collision/timeout
`0.383/0.133/0.483`; `22/29` timeout episodes entered the strict `5 mm` XY
band at least once. Soft latch, faster latch, `guarded_insert_xy_tolerance:
0.008`, contact-aware deployment guard, policy-only, and `guard_blend: 0.75`
did not improve the same seed window. See:

```text
results\ur5e_full\high_start\hard\correction\hard_bucket_timeout_trace_v3_summary.md
```

Hard-bucket timeout-progress v4 smoke:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_timeout_progress_v4_smoke.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_timeout_progress_v4_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_timeout_progress_v4_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_timeout_progress_v4_smoke_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_timeout_progress_v4_smoke_w10_e1.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_timeout_progress_v4_smoke_w10_e1.yaml
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_timeout_progress_v4_smoke_w03_e1.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_timeout_progress_v4_smoke_w03_e1.yaml
```

This v4 smoke is not promoted. The dataset correctly captures timeout-progress
states (`512` samples, all timeout, all near-hole, `oracle_down_action=1.000`,
`oracle_lift_action=0.000`), but progress-only labels are unsafe: on seed
`622000`, v3 e1 hard bucket was `0.500/0.150/0.350`, v4 w10 became
`0.250/0.550/0.200`, and v4 w03 became `0.400/0.300/0.300`. It reduces timeout
mostly by increasing collision. See:

```text
results\ur5e_full\high_start\hard\correction\timeout_progress_v4_smoke_summary.md
```

Hard high-start visual contribution audit:

```powershell
$base = 'configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml'
python scripts\eval_guarded_policy.py --config $base --hard-bucket-only --episodes 10 --control-mode policy --image-ablation normal --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_policy_normal_10ep.csv --output-md results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_policy_normal_10ep.md
python scripts\eval_guarded_policy.py --config $base --hard-bucket-only --episodes 10 --control-mode policy --image-ablation black --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_policy_black_10ep.csv --output-md results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_policy_black_10ep.md
python scripts\eval_guarded_policy.py --config $base --hard-bucket-only --episodes 10 --control-mode policy --image-ablation noise --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_policy_noise_10ep.csv --output-md results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_policy_noise_10ep.md
python scripts\eval_guarded_policy.py --config $base --hard-bucket-only --episodes 10 --control-mode policy --image-ablation shuffle --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_policy_shuffle_10ep.csv --output-md results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_policy_shuffle_10ep.md
python scripts\eval_guarded_policy.py --config $base --hard-bucket-only --episodes 10 --control-mode guarded --image-ablation normal --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_guarded_normal_10ep.csv --output-md results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_guarded_normal_10ep.md
python scripts\eval_guarded_policy.py --config $base --hard-bucket-only --episodes 10 --control-mode guarded --image-ablation black --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_guarded_black_10ep.csv --output-md results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_guarded_black_10ep.md
python scripts\eval_guarded_policy.py --config $base --hard-bucket-only --episodes 10 --control-mode guarded --image-ablation noise --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_guarded_noise_10ep.csv --output-md results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_guarded_noise_10ep.md
python scripts\eval_guarded_policy.py --config $base --hard-bucket-only --episodes 10 --control-mode guarded --image-ablation shuffle --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_guarded_shuffle_10ep.csv --output-md results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_guarded_shuffle_10ep.md
python scripts\eval_guarded_policy.py --config $base --hard-bucket-only --episodes 10 --control-mode guard_only --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_guard_only_10ep.csv --output-md results\ur5e_full\high_start\hard\visual_audit\eval_visual_audit_pred0_guard_only_10ep.md
```

Hard high-start key-frame visibility audit:

```powershell
$base = 'configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml'
python scripts\audit_visual_visibility.py `
  --config $base `
  --episodes 3 `
  --segmentation-stride 10 `
  --max-frames-per-episode 8 `
  --visibility-output-csv results\ur5e_full\high_start\hard\visual_audit\visibility_pred0_guarded_3ep.csv `
  --visibility-output-md results\ur5e_full\high_start\hard\visual_audit\visibility_pred0_guarded_3ep.md `
  --frame-dir results\ur5e_full\high_start\hard\visual_audit\frames_pred0_guarded_3ep
```

Hard high-start crop offset scan:

```powershell
$base = 'configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml'
python scripts\scan_visual_crop_offset.py `
  --config $base `
  --episodes 3 `
  --segmentation-stride 10 `
  --scan-x-offsets -32 -24 -18 -12 -6 0 6 12 `
  --scan-y-offsets -24 -16 -8 0 8 16 24 `
  --scan-output-csv results\ur5e_full\high_start\hard\visual_audit\crop_offset_scan_pred0_guarded_3ep.csv `
  --scan-output-md results\ur5e_full\high_start\hard\visual_audit\crop_offset_scan_pred0_guarded_3ep.md
```

The smoke audit is summarized in `VISUAL_AUDIT.md`. Main result: visual input
does matter, because policy-only normal image reached `0.100` while
black/noise/shuffle reached `0.000`, and guarded normal reached `0.400` while
guarded corrupted-image runs reached `0.100`. But the privileged guard/oracle
still contributes heavily: guard-only reached `0.500`.

The key-frame visibility audit shows why the next visual step should be
camera/crop work: hole center and peg tip project into the full wrist frame,
but the current center crop never contains both in the 3-episode hard smoke;
segmentation found hole geometry in the crop but no peg geometry in the crop.
The crop offset scan selected `near_hole_crop_offset: [-18, 0]` as the first
visibility candidate. This is a candidate for new data collection and
fine-tuning, not a setting to apply directly to the old center-crop checkpoint.

Shifted-crop smoke collection and fine-tuning:

```powershell
python scripts\collect_image_expert_dataset.py `
  --config configs\sim\ur5e_full\collect_high_start_hard_safe_50k.yaml `
  --samples 1024 `
  --output datasets\ur5e_full\high_start\hard\image_expert_1k_high_start_hard_safe_visual_camera_crop_left.npz `
  --near-hole-crop-offset -18 0

python scripts\pretrain_image_actor_bc.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_safe_50k.yaml `
  --dataset datasets\ur5e_full\high_start\hard\image_expert_1k_high_start_hard_safe_visual_camera_crop_left.npz `
  --output checkpoints\ur5e_full\high_start\hard\sac_image_bc_1k_high_start_hard_safe_visual_camera_crop_left.zip `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip `
  --epochs 2 `
  --near-hole-crop-offset -18 0
```

Conservative larger-data shifted-crop check:

```powershell
python scripts\collect_image_expert_dataset.py `
  --config configs\sim\ur5e_full\collect_high_start_hard_safe_50k.yaml `
  --samples 10000 `
  --output datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_safe_visual_camera_crop_left.npz `
  --near-hole-crop-offset -18 0

python scripts\pretrain_image_actor_bc.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_safe_50k.yaml `
  --dataset datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_safe_visual_camera_crop_left.npz `
  --output checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_safe_visual_camera_crop_left_lr3e6_e1.zip `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip `
  --epochs 1 `
  --learning-rate 0.000003 `
  --near-hole-crop-offset -18 0
```

Same-seed comparison/evaluation commands:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip `
  --episodes 10 `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_center_baseline_50k_10ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_center_baseline_50k_10ep.md

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_1k_high_start_hard_safe_visual_camera_crop_left.zip `
  --episodes 10 `
  --near-hole-crop-offset -18 0 `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_crop_left_1k_e2_10ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_crop_left_1k_e2_10ep.md

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_safe_visual_camera_crop_left_lr3e6_e1.zip `
  --episodes 10 `
  --near-hole-crop-offset -18 0 `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_crop_left_10k_lr3e6_e1_10ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_crop_left_10k_lr3e6_e1_10ep.md
```

Shifted-crop visibility audit after conservative fine-tune:

```powershell
python scripts\audit_visual_visibility.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_safe_visual_camera_crop_left_lr3e6_e1.zip `
  --episodes 2 `
  --near-hole-crop-offset -18 0 `
  --segmentation-stride 10 `
  --max-frames-per-episode 8 `
  --visibility-output-csv results\ur5e_full\high_start\hard\visual_audit\visibility_crop_left_10k_lr3e6_e1_2ep.csv `
  --visibility-output-md results\ur5e_full\high_start\hard\visual_audit\visibility_crop_left_10k_lr3e6_e1_2ep.md `
  --frame-dir results\ur5e_full\high_start\hard\visual_audit\frames_crop_left_10k_lr3e6_e1_2ep
```

Result: crop-left improves the geometric framing metric, but it is not a
better policy after short BC fine-tuning. Same-seed 10-episode guarded matrix:
center baseline reached clean `0.600`, visual_camera `0.700`,
visual_camera_control `0.500`, hard bucket `0.400`; the `1k` crop-left
fine-tune reached `0.500`, `0.400`, `0.300`, `0.300`; the conservative `10k`
crop-left fine-tune reached `0.500`, `0.400`, `0.100`, `0.200`. Keep the center
baseline for demos and use the crop result to motivate camera-pose / second-view
audits before collecting larger shifted-crop datasets.

Wrist camera pose / crop scan:

```powershell
python scripts\scan_wrist_camera_pose.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip `
  --episodes 3 `
  --sample-stride 10 `
  --scan-pos-x-offsets 0 `
  --scan-pos-y-offsets 0 `
  --scan-pos-z-offsets 0 `
  --scan-roll-deg 0 `
  --scan-pitch-deg -15 0 15 `
  --scan-yaw-deg -15 0 15 `
  --scan-fovy 90 100 120 `
  --scan-crop-x-offsets 0 -18 -24 `
  --scan-crop-y-offsets 0 `
  --scan-output-csv results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_rot_fov_crop_3ep.csv `
  --scan-output-md results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_rot_fov_crop_3ep.md
```

Position scan around the wrist camera mount:

```powershell
python scripts\scan_wrist_camera_pose.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_pred0_guarded_50k.yaml `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip `
  --episodes 3 `
  --sample-stride 10 `
  --scan-pos-x-offsets -0.04 0 0.04 `
  --scan-pos-y-offsets -0.04 0 0.04 `
  --scan-pos-z-offsets -0.04 0 0.04 `
  --scan-roll-deg 0 `
  --scan-pitch-deg 0 `
  --scan-yaw-deg 0 15 `
  --scan-fovy 100 `
  --scan-crop-x-offsets -18 `
  --scan-crop-y-offsets 0 `
  --save-candidate-ids 3 27 `
  --frame-dir results\ur5e_full\high_start\hard\visual_audit\frames_wrist_camera_pose_scan_pos_yaw_crop_3ep `
  --max-saved-frames-per-candidate 8 `
  --scan-output-csv results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_pos_yaw_crop_3ep.csv `
  --scan-output-md results\ur5e_full\high_start\hard\visual_audit\wrist_camera_pose_scan_pos_yaw_crop_3ep.md
```

Current result: rotation/FOV alone is weak, but moving the wrist camera local
position by `[-0.04,-0.04,0.00]` with crop `[-18,0]` reached sampled
insert-band and near-XY crop-visible rates of `1.000` in the 3-episode hard
visibility scan. This is a visibility candidate only; next training must collect
data with that camera pose instead of evaluating the old center-crop checkpoint
as if it were trained for the new camera.

Wrist camera pose smoke dataset/training/eval:

```powershell
python scripts\collect_image_expert_dataset.py `
  --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_smoke.yaml

python scripts\inspect_image_expert_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\image_expert_1k_high_start_hard_wrist_pose_visual_camera.npz `
  --output-md results\ur5e_full\high_start\hard\visual_audit\image_expert_1k_wrist_pose_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\image_expert_1k_wrist_pose_inspection.csv

python scripts\pretrain_image_actor_bc.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_smoke.yaml

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_smoke.yaml
```

Smoke result: the new camera config path works, but the 1k/2-epoch checkpoint is
not usable. Dataset collection had only `0.214` oracle success over `14`
episodes, and the guarded 10-episode eval reached clean `0.200`,
visual_camera `0.300`, visual_camera_control `0.100`, full_light_geometry
`0.200`, full_contact_light `0.100`, and hard bucket `0.000` with collision
`1.000`. Treat this as a wiring/feasibility check. The next real training run
needs a larger wrist-pose replay/scratch dataset, not another tiny fine-tune.

Wrist camera pose 10k scratch smoke:

```powershell
python scripts\collect_image_expert_dataset.py `
  --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_smoke.yaml `
  --samples 10000 `
  --seed 564000 `
  --output datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_wrist_pose_visual_camera_seed564k.npz

python scripts\inspect_image_expert_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_wrist_pose_visual_camera_seed564k.npz `
  --output-md results\ur5e_full\high_start\hard\visual_audit\image_expert_10k_wrist_pose_seed564k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\image_expert_10k_wrist_pose_seed564k_inspection.csv

python scripts\pretrain_image_actor_bc.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_10k_scratch.yaml

python scripts\pretrain_image_actor_bc.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_10k_scratch.yaml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_wrist_pose_visual_camera_scratch_e10.zip `
  --output checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_wrist_pose_visual_camera_scratch_e20.zip `
  --epochs 10 `
  --learning-rate 0.00005

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_10k_scratch.yaml

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_10k_scratch.yaml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_wrist_pose_visual_camera_scratch_e20.zip `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_10k_scratch_e20_10ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_10k_scratch_e20_10ep.md
```

Result: `10k` scratch is much better than the `1k` fine-tune, but still not
promoted. e20 reached clean `0.500`, visual_camera `0.500`,
visual_camera_control `0.400`, full_light_geometry `0.100`, full_contact_light
`0.400`, and hard bucket `0.300`. The next run should scale to about `50k`
wrist-pose samples or use weighted replay; just adding more epochs to the 10k
scratch model is unlikely to close the gap alone.

Wrist camera pose 50k scratch:

```powershell
python scripts\collect_image_expert_dataset.py `
  --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_50k.yaml

python scripts\inspect_image_expert_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\image_expert_50k_high_start_hard_wrist_pose_visual_camera_seed564k.npz `
  --output-md results\ur5e_full\high_start\hard\visual_audit\image_expert_50k_wrist_pose_seed564k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\image_expert_50k_wrist_pose_seed564k_inspection.csv

python scripts\pretrain_image_actor_bc.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_50k_scratch.yaml

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_50k_scratch.yaml
```

Current 50k result:

| Model | Episodes | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| old center-camera baseline | 20 | 0.550 | 0.500 | 0.500 | 0.400 | 0.400 | 0.450 |
| wrist-pose 50k scratch e20 | 20 | 0.550 | 0.600 | 0.350 | 0.400 | 0.400 | 0.400 |

The wrist-pose 50k model is competitive but not yet promoted. It improves
visual_camera but regresses on visual_camera_control, so the next run should add
wrist-pose control-randomized expert data and weighted replay from the 50k
scratch checkpoint.

Wrist camera pose control replay:

```powershell
python scripts\collect_image_expert_dataset.py `
  --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_50k.yaml

python scripts\inspect_image_expert_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\image_expert_50k_high_start_hard_wrist_pose_visual_camera_control_seed580k.npz `
  --output-md results\ur5e_full\high_start\hard\visual_audit\image_expert_50k_wrist_pose_control_seed580k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\image_expert_50k_wrist_pose_control_seed580k_inspection.csv

python scripts\pretrain_image_actor_bc_weighted.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_replay_100k_e4.yaml

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_replay_100k_e4.yaml
```

Heavier control replay check:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_replay_100k_e4.yaml `
  --dataset-weights 0.25 0.75 `
  --output checkpoints\ur5e_full\high_start\hard\sac_image_bc_100k_high_start_hard_wrist_pose_control_replay_w75_e4.zip `
  --metadata-output results\ur5e_full\high_start\hard\visual_audit\training_metadata_wrist_pose_control_replay_100k_w75_e4.json `
  --seed 582000

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_replay_100k_e4.yaml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_100k_high_start_hard_wrist_pose_control_replay_w75_e4.zip `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_replay_100k_w75_e4_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_replay_100k_w75_e4_20ep.md
```

Replay result:

| Model | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| wrist-pose 50k scratch e20 | 0.550 | 0.600 | 0.350 | 0.400 | 0.400 | 0.400 |
| control replay 0.55 e4 | 0.550 | 0.600 | 0.350 | 0.400 | 0.300 | 0.400 |
| control replay 0.75 e4 | 0.550 | 0.600 | 0.350 | 0.400 | 0.300 | 0.400 |

Generic control replay did not improve `visual_camera_control`. Next should be
control failure analysis by delay/filter/scale buckets, then targeted data or
guarded-control adjustment for the failing regime.

Current narrowed-hole full UR5e adapted checkpoint:

```text
checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip
```

Pre-narrow-hole full UR5e adapted checkpoint:

```text
checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip
```

Checked full UR5e result before adaptation, using the adapter-trained image policy:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy only | 0.080 | 0.260 | 0.250 | 0.140 | 0.150 | - |
| guarded blend 0.75 | 0.080 | 0.260 | 0.250 | 0.620 | 0.650 | 0.590 |

Checked full UR5e result after 50k full-model BC adaptation, before the
narrow-hole geometry update:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy only | 0.950 | 0.660 | 0.610 | 0.680 | 0.650 | - |
| guarded geometry | 0.950 | 0.660 | 0.610 | 0.840 | 0.840 | 0.810 |
| guarded all | 0.990 | 0.970 | 0.950 | 0.840 | 0.840 | 0.820 |

Checked after hiding full UR5e debug markers and narrowing the hole to about
`40 mm` base opening, using the same adapted checkpoint and guarded-all mode:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| guarded all, 10 episodes | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.700 |
| guarded all, 30 episodes, align 0.025 | 0.800 | 0.800 | 0.800 | 0.767 | 0.767 | 0.667 |
| guarded all, 30 episodes, align 0.020, blend 1.0 | 0.933 | 0.900 | 0.833 | 0.867 | 0.867 | 0.800 |
| guarded all, 100 episodes, align 0.020, blend 1.0 | 0.970 | 0.910 | 0.860 | 0.830 | 0.830 | 0.770 |

Policy-only 100-episode narrowed-hole baseline:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact |
| --- | ---: | ---: | ---: | ---: | ---: |
| policy only | 0.750 | 0.690 | 0.640 | 0.600 | 0.620 |

After collecting and training the 50k narrowed-hole dataset:

```text
datasets\ur5e_full\adapt\image_expert_50k_narrow_hole_full_light_geometry.npz
checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip
```

Collection summary: `50000` samples, `545` episodes, `0.824` success, `0.154`
collision. BC summary: 10 epochs, final train loss `0.039346`, final validation
loss `0.041165`.

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy only, 100 episodes | 0.850 | 0.800 | 0.740 | 0.740 | 0.740 | - |
| guarded all, 100 episodes | 0.980 | 0.930 | 0.860 | 0.830 | 0.840 | 0.780 |

After the narrowed-hole correction pass:

```text
datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_8k_min006.npz
checkpoints\ur5e_full\correction\sac_image_bc_50k_narrow_correction_8k_w10_e2.zip
```

The command requested 8k correction samples, but the strict
`min_correction_norm=0.006` filter and `max_episodes_per_config=2000` cap
produced `1836` high-signal samples. Weighted BC used 90% narrowed-hole expert
replay and 10% correction replay for 2 epochs.

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| correction policy only, 100 episodes | 0.870 | 0.780 | 0.760 | 0.750 | 0.720 | - |
| correction guarded all, 100 episodes | 0.970 | 0.940 | 0.870 | 0.830 | 0.840 | 0.780 |

The refreshed demo with `guarded_align_xy_tolerance=0.020` and
`guard_blend=1.0` succeeded in `91` steps and was written to:

```text
demos\ur5e_full\adapt\demo_guarded_all_50k_narrow_hole_full_light_geometry.gif
```

The current best full UR5e demo/deployment-style simulation is the adapted
checkpoint `checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip`
with `guard_scenario_filter=all`, `guarded_align_xy_tolerance=0.020`, and
`guard_blend=1.0`. The remaining weakness is the `0.13 - 0.18` collision rate
under visual_camera_control/full/hard conditions.

Checked high-start smoke:

| Stage | Domain | Result |
| --- | --- | --- |
| reset | high-start | starts about `0.15 - 0.25 m` above and `0.08 - 0.16 m` away in XY |
| oracle smoke | visual_camera | `1.000` success, `0.000` collision |
| oracle smoke | full_light_geometry | too hard for first stage: `0.143` success, `0.571` collision |
| BC smoke | visual_camera | 1 epoch completed |

Use `visual_camera` as the first high-start curriculum stage. Add control and
geometry randomization only after high-start search works reliably.

UR5e mainline branch verification:

```powershell
python scripts\eval_matrix.py --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\ur5e\mainline\eval_matrix_default_ur5e_750k_crop.csv --output-md results\ur5e\mainline\eval_matrix_default_ur5e_750k_crop.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_guarded_policy.py --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --seed 90000 --device cpu --include-hard-bucket --output-csv results\ur5e\mainline\eval_guarded_default_ur5e_750k_blend075.csv --output-md results\ur5e\mainline\eval_guarded_default_ur5e_750k_blend075.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --guard-scenario-filter geometry --guard-start-xy 0.06 --guard-start-z 0.08 --guard-risk-xy 0.0 --guard-blend 0.75 --guard-min-policy-steps 0
```

The same UR5e mainline commands are now available as config-driven short
commands. These use the branch-default UR5e model and the recommended
near-hole crop policy:

```powershell
python scripts\eval_matrix.py --config configs\sim\ur5e\eval_image_crop.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e\eval_guarded_image_crop.yaml
python scripts\demo_policy.py --config configs\sim\ur5e\demo_guarded_image_crop.yaml
python scripts\scan_guarded_policy_params.py --config configs\sim\ur5e\scan_guarded_policy_focused.yaml
```

Structured-layout smoke for future UR5e data and BC experiments:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e\collect_image_expert_smoke.yaml
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e\pretrain_image_bc_smoke.yaml
```

For MP4 demo output, install the current dependency set:

```powershell
python -m pip install -r requirements.txt
```

If the MP4 backend is still unavailable, `demo_policy.py` automatically saves a
same-stem GIF fallback.

Checked UR5e mainline result:

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy only | 0.980 | 0.980 | 0.920 | 0.580 | 0.600 | - |
| guarded blend 0.75 | 0.980 | 0.980 | 0.910 | 0.710 | 0.640 | 0.530 |

## UR5e Adapter Fixed-Camera Baselines

The usable UR5e adapter image baselines use the fixed wrist-camera pose
in `assets\ur5e_adapter\ur5e_peg_in_hole.xml` and trains from scratch. Starting
from the old side-camera policy was tested and gave poor clean performance
because it kept an early-descent bias.

Recommended 50k fixed-camera oracle dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz --samples 50000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --compressed
```

Train the recommended 50k scratch image BC model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz --output checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip --epochs 30 --batch-size 512 --learning-rate 0.0001 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render the recommended 50k model:

```powershell
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_50k_scratch.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_50k_scratch.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_fixedcam_50k_scratch_hd.gif --trajectory-output results\demo_ur5e_adapter_fixedcam_50k_scratch_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Fast 5k smoke dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_5k_oracle.npz --samples 5000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --compressed
```

Train the 5k smoke model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_5k_oracle.npz --output checkpoints_image_bc_ur5e_adapter_fixedcam_5k_scratch\sac_image_bc.zip --epochs 50 --batch-size 256 --learning-rate 0.0001 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render the 5k smoke model:

```powershell
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_5k_scratch\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_5k_scratch\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_fixedcam_5k_scratch_hd.gif --trajectory-output results\demo_ur5e_adapter_fixedcam_5k_scratch_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current UR5e fixedcam results:

| Model | Episodes | Success | Collision |
| --- | ---: | ---: | ---: |
| `checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip` | 100 clean eval_policy | 1.000 | 0.000 |
| `checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip` | 100 clean eval_matrix | 0.950 | 0.050 |
| `checkpoints_image_bc_ur5e_adapter_fixedcam_5k_scratch\sac_image_bc.zip` | 100 clean | 0.790 | 0.200 |

The 50k clean baseline is strong, but the same model is not yet robust to
visual/camera/control randomization. See
`results\eval_matrix_ur5e_adapter_fixedcam_50k_scratch.md`.

## UR5e Adapter Visual-Camera Baseline

The current recommended UR5e visual-camera baseline is trained on a mixed
dataset: 50k clean fixed-camera oracle samples plus 100k `visual_camera`
randomized oracle samples.

Current recommended model:

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip
```

Collect the visual-camera oracle dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_oracle.npz --samples 50000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera --compressed
```

Merge clean and visual-camera datasets:

```powershell
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle.npz --compressed
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle.npz --compressed
```

Train from the clean 50k model, then continue with a lower learning rate:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle\sac_image_bc.zip --epochs 20 --batch-size 512 --learning-rate 0.00003 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35\sac_image_bc.zip --epochs 15 --batch-size 512 --learning-rate 0.00001 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip --epochs 20 --batch-size 512 --learning-rate 0.00001 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render the visual-camera model:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_100k_e35_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_100k_e35_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_150k_e20_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_150k_e20_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current visual-camera result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean e35 | 0.960 | 0.040 |
| visual_camera e35 | 0.660 | 0.340 |
| visual_camera_control e35 | 0.440 | 0.560 |
| clean e20 | 0.960 | 0.040 |
| visual_camera e20 | 0.810 | 0.190 |
| visual_camera_control e20 | 0.480 | 0.520 |
| full_light_geometry e20 | 0.140 | 0.840 |
| full_contact_light e20 | 0.140 | 0.840 |

The next UR5e step should improve visual-camera robustness before moving to
control or contact randomization. The current failure mode is still collision
under image/camera perturbations.

## UR5e Adapter Mild Control Baseline

Default `visual_camera_control` data collection was tested first, but the
oracle only reached `0.910` success and `0.089` collision. For the first
control-stage baseline, use a milder control randomization range:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_mild_50k_oracle.npz --samples 50000 --seed 190000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 0.9 1.1 --control-action-noise-std-range 0 0.0004 --control-action-delay-range 0 1 --control-action-filter-alpha-range 0.75 1.0 --compressed
```

Merge clean, visual-camera, and mild-control data:

```powershell
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_mild_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle.npz --compressed
```

Continue from the 150k visual-camera model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip --epochs 20 --batch-size 512 --learning-rate 0.00001 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_control_mild_200k_e20_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_control_mild_200k_e20_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current mild-control result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 0.930 | 0.070 |
| visual_camera | 0.920 | 0.080 |
| visual_camera_control | 0.600 | 0.400 |
| full_light_geometry | 0.200 | 0.790 |
| full_contact_light | 0.200 | 0.770 |

This is a useful control-stage improvement, not the final control-robust
policy.

## UR5e Adapter Success-Only Control Baseline

The next control-stage baseline targets the default `visual_camera_control`
range directly. The key change is `--success-only`: failed/collision oracle
episodes are used for diagnostics but are not written into the BC dataset.

First confirm which control component is limiting the mild-control model:

```powershell
python scripts\scan_control_randomization.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip --output results\control_randomization_scan_ur5e_mild_200k_e20.csv --episodes 30 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

The scan shows that delay is the main weak point. Then scan oracle gains under
default control randomization:

```powershell
python scripts\scan_oracle_control_gain.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\oracle_control_gain_scan_ur5e_default_control.csv --output-md results\oracle_control_gain_scan_ur5e_default_control.md --episodes 100 --gains 1.0 0.7 0.5 0.35 0.25 0.18 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

For UR5e default control, `gain=1.0` remains best:

| Oracle gain | Success | Collision |
| ---: | ---: | ---: |
| 1.000 | 0.910 | 0.090 |
| 0.700 | 0.890 | 0.110 |
| 0.500 | 0.840 | 0.160 |
| 0.350 | 0.660 | 0.340 |
| 0.250 | 0.230 | 0.770 |
| 0.180 | 0.030 | 0.970 |

Collect default-control success-only data:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz --samples 50000 --seed 260000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --success-only --compressed
```

Merge clean, visual-camera, mild-control, and success-only default-control data:

```powershell
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_mild_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle.npz --compressed
```

Continue from the mild-control model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15\sac_image_bc.zip --epochs 15 --batch-size 512 --learning-rate 0.000008 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_control_success_250k_e15_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_control_success_250k_e15_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current success-only control result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 0.950 | 0.050 |
| visual_camera | 0.910 | 0.090 |
| visual_camera_control | 0.730 | 0.270 |
| full_light_geometry | 0.250 | 0.730 |
| full_contact_light | 0.270 | 0.690 |

This reaches the previous target of default `visual_camera_control >= 0.70`.

## UR5e Adapter Delay-Filter Success Baseline

The 250k success-only model still had a delay/filter weakness. Add one focused
success-only batch with scale and noise disabled, then add one more default
control success-only batch:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay_filter_success_50k_oracle.npz --samples 50000 --seed 310000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 2 --control-action-filter-alpha-range 0.55 1.0 --success-only --compressed
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay_filter_success_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle.npz --compressed
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle_e10\sac_image_bc.zip --epochs 10 --batch-size 512 --learning-rate 0.000006 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_seed330k_oracle.npz --samples 50000 --seed 330000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --success-only --compressed
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_seed330k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz --compressed
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle_e10\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --epochs 8 --batch-size 512 --learning-rate 0.000005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render the current recommended UR5e model:

```powershell
python scripts\scan_control_randomization.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --output results\control_randomization_scan_ur5e_delay_filter_success_350k_e8.csv --episodes 30 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_control_delay_filter_success_350k_e8_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_control_delay_filter_success_350k_e8_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current delay-filter success result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 0.990 | 0.010 |
| visual_camera | 0.930 | 0.070 |
| visual_camera_control | 0.860 | 0.140 |
| full_light_geometry | 0.290 | 0.670 |
| full_contact_light | 0.270 | 0.680 |

Analyze the remaining `visual_camera_control` failures before collecting the
next dataset:

```powershell
python scripts\analyze_control_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --episodes 200 --output-csv results\control_failure_analysis_ur5e_delay_filter_success_350k_e8.csv --output-md results\control_failure_analysis_ur5e_delay_filter_success_350k_e8.md --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Control failure analysis result:

| Bucket | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| overall | 200 | 0.830 | 0.165 | 0.005 |
| delay_2 | 72 | 0.764 | 0.236 | 0.000 |
| delay_1 | 63 | 0.794 | 0.190 | 0.016 |
| delay_0 | 65 | 0.938 | 0.062 | 0.000 |
| filter low <0.70 | 62 | 0.790 | 0.210 | 0.000 |
| scale low <0.90 | 43 | 0.721 | 0.279 | 0.000 |
| noise high >=0.00055 | 50 | 0.820 | 0.180 | 0.000 |

The next control dataset should bias toward `delay=2`, low filter alpha
`0.55-0.70`, low action scale `0.8-0.9`, and high noise
`0.00055-0.0008`. This is still a control-randomization problem; full
geometry/contact randomization should wait until default `visual_camera_control`
is closer to `0.90`.

## UR5e Adapter Hard-Control Weighted Baseline

Collect the hard-control success-only dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz --samples 50000 --seed 360000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 0.8 0.9 --control-action-noise-std-range 0.00055 0.0008 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --success-only --compressed
```

The hard-control oracle reached only `0.771` success and `0.229` collision, so
this data is useful as a targeted stress bucket, not as a standalone policy
distribution. First train a single-copy 400k model:

```powershell
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_success_400k_oracle.npz --compressed
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_success_400k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_success_400k_oracle_e6\sac_image_bc.zip --epochs 6 --batch-size 512 --learning-rate 0.000004 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Then train a hard-weighted 500k model by repeating the hard-control 50k dataset
three times:

```powershell
python scripts\merge_image_expert_datasets.py --inputs datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz --output datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle.npz --compressed
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_success_400k_oracle_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --epochs 5 --batch-size 512 --learning-rate 0.000003 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate and render the hard-weighted model:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\analyze_control_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --episodes 100 --output-csv results\control_failure_analysis_ur5e_hard_weighted_500k_e5_hard_control.csv --output-md results\control_failure_analysis_ur5e_hard_weighted_500k_e5_hard_control.md --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --control-action-scale-range 0.8 0.9 --control-action-noise-std-range 0.00055 0.0008 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70
python scripts\analyze_control_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --episodes 200 --output-csv results\control_failure_analysis_ur5e_hard_weighted_500k_e5.csv --output-md results\control_failure_analysis_ur5e_hard_weighted_500k_e5.md --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\demo_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --output demos\image_bc_ur5e_adapter_visual_camera_control_hard_weighted_500k_e5_hd.gif --trajectory-output results\demo_ur5e_adapter_visual_camera_control_hard_weighted_500k_e5_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current hard-weighted result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 0.960 | 0.040 |
| visual_camera | 0.990 | 0.010 |
| visual_camera_control | 0.890 | 0.110 |
| hard-control fixed bucket | 0.770 | 0.230 |
| full_light_geometry | 0.300 | 0.660 |
| full_contact_light | 0.310 | 0.660 |

This version improves default control and hard-control robustness, but trades
off some clean performance compared with the 350k model. It is the current
control-robust recommendation; use the 350k model if the immediate goal is the
highest clean score.

## UR5e Adapter Balanced Weighted BC Trial

The 500k hard-weighted model improves control robustness but lowers clean
success to `0.960`. A balanced weighted BC trial can train from several source
datasets without materializing another merged `.npz`:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz --dataset-weights 0.55 0.18 0.12 0.05 0.10 --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_balanced_weighted_550k_oracle_e6\sac_image_bc.zip --epochs 6 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Balanced weighted result:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 0.980 | 0.020 |
| visual_camera | 0.980 | 0.020 |
| visual_camera_control | 0.890 | 0.110 |
| hard-control fixed bucket | 0.740 | 0.260 |
| full_light_geometry | 0.310 | 0.660 |
| full_contact_light | 0.300 | 0.670 |

This trial recovers clean performance but does not improve default
`visual_camera_control` beyond the hard-weighted model. It is a useful
alternative if clean robustness matters more than the fixed hard-control bucket.

Safety filtering was also checked with the deployment-style inference path:

```powershell
python scripts\run_policy_inference.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --episodes 100 --output results\policy_inference_ur5e_hard_weighted_500k_e5_alpha08_trace.csv --device cpu --seed 90000 --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --safety-action-filter-alpha 0.8
python scripts\run_policy_inference.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip --episodes 100 --output results\policy_inference_ur5e_hard_weighted_500k_e5_alpha06_trace.csv --device cpu --seed 90000 --domain-randomization-level visual_camera_control --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --safety-action-filter-alpha 0.6
```

The action filter did not improve success: `alpha=0.8` reached `0.870`, and
`alpha=0.6` reached `0.860`.

## Hole Geometry Curriculum Scan

Before collecting narrowed-hole data, scan the staged oracle over fixed hole
sizes:

```powershell
python scripts\scan_hole_geometry_oracle.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\hole_geometry_oracle_scan_ur5e_adapter.csv --output-md results\hole_geometry_oracle_scan_ur5e_adapter.md --episodes 50 --hole-half-sizes 0.045 0.029 0.025 0.020 0.017 0.015 --peg-radii 0.012 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\scan_hole_geometry_oracle.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\hole_geometry_oracle_scan_ur5e_adapter_approach02.csv --output-md results\hole_geometry_oracle_scan_ur5e_adapter_approach02.md --episodes 50 --hole-half-sizes 0.045 0.029 0.025 0.020 0.017 0.015 --peg-radii 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Default approach `0.06` is too aggressive for narrowed holes:

| Hole half-size | Clearance | Success | Collision |
| ---: | ---: | ---: | ---: |
| 0.045 | 0.033 | 1.000 | 0.000 |
| 0.029 | 0.017 | 0.860 | 0.120 |
| 0.025 | 0.013 | 0.800 | 0.200 |
| 0.020 | 0.008 | 0.720 | 0.280 |
| 0.017 | 0.005 | 0.640 | 0.320 |
| 0.015 | 0.003 | 0.500 | 0.480 |

With `approach_xy_tolerance=0.02`, the oracle becomes stable down to
hole half-size `0.020`:

| Hole half-size | Clearance | Success | Collision |
| ---: | ---: | ---: | ---: |
| 0.045 | 0.033 | 1.000 | 0.000 |
| 0.029 | 0.017 | 1.000 | 0.000 |
| 0.025 | 0.013 | 1.000 | 0.000 |
| 0.020 | 0.008 | 1.000 | 0.000 |
| 0.017 | 0.005 | 0.800 | 0.040 |
| 0.015 | 0.003 | 0.680 | 0.180 |

Recommended next geometry-curriculum range: start with
`geometry_hole_half_size_range 0.020 0.025`, `geometry_peg_radius_range 0.012
0.012`, and `approach_xy_tolerance 0.02`. Do not start at `0.017` or tighter
until the oracle itself is improved.

## Narrow Geometry Curriculum Attempt

Collect the first success-only narrowed-hole dataset. This keeps control
execution exact so the first geometry batch isolates hole-size difficulty:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --samples 50000 --seed 520000 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.020 0.025 --geometry-peg-radius-range 0.012 0.012 --success-only --compressed
```

Observed oracle collection result:

| Samples | Episodes | Success | Collision |
| ---: | ---: | ---: | ---: |
| 50000 | 3474 | 0.996 | 0.004 |

Weighted continuation from the balanced model:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.45 0.12 0.10 0.05 0.08 0.20 --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_balanced_weighted_550k_oracle_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6\sac_image_bc.zip --epochs 6 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Narrow-only continuation used as an upper-bound diagnostic:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_balanced_weighted_550k_oracle_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_narrow_only_50k_oracle_e12\sac_image_bc.zip --epochs 12 --batch-size 512 --learning-rate 0.000002 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the weighted continuation on the standard matrix:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Evaluate the exact target narrow-geometry bucket:

```powershell
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6\sac_image_bc.zip --episodes 100 --device cpu --seed 610000 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.020 0.025 --geometry-peg-radius-range 0.012 0.012 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current result summary:

| Model | Target narrow geometry | Clean | Visual camera control | Full light geometry |
| --- | ---: | ---: | ---: | ---: |
| balanced 550k | 0.210 | 0.980 | 0.890 | 0.310 |
| weighted narrow 600k | 0.340 | 0.950 | 0.850 | 0.350 |
| narrow-only 50k | 0.450 | 0.820 | 0.580 | 0.360 |

The narrow data is useful, but this is not a new recommended policy yet. The
next iteration should add an intermediate geometry range and/or improve
near-hole visual alignment, instead of just increasing narrow-only BC weight.
Full details are in `results\geometry_curriculum_narrow_summary.md`.

## Resolution A/B For Intermediate Geometry

This test checks whether directly increasing the full wrist-camera image from
`100x100` to `128x128` helps near-hole geometry. It uses scratch BC models so
the input shapes are comparable without checkpoint migration.

Collect the 100x100 intermediate-geometry dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_20k_100_oracle.npz --samples 20000 --seed 630000 --image-width 100 --image-height 100 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --success-only --compressed
```

Collect the 128x128 intermediate-geometry dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_20k_128_oracle.npz --samples 20000 --seed 630001 --image-width 128 --image-height 128 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --success-only --compressed
```

Train the 100x100 scratch BC model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_20k_100_oracle.npz --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_20k_100_scratch_e30\sac_image_bc.zip --epochs 30 --batch-size 512 --learning-rate 0.0001 --image-width 100 --image-height 100 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Train the 128x128 scratch BC model:

```powershell
python scripts\pretrain_image_actor_bc.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_20k_128_oracle.npz --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_20k_128_scratch_e30\sac_image_bc.zip --epochs 30 --batch-size 512 --learning-rate 0.0001 --image-width 128 --image-height 128 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the target intermediate geometry bucket:

```powershell
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_20k_100_scratch_e30\sac_image_bc.zip --episodes 100 --device cpu --seed 650000 --width 100 --height 100 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_20k_128_scratch_e30\sac_image_bc.zip --episodes 100 --device cpu --seed 650000 --width 128 --height 128 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current A/B result:

| Scenario | 100x100 | 128x128 |
| --- | ---: | ---: |
| BC final validation loss | 0.164 | 0.132 |
| Intermediate geometry success | 0.880 | 0.860 |
| Narrow geometry success | 0.750 | 0.720 |
| Clean success | 0.670 | 0.180 |

The lower 128x128 BC loss did not improve rollout success. Do not switch the
mainline to 128x128 yet; prefer staged geometry curriculum or a targeted
near-hole crop. Full details are in
`results\resolution_ab_intermediate_geometry_summary.md`.

## Staged Geometry Curriculum

Collect a 50k intermediate-geometry dataset at the current `100x100`
resolution:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz --samples 50000 --seed 680000 --image-width 100 --image-height 100 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --success-only --compressed
```

Observed collection result:

| Samples | Episodes | Oracle success | Oracle collision |
| ---: | ---: | ---: | ---: |
| 50000 | 3214 | 0.996 | 0.000 |

Stage 1: add intermediate geometry while replaying clean/control data:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz --dataset-weights 0.45 0.12 0.10 0.05 0.08 0.20 --model checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_balanced_weighted_550k_oracle_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_600k_oracle_e6\sac_image_bc.zip --epochs 6 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Stage 2: add low-weight narrow geometry on top of the intermediate model:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.42 0.12 0.10 0.05 0.08 0.15 0.08 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_600k_oracle_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip --epochs 5 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.0000015 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the staged model:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current staged curriculum result:

| Model | Intermediate bucket | Narrow bucket | Clean | Visual camera control | Full light geometry |
| --- | ---: | ---: | ---: | ---: | ---: |
| balanced 550k | 0.310 | 0.180 | 0.980 | 0.890 | 0.310 |
| intermediate 600k | 0.450 | 0.290 | 0.950 | 0.870 | 0.370 |
| staged intermediate+narrow 650k | 0.510 | 0.330 | 0.960 | 0.850 | 0.390 |

The staged model is the best geometry-curriculum candidate so far, but it is
not a replacement for the current control-focused model because default
`visual_camera_control` drops to `0.850`. Full details are in
`results\geometry_curriculum_staged_summary.md`.

## Near-Hole Crop Observation

The near-hole crop adds a second image key:

```text
cam_image: 100x100x1
near_hole_crop: 64x64x1
```

Existing `.npz` datasets can be reused. If `near_hole_crops` is not stored in a
dataset, the BC trainer derives it from `cam_images` when
`--include-near-hole-crop` is passed.

Analyze no-crop geometry failures:

```powershell
python scripts\analyze_geometry_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip --episodes 100 --seed 730000 --output-csv results\geometry_failure_analysis_staged_650k_intermediate.csv --output-md results\geometry_failure_analysis_staged_650k_intermediate.md --device cpu --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\analyze_geometry_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip --episodes 100 --seed 740000 --output-csv results\geometry_failure_analysis_staged_650k_narrow.csv --output-md results\geometry_failure_analysis_staged_650k_narrow.md --device cpu --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.020 0.025 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Train the crop model. The first low-learning-rate scratch run underfit, but it
is the checkpoint used by the continued `e16` run:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.40 0.12 0.08 0.05 0.08 0.15 0.12 --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e6\sac_image_bc.zip --epochs 6 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Continue with the effective higher learning rate:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.40 0.12 0.08 0.05 0.08 0.15 0.12 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e6\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --epochs 10 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.00005 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the crop model:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --episodes 100 --device cpu --seed 690000 --width 100 --height 100 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\eval_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --episodes 100 --device cpu --seed 700000 --width 100 --height 100 --domain-randomization-level full_light_geometry --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 0 --control-action-filter-alpha-range 1 1 --geometry-hole-center-xy-jitter 0 0 --geometry-fixture-height-jitter 0 --geometry-table-height-jitter 0 --geometry-hole-half-size-range 0.020 0.025 --geometry-peg-radius-range 0.012 0.012 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current crop result:

| Model | Crop | Intermediate bucket | Narrow bucket | Visual camera control | Full light geometry | Full contact light |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| staged 650k | no | 0.510 | 0.330 | 0.850 | 0.390 | 0.400 |
| staged crop 650k e16 | yes | 0.890 | 0.770 | 0.880 | 0.530 | 0.570 |

The crop model is the strongest geometry candidate so far. Full details are in
`results\near_hole_crop_summary.md`.

## Crop Control And Full-Light Replay

The crop model's remaining control failures were concentrated around delay 2,
low filter alpha, low action scale, and low noise:

```powershell
python scripts\analyze_control_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --episodes 200 --output-csv results\control_failure_analysis_ur5e_staged_crop_650k_e16.csv --output-md results\control_failure_analysis_ur5e_staged_crop_650k_e16.md --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Collect a hard control replay dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz --samples 50000 --seed 760000 --image-width 100 --image-height 100 --include-near-hole-crop --near-hole-crop-size 64 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 0.8 0.9 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --success-only --compressed
```

Observed collection result: `50000` samples, `2061` episodes, `0.799` oracle
success, `0.201` oracle collision.

Train the control replay model:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.35 0.14 0.15 0.06 0.04 0.10 0.10 0.06 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_control_replay_700k_oracle_e4\sac_image_bc.zip --epochs 4 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000005 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

The control replay model reaches `visual_camera_control=0.900`, but
`full_light_geometry` remains `0.520`, so add a combined geometry+control
dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz --samples 50000 --seed 780000 --image-width 100 --image-height 100 --include-near-hole-crop --near-hole-crop-size 64 --expert-action-gain 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --success-only --compressed
```

Observed collection result: `50000` samples, `4003` episodes, `0.553` oracle
success, `0.445` oracle collision.

Train the final full-light replay model:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.30 0.12 0.10 0.15 0.06 0.04 0.08 0.10 0.05 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_control_replay_700k_oracle_e4\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --epochs 4 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000003 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the final crop replay model:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Current result:

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| staged crop 650k e16 | 0.960 | 0.960 | 0.880 | 0.530 | 0.570 |
| crop control replay 700k e4 | 0.960 | 0.970 | 0.900 | 0.520 | 0.570 |
| crop full-light replay 750k e4 | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 |

The current strongest crop-enabled model is:

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip
```

Full details are in `results\crop_control_replay_summary.md`.

## Hard Full-Light Replay Attempt

Run combined full-light failure analysis on the current recommended crop model:

```powershell
python scripts\analyze_geometry_failures.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 200 --seed 820000 --output-csv results\geometry_failure_analysis_staged_crop_full_light_replay_750k_e4_full_light.csv --output-md results\geometry_failure_analysis_staged_crop_full_light_replay_750k_e4_full_light.md --device cpu --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.2 --control-action-noise-std-range 0 0.0008 --control-action-delay-range 0 2 --control-action-filter-alpha-range 0.55 1.0 --geometry-hole-center-xy-jitter 0.002 0.002 --geometry-fixture-height-jitter 0.001 --geometry-table-height-jitter 0.001 --geometry-hole-half-size-range 0.025 0.029 --geometry-peg-radius-range 0.0115 0.0125 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

The 200-episode analysis reached `0.650` success but still showed collision
concentration around `delay_2`, `low_<0.70` filter alpha, and low-noise
combined buckets.

Scan staged-oracle gain in the targeted hard full-light bucket:

```powershell
python scripts\scan_oracle_control_gain.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise.csv --output-md results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise.md --episodes 50 --seed 842000 --gains 1.0 0.7 0.5 0.35 0.25 0.18 --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Collect the hard full-light replay dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_gain05_success_50k_oracle.npz --samples 50000 --seed 845000 --image-width 100 --image-height 100 --include-near-hole-crop --near-hole-crop-size 64 --expert-action-gain 0.5 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --success-only --compressed
```

Observed collection result: `50000` samples, `7065` episodes, `0.267` oracle
success, `0.733` oracle collision.

Train the hard replay attempt:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_gain05_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.27 0.10 0.08 0.13 0.10 0.05 0.03 0.07 0.10 0.07 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_hard_full_light_replay_800k_oracle_e4\sac_image_bc.zip --epochs 4 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

This attempt is a negative result:

| Model | Standard full light | Full contact light | Hard full-light bucket |
| --- | ---: | ---: | ---: |
| crop full-light replay 750k e4 | 0.580 | 0.590 | 0.330 |
| hard full-light replay 800k e4 | 0.550 | 0.530 | 0.310 |

Do not promote the 800k hard replay model. Full details are in
`results\hard_full_light_replay_summary.md`.

## Guarded Two-Stage Oracle

The hard full-light bucket is limited by oracle/controller stability, not just
BC data volume. The selected guarded oracle improves the hard bucket before any
new policy training:

| Controller | Seed | Episodes | Success | Collision |
| --- | ---: | ---: | ---: | ---: |
| staged, gain 0.5 | 847000 | 100 | 0.280 | 0.720 |
| guarded_two_stage, gain 1.0 | 847000 | 100 | 0.440 | 0.560 |

Selected hard-bucket scan:

```powershell
python scripts\scan_oracle_control_gain.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise_guarded_selected_100ep.csv --output-md results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise_guarded_selected_100ep.md --episodes 100 --seed 847000 --gains 1.0 0.85 --oracle-mode guarded_two_stage --guarded-align-xy-tolerance 0.025 --guarded-insert-xy-tolerance 0.005 --guarded-retract-xy-tolerance 0.012 --guarded-preinsert-height 0.000 --guarded-max-xy-action 0.005 --guarded-max-down-action 0.0035 --guarded-max-up-action 0.005 --guarded-prediction-steps 1.0 --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Matching staged baseline:

```powershell
python scripts\scan_oracle_control_gain.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-csv results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise_staged_selected_seed847k_100ep.csv --output-md results\oracle_gain_scan_full_light_delay2_lowalpha_lownoise_staged_selected_seed847k_100ep.md --episodes 100 --seed 847000 --gains 1.0 0.7 0.5 --oracle-mode staged --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Next dataset collection candidate:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_guarded_success_50k_oracle.npz --samples 50000 --seed 848000 --image-width 100 --image-height 100 --include-near-hole-crop --near-hole-crop-size 64 --expert-action-gain 1.0 --oracle-mode guarded_two_stage --guarded-align-xy-tolerance 0.025 --guarded-insert-xy-tolerance 0.005 --guarded-retract-xy-tolerance 0.012 --guarded-preinsert-height 0.000 --guarded-max-xy-action 0.005 --guarded-max-down-action 0.0035 --guarded-max-up-action 0.005 --guarded-prediction-steps 1.0 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --success-only --compressed
```

Full details are in `results\guarded_oracle_summary.md`.

## Guarded Hard Replay Attempt

The guarded oracle was used to collect a 50k hard full-light success-only
dataset:

```powershell
python scripts\collect_image_expert_dataset.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_guarded_success_50k_oracle.npz --samples 50000 --seed 848000 --image-width 100 --image-height 100 --include-near-hole-crop --near-hole-crop-size 64 --expert-action-gain 1.0 --oracle-mode guarded_two_stage --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02 --domain-randomization-level full_light_geometry --control-action-scale-range 0.8 1.1 --control-action-noise-std-range 0 0.00025 --control-action-delay-range 2 2 --control-action-filter-alpha-range 0.55 0.70 --success-only --compressed
```

Collection result: `50000` samples, `5127` episodes, `0.376` oracle success,
`0.608` oracle collision.

Two BC replay attempts were tested from the current 750k recommendation:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_guarded_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.29 0.10 0.08 0.13 0.08 0.05 0.03 0.07 0.10 0.07 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_guarded_hard_replay_800k_oracle_e4\sac_image_bc.zip --epochs 4 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000002 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_guarded_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz --dataset-weights 0.30 0.10 0.08 0.14 0.04 0.05 0.03 0.07 0.11 0.08 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_guarded_hard_replay_light_790k_oracle_e2\sac_image_bc.zip --epochs 2 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000001 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Result:

| Model | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 750k recommended | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 | 0.330 |
| guarded hard replay 800k e4 | 0.960 | 0.950 | 0.880 | 0.550 | 0.530 | 0.340 |
| guarded hard replay light 790k e2 | 0.980 | 0.980 | 0.910 | 0.550 | 0.580 | 0.340 |

Do not promote either guarded replay model. Full details are in
`results\guarded_hard_replay_summary.md`.

## Deployment-Time Guarded Insert

Evaluate the current recommended 750k visual policy without a guarded wrapper:

```powershell
python scripts\eval_guarded_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --seed 90000 --device cpu --output-csv results\eval_guarded_policy_matrix_750k_no_guard_core.csv --output-md results\eval_guarded_policy_matrix_750k_no_guard_core.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --guard-scenario-filter none --guard-start-xy 0.06 --guard-start-z 0.10 --guard-risk-xy 0.0 --guard-blend 1.0
```

Evaluate an aggressive wrapper that guards every scenario:

```powershell
python scripts\eval_guarded_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --seed 90000 --device cpu --include-hard-bucket --output-csv results\eval_guarded_policy_matrix_750k_override.csv --output-md results\eval_guarded_policy_matrix_750k_override.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --guard-scenario-filter all --guard-start-xy 0.06 --guard-start-z 0.10 --guard-risk-xy 0.0 --guard-blend 1.0
```

Evaluate the selected geometry/contact guarded wrapper:

```powershell
python scripts\eval_guarded_policy.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --episodes 100 --seed 90000 --device cpu --include-hard-bucket --output-csv results\eval_guarded_policy_matrix_750k_geometry_only_override.csv --output-md results\eval_guarded_policy_matrix_750k_geometry_only_override.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --guard-scenario-filter geometry --guard-start-xy 0.06 --guard-start-z 0.10 --guard-risk-xy 0.0 --guard-blend 1.0
```

Result:

| Configuration | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no guard | 0.980 | 0.980 | 0.910 | 0.580 | 0.580 | 0.330 |
| guard all scenarios | 1.000 | 1.000 | 0.830 | 0.690 | 0.660 | 0.480 |
| guard geometry/contact only | 0.980 | 0.980 | 0.920 | 0.690 | 0.660 | 0.480 |

The selected wrapper is a positive deployment-time result. It does not replace
the policy checkpoint; it wraps the current 750k policy during final insertion.
Full details are in `results\guarded_policy_summary.md`.

The wrapper is also available in `scripts\demo_policy.py` through
`--guarded-policy`. Demo trajectory CSVs include `guard_enabled`,
`guard_active`, `policy_action_*`, `guarded_action_*`, and `final_action_*`.
The checked demo files are:

| Demo | Seed | Result |
| --- | ---: | --- |
| `demos\guarded_policy_full_light_no_guard.gif` | 90000 | success, 12 steps |
| `demos\guarded_policy_full_light_guarded.gif` | 90000 | success, 11 steps, 11 guard rows |
| `demos\guarded_policy_hard_bucket_no_guard.gif` | 90005 | collision failure, 11 steps |
| `demos\guarded_policy_hard_bucket_guarded.gif` | 90005 | success, 20 steps, 20 guard rows |

Render the hard-bucket no-guard contrast episode:

```powershell
python scripts\demo_policy.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --output demos\guarded_policy_hard_bucket_no_guard.gif `
  --trajectory-output demos\guarded_policy_hard_bucket_no_guard_trajectory.csv `
  --episodes 1 `
  --seed 90005 `
  --device cpu `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --render-cameras overview wrist_cam `
  --render-width 640 `
  --render-height 480 `
  --fps 20 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02
```

Render the same episode with selective guarded insertion:

```powershell
python scripts\demo_policy.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --output demos\guarded_policy_hard_bucket_guarded.gif `
  --trajectory-output demos\guarded_policy_hard_bucket_guarded_trajectory.csv `
  --episodes 1 `
  --seed 90005 `
  --device cpu `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --render-cameras overview wrist_cam `
  --render-width 640 `
  --render-height 480 `
  --fps 20 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-name hard_full_light_bucket `
  --guard-start-xy 0.06 `
  --guard-start-z 0.10 `
  --guard-blend 1.0
```

Full demo details are in `results\guarded_demo_summary.md`.

## Guarded Parameter Scan

Run the focused one-at-a-time guarded parameter scan:

```powershell
python scripts\scan_guarded_policy_params.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --preset focused `
  --scenario-preset targeted `
  --episodes 30 `
  --seed 90000 `
  --device cpu `
  --output-csv results\guarded_policy_param_scan_focused.csv `
  --output-md results\guarded_policy_param_scan_focused.md `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guard-scenario-filter geometry
```

Validate the previous `blend=1.0` wrapper against the new `blend=0.75`
candidate on the full core matrix:

```powershell
python scripts\scan_guarded_policy_params.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --preset grid `
  --scenario-preset core `
  --episodes 100 `
  --seed 90000 `
  --device cpu `
  --output-csv results\guarded_policy_param_scan_blend_validation_100ep.csv `
  --output-md results\guarded_policy_param_scan_blend_validation_100ep.md `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guard-scenario-filter geometry `
  --guard-start-xy-values 0.06 `
  --guard-start-z-values 0.10 `
  --guard-blend-values 0.75 1.0 `
  --guarded-max-down-action-values 0.0035 `
  --guarded-align-xy-tolerance-values 0.025
```

Result:

| Configuration | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no guard | 0.980 | 0.980 | 0.910 | 0.580 | 0.600 | 0.320 |
| guard blend 0.75 | 0.980 | 0.980 | 0.900 | 0.710 | 0.650 | 0.530 |
| guard blend 1.0 | 0.980 | 0.980 | 0.910 | 0.690 | 0.660 | 0.480 |

Promote `guard_blend=0.75` as the next guarded deployment candidate. Full
details are in `results\guarded_policy_param_scan_summary.md`.

Late-activation follow-up:

```powershell
python scripts\scan_guarded_policy_params.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 100 `
  --seed 90000 `
  --device cpu `
  --preset grid `
  --scenario-preset core `
  --guard-scenario-filter geometry `
  --guard-start-xy-values 0.03 0.06 `
  --guard-start-z-values 0.08 0.10 `
  --guard-blend-values 0.75 `
  --guard-min-policy-step-values 0 `
  --guarded-max-down-action-values 0.0035 `
  --guarded-align-xy-tolerance-values 0.025 `
  --output-csv results\guarded_policy_late_activation_validation_100ep.csv `
  --output-md results\guarded_policy_late_activation_validation_100ep.md `
  --approach-xy-tolerance 0.02 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01
```

Current guarded deployment recommendation:

```text
guard_scenario_filter = geometry
guard_start_xy = 0.06
guard_start_z = 0.08
guard_blend = 0.75
guard_min_policy_steps = 0
```

`guard_min_policy_steps` is available in `eval_guarded_policy.py`,
`run_policy_inference.py`, and `scan_guarded_policy_params.py`, but keep it at
`0` for the current policy. Delaying guard activation reduced guard steps but
lost hard-bucket recovery. Full details are in
`results\guarded_late_activation_summary.md`.

## Guarded Deployment Inference

Run a deployment-style smoke where geometry-only guard is available but should
not activate in the control-only scenario:

```powershell
python scripts\run_policy_inference.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 1 `
  --seed 90000 `
  --device cpu `
  --output results\policy_inference_visual_camera_control_guarded_smoke.csv `
  --domain-randomization-level visual_camera_control `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-blend 0.75 `
  --guard-start-z 0.08 `
  --guard-min-policy-steps 0
```

Run the hard-bucket no-guard deployment contrast:

```powershell
python scripts\run_policy_inference.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 1 `
  --seed 90005 `
  --device cpu `
  --output results\policy_inference_hard_bucket_no_guard_smoke.csv `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02
```

Run the same hard-bucket episode with guarded insertion:

```powershell
python scripts\run_policy_inference.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 1 `
  --seed 90005 `
  --device cpu `
  --output results\policy_inference_hard_bucket_guarded_blend075_smoke.csv `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-name hard_full_light_bucket `
  --guard-blend 0.75 `
  --guard-start-xy 0.06 `
  --guard-start-z 0.08 `
  --guard-min-policy-steps 0
```

Result:

| Scenario | Configuration | Success | Collision | Steps | Guard steps |
| --- | --- | ---: | ---: | ---: | ---: |
| visual_camera_control | guarded geometry blend 0.75 | 1 | 0 | 10 | 0 |
| hard bucket | no guard | 0 | 1 | 11 | 0 |
| hard bucket | guarded geometry blend 0.75 | 1 | 0 | 34 | 34 |

Trace CSVs include `guard_enabled`, `guard_active`, `policy_action_*`,
`guard_should_activate`, `guard_can_activate`, `guard_activated`,
`guard_down_blocked`, `guard_dist_xy`, `guard_z_above_target`,
`guarded_action_*`, `final_action_*`, `raw_action_*`, and `safe_action_*`.
Full details are in `results\policy_inference_guarded_summary.md`.

Run the matching HD deployment demos:

```powershell
python scripts\demo_policy.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --seed 90005 `
  --device cpu `
  --output demos\guarded_deployment_hard_bucket_no_guard_z08_hd.gif `
  --trajectory-output demos\guarded_deployment_hard_bucket_no_guard_z08_trajectory.csv `
  --width 100 `
  --height 100 `
  --render-width 640 `
  --render-height 480 `
  --render-cameras overview wrist_cam `
  --fps 20 `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02
```

```powershell
python scripts\demo_policy.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --seed 90005 `
  --device cpu `
  --output demos\guarded_deployment_hard_bucket_guarded_z08_hd.gif `
  --trajectory-output demos\guarded_deployment_hard_bucket_guarded_z08_trajectory.csv `
  --width 100 `
  --height 100 `
  --render-width 640 `
  --render-height 480 `
  --render-cameras overview wrist_cam `
  --fps 20 `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-name hard_full_light_bucket `
  --guard-blend 0.75 `
  --guard-start-xy 0.06 `
  --guard-start-z 0.08 `
  --guard-min-policy-steps 0
```

```powershell
python scripts\demo_policy.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --seed 90000 `
  --device cpu `
  --output demos\guarded_deployment_full_light_guarded_z08_hd.gif `
  --trajectory-output demos\guarded_deployment_full_light_guarded_z08_trajectory.csv `
  --width 100 `
  --height 100 `
  --render-width 640 `
  --render-height 480 `
  --render-cameras overview wrist_cam `
  --fps 20 `
  --domain-randomization-level full_light_geometry `
  --control-action-scale-range 0.8 1.2 `
  --control-action-noise-std-range 0 0.0008 `
  --control-action-delay-range 0 2 `
  --control-action-filter-alpha-range 0.55 1.0 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-name full_light_geometry `
  --guard-blend 0.75 `
  --guard-start-xy 0.06 `
  --guard-start-z 0.08 `
  --guard-min-policy-steps 0
```

The saved GIFs are `1280x480` because two `640x480` camera views are
concatenated. The summarized demo outcomes are in
`results\guarded_deployment_demo_summary.md`.

## Geometry Clearance Curriculum Scan

Run the targeted clearance scan over standard full-light geometry and the hard
delay/low-filter bucket:

```powershell
python scripts\scan_geometry_clearance.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --tier-preset all `
  --scenario-preset targeted `
  --episodes 30 `
  --seed 930000 `
  --device cpu `
  --output-csv results\geometry_clearance_scan_targeted_30ep.csv `
  --output-md results\geometry_clearance_scan_targeted_30ep.md `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02
```

Run the full-contact clearance scan:

```powershell
python scripts\scan_geometry_clearance.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --tier-preset all `
  --scenario-preset full_contact `
  --episodes 30 `
  --seed 930000 `
  --device cpu `
  --output-csv results\geometry_clearance_scan_full_contact_30ep.csv `
  --output-md results\geometry_clearance_scan_full_contact_30ep.md `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02
```

Guarded blend `0.75` result:

| Tier | Mean clearance | Full light | Hard bucket | Full contact |
| --- | ---: | ---: | ---: | ---: |
| wide_legacy | 14.9 mm | 0.600 | 0.400 | 0.633 |
| medium | 9.9 mm | 0.667 | 0.333 | 0.567 |
| narrow | 6.9 mm | 0.533 | 0.367 | 0.600 |
| tight | 4.4 mm | 0.467 | 0.267 | 0.533 |

Use `medium` as the next curriculum target, mixed with current wide clearance.
Do not jump directly to narrow/tight as the default distribution; hard-control
success is still too low. Full details are in
`results\geometry_clearance_scan_summary.md`.

## Medium Clearance Dataset Diagnostics

Expert collection now writes v2 diagnostic arrays into new `.npz` files:
`hole_half_size`, `peg_radius`, `hole_clearance`, `hole_center_offset`,
control scale/noise/delay/filter values, fixture/table height offsets, and
contact/dynamics multipliers. Metadata also records success, collision,
timeout, kept-episode rates, array shapes, and summary diagnostics.

Inspect any image expert dataset:

```powershell
python scripts\inspect_image_expert_dataset.py `
  --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_smoke_oracle.npz `
  --output-md results\image_expert_medium_guarded_success_smoke_inspection.md `
  --output-csv results\image_expert_medium_guarded_success_smoke_inspection.csv
```

Medium clearance guarded smoke:

```powershell
python scripts\collect_image_expert_dataset.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_smoke_oracle.npz `
  --samples 500 `
  --seed 940000 `
  --image-width 100 `
  --image-height 100 `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --expert-action-gain 1.0 `
  --oracle-mode guarded_two_stage `
  --guarded-align-xy-tolerance 0.025 `
  --guarded-insert-xy-tolerance 0.005 `
  --guarded-retract-xy-tolerance 0.012 `
  --guarded-preinsert-height 0.000 `
  --guarded-max-xy-action 0.005 `
  --guarded-max-down-action 0.0035 `
  --guarded-max-up-action 0.005 `
  --guarded-prediction-steps 1.0 `
  --rollout-noise-std 0.0005 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --domain-randomization-level full_light_geometry `
  --geometry-hole-half-size-range 0.020 0.024 `
  --geometry-peg-radius-range 0.0115 0.0125 `
  --success-only `
  --compressed
```

Medium clearance hard-control guarded smoke:

```powershell
python scripts\collect_image_expert_dataset.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --output datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_smoke_oracle.npz `
  --samples 500 `
  --seed 941000 `
  --image-width 100 `
  --image-height 100 `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --expert-action-gain 1.0 `
  --oracle-mode guarded_two_stage `
  --guarded-align-xy-tolerance 0.025 `
  --guarded-insert-xy-tolerance 0.005 `
  --guarded-retract-xy-tolerance 0.012 `
  --guarded-preinsert-height 0.000 `
  --guarded-max-xy-action 0.005 `
  --guarded-max-down-action 0.0035 `
  --guarded-max-up-action 0.005 `
  --guarded-prediction-steps 1.0 `
  --rollout-noise-std 0.0005 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --domain-randomization-level full_light_geometry `
  --geometry-hole-half-size-range 0.020 0.024 `
  --geometry-peg-radius-range 0.0115 0.0125 `
  --control-action-scale-range 0.8 1.1 `
  --control-action-noise-std-range 0 0.00025 `
  --control-action-delay-range 2 2 `
  --control-action-filter-alpha-range 0.55 0.70 `
  --success-only `
  --compressed
```

Checked 500-sample smoke result:

| Dataset | Episodes | Success | Collision | Mean clearance | Mean delay | Mean alpha |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| medium guarded success | 58 | 0.603 | 0.345 | 9.93 mm | 1.11 | 0.777 |
| medium hard guarded success | 87 | 0.299 | 0.701 | 10.36 mm | 2.00 | 0.627 |

Full 50k checked result:

| Dataset | Episodes | Success | Collision | Mean clearance | Mean delay | Mean alpha |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| medium guarded success 50k | 5142 | 0.579 | 0.385 | 10.05 mm | 0.88 | 0.785 |
| medium hard guarded success 50k | 8096 | 0.345 | 0.647 | 10.11 mm | 2.00 | 0.628 |

The full datasets are:

```text
datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_50k_oracle.npz
datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_50k_oracle.npz
```

Inspect the full datasets:

```powershell
python scripts\inspect_image_expert_dataset.py --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_50k_oracle.npz --output-md results\image_expert_medium_guarded_success_50k_inspection.md --output-csv results\image_expert_medium_guarded_success_50k_inspection.csv
python scripts\inspect_image_expert_dataset.py --dataset datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_50k_oracle.npz --output-md results\image_expert_medium_hard_guarded_success_50k_inspection.md --output-csv results\image_expert_medium_hard_guarded_success_50k_inspection.csv
```

Medium replay continuation from the current 750k crop model:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --include-near-hole-crop --near-hole-crop-size 64 --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_50k_oracle.npz --dataset-weights 0.255 0.102 0.085 0.128 0.051 0.034 0.068 0.085 0.042 0.100 0.050 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2\sac_image_bc.zip --epochs 2 --samples-per-epoch 300000 --batch-size 512 --learning-rate 0.000001 --validation-batches 20 --approach-xy-tolerance 0.02 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --device cpu
```

Evaluate the medium replay candidate:

```powershell
python scripts\eval_matrix.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2.csv --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
python scripts\scan_geometry_clearance.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --agent sac --observation-mode image --include-near-hole-crop --near-hole-crop-size 64 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2\sac_image_bc.zip --tier-preset wide_medium --scenario-preset targeted --episodes 30 --seed 960000 --device cpu --output-csv results\geometry_clearance_scan_medium_replay_light_850k_targeted_30ep.csv --output-md results\geometry_clearance_scan_medium_replay_light_850k_targeted_30ep.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --approach-xy-tolerance 0.02
```

Medium replay result:

| Model | Clean | Visual camera | Visual camera control | Full light | Full contact |
| --- | ---: | ---: | ---: | ---: | ---: |
| medium replay e4 | 0.960 | 0.970 | 0.860 | 0.540 | 0.570 |
| medium replay light e2 | 0.970 | 0.980 | 0.900 | 0.550 | 0.660 |

Do not promote either medium replay as the current recommendation. The light
replay improves `full_contact_light`, but `full_light_geometry` remains below
the current 750k baseline. The next iteration should add near-failure
correction/DAgger-style data instead of only raising medium success-only replay
weight.

## Policy vs Oracle Correction Analysis

Use this analysis before collecting corrective data. It executes the learned
policy, queries the guarded two-stage oracle on the same pre-step state, and
logs the policy action, oracle action, correction vector, near-hole flag, and
whether the row falls in the last few steps before a collision or timeout.

```powershell
python scripts\analyze_policy_oracle_corrections.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --episodes 50 `
  --device cpu `
  --seed 980000 `
  --scenario-preset targeted `
  --tier-preset wide_medium `
  --output-csv results\policy_oracle_corrections_750k_targeted_50ep_steps.csv `
  --episode-output-csv results\policy_oracle_corrections_750k_targeted_50ep_episodes.csv `
  --output-md results\policy_oracle_corrections_750k_targeted_50ep.md
```

Checked result:

| Tier | Scenario | Success | Collision | Failure corr | Failure opposed | Policy down / oracle up |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| wide_legacy | full_light_geometry | 0.640 | 0.360 | 0.005 | 0.035 | 0.065 |
| wide_legacy | hard_full_light_bucket | 0.320 | 0.680 | 0.004 | 0.007 | 0.070 |
| medium | full_light_geometry | 0.660 | 0.300 | 0.005 | 0.189 | 0.125 |
| medium | hard_full_light_bucket | 0.400 | 0.560 | 0.004 | 0.076 | 0.059 |

The main signal is medium `full_light_geometry`: in the failure window,
policy-vs-oracle action opposition is much higher than wide
`full_light_geometry`. The next data collection pass should target rows with
`failure_window=True`, high `correction_norm`, and preferably `near_hole=True`
as DAgger-style corrective samples.

## Near-Hole Correction Dataset

Collect focused DAgger-style corrective samples from policy-visited failure
windows. This pass keeps only medium-clearance near-hole rows with
`correction_norm >= 0.006`.

```powershell
python scripts\collect_image_correction_dataset.py `
  --agent sac `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --output datasets\image_correction_ur5e_adapter_medium_targeted_near_hole_failure_window_10k_min006_oracle.npz `
  --samples 10000 `
  --max-episodes-per-config 9000 `
  --scenario-preset targeted `
  --tier-preset medium `
  --selection near_hole_failure_window `
  --failure-window-steps 10 `
  --near-hole-xy 0.03 `
  --near-hole-z 0.10 `
  --min-correction-norm 0.006 `
  --max-samples-per-episode 6 `
  --include-near-hole-crop `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --compressed
```

Inspect correction-specific signals:

```powershell
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\image_correction_ur5e_adapter_medium_targeted_near_hole_failure_window_10k_min006_oracle.npz `
  --output-md results\image_correction_medium_targeted_near_hole_failure_window_10k_min006_correction_inspection.md `
  --output-csv results\image_correction_medium_targeted_near_hole_failure_window_10k_min006_correction_inspection.csv
```

Actual collected dataset: `8405` samples from `16003` policy episodes. It is
more focused than the first 2k correction pass: near-hole rate `1.000`,
opposed-action rate `0.470`, mean correction norm `0.00960`.

The best correction candidate so far is the 8% correction, 1 epoch variant:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --datasets datasets\image_expert_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_hard_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_50k_seed130k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_visual_camera_control_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz datasets\image_correction_ur5e_adapter_medium_targeted_near_hole_failure_window_10k_min006_oracle.npz `
  --dataset-weights 0.276 0.110 0.092 0.138 0.055 0.037 0.074 0.092 0.046 0.080 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --output checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1\sac_image_bc.zip `
  --metadata-output results\training_metadata_correction_nearhole_8k_w08_replay_858k_oracle_e1.json `
  --epochs 1 `
  --samples-per-epoch 200000 `
  --batch-size 512 `
  --learning-rate 0.0000008 `
  --validation-batches 20 `
  --approach-xy-tolerance 0.02 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --device cpu
```

Evaluate it:

```powershell
python scripts\eval_matrix.py `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --agent sac `
  --observation-mode image `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1\sac_image_bc.zip `
  --episodes 100 `
  --seed 90000 `
  --device cpu `
  --output-csv results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1.csv `
  --output-md results\eval_matrix_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1.md `
  --approach-xy-tolerance 0.02 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01
```

Correction experiment result:

| Model | Clean | Visual camera | Control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| 750k baseline | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 |
| correction 8k w08 e1 | 0.980 | 0.980 | 0.900 | 0.590 | 0.630 |
| correction 8k w05 e2 | 0.980 | 0.970 | 0.930 | 0.570 | 0.630 |
| correction 8k w08 e2 | 0.960 | 0.950 | 0.910 | 0.590 | 0.630 |

Do not promote the correction models yet. The e1 variant is a useful candidate,
but the gain is modest and not consistent across the medium/hard geometry scan.
Full details are in `results\correction_nearhole_8k_experiment_summary.md`.

Outcome-specific correction collection is supported with
`--episode-outcome-filter`. This is useful for diagnostics because collision
and timeout failure windows have different action-disagreement profiles:

```powershell
python scripts\collect_image_correction_dataset.py `
  --agent sac `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --output datasets\image_correction_ur5e_adapter_wide_medium_targeted_near_hole_collision_window_4k_min006_oracle.npz `
  --samples 4000 `
  --max-episodes-per-config 5000 `
  --scenario-preset targeted `
  --tier-preset wide_medium `
  --selection near_hole_failure_window `
  --episode-outcome-filter collision `
  --failure-window-steps 10 `
  --near-hole-xy 0.03 `
  --near-hole-z 0.10 `
  --min-correction-norm 0.006 `
  --max-samples-per-episode 6 `
  --include-near-hole-crop `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --compressed
```

```powershell
python scripts\collect_image_correction_dataset.py `
  --agent sac `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml `
  --output datasets\image_correction_ur5e_adapter_wide_medium_targeted_near_hole_timeout_window_4k_min006_oracle.npz `
  --samples 4000 `
  --max-episodes-per-config 5000 `
  --scenario-preset targeted `
  --tier-preset wide_medium `
  --selection near_hole_failure_window `
  --episode-outcome-filter timeout `
  --failure-window-steps 10 `
  --near-hole-xy 0.03 `
  --near-hole-z 0.10 `
  --min-correction-norm 0.006 `
  --max-samples-per-episode 6 `
  --include-near-hole-crop `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --approach-xy-tolerance 0.02 `
  --compressed
```

Outcome-split result:

| Model | Clean | Visual camera | Control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| 750k baseline | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 |
| outcome split w04w04 e1 | 0.980 | 0.980 | 0.910 | 0.560 | 0.600 |
| outcome split w06w02 e1 | 0.980 | 0.980 | 0.900 | 0.580 | 0.590 |

Do not promote outcome-split correction models. Timeout correction rows are
diagnostically strong but conflict with success-replay BC when oversampled.
Full details are in `results\correction_outcome_split_6k_experiment_summary.md`.

## Current Recommended UR5e Model

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip
```

This is the current recommended crop-enabled UR5e adapter model. Use
`--include-near-hole-crop --near-hole-crop-size 64` for training, evaluation,
demo, and deployment-style inference with this checkpoint.

## Current Best Simplified Sidecam Model

```text
checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip
```

This is the delay-robust image BC model for the older simplified sidecam setup.

## Reproduce Current Best Training

Collect the delay-robust expert dataset:

```powershell
python scripts\collect_image_expert_dataset.py --output datasets\image_expert_50k_sidecam_visual_camera_control_delay3_oracle.npz --samples 50000 --expert-action-gain 0.22 --rollout-noise-std 0.0005 --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 3 --control-action-filter-alpha-range 1 1 --compressed
```

Continue image actor behavior cloning:

```powershell
python scripts\pretrain_image_actor_bc.py --dataset datasets\image_expert_50k_sidecam_visual_camera_control_delay3_oracle.npz --model checkpoints_image_bc_50k_sidecam_visual_camera_control_oracle\sac_image_bc.zip --output checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --epochs 10 --batch-size 256 --learning-rate 0.000012 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

## Evaluate

Clean environment:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Default control randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control
```

High-delay control randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 1 1 --control-action-noise-std-range 0 0 --control-action-delay-range 0 3 --control-action-filter-alpha-range 1 1
```

High combined control randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 0.75 1.25 --control-action-noise-std-range 0 0.0015 --control-action-delay-range 0 3 --control-action-filter-alpha-range 0.4 1.0
```

Light geometry randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level full_light_geometry
```

Current strongest default full randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level full_contact_light
```

High contact/dynamics randomization:

```powershell
python scripts\eval_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level full_contact_light --contact-friction-multiplier-range 0.5 1.5 --contact-solref-time-multiplier-range 0.6 1.6 --contact-solref-damping-multiplier-range 0.6 1.5 --contact-solimp-width-multiplier-range 0.5 1.5 --dynamics-joint-damping-multiplier-range 0.6 1.5 --dynamics-actuator-kp-multiplier-range 0.6 1.4
```

## Demo

`--width` and `--height` are the policy observation image size. Use
`--render-width` and `--render-height` to control the saved GIF resolution.
Use `--trajectory-output` to save per-step diagnostics as CSV. Use
`--render-cameras overview wrist_cam` to concatenate multiple camera views.

Recommended full-contact-light image demo:

```powershell
python scripts\demo_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --output demos\image_bc_sidecam_full_contact_light_hd.gif --width 100 --height 100 --render-width 640 --render-height 480 --fps 20 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level full_contact_light
```

Multi-camera diagnostic demo with trajectory CSV:

```powershell
python scripts\demo_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --output demos\image_bc_sidecam_full_contact_light_multicam_hd.gif --trajectory-output results\demo_full_contact_light_trace.csv --width 100 --height 100 --render-width 640 --render-height 480 --render-cameras overview wrist_cam --fps 20 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level full_contact_light
```

High combined control demo:

```powershell
python scripts\demo_policy.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --output demos\image_bc_sidecam_visual_camera_control_delay3_hd.gif --width 100 --height 100 --render-width 640 --render-height 480 --fps 20 --device cpu --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --domain-randomization-level visual_camera_control --control-action-scale-range 0.75 1.25 --control-action-noise-std-range 0 0.0015 --control-action-delay-range 0 3 --control-action-filter-alpha-range 0.4 1.0
```

State baseline demo:

```powershell
python scripts\demo_policy.py --agent sac --observation-mode state --model checkpoints_state_tuned_v21_bc_mid\sac_state_bc.zip --output demos\state_bc_high_precision_hd.gif --render-width 640 --render-height 480 --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

## Policy Inference Interface

Run the current best policy through the deployment-style MuJoCo inference
interface with action limiting, workspace limiting, and per-step CSV logging:

```powershell
python scripts\run_policy_inference.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 1 --output results\policy_inference_trace.csv --device cpu --domain-randomization-level full_contact_light --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

The default `--control-frequency-hz 50` matches the current MuJoCo control
period of `0.02 s`. Use an explicit value such as `20` when prototyping a real
robot dry-run loop.
Internally this path uses `PolicyInferenceSession` plus
`MujocoObservationProvider` and `MujocoActionExecutor`; real hardware should
replace only the provider/executor layer.
Guarded deployment now follows the same adapter structure:
`MujocoGuardStateProvider` converts MuJoCo telemetry into
`GuardedDeploymentState`, while `RealGuardStateProvider` does the same for
real-robot dry-run telemetry.

Use a smoother action safety layer:

```powershell
python scripts\run_policy_inference.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 1 --output results\policy_inference_trace_smooth.csv --device cpu --domain-randomization-level full_contact_light --success-xy-tolerance 0.005 --success-z-tolerance 0.01 --safety-action-filter-alpha 0.6
```

## Real Backend Dry Run

UR5e branch note: the current recommended real dry-run config lives under
`configs\real\ur5e\`. It enables `include_near_hole_crop: true`, because the
current recommended UR5e image policy expects both `cam_image` and
`near_hole_crop`.

Prepare an ignored local real-data read-only session:

```powershell
python scripts\prepare_real_ur5e_session.py `
  --session-id real_ur5e_YYYYMMDD `
  --ur-host <UR5E_IP> `
  --camera-device-index 0 `
  --overwrite
```

This writes:

- `configs\real\ur5e\real_ur5e_YYYYMMDD_local.yaml`
- `results\real\ur5e\real_ur5e_YYYYMMDD\COMMANDS.md`

Edit the local YAML before running the generated commands. The strict real
preflight now requires measured `crop_xywh`, camera intrinsics, and
`tool0_to_camera_*` values:

Tune camera crop and orientation from recorded frames:

```powershell
python scripts\inspect_real_camera_crop.py `
  --input results\real\ur5e\real_ur5e_YYYYMMDD\camera_tuning_frames `
  --output-dir results\real\ur5e\real_ur5e_YYYYMMDD\crop_inspection `
  --summary-md results\real\ur5e\real_ur5e_YYYYMMDD\crop_inspection_summary.md `
  --stats-output results\real\ur5e\real_ur5e_YYYYMMDD\crop_inspection_stats.csv `
  --output-json results\real\ur5e\real_ur5e_YYYYMMDD\crop_inspection_summary.json `
  --auto-crop-fractions 0.50 0.65 0.80 `
  --auto-offset-fraction 0.15 `
  --include-flips `
  --max-combinations 240
```

Use the top-ranked candidate only as a starting point. Inspect the preview
sheets before copying the config snippet.

```powershell
python scripts\check_real_deployment_config.py `
  --config configs\real\ur5e\real_ur5e_YYYYMMDD_local.yaml `
  --target-calibration results\real\ur5e\real_ur5e_YYYYMMDD\target_calibration.yaml `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --require-camera-calibration `
  --require-image-crop `
  --fail-on-warn `
  --output-md results\real\ur5e\real_ur5e_YYYYMMDD\config_check.md `
  --output-json results\real\ur5e\real_ur5e_YYYYMMDD\config_check.json
```

UR5e read-only software gate smoke:

```powershell
python scripts\check_real_deployment_config.py `
  --config configs\real\ur5e\synthetic_smoke.yaml `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --output-md results\real\ur5e\smoke\config_check.md `
  --output-json results\real\ur5e\smoke\config_check.json

python scripts\run_real_dryrun_preflight.py `
  --config configs\real\ur5e\synthetic_smoke.yaml `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip `
  --max-steps 4 `
  --trace-output results\real\ur5e\smoke\dryrun_trace.csv `
  --check-output-md results\real\ur5e\smoke\dryrun_check.md `
  --check-output-json results\real\ur5e\smoke\dryrun_check.json `
  --summary-md results\real\ur5e\smoke\dryrun_summary.md `
  --allow-action-limited

python scripts\check_real_motion_readiness.py `
  --bundle-summary-json results\real\ur5e\smoke\capture_bundle_summary.json `
  --allow-synthetic `
  --allow-smoke-paths `
  --output-md results\real\ur5e\smoke\motion_readiness_synthetic_allowed.md `
  --output-json results\real\ur5e\smoke\motion_readiness_synthetic_allowed.json

python scripts\inspect_real_camera_crop.py `
  --synthetic-smoke `
  --output-dir results\real\ur5e\smoke\crop_inspection `
  --stats-output results\real\ur5e\smoke\crop_inspection_stats.csv `
  --summary-md results\real\ur5e\smoke\crop_inspection_summary.md `
  --output-json results\real\ur5e\smoke\crop_inspection_summary.json `
  --max-frames 3 `
  --auto-crop-fractions 0.60 0.80 `
  --auto-offset-fraction 0.10 `
  --include-flips `
  --max-combinations 160
```

Checked UR5e real smoke outputs:

| Gate | Result | Summary |
| --- | --- | --- |
| config check | PASS | `results\real\ur5e\smoke\config_check.md` |
| dry-run preflight | PASS | `results\real\ur5e\smoke\dryrun_summary.md` |
| crop/orientation inspection | PASS | `results\real\ur5e\smoke\crop_inspection_summary.md` |
| synthetic capture bundle | PASS | `results\real\ur5e\smoke\capture_bundle_summary.md` |
| readiness with synthetic allowed | PASS | `results\real\ur5e\smoke\motion_readiness_synthetic_allowed.md` |
| readiness default synthetic gate | FAIL expected | `results\real\ur5e\smoke\motion_readiness_synthetic_expected_fail.md` |

Check the static real deployment configuration before recording real camera or
UR TCP data. This does not connect to hardware:

```powershell
python scripts\check_real_deployment_config.py `
  --config configs\real_ur5_dryrun.yaml `
  --target-calibration configs\real_hole_target_calibration.yaml `
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip `
  --expected-pose-frame robot_base `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --output-md results\real_deployment_config_check.md `
  --output-json results\real_deployment_config_check.json
```

Smoke-test the static configuration checker without hardware:

```powershell
python scripts\check_real_deployment_config.py `
  --config configs\real_ur5_dryrun.yaml `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --output-md results\real_deployment_config_check_synthetic_smoke.md `
  --output-json results\real_deployment_config_check_synthetic_smoke.json
```

Validate the real-robot provider/executor path without loading a model or moving
hardware:

```powershell
python scripts\run_real_policy_dryrun.py --zero-policy --episodes 1 --max-steps 5 --output results\real_policy_dryrun_zero_trace.csv
```

Run the trained image policy against a real-camera image or image folder while
still using a dry-run UR5 executor:

```powershell
python scripts\run_real_policy_dryrun.py --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --image-dir path\to\camera_frames --episodes 1 --output results\real_policy_dryrun_trace.csv
```

Run the real dry-run path with guarded final insertion enabled. This still does
not move hardware; it only checks the provider, policy/zero-policy, safety
filter, guarded controller, and trace logging path:

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 2 `
  --peg-tip-pos 0.55 0.05 0.72 `
  --target-pos 0.55 0.05 0.65 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_guarded_smoke.csv
```

Guarded interface refactor details and smoke results are in
`results\guarded_deployment_interface_refactor_summary.md`.

Run the same guarded dry-run path with a per-step pose CSV instead of static
`--peg-tip-pos` and `--target-pos` values:

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --pose-trace configs\real_pose_trace_smoke.csv `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_pose_trace_guarded_smoke.csv
```

Pose trace CSVs should provide `peg_tip_x/y/z` and `target_x/y/z` in meters in
the same frame. `tcp_x/y/z` and `hole_x/y/z` are accepted aliases. The trace
output includes `pose_source`, `pose_frame`, `pose_step`, and `pose_timestamp`.
Details are in `results\real_pose_trace_dryrun_summary.md`.

Run the dry-run path with UR-style TCP pose traces. `tcp_rx/ry/rz` are UR
rotation-vector values in radians, and `--tcp-to-peg-tip-xyz` is the measured
offset from the active TCP/tool frame to the peg tip:

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-pose-trace configs\real_tcp_pose_trace_smoke.csv `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_tcp_pose_guarded_smoke.csv
```

Run TCP trace replay with a separate fixed hole/fixture calibration file. This
is the preferred dry-run structure when TCP pose comes from UR RTDE and target
pose comes from fixture registration or hand-eye calibration:

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-pose-trace configs\real_tcp_pose_trace_no_target_smoke.csv `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_target_calibration_guarded_smoke.csv
```

The output trace includes `target_source`, `target_frame`, and
`target_timestamp`. Details are in
`results\real_target_calibration_dryrun_summary.md`.

Check a dry-run trace before using it for real deployment decisions. The
checker validates required trace columns, pose/target frames and sources,
safe-action limits, workspace clipping, guard activation behavior, distance
consistency, and optional TCP-to-peg-tip conversion:

```powershell
python scripts\check_real_dryrun_trace.py `
  --trace results\real_policy_dryrun_target_calibration_guarded_smoke.csv `
  --output-md results\real_dryrun_trace_check_target_calibration_smoke.md `
  --max-safe-action 0.002 `
  --expected-pose-frame robot_base `
  --require-nonstatic-target `
  --tcp-to-peg-tip-xyz 0 0 -0.11
```

For older TCP-pose and direct pose-trace smoke files:

```powershell
python scripts\check_real_dryrun_trace.py `
  --trace results\real_policy_dryrun_tcp_pose_guarded_smoke.csv `
  --output-md results\real_dryrun_trace_check_tcp_pose_smoke.md `
  --max-safe-action 0.002 `
  --expected-pose-frame robot_base `
  --tcp-to-peg-tip-xyz 0 0 -0.11

python scripts\check_real_dryrun_trace.py `
  --trace results\real_policy_dryrun_pose_trace_guarded_smoke.csv `
  --output-md results\real_dryrun_trace_check_pose_trace_smoke.md `
  --max-safe-action 0.002 `
  --expected-pose-frame robot_base
```

The current checker smoke summary is in
`results\real_dryrun_trace_checker_summary.md`.

Build a fixed hole/fixture target calibration file from repeated target
measurements. The measurement CSV should contain `target_x/y/z` or `hole_x/y/z`
in meters, plus an optional frame column such as `target_frame` or
`pose_frame`:

Record repeated hole/target measurements from UR RTDE. This is read-only: move
the robot manually or by teach pendant so that the active TCP is at the measured
hole target point, then record samples. If the active TCP is not exactly the
target point, provide the measured TCP-frame offset with `--tcp-to-target-xyz`:

```powershell
python scripts\record_ur_rtde_target_measurements.py `
  --host 192.168.0.10 `
  --samples 20 `
  --frequency-hz 5 `
  --pose-frame robot_base `
  --target-id real_hole `
  --tcp-to-target-xyz 0 0 0 `
  --output results\real_hole_measurements.csv `
  --summary-md results\real_hole_measurements_summary.md
```

Smoke-test the target measurement recorder without hardware:

```powershell
python scripts\record_ur_rtde_target_measurements.py `
  --synthetic-smoke `
  --samples 6 `
  --frequency-hz 100 `
  --output results\real_hole_measurements_synthetic_smoke.csv `
  --summary-md results\real_hole_measurements_synthetic_smoke_summary.md
```

Convert the recorded measurement CSV into the fixed target calibration consumed
by the real dry-run and preflight scripts:

```powershell
python scripts\make_real_target_calibration.py `
  --input-csv results\real_hole_measurements.csv `
  --output configs\real_hole_target_calibration.yaml `
  --summary-md results\real_target_calibration_builder_summary.md `
  --target-id real_hole `
  --target-source fixture_calibration `
  --pose-frame robot_base `
  --method mean
```

If you already have one trusted measured target position:

```powershell
python scripts\make_real_target_calibration.py `
  --target-pos 0.550 0.050 0.650 `
  --output configs\real_hole_target_calibration.yaml `
  --summary-md results\real_target_calibration_builder_summary.md
```

Smoke-test the builder without hardware:

```powershell
python scripts\make_real_target_calibration.py `
  --synthetic-smoke `
  --synthetic-input-output results\real_target_calibration_builder_synthetic_input.csv `
  --output configs\real_hole_target_calibration_generated_smoke.yaml `
  --summary-md results\real_target_calibration_builder_smoke_summary.md
```

Run the complete real dry-run preflight gate. This wrapper first runs
`run_real_policy_dryrun.py`, then runs `check_real_dryrun_trace.py`, and finally
writes a compact summary. It still does not command robot motion:

```powershell
python scripts\run_real_dryrun_preflight.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-pose-trace configs\real_tcp_pose_trace_no_target_smoke.csv `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --trace-output results\real_policy_dryrun_preflight_target_calibration_smoke.csv `
  --check-output-md results\real_dryrun_preflight_target_calibration_check.md `
  --summary-md results\real_dryrun_preflight_target_calibration_summary.md
```

For a real preflight, replace the smoke TCP CSV with a trace recorded from UR
RTDE and replace the target calibration file with the measured fixture/hole
calibration. The default preflight requires non-static pose and target sources,
uses guarded final insertion, and fails on checker errors.

Record a read-only UR RTDE TCP pose trace for later dry-run replay. This script
does not command robot motion:

```powershell
python scripts\record_ur_rtde_tcp_pose_trace.py `
  --host 192.168.0.10 `
  --samples 200 `
  --frequency-hz 20 `
  --pose-frame robot_base `
  --target-pos 0.55 0.05 0.65 `
  --output results\ur_rtde_tcp_pose_trace.csv
```

When the hole target comes from a separate fixture calibration, omit embedded
target columns so the dry-run path uses `--target-calibration` instead of a
target pose inside the TCP trace:

```powershell
python scripts\record_ur_rtde_tcp_pose_trace.py `
  --host 192.168.0.10 `
  --samples 200 `
  --frequency-hz 20 `
  --pose-frame robot_base `
  --no-target-columns `
  --output results\ur_rtde_tcp_pose_trace.csv
```

Smoke-test the recorder without a robot:

```powershell
python scripts\record_ur_rtde_tcp_pose_trace.py `
  --synthetic-smoke `
  --samples 4 `
  --frequency-hz 100 `
  --output results\ur_rtde_tcp_pose_trace_synthetic_smoke.csv
```

Record raw frames from a real USB/RTSP camera before running the camera
preflight. Live recording uses OpenCV; install it if needed with
`python -m pip install opencv-python`:

```powershell
python scripts\record_real_camera_frames.py `
  --device-index 0 `
  --frames 20 `
  --frequency-hz 5 `
  --warmup-frames 10 `
  --output-dir results\real_camera_frames `
  --stats-output results\real_camera_frames_stats.csv `
  --summary-md results\real_camera_frames_summary.md
```

For an RTSP or other OpenCV source, replace `--device-index 0` with:

```powershell
--source rtsp://user:password@camera-host/stream
```

Smoke-test the frame recorder without a camera:

```powershell
python scripts\record_real_camera_frames.py `
  --synthetic-smoke `
  --frames 4 `
  --frequency-hz 100 `
  --output-dir results\real_camera_frames_synthetic_smoke `
  --stats-output results\real_camera_frames_synthetic_smoke_stats.csv `
  --summary-md results\real_camera_frames_synthetic_smoke_summary.md
```

Preview preprocessing for a real camera frame directory:

```powershell
python scripts\preprocess_camera_frames.py --input path\to\camera_frames --output-dir results\preprocessed_camera_frames --stats-output results\preprocessed_camera_frames_stats.csv --width 100 --height 100 --crop-xywh 0 0 640 480 --rotate-k 0
```

Run the real camera preflight before feeding images to the policy. This checks
that frames are readable, preprocessing produces the expected `100x100x1`
policy input, images are not blank or saturated, and adjacent frames are not
unexpectedly identical:

```powershell
python scripts\check_real_camera_preflight.py `
  --input path\to\camera_frames `
  --output-dir results\real_camera_preflight_frames `
  --stats-output results\real_camera_preflight_stats.csv `
  --summary-md results\real_camera_preflight_summary.md `
  --width 100 `
  --height 100 `
  --crop-xywh 0 0 640 480 `
  --rotate-k 0 `
  --max-frames 20
```

Smoke-test the camera preflight without real frames:

```powershell
python scripts\check_real_camera_preflight.py `
  --synthetic-smoke `
  --synthetic-frames 4 `
  --output-dir results\real_camera_preflight_synthetic_smoke_frames `
  --stats-output results\real_camera_preflight_synthetic_smoke_stats.csv `
  --summary-md results\real_camera_preflight_synthetic_smoke_summary.md `
  --output-json results\real_camera_preflight_synthetic_smoke_summary.json `
  --crop-xywh 20 10 160 120 `
  --rotate-k 1 `
  --flip-horizontal
```

Smoke-test preprocessing without camera frames:

```powershell
python scripts\preprocess_camera_frames.py --synthetic-smoke --output-dir results\preprocessed_camera_frames_smoke --stats-output results\preprocessed_camera_frames_smoke_stats.csv --crop-xywh 20 10 160 120 --rotate-k 1 --flip-horizontal
```

Run the combined real camera + policy dry-run preflight gate. This first checks
the camera frames and preprocessing, then feeds the same frames into the real
policy dry-run preflight with TCP pose trace and target calibration checks. It
still does not command robot motion:

```powershell
python scripts\run_real_camera_policy_preflight.py `
  --image-input path\to\camera_frames `
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip `
  --episodes 1 `
  --max-steps 20 `
  --tcp-pose-trace results\ur_rtde_tcp_pose_trace.csv `
  --target-calibration configs\real_hole_target_calibration.yaml `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --camera-crop-xywh 0 0 640 480 `
  --camera-rotate-k 0 `
  --expected-pose-frame robot_base `
  --summary-md results\real_camera_policy_preflight_summary.md `
  --output-json results\real_camera_policy_preflight_summary.json
```

Smoke-test the combined preflight without real hardware or live camera input:

```powershell
python scripts\run_real_camera_policy_preflight.py `
  --image-input results\real_camera_frames_synthetic_smoke `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-pose-trace configs\real_tcp_pose_trace_no_target_smoke.csv `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --camera-max-frames 4 `
  --camera-output-dir results\real_camera_policy_preflight_synthetic_smoke_camera_frames `
  --camera-stats-output results\real_camera_policy_preflight_synthetic_smoke_camera_stats.csv `
  --camera-summary-md results\real_camera_policy_preflight_synthetic_smoke_camera_summary.md `
  --camera-output-json results\real_camera_policy_preflight_synthetic_smoke_camera_summary.json `
  --dryrun-trace-output results\real_policy_dryrun_camera_policy_preflight_synthetic_smoke_trace.csv `
  --dryrun-check-output-md results\real_dryrun_camera_policy_preflight_synthetic_smoke_check.md `
  --dryrun-check-output-json results\real_dryrun_camera_policy_preflight_synthetic_smoke_check.json `
  --dryrun-summary-md results\real_dryrun_camera_policy_preflight_synthetic_smoke_summary.md `
  --summary-md results\real_camera_policy_preflight_synthetic_smoke_summary.md `
  --output-json results\real_camera_policy_preflight_synthetic_smoke_summary.json
```

Run a read-only capture bundle and preflight it in one command. The bundle now
runs `check_real_deployment_config.py` first, then records camera frames and UR
TCP poses in parallel, and finally runs `run_real_camera_policy_preflight.py`.
If the config check fails, it skips recorder startup and still writes a summary.
Arguments not recognized by the bundle script, such as `--model`,
`--zero-policy`, `--tcp-to-peg-tip-xyz`, and camera preprocessing flags, are
forwarded to the combined preflight. The bundle generates one session id and
writes it into both recorder CSVs; pass `--session-id` only when you want a
specific id in the logs:

```powershell
python scripts\run_real_capture_bundle.py `
  --config configs\real_ur5_dryrun.yaml `
  --config-check-output-md results\real_capture_bundle_config_check.md `
  --config-check-output-json results\real_capture_bundle_config_check.json `
  --record-camera-device-index 0 `
  --record-camera-frames 20 `
  --record-camera-frequency-hz 5 `
  --record-camera-warmup-frames 10 `
  --record-tcp-host 192.168.0.10 `
  --record-tcp-samples 20 `
  --record-tcp-frequency-hz 20 `
  --record-tcp-pose-frame robot_base `
  --target-calibration configs\real_hole_target_calibration.yaml `
  --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip `
  --episodes 1 `
  --max-steps 20 `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --camera-crop-xywh 0 0 640 480 `
  --camera-rotate-k 0 `
  --expected-pose-frame robot_base `
  --summary-md results\real_capture_bundle_summary.md `
  --preflight-summary-md results\real_capture_bundle_preflight_summary.md `
  --preflight-output-json results\real_capture_bundle_preflight_summary.json
```

Smoke-test the capture bundle without a robot or live camera:

```powershell
python scripts\run_real_capture_bundle.py `
  --session-id synthetic_config_gate_smoke `
  --config configs\real_ur5_dryrun.yaml `
  --config-check-output-md results\real_capture_bundle_config_gate_synthetic_smoke_config_check.md `
  --config-check-output-json results\real_capture_bundle_config_gate_synthetic_smoke_config_check.json `
  --record-camera-synthetic-smoke `
  --record-camera-frames 4 `
  --record-camera-frequency-hz 100 `
  --record-camera-output-dir results\real_capture_bundle_config_gate_synthetic_smoke_camera_frames `
  --record-camera-stats-output results\real_capture_bundle_config_gate_synthetic_smoke_camera_stats.csv `
  --record-camera-summary-md results\real_capture_bundle_config_gate_synthetic_smoke_camera_record_summary.md `
  --record-tcp-synthetic-smoke `
  --record-tcp-samples 4 `
  --record-tcp-frequency-hz 100 `
  --record-tcp-output results\real_capture_bundle_config_gate_synthetic_smoke_tcp_pose_trace.csv `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --camera-max-frames 4 `
  --camera-output-dir results\real_capture_bundle_config_gate_synthetic_smoke_preflight_camera_frames `
  --camera-stats-output results\real_capture_bundle_config_gate_synthetic_smoke_preflight_camera_stats.csv `
  --camera-summary-md results\real_capture_bundle_config_gate_synthetic_smoke_preflight_camera_summary.md `
  --camera-output-json results\real_capture_bundle_config_gate_synthetic_smoke_preflight_camera_summary.json `
  --dryrun-trace-output results\real_capture_bundle_config_gate_synthetic_smoke_policy_trace.csv `
  --dryrun-check-output-md results\real_capture_bundle_config_gate_synthetic_smoke_dryrun_check.md `
  --dryrun-check-output-json results\real_capture_bundle_config_gate_synthetic_smoke_dryrun_check.json `
  --dryrun-summary-md results\real_capture_bundle_config_gate_synthetic_smoke_dryrun_summary.md `
  --summary-md results\real_capture_bundle_config_gate_synthetic_smoke_summary.md `
  --output-json results\real_capture_bundle_config_gate_synthetic_smoke_summary.json `
  --preflight-summary-md results\real_capture_bundle_config_gate_synthetic_smoke_preflight_summary.md `
  --preflight-output-json results\real_capture_bundle_config_gate_synthetic_smoke_preflight_summary.json
```

Checked gate smoke outputs:

| Scenario | Expected exit | Summary |
| --- | ---: | --- |
| config pass | 0 | `results\real_capture_bundle_config_gate_synthetic_smoke_summary.md` |
| missing config | 1 | `results\real_capture_bundle_config_gate_failure_smoke_summary.md` |

After a real read-only capture bundle passes, run the real motion readiness
gate before allowing any robot motion. This still only reads the bundle summary
and generated preflight reports; it does not connect to the robot:

```powershell
python scripts\check_real_motion_readiness.py `
  --bundle-summary-json results\real_capture_bundle_summary.json `
  --output-md results\real_motion_readiness_check.md `
  --output-json results\real_motion_readiness_check.json `
  --min-camera-frames 20 `
  --min-tcp-samples 20 `
  --min-dryrun-rows 2 `
  --expected-pose-frame robot_base `
  --expected-target-source fixture_calibration `
  --expected-guard-blend 0.75 `
  --max-safe-action 0.002
```

The readiness checker intentionally fails synthetic/zero-policy bundles unless
they are explicitly allowed. Smoke-test that behavior:

```powershell
python scripts\check_real_motion_readiness.py `
  --bundle-summary-json results\real_capture_bundle_config_gate_synthetic_smoke_summary.json `
  --output-md results\real_motion_readiness_synthetic_expected_fail.md `
  --output-json results\real_motion_readiness_synthetic_expected_fail.json
```

Smoke-test the checker itself by explicitly allowing synthetic inputs:

```powershell
python scripts\check_real_motion_readiness.py `
  --bundle-summary-json results\real_capture_bundle_config_gate_synthetic_smoke_summary.json `
  --allow-synthetic `
  --allow-zero-policy `
  --allow-smoke-paths `
  --min-camera-frames 4 `
  --min-tcp-samples 4 `
  --min-dryrun-rows 4 `
  --output-md results\real_motion_readiness_synthetic_smoke.md `
  --output-json results\real_motion_readiness_synthetic_smoke.json
```

Checked readiness smoke outputs:

| Scenario | Expected exit | Summary |
| --- | ---: | --- |
| synthetic default gate | 1 | `results\real_motion_readiness_synthetic_expected_fail.md` |
| synthetic explicitly allowed | 0 | `results\real_motion_readiness_synthetic_smoke.md` |

## UR5e High-Start Wrist-Pose Control Work

Control-state observation smoke commands:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_smoke.yaml
```

```powershell
python scripts\inspect_image_expert_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\image_expert_512_high_start_hard_wrist_pose_control_state_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\visual_audit\image_expert_512_wrist_pose_control_state_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\image_expert_512_wrist_pose_control_state_smoke_inspection.csv
```

```powershell
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_smoke.yaml
```

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_smoke.yaml
```

Weighted replay smoke for `control_state`:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --datasets datasets\ur5e_full\high_start\hard\image_expert_512_high_start_hard_wrist_pose_control_state_smoke.npz `
  --output checkpoints\ur5e_full\high_start\hard\sac_image_bc_512_high_start_hard_wrist_pose_control_state_weighted_smoke.zip `
  --metadata-output results\ur5e_full\high_start\hard\visual_audit\training_metadata_wrist_pose_control_state_weighted_smoke.json `
  --epochs 1 `
  --samples-per-epoch 256 `
  --batch-size 128 `
  --learning-rate 0.0001 `
  --validation-batches 2 `
  --device cpu `
  --seed 588100 `
  --image-width 100 `
  --image-height 100 `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --near-hole-crop-offset -18 0 `
  --include-control-state `
  --wrist-camera-pos-offset -0.04 -0.04 0.0 `
  --wrist-camera-rot-offset-deg 0 0 0 `
  --wrist-camera-fovy 100 `
  --max-steps 1000 `
  --action-scale 0.005 `
  --target-low 0.50 0.00 0.65 `
  --target-high 0.60 0.10 0.65 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --geometry-hole-half-size-range 0.017 0.021 `
  --approach-xy-tolerance 0.06 `
  --approach-height 0.12
```

Derived-control-state smoke from an older dataset without a stored
`control_state` array:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py `
  --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml `
  --datasets datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_wrist_pose_visual_camera_seed564k.npz `
  --output checkpoints\ur5e_full\high_start\hard\sac_image_bc_10k_high_start_hard_wrist_pose_control_state_derived_smoke.zip `
  --metadata-output results\ur5e_full\high_start\hard\visual_audit\training_metadata_wrist_pose_control_state_derived_smoke.json `
  --epochs 1 `
  --samples-per-epoch 128 `
  --batch-size 64 `
  --learning-rate 0.0001 `
  --validation-batches 1 `
  --device cpu `
  --seed 588200 `
  --image-width 100 `
  --image-height 100 `
  --include-near-hole-crop `
  --near-hole-crop-size 64 `
  --near-hole-crop-offset -18 0 `
  --include-control-state `
  --wrist-camera-pos-offset -0.04 -0.04 0.0 `
  --wrist-camera-rot-offset-deg 0 0 0 `
  --wrist-camera-fovy 100 `
  --max-steps 1000 `
  --action-scale 0.005 `
  --target-low 0.50 0.00 0.65 `
  --target-high 0.60 0.10 0.65 `
  --success-xy-tolerance 0.005 `
  --success-z-tolerance 0.01 `
  --geometry-hole-half-size-range 0.017 0.021 `
  --approach-xy-tolerance 0.06 `
  --approach-height 0.12
```

The smoke checkpoint is wiring-only. Do not use it as a performance model.

10k control-state signal run:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_10k.yaml
python scripts\inspect_image_expert_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\image_expert_10k_high_start_hard_wrist_pose_control_state_visual_camera_control_seed590k.npz `
  --output-md results\ur5e_full\high_start\hard\visual_audit\image_expert_10k_wrist_pose_control_state_visual_camera_control_seed590k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\image_expert_10k_wrist_pose_control_state_visual_camera_control_seed590k_inspection.csv
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_10k_scratch.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_10k_scratch.yaml
```

60k mixed control-state scratch run:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml
python scripts\analyze_control_failures.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_60k_high_start_hard_wrist_pose_control_state_mix_scratch_e8.zip `
  --episodes 80 `
  --seed 584000 `
  --domain-randomization-level visual_camera_control `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\control_failure_wrist_pose_control_state_mix_60k_scratch_e8_80ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\control_failure_wrist_pose_control_state_mix_60k_scratch_e8_80ep.md
```

Stack3 frame-stacking trial. This is wired and tested, but the performance run
regressed, so use it as a reference experiment rather than a promoted model:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_stack3_smoke.yaml
python scripts\inspect_image_expert_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\image_expert_512_high_start_hard_wrist_pose_control_state_stack3_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\visual_audit\image_expert_stack3_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\image_expert_stack3_smoke_inspection.csv
python scripts\pretrain_image_actor_bc.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_stack3_smoke.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_stack3_smoke.yaml
```

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_mix_stack3_scratch_e6.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_stack3_scratch_e6.yaml
python scripts\analyze_control_failures.py --config configs\sim\ur5e_full\analyze_high_start_hard_wrist_pose_control_state_mix_stack3_scratch_e6.yaml
```

DAgger v2 handoff correction for the wrist-pose + control-state model:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_dagger_v2_2k.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_dagger_v2.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_wrist_pose_control_state_dagger_v2_2k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_wrist_pose_control_state_dagger_v2_2k_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml
python scripts\analyze_control_failures.py --config configs\sim\ur5e_full\analyze_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml
```

DAgger v2 image ablation checks:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --image-ablation black `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_black_guarded_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_black_guarded_20ep.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --image-ablation noise `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_noise_guarded_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_noise_guarded_20ep.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --image-ablation shuffle `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_shuffle_guarded_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_shuffle_guarded_20ep.md
```

```powershell
python scripts\analyze_control_failures.py `
  --config configs\sim\ur5e_full\analyze_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --episodes 40 `
  --image-ablation black `
  --output-csv results\ur5e_full\high_start\hard\correction\control_failure_wrist_pose_control_state_dagger_v2_2k_w10_e2_black_40ep.csv `
  --output-md results\ur5e_full\high_start\hard\correction\control_failure_wrist_pose_control_state_dagger_v2_2k_w10_e2_black_40ep.md
python scripts\analyze_control_failures.py `
  --config configs\sim\ur5e_full\analyze_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --episodes 40 `
  --image-ablation noise `
  --output-csv results\ur5e_full\high_start\hard\correction\control_failure_wrist_pose_control_state_dagger_v2_2k_w10_e2_noise_40ep.csv `
  --output-md results\ur5e_full\high_start\hard\correction\control_failure_wrist_pose_control_state_dagger_v2_2k_w10_e2_noise_40ep.md
python scripts\analyze_control_failures.py `
  --config configs\sim\ur5e_full\analyze_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --episodes 40 `
  --image-ablation shuffle `
  --output-csv results\ur5e_full\high_start\hard\correction\control_failure_wrist_pose_control_state_dagger_v2_2k_w10_e2_shuffle_40ep.csv `
  --output-md results\ur5e_full\high_start\hard\correction\control_failure_wrist_pose_control_state_dagger_v2_2k_w10_e2_shuffle_40ep.md
```

Current DAgger v2 2k w10 e2 signal:

| Check | Result |
| --- | --- |
| guarded visual_camera_control | `0.500` success, `0.300` collision |
| policy-only visual_camera_control 80ep | `0.263` success, `0.438` collision, `0.300` timeout |
| policy-only ablation normal/black/noise/shuffle | `0.300/0.000/0.000/0.000` success over 40-episode windows |
| second-seed guarded 60ep vs mixed e8 | DAgger v2 `0.650/0.500/0.500/0.400/0.417/0.217`; mixed e8 `0.633/0.450/0.483/0.367/0.417/0.217` |
| second-seed policy-only 160ep vs mixed e8 | DAgger v2 `0.181/0.556/0.263`; mixed e8 `0.156/0.575/0.269` |
| hard-bucket multi-seed 60ep | seed602 `0.217/0.217`, seed604 `0.200/0.250`, seed605 `0.450/0.433` for DAgger v2 / mixed e8 |
| status | real but modest gain; no hard-bucket net gain; not promoted and do not scale this exact DAgger v2 recipe |

DAgger v2 validation commands for a larger second-seed comparison:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --episodes 60 `
  --seed 602000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_60ep_seed602k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_60ep_seed602k.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --episodes 60 `
  --seed 602000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_mix_60k_scratch_e8_60ep_seed602k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_mix_60k_scratch_e8_60ep_seed602k.md
python scripts\analyze_control_failures.py `
  --config configs\sim\ur5e_full\analyze_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --episodes 160 `
  --seed 603000 `
  --output-csv results\ur5e_full\high_start\hard\correction\control_failure_wrist_pose_control_state_dagger_v2_2k_w10_e2_160ep_seed603k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\control_failure_wrist_pose_control_state_dagger_v2_2k_w10_e2_160ep_seed603k.md
python scripts\analyze_control_failures.py `
  --config configs\sim\ur5e_full\analyze_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --episodes 160 `
  --seed 603000 `
  --output-csv results\ur5e_full\high_start\hard\correction\control_failure_wrist_pose_control_state_mix_60k_scratch_e8_160ep_seed603k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\control_failure_wrist_pose_control_state_mix_60k_scratch_e8_160ep_seed603k.md
```

The hard-bucket-only multi-seed comparison below is the current scale-up gate:
it did not justify scaling DAgger v2 to `5k - 10k`.

Hard-bucket-only validation commands:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --hard-bucket-only `
  --episodes 60 `
  --seed 604000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_hard_60ep_seed604k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_hard_60ep_seed604k.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --hard-bucket-only `
  --episodes 60 `
  --seed 604000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_mix_60k_scratch_e8_hard_60ep_seed604k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_mix_60k_scratch_e8_hard_60ep_seed604k.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --hard-bucket-only `
  --episodes 60 `
  --seed 605000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_hard_60ep_seed605k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_hard_60ep_seed605k.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --hard-bucket-only `
  --episodes 60 `
  --seed 605000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_mix_60k_scratch_e8_hard_60ep_seed605k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_mix_60k_scratch_e8_hard_60ep_seed605k.md
```

Current decision: keep DAgger v2 as a diagnostic model, but change the next
correction data recipe toward hard-bucket low-Z misalignment and
geometry/contact failures instead of simply increasing this dataset size.

Hard-bucket episode trace diagnostics. These use the same guarded evaluator but
write one row per episode with guard-step counts, final/min XY/Z, low-Z
misalignment counters, insert-band misalignment counters, and sampled
control/geometry parameters:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_dagger_v2_2k_w10_e2.yaml `
  --hard-bucket-only `
  --episodes 60 `
  --seed 604000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_hard_trace_60ep_seed604k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_hard_trace_60ep_seed604k.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_dagger_v2_2k_w10_e2_hard_trace_episodes_60ep_seed604k.csv
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --hard-bucket-only `
  --episodes 60 `
  --seed 604000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_mix_60k_scratch_e8_hard_trace_60ep_seed604k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_mix_60k_scratch_e8_hard_trace_60ep_seed604k.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_mix_60k_scratch_e8_hard_trace_episodes_60ep_seed604k.csv
```

Seed `604000` trace result:

| Model | Success | Collision | Timeout | Pre-guard failures | Guarded failures | Low-Z misaligned failures | Mean guarded-failure XY |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DAgger v2 | 12/60 | 26/60 | 22/60 | 16 | 32 | 32 | 0.01824 |
| mixed e8 | 15/60 | 23/60 | 22/60 | 15 | 30 | 33 | 0.01856 |

This means the hard-bucket issue is not only final `5 mm` insertion. Many
failures happen before the guard activates, and guarded failures still end
around `18 mm` XY error. The next correction dataset should include
hard-bucket approach/handoff states, not just low-Z insertion recovery.

Hard-bucket-focused correction v3. This is the current strongest hard-bucket
line, but it is still a candidate because timeout remains high:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_hard_bucket_v3_smoke.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_hard_bucket_v3_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_wrist_pose_control_state_hard_bucket_v3_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_wrist_pose_control_state_hard_bucket_v3_smoke_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_hard_bucket_v3_smoke_w10_e1.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_smoke_w10_e1.yaml

python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_hard_bucket_v3.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_wrist_pose_control_state_hard_bucket_v3_2k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_wrist_pose_control_state_hard_bucket_v3_2k_inspection.csv
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2.yaml
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1.yaml
```

Hard-bucket v3 2k gate commands:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2.yaml --hard-bucket-only --episodes 60 --seed 602000 --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2_hard_trace_60ep_seed602k.csv --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2_hard_trace_60ep_seed602k.md --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2_hard_trace_episodes_60ep_seed602k.csv
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2.yaml --hard-bucket-only --episodes 60 --seed 604000 --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2_hard_trace_60ep_seed604k.csv --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2_hard_trace_60ep_seed604k.md --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2_hard_trace_episodes_60ep_seed604k.csv
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2.yaml --hard-bucket-only --episodes 60 --seed 605000 --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2_hard_trace_60ep_seed605k.csv --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2_hard_trace_60ep_seed605k.md --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e2_hard_trace_episodes_60ep_seed605k.csv

python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1.yaml --hard-bucket-only --episodes 60 --seed 602000 --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1_hard_trace_60ep_seed602k.csv --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1_hard_trace_60ep_seed602k.md --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1_hard_trace_episodes_60ep_seed602k.csv
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1.yaml --hard-bucket-only --episodes 60 --seed 604000 --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1_hard_trace_60ep_seed604k.csv --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1_hard_trace_60ep_seed604k.md --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1_hard_trace_episodes_60ep_seed604k.csv
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1.yaml --hard-bucket-only --episodes 60 --seed 605000 --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1_hard_trace_60ep_seed605k.csv --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1_hard_trace_60ep_seed605k.md --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1_hard_trace_episodes_60ep_seed605k.csv
```

Hard-bucket gate summary:

| Model | Avg success | Avg collision | Avg timeout |
| --- | ---: | ---: | ---: |
| mixed e8 | 0.300 | 0.406 | 0.295 |
| DAgger v2 | 0.289 | 0.417 | 0.295 |
| hard v3 smoke | 0.356 | 0.300 | 0.344 |
| hard v3 2k w10 e2 | 0.417 | 0.145 | 0.439 |
| hard v3 2k w10 e1 | 0.416 | 0.167 | 0.417 |

Use `results\ur5e_full\high_start\hard\correction\hard_bucket_v3_2k_summary.md`
for the compact interpretation. Current decision: keep e1/e2 as candidates,
but do not promote yet because timeout is too high.

Hard-bucket timeout correction v4b/v4b2 diagnostics. These are recorded as
negative-result commands; do not scale the recipe without changing the label or
controller design:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_balanced_v4b_smoke.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_balanced_v4b_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_balanced_v4b_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_balanced_v4b_smoke_inspection.csv

python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke.yaml
python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_balanced_v4b2_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_balanced_v4b2_smoke_inspection.csv

python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke_w03_e1.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke_w03_e1.yaml

python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke_w01_e1.yaml
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke_w01_e1.yaml
```

High-approach correction smoke. This is the next positive data path after the
fixture-clearance diagnostics: collect high-altitude recenter labels before the
peg enters fixture height.

```powershell
python -m py_compile scripts\collect_image_correction_dataset.py scripts\inspect_image_correction_dataset.py

python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_approach_smoke.yaml

python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_approach_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_approach_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_approach_smoke_inspection.csv
```

Smoke acceptance result: `512` samples from `26` hard/narrow episodes,
`approach_window_rate=1.000`, `approach_recenter=512`, mean XY/Z above target
about `69.8 mm / 108.9 mm`.

High-approach correction 2k candidate:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_approach_2k.yaml

python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_approach.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_approach_2k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_approach_2k_inspection.csv

python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_approach_2k_w10_e1.yaml

python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_approach_2k_w10_e1.yaml

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_approach_2k_w10_e1.yaml `
  --seed 614000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_approach_2k_w10_e1_20ep_seed614k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_wrist_pose_control_state_approach_2k_w10_e1_20ep_seed614k.md

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_approach_2k_w10_e1.yaml `
  --hard-bucket-only `
  --episodes 20 `
  --seed 622000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_hard_20ep_seed622k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_hard_20ep_seed622k.md
```

2k result: dataset has `2048` samples, `approach_window_rate=1.000`, and
`approach_recenter=2048`. The 10% replay / 1 epoch candidate saved to
`checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_approach_2k_w10_e1.zip`.
Same-seed `614000` matrix reached clean/visual_camera/visual_camera_control/
full_light/full_contact/hard success `0.700/0.700/0.600/0.700/0.650/0.650`.
Hard-only seed `622000` reached `0.500/0.150/0.350`, flat versus v3 but not
regressed.

Approach 2k candidate multi-seed and visual ablation:

```powershell
foreach ($seed in 602000,604000,605000) {
  python scripts\eval_guarded_policy.py `
    --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_approach_2k_w10_e1.yaml `
    --hard-bucket-only `
    --episodes 60 `
    --seed $seed `
    --output-csv "results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_hard_60ep_seed$seed.csv" `
    --output-md "results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_hard_60ep_seed$seed.md"
}

foreach ($mode in 'normal','black','noise','shuffle') {
  python scripts\eval_guarded_policy.py `
    --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_approach_2k_w10_e1.yaml `
    --hard-bucket-only `
    --episodes 40 `
    --seed 617000 `
    --control-mode policy `
    --image-ablation $mode `
    --output-csv "results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_policy_hard_${mode}_40ep.csv" `
    --output-md "results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_policy_hard_${mode}_40ep.md"
}
```

Result: approach 2k is visual-positive but not promoted. Hard-only 60-episode
multi-seed average is about `0.400/0.194/0.406`, slightly below v3's
`0.417/0.167/0.417`. Policy-only image ablation shows the learned model still
uses vision: normal hard-bucket success `0.300`, black/noise/shuffle `0.000`.
See `results\ur5e_full\high_start\hard\correction\approach_2k_candidate_summary.md`.

Failure trace and controller-gate diagnostics for approach 2k:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_approach_2k_w10_e1.yaml `
  --hard-bucket-only `
  --episodes 60 `
  --seed 602000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_hard_trace_60ep_seed602k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_hard_trace_60ep_seed602k.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_hard_trace_episodes_60ep_seed602k.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_hard_failure_step_trace_60ep_seed602k.csv `
  --step-trace-outcome-filter failure

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1.yaml `
  --hard-bucket-only `
  --episodes 60 `
  --seed 602000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_trace_60ep_seed602k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_trace_60ep_seed602k.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_trace_episodes_60ep_seed602k.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_failure_step_trace_60ep_seed602k.csv `
  --step-trace-outcome-filter failure

python scripts\analyze_step_trace_failures.py `
  --trace v3=results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_failure_step_trace_60ep_seed602k.csv `
  --trace approach=results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_hard_failure_step_trace_60ep_seed602k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\approach_vs_v3_failure_trace_seed602k_summary.md `
  --output-csv results\ur5e_full\high_start\hard\correction\approach_vs_v3_failure_trace_seed602k_episodes.csv
```

Controller gate diagnostics on approach 2k, seed `602000`, 60 hard-bucket
episodes:

| Variant | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| approach baseline | 0.367 | 0.267 | 0.367 |
| fixture clearance gate | 0.350 | 0.283 | 0.367 |
| hover/descent gate | 0.350 | 0.267 | 0.383 |
| lift-before-lateral gate | 0.150 | 0.267 | 0.583 |

Conclusion: do not promote these broad controller gates. See
`results\ur5e_full\high_start\hard\correction\controller_gate_diagnostics_seed602k_summary.md`.

Fixture-wall pre-contact correction smoke. This targets the collision band where
the peg is still above the fixture but already laterally close enough to hit the
fixture wall during descent.

```powershell
python -m py_compile scripts\collect_image_correction_dataset.py scripts\inspect_image_correction_dataset.py

python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_fixture_wall_smoke.yaml

python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_512_high_start_hard_wrist_pose_control_state_fixture_wall_smoke.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_fixture_wall_smoke_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_fixture_wall_smoke_inspection.csv
```

Smoke acceptance result: `512` samples from `23` source episodes,
`fixture_wall_window_rate=1.000`, `fixture_wall_recenter=512`, median XY/Z
above target about `32.3 mm / 69.9 mm`, and `oracle_down_action_rate=0.000`.
This validates the data path; it is not a trained/promoted checkpoint yet.

Fixture-wall correction 2k candidate:

```powershell
python scripts\collect_image_correction_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_fixture_wall_2k.yaml

python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_fixture_wall.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_fixture_wall_2k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_fixture_wall_2k_inspection.csv

python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_fixture_wall_2k_w10_e1.yaml

python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_fixture_wall_2k_w10_e1.yaml

foreach ($seed in 602000,604000,605000) {
  python scripts\eval_guarded_policy.py `
    --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_fixture_wall_2k_w10_e1.yaml `
    --hard-bucket-only `
    --episodes 60 `
    --seed $seed `
    --output-csv "results\ur5e_full\high_start\hard\correction\eval_fixture_wall_2k_w10_e1_hard_60ep_seed$seed.csv" `
    --output-md "results\ur5e_full\high_start\hard\correction\eval_fixture_wall_2k_w10_e1_hard_60ep_seed$seed.md"
}
```

Result: fixture-wall 2k w10 e1 is not promoted. Three-seed hard-bucket average
is `0.428/0.128/0.444`, compared with v3 `0.417/0.167/0.417` and approach
2k `0.400/0.194/0.406`. It reduces collision but increases timeout.

Fixture-wall trace and lower replay-weight check:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_fixture_wall_2k_w10_e1.yaml `
  --hard-bucket-only `
  --episodes 60 `
  --seed 602000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_fixture_wall_2k_w10_e1_hard_trace_60ep_seed602k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_fixture_wall_2k_w10_e1_hard_trace_60ep_seed602k.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_fixture_wall_2k_w10_e1_hard_trace_episodes_60ep_seed602k.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_fixture_wall_2k_w10_e1_hard_failure_step_trace_60ep_seed602k.csv `
  --step-trace-outcome-filter failure

python scripts\analyze_step_trace_failures.py `
  --trace fixture_wall=results\ur5e_full\high_start\hard\correction\eval_fixture_wall_2k_w10_e1_hard_failure_step_trace_60ep_seed602k.csv `
  --trace approach=results\ur5e_full\high_start\hard\correction\eval_approach_2k_w10_e1_hard_failure_step_trace_60ep_seed602k.csv `
  --trace v3=results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_failure_step_trace_60ep_seed602k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\fixture_wall_vs_v3_approach_failure_trace_seed602k_summary.md `
  --output-csv results\ur5e_full\high_start\hard\correction\fixture_wall_vs_v3_approach_failure_trace_seed602k_episodes.csv

python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_fixture_wall_2k_w05_e1.yaml

python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_fixture_wall_2k_w05_e1.yaml

foreach ($seed in 602000,604000,605000) {
  python scripts\eval_guarded_policy.py `
    --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_fixture_wall_2k_w05_e1.yaml `
    --hard-bucket-only `
    --episodes 60 `
    --seed $seed `
    --output-csv "results\ur5e_full\high_start\hard\correction\eval_fixture_wall_2k_w05_e1_hard_60ep_seed$seed.csv" `
    --output-md "results\ur5e_full\high_start\hard\correction\eval_fixture_wall_2k_w05_e1_hard_60ep_seed$seed.md"
}
```

Result: w05 is also not promoted. Three-seed hard-bucket average is
`0.405/0.139/0.456`, worse than w10. The failure trace shows the next recipe
needs explicit timeout-progress / slow-insert supervision, not just different
fixture-wall replay weight.

Fixture-wall plus small timeout-progress replay smoke:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_fixture_wall_progress_w03_e1.yaml

python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_fixture_wall_progress_w03_e1.yaml

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_fixture_wall_progress_w03_e1.yaml `
  --hard-bucket-only `
  --episodes 20 `
  --seed 621000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_fixture_wall_progress_w03_e1_hard_20ep_seed621k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_fixture_wall_progress_w03_e1_hard_20ep_seed621k.md

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_fixture_wall_progress_w03_e1.yaml `
  --hard-bucket-only `
  --episodes 20 `
  --seed 622000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_fixture_wall_progress_w03_e1_hard_20ep_seed622k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_fixture_wall_progress_w03_e1_hard_20ep_seed622k.md
```

Result: not promoted. It reached hard bucket `0.500/0.050/0.450` in the
default 20-episode matrix, but clean/full-light regressed and same-seed hard
checks were unstable: seed `621000` `0.300/0.150/0.550`, seed `622000`
`0.450/0.250/0.300`.

Same-seed hard-bucket gate on seed `622000`, 20 episodes:

| Model | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| v3 e1 baseline | 0.500 | 0.150 | 0.350 |
| v4 progress-only w03 e1 | 0.400 | 0.300 | 0.300 |
| v4b2 w03 e1 | 0.350 | 0.400 | 0.250 |
| v4b2 w01 e1 | 0.400 | 0.300 | 0.300 |

Conclusion: v4b2 improved label balance versus v4b, but still converts too
many timeout cases into collision. Keep it as a diagnostic dataset only.

Collision-conversion trace diagnostics:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_hard_bucket_v3_2k_w10_e1.yaml `
  --hard-bucket-only `
  --episodes 20 `
  --seed 622000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_failure_trace_contacts_20ep_seed622k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_failure_trace_contacts_20ep_seed622k.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_failure_trace_contacts_episodes_20ep_seed622k.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_failure_step_trace_contacts_20ep_seed622k.csv `
  --step-trace-outcome-filter failure

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke_w01_e1.yaml `
  --hard-bucket-only `
  --episodes 20 `
  --seed 622000 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_hard_failure_trace_contacts_20ep_seed622k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_hard_failure_trace_contacts_20ep_seed622k.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_hard_failure_trace_contacts_episodes_20ep_seed622k.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_hard_failure_step_trace_contacts_20ep_seed622k.csv `
  --step-trace-outcome-filter failure

python scripts\analyze_step_trace_failures.py `
  --trace v3_e1=results\ur5e_full\high_start\hard\correction\eval_v3_e1_hard_failure_step_trace_contacts_20ep_seed622k.csv `
  --trace v4b2_w01=results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_hard_failure_step_trace_contacts_20ep_seed622k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\v4b2_collision_conversion_trace_contacts_summary.md `
  --output-csv results\ur5e_full\high_start\hard\correction\v4b2_collision_conversion_trace_contacts_episodes.csv
```

The trace showed v4b2 collisions are approach/fixture-clearance failures, not
final insert-band misses. A wider contact-aware guard was also tested and is not
promoted:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke_w01_e1.yaml `
  --hard-bucket-only `
  --episodes 20 `
  --seed 622000 `
  --guard-start-xy 0.09 `
  --guarded-oracle-mode contact_aware_recovery `
  --contact-recovery-z-max 0.10 `
  --contact-recovery-lift-height 0.12 `
  --contact-recovery-lift-z-tolerance 0.015 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_contact_guard09_hard_20ep_seed622k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_contact_guard09_hard_20ep_seed622k.md
```

It reached only `0.050/0.400/0.550`, so broad early oracle takeover should not
be used.

Fixture-clearance safety gate diagnostic. This keeps normal guard activation
narrow and only forces a Z-up action when the peg is already low over the
fixture while still laterally far from the hole:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke_w01_e1.yaml `
  --hard-bucket-only `
  --episodes 20 `
  --seed 622000 `
  --guard-fixture-clearance-enabled `
  --guard-fixture-clearance-xy-min 0.020 `
  --guard-fixture-clearance-xy-max 0.130 `
  --guard-fixture-clearance-z-max 0.060 `
  --guard-fixture-clearance-lift-height 0.100 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_fixture_gate_xy13_hard_20ep_seed622k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_fixture_gate_xy13_hard_20ep_seed622k.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_fixture_gate_xy13_hard_episodes_20ep_seed622k.csv
```

Current same-seed fixture-gate result:

| Variant | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| v4b2 w01 no fixture gate | 0.400 | 0.300 | 0.300 |
| fixture `xy_max=0.09,z_max=0.06,lift=0.10` | 0.400 | 0.250 | 0.350 |
| fixture `xy_max=0.13,z_max=0.06,lift=0.10` | 0.400 | 0.200 | 0.400 |
| fixture `xy_max=0.13,z_max=0.08,lift=0.12` | 0.400 | 0.200 | 0.400 |

Interpretation: the gate reduces approach/fixture collisions, but it mostly
converts one collision into timeout and does not recover success. Keep it as a
diagnostic/deployment safety feature; do not treat it as a promoted training
result.

Two-stage fixture realign diagnostic. This keeps the fixture gate active after
lifting and tries to re-align at a safe height before release:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_balanced_v4b2_smoke_w01_e1.yaml `
  --hard-bucket-only `
  --episodes 20 `
  --seed 622000 `
  --guard-fixture-clearance-enabled `
  --guard-fixture-clearance-realign-enabled `
  --guard-fixture-clearance-xy-min 0.020 `
  --guard-fixture-clearance-xy-max 0.130 `
  --guard-fixture-clearance-z-max 0.060 `
  --guard-fixture-clearance-lift-height 0.100 `
  --guard-fixture-clearance-realign-start-z 0.060 `
  --guard-fixture-clearance-realign-xy 0.020 `
  --guard-fixture-clearance-max-steps 240 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_fixture_gate_realign_start06_xy13_hard_20ep_seed622k.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_fixture_gate_realign_start06_xy13_hard_20ep_seed622k.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_v4b2_w01_fixture_gate_realign_start06_xy13_hard_episodes_20ep_seed622k.csv
```

Current same-seed realign results:

| Variant | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| realign start Z `0.060`, max XY `0.005` | 0.400 | 0.250 | 0.350 |
| realign start Z `0.045`, max XY `0.005` | 0.400 | 0.300 | 0.300 |
| realign start Z `0.045`, max XY `0.002` | 0.400 | 0.300 | 0.300 |

Interpretation: high-threshold realign barely activates, while earlier realign
reintroduces low-altitude scraping. Keep this as a diagnostic option, not a
default controller.

Control-state image ablation audit. These commands preserve `control_state` and
only corrupt image observations:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --image-ablation black `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_black_guarded_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_black_guarded_20ep.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --image-ablation noise `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_noise_guarded_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_noise_guarded_20ep.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --image-ablation shuffle `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_shuffle_guarded_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_shuffle_guarded_20ep.md
```

Policy-only ablation audit:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --control-mode policy `
  --image-ablation normal `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_normal_policy_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_normal_policy_20ep.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --control-mode policy `
  --image-ablation black `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_black_policy_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_black_policy_20ep.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --control-mode policy `
  --image-ablation noise `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_noise_policy_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_noise_policy_20ep.md
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --control-mode policy `
  --image-ablation shuffle `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_shuffle_policy_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_shuffle_policy_20ep.md
```

Guard-only ceiling for the same scenarios:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_mix_60k_scratch_e8.yaml `
  --control-mode guard_only `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_guard_only_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_control_state_mix_60k_scratch_e8_guard_only_20ep.md
```

Collect the targeted delay-2 control dataset:

```powershell
python scripts\collect_image_expert_dataset.py --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_targeted_delay2_20k.yaml
```

Inspect the targeted dataset:

```powershell
python scripts\inspect_image_expert_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\image_expert_20k_high_start_hard_wrist_pose_control_targeted_delay2_seed585k.npz `
  --output-md results\ur5e_full\high_start\hard\visual_audit\image_expert_20k_wrist_pose_control_targeted_delay2_seed585k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\image_expert_20k_wrist_pose_control_targeted_delay2_seed585k_inspection.csv
```

Train the targeted replay checkpoint:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_targeted_delay2_w60_e4.yaml
```

Evaluate the targeted replay checkpoint:

```powershell
python scripts\eval_guarded_policy.py --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_targeted_delay2_w60_e4.yaml
```

Analyze control failures for the targeted checkpoint:

```powershell
python scripts\analyze_control_failures.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_targeted_delay2_w60_e4.yaml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_70k_high_start_hard_wrist_pose_control_targeted_delay2_w60_e4.zip `
  --episodes 80 `
  --seed 584000 `
  --domain-randomization-level visual_camera_control `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\control_failure_wrist_pose_control_targeted_delay2_w60_e4_80ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\control_failure_wrist_pose_control_targeted_delay2_w60_e4_80ep.md
```

Near-action limiter checks already run and are not promoted:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_50k_scratch.yaml `
  --model checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_wrist_pose_visual_camera_scratch_e20.zip `
  --episodes 20 `
  --seed 574000 `
  --guard-near-action-scale-enabled `
  --guard-near-action-xy-tolerance 0.020 `
  --guard-near-action-z-threshold 0.070 `
  --guard-near-max-xy-action 0.005 `
  --guard-near-max-down-action 0.0025 `
  --output-csv results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_50k_scratch_e20_near_limiter_mild_20ep.csv `
  --output-md results\ur5e_full\high_start\hard\visual_audit\eval_wrist_pose_50k_scratch_e20_near_limiter_mild_20ep.md
```

## Evaluation Matrix

Run the standard five-environment matrix:

```powershell
python scripts\eval_matrix.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --output-csv results\eval_matrix_latest.csv --output-md results\eval_matrix_latest.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

Include stress scenarios for high delay, combined control noise, and high
contact/dynamics randomization:

```powershell
python scripts\eval_matrix.py --agent sac --observation-mode image --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --episodes 100 --device cpu --include-stress --output-csv results\eval_matrix_stress_latest.csv --output-md results\eval_matrix_stress_latest.md --success-xy-tolerance 0.005 --success-z-tolerance 0.01
```

## Sensitivity Scans

Control randomization scan:

```powershell
python scripts\scan_control_randomization.py --model checkpoints_image_bc_50k_sidecam_visual_camera_control_oracle\sac_image_bc.zip --output results\control_randomization_scan.csv --episodes 50 --device cpu
```

Contact/dynamics scan:

```powershell
python scripts\scan_contact_randomization.py --model checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip --output results\contact_randomization_scan.csv --episodes 50 --device cpu
```

## Reference Results

Current best model:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean | 1.000 | 0.000 |
| visual_camera_control | 0.980 | 0.010 |
| high_delay 0-3 | 0.950 | 0.020 |
| high combined control | 0.970 | 0.010 |
| full_light_geometry | 0.960 | 0.010 |
| full_contact_light | 0.970 | 0.010 |
| high full_contact_light | 0.970 | 0.010 |

UR5e adapter fixedcam models:

| Environment | Success | Collision |
| --- | ---: | ---: |
| clean fixedcam 50k scratch eval_policy | 1.000 | 0.000 |
| clean fixedcam 50k scratch eval_matrix | 0.950 | 0.050 |
| visual_camera fixedcam 50k scratch | 0.040 | 0.850 |
| visual_camera_control fixedcam 50k scratch | 0.070 | 0.840 |
| clean clean+visual_camera 100k e35 | 0.960 | 0.040 |
| visual_camera clean+visual_camera 100k e35 | 0.660 | 0.340 |
| visual_camera_control clean+visual_camera 100k e35 | 0.440 | 0.560 |
| clean clean+visual_camera 150k e20 | 0.960 | 0.040 |
| visual_camera clean+visual_camera 150k e20 | 0.810 | 0.190 |
| visual_camera_control clean+visual_camera 150k e20 | 0.480 | 0.520 |
| clean mild-control 200k e20 | 0.930 | 0.070 |
| visual_camera mild-control 200k e20 | 0.920 | 0.080 |
| visual_camera_control mild-control 200k e20 | 0.600 | 0.400 |
| clean success-only control 250k e15 | 0.950 | 0.050 |
| visual_camera success-only control 250k e15 | 0.910 | 0.090 |
| visual_camera_control success-only control 250k e15 | 0.730 | 0.270 |
| full_light_geometry success-only control 250k e15 | 0.250 | 0.730 |
| full_contact_light success-only control 250k e15 | 0.270 | 0.690 |
| clean delay-filter success 300k e10 | 0.970 | 0.030 |
| visual_camera delay-filter success 300k e10 | 0.940 | 0.060 |
| visual_camera_control delay-filter success 300k e10 | 0.780 | 0.220 |
| clean delay-filter success 350k e8 | 0.990 | 0.010 |
| visual_camera delay-filter success 350k e8 | 0.930 | 0.070 |
| visual_camera_control delay-filter success 350k e8 | 0.860 | 0.140 |
| full_light_geometry delay-filter success 350k e8 | 0.290 | 0.670 |
| full_contact_light delay-filter success 350k e8 | 0.270 | 0.680 |
| clean hard-control 400k e6 | 0.980 | 0.020 |
| visual_camera hard-control 400k e6 | 0.960 | 0.040 |
| visual_camera_control hard-control 400k e6 | 0.880 | 0.120 |
| hard-control fixed bucket hard-control 400k e6 | 0.700 | 0.300 |
| clean hard-weighted 500k e5 | 0.960 | 0.040 |
| visual_camera hard-weighted 500k e5 | 0.990 | 0.010 |
| visual_camera_control hard-weighted 500k e5 | 0.890 | 0.110 |
| hard-control fixed bucket hard-weighted 500k e5 | 0.770 | 0.230 |
| full_light_geometry hard-weighted 500k e5 | 0.300 | 0.660 |
| full_contact_light hard-weighted 500k e5 | 0.310 | 0.660 |
| clean fixedcam 5k scratch | 0.790 | 0.200 |

## Insert-Drift Late-Stage Correction

Collect and inspect the late insert-band drift correction dataset:

```powershell
python scripts\collect_image_correction_dataset.py `
  --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_insert_drift_2k.yaml

python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_insert_drift.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_insert_drift_2k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_insert_drift_2k_inspection.csv
```

Train the current non-promoted insert-drift candidate:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1.yaml
```

Evaluate it:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1.yaml

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_hard_60ep.yaml
```

## Insert-Settle Late-Stage Correction

Collect and inspect the insert-settle dataset:

```powershell
python scripts\collect_image_correction_dataset.py `
  --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_insert_settle_2k.yaml

python scripts\inspect_image_correction_dataset.py `
  --dataset datasets\ur5e_full\high_start\hard\correction\image_correction_2k_high_start_hard_wrist_pose_control_state_insert_settle.npz `
  --output-md results\ur5e_full\high_start\hard\correction\image_correction_insert_settle_2k_inspection.md `
  --output-csv results\ur5e_full\high_start\hard\correction\image_correction_insert_settle_2k_inspection.csv
```

Train and evaluate the two non-promoted insert-settle candidates:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_insert_settle_2k_w05_e1.yaml

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_settle_2k_w05_e1.yaml

python scripts\pretrain_image_actor_bc_weighted.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_insert_settle_2k_w10_e1.yaml

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_settle_2k_w10_e1.yaml
```

## Insert Late-Stage Timeout Trace And Guard Scan

Generate timeout-only step traces for the two late-stage BC candidates:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_hard_60ep.yaml `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_hard_trace_60ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_hard_trace_60ep_seed602000.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_hard_trace_episodes_60ep_seed602000.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_hard_timeout_step_trace_60ep_seed602000.csv `
  --step-trace-outcome-filter timeout

python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_settle_2k_w05_e1_hard_60ep.yaml `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_settle_2k_w05_e1_hard_trace_60ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_settle_2k_w05_e1_hard_trace_60ep_seed602000.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_settle_2k_w05_e1_hard_trace_episodes_60ep_seed602000.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_settle_2k_w05_e1_hard_timeout_step_trace_60ep_seed602000.csv `
  --step-trace-outcome-filter timeout
```

Summarize timeout failure modes:

```powershell
python scripts\analyze_step_trace_failures.py `
  --trace insert_drift_w10=results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_hard_timeout_step_trace_60ep_seed602000.csv `
  --trace insert_settle_w05=results\ur5e_full\high_start\hard\correction\eval_insert_settle_2k_w05_e1_hard_timeout_step_trace_60ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\insert_late_bc_timeout_trace_seed602000_summary.md `
  --output-csv results\ur5e_full\high_start\hard\correction\insert_late_bc_timeout_trace_seed602000_episodes.csv `
  --success-xy-tolerance 0.005 `
  --near-xy 0.010 `
  --low-z 0.020 `
  --window-steps 20
```

Latest conclusion:

- both insert-drift and insert-settle w05 produced `27/60` timeouts on hard seed `602000`
- most timeouts entered the strict 5 mm insert band, then drifted out to about `6 - 7 mm` XY
- scalar guard scans did not improve the same-seed baseline; results are recorded in:

```text
results\ur5e_full\high_start\hard\correction\insert_late_bc_guard_scalar_scan_seed602000_summary.md
```

Next implementation should be a stateful final insertion servo, not more
single-threshold guarded-two-stage tuning.

## Final Servo MVP

Run the current non-promoted fast-latch final-servo smoke:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_20ep.yaml
```

Run the same hard-bucket 60-episode gate:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_hard_60ep.yaml
```

Current result:

```text
20ep hard seed 602000: 0.500 / 0.150 / 0.350
60ep hard seed 602000: 0.417 / 0.133 / 0.450
```

Numbers are `success / collision / timeout`. This is flat versus the
insert-drift baseline, so final servo is implemented and traceable but not
promoted as a performance improvement yet.

Summary:

```text
results\ur5e_full\high_start\hard\correction\final_servo_mvp_summary.md
```

## Final Servo Soft-Unjam And Bias Diagnostics

Run the current soft-unjam 20ep diagnostic config:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_soft_unjam_20ep.yaml
```

Run the +3mm X final-descent bias diagnostic from the fast-latch config:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_20ep.yaml `
  --guard-final-servo-descend-xy-bias 0.003 0.0 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_biasx3mm_20ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_biasx3mm_20ep_seed602000.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_biasx3mm_episodes_20ep_seed602000.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_final_servo_biasx3mm_failure_step_trace_20ep_seed602000.csv
```

Current conclusion:

```text
soft-unjam Z-first 20mm: 0.500 / 0.150 / 0.350, mean return 273.706
descend bias +3mm X:    0.500 / 0.150 / 0.350, mean return 218.903
```

Numbers are `success / collision / timeout`. These diagnostics are not
promoted. They indicate that the remaining timeout bucket is already
contact-limited after wedging; next work should prevent the low-Z drift before
the peg gets wedged.

## Preinsert Recenter Diagnostics

Run the current preinsert recenter smoke config:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_preinsert_recenter_20ep.yaml
```

Run the earlier 35mm diagnostic variant:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_preinsert_recenter_20ep.yaml `
  --guard-preinsert-recenter-start-z 0.035 `
  --guard-preinsert-recenter-trigger-xy 0.0035 `
  --guard-preinsert-recenter-stable-xy 0.003 `
  --guard-preinsert-recenter-height 0.035 `
  --guard-preinsert-recenter-z-tolerance 0.008 `
  --guard-preinsert-recenter-max-steps 60 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_preinsert_recenter_early35_20ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_preinsert_recenter_early35_20ep_seed602000.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_preinsert_recenter_early35_episodes_20ep_seed602000.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_2k_w10_e1_preinsert_recenter_early35_failure_step_trace_20ep_seed602000.csv
```

Current conclusion:

```text
preinsert 25mm:       0.500 / 0.150 / 0.350, mean return 420.434
preinsert early 35mm: 0.500 / 0.150 / 0.350, mean return 460.382
preinsert short:      0.500 / 0.150 / 0.350, mean return 441.059
```

Numbers are `success / collision / timeout`. These diagnostics are not
promoted. They show that threshold-only pre-wedge guards improve trajectory
quality but do not solve the insertion timeout. Next work should improve the
low-level UR5e controller so commanded Cartesian recentering reliably moves the
peg tip toward the hole.

## Pose-IK Recovery Sequence

Collect the smoke dataset:

```powershell
python scripts\collect_image_correction_dataset.py `
  --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_recovery_sequence_pose_ik_smoke.yaml
```

Collect the 2k dataset:

```powershell
python scripts\collect_image_correction_dataset.py `
  --config configs\sim\ur5e_full\collect_high_start_hard_wrist_pose_control_state_recovery_sequence_pose_ik_2k.yaml
```

Train the low-weight replay checkpoint:

```powershell
python scripts\pretrain_image_actor_bc_weighted.py `
  --config configs\sim\ur5e_full\pretrain_high_start_hard_wrist_pose_control_state_recovery_sequence_pose_ik_2k_w08_e1.yaml
```

Run the hard-bucket gate:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_recovery_sequence_pose_ik_2k_w08_e1_final_servo_pose_ik_hard_60ep.yaml
```

Generic runtime lift-before-lateral smoke:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_hard_60ep.yaml `
  --episodes 20 `
  --guarded-lift-before-lateral `
  --guarded-lift-before-lateral-xy-tolerance 0.020 `
  --guarded-lift-before-lateral-z-margin 0.010
```

Current conclusion:

```text
recovery sequence hard 60ep:        0.717 / 0.100 / 0.183
runtime lift-before-lateral 20ep:   0.150 / 0.800 / 0.050
```

Numbers are `success / collision / timeout`. Do not scale this replay family
until the controller/guard structure changes.

## Controller Gain And Frame-Skip Diagnostics

Run the nominal Kp=2 hard gate:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_hard_60ep.yaml `
  --episodes 60 `
  --nominal-actuator-kp-multiplier 2.0 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_hard_60ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_hard_60ep_seed602000.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_hard_episodes_60ep_seed602000.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_hard_failure_step_trace_60ep_seed602000.csv
```

Run the Kp=2 + `frame_skip=20` hard gate:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_hard_60ep.yaml `
  --episodes 60 `
  --nominal-actuator-kp-multiplier 2.0 `
  --frame-skip 20 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_fs20_hard_60ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_fs20_hard_60ep_seed602000.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_fs20_hard_episodes_60ep_seed602000.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_fs20_hard_failure_step_trace_60ep_seed602000.csv
```

Run the current IK-weight candidate hard gate:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_hard_60ep.yaml
```

Run the current IK-weight candidate 100ep matrix:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_matrix_100ep.yaml
```

Run the current best Kp2 controller hard gate:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_kp2_hard_60ep.yaml
```

Run the current best Kp2 controller 100ep matrix:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_kp2_matrix_100ep.yaml
```

Render the current best Kp2 controller high-resolution demo:

```powershell
python scripts\demo_policy.py `
  --config configs\sim\ur5e_full\demo_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_kp2.yaml
```

Checked demo result:

```text
success=True, collision=False, steps=309, final XY/Z error about 4.3 mm / 9.7 mm
output: demos\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori006_it48_kp2.gif
trace:  results\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori006_it48_kp2_trace.csv
```

The demo config requests MP4 output, but on the current machine `imageio`
lacks an ffmpeg/pyav backend, so `demo_policy.py` falls back to a `2560x720`
GIF. `python -m pip install imageio-ffmpeg` timed out in this environment.

Run the current best lower-orientation Kp2 controller hard gate:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori003_it64_kp2_hard_60ep.yaml
```

Run the current best lower-orientation Kp2 controller 100ep matrix:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori003_it64_kp2_matrix_100ep.yaml
```

Render the current best lower-orientation Kp2 controller high-resolution demo:

```powershell
python scripts\demo_policy.py `
  --config configs\sim\ur5e_full\demo_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori003_it64_kp2.yaml
```

Checked lower-orientation result:

```text
hard 60ep seed602000: 0.883 / 0.000 / 0.117
hard 60ep seed604000: 0.900 / 0.000 / 0.100
100ep matrix:
  clean:                 0.970 / 0.000 / 0.030
  visual_camera:         0.970 / 0.000 / 0.030
  visual_camera_control: 0.940 / 0.000 / 0.060
  full_light_geometry:   0.910 / 0.000 / 0.090
  full_contact_light:    0.910 / 0.000 / 0.090
  hard_full_light_bucket:0.910 / 0.000 / 0.090
demo: success=True, collision=False, steps=335, final XY/Z error about 4.5 mm / 9.6 mm
output: demos\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori003_it64_kp2.gif
trace:  results\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori003_it64_kp2_trace.csv
```

The first five 100ep matrix rows are in
`eval_insert_drift_pose_ik_wori003_it64_kp2_matrix_100ep_seed602000.*`.
The hard-bucket 100ep row is in
`eval_insert_drift_pose_ik_wori003_it64_kp2_hard_100ep_seed602000.*`.
The matrix config has been fixed to include `include_hard_bucket: true` for
future reruns.

Run the latest low-Z preinsert lift-first smoke:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori003_it64_kp2_preinsert_lift_first_20ep.yaml
```

Fair same-seed baseline for the promoted controller:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori003_it64_kp2_hard_60ep.yaml `
  --episodes 20 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_baseline_20ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_baseline_20ep_seed602000.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_baseline_episodes_20ep_seed602000.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_baseline_failure_step_trace_20ep_seed602000.csv
```

Narrow diagnostic override that avoids the broad-regression band:

```powershell
python scripts\eval_guarded_policy.py `
  --config configs\sim\ur5e_full\eval_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori003_it64_kp2_preinsert_lift_first_20ep.yaml `
  --guard-preinsert-recenter-trigger-xy 0.008 `
  --guard-preinsert-recenter-stable-xy 0.0065 `
  --guard-preinsert-recenter-max-steps 40 `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_preinsert_lift_first_narrow_20ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_preinsert_lift_first_narrow_20ep_seed602000.md `
  --episode-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_preinsert_lift_first_narrow_episodes_20ep_seed602000.csv `
  --step-output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_preinsert_lift_first_narrow_failure_step_trace_20ep_seed602000.csv
```

Low-Z lift-first result:

```text
promoted baseline 20ep:                  0.950 / 0.000 / 0.050
broad preinsert lift-first 20ep:         0.850 / 0.000 / 0.150
narrow preinsert lift-first 20ep:        0.950 / 0.000 / 0.050
narrow higher lift height 45mm 20ep:     0.950 / 0.000 / 0.050
early high lift height 80mm 20ep:        0.900 / 0.000 / 0.100
```

Conclusion: keep `guard_preinsert_recenter_lift_before_lateral` as an opt-in
diagnostic only. Broad preinsert recenter is too disruptive, and narrow
preinsert recenter does not improve the remaining timeout. Next work should
inspect TCP tracking/IK response in the remaining timeout or implement a true
retreat-and-retry sequence instead of more threshold-only preinsert scans.

Analyze command-to-motion transfer for the hard timeout:

```powershell
python scripts\analyze_tcp_response_trace.py `
  --trace baseline=results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_baseline_failure_step_trace_20ep_seed602000.csv `
  --trace holdz=results\ur5e_full\high_start\hard\correction\eval_wori003_it64_kp2_holdz_failure_trace_seed602019.csv `
  --trace retry40=results\ur5e_full\high_start\hard\correction\eval_wori003_it64_kp2_retry40_failure_trace_seed602019.csv `
  --trace holdz_latch_wide=results\ur5e_full\high_start\hard\correction\eval_wori003_it64_kp2_holdz_latch_wide_failure_trace_seed602019.csv `
  --trace holdz_finalservo120=results\ur5e_full\high_start\hard\correction\eval_wori003_it64_kp2_holdz_finalservo120_retry2_failure_trace_seed602019.csv `
  --output-md results\ur5e_full\controller_diagnostics\tcp_response_holdz_retry_seed602019.md `
  --output-csv results\ur5e_full\controller_diagnostics\tcp_response_holdz_retry_seed602019.csv
```

Hard-case seed `602019` diagnostic results:

```text
baseline last 100 steps:
  final XY command ~= 5.0 mm
  applied XY command ~= 4.5 mm
  actual peg-tip XY delta ~= 0.009 mm
  actual / applied XY ~= 0.002

hold-Z:
  reached XY ~= 4.92 mm but stayed high at Z ~= 48.9 mm
  failure mode is insert-band lift/descent oscillation under delay/filter

retry40:
  retry was active for 480 steps but still timed out

wide latch:
  reached Z ~= 8.2 mm, but XY drifted to ~= 10.4 mm and lateral response stayed weak

early final-servo with retries:
  final-servo was active for 636 steps but still timed out around XY ~= 8.2 mm, Z ~= 47.3 mm

near-action limiting:
  reduced IK/tracking error but stalled around 9 - 12 mm XY and did not enter the insert band
```

Conclusion: the remaining hard timeout is not just a missing guard trigger.
The next change should either add a true stateful retreat/recenter phase with
height hysteresis, or tune the low-level IK/controller tracking under
delay/filter before moving to multi-geometry.

Summarize Kp=2 failure modes:

```powershell
python scripts\analyze_step_trace_failures.py `
  --trace kp2=results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_hard_failure_step_trace_60ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_hard_failure_modes_60ep_seed602000.md `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_kp2_hard_failure_modes_60ep_seed602000.csv
```

Current conclusion:

```text
pose-IK baseline hard 60ep: 0.717 / 0.100 / 0.183
Kp=2 hard 60ep:            0.733 / 0.000 / 0.267
Kp=2 + fs20 hard 60ep:     0.733 / 0.000 / 0.267
Kp=4 hard 20ep:            0.250 / 0.000 / 0.750
IK 0.06/48 hard 60ep:      0.767 / 0.100 / 0.133
IK 0.06/48 20ep x3 avg:    0.767 / 0.100 / 0.133
IK 0.06/48 + Kp2 hard 60:  0.850 / 0.000 / 0.150
IK 0.06/48 + Kp2 seed604:  0.867 / 0.000 / 0.133
IK 0.03/64 + Kp2 hard 60:  0.883 / 0.000 / 0.117
IK 0.03/64 + Kp2 seed604:  0.900 / 0.000 / 0.100
```

100ep matrix success rates for IK `0.06/48`:

```text
clean:                 0.850
visual_camera:         0.840
visual_camera_control: 0.840
full_light_geometry:   0.850
full_contact_light:    0.850
hard_full_light_bucket:0.790
```

100ep matrix success rates for IK `0.06/48 + Kp2`:

```text
clean:                 0.910 / 0.000 / 0.090
visual_camera:         0.910 / 0.000 / 0.090
visual_camera_control: 0.910 / 0.000 / 0.090
full_light_geometry:   0.900 / 0.000 / 0.100
full_contact_light:    0.900 / 0.000 / 0.100
hard_full_light_bucket:0.890 / 0.000 / 0.110
```

Analyze the hard-gate failure modes for the candidate:

```powershell
python scripts\analyze_step_trace_failures.py `
  --trace wori006_it48=results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori006_it48_hard_failure_step_trace_60ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori006_it48_hard_failure_modes_60ep_seed602000.md `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori006_it48_hard_failure_modes_60ep_seed602000.csv
```

Analyze the hard-gate failure modes for the Kp2 candidate:

```powershell
python scripts\analyze_step_trace_failures.py `
  --trace wori006_it48_kp2=results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori006_it48_kp2_hard_failure_step_trace_60ep_seed602000.csv `
  --output-md results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori006_it48_kp2_hard_failure_modes_60ep_seed602000.md `
  --output-csv results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori006_it48_kp2_hard_failure_modes_60ep_seed602000.csv
```

Kp=2 removes collisions but mostly turns them into timeouts, so it is not
promoted alone as a default. Combined with lower orientation-weight pose IK,
Kp2 is now the current best controller candidate because it improves hard-gate
success and keeps collisions at zero. Treat `ik_orientation_weight=0.03`,
`ik_max_iterations=64`, and `nominal_actuator_kp_multiplier=2.0` as current
best. Wider align tolerance `0.030` regressed to
`0.833 / 0.000 / 0.167`, so do not promote wider align.
