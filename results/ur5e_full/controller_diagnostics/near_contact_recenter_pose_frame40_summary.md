# Near-Contact Recenter Diagnostic

- Model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Recenter steps: `12`
- Max XY action: `0.0050 m`
- Z action: `0.0000 m`
- XY offsets mm: `[6.0, 10.0, 20.0, 30.0]`
- Z-above mm: `[8.0, 15.0, 30.0, 50.0]`
- Angles deg: `[0.0, 90.0, 180.0, 270.0]`

## By IK Mode

| mode | probes | setup ok | setup coll | coll | success | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm | ik err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 64 | 0.453 | 0.125 | 0.125 | 0.500 | 5.352 | 0.281 | 0.982 | 0.313 | -9.503 | 7.390 | 3.036 | 3.715 |

## By IK Mode And Dynamics

| mode | kp | damping | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 1.00 | 1.00 | 64 | 0.125 | 5.352 | 0.281 | 0.982 | 0.313 | -9.503 | 7.390 | 3.036 |

## By IK Mode And Z

| mode | z mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 8.0 | 16 | 0.000 | 3.312 | 0.342 | 0.990 | 0.350 | -2.258 | 7.390 |
| pose | 15.0 | 16 | 0.000 | 6.147 | 0.335 | 0.993 | 0.377 | -7.478 | 7.329 |
| pose | 30.0 | 16 | 0.188 | 5.459 | 0.215 | 0.960 | 0.267 | -14.420 | 5.907 |
| pose | 50.0 | 16 | 0.312 | 6.491 | 0.231 | 0.985 | 0.259 | -13.855 | 4.478 |

## By IK Mode And XY Offset

| mode | offset mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 6.0 | 16 | 0.000 | 3.696 | 0.257 | 0.989 | 0.302 | -11.809 | 4.648 |
| pose | 10.0 | 16 | 0.000 | 6.067 | 0.284 | 0.994 | 0.316 | -11.897 | 5.127 |
| pose | 20.0 | 16 | 0.062 | 7.919 | 0.312 | 0.995 | 0.339 | -10.540 | 5.909 |
| pose | 30.0 | 16 | 0.438 | 3.728 | 0.270 | 0.949 | 0.297 | -3.764 | 7.390 |
