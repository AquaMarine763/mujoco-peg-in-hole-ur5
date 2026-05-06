# Guarded Oracle Summary

- Generated: `2026-05-06T18:35:00`
- Scenario: hard `full_light_geometry` bucket
- Control bucket: `delay=2`, `filter_alpha=0.55:0.70`, `action_scale=0.8:1.1`, `noise=0.0:0.00025`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`

## Controller Change

The new `guarded_two_stage` oracle keeps the original Cartesian staged target
but adds controller-side safeguards:

- optional prediction from the most recent applied action
- wider XY alignment gate before aggressive descent
- separate XY speed and downward Z speed limits
- CLI support in `scan_oracle_control_gain.py`, `collect_image_expert_dataset.py`,
  and `oracle_rollout.py`

The best candidate uses:

| Parameter | Value |
| --- | ---: |
| `oracle_mode` | `guarded_two_stage` |
| `expert_action_gain` | `1.0` |
| `guarded_align_xy_tolerance` | `0.025` |
| `guarded_insert_xy_tolerance` | `0.005` |
| `guarded_preinsert_height` | `0.000` |
| `guarded_max_xy_action` | `0.005` |
| `guarded_max_down_action` | `0.0035` |
| `guarded_max_up_action` | `0.005` |
| `guarded_prediction_steps` | `1.0` |

## Result

| Controller | Seed | Episodes | Gain | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| staged | 846000 | 50 | 0.5 | 0.300 | 0.700 | 0.000 |
| guarded_two_stage | 846000 | 50 | 1.0 | 0.520 | 0.480 | 0.000 |
| staged | 847000 | 100 | 0.5 | 0.280 | 0.720 | 0.000 |
| guarded_two_stage | 847000 | 100 | 1.0 | 0.440 | 0.560 | 0.000 |

## Conclusion

This is a positive oracle/controller result. The selected guarded controller
improves the hard bucket from `0.280` to `0.440` success on the 100-episode
check and lowers collision from `0.720` to `0.560`.

The next step is to collect a guarded hard full-light dataset from this
controller, then run a low-weight BC replay from the current recommended
750k crop model. Do not train from the earlier 800k hard replay model.
