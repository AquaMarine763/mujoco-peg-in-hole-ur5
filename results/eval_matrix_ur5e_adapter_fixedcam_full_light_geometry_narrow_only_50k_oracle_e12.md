# Evaluation Matrix

- Generated: `2026-05-06T14:40:56`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_narrow_only_50k_oracle_e12\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.820 | 0.180 | 0.000 | 101.460 | 50.2 | 0.01076 | 0.01811 |
| visual_camera | visual_camera | 0.760 | 0.230 | 0.010 | 62.907 | 57.0 | 0.01413 | 0.01934 |
| visual_camera_control | visual_camera_control | 0.580 | 0.380 | 0.040 | 4.158 | 73.6 | 0.02267 | 0.02580 |
| full_light_geometry | full_light_geometry | 0.360 | 0.590 | 0.050 | -118.572 | 40.9 | 0.03376 | 0.02611 |
| full_contact_light | full_contact_light | 0.390 | 0.570 | 0.040 | -103.476 | 38.8 | 0.03332 | 0.02475 |
