# Split Final-Servo 60ep Profile Gate

Generated: 2026-05-22

Baseline config: `configs\sim\ur5e_full\eval_high_start_hard_localkp3_recovery_strictstable49_60ep.yaml`

Split-servo overrides:

- `guard_final_servo_split_recovery_enabled=true`
- contact unjam: wall steps `6`, lift height `0.045 m`
- near miss: steps `30`, XY/Z max `0.0068/0.060 m`, max steps `500`, max down action `0.0025 m`
- low recenter height `0.008 m`
- near-miss XY bias `[0.0035, 0.0035]`

## Matrix

| Profile | Episodes | Success | Collision | Timeout | Failed Seeds |
|---|---:|---:|---:|---:|---|
| `single` | 60 | 0.967 | 0.000 | 0.033 | 612010, 612032 |
| `round_square` | 60 | 0.967 | 0.000 | 0.033 | 612010, 612032 |
| `square_square` | 60 | 0.950 | 0.000 | 0.050 | 612010, 612021, 612032 |
| `mixed_basic` | 60 | 0.967 | 0.000 | 0.033 | 612010, 612032 |

## Interpretation

The split final-servo setting passes the larger same-seed 60ep profile gate with zero collisions. It keeps non-square profiles at `58/60` success and keeps `square_square` at `57/60`.

The remaining failures are still timeout-only. Seeds `612010` and `612032` appear across all profiles, so they are not square-only geometry failures. `square_square` adds one extra failure, `612021`, which supports the current diagnosis that square insertion is more sensitive in the last few millimeters.

Next useful work should not be more broad one-parameter scanning. The likely next target is a more deliberate high-tilt/contact unjam path for `612010/612032`, plus a per-seed contact trace run if exact wall/plate contact timing is needed.
