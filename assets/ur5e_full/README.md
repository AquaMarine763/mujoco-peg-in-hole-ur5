# Full UR5e Peg-In-Hole Model

`ur5e_peg_in_hole_full.xml` is the full UR5e task adapter for demos and
validation runs. It is based on DeepMind MuJoCo Menagerie
`universal_robots_ur5e/ur5e.xml` and vendors the UR5e OBJ visual meshes,
Menagerie inertials, position-style actuator parameters, and collision
geometry.

The model keeps the current peg-in-hole task interface:

- Joints: `shoulder_pan`, `shoulder_lift`, `elbow`, `wrist_1`, `wrist_2`,
  `wrist_3`
- Actuators: `shoulder_pan_ctrl`, `shoulder_lift_ctrl`, `elbow_ctrl`,
  `wrist_1_ctrl`, `wrist_2_ctrl`, `wrist_3_ctrl`
- Bodies/sites/cameras: `tool0`, `eef_site`, `peg_tip`, `wrist_cam`,
  `hole_body`, `hole_site`, `overview`
- Task geoms: `peg_geom`, `table_top`, `hole_plate`, `hole_north`,
  `hole_south`, `hole_east`, `hole_west`

Use it explicitly with:

```powershell
--model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml
```

The branch default remains the lighter `assets/ur5e_adapter` model so existing
training and evaluation results remain comparable. Use this full model when the
demo or validation needs the actual UR5e geometry in the rendered scene.

## Validation

```powershell
python scripts\inspect_robot_model.py --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml --output-md results\robot_model_ur5e_full.md --fail-on-missing
python scripts\oracle_rollout.py --model-path assets\ur5e_full\ur5e_peg_in_hole_full.xml --observation-mode state --episodes 3 --max-steps 120
```

## Source

The UR5e robot model and meshes are from DeepMind MuJoCo Menagerie,
`universal_robots_ur5e`, released under BSD-3-Clause. See `LICENSE`.
