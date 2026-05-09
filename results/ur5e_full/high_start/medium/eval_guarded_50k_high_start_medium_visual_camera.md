# Guarded Policy Evaluation

- Generated: `2026-05-08T22:25:41`
- Model: `checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `556000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.12`
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
| clean | none | True | 0.680 | 0.060 | 0.260 | 267.471 | 436.2 | 347.6 (0.80) | 1.000 | 0.00778 | 0.01420 |
| visual_camera | visual_camera | True | 0.620 | 0.140 | 0.240 | 205.128 | 405.5 | 318.2 (0.78) | 0.990 | 0.01035 | 0.01769 |
| visual_camera_control | visual_camera_control | True | 0.510 | 0.210 | 0.280 | 185.716 | 431.1 | 339.2 (0.79) | 0.950 | 0.01374 | 0.02008 |
| full_light_geometry | full_light_geometry | True | 0.510 | 0.230 | 0.260 | 180.833 | 421.4 | 329.4 (0.78) | 0.960 | 0.01472 | 0.01967 |
| full_contact_light | full_contact_light | True | 0.510 | 0.260 | 0.230 | 193.333 | 399.0 | 299.0 (0.75) | 0.940 | 0.01791 | 0.02225 |
| hard_full_light_bucket | full_light_geometry | True | 0.490 | 0.250 | 0.260 | 237.262 | 424.2 | 317.1 (0.75) | 0.950 | 0.01619 | 0.02028 |
