# Guarded Policy Parameter Scan Summary

- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip`
- MuJoCo model: `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Observation: image policy with `--include-near-hole-crop --near-hole-crop-size 64`
- Guard scenario filter: `geometry`
- Validation seed: `90000`
- Validation episodes: `100` per scenario

The focused 30-episode scan found `guard_blend=0.75` as the best candidate.
It keeps the same activation geometry as the previous guarded wrapper
(`guard_start_xy=0.06`, `guard_start_z=0.10`, `guarded_max_down_action=0.0035`,
`guarded_align_xy_tolerance=0.025`) but blends 75% guarded action with 25%
learned policy action during final insertion.

| Configuration | Clean | Visual camera | Visual camera control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no guard | 0.980 | 0.980 | 0.910 | 0.580 | 0.600 | 0.320 |
| guard blend 0.75 | 0.980 | 0.980 | 0.900 | 0.710 | 0.650 | 0.530 |
| guard blend 1.0 | 0.980 | 0.980 | 0.910 | 0.690 | 0.660 | 0.480 |

Conclusion: promote `guard_blend=0.75` as the next guarded deployment candidate.
It improves the hard bucket over both no guard and the previous `blend=1.0`
wrapper. Full contact is slightly lower than `blend=1.0`, so keep `blend=1.0`
as a fallback baseline for contact-heavy evaluation.

The guard is disabled in `clean`, `visual_camera`, and `visual_camera_control`
when using `--guard-scenario-filter geometry`; their guarded-step count is zero.
Small differences in those rows should be treated as evaluation variance rather
than a guarded-action effect.

Detailed results:

- Focused scan: `results/guarded_policy_param_scan_focused.md`
- 100-episode blend validation: `results/guarded_policy_param_scan_blend_validation_100ep.md`
