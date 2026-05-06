# Oracle Control Gain Scan

- Generated: `2026-05-06T18:38:55`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Domain randomization level: `full_light_geometry`
- Oracle mode: `staged`
- Episodes per gain: `100`
- Seed: `847000`
- Control scale range: `0.8:1.1`
- Control noise std range: `0.0:0.00025`
- Control delay range: `2:2`
- Control filter alpha range: `0.55:0.7`

| Gain | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.000 | 0.150 | 0.850 | 0.000 | 11.2 | 0.02690 | 0.04028 |
| 0.700 | 0.210 | 0.790 | 0.000 | 11.4 | 0.02681 | 0.03802 |
| 0.500 | 0.280 | 0.720 | 0.000 | 13.4 | 0.02598 | 0.03575 |
