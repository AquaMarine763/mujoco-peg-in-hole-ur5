# Real Capture Bundle Summary

- Overall: **PASS**
- Config check verdict: **PASS**
- Camera recorder return code: `0`
- TCP recorder return code: `0`
- Combined preflight verdict: **PASS**
- Session id: `ur5e_config_gate_synthetic_smoke`
- Camera frames: `results\real\ur5e\smoke\capture_camera_frames`
- Camera stats: `results\real\ur5e\smoke\capture_camera_stats.csv`
- TCP trace: `results\real\ur5e\smoke\capture_tcp_pose_trace.csv`
- Target calibration: `configs\real\ur5e\target_calibration_smoke.yaml`
- TCP target columns: `omitted`
- Combined preflight summary: `results\real\ur5e\smoke\capture_preflight_summary.md`

## Commands

Config check:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/check_real_deployment_config.py --config configs\real\ur5e\synthetic_smoke.yaml --output-md results\real\ur5e\smoke\capture_config_check.md --output-json results\real\ur5e\smoke\capture_config_check.json --target-calibration configs\real\ur5e\target_calibration_smoke.yaml --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --tcp-to-peg-tip-xyz 0 0 -0.11
```

Camera recorder:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/record_real_camera_frames.py --output-dir results\real\ur5e\smoke\capture_camera_frames --stats-output results\real\ur5e\smoke\capture_camera_stats.csv --summary-md results\real\ur5e\smoke\capture_camera_summary.md --frames 10 --frequency-hz 5 --warmup-frames 1 --prefix camera_frame --session-id ur5e_config_gate_synthetic_smoke --device-index 0 --synthetic-smoke
```

TCP recorder:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/record_ur_rtde_tcp_pose_trace.py --output results\real\ur5e\smoke\capture_tcp_pose_trace.csv --samples 10 --frequency-hz 20 --pose-frame robot_base --session-id ur5e_config_gate_synthetic_smoke --target-pos 0.55 0.05 0.65 --synthetic-smoke --no-target-columns
```

Combined preflight:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/run_real_camera_policy_preflight.py --config configs\real\ur5e\synthetic_smoke.yaml --image-input results\real\ur5e\smoke\capture_camera_frames --tcp-pose-trace results\real\ur5e\smoke\capture_tcp_pose_trace.csv --summary-md results\real\ur5e\smoke\capture_preflight_summary.md --output-json results\real\ur5e\smoke\capture_preflight_summary.json --target-calibration configs\real\ur5e\target_calibration_smoke.yaml --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --device cpu --episodes 1 --max-steps 4 --tcp-to-peg-tip-xyz 0 0 -0.11 --allow-action-limited --camera-output-dir results\real\ur5e\smoke\capture_preflight_camera_frames --camera-stats-output results\real\ur5e\smoke\capture_preflight_camera_stats.csv --camera-summary-md results\real\ur5e\smoke\capture_preflight_camera_summary.md --camera-output-json results\real\ur5e\smoke\capture_preflight_camera_summary.json --dryrun-trace-output results\real\ur5e\smoke\capture_policy_trace.csv --dryrun-check-output-md results\real\ur5e\smoke\capture_dryrun_check.md --dryrun-check-output-json results\real\ur5e\smoke\capture_dryrun_check.json --dryrun-summary-md results\real\ur5e\smoke\capture_dryrun_summary.md
```

## Metrics

| Metric | Value |
| --- | ---: |
| `camera.interval_avg_s` | 0.200657011 |
| `camera.interval_max_s` | 0.2010781 |
| `camera.interval_min_s` | 0.2001498 |
| `camera.rows` | 10 |
| `camera.session_id_count` | 1 |
| `camera.session_ids` | ur5e_config_gate_synthetic_smoke |
| `camera.timestamp_first` | 7.99998816e-07 |
| `camera.timestamp_last` | 1.8059139 |
| `camera.timestamp_monotonic` | True |
| `camera.timestamp_rows` | 10 |
| `camera.timestamp_span_s` | 1.8059131 |
| `camera.wall_time_first_unix` | 1.77817261e+09 |
| `camera.wall_time_last_unix` | 1.77817261e+09 |
| `camera.wall_time_monotonic` | True |
| `camera.wall_time_rows` | 10 |
| `camera.wall_time_span_s` | 1.8059144 |
| `tcp.interval_avg_s` | 0.0505543333 |
| `tcp.interval_max_s` | 0.0522802 |
| `tcp.interval_min_s` | 0.0501124 |
| `tcp.rows` | 10 |
| `tcp.session_id_count` | 1 |
| `tcp.session_ids` | ur5e_config_gate_synthetic_smoke |
| `tcp.timestamp_first` | 4.99996531e-07 |
| `tcp.timestamp_last` | 0.4549895 |
| `tcp.timestamp_monotonic` | True |
| `tcp.timestamp_rows` | 10 |
| `tcp.timestamp_span_s` | 0.454989 |
| `tcp.wall_time_first_unix` | 1.77817261e+09 |
| `tcp.wall_time_last_unix` | 1.77817261e+09 |
| `tcp.wall_time_monotonic` | True |
| `tcp.wall_time_rows` | 10 |
| `tcp.wall_time_span_s` | 0.454989433 |
| `config_check.verdict` | PASS |
| `preflight.verdict` | PASS |
| `preflight.camera_verdict` | PASS |
| `preflight.dryrun_verdict` | PASS |
