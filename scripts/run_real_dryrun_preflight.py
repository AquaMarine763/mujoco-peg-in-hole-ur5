from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a real-robot dry-run trace and then gate it with the offline "
            "trace checker. This does not command hardware motion."
        )
    )
    parser.add_argument("--config", type=Path, default=Path("configs/real_ur5_dryrun.yaml"))
    parser.add_argument("--agent", choices=["sac", "ppo", "a2c"], default="sac")
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--zero-policy", action="store_true")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--seed", type=int, default=130_000)
    parser.add_argument("--image-path", type=Path, default=None)
    parser.add_argument("--image-dir", type=Path, default=None)
    parser.add_argument("--pose-trace", type=Path, default=None)
    parser.add_argument("--tcp-pose-trace", type=Path, default=None)
    parser.add_argument("--target-calibration", type=Path, default=None)
    parser.add_argument("--pose-frame", default=None)
    parser.add_argument("--tcp-to-peg-tip-xyz", nargs=3, type=float, default=None)
    parser.add_argument("--control-frequency-hz", type=float, default=None)
    parser.add_argument("--include-near-hole-crop", dest="include_near_hole_crop", action="store_true", default=None)
    parser.add_argument("--no-include-near-hole-crop", dest="include_near_hole_crop", action="store_false")
    parser.add_argument("--near-hole-crop-size", type=int, default=None)
    parser.add_argument("--safety-max-action", type=float, default=0.002)
    parser.add_argument("--safety-action-filter-alpha", type=float, default=None)
    parser.add_argument("--safety-workspace-low", nargs=3, type=float, default=None)
    parser.add_argument("--safety-workspace-high", nargs=3, type=float, default=None)
    parser.add_argument("--trace-output", type=Path, default=Path("results/real_policy_dryrun_preflight_trace.csv"))
    parser.add_argument("--check-output-md", type=Path, default=Path("results/real_dryrun_preflight_check.md"))
    parser.add_argument("--check-output-json", type=Path, default=None)
    parser.add_argument("--summary-md", type=Path, default=Path("results/real_dryrun_preflight_summary.md"))

    parser.add_argument("--guarded-policy", dest="guarded_policy", action="store_true", default=True)
    parser.add_argument("--no-guarded-policy", dest="guarded_policy", action="store_false")
    parser.add_argument(
        "--guard-scenario-filter",
        choices=["none", "all", "geometry", "hard"],
        default="geometry",
    )
    parser.add_argument("--guard-scenario-name", default="real_ur5_dryrun")
    parser.add_argument(
        "--guard-scenario-level",
        choices=["none", "visual_camera_control", "full_light_geometry", "full_contact_light", "full"],
        default="full_light_geometry",
    )
    parser.add_argument("--guard-start-xy", type=float, default=0.060)
    parser.add_argument("--guard-start-z", type=float, default=0.080)
    parser.add_argument("--guard-risk-xy", type=float, default=0.0)
    parser.add_argument("--guard-blend", type=float, default=0.75)
    parser.add_argument("--guard-min-policy-steps", type=int, default=0)
    parser.add_argument("--guard-block-down-when-unaligned", action="store_true")
    parser.add_argument("--guard-release-on-high", action="store_true")
    parser.add_argument("--guard-action-gain", type=float, default=1.0)
    parser.add_argument("--guard-action-limit", type=float, default=0.002)
    parser.add_argument("--guard-approach-height", type=float, default=None)
    parser.add_argument("--guarded-align-xy-tolerance", type=float, default=0.025)
    parser.add_argument("--guarded-insert-xy-tolerance", type=float, default=0.005)
    parser.add_argument("--guarded-retract-xy-tolerance", type=float, default=0.012)
    parser.add_argument("--guarded-preinsert-height", type=float, default=0.0)
    parser.add_argument("--guarded-max-xy-action", type=float, default=0.002)
    parser.add_argument("--guarded-max-down-action", type=float, default=0.0015)
    parser.add_argument("--guarded-max-up-action", type=float, default=0.002)
    parser.add_argument("--guarded-prediction-steps", type=float, default=1.0)

    parser.add_argument("--expected-pose-frame", default="robot_base")
    parser.add_argument("--expected-target-frame", default=None)
    parser.add_argument("--require-nonstatic-pose", dest="require_nonstatic_pose", action="store_true", default=True)
    parser.add_argument("--allow-static-pose", dest="require_nonstatic_pose", action="store_false")
    parser.add_argument(
        "--require-nonstatic-target",
        dest="require_nonstatic_target",
        action="store_true",
        default=True,
    )
    parser.add_argument("--allow-static-target", dest="require_nonstatic_target", action="store_false")
    parser.add_argument("--allow-action-limited", action="store_true")
    parser.add_argument("--allow-workspace-limited", action="store_true")
    parser.add_argument("--fail-on-warn", action="store_true")
    return parser.parse_args()


