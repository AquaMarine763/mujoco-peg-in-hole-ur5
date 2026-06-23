# Visual Yaw Re-acquire Trace Analysis

Offline diagnostic only: this compares visual-yaw predictions with sim truth already recorded in traces.

- Traces: `3`
- Re-acquire rows: `0`
- Visibility gate: raw_norm >= `0.08`, cam_std >= `18.0`, crop_std >= `16.0`
- Temporal gate: last `3` predictions, max adjacent delta <= `12.0 deg`
- Sign mismatch ignores predictions/truth below `15.0 deg`

## Gate Summary

| gate | rows | coverage | mean abs err deg | max abs err deg | >bad err | >high err | sign mismatch | mean true abs | mean pred abs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all_reacquire | 0 | nan | nan | nan | nan | nan | nan | nan | nan |
| visible_reacquire | 0 | nan | nan | nan | nan | nan | nan | nan | nan |
| visible_reacquire_pred_delta_stable | 0 | nan | nan | nan | nan | nan | nan | nan | nan |
| visible_reacquire_pred_sign_stable | 0 | nan | nan | nan | nan | nan | nan | nan | nan |
| visible_reacquire_pred_delta_and_sign_stable | 0 | nan | nan | nan | nan | nan | nan | nan | nan |

## Worst Re-acquire Episodes

| file | seed | episode | outcome | reacquire rows | visible rows | sign mismatch | high error | max abs err deg | first step | last step |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
