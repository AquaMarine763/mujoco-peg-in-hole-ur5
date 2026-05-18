# Guarded Policy Evaluation

- Generated: `2026-05-18T18:55:18`
- Model: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_insert_drift_2k_w10_e1.zip`
- MuJoCo model path: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Observation mode: `image`
- Control mode: `guarded`
- Image ablation: `normal`
- Episodes per scenario: `100`
- Seed: `602000`
- Frame skip: `10`
- Step trace CSV: `results\ur5e_full\high_start\hard\correction\eval_insert_drift_pose_ik_wori003_it64_kp2_matrix_failure_step_trace_100ep_seed602000.csv`
- Step trace outcome filter: `failure`
- Near-hole crop offset: `(-18, 0)`
- Include control state: `True`
- Image frame stack: `1`
- Wrist camera pos offset: `(-0.04, -0.04, 0.0)`
- Wrist camera rot offset deg: `(0.0, 0.0, 0.0)`
- Wrist camera FOV override: `100.0`
- IK control mode: `pose`
- IK orientation/posture weight: `0.03/0.01`
- IK step limit/max iterations: `0.06/64`
- Nominal joint damping / actuator Kp multiplier: `1.0/2.0`
- Guard start XY: `0.06`
- Guard start Z above target: `0.12`
- Guard risk XY: `0.0`
- Guard scenario filter: `all`
- Guard blend: `1.0`
- Guard min policy steps: `0`
- Guard block down when unaligned: `False`
- Guard retry enabled: `False`
- Guard retry stall steps: `80`
- Guard retry XY/Z band: `0.015/0.06`
- Guard retry lift/release/max attempts/max steps: `0.08/0.005/2/120`
- Guard insert latch enabled: `False`
- Guard insert latch XY/release XY: `0.005/0.009`
- Guard insert latch resume/recenter/max down: `0.005/0.0/0.0`
- Guard hover enabled: `False`
- Guard hover XY/release/height/Z tol/steps/max down: `0.004/0.006/0.05/0.01/6/0.002`
- Guard near action scale enabled: `False`
- Guard near XY/Z/max XY/max down: `0.02/0.07/0.002/0.0015`
- Guard fixture clearance enabled: `False`
- Guard fixture clearance XY/Z/lift/max up: `0.02-0.09/0.06/0.1/0.005`
- Guard fixture clearance realign enabled: `False`
- Guard fixture clearance realign start Z/XY/max XY/max down/max steps: `0.0/0.02/0.005/0.0/240`
- Guard preinsert recenter enabled: `False`
- Guard preinsert recenter start/min Z, trigger/stable XY: `0.025/0.0/0.004/0.0035`
- Guard preinsert recenter height/Z tol/stable/max steps/max XY/max up: `0.025/0.006/3/80/0.005/0.005`
- Guard final servo enabled: `True`
- Guard final servo start XY/Z/min Z: `0.005/0.035/0.01`
- Guard final servo hover/stable/release: `0.008/0.0065/0.012`
- Guard final servo stable/stall/retries: `1/80/0`
- Guard final servo max XY/down/descend bias/lift/recovery steps: `0.005/0.0035/(0.0, 0.0)/0.06/160`
- Guard final servo recovery mode/soft lift/min height/z tol/hold/max up: `lift_recenter/0.006/0.012/0.001/4/0.002`
- Guarded oracle mode: `guarded_two_stage`
- Guarded align/insert XY: `0.02/0.005`
- Guarded max XY/down/up action: `0.005/0.0035/0.005`
- Guarded prediction steps: `0.0`
- Guarded hold Z until insert: `False`
- Guarded lift before lateral: `False`
- Guarded lift-before-lateral XY/Z margin: `0.02/0.01`
- Contact recovery XY/Z/lift/Z tol/max down: `0.005/0.05/0.06/0.01/0.001`
- Timeout progress XY/Z/max down: `0.01/0.06/0.0015`

| Scenario | Level | Mode | Image | Guard | Success | Collision | Timeout | Mean return | Mean steps | Guard steps | Retry steps | Latch steps | Hover steps | Near limited | Fixture steps | Fixture realign | Preinsert | Final servo | Final servo descend | Final XY | Final Z |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | none | guarded | normal | True | 0.970 | 0.000 | 0.030 | 313.099 | 300.8 | 135.3 (0.45) | 0.0 (0.00) | 0.0 (0.00, down 0.00) | 0.0 (0.00, latched 0.00, block 0.00) | 0.0 (0.00) | 0.0 (0.00) | 0.0 (0.00) | 0.0 (0.00, trig 0.00, rel 0.00) | 25.4 (0.08, trig 0.95, rec 0.00) | 10.4 (0.41) | 0.00306 | 0.01151 |
| visual_camera | visual_camera | guarded | normal | True | 0.970 | 0.000 | 0.030 | 316.732 | 313.4 | 142.8 (0.46) | 0.0 (0.00) | 0.0 (0.00, down 0.00) | 0.0 (0.00, latched 0.00, block 0.00) | 0.0 (0.00) | 0.0 (0.00) | 0.0 (0.00) | 0.0 (0.00, trig 0.00, rel 0.00) | 25.4 (0.08, trig 0.95, rec 0.00) | 10.4 (0.41) | 0.00306 | 0.01145 |
| visual_camera_control | visual_camera_control | guarded | normal | True | 0.940 | 0.000 | 0.060 | 311.063 | 322.7 | 153.0 (0.47) | 0.0 (0.00) | 0.0 (0.00, down 0.00) | 0.0 (0.00, latched 0.00, block 0.00) | 0.0 (0.00) | 0.0 (0.00) | 0.0 (0.00) | 0.0 (0.00, trig 0.00, rel 0.00) | 25.2 (0.08, trig 0.94, rec 0.00) | 10.5 (0.42) | 0.00326 | 0.01215 |
| full_light_geometry | full_light_geometry | guarded | normal | True | 0.910 | 0.000 | 0.090 | 319.177 | 340.9 | 172.2 (0.51) | 0.0 (0.00) | 0.0 (0.00, down 0.00) | 0.0 (0.00, latched 0.00, block 0.00) | 0.0 (0.00) | 0.0 (0.00) | 0.0 (0.00) | 0.0 (0.00, trig 0.00, rel 0.00) | 28.8 (0.08, trig 0.94, rec 0.00) | 14.1 (0.49) | 0.00337 | 0.01211 |
| full_contact_light | full_contact_light | guarded | normal | True | 0.910 | 0.000 | 0.090 | 320.167 | 343.4 | 173.8 (0.51) | 0.0 (0.00) | 0.0 (0.00, down 0.00) | 0.0 (0.00, latched 0.00, block 0.00) | 0.0 (0.00) | 0.0 (0.00) | 0.0 (0.00) | 0.0 (0.00, trig 0.00, rel 0.00) | 29.2 (0.09, trig 0.94, rec 0.00) | 14.5 (0.50) | 0.00334 | 0.01194 |
