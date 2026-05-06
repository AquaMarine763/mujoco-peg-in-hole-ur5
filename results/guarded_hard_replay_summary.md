# Guarded Hard Replay Summary

- Generated: `2026-05-06T19:15:00`
- Base model: `staged_crop_full_light_replay_750k_e4`
- Observation mode: `image + near_hole_crop`
- New dataset: `image_expert_ur5e_adapter_fixedcam_full_light_geometry_delay2_lowalpha_lownoise_guarded_success_50k_oracle.npz`

## Dataset

The guarded two-stage oracle produced a better hard-bucket dataset than the
previous gain-0.5 hard oracle, but it is still a difficult distribution:

| Dataset | Samples | Episodes | Oracle success | Oracle collision |
| --- | ---: | ---: | ---: | ---: |
| old gain-0.5 hard full-light | 50000 | 7065 | 0.267 | 0.733 |
| guarded hard full-light | 50000 | 5127 | 0.376 | 0.608 |

The guarded data uses `delay=2`, `filter_alpha=0.55:0.70`,
`action_scale=0.8:1.1`, and `noise=0.0:0.00025`.

## Replay Attempts

Two replay attempts were tested from the current recommended 750k model:

| Attempt | Guarded weight | LR | Epochs | Final val loss |
| --- | ---: | ---: | ---: | ---: |
| `staged_crop_guarded_hard_replay_800k_e4` | 0.08 | 0.000002 | 4 | 0.110405 |
| `staged_crop_guarded_hard_replay_light_790k_e2` | 0.04 | 0.000001 | 2 | 0.100362 |

## Standard Matrix

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| `staged_crop_full_light_replay_750k_e4` | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 |
| `staged_crop_guarded_hard_replay_800k_e4` | 0.960 | 0.950 | 0.880 | 0.550 | 0.530 |
| `staged_crop_guarded_hard_replay_light_790k_e2` | 0.980 | 0.980 | 0.910 | 0.550 | 0.580 |

## Hard Bucket

All models below were evaluated on the same seed `850000` with
`delay=2`, low filter alpha, low noise, and full light-geometry randomization.

| Model | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| `staged_crop_full_light_replay_750k_e4` | 0.330 | 0.660 | 0.010 |
| `staged_crop_guarded_hard_replay_800k_e4` | 0.340 | 0.660 | 0.000 |
| `staged_crop_guarded_hard_replay_light_790k_e2` | 0.340 | 0.660 | 0.000 |

## Conclusion

Do not promote either guarded replay model. The guarded oracle improves data
collection quality, but direct BC replay only gives a negligible hard-bucket
gain and either degrades or fails to improve the standard full-light matrix.

The current recommended policy remains
`staged_crop_full_light_replay_750k_e4`.

The next useful step is not more hard success-only BC. The policy needs either
deployment-time guarded insertion around the learned visual policy, or a
training objective that teaches the policy the guarded correction behavior
directly through online interaction or DAgger-style relabeling.
