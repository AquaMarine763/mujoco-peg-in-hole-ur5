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
| pose | 64 | 0.406 | 0.125 | 0.031 | 0.000 | 7.188 | 0.191 | 0.977 | 0.250 | 8.251 | 7.475 | 2.829 | 3.438 |

## By IK Mode And Dynamics

| mode | kp | damping | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt | track err mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 4.00 | 1.00 | 64 | 0.031 | 7.188 | 0.191 | 0.977 | 0.250 | 8.251 | 7.475 | 2.829 |

## By IK Mode And Z

| mode | z mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 8.0 | 16 | 0.000 | 5.707 | 0.181 | 0.984 | 0.241 | 11.502 | 7.475 |
| pose | 15.0 | 16 | 0.000 | 5.759 | 0.178 | 0.983 | 0.239 | 10.303 | 7.224 |
| pose | 30.0 | 16 | 0.125 | 5.865 | 0.177 | 0.960 | 0.242 | 6.737 | 4.918 |
| pose | 50.0 | 16 | 0.000 | 11.422 | 0.228 | 0.981 | 0.279 | 4.462 | 4.017 |

## By IK Mode And XY Offset

| mode | offset mm | probes | coll | xy reduction mm | reduction/cmd | alignment | step gain | z drift mm | max tilt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pose | 6.0 | 16 | 0.000 | 3.622 | 0.115 | 0.964 | 0.186 | 8.590 | 4.190 |
| pose | 10.0 | 16 | 0.000 | 6.291 | 0.178 | 0.986 | 0.234 | 8.561 | 4.345 |
| pose | 20.0 | 16 | 0.000 | 8.672 | 0.220 | 0.988 | 0.275 | 8.397 | 5.776 |
| pose | 30.0 | 16 | 0.125 | 10.168 | 0.252 | 0.969 | 0.307 | 7.456 | 7.475 |
