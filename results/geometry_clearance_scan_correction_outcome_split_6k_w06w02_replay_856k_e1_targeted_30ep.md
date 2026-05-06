# Geometry Clearance Scan

- Generated: `2026-05-07T03:13:10`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_outcome_split_6k_w06w02_replay_856k_oracle_e1\sac_image_bc.zip`
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
| wide_current | 0.500 | 0.567 | 0.567 |
| medium | 0.400 | 0.533 | 0.567 |

### hard_full_light_bucket

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.267 | 0.433 | 0.400 |
| medium | 0.333 | 0.267 | 0.300 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | no_guard | 0.500 | 0.500 | 0.000 | -67.061 | 17.8 | 0.0 | 0.01979 | 0.02798 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_075 | 0.567 | 0.433 | 0.000 | -37.450 | 28.0 | 26.1 | 0.01753 | 0.02778 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_100 | 0.567 | 0.400 | 0.033 | -28.665 | 30.4 | 28.5 | 0.01740 | 0.02884 | 15.0 mm |
| wide_current | hard_full_light_bucket | no_guard | 0.267 | 0.733 | 0.000 | -173.875 | 12.7 | 0.0 | 0.02823 | 0.03348 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_075 | 0.433 | 0.567 | 0.000 | -105.038 | 15.6 | 13.4 | 0.02460 | 0.03081 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_100 | 0.400 | 0.567 | 0.033 | -109.679 | 21.1 | 18.8 | 0.02496 | 0.03371 | 14.8 mm |
| medium | full_light_geometry | no_guard | 0.400 | 0.600 | 0.000 | -106.133 | 21.2 | 0.0 | 0.02512 | 0.03053 | 10.0 mm |
| medium | full_light_geometry | guard_blend_075 | 0.533 | 0.433 | 0.033 | -42.024 | 30.5 | 28.3 | 0.01927 | 0.02815 | 10.0 mm |
| medium | full_light_geometry | guard_blend_100 | 0.567 | 0.433 | 0.000 | -50.838 | 23.1 | 20.9 | 0.01842 | 0.02588 | 10.0 mm |
| medium | hard_full_light_bucket | no_guard | 0.333 | 0.667 | 0.000 | -150.460 | 12.8 | 0.0 | 0.02885 | 0.03376 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_075 | 0.267 | 0.733 | 0.000 | -181.643 | 9.6 | 7.1 | 0.02954 | 0.03602 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_100 | 0.300 | 0.700 | 0.000 | -168.089 | 9.8 | 7.3 | 0.02885 | 0.03500 | 9.8 mm |
