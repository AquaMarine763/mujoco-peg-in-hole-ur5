# Evaluation Matrix

- Generated: `2026-05-06T22:17:58`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_medium_replay_850k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.960 | 0.040 | 0.000 | 166.042 | 26.3 | 0.00563 | 0.00992 |
| visual_camera | visual_camera | 0.970 | 0.030 | 0.000 | 162.347 | 25.9 | 0.00547 | 0.00951 |
| visual_camera_control | visual_camera_control | 0.860 | 0.130 | 0.010 | 125.279 | 37.2 | 0.00964 | 0.01623 |
| full_light_geometry | full_light_geometry | 0.540 | 0.450 | 0.010 | -38.370 | 26.3 | 0.01604 | 0.02709 |
| full_contact_light | full_contact_light | 0.570 | 0.420 | 0.010 | -16.306 | 34.7 | 0.01494 | 0.02679 |
