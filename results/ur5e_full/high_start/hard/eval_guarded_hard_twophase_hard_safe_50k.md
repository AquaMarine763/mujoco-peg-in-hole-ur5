# Guarded Policy Evaluation

- Generated: `2026-05-09T01:02:32`
- Model: `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `571000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.12`
- Guard risk XY: `0.0`
- Guard scenario filter: `all`
- Guard blend: `1.0`
- Guard min policy steps: `0`
- Guard block down when unaligned: `True`
- Guarded oracle mode: `high_start_two_phase`
- Guarded align/insert XY: `0.03/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.490 | 0.100 | 0.410 | 94.861 | 589.4 | 412.4 (0.70) | 0.970 | 0.01231 | 0.02092 |
| visual_camera | visual_camera | True | 0.340 | 0.190 | 0.470 | 35.777 | 631.4 | 404.6 (0.64) | 0.960 | 0.01474 | 0.02856 |
| visual_camera_control | visual_camera_control | True | 0.320 | 0.260 | 0.420 | -13.127 | 615.2 | 373.9 (0.61) | 0.920 | 0.02686 | 0.03465 |
| full_light_geometry | full_light_geometry | True | 0.350 | 0.260 | 0.390 | 125.659 | 584.4 | 386.9 (0.66) | 0.920 | 0.01713 | 0.02509 |
| full_contact_light | full_contact_light | True | 0.350 | 0.300 | 0.350 | 97.371 | 562.0 | 341.9 (0.61) | 0.910 | 0.02326 | 0.03229 |
| hard_full_light_bucket | full_light_geometry | True | 0.270 | 0.340 | 0.390 | 125.727 | 587.3 | 352.6 (0.60) | 0.900 | 0.02064 | 0.02929 |
