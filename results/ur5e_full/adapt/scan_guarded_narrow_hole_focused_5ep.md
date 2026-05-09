# Guarded Policy Parameter Scan

- Generated: `2026-05-08T15:25:14`
- Model: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Preset: `focused`
- Scenario preset: `targeted`
- Candidates: `13`
- Episodes per candidate/scenario: `5`
- Seed: `93000`
- Guard scenario filter: `all`

## Candidate Summary

| Candidate | visual_camera_control | full_light_geometry | full_contact_light | hard_full_light_bucket | Mean success | Mean collision | Guard steps | Guard ep. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `guard_xy060_z100_blend100_down0035_align020` | 0.800 | 1.000 | 1.000 | 0.800 | 0.900 | 0.100 | 88.2 | 1.000 |
| `guard_xy060_z100_blend100_down0035_align015` | 0.800 | 1.000 | 1.000 | 0.800 | 0.900 | 0.100 | 89.8 | 1.000 |
| `guard_xy060_z100_blend100_down0035_align025` | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.200 | 81.5 | 1.000 |
| `guard_xy040_z100_blend100_down0035_align025` | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.200 | 72.2 | 1.000 |
| `guard_xy050_z100_blend100_down0035_align025` | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.200 | 76.4 | 1.000 |
| `guard_xy070_z100_blend100_down0035_align025` | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.200 | 87.0 | 1.000 |
| `guard_xy060_z060_blend100_down0035_align025` | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.200 | 67.1 | 1.000 |
| `guard_xy060_z080_blend100_down0035_align025` | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.200 | 81.5 | 1.000 |
| `guard_xy060_z100_blend075_down0035_align025` | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.200 | 82.3 | 1.000 |
| `guard_xy060_z100_blend050_down0035_align025` | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.200 | 84.6 | 1.000 |
| `guard_xy060_z100_blend100_down0025_align025` | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.200 | 88.1 | 1.000 |
| `guard_xy060_z100_blend100_down0045_align025` | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.200 | 78.3 | 1.000 |
| `no_guard` | 0.400 | 0.400 | 0.400 | 0.400 | 0.400 | 0.200 | 0.0 | 0.000 |

## Per-Scenario Rows

