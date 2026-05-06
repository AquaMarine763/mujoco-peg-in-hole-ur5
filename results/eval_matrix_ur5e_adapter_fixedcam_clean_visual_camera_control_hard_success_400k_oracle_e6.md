# Evaluation Matrix

- Generated: `2026-05-06T12:51:42`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_hard_success_400k_oracle_e6\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 165.073 | 22.5 | 0.00484 | 0.00879 |
| visual_camera | visual_camera | 0.960 | 0.040 | 0.000 | 148.964 | 24.0 | 0.00889 | 0.00905 |
| visual_camera_control | visual_camera_control | 0.880 | 0.120 | 0.000 | 124.932 | 32.7 | 0.00912 | 0.01486 |
| full_light_geometry | full_light_geometry | 0.310 | 0.650 | 0.040 | -125.875 | 33.8 | 0.03652 | 0.02638 |
| full_contact_light | full_contact_light | 0.290 | 0.690 | 0.020 | -139.500 | 34.7 | 0.03742 | 0.02875 |
