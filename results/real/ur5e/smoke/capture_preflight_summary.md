# Real Camera Policy Preflight Summary

- Overall: **PASS**
- Camera verdict: **PASS**
- Dry-run verdict: **PASS**
- Image input: `results\real\ur5e\smoke\capture_camera_frames`
- Camera summary: `results\real\ur5e\smoke\capture_preflight_camera_summary.md`
- Dry-run summary: `results\real\ur5e\smoke\capture_dryrun_summary.md`
- Dry-run trace: `results\real\ur5e\smoke\capture_policy_trace.csv`

## Commands

Camera preflight:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/check_real_camera_preflight.py --input results\real\ur5e\smoke\capture_camera_frames --output-dir results\real\ur5e\smoke\capture_preflight_camera_frames --stats-output results\real\ur5e\smoke\capture_preflight_camera_stats.csv --summary-md results\real\ur5e\smoke\capture_preflight_camera_summary.md --output-json results\real\ur5e\smoke\capture_preflight_camera_summary.json --width 100 --height 100 --rotate-k 0 --max-frames 20 --min-frames 1 --min-processed-mean 2 --max-processed-mean 253 --min-processed-std 2 --max-zero-fraction 0.98 --max-255-fraction 0.98 --min-frame-diff-mean 0
```

Dry-run preflight:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/run_real_dryrun_preflight.py --config configs\real\ur5e\synthetic_smoke.yaml --agent sac --episodes 1 --seed 130000 --device cpu --safety-max-action 0.002 --trace-output results\real\ur5e\smoke\capture_policy_trace.csv --check-output-md results\real\ur5e\smoke\capture_dryrun_check.md --check-output-json results\real\ur5e\smoke\capture_dryrun_check.json --summary-md results\real\ur5e\smoke\capture_dryrun_summary.md --image-dir results\real\ur5e\smoke\capture_camera_frames --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --max-steps 4 --tcp-pose-trace results\real\ur5e\smoke\capture_tcp_pose_trace.csv --target-calibration configs\real\ur5e\target_calibration_smoke.yaml --tcp-to-peg-tip-xyz 0 0 -0.11 --guarded-policy --guard-scenario-filter geometry --guard-scenario-name real_ur5_dryrun --guard-scenario-level full_light_geometry --guard-start-xy 0.06 --guard-start-z 0.08 --guard-risk-xy 0 --guard-blend 0.75 --guard-min-policy-steps 0 --guard-action-gain 1 --guard-action-limit 0.002 --guarded-align-xy-tolerance 0.025 --guarded-insert-xy-tolerance 0.005 --guarded-retract-xy-tolerance 0.012 --guarded-preinsert-height 0 --guarded-max-xy-action 0.002 --guarded-max-down-action 0.0015 --guarded-max-up-action 0.002 --guarded-prediction-steps 1 --expected-pose-frame robot_base --require-nonstatic-pose --require-nonstatic-target --allow-action-limited
```

## Key Metrics

| Metric | Value |
| --- | ---: |
| `camera.frames_ok` | 10 |
| `camera.frames_failed` | 0 |
| `camera.processed_mean_avg` | 126.92977 |
| `camera.processed_std_avg` | 48.53758838730248 |
| `camera.frame_diff_mean_avg` | 0.9730888803799947 |
| `dryrun.rows` | 5 |
| `dryrun.safe_action_max_abs_component` | 0.0019487999999999728 |
| `dryrun.workspace_limited_rows` | 0 |
| `dryrun.guard_active_rows` | 4 |
| `dryrun.tcp_to_peg_tip_max_error` | 4.52995300159742e-08 |

## Issues

| Source | Severity | Code | Count | Message |
| --- | --- | --- | ---: | --- |
| all | INFO | `no_issues` | 0 | No issues detected. |
