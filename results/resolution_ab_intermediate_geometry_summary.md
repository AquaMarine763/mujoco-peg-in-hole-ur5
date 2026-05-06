# Resolution A/B: Intermediate Geometry

- Generated: `2026-05-06T15:25:00`
- MuJoCo model path: `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Compared resolutions: `100x100` vs `128x128`
- Training setup: 20k success-only oracle samples, scratch SAC image actor,
  `30` BC epochs, batch size `512`, learning rate `0.0001`
- Geometry data bucket: `full_light_geometry` with identity control,
  `hole_half_size=0.025-0.029`, `peg_radius=0.012`, no hole-center or height
  jitter, `approach_xy_tolerance=0.02`

## Dataset Quality

| Resolution | Samples | Episodes | Oracle success | Oracle collision |
| --- | ---: | ---: | ---: | ---: |
| 100x100 | 20000 | 1294 | 0.997 | 0.001 |
| 128x128 | 20000 | 1304 | 0.997 | 0.000 |

## Training Loss

| Resolution | Final validation loss |
| --- | ---: |
| 100x100 | 0.164395 |
| 128x128 | 0.131773 |

The 128x128 model fits the BC validation split better, but that did not
translate into better rollout success.

## Rollout Evaluation

| Scenario | 100x100 success | 100x100 collision | 128x128 success | 128x128 collision |
| --- | ---: | ---: | ---: | ---: |
| Intermediate geometry, identity control | 0.880 | 0.120 | 0.860 | 0.140 |
| Narrow geometry, identity control | 0.750 | 0.180 | 0.720 | 0.180 |
| Clean | 0.670 | 0.320 | 0.180 | 0.780 |

## Conclusion

Directly increasing the whole wrist image from 100x100 to 128x128 is not a
clear win in this setup. The 128x128 model has lower BC loss but worse rollout
success and much worse clean generalization. The next geometry iteration should
therefore prioritize staged geometry curriculum and/or a targeted near-hole
crop over simply switching the whole image policy to 128x128.
