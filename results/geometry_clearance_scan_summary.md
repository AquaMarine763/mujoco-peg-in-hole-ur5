# Geometry Clearance Scan Summary

- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip`
- MuJoCo model: `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Observation: image policy with `--include-near-hole-crop --near-hole-crop-size 64`
- Episodes: `30` per tier/scenario/guard configuration
- Seed: `930000`
- Guarded candidate: `guard_blend=0.75`

| Tier | Mean clearance | Full light no guard | Full light guard 0.75 | Hard no guard | Hard guard 0.75 | Full contact no guard | Full contact guard 0.75 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | 14.9 mm | 0.567 | 0.600 | 0.200 | 0.400 | 0.500 | 0.633 |
| medium | 9.9 mm | 0.533 | 0.667 | 0.300 | 0.333 | 0.500 | 0.567 |
| narrow | 6.9 mm | 0.300 | 0.533 | 0.167 | 0.367 | 0.300 | 0.600 |
| tight | 4.4 mm | 0.200 | 0.467 | 0.133 | 0.267 | 0.200 | 0.533 |

Conclusion: use `medium` as the next curriculum target, but do not switch the
whole training distribution to narrow or tight yet. Medium clearance is still
learnable in standard `full_light_geometry` with guarded insertion (`0.667`),
but the hard delay/low-filter bucket remains weak (`0.333`). The next dataset
should therefore mix current wide + medium clearance and emphasize
hard-control correction near the hole.

The scan also shows that `guard_blend=0.75` is still the better default for
clearance curriculum: it consistently beats no guard and is generally more
robust than full override, especially in hard-control and narrowed geometry
settings.

Detailed reports:

- Targeted geometry/hard scan: `results/geometry_clearance_scan_targeted_30ep.md`
- Full-contact scan: `results/geometry_clearance_scan_full_contact_30ep.md`
