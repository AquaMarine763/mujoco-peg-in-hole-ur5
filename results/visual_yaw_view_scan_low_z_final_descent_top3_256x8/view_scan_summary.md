# Visual Yaw View Scan

- Samples per candidate: `256`
- Epochs: `8`
- Seed: `914000`
- Candidate group: `final_descent`
- Tip Z-above range: `(0.012, 0.035)`
- Tip XY-offset range: `(0.0, 0.004)`
- Yaw sampling: `stratified` / bins `12`

| Candidate | Cam offset | Crop offset | Crop src | FOV | Best val yaw | Key val yaw | Square val yaw | Triangle val yaw | Hex val yaw |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `crop_wider_high` | `(-0.04, -0.04, 0.0)` | `(-18, -12)` | 80 | 100.0 | 45.093 | 71.740 | 11.887 | 22.954 | 16.259 |
| `open_high` | `(-0.025, -0.045, 0.04)` | `(-10, 0)` | 96 | 110.0 | 50.405 | 79.782 | 8.224 | 20.052 | 11.615 |
| `raise_center_wide` | `(-0.03, -0.04, 0.02)` | `(-10, 0)` | 96 | 110.0 | 55.330 | 88.247 | 11.287 | 20.495 | 11.431 |

Best candidate by key error: `crop_wider_high`
