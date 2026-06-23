# Shape Yaw Sensitivity Scan

This is an analytic 2D cross-section scan. It does not use visual-only debug highlights
and does not run the policy. The purpose is to pick clearances where yaw alignment
becomes necessary before building the visual yaw estimator and guarded yaw-align phase.

A `discriminative` clearance means all tested small yaw errors pass while all tested
large yaw errors fail under the configured good/bad yaw thresholds.

## Summary

| profile | clearance mm | discriminative | max passing yaw deg | min failing yaw deg |
|---|---:|---:|---:|---:|
| hex_hex | 0.50 | True | 5.00 | 6.00 |
| hex_hex | 0.75 | False | 8.00 | 10.00 |
| hex_hex | 1.00 | False | 10.00 | nan |
| hex_hex | 1.25 | False | 10.00 | nan |
| hex_hex | 1.50 | False | 10.00 | nan |
| hex_hex | 1.75 | False | 10.00 | nan |
| hex_hex | 2.00 | False | 10.00 | nan |
| hex_hex | 2.50 | False | 10.00 | nan |
| rectangular_key | 0.50 | False | 1.50 | 2.00 |
| rectangular_key | 0.75 | True | 2.00 | 2.50 |
| rectangular_key | 1.00 | True | 3.00 | 4.00 |
| rectangular_key | 1.25 | True | 3.00 | 4.00 |
| rectangular_key | 1.50 | True | 4.00 | 5.00 |
| rectangular_key | 1.75 | True | 5.00 | 6.00 |
| rectangular_key | 2.00 | True | 6.00 | 8.00 |
| rectangular_key | 2.50 | True | 6.00 | 8.00 |
| square_square | 0.50 | True | 2.00 | 2.50 |
| square_square | 0.75 | True | 3.00 | 4.00 |
| square_square | 1.00 | True | 4.00 | 5.00 |
| square_square | 1.25 | True | 6.00 | 8.00 |
| square_square | 1.50 | True | 6.00 | 8.00 |
| square_square | 1.75 | False | 8.00 | 10.00 |
| square_square | 2.00 | False | 10.00 | nan |
| square_square | 2.50 | False | 10.00 | nan |
| triangle_triangle | 0.50 | True | 2.50 | 3.00 |
| triangle_triangle | 0.75 | True | 4.00 | 5.00 |
| triangle_triangle | 1.00 | True | 5.00 | 6.00 |
| triangle_triangle | 1.25 | True | 6.00 | 8.00 |
| triangle_triangle | 1.50 | False | 8.00 | 10.00 |
| triangle_triangle | 1.75 | False | 10.00 | nan |
| triangle_triangle | 2.00 | False | 10.00 | nan |
| triangle_triangle | 2.50 | False | 10.00 | nan |

## Detailed Rows

