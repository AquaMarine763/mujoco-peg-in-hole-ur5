# Geometry Failure Analysis

- Generated: `2026-05-06T19:10:01`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_guarded_hard_replay_light_790k_oracle_e2\sac_image_bc.zip`
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
| 100 | 0.340 | 0.660 | 0.000 | 0.02543 | 0.03381 | 0.03657 | 0.04713 |

## Failure Subset

| Subset | Episodes | Mean final XY | Mean min XY | Mean final Z | Mean action Z | Mean action XY norm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| collisions | 66 | 0.03657 | 0.03390 | 0.04713 | 0.00309 | 0.00609 |
| timeouts | 0 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |

## By Delay

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2 | 100 | 0.340 | 0.660 | 0.000 | 14.4 | 0.02543 | 0.03381 |

## By Filter Alpha

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.70 | 100 | 0.340 | 0.660 | 0.000 | 14.4 | 0.02543 | 0.03381 |

## By Scale

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.90 | 36 | 0.500 | 0.500 | 0.000 | 15.2 | 0.02218 | 0.02831 |
| mid_0.90_1.10 | 64 | 0.250 | 0.750 | 0.000 | 14.0 | 0.02725 | 0.03691 |

## By Noise

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low_<0.00025 | 100 | 0.340 | 0.660 | 0.000 | 14.4 | 0.02543 | 0.03381 |

## Worst Joint Buckets

| Bucket | Episodes | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| delay_2|low_<0.70|mid_0.90_1.10|low_<0.00025 | 64 | 0.250 | 0.750 | 0.000 | 14.0 | 0.02725 | 0.03691 |
| delay_2|low_<0.70|low_<0.90|low_<0.00025 | 36 | 0.500 | 0.500 | 0.000 | 15.2 | 0.02218 | 0.02831 |

## Failure XY Buckets

| Final XY bucket | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| aligned_<0.005 | 34 | 1.000 | 0.000 | 0.000 |
| off_0.015_0.030 | 22 | 0.000 | 1.000 | 0.000 |
| far_>=0.030 | 44 | 0.000 | 1.000 | 0.000 |

## Interpretation

If most collisions have non-trivial final or minimum XY error, the policy is descending or contacting before lateral alignment is robust. That is the target failure mode for a near-hole crop or a two-stage approach/insert controller.
