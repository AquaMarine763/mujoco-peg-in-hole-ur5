# Image Correction Dataset Inspection

- Dataset: `datasets\image_correction_ur5e_adapter_medium_targeted_near_hole_failure_window_10k_min006_oracle.npz`
- Metadata: `datasets\image_correction_ur5e_adapter_medium_targeted_near_hole_failure_window_10k_min006_oracle.npz.json`
- Schema: `image_correction_v1_policy_failure_window`
- Samples: `8405`
- Unique source episodes: `2616`
- Episodes completed while collecting: `16003`
- Selection: `near_hole_failure_window`
- Scenario preset: `targeted`
- Tier preset: `medium`
- Min correction norm: `0.006`
- Has near-hole crops: `True`

## Correction Signals

| Signal | Rate |
| --- | ---: |
| near hole | 1.0000 |
| failure window | 1.0000 |
| opposed actions | 0.469958 |
| policy down or oracle up | 0.194527 |
| policy down and oracle less down | 0.439024 |
| opposed actions near hole | 0.469958 |

## Outcome Counts

| Outcome | Samples |
| --- | ---: |
| collision | 4234 |
| timeout | 4171 |

## Scenario Counts

| Scenario | Samples |
| --- | ---: |
| full_light_geometry | 5000 |
| hard_full_light_bucket | 3405 |

## Tier Counts

| Tier | Samples |
| --- | ---: |
| medium | 8405 |

## Arrays

| Key | Shape | Dtype |
| --- | --- | --- |
| `action_cosine` | `[8405]` | `float32` |
| `actions` | `[8405, 3]` | `float32` |
| `actuator_kp_multiplier` | `[8405]` | `float32` |
| `cam_images` | `[8405, 100, 100, 1]` | `uint8` |
| `contact_friction_multiplier` | `[8405]` | `float32` |
| `contact_solimp_width_multiplier` | `[8405]` | `float32` |
| `contact_solref_damping_multiplier` | `[8405]` | `float32` |
| `contact_solref_time_multiplier` | `[8405]` | `float32` |
| `control_action_delay` | `[8405]` | `int32` |
| `control_action_filter_alpha` | `[8405]` | `float32` |
| `control_action_noise_std` | `[8405]` | `float32` |
| `control_action_scale_multiplier` | `[8405]` | `float32` |
| `correction_norm` | `[8405]` | `float32` |
| `correction_raw_actions` | `[8405, 3]` | `float32` |
| `correction_xy_norm` | `[8405]` | `float32` |
| `desired_z` | `[8405]` | `float32` |
| `dist_xy` | `[8405]` | `float32` |
| `dist_z` | `[8405]` | `float32` |
| `episode_collision` | `[8405]` | `bool` |
| `episode_id` | `[8405]` | `int32` |
| `episode_outcome` | `[8405]` | `<U9` |
| `episode_success` | `[8405]` | `bool` |
| `episode_timeout` | `[8405]` | `bool` |
| `failure_window` | `[8405]` | `bool` |
| `final_step` | `[8405]` | `int32` |
| `fixture_height_offset` | `[8405]` | `float32` |
| `hole_center_offset` | `[8405, 2]` | `float32` |
| `hole_clearance` | `[8405]` | `float32` |
| `hole_half_size` | `[8405]` | `float32` |
| `joint_damping_multiplier` | `[8405]` | `float32` |
| `near_hole` | `[8405]` | `bool` |
| `near_hole_crops` | `[8405, 64, 64, 1]` | `uint8` |
| `opposed_actions` | `[8405]` | `bool` |
| `oracle_norm` | `[8405]` | `float32` |
| `peg_radius` | `[8405]` | `float32` |
| `peg_tip_pos` | `[8405, 3]` | `float32` |
| `policy_actions` | `[8405, 3]` | `float32` |
| `policy_down_or_oracle_up` | `[8405]` | `bool` |
| `policy_down_oracle_less_down` | `[8405]` | `bool` |
| `policy_norm` | `[8405]` | `float32` |
| `policy_raw_actions` | `[8405, 3]` | `float32` |
| `raw_actions` | `[8405, 3]` | `float32` |
| `scenario` | `[8405]` | `<U22` |
| `seed` | `[8405]` | `int32` |
| `step_id` | `[8405]` | `int32` |
| `steps_to_end` | `[8405]` | `int32` |
| `table_height_offset` | `[8405]` | `float32` |
| `target_pos` | `[8405, 3]` | `float32` |
| `tier` | `[8405]` | `<U6` |
| `z_above_target` | `[8405]` | `float32` |

## Distributions

