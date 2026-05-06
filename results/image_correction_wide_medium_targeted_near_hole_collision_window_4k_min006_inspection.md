# Image Correction Dataset Inspection

- Dataset: `datasets\image_correction_ur5e_adapter_wide_medium_targeted_near_hole_collision_window_4k_min006_oracle.npz`
- Metadata: `datasets\image_correction_ur5e_adapter_wide_medium_targeted_near_hole_collision_window_4k_min006_oracle.npz.json`
- Schema: `image_correction_v1_policy_failure_window`
- Samples: `4000`
- Unique source episodes: `1779`
- Episodes completed while collecting: `14990`
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
| opposed actions | 0.257500 |
| policy down or oracle up | 0.286750 |
| policy down and oracle less down | 0.513750 |
| opposed actions near hole | 0.257500 |

## Outcome Counts

| Outcome | Samples |
| --- | ---: |
| collision | 4000 |

## Scenario Counts

| Scenario | Samples |
| --- | ---: |
| full_light_geometry | 2000 |
| hard_full_light_bucket | 2000 |

## Tier Counts

| Tier | Samples |
| --- | ---: |
| medium | 2000 |
| wide_current | 2000 |

## Arrays

| Key | Shape | Dtype |
| --- | --- | --- |
| `action_cosine` | `[4000]` | `float32` |
| `actions` | `[4000, 3]` | `float32` |
| `actuator_kp_multiplier` | `[4000]` | `float32` |
| `cam_images` | `[4000, 100, 100, 1]` | `uint8` |
| `contact_friction_multiplier` | `[4000]` | `float32` |
| `contact_solimp_width_multiplier` | `[4000]` | `float32` |
| `contact_solref_damping_multiplier` | `[4000]` | `float32` |
| `contact_solref_time_multiplier` | `[4000]` | `float32` |
| `control_action_delay` | `[4000]` | `int32` |
| `control_action_filter_alpha` | `[4000]` | `float32` |
| `control_action_noise_std` | `[4000]` | `float32` |
| `control_action_scale_multiplier` | `[4000]` | `float32` |
| `correction_norm` | `[4000]` | `float32` |
| `correction_raw_actions` | `[4000, 3]` | `float32` |
| `correction_xy_norm` | `[4000]` | `float32` |
| `desired_z` | `[4000]` | `float32` |
| `dist_xy` | `[4000]` | `float32` |
| `dist_z` | `[4000]` | `float32` |
| `episode_collision` | `[4000]` | `bool` |
| `episode_id` | `[4000]` | `int32` |
| `episode_outcome` | `[4000]` | `<U9` |
| `episode_success` | `[4000]` | `bool` |
| `episode_timeout` | `[4000]` | `bool` |
| `failure_window` | `[4000]` | `bool` |
| `final_step` | `[4000]` | `int32` |
| `fixture_height_offset` | `[4000]` | `float32` |
| `hole_center_offset` | `[4000, 2]` | `float32` |
| `hole_clearance` | `[4000]` | `float32` |
| `hole_half_size` | `[4000]` | `float32` |
| `joint_damping_multiplier` | `[4000]` | `float32` |
| `near_hole` | `[4000]` | `bool` |
| `near_hole_crops` | `[4000, 64, 64, 1]` | `uint8` |
| `opposed_actions` | `[4000]` | `bool` |
| `oracle_norm` | `[4000]` | `float32` |
| `peg_radius` | `[4000]` | `float32` |
| `peg_tip_pos` | `[4000, 3]` | `float32` |
| `policy_actions` | `[4000, 3]` | `float32` |
| `policy_down_or_oracle_up` | `[4000]` | `bool` |
| `policy_down_oracle_less_down` | `[4000]` | `bool` |
| `policy_norm` | `[4000]` | `float32` |
| `policy_raw_actions` | `[4000, 3]` | `float32` |
| `raw_actions` | `[4000, 3]` | `float32` |
| `scenario` | `[4000]` | `<U22` |
| `seed` | `[4000]` | `int32` |
| `step_id` | `[4000]` | `int32` |
| `steps_to_end` | `[4000]` | `int32` |
| `table_height_offset` | `[4000]` | `float32` |
| `target_pos` | `[4000, 3]` | `float32` |
| `tier` | `[4000]` | `<U12` |
| `z_above_target` | `[4000]` | `float32` |

## Distributions

