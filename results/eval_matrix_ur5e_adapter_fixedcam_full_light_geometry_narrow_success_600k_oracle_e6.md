# Evaluation Matrix

- Generated: `2026-05-06T14:34:36`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_narrow_success_600k_oracle_e6\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.950 | 0.050 | 0.000 | 158.764 | 25.6 | 0.00607 | 0.01081 |
| visual_camera | visual_camera | 0.990 | 0.010 | 0.000 | 162.717 | 22.9 | 0.00458 | 0.00798 |
| visual_camera_control | visual_camera_control | 0.850 | 0.150 | 0.000 | 113.564 | 34.1 | 0.01027 | 0.01647 |
| full_light_geometry | full_light_geometry | 0.350 | 0.610 | 0.040 | -109.489 | 37.3 | 0.03405 | 0.02734 |
| full_contact_light | full_contact_light | 0.390 | 0.580 | 0.030 | -89.908 | 37.3 | 0.03537 | 0.02613 |
