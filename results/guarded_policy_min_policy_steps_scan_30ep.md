# Guarded Policy Parameter Scan

- Generated: `2026-05-07T04:09:27`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Preset: `grid`
- Scenario preset: `targeted`
- Candidates: `9`
- Episodes per candidate/scenario: `30`
- Seed: `971000`
- Guard scenario filter: `geometry`

## Candidate Summary

| Candidate | visual_camera_control | full_light_geometry | full_contact_light | hard_full_light_bucket | Mean success | Mean collision | Guard steps | Guard ep. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `guard_xy0p03_z0p08_blend0p75_min15_down0p0035_align0p025` | 0.900 | 0.700 | 0.667 | 0.200 | 0.617 | 0.383 | 7.7 | 0.317 |
| `guard_xy0p06_z0p08_blend0p75_min15_down0p0035_align0p025` | 0.900 | 0.700 | 0.667 | 0.200 | 0.617 | 0.383 | 7.7 | 0.308 |
| `no_guard` | 0.900 | 0.700 | 0.600 | 0.200 | 0.600 | 0.400 | 0.0 | 0.000 |
| `guard_xy0p03_z0p08_blend0p75_min10_down0p0035_align0p025` | 0.900 | 0.633 | 0.633 | 0.200 | 0.592 | 0.400 | 12.6 | 0.442 |
| `guard_xy0p06_z0p08_blend0p75_min10_down0p0035_align0p025` | 0.900 | 0.633 | 0.633 | 0.200 | 0.592 | 0.400 | 12.6 | 0.458 |
| `guard_xy0p03_z0p08_blend0p75_min0_down0p0035_align0p025` | 0.900 | 0.600 | 0.600 | 0.233 | 0.583 | 0.400 | 23.0 | 0.525 |
| `guard_xy0p03_z0p08_blend0p75_min5_down0p0035_align0p025` | 0.900 | 0.633 | 0.600 | 0.200 | 0.583 | 0.408 | 20.9 | 0.517 |
| `guard_xy0p06_z0p08_blend0p75_min0_down0p0035_align0p025` | 0.900 | 0.600 | 0.567 | 0.233 | 0.575 | 0.408 | 23.9 | 0.717 |
| `guard_xy0p06_z0p08_blend0p75_min5_down0p0035_align0p025` | 0.900 | 0.567 | 0.600 | 0.200 | 0.567 | 0.425 | 21.1 | 0.708 |

## Per-Scenario Rows

