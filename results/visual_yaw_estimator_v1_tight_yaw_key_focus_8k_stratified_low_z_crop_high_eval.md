# Visual Yaw Estimator Eval

- Dataset: `datasets\visual_yaw_v1_tight_yaw_key_focus_8k_stratified_low_z_crop_high.npz`
- Checkpoint: `results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_low_z_crop_high.pt`
- Split: `validation`
- Samples evaluated: `2048`
- Checkpoint best epoch: `35`
- Worst sheet: `results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_low_z_crop_high_eval_worst_key.png`
- Bad threshold: `>15.0 deg`

## Overall

| Samples | Mean deg | P50 deg | P90 deg | P95 deg | Max deg | Bad frac |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2048 | 2.079 | 1.348 | 4.627 | 6.153 | 46.748 | 0.005 |

## Per Profile

| Profile | Samples | Mean deg | P50 deg | P90 deg | P95 deg | Max deg | Bad frac |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `square_square` | 352 | 1.286 | 0.851 | 2.349 | 3.078 | 34.871 | 0.006 |
| `triangle_triangle` | 314 | 1.827 | 1.049 | 3.191 | 4.239 | 46.748 | 0.013 |
| `hex_hex` | 363 | 1.249 | 0.870 | 2.599 | 3.328 | 14.332 | 0.000 |
| `rectangular_key` | 1019 | 2.726 | 2.113 | 5.677 | 7.377 | 23.822 | 0.004 |

## Worst Yaw Bins

| Profile | Bin deg | Samples | Mean deg | P95 deg | Max deg | Bad frac |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `square_square` | 15.0..22.5 | 4 | 11.013 | 30.406 | 34.871 | 0.250 |
| `triangle_triangle` | -40.0..-30.0 | 29 | 2.703 | 12.639 | 37.872 | 0.069 |
| `rectangular_key` | 30.0..60.0 | 40 | 4.670 | 11.454 | 15.642 | 0.050 |
| `rectangular_key` | 90.0..120.0 | 94 | 3.985 | 8.615 | 13.325 | 0.000 |
| `rectangular_key` | 0.0..30.0 | 35 | 3.120 | 8.267 | 11.579 | 0.000 |
| `rectangular_key` | 120.0..150.0 | 99 | 3.429 | 8.021 | 23.822 | 0.010 |
| `rectangular_key` | 60.0..90.0 | 86 | 3.255 | 7.785 | 15.422 | 0.012 |
| `rectangular_key` | -180.0..-150.0 | 89 | 2.825 | 7.031 | 11.990 | 0.000 |
| `hex_hex` | 15.0..20.0 | 21 | 2.136 | 6.968 | 14.332 | 0.000 |
| `triangle_triangle` | 40.0..50.0 | 22 | 3.445 | 6.566 | 39.274 | 0.045 |
| `rectangular_key` | -90.0..-60.0 | 94 | 2.071 | 5.828 | 12.070 | 0.000 |
| `rectangular_key` | -30.0..0.0 | 105 | 2.350 | 5.672 | 12.677 | 0.000 |
| `triangle_triangle` | 10.0..20.0 | 9 | 3.497 | 5.671 | 5.693 | 0.000 |
| `rectangular_key` | 150.0..180.0 | 99 | 2.429 | 5.189 | 6.962 | 0.000 |
| `rectangular_key` | -150.0..-120.0 | 99 | 2.022 | 5.109 | 8.301 | 0.000 |
| `rectangular_key` | -60.0..-30.0 | 95 | 2.075 | 5.077 | 8.449 | 0.000 |
| `triangle_triangle` | 30.0..40.0 | 7 | 3.212 | 5.036 | 5.051 | 0.000 |
| `hex_hex` | -30.0..-25.0 | 42 | 1.261 | 4.847 | 5.532 | 0.000 |
| `rectangular_key` | -120.0..-90.0 | 84 | 1.870 | 4.496 | 14.438 | 0.000 |
| `triangle_triangle` | -50.0..-40.0 | 35 | 2.517 | 4.357 | 46.748 | 0.029 |
| `triangle_triangle` | 0.0..10.0 | 18 | 1.996 | 4.304 | 4.466 | 0.000 |
| `hex_hex` | -25.0..-20.0 | 41 | 1.130 | 4.104 | 4.471 | 0.000 |
| `square_square` | 30.0..37.5 | 18 | 2.058 | 4.088 | 8.064 | 0.000 |
| `hex_hex` | 20.0..25.0 | 46 | 1.448 | 3.804 | 7.748 | 0.000 |

## Worst Samples

| Index | Profile | Target deg | Pred deg | Signed err deg | Abs err deg |
| ---: | --- | ---: | ---: | ---: | ---: |
| 397 | `rectangular_key` | 122.642 | 98.820 | -23.822 | 23.822 |
| 3805 | `rectangular_key` | 47.695 | 32.053 | -15.642 | 15.642 |
| 829 | `rectangular_key` | 60.469 | 45.047 | -15.422 | 15.422 |
| 4765 | `rectangular_key` | 49.695 | 34.416 | -15.279 | 15.279 |
| 3061 | `rectangular_key` | -102.455 | -88.018 | 14.438 | 14.438 |
| 2466 | `rectangular_key` | 109.205 | 122.530 | 13.325 | 13.325 |
| 1050 | `rectangular_key` | 111.067 | 124.063 | 12.996 | 12.996 |
| 6468 | `rectangular_key` | -9.485 | -22.162 | -12.677 | 12.677 |
| 1543 | `rectangular_key` | -64.707 | -76.777 | -12.070 | 12.070 |
| 840 | `rectangular_key` | -170.361 | 177.649 | -11.990 | 11.990 |
| 3888 | `rectangular_key` | -176.534 | 171.831 | -11.636 | 11.636 |
| 1237 | `rectangular_key` | 29.053 | 40.632 | 11.579 | 11.579 |
| 2365 | `rectangular_key` | 43.479 | 32.227 | -11.252 | 11.252 |
| 5467 | `rectangular_key` | 142.376 | 131.833 | -10.544 | 10.544 |
| 4406 | `rectangular_key` | 96.119 | 106.310 | 10.191 | 10.191 |
| 2130 | `rectangular_key` | 108.212 | 118.107 | 9.895 | 9.895 |
| 6258 | `rectangular_key` | 103.051 | 93.446 | -9.605 | 9.605 |
| 5562 | `rectangular_key` | 124.753 | 115.295 | -9.458 | 9.458 |
| 4284 | `rectangular_key` | -13.368 | -22.721 | -9.353 | 9.353 |
| 4075 | `rectangular_key` | 128.231 | 137.521 | 9.290 | 9.290 |
| 1981 | `rectangular_key` | 49.793 | 40.731 | -9.062 | 9.062 |
| 1333 | `rectangular_key` | 52.830 | 43.799 | -9.030 | 9.030 |
| 5725 | `rectangular_key` | 23.184 | 14.188 | -8.997 | 8.997 |
| 6541 | `rectangular_key` | 54.009 | 62.654 | 8.645 | 8.645 |
