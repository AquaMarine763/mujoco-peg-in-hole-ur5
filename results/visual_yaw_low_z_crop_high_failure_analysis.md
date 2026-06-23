# Low-Z Crop-High Failure Analysis

- Source summary: results\visual_yaw_low_z_crop_high_120ep_summary.md
- Runtime config: configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_eval.yaml
- Overall guarded result: 111/120, collision 0/120, timeout 9/120.
- All failures are timeouts; 7/9 finish with final yaw error above 150 deg, which keeps wrong-yaw-basin recovery as the main bottleneck.
- 2/9 failures have final yaw error at or below 30 deg; these are better candidates for a narrow descent/yaw-gate timing fix than for stronger yaw re-acquire.

## Category Counts

| Category | Count |
| --- | ---: |
| near_insert_yaw_gate_timeout | 2 |
| wrong_yaw_far_high_z | 5 |
| wrong_yaw_low_z_or_drift | 2 |

## Failed Episodes

| Base seed | Episode | Seed | Category | Final yaw deg | Final XY | Final Z | Min XY | Min Z | Near-XY steps | Low-Z steps | Insert-band steps | Visual-yaw steps | Descent steps |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 906500 | 8 | 906508 | wrong_yaw_far_high_z | 176.833 | 0.12545 | 0.10863 | 0.0675 | 0.10266 | 0 | 0 | 0 | 0 | 0 |
| 906500 | 10 | 906510 | wrong_yaw_far_high_z | 174.547 | 0.18167 | 0.12742 | 0.01327 | 0.06606 | 9 | 0 | 0 | 49 | 0 |
| 909500 | 2 | 909502 | near_insert_yaw_gate_timeout | 23.623 | 0.00153 | 0.05277 | 0.0001 | 0.00051 | 185 | 60 | 28 | 323 | 119 |
| 909500 | 6 | 909506 | near_insert_yaw_gate_timeout | 10.411 | 0.00393 | 0.0003 | 0.00045 | 6E-05 | 81 | 475 | 422 | 164 | 61 |
| 909500 | 13 | 909513 | wrong_yaw_far_high_z | 176.217 | 0.11469 | 0.11552 | 0.06413 | 0.10477 | 0 | 0 | 0 | 0 | 0 |
| 910500 | 13 | 910513 | wrong_yaw_far_high_z | 178.562 | 0.15508 | 0.09874 | 0.06203 | 0.09162 | 0 | 0 | 0 | 0 | 0 |
| 911500 | 4 | 911504 | wrong_yaw_far_high_z | 175.41 | 0.18638 | 0.11753 | 0.01376 | 0.0861 | 14 | 0 | 0 | 48 | 0 |
| 911500 | 13 | 911513 | wrong_yaw_low_z_or_drift | 175.605 | 0.0007 | 0.00278 | 0.00038 | 0.00045 | 819 | 754 | 735 | 0 | 786 |
| 911500 | 17 | 911517 | wrong_yaw_low_z_or_drift | 177.342 | 0.23649 | 0.05558 | 0.00054 | 5E-05 | 145 | 202 | 121 | 204 | 116 |

## Interpretation

- The low-Z crop-high estimator improved success without adding collision risk, but most residual failures are not small final-insertion misses; they are still yaw-basin failures that either never reach low Z or drift back out after briefly becoming near. A stronger generic descent push would likely be the wrong next move.
- The two low-yaw-error failures should be reviewed separately. Seed 909506 is especially close to success: final yaw is only 10.411 deg against a 10 deg gate and final Z is 0.3 mm.
- The next control experiment should be targeted: protect the visually aligned yaw target through low-Z descent and handle 170-179 deg re-acquire separately, instead of widening all brake or descent thresholds.
