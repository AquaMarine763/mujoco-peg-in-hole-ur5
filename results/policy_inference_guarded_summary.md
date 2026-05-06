# Guarded Policy Inference Summary

- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip`
- MuJoCo model: `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Observation: image policy with `--include-near-hole-crop --near-hole-crop-size 64`
- Deployment path: `scripts/run_policy_inference.py`
- Guard wrapper: `--guarded-policy --guard-scenario-filter geometry --guard-blend 0.75`

`run_policy_inference.py` now applies the guarded wrapper before the safety
filter, so the final action still passes through action limiting, workspace
limiting, and optional action smoothing. The trace CSV records
`guard_enabled`, `guard_active`, `guard_should_activate`,
`guard_can_activate`, `guard_activated`, `guard_down_blocked`,
`guard_steps_since_reset`, `guard_dist_xy`, `guard_z_above_target`,
`policy_action_*`, `guarded_action_*`, `final_action_*`, `raw_action_*`, and
`safe_action_*`.

| Scenario | Seed | Configuration | Success | Collision | Steps | Guard steps | Final XY | Final Z | Trace |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| visual_camera_control | 90000 | guarded geometry blend 0.75 | 1 | 0 | 10 | 0 | 0.00498 | 0.00674 | `results/policy_inference_visual_camera_control_guarded_smoke.csv` |
| hard bucket | 90005 | no guard | 0 | 1 | 11 | 0 | 0.02048 | 0.02625 | `results/policy_inference_hard_bucket_no_guard_smoke.csv` |
| hard bucket | 90005 | guarded geometry blend 0.75 | 1 | 0 | 34 | 34 | 0.00479 | 0.00768 | `results/policy_inference_hard_bucket_guarded_trace_rich_smoke.csv` |

The deployment smoke reproduces the intended two-stage behavior: normal control
randomization is not guarded, while the hard full-light bucket uses guarded
final insertion and succeeds on the matched seed where the learned policy alone
collides.

The matching HD GIF demo summary is in
`results\guarded_deployment_demo_summary.md`.
