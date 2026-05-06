# Evaluation Matrix

- Generated: `2026-05-06T19:00:07`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_guarded_hard_replay_800k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.960 | 0.040 | 0.000 | 164.439 | 25.5 | 0.00560 | 0.01001 |
| visual_camera | visual_camera | 0.950 | 0.050 | 0.000 | 157.298 | 26.4 | 0.00599 | 0.01086 |
| visual_camera_control | visual_camera_control | 0.880 | 0.110 | 0.010 | 131.510 | 33.9 | 0.00852 | 0.01519 |
| full_light_geometry | full_light_geometry | 0.550 | 0.430 | 0.020 | -39.013 | 25.5 | 0.01464 | 0.02595 |
| full_contact_light | full_contact_light | 0.530 | 0.470 | 0.000 | -46.467 | 26.7 | 0.01547 | 0.02786 |
