# Guarded Policy Evaluation

- Generated: `2026-05-09T11:51:55`
- Model: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_50k_high_start_hard_correction_smoke.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `20`
- Seed: `574000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.12`
- Guard risk XY: `0.0`
- Guard scenario filter: `all`
- Guard blend: `1.0`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guarded oracle mode: `guarded_two_stage`
- Guarded align/insert XY: `0.02/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.500 | 0.300 | 0.200 | 322.050 | 473.4 | 288.3 (0.61) | 0.800 | 0.02280 | 0.02569 |
| visual_camera | visual_camera | True | 0.250 | 0.300 | 0.450 | 122.464 | 627.6 | 416.9 (0.66) | 0.950 | 0.01765 | 0.02958 |
| visual_camera_control | visual_camera_control | True | 0.400 | 0.300 | 0.300 | 145.114 | 501.4 | 306.9 (0.61) | 0.950 | 0.02896 | 0.02664 |
| full_light_geometry | full_light_geometry | True | 0.300 | 0.200 | 0.500 | 152.017 | 650.9 | 460.8 (0.71) | 0.950 | 0.01572 | 0.02354 |
| full_contact_light | full_contact_light | True | 0.250 | 0.400 | 0.350 | 187.548 | 561.5 | 330.0 (0.59) | 1.000 | 0.01883 | 0.03104 |
| hard_full_light_bucket | full_light_geometry | True | 0.350 | 0.400 | 0.250 | 247.254 | 485.6 | 295.2 (0.61) | 0.850 | 0.02161 | 0.02894 |
