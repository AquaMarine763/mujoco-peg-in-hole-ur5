# Evaluation Matrix

- Generated: `2026-05-05T22:07:35`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_150k_oracle_e20\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.960 | 0.040 | 0.000 | 151.358 | 21.8 | 0.00551 | 0.01003 |
| visual_camera | visual_camera | 0.810 | 0.190 | 0.000 | 105.911 | 32.9 | 0.01282 | 0.01703 |
| visual_camera_control | visual_camera_control | 0.480 | 0.520 | 0.000 | -1.334 | 61.1 | 0.02351 | 0.03830 |
| full_light_geometry | full_light_geometry | 0.140 | 0.840 | 0.020 | -212.671 | 29.4 | 0.04157 | 0.03187 |
| full_contact_light | full_contact_light | 0.140 | 0.840 | 0.020 | -210.216 | 31.3 | 0.04052 | 0.03229 |
