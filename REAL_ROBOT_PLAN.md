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
  image or image folder and preprocesses it to the policy shape.
- `DryRunUR5ActionExecutor`: accepts safe Cartesian actions and logs them
  without moving hardware.
- `scripts/run_policy_inference.py`: command-line entry point for the MuJoCo
  backend.
- `scripts/run_real_policy_dryrun.py`: command-line entry point for the
  real-backend dry-run path.
- `configs/real_ur5_dryrun.yaml`: conservative placeholder configuration.

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

1. Replace placeholder camera and tool transforms in
   `configs/real_ur5_dryrun.yaml` with measured values.
2. Validate real camera preprocessing with representative frames.
3. Add a UR5 action executor that can run in explicit dry-run mode first, then
   guarded motion mode.
4. Replace or calibrate the simplified MuJoCo arm with a UR5/UR5e model before
   relying on dynamics results.

## Do Not Assume

- Do not assume the simplified MuJoCo link lengths, inertia, damping, or
  actuators match a real UR5.
- Do not assume the current wrist camera pose matches a real mounted camera.
- Do not assume simulation success implies real insertion safety.
- Do not bypass the safety filter when moving real hardware.
