# Guarded Policy Evaluation

- Generated: `2026-05-08T17:59:46`
- Model: `checkpoints\ur5e_full\correction\sac_image_bc_50k_narrow_correction_8k_w10_e2.zip`
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
| clean | none | True | 0.970 | 0.020 | 0.010 | 259.146 | 110.2 | 102.8 (0.93) | 1.000 | 0.00528 | 0.00899 |
| visual_camera | visual_camera | True | 0.940 | 0.050 | 0.010 | 244.713 | 109.1 | 101.0 (0.93) | 1.000 | 0.00585 | 0.01026 |
| visual_camera_control | visual_camera_control | True | 0.870 | 0.130 | 0.000 | 205.465 | 103.6 | 95.0 (0.92) | 1.000 | 0.00828 | 0.01361 |
| full_light_geometry | full_light_geometry | True | 0.830 | 0.130 | 0.040 | 208.140 | 105.1 | 96.3 (0.92) | 1.000 | 0.00839 | 0.01401 |
| full_contact_light | full_contact_light | True | 0.840 | 0.140 | 0.020 | 200.600 | 102.9 | 94.1 (0.91) | 0.990 | 0.00930 | 0.01399 |
| hard_full_light_bucket | full_light_geometry | True | 0.780 | 0.180 | 0.040 | 174.828 | 106.6 | 97.4 (0.91) | 0.990 | 0.00977 | 0.01543 |
