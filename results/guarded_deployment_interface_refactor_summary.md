# Guarded Deployment Interface Refactor Summary

Generated: 2026-05-07

## Goal

Move guarded final insertion from a MuJoCo-only wrapper toward a deployment
controller that can be reused by both simulation and real-robot dry runs.

## Implementation

The guarded controller now has a backend-neutral state layer:

- `GuardedDeploymentState`: peg/TCP pose, hole/target pose, previous applied
  action, approach height, action bounds, and optional XY distance.
- `MujocoGuardStateProvider`: converts MuJoCo `info` plus environment action
  bounds into `GuardedDeploymentState`.
- `RealGuardStateProvider`: converts real-robot dry-run telemetry shaped like
  the trace `info` into `GuardedDeploymentState`.
- `guarded_two_stage_oracle_action_from_state`: computes the final-insertion
  action from explicit state arrays instead of requiring a MuJoCo env object.

Existing MuJoCo scripts still keep their old behavior, but `run_policy_inference.py`,
`demo_policy.py`, `eval_guarded_policy.py`, and `scan_guarded_policy_params.py`
now explicitly use `MujocoGuardStateProvider`.

`run_real_policy_dryrun.py` now supports `--guarded-policy` and uses
`RealGuardStateProvider`, so real-camera/dry-run traces can exercise the same
guarded final-insertion logic before any hardware executor is connected.

## Compatibility Checks

Backend-neutral oracle parity check:

```text
oracle_allclose = True
controller_allclose = True
guard_active = True
guard_activated = True
action = [-0.00452166, -0.00307723, 0.00297779]
```

MuJoCo deployment smoke after the refactor:

```text
results\policy_inference_guarded_provider_refactor_smoke.csv
success_rate = 1.000
collision_rate = 0.000
steps = 34
guard_steps = 34
final_dist_xy = 0.00479
final_dist_z = 0.00768
```

Real dry-run guarded smoke:

```text
results\real_policy_dryrun_guarded_smoke.csv
zero_policy = true
guarded_policy = true
steps = 2
guard_steps = 2
```

The real dry-run smoke does not move hardware. It only verifies that static
near-hole telemetry can activate the guarded controller and that the trace CSV
contains guard diagnostics and guarded actions.

## Current Boundary

The real adapter still assumes the caller provides calibrated `peg_tip_pos` and
`target_pos`. The next deployment step is to replace those static values with
measured UR5/UR5e TCP pose plus a calibrated hole-pose estimate from the camera
or fixture registration.
