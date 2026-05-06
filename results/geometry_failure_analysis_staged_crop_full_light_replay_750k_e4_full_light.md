# Geometry Failure Analysis

- Generated: `2026-05-06T17:45:18`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Domain randomization level: `full_light_geometry`
- Episodes: `200`
- Seed: `820000`
- Image size: `100x100`
- Near-hole crop: `True`
- Hole half-size range: `0.025:0.029`
- Peg radius range: `0.0115:0.0125`

## Overall

| Episodes | Success | Collision | Timeout | Mean final XY | Mean final Z | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 200 | 0.650 | 0.345 | 0.005 | 0.01441 | 0.02046 | 0.03413 | 0.04407 |

## Failure Subset

| Subset | Episodes | Mean final XY | Mean min XY | Mean final Z | Mean action Z | Mean action XY norm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| collisions | 69 | 0.03436 | 0.02546 | 0.04361 | 0.00225 | 0.00597 |
| timeouts | 1 | 0.01864 | 0.00377 | 0.07561 | 0.00079 | 0.00421 |

## By Delay

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_0 | 68 | 0.882 | 0.103 | 0.015 | 27.7 | 0.00933 | 0.01100 |
| delay_1 | 63 | 0.635 | 0.365 | 0.000 | 23.2 | 0.01184 | 0.02221 |
| delay_2 | 69 | 0.435 | 0.565 | 0.000 | 16.1 | 0.02175 | 0.02820 |

## By Filter Alpha

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| high_>=0.85 | 73 | 0.699 | 0.301 | 0.000 | 20.1 | 0.01228 | 0.01811 |
| low_<0.70 | 63 | 0.556 | 0.429 | 0.016 | 23.5 | 0.01918 | 0.02337 |
| mid_0.70_0.85 | 64 | 0.688 | 0.312 | 0.000 | 23.6 | 0.01213 | 0.02029 |

## By Scale

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| high_>1.10 | 53 | 0.717 | 0.283 | 0.000 | 20.2 | 0.01286 | 0.01739 |
| low_<0.90 | 54 | 0.593 | 0.389 | 0.019 | 24.7 | 0.01726 | 0.02211 |
| mid_0.90_1.10 | 93 | 0.645 | 0.355 | 0.000 | 22.0 | 0.01363 | 0.02126 |

## By Noise

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| high_>=0.00055 | 62 | 0.629 | 0.355 | 0.016 | 27.1 | 0.01546 | 0.02242 |
| low_<0.00025 | 60 | 0.567 | 0.433 | 0.000 | 19.8 | 0.01538 | 0.02285 |
| mid_0.00025_0.00055 | 78 | 0.731 | 0.269 | 0.000 | 20.4 | 0.01282 | 0.01708 |

## Worst Joint Buckets

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2|low_<0.70|mid_0.90_1.10|low_<0.00025 | 5 | 0.000 | 1.000 | 0.000 | 7.2 | 0.03680 | 0.04914 |
| delay_2|low_<0.70|low_<0.90|low_<0.00025 | 5 | 0.400 | 0.600 | 0.000 | 16.4 | 0.02203 | 0.01689 |
| delay_2|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 5 | 0.400 | 0.600 | 0.000 | 19.2 | 0.01683 | 0.02353 |
| delay_1|low_<0.70|mid_0.90_1.10|high_>=0.00055 | 4 | 0.500 | 0.500 | 0.000 | 15.5 | 0.01805 | 0.02888 |
| delay_2|mid_0.70_0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 0.500 | 0.500 | 0.000 | 16.8 | 0.01678 | 0.02846 |
| delay_2|low_<0.70|mid_0.90_1.10|mid_0.00025_0.00055 | 8 | 0.625 | 0.375 | 0.000 | 20.2 | 0.01876 | 0.02022 |
| delay_1|high_>=0.85|mid_0.90_1.10|low_<0.00025 | 6 | 0.667 | 0.333 | 0.000 | 18.0 | 0.00977 | 0.01793 |
| delay_1|mid_0.70_0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 7 | 0.714 | 0.286 | 0.000 | 17.1 | 0.01289 | 0.01962 |
| delay_0|low_<0.70|low_<0.90|high_>=0.00055 | 4 | 0.500 | 0.250 | 0.250 | 71.2 | 0.02911 | 0.02467 |
| delay_1|high_>=0.85|high_>1.10|mid_0.00025_0.00055 | 4 | 0.750 | 0.250 | 0.000 | 23.2 | 0.00725 | 0.01676 |
| delay_0|low_<0.70|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 0.750 | 0.250 | 0.000 | 15.2 | 0.00688 | 0.01709 |
| delay_1|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 4 | 0.750 | 0.250 | 0.000 | 59.5 | 0.00776 | 0.02694 |
| delay_1|high_>=0.85|mid_0.90_1.10|high_>=0.00055 | 5 | 0.800 | 0.200 | 0.000 | 44.6 | 0.00739 | 0.02289 |
| delay_2|high_>=0.85|low_<0.90|mid_0.00025_0.00055 | 5 | 0.800 | 0.200 | 0.000 | 26.2 | 0.01007 | 0.01594 |
| delay_0|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 6 | 1.000 | 0.000 | 0.000 | 22.7 | 0.00459 | 0.00747 |
| delay_0|mid_0.70_0.85|high_>1.10|mid_0.00025_0.00055 | 5 | 1.000 | 0.000 | 0.000 | 22.6 | 0.00390 | 0.00836 |
| delay_0|mid_0.70_0.85|low_<0.90|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 32.0 | 0.00438 | 0.00810 |
| delay_0|high_>=0.85|high_>1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 16.0 | 0.00403 | 0.00819 |

## Failure XY Buckets

| Final XY bucket | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| aligned_<0.005 | 130 | 1.000 | 0.000 | 0.000 |
| off_0.015_0.030 | 41 | 0.000 | 0.976 | 0.024 |
| far_>=0.030 | 29 | 0.000 | 1.000 | 0.000 |

## Interpretation

If most collisions have non-trivial final or minimum XY error, the policy is descending or contacting before lateral alignment is robust. That is the target failure mode for a near-hole crop or a two-stage approach/insert controller.
