# Evaluation Matrix

- Generated: `2026-05-06T17:26:51`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 165.403 | 22.5 | 0.00479 | 0.00868 |
| visual_camera | visual_camera | 0.980 | 0.020 | 0.000 | 160.362 | 22.1 | 0.00497 | 0.00883 |
| visual_camera_control | visual_camera_control | 0.910 | 0.090 | 0.000 | 134.579 | 30.1 | 0.00745 | 0.01317 |
| full_light_geometry | full_light_geometry | 0.580 | 0.410 | 0.010 | -30.372 | 23.6 | 0.01438 | 0.02391 |
| full_contact_light | full_contact_light | 0.590 | 0.390 | 0.020 | -21.249 | 27.6 | 0.01486 | 0.02371 |
