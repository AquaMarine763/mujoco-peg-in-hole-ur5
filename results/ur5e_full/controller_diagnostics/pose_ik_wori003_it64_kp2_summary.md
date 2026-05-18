# Pose IK 0.03 / 64 Iterations + Kp2 Summary

Generated on 2026-05-18.

## Setup

- Model: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_insert_drift_2k_w10_e1.zip`
- MuJoCo XML: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Controller: pose IK + guarded final servo
- Candidate settings:
  - `ik_orientation_weight=0.03`
  - `ik_max_iterations=64`
  - `nominal_actuator_kp_multiplier=2.0`

## Hard-Bucket Result

| Variant | Seed | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: |
| previous best `0.06/48 + Kp2` | 602000 | 60 | 0.850 | 0.000 | 0.150 |
| previous best `0.06/48 + Kp2` | 604000 | 60 | 0.867 | 0.000 | 0.133 |
| current candidate `0.03/64 + Kp2` | 602000 | 60 | 0.883 | 0.000 | 0.117 |
| current candidate `0.03/64 + Kp2` | 604000 | 60 | 0.900 | 0.000 | 0.100 |
| current candidate `0.03/64 + Kp2` | 602000 | 100 | 0.910 | 0.000 | 0.090 |

The candidate improves hard-bucket success on both checked seeds without reintroducing collisions.

## 100-Episode Matrix

| Scenario | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| clean | 0.970 | 0.000 | 0.030 |
| visual_camera | 0.970 | 0.000 | 0.030 |
| visual_camera_control | 0.940 | 0.000 | 0.060 |
| full_light_geometry | 0.910 | 0.000 | 0.090 |
| full_contact_light | 0.910 | 0.000 | 0.090 |
| hard_full_light_bucket | 0.910 | 0.000 | 0.090 |

The first five rows come from `eval_insert_drift_pose_ik_wori003_it64_kp2_matrix_100ep_seed602000.*`. The hard-bucket row was run separately with the same seed because the initial matrix config missed `include_hard_bucket`; the config has now been fixed.

## Failure Shape

On hard seed `602000`, the candidate has `9` failures over 100 episodes:

- `7` timeout episodes never enter final servo, ending around `7.5 - 21 mm` XY and `18 - 65 mm` above target.
- `2` timeout episodes enter final-servo descent and end very close to success, around `6.3 mm` XY and `8.7 mm` above target.
- Collisions remain `0`.

Compared with `0.06/48 + Kp2`, the remaining failures are lower and closer to the hole, which supports the hypothesis that loosening pose orientation weight improves Cartesian tracking authority.

## Demo Check

Config:

```text
configs\sim\ur5e_full\demo_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori003_it64_kp2.yaml
```

Result:

- success: `True`
- collision: `False`
- steps: `335`
- final XY/Z error: about `4.5 mm / 9.6 mm`
- output: `demos\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori003_it64_kp2.gif`
- trajectory trace: `results\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori003_it64_kp2_trace.csv`

The requested MP4 output fell back to GIF because the local `imageio` video backend is unavailable.

## Decision

Treat `ik_orientation_weight=0.03`, `ik_max_iterations=64`, and `nominal_actuator_kp_multiplier=2.0` as the current best full-UR5e controller candidate.

Next work:

1. Promote this as the controller milestone and consider pushing/tagging.
2. Then target the remaining near-success final-servo timeouts and the higher pre-final-servo alignment timeouts separately.
