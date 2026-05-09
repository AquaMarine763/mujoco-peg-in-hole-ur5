# Guarded Policy Evaluation

- Generated: `2026-05-08T20:07:09`
- Model: `checkpoints\ur5e_full\high_start\easy\sac_image_bc_50k_high_start_easy_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `534000`
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
| clean | none | True | 0.620 | 0.150 | 0.230 | 172.054 | 331.8 | 280.9 (0.85) | 1.000 | 0.01044 | 0.01712 |
| visual_camera | visual_camera | True | 0.630 | 0.170 | 0.200 | 188.058 | 330.5 | 266.2 (0.81) | 0.960 | 0.01235 | 0.01692 |
| visual_camera_control | visual_camera_control | True | 0.590 | 0.260 | 0.150 | 183.267 | 293.1 | 233.2 (0.80) | 0.960 | 0.01580 | 0.02044 |
| full_light_geometry | full_light_geometry | True | 0.580 | 0.210 | 0.210 | 178.777 | 323.3 | 267.0 (0.83) | 0.960 | 0.01402 | 0.01862 |
| full_contact_light | full_contact_light | True | 0.540 | 0.220 | 0.240 | 200.525 | 345.9 | 280.5 (0.81) | 0.960 | 0.01294 | 0.01932 |
| hard_full_light_bucket | full_light_geometry | True | 0.480 | 0.300 | 0.220 | 129.050 | 322.3 | 259.4 (0.80) | 0.940 | 0.01779 | 0.02128 |
