# Evaluation Matrix

- Generated: `2026-05-06T14:09:02`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_balanced_weighted_550k_oracle_e6\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 162.609 | 21.4 | 0.00481 | 0.00879 |
| visual_camera | visual_camera | 0.980 | 0.020 | 0.000 | 156.315 | 22.7 | 0.00762 | 0.00826 |
| visual_camera_control | visual_camera_control | 0.890 | 0.110 | 0.000 | 125.270 | 31.3 | 0.00852 | 0.01405 |
| full_light_geometry | full_light_geometry | 0.310 | 0.660 | 0.030 | -125.423 | 36.3 | 0.03767 | 0.02759 |
| full_contact_light | full_contact_light | 0.300 | 0.670 | 0.030 | -132.165 | 37.8 | 0.03848 | 0.02925 |
