# Geometry Clearance Scan

- Generated: `2026-05-06T23:54:34`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
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
| wide_current | 0.533 | 0.533 | 0.533 |
| medium | 0.400 | 0.533 | 0.500 |

### hard_full_light_bucket

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.333 | 0.467 | 0.400 |
| medium | 0.367 | 0.300 | 0.300 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | no_guard | 0.533 | 0.467 | 0.000 | -49.423 | 21.8 | 0.0 | 0.01892 | 0.02537 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_075 | 0.533 | 0.433 | 0.033 | -33.114 | 33.8 | 31.9 | 0.01745 | 0.03048 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_100 | 0.533 | 0.400 | 0.067 | -26.185 | 36.1 | 34.2 | 0.01735 | 0.03181 | 15.0 mm |
| wide_current | hard_full_light_bucket | no_guard | 0.333 | 0.667 | 0.000 | -141.710 | 15.3 | 0.0 | 0.02642 | 0.03263 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_075 | 0.467 | 0.533 | 0.000 | -90.238 | 15.8 | 13.5 | 0.02314 | 0.02948 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_100 | 0.400 | 0.567 | 0.033 | -109.946 | 21.4 | 19.1 | 0.02462 | 0.03375 | 14.8 mm |
| medium | full_light_geometry | no_guard | 0.400 | 0.567 | 0.033 | -100.186 | 23.0 | 0.0 | 0.02509 | 0.02838 | 10.0 mm |
| medium | full_light_geometry | guard_blend_075 | 0.533 | 0.433 | 0.033 | -42.620 | 30.1 | 27.9 | 0.01912 | 0.02808 | 10.0 mm |
| medium | full_light_geometry | guard_blend_100 | 0.500 | 0.500 | 0.000 | -74.171 | 33.8 | 31.6 | 0.01937 | 0.03149 | 10.0 mm |
| medium | hard_full_light_bucket | no_guard | 0.367 | 0.633 | 0.000 | -137.039 | 12.6 | 0.0 | 0.02802 | 0.03237 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_075 | 0.300 | 0.700 | 0.000 | -167.628 | 10.1 | 7.6 | 0.02863 | 0.03480 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_100 | 0.300 | 0.700 | 0.000 | -167.663 | 9.8 | 7.3 | 0.02852 | 0.03500 | 9.8 mm |
