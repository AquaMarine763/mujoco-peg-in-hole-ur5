# Control Failure Analysis

- Generated: `2026-05-06T14:08:27`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_balanced_weighted_550k_oracle_e6\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Domain randomization level: `visual_camera_control`
- Episodes: `100`
- Seed: `150000`
- Success tolerances: `xy=0.005`, `z=0.01`

## Overall

| Episodes | Success | Collision | Timeout | Failures | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.740 | 0.260 | 0.000 | 26 | 0.04843 | 0.05392 |

## By Delay

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2 | 100 | 0.740 | 0.260 | 0.000 | 34.4 | 0.01564 | 0.01991 |

## By Filter Alpha

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.70 | 100 | 0.740 | 0.260 | 0.000 | 34.4 | 0.01564 | 0.01991 |

## By Scale

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.90 | 100 | 0.740 | 0.260 | 0.000 | 34.4 | 0.01564 | 0.01991 |

## By Noise

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| high_>=0.00055 | 100 | 0.740 | 0.260 | 0.000 | 34.4 | 0.01564 | 0.01991 |

## Worst Joint Buckets

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2|low_<0.70|low_<0.90|high_>=0.00055 | 100 | 0.740 | 0.260 | 0.000 | 34.4 | 0.01564 | 0.01991 |

## Suggested Next Data Bias

Prioritize new success-only data around `delay_2`, `low_<0.70`, `low_<0.90`, and `high_>=0.00055`. These buckets currently have the highest collision/timeout rates in the evaluated control-randomization distribution.
