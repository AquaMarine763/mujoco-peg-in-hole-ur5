# Evaluation Matrix

- Generated: `2026-05-05T21:09:32`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.940 | 0.060 | 0.000 | 147.312 | 23.7 | 0.00634 | 0.01155 |
| visual_camera | visual_camera | 0.570 | 0.430 | 0.000 | 18.243 | 48.3 | 0.02327 | 0.03143 |
| visual_camera_control | visual_camera_control | 0.380 | 0.620 | 0.000 | -32.444 | 66.2 | 0.02990 | 0.04347 |
| full_light_geometry | full_light_geometry | 0.100 | 0.900 | 0.000 | -231.334 | 28.5 | 0.03921 | 0.03676 |
| full_contact_light | full_contact_light | 0.090 | 0.910 | 0.000 | -231.614 | 29.7 | 0.03854 | 0.03752 |
