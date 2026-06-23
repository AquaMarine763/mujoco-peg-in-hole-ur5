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
| hold_xy60 | 40 | 34 | 0.850 | 0 | 6 | 436.0 | 121.007 | 12.60 | 40.71 | 75.19 |
| reacquire_narrow | 40 | 35 | 0.875 | 1 | 4 | 417.6 | 109.040 | 14.80 | 36.05 | 120.55 |
| reacquire_narrow_gated | 40 | 34 | 0.850 | 0 | 6 | 440.1 | 146.775 | 11.48 | 47.96 | 117.68 |

## Failure Mode Breakdown

### baseline

| mode | episodes |
| --- | ---: |
| timeout_wrong_yaw_basin | 4 |
| timeout_yaw_not_aligned | 1 |

### hold_xy60

| mode | episodes |
| --- | ---: |
| timeout_wrong_yaw_basin | 4 |
| timeout_never_descended_low | 1 |
| timeout_yaw_not_aligned | 1 |

### reacquire_narrow

| mode | episodes |
| --- | ---: |
| timeout_wrong_yaw_basin | 3 |
| collision | 1 |
| timeout_never_descended_low | 1 |

### reacquire_narrow_gated

| mode | episodes |
| --- | ---: |
| timeout_wrong_yaw_basin | 5 |
| timeout_never_descended_low | 1 |

## Correct High-Yaw Visual Evidence

Rows counted here have visible observations, true key yaw in the wrong basin, predicted yaw also large, and prediction/truth error within the configured threshold.

| run | outcome | episodes | episodes with evidence | evidence rows | xy-gate rows | raw-norm rows | inactive rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | failure | 5 | 5 | 112 | 0 | 0 | 0 |
| baseline | success | 35 | 35 | 230 | 0 | 0 | 0 |
| hold_xy60 | failure | 6 | 6 | 153 | 0 | 0 | 0 |
| hold_xy60 | success | 34 | 34 | 217 | 0 | 0 | 0 |
| reacquire_narrow | failure | 5 | 5 | 190 | 0 | 0 | 0 |
| reacquire_narrow | success | 35 | 35 | 242 | 0 | 0 | 0 |
| reacquire_narrow_gated | failure | 6 | 6 | 181 | 0 | 0 | 0 |
| reacquire_narrow_gated | success | 34 | 34 | 212 | 0 | 0 | 0 |

## Failure Episodes