def path_arg(path: Path | None) -> str | None:
    if path is None:
        return None
    if path.is_absolute():
        return str(path)
    return str(path)


def repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def extend_path_arg(command: list[str], flag: str, path: Path | None) -> None:
    value = path_arg(path)
    if value is not None:
        command.extend([flag, value])


def extend_values(command: list[str], flag: str, values: list[float] | tuple[float, ...] | None) -> None:
    if values is not None:
        command.append(flag)
        command.extend(f"{float(value):.12g}" for value in values)


def extend_optional(command: list[str], flag: str, value: Any) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def command_text(command: list[str]) -> str:
    return " ".join(f'"{part}"' if " " in part else part for part in command)


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    print(f"\n> {command_text(command)}")
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result


def build_dryrun_command(args: argparse.Namespace) -> list[str]:
    if not args.zero_policy and args.model is None:
        raise ValueError("Provide --model or use --zero-policy.")

    command = [
        sys.executable,
        "scripts/run_real_policy_dryrun.py",
        "--config",
        path_arg(args.config) or "",
        "--agent",
        args.agent,
        "--episodes",
        str(args.episodes),
        "--output",
        path_arg(args.trace_output) or "",
        "--seed",
        str(args.seed),
        "--device",
        args.device,
        "--safety-max-action",
        f"{float(args.safety_max_action):.12g}",
    ]
    if args.zero_policy:
        command.append("--zero-policy")
    else:
        extend_path_arg(command, "--model", args.model)
    if args.stochastic:
        command.append("--stochastic")

    extend_optional(command, "--max-steps", args.max_steps)
    extend_path_arg(command, "--image-path", args.image_path)
    extend_path_arg(command, "--image-dir", args.image_dir)
    extend_path_arg(command, "--pose-trace", args.pose_trace)
    extend_path_arg(command, "--tcp-pose-trace", args.tcp_pose_trace)
    extend_path_arg(command, "--target-calibration", args.target_calibration)
    extend_optional(command, "--pose-frame", args.pose_frame)
    extend_values(command, "--tcp-to-peg-tip-xyz", args.tcp_to_peg_tip_xyz)
    extend_optional(command, "--control-frequency-hz", args.control_frequency_hz)
    if args.include_near_hole_crop is True:
        command.append("--include-near-hole-crop")
    elif args.include_near_hole_crop is False:
        command.append("--no-include-near-hole-crop")
    extend_optional(command, "--near-hole-crop-size", args.near_hole_crop_size)
    extend_optional(command, "--safety-action-filter-alpha", args.safety_action_filter_alpha)
    extend_values(command, "--safety-workspace-low", args.safety_workspace_low)
    extend_values(command, "--safety-workspace-high", args.safety_workspace_high)

    if args.guarded_policy:
        command.extend(
            [
                "--guarded-policy",
                "--guard-scenario-filter",
                args.guard_scenario_filter,
                "--guard-scenario-name",
                args.guard_scenario_name,
                "--guard-scenario-level",
                args.guard_scenario_level,
                "--guard-start-xy",
                f"{args.guard_start_xy:.12g}",
                "--guard-start-z",
                f"{args.guard_start_z:.12g}",
                "--guard-risk-xy",
                f"{args.guard_risk_xy:.12g}",
                "--guard-blend",
                f"{args.guard_blend:.12g}",
                "--guard-min-policy-steps",
                str(args.guard_min_policy_steps),
                "--guard-action-gain",
                f"{args.guard_action_gain:.12g}",
                "--guard-action-limit",
                f"{args.guard_action_limit:.12g}",
                "--guarded-align-xy-tolerance",
                f"{args.guarded_align_xy_tolerance:.12g}",
                "--guarded-insert-xy-tolerance",
                f"{args.guarded_insert_xy_tolerance:.12g}",
                "--guarded-retract-xy-tolerance",
                f"{args.guarded_retract_xy_tolerance:.12g}",
                "--guarded-preinsert-height",
                f"{args.guarded_preinsert_height:.12g}",
                "--guarded-max-xy-action",
                f"{args.guarded_max_xy_action:.12g}",
                "--guarded-max-down-action",
                f"{args.guarded_max_down_action:.12g}",
                "--guarded-max-up-action",
                f"{args.guarded_max_up_action:.12g}",
                "--guarded-prediction-steps",
                f"{args.guarded_prediction_steps:.12g}",
            ]
        )
        extend_optional(command, "--guard-approach-height", args.guard_approach_height)
        if args.guard_block_down_when_unaligned:
            command.append("--guard-block-down-when-unaligned")
        if args.guard_release_on_high:
            command.append("--guard-release-on-high")

    return command


