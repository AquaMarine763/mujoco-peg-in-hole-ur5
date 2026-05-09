# Evaluation Matrix

- Generated: `2026-05-08T16:15:54`
- Model: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.850 | 0.150 | 0.000 | 199.876 | 100.6 | 0.00738 | 0.01479 |
| visual_camera | visual_camera | 0.800 | 0.170 | 0.030 | 176.705 | 101.8 | 0.00855 | 0.01552 |
| visual_camera_control | visual_camera_control | 0.740 | 0.240 | 0.020 | 141.441 | 96.7 | 0.01077 | 0.01841 |
| full_light_geometry | full_light_geometry | 0.740 | 0.240 | 0.020 | 141.989 | 97.8 | 0.01097 | 0.01849 |
| full_contact_light | full_contact_light | 0.740 | 0.240 | 0.020 | 140.677 | 97.9 | 0.01159 | 0.01847 |
