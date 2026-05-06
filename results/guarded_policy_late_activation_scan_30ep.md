# Guarded Policy Parameter Scan

- Generated: `2026-05-07T03:59:32`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Preset: `grid`
- Scenario preset: `targeted`
- Candidates: `17`
- Episodes per candidate/scenario: `30`
- Seed: `970000`
- Guard scenario filter: `geometry`

## Candidate Summary

| Candidate | visual_camera_control | full_light_geometry | full_contact_light | hard_full_light_bucket | Mean success | Mean collision | Guard steps | Guard ep. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | 0.867 | 0.700 | 0.800 | 0.467 | 0.708 | 0.267 | 23.5 | 0.733 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | 0.867 | 0.700 | 0.800 | 0.467 | 0.708 | 0.267 | 23.5 | 0.733 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | 0.867 | 0.700 | 0.800 | 0.400 | 0.692 | 0.283 | 17.1 | 0.592 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | 0.867 | 0.700 | 0.800 | 0.400 | 0.692 | 0.283 | 17.1 | 0.592 |
| `guard_xy0p04_z0p08_blend0p75_down0p0035_align0p025` | 0.867 | 0.700 | 0.800 | 0.367 | 0.683 | 0.292 | 20.3 | 0.667 |
| `guard_xy0p04_z0p1_blend0p75_down0p0035_align0p025` | 0.867 | 0.700 | 0.800 | 0.367 | 0.683 | 0.292 | 20.3 | 0.667 |
| `guard_xy0p04_z0p06_blend0p75_down0p0035_align0p025` | 0.867 | 0.633 | 0.700 | 0.367 | 0.642 | 0.317 | 20.7 | 0.650 |
| `guard_xy0p06_z0p06_blend0p75_down0p0035_align0p025` | 0.867 | 0.633 | 0.700 | 0.367 | 0.642 | 0.317 | 19.6 | 0.717 |
| `guard_xy0p03_z0p06_blend0p75_down0p0035_align0p025` | 0.867 | 0.600 | 0.700 | 0.367 | 0.633 | 0.325 | 17.9 | 0.592 |
| `guard_xy0p02_z0p08_blend0p75_down0p0035_align0p025` | 0.867 | 0.600 | 0.667 | 0.400 | 0.633 | 0.333 | 20.4 | 0.550 |
| `guard_xy0p02_z0p1_blend0p75_down0p0035_align0p025` | 0.867 | 0.600 | 0.667 | 0.400 | 0.633 | 0.333 | 20.5 | 0.550 |
| `guard_xy0p02_z0p06_blend0p75_down0p0035_align0p025` | 0.867 | 0.567 | 0.667 | 0.367 | 0.617 | 0.342 | 19.9 | 0.550 |
| `no_guard` | 0.867 | 0.667 | 0.600 | 0.233 | 0.592 | 0.400 | 0.0 | 0.000 |
| `guard_xy0p02_z0p04_blend0p75_down0p0035_align0p025` | 0.867 | 0.600 | 0.567 | 0.300 | 0.583 | 0.400 | 16.5 | 0.492 |
| `guard_xy0p03_z0p04_blend0p75_down0p0035_align0p025` | 0.867 | 0.600 | 0.567 | 0.300 | 0.583 | 0.400 | 16.5 | 0.492 |
| `guard_xy0p04_z0p04_blend0p75_down0p0035_align0p025` | 0.867 | 0.600 | 0.567 | 0.300 | 0.583 | 0.400 | 16.5 | 0.492 |
| `guard_xy0p06_z0p04_blend0p75_down0p0035_align0p025` | 0.867 | 0.600 | 0.567 | 0.300 | 0.583 | 0.400 | 16.6 | 0.492 |

## Per-Scenario Rows

