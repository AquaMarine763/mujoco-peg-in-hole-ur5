# Control Failure Analysis

- Generated: `2026-05-06T12:52:08`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_success_400k_oracle_e6\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Domain randomization level: `visual_camera_control`
- Episodes: `100`
- Seed: `150000`
- Success tolerances: `xy=0.005`, `z=0.01`

## Overall

| Episodes | Success | Collision | Timeout | Failures | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.700 | 0.300 | 0.000 | 30 | 0.04780 | 0.05740 |

## By Delay

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2 | 100 | 0.700 | 0.300 | 0.000 | 39.5 | 0.01735 | 0.02275 |

## By Filter Alpha

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.70 | 100 | 0.700 | 0.300 | 0.000 | 39.5 | 0.01735 | 0.02275 |

## By Scale

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.90 | 100 | 0.700 | 0.300 | 0.000 | 39.5 | 0.01735 | 0.02275 |

## By Noise

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| high_>=0.00055 | 100 | 0.700 | 0.300 | 0.000 | 39.5 | 0.01735 | 0.02275 |

## Worst Joint Buckets

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2|low_<0.70|low_<0.90|high_>=0.00055 | 100 | 0.700 | 0.300 | 0.000 | 39.5 | 0.01735 | 0.02275 |

## Suggested Next Data Bias

Prioritize new success-only data around `delay_2`, `low_<0.70`, `low_<0.90`, and `high_>=0.00055`. These buckets currently have the highest collision/timeout rates in the evaluated control-randomization distribution.
