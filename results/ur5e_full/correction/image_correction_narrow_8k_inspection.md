# Image Correction Dataset Inspection

- Dataset: `datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_8k_min006.npz`
- Metadata: `datasets\ur5e_full\correction\image_correction_narrow_near_hole_failure_window_8k_min006.npz.json`
- Schema: `image_correction_v1_policy_failure_window`
- Samples: `1836`
- Unique source episodes: `383`
- Episodes completed while collecting: `4000`
- Selection: `near_hole_failure_window`
- Scenario preset: `targeted`
- Tier preset: `narrow`
- Min correction norm: `0.006`
- Has near-hole crops: `True`

## Correction Signals

| Signal | Rate |
| --- | ---: |
| near hole | 1.0000 |
| failure window | 1.0000 |
| opposed actions | 0.521786 |
| policy down or oracle up | 0.950980 |
| policy down and oracle less down | 0.989651 |
| opposed actions near hole | 0.521786 |

## Outcome Counts

| Outcome | Samples |
| --- | ---: |
| collision | 857 |
| timeout | 979 |

## Scenario Counts

| Scenario | Samples |
| --- | ---: |
| full_light_geometry | 843 |
| hard_full_light_bucket | 993 |

## Tier Counts

| Tier | Samples |
| --- | ---: |
| narrow | 1836 |

## Arrays

| Key | Shape | Dtype |
| --- | --- | --- |
| `action_cosine` | `[1836]` | `float32` |
| `actions` | `[1836, 3]` | `float32` |
| `actuator_kp_multiplier` | `[1836]` | `float32` |
| `cam_images` | `[1836, 100, 100, 1]` | `uint8` |
| `contact_friction_multiplier` | `[1836]` | `float32` |
| `contact_solimp_width_multiplier` | `[1836]` | `float32` |
| `contact_solref_damping_multiplier` | `[1836]` | `float32` |
| `contact_solref_time_multiplier` | `[1836]` | `float32` |
| `control_action_delay` | `[1836]` | `int32` |
| `control_action_filter_alpha` | `[1836]` | `float32` |
| `control_action_noise_std` | `[1836]` | `float32` |
| `control_action_scale_multiplier` | `[1836]` | `float32` |
| `correction_norm` | `[1836]` | `float32` |
| `correction_raw_actions` | `[1836, 3]` | `float32` |
| `correction_xy_norm` | `[1836]` | `float32` |
| `desired_z` | `[1836]` | `float32` |
| `dist_xy` | `[1836]` | `float32` |
| `dist_z` | `[1836]` | `float32` |
| `episode_collision` | `[1836]` | `bool` |
| `episode_id` | `[1836]` | `int32` |
| `episode_outcome` | `[1836]` | `<U9` |
| `episode_success` | `[1836]` | `bool` |
| `episode_timeout` | `[1836]` | `bool` |
| `failure_window` | `[1836]` | `bool` |
| `final_step` | `[1836]` | `int32` |
| `fixture_height_offset` | `[1836]` | `float32` |
| `hole_center_offset` | `[1836, 2]` | `float32` |
| `hole_clearance` | `[1836]` | `float32` |
| `hole_half_size` | `[1836]` | `float32` |
| `joint_damping_multiplier` | `[1836]` | `float32` |
| `near_hole` | `[1836]` | `bool` |
| `near_hole_crops` | `[1836, 64, 64, 1]` | `uint8` |
| `opposed_actions` | `[1836]` | `bool` |
| `oracle_norm` | `[1836]` | `float32` |
| `peg_radius` | `[1836]` | `float32` |
| `peg_tip_pos` | `[1836, 3]` | `float32` |
| `policy_actions` | `[1836, 3]` | `float32` |
| `policy_down_or_oracle_up` | `[1836]` | `bool` |
| `policy_down_oracle_less_down` | `[1836]` | `bool` |
| `policy_norm` | `[1836]` | `float32` |
| `policy_raw_actions` | `[1836, 3]` | `float32` |
| `raw_actions` | `[1836, 3]` | `float32` |
| `scenario` | `[1836]` | `<U22` |
| `seed` | `[1836]` | `int32` |
| `step_id` | `[1836]` | `int32` |
| `steps_to_end` | `[1836]` | `int32` |
| `table_height_offset` | `[1836]` | `float32` |
| `target_pos` | `[1836, 3]` | `float32` |
| `tier` | `[1836]` | `<U6` |
| `z_above_target` | `[1836]` | `float32` |

## Distributions

