# Guarded Policy Evaluation

- Generated: `2026-05-08T23:25:21`
- Model: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_20k_high_start_hard_safe_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `563000`
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
| clean | none | True | 0.480 | 0.100 | 0.420 | 162.490 | 595.9 | 409.2 (0.69) | 1.000 | 0.00897 | 0.02082 |
| visual_camera | visual_camera | True | 0.400 | 0.190 | 0.410 | 116.315 | 595.6 | 396.0 (0.66) | 0.910 | 0.02195 | 0.02627 |
| visual_camera_control | visual_camera_control | True | 0.340 | 0.300 | 0.360 | 143.982 | 560.3 | 350.0 (0.62) | 0.870 | 0.02698 | 0.02839 |
| full_light_geometry | full_light_geometry | True | 0.350 | 0.240 | 0.410 | 113.732 | 584.9 | 380.2 (0.65) | 0.900 | 0.02578 | 0.02884 |
| full_contact_light | full_contact_light | True | 0.390 | 0.290 | 0.320 | 216.538 | 530.8 | 327.9 (0.62) | 0.940 | 0.01751 | 0.02601 |
| hard_full_light_bucket | full_light_geometry | True | 0.240 | 0.370 | 0.390 | 69.964 | 591.1 | 352.6 (0.60) | 0.830 | 0.03544 | 0.03332 |
