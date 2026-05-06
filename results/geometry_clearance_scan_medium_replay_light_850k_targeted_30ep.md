# Geometry Clearance Scan

- Generated: `2026-05-06T22:26:07`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2\sac_image_bc.zip`
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
| wide_current | 0.533 | 0.533 | 0.567 |
| medium | 0.433 | 0.533 | 0.500 |

### hard_full_light_bucket

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.233 | 0.467 | 0.433 |
| medium | 0.300 | 0.300 | 0.300 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | no_guard | 0.533 | 0.467 | 0.000 | -57.035 | 19.7 | 0.0 | 0.01928 | 0.02586 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_075 | 0.533 | 0.467 | 0.000 | -49.919 | 31.1 | 29.2 | 0.01826 | 0.02993 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_100 | 0.567 | 0.400 | 0.033 | -28.906 | 30.5 | 28.6 | 0.01749 | 0.02894 | 15.0 mm |
| wide_current | hard_full_light_bucket | no_guard | 0.233 | 0.767 | 0.000 | -191.933 | 11.5 | 0.0 | 0.02888 | 0.03372 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_075 | 0.467 | 0.533 | 0.000 | -91.350 | 16.5 | 14.2 | 0.02364 | 0.02937 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_100 | 0.433 | 0.533 | 0.033 | -95.425 | 21.7 | 19.5 | 0.02452 | 0.03258 | 14.8 mm |
| medium | full_light_geometry | no_guard | 0.433 | 0.567 | 0.000 | -97.552 | 17.0 | 0.0 | 0.02505 | 0.02867 | 10.0 mm |
| medium | full_light_geometry | guard_blend_075 | 0.533 | 0.433 | 0.033 | -43.626 | 30.1 | 27.9 | 0.01959 | 0.02793 | 10.0 mm |
| medium | full_light_geometry | guard_blend_100 | 0.500 | 0.500 | 0.000 | -72.366 | 34.8 | 32.5 | 0.01971 | 0.03114 | 10.0 mm |
| medium | hard_full_light_bucket | no_guard | 0.300 | 0.667 | 0.033 | -160.301 | 16.8 | 0.0 | 0.02973 | 0.03418 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_075 | 0.300 | 0.700 | 0.000 | -168.203 | 10.0 | 7.5 | 0.02933 | 0.03457 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_100 | 0.300 | 0.700 | 0.000 | -168.015 | 9.7 | 7.1 | 0.02900 | 0.03487 | 9.8 mm |
