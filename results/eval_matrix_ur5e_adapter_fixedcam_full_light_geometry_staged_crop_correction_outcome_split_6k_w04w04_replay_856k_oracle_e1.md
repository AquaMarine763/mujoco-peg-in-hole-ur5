# Evaluation Matrix

- Generated: `2026-05-07T03:08:39`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_outcome_split_6k_w04w04_replay_856k_oracle_e1\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 148.356 | 23.4 | 0.00493 | 0.00860 |
| visual_camera | visual_camera | 0.980 | 0.020 | 0.000 | 144.740 | 22.8 | 0.00500 | 0.00885 |
| visual_camera_control | visual_camera_control | 0.910 | 0.090 | 0.000 | 121.204 | 31.4 | 0.00751 | 0.01284 |
| full_light_geometry | full_light_geometry | 0.560 | 0.420 | 0.020 | -26.514 | 26.1 | 0.01486 | 0.02632 |
| full_contact_light | full_contact_light | 0.600 | 0.400 | 0.000 | -16.267 | 24.9 | 0.01450 | 0.02394 |
