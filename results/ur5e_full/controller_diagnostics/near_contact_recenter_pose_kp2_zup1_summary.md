# Near-Contact Recenter Diagnostic

- Model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Recenter steps: `12`
- Max XY action: `0.0050 m`
- Z action: `0.0010 m`
- XY offsets mm: `[6.0, 10.0, 20.0, 30.0]`
- Z-above mm: `[8.0, 15.0, 30.0, 50.0]`
- Angles deg: `[0.0, 90.0, 180.0, 270.0]`

## By IK Mode

| mode | probes | setup ok | setup coll | coll | success | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm | ik err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 64 | 0.438 | 0.125 | 0.125 | 0.094 | 5.672 | 0.163 | 0.980 | 0.176 | -0.409 | 8.108 | 3.295 | 3.578 |

## By IK Mode And Dynamics

| mode | kp | damping | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 2.00 | 1.00 | 64 | 0.125 | 5.672 | 0.163 | 0.980 | 0.176 | -0.409 | 8.108 | 3.295 |

## By IK Mode And Z

| mode | z mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 8.0 | 16 | 0.000 | 5.185 | 0.176 | 0.994 | 0.185 | 0.708 | 8.108 |
| pose | 15.0 | 16 | 0.000 | 6.545 | 0.177 | 0.995 | 0.190 | 0.346 | 7.700 |
| pose | 30.0 | 16 | 0.188 | 5.392 | 0.150 | 0.950 | 0.167 | -0.739 | 6.206 |
| pose | 50.0 | 16 | 0.312 | 5.567 | 0.147 | 0.983 | 0.162 | -1.951 | 4.263 |

## By IK Mode And XY Offset

| mode | offset mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 6.0 | 16 | 0.000 | 3.540 | 0.144 | 0.988 | 0.164 | -0.894 | 4.328 |
| pose | 10.0 | 16 | 0.000 | 6.625 | 0.166 | 0.995 | 0.175 | -0.691 | 4.494 |
| pose | 20.0 | 16 | 0.062 | 8.009 | 0.181 | 0.995 | 0.190 | -0.461 | 6.206 |
| pose | 30.0 | 16 | 0.438 | 4.515 | 0.160 | 0.943 | 0.175 | 0.411 | 8.108 |
