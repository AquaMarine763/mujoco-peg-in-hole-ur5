# Real Dry-run Trace Checker Summary

This step adds `scripts/check_real_dryrun_trace.py`, an offline checker for
real-policy dry-run CSV traces. It is intended to run after a dry-run and before
using the trace to make deployment decisions.

## What It Checks

| Area | Checks |
| --- | --- |
| Schema | Required dry-run columns such as `peg_tip_*`, `target_*`, action vectors, and limit flags are present. |
| Frames and sources | `pose_frame` can be checked against an expected frame, `pose_frame` and `target_frame` are compared, and static pose/target sources can be rejected. |
| Action safety | Reports max component and norm for policy, raw, final, limited, filtered, safe, commanded, and applied actions. Flags `safe_action_*` above the configured per-axis limit. |
| Limit events | Flags `workspace_limited=True` as an error by default and `action_limited=True` as a warning by default. |
| Guard behavior | Reports first guard activation, activation height, unaligned guard rows, downward motion before guard activation, and downward motion while unaligned. |
| Pose consistency | Verifies `dist_xy` and `dist_z` against `peg_tip_pos` and `target_pos`, and checks monotonic `step`, `pose_step`, and `pose_timestamp` within each episode. |
| TCP conversion | With `--tcp-to-peg-tip-xyz`, verifies `peg_tip_pos = tcp_pos + R(tcp_rotvec) * tcp_to_peg_tip_xyz`. |

## Smoke Results

| Trace | Verdict | Rows | Issues |
| --- | --- | ---: | ---: |
| `results\real_policy_dryrun_target_calibration_guarded_smoke.csv` | PASS | 4 | 0 |
| `results\real_policy_dryrun_tcp_pose_guarded_smoke.csv` | PASS | 4 | 0 |
| `results\real_policy_dryrun_pose_trace_guarded_smoke.csv` | PASS | 4 | 0 |

Generated reports:

| Report | Purpose |
| --- | --- |
| `results\real_dryrun_trace_check_target_calibration_smoke.md` | Preferred target-calibration dry-run check. |
| `results\real_dryrun_trace_check_tcp_pose_smoke.md` | Legacy TCP pose trace check with target embedded in the TCP CSV. |
| `results\real_dryrun_trace_check_pose_trace_smoke.md` | Direct peg-tip and target pose trace check. |

## Recommended Real Dry-run Gate

For the current preferred path, run:

```powershell
python scripts\check_real_dryrun_trace.py `
  --trace results\real_policy_dryrun_target_calibration_guarded_smoke.csv `
  --output-md results\real_dryrun_trace_check_target_calibration_smoke.md `
  --max-safe-action 0.002 `
  --expected-pose-frame robot_base `
  --require-nonstatic-target `
  --tcp-to-peg-tip-xyz 0 0 -0.11
```

Interpretation:

| Verdict | Meaning |
| --- | --- |
| PASS | The trace is internally consistent under the configured checks. This is necessary but not sufficient for hardware motion. |
| WARN | The trace is usable for debugging, but at least one deployment-relevant assumption needs manual review. |
| FAIL | Do not use the trace as a deployment gate until the reported errors are fixed. |
