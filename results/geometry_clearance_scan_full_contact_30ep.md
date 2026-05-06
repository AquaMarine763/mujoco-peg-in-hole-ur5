# Geometry Clearance Scan

- Generated: `2026-05-06T20:58:35`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Episodes per combination: `30`
- Seed: `930000`
- Scenario preset: `full_contact`
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

### full_contact_light

| Tier | no guard | guard blend 0.75 | guard blend 1.0 |
| --- | ---: | ---: | ---: |
| wide_current | 0.500 | 0.633 | 0.633 |
| medium | 0.500 | 0.567 | 0.533 |
| narrow | 0.300 | 0.600 | 0.500 |
| tight | 0.200 | 0.533 | 0.533 |

## Detailed Rows

| Tier | Scenario | Guard | Success | Collision | Timeout | Return | Steps | Guard steps | Final XY | Final Z | Mean clearance |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_contact_light | no_guard | 0.500 | 0.467 | 0.033 | -49.981 | 24.7 | 0.0 | 0.01602 | 0.02666 | 14.9 mm |
| wide_current | full_contact_light | guard_blend_075 | 0.633 | 0.333 | 0.033 | 6.019 | 37.0 | 35.7 | 0.01265 | 0.02575 | 14.9 mm |
| wide_current | full_contact_light | guard_blend_100 | 0.633 | 0.300 | 0.067 | 17.773 | 40.9 | 39.6 | 0.01146 | 0.02724 | 14.9 mm |
| medium | full_contact_light | no_guard | 0.500 | 0.433 | 0.067 | -36.892 | 29.3 | 0.0 | 0.01751 | 0.02726 | 9.9 mm |
| medium | full_contact_light | guard_blend_075 | 0.567 | 0.333 | 0.100 | -0.956 | 49.4 | 48.1 | 0.01289 | 0.03178 | 9.9 mm |
| medium | full_contact_light | guard_blend_100 | 0.533 | 0.333 | 0.133 | -15.507 | 48.6 | 47.3 | 0.01282 | 0.03342 | 9.9 mm |
| narrow | full_contact_light | no_guard | 0.300 | 0.600 | 0.100 | -112.300 | 40.1 | 0.0 | 0.02251 | 0.03297 | 6.9 mm |
| narrow | full_contact_light | guard_blend_075 | 0.600 | 0.333 | 0.067 | -7.806 | 35.5 | 34.3 | 0.01279 | 0.02722 | 6.9 mm |
| narrow | full_contact_light | guard_blend_100 | 0.500 | 0.400 | 0.100 | -43.329 | 50.6 | 49.4 | 0.01359 | 0.03397 | 6.9 mm |
| tight | full_contact_light | no_guard | 0.200 | 0.733 | 0.067 | -182.990 | 37.1 | 0.0 | 0.02557 | 0.03732 | 4.4 mm |
| tight | full_contact_light | guard_blend_075 | 0.533 | 0.467 | 0.000 | -44.846 | 39.9 | 38.7 | 0.01564 | 0.03095 | 4.4 mm |
| tight | full_contact_light | guard_blend_100 | 0.533 | 0.400 | 0.067 | -25.380 | 41.4 | 40.2 | 0.01463 | 0.03192 | 4.4 mm |
