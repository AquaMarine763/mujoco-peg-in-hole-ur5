# Pose IK Orientation 0.06 / Iterations 48 Matrix Summary

Generated on 2026-05-17.

## Setup

- Model: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_insert_drift_2k_w10_e1.zip`
- MuJoCo XML: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Controller: pose IK + guarded final servo
- Baseline: `ik_orientation_weight=0.12`, `ik_max_iterations=24`
- Candidate: `ik_orientation_weight=0.06`, `ik_max_iterations=48`
- Seed: `602000`
- Episodes: `100` per scenario

## 100-Episode Matrix

| Scenario | Baseline S/C/T | Candidate S/C/T | Success delta | Timeout delta | Collision delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| clean | 0.780 / 0.040 / 0.180 | 0.850 / 0.010 / 0.140 | +0.070 | -0.040 | -0.030 |
| visual_camera | 0.780 / 0.030 / 0.190 | 0.840 / 0.030 / 0.130 | +0.060 | -0.060 | +0.000 |
| visual_camera_control | 0.770 / 0.060 / 0.170 | 0.840 / 0.050 / 0.110 | +0.070 | -0.060 | -0.010 |
| full_light_geometry | 0.790 / 0.040 / 0.170 | 0.850 / 0.050 / 0.100 | +0.060 | -0.070 | +0.010 |
| full_contact_light | 0.800 / 0.040 / 0.160 | 0.850 / 0.060 / 0.090 | +0.050 | -0.070 | +0.020 |
| hard_full_light_bucket | 0.750 / 0.090 / 0.160 | 0.790 / 0.080 / 0.130 | +0.040 | -0.030 | -0.010 |

Numbers are success / collision / timeout.

## Interpretation

The candidate improves success rate across all six scenarios and consistently reduces timeouts. The effect is modest but broader than the hard-bucket-only signal.

The remaining risk is collision rate. The candidate does not collapse collision safety, but full-light and full-contact collision rates rise slightly versus the baseline. This means it should be treated as the next controller candidate, not a final default.

## Decision

Keep `ik_orientation_weight=0.06` and `ik_max_iterations=48` as the current best controller candidate.

Follow-up on 2026-05-18: adding `nominal_actuator_kp_multiplier=2.0` to this candidate improved the 100ep matrix again and removed collisions. The newer summary is:

```text
results\ur5e_full\controller_diagnostics\pose_ik_wori006_it48_kp2_summary.md
```

## Failure Trace

Hard 60ep failure analysis:

- `6` collision episodes, all classified as `high_fixture_wall_collision`.
- `8` timeout episodes:
  - `2` insert-band low-Z drift
  - `6` near-XY no-insert timeouts
- Collision failures were around `20 - 30 mm` XY and about `50 mm` above target.
- Timeout failures were low-Z failures around `5 - 10 mm` XY and about `8 mm` above target.
- The failure rows are all in the hard delay-2 bucket, so this is still a control-delay/tracking problem.

Raising `guard_start_z` from `0.12` to `0.16` or `0.20` did not change the 20ep hard result; both stayed `0.900 / 0.050 / 0.050`.

Next step:

1. Inspect whether delay-aware guarded actions can reduce high-fixture-wall collisions without reintroducing timeout.
2. If failure modes are acceptable, make the candidate the default for the next high-start controller/guard iteration.
3. Do not combine it with Kp=2 by default; Kp=2 removed collisions in one short run but worsened timeout in the 60-episode hard gate.
