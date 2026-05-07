# Real Capture Bundle Summary

- Overall: **FAIL**
- Config check verdict: **FAIL**
- Camera recorder return code: `-1`
- TCP recorder return code: `-1`
- Combined preflight verdict: **SKIPPED**
- Session id: `synthetic_config_gate_failure_smoke`
- Camera frames: `results\real_capture_bundle_config_gate_failure_smoke_camera_frames`
- Camera stats: `results\real_capture_bundle_config_gate_failure_smoke_camera_stats.csv`
- TCP trace: `results\real_capture_bundle_config_gate_failure_smoke_tcp_pose_trace.csv`
- Target calibration: `configs\real_hole_target_calibration_smoke.yaml`
- TCP target columns: `omitted`
- Combined preflight summary: `results\real_capture_bundle_config_gate_failure_smoke_preflight_summary.md`

## Commands

Config check:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/check_real_deployment_config.py --config configs\missing_real_ur5_dryrun.yaml --output-md results\real_capture_bundle_config_gate_failure_smoke_config_check.md --output-json results\real_capture_bundle_config_gate_failure_smoke_config_check.json --target-calibration configs\real_hole_target_calibration_smoke.yaml --tcp-to-peg-tip-xyz 0 0 -0.11
```

Camera recorder:

SKIPPED

TCP recorder:

SKIPPED

Combined preflight:

SKIPPED

## Metrics

| Metric | Value |
| --- | ---: |
