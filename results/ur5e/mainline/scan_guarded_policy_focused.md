# Guarded Policy Parameter Scan

- Generated: `2026-05-08T00:33:43`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `default`
- Preset: `focused`
- Scenario preset: `targeted`
- Candidates: `13`
- Episodes per candidate/scenario: `30`
- Seed: `91000`
- Guard scenario filter: `geometry`

## Candidate Summary

| Candidate | visual_camera_control | full_light_geometry | full_contact_light | hard_full_light_bucket | Mean success | Mean collision | Guard steps | Guard ep. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `guard_xy060_z100_blend100_down0035_align020` | 1.000 | 0.667 | 0.667 | 0.600 | 0.733 | 0.258 | 24.4 | 0.750 |
| `guard_xy060_z100_blend050_down0035_align025` | 0.967 | 0.600 | 0.700 | 0.667 | 0.733 | 0.267 | 27.1 | 0.750 |
| `guard_xy060_z100_blend100_down0035_align015` | 0.967 | 0.667 | 0.667 | 0.600 | 0.725 | 0.267 | 25.0 | 0.750 |
| `guard_xy060_z100_blend075_down0035_align025` | 1.000 | 0.567 | 0.667 | 0.633 | 0.717 | 0.275 | 29.1 | 0.750 |
| `guard_xy060_z100_blend100_down0035_align025` | 1.000 | 0.600 | 0.633 | 0.567 | 0.700 | 0.283 | 26.4 | 0.750 |
| `guard_xy060_z080_blend100_down0035_align025` | 1.000 | 0.600 | 0.633 | 0.567 | 0.700 | 0.283 | 26.4 | 0.750 |
| `guard_xy060_z100_blend100_down0025_align025` | 1.000 | 0.600 | 0.667 | 0.500 | 0.692 | 0.292 | 26.8 | 0.750 |
| `guard_xy060_z100_blend100_down0045_align025` | 1.000 | 0.600 | 0.633 | 0.533 | 0.692 | 0.292 | 28.1 | 0.750 |
| `guard_xy060_z060_blend100_down0035_align025` | 0.967 | 0.600 | 0.467 | 0.633 | 0.667 | 0.325 | 25.2 | 0.750 |
| `guard_xy040_z100_blend100_down0035_align025` | 1.000 | 0.500 | 0.667 | 0.467 | 0.658 | 0.317 | 29.9 | 0.725 |
| `no_guard` | 0.933 | 0.667 | 0.533 | 0.500 | 0.658 | 0.333 | 0.0 | 0.000 |
| `guard_xy050_z100_blend100_down0035_align025` | 1.000 | 0.500 | 0.633 | 0.467 | 0.650 | 0.325 | 29.4 | 0.742 |
| `guard_xy070_z100_blend100_down0035_align025` | 1.000 | 0.533 | 0.500 | 0.467 | 0.625 | 0.358 | 29.2 | 0.750 |

## Per-Scenario Rows

