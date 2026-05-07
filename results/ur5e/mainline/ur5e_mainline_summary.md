# UR5e Mainline Summary

- Branch: `feature/ur5e-mainline`
- Default model: `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Legacy model: `assets/ur5_peg_in_hole.xml`
- Recommended policy:
  `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip`
- Observation: image plus `near_hole_crop=64`

## Smoke Checks

| Check | Result |
| --- | --- |
| default robot model inspection | PASS |
| legacy UR5-like robot model inspection | PASS |
| default state random rollout | PASS, random policy collision expected |
| default image random rollout | PASS, random policy collision expected |
| default oracle rollout | 3/3 success, 0/3 collision |

## Policy Evaluation

| Evaluation | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| policy only | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 | - |
| guarded blend 0.75 | 0.980 | 0.980 | 0.920 | 0.710 | 0.650 | 0.530 |
| guarded blend 0.50 | 0.980 | 0.980 | 0.910 | 0.620 | 0.650 | 0.490 |
| guarded align 0.020 blend 1.0 | 0.980 | 0.980 | 0.920 | 0.630 | 0.630 | 0.420 |

Config-driven result files:

- `results/ur5e/mainline/eval_matrix_image_crop.md`
- `results/ur5e/mainline/eval_guarded_image_crop.md`
- `results/ur5e/mainline/eval_guarded_image_crop_blend050.md`
- `results/ur5e/mainline/eval_guarded_image_crop_align020_blend100.md`
- `results/ur5e/mainline/scan_guarded_policy_focused.md`

The focused 30-episode guarded scan suggested `blend=0.50` and
`align_xy=0.020` as possible challengers, but 100-episode validation did not
beat the existing `blend=0.75` deployment candidate. Keep the recommended
guarded setting as:

```text
guard_scenario_filter = geometry
guard_start_xy = 0.06
guard_start_z = 0.08
guard_blend = 0.75
guard_min_policy_steps = 0
guarded_align_xy_tolerance = 0.025
guarded_max_down_action = 0.0035
```

The UR5e adapter can now be treated as the default simulation model on this
branch. The next branch step is to keep new UR5e training/evaluation outputs
under `results/ur5e/mainline/` or matching `ur5e` artifact directories instead
of adding more root-level experiment folders.
