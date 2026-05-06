# Guarded Deployment Demo Summary

Generated: 2026-05-07

## Setup

- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation: image policy with `--include-near-hole-crop --near-hole-crop-size 64`
- Guard candidate: `guard_scenario_filter=geometry`, `guard_start_xy=0.06`, `guard_start_z=0.08`, `guard_blend=0.75`, `guard_min_policy_steps=0`
- Render: `overview` and `wrist_cam`, `640x480` each, concatenated to `1280x480`

## Demo Results

| Demo | Seed | Success | Collision | Last step | Guard active steps | First guard step | First guard XY | First guard Z | Down-blocked steps | Final XY | Final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `demos\guarded_deployment_hard_bucket_no_guard_z08_hd.gif` | 90005 | 0 | 1 | 11 | 0 | n/a | n/a | n/a | 0 | 0.02048 | 0.02625 |
| `demos\guarded_deployment_hard_bucket_guarded_z08_hd.gif` | 90005 | 1 | 0 | 34 | 34 | 1 | 0.05259 | 0.07675 | 0 | 0.00478 | 0.00768 |
| `demos\guarded_deployment_full_light_guarded_z08_hd.gif` | 90000 | 1 | 0 | 11 | 11 | 1 | 0.04887 | 0.07752 | 0 | 0.00327 | 0.00721 |

The hard-bucket pair is the key deployment diagnostic. With the same seed, the
learned visual policy alone collides, while the guarded deployment wrapper
starts final-insertion correction at step 1 and reaches the success tolerance.

`guard_down_blocked` did not trigger in these demos because the optional
downward-action blocking switch was not enabled. A separate 100-episode
validation with that switch kept hard-bucket success at `0.530`, kept
full-contact success at `0.640`, and slightly reduced full-light success from
`0.710` to `0.700`, so it should stay optional for now.

## Trajectory CSVs

The matching per-step diagnostics are:

```text
demos\guarded_deployment_hard_bucket_no_guard_z08_trajectory.csv
demos\guarded_deployment_hard_bucket_guarded_z08_trajectory.csv
demos\guarded_deployment_full_light_guarded_z08_trajectory.csv
```

These CSVs include the learned policy action, guarded action, final action,
commanded/applied action after the environment control chain, randomized
episode parameters, and guard diagnostics such as `guard_activated`,
`guard_dist_xy`, and `guard_z_above_target`.
