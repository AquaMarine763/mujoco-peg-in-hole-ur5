# Pose IK 0.06 / 48 Iterations + Kp2 Summary

Generated on 2026-05-18.

## Setup

- Model: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_insert_drift_2k_w10_e1.zip`
- MuJoCo XML: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Controller: pose IK + guarded final servo
- Candidate settings:
  - `ik_orientation_weight=0.06`
  - `ik_max_iterations=48`
  - `nominal_actuator_kp_multiplier=2.0`
- Seed: `602000`

## Hard 60-Episode Gate

| Variant | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| pose IK baseline, `0.12/24` | 0.717 | 0.100 | 0.183 |
| pose IK candidate, `0.06/48` | 0.767 | 0.100 | 0.133 |
| pose IK candidate + Kp2 | 0.850 | 0.000 | 0.150 |
| pose IK candidate + Kp2 + align 0.030 | 0.833 | 0.000 | 0.167 |

Numbers are success / collision / timeout. The Kp2 combination is the best hard-gate result so far because it increases success and removes collisions.

Additional hard seed check:

| Variant | Seed | Episodes | Success | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: |
| pose IK candidate + Kp2 | 604000 | 60 | 0.867 | 0.000 | 0.133 |

## 100-Episode Matrix

| Scenario | Baseline `0.12/24` | `0.06/48` | `0.06/48 + Kp2` |
| --- | ---: | ---: | ---: |
| clean | 0.780 / 0.040 / 0.180 | 0.850 / 0.010 / 0.140 | 0.910 / 0.000 / 0.090 |
| visual_camera | 0.780 / 0.030 / 0.190 | 0.840 / 0.030 / 0.130 | 0.910 / 0.000 / 0.090 |
| visual_camera_control | 0.770 / 0.060 / 0.170 | 0.840 / 0.050 / 0.110 | 0.910 / 0.000 / 0.090 |
| full_light_geometry | 0.790 / 0.040 / 0.170 | 0.850 / 0.050 / 0.100 | 0.900 / 0.000 / 0.100 |
| full_contact_light | 0.800 / 0.040 / 0.160 | 0.850 / 0.060 / 0.090 | 0.900 / 0.000 / 0.100 |
| hard_full_light_bucket | 0.750 / 0.090 / 0.160 | 0.790 / 0.080 / 0.130 | 0.890 / 0.000 / 0.110 |

Numbers are success / collision / timeout.

## Remaining Failures

The hard 60ep Kp2 failure trace has `9` failures, all timeouts:

- `7` misaligned timeouts
- `2` near-XY no-insert timeouts
- `0` collisions

The timeout failures remain delay-2 dominated. They usually end high above the target with XY around `20 - 30 mm`, which suggests the next improvement should target high-level approach progress under delayed control rather than collision avoidance.

Widening `guarded_align_xy_tolerance` to `0.030` did not help: the hard 60ep result regressed slightly to `0.833 / 0.000 / 0.167`.

## Demo Check

The current Kp2 candidate demo is generated with:

```text
configs\sim\ur5e_full\demo_high_start_hard_wrist_pose_control_state_insert_drift_2k_w10_e1_final_servo_pose_ik_wori006_it48_kp2.yaml
```

Result:

- success: `True`
- collision: `False`
- steps: `309`
- final XY/Z error: about `4.3 mm / 9.7 mm`
- output: `demos\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori006_it48_kp2.gif`
- trajectory trace: `results\ur5e_full\high_start\hard\correction\demo_insert_drift_pose_ik_wori006_it48_kp2_trace.csv`

The GIF is `2560x720` with `310` frames. The requested MP4 output fell back to GIF because the local `imageio` video backend is unavailable.

## Decision

Treat `ik_orientation_weight=0.06`, `ik_max_iterations=48`, and `nominal_actuator_kp_multiplier=2.0` as the current best full-UR5e controller candidate.

Do not promote fixture-clearance lift or wider align tolerance. They did not improve the candidate.

Next work:

1. Use the Kp2 candidate for the next high-start controller/guard iteration.
2. Inspect or redesign approach progress for delay-2 high-misalignment timeouts.
3. Consider pushing/tagging this as a stable controller milestone after the next focused timeout-improvement pass or on user request.
