# Low-Z Crop-High Reacquire Comparison

- Baseline config: configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_eval.yaml
- High-yaw-only config: configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_reacquire_high_yaw_action_selection_eval.yaml
- Narrow local-descent config: configs\sim2real\multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_crop_high_wrong_basin_reacquire_narrow_eval.yaml

| Variant | Seeds | Episodes | Success | Collision | Timeout | Note |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| low_z_crop_high_baseline | 906500,909500 | 40 | 35 | 0 | 5 | reference subset from 111/120 run |
| low_z_crop_high_wrong_basin_reacquire_narrow | 906500,909500 | 40 | 35 | 0 | 5 | local re-acquire descent enabled |
| low_z_crop_high_high_yaw_only | 906500,909500 | 40 | 36 | 0 | 4 | local re-acquire descent disabled |
| low_z_crop_high_baseline | 906500..911500 | 120 | 111 | 0 | 9 | same six seed reference |
| low_z_crop_high_high_yaw_only | 906500..911500 | 120 | 112 | 0 | 8 | current diagnostic best, marginal +1/120 |

## Decision

- Keep high-yaw-only as the better diagnostic candidate: it reaches 112/120 with zero collision.
- Do not promote it as final: the improvement over low-Z crop-high is only +1/120 and all remaining failures are still high-yaw-basin timeouts.
- Keep local re-acquire descent disabled for now: on the paired 40ep subset it does not improve over the low-Z baseline.
