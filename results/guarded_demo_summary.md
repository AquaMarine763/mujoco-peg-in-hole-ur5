# Guarded Policy Demo Summary

- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip`
- MuJoCo model: `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Observation: image policy with `--include-near-hole-crop --near-hole-crop-size 64`
- Guard wrapper: selective geometry/contact final-insertion guard from `peg_in_hole_mujoco/guarded_policy.py`
- Render: `overview` and `wrist_cam`, `640x480` each, concatenated side by side

| Scenario | Seed | Configuration | Success | Collision | Steps | Guard rows | Final XY | Final Z | Demo |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| full_light_geometry | 90000 | no guard | 1 | 0 | 12 | 0 | 0.00193 | 0.00551 | `demos/guarded_policy_full_light_no_guard.gif` |
| full_light_geometry | 90000 | guarded geometry | 1 | 0 | 11 | 11 | 0.00386 | 0.00463 | `demos/guarded_policy_full_light_guarded.gif` |
| hard bucket | 90005 | no guard | 0 | 1 | 11 | 0 | 0.02048 | 0.02625 | `demos/guarded_policy_hard_bucket_no_guard.gif` |
| hard bucket | 90005 | guarded geometry | 1 | 0 | 20 | 20 | 0.00475 | 0.00790 | `demos/guarded_policy_hard_bucket_guarded.gif` |

The hard-bucket pair is the main deployment-time diagnostic: with the same
randomized episode seed, the learned visual policy alone collides, while the
selective guarded wrapper completes the final insertion.