| Candidate | Scenario | Success | Collision | Timeout | Return | Steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `no_guard` | visual_camera_control | 0.933 | 0.067 | 0.000 | 134.107 | 34.1 | 0.0 | 0.000 | 0.00637 | 0.01251 |
| `guard_xy060_z100_blend100_down0035_align025` | visual_camera_control | 1.000 | 0.000 | 0.000 | 155.461 | 27.5 | 0.0 | 0.000 | 0.00416 | 0.00791 |
| `guard_xy040_z100_blend100_down0035_align025` | visual_camera_control | 1.000 | 0.000 | 0.000 | 155.646 | 27.6 | 0.0 | 0.000 | 0.00410 | 0.00791 |
| `guard_xy050_z100_blend100_down0035_align025` | visual_camera_control | 1.000 | 0.000 | 0.000 | 155.301 | 27.3 | 0.0 | 0.000 | 0.00417 | 0.00792 |
| `guard_xy070_z100_blend100_down0035_align025` | visual_camera_control | 1.000 | 0.000 | 0.000 | 155.527 | 27.5 | 0.0 | 0.000 | 0.00409 | 0.00792 |
| `guard_xy060_z060_blend100_down0035_align025` | visual_camera_control | 0.967 | 0.033 | 0.000 | 143.303 | 31.0 | 0.0 | 0.000 | 0.00515 | 0.01019 |
| `guard_xy060_z080_blend100_down0035_align025` | visual_camera_control | 1.000 | 0.000 | 0.000 | 155.375 | 27.3 | 0.0 | 0.000 | 0.00417 | 0.00794 |
| `guard_xy060_z100_blend075_down0035_align025` | visual_camera_control | 1.000 | 0.000 | 0.000 | 155.757 | 27.6 | 0.0 | 0.000 | 0.00406 | 0.00792 |
| `guard_xy060_z100_blend050_down0035_align025` | visual_camera_control | 0.967 | 0.033 | 0.000 | 144.050 | 31.4 | 0.0 | 0.000 | 0.00521 | 0.01022 |
| `guard_xy060_z100_blend100_down0025_align025` | visual_camera_control | 1.000 | 0.000 | 0.000 | 155.186 | 27.2 | 0.0 | 0.000 | 0.00409 | 0.00792 |
| `guard_xy060_z100_blend100_down0045_align025` | visual_camera_control | 1.000 | 0.000 | 0.000 | 155.823 | 27.7 | 0.0 | 0.000 | 0.00421 | 0.00793 |
| `guard_xy060_z100_blend100_down0035_align020` | visual_camera_control | 1.000 | 0.000 | 0.000 | 155.605 | 27.5 | 0.0 | 0.000 | 0.00413 | 0.00792 |
| `guard_xy060_z100_blend100_down0035_align015` | visual_camera_control | 0.967 | 0.033 | 0.000 | 146.185 | 30.3 | 0.0 | 0.000 | 0.00528 | 0.01022 |
| `no_guard` | full_light_geometry | 0.667 | 0.300 | 0.033 | 15.245 | 27.4 | 0.0 | 0.000 | 0.00989 | 0.01864 |
| `guard_xy060_z100_blend100_down0035_align025` | full_light_geometry | 0.600 | 0.400 | 0.000 | -19.530 | 40.8 | 39.7 | 1.000 | 0.01158 | 0.02810 |
| `guard_xy040_z100_blend100_down0035_align025` | full_light_geometry | 0.500 | 0.500 | 0.000 | -43.402 | 55.0 | 52.3 | 1.000 | 0.01298 | 0.03609 |
| `guard_xy050_z100_blend100_down0035_align025` | full_light_geometry | 0.500 | 0.500 | 0.000 | -50.560 | 49.5 | 47.7 | 1.000 | 0.01290 | 0.03509 |
| `guard_xy070_z100_blend100_down0035_align025` | full_light_geometry | 0.533 | 0.467 | 0.000 | -40.630 | 46.7 | 46.2 | 1.000 | 0.01272 | 0.03245 |
| `guard_xy060_z060_blend100_down0035_align025` | full_light_geometry | 0.600 | 0.400 | 0.000 | -10.644 | 47.8 | 42.6 | 1.000 | 0.01118 | 0.03090 |
| `guard_xy060_z080_blend100_down0035_align025` | full_light_geometry | 0.600 | 0.400 | 0.000 | -19.531 | 40.8 | 39.7 | 1.000 | 0.01158 | 0.02810 |
| `guard_xy060_z100_blend075_down0035_align025` | full_light_geometry | 0.567 | 0.433 | 0.000 | -17.352 | 50.6 | 49.5 | 1.000 | 0.01158 | 0.03293 |
| `guard_xy060_z100_blend050_down0035_align025` | full_light_geometry | 0.600 | 0.400 | 0.000 | 2.699 | 53.5 | 52.5 | 1.000 | 0.01124 | 0.02954 |
| `guard_xy060_z100_blend100_down0025_align025` | full_light_geometry | 0.600 | 0.367 | 0.033 | 0.648 | 47.4 | 46.3 | 1.000 | 0.01143 | 0.03151 |
| `guard_xy060_z100_blend100_down0045_align025` | full_light_geometry | 0.600 | 0.400 | 0.000 | -16.917 | 45.5 | 44.4 | 1.000 | 0.01158 | 0.03019 |
| `guard_xy060_z100_blend100_down0035_align020` | full_light_geometry | 0.667 | 0.333 | 0.000 | 12.229 | 35.9 | 34.9 | 1.000 | 0.01058 | 0.02493 |
| `guard_xy060_z100_blend100_down0035_align015` | full_light_geometry | 0.667 | 0.333 | 0.000 | 24.051 | 39.0 | 37.9 | 1.000 | 0.01029 | 0.02588 |
| `no_guard` | full_contact_light | 0.533 | 0.467 | 0.000 | -45.975 | 31.9 | 0.0 | 0.000 | 0.01268 | 0.02406 |
| `guard_xy060_z100_blend100_down0035_align025` | full_contact_light | 0.633 | 0.333 | 0.033 | -1.304 | 40.6 | 39.6 | 1.000 | 0.01077 | 0.02763 |
| `guard_xy040_z100_blend100_down0035_align025` | full_contact_light | 0.667 | 0.300 | 0.033 | 15.528 | 40.7 | 38.0 | 0.967 | 0.00991 | 0.02621 |
| `guard_xy050_z100_blend100_down0035_align025` | full_contact_light | 0.633 | 0.333 | 0.033 | 0.066 | 40.3 | 38.6 | 1.000 | 0.01081 | 0.02762 |
| `guard_xy070_z100_blend100_down0035_align025` | full_contact_light | 0.500 | 0.467 | 0.033 | -51.579 | 46.2 | 45.7 | 1.000 | 0.01333 | 0.03471 |
| `guard_xy060_z060_blend100_down0035_align025` | full_contact_light | 0.467 | 0.533 | 0.000 | -74.489 | 39.9 | 34.7 | 1.000 | 0.01412 | 0.03265 |
| `guard_xy060_z080_blend100_down0035_align025` | full_contact_light | 0.633 | 0.333 | 0.033 | -1.304 | 40.6 | 39.6 | 1.000 | 0.01077 | 0.02763 |
| `guard_xy060_z100_blend075_down0035_align025` | full_contact_light | 0.667 | 0.333 | 0.000 | 12.276 | 40.1 | 39.1 | 1.000 | 0.01062 | 0.02589 |
| `guard_xy060_z100_blend050_down0035_align025` | full_contact_light | 0.700 | 0.300 | 0.000 | 26.011 | 35.2 | 34.2 | 1.000 | 0.01001 | 0.02277 |
| `guard_xy060_z100_blend100_down0025_align025` | full_contact_light | 0.667 | 0.333 | 0.000 | -1.062 | 32.1 | 31.1 | 1.000 | 0.01083 | 0.02420 |
| `guard_xy060_z100_blend100_down0045_align025` | full_contact_light | 0.633 | 0.333 | 0.033 | -2.462 | 40.4 | 39.4 | 1.000 | 0.01096 | 0.02739 |
| `guard_xy060_z100_blend100_down0035_align020` | full_contact_light | 0.667 | 0.333 | 0.000 | 7.583 | 35.3 | 34.3 | 1.000 | 0.01083 | 0.02523 |
| `guard_xy060_z100_blend100_down0035_align015` | full_contact_light | 0.667 | 0.333 | 0.000 | 16.024 | 34.4 | 33.4 | 1.000 | 0.01064 | 0.02498 |
| `no_guard` | hard_full_light_bucket | 0.500 | 0.500 | 0.000 | -76.145 | 19.1 | 0.0 | 0.000 | 0.01523 | 0.02220 |
| `guard_xy060_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.567 | 0.400 | 0.033 | -35.623 | 27.6 | 26.4 | 1.000 | 0.01389 | 0.02559 |
| `guard_xy040_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.467 | 0.467 | 0.067 | -61.427 | 32.5 | 29.1 | 0.933 | 0.01546 | 0.03149 |
| `guard_xy050_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.467 | 0.467 | 0.067 | -61.116 | 33.4 | 31.2 | 0.967 | 0.01546 | 0.03140 |
| `guard_xy070_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.467 | 0.500 | 0.033 | -78.555 | 25.5 | 24.9 | 1.000 | 0.01638 | 0.02992 |
| `guard_xy060_z060_blend100_down0035_align025` | hard_full_light_bucket | 0.633 | 0.333 | 0.033 | -3.348 | 28.3 | 23.4 | 1.000 | 0.01266 | 0.02364 |
| `guard_xy060_z080_blend100_down0035_align025` | hard_full_light_bucket | 0.567 | 0.400 | 0.033 | -35.623 | 27.6 | 26.4 | 1.000 | 0.01389 | 0.02559 |
| `guard_xy060_z100_blend075_down0035_align025` | hard_full_light_bucket | 0.633 | 0.333 | 0.033 | -4.215 | 29.1 | 27.9 | 1.000 | 0.01279 | 0.02307 |
| `guard_xy060_z100_blend050_down0035_align025` | hard_full_light_bucket | 0.667 | 0.333 | 0.000 | 2.064 | 22.9 | 21.8 | 1.000 | 0.01230 | 0.02194 |
| `guard_xy060_z100_blend100_down0025_align025` | hard_full_light_bucket | 0.500 | 0.467 | 0.033 | -58.301 | 30.8 | 29.7 | 1.000 | 0.01509 | 0.02984 |
| `guard_xy060_z100_blend100_down0045_align025` | hard_full_light_bucket | 0.533 | 0.433 | 0.033 | -45.757 | 29.9 | 28.7 | 1.000 | 0.01419 | 0.02823 |
| `guard_xy060_z100_blend100_down0035_align020` | hard_full_light_bucket | 0.600 | 0.367 | 0.033 | -14.241 | 29.5 | 28.4 | 1.000 | 0.01344 | 0.02605 |
| `guard_xy060_z100_blend100_down0035_align015` | hard_full_light_bucket | 0.600 | 0.367 | 0.033 | -5.898 | 29.7 | 28.5 | 1.000 | 0.01335 | 0.02562 |