| Candidate | Scenario | Success | Collision | Timeout | Return | Steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `no_guard` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.858 | 24.4 | 0.0 | 0.000 | 0.00923 | 0.01413 |
| `guard_xy0p02_z0p04_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.837 | 24.4 | 0.0 | 0.000 | 0.00926 | 0.01414 |
| `guard_xy0p02_z0p06_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.613 | 24.3 | 0.0 | 0.000 | 0.00919 | 0.01413 |
| `guard_xy0p02_z0p08_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 93.113 | 25.2 | 0.0 | 0.000 | 0.00916 | 0.01411 |
| `guard_xy0p02_z0p1_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 92.092 | 24.5 | 0.0 | 0.000 | 0.00924 | 0.01419 |
| `guard_xy0p03_z0p04_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.702 | 24.4 | 0.0 | 0.000 | 0.00919 | 0.01413 |
| `guard_xy0p03_z0p06_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.749 | 24.4 | 0.0 | 0.000 | 0.00926 | 0.01411 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.807 | 24.5 | 0.0 | 0.000 | 0.00916 | 0.01413 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.978 | 24.4 | 0.0 | 0.000 | 0.00921 | 0.01415 |
| `guard_xy0p04_z0p04_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.915 | 24.5 | 0.0 | 0.000 | 0.00927 | 0.01414 |
| `guard_xy0p04_z0p06_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.854 | 24.4 | 0.0 | 0.000 | 0.00923 | 0.01413 |
| `guard_xy0p04_z0p08_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 92.208 | 24.5 | 0.0 | 0.000 | 0.00927 | 0.01418 |
| `guard_xy0p04_z0p1_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.491 | 24.3 | 0.0 | 0.000 | 0.00918 | 0.01412 |
| `guard_xy0p06_z0p04_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.618 | 24.3 | 0.0 | 0.000 | 0.00923 | 0.01411 |
| `guard_xy0p06_z0p06_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.878 | 24.4 | 0.0 | 0.000 | 0.00925 | 0.01414 |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.702 | 24.3 | 0.0 | 0.000 | 0.00926 | 0.01413 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 91.525 | 24.2 | 0.0 | 0.000 | 0.00924 | 0.01413 |
| `no_guard` | full_light_geometry | 0.667 | 0.300 | 0.033 | 13.787 | 26.5 | 0.0 | 0.000 | 0.01399 | 0.01829 |
| `guard_xy0p02_z0p04_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.600 | 0.333 | 0.067 | 9.549 | 41.8 | 33.8 | 0.767 | 0.01496 | 0.02817 |
| `guard_xy0p02_z0p06_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.567 | 0.300 | 0.133 | 27.281 | 52.4 | 46.3 | 0.867 | 0.01473 | 0.03195 |
| `guard_xy0p02_z0p08_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.600 | 0.300 | 0.100 | 23.596 | 47.0 | 41.7 | 0.867 | 0.01456 | 0.02920 |
| `guard_xy0p02_z0p1_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.600 | 0.300 | 0.100 | 23.808 | 47.1 | 41.8 | 0.867 | 0.01457 | 0.02928 |
| `guard_xy0p03_z0p04_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.600 | 0.333 | 0.067 | 9.745 | 41.8 | 33.9 | 0.767 | 0.01495 | 0.02817 |
| `guard_xy0p03_z0p06_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.600 | 0.267 | 0.133 | 37.481 | 48.3 | 42.6 | 0.867 | 0.01426 | 0.02957 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.700 | 0.233 | 0.067 | 46.568 | 37.0 | 33.1 | 0.867 | 0.01336 | 0.02273 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.700 | 0.233 | 0.067 | 46.568 | 37.0 | 33.1 | 0.867 | 0.01338 | 0.02275 |
| `guard_xy0p04_z0p04_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.600 | 0.333 | 0.067 | 9.957 | 41.8 | 33.9 | 0.767 | 0.01495 | 0.02814 |
| `guard_xy0p04_z0p06_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.633 | 0.233 | 0.133 | 51.896 | 49.3 | 43.8 | 0.900 | 0.01360 | 0.02826 |
| `guard_xy0p04_z0p08_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.700 | 0.200 | 0.100 | 64.019 | 42.3 | 39.6 | 0.933 | 0.01048 | 0.02480 |
| `guard_xy0p04_z0p1_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.700 | 0.200 | 0.100 | 63.914 | 42.3 | 39.6 | 0.933 | 0.01048 | 0.02482 |
| `guard_xy0p06_z0p04_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.600 | 0.333 | 0.067 | 9.680 | 41.8 | 33.9 | 0.767 | 0.01492 | 0.02817 |
| `guard_xy0p06_z0p06_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.633 | 0.233 | 0.133 | 51.712 | 49.2 | 43.8 | 0.967 | 0.01359 | 0.02827 |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.700 | 0.200 | 0.100 | 68.108 | 48.7 | 47.4 | 1.000 | 0.01046 | 0.02629 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.700 | 0.200 | 0.100 | 68.154 | 48.7 | 47.4 | 1.000 | 0.01049 | 0.02631 |
| `no_guard` | full_contact_light | 0.600 | 0.400 | 0.000 | -25.653 | 26.2 | 0.0 | 0.000 | 0.01528 | 0.02091 |
| `guard_xy0p02_z0p04_blend0p75_down0p0035_align0p025` | full_contact_light | 0.567 | 0.433 | 0.000 | -37.515 | 31.4 | 23.4 | 0.733 | 0.01618 | 0.02501 |
| `guard_xy0p02_z0p06_blend0p75_down0p0035_align0p025` | full_contact_light | 0.667 | 0.300 | 0.033 | 15.077 | 29.8 | 23.8 | 0.800 | 0.01432 | 0.02095 |
| `guard_xy0p02_z0p08_blend0p75_down0p0035_align0p025` | full_contact_light | 0.667 | 0.300 | 0.033 | 17.967 | 33.5 | 28.3 | 0.800 | 0.01435 | 0.02292 |
| `guard_xy0p02_z0p1_blend0p75_down0p0035_align0p025` | full_contact_light | 0.667 | 0.300 | 0.033 | 18.164 | 33.7 | 28.5 | 0.800 | 0.01433 | 0.02297 |
| `guard_xy0p03_z0p04_blend0p75_down0p0035_align0p025` | full_contact_light | 0.567 | 0.433 | 0.000 | -37.041 | 31.4 | 23.3 | 0.733 | 0.01617 | 0.02509 |
| `guard_xy0p03_z0p06_blend0p75_down0p0035_align0p025` | full_contact_light | 0.700 | 0.267 | 0.033 | 24.440 | 24.8 | 19.1 | 0.867 | 0.01390 | 0.01857 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | full_contact_light | 0.800 | 0.167 | 0.033 | 67.589 | 26.8 | 22.9 | 0.867 | 0.01190 | 0.01588 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | full_contact_light | 0.800 | 0.167 | 0.033 | 67.599 | 26.8 | 22.9 | 0.867 | 0.01189 | 0.01589 |
| `guard_xy0p04_z0p04_blend0p75_down0p0035_align0p025` | full_contact_light | 0.567 | 0.433 | 0.000 | -37.396 | 31.3 | 23.3 | 0.733 | 0.01622 | 0.02501 |
| `guard_xy0p04_z0p06_blend0p75_down0p0035_align0p025` | full_contact_light | 0.700 | 0.267 | 0.033 | 24.669 | 24.8 | 19.3 | 0.900 | 0.01388 | 0.01866 |
| `guard_xy0p04_z0p08_blend0p75_down0p0035_align0p025` | full_contact_light | 0.800 | 0.200 | 0.000 | 51.341 | 20.4 | 17.8 | 0.933 | 0.01007 | 0.01520 |
| `guard_xy0p04_z0p1_blend0p75_down0p0035_align0p025` | full_contact_light | 0.800 | 0.200 | 0.000 | 51.340 | 20.4 | 17.8 | 0.933 | 0.01007 | 0.01520 |
| `guard_xy0p06_z0p04_blend0p75_down0p0035_align0p025` | full_contact_light | 0.567 | 0.433 | 0.000 | -37.024 | 31.5 | 23.4 | 0.733 | 0.01622 | 0.02508 |
| `guard_xy0p06_z0p06_blend0p75_down0p0035_align0p025` | full_contact_light | 0.700 | 0.267 | 0.033 | 24.231 | 24.4 | 19.0 | 0.933 | 0.01384 | 0.01864 |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | full_contact_light | 0.800 | 0.200 | 0.000 | 54.213 | 25.1 | 23.7 | 0.967 | 0.01009 | 0.01652 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | full_contact_light | 0.800 | 0.200 | 0.000 | 54.187 | 25.0 | 23.7 | 0.967 | 0.01011 | 0.01652 |
| `no_guard` | hard_full_light_bucket | 0.233 | 0.767 | 0.000 | -185.321 | 16.8 | 0.0 | 0.000 | 0.02527 | 0.03383 |
| `guard_xy0p02_z0p04_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.300 | 0.700 | 0.000 | -162.260 | 16.2 | 8.9 | 0.467 | 0.02421 | 0.03325 |
| `guard_xy0p02_z0p06_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.367 | 0.633 | 0.000 | -133.185 | 15.7 | 9.5 | 0.533 | 0.02288 | 0.03296 |
| `guard_xy0p02_z0p08_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.400 | 0.600 | 0.000 | -118.477 | 17.1 | 11.6 | 0.533 | 0.02229 | 0.03162 |
| `guard_xy0p02_z0p1_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.400 | 0.600 | 0.000 | -118.495 | 17.2 | 11.7 | 0.533 | 0.02229 | 0.03161 |
| `guard_xy0p03_z0p04_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.300 | 0.700 | 0.000 | -162.329 | 16.2 | 8.9 | 0.467 | 0.02422 | 0.03326 |
| `guard_xy0p03_z0p06_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.367 | 0.633 | 0.000 | -133.120 | 15.7 | 9.9 | 0.633 | 0.02284 | 0.03294 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.400 | 0.600 | 0.000 | -118.292 | 16.7 | 12.2 | 0.633 | 0.02217 | 0.03092 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.400 | 0.600 | 0.000 | -118.289 | 16.7 | 12.2 | 0.633 | 0.02217 | 0.03091 |
| `guard_xy0p04_z0p04_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.300 | 0.700 | 0.000 | -162.326 | 16.2 | 8.9 | 0.467 | 0.02421 | 0.03325 |
| `guard_xy0p04_z0p06_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.367 | 0.633 | 0.000 | -124.120 | 25.2 | 19.7 | 0.800 | 0.02261 | 0.03586 |
| `guard_xy0p04_z0p08_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.367 | 0.633 | 0.000 | -122.818 | 27.2 | 23.9 | 0.800 | 0.02239 | 0.03446 |
| `guard_xy0p04_z0p1_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.367 | 0.633 | 0.000 | -122.817 | 27.2 | 23.9 | 0.800 | 0.02239 | 0.03446 |
| `guard_xy0p06_z0p04_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.300 | 0.700 | 0.000 | -162.330 | 16.2 | 8.9 | 0.467 | 0.02421 | 0.03326 |
| `guard_xy0p06_z0p06_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.367 | 0.633 | 0.000 | -128.444 | 20.8 | 15.8 | 0.967 | 0.02301 | 0.03488 |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.467 | 0.533 | 0.000 | -85.281 | 24.3 | 22.8 | 0.967 | 0.01996 | 0.03019 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.467 | 0.533 | 0.000 | -85.293 | 24.3 | 22.8 | 0.967 | 0.01995 | 0.03019 |
