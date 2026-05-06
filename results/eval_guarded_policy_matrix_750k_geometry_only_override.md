# Guarded Policy Evaluation

- Generated: `2026-05-06T19:40:19`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.1`
- Guard risk XY: `0.0`
- Guard scenario filter: `geometry`
- Guard blend: `1.0`
- Guarded align/insert XY: `0.025/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | False | 0.980 | 0.020 | 0.000 | 147.442 | 22.5 | 0.0 (0.00) | 0.000 | 0.00480 | 0.00869 |
| visual_camera | visual_camera | False | 0.980 | 0.020 | 0.000 | 144.690 | 22.3 | 0.0 (0.00) | 0.000 | 0.00497 | 0.00885 |
| visual_camera_control | visual_camera_control | False | 0.920 | 0.080 | 0.000 | 122.691 | 28.8 | 0.0 (0.00) | 0.000 | 0.00718 | 0.01247 |
| full_light_geometry | full_light_geometry | True | 0.690 | 0.240 | 0.070 | 40.293 | 39.6 | 38.5 (0.97) | 0.980 | 0.01096 | 0.02458 |
| full_contact_light | full_contact_light | True | 0.660 | 0.290 | 0.050 | 21.523 | 36.8 | 35.6 (0.97) | 0.970 | 0.01238 | 0.02525 |
| hard_full_light_bucket | full_light_geometry | True | 0.480 | 0.520 | 0.000 | -83.271 | 21.6 | 20.3 (0.94) | 0.920 | 0.02055 | 0.02981 |
