# Low-Z Crop-High High-Yaw Reacquire 120ep Summary

- Config: configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_reacquire_high_yaw_action_selection_eval.yaml
- Base low-Z crop-high reference: 111/120, collision 0/120, timeout 9/120.
- Historical visible-brake reference before low-Z crop: 104/120, collision 0/120, timeout 16/120.
- Result: 112/120, collision 0/120, timeout 8/120, success rate 0.9333.
- Interpretation: this is numerically the best same-six-seed result so far, but the gain over low-Z crop-high is only +1/120 and one seed regresses, so keep it diagnostic until the residual timeout modes are better understood.

| Base seed | Episodes | Success | Collision | Timeout | Success rate | Mean steps | Mean final yaw deg | Mean min XY |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 906500 | 20 | 18 | 0 | 2 | 0.9 | 408.9 | 19.173 | 0.00434 |
| 907500 | 20 | 20 | 0 | 0 | 1 | 302 | 1.714 | 0.00055 |
| 908500 | 20 | 19 | 0 | 1 | 0.95 | 394.6 | 10.717 | 0.00042 |
| 909500 | 20 | 18 | 0 | 2 | 0.9 | 413.4 | 19.657 | 0.00341 |
| 910500 | 20 | 19 | 0 | 1 | 0.95 | 344.8 | 10.876 | 0.00344 |
| 911500 | 20 | 18 | 0 | 2 | 0.9 | 441.4 | 19.13 | 0.00107 |
| **Total** | **120** | **112** | **0** | **8** | **0.9333** | **384.2** | **13.544** | **0.0022** |

## Seed-Level Comparison

| Base seed | Low-Z crop-high baseline | High-yaw reacquire | Delta |
| ---: | ---: | ---: | ---: |
| 906500 | 18/20 | 18/20 | 0 |
| 907500 | 20/20 | 20/20 | 0 |
| 908500 | 20/20 | 19/20 | -1 |
| 909500 | 17/20 | 18/20 | +1 |
| 910500 | 19/20 | 19/20 | 0 |
| 911500 | 17/20 | 18/20 | +1 |
