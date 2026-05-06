# Guarded Policy Parameter Scan

- Generated: `2026-05-07T04:05:09`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Preset: `grid`
- Scenario preset: `core`
- Candidates: `5`
- Episodes per candidate/scenario: `100`
- Seed: `90000`
- Guard scenario filter: `geometry`

## Candidate Summary

| Candidate | clean | visual_camera | visual_camera_control | full_light_geometry | full_contact_light | hard_full_light_bucket | Mean success | Mean collision | Guard steps | Guard ep. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | 0.980 | 0.980 | 0.910 | 0.710 | 0.640 | 0.530 | 0.792 | 0.192 | 15.4 | 0.478 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | 0.980 | 0.980 | 0.910 | 0.710 | 0.640 | 0.530 | 0.792 | 0.192 | 15.4 | 0.478 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | 0.980 | 0.980 | 0.920 | 0.650 | 0.660 | 0.410 | 0.767 | 0.217 | 13.6 | 0.390 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | 0.980 | 0.980 | 0.900 | 0.650 | 0.660 | 0.420 | 0.765 | 0.217 | 13.6 | 0.390 |
| `no_guard` | 0.980 | 0.980 | 0.920 | 0.580 | 0.590 | 0.320 | 0.728 | 0.267 | 0.0 | 0.000 |

## Per-Scenario Rows

| Candidate | Scenario | Success | Collision | Timeout | Return | Steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `no_guard` | clean | 0.980 | 0.020 | 0.000 | 147.402 | 22.5 | 0.0 | 0.000 | 0.00482 | 0.00871 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | clean | 0.980 | 0.020 | 0.000 | 147.345 | 22.5 | 0.0 | 0.000 | 0.00479 | 0.00870 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | clean | 0.980 | 0.020 | 0.000 | 147.414 | 22.5 | 0.0 | 0.000 | 0.00479 | 0.00869 |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | clean | 0.980 | 0.020 | 0.000 | 147.302 | 22.4 | 0.0 | 0.000 | 0.00480 | 0.00869 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | clean | 0.980 | 0.020 | 0.000 | 147.318 | 22.4 | 0.0 | 0.000 | 0.00480 | 0.00869 |
| `no_guard` | visual_camera | 0.980 | 0.020 | 0.000 | 144.467 | 22.3 | 0.0 | 0.000 | 0.00500 | 0.00884 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | visual_camera | 0.980 | 0.020 | 0.000 | 144.732 | 22.4 | 0.0 | 0.000 | 0.00499 | 0.00884 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | visual_camera | 0.980 | 0.020 | 0.000 | 144.404 | 22.3 | 0.0 | 0.000 | 0.00500 | 0.00883 |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | visual_camera | 0.980 | 0.020 | 0.000 | 144.282 | 22.1 | 0.0 | 0.000 | 0.00499 | 0.00884 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | visual_camera | 0.980 | 0.020 | 0.000 | 144.331 | 22.2 | 0.0 | 0.000 | 0.00498 | 0.00880 |
| `no_guard` | visual_camera_control | 0.920 | 0.080 | 0.000 | 122.478 | 28.6 | 0.0 | 0.000 | 0.00714 | 0.01247 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.920 | 0.080 | 0.000 | 122.505 | 28.6 | 0.0 | 0.000 | 0.00716 | 0.01249 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.900 | 0.090 | 0.010 | 115.481 | 31.5 | 0.0 | 0.000 | 0.00776 | 0.01389 |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.910 | 0.090 | 0.000 | 119.331 | 30.1 | 0.0 | 0.000 | 0.00743 | 0.01315 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.910 | 0.090 | 0.000 | 119.062 | 30.0 | 0.0 | 0.000 | 0.00750 | 0.01315 |
| `no_guard` | full_light_geometry | 0.580 | 0.410 | 0.010 | -25.058 | 23.7 | 0.0 | 0.000 | 0.01447 | 0.02402 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.650 | 0.290 | 0.060 | 23.012 | 38.2 | 34.2 | 0.860 | 0.01301 | 0.02629 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.650 | 0.290 | 0.060 | 23.052 | 38.2 | 34.2 | 0.860 | 0.01301 | 0.02629 |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.710 | 0.230 | 0.060 | 50.306 | 39.4 | 38.3 | 0.980 | 0.01107 | 0.02389 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.710 | 0.230 | 0.060 | 50.343 | 39.4 | 38.3 | 0.980 | 0.01108 | 0.02391 |
| `no_guard` | full_contact_light | 0.590 | 0.390 | 0.020 | -13.971 | 27.9 | 0.0 | 0.000 | 0.01472 | 0.02419 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | full_contact_light | 0.660 | 0.320 | 0.020 | 14.822 | 35.1 | 31.2 | 0.830 | 0.01359 | 0.02554 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | full_contact_light | 0.660 | 0.320 | 0.020 | 14.787 | 35.1 | 31.2 | 0.830 | 0.01358 | 0.02553 |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | full_contact_light | 0.640 | 0.330 | 0.030 | 11.111 | 36.1 | 35.0 | 0.970 | 0.01332 | 0.02669 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | full_contact_light | 0.640 | 0.330 | 0.030 | 11.133 | 36.1 | 35.0 | 0.970 | 0.01330 | 0.02671 |
| `no_guard` | hard_full_light_bucket | 0.320 | 0.680 | 0.000 | -149.913 | 17.2 | 0.0 | 0.000 | 0.02443 | 0.03097 |
| `guard_xy0p03_z0p08_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.410 | 0.570 | 0.020 | -105.465 | 20.4 | 16.1 | 0.650 | 0.02277 | 0.03110 |
| `guard_xy0p03_z0p1_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.420 | 0.560 | 0.020 | -101.110 | 20.5 | 16.2 | 0.650 | 0.02256 | 0.03111 |
| `guard_xy0p06_z0p08_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.530 | 0.460 | 0.010 | -57.708 | 20.3 | 18.9 | 0.920 | 0.01957 | 0.02768 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.530 | 0.460 | 0.010 | -57.704 | 20.3 | 18.9 | 0.920 | 0.01957 | 0.02767 |
