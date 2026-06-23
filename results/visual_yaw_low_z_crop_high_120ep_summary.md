# Low-Z Crop-High Visual Yaw 120ep Summary

- Config: `configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_eval.yaml`
- Estimator: `results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_low_z_crop_high.pt`
- Runtime change: `near_hole_crop_offset: [-18, -12]`; wrist camera pose unchanged.
- Baseline reference: visible-brake historical `104/120`, collision `0/120`, timeout `16/120`.
- Result: `111/120`, collision `0/120`, timeout `9/120`, success rate `0.925`.
- Interpretation: low-Z crop-high improves the same six-seed rectangular-key guarded evaluation, but remaining failures are still timeout/wrong-yaw-basin style rather than collision failures.

| Base seed | Episodes | Success | Collision | Timeout | Success rate | Mean steps | Mean final yaw deg | Mean min XY |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 906500 | 20 | 18 | 0 | 2 | 0.9 | 405.7 | 19.184 | 0.00455 |
| 907500 | 20 | 20 | 0 | 0 | 1 | 318.6 | 1.542 | 0.00034 |
| 908500 | 20 | 20 | 0 | 0 | 1 | 342.2 | 2.24 | 0.00044 |
| 909500 | 20 | 17 | 0 | 3 | 0.85 | 410.8 | 12.198 | 0.00344 |
| 910500 | 20 | 19 | 0 | 1 | 0.95 | 346.6 | 10.906 | 0.00343 |
| 911500 | 20 | 17 | 0 | 3 | 0.85 | 439.1 | 27.515 | 0.00101 |
| **Total** | **120** | **111** | **0** | **9** | **0.925** | **377.2** | **12.264** | **0.0022** |

Source episode CSVs are intentionally not duplicated here; use the `source` column in the CSV summary for exact file provenance.