| Metric | Count | Mean | Std | Min | P05 | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hole_half_size | 8405.0 | 0.021754 | 0.001146 | 0.020000 | 0.020129 | 0.021631 | 0.023745 | 0.024000 |
| peg_radius | 8405.0 | 0.011997 | 0.000286 | 0.011500 | 0.011549 | 0.011993 | 0.012445 | 0.012500 |
| hole_clearance | 8405.0 | 0.009757 | 0.001195 | 0.007572 | 0.008033 | 0.009614 | 0.011829 | 0.012446 |
| control_action_scale_multiplier | 8405.0 | 0.995284 | 0.106622 | 0.800171 | 0.821609 | 1.0003 | 1.1702 | 1.2000 |
| control_action_noise_std | 8405.0 | 0.000288 | 0.000227 | 0.000000 | 0.000021 | 0.000211 | 0.000730 | 0.000800 |
| control_action_delay | 8405.0 | 1.3386 | 0.802904 | 0.000000 | 0.000000 | 2.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 8405.0 | 0.721759 | 0.129932 | 0.550007 | 0.563817 | 0.680022 | 0.965951 | 0.999616 |
| fixture_height_offset | 8405.0 | -0.000037 | 0.000571 | -0.001000 | -0.000902 | -0.000041 | 0.000869 | 0.001000 |
| table_height_offset | 8405.0 | -0.000002 | 0.000573 | -0.001000 | -0.000886 | -0.000003 | 0.000901 | 0.000997 |
| desired_z | 8405.0 | 0.704258 | 0.017753 | 0.651296 | 0.680519 | 0.699863 | 0.730344 | 0.731000 |
| step_id | 8405.0 | 121.1710 | 88.5725 | 0.000000 | 3.0000 | 190.0000 | 199.0000 | 199.0000 |
| steps_to_end | 8405.0 | 4.6020 | 2.6306 | 1.0000 | 1.0000 | 4.0000 | 10.0000 | 10.0000 |
| dist_xy | 8405.0 | 0.014226 | 0.005577 | 0.000090 | 0.007606 | 0.012497 | 0.024920 | 0.029939 |
| dist_z | 8405.0 | 0.038075 | 0.021731 | 0.007424 | 0.008101 | 0.040213 | 0.070308 | 0.085510 |
| z_above_target | 8405.0 | 0.038075 | 0.021731 | 0.007424 | 0.008101 | 0.040213 | 0.070308 | 0.085510 |
| policy_norm | 8405.0 | 0.007000 | 0.001212 | 0.001303 | 0.004765 | 0.007171 | 0.008586 | 0.008660 |
| oracle_norm | 8405.0 | 0.006365 | 0.000601 | 0.003560 | 0.005275 | 0.006103 | 0.007071 | 0.007071 |
| correction_norm | 8405.0 | 0.009604 | 0.002519 | 0.006001 | 0.006300 | 0.009121 | 0.014233 | 0.015671 |
| correction_xy_norm | 8405.0 | 0.006687 | 0.003455 | 0.000014 | 0.001411 | 0.007337 | 0.011539 | 0.012065 |
| action_cosine | 8405.0 | -0.061021 | 0.479608 | -0.999238 | -0.932200 | 0.053496 | 0.531850 | 0.726457 |
| near_hole_rate | 8405.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| failure_window_rate | 8405.0 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| opposed_actions_rate | 8405.0 | 0.469958 | 0.499097 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| policy_down_or_oracle_up_rate | 8405.0 | 0.194527 | 0.395836 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| policy_down_oracle_less_down_rate | 8405.0 | 0.439024 | 0.496268 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| episode_success_rate | 8405.0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| episode_collision_rate | 8405.0 | 0.503748 | 0.499986 | 0.000000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 |
| episode_timeout_rate | 8405.0 | 0.498394 | 0.499997 | 0.000000 | 0.000000 | 0.000000 | 1.0000 | 1.0000 |
| hole_center_offset_x | 8405.0 | 0.000081 | 0.001156 | -0.001999 | -0.001766 | 0.000103 | 0.001815 | 0.001999 |
| hole_center_offset_y | 8405.0 | 0.000043 | 0.001164 | -0.001999 | -0.001783 | 0.000053 | 0.001838 | 0.002000 |
| hole_center_offset_norm | 8405.0 | 0.001536 | 0.000584 | 0.000045 | 0.000482 | 0.001623 | 0.002441 | 0.002793 |
| action_norm | 8405.0 | 1.2730 | 0.120192 | 0.711938 | 1.0549 | 1.2207 | 1.4142 | 1.4142 |
| raw_action_norm | 8405.0 | 0.006365 | 0.000601 | 0.003560 | 0.005275 | 0.006103 | 0.007071 | 0.007071 |
| policy_action_norm | 8405.0 | 1.4000 | 0.242450 | 0.260570 | 0.952966 | 1.4342 | 1.7172 | 1.7320 |
| policy_raw_action_norm | 8405.0 | 0.007000 | 0.001212 | 0.001303 | 0.004765 | 0.007171 | 0.008586 | 0.008660 |
| correction_raw_action_norm | 8405.0 | 0.009604 | 0.002519 | 0.006001 | 0.006300 | 0.009121 | 0.014233 | 0.015671 |
