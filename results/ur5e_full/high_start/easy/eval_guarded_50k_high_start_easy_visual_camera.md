# Guarded Policy Evaluation

- Generated: `2026-05-08T19:51:39`
- Model: `checkpoints\ur5e_full\high_start\easy\sac_image_bc_50k_high_start_easy_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `542000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.1`
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
| clean | none | True | 0.670 | 0.120 | 0.210 | 175.024 | 317.6 | 274.6 (0.86) | 1.000 | 0.00904 | 0.01575 |
| visual_camera | visual_camera | True | 0.540 | 0.180 | 0.280 | 92.929 | 351.3 | 297.3 (0.85) | 0.940 | 0.01440 | 0.01833 |
| visual_camera_control | visual_camera_control | True | 0.500 | 0.270 | 0.230 | 141.670 | 327.9 | 257.3 (0.78) | 0.940 | 0.01714 | 0.02027 |
| full_light_geometry | full_light_geometry | True | 0.530 | 0.270 | 0.200 | 140.194 | 314.1 | 257.2 (0.82) | 0.960 | 0.01599 | 0.02007 |
| full_contact_light | full_contact_light | True | 0.530 | 0.340 | 0.130 | 190.909 | 275.2 | 215.6 (0.78) | 0.950 | 0.01739 | 0.02262 |
| hard_full_light_bucket | full_light_geometry | True | 0.530 | 0.260 | 0.210 | 132.940 | 320.5 | 250.6 (0.78) | 0.910 | 0.01719 | 0.01811 |
