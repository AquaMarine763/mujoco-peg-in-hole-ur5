# Guarded Policy Evaluation

- Generated: `2026-05-08T00:27:10`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `default`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.08`
- Guard risk XY: `0.0`
- Guard scenario filter: `geometry`
- Guard blend: `0.75`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guarded align/insert XY: `0.025/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | False | 0.980 | 0.020 | 0.000 | 147.473 | 22.6 | 0.0 (0.00) | 0.000 | 0.00479 | 0.00870 |
| visual_camera | visual_camera | False | 0.980 | 0.020 | 0.000 | 144.568 | 22.3 | 0.0 (0.00) | 0.000 | 0.00499 | 0.00881 |
| visual_camera_control | visual_camera_control | False | 0.920 | 0.080 | 0.000 | 122.810 | 28.9 | 0.0 (0.00) | 0.000 | 0.00719 | 0.01246 |
| full_light_geometry | full_light_geometry | True | 0.710 | 0.230 | 0.060 | 50.321 | 39.5 | 38.3 (0.97) | 0.980 | 0.01108 | 0.02390 |
| full_contact_light | full_contact_light | True | 0.650 | 0.320 | 0.030 | 15.318 | 36.3 | 35.2 (0.97) | 0.970 | 0.01317 | 0.02631 |
| hard_full_light_bucket | full_light_geometry | True | 0.530 | 0.460 | 0.010 | -57.704 | 20.3 | 18.9 (0.93) | 0.920 | 0.01957 | 0.02768 |
