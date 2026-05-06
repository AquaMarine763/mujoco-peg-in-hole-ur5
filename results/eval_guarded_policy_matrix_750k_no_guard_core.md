# Guarded Policy Evaluation

- Generated: `2026-05-06T19:44:16`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.1`
- Guard risk XY: `0.0`
- Guard scenario filter: `none`
- Guard blend: `1.0`
- Guarded align/insert XY: `0.025/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | False | 0.980 | 0.020 | 0.000 | 147.429 | 22.5 | 0.0 (0.00) | 0.000 | 0.00479 | 0.00870 |
| visual_camera | visual_camera | False | 0.980 | 0.020 | 0.000 | 144.249 | 22.2 | 0.0 (0.00) | 0.000 | 0.00499 | 0.00880 |
| visual_camera_control | visual_camera_control | False | 0.910 | 0.090 | 0.000 | 119.126 | 30.1 | 0.0 (0.00) | 0.000 | 0.00748 | 0.01316 |
| full_light_geometry | full_light_geometry | False | 0.580 | 0.410 | 0.010 | -25.446 | 23.6 | 0.0 (0.00) | 0.000 | 0.01444 | 0.02388 |
| full_contact_light | full_contact_light | False | 0.580 | 0.400 | 0.020 | -17.212 | 28.8 | 0.0 (0.00) | 0.000 | 0.01494 | 0.02428 |
