# Visual Yaw Dataset

- Schema: `visual_yaw_v1_near_hole_no_tip_highlight`
- Output: `datasets\visual_yaw_v1_tight_yaw_stratified_smoke_96.npz`
- Samples: `96`
- Profiles: `rectangular_key, rectangular_key, rectangular_key, square_square, triangle_triangle, hex_hex`
- Fixture mode / variant: `true_mesh` / `tight_yaw`
- Peg-tip visual helpers enabled: `False`
- Domain randomization: `False` / `visual_camera`
- Yaw sampling: `stratified` / bins `12`
- Mean/max IK error: `0.000002` / `0.000118`
- Mean/max abs yaw error deg: `63.827` / `179.488`

| Profile | Samples |
| --- | ---: |
| `hex_hex` | 16 |
| `rectangular_key` | 48 |
| `square_square` | 16 |
| `triangle_triangle` | 16 |
