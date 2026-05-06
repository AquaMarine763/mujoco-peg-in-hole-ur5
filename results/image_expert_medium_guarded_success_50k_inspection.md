# Image Expert Dataset Inspection

- Dataset: `mujoco_peg_in_hole\datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_50k_oracle.npz`
- Metadata: `mujoco_peg_in_hole\datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_guarded_success_50k_oracle.npz.json`
- Schema: `image_expert_v2_diagnostics`
- Samples: `50000`
- Episodes completed: `5142`
- Success rate: `0.5791520809023726`
- Collision rate: `0.38486970050563984`
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
| hole_half_size | 50000.0 | 0.022060 | 0.001163 | 0.020002 | 0.020207 | 0.022070 | 0.023824 | 0.023998 |
| peg_radius | 50000.0 | 0.012009 | 0.000289 | 0.011500 | 0.011551 | 0.012021 | 0.012448 | 0.012500 |
| hole_clearance | 50000.0 | 0.010051 | 0.001200 | 0.007560 | 0.008136 | 0.010054 | 0.011913 | 0.012464 |
| control_action_scale_multiplier | 50000.0 | 1.0078 | 0.114593 | 0.800467 | 0.823500 | 1.0109 | 1.1819 | 1.2000 |
| control_action_noise_std | 50000.0 | 0.000401 | 0.000233 | 0.000000 | 0.000040 | 0.000408 | 0.000760 | 0.000799 |
| control_action_delay | 50000.0 | 0.875920 | 0.774935 | 0.000000 | 0.000000 | 1.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 50000.0 | 0.785455 | 0.128804 | 0.550701 | 0.572896 | 0.789477 | 0.980514 | 0.999983 |
| fixture_height_offset | 50000.0 | 0.000021 | 0.000581 | -0.001000 | -0.000892 | 0.000033 | 0.000899 | 0.001000 |
| table_height_offset | 50000.0 | 0.000002 | 0.000586 | -0.000999 | -0.000914 | 0.000009 | 0.000892 | 0.001000 |
| contact_friction_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solref_time_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solref_damping_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solimp_width_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| joint_damping_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| actuator_kp_multiplier | 50000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| desired_z | 50000.0 | 0.696685 | 0.024772 | 0.649164 | 0.665770 | 0.687680 | 0.730660 | 0.731000 |
| step_id | 50000.0 | 9.1816 | 7.0385 | 0.000000 | 0.000000 | 8.0000 | 23.0000 | 43.0000 |
| hole_center_offset_x | 50000.0 | -0.000004 | 0.001154 | -0.001997 | -0.001807 | -0.000014 | 0.001789 | 0.002000 |
| hole_center_offset_y | 50000.0 | 0.000002 | 0.001155 | -0.001998 | -0.001788 | 0.000001 | 0.001798 | 0.001999 |
| hole_center_offset_norm | 50000.0 | 0.001534 | 0.000561 | 0.000043 | 0.000527 | 0.001592 | 0.002404 | 0.002807 |
| action_norm | 50000.0 | 1.1249 | 0.187417 | 0.171840 | 0.789739 | 1.1821 | 1.4142 | 1.4142 |
| raw_action_norm | 50000.0 | 0.005625 | 0.000937 | 0.000859 | 0.003949 | 0.005911 | 0.007071 | 0.007071 |
| unique_episode_id_count | 2978.0 | 2978.0 | 0.000000 | 2978.0 | 2978.0 | 2978.0 | 2978.0 | 2978.0 |
