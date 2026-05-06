# Evaluation Matrix

- Generated: `2026-05-06T22:25:22`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_light_850k_oracle_e2\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.970 | 0.030 | 0.000 | 165.576 | 24.3 | 0.00525 | 0.00919 |
| visual_camera | visual_camera | 0.980 | 0.020 | 0.000 | 162.789 | 23.7 | 0.00507 | 0.00880 |
| visual_camera_control | visual_camera_control | 0.900 | 0.100 | 0.000 | 134.984 | 33.1 | 0.00807 | 0.01370 |
| full_light_geometry | full_light_geometry | 0.550 | 0.440 | 0.010 | -32.867 | 26.6 | 0.01531 | 0.02670 |
| full_contact_light | full_contact_light | 0.660 | 0.330 | 0.010 | 5.182 | 24.9 | 0.01339 | 0.02109 |
