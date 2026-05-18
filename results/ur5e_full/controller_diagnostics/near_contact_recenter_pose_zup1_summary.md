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
| pose | 64 | 0.453 | 0.125 | 0.125 | 0.219 | 3.917 | 0.093 | 0.940 | 0.098 | -2.992 | 8.389 | 4.230 | 3.622 |

## By IK Mode And Dynamics

| mode | kp | damping | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 1.00 | 1.00 | 64 | 0.125 | 3.917 | 0.093 | 0.940 | 0.098 | -2.992 | 8.389 | 4.230 |

## By IK Mode And Z

| mode | z mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 8.0 | 16 | 0.000 | 3.046 | 0.104 | 0.988 | 0.107 | -1.654 | 8.389 |
| pose | 15.0 | 16 | 0.000 | 5.107 | 0.110 | 0.993 | 0.113 | -3.624 | 8.375 |
| pose | 30.0 | 16 | 0.188 | 4.100 | 0.082 | 0.815 | 0.092 | -3.504 | 6.474 |
| pose | 50.0 | 16 | 0.312 | 3.415 | 0.076 | 0.962 | 0.079 | -3.188 | 4.262 |

## By IK Mode And XY Offset

| mode | offset mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 6.0 | 16 | 0.000 | 3.056 | 0.091 | 0.988 | 0.094 | -3.562 | 4.516 |
| pose | 10.0 | 16 | 0.000 | 4.593 | 0.096 | 0.993 | 0.097 | -3.748 | 4.942 |
| pose | 20.0 | 16 | 0.062 | 5.002 | 0.101 | 0.993 | 0.103 | -3.094 | 6.474 |
| pose | 30.0 | 16 | 0.438 | 3.016 | 0.085 | 0.785 | 0.096 | -1.566 | 8.389 |
