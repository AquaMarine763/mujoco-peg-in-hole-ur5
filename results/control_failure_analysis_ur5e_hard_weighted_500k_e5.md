# Control Failure Analysis

- Generated: `2026-05-06T13:07:06`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Domain randomization level: `visual_camera_control`
- Episodes: `200`
- Seed: `150000`
- Success tolerances: `xy=0.005`, `z=0.01`

## Overall

| Episodes | Success | Collision | Timeout | Failures | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 200 | 0.865 | 0.135 | 0.000 | 27 | 0.04368 | 0.05824 |

## By Delay

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2 | 72 | 0.778 | 0.222 | 0.000 | 36.2 | 0.01231 | 0.01757 |
| delay_1 | 63 | 0.873 | 0.127 | 0.000 | 37.9 | 0.00829 | 0.01625 |
| delay_0 | 65 | 0.954 | 0.046 | 0.000 | 28.1 | 0.00707 | 0.01002 |

## By Filter Alpha

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.70 | 62 | 0.823 | 0.177 | 0.000 | 36.1 | 0.01070 | 0.01625 |
| mid_0.70_0.85 | 75 | 0.853 | 0.147 | 0.000 | 33.4 | 0.00951 | 0.01640 |
| high_>=0.85 | 63 | 0.921 | 0.079 | 0.000 | 33.0 | 0.00780 | 0.01114 |

## By Scale

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.90 | 43 | 0.767 | 0.233 | 0.000 | 49.7 | 0.01258 | 0.02262 |
| mid_0.90_1.10 | 97 | 0.856 | 0.144 | 0.000 | 32.2 | 0.01044 | 0.01419 |
| high_>1.10 | 60 | 0.950 | 0.050 | 0.000 | 26.1 | 0.00523 | 0.00985 |

## By Noise

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| high_>=0.00055 | 50 | 0.840 | 0.160 | 0.000 | 35.8 | 0.01003 | 0.01638 |
| low_<0.00025 | 75 | 0.867 | 0.133 | 0.000 | 34.9 | 0.00883 | 0.01475 |
| mid_0.00025_0.00055 | 75 | 0.880 | 0.120 | 0.000 | 32.3 | 0.00939 | 0.01353 |

## Worst Joint Buckets

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2|low_<0.70|mid_0.90_1.10|high_>=0.00055 | 4 | 0.250 | 0.750 | 0.000 | 44.0 | 0.03262 | 0.03315 |
| delay_1|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 4 | 0.500 | 0.500 | 0.000 | 75.0 | 0.02118 | 0.04276 |
| delay_2|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 7 | 0.714 | 0.286 | 0.000 | 18.0 | 0.01712 | 0.01979 |
| delay_0|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 0.750 | 0.250 | 0.000 | 41.5 | 0.03111 | 0.00952 |
| delay_2|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 9 | 0.889 | 0.111 | 0.000 | 36.8 | 0.00761 | 0.01500 |
| delay_2|mid_0.70_0.85|high_>1.10|low_<0.00025 | 9 | 0.889 | 0.111 | 0.000 | 36.7 | 0.00660 | 0.01337 |
| delay_0|low_<0.70|mid_0.90_1.10|mid_0.00025_0.00055 | 7 | 1.000 | 0.000 | 0.000 | 23.3 | 0.00428 | 0.00789 |
| delay_0|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 6 | 1.000 | 0.000 | 0.000 | 31.3 | 0.00477 | 0.00785 |
| delay_2|high_>=0.85|mid_0.90_1.10|low_<0.00025 | 5 | 1.000 | 0.000 | 0.000 | 37.4 | 0.00350 | 0.00810 |
| delay_1|mid_0.70_0.85|high_>1.10|mid_0.00025_0.00055 | 5 | 1.000 | 0.000 | 0.000 | 20.2 | 0.00267 | 0.00832 |
| delay_0|mid_0.70_0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 18.8 | 0.00483 | 0.00820 |
| delay_1|high_>=0.85|high_>1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 39.5 | 0.00346 | 0.00816 |
| delay_0|low_<0.70|mid_0.90_1.10|high_>=0.00055 | 4 | 1.000 | 0.000 | 0.000 | 28.2 | 0.00484 | 0.00791 |
| delay_0|mid_0.70_0.85|high_>1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 12.8 | 0.00411 | 0.00841 |
| delay_2|low_<0.70|mid_0.90_1.10|low_<0.00025 | 4 | 1.000 | 0.000 | 0.000 | 41.8 | 0.00387 | 0.00796 |
| delay_1|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 29.2 | 0.00400 | 0.00797 |
| delay_1|low_<0.70|high_>1.10|high_>=0.00055 | 4 | 1.000 | 0.000 | 0.000 | 21.2 | 0.00392 | 0.00803 |

## Suggested Next Data Bias

Prioritize new success-only data around `delay_2`, `low_<0.70`, `low_<0.90`, and `high_>=0.00055`. These buckets currently have the highest collision/timeout rates in the evaluated control-randomization distribution.
