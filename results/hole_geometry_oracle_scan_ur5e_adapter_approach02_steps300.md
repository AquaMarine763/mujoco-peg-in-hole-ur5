# Hole Geometry Oracle Scan

- Generated: `2026-05-06T14:14:15`
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
| 0.020 | 0.040 | 0.012 | 0.024 | 0.008 | 0.940 | 0.060 | 0.000 | 23.3 | 0.00463 | 0.01207 |
| 0.017 | 0.034 | 0.012 | 0.024 | 0.005 | 0.840 | 0.120 | 0.040 | 52.4 | 0.00644 | 0.01910 |
| 0.015 | 0.030 | 0.012 | 0.024 | 0.003 | 0.580 | 0.360 | 0.060 | 98.8 | 0.00987 | 0.03842 |
| 0.014 | 0.028 | 0.012 | 0.024 | 0.002 | 0.500 | 0.500 | 0.000 | 98.4 | 0.01140 | 0.04534 |
