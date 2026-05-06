# Geometry Failure Analysis

- Generated: `2026-05-06T17:16:57`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_control_replay_700k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Domain randomization level: `full_light_geometry`
- Episodes: `100`
- Seed: `740000`
- Image size: `100x100`
- Near-hole crop: `True`
- Hole half-size range: `0.02:0.025`
- Peg radius range: `0.012:0.012`

## Overall

| Episodes | Success | Collision | Timeout | Mean final XY | Mean final Z | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.780 | 0.120 | 0.100 | 0.01235 | 0.01212 | 0.04189 | 0.02720 |

## Failure Subset

| Subset | Episodes | Mean final XY | Mean min XY | Mean final Z | Mean action Z | Mean action XY norm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| collisions | 12 | 0.06692 | 0.03221 | 0.02521 | 0.00059 | 0.00521 |
| timeouts | 10 | 0.01185 | 0.00310 | 0.02959 | 0.00148 | 0.00483 |

## Failure XY Buckets

| Final XY bucket | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| aligned_<0.005 | 78 | 1.000 | 0.000 | 0.000 |
| near_0.005_0.015 | 9 | 0.000 | 0.000 | 1.000 |
| off_0.015_0.030 | 5 | 0.000 | 0.800 | 0.200 |
| far_>=0.030 | 8 | 0.000 | 1.000 | 0.000 |

## Interpretation

If most collisions have non-trivial final or minimum XY error, the policy is descending or contacting before lateral alignment is robust. That is the target failure mode for a near-hole crop or a two-stage approach/insert controller.
