# Crop Control Replay Summary

- Generated: `2026-05-06T17:35:00`
- MuJoCo model path: `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Observation mode: `image + near_hole_crop`
- Crop size: `64x64`

## New Data

Two success-only replay datasets were added:

| Dataset | Samples | Episodes | Oracle success | Oracle collision | Purpose |
| --- | ---: | ---: | ---: | ---: | --- |
| `visual_camera_control_delay2_lowalpha_lowscale_lownoise_success_50k_oracle.npz` | 50000 | 2061 | 0.799 | 0.201 | Hard control bucket: delay 2, low filter alpha, low action scale, low noise. |
| `full_light_geometry_control_success_50k_oracle.npz` | 50000 | 4003 | 0.553 | 0.445 | Combined geometry + control distribution used by standard `full_light_geometry`. |

The second dataset is difficult even for the oracle, which explains why
`full_light_geometry` is currently the main bottleneck.

## Standard Matrix

| Model | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| `staged_crop_650k_scratch_e16` | 0.960 | 0.960 | 0.880 | 0.530 | 0.570 |
| `staged_crop_control_replay_700k_e4` | 0.960 | 0.970 | 0.900 | 0.520 | 0.570 |
| `staged_crop_full_light_replay_750k_e4` | 0.980 | 0.980 | 0.910 | 0.580 | 0.590 |

## Target Buckets

| Model | Intermediate geometry | Narrow geometry |
| --- | ---: | ---: |
| `staged_crop_control_replay_700k_e4` | 0.800 | 0.790 |
| `staged_crop_full_light_replay_750k_e4` | 0.920 | 0.790 |

## Control Failure Analysis

On the 200-episode `visual_camera_control` failure-analysis seed, the final
model improves success from `0.820` to `0.845`. The hardest remaining buckets
are still low action scale, delay 2, and low filter alpha.

## Conclusion

`staged_crop_full_light_replay_750k_e4` is the current strongest crop-enabled
model. It reaches the near-term target of `visual_camera_control >= 0.90` while
keeping `full_light_geometry >= 0.55`. The next bottleneck is still combined
geometry + control under the standard `full_light_geometry` distribution.
