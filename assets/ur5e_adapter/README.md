# UR5e Adapter

This directory contains a lightweight UR5e MJCF adapter. The project still
runs on `assets/ur5_peg_in_hole.xml` by default unless scripts are called with
`--model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml`.

`ur5e_peg_in_hole.xml` is derived from the DeepMind MuJoCo Menagerie
`universal_robots_ur5e/ur5e.xml` model. It keeps the UR5e joint chain,
inertials, actuator style, and simplified collision geometry, but does not
vendor the large visual mesh assets. See `LICENSE` in this directory for the
upstream BSD-3-Clause license notice.

To use another real UR5/UR5e model with the current environment, create an
adapter MJCF that exposes the same task interface names expected by the code:

## Required Names

- Joints: `shoulder_pan`, `shoulder_lift`, `elbow`, `wrist_1`, `wrist_2`,
  `wrist_3`
- Actuators: `shoulder_pan_ctrl`, `shoulder_lift_ctrl`, `elbow_ctrl`,
  `wrist_1_ctrl`, `wrist_2_ctrl`, `wrist_3_ctrl`
- Bodies: `hole_body`, `tool0`
- Sites: `peg_tip`, `eef_site`, `hole_site`
- Cameras: `overview`, `wrist_cam`
- Task geoms: `table_top`, `peg_geom`, `hole_plate`, `hole_north`,
  `hole_south`, `hole_east`, `hole_west`

`hole_body` must be a MuJoCo mocap body because the environment randomizes the
fixture pose at reset.

## Check Compatibility

From the repository root:

```powershell
python scripts\inspect_robot_model.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --output-md results\robot_model_ur5e_adapter.md --fail-on-missing
```

If the report is compatible, the same XML can be passed to training,
evaluation, demo, and dataset commands with:

```powershell
--model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml
```

Run a quick staged-oracle check after changing transforms:

```powershell
python scripts\oracle_rollout.py --model-path assets\ur5e_adapter\ur5e_peg_in_hole.xml --observation-mode state --episodes 3
```
