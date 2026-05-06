# Geometry Clearance Scan

- Generated: `2026-05-07T03:08:20`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_outcome_split_6k_w04w04_replay_856k_oracle_e1\sac_image_bc.zip`
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
| wide_current | 0.500 | 0.600 | 0.567 |
| medium | 0.400 | 0.533 | 0.533 |

### hard_full_light_bucket

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.333 | 0.433 | 0.400 |
| medium | 0.333 | 0.267 | 0.300 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | no_guard | 0.500 | 0.500 | 0.000 | -67.748 | 17.2 | 0.0 | 0.01978 | 0.02806 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_075 | 0.600 | 0.400 | 0.000 | -22.677 | 28.4 | 26.5 | 0.01675 | 0.02647 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_100 | 0.567 | 0.400 | 0.033 | -28.606 | 30.5 | 28.5 | 0.01740 | 0.02880 | 15.0 mm |
| wide_current | hard_full_light_bucket | no_guard | 0.333 | 0.667 | 0.000 | -143.176 | 14.8 | 0.0 | 0.02621 | 0.03181 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_075 | 0.433 | 0.567 | 0.000 | -104.840 | 15.3 | 13.1 | 0.02443 | 0.03079 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_100 | 0.400 | 0.567 | 0.033 | -110.096 | 21.4 | 19.1 | 0.02482 | 0.03371 | 14.8 mm |
| medium | full_light_geometry | no_guard | 0.400 | 0.600 | 0.000 | -106.872 | 21.6 | 0.0 | 0.02583 | 0.03070 | 10.0 mm |
| medium | full_light_geometry | guard_blend_075 | 0.533 | 0.433 | 0.033 | -42.172 | 30.1 | 27.9 | 0.01929 | 0.02806 | 10.0 mm |
| medium | full_light_geometry | guard_blend_100 | 0.533 | 0.467 | 0.000 | -63.701 | 27.9 | 25.6 | 0.01896 | 0.02828 | 10.0 mm |
| medium | hard_full_light_bucket | no_guard | 0.333 | 0.667 | 0.000 | -151.030 | 12.2 | 0.0 | 0.02934 | 0.03379 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_075 | 0.267 | 0.733 | 0.000 | -181.655 | 9.6 | 7.1 | 0.02951 | 0.03599 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_100 | 0.300 | 0.700 | 0.000 | -168.031 | 9.8 | 7.3 | 0.02882 | 0.03498 | 9.8 mm |
