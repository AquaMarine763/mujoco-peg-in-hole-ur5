# Guarded Policy Evaluation

- Generated: `2026-05-09T00:01:35`
- Model: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `566000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.12`
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
| clean | none | True | 0.480 | 0.150 | 0.370 | 247.875 | 569.3 | 404.7 (0.71) | 0.960 | 0.01279 | 0.02186 |
| visual_camera | visual_camera | True | 0.450 | 0.220 | 0.330 | 206.197 | 542.8 | 355.0 (0.65) | 0.920 | 0.01718 | 0.02225 |
| visual_camera_control | visual_camera_control | True | 0.330 | 0.270 | 0.400 | 134.732 | 580.0 | 375.0 (0.65) | 0.880 | 0.02528 | 0.03007 |
| full_light_geometry | full_light_geometry | True | 0.270 | 0.370 | 0.360 | 173.892 | 548.5 | 341.4 (0.62) | 0.880 | 0.02343 | 0.02867 |
| full_contact_light | full_contact_light | True | 0.310 | 0.370 | 0.320 | 196.794 | 529.5 | 332.0 (0.63) | 0.870 | 0.02611 | 0.02739 |
| hard_full_light_bucket | full_light_geometry | True | 0.330 | 0.260 | 0.410 | 188.742 | 609.9 | 385.6 (0.63) | 0.910 | 0.02427 | 0.03019 |
