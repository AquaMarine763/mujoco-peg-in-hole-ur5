# Real Motion Readiness Check

- Verdict: **PASS**
- Bundle summary: `results\real_capture_bundle_config_gate_synthetic_smoke_summary.json`
- Expected pose frame: `robot_base`
- Expected target source: `fixture_calibration`
- Minimum camera frames: `4`
- Minimum TCP samples: `4`
- Minimum dry-run rows: `4`

## Metrics

| Metric | Value |
| --- | ---: |
| `camera.rows` | 4 |
| `camera.session_ids` | synthetic_config_gate_smoke |
| `camera_preflight.frame_diff_mean_min` | 0.7857000231742859 |
| `camera_preflight.frames_ok` | 4 |
| `capture_bundle.verdict` | PASS |
| `config.pose_frame` | robot_base |
| `config.target_frame` | robot_base |
| `config.target_id` | smoke_hole |
| `config.target_source` | fixture_calibration |
| `config.tcp_to_peg_tip_norm` | 0.11 |
| `dryrun.guard_active_rows` | 3 |
| `dryrun.guard_enabled_rows` | 4 |
| `dryrun.pose_frames` | robot_base |
| `dryrun.pose_sources` | tcp_csv |
| `dryrun.rows` | 4 |
| `dryrun.safe_action_max_abs_component` | 0.0010529999546706748 |
| `dryrun.target_sources` | fixture_calibration |
| `session_id` | synthetic_config_gate_smoke |
| `tcp.rows` | 4 |
| `tcp.session_ids` | synthetic_config_gate_smoke |

## Issues

| Severity | Code | Count | Details |
| --- | --- | ---: | --- |
| INFO | `synthetic_inputs_allowed` | 2 | camera_record, tcp_record |
| INFO | `zero_policy_allowed` | 1 | Zero-policy dry-run was explicitly allowed. |
