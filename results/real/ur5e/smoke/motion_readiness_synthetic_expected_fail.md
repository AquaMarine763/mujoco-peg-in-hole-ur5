# Real Motion Readiness Check

- Verdict: **FAIL**
- Bundle summary: `results\real\ur5e\smoke\capture_bundle_summary.json`
- Expected pose frame: `robot_base`
- Expected target source: `fixture_calibration`
- Minimum camera frames: `10`
- Minimum TCP samples: `10`
- Minimum dry-run rows: `2`

## Metrics

| Metric | Value |
| --- | ---: |
| `camera.rows` | 10 |
| `camera.session_ids` | ur5e_config_gate_synthetic_smoke |
| `camera_preflight.frame_diff_mean_min` | 0.3366999924182892 |
| `camera_preflight.frames_ok` | 10 |
| `capture_bundle.verdict` | PASS |
| `config.pose_frame` | robot_base |
| `config.target_frame` | robot_base |
| `config.target_id` | smoke_hole |
| `config.target_source` | fixture_calibration |
| `config.tcp_to_peg_tip_norm` | 0.11 |
| `dryrun.guard_active_rows` | 4 |
| `dryrun.guard_enabled_rows` | 5 |
| `dryrun.pose_frames` | robot_base |
| `dryrun.pose_sources` | tcp_csv |
| `dryrun.rows` | 5 |
| `dryrun.safe_action_max_abs_component` | 0.0019487999999999728 |
| `dryrun.target_sources` | fixture_calibration |
| `session_id` | ur5e_config_gate_synthetic_smoke |
| `tcp.rows` | 10 |
| `tcp.session_ids` | ur5e_config_gate_synthetic_smoke |

## Issues

| Severity | Code | Count | Details |
| --- | --- | ---: | --- |
| ERROR | `config_path_is_smoke` | 1 | configs\real\ur5e\synthetic_smoke.yaml |
| ERROR | `synthetic_inputs` | 2 | camera_record, tcp_record |
| ERROR | `target_calibration_path_is_smoke` | 1 | configs\real\ur5e\target_calibration_smoke.yaml |