| Metric | Count | Mean | Std | Min | P05 | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hole_half_size | 4000.0 | 0.024483 | 0.002784 | 0.020000 | 0.020357 | 0.024500 | 0.028630 | 0.028984 |
| peg_radius | 4000.0 | 0.011987 | 0.000290 | 0.011500 | 0.011540 | 0.011985 | 0.012453 | 0.012500 |
| hole_clearance | 4000.0 | 0.012496 | 0.002789 | 0.007528 | 0.008367 | 0.012489 | 0.016595 | 0.017446 |
| control_action_scale_multiplier | 4000.0 | 0.997411 | 0.107133 | 0.800041 | 0.822293 | 1.0060 | 1.1764 | 1.1999 |
| control_action_noise_std | 4000.0 | 0.000270 | 0.000223 | 0.000000 | 0.000019 | 0.000191 | 0.000721 | 0.000798 |
| control_action_delay | 4000.0 | 1.5453 | 0.686624 | 0.000000 | 0.000000 | 2.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 4000.0 | 0.703252 | 0.121441 | 0.550271 | 0.565226 | 0.663864 | 0.954466 | 0.999862 |
| fixture_height_offset | 4000.0 | -0.000007 | 0.000590 | -0.000999 | -0.000911 | -0.000003 | 0.000895 | 0.001000 |
| table_height_offset | 4000.0 | -0.000017 | 0.000577 | -0.000998 | -0.000897 | -0.000046 | 0.000919 | 0.000999 |
| desired_z | 4000.0 | 0.713924 | 0.019553 | 0.651349 | 0.672988 | 0.722439 | 0.730728 | 0.731000 |
| step_id | 4000.0 | 57.3625 | 71.1721 | 0.000000 | 2.0000 | 8.0000 | 185.0000 | 199.0000 |
| steps_to_end | 4000.0 | 4.1930 | 2.5492 | 1.0000 | 1.0000 | 4.0000 | 9.0000 | 10.0000 |
| dist_xy | 4000.0 | 0.017266 | 0.006318 | 0.000173 | 0.005774 | 0.018111 | 0.027166 | 0.029989 |
| dist_z | 4000.0 | 0.052902 | 0.017462 | 0.006078 | 0.009679 | 0.054150 | 0.075865 | 0.088163 |
| z_above_target | 4000.0 | 0.052902 | 0.017462 | 0.006078 | 0.009679 | 0.054150 | 0.075865 | 0.088163 |
| policy_norm | 4000.0 | 0.007142 | 0.001166 | 0.001416 | 0.004980 | 0.007259 | 0.008652 | 0.008660 |
| oracle_norm | 4000.0 | 0.006333 | 0.000580 | 0.003559 | 0.005363 | 0.006103 | 0.007071 | 0.007071 |
| correction_norm | 4000.0 | 0.008703 | 0.002506 | 0.006001 | 0.006149 | 0.007851 | 0.014131 | 0.015608 |
| correction_xy_norm | 4000.0 | 0.005423 | 0.003508 | 0.000023 | 0.001071 | 0.004250 | 0.011566 | 0.012064 |
| action_cosine | 4000.0 | 0.135147 | 0.474789 | -0.999596 | -0.908704 | 0.323085 | 0.593749 | 0.719919 |
| near_hole_rate | 4000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| failure_window_rate | 4000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| opposed_actions_rate | 4000.0 | 0.257500 | 0.437257 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| policy_down_or_oracle_up_rate | 4000.0 | 0.286750 | 0.452244 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| policy_down_oracle_less_down_rate | 4000.0 | 0.513750 | 0.499811 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| episode_success_rate | 4000.0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| episode_collision_rate | 4000.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| episode_timeout_rate | 4000.0 | 0.001500 | 0.038701 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.0000 |
| hole_center_offset_x | 4000.0 | 0.000098 | 0.001147 | -0.002000 | -0.001777 | 0.000152 | 0.001790 | 0.001998 |
| hole_center_offset_y | 4000.0 | -0.000053 | 0.001147 | -0.001996 | -0.001818 | -0.000076 | 0.001769 | 0.002000 |
| hole_center_offset_norm | 4000.0 | 0.001523 | 0.000567 | 0.000031 | 0.000477 | 0.001579 | 0.002393 | 0.002813 |
| action_norm | 4000.0 | 1.2666 | 0.116038 | 0.711881 | 1.0726 | 1.2207 | 1.4142 | 1.4142 |
| raw_action_norm | 4000.0 | 0.006333 | 0.000580 | 0.003559 | 0.005363 | 0.006103 | 0.007071 | 0.007071 |
| policy_action_norm | 4000.0 | 1.4285 | 0.233206 | 0.283294 | 0.995935 | 1.4518 | 1.7303 | 1.7320 |
| policy_raw_action_norm | 4000.0 | 0.007142 | 0.001166 | 0.001416 | 0.004980 | 0.007259 | 0.008652 | 0.008660 |
| correction_raw_action_norm | 4000.0 | 0.008703 | 0.002506 | 0.006001 | 0.006149 | 0.007851 | 0.014131 | 0.015608 |
