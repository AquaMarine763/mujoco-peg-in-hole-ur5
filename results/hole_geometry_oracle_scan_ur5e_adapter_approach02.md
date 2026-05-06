# Hole Geometry Oracle Scan

- Generated: `2026-05-06T14:13:33`
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
| 0.045 | 0.090 | 0.012 | 0.024 | 0.033 | 1.000 | 0.000 | 0.000 | 14.9 | 0.00310 | 0.00745 |
| 0.029 | 0.058 | 0.012 | 0.024 | 0.017 | 1.000 | 0.000 | 0.000 | 16.9 | 0.00373 | 0.00776 |
| 0.025 | 0.050 | 0.012 | 0.024 | 0.013 | 1.000 | 0.000 | 0.000 | 15.5 | 0.00335 | 0.00777 |
| 0.020 | 0.040 | 0.012 | 0.024 | 0.008 | 1.000 | 0.000 | 0.000 | 14.9 | 0.00370 | 0.00788 |
| 0.017 | 0.034 | 0.012 | 0.024 | 0.005 | 0.800 | 0.040 | 0.160 | 49.3 | 0.00472 | 0.01653 |
| 0.015 | 0.030 | 0.012 | 0.024 | 0.003 | 0.680 | 0.180 | 0.140 | 65.3 | 0.00698 | 0.02642 |
