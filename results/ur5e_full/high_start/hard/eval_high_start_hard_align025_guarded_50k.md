# Guarded Policy Evaluation

- Generated: `2026-05-09T01:55:36`
- Model: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `571000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.12`
- Guard risk XY: `0.0`
- Guard scenario filter: `all`
- Guard blend: `1.0`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guarded oracle mode: `guarded_two_stage`
- Guarded align/insert XY: `0.025/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.530 | 0.050 | 0.420 | 194.474 | 591.1 | 431.2 (0.73) | 0.970 | 0.01013 | 0.01894 |
| visual_camera | visual_camera | True | 0.370 | 0.170 | 0.460 | 110.376 | 617.7 | 409.0 (0.66) | 0.950 | 0.01532 | 0.02699 |
| visual_camera_control | visual_camera_control | True | 0.310 | 0.330 | 0.360 | 62.560 | 562.5 | 335.1 (0.60) | 0.900 | 0.03037 | 0.03363 |
| full_light_geometry | full_light_geometry | True | 0.340 | 0.280 | 0.380 | 163.424 | 567.4 | 383.6 (0.68) | 0.890 | 0.01957 | 0.02512 |
| full_contact_light | full_contact_light | True | 0.290 | 0.320 | 0.390 | 107.777 | 572.2 | 363.3 (0.63) | 0.870 | 0.02864 | 0.03327 |
| hard_full_light_bucket | full_light_geometry | True | 0.270 | 0.340 | 0.390 | 164.292 | 575.4 | 356.5 (0.62) | 0.860 | 0.02226 | 0.02793 |
