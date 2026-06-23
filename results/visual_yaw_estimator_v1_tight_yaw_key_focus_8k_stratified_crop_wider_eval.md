# Visual Yaw Estimator Eval

- Dataset: `datasets\visual_yaw_v1_tight_yaw_key_focus_8k_stratified_crop_wider.npz`
- Checkpoint: `results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_crop_wider.pt`
- Split: `validation`
- Samples evaluated: `2048`
- Checkpoint best epoch: `38`
- Worst sheet: `results\visual_yaw_estimator_v1_tight_yaw_key_focus_8k_stratified_crop_wider_eval_worst_key.png`
- Bad threshold: `>15.0 deg`

## Overall

| Samples | Mean deg | P50 deg | P90 deg | P95 deg | Max deg | Bad frac |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2048 | 2.100 | 1.320 | 4.507 | 5.743 | 87.042 | 0.006 |

## Per Profile

| Profile | Samples | Mean deg | P50 deg | P90 deg | P95 deg | Max deg | Bad frac |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `square_square` | 348 | 1.393 | 1.059 | 2.785 | 3.799 | 14.436 | 0.000 |
| `triangle_triangle` | 336 | 1.902 | 1.169 | 3.140 | 5.037 | 50.905 | 0.012 |
| `hex_hex` | 356 | 1.245 | 0.758 | 2.336 | 3.322 | 25.646 | 0.008 |
| `rectangular_key` | 1008 | 2.713 | 1.911 | 5.347 | 6.784 | 87.042 | 0.006 |

## Worst Yaw Bins

| Profile | Bin deg | Samples | Mean deg | P95 deg | Max deg | Bad frac |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `triangle_triangle` | 10.0..20.0 | 8 | 5.977 | 20.543 | 27.709 | 0.125 |
| `square_square` | 15.0..22.5 | 6 | 5.853 | 13.527 | 14.436 | 0.000 |
| `hex_hex` | 5.0..10.0 | 13 | 3.702 | 13.517 | 17.605 | 0.077 |
| `rectangular_key` | 30.0..60.0 | 32 | 6.140 | 12.977 | 22.405 | 0.031 |
| `triangle_triangle` | 30.0..40.0 | 5 | 5.537 | 10.500 | 11.093 | 0.000 |
| `rectangular_key` | 90.0..120.0 | 98 | 3.662 | 10.281 | 27.974 | 0.010 |
| `square_square` | 22.5..30.0 | 1 | 9.583 | 9.583 | 9.583 | 0.000 |
| `triangle_triangle` | 20.0..30.0 | 3 | 5.243 | 8.897 | 9.377 | 0.000 |
| `rectangular_key` | -180.0..-150.0 | 87 | 2.989 | 7.824 | 15.779 | 0.011 |
| `rectangular_key` | 0.0..30.0 | 57 | 3.065 | 6.959 | 24.446 | 0.018 |
| `rectangular_key` | 60.0..90.0 | 84 | 3.283 | 6.904 | 10.954 | 0.000 |
| `rectangular_key` | 120.0..150.0 | 103 | 2.652 | 6.481 | 9.948 | 0.000 |
| `triangle_triangle` | 40.0..50.0 | 17 | 2.667 | 5.901 | 8.355 | 0.000 |
| `square_square` | 7.5..15.0 | 12 | 2.039 | 5.835 | 7.635 | 0.000 |
| `rectangular_key` | 150.0..180.0 | 91 | 2.537 | 5.541 | 6.219 | 0.000 |
| `triangle_triangle` | 50.0..60.0 | 51 | 1.927 | 5.437 | 6.496 | 0.000 |
| `hex_hex` | 15.0..20.0 | 25 | 2.419 | 5.198 | 25.646 | 0.040 |
| `triangle_triangle` | -60.0..-50.0 | 68 | 2.145 | 5.014 | 49.918 | 0.015 |
| `rectangular_key` | -120.0..-90.0 | 77 | 2.002 | 4.976 | 8.537 | 0.000 |
| `square_square` | 37.5..45.0 | 46 | 1.711 | 4.837 | 9.446 | 0.000 |
| `rectangular_key` | -90.0..-60.0 | 107 | 1.982 | 4.798 | 6.320 | 0.000 |
| `rectangular_key` | -60.0..-30.0 | 80 | 2.271 | 4.794 | 20.275 | 0.013 |
| `hex_hex` | 10.0..15.0 | 8 | 2.925 | 4.723 | 4.801 | 0.000 |
| `square_square` | -45.0..-37.5 | 59 | 1.608 | 4.406 | 5.530 | 0.000 |

## Worst Samples

| Index | Profile | Target deg | Pred deg | Signed err deg | Abs err deg |
| ---: | --- | ---: | ---: | ---: | ---: |
| 4969 | `rectangular_key` | -145.960 | 126.998 | -87.042 | 87.042 |
| 6618 | `rectangular_key` | 102.227 | 130.202 | 27.974 | 27.974 |
| 4189 | `rectangular_key` | 27.003 | 51.449 | 24.446 | 24.446 |
| 3949 | `rectangular_key` | 54.100 | 76.505 | 22.405 | 22.405 |
| 7495 | `rectangular_key` | -49.989 | -70.264 | -20.275 | 20.275 |
| 4321 | `rectangular_key` | -151.288 | -167.067 | -15.779 | 15.779 |
| 6733 | `rectangular_key` | 51.197 | 64.212 | 13.015 | 13.015 |
| 6589 | `rectangular_key` | 51.422 | 64.367 | 12.945 | 12.945 |
| 3134 | `rectangular_key` | 91.306 | 104.243 | 12.937 | 12.937 |
| 5725 | `rectangular_key` | 45.019 | 57.321 | 12.302 | 12.302 |
| 3877 | `rectangular_key` | 51.614 | 63.393 | 11.779 | 11.779 |
| 4428 | `rectangular_key` | 39.420 | 50.936 | 11.516 | 11.516 |
| 3450 | `rectangular_key` | 110.695 | 122.070 | 11.375 | 11.375 |
| 5089 | `rectangular_key` | -149.702 | -138.630 | 11.073 | 11.073 |
| 829 | `rectangular_key` | 61.087 | 72.040 | 10.954 | 10.954 |
| 5994 | `rectangular_key` | 101.779 | 112.578 | 10.798 | 10.798 |
| 3997 | `rectangular_key` | 59.313 | 69.861 | 10.548 | 10.548 |
| 7656 | `rectangular_key` | -159.878 | -170.313 | -10.435 | 10.435 |
| 3738 | `rectangular_key` | 109.709 | 99.321 | -10.388 | 10.388 |
| 734 | `rectangular_key` | 98.595 | 108.858 | 10.262 | 10.262 |
| 6085 | `rectangular_key` | 57.850 | 47.723 | -10.126 | 10.126 |
| 4957 | `rectangular_key` | 48.679 | 58.762 | 10.083 | 10.083 |
| 7099 | `rectangular_key` | 132.702 | 122.754 | -9.948 | 9.948 |
| 7165 | `rectangular_key` | 22.128 | 12.579 | -9.549 | 9.549 |
