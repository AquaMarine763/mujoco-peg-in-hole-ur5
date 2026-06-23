# Shape Yaw Sensitivity Scan

This is an analytic 2D cross-section scan. It does not use visual-only debug highlights
and does not run the policy. The purpose is to pick clearances where yaw alignment
becomes necessary before building the visual yaw estimator and guarded yaw-align phase.

A `discriminative` clearance means all tested small yaw errors pass while all tested
large yaw errors fail under the configured good/bad yaw thresholds.

## Summary

| profile | clearance mm | discriminative | max passing yaw deg | min failing yaw deg |
|---|---:|---:|---:|---:|
| hex_hex | 0.25 | True | 2.00 | 3.00 |
| hex_hex | 0.50 | True | 5.00 | 8.00 |
| hex_hex | 0.75 | False | 8.00 | 10.00 |
| hex_hex | 1.00 | False | 10.00 | 15.00 |
| hex_hex | 1.50 | False | 15.00 | nan |
| hex_hex | 2.00 | False | 15.00 | nan |
| hex_hex | 3.00 | False | 15.00 | nan |
| hex_hex | 4.00 | False | 15.00 | nan |
| rectangular_key | 0.25 | False | 0.00 | 1.00 |
| rectangular_key | 0.50 | False | 1.00 | 2.00 |
| rectangular_key | 0.75 | True | 2.00 | 3.00 |
| rectangular_key | 1.00 | True | 3.00 | 5.00 |
| rectangular_key | 1.50 | True | 3.00 | 5.00 |
| rectangular_key | 2.00 | True | 5.00 | 8.00 |
| rectangular_key | 3.00 | False | 8.00 | 10.00 |
| rectangular_key | 4.00 | False | 10.00 | 15.00 |
| square_square | 0.25 | False | 1.00 | 2.00 |
| square_square | 0.50 | True | 2.00 | 3.00 |
| square_square | 0.75 | True | 3.00 | 5.00 |
| square_square | 1.00 | True | 3.00 | 5.00 |
| square_square | 1.50 | True | 5.00 | 8.00 |
| square_square | 2.00 | False | 10.00 | 15.00 |
| square_square | 3.00 | False | 15.00 | nan |
| square_square | 4.00 | False | 15.00 | nan |
| triangle_triangle | 0.25 | False | 1.00 | 2.00 |
| triangle_triangle | 0.50 | True | 2.00 | 3.00 |
| triangle_triangle | 0.75 | True | 3.00 | 5.00 |
| triangle_triangle | 1.00 | True | 5.00 | 8.00 |
| triangle_triangle | 1.50 | False | 8.00 | 10.00 |
| triangle_triangle | 2.00 | False | 10.00 | 15.00 |
| triangle_triangle | 3.00 | False | 15.00 | nan |
| triangle_triangle | 4.00 | False | 15.00 | nan |

## Detailed Rows

