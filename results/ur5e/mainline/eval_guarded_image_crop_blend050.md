# Guarded Policy Evaluation

- Generated: `2026-05-08T00:35:04`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `default`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.08`
- Guard risk XY: `0.0`
- Guard scenario filter: `geometry`
- Guard blend: `0.5`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guarded align/insert XY: `0.025/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | False | 0.980 | 0.020 | 0.000 | 147.146 | 22.4 | 0.0 (0.00) | 0.000 | 0.00479 | 0.00869 |
| visual_camera | visual_camera | False | 0.980 | 0.020 | 0.000 | 144.519 | 22.3 | 0.0 (0.00) | 0.000 | 0.00500 | 0.00884 |
| visual_camera_control | visual_camera_control | False | 0.910 | 0.090 | 0.000 | 118.979 | 29.9 | 0.0 (0.00) | 0.000 | 0.00747 | 0.01314 |
| full_light_geometry | full_light_geometry | True | 0.620 | 0.380 | 0.010 | 2.325 | 39.5 | 38.4 (0.97) | 0.980 | 0.01310 | 0.02740 |
| full_contact_light | full_contact_light | True | 0.650 | 0.340 | 0.010 | 9.970 | 33.0 | 31.8 (0.97) | 0.970 | 0.01322 | 0.02458 |
| hard_full_light_bucket | full_light_geometry | True | 0.490 | 0.500 | 0.010 | -72.777 | 19.1 | 17.7 (0.93) | 0.920 | 0.02048 | 0.02826 |
