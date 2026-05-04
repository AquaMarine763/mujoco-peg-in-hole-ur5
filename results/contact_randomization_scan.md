# Contact And Dynamics Randomization Scan

Model:
`checkpoints_image_bc_50k_sidecam_visual_camera_control_delay3_oracle/sac_image_bc.zip`

The scan keeps visual, camera, control, and light geometry randomization active,
then isolates light contact/dynamics factors.

Default `full_contact_light` ranges:

- contact friction multiplier: `0.7-1.3`
- contact solref time multiplier: `0.8-1.25`
- contact solref damping multiplier: `0.8-1.2`
- contact solimp width multiplier: `0.8-1.2`
- arm joint damping multiplier: `0.8-1.2`
- actuator kp multiplier: `0.8-1.2`

50-episode scan with seed `80000`:

| Setting | Success | Collision | Timeout |
| --- | ---: | ---: | ---: |
| full_light_geometry_reference | 0.90 | 0.08 | 0.02 |
| friction_only | 0.90 | 0.06 | 0.04 |
| solref_time_only | 0.90 | 0.06 | 0.04 |
| solref_damping_only | 0.90 | 0.06 | 0.04 |
| solimp_width_only | 0.90 | 0.06 | 0.04 |
| joint_damping_only | 0.90 | 0.06 | 0.04 |
| actuator_kp_only | 0.90 | 0.06 | 0.04 |
| default_contact_light | 0.90 | 0.08 | 0.02 |
| high_contact_light | 0.88 | 0.08 | 0.04 |

100-episode confirmation runs with seed `1000`:

| Setting | Success | Collision | Mean return |
| --- | ---: | ---: | ---: |
| default_contact_light | 0.97 | 0.01 | 56.654 |
| high_contact_light | 0.97 | 0.01 | 56.808 |

Conclusion:

- The current light contact/dynamics ranges do not create a new dominant
  bottleneck for the delay-robust image policy.
- The 50-episode factor scan varies by seed, but isolated contact/dynamics
  factors are very close to the reference.
- Since the 100-episode default and high-contact confirmations both remain at
  `0.97` success with `0.01` collision, this stage does not need a new BC
  dataset.
- The next meaningful challenge is a calibrated real-robot interface and/or a
  stronger contact profile tied to measured hardware behavior.