| profile | clearance mm | yaw error deg | pass | min margin mm | period deg |
|---|---:|---:|---:|---:|---:|
| rectangular_key | 0.25 | 0.00 | True | 0.077 | 360 |
| rectangular_key | 0.25 | 1.00 | False | -0.072 | 360 |
| rectangular_key | 0.25 | 2.00 | False | -0.393 | 360 |
| rectangular_key | 0.25 | 3.00 | False | -0.711 | 360 |
| rectangular_key | 0.25 | 5.00 | False | -1.343 | 360 |
| rectangular_key | 0.25 | 8.00 | False | -2.276 | 360 |
| rectangular_key | 0.25 | 10.00 | False | -2.887 | 360 |
| rectangular_key | 0.25 | 15.00 | False | -4.368 | 360 |
| rectangular_key | 0.50 | 0.00 | True | 0.154 | 360 |
| rectangular_key | 0.50 | 1.00 | True | 0.069 | 360 |
| rectangular_key | 0.50 | 2.00 | False | -0.143 | 360 |
| rectangular_key | 0.50 | 3.00 | False | -0.461 | 360 |
| rectangular_key | 0.50 | 5.00 | False | -1.093 | 360 |
| rectangular_key | 0.50 | 8.00 | False | -2.026 | 360 |
| rectangular_key | 0.50 | 10.00 | False | -2.637 | 360 |
| rectangular_key | 0.50 | 15.00 | False | -4.118 | 360 |
| rectangular_key | 0.75 | 0.00 | True | 0.193 | 360 |
| rectangular_key | 0.75 | 1.00 | True | 0.143 | 360 |
| rectangular_key | 0.75 | 2.00 | True | 0.106 | 360 |
| rectangular_key | 0.75 | 3.00 | False | -0.211 | 360 |
| rectangular_key | 0.75 | 5.00 | False | -0.843 | 360 |
| rectangular_key | 0.75 | 8.00 | False | -1.776 | 360 |
| rectangular_key | 0.75 | 10.00 | False | -2.387 | 360 |
| rectangular_key | 0.75 | 15.00 | False | -3.868 | 360 |
| rectangular_key | 1.00 | 0.00 | True | 0.230 | 360 |
| rectangular_key | 1.00 | 1.00 | True | 0.219 | 360 |
| rectangular_key | 1.00 | 2.00 | True | 0.143 | 360 |
| rectangular_key | 1.00 | 3.00 | True | 0.039 | 360 |
| rectangular_key | 1.00 | 5.00 | False | -0.593 | 360 |
| rectangular_key | 1.00 | 8.00 | False | -1.526 | 360 |
| rectangular_key | 1.00 | 10.00 | False | -2.137 | 360 |
| rectangular_key | 1.00 | 15.00 | False | -3.618 | 360 |
| rectangular_key | 1.50 | 0.00 | True | 0.369 | 360 |
| rectangular_key | 1.50 | 1.00 | True | 0.316 | 360 |
| rectangular_key | 1.50 | 2.00 | True | 0.281 | 360 |
| rectangular_key | 1.50 | 3.00 | True | 0.221 | 360 |
| rectangular_key | 1.50 | 5.00 | False | -0.093 | 360 |
| rectangular_key | 1.50 | 8.00 | False | -1.026 | 360 |
| rectangular_key | 1.50 | 10.00 | False | -1.637 | 360 |
| rectangular_key | 1.50 | 15.00 | False | -3.118 | 360 |
| rectangular_key | 2.00 | 0.00 | True | 0.492 | 360 |
| rectangular_key | 2.00 | 1.00 | True | 0.429 | 360 |
| rectangular_key | 2.00 | 2.00 | True | 0.405 | 360 |
| rectangular_key | 2.00 | 3.00 | True | 0.340 | 360 |
| rectangular_key | 2.00 | 5.00 | True | 0.252 | 360 |
| rectangular_key | 2.00 | 8.00 | False | -0.526 | 360 |
| rectangular_key | 2.00 | 10.00 | False | -1.137 | 360 |
| rectangular_key | 2.00 | 15.00 | False | -2.618 | 360 |
| rectangular_key | 3.00 | 0.00 | True | 0.720 | 360 |
| rectangular_key | 3.00 | 1.00 | True | 0.693 | 360 |
| rectangular_key | 3.00 | 2.00 | True | 0.631 | 360 |
| rectangular_key | 3.00 | 3.00 | True | 0.597 | 360 |
| rectangular_key | 3.00 | 5.00 | True | 0.484 | 360 |
| rectangular_key | 3.00 | 8.00 | True | 0.331 | 360 |
| rectangular_key | 3.00 | 10.00 | False | -0.137 | 360 |
| rectangular_key | 3.00 | 15.00 | False | -1.618 | 360 |
| rectangular_key | 4.00 | 0.00 | True | 1.001 | 360 |
| rectangular_key | 4.00 | 1.00 | True | 0.917 | 360 |
| rectangular_key | 4.00 | 2.00 | True | 0.913 | 360 |
| rectangular_key | 4.00 | 3.00 | True | 0.828 | 360 |
| rectangular_key | 4.00 | 5.00 | True | 0.738 | 360 |
| rectangular_key | 4.00 | 8.00 | True | 0.559 | 360 |
| rectangular_key | 4.00 | 10.00 | True | 0.469 | 360 |
| rectangular_key | 4.00 | 15.00 | False | -0.618 | 360 |
| square_square | 0.25 | 0.00 | True | 0.250 | 90 |
| square_square | 0.25 | 1.00 | True | 0.042 | 90 |
| square_square | 0.25 | 2.00 | False | -0.161 | 90 |
| square_square | 0.25 | 3.00 | False | -0.362 | 90 |
| square_square | 0.25 | 5.00 | False | -0.750 | 90 |
| square_square | 0.25 | 8.00 | False | -1.303 | 90 |
| square_square | 0.25 | 10.00 | False | -1.651 | 90 |
| square_square | 0.25 | 15.00 | False | -2.447 | 90 |
| square_square | 0.50 | 0.00 | True | 0.500 | 90 |
| square_square | 0.50 | 1.00 | True | 0.292 | 90 |
| square_square | 0.50 | 2.00 | True | 0.089 | 90 |
| square_square | 0.50 | 3.00 | False | -0.112 | 90 |
| square_square | 0.50 | 5.00 | False | -0.500 | 90 |
| square_square | 0.50 | 8.00 | False | -1.053 | 90 |
| square_square | 0.50 | 10.00 | False | -1.401 | 90 |
| square_square | 0.50 | 15.00 | False | -2.197 | 90 |
| square_square | 0.75 | 0.00 | True | 0.750 | 90 |
| square_square | 0.75 | 1.00 | True | 0.542 | 90 |
| square_square | 0.75 | 2.00 | True | 0.339 | 90 |
| square_square | 0.75 | 3.00 | True | 0.138 | 90 |
| square_square | 0.75 | 5.00 | False | -0.250 | 90 |
| square_square | 0.75 | 8.00 | False | -0.803 | 90 |
| square_square | 0.75 | 10.00 | False | -1.151 | 90 |
| square_square | 0.75 | 15.00 | False | -1.947 | 90 |
| square_square | 1.00 | 0.00 | True | 1.000 | 90 |
| square_square | 1.00 | 1.00 | True | 0.792 | 90 |
| square_square | 1.00 | 2.00 | True | 0.589 | 90 |
| square_square | 1.00 | 3.00 | True | 0.388 | 90 |
| square_square | 1.00 | 5.00 | False | -0.000 | 90 |
| square_square | 1.00 | 8.00 | False | -0.553 | 90 |
| square_square | 1.00 | 10.00 | False | -0.901 | 90 |
| square_square | 1.00 | 15.00 | False | -1.697 | 90 |
| square_square | 1.50 | 0.00 | True | 1.500 | 90 |
| square_square | 1.50 | 1.00 | True | 1.292 | 90 |
| square_square | 1.50 | 2.00 | True | 1.089 | 90 |
| square_square | 1.50 | 3.00 | True | 0.888 | 90 |
| square_square | 1.50 | 5.00 | True | 0.500 | 90 |
| square_square | 1.50 | 8.00 | False | -0.053 | 90 |
| square_square | 1.50 | 10.00 | False | -0.401 | 90 |
| square_square | 1.50 | 15.00 | False | -1.197 | 90 |
| square_square | 2.00 | 0.00 | True | 2.000 | 90 |
| square_square | 2.00 | 1.00 | True | 1.792 | 90 |
| square_square | 2.00 | 2.00 | True | 1.589 | 90 |
| square_square | 2.00 | 3.00 | True | 1.388 | 90 |
| square_square | 2.00 | 5.00 | True | 1.000 | 90 |
| square_square | 2.00 | 8.00 | True | 0.447 | 90 |
| square_square | 2.00 | 10.00 | True | 0.099 | 90 |
| square_square | 2.00 | 15.00 | False | -0.697 | 90 |
| square_square | 3.00 | 0.00 | True | 3.000 | 90 |
| square_square | 3.00 | 1.00 | True | 2.792 | 90 |
| square_square | 3.00 | 2.00 | True | 2.589 | 90 |
| square_square | 3.00 | 3.00 | True | 2.388 | 90 |
| square_square | 3.00 | 5.00 | True | 2.000 | 90 |
| square_square | 3.00 | 8.00 | True | 1.447 | 90 |
| square_square | 3.00 | 10.00 | True | 1.099 | 90 |
| square_square | 3.00 | 15.00 | True | 0.303 | 90 |
| square_square | 4.00 | 0.00 | True | 4.000 | 90 |
| square_square | 4.00 | 1.00 | True | 3.792 | 90 |
| square_square | 4.00 | 2.00 | True | 3.589 | 90 |
| square_square | 4.00 | 3.00 | True | 3.388 | 90 |
| square_square | 4.00 | 5.00 | True | 3.000 | 90 |
| square_square | 4.00 | 8.00 | True | 2.447 | 90 |
| square_square | 4.00 | 10.00 | True | 2.099 | 90 |
| square_square | 4.00 | 15.00 | True | 1.303 | 90 |
| triangle_triangle | 0.25 | 0.00 | True | 0.250 | 120 |
| triangle_triangle | 0.25 | 1.00 | True | 0.070 | 120 |
| triangle_triangle | 0.25 | 2.00 | False | -0.109 | 120 |
| triangle_triangle | 0.25 | 3.00 | False | -0.286 | 120 |
| triangle_triangle | 0.25 | 5.00 | False | -0.633 | 120 |
| triangle_triangle | 0.25 | 8.00 | False | -1.138 | 120 |
| triangle_triangle | 0.25 | 10.00 | False | -1.463 | 120 |
| triangle_triangle | 0.25 | 15.00 | False | -2.235 | 120 |
| triangle_triangle | 0.50 | 0.00 | True | 0.500 | 120 |
| triangle_triangle | 0.50 | 1.00 | True | 0.320 | 120 |
| triangle_triangle | 0.50 | 2.00 | True | 0.141 | 120 |
| triangle_triangle | 0.50 | 3.00 | False | -0.036 | 120 |
| triangle_triangle | 0.50 | 5.00 | False | -0.383 | 120 |
| triangle_triangle | 0.50 | 8.00 | False | -0.888 | 120 |
| triangle_triangle | 0.50 | 10.00 | False | -1.213 | 120 |
| triangle_triangle | 0.50 | 15.00 | False | -1.985 | 120 |
| triangle_triangle | 0.75 | 0.00 | True | 0.750 | 120 |
| triangle_triangle | 0.75 | 1.00 | True | 0.570 | 120 |
| triangle_triangle | 0.75 | 2.00 | True | 0.391 | 120 |
| triangle_triangle | 0.75 | 3.00 | True | 0.214 | 120 |
| triangle_triangle | 0.75 | 5.00 | False | -0.133 | 120 |
| triangle_triangle | 0.75 | 8.00 | False | -0.638 | 120 |
| triangle_triangle | 0.75 | 10.00 | False | -0.963 | 120 |
| triangle_triangle | 0.75 | 15.00 | False | -1.735 | 120 |
| triangle_triangle | 1.00 | 0.00 | True | 1.000 | 120 |
| triangle_triangle | 1.00 | 1.00 | True | 0.820 | 120 |
| triangle_triangle | 1.00 | 2.00 | True | 0.641 | 120 |
| triangle_triangle | 1.00 | 3.00 | True | 0.464 | 120 |
| triangle_triangle | 1.00 | 5.00 | True | 0.117 | 120 |
| triangle_triangle | 1.00 | 8.00 | False | -0.388 | 120 |
| triangle_triangle | 1.00 | 10.00 | False | -0.713 | 120 |
| triangle_triangle | 1.00 | 15.00 | False | -1.485 | 120 |
| triangle_triangle | 1.50 | 0.00 | True | 1.500 | 120 |
| triangle_triangle | 1.50 | 1.00 | True | 1.320 | 120 |
| triangle_triangle | 1.50 | 2.00 | True | 1.141 | 120 |
| triangle_triangle | 1.50 | 3.00 | True | 0.964 | 120 |
| triangle_triangle | 1.50 | 5.00 | True | 0.617 | 120 |
| triangle_triangle | 1.50 | 8.00 | True | 0.112 | 120 |
| triangle_triangle | 1.50 | 10.00 | False | -0.213 | 120 |
| triangle_triangle | 1.50 | 15.00 | False | -0.985 | 120 |
| triangle_triangle | 2.00 | 0.00 | True | 2.000 | 120 |
| triangle_triangle | 2.00 | 1.00 | True | 1.820 | 120 |
| triangle_triangle | 2.00 | 2.00 | True | 1.641 | 120 |
| triangle_triangle | 2.00 | 3.00 | True | 1.464 | 120 |
| triangle_triangle | 2.00 | 5.00 | True | 1.117 | 120 |
| triangle_triangle | 2.00 | 8.00 | True | 0.612 | 120 |
| triangle_triangle | 2.00 | 10.00 | True | 0.287 | 120 |
| triangle_triangle | 2.00 | 15.00 | False | -0.485 | 120 |
| triangle_triangle | 3.00 | 0.00 | True | 3.000 | 120 |
| triangle_triangle | 3.00 | 1.00 | True | 2.820 | 120 |
| triangle_triangle | 3.00 | 2.00 | True | 2.641 | 120 |
| triangle_triangle | 3.00 | 3.00 | True | 2.464 | 120 |
| triangle_triangle | 3.00 | 5.00 | True | 2.117 | 120 |
| triangle_triangle | 3.00 | 8.00 | True | 1.612 | 120 |
| triangle_triangle | 3.00 | 10.00 | True | 1.287 | 120 |
| triangle_triangle | 3.00 | 15.00 | True | 0.515 | 120 |
| triangle_triangle | 4.00 | 0.00 | True | 4.000 | 120 |
| triangle_triangle | 4.00 | 1.00 | True | 3.820 | 120 |
| triangle_triangle | 4.00 | 2.00 | True | 3.641 | 120 |
| triangle_triangle | 4.00 | 3.00 | True | 3.464 | 120 |
| triangle_triangle | 4.00 | 5.00 | True | 3.117 | 120 |
| triangle_triangle | 4.00 | 8.00 | True | 2.612 | 120 |
| triangle_triangle | 4.00 | 10.00 | True | 2.287 | 120 |
| triangle_triangle | 4.00 | 15.00 | True | 1.515 | 120 |
| hex_hex | 0.25 | 0.00 | True | 0.250 | 60 |
| hex_hex | 0.25 | 1.00 | True | 0.147 | 60 |
| hex_hex | 0.25 | 2.00 | True | 0.047 | 60 |
| hex_hex | 0.25 | 3.00 | False | -0.050 | 60 |
| hex_hex | 0.25 | 5.00 | False | -0.233 | 60 |
| hex_hex | 0.25 | 8.00 | False | -0.484 | 60 |
| hex_hex | 0.25 | 10.00 | False | -0.634 | 60 |
| hex_hex | 0.25 | 15.00 | False | -0.949 | 60 |
| hex_hex | 0.50 | 0.00 | True | 0.500 | 60 |
| hex_hex | 0.50 | 1.00 | True | 0.397 | 60 |
| hex_hex | 0.50 | 2.00 | True | 0.297 | 60 |
| hex_hex | 0.50 | 3.00 | True | 0.200 | 60 |
| hex_hex | 0.50 | 5.00 | True | 0.017 | 60 |
| hex_hex | 0.50 | 8.00 | False | -0.234 | 60 |
| hex_hex | 0.50 | 10.00 | False | -0.384 | 60 |
| hex_hex | 0.50 | 15.00 | False | -0.699 | 60 |
| hex_hex | 0.75 | 0.00 | True | 0.750 | 60 |
| hex_hex | 0.75 | 1.00 | True | 0.647 | 60 |
| hex_hex | 0.75 | 2.00 | True | 0.547 | 60 |
| hex_hex | 0.75 | 3.00 | True | 0.450 | 60 |
| hex_hex | 0.75 | 5.00 | True | 0.267 | 60 |
| hex_hex | 0.75 | 8.00 | True | 0.016 | 60 |
| hex_hex | 0.75 | 10.00 | False | -0.134 | 60 |
| hex_hex | 0.75 | 15.00 | False | -0.449 | 60 |
| hex_hex | 1.00 | 0.00 | True | 1.000 | 60 |
| hex_hex | 1.00 | 1.00 | True | 0.897 | 60 |
| hex_hex | 1.00 | 2.00 | True | 0.797 | 60 |
| hex_hex | 1.00 | 3.00 | True | 0.700 | 60 |
| hex_hex | 1.00 | 5.00 | True | 0.517 | 60 |
| hex_hex | 1.00 | 8.00 | True | 0.266 | 60 |
| hex_hex | 1.00 | 10.00 | True | 0.116 | 60 |
| hex_hex | 1.00 | 15.00 | False | -0.199 | 60 |
| hex_hex | 1.50 | 0.00 | True | 1.500 | 60 |
| hex_hex | 1.50 | 1.00 | True | 1.397 | 60 |
| hex_hex | 1.50 | 2.00 | True | 1.297 | 60 |
| hex_hex | 1.50 | 3.00 | True | 1.200 | 60 |
| hex_hex | 1.50 | 5.00 | True | 1.017 | 60 |
| hex_hex | 1.50 | 8.00 | True | 0.766 | 60 |
| hex_hex | 1.50 | 10.00 | True | 0.616 | 60 |
| hex_hex | 1.50 | 15.00 | True | 0.301 | 60 |
| hex_hex | 2.00 | 0.00 | True | 2.000 | 60 |
| hex_hex | 2.00 | 1.00 | True | 1.897 | 60 |
| hex_hex | 2.00 | 2.00 | True | 1.797 | 60 |
| hex_hex | 2.00 | 3.00 | True | 1.700 | 60 |
| hex_hex | 2.00 | 5.00 | True | 1.517 | 60 |
| hex_hex | 2.00 | 8.00 | True | 1.266 | 60 |
| hex_hex | 2.00 | 10.00 | True | 1.116 | 60 |
| hex_hex | 2.00 | 15.00 | True | 0.801 | 60 |
| hex_hex | 3.00 | 0.00 | True | 3.000 | 60 |
| hex_hex | 3.00 | 1.00 | True | 2.897 | 60 |
| hex_hex | 3.00 | 2.00 | True | 2.797 | 60 |
| hex_hex | 3.00 | 3.00 | True | 2.700 | 60 |
| hex_hex | 3.00 | 5.00 | True | 2.517 | 60 |
| hex_hex | 3.00 | 8.00 | True | 2.266 | 60 |
| hex_hex | 3.00 | 10.00 | True | 2.116 | 60 |
| hex_hex | 3.00 | 15.00 | True | 1.801 | 60 |
| hex_hex | 4.00 | 0.00 | True | 4.000 | 60 |
| hex_hex | 4.00 | 1.00 | True | 3.897 | 60 |
| hex_hex | 4.00 | 2.00 | True | 3.797 | 60 |
| hex_hex | 4.00 | 3.00 | True | 3.700 | 60 |
| hex_hex | 4.00 | 5.00 | True | 3.517 | 60 |
| hex_hex | 4.00 | 8.00 | True | 3.266 | 60 |
| hex_hex | 4.00 | 10.00 | True | 3.116 | 60 |
| hex_hex | 4.00 | 15.00 | True | 2.801 | 60 |
