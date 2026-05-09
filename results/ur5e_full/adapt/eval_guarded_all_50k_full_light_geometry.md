# Guarded Policy Evaluation

- Generated: `2026-05-08T15:58:38`
- Model: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip`
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
| clean | none | True | 0.970 | 0.020 | 0.010 | 259.283 | 110.1 | 102.8 (0.93) | 1.000 | 0.00531 | 0.00899 |
| visual_camera | visual_camera | True | 0.910 | 0.080 | 0.010 | 229.929 | 107.1 | 98.8 (0.92) | 1.000 | 0.00655 | 0.01149 |
| visual_camera_control | visual_camera_control | True | 0.860 | 0.140 | 0.000 | 199.394 | 102.8 | 94.0 (0.91) | 1.000 | 0.00881 | 0.01400 |
| full_light_geometry | full_light_geometry | True | 0.830 | 0.150 | 0.020 | 199.804 | 102.7 | 93.8 (0.91) | 0.980 | 0.00904 | 0.01469 |
| full_contact_light | full_contact_light | True | 0.830 | 0.150 | 0.020 | 195.557 | 102.1 | 93.2 (0.91) | 0.990 | 0.00958 | 0.01442 |
| hard_full_light_bucket | full_light_geometry | True | 0.770 | 0.180 | 0.050 | 171.709 | 106.7 | 97.5 (0.91) | 0.980 | 0.01017 | 0.01538 |
