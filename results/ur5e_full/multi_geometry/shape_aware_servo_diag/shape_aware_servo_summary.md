# Shape-Aware Servo Diagnostic

Date: 2026-05-21

Branch: `feature/multi-geometry`

## What Changed

- Added square-peg orientation diagnostics to `PegInHoleMujocoEnv` info:
  - square symmetry yaw error relative to the hole axes
  - square peg top-down projected half-width and clearance margin
  - tilt-induced lateral extent
  - tilt-aware projected half-width and clearance margin
- Added those fields to `scripts/eval_guarded_policy.py` step traces.
- Added `scripts/analyze_square_peg_trace.py` to summarize square-peg failure/success traces.

## Diagnostic Runs

Strict high-start config:

`configs/sim/ur5e_full/eval_high_start_hard_localkp3_recovery_strictstable49_60ep.yaml`

Profile:

`square_square`

Seeds:

- success references: `612000`, `612001`, `612002`
- known timeouts: `612008`, `612010`, `612013`

Machine-readable summary:

- `shape_orientation_summary.csv`
- `shape_orientation_summary.md`

## Key Findings

The `square_square` failures split into at least two buckets.

1. Persistent tilted/wedged insertion

   Seed `612010` ends at about `6.70 mm` XY and `7.62 mm` Z with final peg tilt about `20.65 deg`. Its final tilt-aware clearance margin is strongly negative. This looks like a genuine square-peg wedging case, not just missing episode length.

2. Low-tilt final-servo timeout

   Seeds `612008` and `612013` end with low final tilt (`1.07 deg` and `1.47 deg`) and positive final projected clearance margins, but still spend hundreds of steps in final-servo. These are more likely final-servo/low-recenter phase failures: the controller enters the insert band, drifts or lifts out, and does not complete before timeout.

Success references also show temporary tilt can be high during the episode, so a simple max-tilt threshold is not a good success/failure classifier. The more useful signal is persistent final/late-stage tilt combined with low-Z stall.

## Current Conclusion

Do not scale square-square BC data yet. The actor-contribution diagnostic already showed the current result is guard/controller dominated. This shape diagnostic now shows the controller gap is mixed:

- one bucket needs tilt-aware or orientation-retaining recovery,
- another bucket needs better final-servo phase logic/low-Z recenter completion even when orientation is not the main issue.

## Next Step

Implement an opt-in square-aware final-servo recovery gate rather than changing defaults:

- only activate for `peg_shape == square`
- only inside final-servo or low-Z guarded insertion
- trigger on persistent high final-stage tilt, not one-frame max tilt
- lift to a small safe height, re-align XY, and hold orientation before descending again
- keep existing strictstable49 defaults unchanged until a 20ep/60ep square-square gate improves without hurting `single` or `round_square`
