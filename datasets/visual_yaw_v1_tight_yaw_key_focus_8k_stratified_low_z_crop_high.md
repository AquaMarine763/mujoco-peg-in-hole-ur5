# Visual Yaw Dataset

- Schema: `visual_yaw_v1_near_hole_no_tip_highlight`
- Output: `datasets\visual_yaw_v1_tight_yaw_key_focus_8k_stratified_low_z_crop_high.npz`
- Samples: `8192`
- Profiles: `rectangular_key, rectangular_key, rectangular_key, square_square, triangle_triangle, hex_hex`
- Fixture mode / variant: `true_mesh` / `tight_yaw`
- Peg-tip visual helpers enabled: `False`
- Domain randomization: `False` / `visual_camera`
- Yaw sampling: `stratified` / bins `12`
- Mean/max IK error: `0.000009` / `0.003798`
- Mean/max abs yaw error deg: `62.186` / `179.998`

| Profile | Samples |
| --- | ---: |
| `hex_hex` | 1365 |
| `rectangular_key` | 4097 |
| `square_square` | 1365 |
| `triangle_triangle` | 1365 |
