# Split Final-Servo Profile Matrix

Generated: 2026-05-22

Config baseline: `configs\sim\ur5e_full\eval_high_start_hard_localkp3_recovery_strictstable49_60ep.yaml`

Split-servo overrides:

- `guard_final_servo_split_recovery_enabled=true`
- contact unjam: wall steps `6`, lift height `0.045 m`
- near miss: steps `30`, XY/Z max `0.0068/0.060 m`, max steps `500`, max down action `0.0025 m`
- low recenter height `0.008 m`
- near-miss XY bias `[0.0035, 0.0035]`

## 20ep Matrix, Seed 612000

| Profile | Success | Collision | Timeout | Mean Steps | Failed Seed |
|---|---:|---:|---:|---:|---|
| `single` | 0.950 | 0.000 | 0.050 | 387.10 | 612010 |
| `round_square` | 0.950 | 0.000 | 0.050 | 387.15 | 612010 |
| `square_square` | 0.950 | 0.000 | 0.050 | 381.70 | 612010 |
| `mixed_basic` | 0.950 | 0.000 | 0.050 | 376.40 | 612010 |

## Interpretation

The split final-servo setting improves `square_square` from the strictstable49 baseline `0.850/0.000/0.150` to `0.950/0.000/0.050` without a same-seed regression on `single`, `round_square`, or `mixed_basic`.

The remaining common failure is seed `612010`, which earlier contact diagnostics identified as a persistent high-tilt wall-contact case. This suggests the low-contact near-miss branch is useful, while the contact unjam branch still needs a stronger or more deliberate retreat/recenter strategy before the high-tilt case is solved.
