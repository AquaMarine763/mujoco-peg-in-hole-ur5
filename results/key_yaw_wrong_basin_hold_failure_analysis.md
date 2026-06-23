# Key Yaw Failure Mode Analysis

Offline sim diagnostic for rectangular-key tight-yaw traces.

- Wrong-yaw basin threshold: `90.0 deg`
- Yaw failure threshold: `10.0 deg`
- Near XY threshold: `8.0 mm`
- Low-Z threshold: `30.0 mm`
- Final prediction window: `80` steps

## Run Summary

| run | episodes | success | success rate | collision | timeout | mean steps | mean failure yaw deg | mean failure min XY mm | mean failure min Z mm | mean failure final XY mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 40 | 35 | 0.875 | 0 | 5 | 431.6 | 144.025 | 15.09 | 28.92 | 112.34 |
| wrong_basin_hold_wide | 40 | 33 | 0.825 | 0 | 7 | 520.0 | 105.056 | 11.29 | 35.06 | 68.82 |
| wrong_basin_hold_xy60 | 40 | 34 | 0.850 | 0 | 6 | 436.0 | 121.007 | 12.60 | 40.71 | 75.19 |

## Failure Mode Breakdown

### baseline

| mode | episodes |
| --- | ---: |
| timeout_wrong_yaw_basin | 4 |
| timeout_yaw_not_aligned | 1 |

### wrong_basin_hold_wide

| mode | episodes |
| --- | ---: |
| timeout_wrong_yaw_basin | 3 |
| timeout_yaw_not_aligned | 3 |
| timeout_never_descended_low | 1 |

### wrong_basin_hold_xy60

| mode | episodes |
| --- | ---: |
| timeout_wrong_yaw_basin | 4 |
| timeout_never_descended_low | 1 |
| timeout_yaw_not_aligned | 1 |

## Correct High-Yaw Visual Evidence

Rows counted here have visible observations, true key yaw in the wrong basin, predicted yaw also large, and prediction/truth error within the configured threshold.

| run | outcome | episodes | episodes with evidence | evidence rows | xy-gate rows | raw-norm rows | inactive rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | failure | 5 | 5 | 112 | 0 | 0 | 0 |
| baseline | success | 35 | 35 | 230 | 0 | 0 | 0 |
| wrong_basin_hold_wide | failure | 7 | 7 | 384 | 0 | 0 | 0 |
| wrong_basin_hold_wide | success | 33 | 33 | 225 | 0 | 0 | 0 |
| wrong_basin_hold_xy60 | failure | 6 | 6 | 153 | 0 | 0 | 0 |
| wrong_basin_hold_xy60 | success | 34 | 34 | 217 | 0 | 0 | 0 |

## Failure Episodes

