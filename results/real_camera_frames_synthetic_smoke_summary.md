# Real Camera Frame Recording Summary

- Source: `synthetic_smoke`
- Output directory: `results\real_camera_frames_synthetic_smoke`
- Stats CSV: `results\real_camera_frames_synthetic_smoke_stats.csv`
- Frames: `4`
- Requested frequency: `100.0` Hz
- Warmup frames: `10`

## Metrics

| Metric | Value |
| --- | ---: |
| `frames` | 4 |
| `interval_avg` | 0.0249137667 |
| `interval_max` | 0.0544109 |
| `interval_min` | 0.0100246 |
| `mean_avg` | 127.489974 |
| `mean_max` | 127.505469 |
| `mean_min` | 127.479948 |
| `std_avg` | 75.5281903 |
| `std_max` | 75.5358874 |
| `std_min` | 75.519266 |

## Next Command

```powershell
python scripts\check_real_camera_preflight.py --input results\real_camera_frames_synthetic_smoke --output-dir results\real_camera_preflight_frames --stats-output results\real_camera_preflight_stats.csv --summary-md results\real_camera_preflight_summary.md --width 100 --height 100 --max-frames 20
```
