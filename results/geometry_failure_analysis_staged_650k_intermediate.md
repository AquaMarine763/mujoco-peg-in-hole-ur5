# Geometry Failure Analysis

- Generated: `2026-05-06T16:30:19`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Domain randomization level: `full_light_geometry`
- Episodes: `100`
- Seed: `730000`
- Image size: `100x100`
- Near-hole crop: `False`
- Hole half-size range: `0.025:0.029`
- Peg radius range: `0.012:0.012`

## Overall

| Episodes | Success | Collision | Timeout | Mean final XY | Mean final Z | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.600 | 0.400 | 0.000 | 0.02389 | 0.02007 | 0.05343 | 0.03873 |

## Failure Subset

| Subset | Episodes | Mean final XY | Mean min XY | Mean final Z | Mean action Z | Mean action XY norm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| collisions | 40 | 0.05343 | 0.02208 | 0.03873 | 0.00124 | 0.00551 |
| timeouts | 0 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |

## Failure XY Buckets

| Final XY bucket | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| aligned_<0.005 | 60 | 1.000 | 0.000 | 0.000 |
| off_0.015_0.030 | 25 | 0.000 | 1.000 | 0.000 |
| far_>=0.030 | 15 | 0.000 | 1.000 | 0.000 |

## Interpretation

If most collisions have non-trivial final or minimum XY error, the policy is descending or contacting before lateral alignment is robust. That is the target failure mode for a near-hole crop or a two-stage approach/insert controller.
