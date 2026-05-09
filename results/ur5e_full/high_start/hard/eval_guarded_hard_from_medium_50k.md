# Guarded Policy Evaluation

- Generated: `2026-05-08T22:55:08`
- Model: `checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `557000`
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
| clean | none | True | 0.400 | 0.120 | 0.480 | 134.709 | 632.4 | 449.9 (0.71) | 0.970 | 0.01079 | 0.02202 |
| visual_camera | visual_camera | True | 0.370 | 0.220 | 0.410 | 84.625 | 592.2 | 370.9 (0.63) | 0.870 | 0.02737 | 0.03200 |
| visual_camera_control | visual_camera_control | True | 0.350 | 0.340 | 0.310 | 148.189 | 522.5 | 331.6 (0.63) | 0.870 | 0.02651 | 0.02685 |
| full_light_geometry | full_light_geometry | True | 0.220 | 0.320 | 0.460 | 18.090 | 628.7 | 382.8 (0.61) | 0.820 | 0.03625 | 0.02916 |
| full_contact_light | full_contact_light | True | 0.340 | 0.300 | 0.360 | 88.911 | 565.0 | 361.5 (0.64) | 0.880 | 0.02703 | 0.02601 |
| hard_full_light_bucket | full_light_geometry | True | 0.270 | 0.360 | 0.370 | 134.884 | 557.2 | 348.4 (0.63) | 0.880 | 0.02534 | 0.02987 |
