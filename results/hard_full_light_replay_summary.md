# Hard Full-Light Replay Summary

- Generated: `2026-05-06T18:05:00`
- Base model: `staged_crop_full_light_replay_750k_e4`
- Attempted model: `staged_crop_hard_full_light_replay_800k_e4`
- Observation mode: `image + near_hole_crop`

## Failure Analysis

The 200-episode combined full-light analysis of the current recommended model
shows that standard `full_light_geometry` is close to, but not fully stable:

| Episodes | Success | Collision | Timeout | Mean failure XY |
| ---: | ---: | ---: | ---: | ---: |
| 200 | 0.650 | 0.345 | 0.005 | 0.03413 |

The worst combined buckets are still dominated by delay 2, low filter alpha,
low or mid action scale, and low noise.

## Oracle Gain Scan

The targeted hard full-light bucket is difficult even for the staged oracle:

| Gain | Success | Collision | Timeout |
| ---: | ---: | ---: | ---: |
| 1.000 | 0.220 | 0.780 | 0.000 |
| 0.700 | 0.180 | 0.820 | 0.000 |
| 0.500 | 0.260 | 0.740 | 0.000 |
| 0.350 | 0.180 | 0.780 | 0.040 |
| 0.250 | 0.000 | 0.700 | 0.300 |
| 0.180 | 0.000 | 0.660 | 0.340 |

The formal 50k hard full-light dataset used `expert_action_gain=0.5` and still
only reached `0.267` oracle episode success.

## Result

The hard replay attempt did not improve the target bucket or the standard
matrix:

| Model | Standard full light | Full contact light | Hard full-light bucket |
| --- | ---: | ---: | ---: |
| `staged_crop_full_light_replay_750k_e4` | 0.580 | 0.590 | 0.330 |
| `staged_crop_hard_full_light_replay_800k_e4` | 0.550 | 0.530 | 0.310 |

## Conclusion

Do not promote `staged_crop_hard_full_light_replay_800k_e4`. The current
recommended model remains `staged_crop_full_light_replay_750k_e4`.

The failure suggests that adding rare success-only trajectories from an
unstable oracle is not enough for this bucket. The next useful work is to
improve the oracle/controller for delay-2 low-alpha full-light episodes, or to
add a deployment-time guarded two-stage insert controller instead of pushing
more BC weight onto this weak data.
