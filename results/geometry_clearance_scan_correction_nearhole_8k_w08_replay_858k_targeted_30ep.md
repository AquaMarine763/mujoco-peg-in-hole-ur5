# Geometry Clearance Scan

- Generated: `2026-05-06T23:52:09`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e2\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Episodes per combination: `30`
- Seed: `960000`
- Scenario preset: `targeted`
- Tier preset: `wide_medium`
- Success tolerances: `xy=0.005`, `z=0.01`

## Tier Summary

| Tier | Hole half size | Peg radius | Clearance range |
| --- | ---: | ---: | ---: |
| wide_current | 0.025:0.029 | 0.0115:0.0125 | 12.5-17.5 mm |
| medium | 0.02:0.024 | 0.0115:0.0125 | 7.5-12.5 mm |

## Success Matrix

### full_light_geometry

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.533 | 0.600 | 0.533 |
| medium | 0.467 | 0.533 | 0.500 |

### hard_full_light_bucket

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.300 | 0.400 | 0.367 |
| medium | 0.333 | 0.300 | 0.267 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | no_guard | 0.533 | 0.467 | 0.000 | -52.080 | 18.4 | 0.0 | 0.01932 | 0.02670 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_075 | 0.600 | 0.400 | 0.000 | -23.121 | 28.4 | 26.6 | 0.01702 | 0.02660 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_100 | 0.533 | 0.433 | 0.033 | -42.888 | 30.2 | 28.4 | 0.01851 | 0.03030 | 15.0 mm |
| wide_current | hard_full_light_bucket | no_guard | 0.300 | 0.700 | 0.000 | -159.048 | 13.1 | 0.0 | 0.02780 | 0.03304 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_075 | 0.400 | 0.567 | 0.033 | -103.324 | 20.7 | 18.5 | 0.02471 | 0.03352 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_100 | 0.367 | 0.600 | 0.033 | -123.796 | 20.7 | 18.5 | 0.02590 | 0.03504 | 14.8 mm |
| medium | full_light_geometry | no_guard | 0.467 | 0.500 | 0.033 | -75.391 | 19.4 | 0.0 | 0.02421 | 0.02582 | 10.0 mm |
| medium | full_light_geometry | guard_blend_075 | 0.533 | 0.433 | 0.033 | -46.571 | 24.6 | 22.3 | 0.02015 | 0.02730 | 10.0 mm |
| medium | full_light_geometry | guard_blend_100 | 0.500 | 0.500 | 0.000 | -76.933 | 28.2 | 26.0 | 0.02036 | 0.03011 | 10.0 mm |
| medium | hard_full_light_bucket | no_guard | 0.333 | 0.667 | 0.000 | -151.312 | 12.0 | 0.0 | 0.02966 | 0.03371 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_075 | 0.300 | 0.700 | 0.000 | -168.000 | 9.9 | 7.4 | 0.02935 | 0.03485 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_100 | 0.267 | 0.733 | 0.000 | -181.984 | 9.5 | 7.0 | 0.02972 | 0.03637 | 9.8 mm |
