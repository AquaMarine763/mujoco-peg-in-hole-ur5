# Image Expert Dataset Inspection

- Dataset: `mujoco_peg_in_hole\datasets\image_correction_ur5e_adapter_medium_targeted_failure_window_smoke_200_oracle.npz`
- Metadata: `mujoco_peg_in_hole\datasets\image_correction_ur5e_adapter_medium_targeted_failure_window_smoke_200_oracle.npz.json`
- Schema: `image_correction_v1_policy_failure_window`
- Samples: `200`
- Episodes completed: `150`
- Success rate: `unknown`
- Collision rate: `unknown`
- Success-only: `unknown`
- Has near-hole crops: `True`

## Arrays

| Key | Shape | Dtype |
| --- | --- | --- |
| `action_cosine` | `[200]` | `float32` |
| `actions` | `[200, 3]` | `float32` |
| `actuator_kp_multiplier` | `[200]` | `float32` |
| `cam_images` | `[200, 100, 100, 1]` | `uint8` |
| `contact_friction_multiplier` | `[200]` | `float32` |
| `contact_solimp_width_multiplier` | `[200]` | `float32` |
| `contact_solref_damping_multiplier` | `[200]` | `float32` |
| `contact_solref_time_multiplier` | `[200]` | `float32` |
| `control_action_delay` | `[200]` | `int32` |
| `control_action_filter_alpha` | `[200]` | `float32` |
| `control_action_noise_std` | `[200]` | `float32` |
| `control_action_scale_multiplier` | `[200]` | `float32` |
| `correction_norm` | `[200]` | `float32` |
| `correction_raw_actions` | `[200, 3]` | `float32` |
| `correction_xy_norm` | `[200]` | `float32` |
| `desired_z` | `[200]` | `float32` |
| `dist_xy` | `[200]` | `float32` |
| `dist_z` | `[200]` | `float32` |
| `episode_collision` | `[200]` | `bool` |
| `episode_id` | `[200]` | `int32` |
| `episode_outcome` | `[200]` | `<U9` |
| `episode_success` | `[200]` | `bool` |
| `episode_timeout` | `[200]` | `bool` |
| `failure_window` | `[200]` | `bool` |
| `final_step` | `[200]` | `int32` |
| `fixture_height_offset` | `[200]` | `float32` |
| `hole_center_offset` | `[200, 2]` | `float32` |
| `hole_clearance` | `[200]` | `float32` |
| `hole_half_size` | `[200]` | `float32` |
| `joint_damping_multiplier` | `[200]` | `float32` |
| `near_hole` | `[200]` | `bool` |
| `near_hole_crops` | `[200, 64, 64, 1]` | `uint8` |
| `opposed_actions` | `[200]` | `bool` |
| `oracle_norm` | `[200]` | `float32` |
| `peg_radius` | `[200]` | `float32` |
| `peg_tip_pos` | `[200, 3]` | `float32` |
| `policy_actions` | `[200, 3]` | `float32` |
| `policy_down_or_oracle_up` | `[200]` | `bool` |
| `policy_down_oracle_less_down` | `[200]` | `bool` |
| `policy_norm` | `[200]` | `float32` |
| `policy_raw_actions` | `[200, 3]` | `float32` |
| `raw_actions` | `[200, 3]` | `float32` |
| `scenario` | `[200]` | `<U22` |
| `seed` | `[200]` | `int32` |
| `step_id` | `[200]` | `int32` |
| `steps_to_end` | `[200]` | `int32` |
| `table_height_offset` | `[200]` | `float32` |
| `target_pos` | `[200, 3]` | `float32` |
| `tier` | `[200]` | `<U6` |
| `z_above_target` | `[200]` | `float32` |

## Distributions

| Metric | Count | Mean | Std | Min | P05 | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hole_half_size | 200.0000 | 0.021973 | 0.001331 | 0.020011 | 0.020061 | 0.021907 | 0.023867 | 0.023928 |
| peg_radius | 200.0000 | 0.012037 | 0.000298 | 0.011559 | 0.011595 | 0.012059 | 0.012449 | 0.012476 |
| hole_clearance | 200.0000 | 0.009937 | 0.001325 | 0.007810 | 0.008026 | 0.009984 | 0.011841 | 0.011989 |
| control_action_scale_multiplier | 200.0000 | 0.981785 | 0.098398 | 0.800933 | 0.833942 | 0.980038 | 1.1556 | 1.1590 |
| control_action_noise_std | 200.0000 | 0.000309 | 0.000239 | 0.000002 | 0.000020 | 0.000220 | 0.000714 | 0.000756 |
| control_action_delay | 200.0000 | 1.5100 | 0.721041 | 0.000000 | 0.000000 | 2.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 200.0000 | 0.704795 | 0.125621 | 0.553284 | 0.557371 | 0.661998 | 0.958174 | 0.975390 |
| fixture_height_offset | 200.0000 | -0.000020 | 0.000573 | -0.001000 | -0.000828 | -0.000002 | 0.000847 | 0.000984 |
| table_height_offset | 200.0000 | -0.000023 | 0.000546 | -0.000966 | -0.000838 | -0.000111 | 0.000826 | 0.000981 |
| contact_friction_multiplier | 200.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solref_time_multiplier | 200.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solref_damping_multiplier | 200.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solimp_width_multiplier | 200.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| joint_damping_multiplier | 200.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| actuator_kp_multiplier | 200.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| desired_z | 200.0000 | 0.721301 | 0.014807 | 0.675862 | 0.688438 | 0.729456 | 0.730461 | 0.730894 |
| step_id | 200.0000 | 40.7150 | 71.5889 | 0.000000 | 0.000000 | 5.0000 | 197.0000 | 199.0000 |
| hole_center_offset_x | 200.0000 | 0.000274 | 0.001089 | -0.001975 | -0.001436 | 0.000429 | 0.001840 | 0.001969 |
| hole_center_offset_y | 200.0000 | -0.000095 | 0.001251 | -0.001952 | -0.001808 | -0.000300 | 0.001850 | 0.001904 |
| hole_center_offset_norm | 200.0000 | 0.001588 | 0.000558 | 0.000442 | 0.000660 | 0.001738 | 0.002255 | 0.002661 |
| action_norm | 200.0000 | 1.2857 | 0.136006 | 1.0001 | 1.0374 | 1.2502 | 1.4142 | 1.4142 |
| raw_action_norm | 200.0000 | 0.006428 | 0.000680 | 0.005000 | 0.005187 | 0.006251 | 0.007071 | 0.007071 |
| unique_episode_id_count | 53.0000 | 53.0000 | 0.000000 | 53.0000 | 53.0000 | 53.0000 | 53.0000 | 53.0000 |
