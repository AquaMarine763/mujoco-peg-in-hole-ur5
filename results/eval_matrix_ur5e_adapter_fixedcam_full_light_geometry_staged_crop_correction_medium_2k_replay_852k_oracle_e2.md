# Evaluation Matrix

- Generated: `2026-05-06T23:13:42`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_correction_medium_2k_replay_852k_oracle_e2\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 168.399 | 24.0 | 0.00491 | 0.00859 |
| visual_camera | visual_camera | 0.960 | 0.040 | 0.000 | 158.355 | 25.1 | 0.00574 | 0.01015 |
| visual_camera_control | visual_camera_control | 0.910 | 0.090 | 0.000 | 138.325 | 32.0 | 0.00753 | 0.01309 |
| full_light_geometry | full_light_geometry | 0.550 | 0.440 | 0.010 | -38.202 | 26.2 | 0.01458 | 0.02586 |
| full_contact_light | full_contact_light | 0.620 | 0.370 | 0.010 | -11.176 | 24.3 | 0.01395 | 0.02302 |
