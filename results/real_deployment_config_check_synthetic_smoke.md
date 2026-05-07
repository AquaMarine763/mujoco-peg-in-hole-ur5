# Real Deployment Config Check

- Verdict: **PASS**
- Config: `configs\real_ur5_dryrun.yaml`
- Target calibration: `configs\real_hole_target_calibration_smoke.yaml`
- Model: `None`
- Expected pose frame: `robot_base`

## Metrics

| Metric | Value |
| --- | ---: |
| `config_path` | configs\real_ur5_dryrun.yaml |
| `control_frequency_hz` | 20 |
| `image_height` | 100 |
| `image_width` | 100 |
| `max_steps` | 50 |
| `peg_tip_pos` | [0.55, 0.05, 0.78] |
| `pose_frame` | robot_base |
| `safety_action_filter_alpha` | 0.6 |
| `safety_max_action` | 0.002 |
| `safety_workspace_high` | [0.65, 0.15, 0.82] |
| `safety_workspace_low` | [0.45, -0.1, 0.6] |
| `target_calibration_path` | configs\real_hole_target_calibration_smoke.yaml |
| `target_frame` | robot_base |
| `target_id` | smoke_hole |
| `target_pos` | [0.55, 0.05, 0.65] |
| `target_source` | fixture_calibration |
| `tcp_to_peg_tip_norm` | 0.11 |
| `tcp_to_peg_tip_xyz` | [0, 0, -0.11] |
| `tool0_tcp_offset_mismatch` | 0 |

## Issues

| Severity | Code | Count | Details |
| --- | --- | ---: | --- |
| INFO | `no_issues` | 0 | No issues detected. |
