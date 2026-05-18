# Near-Contact Recenter Diagnostic

- Model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Recenter steps: `12`
- Max XY action: `0.0050 m`
- Z action: `0.0020 m`
- XY offsets mm: `[6.0, 10.0, 20.0, 30.0]`
- Z-above mm: `[8.0, 15.0, 30.0, 50.0]`
- Angles deg: `[0.0, 90.0, 180.0, 270.0]`

## By IK Mode

| mode | probes | setup ok | setup coll | coll | success | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm | ik err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 64 | 0.453 | 0.125 | 0.125 | 0.188 | 4.024 | 0.094 | 0.946 | 0.098 | -2.347 | 8.446 | 4.585 | 3.588 |

## By IK Mode And Dynamics

| mode | kp | damping | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 1.00 | 1.00 | 64 | 0.125 | 4.024 | 0.094 | 0.946 | 0.098 | -2.347 | 8.446 | 4.585 |

## By IK Mode And Z

| mode | z mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 8.0 | 16 | 0.000 | 3.418 | 0.105 | 0.988 | 0.108 | -1.410 | 8.446 |
| pose | 15.0 | 16 | 0.000 | 5.097 | 0.110 | 0.993 | 0.113 | -2.631 | 8.392 |
| pose | 30.0 | 16 | 0.188 | 4.101 | 0.083 | 0.838 | 0.090 | -2.686 | 6.474 |
| pose | 50.0 | 16 | 0.312 | 3.481 | 0.079 | 0.966 | 0.081 | -2.661 | 4.268 |

## By IK Mode And XY Offset

| mode | offset mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 6.0 | 16 | 0.000 | 3.056 | 0.091 | 0.988 | 0.094 | -2.762 | 4.490 |
| pose | 10.0 | 16 | 0.000 | 4.632 | 0.096 | 0.993 | 0.098 | -2.923 | 4.877 |
| pose | 20.0 | 16 | 0.062 | 5.218 | 0.102 | 0.995 | 0.105 | -2.522 | 6.474 |
| pose | 30.0 | 16 | 0.438 | 3.190 | 0.087 | 0.810 | 0.096 | -1.181 | 8.446 |
