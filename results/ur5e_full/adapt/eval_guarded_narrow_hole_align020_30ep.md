# Guarded Policy Evaluation

- Generated: `2026-05-08T15:30:22`
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
- Guarded align/insert XY: `0.02/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.867 | 0.133 | 0.000 | 208.332 | 98.3 | 91.1 (0.93) | 1.000 | 0.00777 | 0.01369 |
| visual_camera | visual_camera | True | 0.867 | 0.133 | 0.000 | 208.690 | 99.0 | 90.6 (0.91) | 1.000 | 0.00827 | 0.01385 |
| visual_camera_control | visual_camera_control | True | 0.833 | 0.167 | 0.000 | 184.245 | 96.6 | 87.3 (0.90) | 1.000 | 0.01077 | 0.01520 |
| full_light_geometry | full_light_geometry | True | 0.800 | 0.200 | 0.000 | 176.594 | 96.8 | 87.5 (0.90) | 0.967 | 0.01119 | 0.01657 |
| full_contact_light | full_contact_light | True | 0.800 | 0.167 | 0.033 | 184.226 | 97.6 | 88.3 (0.90) | 1.000 | 0.01020 | 0.01521 |
| hard_full_light_bucket | full_light_geometry | True | 0.767 | 0.200 | 0.033 | 163.073 | 101.2 | 91.5 (0.90) | 0.967 | 0.01218 | 0.01625 |
