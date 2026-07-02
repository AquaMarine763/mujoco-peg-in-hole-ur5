# Visual Yaw Estimator Eval

- Dataset: `datasets\visual_yaw_v2_rectangular_key_low_z_crop_high_plus_909502_911504_targeted.npz`
- Checkpoint: `results\visual_yaw_estimator_v2_rectangular_key_low_z_crop_high_plus_909502_911504_targeted.pt`
- Split: `full`
- Samples evaluated: `18444`
- Checkpoint best epoch: `30`
- Worst sheet: `results\visual_yaw_estimator_v2_rectangular_key_low_z_crop_high_plus_909502_911504_targeted_eval_full_worst.png`
- Bad threshold: `>15.0 deg`

## Overall

| Samples | Mean deg | P50 deg | P90 deg | P95 deg | Max deg | Bad frac |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 18444 | 2.474 | 1.602 | 5.891 | 7.500 | 120.911 | 0.004 |

## Per Profile

| Profile | Samples | Mean deg | P50 deg | P90 deg | P95 deg | Max deg | Bad frac |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `square_square` | 2730 | 1.238 | 0.947 | 2.552 | 3.167 | 31.235 | 0.001 |
| `triangle_triangle` | 2730 | 1.752 | 1.357 | 3.383 | 4.372 | 39.800 | 0.004 |
| `hex_hex` | 2730 | 1.116 | 0.864 | 2.265 | 2.915 | 18.841 | 0.002 |
| `rectangular_key` | 10254 | 3.358 | 2.475 | 7.216 | 8.977 | 120.911 | 0.005 |

## Worst Yaw Bins

| Profile | Bin deg | Samples | Mean deg | P95 deg | Max deg | Bad frac |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `triangle_triangle` | 20.0..30.0 | 16 | 6.995 | 16.371 | 16.371 | 0.125 |
| `square_square` | 22.5..30.0 | 28 | 5.043 | 16.091 | 19.937 | 0.071 |
| `rectangular_key` | 90.0..120.0 | 794 | 4.852 | 12.892 | 20.926 | 0.028 |
| `rectangular_key` | 30.0..60.0 | 300 | 4.494 | 11.191 | 21.479 | 0.013 |
| `rectangular_key` | 150.0..180.0 | 746 | 4.328 | 10.411 | 15.699 | 0.003 |
| `square_square` | 15.0..22.5 | 50 | 3.500 | 9.960 | 31.235 | 0.040 |
| `rectangular_key` | -60.0..-30.0 | 738 | 3.955 | 9.277 | 15.903 | 0.005 |
| `rectangular_key` | -90.0..-60.0 | 1110 | 4.069 | 9.257 | 23.297 | 0.002 |
| `rectangular_key` | 120.0..150.0 | 754 | 3.721 | 8.895 | 15.165 | 0.003 |
| `rectangular_key` | 60.0..90.0 | 698 | 3.530 | 8.728 | 18.494 | 0.003 |
| `rectangular_key` | -120.0..-90.0 | 752 | 3.638 | 8.651 | 14.680 | 0.000 |
| `rectangular_key` | -30.0..0.0 | 756 | 3.449 | 8.385 | 120.911 | 0.005 |
| `hex_hex` | 10.0..15.0 | 48 | 2.299 | 7.555 | 18.841 | 0.042 |
| `rectangular_key` | -180.0..-150.0 | 1082 | 2.700 | 7.435 | 11.834 | 0.000 |
| `rectangular_key` | -150.0..-120.0 | 818 | 2.620 | 6.705 | 14.165 | 0.000 |
| `triangle_triangle` | 30.0..40.0 | 40 | 3.166 | 5.649 | 8.515 | 0.000 |
| `triangle_triangle` | -50.0..-40.0 | 354 | 2.056 | 5.339 | 8.815 | 0.000 |
| `triangle_triangle` | 10.0..20.0 | 40 | 2.722 | 5.330 | 6.906 | 0.000 |
| `square_square` | 30.0..37.5 | 102 | 2.139 | 4.805 | 4.971 | 0.000 |
| `square_square` | 7.5..15.0 | 66 | 1.771 | 4.685 | 4.990 | 0.000 |
| `rectangular_key` | 0.0..30.0 | 1706 | 1.695 | 4.622 | 29.878 | 0.007 |
| `triangle_triangle` | 50.0..60.0 | 376 | 1.820 | 4.369 | 6.054 | 0.000 |
| `hex_hex` | 5.0..10.0 | 48 | 1.986 | 4.167 | 17.240 | 0.042 |
| `hex_hex` | 15.0..20.0 | 158 | 1.908 | 4.159 | 11.316 | 0.000 |

## Worst Samples

| Index | Profile | Target deg | Pred deg | Signed err deg | Abs err deg |
| ---: | --- | ---: | ---: | ---: | ---: |
| 8612 | `rectangular_key` | -27.066 | 93.845 | 120.911 | 120.911 |
| 420 | `rectangular_key` | -27.066 | 93.845 | 120.911 | 120.911 |
| 2820 | `rectangular_key` | 18.976 | -10.902 | -29.878 | 29.878 |
| 11012 | `rectangular_key` | 18.976 | -10.902 | -29.878 | 29.878 |
| 9932 | `rectangular_key` | 6.209 | -22.522 | -28.732 | 28.732 |
| 1740 | `rectangular_key` | 6.209 | -22.522 | -28.732 | 28.732 |
| 61 | `rectangular_key` | 29.328 | 52.779 | 23.451 | 23.451 |
| 8253 | `rectangular_key` | 29.328 | 52.779 | 23.451 | 23.451 |
| 3126 | `rectangular_key` | -79.889 | -103.186 | -23.297 | 23.297 |
| 11318 | `rectangular_key` | -79.889 | -103.186 | -23.297 | 23.297 |
| 12141 | `rectangular_key` | 31.651 | 53.130 | 21.479 | 21.479 |
| 3949 | `rectangular_key` | 31.651 | 53.130 | 21.479 | 21.479 |
| 7890 | `rectangular_key` | 104.712 | 125.638 | 20.926 | 20.926 |
| 16082 | `rectangular_key` | 104.712 | 125.638 | 20.926 | 20.926 |
| 15122 | `rectangular_key` | 108.249 | 88.411 | -19.837 | 19.837 |
| 6930 | `rectangular_key` | 108.249 | 88.411 | -19.837 | 19.837 |
| 5366 | `rectangular_key` | 82.910 | 64.416 | -18.494 | 18.494 |
| 13558 | `rectangular_key` | 82.910 | 64.416 | -18.494 | 18.494 |
| 776 | `rectangular_key` | -28.232 | -46.328 | -18.096 | 18.096 |
| 8968 | `rectangular_key` | -28.232 | -46.328 | -18.096 | 18.096 |
| 2102 | `rectangular_key` | 98.775 | 80.736 | -18.039 | 18.039 |
| 10294 | `rectangular_key` | 98.775 | 80.736 | -18.039 | 18.039 |
| 1237 | `rectangular_key` | 29.053 | 46.709 | 17.656 | 17.656 |
| 9429 | `rectangular_key` | 29.053 | 46.709 | 17.656 | 17.656 |
