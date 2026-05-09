# Guarded Policy Evaluation

- Generated: `2026-05-09T11:56:49`
- Model: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `20`
- Seed: `574000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.12`
- Guard risk XY: `0.0`
- Guard scenario filter: `all`
- Guard blend: `1.0`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guarded oracle mode: `guarded_two_stage`
- Guarded align/insert XY: `0.02/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.450 | 0.350 | 0.200 | 255.140 | 451.9 | 277.5 (0.61) | 0.800 | 0.03024 | 0.02294 |
| visual_camera | visual_camera | True | 0.250 | 0.250 | 0.500 | 70.793 | 649.5 | 421.5 (0.65) | 0.950 | 0.02728 | 0.03578 |
| visual_camera_control | visual_camera_control | True | 0.400 | 0.350 | 0.250 | 176.774 | 482.9 | 289.3 (0.60) | 0.900 | 0.03250 | 0.03077 |
| full_light_geometry | full_light_geometry | True | 0.250 | 0.300 | 0.450 | 170.074 | 608.9 | 427.0 (0.70) | 0.950 | 0.01852 | 0.02764 |
| full_contact_light | full_contact_light | True | 0.300 | 0.350 | 0.350 | 260.720 | 562.4 | 333.0 (0.59) | 0.950 | 0.01908 | 0.03058 |
| hard_full_light_bucket | full_light_geometry | True | 0.350 | 0.450 | 0.200 | 244.664 | 447.2 | 268.1 (0.60) | 0.850 | 0.02522 | 0.02939 |
