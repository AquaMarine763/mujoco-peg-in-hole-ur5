# Narrow Geometry Curriculum Summary

- Generated: `2026-05-06T14:45:00`
- MuJoCo model path: `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Target narrow geometry: `full_light_geometry` with control channel fixed to identity, `hole_half_size=0.020-0.025`, `peg_radius=0.012`, no hole-center or height jitter.
- Success tolerances: `xy=0.005`, `z=0.01`

## Dataset

The first 50k narrowed-hole dataset was collected with a conservative staged
oracle (`approach_xy_tolerance=0.02`):

| Dataset | Samples | Episodes | Oracle success | Oracle collision |
| --- | ---: | ---: | ---: | ---: |
| `image_expert_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_50k_oracle.npz` | 50000 | 3474 | 0.996 | 0.004 |

## Target Narrow-Geometry Evaluation

| Model | Success | Collision | Interpretation |
| --- | ---: | ---: | --- |
| `balanced_weighted_550k_e6` | 0.210 | 0.680 | Pre-geometry baseline. |
| `narrow_success_600k_e6` | 0.340 | 0.540 | Weighted continuation improves narrow geometry, but not enough. |
| `narrow_only_50k_e12` | 0.450 | 0.440 | Narrow-only continuation gives the best target score but forgets previous skills. |

## Standard Matrix Tradeoff

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| `balanced_weighted_550k_e6` | 0.980 | 0.980 | 0.890 | 0.310 | 0.300 |
| `narrow_success_600k_e6` | 0.950 | 0.990 | 0.850 | 0.350 | 0.390 |
| `narrow_only_50k_e12` | 0.820 | 0.760 | 0.580 | 0.360 | 0.390 |

## Conclusion

The narrowed-hole dataset is valid, and BC does move the policy in the right
direction on the target geometry. However, the policy still collides too often,
and stronger narrow-only training causes serious clean/control forgetting. The
next iteration should not simply increase narrow-hole weight. Prefer either:

- Add a staged geometry curriculum with an intermediate range such as
  `hole_half_size=0.025-0.029` plus `0.020-0.025`, keeping clean/control replay
  strong.
- Improve the image policy/observation for final alignment before narrowing
  further: higher-resolution crop, auxiliary low-dimensional relative pose, or
  a two-stage image policy with a near-hole insertion controller.
