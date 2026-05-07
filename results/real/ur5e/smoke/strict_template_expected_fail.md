# Real Deployment Config Check

- Verdict: **FAIL**
- Config: `configs\real\ur5e\dryrun_template.yaml`
- Target calibration: `configs\real\ur5e\target_calibration_smoke.yaml`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- Expected pose frame: `robot_base`

## Metrics

| Metric | Value |
| --- | ---: |
| `camera_cx` | 0 |
| `camera_cy` | 0 |
| `camera_fx` | 0 |
| `camera_fy` | 0 |
| `config_path` | configs\real\ur5e\dryrun_template.yaml |
| `control_frequency_hz` | 20 |
| `crop_xywh` | none |
| `image_height` | 100 |
| `image_width` | 100 |
| `include_near_hole_crop` | True |
| `max_steps` | 50 |
| `model_expects_near_hole_crop` | True |
| `model_path` | checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip |
| `model_size_bytes` | 24891314 |
| `near_hole_crop_size` | 64 |
| `peg_tip_pos` | [0.55, 0.05, 0.78] |
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
| `tcp_to_peg_tip_norm` | 0.11 |
| `tcp_to_peg_tip_xyz` | [0, 0, -0.11] |
| `tool0_tcp_offset_mismatch` | 0 |
| `tool0_to_camera_rpy` | [0, 0, 0] |
| `tool0_to_camera_xyz` | [0, 0, 0] |

## Issues

| Severity | Code | Count | Details |
| --- | --- | ---: | --- |
| ERROR | `camera_fx_invalid` | 1 | 0 |
| ERROR | `camera_fy_invalid` | 1 | 0 |
| ERROR | `crop_xywh_missing` | 1 | Set crop_xywh from measured real camera frames before real capture preflight. |
| WARN | `tool0_to_camera_xyz_near_zero` | 1 | 0 |
