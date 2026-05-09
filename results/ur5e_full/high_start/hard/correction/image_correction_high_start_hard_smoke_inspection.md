# Image Correction Dataset Inspection

- Dataset: `datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_near_hole_plateau_smoke.npz`
- Metadata: `datasets\ur5e_full\high_start\hard\correction\image_correction_high_start_hard_near_hole_plateau_smoke.npz.json`
- Schema: `image_correction_v1_policy_failure_window`
- Samples: `256`
- Unique source episodes: `18`
- Episodes completed while collecting: `29`
- Selection: `failed_episode_near_hole`
- Scenario preset: `visual`
- Tier preset: `narrow`
- Min correction norm: `0.003`
- Has near-hole crops: `True`

## Correction Signals

| Signal | Rate |
| --- | ---: |
| near hole | 1.0000 |
| failure window | 0.644531 |
| opposed actions | 0.722656 |
| policy down or oracle up | 0.867188 |
| policy down and oracle less down | 1.0000 |
| opposed actions near hole | 0.722656 |

## Outcome Counts

| Outcome | Samples |
| --- | ---: |
| collision | 96 |
| timeout | 160 |

## Scenario Counts

| Scenario | Samples |
| --- | ---: |
| visual_camera | 256 |

## Tier Counts

| Tier | Samples |
| --- | ---: |
| narrow | 256 |

## Arrays

| Key | Shape | Dtype |
| --- | --- | --- |
| `action_cosine` | `[256]` | `float32` |
| `actions` | `[256, 3]` | `float32` |
| `actuator_kp_multiplier` | `[256]` | `float32` |
| `cam_images` | `[256, 100, 100, 1]` | `uint8` |
| `contact_friction_multiplier` | `[256]` | `float32` |
| `contact_solimp_width_multiplier` | `[256]` | `float32` |
| `contact_solref_damping_multiplier` | `[256]` | `float32` |
| `contact_solref_time_multiplier` | `[256]` | `float32` |
| `control_action_delay` | `[256]` | `int32` |
| `control_action_filter_alpha` | `[256]` | `float32` |
| `control_action_noise_std` | `[256]` | `float32` |
| `control_action_scale_multiplier` | `[256]` | `float32` |
| `correction_norm` | `[256]` | `float32` |
| `correction_raw_actions` | `[256, 3]` | `float32` |
| `correction_xy_norm` | `[256]` | `float32` |
| `desired_z` | `[256]` | `float32` |
| `dist_xy` | `[256]` | `float32` |
| `dist_z` | `[256]` | `float32` |
| `episode_collision` | `[256]` | `bool` |
| `episode_id` | `[256]` | `int32` |
| `episode_outcome` | `[256]` | `<U9` |
| `episode_success` | `[256]` | `bool` |
| `episode_timeout` | `[256]` | `bool` |
| `failure_window` | `[256]` | `bool` |
| `final_step` | `[256]` | `int32` |
| `fixture_height_offset` | `[256]` | `float32` |
| `hole_center_offset` | `[256, 2]` | `float32` |
| `hole_clearance` | `[256]` | `float32` |
| `hole_half_size` | `[256]` | `float32` |
| `joint_damping_multiplier` | `[256]` | `float32` |
| `near_hole` | `[256]` | `bool` |
| `near_hole_crops` | `[256, 64, 64, 1]` | `uint8` |
| `opposed_actions` | `[256]` | `bool` |
| `oracle_norm` | `[256]` | `float32` |
| `peg_radius` | `[256]` | `float32` |
| `peg_tip_pos` | `[256, 3]` | `float32` |
| `policy_actions` | `[256, 3]` | `float32` |
| `policy_down_or_oracle_up` | `[256]` | `bool` |
| `policy_down_oracle_less_down` | `[256]` | `bool` |
| `policy_norm` | `[256]` | `float32` |
| `policy_raw_actions` | `[256, 3]` | `float32` |
| `raw_actions` | `[256, 3]` | `float32` |
| `scenario` | `[256]` | `<U13` |
| `seed` | `[256]` | `int32` |
| `step_id` | `[256]` | `int32` |
| `steps_to_end` | `[256]` | `int32` |
| `table_height_offset` | `[256]` | `float32` |
| `target_pos` | `[256, 3]` | `float32` |
| `tier` | `[256]` | `<U6` |
| `z_above_target` | `[256]` | `float32` |

