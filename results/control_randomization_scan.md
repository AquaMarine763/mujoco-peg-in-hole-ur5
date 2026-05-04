# Control Randomization Sensitivity Scan

Model:
`checkpoints_image_bc_50k_sidecam_visual_camera_control_oracle/sac_image_bc.zip`

Evaluation threshold: `success_xy_tolerance=0.005`,
`success_z_tolerance=0.01`.

The quick scan used 50 episodes per setting with seed `70000`. It isolates
control-channel factors while keeping visual+camera randomization active.

| Setting | Scale | Noise std | Delay | Filter alpha | Success | Collision | Timeout |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| visual_camera_reference | 1.0:1.0 | 0.0:0.0 | 0:0 | 1.0:1.0 | 0.94 | 0.02 | 0.04 |
| scale_only | 0.8:1.2 | 0.0:0.0 | 0:0 | 1.0:1.0 | 0.92 | 0.02 | 0.06 |
| noise_only | 1.0:1.0 | 0.0:0.0008 | 0:0 | 1.0:1.0 | 0.96 | 0.02 | 0.02 |
| delay_only | 1.0:1.0 | 0.0:0.0 | 0:2 | 1.0:1.0 | 0.88 | 0.02 | 0.10 |
| filter_only | 1.0:1.0 | 0.0:0.0 | 0:0 | 0.55:1.0 | 0.94 | 0.02 | 0.04 |
| delay_filter | 1.0:1.0 | 0.0:0.0 | 0:2 | 0.55:1.0 | 0.90 | 0.02 | 0.08 |
| default_control | 0.8:1.2 | 0.0:0.0008 | 0:2 | 0.55:1.0 | 0.88 | 0.02 | 0.10 |
| high_noise | 1.0:1.0 | 0.0:0.0015 | 0:0 | 1.0:1.0 | 0.92 | 0.02 | 0.06 |
| high_delay | 1.0:1.0 | 0.0:0.0 | 0:3 | 1.0:1.0 | 0.78 | 0.02 | 0.20 |
| high_all | 0.75:1.25 | 0.0:0.0015 | 0:3 | 0.4:1.0 | 0.72 | 0.10 | 0.18 |

100-episode confirmation runs with seed `1000`:

| Setting | Success | Collision | Mean return |
| --- | ---: | ---: | ---: |
| default_control | 0.92 | 0.02 | 50.728 |
| high_delay | 0.85 | 0.02 | 46.569 |
| high_all | 0.82 | 0.08 | 36.582 |

Conclusion:

- Action delay is the dominant isolated control factor. It mainly causes
  timeouts rather than immediate collisions.
- Noise and low-pass filtering at the current default levels are comparatively
  mild.
- Strong combined randomization increases both timeouts and collisions.
- The next training improvement should target `0-3` step delay robustness
  before expanding dynamics/contact randomization.
