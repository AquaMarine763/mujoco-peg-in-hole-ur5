# Guarded Policy Parameter Scan

- Generated: `2026-05-09T01:32:58`
- Model: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Preset: `grid`
- Scenario preset: `targeted`
- Candidates: `13`
- Episodes per candidate/scenario: `5`
- Seed: `572000`
- Guard scenario filter: `all`
- Initialization mode: `target_relative_high_start`
- Initial tip Z above target range: `[0.15, 0.25]`
- Initial tip XY offset range: `[0.08, 0.16]`
- Guarded oracle mode values: `['guarded_two_stage', 'high_start_two_phase']`
- Scan block-down values: `True`

## Candidate Summary

| Candidate | visual_camera_control | full_light_geometry | full_contact_light | hard_full_light_bucket | Mean success | Mean collision | Guard steps | Guard ep. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_guardedtwostage_block0` | 0.400 | 0.000 | 0.400 | 0.400 | 0.300 | 0.150 | 522.5 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_guardedtwostage_block1` | 0.400 | 0.000 | 0.400 | 0.400 | 0.300 | 0.150 | 522.5 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_highstarttwophase_block0` | 0.400 | 0.000 | 0.400 | 0.400 | 0.300 | 0.150 | 522.5 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_highstarttwophase_block1` | 0.400 | 0.000 | 0.400 | 0.400 | 0.300 | 0.150 | 522.4 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_guardedtwostage_block0` | 0.400 | 0.000 | 0.400 | 0.400 | 0.300 | 0.150 | 520.4 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_guardedtwostage_block1` | 0.400 | 0.000 | 0.400 | 0.400 | 0.300 | 0.150 | 520.4 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_highstarttwophase_block0` | 0.400 | 0.000 | 0.400 | 0.400 | 0.300 | 0.150 | 520.3 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_highstarttwophase_block1` | 0.400 | 0.000 | 0.400 | 0.400 | 0.300 | 0.150 | 520.2 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_guardedtwostage_block0` | 0.600 | 0.000 | 0.400 | 0.200 | 0.300 | 0.150 | 523.8 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_guardedtwostage_block1` | 0.600 | 0.000 | 0.400 | 0.200 | 0.300 | 0.150 | 523.8 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_highstarttwophase_block0` | 0.600 | 0.000 | 0.400 | 0.200 | 0.300 | 0.150 | 523.8 | 0.950 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_highstarttwophase_block1` | 0.600 | 0.000 | 0.400 | 0.200 | 0.300 | 0.150 | 523.8 | 0.950 |
| `no_guard` | 0.400 | 0.000 | 0.000 | 0.400 | 0.200 | 0.350 | 0.0 | 0.000 |

## Per-Scenario Rows

