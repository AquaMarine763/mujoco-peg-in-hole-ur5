# Hole Geometry Oracle Scan

- Generated: `2026-05-06T14:13:54`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Observation mode: `state`
- Episodes per size: `50`
- Seed: `510000`
- Success tolerances: `xy=0.005`, `z=0.01`
- Hole center jitter: `0.0:0.0`
- Fixture height jitter: `0.0`
- Table height jitter: `0.0`

| Hole half-size | Hole side | Peg radius | Peg diameter | Clearance | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.020 | 0.040 | 0.012 | 0.024 | 0.008 | 0.940 | 0.060 | 0.000 | 25.7 | 0.00486 | 0.01270 |
| 0.017 | 0.034 | 0.012 | 0.024 | 0.005 | 0.840 | 0.100 | 0.060 | 56.0 | 0.00643 | 0.01921 |
| 0.015 | 0.030 | 0.012 | 0.024 | 0.003 | 0.620 | 0.280 | 0.100 | 102.0 | 0.00875 | 0.03504 |
| 0.014 | 0.028 | 0.012 | 0.024 | 0.002 | 0.480 | 0.340 | 0.180 | 133.8 | 0.00986 | 0.04294 |
