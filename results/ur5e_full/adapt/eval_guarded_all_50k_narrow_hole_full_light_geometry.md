# Guarded Policy Evaluation

- Generated: `2026-05-08T16:20:40`
- Model: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.08`
- Guard risk XY: `0.0`
- Guard scenario filter: `all`
- Guard blend: `1.0`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guarded align/insert XY: `0.02/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.980 | 0.020 | 0.000 | 260.851 | 109.8 | 102.4 (0.93) | 1.000 | 0.00527 | 0.00902 |
| visual_camera | visual_camera | True | 0.930 | 0.070 | 0.000 | 236.656 | 107.4 | 99.2 (0.92) | 1.000 | 0.00620 | 0.01110 |
| visual_camera_control | visual_camera_control | True | 0.860 | 0.140 | 0.000 | 200.369 | 103.2 | 94.5 (0.92) | 1.000 | 0.00853 | 0.01400 |
| full_light_geometry | full_light_geometry | True | 0.830 | 0.130 | 0.040 | 207.862 | 105.0 | 96.2 (0.92) | 0.990 | 0.00843 | 0.01401 |
| full_contact_light | full_contact_light | True | 0.840 | 0.140 | 0.020 | 200.303 | 102.9 | 94.0 (0.91) | 0.990 | 0.00936 | 0.01399 |
| hard_full_light_bucket | full_light_geometry | True | 0.780 | 0.180 | 0.040 | 174.283 | 106.4 | 97.2 (0.91) | 0.990 | 0.00986 | 0.01544 |
