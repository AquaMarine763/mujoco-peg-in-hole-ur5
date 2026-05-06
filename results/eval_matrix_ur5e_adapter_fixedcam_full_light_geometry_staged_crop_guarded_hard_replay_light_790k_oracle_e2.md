# Evaluation Matrix

- Generated: `2026-05-06T19:09:36`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_guarded_hard_replay_light_790k_oracle_e2\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 168.230 | 23.8 | 0.00489 | 0.00862 |
| visual_camera | visual_camera | 0.980 | 0.020 | 0.000 | 162.542 | 23.5 | 0.00494 | 0.00890 |
| visual_camera_control | visual_camera_control | 0.910 | 0.080 | 0.010 | 139.410 | 32.0 | 0.00753 | 0.01325 |
| full_light_geometry | full_light_geometry | 0.550 | 0.430 | 0.020 | -37.147 | 27.5 | 0.01434 | 0.02558 |
| full_contact_light | full_contact_light | 0.580 | 0.400 | 0.020 | -26.068 | 24.4 | 0.01455 | 0.02481 |
