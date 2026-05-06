# Guarded Policy Parameter Scan

- Generated: `2026-05-06T20:27:50`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Preset: `focused`
- Scenario preset: `targeted`
- Candidates: `13`
- Episodes per candidate/scenario: `30`
- Seed: `90000`
- Guard scenario filter: `geometry`

## Candidate Summary

| Candidate | visual_camera_control | full_light_geometry | full_contact_light | hard_full_light_bucket | Mean success | Mean collision | Guard steps | Guard ep. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `guard_xy060_z100_blend075_down0035_align025` | 0.900 | 0.767 | 0.767 | 0.533 | 0.742 | 0.225 | 21.8 | 0.692 |
| `guard_xy060_z100_blend100_down0035_align025` | 0.933 | 0.733 | 0.733 | 0.467 | 0.717 | 0.258 | 21.1 | 0.692 |
| `guard_xy070_z100_blend100_down0035_align025` | 0.867 | 0.733 | 0.767 | 0.467 | 0.708 | 0.267 | 21.4 | 0.717 |
| `guard_xy060_z100_blend050_down0035_align025` | 0.933 | 0.600 | 0.767 | 0.533 | 0.708 | 0.292 | 21.4 | 0.692 |
| `guard_xy060_z080_blend100_down0035_align025` | 0.900 | 0.733 | 0.733 | 0.467 | 0.708 | 0.267 | 21.1 | 0.692 |
| `guard_xy060_z100_blend100_down0025_align025` | 0.900 | 0.667 | 0.733 | 0.467 | 0.692 | 0.258 | 25.1 | 0.692 |
| `guard_xy060_z100_blend100_down0045_align025` | 0.900 | 0.733 | 0.667 | 0.467 | 0.692 | 0.258 | 23.8 | 0.692 |
| `guard_xy040_z100_blend100_down0035_align025` | 0.900 | 0.700 | 0.700 | 0.433 | 0.683 | 0.275 | 23.8 | 0.642 |
| `guard_xy050_z100_blend100_down0035_align025` | 0.933 | 0.667 | 0.700 | 0.433 | 0.683 | 0.275 | 23.4 | 0.683 |
| `no_guard` | 0.933 | 0.667 | 0.700 | 0.400 | 0.675 | 0.325 | 0.0 | 0.000 |
| `guard_xy060_z060_blend100_down0035_align025` | 0.900 | 0.600 | 0.667 | 0.400 | 0.642 | 0.333 | 17.4 | 0.692 |
| `guard_xy060_z100_blend100_down0035_align020` | 0.867 | 0.600 | 0.667 | 0.433 | 0.642 | 0.333 | 22.1 | 0.692 |
| `guard_xy060_z100_blend100_down0035_align015` | 0.900 | 0.600 | 0.600 | 0.400 | 0.625 | 0.358 | 19.2 | 0.692 |

## Per-Scenario Rows

