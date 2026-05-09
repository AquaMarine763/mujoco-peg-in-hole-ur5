# Guarded Policy Evaluation

- Generated: `2026-05-08T15:50:52`
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
- Guarded align/insert XY: `0.02/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.933 | 0.033 | 0.033 | 251.179 | 109.9 | 102.7 (0.93) | 1.000 | 0.00579 | 0.00944 |
| visual_camera | visual_camera | True | 0.900 | 0.100 | 0.000 | 223.574 | 104.4 | 95.9 (0.92) | 1.000 | 0.00720 | 0.01230 |
| visual_camera_control | visual_camera_control | True | 0.833 | 0.167 | 0.000 | 184.576 | 99.1 | 89.8 (0.91) | 1.000 | 0.01035 | 0.01507 |
| full_light_geometry | full_light_geometry | True | 0.867 | 0.133 | 0.000 | 206.326 | 104.1 | 94.8 (0.91) | 0.967 | 0.00976 | 0.01350 |
| full_contact_light | full_contact_light | True | 0.867 | 0.100 | 0.033 | 213.165 | 103.2 | 93.9 (0.91) | 1.000 | 0.00892 | 0.01234 |
| hard_full_light_bucket | full_light_geometry | True | 0.800 | 0.167 | 0.033 | 179.150 | 105.5 | 95.8 (0.91) | 0.967 | 0.01126 | 0.01471 |
