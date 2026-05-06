# Oracle Control Gain Scan

- Generated: `2026-05-06T18:39:49`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Domain randomization level: `full_light_geometry`
- Oracle mode: `guarded_two_stage`
- Episodes per gain: `50`
- Seed: `846000`
- Control scale range: `0.8:1.1`
- Control noise std range: `0.0:0.00025`
- Control delay range: `2:2`
- Control filter alpha range: `0.55:0.7`
- Guarded align XY tolerance: `0.025`
- Guarded insert XY tolerance: `0.005`
- Guarded preinsert height: `0.0`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `1.0`

| Gain | Success | Collision | Timeout | Mean steps | Mean final XY | Mean final Z |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.000 | 0.520 | 0.480 | 0.000 | 18.0 | 0.02034 | 0.02803 |
| 0.850 | 0.500 | 0.500 | 0.000 | 17.7 | 0.02118 | 0.02889 |