| Candidate | Scenario | Success | Collision | Timeout | Return | Steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `no_guard` | visual_camera_control | 0.400 | 0.000 | 0.600 | -33.706 | 694.0 | 0.0 | 0.000 | 0.00883 | 0.02147 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_guardedtwostage_block0` | visual_camera_control | 0.600 | 0.000 | 0.400 | 260.255 | 540.8 | 407.6 | 1.000 | 0.00488 | 0.02058 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_guardedtwostage_block1` | visual_camera_control | 0.600 | 0.000 | 0.400 | 259.618 | 540.8 | 407.6 | 1.000 | 0.00487 | 0.02056 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_highstarttwophase_block0` | visual_camera_control | 0.600 | 0.000 | 0.400 | 259.587 | 540.8 | 407.6 | 1.000 | 0.00488 | 0.02056 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_highstarttwophase_block1` | visual_camera_control | 0.600 | 0.000 | 0.400 | 259.583 | 540.8 | 407.6 | 1.000 | 0.00487 | 0.02055 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_guardedtwostage_block0` | visual_camera_control | 0.400 | 0.000 | 0.600 | 48.339 | 686.4 | 553.2 | 1.000 | 0.00443 | 0.02672 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_guardedtwostage_block1` | visual_camera_control | 0.400 | 0.000 | 0.600 | 48.218 | 686.4 | 553.2 | 1.000 | 0.00441 | 0.02671 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_highstarttwophase_block0` | visual_camera_control | 0.400 | 0.000 | 0.600 | 48.235 | 686.4 | 553.2 | 1.000 | 0.00439 | 0.02671 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_highstarttwophase_block1` | visual_camera_control | 0.400 | 0.000 | 0.600 | 48.288 | 686.4 | 553.2 | 1.000 | 0.00438 | 0.02673 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_guardedtwostage_block0` | visual_camera_control | 0.400 | 0.000 | 0.600 | 16.963 | 683.2 | 550.0 | 1.000 | 0.00405 | 0.02721 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_guardedtwostage_block1` | visual_camera_control | 0.400 | 0.000 | 0.600 | 17.219 | 683.0 | 549.8 | 1.000 | 0.00406 | 0.02721 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_highstarttwophase_block0` | visual_camera_control | 0.400 | 0.000 | 0.600 | 17.257 | 683.0 | 549.8 | 1.000 | 0.00405 | 0.02728 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_highstarttwophase_block1` | visual_camera_control | 0.400 | 0.000 | 0.600 | 17.309 | 683.0 | 549.8 | 1.000 | 0.00406 | 0.02725 |
| `no_guard` | full_light_geometry | 0.000 | 0.600 | 0.400 | 241.919 | 722.4 | 0.0 | 0.000 | 0.02834 | 0.04390 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_guardedtwostage_block0` | full_light_geometry | 0.000 | 0.200 | 0.800 | 289.910 | 855.6 | 634.0 | 0.800 | 0.01930 | 0.04315 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_guardedtwostage_block1` | full_light_geometry | 0.000 | 0.200 | 0.800 | 289.617 | 855.6 | 634.2 | 0.800 | 0.01929 | 0.04311 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_highstarttwophase_block0` | full_light_geometry | 0.000 | 0.200 | 0.800 | 289.227 | 855.6 | 634.0 | 0.800 | 0.01938 | 0.04311 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_highstarttwophase_block1` | full_light_geometry | 0.000 | 0.200 | 0.800 | 288.163 | 855.6 | 634.2 | 0.800 | 0.01921 | 0.04316 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_guardedtwostage_block0` | full_light_geometry | 0.000 | 0.200 | 0.800 | 270.844 | 855.6 | 634.0 | 0.800 | 0.01917 | 0.04411 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_guardedtwostage_block1` | full_light_geometry | 0.000 | 0.200 | 0.800 | 270.643 | 855.6 | 634.2 | 0.800 | 0.01919 | 0.04411 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_highstarttwophase_block0` | full_light_geometry | 0.000 | 0.200 | 0.800 | 268.940 | 855.6 | 634.2 | 0.800 | 0.01904 | 0.04410 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_highstarttwophase_block1` | full_light_geometry | 0.000 | 0.200 | 0.800 | 269.523 | 855.6 | 634.0 | 0.800 | 0.01918 | 0.04408 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_guardedtwostage_block0` | full_light_geometry | 0.000 | 0.200 | 0.800 | 292.106 | 855.6 | 634.2 | 0.800 | 0.01839 | 0.04571 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_guardedtwostage_block1` | full_light_geometry | 0.000 | 0.200 | 0.800 | 291.469 | 855.6 | 634.2 | 0.800 | 0.01840 | 0.04568 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_highstarttwophase_block0` | full_light_geometry | 0.000 | 0.200 | 0.800 | 289.716 | 855.6 | 634.2 | 0.800 | 0.01823 | 0.04564 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_highstarttwophase_block1` | full_light_geometry | 0.000 | 0.200 | 0.800 | 291.397 | 855.6 | 634.2 | 0.800 | 0.01837 | 0.04568 |
| `no_guard` | full_contact_light | 0.000 | 0.400 | 0.600 | -424.353 | 733.4 | 0.0 | 0.000 | 0.01669 | 0.03270 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_guardedtwostage_block0` | full_contact_light | 0.400 | 0.200 | 0.400 | 82.448 | 598.2 | 482.0 | 1.000 | 0.01075 | 0.02392 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_guardedtwostage_block1` | full_contact_light | 0.400 | 0.200 | 0.400 | 82.822 | 598.2 | 482.0 | 1.000 | 0.01075 | 0.02398 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_highstarttwophase_block0` | full_contact_light | 0.400 | 0.200 | 0.400 | 82.982 | 598.2 | 482.0 | 1.000 | 0.01075 | 0.02394 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_highstarttwophase_block1` | full_contact_light | 0.400 | 0.200 | 0.400 | 82.583 | 598.2 | 482.0 | 1.000 | 0.01075 | 0.02394 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_guardedtwostage_block0` | full_contact_light | 0.400 | 0.200 | 0.400 | 55.186 | 595.0 | 478.8 | 1.000 | 0.01073 | 0.02471 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_guardedtwostage_block1` | full_contact_light | 0.400 | 0.200 | 0.400 | 37.616 | 594.6 | 478.4 | 1.000 | 0.01073 | 0.02394 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_highstarttwophase_block0` | full_contact_light | 0.400 | 0.200 | 0.400 | 37.375 | 594.6 | 478.4 | 1.000 | 0.01073 | 0.02392 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_highstarttwophase_block1` | full_contact_light | 0.400 | 0.200 | 0.400 | 45.515 | 594.6 | 478.4 | 1.000 | 0.01073 | 0.02435 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_guardedtwostage_block0` | full_contact_light | 0.400 | 0.200 | 0.400 | 21.498 | 591.8 | 475.6 | 1.000 | 0.01039 | 0.02523 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_guardedtwostage_block1` | full_contact_light | 0.400 | 0.200 | 0.400 | 32.588 | 592.2 | 476.0 | 1.000 | 0.01042 | 0.02568 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_highstarttwophase_block0` | full_contact_light | 0.400 | 0.200 | 0.400 | 20.894 | 591.8 | 475.6 | 1.000 | 0.01040 | 0.02521 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_highstarttwophase_block1` | full_contact_light | 0.400 | 0.200 | 0.400 | 33.480 | 591.6 | 475.4 | 1.000 | 0.01041 | 0.02568 |
| `no_guard` | hard_full_light_bucket | 0.400 | 0.400 | 0.200 | -209.097 | 543.2 | 0.0 | 0.000 | 0.01607 | 0.02631 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_guardedtwostage_block0` | hard_full_light_bucket | 0.200 | 0.200 | 0.600 | -16.905 | 688.2 | 571.4 | 1.000 | 0.01278 | 0.03327 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_guardedtwostage_block1` | hard_full_light_bucket | 0.200 | 0.200 | 0.600 | -16.912 | 688.2 | 571.4 | 1.000 | 0.01277 | 0.03327 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_highstarttwophase_block0` | hard_full_light_bucket | 0.200 | 0.200 | 0.600 | -16.900 | 688.2 | 571.4 | 1.000 | 0.01278 | 0.03327 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p02_highstarttwophase_block1` | hard_full_light_bucket | 0.200 | 0.200 | 0.600 | -16.917 | 688.2 | 571.4 | 1.000 | 0.01278 | 0.03327 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_guardedtwostage_block0` | hard_full_light_bucket | 0.400 | 0.200 | 0.400 | 166.718 | 540.8 | 424.0 | 1.000 | 0.01230 | 0.02952 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_guardedtwostage_block1` | hard_full_light_bucket | 0.400 | 0.200 | 0.400 | 166.721 | 540.8 | 424.0 | 1.000 | 0.01230 | 0.02952 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_highstarttwophase_block0` | hard_full_light_bucket | 0.400 | 0.200 | 0.400 | 166.724 | 540.8 | 424.0 | 1.000 | 0.01230 | 0.02953 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p025_highstarttwophase_block1` | hard_full_light_bucket | 0.400 | 0.200 | 0.400 | 166.728 | 540.8 | 424.0 | 1.000 | 0.01230 | 0.02952 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_guardedtwostage_block0` | hard_full_light_bucket | 0.400 | 0.200 | 0.400 | 147.824 | 538.4 | 421.6 | 1.000 | 0.01232 | 0.02965 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_guardedtwostage_block1` | hard_full_light_bucket | 0.400 | 0.200 | 0.400 | 147.833 | 538.4 | 421.6 | 1.000 | 0.01232 | 0.02964 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_highstarttwophase_block0` | hard_full_light_bucket | 0.400 | 0.200 | 0.400 | 147.823 | 538.4 | 421.6 | 1.000 | 0.01232 | 0.02965 |
| `guard_xy0p06_z0p12_blend1_min0_down0p0035_align0p03_highstarttwophase_block1` | hard_full_light_bucket | 0.400 | 0.200 | 0.400 | 147.830 | 538.4 | 421.6 | 1.000 | 0.01232 | 0.02964 |
