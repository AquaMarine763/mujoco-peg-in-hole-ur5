# Geometry Clearance Scan

- Generated: `2026-05-07T00:02:55`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1\sac_image_bc.zip`
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
| wide_current | 0.500 | 0.533 | 0.567 |
| medium | 0.433 | 0.533 | 0.500 |

### hard_full_light_bucket

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.367 | 0.467 | 0.400 |
| medium | 0.333 | 0.300 | 0.300 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | no_guard | 0.500 | 0.500 | 0.000 | -67.610 | 16.5 | 0.0 | 0.01989 | 0.02779 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_075 | 0.533 | 0.467 | 0.000 | -51.869 | 27.4 | 25.5 | 0.01867 | 0.02900 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_100 | 0.567 | 0.400 | 0.033 | -28.594 | 30.6 | 28.7 | 0.01749 | 0.02884 | 15.0 mm |
| wide_current | hard_full_light_bucket | no_guard | 0.367 | 0.633 | 0.000 | -129.823 | 14.4 | 0.0 | 0.02598 | 0.03181 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_075 | 0.467 | 0.533 | 0.000 | -90.788 | 15.5 | 13.3 | 0.02375 | 0.02937 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_100 | 0.400 | 0.567 | 0.033 | -109.611 | 21.1 | 18.8 | 0.02505 | 0.03367 | 14.8 mm |
| medium | full_light_geometry | no_guard | 0.433 | 0.567 | 0.000 | -101.258 | 15.7 | 0.0 | 0.02550 | 0.02912 | 10.0 mm |
| medium | full_light_geometry | guard_blend_075 | 0.533 | 0.433 | 0.033 | -46.276 | 24.6 | 22.4 | 0.02003 | 0.02745 | 10.0 mm |
| medium | full_light_geometry | guard_blend_100 | 0.500 | 0.500 | 0.000 | -76.997 | 28.2 | 26.0 | 0.02034 | 0.03020 | 10.0 mm |
| medium | hard_full_light_bucket | no_guard | 0.333 | 0.667 | 0.000 | -151.101 | 12.7 | 0.0 | 0.02858 | 0.03378 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_075 | 0.300 | 0.700 | 0.000 | -162.923 | 15.3 | 12.8 | 0.02792 | 0.03556 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_100 | 0.300 | 0.700 | 0.000 | -165.066 | 14.7 | 12.1 | 0.02774 | 0.03592 | 9.8 mm |
