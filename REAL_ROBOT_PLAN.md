# Real Robot Plan

This project currently uses a simplified UR5-like MuJoCo arm, not a calibrated
UR5/UR5e digital twin. The current value of the project is the task loop,
policy interface, domain randomization, evaluation matrix, and diagnostics. Do
not run a learned policy on a real robot until the items below are complete.

## Current Deployment Interface

The policy interface is:

```text
observation -> SB3 policy -> dx, dy, dz -> safety filter -> action executor
```

Current implementation:

- `SB3PolicyAdapter`: wraps a Stable-Baselines3 model.
- `SafetyFilter`: limits per-step Cartesian motion and clips the target inside
  a workspace box.
- `PolicyInferenceSession`: runs the policy through backend-neutral
  observation/action interfaces and logs each inference step.
- `MujocoObservationProvider`: adapts MuJoCo reset/observation into the generic
  interface.
- `MujocoActionExecutor`: adapts safe Cartesian actions into MuJoCo `env.step`.
- `RealCameraObservationProvider`: dry-run provider that loads a real camera
  image or image folder and preprocesses it to the policy shape, including the
  optional `near_hole_crop` key required by the current UR5e image policy.
- `preprocess_camera_image`: shared preprocessing path for real frames:
  `crop_xywh -> rotate_k -> flip -> resize -> grayscale uint8[100,100,1]`.
- `DryRunUR5ActionExecutor`: accepts safe Cartesian actions and logs them
  without moving hardware.
- `scripts/run_policy_inference.py`: command-line entry point for the MuJoCo
  backend.
- `scripts/run_real_policy_dryrun.py`: command-line entry point for the
  real-backend dry-run path.
- `scripts/preprocess_camera_frames.py`: offline checker for camera frame
  preprocessing and image statistics.
- `scripts/prepare_real_ur5e_session.py`: creates an ignored local UR5e
  read-only capture session config and command checklist.
- `scripts/inspect_real_camera_crop.py`: generates real camera crop/orientation
  preview sheets for selecting `crop_xywh`, `rotate_k`, and flip settings.
- `scripts/run_real_capture_bundle.py`: records camera frames and UR TCP poses,
  then runs the combined read-only policy preflight.
- `scripts/check_real_motion_readiness.py`: checks a capture bundle before any
  future motion executor is allowed.
- `configs/real/ur5e/dryrun_template.yaml`: conservative UR5e placeholder
  configuration for measured real-cell values.
- `configs/real/ur5e/synthetic_smoke.yaml`: deterministic read-only UR5e
  smoke config for software gates without hardware.
- `scripts/inspect_robot_model.py`: checks whether a candidate MJCF exposes
  the joint, actuator, body, site, camera, and task-geometry names expected by
  the current environment.
- `assets/ur5e_adapter/ur5e_peg_in_hole.xml`: lightweight UR5e adapter derived
  from DeepMind MuJoCo Menagerie. It keeps the UR5e joint chain, inertials,
  actuator style, and simplified collision geoms, but does not include the
  large visual mesh assets.

The action is a Cartesian peg-tip displacement in meters. The default step
limit is `0.005 m`. The current MuJoCo session logs a `50 Hz` control
frequency because the simulator step period is `0.02 s`; a real UR5 dry-run can
use a lower explicit frequency such as `20 Hz` after the real control chain is
measured.

## Calibration Required Before Real UR5

- Confirm the exact robot model: UR5, UR5e, or another UR series arm.
- Calibrate camera intrinsics for the wrist camera.
- Calibrate wrist camera extrinsics relative to `tool0`.
- Calibrate peg tip transform relative to `tool0`.
- Define the real hole frame and table frame.
- Verify the sign convention of `dx, dy, dz` against the real controller.
- Match policy observation preprocessing: crop, resize, grayscale conversion,
  brightness, and camera orientation.
- Measure real control latency and command frequency.
- Validate that the policy action unit is meters, not controller-specific
  speed or joint increments.

## MuJoCo UR5e Model Adapter

Do not replace the working simplified model in-place. The current lightweight
UR5e adapter can be checked with:

```powershell
python scripts\inspect_robot_model.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-md results\robot_model_ur5e_adapter.md --fail-on-missing
```

The adapter must preserve the current task-facing names, including
`peg_tip`, `eef_site`, `tool0`, `hole_body`, `hole_site`, `wrist_cam`, and the
six joint/actuator names. If the source UR5e MJCF uses different internal link
or collision names, wrap it with adapter sites/bodies/actuators instead of
changing the training scripts.

Current limitation: this adapter is useful for validating UR5e kinematics and
the model-selection pipeline, but it is not yet a calibrated visual/dynamics
digital twin. Before real-robot transfer, replace or extend it with measured
tool, camera, peg, table, and fixture transforms.

## Safety Checklist

- Start with a dry run that computes actions but sends zero motion.
- Enforce a conservative workspace around the fixture.
- Enforce maximum Cartesian step and velocity limits.
- Enforce a minimum and maximum allowed `z` range.
- Add a physical emergency stop procedure outside the policy process.
- Add force/torque or current-limit stop conditions before insertion trials.
- Start with the peg above the hole, not from arbitrary approach poses.
- Run at low speed and low force until the real control chain is validated.

## Next Engineering Steps

1. Copy `configs/real/ur5e/dryrun_template.yaml` to an ignored local config
   with `scripts/prepare_real_ur5e_session.py`, then replace placeholder
   camera/tool/fixture values with measured values.
2. Validate `crop_xywh`, `rotate_k`, and flip settings with representative
   real wrist-camera frames, including `near_hole_crop=64`, using
   `scripts/inspect_real_camera_crop.py`.
3. Run a real read-only capture bundle and require
   `--require-camera-calibration`, `--require-image-crop`, and
   `--fail-on-warn` to pass.
4. Add a UR5 action executor that can run in explicit dry-run mode first, then
   guarded motion mode.
5. Calibrate the UR5e adapter transforms against the physical setup.
6. Run the existing eval/demo pipeline with `--model-path` pointing at the
   adapter before relying on dynamics results.

## Do Not Assume

- Do not assume the simplified MuJoCo link lengths, inertia, damping, or
  actuators match a real UR5.
- Do not assume the current wrist camera pose matches a real mounted camera.
- Do not assume simulation success implies real insertion safety.
- Do not bypass the safety filter when moving real hardware.
