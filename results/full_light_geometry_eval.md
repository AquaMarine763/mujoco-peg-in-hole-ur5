# Full Light Geometry Evaluation

Model:
`checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle/sac_image_bc.zip`

Environment level: `full_light_geometry`

This level keeps the existing visual, camera, and control randomization, then
adds light geometry perturbations:

- hole center XY jitter: `+-2 mm`
- fixture height jitter: `+-1 mm`
- table height jitter: `+-1 mm`
- hole half-size range: `25-29 mm`
- peg radius range: `11.5-12.5 mm`

Evaluation threshold: `success_xy_tolerance=0.005`,
`success_z_tolerance=0.01`.

100-episode result:

| Success | Collision | Mean return |
| ---: | ---: | ---: |
| 0.960 | 0.010 | 55.771 |

Demo:
`demos/image_bc_sidecam_full_light_geometry.gif`

Conclusion:

The delay-robust control model already clears the initial light-geometry target
of `>=0.90` success rate. The next full-randomization step can move to a
slightly harder geometry/contact stage rather than collecting a new dataset for
this exact configuration.
