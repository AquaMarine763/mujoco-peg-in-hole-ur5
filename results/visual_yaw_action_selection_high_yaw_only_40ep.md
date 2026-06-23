# Visual Yaw Action-Selection Analysis

Offline diagnostic only: this compares visual-yaw predictions with simulator truth recorded in traces.

- Traces: `2`
- Scope: `reacquire`
- Scoped rows: `205`
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
| scoped_all | 205 | 1.000 | 0.000 | 1.000 | 0.000 | 8.782 | 47.283 | 0.049 | 0.005 | 0.000 | 21.369 | 14.431 | 0.0284 | 0.0688 | 0.000 | 1.000 |
| visible | 204 | 0.995 | 0.000 | 1.000 | 0.000 | 8.640 | 47.283 | 0.044 | 0.005 | 0.000 | 21.360 | 14.202 | 0.0280 | 0.0688 | 0.000 | 1.000 |
| visible_delta_stable | 201 | 0.980 | 0.000 | 1.000 | 0.000 | 8.491 | 24.770 | 0.040 | 0.000 | 0.000 | 21.368 | 13.853 | 0.0273 | 0.0690 | 0.000 | 1.000 |
| yaw_reapply_mid_high | 8 | 0.039 | 0.000 | 1.000 | 0.000 | 9.097 | 24.770 | 0.250 | 0.000 | 0.000 | 64.542 | 73.309 | 0.1127 | 0.0788 | 0.000 | 1.000 |
| yaw_reapply_high_only | 14 | 0.068 | 0.000 | 1.000 | 0.000 | 5.741 | 24.770 | 0.143 | 0.000 | 0.000 | 82.464 | 87.168 | 0.1128 | 0.0789 | 0.000 | 1.000 |
| descent_small_yaw_xy30 | 147 | 0.717 | 0.000 | 1.000 | 0.000 | 9.572 | 17.274 | 0.041 | 0.000 | 0.000 | 11.308 | 1.775 | 0.0112 | 0.0711 | 0.000 | 1.000 |
| descent_small_yaw_xy16 | 133 | 0.649 | 0.000 | 1.000 | 0.000 | 9.881 | 17.274 | 0.045 | 0.000 | 0.000 | 11.569 | 1.732 | 0.0102 | 0.0715 | 0.000 | 1.000 |
| descent_tiny_yaw_xy16 | 80 | 0.390 | 0.000 | 1.000 | 0.000 | 10.733 | 17.274 | 0.075 | 0.000 | 0.000 | 11.668 | 1.007 | 0.0093 | 0.0709 | 0.000 | 1.000 |
| descent_tiny_yaw_xy8 | 38 | 0.185 | 0.000 | 1.000 | 0.000 | 11.434 | 17.274 | 0.053 | 0.000 | 0.000 | 12.176 | 0.839 | 0.0058 | 0.0677 | 0.000 | 1.000 |
| descent_tiny_yaw_xy8_mid_z | 38 | 0.185 | 0.000 | 1.000 | 0.000 | 11.434 | 17.274 | 0.053 | 0.000 | 0.000 | 12.176 | 0.839 | 0.0058 | 0.0677 | 0.000 | 1.000 |
| hold_recenter_only | 50 | 0.244 | 0.000 | 1.000 | 0.000 | 6.409 | 47.283 | 0.040 | 0.020 | 0.000 | 44.042 | 42.217 | 0.0654 | 0.0603 | 0.000 | 1.000 |

## Current Action Buckets

| name | rows | coverage | success rows | timeout rows | collision rows | mean err | max err | >bad | >high | sign mismatch | mean true | mean pred | mean XY | mean Z | down | up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| aligned_descent | 101 | 0.493 | 0.000 | 1.000 | 0.000 | 9.520 | 17.274 | 0.050 | 0.000 | 0.000 | 11.053 | 1.587 | 0.0095 | 0.0697 | 0.000 | 1.000 |
| visual_yaw_applied | 77 | 0.376 | 0.000 | 1.000 | 0.000 | 8.147 | 47.283 | 0.013 | 0.013 | 0.000 | 14.967 | 8.370 | 0.0321 | 0.0642 | 0.000 | 1.000 |
| reacquire_relaxed_yaw | 20 | 0.098 | 0.000 | 1.000 | 0.000 | 4.795 | 24.770 | 0.100 | 0.000 | 0.000 | 100.493 | 104.562 | 0.1103 | 0.0783 | 0.000 | 1.000 |
| yaw_ok_recenter | 6 | 0.029 | 0.000 | 1.000 | 0.000 | 12.976 | 15.026 | 0.167 | 0.000 | 0.000 | 13.120 | 0.187 | 0.0130 | 0.0814 | 0.000 | 1.000 |
| low_visibility_brake | 1 | 0.005 | 0.000 | 1.000 | 0.000 | 37.727 | 37.727 | 1.000 | 0.000 | 0.000 | 23.366 | 61.092 | 0.1027 | 0.0604 | 0.000 | 1.000 |

## Worst Episodes

| file | seed | episode | outcome | scoped rows | visible-delta rows | yaw cand | descent cand | sign mismatch | high error | max err | first step | last step |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| visual_yaw_align_rectangular_key_20ep_seed908500_steps.csv | 908516 | 16 | timeout | 205 | 201 | 8 | 147 | 0 | 1 | 47.283 | 286 | 490 |
