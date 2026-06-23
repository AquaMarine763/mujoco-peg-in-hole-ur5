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
| temporal_gate | 60 | 47 | 0.783 | 0 | 13 | 477.6 | 136.954 | 12.64 | 42.28 | 117.98 |
| visible_brake | 80 | 70 | 0.875 | 0 | 10 | 413.6 | 108.248 | 10.20 | 24.94 | 101.05 |

## Failure Mode Breakdown

### temporal_gate

| mode | episodes |
| --- | ---: |
| timeout_wrong_yaw_basin | 10 |
| timeout_yaw_not_aligned | 2 |
| timeout_never_descended_low | 1 |

### visible_brake

| mode | episodes |
| --- | ---: |
| timeout_wrong_yaw_basin | 6 |
| timeout_yaw_not_aligned | 2 |
| timeout_low_z_or_insert_misaligned | 1 |
| timeout_never_descended_low | 1 |

## Correct High-Yaw Visual Evidence

Rows counted here have visible observations, true key yaw in the wrong basin, predicted yaw also large, and prediction/truth error within the configured threshold.

| run | outcome | episodes | episodes with evidence | evidence rows | xy-gate rows | raw-norm rows | inactive rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| temporal_gate | failure | 13 | 13 | 414 | 0 | 0 | 0 |
| temporal_gate | success | 47 | 47 | 291 | 0 | 0 | 0 |
| visible_brake | failure | 10 | 10 | 316 | 0 | 0 | 0 |
| visible_brake | success | 70 | 70 | 422 | 0 | 0 | 0 |

## Failure Episodes

