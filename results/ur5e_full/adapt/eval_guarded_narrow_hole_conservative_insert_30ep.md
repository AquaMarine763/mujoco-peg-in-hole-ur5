# Guarded Policy Evaluation

- Generated: `2026-05-08T15:52:53`
- Model: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `30`
- Seed: `90000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.08`
- Guard risk XY: `0.0`
- Guard scenario filter: `all`
- Guard blend: `1.0`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guarded align/insert XY: `0.02/0.003`
- Guarded max XY/down/up action: `0.005/0.0025/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.933 | 0.033 | 0.033 | 279.602 | 130.8 | 123.6 (0.94) | 1.000 | 0.00584 | 0.00917 |
| visual_camera | visual_camera | True | 0.867 | 0.100 | 0.033 | 246.285 | 127.3 | 118.8 (0.93) | 1.000 | 0.00734 | 0.01199 |
| visual_camera_control | visual_camera_control | True | 0.800 | 0.167 | 0.033 | 215.330 | 123.9 | 114.6 (0.93) | 1.000 | 0.01043 | 0.01483 |
| full_light_geometry | full_light_geometry | True | 0.833 | 0.133 | 0.033 | 231.657 | 123.8 | 114.5 (0.92) | 0.967 | 0.00985 | 0.01347 |
| full_contact_light | full_contact_light | True | 0.833 | 0.100 | 0.067 | 237.539 | 122.2 | 112.9 (0.92) | 1.000 | 0.00902 | 0.01208 |
| hard_full_light_bucket | full_light_geometry | True | 0.800 | 0.167 | 0.033 | 202.680 | 122.6 | 112.9 (0.92) | 0.967 | 0.01128 | 0.01464 |
