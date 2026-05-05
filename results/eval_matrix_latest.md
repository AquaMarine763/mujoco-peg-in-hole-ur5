# Evaluation Matrix

- Generated: `2026-05-05T17:05:10`
- Model: `checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle\sac_image_bc.zip`
- Observation mode: `image`
- Episodes per scenario: `100`
- Seed: `90000`
- Success tolerances: `xy=0.005`, `z=0.01`

| Scenario | Level | Success | Collision | Timeout | Mean return | Mean steps | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | 1.000 | 0.000 | 0.000 | 161.685 | 20.6 | 0.00233 | 0.00811 |
| visual_camera | visual_camera | 0.960 | 0.020 | 0.020 | 147.203 | 25.1 | 0.00578 | 0.00920 |
| visual_camera_control | visual_camera_control | 0.970 | 0.020 | 0.010 | 148.031 | 24.9 | 0.00637 | 0.00857 |
| full_light_geometry | full_light_geometry | 0.970 | 0.020 | 0.010 | 148.194 | 25.6 | 0.00675 | 0.00877 |
| full_contact_light | full_contact_light | 0.960 | 0.020 | 0.020 | 146.904 | 28.5 | 0.00676 | 0.00889 |
