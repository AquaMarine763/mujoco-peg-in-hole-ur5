# Control Failure Analysis

- Generated: `2026-05-06T17:05:41`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Domain randomization level: `visual_camera_control`
- Episodes: `200`
- Seed: `150000`
- Success tolerances: `xy=0.005`, `z=0.01`

## Overall

| Episodes | Success | Collision | Timeout | Failures | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 200 | 0.820 | 0.180 | 0.000 | 36 | 0.04209 | 0.05779 |

## By Delay

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2 | 72 | 0.694 | 0.306 | 0.000 | 40.7 | 0.01559 | 0.02066 |
| delay_1 | 63 | 0.889 | 0.111 | 0.000 | 34.0 | 0.00827 | 0.01482 |
| delay_0 | 65 | 0.892 | 0.108 | 0.000 | 37.9 | 0.00818 | 0.01464 |

## By Filter Alpha

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.70 | 62 | 0.726 | 0.274 | 0.000 | 46.7 | 0.01429 | 0.02290 |
| high_>=0.85 | 63 | 0.841 | 0.159 | 0.000 | 31.1 | 0.01013 | 0.01281 |
| mid_0.70_0.85 | 75 | 0.880 | 0.120 | 0.000 | 35.7 | 0.00867 | 0.01528 |

## By Scale

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.90 | 43 | 0.628 | 0.372 | 0.000 | 67.6 | 0.01821 | 0.03159 |
| mid_0.90_1.10 | 97 | 0.825 | 0.175 | 0.000 | 29.2 | 0.01080 | 0.01402 |
| high_>1.10 | 60 | 0.950 | 0.050 | 0.000 | 30.0 | 0.00573 | 0.01092 |

## By Noise

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.00025 | 75 | 0.800 | 0.200 | 0.000 | 39.9 | 0.01179 | 0.01750 |
| mid_0.00025_0.00055 | 75 | 0.813 | 0.187 | 0.000 | 36.5 | 0.01117 | 0.01715 |
| high_>=0.00055 | 50 | 0.860 | 0.140 | 0.000 | 36.2 | 0.00905 | 0.01549 |

## Worst Joint Buckets

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2|low_<0.70|mid_0.90_1.10|high_>=0.00055 | 4 | 0.500 | 0.500 | 0.000 | 50.8 | 0.02603 | 0.03419 |
| delay_2|low_<0.70|mid_0.90_1.10|low_<0.00025 | 4 | 0.500 | 0.500 | 0.000 | 56.0 | 0.02155 | 0.02738 |
| delay_2|high_>=0.85|mid_0.90_1.10|low_<0.00025 | 5 | 0.600 | 0.400 | 0.000 | 20.0 | 0.01782 | 0.00790 |
| delay_2|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 9 | 0.667 | 0.333 | 0.000 | 35.0 | 0.01629 | 0.01923 |
| delay_0|low_<0.70|mid_0.90_1.10|high_>=0.00055 | 4 | 0.750 | 0.250 | 0.000 | 44.5 | 0.01284 | 0.02301 |
| delay_0|mid_0.70_0.85|high_>1.10|mid_0.00025_0.00055 | 4 | 0.750 | 0.250 | 0.000 | 50.0 | 0.01311 | 0.02505 |
| delay_2|mid_0.70_0.85|high_>1.10|low_<0.00025 | 9 | 0.778 | 0.222 | 0.000 | 38.7 | 0.01268 | 0.02060 |
| delay_0|low_<0.70|mid_0.90_1.10|mid_0.00025_0.00055 | 7 | 0.857 | 0.143 | 0.000 | 42.0 | 0.00962 | 0.01712 |
| delay_2|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 7 | 0.857 | 0.143 | 0.000 | 27.9 | 0.01212 | 0.01382 |
| delay_0|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 6 | 1.000 | 0.000 | 0.000 | 23.0 | 0.00431 | 0.00795 |
| delay_1|mid_0.70_0.85|high_>1.10|mid_0.00025_0.00055 | 5 | 1.000 | 0.000 | 0.000 | 18.4 | 0.00357 | 0.00832 |
| delay_0|mid_0.70_0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 21.0 | 0.00456 | 0.00776 |
| delay_1|high_>=0.85|high_>1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 29.0 | 0.00416 | 0.00796 |
| delay_0|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 30.8 | 0.00487 | 0.00780 |
| delay_1|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 4 | 1.000 | 0.000 | 0.000 | 19.0 | 0.00366 | 0.00802 |
| delay_1|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 16.8 | 0.00389 | 0.00794 |
| delay_1|low_<0.70|high_>1.10|high_>=0.00055 | 4 | 1.000 | 0.000 | 0.000 | 21.8 | 0.00241 | 0.00804 |

## Suggested Next Data Bias

Prioritize new success-only data around `delay_2`, `low_<0.70`, `low_<0.90`, and `low_<0.00025`. These buckets currently have the highest collision/timeout rates in the evaluated control-randomization distribution.
