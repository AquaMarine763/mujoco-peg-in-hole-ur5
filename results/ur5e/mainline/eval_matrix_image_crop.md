# Evaluation Matrix

- Generated: `2026-05-08T00:26:04`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `default`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.980 | 0.020 | 0.000 | 165.566 | 22.5 | 0.00478 | 0.00868 |
| visual_camera | visual_camera | 0.980 | 0.020 | 0.000 | 160.794 | 22.3 | 0.00499 | 0.00880 |
| visual_camera_control | visual_camera_control | 0.910 | 0.090 | 0.000 | 134.685 | 30.0 | 0.00747 | 0.01315 |
| full_light_geometry | full_light_geometry | 0.580 | 0.410 | 0.010 | -30.441 | 23.7 | 0.01444 | 0.02395 |
| full_contact_light | full_contact_light | 0.590 | 0.390 | 0.020 | -23.908 | 26.4 | 0.01474 | 0.02422 |
