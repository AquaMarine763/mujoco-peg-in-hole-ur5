# Real Capture Bundle Summary

- Overall: **PASS**
- Camera recorder return code: `0`
- TCP recorder return code: `0`
- Combined preflight verdict: **PASS**
- Camera frames: `results\real_capture_bundle_synthetic_smoke_camera_frames`
- Camera stats: `results\real_capture_bundle_synthetic_smoke_camera_stats.csv`
- TCP trace: `results\real_capture_bundle_synthetic_smoke_tcp_pose_trace.csv`
- Target calibration: `configs\real_hole_target_calibration_smoke.yaml`
- TCP target columns: `omitted`
- Combined preflight summary: `results\real_capture_bundle_synthetic_smoke_preflight_summary.md`

## Commands

Camera recorder:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/record_real_camera_frames.py --output-dir results\real_capture_bundle_synthetic_smoke_camera_frames --stats-output results\real_capture_bundle_synthetic_smoke_camera_stats.csv --summary-md results\real_capture_bundle_synthetic_smoke_camera_record_summary.md --frames 4 --frequency-hz 100 --warmup-frames 10 --prefix camera_frame --device-index 0 --synthetic-smoke
```

TCP recorder:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/record_ur_rtde_tcp_pose_trace.py --output results\real_capture_bundle_synthetic_smoke_tcp_pose_trace.csv --samples 4 --frequency-hz 100 --pose-frame robot_base --target-pos 0.55 0.05 0.65 --synthetic-smoke --no-target-columns
```

Combined preflight:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/run_real_camera_policy_preflight.py --image-input results\real_capture_bundle_synthetic_smoke_camera_frames --tcp-pose-trace results\real_capture_bundle_synthetic_smoke_tcp_pose_trace.csv --summary-md results\real_capture_bundle_synthetic_smoke_preflight_summary.md --output-json results\real_capture_bundle_synthetic_smoke_preflight_summary.json --target-calibration configs\real_hole_target_calibration_smoke.yaml --zero-policy --episodes 1 --max-steps 3 --tcp-to-peg-tip-xyz 0 0 -0.11 --camera-max-frames 4 --camera-output-dir results\real_capture_bundle_synthetic_smoke_preflight_camera_frames --camera-stats-output results\real_capture_bundle_synthetic_smoke_preflight_camera_stats.csv --camera-summary-md results\real_capture_bundle_synthetic_smoke_preflight_camera_summary.md --camera-output-json results\real_capture_bundle_synthetic_smoke_preflight_camera_summary.json --dryrun-trace-output results\real_capture_bundle_synthetic_smoke_policy_trace.csv --dryrun-check-output-md results\real_capture_bundle_synthetic_smoke_dryrun_check.md --dryrun-check-output-json results\real_capture_bundle_synthetic_smoke_dryrun_check.json --dryrun-summary-md results\real_capture_bundle_synthetic_smoke_dryrun_summary.md
```

## Metrics

| Metric | Value |
| --- | ---: |
| `camera.interval_avg_s` | 0.0242037 |
| `camera.interval_max_s` | 0.0517913 |
| `camera.interval_min_s` | 0.0102872 |
| `camera.rows` | 4 |
| `camera.timestamp_first` | 7.99998816e-07 |
| `camera.timestamp_last` | 0.0726119 |
| `camera.timestamp_monotonic` | True |
| `camera.timestamp_rows` | 4 |
| `camera.timestamp_span_s` | 0.0726111 |
| `tcp.interval_avg_s` | 0.0105583 |
| `tcp.interval_max_s` | 0.0106638 |
| `tcp.interval_min_s` | 0.0104606 |
| `tcp.rows` | 4 |
| `tcp.timestamp_first` | 5.99997293e-07 |
| `tcp.timestamp_last` | 0.0316755 |
| `tcp.timestamp_monotonic` | True |
| `tcp.timestamp_rows` | 4 |
| `tcp.timestamp_span_s` | 0.0316749 |
| `preflight.verdict` | PASS |
| `preflight.camera_verdict` | PASS |
| `preflight.dryrun_verdict` | PASS |
