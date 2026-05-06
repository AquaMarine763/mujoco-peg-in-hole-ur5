# Geometry Failure Analysis

- Generated: `2026-05-06T16:30:21`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Domain randomization level: `full_light_geometry`
- Episodes: `100`
- Seed: `740000`
- Image size: `100x100`
- Near-hole crop: `False`
- Hole half-size range: `0.02:0.025`
- Peg radius range: `0.012:0.012`

## Overall

| Episodes | Success | Collision | Timeout | Mean final XY | Mean final Z | Mean failure XY | Mean failure Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.340 | 0.580 | 0.090 | 0.04223 | 0.02223 | 0.06195 | 0.02977 |

## Failure Subset

| Subset | Episodes | Mean final XY | Mean min XY | Mean final Z | Mean action Z | Mean action XY norm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| collisions | 58 | 0.06891 | 0.03067 | 0.02944 | 0.00126 | 0.00540 |
| timeouts | 9 | 0.01257 | 0.00330 | 0.03394 | 0.00185 | 0.00536 |

## Failure XY Buckets

| Final XY bucket | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| aligned_<0.005 | 34 | 1.000 | 0.000 | 0.000 |
| near_0.005_0.015 | 7 | 0.000 | 0.000 | 1.000 |
| off_0.015_0.030 | 24 | 0.000 | 0.958 | 0.083 |
| far_>=0.030 | 35 | 0.000 | 1.000 | 0.000 |

## Interpretation

If most collisions have non-trivial final or minimum XY error, the policy is descending or contacting before lateral alignment is robust. That is the target failure mode for a near-hole crop or a two-stage approach/insert controller.
