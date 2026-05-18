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
| pose | 64 | 0.453 | 0.125 | 0.125 | 0.500 | 4.961 | 0.170 | 0.971 | 0.183 | -6.210 | 8.015 | 3.395 | 3.683 |

## By IK Mode And Dynamics

| mode | kp | damping | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 1.00 | 1.00 | 64 | 0.125 | 4.961 | 0.170 | 0.971 | 0.183 | -6.210 | 8.015 | 3.395 |

## By IK Mode And Z

| mode | z mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 8.0 | 16 | 0.000 | 3.118 | 0.193 | 0.990 | 0.197 | -2.133 | 8.015 |
| pose | 15.0 | 16 | 0.000 | 6.061 | 0.193 | 0.993 | 0.212 | -7.104 | 7.947 |
| pose | 30.0 | 16 | 0.188 | 5.398 | 0.151 | 0.923 | 0.172 | -8.156 | 6.263 |
| pose | 50.0 | 16 | 0.312 | 5.266 | 0.144 | 0.980 | 0.152 | -7.447 | 4.328 |

## By IK Mode And XY Offset

| mode | offset mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 6.0 | 16 | 0.000 | 3.633 | 0.167 | 0.989 | 0.183 | -7.358 | 4.606 |
| pose | 10.0 | 16 | 0.000 | 5.929 | 0.174 | 0.995 | 0.183 | -7.577 | 5.120 |
| pose | 20.0 | 16 | 0.062 | 6.844 | 0.185 | 0.995 | 0.194 | -6.751 | 6.263 |
| pose | 30.0 | 16 | 0.438 | 3.437 | 0.154 | 0.906 | 0.173 | -3.154 | 8.015 |
