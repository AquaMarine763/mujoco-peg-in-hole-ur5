# Sim2Real Learned-Vision Multi-Shape Plan

Branch: `feature/sim2real-learned-vision-multishape`

Baseline frozen from: `v0.7.8-visual-yaw-key-estimator-v2`

## Motivation

The current visual-yaw alignment stack is strong in simulation, but it is not yet
a clean sim-to-real visual policy. The `v0.7.8` gate reached `60/60` across
`square_square`, `triangle_triangle`, `hex_hex`, and `rectangular_key`, with
zero collision and zero timeout. However, the policy-observation panels show
three transfer risks:

- `cam_image` is only `100x100`, and `near_hole_crop` is only `64x64`.
- Near-hole views can be occluded by the wrist/tool as the peg descends.
- The hole often appears near the left edge of the crop because earlier configs
  intentionally used offsets such as `[-18, 0]` and `[-18, -12]`.

This branch should reduce reliance on geometry-truth shaping and guarded
special cases, while keeping the proven `v0.7.8` result as the rollback point.

## Shape Scope

Use one same-shape insertion task family, including all target shapes:

- `round_round`
- `slot_slot`
- `square_square`
- `triangle_triangle`
- `hex_hex`
- `rectangular_key`

Do not treat round and slot as legacy side cases. They should be part of the
same training/evaluation matrix as the four visual-yaw shapes.

## Principle

The long-term policy should learn most of the alignment behavior from images,
not from direct geometry truth. Geometry truth may still be used for:

- dataset labels during supervised pretraining;
- offline diagnostics and evaluation;
- conservative real-robot safety checks;
- teacher/oracle collection before deployment.

Geometry truth should not be required at runtime for ordinary alignment
decisions once the learned visual stack is mature.

## Phase 1: Observation Quality Audit

Goal: prove what the policy can and cannot see.

Actions:

1. Collect rollout observation snapshots for all six shapes.
2. Save `cam_image`, `near_hole_crop`, overview frame, wrist-camera frame, true
   XY error, true yaw error, predicted yaw, raw norm, Z height, and success
   state.
3. Compute visibility metrics:
   - hole center distance from image center;
   - out-of-frame rate;
   - crop border-touch rate;
   - low-Z occlusion rate;
   - image/crop contrast and variance;
   - yaw-estimator error by shape and height band.
4. Produce contact sheets for human review.

Success criterion: identify a camera/crop configuration that keeps the hole
visible and near-centered through the approach and near-hole bands for all six
shapes.

## Phase 2: Camera And Crop Redesign

Start with changes that preserve the saved policy observation shapes:

- keep `cam_image=100x100`;
- keep `near_hole_crop=64x64`;
- scan `near_hole_crop_source_size` from `80` to `96`, `112`, and `128`;
- scan crop offsets around `[-18, -12]`, `[-12, -8]`, `[-8, -4]`, and `[0, 0]`;
- move the wrist camera away from self-occlusion by scanning small tool-frame
  offsets and pitch/yaw rotations;
- keep one wrist camera first, and add a second camera only if the single-camera
  scan cannot keep the hole visible.

The first decision metric is not success rate. The first decision metric is
whether the visual input is usable for real deployment.

## Phase 3: Learned Visual Alignment Model

Train a shape-aware visual alignment stack that covers all six shapes.

Dataset design:

- balanced per shape;
- stratified by yaw;
- stratified by Z height, especially low-Z and near-hole bands;
- includes random XY offsets and realistic camera/crop jitter;
- disables debug peg-tip highlights during training;
- stores shape ID or shape embedding only if it is also available in real
  deployment.

Model outputs to consider:

- XY residual toward the hole center;
- shape yaw residual;
- confidence/visibility score;
- optional descent permission score.

The goal is to replace runtime geometry-truth alignment logic with learned
visual estimates wherever practical.

## Phase 4: Reduce Runtime Geometry Truth

Run ablations that remove or weaken privileged runtime signals:

- visual-yaw estimator only from images;
- no simulator-truth shape-yaw at runtime except logging;
- guard still allowed for safety envelopes;
- final insertion safety still allowed for collision avoidance;
- compare normal images, shuffled images, black images, and crop-only / cam-only
  inputs.

Promotion target:

- six-shape same-shape gate at least `95%`;
- zero or near-zero collision;
- no shape-specific collapse;
- clear demo evidence that wrist rotation and insertion are driven by visible
  shape alignment.

## Phase 5: Sim-To-Real Preflight

Before any real insertion:

1. Run real camera dry-run with no robot motion or zero-action motion.
2. Convert real camera frames into the same `cam_image + near_hole_crop` tensors.
3. Compare sim and real contact sheets by shape.
4. Check whether hole position, scale, contrast, and occlusion match the chosen
   sim camera/crop distribution.
5. Only then run guarded low-speed approach trials above the hole.

## Current Decision

Open this branch as the next research line. Do not overwrite the `v0.7.8`
baseline. The next implementation step is the observation-quality audit and
camera/crop scan, with `round_round` and `slot_slot` included from the start.
