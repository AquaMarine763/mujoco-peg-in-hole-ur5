# Real Camera Frame Recording Summary

- Source: `synthetic_smoke`
- Output directory: `results\real_capture_bundle_session_synthetic_smoke_camera_frames`
- Stats CSV: `results\real_capture_bundle_session_synthetic_smoke_camera_stats.csv`
- Frames: `4`
- Requested frequency: `100.0` Hz
- Warmup frames: `10`

## Metrics

| Metric | Value |
| --- | ---: |
| `frames` | 4 |
| `interval_avg` | 0.0245987667 |
| `interval_max` | 0.0531299 |
| `interval_min` | 0.0103135 |
| `mean_avg` | 127.489974 |
| `mean_max` | 127.505469 |
| `mean_min` | 127.479948 |
| `std_avg` | 75.5281903 |
| `std_max` | 75.5358874 |
| `std_min` | 75.519266 |

## Next Command

```powershell
python scripts\check_real_camera_preflight.py --input results\real_capture_bundle_session_synthetic_smoke_camera_frames --output-dir results\real_camera_preflight_frames --stats-output results\real_camera_preflight_stats.csv --summary-md results\real_camera_preflight_summary.md --width 100 --height 100 --max-frames 20
```
