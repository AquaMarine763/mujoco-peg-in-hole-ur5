# Controller Gain And Frame-Skip Diagnostic

Generated on 2026-05-17 while investigating the full-UR5e hard high-start plateau.

## What Changed

- `PegInHoleMujocoEnv` now supports nominal arm dynamics multipliers:
  - `nominal_joint_damping_multiplier`
  - `nominal_actuator_kp_multiplier`
- `scripts/eval_guarded_policy.py` exposes:
  - `--nominal-joint-damping-multiplier`
  - `--nominal-actuator-kp-multiplier`
  - `--frame-skip`
- Contact/dynamics randomization now composes sampled random multipliers on top of the nominal multipliers.

## Evaluation Results

All rows use the insert-drift w10 e1 checkpoint, pose IK, final-servo hard config, hard full-light bucket, seed `602000`.

| Variant | Episodes | Success | Collision | Timeout | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Kp 1, frame_skip 10 | 20 | 0.850 | 0.050 | 0.100 | same-seed short control |
| Kp 2, frame_skip 10 | 20 | 0.900 | 0.000 | 0.100 | short smoke improved collision |
| Kp 2, frame_skip 10 | 60 | 0.733 | 0.000 | 0.267 | removes collisions but increases timeout |
| Kp 4, frame_skip 10 | 20 | 0.250 | 0.000 | 0.750 | too aggressive / not promoted |
| Kp 2, two-phase oracle | 20 | 0.900 | 0.000 | 0.100 | flat versus Kp 2 |
| Kp 2, frame_skip 20 | 20 | 0.900 | 0.000 | 0.100 | fewer guard/final-servo steps |
| Kp 2, frame_skip 20 | 60 | 0.733 | 0.000 | 0.267 | same success as Kp 2 frame_skip 10 |
| orientation 0.06, IK iters 48 | 20 | 0.900 | 0.050 | 0.050 | best 20ep timeout result |
| orientation 0.06, IK iters 48 | 60 | 0.767 | 0.100 | 0.133 | modest 60ep improvement |
| orientation 0.06, IK iters 48, Kp 2 | 20 | 0.900 | 0.000 | 0.100 | Kp removed collision but lost timeout gain |
| orientation 0.03, IK iters 64 | 20 | 0.850 | 0.000 | 0.150 | too little orientation weight |
| orientation 0.06, IK iters 48, seed 604000 | 20 | 0.700 | 0.200 | 0.100 | matches default seed 604000 success |
| orientation 0.06, IK iters 48, seed 605000 | 20 | 0.700 | 0.050 | 0.250 | timeout worse than default seed 605000 |
| orientation 0.06, IK iters 48, Kp 2 | 60 | 0.850 | 0.000 | 0.150 | best hard-gate result so far |
| orientation 0.06, IK iters 48, Kp 2, align 0.030 | 60 | 0.833 | 0.000 | 0.167 | wider align regressed slightly |

Previous pose-IK hard gate for comparison: `0.717 / 0.100 / 0.183` over 60 episodes.
Previous pose-IK 20ep x 3-seed average was `0.750 / 0.117 / 0.133`; orientation `0.06` with 48 IK iterations is `0.767 / 0.100 / 0.133` over the same seed windows.

The 100-episode matrix also favored the `0.06/48` setting:

| Scenario | Baseline success | Candidate success | Delta |
| --- | ---: | ---: | ---: |
| clean | 0.780 | 0.850 | +0.070 |
| visual_camera | 0.780 | 0.840 | +0.060 |
| visual_camera_control | 0.770 | 0.840 | +0.070 |
| full_light_geometry | 0.790 | 0.850 | +0.060 |
| full_contact_light | 0.800 | 0.850 | +0.050 |
| hard_full_light_bucket | 0.750 | 0.790 | +0.040 |

Detailed matrix summary: `results\ur5e_full\controller_diagnostics\pose_ik_wori006_it48_matrix_summary.md`.

The Kp2 combination improved the 100-episode matrix again and removed all collisions:

| Scenario | Candidate success | Candidate + Kp2 success | Candidate + Kp2 collision |
| --- | ---: | ---: | ---: |
| clean | 0.850 | 0.910 | 0.000 |
| visual_camera | 0.840 | 0.910 | 0.000 |
| visual_camera_control | 0.840 | 0.910 | 0.000 |
| full_light_geometry | 0.850 | 0.900 | 0.000 |
| full_contact_light | 0.850 | 0.900 | 0.000 |
| hard_full_light_bucket | 0.790 | 0.890 | 0.000 |

Kp2 summary: `results\ur5e_full\controller_diagnostics\pose_ik_wori006_it48_kp2_summary.md`.

## Interpretation

Kp 2 is useful as a diagnostic because it removes hard-bucket collisions in this seed, but it does not materially improve the 60-episode success gate. It mostly converts some collision cases into timeout cases.

Lowering the pose-IK orientation weight from `0.12` to `0.06`, increasing IK iterations from `24` to `48`, and applying a nominal Kp multiplier of `2.0` is the current best controller candidate. It improves the hard 60ep seed `602000` to `0.850 / 0.000 / 0.150`, and the 100ep matrix improves success across all scenarios while removing collisions.

The failure trace splits into:

- `misaligned_timeout`: the peg stays about `20 - 40 mm` off in XY and around `80 - 100 mm` above target.
- `near_xy_timeout_no_insert`: the peg reaches about `5 - 9 mm` XY but does not finish the last insertion stage.

In both classes, the trace shows millimeter-level applied actions while the measured peg-tip motion is much smaller. This keeps the main bottleneck at low-level Cartesian tracking / IK / guard behavior, not more same-family correction BC replay.

## Decision

Do not promote frame_skip 20, fixture-clearance lift, or wider align tolerance. Keep `ik_orientation_weight=0.06`, `ik_max_iterations=48`, and `nominal_actuator_kp_multiplier=2.0` as the current best controller candidate.

Next useful work:

1. Add a focused diagnostic or controller change for Cartesian tracking under guard activation, especially high-Z misalignment with delay-2 control randomization.
2. Inspect whether pose IK target error and joint target tracking can be reduced with IK weights, iteration count, or posture regularization.
3. Only after measured tracking improves, rerun the hard 60-episode gate and then decide whether to collect new correction data.
