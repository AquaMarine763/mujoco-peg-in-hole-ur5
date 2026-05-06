# Near-Hole Crop Summary

- Generated: `2026-05-06T17:00:00`
- MuJoCo model path: `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Observation mode: `image`
- New observation when enabled:
  - `cam_image`: `100x100x1`
  - `near_hole_crop`: centered `64x64x1` crop from `cam_image`
- Training note: existing datasets do not need to be regenerated. When
  `--include-near-hole-crop` is passed, the BC trainer derives
  `near_hole_crop` from `cam_images` if `near_hole_crops` is absent.

## Failure Motivation

The no-crop staged geometry model still failed mostly by colliding with
non-trivial XY error:

| Bucket | Success | Collision | Timeout | Mean failure XY |
| --- | ---: | ---: | ---: | ---: |
| Intermediate geometry, no crop | 0.600 | 0.400 | 0.000 | 0.05343 |
| Narrow geometry, no crop | 0.340 | 0.580 | 0.090 | 0.06195 |

This matches the suspected failure mode: the policy often descends or contacts
before lateral alignment is robust.

## Result

The crop model was trained from scratch on the staged dataset mix with
`cam_image + near_hole_crop`. It is the strongest geometry candidate so far.

| Model | Crop | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `staged_intermediate_narrow_650k_e5` | no | 0.960 | 0.960 | 0.850 | 0.390 | 0.400 |
| `staged_crop_650k_scratch_e16` | yes | 0.960 | 0.960 | 0.880 | 0.530 | 0.570 |

Target bucket comparison:

| Model | Crop | Intermediate geometry | Narrow geometry |
| --- | --- | ---: | ---: |
| `staged_intermediate_narrow_650k_e5` | no | 0.510 | 0.330 |
| `staged_crop_650k_scratch_e16` | yes | 0.890 | 0.770 |

Same-seed narrow failure analysis (`seed=740000`) shows the collision reduction
directly:

| Model | Crop | Success | Collision | Timeout | Mean failure XY |
| --- | --- | ---: | ---: | ---: | ---: |
| `staged_intermediate_narrow_650k_e5` | no | 0.340 | 0.580 | 0.090 | 0.06195 |
| `staged_crop_650k_scratch_e16` | yes | 0.830 | 0.150 | 0.020 | 0.04806 |

## Conclusion

The near-hole crop is a clear win. It improves geometry robustness while also
recovering `visual_camera_control` from `0.850` to `0.880`. The next step should
repeat and extend this crop model with stronger control replay and then test
whether it can reach `visual_camera_control >= 0.90` while keeping
`full_light_geometry >= 0.55`.
