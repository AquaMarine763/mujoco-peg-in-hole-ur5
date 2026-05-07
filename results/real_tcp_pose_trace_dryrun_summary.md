# Real TCP Pose Trace Dry-Run Summary

Generated: 2026-05-07

## Goal

Add a UR5/UR5e-oriented pose input path before connecting live robot control.
The real dry-run backend can now consume TCP pose traces shaped like UR RTDE
`getActualTCPPose()` output and convert them into `peg_tip_pos` for the guarded
controller.

## Format

Example:

```text
configs\real_tcp_pose_trace_smoke.csv
```

Required columns:

```text
tcp_x, tcp_y, tcp_z, tcp_rx, tcp_ry, tcp_rz
```

Optional target columns:

```text
target_x, target_y, target_z
```

If target columns are absent, the dry-run config `target_pos` is used.
Alternatively, pass `--target-calibration` to load the target from a separate
fixture/hole calibration file; see
`results\real_target_calibration_dryrun_summary.md`.

## Conversion

The adapter computes:

```text
peg_tip_pos = tcp_pos + R(tcp_rx, tcp_ry, tcp_rz) * tcp_to_peg_tip_xyz
```

For the smoke trace:

```text
tcp_to_peg_tip_xyz = [0, 0, -0.11]
tcp_z = 0.8300
peg_tip_z = 0.7200
```

## Smoke Results

Command:

```powershell
python scripts\run_real_policy_dryrun.py `
  --zero-policy `
  --episodes 1 `
  --max-steps 3 `
  --tcp-pose-trace configs\real_tcp_pose_trace_smoke.csv `
  --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --guarded-policy `
  --guard-scenario-filter geometry `
  --guard-scenario-level full_light_geometry `
  --guard-start-z 0.10 `
  --guard-action-limit 0.002 `
  --output results\real_policy_dryrun_tcp_pose_guarded_smoke.csv
```

Result:

```text
steps = 3
guard_steps = 3
pose_source = tcp_csv
final_dist_xy = 0.00000
final_dist_z = 0.06550
```

The trace now logs both derived peg-tip pose and raw TCP pose:

```text
peg_tip_x/y/z
tcp_pos_x/y/z
tcp_rotvec_x/y/z
```

## RTDE Recorder

`scripts\record_ur_rtde_tcp_pose_trace.py` records read-only TCP poses from a
UR controller into the same CSV format. It uses `getActualTCPPose()` and does
not command robot motion.

Synthetic recorder smoke:

```powershell
python scripts\record_ur_rtde_tcp_pose_trace.py `
  --synthetic-smoke `
  --samples 4 `
  --frequency-hz 100 `
  --output results\ur_rtde_tcp_pose_trace_synthetic_smoke.csv
```

Synthetic output:

```text
results\ur_rtde_tcp_pose_trace_synthetic_smoke.csv
samples = 4
```
