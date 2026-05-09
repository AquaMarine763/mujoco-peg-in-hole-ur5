# Guarded Policy Evaluation

- Generated: `2026-05-08T22:01:32`
- Model: `checkpoints\ur5e_full\high_start\medium\sac_image_bc_20k_high_start_medium_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `555000`
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
| clean | none | True | 0.560 | 0.220 | 0.220 | 212.827 | 387.8 | 309.5 (0.80) | 0.970 | 0.01367 | 0.02037 |
| visual_camera | visual_camera | True | 0.530 | 0.250 | 0.220 | 211.854 | 396.2 | 293.4 (0.74) | 0.950 | 0.01541 | 0.01987 |
| visual_camera_control | visual_camera_control | True | 0.540 | 0.250 | 0.210 | 202.213 | 386.2 | 296.4 (0.77) | 0.930 | 0.01566 | 0.02057 |
| full_light_geometry | full_light_geometry | True | 0.520 | 0.220 | 0.260 | 221.610 | 403.7 | 309.4 (0.77) | 0.970 | 0.01398 | 0.01930 |
| full_contact_light | full_contact_light | True | 0.480 | 0.300 | 0.220 | 161.805 | 381.0 | 257.8 (0.68) | 0.910 | 0.01975 | 0.02145 |
| hard_full_light_bucket | full_light_geometry | True | 0.440 | 0.330 | 0.230 | 129.802 | 386.2 | 284.3 (0.74) | 0.900 | 0.02147 | 0.02222 |
