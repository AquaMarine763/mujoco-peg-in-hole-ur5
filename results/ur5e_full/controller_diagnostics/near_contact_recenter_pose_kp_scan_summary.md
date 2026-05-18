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
| pose | 192 | 0.432 | 0.125 | 0.120 | 0.125 | 5.101 | 0.148 | 0.966 | 0.173 | -1.190 | 8.360 | 3.244 | 3.611 |

## By IK Mode And Dynamics

| mode | kp | damping | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 1.00 | 1.00 | 64 | 0.125 | 3.860 | 0.092 | 0.937 | 0.096 | -3.645 | 8.360 | 4.054 |
| pose | 2.00 | 1.00 | 64 | 0.125 | 5.451 | 0.162 | 0.980 | 0.176 | -1.890 | 8.131 | 3.173 |
| pose | 4.00 | 1.00 | 64 | 0.109 | 5.993 | 0.191 | 0.981 | 0.246 | 1.965 | 7.479 | 2.506 |

## By IK Mode And Z

| mode | z mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 8.0 | 48 | 0.000 | 4.405 | 0.156 | 0.989 | 0.178 | 0.805 | 8.360 |
| pose | 15.0 | 48 | 0.000 | 5.844 | 0.157 | 0.991 | 0.182 | -0.849 | 8.308 |
| pose | 30.0 | 48 | 0.188 | 4.768 | 0.135 | 0.911 | 0.163 | -1.849 | 6.473 |
| pose | 50.0 | 48 | 0.292 | 5.389 | 0.146 | 0.973 | 0.168 | -2.867 | 4.275 |

## By IK Mode And XY Offset

| mode | offset mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 6.0 | 48 | 0.000 | 3.447 | 0.119 | 0.981 | 0.149 | -1.610 | 4.542 |
| pose | 10.0 | 48 | 0.000 | 5.690 | 0.148 | 0.992 | 0.170 | -1.692 | 4.973 |
| pose | 20.0 | 48 | 0.062 | 6.892 | 0.167 | 0.991 | 0.188 | -1.318 | 6.473 |
| pose | 30.0 | 48 | 0.417 | 4.377 | 0.159 | 0.898 | 0.184 | -0.140 | 8.360 |
