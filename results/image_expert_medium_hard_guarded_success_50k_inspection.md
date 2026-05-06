# Image Expert Dataset Inspection

- Dataset: `mujoco_peg_in_hole\datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_50k_oracle.npz`
- Metadata: `mujoco_peg_in_hole\datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_50k_oracle.npz.json`
- Schema: `image_expert_v2_diagnostics`
- Samples: `50000`
- Episodes completed: `8096`
- Success rate: `0.3447381422924901`
- Collision rate: `0.6467391304347826`
- Success-only: `True`
- Has near-hole crops: `True`

## Arrays

| Key | Shape | Dtype |
| --- | --- | --- |
| `actions` | `[50000, 3]` | `float32` |
| `actuator_kp_multiplier` | `[50000]` | `float32` |
| `cam_images` | `[50000, 100, 100, 1]` | `uint8` |
| `contact_friction_multiplier` | `[50000]` | `float32` |
| `contact_solimp_width_multiplier` | `[50000]` | `float32` |
| `contact_solref_damping_multiplier` | `[50000]` | `float32` |
| `contact_solref_time_multiplier` | `[50000]` | `float32` |
| `control_action_delay` | `[50000]` | `int32` |
| `control_action_filter_alpha` | `[50000]` | `float32` |
| `control_action_noise_std` | `[50000]` | `float32` |
| `control_action_scale_multiplier` | `[50000]` | `float32` |
| `desired_z` | `[50000]` | `float32` |
| `episode_id` | `[50000]` | `int32` |
| `fixture_height_offset` | `[50000]` | `float32` |
| `hole_center_offset` | `[50000, 2]` | `float32` |
| `hole_clearance` | `[50000]` | `float32` |
| `hole_half_size` | `[50000]` | `float32` |
| `joint_damping_multiplier` | `[50000]` | `float32` |
| `near_hole_crops` | `[50000, 64, 64, 1]` | `uint8` |
| `peg_radius` | `[50000]` | `float32` |
| `peg_tip_pos` | `[50000, 3]` | `float32` |
| `raw_actions` | `[50000, 3]` | `float32` |
| `step_id` | `[50000]` | `int32` |
| `table_height_offset` | `[50000]` | `float32` |
| `target_pos` | `[50000, 3]` | `float32` |

## Distributions

| Metric | Count | Mean | Std | Min | P05 | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hole_half_size | 50000.0 | 0.022114 | 0.001172 | 0.020002 | 0.020214 | 0.022140 | 0.023832 | 0.024000 |
| peg_radius | 50000.0 | 0.012005 | 0.000291 | 0.011501 | 0.011551 | 0.012005 | 0.012455 | 0.012499 |
| hole_clearance | 50000.0 | 0.010109 | 0.001210 | 0.007542 | 0.008158 | 0.010164 | 0.011927 | 0.012489 |
| control_action_scale_multiplier | 50000.0 | 0.959744 | 0.085605 | 0.800362 | 0.821474 | 0.963970 | 1.0887 | 1.1000 |
| control_action_noise_std | 50000.0 | 0.000124 | 0.000072 | 0.000000 | 0.000012 | 0.000125 | 0.000235 | 0.000250 |
| control_action_delay | 50000.0 | 2.0000 | 0.000000 | 2.0000 | 2.0000 | 2.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 50000.0 | 0.627885 | 0.042471 | 0.550058 | 0.559325 | 0.629218 | 0.692878 | 0.699930 |
| fixture_height_offset | 50000.0 | 0.000005 | 0.000570 | -0.001000 | -0.000893 | 0.000025 | 0.000882 | 0.000998 |
| table_height_offset | 50000.0 | 0.000004 | 0.000578 | -0.000998 | -0.000901 | -0.000002 | 0.000904 | 0.001000 |
| contact_friction_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solref_time_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solref_damping_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solimp_width_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| joint_damping_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| actuator_kp_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| desired_z | 50000.0 | 0.697482 | 0.022991 | 0.649994 | 0.668552 | 0.692033 | 0.730547 | 0.730998 |
| step_id | 50000.0 | 9.6196 | 7.2794 | 0.000000 | 0.000000 | 8.0000 | 25.0000 | 45.0000 |
| hole_center_offset_x | 50000.0 | 0.000065 | 0.001160 | -0.001998 | -0.001791 | 0.000074 | 0.001845 | 0.002000 |
| hole_center_offset_y | 50000.0 | -0.000010 | 0.001161 | -0.001996 | -0.001823 | -0.000012 | 0.001804 | 0.002000 |
| hole_center_offset_norm | 50000.0 | 0.001543 | 0.000565 | 0.000043 | 0.000494 | 0.001626 | 0.002384 | 0.002792 |
| action_norm | 50000.0 | 1.1710 | 0.170044 | 0.306560 | 0.853209 | 1.2207 | 1.4142 | 1.4142 |
| raw_action_norm | 50000.0 | 0.005855 | 0.000850 | 0.001533 | 0.004266 | 0.006103 | 0.007071 | 0.007071 |
| unique_episode_id_count | 2791.0 | 2791.0 | 0.000000 | 2791.0 | 2791.0 | 2791.0 | 2791.0 | 2791.0 |