| Candidate | Scenario | Success | Collision | Timeout | Return | Steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `no_guard` | visual_camera_control | 0.400 | 0.200 | 0.400 | 65.395 | 128.2 | 0.0 | 0.000 | 0.00943 | 0.01685 |
| `guard_xy060_z100_blend100_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 164.763 | 93.6 | 77.8 | 1.000 | 0.00825 | 0.01639 |
| `guard_xy040_z100_blend100_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 166.045 | 96.4 | 70.2 | 1.000 | 0.00835 | 0.01642 |
| `guard_xy050_z100_blend100_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 164.947 | 93.6 | 72.6 | 1.000 | 0.00827 | 0.01648 |
| `guard_xy070_z100_blend100_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 164.681 | 93.6 | 83.0 | 1.000 | 0.00826 | 0.01638 |
| `guard_xy060_z060_blend100_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 171.417 | 100.0 | 65.2 | 1.000 | 0.00825 | 0.01645 |
| `guard_xy060_z080_blend100_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 164.763 | 93.6 | 77.8 | 1.000 | 0.00825 | 0.01639 |
| `guard_xy060_z100_blend075_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 168.379 | 95.0 | 79.2 | 1.000 | 0.00847 | 0.01690 |
| `guard_xy060_z100_blend050_down0035_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 166.959 | 95.2 | 79.4 | 1.000 | 0.00869 | 0.01670 |
| `guard_xy060_z100_blend100_down0025_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 167.027 | 100.8 | 85.0 | 1.000 | 0.00836 | 0.01652 |
| `guard_xy060_z100_blend100_down0045_align025` | visual_camera_control | 0.800 | 0.200 | 0.000 | 166.982 | 92.4 | 76.6 | 1.000 | 0.00804 | 0.01687 |
| `guard_xy060_z100_blend100_down0035_align020` | visual_camera_control | 0.800 | 0.200 | 0.000 | 173.675 | 94.6 | 78.8 | 1.000 | 0.00824 | 0.01651 |
| `guard_xy060_z100_blend100_down0035_align015` | visual_camera_control | 0.800 | 0.200 | 0.000 | 188.739 | 99.2 | 83.4 | 1.000 | 0.00831 | 0.01658 |
| `no_guard` | full_light_geometry | 0.400 | 0.200 | 0.400 | 71.118 | 128.8 | 0.0 | 0.000 | 0.00907 | 0.01693 |
| `guard_xy060_z100_blend100_down0035_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 167.870 | 95.4 | 79.4 | 1.000 | 0.00793 | 0.01662 |
| `guard_xy040_z100_blend100_down0035_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 168.355 | 96.4 | 70.0 | 1.000 | 0.00792 | 0.01648 |
| `guard_xy050_z100_blend100_down0035_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 167.777 | 95.0 | 73.8 | 1.000 | 0.00794 | 0.01663 |
| `guard_xy070_z100_blend100_down0035_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 167.833 | 95.4 | 84.6 | 1.000 | 0.00793 | 0.01663 |
| `guard_xy060_z060_blend100_down0035_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 173.231 | 99.6 | 62.8 | 1.000 | 0.00795 | 0.01653 |
| `guard_xy060_z080_blend100_down0035_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 167.870 | 95.4 | 79.4 | 1.000 | 0.00793 | 0.01662 |
| `guard_xy060_z100_blend075_down0035_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 169.107 | 96.8 | 80.8 | 1.000 | 0.00801 | 0.01657 |
| `guard_xy060_z100_blend050_down0035_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 171.691 | 98.0 | 82.0 | 1.000 | 0.00811 | 0.01653 |
| `guard_xy060_z100_blend100_down0025_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 169.971 | 102.2 | 86.2 | 1.000 | 0.00804 | 0.01660 |
| `guard_xy060_z100_blend100_down0045_align025` | full_light_geometry | 0.800 | 0.200 | 0.000 | 170.236 | 93.2 | 77.2 | 1.000 | 0.00773 | 0.01741 |
| `guard_xy060_z100_blend100_down0035_align020` | full_light_geometry | 1.000 | 0.000 | 0.000 | 273.579 | 112.6 | 96.6 | 1.000 | 0.00474 | 0.00851 |
| `guard_xy060_z100_blend100_down0035_align015` | full_light_geometry | 1.000 | 0.000 | 0.000 | 291.554 | 108.8 | 92.8 | 1.000 | 0.00483 | 0.00837 |
| `no_guard` | full_contact_light | 0.400 | 0.200 | 0.400 | 71.042 | 128.8 | 0.0 | 0.000 | 0.00905 | 0.01696 |
| `guard_xy060_z100_blend100_down0035_align025` | full_contact_light | 0.800 | 0.200 | 0.000 | 170.265 | 98.8 | 82.8 | 1.000 | 0.00787 | 0.01684 |
| `guard_xy040_z100_blend100_down0035_align025` | full_contact_light | 0.800 | 0.200 | 0.000 | 170.256 | 99.2 | 72.6 | 1.000 | 0.00799 | 0.01676 |
| `guard_xy050_z100_blend100_down0035_align025` | full_contact_light | 0.800 | 0.200 | 0.000 | 170.397 | 98.8 | 77.6 | 1.000 | 0.00789 | 0.01689 |
| `guard_xy070_z100_blend100_down0035_align025` | full_contact_light | 0.800 | 0.200 | 0.000 | 169.966 | 98.6 | 87.8 | 1.000 | 0.00789 | 0.01678 |
| `guard_xy060_z060_blend100_down0035_align025` | full_contact_light | 0.800 | 0.200 | 0.000 | 175.002 | 104.0 | 67.6 | 1.000 | 0.00799 | 0.01641 |
| `guard_xy060_z080_blend100_down0035_align025` | full_contact_light | 0.800 | 0.200 | 0.000 | 170.235 | 98.8 | 82.8 | 1.000 | 0.00787 | 0.01683 |
| `guard_xy060_z100_blend075_down0035_align025` | full_contact_light | 0.800 | 0.200 | 0.000 | 172.574 | 98.6 | 82.6 | 1.000 | 0.00799 | 0.01685 |
| `guard_xy060_z100_blend050_down0035_align025` | full_contact_light | 0.800 | 0.200 | 0.000 | 173.806 | 98.4 | 82.4 | 1.000 | 0.00811 | 0.01684 |
| `guard_xy060_z100_blend100_down0025_align025` | full_contact_light | 0.800 | 0.200 | 0.000 | 171.890 | 103.6 | 87.6 | 1.000 | 0.00802 | 0.01654 |
| `guard_xy060_z100_blend100_down0045_align025` | full_contact_light | 0.800 | 0.200 | 0.000 | 169.719 | 95.4 | 79.4 | 1.000 | 0.00771 | 0.01699 |
| `guard_xy060_z100_blend100_down0035_align020` | full_contact_light | 1.000 | 0.000 | 0.000 | 274.735 | 108.0 | 92.0 | 1.000 | 0.00473 | 0.00884 |
| `guard_xy060_z100_blend100_down0035_align015` | full_contact_light | 1.000 | 0.000 | 0.000 | 290.325 | 109.0 | 93.0 | 1.000 | 0.00485 | 0.00829 |
| `no_guard` | hard_full_light_bucket | 0.400 | 0.200 | 0.400 | 55.560 | 135.0 | 0.0 | 0.000 | 0.01051 | 0.01615 |
| `guard_xy060_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 159.561 | 102.2 | 85.8 | 1.000 | 0.00891 | 0.01644 |
| `guard_xy040_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 159.647 | 103.0 | 75.8 | 1.000 | 0.00904 | 0.01647 |
| `guard_xy050_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 159.866 | 103.6 | 81.8 | 1.000 | 0.00895 | 0.01642 |
| `guard_xy070_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 159.940 | 103.8 | 92.8 | 1.000 | 0.00889 | 0.01651 |
| `guard_xy060_z060_blend100_down0035_align025` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 162.494 | 107.4 | 72.8 | 1.000 | 0.00892 | 0.01647 |
| `guard_xy060_z080_blend100_down0035_align025` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 159.562 | 102.2 | 85.8 | 1.000 | 0.00891 | 0.01644 |
| `guard_xy060_z100_blend075_down0035_align025` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 157.342 | 103.0 | 86.6 | 1.000 | 0.00916 | 0.01613 |
| `guard_xy060_z100_blend050_down0035_align025` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 152.636 | 110.8 | 94.4 | 1.000 | 0.00928 | 0.01615 |
| `guard_xy060_z100_blend100_down0025_align025` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 161.941 | 110.0 | 93.6 | 1.000 | 0.00901 | 0.01617 |
| `guard_xy060_z100_blend100_down0045_align025` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 159.670 | 96.6 | 80.2 | 1.000 | 0.00882 | 0.01648 |
| `guard_xy060_z100_blend100_down0035_align020` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 167.217 | 101.8 | 85.4 | 1.000 | 0.00890 | 0.01654 |
| `guard_xy060_z100_blend100_down0035_align015` | hard_full_light_bucket | 0.800 | 0.200 | 0.000 | 180.675 | 106.6 | 90.2 | 1.000 | 0.00895 | 0.01651 |
