# Evaluation Matrix

- Generated: `2026-05-06T13:06:22`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_weighted_500k_oracle_e5\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.960 | 0.040 | 0.010 | 157.206 | 23.9 | 0.00549 | 0.01012 |
| visual_camera | visual_camera | 0.990 | 0.010 | 0.000 | 161.346 | 23.2 | 0.00455 | 0.00820 |
| visual_camera_control | visual_camera_control | 0.890 | 0.110 | 0.000 | 123.760 | 28.9 | 0.00867 | 0.01342 |
| full_light_geometry | full_light_geometry | 0.300 | 0.660 | 0.040 | -127.828 | 35.5 | 0.03805 | 0.02756 |
| full_contact_light | full_contact_light | 0.310 | 0.660 | 0.030 | -130.434 | 35.0 | 0.03788 | 0.02730 |
