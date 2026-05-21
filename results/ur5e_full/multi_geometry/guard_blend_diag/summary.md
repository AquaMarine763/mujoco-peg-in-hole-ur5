# Multi-Geometry Guard-Blend Diagnostic

Generated: 2026-05-21

Task: `square_square`, strict high-start guarded config, 20 episodes, seed `612000`.

## Guard Blend Sweep

| Model | Guard blend | Success | Collision | Timeout | Mean final XY | Mean final Z |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| base insert-drift w10 | 1.00 | 0.850 | 0.000 | 0.150 | 2.71 mm | 11.60 mm |
| base insert-drift w10 | 0.75 | 0.850 | 0.000 | 0.150 | 3.26 mm | 14.51 mm |
| base insert-drift w10 | 0.50 | 0.700 | 0.000 | 0.300 | 4.56 mm | 18.88 mm |
| square-square w05 | 1.00 | 0.850 | 0.000 | 0.150 | 2.69 mm | 11.21 mm |
| square-square w05 | 0.75 | 0.850 | 0.000 | 0.150 | 3.32 mm | 13.97 mm |
| square-square w05 | 0.50 | 0.650 | 0.000 | 0.350 | 4.52 mm | 19.50 mm |

## Actor Versus Guard

| Model | Control mode | Success | Collision | Timeout | Mean final XY | Mean final Z |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| base insert-drift w10 | policy | 0.000 | 0.000 | 1.000 | 19.56 mm | 76.34 mm |
| base insert-drift w10 | guard_only | 0.850 | 0.000 | 0.150 | 3.76 mm | 13.46 mm |
| square-square w05 | policy | 0.000 | 0.100 | 0.900 | 19.45 mm | 69.06 mm |
| square-square w05 | guard_only | 0.850 | 0.000 | 0.150 | 3.76 mm | 13.46 mm |

## Conclusion

The square-square w05 replay does not add a useful near-hole actor contribution under the current deployment stack. Lowering `guard_blend` from `1.0` to `0.75` is flat, and lowering to `0.5` regresses both models. `policy` mode has zero success, while `guard_only` matches the guarded success rate.

The next multi-geometry step should be controller-side: add a shape-aware final insertion / low-recenter strategy for `square_square`, rather than scaling one-step BC replay.