| Candidate | Scenario | Success | Collision | Timeout | Return | Steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `no_guard` | visual_camera_control | 0.900 | 0.100 | 0.000 | 113.870 | 29.1 | 0.0 | 0.000 | 0.00799 | 0.01141 |
| `guard_xy0p03_z0p08_blend0p75_min0_down0p0035_align0p025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 114.382 | 29.4 | 0.0 | 0.000 | 0.00797 | 0.01142 |
| `guard_xy0p03_z0p08_blend0p75_min5_down0p0035_align0p025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 113.938 | 29.2 | 0.0 | 0.000 | 0.00806 | 0.01140 |
| `guard_xy0p03_z0p08_blend0p75_min10_down0p0035_align0p025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 114.168 | 29.2 | 0.0 | 0.000 | 0.00798 | 0.01141 |
| `guard_xy0p03_z0p08_blend0p75_min15_down0p0035_align0p025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 113.737 | 29.0 | 0.0 | 0.000 | 0.00800 | 0.01138 |
| `guard_xy0p06_z0p08_blend0p75_min0_down0p0035_align0p025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 115.952 | 30.4 | 0.0 | 0.000 | 0.00795 | 0.01142 |
| `guard_xy0p06_z0p08_blend0p75_min5_down0p0035_align0p025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 114.045 | 29.2 | 0.0 | 0.000 | 0.00799 | 0.01142 |
| `guard_xy0p06_z0p08_blend0p75_min10_down0p0035_align0p025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 114.466 | 29.3 | 0.0 | 0.000 | 0.00795 | 0.01140 |
| `guard_xy0p06_z0p08_blend0p75_min15_down0p0035_align0p025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 114.016 | 29.1 | 0.0 | 0.000 | 0.00795 | 0.01140 |
| `no_guard` | full_light_geometry | 0.700 | 0.300 | 0.000 | 22.231 | 30.9 | 0.0 | 0.000 | 0.01117 | 0.02066 |
| `guard_xy0p03_z0p08_blend0p75_min0_down0p0035_align0p025` | full_light_geometry | 0.600 | 0.367 | 0.033 | 5.284 | 43.8 | 39.0 | 0.900 | 0.01269 | 0.03014 |
| `guard_xy0p03_z0p08_blend0p75_min5_down0p0035_align0p025` | full_light_geometry | 0.633 | 0.367 | 0.000 | 2.798 | 38.0 | 32.2 | 0.900 | 0.01237 | 0.02744 |
| `guard_xy0p03_z0p08_blend0p75_min10_down0p0035_align0p025` | full_light_geometry | 0.633 | 0.367 | 0.000 | 1.697 | 33.9 | 24.4 | 0.767 | 0.01260 | 0.02598 |
| `guard_xy0p03_z0p08_blend0p75_min15_down0p0035_align0p025` | full_light_geometry | 0.700 | 0.300 | 0.000 | 25.407 | 27.7 | 14.9 | 0.533 | 0.01148 | 0.02134 |
| `guard_xy0p06_z0p08_blend0p75_min0_down0p0035_align0p025` | full_light_geometry | 0.600 | 0.367 | 0.033 | 3.688 | 41.5 | 39.3 | 1.000 | 0.01304 | 0.02929 |
| `guard_xy0p06_z0p08_blend0p75_min5_down0p0035_align0p025` | full_light_geometry | 0.567 | 0.433 | 0.000 | -25.433 | 36.7 | 31.6 | 1.000 | 0.01386 | 0.03010 |
| `guard_xy0p06_z0p08_blend0p75_min10_down0p0035_align0p025` | full_light_geometry | 0.633 | 0.367 | 0.000 | 0.549 | 33.7 | 24.2 | 0.767 | 0.01263 | 0.02601 |
| `guard_xy0p06_z0p08_blend0p75_min15_down0p0035_align0p025` | full_light_geometry | 0.700 | 0.300 | 0.000 | 25.231 | 27.7 | 14.9 | 0.533 | 0.01144 | 0.02130 |
| `no_guard` | full_contact_light | 0.600 | 0.400 | 0.000 | -14.050 | 39.3 | 0.0 | 0.000 | 0.01336 | 0.02659 |
| `guard_xy0p03_z0p08_blend0p75_min0_down0p0035_align0p025` | full_contact_light | 0.600 | 0.367 | 0.033 | 14.041 | 49.8 | 45.1 | 0.867 | 0.01354 | 0.03110 |
| `guard_xy0p03_z0p08_blend0p75_min5_down0p0035_align0p025` | full_contact_light | 0.600 | 0.367 | 0.033 | 13.547 | 50.0 | 44.3 | 0.867 | 0.01352 | 0.03151 |
| `guard_xy0p03_z0p08_blend0p75_min10_down0p0035_align0p025` | full_contact_light | 0.633 | 0.333 | 0.033 | 10.774 | 32.7 | 23.2 | 0.767 | 0.01307 | 0.02588 |
| `guard_xy0p03_z0p08_blend0p75_min15_down0p0035_align0p025` | full_contact_light | 0.667 | 0.333 | 0.000 | 10.912 | 27.2 | 14.3 | 0.567 | 0.01205 | 0.02346 |
| `guard_xy0p06_z0p08_blend0p75_min0_down0p0035_align0p025` | full_contact_light | 0.567 | 0.400 | 0.033 | -6.122 | 43.9 | 41.6 | 1.000 | 0.01393 | 0.03188 |
| `guard_xy0p06_z0p08_blend0p75_min5_down0p0035_align0p025` | full_contact_light | 0.600 | 0.367 | 0.033 | 13.324 | 49.6 | 44.5 | 1.000 | 0.01336 | 0.03140 |
| `guard_xy0p06_z0p08_blend0p75_min10_down0p0035_align0p025` | full_contact_light | 0.633 | 0.333 | 0.033 | 10.817 | 32.7 | 23.3 | 0.800 | 0.01309 | 0.02591 |
| `guard_xy0p06_z0p08_blend0p75_min15_down0p0035_align0p025` | full_contact_light | 0.667 | 0.333 | 0.000 | 10.865 | 27.2 | 14.3 | 0.533 | 0.01208 | 0.02347 |
| `no_guard` | hard_full_light_bucket | 0.200 | 0.800 | 0.000 | -205.340 | 10.2 | 0.0 | 0.000 | 0.02993 | 0.03803 |
| `guard_xy0p03_z0p08_blend0p75_min0_down0p0035_align0p025` | hard_full_light_bucket | 0.233 | 0.767 | 0.000 | -188.085 | 13.5 | 8.1 | 0.333 | 0.02948 | 0.04001 |
| `guard_xy0p03_z0p08_blend0p75_min5_down0p0035_align0p025` | hard_full_light_bucket | 0.200 | 0.800 | 0.000 | -203.596 | 13.6 | 7.2 | 0.300 | 0.03010 | 0.03993 |
| `guard_xy0p03_z0p08_blend0p75_min10_down0p0035_align0p025` | hard_full_light_bucket | 0.200 | 0.800 | 0.000 | -205.901 | 10.4 | 2.8 | 0.233 | 0.03009 | 0.03799 |
| `guard_xy0p03_z0p08_blend0p75_min15_down0p0035_align0p025` | hard_full_light_bucket | 0.200 | 0.800 | 0.000 | -205.744 | 10.1 | 1.5 | 0.167 | 0.02996 | 0.03796 |
| `guard_xy0p06_z0p08_blend0p75_min0_down0p0035_align0p025` | hard_full_light_bucket | 0.233 | 0.767 | 0.000 | -184.354 | 17.7 | 14.9 | 0.867 | 0.02921 | 0.04104 |
| `guard_xy0p06_z0p08_blend0p75_min5_down0p0035_align0p025` | hard_full_light_bucket | 0.200 | 0.800 | 0.000 | -203.344 | 13.7 | 8.5 | 0.833 | 0.02980 | 0.04003 |
| `guard_xy0p06_z0p08_blend0p75_min10_down0p0035_align0p025` | hard_full_light_bucket | 0.200 | 0.800 | 0.000 | -205.779 | 10.4 | 3.0 | 0.267 | 0.03002 | 0.03799 |
| `guard_xy0p06_z0p08_blend0p75_min15_down0p0035_align0p025` | hard_full_light_bucket | 0.200 | 0.800 | 0.000 | -205.741 | 10.1 | 1.5 | 0.167 | 0.02997 | 0.03796 |
