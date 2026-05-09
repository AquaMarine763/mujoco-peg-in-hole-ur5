# Image Correction Dataset Inspection

- Dataset: `datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_smoke.npz`
- Metadata: `datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_smoke.npz.json`
- Schema: `image_correction_v1_policy_failure_window`
- Samples: `256`
- Unique source episodes: `42`
- Episodes completed while collecting: `270`
- Selection: `near_hole_failure_window`
- Scenario preset: `targeted`
- Tier preset: `narrow`
- Min correction norm: `0.004`
- Has near-hole crops: `True`

## Correction Signals

| Signal | Rate |
| --- | ---: |
| near hole | 1.0000 |
| failure window | 1.0000 |
| opposed actions | 0.230469 |
| policy down or oracle up | 0.742188 |
| policy down and oracle less down | 0.980469 |
| opposed actions near hole | 0.230469 |

## Outcome Counts

| Outcome | Samples |
| --- | ---: |
| collision | 191 |
| timeout | 65 |

## Scenario Counts

| Scenario | Samples |
| --- | ---: |
| full_light_geometry | 128 |
| hard_full_light_bucket | 128 |

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
| `scenario` | `[256]` | `<U22` |
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
| hole_half_size | 256.0000 | 0.019038 | 0.001148 | 0.017012 | 0.017075 | 0.018980 | 0.020721 | 0.020736 |
| peg_radius | 256.0000 | 0.012000 | 0.000276 | 0.011525 | 0.011541 | 0.012007 | 0.012432 | 0.012474 |
| hole_clearance | 256.0000 | 0.007038 | 0.001235 | 0.004875 | 0.005035 | 0.007273 | 0.008731 | 0.008923 |
| control_action_scale_multiplier | 256.0000 | 0.967761 | 0.101481 | 0.813839 | 0.817671 | 0.933983 | 1.1356 | 1.1720 |
| control_action_noise_std | 256.0000 | 0.000267 | 0.000213 | 0.000010 | 0.000030 | 0.000183 | 0.000691 | 0.000776 |
| control_action_delay | 256.0000 | 1.3164 | 0.846341 | 0.000000 | 0.000000 | 2.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 256.0000 | 0.714179 | 0.131955 | 0.550391 | 0.550574 | 0.658572 | 0.925460 | 0.975963 |
| fixture_height_offset | 256.0000 | 0.000122 | 0.000556 | -0.000968 | -0.000799 | 0.000183 | 0.000895 | 0.000990 |
| table_height_offset | 256.0000 | -0.000150 | 0.000586 | -0.000965 | -0.000866 | -0.000226 | 0.000803 | 0.000982 |
| desired_z | 256.0000 | 0.716758 | 0.022868 | 0.673211 | 0.673829 | 0.729638 | 0.730895 | 0.730990 |
| step_id | 256.0000 | 91.9492 | 62.8295 | 27.0000 | 31.0000 | 64.0000 | 198.0000 | 199.0000 |
| steps_to_end | 256.0000 | 4.0820 | 2.2055 | 1.0000 | 1.0000 | 4.0000 | 8.0000 | 8.0000 |
| dist_xy | 256.0000 | 0.019538 | 0.007610 | 0.005769 | 0.005946 | 0.022789 | 0.027442 | 0.029940 |
| dist_z | 256.0000 | 0.041120 | 0.019568 | 0.007192 | 0.007285 | 0.051417 | 0.055367 | 0.056954 |
| z_above_target | 256.0000 | 0.041120 | 0.019568 | 0.007192 | 0.007285 | 0.051417 | 0.055367 | 0.056954 |
| policy_norm | 256.0000 | 0.004656 | 0.001010 | 0.002564 | 0.002897 | 0.004802 | 0.006087 | 0.006855 |
| oracle_norm | 256.0000 | 0.006888 | 0.000493 | 0.005048 | 0.005399 | 0.007071 | 0.007071 | 0.007071 |
| correction_norm | 256.0000 | 0.006535 | 0.001748 | 0.004008 | 0.004155 | 0.006253 | 0.010170 | 0.010904 |
| correction_xy_norm | 256.0000 | 0.002414 | 0.001972 | 0.000094 | 0.000345 | 0.001644 | 0.006091 | 0.008057 |
| action_cosine | 256.0000 | 0.310128 | 0.512658 | -0.983799 | -0.809856 | 0.497468 | 0.801663 | 0.881145 |
| near_hole_rate | 256.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| failure_window_rate | 256.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| opposed_actions_rate | 256.0000 | 0.230469 | 0.421133 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| policy_down_or_oracle_up_rate | 256.0000 | 0.742188 | 0.437430 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| policy_down_oracle_less_down_rate | 256.0000 | 0.980469 | 0.138383 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| episode_success_rate | 256.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| episode_collision_rate | 256.0000 | 0.746094 | 0.435245 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| episode_timeout_rate | 256.0000 | 0.253906 | 0.435245 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| hole_center_offset_x | 256.0000 | -0.000227 | 0.001083 | -0.001872 | -0.001774 | -0.000478 | 0.001821 | 0.001851 |
| hole_center_offset_y | 256.0000 | -0.000024 | 0.001133 | -0.001937 | -0.001863 | -0.000208 | 0.001739 | 0.001761 |
| hole_center_offset_norm | 256.0000 | 0.001491 | 0.000537 | 0.000374 | 0.000598 | 0.001544 | 0.002500 | 0.002626 |
| action_norm | 256.0000 | 1.3777 | 0.098598 | 1.0095 | 1.0798 | 1.4142 | 1.4142 | 1.4142 |
| raw_action_norm | 256.0000 | 0.006888 | 0.000493 | 0.005048 | 0.005399 | 0.007071 | 0.007071 | 0.007071 |
| policy_action_norm | 256.0000 | 0.931198 | 0.202060 | 0.512741 | 0.579474 | 0.960487 | 1.2173 | 1.3710 |
| policy_raw_action_norm | 256.0000 | 0.004656 | 0.001010 | 0.002564 | 0.002897 | 0.004802 | 0.006087 | 0.006855 |
| correction_raw_action_norm | 256.0000 | 0.006535 | 0.001748 | 0.004008 | 0.004155 | 0.006253 | 0.010170 | 0.010904 |
