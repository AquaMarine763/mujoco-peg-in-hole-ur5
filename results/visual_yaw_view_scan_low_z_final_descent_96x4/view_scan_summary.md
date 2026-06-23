# Visual Yaw View Scan

- Samples per candidate: `96`
- Epochs: `4`
- Seed: `913000`
- Candidate group: `final_descent`
- Tip Z-above range: `(0.012, 0.035)`
- Tip XY-offset range: `(0.0, 0.004)`
- Yaw sampling: `stratified` / bins `12`

| Candidate | Cam offset | Crop offset | Crop src | FOV | Best val yaw | Key val yaw | Square val yaw | Triangle val yaw | Hex val yaw |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `crop_wider_high` | `(-0.04, -0.04, 0.0)` | `(-18, -12)` | 80 | 100.0 | 30.227 | 59.575 | 15.973 | 16.853 | 11.385 |
| `open_high` | `(-0.025, -0.045, 0.04)` | `(-10, 0)` | 96 | 110.0 | 39.733 | 69.712 | 5.158 | 10.678 | 12.045 |
| `raise_center_wide` | `(-0.03, -0.04, 0.02)` | `(-10, 0)` | 96 | 110.0 | 45.941 | 72.748 | 13.609 | 15.889 | 12.548 |
| `raise_center` | `(-0.03, -0.04, 0.02)` | `(-14, 0)` | 80 | 100.0 | 41.821 | 82.181 | 11.916 | 10.791 | 14.221 |
| `crop_wider_low` | `(-0.04, -0.04, 0.0)` | `(-18, 12)` | 80 | 100.0 | 45.332 | 82.547 | 18.875 | 22.390 | 16.241 |
| `crop_wider` | `(-0.04, -0.04, 0.0)` | `(-18, 0)` | 80 | 100.0 | 58.251 | 83.286 | 18.354 | 13.762 | 17.467 |
| `crop_wider_centered` | `(-0.04, -0.04, 0.0)` | `(-10, 0)` | 80 | 100.0 | 66.943 | 99.962 | 40.262 | 45.163 | 20.147 |

Best candidate by key error: `crop_wider_high`
