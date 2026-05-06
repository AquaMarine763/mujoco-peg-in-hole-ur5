# Oracle Control Gain Scan

- Generated: `2026-05-06T17:47:14`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Domain randomization level: `full_light_geometry`
- Episodes per gain: `50`
- Seed: `842000`
- Control scale range: `0.8:1.1`
- Control noise std range: `0.0:0.00025`
- Control delay range: `2:2`
- Control filter alpha range: `0.55:0.7`

| Gain | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.000 | 0.220 | 0.780 | 0.000 | 15.9 | 0.02590 | 0.03633 |
| 0.700 | 0.180 | 0.820 | 0.000 | 10.8 | 0.02750 | 0.03777 |
| 0.500 | 0.260 | 0.740 | 0.000 | 12.1 | 0.02671 | 0.03653 |
| 0.350 | 0.180 | 0.780 | 0.040 | 27.4 | 0.02825 | 0.03969 |
| 0.250 | 0.000 | 0.700 | 0.300 | 68.4 | 0.02881 | 0.04804 |
| 0.180 | 0.000 | 0.660 | 0.340 | 72.0 | 0.02988 | 0.04074 |
