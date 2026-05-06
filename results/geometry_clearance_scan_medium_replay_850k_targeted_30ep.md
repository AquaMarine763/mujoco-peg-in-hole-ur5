# Geometry Clearance Scan

- Generated: `2026-05-06T22:18:50`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_850k_oracle_e4\sac_image_bc.zip`
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
| wide_current | 0.467 | 0.567 | 0.567 |
| medium | 0.433 | 0.567 | 0.467 |

### hard_full_light_bucket

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.233 | 0.500 | 0.433 |
| medium | 0.300 | 0.333 | 0.267 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | no_guard | 0.467 | 0.533 | 0.000 | -86.608 | 16.4 | 0.0 | 0.02098 | 0.02846 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_075 | 0.567 | 0.433 | 0.000 | -40.253 | 28.1 | 26.1 | 0.01827 | 0.02784 | 15.0 mm |
| wide_current | full_light_geometry | guard_blend_100 | 0.567 | 0.400 | 0.033 | -29.074 | 30.5 | 28.6 | 0.01763 | 0.02895 | 15.0 mm |
| wide_current | hard_full_light_bucket | no_guard | 0.233 | 0.733 | 0.033 | -177.305 | 17.6 | 0.0 | 0.02844 | 0.03576 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_075 | 0.500 | 0.500 | 0.000 | -77.544 | 17.4 | 15.2 | 0.02330 | 0.02824 | 14.8 mm |
| wide_current | hard_full_light_bucket | guard_blend_100 | 0.433 | 0.533 | 0.033 | -95.881 | 22.0 | 19.8 | 0.02455 | 0.03257 | 14.8 mm |
| medium | full_light_geometry | no_guard | 0.433 | 0.533 | 0.033 | -94.635 | 17.8 | 0.0 | 0.02474 | 0.02709 | 10.0 mm |
| medium | full_light_geometry | guard_blend_075 | 0.567 | 0.400 | 0.033 | -29.991 | 30.6 | 28.4 | 0.01868 | 0.02670 | 10.0 mm |
| medium | full_light_geometry | guard_blend_100 | 0.467 | 0.533 | 0.000 | -86.371 | 39.0 | 36.8 | 0.02043 | 0.03394 | 10.0 mm |
| medium | hard_full_light_bucket | no_guard | 0.300 | 0.667 | 0.033 | -160.821 | 16.3 | 0.0 | 0.02953 | 0.03430 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_075 | 0.333 | 0.667 | 0.000 | -153.322 | 10.2 | 7.9 | 0.02774 | 0.03364 | 9.8 mm |
| medium | hard_full_light_bucket | guard_blend_100 | 0.267 | 0.733 | 0.000 | -182.028 | 9.2 | 6.9 | 0.02913 | 0.03681 | 9.8 mm |