| Candidate | Scenario | Success | Collision | Timeout | Return | Steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `no_guard` | visual_camera_control | 0.933 | 0.067 | 0.000 | 124.586 | 23.6 | 0.0 | 0.000 | 0.00729 | 0.01066 |
| `guard_xy060_z100_blend100_down0035_align025` | visual_camera_control | 0.933 | 0.067 | 0.000 | 124.535 | 23.6 | 0.0 | 0.000 | 0.00734 | 0.01062 |
| `guard_xy040_z100_blend100_down0035_align025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 114.787 | 26.4 | 0.0 | 0.000 | 0.00843 | 0.01300 |
| `guard_xy050_z100_blend100_down0035_align025` | visual_camera_control | 0.933 | 0.067 | 0.000 | 124.500 | 23.5 | 0.0 | 0.000 | 0.00733 | 0.01065 |
| `guard_xy070_z100_blend100_down0035_align025` | visual_camera_control | 0.867 | 0.133 | 0.000 | 103.548 | 31.1 | 0.0 | 0.000 | 0.00957 | 0.01529 |
| `guard_xy060_z060_blend100_down0035_align025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 113.952 | 28.5 | 0.0 | 0.000 | 0.00842 | 0.01289 |
| `guard_xy060_z080_blend100_down0035_align025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 113.036 | 28.0 | 0.0 | 0.000 | 0.00843 | 0.01291 |
| `guard_xy060_z100_blend075_down0035_align025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 113.616 | 28.4 | 0.0 | 0.000 | 0.00845 | 0.01289 |
| `guard_xy060_z100_blend050_down0035_align025` | visual_camera_control | 0.933 | 0.067 | 0.000 | 124.713 | 23.7 | 0.0 | 0.000 | 0.00730 | 0.01063 |
| `guard_xy060_z100_blend100_down0025_align025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 112.906 | 27.9 | 0.0 | 0.000 | 0.00845 | 0.01292 |
| `guard_xy060_z100_blend100_down0045_align025` | visual_camera_control | 0.900 | 0.100 | 0.000 | 112.996 | 28.0 | 0.0 | 0.000 | 0.00842 | 0.01290 |
| `guard_xy060_z100_blend100_down0035_align020` | visual_camera_control | 0.867 | 0.133 | 0.000 | 102.447 | 30.3 | 0.0 | 0.000 | 0.00953 | 0.01531 |
| `guard_xy060_z100_blend100_down0035_align015` | visual_camera_control | 0.900 | 0.100 | 0.000 | 112.851 | 27.8 | 0.0 | 0.000 | 0.00847 | 0.01293 |
| `no_guard` | full_light_geometry | 0.667 | 0.333 | 0.000 | 2.748 | 15.8 | 0.0 | 0.000 | 0.01275 | 0.01954 |
| `guard_xy060_z100_blend100_down0035_align025` | full_light_geometry | 0.733 | 0.200 | 0.067 | 56.129 | 39.4 | 38.2 | 0.933 | 0.01118 | 0.02343 |
| `guard_xy040_z100_blend100_down0035_align025` | full_light_geometry | 0.700 | 0.200 | 0.100 | 58.092 | 45.8 | 43.1 | 0.900 | 0.01157 | 0.02630 |
| `guard_xy050_z100_blend100_down0035_align025` | full_light_geometry | 0.667 | 0.233 | 0.100 | 43.480 | 45.4 | 43.5 | 0.933 | 0.01162 | 0.02596 |
| `guard_xy070_z100_blend100_down0035_align025` | full_light_geometry | 0.733 | 0.200 | 0.067 | 55.010 | 39.5 | 38.7 | 0.967 | 0.01141 | 0.02345 |
| `guard_xy060_z060_blend100_down0035_align025` | full_light_geometry | 0.600 | 0.333 | 0.067 | -1.482 | 37.1 | 31.8 | 0.933 | 0.01339 | 0.02855 |
| `guard_xy060_z080_blend100_down0035_align025` | full_light_geometry | 0.733 | 0.200 | 0.067 | 56.129 | 39.4 | 38.2 | 0.933 | 0.01118 | 0.02343 |
| `guard_xy060_z100_blend075_down0035_align025` | full_light_geometry | 0.767 | 0.167 | 0.067 | 79.880 | 40.5 | 39.3 | 0.933 | 0.01054 | 0.02194 |
| `guard_xy060_z100_blend050_down0035_align025` | full_light_geometry | 0.600 | 0.400 | 0.033 | 2.511 | 45.4 | 44.3 | 0.933 | 0.01376 | 0.02954 |
| `guard_xy060_z100_blend100_down0025_align025` | full_light_geometry | 0.667 | 0.200 | 0.133 | 59.140 | 52.2 | 51.1 | 0.933 | 0.01137 | 0.03001 |
| `guard_xy060_z100_blend100_down0045_align025` | full_light_geometry | 0.733 | 0.200 | 0.067 | 57.146 | 38.7 | 37.5 | 0.933 | 0.01138 | 0.02328 |
| `guard_xy060_z100_blend100_down0035_align020` | full_light_geometry | 0.600 | 0.333 | 0.067 | 15.078 | 44.0 | 42.9 | 0.933 | 0.01327 | 0.03028 |
| `guard_xy060_z100_blend100_down0035_align015` | full_light_geometry | 0.600 | 0.367 | 0.033 | 2.472 | 35.7 | 34.6 | 0.933 | 0.01436 | 0.02810 |
| `no_guard` | full_contact_light | 0.700 | 0.300 | 0.000 | 14.263 | 14.6 | 0.0 | 0.000 | 0.01313 | 0.02034 |
| `guard_xy060_z100_blend100_down0035_align025` | full_contact_light | 0.733 | 0.233 | 0.033 | 34.186 | 26.7 | 25.7 | 0.933 | 0.01204 | 0.01929 |
| `guard_xy040_z100_blend100_down0035_align025` | full_contact_light | 0.700 | 0.233 | 0.067 | 37.056 | 32.2 | 29.5 | 0.900 | 0.01278 | 0.02346 |
| `guard_xy050_z100_blend100_down0035_align025` | full_contact_light | 0.700 | 0.233 | 0.067 | 36.842 | 32.5 | 30.7 | 0.933 | 0.01226 | 0.02178 |
| `guard_xy070_z100_blend100_down0035_align025` | full_contact_light | 0.767 | 0.200 | 0.033 | 49.006 | 26.9 | 26.1 | 0.967 | 0.01112 | 0.01768 |
| `guard_xy060_z060_blend100_down0035_align025` | full_contact_light | 0.667 | 0.300 | 0.033 | 7.991 | 26.8 | 21.5 | 0.933 | 0.01361 | 0.02352 |
| `guard_xy060_z080_blend100_down0035_align025` | full_contact_light | 0.733 | 0.233 | 0.033 | 34.187 | 26.7 | 25.7 | 0.933 | 0.01204 | 0.01929 |
| `guard_xy060_z100_blend075_down0035_align025` | full_contact_light | 0.767 | 0.200 | 0.033 | 54.680 | 28.1 | 27.0 | 0.933 | 0.01191 | 0.01950 |
| `guard_xy060_z100_blend050_down0035_align025` | full_contact_light | 0.767 | 0.233 | 0.000 | 46.920 | 23.5 | 22.4 | 0.933 | 0.01187 | 0.01809 |
| `guard_xy060_z100_blend100_down0025_align025` | full_contact_light | 0.733 | 0.200 | 0.067 | 52.084 | 32.9 | 31.8 | 0.933 | 0.01170 | 0.02262 |
| `guard_xy060_z100_blend100_down0045_align025` | full_contact_light | 0.667 | 0.233 | 0.100 | 42.662 | 38.4 | 37.4 | 0.933 | 0.01247 | 0.02468 |
| `guard_xy060_z100_blend100_down0035_align020` | full_contact_light | 0.667 | 0.300 | 0.033 | 16.541 | 32.4 | 31.3 | 0.933 | 0.01316 | 0.02403 |
| `guard_xy060_z100_blend100_down0035_align015` | full_contact_light | 0.600 | 0.367 | 0.033 | -4.643 | 29.7 | 28.6 | 0.933 | 0.01473 | 0.02727 |
| `no_guard` | hard_full_light_bucket | 0.400 | 0.600 | 0.000 | -111.341 | 17.7 | 0.0 | 0.000 | 0.02300 | 0.02975 |
| `guard_xy060_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.467 | 0.533 | 0.000 | -89.160 | 21.6 | 20.4 | 0.900 | 0.02184 | 0.03072 |
| `guard_xy040_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.433 | 0.567 | 0.000 | -100.095 | 26.0 | 22.7 | 0.767 | 0.02257 | 0.03278 |
| `guard_xy050_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.433 | 0.567 | 0.000 | -104.288 | 21.8 | 19.6 | 0.867 | 0.02224 | 0.03157 |
| `guard_xy070_z100_blend100_down0035_align025` | hard_full_light_bucket | 0.467 | 0.533 | 0.000 | -89.266 | 21.7 | 20.8 | 0.933 | 0.02198 | 0.03073 |
| `guard_xy060_z060_blend100_down0035_align025` | hard_full_light_bucket | 0.400 | 0.600 | 0.000 | -117.529 | 21.3 | 16.3 | 0.900 | 0.02323 | 0.03087 |
| `guard_xy060_z080_blend100_down0035_align025` | hard_full_light_bucket | 0.467 | 0.533 | 0.000 | -89.160 | 21.6 | 20.4 | 0.900 | 0.02184 | 0.03072 |
| `guard_xy060_z100_blend075_down0035_align025` | hard_full_light_bucket | 0.533 | 0.433 | 0.033 | -46.706 | 21.9 | 20.7 | 0.900 | 0.01991 | 0.02803 |
| `guard_xy060_z100_blend050_down0035_align025` | hard_full_light_bucket | 0.533 | 0.467 | 0.000 | -55.206 | 20.1 | 18.9 | 0.900 | 0.02031 | 0.02793 |
| `guard_xy060_z100_blend100_down0025_align025` | hard_full_light_bucket | 0.467 | 0.533 | 0.000 | -91.803 | 18.9 | 17.7 | 0.900 | 0.02176 | 0.03016 |
| `guard_xy060_z100_blend100_down0045_align025` | hard_full_light_bucket | 0.467 | 0.500 | 0.033 | -78.220 | 21.7 | 20.4 | 0.900 | 0.02166 | 0.03071 |
| `guard_xy060_z100_blend100_down0035_align020` | hard_full_light_bucket | 0.433 | 0.567 | 0.000 | -108.052 | 15.2 | 14.0 | 0.900 | 0.02239 | 0.03056 |
| `guard_xy060_z100_blend100_down0035_align015` | hard_full_light_bucket | 0.400 | 0.600 | 0.000 | -117.247 | 14.8 | 13.5 | 0.900 | 0.02301 | 0.03195 |
