# Evaluation Matrix

- Generated: `2026-05-06T00:38:04`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_success_250k_oracle_e15\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.950 | 0.050 | 0.000 | 154.866 | 24.3 | 0.00585 | 0.01074 |
| visual_camera | visual_camera | 0.910 | 0.090 | 0.000 | 139.151 | 27.9 | 0.00914 | 0.01242 |
| visual_camera_control | visual_camera_control | 0.730 | 0.270 | 0.000 | 81.468 | 47.7 | 0.01452 | 0.02446 |
| full_light_geometry | full_light_geometry | 0.250 | 0.730 | 0.020 | -149.088 | 36.6 | 0.03750 | 0.03049 |
| full_contact_light | full_contact_light | 0.270 | 0.690 | 0.040 | -148.521 | 35.4 | 0.03885 | 0.02788 |