## Distributions

| Metric | Count | Mean | Std | Min | P05 | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hole_half_size | 256.0000 | 0.020000 | 0.000000 | 0.020000 | 0.020000 | 0.020000 | 0.020000 | 0.020000 |
| peg_radius | 256.0000 | 0.012000 | 0.000000 | 0.012000 | 0.012000 | 0.012000 | 0.012000 | 0.012000 |
| hole_clearance | 256.0000 | 0.008000 | 0.000000 | 0.008000 | 0.008000 | 0.008000 | 0.008000 | 0.008000 |
| control_action_scale_multiplier | 256.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| control_action_noise_std | 256.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| control_action_delay | 256.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| control_action_filter_alpha | 256.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| fixture_height_offset | 256.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| table_height_offset | 256.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| desired_z | 256.0000 | 0.733303 | 0.030070 | 0.694013 | 0.696824 | 0.714381 | 0.770000 | 0.770000 |
| step_id | 256.0000 | 565.8320 | 307.2685 | 70.0000 | 89.7500 | 574.5000 | 993.0000 | 999.0000 |
| steps_to_end | 256.0000 | 161.3828 | 182.7432 | 1.0000 | 2.7500 | 56.5000 | 511.2500 | 532.0000 |
| dist_xy | 256.0000 | 0.019887 | 0.015027 | 0.007335 | 0.007804 | 0.010730 | 0.053447 | 0.059983 |
| dist_z | 256.0000 | 0.041476 | 0.032215 | 0.007932 | 0.007938 | 0.026329 | 0.102676 | 0.113201 |
| z_above_target | 256.0000 | 0.041476 | 0.032215 | 0.007932 | 0.007938 | 0.026329 | 0.102676 | 0.113201 |
| policy_norm | 256.0000 | 0.005748 | 0.000836 | 0.003402 | 0.004185 | 0.005718 | 0.007283 | 0.007317 |
| oracle_norm | 256.0000 | 0.007068 | 0.000036 | 0.006626 | 0.007071 | 0.007071 | 0.007071 | 0.007071 |
| correction_norm | 256.0000 | 0.010508 | 0.003307 | 0.003047 | 0.004232 | 0.012335 | 0.014261 | 0.014322 |
| correction_xy_norm | 256.0000 | 0.006156 | 0.003070 | 0.000191 | 0.000839 | 0.007479 | 0.010167 | 0.010263 |
| action_cosine | 256.0000 | -0.405955 | 0.667074 | -0.997980 | -0.992743 | -0.825286 | 0.825307 | 0.919429 |
| near_hole_rate | 256.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| failure_window_rate | 256.0000 | 0.644531 | 0.478655 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| opposed_actions_rate | 256.0000 | 0.722656 | 0.447688 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| policy_down_or_oracle_up_rate | 256.0000 | 0.867188 | 0.339372 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| policy_down_oracle_less_down_rate | 256.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| episode_success_rate | 256.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| episode_collision_rate | 256.0000 | 0.375000 | 0.484123 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| episode_timeout_rate | 256.0000 | 0.625000 | 0.484123 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| hole_center_offset_x | 256.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| hole_center_offset_y | 256.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| hole_center_offset_norm | 256.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| action_norm | 256.0000 | 1.4136 | 0.007230 | 1.3251 | 1.4142 | 1.4142 | 1.4142 | 1.4142 |
| raw_action_norm | 256.0000 | 0.007068 | 0.000036 | 0.006626 | 0.007071 | 0.007071 | 0.007071 | 0.007071 |
| policy_action_norm | 256.0000 | 1.1497 | 0.167189 | 0.680414 | 0.837048 | 1.1436 | 1.4567 | 1.4633 |
| policy_raw_action_norm | 256.0000 | 0.005748 | 0.000836 | 0.003402 | 0.004185 | 0.005718 | 0.007283 | 0.007317 |
| correction_raw_action_norm | 256.0000 | 0.010508 | 0.003307 | 0.003047 | 0.004232 | 0.012335 | 0.014261 | 0.014322 |
