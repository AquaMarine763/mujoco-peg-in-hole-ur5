# Evaluation Matrix

- Generated: `2026-05-08T17:49:08`
- Model: `checkpoints\ur5e_full\correction\sac_image_bc_50k_narrow_correction_8k_w10_e2.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.870 | 0.130 | 0.000 | 212.910 | 108.4 | 0.00714 | 0.01357 |
| visual_camera | visual_camera | 0.780 | 0.140 | 0.080 | 184.839 | 115.3 | 0.00805 | 0.01417 |
| visual_camera_control | visual_camera_control | 0.760 | 0.200 | 0.040 | 159.140 | 108.8 | 0.01008 | 0.01662 |
| full_light_geometry | full_light_geometry | 0.750 | 0.180 | 0.070 | 163.286 | 110.2 | 0.01004 | 0.01578 |
| full_contact_light | full_contact_light | 0.720 | 0.210 | 0.070 | 147.115 | 109.0 | 0.01111 | 0.01702 |
