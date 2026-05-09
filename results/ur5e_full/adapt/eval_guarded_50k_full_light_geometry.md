# Guarded Policy Evaluation

- Generated: `2026-05-08T13:38:37`
- Model: `checkpoints\ur5e_full\adapt\sac_image_bc_50k_full_light_geometry.zip`
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
| clean | none | False | 0.950 | 0.000 | 0.050 | 118.439 | 128.0 | 0.0 (0.00) | 0.000 | 0.00435 | 0.00816 |
| visual_camera | visual_camera | False | 0.660 | 0.000 | 0.340 | 62.733 | 146.0 | 0.0 (0.00) | 0.000 | 0.00588 | 0.00797 |
| visual_camera_control | visual_camera_control | False | 0.610 | 0.020 | 0.370 | 44.589 | 146.9 | 0.0 (0.00) | 0.000 | 0.00699 | 0.00884 |
| full_light_geometry | full_light_geometry | True | 0.840 | 0.150 | 0.010 | 162.528 | 97.0 | 88.3 (0.91) | 0.990 | 0.00908 | 0.01447 |
| full_contact_light | full_contact_light | True | 0.840 | 0.160 | 0.000 | 158.124 | 95.8 | 87.1 (0.91) | 0.990 | 0.00945 | 0.01487 |
| hard_full_light_bucket | full_light_geometry | True | 0.810 | 0.190 | 0.000 | 137.583 | 98.3 | 89.3 (0.91) | 0.990 | 0.01036 | 0.01597 |
