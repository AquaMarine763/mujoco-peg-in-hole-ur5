# Evaluation Matrix

- Generated: `2026-05-08T12:24:10`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 0.080 | 0.220 | 0.700 | -64.577 | 152.9 | 0.02295 | 0.01686 |
| visual_camera | visual_camera | 0.260 | 0.210 | 0.530 | -11.339 | 137.5 | 0.02208 | 0.01651 |
| visual_camera_control | visual_camera_control | 0.250 | 0.220 | 0.530 | -16.841 | 137.2 | 0.02288 | 0.01659 |
| full_light_geometry | full_light_geometry | 0.140 | 0.590 | 0.270 | -136.052 | 91.0 | 0.02822 | 0.03054 |
| full_contact_light | full_contact_light | 0.150 | 0.550 | 0.300 | -127.755 | 94.9 | 0.02785 | 0.02978 |
