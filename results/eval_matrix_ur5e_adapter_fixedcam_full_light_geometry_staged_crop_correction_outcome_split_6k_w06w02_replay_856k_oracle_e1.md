# Evaluation Matrix

- Generated: `2026-05-07T03:13:33`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_outcome_split_6k_w06w02_replay_856k_oracle_e1\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 147.610 | 23.0 | 0.00483 | 0.00856 |
| visual_camera | visual_camera | 0.980 | 0.020 | 0.000 | 144.683 | 23.1 | 0.00497 | 0.00880 |
| visual_camera_control | visual_camera_control | 0.900 | 0.090 | 0.010 | 118.706 | 33.8 | 0.00790 | 0.01388 |
| full_light_geometry | full_light_geometry | 0.580 | 0.400 | 0.020 | -21.445 | 24.4 | 0.01466 | 0.02530 |
| full_contact_light | full_contact_light | 0.590 | 0.380 | 0.030 | -6.740 | 28.8 | 0.01428 | 0.02508 |
