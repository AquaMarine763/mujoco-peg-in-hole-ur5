# Real Motion Readiness Check

- Verdict: **FAIL**
- Bundle summary: `results\real_capture_bundle_config_gate_synthetic_smoke_summary.json`
- Expected pose frame: `robot_base`
- Expected target source: `fixture_calibration`
- Minimum camera frames: `10`
- Minimum TCP samples: `10`
- Minimum dry-run rows: `2`

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
| ERROR | `camera_preflight_frames_too_low` | 1 | 4 < 10 |
| ERROR | `camera_rows_too_low` | 1 | 4 < 10 |
| ERROR | `synthetic_inputs` | 2 | camera_record, tcp_record |
| ERROR | `target_calibration_path_is_smoke` | 1 | configs\real_hole_target_calibration_smoke.yaml |
| ERROR | `tcp_rows_too_low` | 1 | 4 < 10 |
| ERROR | `zero_policy` | 1 | Zero-policy dry-runs validate plumbing only; use a real model before robot motion. |
| WARN | `recommended_model_not_seen` | 1 | checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4 |
