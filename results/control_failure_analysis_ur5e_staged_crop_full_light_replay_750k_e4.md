# Control Failure Analysis

- Generated: `2026-05-06T17:27:51`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Domain randomization level: `visual_camera_control`
- Episodes: `200`
- Seed: `150000`
- Success tolerances: `xy=0.005`, `z=0.01`

## Overall

| Episodes | Success | Collision | Timeout | Failures | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 200 | 0.845 | 0.155 | 0.000 | 31 | 0.04221 | 0.05350 |

## By Delay

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2 | 72 | 0.750 | 0.250 | 0.000 | 34.1 | 0.01350 | 0.01663 |
| delay_0 | 65 | 0.877 | 0.123 | 0.000 | 31.0 | 0.00855 | 0.01538 |
| delay_1 | 63 | 0.921 | 0.079 | 0.000 | 30.1 | 0.00704 | 0.01243 |

## By Filter Alpha

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.70 | 62 | 0.758 | 0.242 | 0.000 | 39.2 | 0.01297 | 0.02028 |
| high_>=0.85 | 63 | 0.857 | 0.143 | 0.000 | 27.2 | 0.00945 | 0.01196 |
| mid_0.70_0.85 | 75 | 0.907 | 0.093 | 0.000 | 29.6 | 0.00763 | 0.01293 |

## By Scale

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.90 | 43 | 0.674 | 0.326 | 0.000 | 60.6 | 0.01629 | 0.02886 |
| mid_0.90_1.10 | 97 | 0.845 | 0.155 | 0.000 | 24.6 | 0.00991 | 0.01227 |
| high_>1.10 | 60 | 0.967 | 0.033 | 0.000 | 22.8 | 0.00515 | 0.00915 |

## By Noise

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.00025 | 75 | 0.827 | 0.173 | 0.000 | 34.3 | 0.01063 | 0.01579 |
| mid_0.00025_0.00055 | 75 | 0.840 | 0.160 | 0.000 | 28.2 | 0.01014 | 0.01438 |
| high_>=0.00055 | 50 | 0.880 | 0.120 | 0.000 | 33.4 | 0.00827 | 0.01434 |

## Worst Joint Buckets

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 9 | 0.667 | 0.333 | 0.000 | 22.2 | 0.01677 | 0.01190 |
| delay_2|low_<0.70|mid_0.90_1.10|high_>=0.00055 | 4 | 0.750 | 0.250 | 0.000 | 25.8 | 0.01558 | 0.01801 |
| delay_0|low_<0.70|mid_0.90_1.10|high_>=0.00055 | 4 | 0.750 | 0.250 | 0.000 | 42.2 | 0.01287 | 0.02433 |
| delay_2|low_<0.70|mid_0.90_1.10|low_<0.00025 | 4 | 0.750 | 0.250 | 0.000 | 27.2 | 0.01257 | 0.00730 |
| delay_2|mid_0.70_0.85|high_>1.10|low_<0.00025 | 9 | 0.778 | 0.222 | 0.000 | 31.3 | 0.01329 | 0.01706 |
| delay_2|high_>=0.85|mid_0.90_1.10|low_<0.00025 | 5 | 0.800 | 0.200 | 0.000 | 27.4 | 0.01037 | 0.00739 |
| delay_0|low_<0.70|mid_0.90_1.10|mid_0.00025_0.00055 | 7 | 0.857 | 0.143 | 0.000 | 38.0 | 0.00964 | 0.01741 |
| delay_2|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 7 | 0.857 | 0.143 | 0.000 | 32.9 | 0.01069 | 0.01390 |
| delay_0|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 6 | 1.000 | 0.000 | 0.000 | 18.5 | 0.00399 | 0.00786 |
| delay_1|mid_0.70_0.85|high_>1.10|mid_0.00025_0.00055 | 5 | 1.000 | 0.000 | 0.000 | 20.4 | 0.00357 | 0.00831 |
| delay_0|mid_0.70_0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 17.5 | 0.00440 | 0.00785 |
| delay_1|high_>=0.85|high_>1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 19.8 | 0.00464 | 0.00812 |
| delay_0|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 19.0 | 0.00478 | 0.00701 |
| delay_1|mid_0.70_0.85|mid_0.90_1.10|low_<0.00025 | 4 | 1.000 | 0.000 | 0.000 | 22.8 | 0.00365 | 0.00816 |
| delay_0|mid_0.70_0.85|high_>1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 13.5 | 0.00393 | 0.00703 |
| delay_1|high_>=0.85|mid_0.90_1.10|mid_0.00025_0.00055 | 4 | 1.000 | 0.000 | 0.000 | 15.2 | 0.00342 | 0.00687 |
| delay_1|low_<0.70|high_>1.10|high_>=0.00055 | 4 | 1.000 | 0.000 | 0.000 | 27.5 | 0.00339 | 0.00797 |

## Suggested Next Data Bias

Prioritize new success-only data around `delay_2`, `low_<0.70`, `low_<0.90`, and `low_<0.00025`. These buckets currently have the highest collision/timeout rates in the evaluated control-randomization distribution.
