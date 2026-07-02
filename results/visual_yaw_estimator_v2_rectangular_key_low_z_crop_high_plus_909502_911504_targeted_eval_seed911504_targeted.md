# Visual Yaw Estimator Eval

- Dataset: `datasets\visual_yaw_key_seed911504_v3_timeout_rollout_targeted_v1.npz`
- Checkpoint: `results\visual_yaw_estimator_v2_rectangular_key_low_z_crop_high_plus_909502_911504_targeted.pt`
- Split: `full`
- Samples evaluated: `83`
- Checkpoint best epoch: `30`
- Worst sheet: `results\visual_yaw_estimator_v2_rectangular_key_low_z_crop_high_plus_909502_911504_targeted_eval_seed911504_targeted_worst.png`
- Bad threshold: `>15.0 deg`

## Overall

| Samples | Mean deg | P50 deg | P90 deg | P95 deg | Max deg | Bad frac |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 83 | 1.885 | 1.351 | 4.272 | 5.095 | 7.496 | 0.000 |

## Per Profile

| Profile | Samples | Mean deg | P50 deg | P90 deg | P95 deg | Max deg | Bad frac |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `rectangular_key` | 83 | 1.885 | 1.351 | 4.272 | 5.095 | 7.496 | 0.000 |

## Worst Yaw Bins

| Profile | Bin deg | Samples | Mean deg | P95 deg | Max deg | Bad frac |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `rectangular_key` | -90.0..-60.0 | 16 | 4.257 | 6.916 | 7.364 | 0.000 |
| `rectangular_key` | -180.0..-150.0 | 16 | 2.031 | 5.079 | 7.496 | 0.000 |
| `rectangular_key` | 0.0..30.0 | 50 | 1.084 | 2.717 | 3.150 | 0.000 |
| `rectangular_key` | -150.0..-120.0 | 1 | 1.648 | 1.648 | 1.648 | 0.000 |

## Worst Samples

| Index | Profile | Target deg | Pred deg | Signed err deg | Abs err deg |
| ---: | --- | ---: | ---: | ---: | ---: |
| 35 | `rectangular_key` | -176.588 | -169.092 | 7.496 | 7.496 |
| 15 | `rectangular_key` | -72.439 | -79.803 | -7.364 | 7.364 |
| 14 | `rectangular_key` | -72.439 | -79.206 | -6.767 | 6.767 |
| 12 | `rectangular_key` | -72.434 | -78.517 | -6.083 | 6.083 |
| 4 | `rectangular_key` | -72.424 | -77.536 | -5.113 | 5.113 |
| 11 | `rectangular_key` | -72.434 | -77.368 | -4.933 | 4.933 |
| 13 | `rectangular_key` | -72.437 | -77.172 | -4.734 | 4.734 |
| 7 | `rectangular_key` | -72.428 | -76.834 | -4.406 | 4.406 |
| 39 | `rectangular_key` | -177.547 | -173.273 | 4.274 | 4.274 |
| 74 | `rectangular_key` | -175.643 | -171.378 | 4.266 | 4.266 |
| 5 | `rectangular_key` | -72.429 | -76.630 | -4.202 | 4.202 |
| 16 | `rectangular_key` | -76.733 | -80.530 | -3.797 | 3.797 |
| 6 | `rectangular_key` | -72.429 | -76.073 | -3.645 | 3.645 |
| 3 | `rectangular_key` | -72.423 | -75.960 | -3.536 | 3.536 |
| 73 | `rectangular_key` | 11.689 | 8.539 | -3.150 | 3.150 |
| 9 | `rectangular_key` | -72.431 | -75.561 | -3.131 | 3.131 |
| 53 | `rectangular_key` | 11.729 | 14.625 | 2.897 | 2.897 |
| 17 | `rectangular_key` | -81.988 | -84.854 | -2.866 | 2.866 |
| 10 | `rectangular_key` | -72.431 | -75.280 | -2.848 | 2.848 |
| 68 | `rectangular_key` | 13.210 | 16.015 | 2.805 | 2.805 |
| 57 | `rectangular_key` | 12.091 | 14.701 | 2.610 | 2.610 |
| 2 | `rectangular_key` | -72.423 | -74.872 | -2.450 | 2.450 |
| 69 | `rectangular_key` | 13.082 | 15.440 | 2.358 | 2.358 |
| 8 | `rectangular_key` | -72.428 | -74.666 | -2.238 | 2.238 |
