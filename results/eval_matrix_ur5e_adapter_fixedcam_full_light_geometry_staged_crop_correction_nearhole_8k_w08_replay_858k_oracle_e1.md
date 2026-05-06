# Evaluation Matrix

- Generated: `2026-05-07T00:03:09`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w08_replay_858k_oracle_e1\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 148.221 | 23.1 | 0.00472 | 0.00864 |
| visual_camera | visual_camera | 0.980 | 0.020 | 0.000 | 143.135 | 21.9 | 0.00505 | 0.00882 |
| visual_camera_control | visual_camera_control | 0.900 | 0.100 | 0.000 | 115.115 | 29.9 | 0.00815 | 0.01323 |
| full_light_geometry | full_light_geometry | 0.590 | 0.400 | 0.010 | -20.941 | 23.1 | 0.01466 | 0.02388 |
| full_contact_light | full_contact_light | 0.630 | 0.360 | 0.010 | -2.557 | 23.5 | 0.01412 | 0.02242 |
