# Image Correction Dataset Inspection

- Dataset: `datasets\image_correction_ur5e_adapter_medium_targeted_failure_window_2k_oracle.npz`
- Metadata: `datasets\image_correction_ur5e_adapter_medium_targeted_failure_window_2k_oracle.npz.json`
- Schema: `image_correction_v1_policy_failure_window`
- Samples: `2000`
- Unique source episodes: `492`
- Episodes completed while collecting: `1207`
- Selection: `failure_window`
- Scenario preset: `targeted`
- Tier preset: `medium`
- Min correction norm: `0.004`
- Has near-hole crops: `True`

## Correction Signals

| Signal | Rate |
| --- | ---: |
| near hole | 0.540500 |
| failure window | 1.0000 |
| opposed actions | 0.285500 |
| policy down or oracle up | 0.189000 |
| policy down and oracle less down | 0.649500 |
| opposed actions near hole | 0.374653 |

## Outcome Counts

| Outcome | Samples |
| --- | ---: |
| collision | 1565 |
| timeout | 435 |

## Scenario Counts

| Scenario | Samples |
| --- | ---: |
| full_light_geometry | 1000 |
| hard_full_light_bucket | 1000 |

## Tier Counts

| Tier | Samples |
| --- | ---: |
| medium | 2000 |

## Arrays

| Key | Shape | Dtype |
| --- | --- | --- |
| `action_cosine` | `[2000]` | `float32` |
| `actions` | `[2000, 3]` | `float32` |
| `actuator_kp_multiplier` | `[2000]` | `float32` |
| `cam_images` | `[2000, 100, 100, 1]` | `uint8` |
| `contact_friction_multiplier` | `[2000]` | `float32` |
| `contact_solimp_width_multiplier` | `[2000]` | `float32` |
| `contact_solref_damping_multiplier` | `[2000]` | `float32` |
| `contact_solref_time_multiplier` | `[2000]` | `float32` |
| `control_action_delay` | `[2000]` | `int32` |
| `control_action_filter_alpha` | `[2000]` | `float32` |
| `control_action_noise_std` | `[2000]` | `float32` |
| `control_action_scale_multiplier` | `[2000]` | `float32` |
| `correction_norm` | `[2000]` | `float32` |
| `correction_raw_actions` | `[2000, 3]` | `float32` |
| `correction_xy_norm` | `[2000]` | `float32` |
| `desired_z` | `[2000]` | `float32` |
| `dist_xy` | `[2000]` | `float32` |
| `dist_z` | `[2000]` | `float32` |
| `episode_collision` | `[2000]` | `bool` |
| `episode_id` | `[2000]` | `int32` |
| `episode_outcome` | `[2000]` | `<U9` |
| `episode_success` | `[2000]` | `bool` |
| `episode_timeout` | `[2000]` | `bool` |
| `failure_window` | `[2000]` | `bool` |
| `final_step` | `[2000]` | `int32` |
| `fixture_height_offset` | `[2000]` | `float32` |
| `hole_center_offset` | `[2000, 2]` | `float32` |
| `hole_clearance` | `[2000]` | `float32` |
| `hole_half_size` | `[2000]` | `float32` |
| `joint_damping_multiplier` | `[2000]` | `float32` |
| `near_hole` | `[2000]` | `bool` |
| `near_hole_crops` | `[2000, 64, 64, 1]` | `uint8` |
| `opposed_actions` | `[2000]` | `bool` |
| `oracle_norm` | `[2000]` | `float32` |
| `peg_radius` | `[2000]` | `float32` |
| `peg_tip_pos` | `[2000, 3]` | `float32` |
| `policy_actions` | `[2000, 3]` | `float32` |
| `policy_down_or_oracle_up` | `[2000]` | `bool` |
| `policy_down_oracle_less_down` | `[2000]` | `bool` |
| `policy_norm` | `[2000]` | `float32` |
| `policy_raw_actions` | `[2000, 3]` | `float32` |
| `raw_actions` | `[2000, 3]` | `float32` |
| `scenario` | `[2000]` | `<U22` |
| `seed` | `[2000]` | `int32` |
| `step_id` | `[2000]` | `int32` |
| `steps_to_end` | `[2000]` | `int32` |
| `table_height_offset` | `[2000]` | `float32` |
| `target_pos` | `[2000, 3]` | `float32` |
| `tier` | `[2000]` | `<U6` |
| `z_above_target` | `[2000]` | `float32` |

## Distributions

