# Project Structure

Mainline model:

```text
assets/ur5e_adapter/ur5e_peg_in_hole.xml
```

Legacy simplified model:

```text
assets/ur5_peg_in_hole.xml
```

Recommended layout for new work:

```text
assets/
  ur5e_adapter/
  ur5_legacy/
configs/
  real/
  sim/
    ur5e/
    ur5/
datasets/
  ur5e/
  ur5/
checkpoints/
  ur5e/
  ur5/
results/
  ur5e/
  ur5/
  real/
demos/
  ur5e/
  ur5/
```

Guidelines:

- Keep the UR5e adapter as the default development model on this branch.
- Keep the legacy UR5-like model only for comparison and regression checks.
- Put new UR5e experiments under `*_ur5e_*` names and new real-robot
  readiness outputs under `results/real/`.
- Do not rename historical artifact paths unless a script or command is being
  updated in the same change.
