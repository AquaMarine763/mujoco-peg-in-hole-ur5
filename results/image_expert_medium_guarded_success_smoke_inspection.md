# Image Expert Dataset Inspection

- Dataset: `mujoco_peg_in_hole\datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_smoke_oracle.npz`
- Metadata: `mujoco_peg_in_hole\datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_smoke_oracle.npz.json`
- Schema: `image_expert_v2_diagnostics`
- Samples: `500`
- Episodes completed: `58`
- Success rate: `0.603448275862069`
- Collision rate: `0.3448275862068966`
- Success-only: `True`
- Has near-hole crops: `True`

## Arrays

| Key | Shape | Dtype |
| --- | --- | --- |
| `actions` | `[500, 3]` | `float32` |
| `actuator_kp_multiplier` | `[500]` | `float32` |
| `cam_images` | `[500, 100, 100, 1]` | `uint8` |
| `contact_friction_multiplier` | `[500]` | `float32` |
| `contact_solimp_width_multiplier` | `[500]` | `float32` |
| `contact_solref_damping_multiplier` | `[500]` | `float32` |
| `contact_solref_time_multiplier` | `[500]` | `float32` |
| `control_action_delay` | `[500]` | `int32` |
| `control_action_filter_alpha` | `[500]` | `float32` |
| `control_action_noise_std` | `[500]` | `float32` |
| `control_action_scale_multiplier` | `[500]` | `float32` |
| `desired_z` | `[500]` | `float32` |
| `episode_id` | `[500]` | `int32` |
| `fixture_height_offset` | `[500]` | `float32` |
| `hole_center_offset` | `[500, 2]` | `float32` |
| `hole_clearance` | `[500]` | `float32` |
| `hole_half_size` | `[500]` | `float32` |
| `joint_damping_multiplier` | `[500]` | `float32` |
| `near_hole_crops` | `[500, 64, 64, 1]` | `uint8` |
| `peg_radius` | `[500]` | `float32` |
| `peg_tip_pos` | `[500, 3]` | `float32` |
| `raw_actions` | `[500, 3]` | `float32` |
| `step_id` | `[500]` | `int32` |
| `table_height_offset` | `[500]` | `float32` |
| `target_pos` | `[500, 3]` | `float32` |

## Distributions

| Metric | Count | Mean | Std | Min | P05 | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hole_half_size | 500.0000 | 0.021951 | 0.001213 | 0.020087 | 0.020387 | 0.021859 | 0.023845 | 0.023902 |
| peg_radius | 500.0000 | 0.012017 | 0.000287 | 0.011520 | 0.011565 | 0.012090 | 0.012385 | 0.012454 |
| hole_clearance | 500.0000 | 0.009933 | 0.001342 | 0.007785 | 0.008352 | 0.009740 | 0.012098 | 0.012135 |
| control_action_scale_multiplier | 500.0000 | 1.0026 | 0.095267 | 0.841396 | 0.846120 | 0.979741 | 1.1638 | 1.1855 |
| control_action_noise_std | 500.0000 | 0.000346 | 0.000260 | 0.000011 | 0.000012 | 0.000259 | 0.000764 | 0.000772 |
| control_action_delay | 500.0000 | 1.1140 | 0.687753 | 0.000000 | 0.000000 | 1.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 500.0000 | 0.777241 | 0.122154 | 0.568228 | 0.602412 | 0.794196 | 0.943509 | 0.971546 |
| fixture_height_offset | 500.0000 | 0.000067 | 0.000614 | -0.000928 | -0.000928 | 0.000167 | 0.000973 | 0.000996 |
| table_height_offset | 500.0000 | 0.000110 | 0.000602 | -0.000955 | -0.000912 | 0.000386 | 0.000930 | 0.000983 |
| contact_friction_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solref_time_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solref_damping_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solimp_width_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| joint_damping_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| actuator_kp_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| desired_z | 500.0000 | 0.698370 | 0.024878 | 0.651365 | 0.664791 | 0.693666 | 0.730808 | 0.730996 |
| step_id | 500.0000 | 7.3580 | 5.3979 | 0.000000 | 0.000000 | 7.0000 | 18.0000 | 25.0000 |
| hole_center_offset_x | 500.0000 | -0.000006 | 0.001227 | -0.001883 | -0.001870 | 0.000310 | 0.001870 | 0.001951 |
| hole_center_offset_y | 500.0000 | -0.000032 | 0.001263 | -0.001877 | -0.001710 | -0.000159 | 0.001684 | 0.001947 |
| hole_center_offset_norm | 500.0000 | 0.001678 | 0.000533 | 0.000389 | 0.000485 | 0.001757 | 0.002486 | 0.002584 |
| action_norm | 500.0000 | 1.1461 | 0.185529 | 0.363430 | 0.790034 | 1.2207 | 1.4142 | 1.4142 |
| raw_action_norm | 500.0000 | 0.005731 | 0.000928 | 0.001817 | 0.003950 | 0.006103 | 0.007071 | 0.007071 |
| unique_episode_id_count | 35.0000 | 35.0000 | 0.000000 | 35.0000 | 35.0000 | 35.0000 | 35.0000 | 35.0000 |
