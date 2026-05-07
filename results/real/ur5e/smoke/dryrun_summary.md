# Real Dry-run Preflight Summary

- Overall: **PASS**
- Dry-run return code: `0`
- Checker return code: `0`
- Checker verdict: **PASS**
- Trace output: `results\real\ur5e\smoke\dryrun_trace.csv`
- Checker report: `results\real\ur5e\smoke\dryrun_check.md`

## Commands

Dry-run:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/run_real_policy_dryrun.py --config configs\real\ur5e\synthetic_smoke.yaml --agent sac --episodes 1 --output results\real\ur5e\smoke\dryrun_trace.csv --seed 130000 --device cpu --safety-max-action 0.002 --model checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_staged_crop_full_light_replay_750k_oracle_e4\sac_image_bc.zip --guarded-policy --guard-scenario-filter geometry --guard-scenario-name real_ur5_dryrun --guard-scenario-level full_light_geometry --guard-start-xy 0.06 --guard-start-z 0.08 --guard-risk-xy 0 --guard-blend 0.75 --guard-min-policy-steps 0 --guard-action-gain 1 --guard-action-limit 0.002 --guarded-align-xy-tolerance 0.025 --guarded-insert-xy-tolerance 0.005 --guarded-retract-xy-tolerance 0.012 --guarded-preinsert-height 0 --guarded-max-xy-action 0.002 --guarded-max-down-action 0.0015 --guarded-max-up-action 0.002 --guarded-prediction-steps 1
```

Checker:

```powershell
D:\ProgramData\miniconda3\python.exe scripts/check_real_dryrun_trace.py --trace results\real\ur5e\smoke\dryrun_trace.csv --output-md results\real\ur5e\smoke\dryrun_check.md --output-json results\real\ur5e\smoke\dryrun_check.json --max-safe-action 0.002 --expected-pose-frame robot_base --require-nonstatic-pose --require-nonstatic-target --allow-action-limited
```

## Key Metrics

| Metric | Value |
| --- | ---: |
| `rows` | 5 |
| `episodes` | 1 |
| `safe_action_max_abs_component` | 0.0019487999999999728 |
| `safe_action_max_norm` | 0.0021147723289035173 |
| `workspace_limited_rows` | 0 |
| `action_limited_rows` | 0 |
| `guard_active_rows` | 4 |
| `guard_activated_rows` | 1 |
| `first_guard_z_above_target` | 0.0700000524520874 |

## Issues

| Severity | Code | Count | Message |
| --- | --- | ---: | --- |
| INFO | `tcp_offset_check_skipped` | 1 | Pass --tcp-to-peg-tip-xyz to verify TCP-to-peg-tip conversion. |
