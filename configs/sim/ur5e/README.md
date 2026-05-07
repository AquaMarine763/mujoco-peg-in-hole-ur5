# UR5e Simulation Configs

These flat YAML files provide command defaults for the UR5e mainline branch.
Command-line arguments still override values from `--config`.

Recommended branch-default policy:

`checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip`

Common commands:

```powershell
python scripts/eval_matrix.py --config configs/sim/ur5e/eval_image_crop.yaml
python scripts/eval_guarded_policy.py --config configs/sim/ur5e/eval_guarded_image_crop.yaml
python scripts/demo_policy.py --config configs/sim/ur5e/demo_guarded_image_crop.yaml
python scripts/scan_guarded_policy_params.py --config configs/sim/ur5e/scan_guarded_policy_focused.yaml
```

Smoke commands for the structured artifact layout:

```powershell
python scripts/collect_image_expert_dataset.py --config configs/sim/ur5e/collect_image_expert_smoke.yaml
python scripts/pretrain_image_actor_bc.py --config configs/sim/ur5e/pretrain_image_bc_smoke.yaml
```
