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
| policy only | 0.980 | 0.980 | 0.920 | 0.580 | 0.600 | - |
| guarded blend 0.75 | 0.980 | 0.980 | 0.910 | 0.710 | 0.640 | 0.530 |

The UR5e adapter can now be treated as the default simulation model on this
branch. The next branch step is to keep new UR5e training/evaluation outputs
under `results/ur5e/mainline/` or matching `ur5e` artifact directories instead
of adding more root-level experiment folders.
