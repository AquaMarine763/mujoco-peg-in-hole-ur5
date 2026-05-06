# Evaluation Matrix

- Generated: `2026-05-06T12:06:51`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_clean_visual_camera_control_delay_filter_success_350k_oracle_e8\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.990 | 0.010 | 0.000 | 164.050 | 20.5 | 0.00452 | 0.00807 |
| visual_camera | visual_camera | 0.930 | 0.070 | 0.000 | 142.023 | 26.4 | 0.00862 | 0.01110 |
| visual_camera_control | visual_camera_control | 0.860 | 0.140 | 0.000 | 122.114 | 34.9 | 0.01003 | 0.01618 |
| full_light_geometry | full_light_geometry | 0.290 | 0.670 | 0.040 | -137.326 | 35.3 | 0.03626 | 0.02623 |
| full_contact_light | full_contact_light | 0.270 | 0.680 | 0.050 | -140.121 | 36.1 | 0.03789 | 0.02863 |