| run | seed | ep | mode | yaw deg | min XY mm | min Z mm | final XY mm | final Z mm | low-Z mis | insert mis | VY steps/block | temp gate | low-vis brake | correct high-yaw evidence/xygate | last true/pred yaw | last phase | top VY reasons |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| baseline | 908510 | 10 | timeout_wrong_yaw_basin | 176.925 | 9.76 | 52.65 | 221.40 | 103.49 | 0 | 0 | 61/77 | 0 | 16 | 19/0 | -176.925/-14.455 | recover_recenter | xy_gate:553; inactive_phase:221 |
| baseline | 908503 | 3 | timeout_wrong_yaw_basin | 175.650 | 23.09 | 39.18 | 136.04 | 110.34 | 2 | 0 | 54/83 | 0 | 29 | 27/0 | -175.650/-160.142 | align_hover | inactive_phase:453; raw_norm_gate:238 |
| baseline | 908516 | 16 | timeout_wrong_yaw_basin | 175.285 | 27.12 | 1.77 | 27.53 | 59.29 | 466 | 329 | 36/219 | 0 | 182 | 18/0 | -175.285/-179.845 | inactive | inactive_phase:378; xy_gate:266 |
| baseline | 906517 | 17 | timeout_wrong_yaw_basin | 172.836 | 15.11 | 33.16 | 159.27 | 43.92 | 62 | 0 | 58/67 | 0 | 9 | 29/0 | -172.836/173.347 | recover_recenter | xy_gate:597; inactive_phase:283 |
| baseline | 908508 | 8 | timeout_yaw_not_aligned | 19.430 | 0.38 | 17.86 | 17.46 | 31.22 | 234 | 8 | 511/425 | 0 | 5 | 19/0 | 19.430/-5.070 | recover_lift | applied:467; inactive_phase:161 |
| hold_xy60 | 906514 | 14 | timeout_never_descended_low | 2.652 | 0.22 | 66.51 | 1.93 | 72.60 | 0 | 0 | 738/683 | 0 | 2 | 14/0 | 2.652/2.312 | near_miss_descend | applied:738; inactive_phase:109 |
| hold_xy60 | 908508 | 8 | timeout_wrong_yaw_basin | 176.274 | 0.51 | 0.00 | 152.40 | 60.79 | 33 | 11 | 397/534 | 0 | 0 | 5/0 | -176.274/-1.644 | recover_recenter | applied:348; target_hold_z_gate:347 |
| hold_xy60 | 908503 | 3 | timeout_wrong_yaw_basin | 175.407 | 23.08 | 79.73 | 85.85 | 105.18 | 0 | 0 | 49/50 | 0 | 1 | 23/0 | -175.407/-155.091 | recover_recenter | inactive_phase:373; raw_norm_gate:296 |
| hold_xy60 | 908516 | 16 | timeout_wrong_yaw_basin | 175.289 | 27.06 | 2.36 | 27.49 | 59.18 | 261 | 150 | 72/243 | 0 | 179 | 27/0 | -175.289/-179.649 | inactive | inactive_phase:378; xy_gate:314 |
| hold_xy60 | 906517 | 17 | timeout_wrong_yaw_basin | 172.186 | 15.11 | 53.89 | 151.66 | 64.22 | 0 | 0 | 50/67 | 0 | 17 | 47/0 | -172.186/178.229 | recover_recenter | xy_gate:471; inactive_phase:272 |
| hold_xy60 | 908510 | 10 | timeout_yaw_not_aligned | 24.236 | 9.64 | 41.76 | 31.83 | 41.76 | 0 | 0 | 65/132 | 0 | 67 | 37/0 | -24.236/-57.440 | recover_recenter | xy_gate:462; inactive_phase:218 |
| reacquire_narrow | 908508 | 8 | collision | 18.171 | 20.31 | 7.01 | 84.81 | 7.01 | 24 | 23 | 116/271 | 0 | 3 | 34/0 | 18.171/-4.448 | align_hover | inactive_phase:188; raw_norm_gate:134 |
| reacquire_narrow | 908513 | 13 | timeout_never_descended_low | 5.287 | 0.51 | 47.04 | 1.29 | 57.05 | 0 | 0 | 201/390 | 0 | 30 | 57/0 | 5.287/2.139 | square_fast_settle | raw_norm_gate:337; applied:177 |
| reacquire_narrow | 908510 | 10 | timeout_wrong_yaw_basin | 176.549 | 9.78 | 56.89 | 201.81 | 104.76 | 0 | 0 | 43/251 | 0 | 14 | 22/0 | -176.549/-14.166 | recover_recenter | xy_gate:372; inactive_phase:213 |
| reacquire_narrow | 908516 | 16 | timeout_wrong_yaw_basin | 174.622 | 30.61 | 23.32 | 143.25 | 23.32 | 59 | 0 | 125/287 | 0 | 41 | 38/0 | -174.622/-178.851 | recover_recenter | inactive_phase:324; xy_gate:317 |
| reacquire_narrow | 906517 | 17 | timeout_wrong_yaw_basin | 170.570 | 12.81 | 45.99 | 171.58 | 50.10 | 0 | 0 | 77/246 | 0 | 7 | 39/0 | 170.570/174.388 | recover_recenter | xy_gate:415; inactive_phase:283 |
| reacquire_narrow_gated | 906514 | 14 | timeout_never_descended_low | 2.683 | 0.05 | 66.47 | 3.47 | 74.47 | 0 | 0 | 738/683 | 0 | 2 | 14/0 | 2.683/2.196 | near_miss_descend | applied:738; inactive_phase:109 |
| reacquire_narrow_gated | 908510 | 10 | timeout_wrong_yaw_basin | 176.770 | 9.63 | 53.79 | 213.47 | 102.45 | 0 | 0 | 61/77 | 0 | 16 | 20/0 | -176.770/-14.394 | recover_recenter | xy_gate:556; inactive_phase:220 |
| reacquire_narrow_gated | 908503 | 3 | timeout_wrong_yaw_basin | 175.636 | 23.09 | 40.23 | 109.97 | 101.97 | 0 | 0 | 56/84 | 0 | 20 | 31/0 | -175.636/-158.530 | recover_recenter | inactive_phase:429; xy_gate:358 |
| reacquire_narrow_gated | 908508 | 8 | timeout_wrong_yaw_basin | 175.525 | 20.31 | 61.22 | 193.50 | 99.19 | 0 | 0 | 108/130 | 0 | 22 | 40/0 | -175.525/-11.920 | recover_recenter | xy_gate:419; raw_norm_gate:267 |
| reacquire_narrow_gated | 908516 | 16 | timeout_wrong_yaw_basin | 175.357 | 0.68 | 10.28 | 81.06 | 62.56 | 362 | 241 | 270/489 | 0 | 2 | 20/0 | -175.357/171.847 | inactive | inactive_phase:388; large_xy_low_z_brake:319 |
| reacquire_narrow_gated | 906517 | 17 | timeout_wrong_yaw_basin | 174.680 | 15.11 | 55.76 | 104.62 | 82.25 | 0 | 0 | 60/222 | 0 | 11 | 56/0 | -174.680/174.180 | recover_recenter | xy_gate:335; inactive_phase:275 |

## Interpretation Hints

- `timeout_wrong_yaw_basin` means the final key yaw error is near a wrong asymmetric basin, usually around 180 deg for the key profile.
- `timeout_yaw_not_aligned` means yaw is still outside the success tolerance but not in the fully flipped basin.
- `timeout_low_z_or_insert_misaligned` means the episode reached low-Z or insertion-band states while still failing the yaw/XY success gates.
- Large `low-vis brake` or `temporal gate` counts with no success usually means the current safety patch is converting risky descent into timeout rather than fixing yaw estimation.
