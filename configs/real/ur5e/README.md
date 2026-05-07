# Real UR5e Readiness Configs

These files are for read-only real-robot preparation. They do not command
hardware motion by themselves.

Use `dryrun_template.yaml` as the editable starting point for measured UR5e
values. Do not use it for motion until camera preprocessing, TCP-to-peg-tip,
target calibration, and workspace bounds have been measured on the real cell.

`synthetic_smoke.yaml` and the matching smoke CSV/YAML files are deterministic
inputs for validating the software gate without hardware.

Create a local ignored session before recording real data:

```powershell
python scripts/prepare_real_ur5e_session.py --session-id real_ur5e_YYYYMMDD --ur-host <UR5E_IP> --camera-device-index 0 --overwrite
```

The generated `configs/real/ur5e/*_local.yaml` and
`results/real/ur5e/real_*/` paths are ignored by git. Edit the local YAML with
measured `crop_xywh`, camera intrinsics, `tool0_to_camera_*`,
`tcp_to_peg_tip_xyz`, workspace bounds, and fixture target calibration before
running the generated `COMMANDS.md`.

For real readiness, run config checks with `--require-camera-calibration`,
`--require-image-crop`, and `--fail-on-warn`. These flags intentionally reject
the unmeasured placeholders in `dryrun_template.yaml`.

Recommended smoke checks:

```powershell
python scripts/check_real_deployment_config.py --config configs/real/ur5e/synthetic_smoke.yaml --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip --output-md results/real/ur5e/smoke/config_check.md --output-json results/real/ur5e/smoke/config_check.json
python scripts/run_real_dryrun_preflight.py --config configs/real/ur5e/synthetic_smoke.yaml --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip --max-steps 4 --trace-output results/real/ur5e/smoke/dryrun_trace.csv --check-output-md results/real/ur5e/smoke/dryrun_check.md --check-output-json results/real/ur5e/smoke/dryrun_check.json --summary-md results/real/ur5e/smoke/dryrun_summary.md
```

Full synthetic capture/readiness smoke:

```powershell
python scripts/run_real_capture_bundle.py `
  --session-id ur5e_config_gate_synthetic_smoke `
  --config configs/real/ur5e/synthetic_smoke.yaml `
  --record-camera-synthetic-smoke --record-camera-frames 10 --record-camera-warmup-frames 1 `
  --record-tcp-synthetic-smoke --record-tcp-samples 10 `
  --target-calibration configs/real/ur5e/target_calibration_smoke.yaml `
  --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip `
  --device cpu --episodes 1 --max-steps 4 --tcp-to-peg-tip-xyz 0 0 -0.11 `
  --allow-action-limited `
  --summary-md results/real/ur5e/smoke/capture_bundle_summary.md `
  --output-json results/real/ur5e/smoke/capture_bundle_summary.json `
  --preflight-summary-md results/real/ur5e/smoke/capture_preflight_summary.md `
  --preflight-output-json results/real/ur5e/smoke/capture_preflight_summary.json

python scripts/check_real_motion_readiness.py `
  --bundle-summary-json results/real/ur5e/smoke/capture_bundle_summary.json `
  --allow-synthetic --allow-smoke-paths `
  --output-md results/real/ur5e/smoke/motion_readiness_synthetic_allowed.md `
  --output-json results/real/ur5e/smoke/motion_readiness_synthetic_allowed.json
```

The default readiness gate should still fail this synthetic bundle unless
`--allow-synthetic` and `--allow-smoke-paths` are provided.
