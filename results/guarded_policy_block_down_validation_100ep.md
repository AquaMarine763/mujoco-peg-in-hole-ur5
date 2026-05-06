# Guarded Policy Evaluation

- Generated: `2026-05-07T04:25:22`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.08`
- Guard risk XY: `0.0`
- Guard scenario filter: `geometry`
- Guard blend: `0.75`
- Guard min policy steps: `0`
- Guard block down when unaligned: `True`
- Guarded align/insert XY: `0.025/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | False | 0.980 | 0.020 | 0.000 | 147.336 | 22.4 | 0.0 (0.00) | 0.000 | 0.00479 | 0.00869 |
| visual_camera | visual_camera | False | 0.980 | 0.020 | 0.000 | 144.270 | 22.2 | 0.0 (0.00) | 0.000 | 0.00499 | 0.00883 |
| visual_camera_control | visual_camera_control | False | 0.910 | 0.090 | 0.000 | 119.038 | 30.0 | 0.0 (0.00) | 0.000 | 0.00744 | 0.01315 |
| full_light_geometry | full_light_geometry | True | 0.700 | 0.240 | 0.060 | 46.006 | 39.2 | 38.1 (0.97) | 0.980 | 0.01125 | 0.02421 |
| full_contact_light | full_contact_light | True | 0.640 | 0.320 | 0.040 | 13.520 | 35.4 | 34.2 (0.97) | 0.970 | 0.01321 | 0.02631 |
| hard_full_light_bucket | full_light_geometry | True | 0.530 | 0.460 | 0.010 | -57.727 | 20.3 | 18.9 (0.93) | 0.920 | 0.01959 | 0.02768 |
