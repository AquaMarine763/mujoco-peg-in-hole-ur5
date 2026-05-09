# Guarded Policy Evaluation

- Generated: `2026-05-08T12:28:38`
- Model: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
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
| clean | none | False | 0.080 | 0.220 | 0.700 | -228.196 | 152.9 | 0.0 (0.00) | 0.000 | 0.02294 | 0.01686 |
| visual_camera | visual_camera | False | 0.260 | 0.210 | 0.530 | -139.461 | 137.8 | 0.0 (0.00) | 0.000 | 0.02203 | 0.01618 |
| visual_camera_control | visual_camera_control | False | 0.250 | 0.220 | 0.530 | -142.523 | 136.8 | 0.0 (0.00) | 0.000 | 0.02290 | 0.01691 |
| full_light_geometry | full_light_geometry | True | 0.620 | 0.280 | 0.100 | 69.208 | 101.2 | 91.8 (0.91) | 0.940 | 0.01599 | 0.01855 |
| full_contact_light | full_contact_light | True | 0.650 | 0.290 | 0.060 | 71.694 | 98.0 | 88.6 (0.90) | 0.930 | 0.01650 | 0.01905 |
| hard_full_light_bucket | full_light_geometry | True | 0.590 | 0.280 | 0.130 | 66.280 | 105.0 | 96.1 (0.92) | 0.950 | 0.01709 | 0.01876 |
