# Low-Z Crop-High High-Yaw Reacquire Failure Analysis

- Source summary: results\visual_yaw_low_z_crop_high_high_yaw_120ep_summary.md
- Overall result: 112/120, collision 0/120, timeout 8/120.
- All remaining failures are timeouts; 8/8 finish above 150 deg yaw error and 0/8 finish at or below 30 deg.
- Compared with the low-Z crop-high baseline failure split, this reduces total timeouts from 9 to 8 but does not remove the wrong-yaw-basin pattern.

## Category Counts

| Category | Count |
| --- | ---: |
| wrong_yaw_far_high_z | 5 |
| wrong_yaw_low_z_or_drift | 3 |

## Failed Episodes

| Base seed | Episode | Seed | Category | Outcome | Final yaw deg | Final XY | Final Z | Min XY | Min Z | Near-XY steps | Low-Z steps | Insert-band steps | Visual-yaw steps | Descent steps |
| ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 906500 | 8 | 906508 | wrong_yaw_far_high_z | timeout | 176.833 | 0.12544 | 0.10863 | 0.0669 | 0.10261 | 0 | 0 | 0 | 0 | 0 |
| 906500 | 10 | 906510 | wrong_yaw_far_high_z | timeout | 174.545 | 0.18224 | 0.12698 | 0.01327 | 0.06572 | 9 | 0 | 0 | 49 | 0 |
| 908500 | 3 | 908503 | wrong_yaw_low_z_or_drift | timeout | 175.723 | 0.00123 | 0.00168 | 0.00032 | 0.00022 | 295 | 233 | 211 | 24 | 259 |
| 909500 | 2 | 909502 | wrong_yaw_low_z_or_drift | timeout | 175.815 | 0.18914 | 0.05624 | 0.00018 | 0.00066 | 210 | 116 | 54 | 350 | 169 |
| 909500 | 13 | 909513 | wrong_yaw_far_high_z | timeout | 176.226 | 0.11483 | 0.11552 | 0.06414 | 0.10477 | 0 | 0 | 0 | 0 | 0 |
| 910500 | 13 | 910513 | wrong_yaw_far_high_z | timeout | 178.562 | 0.15508 | 0.09874 | 0.06201 | 0.09162 | 0 | 0 | 0 | 0 | 0 |
| 911500 | 4 | 911504 | wrong_yaw_far_high_z | timeout | 175.336 | 0.15944 | 0.11384 | 0.01376 | 0.0861 | 14 | 0 | 0 | 46 | 0 |
| 911500 | 13 | 911513 | wrong_yaw_low_z_or_drift | timeout | 175.605 | 0.0007 | 0.00278 | 0.00038 | 0.00046 | 819 | 754 | 735 | 0 | 786 |

## Interpretation

- High-yaw-only re-acquire is safer than the paired narrow re-acquire with local descent, but it is still a marginal gain. The next useful change should inspect the remaining high-yaw timeouts and add a more explicit state condition for when re-acquire is allowed to reset or preserve the IK yaw target.
- The remaining near-insert timeout class is small; broadening descent globally is not justified by this result.
