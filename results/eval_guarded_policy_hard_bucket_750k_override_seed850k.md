# Guarded Policy Evaluation

- Generated: `2026-05-06T19:27:22`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `850000`
- Guard start XY: `0.06`
- Guard start Z above target: `0.1`
- Guard blend: `1.0`
- Guarded align/insert XY: `0.025/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Guard ep. | Final XY | Final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| hard_full_light_bucket | full_light_geometry | 0.410 | 0.590 | 0.000 | -112.726 | 19.1 | 16.9 (0.88) | 0.920 | 0.02345 | 0.03309 |
