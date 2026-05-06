# Geometry Clearance Scan

- Generated: `2026-05-06T23:59:28`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w05_replay_858k_oracle_e2\sac_image_bc.zip`
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
| wide_current | 0.467 | 0.567 | 0.567 |
| medium | 0.433 | 0.533 | 0.500 |

### hard_full_light_bucket

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.333 | 0.433 | 0.400 |
| medium | 0.333 | 0.300 | 0.300 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | no_guard | 0.467 | 0.533 | 0.000 | -86.584 | 15.1 | 0.0 | 0.02028 | 0.02715 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_075 | 0.567 | 0.433 | 0.000 | -37.324 | 27.7 | 25.8 | 0.01759 | 0.02779 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_100 | 0.567 | 0.400 | 0.033 | -28.722 | 30.5 | 28.6 | 0.01740 | 0.02886 | 15.0 mm |
| wide_current | hard_full_light_bucket | no_guard | 0.333 | 0.667 | 0.000 | -143.842 | 14.3 | 0.0 | 0.02652 | 0.03177 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_075 | 0.433 | 0.567 | 0.000 | -105.334 | 15.4 | 13.1 | 0.02460 | 0.03079 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_100 | 0.400 | 0.567 | 0.033 | -109.851 | 21.2 | 19.0 | 0.02492 | 0.03371 | 14.8 mm |
| medium | full_light_geometry | no_guard | 0.433 | 0.567 | 0.000 | -94.031 | 20.9 | 0.0 | 0.02444 | 0.02830 | 10.0 mm |
| medium | full_light_geometry | guard_blend_075 | 0.533 | 0.433 | 0.033 | -42.307 | 30.1 | 27.9 | 0.01941 | 0.02817 | 10.0 mm |
| medium | full_light_geometry | guard_blend_100 | 0.500 | 0.500 | 0.000 | -74.781 | 33.6 | 31.4 | 0.01961 | 0.03112 | 10.0 mm |
| medium | hard_full_light_bucket | no_guard | 0.333 | 0.667 | 0.000 | -150.849 | 12.1 | 0.0 | 0.02850 | 0.03390 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_075 | 0.300 | 0.700 | 0.000 | -162.647 | 15.4 | 12.8 | 0.02773 | 0.03584 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_100 | 0.300 | 0.700 | 0.000 | -167.437 | 9.9 | 7.3 | 0.02852 | 0.03510 | 9.8 mm |
