# Policy vs Oracle Correction Analysis

- Generated: `2026-05-06T22:52:40`
- Model: `mujoco_peg_in_hole\checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- MuJoCo model path: `mujoco_peg_in_hole\assets\ur5e_adapter\ur5e_peg_in_hole.xml`
- Episodes per tier/scenario: `50`
- Scenario preset: `targeted`
- Tier preset: `wide_medium`
- Failure window steps: `8`
- Near-hole window: `xy<=0.03`, `z_above_target<=0.1`

## Summary

| Tier | Scenario | Episodes | Success | Collision | Mean steps | Mean clearance | Mean corr | Near corr | Failure corr | Failure opposed | Failure policy down / oracle up |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | 50 | 0.640 | 0.360 | 26.820 | 14.890 mm | 0.005 | 0.005 | 0.005 | 0.035 | 0.065 |
| wide_current | hard_full_light_bucket | 50 | 0.320 | 0.680 | 19.560 | 15.280 mm | 0.004 | 0.005 | 0.004 | 0.007 | 0.070 |
| medium | full_light_geometry | 50 | 0.660 | 0.300 | 29.640 | 9.890 mm | 0.005 | 0.006 | 0.005 | 0.189 | 0.125 |
| medium | hard_full_light_bucket | 50 | 0.400 | 0.560 | 23.020 | 10.280 mm | 0.004 | 0.005 | 0.004 | 0.076 | 0.059 |

## Largest Failure-Window Corrections

| Tier | Scenario | Episode | Step | Outcome | Dist XY | Z above target | Policy z | Oracle z | Correction norm | Cosine |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| wide_current | full_light_geometry | 20 | 141 | collision | 0.020 | 0.071 | -0.005 | 0.005 | 0.015 | -0.747 |
| wide_current | full_light_geometry | 3 | 174 | collision | 0.024 | 0.071 | -0.005 | 0.005 | 0.014 | -0.626 |
| wide_current | full_light_geometry | 3 | 173 | collision | 0.022 | 0.072 | -0.005 | 0.005 | 0.014 | -0.565 |
| medium | full_light_geometry | 35 | 8 | collision | 0.068 | 0.043 | -0.005 | 0.005 | 0.013 | -0.659 |
| medium | full_light_geometry | 35 | 10 | collision | 0.082 | 0.017 | -0.003 | 0.005 | 0.013 | -0.583 |
| medium | full_light_geometry | 35 | 6 | collision | 0.060 | 0.060 | -0.004 | 0.005 | 0.013 | -0.729 |
| medium | full_light_geometry | 35 | 9 | collision | 0.075 | 0.031 | -0.003 | 0.005 | 0.013 | -0.558 |
| wide_current | hard_full_light_bucket | 34 | 141 | collision | 0.016 | 0.052 | -0.005 | 0.003 | 0.012 | -0.430 |
| medium | full_light_geometry | 35 | 7 | collision | 0.063 | 0.053 | -0.005 | 0.005 | 0.012 | -0.844 |
| medium | hard_full_light_bucket | 20 | 197 | timeout | 0.010 | 0.009 | 0.000 | 0.005 | 0.011 | -0.636 |
| wide_current | full_light_geometry | 20 | 140 | collision | 0.018 | 0.072 | -0.005 | -0.004 | 0.011 | -0.038 |
| medium | hard_full_light_bucket | 7 | 196 | timeout | 0.015 | 0.023 | 0.003 | 0.005 | 0.011 | -0.261 |

## Interpretation

The step CSV is the primary artifact for corrective-data collection. Rows with `failure_window=True`, high `correction_norm`, and `near_hole=True` are the first candidates for DAgger-style relabeling because they show states that the learned policy actually visits shortly before collision or timeout.

If `failure_policy_down_or_oracle_up_rate` is high, the policy is descending while the guarded oracle would retract or slow insertion. If `failure_opposed_action_rate` is high, the XY/Z action direction is often opposite to the corrective action, which indicates that success-only BC is missing recovery examples rather than only needing more samples.
