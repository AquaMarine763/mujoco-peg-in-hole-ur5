# Guarded Policy Evaluation

- Generated: `2026-05-08T19:30:42`
- Model: `checkpoints\ur5e_full\high_start\easy\sac_image_bc_20k_high_start_easy_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `534000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.1`
- Guard risk XY: `0.0`
- Guard scenario filter: `all`
- Guard blend: `1.0`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guarded align/insert XY: `0.02/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | True | 0.600 | 0.200 | 0.200 | 146.545 | 307.1 | 256.9 (0.84) | 0.990 | 0.01343 | 0.01866 |
| visual_camera | visual_camera | True | 0.590 | 0.210 | 0.200 | 123.959 | 326.9 | 246.9 (0.76) | 0.910 | 0.01762 | 0.01655 |
| visual_camera_control | visual_camera_control | True | 0.570 | 0.280 | 0.150 | 138.522 | 296.9 | 223.0 (0.75) | 0.910 | 0.01993 | 0.01909 |
| full_light_geometry | full_light_geometry | True | 0.560 | 0.220 | 0.220 | 151.533 | 331.4 | 268.7 (0.81) | 0.940 | 0.01612 | 0.01821 |
| full_contact_light | full_contact_light | True | 0.530 | 0.220 | 0.250 | 151.898 | 358.0 | 272.5 (0.76) | 0.920 | 0.01876 | 0.01871 |
| hard_full_light_bucket | full_light_geometry | True | 0.470 | 0.330 | 0.200 | 87.764 | 311.1 | 237.0 (0.76) | 0.900 | 0.02222 | 0.02056 |