| run | seed | ep | mode | yaw deg | min XY mm | min Z mm | final XY mm | final Z mm | low-Z mis | insert mis | VY steps/block | temp gate | low-vis brake | correct high-yaw evidence/xygate | last true/pred yaw | last phase | top VY reasons |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| baseline | 908510 | 10 | timeout_wrong_yaw_basin | 176.925 | 9.76 | 52.65 | 221.40 | 103.49 | 0 | 0 | 61/77 | 0 | 16 | 19/0 | -176.925/-14.455 | recover_recenter | xy_gate:553; inactive_phase:221 |
| baseline | 908503 | 3 | timeout_wrong_yaw_basin | 175.650 | 23.09 | 39.18 | 136.04 | 110.34 | 2 | 0 | 54/83 | 0 | 29 | 27/0 | -175.650/-160.142 | align_hover | inactive_phase:453; raw_norm_gate:238 |
| baseline | 908516 | 16 | timeout_wrong_yaw_basin | 175.285 | 27.12 | 1.77 | 27.53 | 59.29 | 466 | 329 | 36/219 | 0 | 182 | 18/0 | -175.285/-179.845 | inactive | inactive_phase:378; xy_gate:266 |
| baseline | 906517 | 17 | timeout_wrong_yaw_basin | 172.836 | 15.11 | 33.16 | 159.27 | 43.92 | 62 | 0 | 58/67 | 0 | 9 | 29/0 | -172.836/173.347 | recover_recenter | xy_gate:597; inactive_phase:283 |
| baseline | 908508 | 8 | timeout_yaw_not_aligned | 19.430 | 0.38 | 17.86 | 17.46 | 31.22 | 234 | 8 | 511/425 | 0 | 5 | 19/0 | 19.430/-5.070 | recover_lift | applied:467; inactive_phase:161 |
| wrong_basin_hold_wide | 906514 | 14 | timeout_never_descended_low | 2.817 | 0.01 | 60.84 | 1.92 | 71.74 | 0 | 0 | 732/686 | 0 | 2 | 188/0 | 2.817/2.472 | near_miss_descend | applied:551; wrong_basin_hold_applied:181 |
| wrong_basin_hold_wide | 908503 | 3 | timeout_wrong_yaw_basin | 175.669 | 23.09 | 40.18 | 118.96 | 104.73 | 0 | 0 | 57/94 | 0 | 37 | 32/0 | -175.669/-156.529 | recover_lift | inactive_phase:438; xy_gate:348 |
| wrong_basin_hold_wide | 908516 | 16 | timeout_wrong_yaw_basin | 175.596 | 15.57 | 50.12 | 137.41 | 96.14 | 0 | 0 | 432/491 | 0 | 8 | 27/0 | -175.596/-57.496 | recover_recenter | wrong_basin_hold_applied:419; inactive_phase:302 |
| wrong_basin_hold_wide | 906517 | 17 | timeout_wrong_yaw_basin | 175.131 | 15.11 | 32.90 | 142.85 | 43.96 | 63 | 0 | 59/69 | 0 | 10 | 30/0 | -175.131/172.715 | recover_recenter | xy_gate:596; inactive_phase:282 |
| wrong_basin_hold_wide | 908512 | 12 | timeout_yaw_not_aligned | 78.571 | 15.47 | 4.99 | 17.41 | 74.63 | 182 | 82 | 339/423 | 0 | 84 | 34/0 | 78.571/74.850 | recover_recenter | inactive_phase:337; wrong_basin_hold_applied:311 |
| wrong_basin_hold_wide | 908518 | 18 | timeout_yaw_not_aligned | 78.472 | 0.08 | 0.36 | 16.40 | 97.56 | 27 | 9 | 428/398 | 0 | 18 | 41/0 | 78.472/84.206 | align_hover | xy_gate:311; wrong_basin_hold_applied:287 |
| wrong_basin_hold_wide | 908510 | 10 | timeout_yaw_not_aligned | 49.134 | 9.70 | 56.06 | 46.79 | 75.02 | 0 | 0 | 323/441 | 0 | 23 | 32/0 | 49.134/63.102 | recover_recenter | wrong_basin_hold_applied:294; xy_gate:270 |
| wrong_basin_hold_xy60 | 906514 | 14 | timeout_never_descended_low | 2.652 | 0.22 | 66.51 | 1.93 | 72.60 | 0 | 0 | 738/683 | 0 | 2 | 14/0 | 2.652/2.312 | near_miss_descend | applied:738; inactive_phase:109 |
| wrong_basin_hold_xy60 | 908508 | 8 | timeout_wrong_yaw_basin | 176.274 | 0.51 | 0.00 | 152.40 | 60.79 | 33 | 11 | 397/534 | 0 | 0 | 5/0 | -176.274/-1.644 | recover_recenter | applied:348; target_hold_z_gate:347 |
| wrong_basin_hold_xy60 | 908503 | 3 | timeout_wrong_yaw_basin | 175.407 | 23.08 | 79.73 | 85.85 | 105.18 | 0 | 0 | 49/50 | 0 | 1 | 23/0 | -175.407/-155.091 | recover_recenter | inactive_phase:373; raw_norm_gate:296 |
| wrong_basin_hold_xy60 | 908516 | 16 | timeout_wrong_yaw_basin | 175.289 | 27.06 | 2.36 | 27.49 | 59.18 | 261 | 150 | 72/243 | 0 | 179 | 27/0 | -175.289/-179.649 | inactive | inactive_phase:378; xy_gate:314 |
| wrong_basin_hold_xy60 | 906517 | 17 | timeout_wrong_yaw_basin | 172.186 | 15.11 | 53.89 | 151.66 | 64.22 | 0 | 0 | 50/67 | 0 | 17 | 47/0 | -172.186/178.229 | recover_recenter | xy_gate:471; inactive_phase:272 |
| wrong_basin_hold_xy60 | 908510 | 10 | timeout_yaw_not_aligned | 24.236 | 9.64 | 41.76 | 31.83 | 41.76 | 0 | 0 | 65/132 | 0 | 67 | 37/0 | -24.236/-57.440 | recover_recenter | xy_gate:462; inactive_phase:218 |

## Interpretation Hints

- `timeout_wrong_yaw_basin` means the final key yaw error is near a wrong asymmetric basin, usually around 180 deg for the key profile.
- `timeout_yaw_not_aligned` means yaw is still outside the success tolerance but not in the fully flipped basin.
- `timeout_low_z_or_insert_misaligned` means the episode reached low-Z or insertion-band states while still failing the yaw/XY success gates.
- Large `low-vis brake` or `temporal gate` counts with no success usually means the current safety patch is converting risky descent into timeout rather than fixing yaw estimation.
