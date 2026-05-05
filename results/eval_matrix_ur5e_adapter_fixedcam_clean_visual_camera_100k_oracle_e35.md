# Evaluation Matrix

- Generated: `2026-05-05T21:17:13`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_100k_oracle_e35\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.960 | 0.040 | 0.000 | 151.868 | 20.8 | 0.00545 | 0.01013 |
| visual_camera | visual_camera | 0.660 | 0.340 | 0.000 | 64.505 | 47.4 | 0.02097 | 0.02623 |
| visual_camera_control | visual_camera_control | 0.440 | 0.560 | 0.000 | -13.711 | 65.2 | 0.02758 | 0.04022 |
| full_light_geometry | full_light_geometry | 0.120 | 0.880 | 0.000 | -220.580 | 31.1 | 0.04197 | 0.03356 |
| full_contact_light | full_contact_light | 0.110 | 0.890 | 0.000 | -222.984 | 30.6 | 0.04048 | 0.03532 |
