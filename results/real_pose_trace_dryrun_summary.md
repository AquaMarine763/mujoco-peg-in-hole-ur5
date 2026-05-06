# Real Pose Trace Dry-Run Summary

Generated: 2026-05-07

## Goal

Add the first concrete real-pose input path for deployment dry runs. Before
connecting UR5/UR5e RTDE or a live vision estimator, the real backend can now
read per-step peg/TCP and hole poses from CSV.

## Pose Trace Format

Example:

```text
configs\real_pose_trace_smoke.csv
```

Required columns:

```text
peg_tip_x, peg_tip_y, peg_tip_z, target_x, target_y, target_z
```

Accepted aliases:

```text
tcp_x/tcp_y/tcp_z or tool_x/tool_y/tool_z
hole_x/hole_y/hole_z
```

Optional columns:

```text
step, timestamp, pose_frame
```

All positions are expected in meters and in a common robot-base frame unless
`pose_frame` states otherwise.

## Smoke Command

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --pose-trace configs\real_pose_trace_smoke.csv `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_pose_trace_guarded_smoke.csv
```

## Result

```text
steps = 3
guard_steps = 3
final_dist_xy = 0.00000
final_dist_z = 0.06550
```

The trace now records:

```text
pose_source, pose_frame, pose_step, pose_timestamp
```

This means the deployment trace can distinguish static placeholder poses from
CSV-fed measured poses. The next step is to replace the CSV source with live
UR5/UR5e TCP pose and calibrated hole-pose estimates while keeping the same
trace schema.
