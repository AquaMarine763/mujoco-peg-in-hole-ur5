# Evaluation Matrix

- Generated: `2026-05-06T16:07:43`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_intermediate_success_600k_oracle_e6\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.950 | 0.040 | 0.010 | 162.421 | 26.4 | 0.00614 | 0.01067 |
| visual_camera | visual_camera | 0.970 | 0.030 | 0.000 | 156.654 | 24.7 | 0.00782 | 0.00888 |
| visual_camera_control | visual_camera_control | 0.870 | 0.130 | 0.000 | 120.973 | 32.4 | 0.00930 | 0.01504 |
| full_light_geometry | full_light_geometry | 0.370 | 0.580 | 0.050 | -94.268 | 40.7 | 0.03761 | 0.02636 |
| full_contact_light | full_contact_light | 0.410 | 0.560 | 0.030 | -86.457 | 37.6 | 0.03756 | 0.02552 |
