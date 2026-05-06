# Evaluation Matrix

- Generated: `2026-05-06T23:59:43`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_nearhole_8k_w05_replay_858k_oracle_e2\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 148.337 | 23.2 | 0.00490 | 0.00865 |
| visual_camera | visual_camera | 0.970 | 0.030 | 0.000 | 141.381 | 23.7 | 0.00540 | 0.00941 |
| visual_camera_control | visual_camera_control | 0.930 | 0.070 | 0.000 | 128.499 | 28.9 | 0.00701 | 0.01177 |
| full_light_geometry | full_light_geometry | 0.570 | 0.420 | 0.010 | -24.054 | 26.7 | 0.01470 | 0.02568 |
| full_contact_light | full_contact_light | 0.630 | 0.360 | 0.010 | -2.038 | 24.6 | 0.01384 | 0.02248 |
