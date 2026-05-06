# Geometry Failure Analysis

- Generated: `2026-05-06T19:01:26`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Domain randomization level: `full_light_geometry`
- Episodes: `100`
- Seed: `850000`
- Image size: `100x100`
- Near-hole crop: `True`
- Hole half-size range: `0.025:0.029`
- Peg radius range: `0.0115:0.0125`

## Overall

| Episodes | Success | Collision | Timeout | Mean final XY | Mean final Z | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.330 | 0.660 | 0.010 | 0.02576 | 0.03363 | 0.03652 | 0.04630 |

## Failure Subset

| Subset | Episodes | Mean final XY | Mean min XY | Mean final Z | Mean action Z | Mean action XY norm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| collisions | 66 | 0.03684 | 0.03412 | 0.04645 | 0.00304 | 0.00612 |
| timeouts | 1 | 0.01511 | 0.00637 | 0.03626 | 0.00248 | 0.00562 |

## By Delay

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2 | 100 | 0.330 | 0.660 | 0.010 | 15.4 | 0.02576 | 0.03363 |

## By Filter Alpha

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.70 | 100 | 0.330 | 0.660 | 0.010 | 15.4 | 0.02576 | 0.03363 |

## By Scale

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.90 | 36 | 0.417 | 0.556 | 0.028 | 19.5 | 0.02371 | 0.03072 |
| mid_0.90_1.10 | 64 | 0.281 | 0.719 | 0.000 | 13.1 | 0.02691 | 0.03527 |

## By Noise

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.00025 | 100 | 0.330 | 0.660 | 0.010 | 15.4 | 0.02576 | 0.03363 |

## Worst Joint Buckets

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2|low_<0.70|mid_0.90_1.10|low_<0.00025 | 64 | 0.281 | 0.719 | 0.000 | 13.1 | 0.02691 | 0.03527 |
| delay_2|low_<0.70|low_<0.90|low_<0.00025 | 36 | 0.417 | 0.556 | 0.028 | 19.5 | 0.02371 | 0.03072 |

## Failure XY Buckets

| Final XY bucket | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| aligned_<0.005 | 33 | 1.000 | 0.000 | 0.000 |
| off_0.015_0.030 | 26 | 0.000 | 0.962 | 0.038 |
| far_>=0.030 | 41 | 0.000 | 1.000 | 0.000 |

## Interpretation

If most collisions have non-trivial final or minimum XY error, the policy is descending or contacting before lateral alignment is robust. That is the target failure mode for a near-hole crop or a two-stage approach/insert controller.
