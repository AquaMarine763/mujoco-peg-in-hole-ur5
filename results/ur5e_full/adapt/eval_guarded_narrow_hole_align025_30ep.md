# Guarded Policy Evaluation

- Generated: `2026-05-08T15:29:01`
- Model: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `30`
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
| clean | none | True | 0.800 | 0.200 | 0.000 | 168.063 | 91.8 | 84.6 (0.92) | 1.000 | 0.00874 | 0.01675 |
| visual_camera | visual_camera | True | 0.800 | 0.200 | 0.000 | 167.906 | 92.7 | 84.3 (0.91) | 1.000 | 0.00921 | 0.01675 |
| visual_camera_control | visual_camera_control | True | 0.800 | 0.200 | 0.000 | 159.966 | 92.9 | 83.7 (0.90) | 1.000 | 0.01123 | 0.01670 |
| full_light_geometry | full_light_geometry | True | 0.767 | 0.200 | 0.033 | 165.716 | 99.1 | 89.7 (0.91) | 0.967 | 0.01119 | 0.01670 |
| full_contact_light | full_contact_light | True | 0.767 | 0.233 | 0.000 | 151.085 | 91.6 | 82.3 (0.90) | 1.000 | 0.01115 | 0.01818 |
| hard_full_light_bucket | full_light_geometry | True | 0.667 | 0.333 | 0.000 | 97.966 | 87.4 | 77.7 (0.89) | 0.967 | 0.01418 | 0.02201 |
