# Evaluation Matrix

- Generated: `2026-05-06T16:14:45`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_intermediate_narrow_650k_oracle_e5\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.960 | 0.040 | 0.000 | 158.252 | 23.8 | 0.00568 | 0.01007 |
| visual_camera | visual_camera | 0.960 | 0.040 | 0.000 | 153.767 | 24.0 | 0.00545 | 0.01004 |
| visual_camera_control | visual_camera_control | 0.850 | 0.150 | 0.000 | 115.513 | 34.5 | 0.01010 | 0.01685 |
| full_light_geometry | full_light_geometry | 0.390 | 0.590 | 0.020 | -92.427 | 40.6 | 0.03386 | 0.02698 |
| full_contact_light | full_contact_light | 0.400 | 0.570 | 0.030 | -82.434 | 39.9 | 0.03553 | 0.02737 |
