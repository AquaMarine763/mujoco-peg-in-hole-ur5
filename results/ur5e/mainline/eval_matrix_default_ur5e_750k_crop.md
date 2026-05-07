# Evaluation Matrix

- Generated: `2026-05-07T23:55:50`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `default`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 165.176 | 22.4 | 0.00481 | 0.00870 |
| visual_camera | visual_camera | 0.980 | 0.020 | 0.000 | 160.571 | 22.3 | 0.00500 | 0.00881 |
| visual_camera_control | visual_camera_control | 0.920 | 0.080 | 0.000 | 137.845 | 28.8 | 0.00714 | 0.01248 |
| full_light_geometry | full_light_geometry | 0.580 | 0.410 | 0.010 | -30.668 | 23.7 | 0.01443 | 0.02362 |
| full_contact_light | full_contact_light | 0.600 | 0.390 | 0.010 | -22.736 | 25.9 | 0.01459 | 0.02300 |
