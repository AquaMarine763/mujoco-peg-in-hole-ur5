# Staged Geometry Curriculum Summary

- Generated: `2026-05-06T16:05:00`
- MuJoCo model path: `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Observation mode: `image`, `100x100`
- Curriculum stages:
  - Intermediate geometry: `hole_half_size=0.025-0.029`, `peg_radius=0.012`
  - Narrow geometry: `hole_half_size=0.020-0.025`, `peg_radius=0.012`
  - Identity control for geometry data and target bucket evaluations.
  - `approach_xy_tolerance=0.02`

## New Dataset

| Dataset | Samples | Episodes | Oracle success | Oracle collision |
| --- | ---: | ---: | ---: | ---: |
| `image_expert_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_50k_oracle.npz` | 50000 | 3214 | 0.996 | 0.000 |

## Target Geometry Buckets

| Model | Intermediate success | Intermediate collision | Narrow success | Narrow collision |
| --- | ---: | ---: | ---: | ---: |
| `balanced_weighted_550k_e6` | 0.310 | 0.660 | 0.180 | 0.690 |
| `intermediate_success_600k_e6` | 0.450 | 0.530 | 0.290 | 0.600 |
| `staged_intermediate_narrow_650k_e5` | 0.510 | 0.470 | 0.330 | 0.550 |

## Standard Matrix

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| `balanced_weighted_550k_e6` | 0.980 | 0.980 | 0.890 | 0.310 | 0.300 |
| `intermediate_success_600k_e6` | 0.950 | 0.970 | 0.870 | 0.370 | 0.410 |
| `staged_intermediate_narrow_650k_e5` | 0.960 | 0.960 | 0.850 | 0.390 | 0.400 |

## Conclusion

The staged geometry curriculum is better than directly adding narrow geometry.
It improves the target intermediate bucket from `0.310` to `0.510`, the narrow
bucket from `0.180` to `0.330`, and default `full_light_geometry` from `0.310`
to `0.390`. However, `visual_camera_control` falls from `0.890` to `0.850`, so
this is a geometry-curriculum candidate, not a replacement for the current
control-focused recommendation.

Next, avoid simply increasing narrow-geometry weight. The remaining failures
are still collision-heavy, so the next useful change is targeted near-hole
visual alignment, such as a crop observation or a two-stage approach/insert
policy, while keeping strong clean/control replay.
