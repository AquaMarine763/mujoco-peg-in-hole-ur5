# Evaluation Matrix

- Generated: `2026-05-06T17:15:40`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_control_replay_700k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.960 | 0.040 | 0.000 | 162.716 | 24.9 | 0.00555 | 0.01008 |
| visual_camera | visual_camera | 0.970 | 0.030 | 0.000 | 158.731 | 24.4 | 0.00531 | 0.00967 |
| visual_camera_control | visual_camera_control | 0.900 | 0.090 | 0.010 | 138.335 | 33.3 | 0.00794 | 0.01394 |
| full_light_geometry | full_light_geometry | 0.520 | 0.470 | 0.010 | -58.617 | 24.2 | 0.01764 | 0.02485 |
| full_contact_light | full_contact_light | 0.570 | 0.410 | 0.020 | -34.091 | 25.8 | 0.01702 | 0.02363 |
