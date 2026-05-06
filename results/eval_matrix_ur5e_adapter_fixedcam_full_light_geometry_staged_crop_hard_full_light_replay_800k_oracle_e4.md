# Evaluation Matrix

- Generated: `2026-05-06T17:57:17`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_hard_full_light_replay_800k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.990 | 0.010 | 0.000 | 169.456 | 22.6 | 0.00453 | 0.00796 |
| visual_camera | visual_camera | 0.960 | 0.040 | 0.000 | 158.839 | 25.3 | 0.00568 | 0.01021 |
| visual_camera_control | visual_camera_control | 0.910 | 0.080 | 0.010 | 140.049 | 32.8 | 0.00749 | 0.01320 |
| full_light_geometry | full_light_geometry | 0.550 | 0.440 | 0.010 | -39.377 | 24.1 | 0.01470 | 0.02532 |
| full_contact_light | full_contact_light | 0.530 | 0.450 | 0.020 | -40.419 | 26.4 | 0.01533 | 0.02659 |
