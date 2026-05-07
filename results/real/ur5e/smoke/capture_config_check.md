# Real Deployment Config Check

- Verdict: **PASS**
- Config: `configs\real\ur5e\synthetic_smoke.yaml`
- Target calibration: `configs\real\ur5e\target_calibration_smoke.yaml`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- Expected pose frame: `robot_base`

## Metrics

| Metric | Value |
| --- | ---: |
| `config_path` | configs\real\ur5e\synthetic_smoke.yaml |
| `control_frequency_hz` | 20 |
| `image_height` | 100 |
| `image_width` | 100 |
| `include_near_hole_crop` | True |
| `max_steps` | 4 |
| `model_expects_near_hole_crop` | True |
| `model_path` | checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip |
| `model_size_bytes` | 24891314 |
| `near_hole_crop_size` | 64 |
| `peg_tip_pos` | [0.55, 0.05, 0.72] |
| `pose_frame` | robot_base |
| `safety_action_filter_alpha` | 0.6 |
| `safety_max_action` | 0.002 |
| `safety_workspace_high` | [0.65, 0.15, 0.82] |
| `safety_workspace_low` | [0.45, -0.1, 0.6] |
| `target_calibration_path` | configs\real\ur5e\target_calibration_smoke.yaml |
| `target_frame` | robot_base |
| `target_id` | smoke_hole |
| `target_pos` | [0.55, 0.05, 0.65] |
| `target_source` | fixture_calibration |
| `tcp_pose_trace_columns` | step, timestamp, pose_frame, tcp_x, tcp_y, tcp_z, tcp_rx, tcp_ry, tcp_rz |
| `tcp_pose_trace_path` | configs\real\ur5e\tcp_pose_trace_no_target_smoke.csv |
| `tcp_to_peg_tip_norm` | 0.11 |
| `tcp_to_peg_tip_xyz` | [0, 0, -0.11] |
| `tool0_tcp_offset_mismatch` | 0 |

## Issues

| Severity | Code | Count | Details |
| --- | --- | ---: | --- |
| INFO | `no_issues` | 0 | No issues detected. |
