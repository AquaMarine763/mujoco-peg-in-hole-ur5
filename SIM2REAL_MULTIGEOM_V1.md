# Sim2Real Multi-Geometry v1

This is the cleaned entry point for the v148/v149 same-shape multi-geometry baseline.

## What This Version Is

`sim2real_multigeom_v1` is an alias layer over the v148/v149 evaluated stack. It is the current multi-geometry baseline to carry toward sim-to-real.

It is not the v221 hard-square-only line. v221 is useful as a focused square-square recovery reference, but v148/v149 is the actual multi-geometry baseline.

Main simulation config:

```powershell
configs\sim2real\multigeom_v1_eval.yaml
```

This inherits:

```powershell
configs\sim\ur5e_full\eval_multi_geometry_v148_square_pose_yaw_align_w020_60ep.yaml
```

Core stack:

- Full UR5e MuJoCo task XML: `assets\ur5e_full\ur5e_peg_in_hole_full.xml`
- Image policy: `checkpoints\ur5e_full\high_start\hard\correction\sac_image_bc_wrist_pose_control_state_insert_drift_2k_w10_e1.zip`
- Observation: wrist image, near-hole crop, and control state
- Start state: peg tip 15-25 cm above target, 8-16 cm XY offset
- Geometry profile: `mixed_same_shape`
- Shapes: `round_round`, `square_square`, `hex_hex`, `triangle_triangle`, `slot_slot`, `rectangular_key`
- Guarded insertion stack: approach adapter, final insert adapter, stateful recovery, square tilt reinsert, square fast settle, square pose/yaw align
- Control randomization: delayed, noisy, filtered, scale-randomized control in the hard bucket

## Current Evidence

Combined v148 + v149 validation:

| Condition | Result |
| --- | ---: |
| Combined mixed same-shape | 720/720 |
| Collision | 0 |
| Timeout | 0 |

Shape breakdown from local validation CSVs:

| Shape | Success |
| --- | ---: |
| `round_round` | 111/111 |
| `square_square` | 125/125 |
| `hex_hex` | 116/116 |
| `triangle_triangle` | 121/121 |
| `slot_slot` | 123/123 |
| `rectangular_key` | 124/124 |

Reference result directories:

```powershell
D:\peg-in-hole-6yh\v148_square_pose_yaw_align_probe\matrix_60ep_weight020_six_seed
D:\peg-in-hole-6yh\v149_v148_fresh_seed_gate_906500_907500
```

## Quick Commands

Run from the repository root.

Evaluate the default mixed same-shape profile:

```powershell
.\scripts\sim2real\eval_multigeom_v1.ps1
```

Evaluate a fixed profile:

```powershell
.\scripts\sim2real\eval_multigeom_v1.ps1 -Profile hex_hex -Seeds 906500,907500 -Episodes 60
```

Render a demo GIF:

```powershell
.\scripts\sim2real\demo_multigeom_v1.ps1 -Profile mixed_same_shape -Seed 906500
```

By default this renders a 2x2 GIF: `overview` in the upper-left, `wrist_cam` in
the lower-left, policy `cam_image` in the upper-right, and policy
`near_hole_crop` in the lower-right. `overview` makes the insertion outcome
easy to inspect, while the right column shows the actual image tensors seen by
the policy. To force a single overview camera:

```powershell
.\scripts\sim2real\demo_multigeom_v1.ps1 -Profile square_square -Seed 906500 -RenderCameras overview -NoPolicyObservationPanel
```

Render a fixed-shape demo:

```powershell
.\scripts\sim2real\demo_multigeom_v1.ps1 -Profile rectangular_key -Seed 906500
```

Run non-strict real preflight config validation:

```powershell
.\scripts\sim2real\preflight_multigeom_v1.ps1
```

Run strict real preflight validation after measured calibration is filled in:

```powershell
.\scripts\sim2real\preflight_multigeom_v1.ps1 -Strict
```

Run synthetic real-interface dry-run without loading the policy:

```powershell
.\scripts\sim2real\dryrun_multigeom_v1.ps1 -ZeroPolicy
```

Run synthetic real-interface dry-run with the policy model:

```powershell
.\scripts\sim2real\dryrun_multigeom_v1.ps1
```

Outputs go to:

```powershell
results\sim2real_multigeom_v1
```

The shortcut scripts also set `PYTHONPATH` to the current repository root and
resolve the policy model from the current worktree first, then from the sibling
`D:\peg-in-hole-6yh\mujoco_peg_in_hole` worktree if this worktree does not have
`checkpoints`.

## Files Added For This Version

Simulation:

```powershell
configs\sim2real\multigeom_v1_eval.yaml
configs\sim2real\multigeom_v1_demo.yaml
scripts\sim2real\eval_multigeom_v1.ps1
scripts\sim2real\demo_multigeom_v1.ps1
```

Real-interface preparation:

```powershell
configs\sim2real\multigeom_v1_real_dryrun.yaml
configs\sim2real\multigeom_v1_real_preflight.yaml
scripts\sim2real\dryrun_multigeom_v1.ps1
scripts\sim2real\preflight_multigeom_v1.ps1
```

## Important Limitations

The authoritative performance entry is `eval_multigeom_v1.ps1`. It uses `eval_guarded_policy.py`, which supports the full v148/v149 stack.

