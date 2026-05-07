# Guarded Policy Evaluation

- Generated: `2026-05-08T00:36:11`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `default`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.08`
- Guard risk XY: `0.0`
- Guard scenario filter: `geometry`
- Guard blend: `1.0`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guarded align/insert XY: `0.02/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | False | 0.980 | 0.020 | 0.000 | 147.370 | 22.5 | 0.0 (0.00) | 0.000 | 0.00479 | 0.00868 |
| visual_camera | visual_camera | False | 0.980 | 0.020 | 0.000 | 144.206 | 22.2 | 0.0 (0.00) | 0.000 | 0.00496 | 0.00882 |
| visual_camera_control | visual_camera_control | False | 0.920 | 0.080 | 0.000 | 122.760 | 28.8 | 0.0 (0.00) | 0.000 | 0.00721 | 0.01248 |
| full_light_geometry | full_light_geometry | True | 0.630 | 0.300 | 0.070 | 25.947 | 41.8 | 40.7 (0.97) | 0.980 | 0.01212 | 0.02847 |
| full_contact_light | full_contact_light | True | 0.630 | 0.360 | 0.010 | -1.919 | 32.6 | 31.5 (0.97) | 0.970 | 0.01322 | 0.02602 |
| hard_full_light_bucket | full_light_geometry | True | 0.420 | 0.580 | 0.000 | -106.680 | 20.7 | 19.3 (0.93) | 0.920 | 0.02169 | 0.03239 |