| profile | clearance mm | yaw error deg | pass | min margin mm | period deg |
|---|---:|---:|---:|---:|---:|
| rectangular_key | 0.50 | 0.00 | True | 0.154 | 360 |
| rectangular_key | 0.50 | 0.50 | True | 0.114 | 360 |
| rectangular_key | 0.50 | 1.00 | True | 0.069 | 360 |
| rectangular_key | 0.50 | 1.50 | True | 0.017 | 360 |
| rectangular_key | 0.50 | 2.00 | False | -0.143 | 360 |
| rectangular_key | 0.50 | 2.50 | False | -0.302 | 360 |
| rectangular_key | 0.50 | 3.00 | False | -0.461 | 360 |
| rectangular_key | 0.50 | 4.00 | False | -0.778 | 360 |
| rectangular_key | 0.50 | 5.00 | False | -1.093 | 360 |
| rectangular_key | 0.50 | 6.00 | False | -1.406 | 360 |
| rectangular_key | 0.50 | 8.00 | False | -2.026 | 360 |
| rectangular_key | 0.50 | 10.00 | False | -2.637 | 360 |
| rectangular_key | 0.75 | 0.00 | True | 0.193 | 360 |
| rectangular_key | 0.75 | 0.50 | True | 0.149 | 360 |
| rectangular_key | 0.75 | 1.00 | True | 0.143 | 360 |
| rectangular_key | 0.75 | 1.50 | True | 0.143 | 360 |
| rectangular_key | 0.75 | 2.00 | True | 0.106 | 360 |
| rectangular_key | 0.75 | 2.50 | False | -0.052 | 360 |
| rectangular_key | 0.75 | 3.00 | False | -0.211 | 360 |
| rectangular_key | 0.75 | 4.00 | False | -0.528 | 360 |
| rectangular_key | 0.75 | 5.00 | False | -0.843 | 360 |
| rectangular_key | 0.75 | 6.00 | False | -1.156 | 360 |
| rectangular_key | 0.75 | 8.00 | False | -1.776 | 360 |
| rectangular_key | 0.75 | 10.00 | False | -2.387 | 360 |
| rectangular_key | 1.00 | 0.00 | True | 0.230 | 360 |
| rectangular_key | 1.00 | 0.50 | True | 0.219 | 360 |
| rectangular_key | 1.00 | 1.00 | True | 0.219 | 360 |
| rectangular_key | 1.00 | 1.50 | True | 0.190 | 360 |
| rectangular_key | 1.00 | 2.00 | True | 0.143 | 360 |
| rectangular_key | 1.00 | 2.50 | True | 0.131 | 360 |
| rectangular_key | 1.00 | 3.00 | True | 0.039 | 360 |
| rectangular_key | 1.00 | 4.00 | False | -0.278 | 360 |
| rectangular_key | 1.00 | 5.00 | False | -0.593 | 360 |
| rectangular_key | 1.00 | 6.00 | False | -0.906 | 360 |
| rectangular_key | 1.00 | 8.00 | False | -1.526 | 360 |
| rectangular_key | 1.00 | 10.00 | False | -2.137 | 360 |
| rectangular_key | 1.25 | 0.00 | True | 0.294 | 360 |
| rectangular_key | 1.25 | 0.50 | True | 0.294 | 360 |
| rectangular_key | 1.25 | 1.00 | True | 0.275 | 360 |
| rectangular_key | 1.25 | 1.50 | True | 0.229 | 360 |
| rectangular_key | 1.25 | 2.00 | True | 0.206 | 360 |
| rectangular_key | 1.25 | 2.50 | True | 0.206 | 360 |
| rectangular_key | 1.25 | 3.00 | True | 0.181 | 360 |
| rectangular_key | 1.25 | 4.00 | False | -0.028 | 360 |
| rectangular_key | 1.25 | 5.00 | False | -0.343 | 360 |
| rectangular_key | 1.25 | 6.00 | False | -0.656 | 360 |
| rectangular_key | 1.25 | 8.00 | False | -1.276 | 360 |
| rectangular_key | 1.25 | 10.00 | False | -1.887 | 360 |
| rectangular_key | 1.50 | 0.00 | True | 0.369 | 360 |
| rectangular_key | 1.50 | 0.50 | True | 0.361 | 360 |
| rectangular_key | 1.50 | 1.00 | True | 0.316 | 360 |
| rectangular_key | 1.50 | 1.50 | True | 0.281 | 360 |
| rectangular_key | 1.50 | 2.00 | True | 0.281 | 360 |
| rectangular_key | 1.50 | 2.50 | True | 0.270 | 360 |
| rectangular_key | 1.50 | 3.00 | True | 0.221 | 360 |
| rectangular_key | 1.50 | 4.00 | True | 0.193 | 360 |
| rectangular_key | 1.50 | 5.00 | False | -0.093 | 360 |
| rectangular_key | 1.50 | 6.00 | False | -0.406 | 360 |
| rectangular_key | 1.50 | 8.00 | False | -1.026 | 360 |
| rectangular_key | 1.50 | 10.00 | False | -1.637 | 360 |
| rectangular_key | 1.75 | 0.00 | True | 0.443 | 360 |
| rectangular_key | 1.75 | 0.50 | True | 0.404 | 360 |
| rectangular_key | 1.75 | 1.00 | True | 0.359 | 360 |
| rectangular_key | 1.75 | 1.50 | True | 0.355 | 360 |
| rectangular_key | 1.75 | 2.00 | True | 0.355 | 360 |
| rectangular_key | 1.75 | 2.50 | True | 0.313 | 360 |
| rectangular_key | 1.75 | 3.00 | True | 0.267 | 360 |
| rectangular_key | 1.75 | 4.00 | True | 0.258 | 360 |
| rectangular_key | 1.75 | 5.00 | True | 0.157 | 360 |
| rectangular_key | 1.75 | 6.00 | False | -0.156 | 360 |
| rectangular_key | 1.75 | 8.00 | False | -0.776 | 360 |
| rectangular_key | 1.75 | 10.00 | False | -1.387 | 360 |
| rectangular_key | 2.00 | 0.00 | True | 0.492 | 360 |
| rectangular_key | 2.00 | 0.50 | True | 0.448 | 360 |
| rectangular_key | 2.00 | 1.00 | True | 0.429 | 360 |
| rectangular_key | 2.00 | 1.50 | True | 0.429 | 360 |
| rectangular_key | 2.00 | 2.00 | True | 0.405 | 360 |
| rectangular_key | 2.00 | 2.50 | True | 0.357 | 360 |
| rectangular_key | 2.00 | 3.00 | True | 0.340 | 360 |
| rectangular_key | 2.00 | 4.00 | True | 0.302 | 360 |
| rectangular_key | 2.00 | 5.00 | True | 0.252 | 360 |
| rectangular_key | 2.00 | 6.00 | True | 0.094 | 360 |
| rectangular_key | 2.00 | 8.00 | False | -0.526 | 360 |
| rectangular_key | 2.00 | 10.00 | False | -1.137 | 360 |
| rectangular_key | 2.50 | 0.00 | True | 0.587 | 360 |
| rectangular_key | 2.50 | 0.50 | True | 0.575 | 360 |
| rectangular_key | 2.50 | 1.00 | True | 0.575 | 360 |
| rectangular_key | 2.50 | 1.50 | True | 0.546 | 360 |
| rectangular_key | 2.50 | 2.00 | True | 0.499 | 360 |
| rectangular_key | 2.50 | 2.50 | True | 0.486 | 360 |
| rectangular_key | 2.50 | 3.00 | True | 0.486 | 360 |
| rectangular_key | 2.50 | 4.00 | True | 0.398 | 360 |
| rectangular_key | 2.50 | 5.00 | True | 0.385 | 360 |
| rectangular_key | 2.50 | 6.00 | True | 0.309 | 360 |
| rectangular_key | 2.50 | 8.00 | False | -0.026 | 360 |
| rectangular_key | 2.50 | 10.00 | False | -0.637 | 360 |
| square_square | 0.50 | 0.00 | True | 0.500 | 90 |
| square_square | 0.50 | 0.50 | True | 0.396 | 90 |
| square_square | 0.50 | 1.00 | True | 0.292 | 90 |
| square_square | 0.50 | 1.50 | True | 0.190 | 90 |
| square_square | 0.50 | 2.00 | True | 0.089 | 90 |
| square_square | 0.50 | 2.50 | False | -0.012 | 90 |
| square_square | 0.50 | 3.00 | False | -0.112 | 90 |
| square_square | 0.50 | 4.00 | False | -0.308 | 90 |
| square_square | 0.50 | 5.00 | False | -0.500 | 90 |
| square_square | 0.50 | 6.00 | False | -0.689 | 90 |
| square_square | 0.50 | 8.00 | False | -1.053 | 90 |
| square_square | 0.50 | 10.00 | False | -1.401 | 90 |
| square_square | 0.75 | 0.00 | True | 0.750 | 90 |
| square_square | 0.75 | 0.50 | True | 0.646 | 90 |
| square_square | 0.75 | 1.00 | True | 0.542 | 90 |
| square_square | 0.75 | 1.50 | True | 0.440 | 90 |
| square_square | 0.75 | 2.00 | True | 0.339 | 90 |
| square_square | 0.75 | 2.50 | True | 0.238 | 90 |
| square_square | 0.75 | 3.00 | True | 0.138 | 90 |
| square_square | 0.75 | 4.00 | False | -0.058 | 90 |
| square_square | 0.75 | 5.00 | False | -0.250 | 90 |
| square_square | 0.75 | 6.00 | False | -0.439 | 90 |
| square_square | 0.75 | 8.00 | False | -0.803 | 90 |
| square_square | 0.75 | 10.00 | False | -1.151 | 90 |
| square_square | 1.00 | 0.00 | True | 1.000 | 90 |
| square_square | 1.00 | 0.50 | True | 0.896 | 90 |
| square_square | 1.00 | 1.00 | True | 0.792 | 90 |
| square_square | 1.00 | 1.50 | True | 0.690 | 90 |
| square_square | 1.00 | 2.00 | True | 0.589 | 90 |
| square_square | 1.00 | 2.50 | True | 0.488 | 90 |
| square_square | 1.00 | 3.00 | True | 0.388 | 90 |
| square_square | 1.00 | 4.00 | True | 0.192 | 90 |
| square_square | 1.00 | 5.00 | False | -0.000 | 90 |
| square_square | 1.00 | 6.00 | False | -0.189 | 90 |
| square_square | 1.00 | 8.00 | False | -0.553 | 90 |
| square_square | 1.00 | 10.00 | False | -0.901 | 90 |
| square_square | 1.25 | 0.00 | True | 1.250 | 90 |
| square_square | 1.25 | 0.50 | True | 1.146 | 90 |
| square_square | 1.25 | 1.00 | True | 1.042 | 90 |
| square_square | 1.25 | 1.50 | True | 0.940 | 90 |
| square_square | 1.25 | 2.00 | True | 0.839 | 90 |
| square_square | 1.25 | 2.50 | True | 0.738 | 90 |
| square_square | 1.25 | 3.00 | True | 0.638 | 90 |
| square_square | 1.25 | 4.00 | True | 0.442 | 90 |
| square_square | 1.25 | 5.00 | True | 0.250 | 90 |
| square_square | 1.25 | 6.00 | True | 0.061 | 90 |
| square_square | 1.25 | 8.00 | False | -0.303 | 90 |
| square_square | 1.25 | 10.00 | False | -0.651 | 90 |
| square_square | 1.50 | 0.00 | True | 1.500 | 90 |
| square_square | 1.50 | 0.50 | True | 1.396 | 90 |
| square_square | 1.50 | 1.00 | True | 1.292 | 90 |
| square_square | 1.50 | 1.50 | True | 1.190 | 90 |
| square_square | 1.50 | 2.00 | True | 1.089 | 90 |
| square_square | 1.50 | 2.50 | True | 0.988 | 90 |
| square_square | 1.50 | 3.00 | True | 0.888 | 90 |
| square_square | 1.50 | 4.00 | True | 0.692 | 90 |
| square_square | 1.50 | 5.00 | True | 0.500 | 90 |
| square_square | 1.50 | 6.00 | True | 0.311 | 90 |
| square_square | 1.50 | 8.00 | False | -0.053 | 90 |
| square_square | 1.50 | 10.00 | False | -0.401 | 90 |
| square_square | 1.75 | 0.00 | True | 1.750 | 90 |
| square_square | 1.75 | 0.50 | True | 1.646 | 90 |
| square_square | 1.75 | 1.00 | True | 1.542 | 90 |
| square_square | 1.75 | 1.50 | True | 1.440 | 90 |
| square_square | 1.75 | 2.00 | True | 1.339 | 90 |
| square_square | 1.75 | 2.50 | True | 1.238 | 90 |
| square_square | 1.75 | 3.00 | True | 1.138 | 90 |
| square_square | 1.75 | 4.00 | True | 0.942 | 90 |
| square_square | 1.75 | 5.00 | True | 0.750 | 90 |
| square_square | 1.75 | 6.00 | True | 0.561 | 90 |
| square_square | 1.75 | 8.00 | True | 0.197 | 90 |
| square_square | 1.75 | 10.00 | False | -0.151 | 90 |
| square_square | 2.00 | 0.00 | True | 2.000 | 90 |
| square_square | 2.00 | 0.50 | True | 1.896 | 90 |
| square_square | 2.00 | 1.00 | True | 1.792 | 90 |
| square_square | 2.00 | 1.50 | True | 1.690 | 90 |
| square_square | 2.00 | 2.00 | True | 1.589 | 90 |
| square_square | 2.00 | 2.50 | True | 1.488 | 90 |
| square_square | 2.00 | 3.00 | True | 1.388 | 90 |
| square_square | 2.00 | 4.00 | True | 1.192 | 90 |
| square_square | 2.00 | 5.00 | True | 1.000 | 90 |
| square_square | 2.00 | 6.00 | True | 0.811 | 90 |
| square_square | 2.00 | 8.00 | True | 0.447 | 90 |
| square_square | 2.00 | 10.00 | True | 0.099 | 90 |
| square_square | 2.50 | 0.00 | True | 2.500 | 90 |
| square_square | 2.50 | 0.50 | True | 2.396 | 90 |
| square_square | 2.50 | 1.00 | True | 2.292 | 90 |
| square_square | 2.50 | 1.50 | True | 2.190 | 90 |
| square_square | 2.50 | 2.00 | True | 2.089 | 90 |
| square_square | 2.50 | 2.50 | True | 1.988 | 90 |
| square_square | 2.50 | 3.00 | True | 1.888 | 90 |
| square_square | 2.50 | 4.00 | True | 1.692 | 90 |
| square_square | 2.50 | 5.00 | True | 1.500 | 90 |
| square_square | 2.50 | 6.00 | True | 1.311 | 90 |
| square_square | 2.50 | 8.00 | True | 0.947 | 90 |
| square_square | 2.50 | 10.00 | True | 0.599 | 90 |
| triangle_triangle | 0.50 | 0.00 | True | 0.500 | 120 |
| triangle_triangle | 0.50 | 0.50 | True | 0.410 | 120 |
| triangle_triangle | 0.50 | 1.00 | True | 0.320 | 120 |
| triangle_triangle | 0.50 | 1.50 | True | 0.230 | 120 |
| triangle_triangle | 0.50 | 2.00 | True | 0.141 | 120 |
| triangle_triangle | 0.50 | 2.50 | True | 0.052 | 120 |
| triangle_triangle | 0.50 | 3.00 | False | -0.036 | 120 |
| triangle_triangle | 0.50 | 4.00 | False | -0.210 | 120 |
| triangle_triangle | 0.50 | 5.00 | False | -0.383 | 120 |
| triangle_triangle | 0.50 | 6.00 | False | -0.553 | 120 |
| triangle_triangle | 0.50 | 8.00 | False | -0.888 | 120 |
| triangle_triangle | 0.50 | 10.00 | False | -1.213 | 120 |
| triangle_triangle | 0.75 | 0.00 | True | 0.750 | 120 |
| triangle_triangle | 0.75 | 0.50 | True | 0.660 | 120 |
| triangle_triangle | 0.75 | 1.00 | True | 0.570 | 120 |
| triangle_triangle | 0.75 | 1.50 | True | 0.480 | 120 |
| triangle_triangle | 0.75 | 2.00 | True | 0.391 | 120 |
| triangle_triangle | 0.75 | 2.50 | True | 0.302 | 120 |
| triangle_triangle | 0.75 | 3.00 | True | 0.214 | 120 |
| triangle_triangle | 0.75 | 4.00 | True | 0.040 | 120 |
| triangle_triangle | 0.75 | 5.00 | False | -0.133 | 120 |
| triangle_triangle | 0.75 | 6.00 | False | -0.303 | 120 |
| triangle_triangle | 0.75 | 8.00 | False | -0.638 | 120 |
| triangle_triangle | 0.75 | 10.00 | False | -0.963 | 120 |
| triangle_triangle | 1.00 | 0.00 | True | 1.000 | 120 |
| triangle_triangle | 1.00 | 0.50 | True | 0.910 | 120 |
| triangle_triangle | 1.00 | 1.00 | True | 0.820 | 120 |
| triangle_triangle | 1.00 | 1.50 | True | 0.730 | 120 |
| triangle_triangle | 1.00 | 2.00 | True | 0.641 | 120 |
| triangle_triangle | 1.00 | 2.50 | True | 0.552 | 120 |
| triangle_triangle | 1.00 | 3.00 | True | 0.464 | 120 |
| triangle_triangle | 1.00 | 4.00 | True | 0.290 | 120 |
| triangle_triangle | 1.00 | 5.00 | True | 0.117 | 120 |
| triangle_triangle | 1.00 | 6.00 | False | -0.053 | 120 |
| triangle_triangle | 1.00 | 8.00 | False | -0.388 | 120 |
| triangle_triangle | 1.00 | 10.00 | False | -0.713 | 120 |
| triangle_triangle | 1.25 | 0.00 | True | 1.250 | 120 |
| triangle_triangle | 1.25 | 0.50 | True | 1.160 | 120 |
| triangle_triangle | 1.25 | 1.00 | True | 1.070 | 120 |
| triangle_triangle | 1.25 | 1.50 | True | 0.980 | 120 |
| triangle_triangle | 1.25 | 2.00 | True | 0.891 | 120 |
| triangle_triangle | 1.25 | 2.50 | True | 0.802 | 120 |
| triangle_triangle | 1.25 | 3.00 | True | 0.714 | 120 |
| triangle_triangle | 1.25 | 4.00 | True | 0.540 | 120 |
| triangle_triangle | 1.25 | 5.00 | True | 0.367 | 120 |
| triangle_triangle | 1.25 | 6.00 | True | 0.197 | 120 |
| triangle_triangle | 1.25 | 8.00 | False | -0.138 | 120 |
| triangle_triangle | 1.25 | 10.00 | False | -0.463 | 120 |
| triangle_triangle | 1.50 | 0.00 | True | 1.500 | 120 |
| triangle_triangle | 1.50 | 0.50 | True | 1.410 | 120 |
| triangle_triangle | 1.50 | 1.00 | True | 1.320 | 120 |
| triangle_triangle | 1.50 | 1.50 | True | 1.230 | 120 |
| triangle_triangle | 1.50 | 2.00 | True | 1.141 | 120 |
| triangle_triangle | 1.50 | 2.50 | True | 1.052 | 120 |
| triangle_triangle | 1.50 | 3.00 | True | 0.964 | 120 |
| triangle_triangle | 1.50 | 4.00 | True | 0.790 | 120 |
| triangle_triangle | 1.50 | 5.00 | True | 0.617 | 120 |
| triangle_triangle | 1.50 | 6.00 | True | 0.447 | 120 |
| triangle_triangle | 1.50 | 8.00 | True | 0.112 | 120 |
| triangle_triangle | 1.50 | 10.00 | False | -0.213 | 120 |
| triangle_triangle | 1.75 | 0.00 | True | 1.750 | 120 |
| triangle_triangle | 1.75 | 0.50 | True | 1.660 | 120 |
| triangle_triangle | 1.75 | 1.00 | True | 1.570 | 120 |
| triangle_triangle | 1.75 | 1.50 | True | 1.480 | 120 |
| triangle_triangle | 1.75 | 2.00 | True | 1.391 | 120 |
| triangle_triangle | 1.75 | 2.50 | True | 1.302 | 120 |
| triangle_triangle | 1.75 | 3.00 | True | 1.214 | 120 |
| triangle_triangle | 1.75 | 4.00 | True | 1.040 | 120 |
| triangle_triangle | 1.75 | 5.00 | True | 0.867 | 120 |
| triangle_triangle | 1.75 | 6.00 | True | 0.697 | 120 |
| triangle_triangle | 1.75 | 8.00 | True | 0.362 | 120 |
| triangle_triangle | 1.75 | 10.00 | True | 0.037 | 120 |
| triangle_triangle | 2.00 | 0.00 | True | 2.000 | 120 |
| triangle_triangle | 2.00 | 0.50 | True | 1.910 | 120 |
| triangle_triangle | 2.00 | 1.00 | True | 1.820 | 120 |
| triangle_triangle | 2.00 | 1.50 | True | 1.730 | 120 |
| triangle_triangle | 2.00 | 2.00 | True | 1.641 | 120 |
| triangle_triangle | 2.00 | 2.50 | True | 1.552 | 120 |
| triangle_triangle | 2.00 | 3.00 | True | 1.464 | 120 |
| triangle_triangle | 2.00 | 4.00 | True | 1.290 | 120 |
| triangle_triangle | 2.00 | 5.00 | True | 1.117 | 120 |
| triangle_triangle | 2.00 | 6.00 | True | 0.947 | 120 |
| triangle_triangle | 2.00 | 8.00 | True | 0.612 | 120 |
| triangle_triangle | 2.00 | 10.00 | True | 0.287 | 120 |
| triangle_triangle | 2.50 | 0.00 | True | 2.500 | 120 |
| triangle_triangle | 2.50 | 0.50 | True | 2.410 | 120 |
| triangle_triangle | 2.50 | 1.00 | True | 2.320 | 120 |
| triangle_triangle | 2.50 | 1.50 | True | 2.230 | 120 |
| triangle_triangle | 2.50 | 2.00 | True | 2.141 | 120 |
| triangle_triangle | 2.50 | 2.50 | True | 2.052 | 120 |
| triangle_triangle | 2.50 | 3.00 | True | 1.964 | 120 |
| triangle_triangle | 2.50 | 4.00 | True | 1.790 | 120 |
| triangle_triangle | 2.50 | 5.00 | True | 1.617 | 120 |
| triangle_triangle | 2.50 | 6.00 | True | 1.447 | 120 |
| triangle_triangle | 2.50 | 8.00 | True | 1.112 | 120 |
| triangle_triangle | 2.50 | 10.00 | True | 0.787 | 120 |
| hex_hex | 0.50 | 0.00 | True | 0.500 | 60 |
| hex_hex | 0.50 | 0.50 | True | 0.448 | 60 |
| hex_hex | 0.50 | 1.00 | True | 0.397 | 60 |
| hex_hex | 0.50 | 1.50 | True | 0.346 | 60 |
| hex_hex | 0.50 | 2.00 | True | 0.297 | 60 |
| hex_hex | 0.50 | 2.50 | True | 0.248 | 60 |
| hex_hex | 0.50 | 3.00 | True | 0.200 | 60 |
| hex_hex | 0.50 | 4.00 | True | 0.107 | 60 |
| hex_hex | 0.50 | 5.00 | True | 0.017 | 60 |
| hex_hex | 0.50 | 6.00 | False | -0.070 | 60 |
| hex_hex | 0.50 | 8.00 | False | -0.234 | 60 |
| hex_hex | 0.50 | 10.00 | False | -0.384 | 60 |
| hex_hex | 0.75 | 0.00 | True | 0.750 | 60 |
| hex_hex | 0.75 | 0.50 | True | 0.698 | 60 |
| hex_hex | 0.75 | 1.00 | True | 0.647 | 60 |
| hex_hex | 0.75 | 1.50 | True | 0.596 | 60 |
| hex_hex | 0.75 | 2.00 | True | 0.547 | 60 |
| hex_hex | 0.75 | 2.50 | True | 0.498 | 60 |
| hex_hex | 0.75 | 3.00 | True | 0.450 | 60 |
| hex_hex | 0.75 | 4.00 | True | 0.357 | 60 |
| hex_hex | 0.75 | 5.00 | True | 0.267 | 60 |
| hex_hex | 0.75 | 6.00 | True | 0.180 | 60 |
| hex_hex | 0.75 | 8.00 | True | 0.016 | 60 |
| hex_hex | 0.75 | 10.00 | False | -0.134 | 60 |
| hex_hex | 1.00 | 0.00 | True | 1.000 | 60 |
| hex_hex | 1.00 | 0.50 | True | 0.948 | 60 |
| hex_hex | 1.00 | 1.00 | True | 0.897 | 60 |
| hex_hex | 1.00 | 1.50 | True | 0.846 | 60 |
| hex_hex | 1.00 | 2.00 | True | 0.797 | 60 |
| hex_hex | 1.00 | 2.50 | True | 0.748 | 60 |
| hex_hex | 1.00 | 3.00 | True | 0.700 | 60 |
| hex_hex | 1.00 | 4.00 | True | 0.607 | 60 |
| hex_hex | 1.00 | 5.00 | True | 0.517 | 60 |
| hex_hex | 1.00 | 6.00 | True | 0.430 | 60 |
| hex_hex | 1.00 | 8.00 | True | 0.266 | 60 |
| hex_hex | 1.00 | 10.00 | True | 0.116 | 60 |
| hex_hex | 1.25 | 0.00 | True | 1.250 | 60 |
| hex_hex | 1.25 | 0.50 | True | 1.198 | 60 |
| hex_hex | 1.25 | 1.00 | True | 1.147 | 60 |
| hex_hex | 1.25 | 1.50 | True | 1.096 | 60 |
| hex_hex | 1.25 | 2.00 | True | 1.047 | 60 |
| hex_hex | 1.25 | 2.50 | True | 0.998 | 60 |
| hex_hex | 1.25 | 3.00 | True | 0.950 | 60 |
| hex_hex | 1.25 | 4.00 | True | 0.857 | 60 |
| hex_hex | 1.25 | 5.00 | True | 0.767 | 60 |
| hex_hex | 1.25 | 6.00 | True | 0.680 | 60 |
| hex_hex | 1.25 | 8.00 | True | 0.516 | 60 |
| hex_hex | 1.25 | 10.00 | True | 0.366 | 60 |
| hex_hex | 1.50 | 0.00 | True | 1.500 | 60 |
| hex_hex | 1.50 | 0.50 | True | 1.448 | 60 |
| hex_hex | 1.50 | 1.00 | True | 1.397 | 60 |
| hex_hex | 1.50 | 1.50 | True | 1.346 | 60 |
| hex_hex | 1.50 | 2.00 | True | 1.297 | 60 |
| hex_hex | 1.50 | 2.50 | True | 1.248 | 60 |
| hex_hex | 1.50 | 3.00 | True | 1.200 | 60 |
| hex_hex | 1.50 | 4.00 | True | 1.107 | 60 |
| hex_hex | 1.50 | 5.00 | True | 1.017 | 60 |
| hex_hex | 1.50 | 6.00 | True | 0.930 | 60 |
| hex_hex | 1.50 | 8.00 | True | 0.766 | 60 |
| hex_hex | 1.50 | 10.00 | True | 0.616 | 60 |
| hex_hex | 1.75 | 0.00 | True | 1.750 | 60 |
| hex_hex | 1.75 | 0.50 | True | 1.698 | 60 |
| hex_hex | 1.75 | 1.00 | True | 1.647 | 60 |
| hex_hex | 1.75 | 1.50 | True | 1.596 | 60 |
| hex_hex | 1.75 | 2.00 | True | 1.547 | 60 |
| hex_hex | 1.75 | 2.50 | True | 1.498 | 60 |
| hex_hex | 1.75 | 3.00 | True | 1.450 | 60 |
| hex_hex | 1.75 | 4.00 | True | 1.357 | 60 |
| hex_hex | 1.75 | 5.00 | True | 1.267 | 60 |
| hex_hex | 1.75 | 6.00 | True | 1.180 | 60 |
| hex_hex | 1.75 | 8.00 | True | 1.016 | 60 |
| hex_hex | 1.75 | 10.00 | True | 0.866 | 60 |
| hex_hex | 2.00 | 0.00 | True | 2.000 | 60 |
| hex_hex | 2.00 | 0.50 | True | 1.948 | 60 |
| hex_hex | 2.00 | 1.00 | True | 1.897 | 60 |
| hex_hex | 2.00 | 1.50 | True | 1.846 | 60 |
| hex_hex | 2.00 | 2.00 | True | 1.797 | 60 |
| hex_hex | 2.00 | 2.50 | True | 1.748 | 60 |
| hex_hex | 2.00 | 3.00 | True | 1.700 | 60 |
| hex_hex | 2.00 | 4.00 | True | 1.607 | 60 |
| hex_hex | 2.00 | 5.00 | True | 1.517 | 60 |
| hex_hex | 2.00 | 6.00 | True | 1.430 | 60 |
| hex_hex | 2.00 | 8.00 | True | 1.266 | 60 |
| hex_hex | 2.00 | 10.00 | True | 1.116 | 60 |
| hex_hex | 2.50 | 0.00 | True | 2.500 | 60 |
| hex_hex | 2.50 | 0.50 | True | 2.448 | 60 |
| hex_hex | 2.50 | 1.00 | True | 2.397 | 60 |
| hex_hex | 2.50 | 1.50 | True | 2.346 | 60 |
| hex_hex | 2.50 | 2.00 | True | 2.297 | 60 |
| hex_hex | 2.50 | 2.50 | True | 2.248 | 60 |
| hex_hex | 2.50 | 3.00 | True | 2.200 | 60 |
| hex_hex | 2.50 | 4.00 | True | 2.107 | 60 |
| hex_hex | 2.50 | 5.00 | True | 2.017 | 60 |
| hex_hex | 2.50 | 6.00 | True | 1.930 | 60 |
| hex_hex | 2.50 | 8.00 | True | 1.766 | 60 |
| hex_hex | 2.50 | 10.00 | True | 1.616 | 60 |
