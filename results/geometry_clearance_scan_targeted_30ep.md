# Geometry Clearance Scan

- Generated: `2026-05-06T20:56:50`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Episodes per combination: `30`
- Seed: `930000`
- Scenario preset: `targeted`
- Tier preset: `all`
- Success tolerances: `xy=0.005`, `z=0.01`

## Tier Summary

| Tier | Hole half size | Peg radius | Clearance range |
| --- | ---: | ---: | ---: |
| wide_current | 0.025:0.029 | 0.0115:0.0125 | 12.5-17.5 mm |
| medium | 0.02:0.024 | 0.0115:0.0125 | 7.5-12.5 mm |
| narrow | 0.017:0.021 | 0.0115:0.0125 | 4.5-9.5 mm |
| tight | 0.015:0.018 | 0.0115:0.0125 | 2.5-6.5 mm |

## Success Matrix

### full_light_geometry

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.567 | 0.600 | 0.533 |
| medium | 0.533 | 0.667 | 0.533 |
| narrow | 0.300 | 0.533 | 0.500 |
| tight | 0.200 | 0.467 | 0.433 |

### hard_full_light_bucket

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.200 | 0.400 | 0.333 |
| medium | 0.300 | 0.333 | 0.333 |
| narrow | 0.167 | 0.367 | 0.233 |
| tight | 0.133 | 0.267 | 0.267 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | no_guard | 0.567 | 0.400 | 0.033 | -24.517 | 20.8 | 0.0 | 0.01543 | 0.02597 | 14.9 mm |
| wide_current | full_light_geometry | guard_blend_075 | 0.600 | 0.333 | 0.067 | 7.317 | 38.0 | 36.7 | 0.01290 | 0.02830 | 14.9 mm |
| wide_current | full_light_geometry | guard_blend_100 | 0.533 | 0.333 | 0.133 | 4.611 | 49.1 | 47.8 | 0.01234 | 0.03268 | 14.9 mm |
| wide_current | hard_full_light_bucket | no_guard | 0.200 | 0.800 | 0.000 | -192.194 | 22.4 | 0.0 | 0.02705 | 0.03963 | 15.1 mm |
| wide_current | hard_full_light_bucket | guard_blend_075 | 0.400 | 0.600 | 0.000 | -115.150 | 21.4 | 19.9 | 0.02190 | 0.03240 | 15.1 mm |
| wide_current | hard_full_light_bucket | guard_blend_100 | 0.333 | 0.667 | 0.000 | -151.436 | 13.8 | 12.3 | 0.02326 | 0.03367 | 15.1 mm |
| medium | full_light_geometry | no_guard | 0.533 | 0.400 | 0.067 | -15.242 | 33.0 | 0.0 | 0.01660 | 0.02564 | 9.9 mm |
| medium | full_light_geometry | guard_blend_075 | 0.667 | 0.267 | 0.067 | 21.352 | 35.1 | 33.8 | 0.01158 | 0.02496 | 9.9 mm |
| medium | full_light_geometry | guard_blend_100 | 0.533 | 0.433 | 0.033 | -50.512 | 46.1 | 44.8 | 0.01373 | 0.03273 | 9.9 mm |
| medium | hard_full_light_bucket | no_guard | 0.300 | 0.700 | 0.000 | -164.885 | 11.9 | 0.0 | 0.02663 | 0.03649 | 10.1 mm |
| medium | hard_full_light_bucket | guard_blend_075 | 0.333 | 0.667 | 0.000 | -151.852 | 15.4 | 13.9 | 0.02409 | 0.03567 | 10.1 mm |
| medium | hard_full_light_bucket | guard_blend_100 | 0.333 | 0.667 | 0.000 | -153.943 | 10.3 | 8.7 | 0.02352 | 0.03496 | 10.1 mm |
| narrow | full_light_geometry | no_guard | 0.300 | 0.600 | 0.100 | -118.590 | 39.2 | 0.0 | 0.02148 | 0.03220 | 6.9 mm |
| narrow | full_light_geometry | guard_blend_075 | 0.533 | 0.333 | 0.133 | -14.329 | 42.1 | 40.8 | 0.01362 | 0.03193 | 6.9 mm |
| narrow | full_light_geometry | guard_blend_100 | 0.500 | 0.433 | 0.100 | -47.672 | 47.8 | 46.5 | 0.01432 | 0.03425 | 6.9 mm |
| narrow | hard_full_light_bucket | no_guard | 0.167 | 0.767 | 0.067 | -186.563 | 23.7 | 0.0 | 0.03053 | 0.03794 | 7.1 mm |
| narrow | hard_full_light_bucket | guard_blend_075 | 0.367 | 0.633 | 0.000 | -138.386 | 11.0 | 9.5 | 0.02364 | 0.03349 | 7.1 mm |
| narrow | hard_full_light_bucket | guard_blend_100 | 0.233 | 0.733 | 0.067 | -181.622 | 21.1 | 19.6 | 0.02533 | 0.04175 | 7.1 mm |
| tight | full_light_geometry | no_guard | 0.200 | 0.767 | 0.033 | -195.364 | 31.6 | 0.0 | 0.02550 | 0.03827 | 4.4 mm |
| tight | full_light_geometry | guard_blend_075 | 0.467 | 0.433 | 0.100 | -41.545 | 42.8 | 41.4 | 0.01469 | 0.03422 | 4.4 mm |
| tight | full_light_geometry | guard_blend_100 | 0.433 | 0.500 | 0.067 | -55.343 | 55.3 | 54.0 | 0.01516 | 0.03894 | 4.4 mm |
| tight | hard_full_light_bucket | no_guard | 0.133 | 0.833 | 0.033 | -218.885 | 22.1 | 0.0 | 0.03513 | 0.03896 | 4.6 mm |
| tight | hard_full_light_bucket | guard_blend_075 | 0.267 | 0.733 | 0.000 | -170.062 | 18.8 | 17.2 | 0.02609 | 0.03952 | 4.6 mm |
| tight | hard_full_light_bucket | guard_blend_100 | 0.267 | 0.733 | 0.000 | -175.655 | 13.6 | 12.1 | 0.02508 | 0.03816 | 4.6 mm |
