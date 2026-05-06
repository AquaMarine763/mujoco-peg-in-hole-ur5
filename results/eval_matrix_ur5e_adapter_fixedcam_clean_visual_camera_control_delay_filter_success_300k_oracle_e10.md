# Evaluation Matrix

- Generated: `2026-05-06T11:48:58`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_300k_oracle_e10\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.970 | 0.030 | 0.000 | 156.772 | 21.3 | 0.00511 | 0.00939 |
| visual_camera | visual_camera | 0.940 | 0.060 | 0.000 | 143.264 | 25.4 | 0.00823 | 0.01039 |
| visual_camera_control | visual_camera_control | 0.780 | 0.220 | 0.000 | 94.344 | 41.8 | 0.01259 | 0.02152 |
| full_light_geometry | full_light_geometry | 0.280 | 0.670 | 0.050 | -132.683 | 37.0 | 0.03618 | 0.02885 |
| full_contact_light | full_contact_light | 0.290 | 0.690 | 0.020 | -144.317 | 31.4 | 0.03788 | 0.02791 |
