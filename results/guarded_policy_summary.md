# Guarded Policy Summary

- Generated: `2026-05-06T20:05:00`
- Base policy: `staged_crop_full_light_replay_750k_e4`
- Observation mode: `image + near_hole_crop`
- Wrapper: learned visual policy plus deployment-time `guarded_two_stage` insert controller

## Implementation

`scripts/eval_guarded_policy.py` evaluates the trained image policy with an
optional guarded insertion wrapper. The learned policy still produces actions
every step. When the guard is active, the final command can be overridden or
blended with `guarded_two_stage`.

Default guarded insert parameters:

| Parameter | Value |
| --- | ---: |
| `guard_start_xy` | 0.060 |
| `guard_start_z` | 0.100 |
| `guard_blend` | 1.0 |
| `guarded_align_xy_tolerance` | 0.025 |
| `guarded_insert_xy_tolerance` | 0.005 |
| `guarded_max_xy_action` | 0.005 |
| `guarded_max_down_action` | 0.0035 |
| `guarded_prediction_steps` | 1.0 |

The script supports `--guard-scenario-filter none|all|geometry|hard`. The best
tested evaluation setting is `geometry`: keep the learned policy unchanged on
clean, visual, and control-only cases, and enable guarded insertion on
geometry/contact stress cases.

## Standard Matrix

| Configuration | Clean | Visual camera | Visual camera control | Full light geometry | Full contact light |
| --- | ---: | ---: | ---: | ---: | ---: |
| no guard | 0.980 | 0.980 | 0.910 | 0.580 | 0.580 |
| guard all scenarios | 1.000 | 1.000 | 0.830 | 0.690 | 0.660 |
| guard geometry/contact only | 0.980 | 0.980 | 0.920 | 0.690 | 0.660 |

## Hard Bucket

The hard bucket uses `full_light_geometry`, `delay=2`,
`filter_alpha=0.55:0.70`, `action_scale=0.8:1.1`, and
`noise=0.0:0.00025`.

| Configuration | Seed | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: |
| no guard | 90000 | 0.330 | 0.670 | 0.000 |
| guard geometry/contact only | 90000 | 0.480 | 0.520 | 0.000 |
| no guard | 850000 | 0.330 | 0.660 | 0.010 |
| guard geometry/contact only | 850000 | 0.410 | 0.590 | 0.000 |

## Conclusion

Deployment-time guarded insertion is more effective than the previous hard
success-only BC replay. It improves the hard bucket from `0.330` to `0.480` on
seed `90000`, and raises standard `full_light_geometry` from `0.580` to
`0.690`.

The important caveat is that unconditional guarded control hurts
`visual_camera_control` (`0.910` to `0.830`). The recommended deployment shape
is therefore selective: use the learned policy normally, and enable guarded
insertion only when entering the geometry/contact-sensitive final insertion
stage.

This wrapper does not replace the recommended policy checkpoint. It is a
deployment-time controller around:

`checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
