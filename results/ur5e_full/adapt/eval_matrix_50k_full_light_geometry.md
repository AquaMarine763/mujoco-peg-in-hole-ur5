# Evaluation Matrix

- Generated: `2026-05-08T15:48:41`
- Model: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.750 | 0.250 | 0.000 | 151.077 | 83.9 | 0.01041 | 0.01907 |
| visual_camera | visual_camera | 0.690 | 0.240 | 0.070 | 133.048 | 96.0 | 0.01065 | 0.01876 |
| visual_camera_control | visual_camera_control | 0.640 | 0.320 | 0.040 | 96.704 | 89.6 | 0.01283 | 0.02190 |
| full_light_geometry | full_light_geometry | 0.600 | 0.360 | 0.040 | 78.005 | 90.6 | 0.01382 | 0.02354 |
| full_contact_light | full_contact_light | 0.620 | 0.320 | 0.060 | 97.124 | 93.8 | 0.01368 | 0.02210 |
