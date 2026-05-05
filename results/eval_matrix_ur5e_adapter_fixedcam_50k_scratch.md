# Evaluation Matrix

- Generated: `2026-05-05T20:40:03`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_50k_scratch\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.950 | 0.050 | 0.000 | 141.981 | 20.3 | 0.00582 | 0.01021 |
| visual_camera | visual_camera | 0.040 | 0.850 | 0.110 | -382.548 | 83.9 | 0.12418 | 0.04107 |
| visual_camera_control | visual_camera_control | 0.070 | 0.840 | 0.090 | -336.508 | 67.0 | 0.09934 | 0.03780 |
| full_light_geometry | full_light_geometry | 0.010 | 0.990 | 0.000 | -385.465 | 45.9 | 0.11853 | 0.03691 |
| full_contact_light | full_contact_light | 0.010 | 0.940 | 0.060 | -397.615 | 53.0 | 0.12463 | 0.04609 |
