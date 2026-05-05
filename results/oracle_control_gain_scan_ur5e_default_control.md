# Oracle Control Gain Scan

- Generated: `2026-05-06T00:18:09`
- MuJoCo model path: `assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Domain randomization level: `visual_camera_control`
- Episodes per gain: `100`
- Seed: `120000`
- Control scale range: `0.8:1.2`
- Control noise std range: `0.0:0.0008`
- Control delay range: `0:2`
- Control filter alpha range: `0.55:1.0`

| Gain | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.000 | 0.910 | 0.090 | 0.000 | 26.3 | 0.00717 | 0.01029 |
| 0.700 | 0.890 | 0.110 | 0.000 | 33.5 | 0.00822 | 0.01415 |
| 0.500 | 0.840 | 0.160 | 0.000 | 37.2 | 0.01064 | 0.01692 |
| 0.350 | 0.660 | 0.340 | 0.000 | 58.2 | 0.01716 | 0.02844 |
| 0.250 | 0.230 | 0.770 | 0.000 | 99.8 | 0.03191 | 0.05647 |
| 0.180 | 0.030 | 0.970 | 0.000 | 121.2 | 0.03866 | 0.06966 |
