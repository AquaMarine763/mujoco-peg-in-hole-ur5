# Geometry Clearance Scan

- Generated: `2026-05-06T23:14:27`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_medium_2k_replay_852k_oracle_e2\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
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
| medium | 0.400 | 0.500 | 0.467 |

### hard_full_light_bucket

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.300 | 0.433 | 0.400 |
| medium | 0.367 | 0.300 | 0.267 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | no_guard | 0.500 | 0.500 | 0.000 | -72.285 | 13.2 | 0.0 | 0.01928 | 0.02599 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_075 | 0.567 | 0.433 | 0.000 | -37.059 | 27.9 | 26.0 | 0.01685 | 0.02781 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_100 | 0.567 | 0.400 | 0.033 | -28.555 | 30.5 | 28.7 | 0.01682 | 0.02906 | 15.0 mm |
| wide_current | hard_full_light_bucket | no_guard | 0.300 | 0.700 | 0.000 | -160.062 | 12.8 | 0.0 | 0.02699 | 0.03294 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_075 | 0.433 | 0.567 | 0.000 | -105.128 | 15.4 | 13.2 | 0.02425 | 0.03086 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_100 | 0.400 | 0.567 | 0.033 | -109.446 | 21.3 | 19.1 | 0.02458 | 0.03378 | 14.8 mm |
| medium | full_light_geometry | no_guard | 0.400 | 0.567 | 0.033 | -102.352 | 22.4 | 0.0 | 0.02434 | 0.02831 | 10.0 mm |
| medium | full_light_geometry | guard_blend_075 | 0.500 | 0.467 | 0.033 | -57.375 | 29.8 | 27.5 | 0.01972 | 0.02962 | 10.0 mm |
| medium | full_light_geometry | guard_blend_100 | 0.467 | 0.533 | 0.000 | -86.395 | 38.7 | 36.4 | 0.01979 | 0.03385 | 10.0 mm |
| medium | hard_full_light_bucket | no_guard | 0.367 | 0.633 | 0.000 | -134.085 | 15.8 | 0.0 | 0.02606 | 0.03234 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_075 | 0.300 | 0.700 | 0.000 | -162.423 | 15.3 | 13.0 | 0.02651 | 0.03634 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_100 | 0.267 | 0.733 | 0.000 | -177.536 | 14.8 | 12.4 | 0.02703 | 0.03790 | 9.8 mm |
