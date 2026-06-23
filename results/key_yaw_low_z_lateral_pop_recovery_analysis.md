# Low-Z Lateral-Pop Recovery Analysis

Date: 2026-06-23

## Summary

This diagnostic targets the late rectangular-key failure tail after gated re-acquire.
The safe recovery-only configuration is:

`configs/sim2real/multigeom_v2_true_fixture_tight_yaw_key_visible_brake_low_z_lateral_pop_recovery_eval.yaml`

Smoke result on seeds `906500,908500,908516`:

| Seed | Success | Collision | Timeout |
| --- | --- | --- | --- |
| 906500 | 1 | 0 | 0 |
| 908500 | 1 | 0 | 0 |
| 908516 | 0 | 0 | 1 |

Conclusion: safe, but not enough to beat the current baseline.

## Rejected Variant

A local late-finish/freeze-XY override was also tested during implementation.
It reduced late XY drift but regressed normal progress:

| Seed | Success | Collision | Timeout |
| --- | --- | --- | --- |
| 906500 | 0 | 0 | 1 |
| 908500 | 1 | 0 | 0 |
| 908516 | 0 | 1 | 0 |

Conclusion: reject the freeze-XY late-finish variant. Keep it default-off.
