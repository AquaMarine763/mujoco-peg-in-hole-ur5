# Evaluation Matrix

- Generated: `2026-05-05T20:57:29`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_visual_camera_50k_oracle\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.870 | 0.130 | 0.000 | 156.528 | 42.2 | 0.00972 | 0.01570 |
| visual_camera | visual_camera | 0.540 | 0.460 | 0.000 | 15.918 | 55.5 | 0.02403 | 0.03364 |
| visual_camera_control | visual_camera_control | 0.410 | 0.590 | 0.000 | -34.315 | 59.3 | 0.02850 | 0.04066 |
| full_light_geometry | full_light_geometry | 0.080 | 0.920 | 0.000 | -231.091 | 30.8 | 0.03896 | 0.03829 |
| full_contact_light | full_contact_light | 0.080 | 0.920 | 0.000 | -231.721 | 29.9 | 0.03935 | 0.03806 |
