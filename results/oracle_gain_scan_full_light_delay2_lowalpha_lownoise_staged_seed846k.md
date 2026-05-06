# Oracle Control Gain Scan

- Generated: `2026-05-06T18:39:26`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Domain randomization level: `full_light_geometry`
- Oracle mode: `staged`
- Episodes per gain: `50`
- Seed: `846000`
- Control scale range: `0.8:1.1`
- Control noise std range: `0.0:0.00025`
- Control delay range: `2:2`
- Control filter alpha range: `0.55:0.7`

| Gain | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.000 | 0.200 | 0.800 | 0.000 | 12.0 | 0.02555 | 0.03774 |
| 0.700 | 0.240 | 0.760 | 0.000 | 11.6 | 0.02603 | 0.03714 |
| 0.500 | 0.300 | 0.700 | 0.000 | 11.6 | 0.02550 | 0.03557 |
| 0.350 | 0.240 | 0.700 | 0.060 | 32.7 | 0.02673 | 0.04099 |
| 0.250 | 0.000 | 0.620 | 0.380 | 87.2 | 0.02793 | 0.04497 |