def build_check_command(args: argparse.Namespace, check_json: Path) -> list[str]:
    command = [
        sys.executable,
        "scripts/check_real_dryrun_trace.py",
        "--trace",
        path_arg(args.trace_output) or "",
        "--output-md",
        path_arg(args.check_output_md) or "",
        "--output-json",
        path_arg(check_json) or "",
        "--max-safe-action",
        f"{float(args.safety_max_action):.12g}",
    ]
    extend_optional(command, "--expected-pose-frame", args.expected_pose_frame)
    extend_optional(command, "--expected-target-frame", args.expected_target_frame)
    extend_values(command, "--tcp-to-peg-tip-xyz", args.tcp_to_peg_tip_xyz)
    command.append("--require-nonstatic-pose" if args.require_nonstatic_pose else "--allow-static-pose")
    command.append("--require-nonstatic-target" if args.require_nonstatic_target else "--allow-static-target")
    if args.allow_action_limited:
        command.append("--allow-action-limited")
    if args.allow_workspace_limited:
        command.append("--allow-workspace-limited")
    if args.fail_on_warn:
        command.append("--fail-on-warn")
    return command


def load_checker_payload(path: Path) -> dict[str, Any] | None:
    resolved_path = repo_path(path)
    if not resolved_path.exists():
        return None
    return json.loads(resolved_path.read_text(encoding="utf-8"))


def render_summary(
    *,
    args: argparse.Namespace,
    dryrun_command: list[str],
    dryrun_result: subprocess.CompletedProcess[str],
    check_command: list[str] | None,
    check_result: subprocess.CompletedProcess[str] | None,
    checker_payload: dict[str, Any] | None,
) -> str:
    dryrun_ok = dryrun_result.returncode == 0
    check_ok = check_result is not None and check_result.returncode == 0
    verdict = checker_payload.get("verdict", "SKIPPED") if checker_payload is not None else "SKIPPED"
    overall = "PASS" if dryrun_ok and check_ok and verdict == "PASS" else "FAIL"
    if dryrun_ok and check_result is not None and verdict == "WARN" and not args.fail_on_warn:
        overall = "WARN"

    metrics = checker_payload.get("metrics", {}) if checker_payload is not None else {}
    issues = checker_payload.get("issues", []) if checker_payload is not None else []

    lines = [
        "# Real Dry-run Preflight Summary",
        "",
        f"- Overall: **{overall}**",
        f"- Dry-run return code: `{dryrun_result.returncode}`",
        f"- Checker return code: `{check_result.returncode if check_result is not None else 'not_run'}`",
        f"- Checker verdict: **{verdict}**",
        f"- Trace output: `{args.trace_output}`",
        f"- Checker report: `{args.check_output_md}`",
        "",
        "## Commands",
        "",
        "Dry-run:",
        "",
        "```powershell",
        command_text(dryrun_command),
        "```",
        "",
    ]
    if check_command is not None:
        lines.extend(
            [
                "Checker:",
                "",
                "```powershell",
                command_text(check_command),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Key Metrics",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
        ]
    )
    for key in (
        "rows",
        "episodes",
        "safe_action_max_abs_component",
        "safe_action_max_norm",
        "workspace_limited_rows",
        "action_limited_rows",
        "guard_active_rows",
        "guard_activated_rows",
        "first_guard_z_above_target",
        "tcp_to_peg_tip_max_error",
    ):
        if key in metrics:
            lines.append(f"| `{key}` | {metrics[key]} |")

    lines.extend(
        [
            "",
            "## Issues",
            "",
            "| Severity | Code | Count | Message |",
            "| --- | --- | ---: | --- |",
        ]
    )
    if not issues:
        lines.append("| INFO | `no_issues` | 0 | No checker issues detected. |")
    else:
        for issue in issues:
            lines.append(
                "| {severity} | `{code}` | {count} | {message} |".format(
                    severity=issue.get("severity", ""),
                    code=issue.get("code", ""),
                    count=issue.get("count", ""),
                    message=issue.get("message", ""),
                )
            )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    check_json = args.check_output_json
    if check_json is None:
        check_json = args.check_output_md.with_suffix(".json")

    dryrun_command = build_dryrun_command(args)
    dryrun_result = run_command(dryrun_command)

    check_command = None
    check_result = None
    checker_payload = None
    if dryrun_result.returncode == 0:
        check_command = build_check_command(args, check_json)
        check_result = run_command(check_command)
        checker_payload = load_checker_payload(check_json)

    summary_path = repo_path(args.summary_md)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        render_summary(
            args=args,
            dryrun_command=dryrun_command,
            dryrun_result=dryrun_result,
            check_command=check_command,
            check_result=check_result,
            checker_payload=checker_payload,
        ),
        encoding="utf-8",
    )
    print(f"saved preflight summary to {args.summary_md}")

    if dryrun_result.returncode != 0:
        sys.exit(dryrun_result.returncode)
    if check_result is not None and check_result.returncode != 0:
        sys.exit(check_result.returncode)


if __name__ == "__main__":
    main()
