# Real Dry-run Preflight Summary

- Overall: **PASS**
- Dry-run return code: `0`
- Checker return code: `0`
- Checker verdict: **PASS**
- Trace output: `results\real_capture_bundle_config_gate_synthetic_smoke_policy_trace.csv`
- Checker report: `results\real_capture_bundle_config_gate_synthetic_smoke_dryrun_check.md`

## Commands

Dry-run:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/run_real_policy_dryrun.py --config configs\real_ur5_dryrun.yaml --agent sac --episodes 1 --output results\real_capture_bundle_config_gate_synthetic_smoke_policy_trace.csv --seed 130000 --device cpu --safety-max-action 0.002 --zero-policy --max-steps 3 --image-dir results\real_capture_bundle_config_gate_synthetic_smoke_camera_frames --tcp-pose-trace results\real_capture_bundle_config_gate_synthetic_smoke_tcp_pose_trace.csv --target-calibration configs\real_hole_target_calibration_smoke.yaml --tcp-to-peg-tip-xyz 0 0 -0.11 --guarded-policy --guard-scenario-filter geometry --guard-scenario-name real_ur5_dryrun --guard-scenario-level full_light_geometry --guard-start-xy 0.06 --guard-start-z 0.1 --guard-risk-xy 0 --guard-blend 0.75 --guard-min-policy-steps 0 --guard-action-gain 1 --guard-action-limit 0.002 --guarded-align-xy-tolerance 0.025 --guarded-insert-xy-tolerance 0.005 --guarded-retract-xy-tolerance 0.012 --guarded-preinsert-height 0 --guarded-max-xy-action 0.002 --guarded-max-down-action 0.0015 --guarded-max-up-action 0.002 --guarded-prediction-steps 1
```

Checker:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/check_real_dryrun_trace.py --trace results\real_capture_bundle_config_gate_synthetic_smoke_policy_trace.csv --output-md results\real_capture_bundle_config_gate_synthetic_smoke_dryrun_check.md --output-json results\real_capture_bundle_config_gate_synthetic_smoke_dryrun_check.json --max-safe-action 0.002 --expected-pose-frame robot_base --tcp-to-peg-tip-xyz 0 0 -0.11 --require-nonstatic-pose --require-nonstatic-target
```

## Key Metrics

| Metric | Value |
| --- | ---: |
| `rows` | 4 |
| `episodes` | 1 |
| `safe_action_max_abs_component` | 0.0010529999546706748 |
| `safe_action_max_norm` | 0.0011370353063782836 |
| `workspace_limited_rows` | 0 |
| `action_limited_rows` | 0 |
| `guard_active_rows` | 3 |
| `guard_activated_rows` | 1 |
| `first_guard_z_above_target` | 0.0700000524520874 |
| `tcp_to_peg_tip_max_error` | 4.52995300159742e-08 |

## Issues

| Severity | Code | Count | Message |
| --- | --- | ---: | --- |
| INFO | `no_issues` | 0 | No checker issues detected. |
