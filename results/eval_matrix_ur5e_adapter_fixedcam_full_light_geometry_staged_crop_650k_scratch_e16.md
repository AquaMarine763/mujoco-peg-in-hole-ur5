# Evaluation Matrix

- Generated: `2026-05-06T16:54:34`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_650k_scratch_e16\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.960 | 0.040 | 0.000 | 162.781 | 25.0 | 0.00566 | 0.00998 |
| visual_camera | visual_camera | 0.960 | 0.040 | 0.000 | 160.137 | 25.9 | 0.00570 | 0.01012 |
| visual_camera_control | visual_camera_control | 0.880 | 0.120 | 0.000 | 127.492 | 33.9 | 0.00863 | 0.01492 |
| full_light_geometry | full_light_geometry | 0.530 | 0.450 | 0.020 | -50.437 | 24.0 | 0.01670 | 0.02603 |
| full_contact_light | full_contact_light | 0.570 | 0.410 | 0.020 | -29.391 | 30.3 | 0.01622 | 0.02441 |