The demo entry now uses the same action-chain components needed for v148/v149 visualization: policy, approach adapter, guarded controller, final-insert adapter, square pose/yaw align, and full-light control/geometry randomization. Still use `eval_multigeom_v1.ps1` for success-rate claims because demo runs are short visual rollouts, not evaluation matrices.

The task XMLs include a visual-only `hole_cavity_visual` geom for demo
readability. The sim2real demo additionally appends a policy observation panel
generated from the live `obs` dict. These outputs do not change collision
geometry, success checks, or controller behavior. The `hole_top` inspection
camera remains available for optional debugging, but it is not part of the
default demo because it can be occluded by the wrist during insertion.

For polygon holes, the visual cavity marker is hidden so it does not cover the
actual `hex_hex` or `triangle_triangle` wall layout with a misleading round
disk. Runtime checks confirm `hex_hex` uses six active wall geoms and
`triangle_triangle` uses three. To make demos less misleading, `hex` and
`triangle` also use separate visual-only polygon wall geoms whose ends overlap
for a connected block appearance. These visual geoms have no contact and do not
change success checks or collision behavior. The underlying polygon holes are
still box-wall scaffolds, not final CAD/mesh fixtures. `slot_slot` and
`rectangular_key` are still rectangular scaffold profiles with different aspect
ratios; replacing them with true rounded-slot and keyed/keyway geometry is a
future geometry-modeling step.

The final-insert adapter is intentionally gated. It may show `0` active steps in clean successful demos because it only takes over in near-hole square fast-settle stall/risk states.

`triangle_triangle` still uses an easy-curriculum triangular hole floor. Keep this visible until the triangular fixture/chamfer model is tightened.

The real dry-run scripts do not send motion to hardware. They validate the policy, observation, safety, target, and guarded-controller interface only.

## Smoke Checks

Latest local smoke checks in this worktree:

```powershell
.\scripts\sim2real\eval_multigeom_v1.ps1 -Profile round_round -Seeds 906500 -Episodes 1 -ResultDir results\sim2real_multigeom_v1_smoke
.\scripts\sim2real\demo_multigeom_v1.ps1 -Profile round_round -Seed 906500 -Episodes 1 -ResultDir results\sim2real_multigeom_v1_smoke
.\scripts\sim2real\preflight_multigeom_v1.ps1
.\scripts\sim2real\dryrun_multigeom_v1.ps1 -ZeroPolicy
```

Observed smoke outcomes:

- eval smoke: `round_round`, seed `906500`, `1/1` success.
- demo smoke: `round_round`, seed `906500`, success, GIF written to `results\sim2real_multigeom_v1_smoke`.
- non-strict real preflight: PASS.
- zero-policy real-interface dry-run: wrote a 4-step trace to `results\sim2real_multigeom_v1`.

Latest full-stack demo smoke after wiring adapters into `demo_policy.py`:

```powershell
.\scripts\sim2real\demo_multigeom_v1.ps1 -Profile round_round -Seed 906500 -Episodes 1 -ResultDir results\sim2real_multigeom_v1_demo_full_smoke2
.\scripts\sim2real\demo_multigeom_v1.ps1 -Profile square_square -Seed 906500 -Episodes 1 -ResultDir results\sim2real_multigeom_v1_demo_full_smoke2
.\scripts\sim2real\demo_multigeom_v1.ps1 -Profile mixed_same_shape -Seed 906500 -Episodes 1 -ResultDir results\sim2real_multigeom_v1_demo_full_smoke2
```

Observed full-stack demo outcomes:

- `round_round`: success, approach adapter active `98` steps.
- `square_square`: success, approach adapter active `104` steps, square pose/yaw align active `47` steps.
- `mixed_same_shape`: success, sampled `rectangular_key`, approach adapter active `105` steps.

Latest policy-observation demo smoke:

```powershell
.\scripts\sim2real\demo_multigeom_v1.ps1 -Profile square_square -Seed 906500 -Episodes 1 -ResultDir results\sim2real_multigeom_v1_demo_grid2x2_smoke
```

Observed outcome: success, zero collision, `202` steps, `adapter_steps=97/0/46`,
GIF size `2560x1440` in the 2x2 layout: `overview`, `cam_image`, `wrist_cam`,
and `near_hole_crop`.

## Real-Robot Gate Before Motion

Before any real UR5e motion:

- Measure and fill `target_calibration`.
- Measure TCP/tool0 to peg-tip transform.
- Measure camera intrinsics and tool0-to-camera transform.
- Record real camera frames and set `crop_xywh`.
- Record TCP pose traces in `robot_base`.
- Confirm safety workspace around the physical fixture.
- Pass strict preflight:

```powershell
.\scripts\sim2real\preflight_multigeom_v1.ps1 -Strict
```

- Pass dry-run with real recorded camera/TCP inputs before enabling a hardware executor.

## Next Work

1. Make demo execution match the full eval stack, or keep demo explicitly visual-only.
2. Build measured real calibration configs from the actual UR5e cell.
3. Add real image/crop inspection commands for each geometry fixture.
4. Add a hardware-disabled replay gate that consumes recorded camera/TCP traces.
5. Only after those pass, design the first guarded low-speed real motion test.
