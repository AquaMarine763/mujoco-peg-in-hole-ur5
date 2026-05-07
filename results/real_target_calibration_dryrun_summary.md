# Real Target Calibration Dry-Run Summary

Generated: 2026-05-07

## Goal

Separate hole/target pose from TCP pose traces. The real dry-run path can now
combine:

- UR-style TCP pose trace for the robot pose
- fixed hole/fixture calibration file for the target pose

This is closer to the intended deployment path, where the robot TCP comes from
UR RTDE and the hole pose comes from fixture registration, hand-eye vision, or a
calibrated workcell frame.

## Target Calibration Format

Example:

```text
configs\real_hole_target_calibration_smoke.yaml
```

Required:

```text
target_pos: [0.55, 0.05, 0.65]
```

Optional:

```text
target_id: smoke_hole
target_source: fixture_calibration
pose_frame: robot_base
target_timestamp: 0.0
```

CSV calibration files are also accepted with `target_x`, `target_y`, and
`target_z` columns.

## Smoke Command

This TCP trace intentionally has no target columns:

```text
configs\real_tcp_pose_trace_no_target_smoke.csv
```

Command:

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-pose-trace configs\real_tcp_pose_trace_no_target_smoke.csv `
  --target-calibration configs\real_hole_target_calibration_smoke.yaml `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_target_calibration_guarded_smoke.csv
```

## Result

```text
steps = 3
guard_steps = 3
pose_source = tcp_csv
target_source = fixture_calibration
target_frame = robot_base
final_dist_xy = 0.00000
final_dist_z = 0.06550
```

The deployment trace now records:

```text
target_source, target_frame, target_timestamp
```

This gives a clean transition path to a live target provider later: the provider
only needs to update `target_pos` and `target_source`, while the guarded
controller and safety filter remain unchanged.
