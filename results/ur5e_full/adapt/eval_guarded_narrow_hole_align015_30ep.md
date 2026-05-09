# Guarded Policy Evaluation

- Generated: `2026-05-08T15:26:56`
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
- Guarded align/insert XY: `0.015/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.833 | 0.133 | 0.033 | 212.387 | 103.3 | 96.1 (0.93) | 1.000 | 0.00791 | 0.01346 |
| visual_camera | visual_camera | True | 0.867 | 0.133 | 0.000 | 218.581 | 102.6 | 94.1 (0.92) | 1.000 | 0.00836 | 0.01361 |
| visual_camera_control | visual_camera_control | True | 0.833 | 0.167 | 0.000 | 193.371 | 99.9 | 90.7 (0.91) | 1.000 | 0.01084 | 0.01510 |
| full_light_geometry | full_light_geometry | True | 0.800 | 0.200 | 0.000 | 183.423 | 98.6 | 89.2 (0.90) | 0.967 | 0.01123 | 0.01644 |
| full_contact_light | full_contact_light | True | 0.800 | 0.167 | 0.033 | 192.362 | 99.8 | 90.5 (0.91) | 1.000 | 0.01029 | 0.01504 |
| hard_full_light_bucket | full_light_geometry | True | 0.767 | 0.200 | 0.033 | 169.538 | 104.2 | 94.5 (0.91) | 0.967 | 0.01219 | 0.01609 |
