# Geometry Failure Analysis

- Generated: `2026-05-06T16:55:25`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip`
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
| 100 | 0.830 | 0.150 | 0.020 | 0.01151 | 0.01203 | 0.04806 | 0.03373 |

## Failure Subset

| Subset | Episodes | Mean final XY | Mean min XY | Mean final Z | Mean action Z | Mean action XY norm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| collisions | 15 | 0.05309 | 0.02589 | 0.03565 | 0.00113 | 0.00490 |
| timeouts | 2 | 0.01040 | 0.00081 | 0.01932 | 0.00296 | 0.00535 |

## Failure XY Buckets

| Final XY bucket | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| aligned_<0.005 | 83 | 1.000 | 0.000 | 0.000 |
| near_0.005_0.015 | 2 | 0.000 | 0.000 | 1.000 |
| off_0.015_0.030 | 7 | 0.000 | 1.000 | 0.000 |
| far_>=0.030 | 8 | 0.000 | 1.000 | 0.000 |

## Interpretation

If most collisions have non-trivial final or minimum XY error, the policy is descending or contacting before lateral alignment is robust. That is the target failure mode for a near-hole crop or a two-stage approach/insert controller.
