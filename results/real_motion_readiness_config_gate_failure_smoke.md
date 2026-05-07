# Real Motion Readiness Check

- Verdict: **FAIL**
- Bundle summary: `results\real_capture_bundle_config_gate_failure_smoke_summary.json`
- Expected pose frame: `robot_base`
- Expected target source: `fixture_calibration`
- Minimum camera frames: `4`
- Minimum TCP samples: `4`
- Minimum dry-run rows: `1`

## Metrics

| Metric | Value |
| --- | ---: |
| `capture_bundle.verdict` | FAIL |
| `config.pose_frame` | robot_base |
| `config.target_frame` | robot_base |
| `config.target_id` | smoke_hole |
| `config.target_source` | fixture_calibration |
| `config.tcp_to_peg_tip_norm` | 0.11 |
| `session_id` | synthetic_config_gate_failure_smoke |

## Issues

| Severity | Code | Count | Details |
| --- | --- | ---: | --- |
| ERROR | `camera_record_returncode` | 1 | -1 |
| ERROR | `capture_bundle_failed` | 1 | capture_bundle verdict is FAIL. |
| ERROR | `capture_bundle_not_pass` | 1 | FAIL |
| ERROR | `config_check_failed` | 1 | config_check verdict is FAIL. |
| ERROR | `config_check_nested_errors` | 1 | config_check reported nested errors. |
| ERROR | `config_check_returncode` | 1 | 1 |
| ERROR | `preflight_missing` | 1 | preflight section is missing. |
| ERROR | `preflight_payload_missing` | 1 | Combined preflight payload is missing. |
| ERROR | `tcp_record_returncode` | 1 | -1 |
