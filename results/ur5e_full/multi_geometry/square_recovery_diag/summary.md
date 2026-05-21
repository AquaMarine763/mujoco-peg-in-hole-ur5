# Square Recovery Diagnostic

Date: 2026-05-21

Branch: `feature/multi-geometry`

## Change

Implemented an opt-in square-aware final-servo recovery path:

- only activates for `peg_shape == square`
- only activates inside `descend` / `low_recenter`
- requires low-Z final-servo state, bounded XY, and persistent high tilt
- adds `square_recover_lift` and `square_recover_recenter` phases
- exposes CLI/config switches through eval, demo, and inference scripts
- adds step-trace fields:
  - `guard_final_servo_square_recovery_active`
  - `guard_final_servo_square_recovery_triggered`
  - `guard_final_servo_square_recovery_tilt_steps`

Defaults remain unchanged. The feature is diagnostic/experimental and is not promoted.

## Main Results

Baseline reference on `square_square`, strictstable49, 20ep seed `612000`:

- `0.850/0.000/0.150`
- failures: timeout-only

Focused high-tilt seed `612010`:

- square recovery only, tilt `12 deg`, lift `35 mm`: timeout
- with near IK orientation weight `0.03`, lift `60 mm`: timeout
- with near IK orientation weight `0.03`, lift `35 mm`, tilt `18 deg`: timeout
- with `max_steps=1500`: still timeout
- with near IK orientation weight `0.06`: still timeout

Targeted 14ep window, seed `612000-612013`, candidate:

- near IK orientation weight `0.03`
- tilt trigger `18 deg`
- lift `35 mm`
- max retries `4`

Result:

- `11/14 = 0.786` success
- zero collisions
- failed seeds stayed `612008`, `612010`, `612013`

Low-recenter narrow-band follow-ups:

- trigger/release `5.2/4.8 mm`: still `11/14`
- trigger/release `5.6/5.1 mm`: still `11/14`

## Interpretation

The new square recovery logic is useful diagnostically but does not solve the current `square_square` bottleneck.

Observed failure buckets:

- `612010`: persistent high-tilt case. Square recovery triggers, lifts, and recenters, but tilt and XY error reappear before successful insertion.
- `612008` / `612013`: low-tilt near-misses. They often end around `5.5 mm` XY with good Z, or around `5.0 mm` XY with too much Z. This is a final-servo/contact tracking problem more than a square-tilt problem.

Important conclusion:

- Do not promote square recovery as default.
- Do not keep scanning simple thresholds.
- The next useful change should target the low-level final insertion behavior: either a more explicit contact-state insert controller, or a geometry-aware success/control criterion that reasons about actual peg-in-hole contact depth and clearance instead of only fixed XY/Z thresholds.
