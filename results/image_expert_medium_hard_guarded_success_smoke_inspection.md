# Image Expert Dataset Inspection

- Dataset: `mujoco_peg_in_hole\datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_smoke_oracle.npz`
- Metadata: `mujoco_peg_in_hole\datasets\image_expert_ur5e_adapter_fixedcam_full_light_geometry_medium_hard_guarded_success_smoke_oracle.npz.json`
- Schema: `image_expert_v2_diagnostics`
- Samples: `500`
- Episodes completed: `87`
- Success rate: `0.2988505747126437`
- Collision rate: `0.7011494252873564`
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
| hole_half_size | 500.0000 | 0.022339 | 0.001043 | 0.020325 | 0.020885 | 0.022102 | 0.023931 | 0.023971 |
| peg_radius | 500.0000 | 0.011976 | 0.000260 | 0.011577 | 0.011577 | 0.011979 | 0.012339 | 0.012474 |
| hole_clearance | 500.0000 | 0.010364 | 0.001125 | 0.008471 | 0.008754 | 0.010151 | 0.012032 | 0.012210 |
| control_action_scale_multiplier | 500.0000 | 0.954316 | 0.078608 | 0.820415 | 0.828889 | 0.959423 | 1.0646 | 1.0853 |
| control_action_noise_std | 500.0000 | 0.000123 | 0.000063 | 0.000003 | 0.000010 | 0.000135 | 0.000217 | 0.000227 |
| control_action_delay | 500.0000 | 2.0000 | 0.000000 | 2.0000 | 2.0000 | 2.0000 | 2.0000 | 2.0000 |
| control_action_filter_alpha | 500.0000 | 0.627423 | 0.043511 | 0.557315 | 0.562255 | 0.626591 | 0.693665 | 0.696096 |
| fixture_height_offset | 500.0000 | -0.000054 | 0.000686 | -0.000939 | -0.000914 | -0.000021 | 0.000945 | 0.000945 |
| table_height_offset | 500.0000 | 0.000114 | 0.000519 | -0.000893 | -0.000603 | 0.000095 | 0.000833 | 0.000924 |
| contact_friction_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solref_time_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solref_damping_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| contact_solimp_width_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| joint_damping_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| actuator_kp_multiplier | 500.0000 | 1.0000 | 0.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| desired_z | 500.0000 | 0.698534 | 0.022039 | 0.654088 | 0.670699 | 0.693642 | 0.730754 | 0.730942 |
| step_id | 500.0000 | 11.0780 | 8.5839 | 0.000000 | 0.000000 | 9.0000 | 29.0000 | 36.0000 |
| hole_center_offset_x | 500.0000 | -0.000090 | 0.001080 | -0.001867 | -0.001867 | -0.000459 | 0.001696 | 0.001924 |
| hole_center_offset_y | 500.0000 | -0.000021 | 0.001170 | -0.001580 | -0.001580 | -0.000308 | 0.001883 | 0.001917 |
| hole_center_offset_norm | 500.0000 | 0.001521 | 0.000483 | 0.000414 | 0.000794 | 0.001564 | 0.002216 | 0.002216 |
| action_norm | 500.0000 | 1.1721 | 0.174033 | 0.700248 | 0.853342 | 1.2207 | 1.4142 | 1.4142 |
| raw_action_norm | 500.0000 | 0.005860 | 0.000870 | 0.003501 | 0.004267 | 0.006103 | 0.007071 | 0.007071 |
| unique_episode_id_count | 26.0000 | 26.0000 | 0.000000 | 26.0000 | 26.0000 | 26.0000 | 26.0000 | 26.0000 |
