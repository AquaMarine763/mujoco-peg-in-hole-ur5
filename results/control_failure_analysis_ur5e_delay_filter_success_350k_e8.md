# Control Failure Analysis

- Generated: `2026-05-06T12:30:58`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Domain randomization level: `visual_camera_control`
- Episodes: `200`
- Seed: `150000`
- Success tolerances: `xy=0.005`, `z=0.01`

## Overall

| Episodes | Success | Collision | Timeout | Failures | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 200 | 0.830 | 0.165 | 0.005 | 34 | 0.04292 | 0.06562 |

## By Delay

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2 | 72 | 0.764 | 0.236 | 0.000 | 39.6 | 0.01320 | 0.02038 |
| delay_1 | 63 | 0.794 | 0.190 | 0.016 | 45.3 | 0.01112 | 0.02117 |
| delay_0 | 65 | 0.938 | 0.062 | 0.000 | 27.7 | 0.00725 | 0.01146 |

## By Filter Alpha

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.70 | 62 | 0.790 | 0.210 | 0.000 | 39.4 | 0.01191 | 0.01918 |
| mid_0.70_0.85 | 75 | 0.800 | 0.200 | 0.000 | 38.5 | 0.01164 | 0.02027 |
| high_>=0.85 | 63 | 0.905 | 0.079 | 0.016 | 34.5 | 0.00811 | 0.01327 |

## By Scale

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.90 | 43 | 0.721 | 0.279 | 0.000 | 56.2 | 0.01428 | 0.02570 |
| mid_0.90_1.10 | 97 | 0.845 | 0.155 | 0.000 | 33.7 | 0.01057 | 0.01603 |
| high_>1.10 | 60 | 0.883 | 0.100 | 0.017 | 30.4 | 0.00805 | 0.01475 |

## By Noise

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| high_>=0.00055 | 50 | 0.820 | 0.180 | 0.000 | 40.3 | 0.01076 | 0.01933 |
| mid_0.00025_0.00055 | 75 | 0.813 | 0.173 | 0.013 | 34.2 | 0.01162 | 0.01768 |
| low_<0.00025 | 75 | 0.853 | 0.147 | 0.000 | 39.0 | 0.00950 | 0.01672 |

## Worst Joint Buckets

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2|low_<0.70|mid_0.90_1.10|high_>=0.00055 | 4 | 0.250 | 0.750 | 0.000 | 73.0 | 0.03306 | 0.05169 |
| delay_2|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 7 | 0.714 | 0.286 | 0.000 | 45.1 | 0.01553 | 0.02369 |
| delay_0|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 0.750 | 0.250 | 0.000 | 42.5 | 0.02605 | 0.01707 |
| delay_1|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 4 | 0.750 | 0.250 | 0.000 | 44.2 | 0.01269 | 0.02484 |
| delay_1|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 0.750 | 0.250 | 0.000 | 52.2 | 0.01210 | 0.02552 |
| delay_2|mid_0.70_0.85|high_>1.10|low_<0.00025 | 9 | 0.778 | 0.222 | 0.000 | 34.6 | 0.01251 | 0.01954 |
| delay_1|mid_0.70_0.85|high_>1.10|mid_0.00025_0.00055 | 5 | 0.800 | 0.200 | 0.000 | 36.0 | 0.01063 | 0.02127 |
| delay_0|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 6 | 0.833 | 0.167 | 0.000 | 44.8 | 0.01020 | 0.02027 |
| delay_2|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 9 | 0.889 | 0.111 | 0.000 | 20.9 | 0.00863 | 0.01251 |
| delay_1|high_>=0.85|high_>1.10|mid_0.00025_0.00055 | 4 | 0.750 | 0.000 | 0.250 | 63.5 | 0.01094 | 0.02403 |
| delay_0|low_<0.70|mid_0.90_1.10|mid_0.00025_0.00055 | 7 | 1.000 | 0.000 | 0.000 | 23.3 | 0.00449 | 0.00786 |
| delay_2|high_>=0.85|mid_0.90_1.10|low_<0.00025 | 5 | 1.000 | 0.000 | 0.000 | 28.2 | 0.00361 | 0.00796 |
| delay_0|mid_0.70_0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 18.0 | 0.00451 | 0.00730 |
| delay_0|low_<0.70|mid_0.90_1.10|high_>=0.00055 | 4 | 1.000 | 0.000 | 0.000 | 24.5 | 0.00404 | 0.00814 |
| delay_0|mid_0.70_0.85|high_>1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 12.5 | 0.00393 | 0.00809 |
| delay_2|low_<0.70|mid_0.90_1.10|low_<0.00025 | 4 | 1.000 | 0.000 | 0.000 | 46.0 | 0.00364 | 0.00795 |
| delay_1|low_<0.70|high_>1.10|high_>=0.00055 | 4 | 1.000 | 0.000 | 0.000 | 21.2 | 0.00316 | 0.00808 |

## Suggested Next Data Bias

Prioritize new success-only data around `delay_2`, `low_<0.70`, `low_<0.90`, and `high_>=0.00055`. These buckets currently have the highest collision/timeout rates in the evaluated control-randomization distribution.
