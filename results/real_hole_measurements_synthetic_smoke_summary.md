# UR RTDE Target Measurement Summary

- Output: `results\real_hole_measurements_synthetic_smoke.csv`
- Samples: `6`
- Source: `synthetic_smoke`
- Pose frame: `robot_base`
- Target id: `real_hole`
- Mean target position: `[0.550108028, 0.050014284, 0.650052319]`
- TCP-to-target offset: `[0.000000000, 0.000000000, 0.000000000]`

## Metrics

| Metric | Value |
| --- | ---: |
| `x_max` | 0.550179436 |
| `x_mean` | 0.550108028 |
| `x_min` | 0.55 |
| `x_range` | 0.000179435705 |
| `x_std` | 6.14563766e-05 |
| `xy_radial_error_max` | 0.000151148376 |
| `y_max` | 0.05012 |
| `y_mean` | 0.0500142839 |
| `y_min` | 0.0498890837 |
| `y_range` | 0.000230916285 |
| `y_std` | 8.56195775e-05 |
| `z_max` | 0.650079962 |
| `z_mean` | 0.650052319 |
| `z_min` | 0.65 |
| `z_range` | 7.99620664e-05 |
| `z_std` | 2.8752462e-05 |

## Next Command

```powershell
python scripts\make_real_target_calibration.py --input-csv results\real_hole_measurements_synthetic_smoke.csv --output configs\real_hole_target_calibration.yaml --summary-md results\real_target_calibration_builder_summary.md --target-id real_hole --target-source fixture_calibration --pose-frame robot_base --method mean
```