| run | seed | ep | mode | yaw deg | min XY mm | min Z mm | final XY mm | final Z mm | low-Z mis | insert mis | VY steps/block | temp gate | low-vis brake | correct high-yaw evidence/xygate | last true/pred yaw | last phase | top VY reasons |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| temporal_gate | 910519 | 19 | timeout_never_descended_low | 0.415 | 0.12 | 39.54 | 1.02 | 40.43 | 0 | 0 | 305/289 | 57 | 6 | 39/0 | -0.415/2.458 | square_fast_settle | xy_gate:346; applied:284 |
| temporal_gate | 909502 | 2 | timeout_wrong_yaw_basin | 177.674 | 3.58 | 52.17 | 203.83 | 53.83 | 0 | 0 | 90/255 | 68 | 5 | 37/0 | -177.674/93.922 | recover_recenter | xy_gate:561; inactive_phase:158 |
| temporal_gate | 910500 | 0 | timeout_wrong_yaw_basin | 177.487 | 13.95 | 35.05 | 140.41 | 59.33 | 4 | 0 | 41/118 | 53 | 31 | 43/0 | -177.487/71.343 | recover_recenter | xy_gate:602; inactive_phase:242 |
| temporal_gate | 908510 | 10 | timeout_wrong_yaw_basin | 176.770 | 9.75 | 53.76 | 213.43 | 102.38 | 0 | 0 | 37/76 | 24 | 15 | 20/0 | -176.770/-14.342 | recover_recenter | xy_gate:556; inactive_phase:220 |
| temporal_gate | 910517 | 17 | timeout_wrong_yaw_basin | 176.637 | 13.72 | 46.36 | 148.19 | 47.21 | 0 | 0 | 24/93 | 57 | 14 | 22/0 | -176.637/61.751 | recover_recenter | xy_gate:733; inactive_phase:166 |
| temporal_gate | 909513 | 13 | timeout_wrong_yaw_basin | 175.263 | 28.80 | 60.55 | 187.23 | 102.88 | 0 | 0 | 41/94 | 50 | 3 | 33/0 | -175.263/-37.576 | recover_recenter | inactive_phase:347; xy_gate:344 |
| temporal_gate | 908516 | 16 | timeout_wrong_yaw_basin | 175.260 | 27.47 | 2.11 | 27.82 | 59.83 | 295 | 169 | 18/230 | 31 | 180 | 28/0 | -175.260/-179.504 | inactive | inactive_phase:379; xy_gate:351 |
| temporal_gate | 908508 | 8 | timeout_wrong_yaw_basin | 174.997 | 0.08 | 0.01 | 147.42 | 96.44 | 32 | 10 | 331/453 | 17 | 16 | 13/0 | -174.997/-46.583 | recover_recenter | applied:288; target_hold_z_gate:235 |
| temporal_gate | 909518 | 18 | timeout_wrong_yaw_basin | 173.042 | 16.05 | 53.96 | 150.61 | 54.97 | 0 | 0 | 40/106 | 46 | 27 | 37/0 | -173.042/-179.085 | recover_recenter | xy_gate:453; raw_norm_gate:217 |
| temporal_gate | 909519 | 19 | timeout_wrong_yaw_basin | 172.410 | 13.20 | 55.63 | 146.77 | 57.64 | 0 | 0 | 5/58 | 53 | 0 | 39/0 | -172.410/175.105 | recover_recenter | xy_gate:627; inactive_phase:240 |
| temporal_gate | 909517 | 17 | timeout_wrong_yaw_basin | 172.222 | 13.53 | 55.68 | 140.48 | 58.16 | 0 | 0 | 1/59 | 45 | 13 | 41/0 | -172.222/173.406 | recover_recenter | xy_gate:502; inactive_phase:265 |
| temporal_gate | 908503 | 3 | timeout_yaw_not_aligned | 14.922 | 0.69 | 23.01 | 3.15 | 77.52 | 34 | 0 | 82/137 | 39 | 16 | 29/0 | 14.922/2.118 | near_miss_descend | inactive_phase:439; raw_norm_gate:229 |
| temporal_gate | 909511 | 11 | timeout_yaw_not_aligned | 13.297 | 23.35 | 71.82 | 23.35 | 74.73 | 0 | 0 | 124/159 | 56 | 2 | 33/0 | 13.297/-1.468 | recover_recenter | xy_gate:352; inactive_phase:295 |
| visible_brake | 908501 | 1 | timeout_low_z_or_insert_misaligned | 0.483 | 7.60 | 0.30 | 103.58 | 60.29 | 315 | 23 | 222/237 | 0 | 79 | 40/0 | -0.483/1.829 | recover_recenter | inactive_phase:335; xy_gate:318 |
| visible_brake | 910519 | 19 | timeout_never_descended_low | 0.006 | 0.17 | 33.64 | 0.99 | 34.61 | 0 | 0 | 327/247 | 0 | 2 | 24/0 | -0.006/2.243 | square_fast_settle | xy_gate:333; applied:309 |
| visible_brake | 910517 | 17 | timeout_wrong_yaw_basin | 179.279 | 13.72 | 51.12 | 287.57 | 51.12 | 0 | 0 | 131/147 | 0 | 14 | 22/0 | -179.279/59.146 | recover_recenter | xy_gate:659; inactive_phase:166 |
| visible_brake | 906517 | 17 | timeout_wrong_yaw_basin | 177.273 | 15.11 | 30.41 | 148.47 | 38.07 | 83 | 0 | 58/67 | 0 | 9 | 30/0 | -177.273/174.176 | recover_recenter | xy_gate:596; inactive_phase:283 |
| visible_brake | 910500 | 0 | timeout_wrong_yaw_basin | 177.219 | 13.53 | 50.40 | 170.89 | 57.78 | 0 | 0 | 66/99 | 0 | 33 | 51/0 | -177.219/112.531 | recover_recenter | xy_gate:550; inactive_phase:295 |
| visible_brake | 907501 | 1 | timeout_wrong_yaw_basin | 176.499 | 22.78 | 58.76 | 172.03 | 77.06 | 0 | 0 | 57/127 | 0 | 70 | 42/0 | 176.499/177.877 | recover_recenter | xy_gate:446; raw_norm_gate:218 |
| visible_brake | 908516 | 16 | timeout_wrong_yaw_basin | 175.290 | 26.97 | 0.39 | 27.49 | 59.43 | 467 | 335 | 36/236 | 0 | 199 | 18/0 | -175.290/-179.751 | inactive | inactive_phase:365; xy_gate:267 |
| visible_brake | 908508 | 8 | timeout_wrong_yaw_basin | 169.377 | 0.61 | 0.13 | 94.64 | 81.02 | 206 | 134 | 159/165 | 0 | 40 | 37/0 | -169.377/-157.737 | recover_recenter | xy_gate:438; inactive_phase:185 |
| visible_brake | 908503 | 3 | timeout_yaw_not_aligned | 14.961 | 0.49 | 20.02 | 2.82 | 77.85 | 38 | 0 | 108/147 | 0 | 15 | 27/0 | 14.961/2.091 | near_miss_descend | inactive_phase:435; raw_norm_gate:229 |
| visible_brake | 908510 | 10 | timeout_yaw_not_aligned | 12.098 | 1.05 | 4.25 | 2.00 | 4.88 | 45 | 39 | 123/191 | 0 | 63 | 25/0 | 12.098/1.284 | square_fast_settle | xy_gate:315; raw_norm_gate:263 |

## Interpretation Hints

- `timeout_wrong_yaw_basin` means the final key yaw error is near a wrong asymmetric basin, usually around 180 deg for the key profile.
- `timeout_yaw_not_aligned` means yaw is still outside the success tolerance but not in the fully flipped basin.
- `timeout_low_z_or_insert_misaligned` means the episode reached low-Z or insertion-band states while still failing the yaw/XY success gates.
- Large `low-vis brake` or `temporal gate` counts with no success usually means the current safety patch is converting risky descent into timeout rather than fixing yaw estimation.
