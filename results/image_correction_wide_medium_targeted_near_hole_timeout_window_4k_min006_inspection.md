# Image Correction Dataset Inspection

- Dataset: `datasets\image_correction_ur5e_adapter_wide_medium_targeted_near_hole_timeout_window_4k_min006_oracle.npz`
- Metadata: `datasets\image_correction_ur5e_adapter_wide_medium_targeted_near_hole_timeout_window_4k_min006_oracle.npz.json`
- Schema: `image_correction_v1_policy_failure_window`
- Samples: `2350`
- Unique source episodes: `405`
- Episodes completed while collecting: `18150`
- Selection: `near_hole_failure_window`
- Scenario preset: `targeted`
- Tier preset: `wide_medium`
- Min correction norm: `0.006`
- Has near-hole crops: `True`

## Correction Signals

| Signal | Rate |
| --- | ---: |
| near hole | 1.0000 |
| failure window | 1.0000 |
| opposed actions | 0.653191 |
| policy down or oracle up | 0.229787 |
| policy down and oracle less down | 0.652766 |
| opposed actions near hole | 0.653191 |

## Outcome Counts

| Outcome | Samples |
| --- | ---: |
| timeout | 2350 |

## Scenario Counts

| Scenario | Samples |
| --- | ---: |
| full_light_geometry | 1267 |
| hard_full_light_bucket | 1083 |

## Tier Counts

| Tier | Samples |
| --- | ---: |
| medium | 1931 |
| wide_current | 419 |

## Arrays

| Key | Shape | Dtype |
| --- | --- | --- |
| `action_cosine` | `[2350]` | `float32` |
| `actions` | `[2350, 3]` | `float32` |
| `actuator_kp_multiplier` | `[2350]` | `float32` |
| `cam_images` | `[2350, 100, 100, 1]` | `uint8` |
| `contact_friction_multiplier` | `[2350]` | `float32` |
| `contact_solimp_width_multiplier` | `[2350]` | `float32` |
| `contact_solref_damping_multiplier` | `[2350]` | `float32` |
| `contact_solref_time_multiplier` | `[2350]` | `float32` |
| `control_action_delay` | `[2350]` | `int32` |
| `control_action_filter_alpha` | `[2350]` | `float32` |
| `control_action_noise_std` | `[2350]` | `float32` |
| `control_action_scale_multiplier` | `[2350]` | `float32` |
| `correction_norm` | `[2350]` | `float32` |
| `correction_raw_actions` | `[2350, 3]` | `float32` |
| `correction_xy_norm` | `[2350]` | `float32` |
| `desired_z` | `[2350]` | `float32` |
| `dist_xy` | `[2350]` | `float32` |
| `dist_z` | `[2350]` | `float32` |
| `episode_collision` | `[2350]` | `bool` |
| `episode_id` | `[2350]` | `int32` |
| `episode_outcome` | `[2350]` | `<U7` |
| `episode_success` | `[2350]` | `bool` |
| `episode_timeout` | `[2350]` | `bool` |
| `failure_window` | `[2350]` | `bool` |
| `final_step` | `[2350]` | `int32` |
| `fixture_height_offset` | `[2350]` | `float32` |
| `hole_center_offset` | `[2350, 2]` | `float32` |
| `hole_clearance` | `[2350]` | `float32` |
| `hole_half_size` | `[2350]` | `float32` |
| `joint_damping_multiplier` | `[2350]` | `float32` |
| `near_hole` | `[2350]` | `bool` |
| `near_hole_crops` | `[2350, 64, 64, 1]` | `uint8` |
| `opposed_actions` | `[2350]` | `bool` |
| `oracle_norm` | `[2350]` | `float32` |
| `peg_radius` | `[2350]` | `float32` |
| `peg_tip_pos` | `[2350, 3]` | `float32` |
| `policy_actions` | `[2350, 3]` | `float32` |
| `policy_down_or_oracle_up` | `[2350]` | `bool` |
| `policy_down_oracle_less_down` | `[2350]` | `bool` |
| `policy_norm` | `[2350]` | `float32` |
| `policy_raw_actions` | `[2350, 3]` | `float32` |
| `raw_actions` | `[2350, 3]` | `float32` |
| `scenario` | `[2350]` | `<U22` |
| `seed` | `[2350]` | `int32` |
| `step_id` | `[2350]` | `int32` |
| `steps_to_end` | `[2350]` | `int32` |
| `table_height_offset` | `[2350]` | `float32` |
| `target_pos` | `[2350, 3]` | `float32` |
| `tier` | `[2350]` | `<U12` |
| `z_above_target` | `[2350]` | `float32` |

## Distributions

