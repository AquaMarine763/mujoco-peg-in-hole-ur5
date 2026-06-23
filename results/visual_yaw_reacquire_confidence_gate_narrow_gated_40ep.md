# Visual Yaw Re-acquire Trace Analysis

Offline diagnostic only: this compares visual-yaw predictions with sim truth already recorded in traces.

- Traces: `2`
- Re-acquire rows: `301`
- Visibility gate: raw_norm >= `0.08`, cam_std >= `18.0`, crop_std >= `16.0`
- Temporal gate: last `3` predictions, max adjacent delta <= `12.0 deg`
- Sign mismatch ignores predictions/truth below `15.0 deg`

## Gate Summary

| gate | rows | coverage | mean abs err deg | max abs err deg | >bad err | >high err | sign mismatch | mean true abs | mean pred abs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all_reacquire | 301 | 1.000 | 8.230 | 47.286 | 0.070 | 0.003 | 0.040 | 63.808 | 60.162 |
| visible_reacquire | 230 | 0.764 | 8.634 | 47.286 | 0.065 | 0.004 | 0.000 | 33.860 | 27.972 |
| visible_reacquire_pred_delta_stable | 221 | 0.734 | 8.316 | 29.569 | 0.050 | 0.000 | 0.000 | 31.797 | 25.295 |
| visible_reacquire_pred_sign_stable | 50 | 0.166 | 7.581 | 47.286 | 0.160 | 0.020 | 0.000 | 116.225 | 121.112 |
| visible_reacquire_pred_delta_and_sign_stable | 42 | 0.140 | 5.561 | 29.569 | 0.095 | 0.000 | 0.000 | 120.542 | 124.330 |

## Worst Re-acquire Episodes

| file | seed | episode | outcome | reacquire rows | visible rows | sign mismatch | high error | max abs err deg | first step | last step |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| visual_yaw_align_rectangular_key_20ep_seed906500_steps.csv | 906517 | 17 | timeout | 96 | 26 | 12 | 0 | 44.236 | 720 | 999 |
| visual_yaw_align_rectangular_key_20ep_seed908500_steps.csv | 908516 | 16 | timeout | 205 | 204 | 0 | 1 | 47.286 | 286 | 999 |
