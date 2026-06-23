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
| high_yaw_arm | 40 | 35 | 0.875 | 0 | 5 | 438.4 | 141.258 | 17.65 | 31.70 | 134.71 |

## Failure Mode Breakdown

### high_yaw_arm

| mode | episodes |
| --- | ---: |
| timeout_wrong_yaw_basin | 4 |
| timeout_never_descended_low | 1 |

## Correct High-Yaw Visual Evidence

Rows counted here have visible observations, true key yaw in the wrong basin, predicted yaw also large, and prediction/truth error within the configured threshold.

| run | outcome | episodes | episodes with evidence | evidence rows | xy-gate rows | raw-norm rows | inactive rows |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| high_yaw_arm | failure | 5 | 5 | 155 | 0 | 0 | 0 |
| high_yaw_arm | success | 35 | 35 | 256 | 0 | 0 | 0 |

## Failure Episodes

| run | seed | ep | mode | yaw deg | min XY mm | min Z mm | final XY mm | final Z mm | low-Z mis | insert mis | VY steps/block | temp gate | low-vis brake | correct high-yaw evidence/xygate | last true/pred yaw | last phase | top VY reasons |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| high_yaw_arm | 908517 | 17 | timeout_never_descended_low | 3.528 | 0.23 | 56.65 | 1.47 | 72.02 | 0 | 0 | 322/320 | 0 | 1 | 44/0 | 3.528/2.659 | near_miss_descend | xy_gate:418; applied:322 |
| high_yaw_arm | 908510 | 10 | timeout_wrong_yaw_basin | 176.770 | 9.73 | 53.76 | 213.44 | 102.39 | 0 | 0 | 61/76 | 0 | 15 | 20/0 | -176.770/-14.382 | recover_recenter | xy_gate:556; inactive_phase:220 |
| high_yaw_arm | 908503 | 3 | timeout_wrong_yaw_basin | 175.656 | 23.09 | 34.38 | 132.11 | 108.24 | 10 | 0 | 55/89 | 0 | 34 | 27/0 | -175.656/-157.366 | align_hover | inactive_phase:448; raw_norm_gate:241 |
| high_yaw_arm | 908516 | 16 | timeout_wrong_yaw_basin | 175.436 | 34.89 | 0.60 | 186.27 | 92.01 | 392 | 292 | 48/96 | 0 | 47 | 23/0 | -175.436/-49.513 | recover_recenter | xy_gate:406; inactive_phase:284 |
| high_yaw_arm | 908508 | 8 | timeout_wrong_yaw_basin | 174.902 | 20.31 | 13.10 | 140.28 | 18.23 | 302 | 164 | 65/146 | 0 | 81 | 41/0 | -174.902/-170.378 | recover_lift | xy_gate:509; inactive_phase:240 |

## Interpretation Hints

- `timeout_wrong_yaw_basin` means the final key yaw error is near a wrong asymmetric basin, usually around 180 deg for the key profile.
- `timeout_yaw_not_aligned` means yaw is still outside the success tolerance but not in the fully flipped basin.
- `timeout_low_z_or_insert_misaligned` means the episode reached low-Z or insertion-band states while still failing the yaw/XY success gates.
- Large `low-vis brake` or `temporal gate` counts with no success usually means the current safety patch is converting risky descent into timeout rather than fixing yaw estimation.
