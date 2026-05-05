# Evaluation Matrix

- Generated: `2026-05-06T00:06:53`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_mild_200k_oracle_e20\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.930 | 0.070 | 0.000 | 149.589 | 24.9 | 0.00653 | 0.01208 |
| visual_camera | visual_camera | 0.920 | 0.080 | 0.000 | 140.142 | 26.6 | 0.00876 | 0.01159 |
| visual_camera_control | visual_camera_control | 0.600 | 0.400 | 0.000 | 45.256 | 58.7 | 0.01910 | 0.03341 |
| full_light_geometry | full_light_geometry | 0.200 | 0.790 | 0.010 | -173.370 | 37.4 | 0.03832 | 0.03214 |
| full_contact_light | full_contact_light | 0.200 | 0.770 | 0.030 | -176.226 | 36.3 | 0.03703 | 0.03116 |
