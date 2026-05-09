# Agent Working Notes

Last updated: 2026-05-09

This file records the standing workflow, user preferences, safety rules, and project constraints for future Codex work in this repository. Read this file before making non-trivial changes.

## Project Goal

Build a MuJoCo peg-in-hole reproduction inspired by `DRL_Peg-in-Hole_UR5`, then evolve it into a UR5e sim-to-real pipeline.

The current focus is:

- Keep the existing lightweight UR5e adapter training pipeline usable.
- Add and validate a full UR5e MuJoCo task model.
- Improve robustness with image observations, near-hole crop, domain randomization, guarded insertion, and staged geometry curriculum.
- Prepare real UR5e deployment in read-only / dry-run form before enabling any real robot motion.

## User Preferences

- Use Chinese for user-facing explanations unless the user asks otherwise.
- Be direct and implementation-first.
- Prefer concrete commands, current metrics, and next-step plans over abstract discussion.
- Keep useful project milestones documented.
- Push useful stable milestones to GitHub when requested, but do not push every small local change automatically.
- Do not ask unnecessary questions; make conservative assumptions when the repo context is enough.

## Safety Rules

- Do not enable real robot motion without explicit user approval.
- Real-robot work must stay read-only, synthetic, dry-run, or config-validation until the user explicitly decides to move forward.
- Keep strict real deployment gates:
  - camera calibration required
  - near-hole image crop required
  - target/workpiece calibration required
  - TCP pose trace validation required
  - dry-run validation required
- Never hard-reset or revert unrelated user changes.
- Do not touch `main` for risky work; use feature branches for model replacement, UR5e migration, or larger experiments.

## Repo Conventions

- Repo root: `D:\peg-in-hole-6yh\mujoco_peg_in_hole`
- Current UR5e branch: `feature/ur5e-mainline`
- Remote: `https://github.com/AquaMarine763/mujoco-peg-in-hole-ur5.git`
- Default task model remains the lightweight UR5e adapter unless explicitly switched:
  - `assets/ur5e_adapter/ur5e_peg_in_hole.xml`
- Full UR5e model lives at:
  - `assets/ur5e_full/ur5e_peg_in_hole_full.xml`
- Current full UR5e task geometry hides debug sites in rendered demos and uses a narrowed hole:
  - peg diameter about `24 mm`
  - base hole opening about `40 mm`
  - randomized geometry opening about `34 - 42 mm`
  - current full UR5e guarded alignment threshold: `0.020 m`
  - current full UR5e guarded blend: `1.0`
- Current recommended full UR5e narrowed-hole checkpoint:
  - `checkpoints\ur5e_full\adapt\sac_image_bc_50k_narrow_hole_full_light_geometry.zip`
- Latest full UR5e narrowed-hole correction candidate:
  - `checkpoints\ur5e_full\correction\sac_image_bc_50k_narrow_correction_8k_w10_e2.zip`
  - Do not treat it as the default unless a later evaluation clearly beats the adapted checkpoint; the first correction pass was mostly flat.
- Latest full UR5e high-start candidate:
  - `checkpoints\ur5e_full\high_start\sac_image_bc_50k_high_start_visual_camera.zip`
  - Do not treat it as the default; 100-episode high-start guarded success is only about `0.15 - 0.24`.
- Latest full UR5e easy high-start candidate:
  - `checkpoints\ur5e_full\high_start\easy\sac_image_bc_50k_high_start_easy_visual_camera.zip`
  - Easy range: `0.08 - 0.15 m` height and `0.04 - 0.10 m` XY offset.
  - Treat it as the current high-start curriculum checkpoint, but not the general default; same-seed success is about `0.48 - 0.63` across scenarios.
- Latest full UR5e medium high-start candidate:
  - `checkpoints\ur5e_full\high_start\medium\sac_image_bc_50k_high_start_medium_visual_camera.zip`
  - Medium range: `0.10 - 0.18 m` height and `0.06 - 0.12 m` XY offset.
  - Treat it as the current best high-start curriculum checkpoint; success is about `0.49 - 0.68` across scenarios.
- Latest full UR5e hard-range high-start candidate:
  - `checkpoints\ur5e_full\high_start\hard\sac_image_bc_50k_high_start_hard_safe_visual_camera.zip`
  - Hard range: `0.15 - 0.25 m` height and `0.08 - 0.16 m` XY offset with `0.12 m` safe approach height.
  - Do not promote it as default; success is about `0.27 - 0.48` across scenarios.
- High-start two-phase controller status:
  - `OracleControllerConfig.mode` supports `high_start_two_phase`.
  - `guarded_oracle_mode: high_start_two_phase` is supported by demo/eval/inference scripts.
  - `guard_block_down_when_unaligned` now applies before guard activation too.
  - Do not make the current two-phase hard config default yet; first eval was mixed and increased timeout.
  - The latest hard high-start guarded scan shows `high_start_two_phase` and hard down-block are not yet clear improvements over `guarded_two_stage`.
  - The focused `align=0.025`, `guarded_two_stage` 100-episode eval is also not promoted; it reached clean `0.530` but only visual_camera `0.370`, visual_camera_control `0.310`, full_contact `0.290`, and hard bucket `0.270`.
  - The latest hard demo failure plateaus near `8.4 mm` XY error and `32.8 mm` height above target, so the next improvement should target near-hole plateau/failure correction rather than more success-only hard data.
- Hard high-start correction status:
  - `collect_image_correction_dataset.py` supports high-start reset args and visual/high-start scenario presets.
  - The first correction smoke collected `256` near-hole failure samples from `29` visual_camera hard high-start episodes.
  - The samples are high-signal: `72.3%` opposed policy/oracle actions and `86.7%` policy-down/oracle-up-or-less-down.
  - The 1-epoch correction smoke checkpoint is not promoted; same-seed 20-episode eval was mixed and the demo still timed out near `8.4 mm` XY error.
- Current near-term plan:
  - expand hard high-start correction from smoke to `2k - 10k` samples and lower the per-sample conflict by tuning correction weight/epochs
  - consider a guarded re-align/retry behavior for the final `5 - 15 mm` XY error band
  - introduce larger randomized initial XY offsets only after original hard high-start search is stable
  - then reintroduce control/geometry/contact randomization

## Editing Workflow

- Check `git status --short --branch` before and after code changes when possible.
- Use `rg` / `rg --files` for searching.
- Use `apply_patch` for manual file edits.
- Keep changes scoped to the requested task.
- Do not rewrite docs or code unrelated to the current milestone.
- Run targeted validation after implementation.
- Update `PLAN.md` when project status, metrics, default commands, branch state, or next milestones change.
- Update this `AGENTS.md` when user preferences, safety rules, workflow rules, or repository-level conventions change.

## Validation Expectations

Use targeted validation rather than broad expensive runs unless needed.

Common checks:

```powershell
python -m py_compile <changed_python_file>
git diff --check
python scripts\inspect_robot_model.py --model-path <model.xml> --fail-on-missing
python scripts\oracle_rollout.py --model-path <model.xml> --observation-mode state --episodes 3 --max-steps 120
```

For policy performance, prefer 100-episode evals for stable numbers.

## Real Robot Boundary

Real deployment is not active yet. The current acceptable real-robot tasks are:

- generate session folders/config templates
- inspect camera frames and crop alignment
- validate deployment YAML
- replay synthetic or recorded observations
- produce readiness reports

Do not send URScript, RTDE servo commands, joint commands, Cartesian motion commands, gripper commands, or any other motion command to a physical robot unless the user explicitly asks for that phase and safety checks have passed.
