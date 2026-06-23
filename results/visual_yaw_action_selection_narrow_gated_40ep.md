# Visual Yaw Action-Selection Analysis

Offline diagnostic only: this compares visual-yaw predictions with simulator truth recorded in traces.

- Traces: `2`
- Scope: `reacquire`
- Scoped rows: `301`
- Visibility gate: raw_norm >= `0.08`, cam_std >= `18.0`, crop_std >= `16.0`
- Temporal gate: last `3` predictions, max adjacent delta <= `12.0 deg`
- Sign mismatch ignores predictions/truth below `15.0 deg`

## Candidate Gates

- `scoped_all`: All rows in the selected scope.
- `visible`: Visibility stats pass.
- `visible_delta_stable`: Visibility stats pass and last predictions are temporally stable.
- `yaw_reapply_mid_high`: Candidate for yaw correction: visible, delta-stable, pred yaw 30-90 deg, Z 50-130 mm.
- `yaw_reapply_high_only`: Candidate for high-yaw correction only: visible, delta-stable, pred yaw 60-120 deg, Z 50-130 mm.
- `descent_small_yaw_xy30`: Candidate for descent: visible, delta-stable, pred yaw <=8 deg, XY <=30 mm, Z 30-130 mm.
- `descent_small_yaw_xy16`: Tighter descent candidate: visible, delta-stable, pred yaw <=8 deg, XY <=16 mm, Z 30-130 mm.
- `descent_tiny_yaw_xy16`: Very conservative descent candidate: visible, delta-stable, pred yaw <=2 deg, XY <=16 mm, Z 30-130 mm.
- `descent_tiny_yaw_xy8`: Very conservative descent candidate: visible, delta-stable, pred yaw <=2 deg, XY <=8 mm, Z 30-130 mm.
- `descent_tiny_yaw_xy8_mid_z`: Tiny-yaw descent candidate away from final low-Z tail: pred yaw <=2 deg, XY <=8 mm, Z 45-130 mm.
- `hold_recenter_only`: Rows that are scoped but fail both yaw-correction and descent candidates.

## Gate Summary

| name | rows | coverage | success rows | timeout rows | collision rows | mean err | max err | >bad | >high | sign mismatch | mean true | mean pred | mean XY | mean Z | down | up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| scoped_all | 301 | 1.000 | 0.000 | 1.000 | 0.000 | 8.230 | 47.286 | 0.070 | 0.003 | 0.040 | 63.808 | 60.162 | 0.0530 | 0.0777 | 0.000 | 0.924 |
| visible | 230 | 0.764 | 0.000 | 1.000 | 0.000 | 8.634 | 47.286 | 0.065 | 0.004 | 0.000 | 33.860 | 27.972 | 0.0349 | 0.0720 | 0.000 | 0.913 |
| visible_delta_stable | 221 | 0.734 | 0.000 | 1.000 | 0.000 | 8.316 | 29.569 | 0.050 | 0.000 | 0.000 | 31.797 | 25.295 | 0.0326 | 0.0718 | 0.000 | 0.923 |
| yaw_reapply_mid_high | 8 | 0.027 | 0.000 | 1.000 | 0.000 | 9.100 | 24.766 | 0.250 | 0.000 | 0.000 | 64.542 | 73.313 | 0.1127 | 0.0788 | 0.000 | 1.000 |
| yaw_reapply_high_only | 21 | 0.070 | 0.000 | 1.000 | 0.000 | 5.862 | 29.569 | 0.143 | 0.000 | 0.000 | 90.050 | 92.364 | 0.1046 | 0.0861 | 0.000 | 0.667 |
| descent_small_yaw_xy30 | 147 | 0.488 | 0.000 | 1.000 | 0.000 | 9.580 | 17.003 | 0.048 | 0.000 | 0.000 | 11.416 | 1.892 | 0.0112 | 0.0712 | 0.000 | 1.000 |
| descent_small_yaw_xy16 | 132 | 0.439 | 0.000 | 1.000 | 0.000 | 9.891 | 17.003 | 0.053 | 0.000 | 0.000 | 11.691 | 1.862 | 0.0102 | 0.0715 | 0.000 | 1.000 |
| descent_tiny_yaw_xy16 | 76 | 0.252 | 0.000 | 1.000 | 0.000 | 10.860 | 17.003 | 0.092 | 0.000 | 0.000 | 11.853 | 1.101 | 0.0091 | 0.0708 | 0.000 | 1.000 |
| descent_tiny_yaw_xy8 | 39 | 0.130 | 0.000 | 1.000 | 0.000 | 11.220 | 17.003 | 0.103 | 0.000 | 0.000 | 12.196 | 1.052 | 0.0060 | 0.0673 | 0.000 | 1.000 |
| descent_tiny_yaw_xy8_mid_z | 39 | 0.130 | 0.000 | 1.000 | 0.000 | 11.220 | 17.003 | 0.103 | 0.000 | 0.000 | 12.196 | 1.052 | 0.0060 | 0.0673 | 0.000 | 1.000 |
| hold_recenter_only | 146 | 0.485 | 0.000 | 1.000 | 0.000 | 6.823 | 47.286 | 0.082 | 0.007 | 0.082 | 116.519 | 118.111 | 0.0918 | 0.0843 | 0.000 | 0.842 |

## Current Action Buckets

| name | rows | coverage | success rows | timeout rows | collision rows | mean err | max err | >bad | >high | sign mismatch | mean true | mean pred | mean XY | mean Z | down | up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| aligned_descent | 74 | 0.246 | 0.000 | 1.000 | 0.000 | 10.794 | 17.003 | 0.068 | 0.000 | 0.000 | 12.256 | 1.557 | 0.0089 | 0.0727 | 0.000 | 1.000 |
| reacquire_descent | 73 | 0.243 | 0.000 | 1.000 | 0.000 | 8.349 | 15.296 | 0.027 | 0.000 | 0.000 | 10.565 | 2.231 | 0.0136 | 0.0696 | 0.000 | 1.000 |
| raw_norm_gate | 65 | 0.216 | 0.000 | 1.000 | 0.000 | 4.900 | 18.555 | 0.031 | 0.000 | 0.185 | 168.763 | 170.591 | 0.1123 | 0.0992 | 0.000 | 0.954 |
| visual_yaw_applied | 44 | 0.146 | 0.000 | 1.000 | 0.000 | 8.354 | 47.286 | 0.114 | 0.023 | 0.000 | 34.753 | 32.713 | 0.0574 | 0.0595 | 0.000 | 0.932 |
| reacquire_relaxed_yaw | 39 | 0.130 | 0.000 | 1.000 | 0.000 | 5.385 | 29.569 | 0.077 | 0.000 | 0.000 | 117.449 | 120.924 | 0.0990 | 0.0891 | 0.000 | 0.564 |
| low_visibility_brake | 6 | 0.020 | 0.000 | 1.000 | 0.000 | 28.805 | 44.236 | 0.667 | 0.000 | 0.000 | 74.800 | 97.806 | 0.1018 | 0.0651 | 0.000 | 1.000 |

## Worst Episodes

| file | seed | episode | outcome | scoped rows | visible-delta rows | yaw cand | descent cand | sign mismatch | high error | max err | first step | last step |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| visual_yaw_align_rectangular_key_20ep_seed906500_steps.csv | 906517 | 17 | timeout | 96 | 20 | 0 | 0 | 12 | 0 | 44.236 | 720 | 856 |
| visual_yaw_align_rectangular_key_20ep_seed908500_steps.csv | 908516 | 16 | timeout | 205 | 201 | 8 | 147 | 0 | 1 | 47.286 | 286 | 490 |
