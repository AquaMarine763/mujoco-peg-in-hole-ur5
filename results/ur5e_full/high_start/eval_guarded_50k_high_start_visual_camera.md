# Guarded Policy Evaluation

- Generated: `2026-05-08T18:39:21`
- Model: `checkpoints\ur5e_full\high_start\sac_image_bc_50k_high_start_visual_camera.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `510000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.08`
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
| clean | none | True | 0.190 | 0.470 | 0.340 | 225.275 | 496.8 | 306.5 (0.62) | 0.760 | 0.03117 | 0.03211 |
| visual_camera | visual_camera | True | 0.240 | 0.420 | 0.340 | -221.860 | 516.5 | 220.5 (0.43) | 0.610 | 0.06557 | 0.04705 |
| visual_camera_control | visual_camera_control | True | 0.180 | 0.470 | 0.350 | -304.241 | 510.7 | 203.3 (0.40) | 0.600 | 0.06743 | 0.05562 |
| full_light_geometry | full_light_geometry | True | 0.170 | 0.510 | 0.320 | -170.625 | 471.0 | 206.1 (0.44) | 0.690 | 0.06076 | 0.04785 |
| full_contact_light | full_contact_light | True | 0.220 | 0.500 | 0.280 | -109.138 | 465.6 | 202.0 (0.43) | 0.700 | 0.05828 | 0.04202 |
| hard_full_light_bucket | full_light_geometry | True | 0.150 | 0.520 | 0.330 | -432.318 | 507.0 | 158.3 (0.31) | 0.570 | 0.08274 | 0.06235 |
