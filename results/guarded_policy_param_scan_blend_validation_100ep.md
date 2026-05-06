# Guarded Policy Parameter Scan

- Generated: `2026-05-06T20:31:19`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Preset: `grid`
- Scenario preset: `core`
- Candidates: `3`
- Episodes per candidate/scenario: `100`
- Seed: `90000`
- Guard scenario filter: `geometry`

## Candidate Summary

| Candidate | clean | visual_camera | visual_camera_control | full_light_geometry | full_contact_light | hard_full_light_bucket | Mean success | Mean collision | Guard steps | Guard ep. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | 0.980 | 0.980 | 0.900 | 0.710 | 0.650 | 0.530 | 0.792 | 0.192 | 15.4 | 0.478 |
| `guard_xy0p06_z0p1_blend1_down0p0035_align0p025` | 0.980 | 0.980 | 0.910 | 0.690 | 0.660 | 0.480 | 0.783 | 0.197 | 15.7 | 0.478 |
| `no_guard` | 0.980 | 0.980 | 0.910 | 0.580 | 0.600 | 0.320 | 0.728 | 0.267 | 0.0 | 0.000 |

## Per-Scenario Rows

| Candidate | Scenario | Success | Collision | Timeout | Return | Steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `no_guard` | clean | 0.980 | 0.020 | 0.000 | 147.265 | 22.4 | 0.0 | 0.000 | 0.00479 | 0.00869 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | clean | 0.980 | 0.020 | 0.000 | 147.534 | 22.6 | 0.0 | 0.000 | 0.00480 | 0.00869 |
| `guard_xy0p06_z0p1_blend1_down0p0035_align0p025` | clean | 0.980 | 0.020 | 0.000 | 147.548 | 22.6 | 0.0 | 0.000 | 0.00479 | 0.00868 |
| `no_guard` | visual_camera | 0.980 | 0.020 | 0.000 | 144.317 | 22.2 | 0.0 | 0.000 | 0.00499 | 0.00883 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | visual_camera | 0.980 | 0.020 | 0.000 | 144.655 | 22.3 | 0.0 | 0.000 | 0.00500 | 0.00885 |
| `guard_xy0p06_z0p1_blend1_down0p0035_align0p025` | visual_camera | 0.980 | 0.020 | 0.000 | 143.969 | 22.1 | 0.0 | 0.000 | 0.00500 | 0.00880 |
| `no_guard` | visual_camera_control | 0.910 | 0.090 | 0.000 | 119.572 | 30.3 | 0.0 | 0.000 | 0.00746 | 0.01317 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 115.716 | 30.6 | 0.0 | 0.000 | 0.00780 | 0.01386 |
| `guard_xy0p06_z0p1_blend1_down0p0035_align0p025` | visual_camera_control | 0.910 | 0.090 | 0.000 | 119.247 | 30.1 | 0.0 | 0.000 | 0.00743 | 0.01315 |
| `no_guard` | full_light_geometry | 0.580 | 0.410 | 0.010 | -26.061 | 23.5 | 0.0 | 0.000 | 0.01439 | 0.02390 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | full_light_geometry | 0.710 | 0.230 | 0.060 | 50.317 | 39.4 | 38.3 | 0.980 | 0.01108 | 0.02390 |
| `guard_xy0p06_z0p1_blend1_down0p0035_align0p025` | full_light_geometry | 0.690 | 0.240 | 0.070 | 40.293 | 39.6 | 38.5 | 0.980 | 0.01096 | 0.02458 |
| `no_guard` | full_contact_light | 0.600 | 0.380 | 0.030 | -11.409 | 26.3 | 0.0 | 0.000 | 0.01448 | 0.02368 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | full_contact_light | 0.650 | 0.320 | 0.030 | 15.433 | 36.3 | 35.2 | 0.970 | 0.01314 | 0.02630 |
| `guard_xy0p06_z0p1_blend1_down0p0035_align0p025` | full_contact_light | 0.660 | 0.290 | 0.050 | 21.523 | 36.8 | 35.6 | 0.970 | 0.01238 | 0.02525 |
| `no_guard` | hard_full_light_bucket | 0.320 | 0.680 | 0.000 | -149.800 | 17.3 | 0.0 | 0.000 | 0.02448 | 0.03099 |
| `guard_xy0p06_z0p1_blend0p75_down0p0035_align0p025` | hard_full_light_bucket | 0.530 | 0.460 | 0.010 | -57.718 | 20.3 | 18.9 | 0.920 | 0.01957 | 0.02767 |
| `guard_xy0p06_z0p1_blend1_down0p0035_align0p025` | hard_full_light_bucket | 0.480 | 0.520 | 0.000 | -83.271 | 21.6 | 20.3 | 0.920 | 0.02055 | 0.02981 |