| Metric | Count | Mean | Std | Min | P05 | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hole_half_size | 2000.0 | 0.021857 | 0.001137 | 0.020000 | 0.020165 | 0.021835 | 0.023804 | 0.023988 |
| peg_radius | 2000.0 | 0.012001 | 0.000297 | 0.011502 | 0.011547 | 0.012004 | 0.012450 | 0.012499 |
| hole_clearance | 2000.0 | 0.009855 | 0.001159 | 0.007580 | 0.008126 | 0.009808 | 0.011853 | 0.012414 |
| control_action_scale_multiplier | 2000.0 | 0.980878 | 0.103029 | 0.800784 | 0.822721 | 0.981784 | 1.1689 | 1.1980 |
| control_action_noise_std | 2000.0 | 0.000274 | 0.000221 | 0.000000 | 0.000021 | 0.000203 | 0.000714 | 0.000796 |
| control_action_delay | 2000.0 | 1.4935 | 0.744283 | 0.000000 | 0.000000 | 2.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 2000.0 | 0.707345 | 0.126166 | 0.550427 | 0.561072 | 0.667847 | 0.963526 | 0.999367 |
| fixture_height_offset | 2000.0 | 0.000001 | 0.000583 | -0.000973 | -0.000872 | 0.000028 | 0.000898 | 0.000994 |
| table_height_offset | 2000.0 | 0.000041 | 0.000594 | -0.000998 | -0.000917 | 0.000065 | 0.000945 | 0.000999 |
| desired_z | 2000.0 | 0.716968 | 0.018108 | 0.653808 | 0.685296 | 0.729250 | 0.730822 | 0.730994 |
| step_id | 2000.0 | 59.2040 | 82.2975 | 0.000000 | 1.0000 | 6.0000 | 198.0000 | 199.0000 |
| steps_to_end | 2000.0 | 3.9730 | 2.1249 | 1.0000 | 1.0000 | 4.0000 | 8.0000 | 8.0000 |
| dist_xy | 2000.0 | 0.037585 | 0.034832 | 0.000920 | 0.008680 | 0.025934 | 0.093602 | 0.229917 |
| dist_z | 2000.0 | 0.048120 | 0.023177 | 0.000474 | 0.007968 | 0.052738 | 0.077878 | 0.081320 |
| z_above_target | 2000.0 | 0.047776 | 0.023878 | -0.013729 | 0.007899 | 0.052738 | 0.077878 | 0.081320 |
| policy_norm | 2000.0 | 0.006648 | 0.001190 | 0.000686 | 0.004600 | 0.006834 | 0.008355 | 0.008654 |
| oracle_norm | 2000.0 | 0.006538 | 0.000676 | 0.003723 | 0.005217 | 0.007071 | 0.007071 | 0.007071 |
| correction_norm | 2000.0 | 0.007754 | 0.002970 | 0.004002 | 0.004166 | 0.007132 | 0.013514 | 0.015668 |
| correction_xy_norm | 2000.0 | 0.005776 | 0.003055 | 0.000128 | 0.001503 | 0.005040 | 0.011210 | 0.012063 |
| action_cosine | 2000.0 | 0.237674 | 0.540488 | -0.999853 | -0.880076 | 0.395166 | 0.835286 | 0.994104 |
| near_hole_rate | 2000.0 | 0.540500 | 0.498357 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| failure_window_rate | 2000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| opposed_actions_rate | 2000.0 | 0.285500 | 0.451652 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| policy_down_or_oracle_up_rate | 2000.0 | 0.189000 | 0.391509 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| policy_down_oracle_less_down_rate | 2000.0 | 0.649500 | 0.477127 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| episode_success_rate | 2000.0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| episode_collision_rate | 2000.0 | 0.782500 | 0.412545 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| episode_timeout_rate | 2000.0 | 0.221500 | 0.415256 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| hole_center_offset_x | 2000.0 | 0.000044 | 0.001135 | -0.001990 | -0.001774 | 0.000056 | 0.001786 | 0.001994 |
| hole_center_offset_y | 2000.0 | -0.000063 | 0.001160 | -0.001997 | -0.001803 | 0.000004 | 0.001767 | 0.001992 |
| hole_center_offset_norm | 2000.0 | 0.001527 | 0.000556 | 0.000071 | 0.000450 | 0.001614 | 0.002315 | 0.002790 |
| action_norm | 2000.0 | 1.3076 | 0.135139 | 0.744619 | 1.0435 | 1.4142 | 1.4142 | 1.4142 |
| raw_action_norm | 2000.0 | 0.006538 | 0.000676 | 0.003723 | 0.005217 | 0.007071 | 0.007071 | 0.007071 |
| policy_action_norm | 2000.0 | 1.3295 | 0.237976 | 0.137274 | 0.919975 | 1.3667 | 1.6710 | 1.7309 |
| policy_raw_action_norm | 2000.0 | 0.006648 | 0.001190 | 0.000686 | 0.004600 | 0.006834 | 0.008355 | 0.008654 |
| correction_raw_action_norm | 2000.0 | 0.007754 | 0.002970 | 0.004002 | 0.004166 | 0.007132 | 0.013514 | 0.015668 |
