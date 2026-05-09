# Guarded Policy Parameter Scan

- Generated: `2026-05-08T15:22:56`
- Model: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Preset: `smoke`
- Scenario preset: `targeted`
- Candidates: `5`
- Episodes per candidate/scenario: `5`
- Seed: `92000`
- Guard scenario filter: `all`

## Candidate Summary

| Candidate | visual_camera_control | full_light_geometry | full_contact_light | hard_full_light_bucket | Mean success | Mean collision | Guard steps | Guard ep. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `guard_xy060_z100_blend075_down0035_align025` | 0.800 | 0.800 | 1.000 | 0.400 | 0.750 | 0.200 | 99.7 | 1.000 |
| `guard_xy060_z080_blend100_down0035_align025` | 0.800 | 0.600 | 1.000 | 0.400 | 0.700 | 0.200 | 103.2 | 1.000 |
| `guard_xy060_z100_blend100_down0035_align025` | 0.800 | 0.400 | 1.000 | 0.400 | 0.650 | 0.200 | 105.5 | 1.000 |
| `guard_xy050_z100_blend100_down0035_align025` | 0.800 | 0.400 | 1.000 | 0.400 | 0.650 | 0.200 | 97.5 | 1.000 |
| `no_guard` | 0.400 | 0.400 | 0.600 | 0.400 | 0.450 | 0.350 | 0.0 | 0.000 |

## Per-Scenario Rows

| Candidate | Scenario | Success | Collision | Timeout | Return | Steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `no_guard` | visual_camera_control | 0.400 | 0.400 | 0.200 | 97.282 | 111.0 | 0.0 | 0.000 | 0.01338 | 0.02512 |
| `guard_xy060_z100_blend100_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 228.143 | 124.8 | 99.2 | 1.000 | 0.00967 | 0.01695 |
| `guard_xy050_z100_blend100_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 228.185 | 127.0 | 90.4 | 1.000 | 0.00956 | 0.01691 |
| `guard_xy060_z080_blend100_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 228.142 | 124.8 | 99.2 | 1.000 | 0.00967 | 0.01695 |
| `guard_xy060_z100_blend075_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 233.762 | 119.6 | 94.0 | 1.000 | 0.00962 | 0.01758 |
| `no_guard` | full_light_geometry | 0.400 | 0.400 | 0.200 | 106.973 | 112.4 | 0.0 | 0.000 | 0.01236 | 0.02522 |
| `guard_xy060_z100_blend100_down0035_align025` | full_light_geometry | 0.400 | 0.200 | 0.400 | 177.759 | 142.2 | 117.0 | 1.000 | 0.00932 | 0.01854 |
| `guard_xy050_z100_blend100_down0035_align025` | full_light_geometry | 0.400 | 0.200 | 0.400 | 179.155 | 146.2 | 110.0 | 1.000 | 0.00926 | 0.01876 |
| `guard_xy060_z080_blend100_down0035_align025` | full_light_geometry | 0.600 | 0.200 | 0.200 | 212.690 | 132.8 | 107.6 | 1.000 | 0.00889 | 0.01891 |
| `guard_xy060_z100_blend075_down0035_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 246.246 | 130.8 | 105.6 | 1.000 | 0.00907 | 0.01730 |
| `no_guard` | full_contact_light | 0.600 | 0.200 | 0.200 | 202.469 | 123.8 | 0.0 | 0.000 | 0.00830 | 0.01696 |
| `guard_xy060_z100_blend100_down0035_align025` | full_contact_light | 1.000 | 0.000 | 0.000 | 329.011 | 139.0 | 114.4 | 1.000 | 0.00456 | 0.00904 |
| `guard_xy050_z100_blend100_down0035_align025` | full_contact_light | 1.000 | 0.000 | 0.000 | 329.677 | 139.8 | 104.6 | 1.000 | 0.00467 | 0.00893 |
| `guard_xy060_z080_blend100_down0035_align025` | full_contact_light | 1.000 | 0.000 | 0.000 | 329.038 | 139.0 | 114.4 | 1.000 | 0.00457 | 0.00905 |
| `guard_xy060_z100_blend075_down0035_align025` | full_contact_light | 1.000 | 0.000 | 0.000 | 332.817 | 132.8 | 108.2 | 1.000 | 0.00453 | 0.00922 |
| `no_guard` | hard_full_light_bucket | 0.400 | 0.400 | 0.200 | 94.287 | 111.2 | 0.0 | 0.000 | 0.01514 | 0.02528 |
| `guard_xy060_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.400 | 0.400 | 0.200 | 104.615 | 118.2 | 91.4 | 1.000 | 0.01380 | 0.03025 |
| `guard_xy050_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.400 | 0.400 | 0.200 | 105.762 | 123.0 | 84.8 | 1.000 | 0.01385 | 0.03000 |
| `guard_xy060_z080_blend100_down0035_align025` | hard_full_light_bucket | 0.400 | 0.400 | 0.200 | 104.613 | 118.2 | 91.4 | 1.000 | 0.01381 | 0.03025 |
| `guard_xy060_z100_blend075_down0035_align025` | hard_full_light_bucket | 0.400 | 0.400 | 0.200 | 114.156 | 117.6 | 90.8 | 1.000 | 0.01430 | 0.02767 |
