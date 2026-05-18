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
| pose | 64 | 0.438 | 0.125 | 0.094 | 0.047 | 6.178 | 0.167 | 0.987 | 0.181 | 1.174 | 8.111 | 3.617 | 3.532 |

## By IK Mode And Dynamics

| mode | kp | damping | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 2.00 | 1.00 | 64 | 0.094 | 6.178 | 0.167 | 0.987 | 0.181 | 1.174 | 8.111 | 3.617 |

## By IK Mode And Z

| mode | z mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 8.0 | 16 | 0.000 | 5.794 | 0.173 | 0.995 | 0.182 | 2.433 | 8.111 |
| pose | 15.0 | 16 | 0.000 | 6.526 | 0.177 | 0.994 | 0.191 | 2.203 | 7.778 |
| pose | 30.0 | 16 | 0.188 | 5.379 | 0.151 | 0.970 | 0.168 | 0.806 | 6.205 |
| pose | 50.0 | 16 | 0.188 | 7.013 | 0.166 | 0.988 | 0.182 | -0.747 | 4.242 |

## By IK Mode And XY Offset

| mode | offset mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 6.0 | 16 | 0.000 | 3.724 | 0.142 | 0.988 | 0.163 | 0.754 | 4.328 |
| pose | 10.0 | 16 | 0.000 | 6.817 | 0.165 | 0.995 | 0.176 | 1.265 | 4.493 |
| pose | 20.0 | 16 | 0.000 | 8.561 | 0.188 | 0.995 | 0.197 | 1.227 | 6.205 |
| pose | 30.0 | 16 | 0.375 | 5.610 | 0.173 | 0.970 | 0.187 | 1.449 | 8.111 |
