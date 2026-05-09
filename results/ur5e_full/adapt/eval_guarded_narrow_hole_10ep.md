# Guarded Policy Evaluation

- Generated: `2026-05-08T15:15:30`
- Model: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `10`
- Seed: `90000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.08`
- Guard risk XY: `0.0`
- Guard scenario filter: `all`
- Guard blend: `0.75`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guarded align/insert XY: `0.025/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.800 | 0.200 | 0.000 | 161.336 | 89.6 | 87.1 (0.97) | 1.000 | 0.00831 | 0.01706 |
| visual_camera | visual_camera | True | 0.800 | 0.200 | 0.000 | 159.160 | 91.1 | 87.6 (0.96) | 1.000 | 0.00881 | 0.01694 |
| visual_camera_control | visual_camera_control | True | 0.800 | 0.200 | 0.000 | 157.277 | 94.2 | 90.5 (0.96) | 1.000 | 0.00946 | 0.01673 |
| full_light_geometry | full_light_geometry | True | 0.800 | 0.200 | 0.000 | 167.172 | 98.9 | 95.3 (0.96) | 1.000 | 0.00924 | 0.01696 |
| full_contact_light | full_contact_light | True | 0.800 | 0.200 | 0.000 | 167.281 | 93.8 | 90.3 (0.96) | 1.000 | 0.00875 | 0.01718 |
| hard_full_light_bucket | full_light_geometry | True | 0.700 | 0.300 | 0.000 | 113.642 | 88.1 | 84.1 (0.95) | 1.000 | 0.01143 | 0.02108 |
