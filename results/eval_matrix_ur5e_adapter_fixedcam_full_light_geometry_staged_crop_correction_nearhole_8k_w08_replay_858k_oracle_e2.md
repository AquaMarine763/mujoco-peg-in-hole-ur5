# Evaluation Matrix

- Generated: `2026-05-06T23:52:24`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e2\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.960 | 0.040 | 0.000 | 141.404 | 25.1 | 0.00553 | 0.00995 |
| visual_camera | visual_camera | 0.950 | 0.050 | 0.000 | 133.493 | 25.1 | 0.00613 | 0.01083 |
| visual_camera_control | visual_camera_control | 0.910 | 0.090 | 0.000 | 118.857 | 30.1 | 0.00792 | 0.01248 |
| full_light_geometry | full_light_geometry | 0.590 | 0.410 | 0.000 | -22.116 | 23.6 | 0.01485 | 0.02426 |
| full_contact_light | full_contact_light | 0.630 | 0.360 | 0.010 | -3.887 | 22.3 | 0.01406 | 0.02220 |