| Metric | Count | Mean | Std | Min | P05 | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hole_half_size | 1836.0 | 0.019119 | 0.001169 | 0.017000 | 0.017204 | 0.019186 | 0.020864 | 0.020977 |
| peg_radius | 1836.0 | 0.011967 | 0.000288 | 0.011501 | 0.011537 | 0.011956 | 0.012426 | 0.012498 |
| hole_clearance | 1836.0 | 0.007152 | 0.001215 | 0.004707 | 0.005171 | 0.007186 | 0.008968 | 0.009406 |
| control_action_scale_multiplier | 1836.0 | 1.0026 | 0.097942 | 0.800449 | 0.832250 | 1.0154 | 1.1726 | 1.1980 |
| control_action_noise_std | 1836.0 | 0.000250 | 0.000211 | 0.000001 | 0.000014 | 0.000174 | 0.000692 | 0.000798 |
| control_action_delay | 1836.0 | 1.5196 | 0.762797 | 0.000000 | 0.000000 | 2.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 1836.0 | 0.690635 | 0.114952 | 0.550344 | 0.558617 | 0.661853 | 0.935153 | 0.998494 |
| fixture_height_offset | 1836.0 | -0.000024 | 0.000595 | -0.000996 | -0.000903 | -0.000059 | 0.000887 | 0.001000 |
| table_height_offset | 1836.0 | -0.000021 | 0.000558 | -0.000999 | -0.000906 | -0.000022 | 0.000875 | 0.000998 |
| desired_z | 1836.0 | 0.702849 | 0.025643 | 0.670204 | 0.673571 | 0.687063 | 0.730835 | 0.731000 |
| step_id | 1836.0 | 130.2996 | 71.2957 | 17.0000 | 29.0000 | 192.0000 | 199.0000 | 199.0000 |
| steps_to_end | 1836.0 | 3.9286 | 2.2706 | 1.0000 | 1.0000 | 4.0000 | 8.0000 | 8.0000 |
| dist_xy | 1836.0 | 0.014978 | 0.008414 | 0.005063 | 0.005858 | 0.009186 | 0.026790 | 0.029963 |
| dist_z | 1836.0 | 0.028468 | 0.022310 | 0.007134 | 0.007247 | 0.008098 | 0.055074 | 0.058309 |
| z_above_target | 1836.0 | 0.028468 | 0.022310 | 0.007134 | 0.007247 | 0.008098 | 0.055074 | 0.058309 |
| policy_norm | 1836.0 | 0.004203 | 0.001078 | 0.000746 | 0.002411 | 0.004159 | 0.005933 | 0.007133 |
| oracle_norm | 1836.0 | 0.006817 | 0.000585 | 0.005000 | 0.005192 | 0.007071 | 0.007071 | 0.007071 |
| correction_norm | 1836.0 | 0.008094 | 0.001610 | 0.006000 | 0.006128 | 0.007690 | 0.010845 | 0.012181 |
| correction_xy_norm | 1836.0 | 0.003808 | 0.002396 | 0.000051 | 0.000515 | 0.004260 | 0.007370 | 0.009831 |
| action_cosine | 1836.0 | -0.129775 | 0.528516 | -0.997522 | -0.917963 | -0.080782 | 0.521052 | 0.583460 |
| near_hole_rate | 1836.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| failure_window_rate | 1836.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| opposed_actions_rate | 1836.0 | 0.521786 | 0.499525 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| policy_down_or_oracle_up_rate | 1836.0 | 0.950980 | 0.215909 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| policy_down_oracle_less_down_rate | 1836.0 | 0.989651 | 0.101200 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| episode_success_rate | 1836.0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| episode_collision_rate | 1836.0 | 0.466776 | 0.498895 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| episode_timeout_rate | 1836.0 | 0.533224 | 0.498895 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| hole_center_offset_x | 1836.0 | 0.000167 | 0.001139 | -0.001989 | -0.001613 | 0.000283 | 0.001816 | 0.001991 |
| hole_center_offset_y | 1836.0 | -0.000059 | 0.001133 | -0.001982 | -0.001799 | -0.000079 | 0.001816 | 0.001998 |
| hole_center_offset_norm | 1836.0 | 0.001508 | 0.000581 | 0.000023 | 0.000407 | 0.001556 | 0.002338 | 0.002809 |
| action_norm | 1836.0 | 1.3634 | 0.117066 | 1.0000 | 1.0383 | 1.4142 | 1.4142 | 1.4142 |
| raw_action_norm | 1836.0 | 0.006817 | 0.000585 | 0.005000 | 0.005192 | 0.007071 | 0.007071 | 0.007071 |
| policy_action_norm | 1836.0 | 0.840680 | 0.215658 | 0.149137 | 0.482268 | 0.831741 | 1.1866 | 1.4266 |
| policy_raw_action_norm | 1836.0 | 0.004203 | 0.001078 | 0.000746 | 0.002411 | 0.004159 | 0.005933 | 0.007133 |
| correction_raw_action_norm | 1836.0 | 0.008094 | 0.001610 | 0.006000 | 0.006128 | 0.007690 | 0.010845 | 0.012181 |
