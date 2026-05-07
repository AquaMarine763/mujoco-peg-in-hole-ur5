# UR5e Real Readiness Smoke Summary

This smoke bundle validates the read-only real-robot deployment path for the
current UR5e image policy. It does not authorize or command real robot motion.

## Scope

- Config: `configs\real\ur5e\synthetic_smoke.yaml`
- Policy: `checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip`
- Observation contract: `cam_image` plus `near_hole_crop`
- Guarded policy defaults: `guard_start_xy=0.060`, `guard_start_z=0.080`, `guard_blend=0.75`
- Inputs: synthetic camera frames and synthetic TCP trace

## Results

| Gate | Verdict | Output |
| --- | --- | --- |
| Static deployment config | PASS | `results\real\ur5e\smoke\config_check.md` |
| Direct guarded dry-run | PASS | `results\real\ur5e\smoke\direct_dryrun_trace.csv` |
| Dry-run preflight | PASS | `results\real\ur5e\smoke\dryrun_summary.md` |
| Synthetic capture bundle | PASS | `results\real\ur5e\smoke\capture_bundle_summary.md` |
| Motion readiness, synthetic allowed | PASS | `results\real\ur5e\smoke\motion_readiness_synthetic_allowed.md` |
| Motion readiness, default gate | FAIL expected | `results\real\ur5e\smoke\motion_readiness_synthetic_expected_fail.md` |
| Strict template gate | FAIL expected | `results\real\ur5e\smoke\strict_template_expected_fail.md` |

## Interpretation

The software path is internally consistent for the current UR5e staged-crop
model: config validation, near-hole crop observation generation, guarded
dry-run inference, synthetic capture, TCP trace handling, and readiness reporting
all pass when synthetic smoke inputs are explicitly allowed.

The default motion-readiness gate still rejects this bundle because it uses
synthetic inputs and smoke output paths. That is intentional. Before real
motion, replace the template config with measured local values, record real
camera/TCP data, and pass readiness without synthetic allowances.

The strict template gate also rejects `dryrun_template.yaml` when
`--require-camera-calibration`, `--require-image-crop`, and `--fail-on-warn`
are enabled. That is intentional: the template still contains unmeasured camera
and crop placeholders.
