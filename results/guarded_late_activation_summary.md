# Guarded Late-Activation Summary

Generated: 2026-05-07

## Goal

After BC correction experiments failed to produce a reliable gain, this pass
returned to deployment-time guarded insertion. The specific question was
whether the guard can activate later so the learned visual policy owns more of
the approach and coarse alignment.

Baseline policy:

```text
checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip
```

## Code Change

`GuardedPolicyConfig` now supports:

```text
guard_min_policy_steps
```

The guarded controller will not latch until at least this many policy actions
have been executed after reset. The argument is exposed in:

- `scripts\eval_guarded_policy.py`
- `scripts\run_policy_inference.py`
- `scripts\scan_guarded_policy_params.py`

Default value is `0`, preserving previous behavior.

## Late XY/Z Activation Scan

30 episodes per targeted scenario, seed `970000`.

| Candidate | Control | Full light | Full contact | Hard bucket | Mean success | Guard steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no guard | 0.867 | 0.667 | 0.600 | 0.233 | 0.592 | 0.0 |
| xy=0.03, z=0.08, blend=0.75 | 0.867 | 0.700 | 0.800 | 0.400 | 0.692 | 17.1 |
| xy=0.04, z=0.08, blend=0.75 | 0.867 | 0.700 | 0.800 | 0.367 | 0.683 | 20.3 |
| xy=0.06, z=0.08, blend=0.75 | 0.867 | 0.700 | 0.800 | 0.467 | 0.708 | 23.5 |
| xy=0.06, z=0.10, blend=0.75 | 0.867 | 0.700 | 0.800 | 0.467 | 0.708 | 23.5 |

The `z=0.08` and `z=0.10` rows are effectively equivalent in this setup. The
`xy=0.03` version reduces guard steps but gives up hard-bucket success.

## 100-Episode Validation

100 episodes per core scenario, seed `90000`.

| Candidate | Clean | Visual | Control | Full light | Full contact | Hard bucket |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no guard | 0.980 | 0.980 | 0.920 | 0.580 | 0.590 | 0.320 |
| xy=0.03, z=0.08, blend=0.75 | 0.980 | 0.980 | 0.920 | 0.650 | 0.660 | 0.410 |
| xy=0.06, z=0.08, blend=0.75 | 0.980 | 0.980 | 0.910 | 0.710 | 0.640 | 0.530 |
| xy=0.06, z=0.10, blend=0.75 | 0.980 | 0.980 | 0.910 | 0.710 | 0.640 | 0.530 |

## Min Policy Steps Scan

30 episodes per targeted scenario, seed `971000`.

| Candidate | Full light | Full contact | Hard bucket | Guard steps |
| --- | ---: | ---: | ---: | ---: |
| xy=0.06, z=0.08, min=0 | 0.600 | 0.567 | 0.233 | 23.9 |
| xy=0.06, z=0.08, min=5 | 0.567 | 0.600 | 0.200 | 21.1 |
| xy=0.06, z=0.08, min=10 | 0.633 | 0.633 | 0.200 | 12.6 |
| xy=0.06, z=0.08, min=15 | 0.700 | 0.667 | 0.200 | 7.7 |

Delaying guard activation can reduce guard steps, but it does not help the hard
bucket. For the current policy and initial-state distribution, hard-bucket
failures often need early guarded correction.

## Downward Blocking Check

The optional `--guard-block-down-when-unaligned` safety switch was validated on
the current recommended candidate with 100 episodes per core scenario, seed
`90000`.

| Scenario | Baseline success | Block-down success | Block-down collision | Block-down timeout |
| --- | ---: | ---: | ---: | ---: |
| clean | 0.980 | 0.980 | 0.020 | 0.000 |
| visual_camera | 0.980 | 0.980 | 0.020 | 0.000 |
| visual_camera_control | 0.910 | 0.910 | 0.090 | 0.000 |
| full_light_geometry | 0.710 | 0.700 | 0.240 | 0.060 |
| full_contact_light | 0.640 | 0.640 | 0.320 | 0.040 |
| hard_full_light_bucket | 0.530 | 0.530 | 0.460 | 0.010 |

This switch is useful as a conservative deployment option, but it did not
improve the current validation matrix and slightly reduced full-light success.
Keep it off by default unless a real-robot dry run shows that early downward
motion before XY alignment is a practical safety concern. Full details are in
`results\guarded_policy_block_down_validation_100ep.md`.

## Recommendation

Keep the deployment candidate as:

```text
guard_scenario_filter = geometry
guard_start_xy = 0.06
guard_start_z = 0.08
guard_blend = 0.75
guard_min_policy_steps = 0
guarded_max_down_action = 0.0035
guarded_align_xy_tolerance = 0.025
```

This is functionally equivalent to the previous `z=0.10` setting in the 100ep
validation, but `z=0.08` is slightly more conservative and better describes the
intended late-insert handoff. Do not set `guard_min_policy_steps > 0` for the
current recommended policy unless the real robot approach phase starts farther
from the hole and has been separately validated.

Also keep `guard_block_down_when_unaligned = False` for the default sim
candidate. Enable it only for hardware safety testing or a dedicated ablation.