| Metric | Count | Mean | Std | Min | P05 | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hole_half_size | 2350.0 | 0.022507 | 0.001988 | 0.020001 | 0.020148 | 0.022033 | 0.026298 | 0.028999 |
| peg_radius | 2350.0 | 0.011995 | 0.000294 | 0.011503 | 0.011546 | 0.011971 | 0.012461 | 0.012500 |
| hole_clearance | 2350.0 | 0.010512 | 0.002040 | 0.007560 | 0.008043 | 0.010059 | 0.014525 | 0.016738 |
| control_action_scale_multiplier | 2350.0 | 0.965933 | 0.105645 | 0.800078 | 0.816422 | 0.964389 | 1.1452 | 1.1976 |
| control_action_noise_std | 2350.0 | 0.000270 | 0.000225 | 0.000000 | 0.000022 | 0.000197 | 0.000723 | 0.000791 |
| control_action_delay | 2350.0 | 1.3098 | 0.848146 | 0.000000 | 0.000000 | 2.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 2350.0 | 0.716021 | 0.129019 | 0.550506 | 0.559330 | 0.667937 | 0.965106 | 0.999039 |
| fixture_height_offset | 2350.0 | -0.000074 | 0.000561 | -0.000991 | -0.000904 | -0.000107 | 0.000849 | 0.000989 |
| table_height_offset | 2350.0 | -0.000015 | 0.000570 | -0.000986 | -0.000887 | 0.000007 | 0.000897 | 0.000999 |
| desired_z | 2350.0 | 0.697090 | 0.011236 | 0.655930 | 0.681232 | 0.696846 | 0.716489 | 0.730547 |
| step_id | 2350.0 | 194.6630 | 2.7530 | 190.0000 | 190.0000 | 195.0000 | 199.0000 | 199.0000 |
| steps_to_end | 2350.0 | 5.3370 | 2.7530 | 1.0000 | 1.0000 | 5.0000 | 10.0000 | 10.0000 |
| dist_xy | 2350.0 | 0.011791 | 0.002805 | 0.001288 | 0.007873 | 0.011767 | 0.016765 | 0.020165 |
| dist_z | 2350.0 | 0.025766 | 0.019775 | 0.007330 | 0.007872 | 0.018639 | 0.075495 | 0.086339 |
| z_above_target | 2350.0 | 0.025766 | 0.019775 | 0.007330 | 0.007872 | 0.018640 | 0.075495 | 0.086339 |
| policy_norm | 2350.0 | 0.007052 | 0.001350 | 0.001343 | 0.004517 | 0.007268 | 0.008652 | 0.008660 |
| oracle_norm | 2350.0 | 0.006495 | 0.000652 | 0.003621 | 0.005305 | 0.006890 | 0.007071 | 0.007071 |
| correction_norm | 2350.0 | 0.010549 | 0.002105 | 0.006008 | 0.007084 | 0.010480 | 0.014257 | 0.015666 |
| correction_xy_norm | 2350.0 | 0.008608 | 0.002357 | 0.000293 | 0.003358 | 0.009093 | 0.011692 | 0.012069 |
| action_cosine | 2350.0 | -0.226016 | 0.399240 | -0.996500 | -0.913257 | -0.226779 | 0.418483 | 0.784691 |
| near_hole_rate | 2350.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| failure_window_rate | 2350.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| opposed_actions_rate | 2350.0 | 0.653191 | 0.475954 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| policy_down_or_oracle_up_rate | 2350.0 | 0.229787 | 0.420696 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| policy_down_oracle_less_down_rate | 2350.0 | 0.652766 | 0.476091 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| episode_success_rate | 2350.0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| episode_collision_rate | 2350.0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| episode_timeout_rate | 2350.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hole_center_offset_x | 2350.0 | 0.000015 | 0.001170 | -0.001997 | -0.001790 | 0.000013 | 0.001775 | 0.002000 |
| hole_center_offset_y | 2350.0 | 0.000100 | 0.001194 | -0.001992 | -0.001820 | 0.000158 | 0.001863 | 0.001995 |
| hole_center_offset_norm | 2350.0 | 0.001573 | 0.000576 | 0.000046 | 0.000524 | 0.001670 | 0.002461 | 0.002760 |
| action_norm | 2350.0 | 1.2989 | 0.130464 | 0.724152 | 1.0610 | 1.3780 | 1.4142 | 1.4142 |
| raw_action_norm | 2350.0 | 0.006495 | 0.000652 | 0.003621 | 0.005305 | 0.006890 | 0.007071 | 0.007071 |
| policy_action_norm | 2350.0 | 1.4104 | 0.269926 | 0.268616 | 0.903452 | 1.4535 | 1.7304 | 1.7320 |
| policy_raw_action_norm | 2350.0 | 0.007052 | 0.001350 | 0.001343 | 0.004517 | 0.007268 | 0.008652 | 0.008660 |
| correction_raw_action_norm | 2350.0 | 0.010549 | 0.002105 | 0.006008 | 0.007084 | 0.010480 | 0.014257 | 0.015666 |
