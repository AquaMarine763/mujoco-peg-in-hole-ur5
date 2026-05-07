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
            "Run the real-camera preflight, then run the real policy dry-run "
            "preflight on the same image frames plus real pose/target inputs."
        )
    )
    parser.add_argument("--image-input", type=Path, required=True, help="Raw camera frame file or directory.")

    parser.add_argument("--camera-output-dir", type=Path, default=Path("results/real_camera_policy_preflight_frames"))
    parser.add_argument("--camera-stats-output", type=Path, default=Path("results/real_camera_policy_preflight_stats.csv"))
    parser.add_argument(
        "--camera-summary-md",
        type=Path,
        default=Path("results/real_camera_policy_preflight_camera_summary.md"),
    )
    parser.add_argument(
        "--camera-output-json",
        type=Path,
        default=Path("results/real_camera_policy_preflight_camera_summary.json"),
    )
    parser.add_argument("--camera-width", type=int, default=100)
    parser.add_argument("--camera-height", type=int, default=100)
    parser.add_argument("--camera-crop-xywh", nargs=4, type=int, default=None)
    parser.add_argument("--camera-rotate-k", type=int, default=0)
    parser.add_argument("--camera-flip-horizontal", action="store_true")
    parser.add_argument("--camera-flip-vertical", action="store_true")
    parser.add_argument("--camera-max-frames", type=int, default=20)
    parser.add_argument("--camera-min-frames", type=int, default=1)
    parser.add_argument("--camera-min-processed-mean", type=float, default=2.0)
    parser.add_argument("--camera-max-processed-mean", type=float, default=253.0)
    parser.add_argument("--camera-min-processed-std", type=float, default=2.0)
    parser.add_argument("--camera-max-zero-fraction", type=float, default=0.98)
    parser.add_argument("--camera-max-255-fraction", type=float, default=0.98)
    parser.add_argument("--camera-min-frame-diff-mean", type=float, default=0.0)
    parser.add_argument("--camera-allow-identical-frames", action="store_true")

    parser.add_argument("--config", type=Path, default=Path("configs/real_ur5_dryrun.yaml"))
    parser.add_argument("--agent", choices=["sac", "ppo", "a2c"], default="sac")
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--zero-policy", action="store_true")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--seed", type=int, default=130_000)
    parser.add_argument("--pose-trace", type=Path, default=None)
    parser.add_argument("--tcp-pose-trace", type=Path, default=None)
    parser.add_argument("--target-calibration", type=Path, default=None)
    parser.add_argument("--pose-frame", default=None)
    parser.add_argument("--tcp-to-peg-tip-xyz", nargs=3, type=float, default=None)
    parser.add_argument("--control-frequency-hz", type=float, default=None)
    parser.add_argument("--safety-max-action", type=float, default=0.002)
    parser.add_argument("--safety-action-filter-alpha", type=float, default=None)
    parser.add_argument("--safety-workspace-low", nargs=3, type=float, default=None)
    parser.add_argument("--safety-workspace-high", nargs=3, type=float, default=None)
    parser.add_argument(
        "--dryrun-trace-output",
        type=Path,
        default=Path("results/real_policy_dryrun_camera_policy_preflight_trace.csv"),
    )
    parser.add_argument(
        "--dryrun-check-output-md",
        type=Path,
        default=Path("results/real_dryrun_camera_policy_preflight_check.md"),
    )
    parser.add_argument(
        "--dryrun-check-output-json",
        type=Path,
        default=Path("results/real_dryrun_camera_policy_preflight_check.json"),
    )
    parser.add_argument(
        "--dryrun-summary-md",
        type=Path,
        default=Path("results/real_dryrun_camera_policy_preflight_summary.md"),
    )

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
    parser.add_argument("--guard-start-z", type=float, default=0.100)
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
    parser.add_argument("--summary-md", type=Path, default=Path("results/real_camera_policy_preflight_summary.md"))
    parser.add_argument("--output-json", type=Path, default=Path("results/real_camera_policy_preflight_summary.json"))
    return parser.parse_args()


def path_arg(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(path)


def repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return REPO_ROOT / path


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


def extend_path_arg(command: list[str], flag: str, path: Path | None) -> None:
    if path is not None:
        command.extend([flag, path_arg(path) or ""])


def extend_optional(command: list[str], flag: str, value: Any) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def extend_values(command: list[str], flag: str, values: list[float] | tuple[float, ...] | None) -> None:
    if values is not None:
        command.append(flag)
        command.extend(f"{float(value):.12g}" for value in values)


def build_camera_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "scripts/check_real_camera_preflight.py",
        "--input",
        path_arg(args.image_input) or "",
        "--output-dir",
        path_arg(args.camera_output_dir) or "",
        "--stats-output",
        path_arg(args.camera_stats_output) or "",
        "--summary-md",
        path_arg(args.camera_summary_md) or "",
        "--output-json",
        path_arg(args.camera_output_json) or "",
        "--width",
        str(args.camera_width),
        "--height",
        str(args.camera_height),
        "--rotate-k",
        str(args.camera_rotate_k),
        "--max-frames",
        str(args.camera_max_frames),
        "--min-frames",
        str(args.camera_min_frames),
        "--min-processed-mean",
        f"{args.camera_min_processed_mean:.12g}",
        "--max-processed-mean",
        f"{args.camera_max_processed_mean:.12g}",
        "--min-processed-std",
        f"{args.camera_min_processed_std:.12g}",
        "--max-zero-fraction",
        f"{args.camera_max_zero_fraction:.12g}",
        "--max-255-fraction",
        f"{args.camera_max_255_fraction:.12g}",
        "--min-frame-diff-mean",
        f"{args.camera_min_frame_diff_mean:.12g}",
    ]
    extend_values(command, "--crop-xywh", args.camera_crop_xywh)
    if args.camera_flip_horizontal:
        command.append("--flip-horizontal")
    if args.camera_flip_vertical:
        command.append("--flip-vertical")
    if args.camera_allow_identical_frames:
        command.append("--allow-identical-frames")
    if args.fail_on_warn:
        command.append("--fail-on-warn")
    return command


def build_dryrun_command(args: argparse.Namespace) -> list[str]:
    if not args.zero_policy and args.model is None:
        raise ValueError("Provide --model or use --zero-policy.")
    image_input = repo_path(args.image_input)
    if not image_input.exists():
        raise FileNotFoundError(image_input)

    command = [
        sys.executable,
        "scripts/run_real_dryrun_preflight.py",
        "--config",
        path_arg(args.config) or "",
        "--agent",
        args.agent,
        "--episodes",
        str(args.episodes),
        "--seed",
        str(args.seed),
        "--device",
        args.device,
        "--safety-max-action",
        f"{float(args.safety_max_action):.12g}",
        "--trace-output",
        path_arg(args.dryrun_trace_output) or "",
        "--check-output-md",
        path_arg(args.dryrun_check_output_md) or "",
        "--check-output-json",
        path_arg(args.dryrun_check_output_json) or "",
        "--summary-md",
        path_arg(args.dryrun_summary_md) or "",
    ]
    if image_input.is_dir():
        command.extend(["--image-dir", path_arg(args.image_input) or ""])
    else:
        command.extend(["--image-path", path_arg(args.image_input) or ""])
    if args.zero_policy:
        command.append("--zero-policy")
    else:
        extend_path_arg(command, "--model", args.model)
    if args.stochastic:
        command.append("--stochastic")

    extend_optional(command, "--max-steps", args.max_steps)
    extend_path_arg(command, "--pose-trace", args.pose_trace)
    extend_path_arg(command, "--tcp-pose-trace", args.tcp_pose_trace)
    extend_path_arg(command, "--target-calibration", args.target_calibration)
    extend_optional(command, "--pose-frame", args.pose_frame)
    extend_values(command, "--tcp-to-peg-tip-xyz", args.tcp_to_peg_tip_xyz)
    extend_optional(command, "--control-frequency-hz", args.control_frequency_hz)
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

    extend_optional(command, "--expected-pose-frame", args.expected_pose_frame)
    extend_optional(command, "--expected-target-frame", args.expected_target_frame)
    command.append("--require-nonstatic-pose" if args.require_nonstatic_pose else "--allow-static-pose")
    command.append("--require-nonstatic-target" if args.require_nonstatic_target else "--allow-static-target")
    if args.allow_action_limited:
        command.append("--allow-action-limited")
    if args.allow_workspace_limited:
        command.append("--allow-workspace-limited")
    if args.fail_on_warn:
        command.append("--fail-on-warn")
    return command


def load_json(path: Path) -> dict[str, Any] | None:
    resolved_path = repo_path(path)
    if not resolved_path.exists():
        return None
    return json.loads(resolved_path.read_text(encoding="utf-8"))


def payload_verdict(payload: dict[str, Any] | None, returncode: int | None) -> str:
    if payload is not None and "verdict" in payload:
        return str(payload["verdict"])
    if returncode is None:
        return "SKIPPED"
    return "PASS" if returncode == 0 else "FAIL"


def overall_verdict(camera_verdict: str, dryrun_verdict: str, camera_returncode: int, dryrun_returncode: int | None) -> str:
    verdicts = [camera_verdict, dryrun_verdict]
    if camera_returncode != 0 or (dryrun_returncode is not None and dryrun_returncode != 0):
        return "FAIL"
    if "FAIL" in verdicts:
        return "FAIL"
    if "WARN" in verdicts:
        return "WARN"
    if "SKIPPED" in verdicts:
        return "FAIL"
    return "PASS"


def issue_rows(source: str, payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if payload is None:
        return []
    rows = []
    for issue in payload.get("issues", []):
        rows.append(
            {
                "source": source,
                "severity": issue.get("severity", ""),
                "code": issue.get("code", ""),
                "count": issue.get("count", ""),
                "message": issue.get("message", issue.get("details", "")),
            }
        )
    return rows


def metric_value(payload: dict[str, Any] | None, key: str) -> Any:
    if payload is None:
        return None
    return payload.get("metrics", {}).get(key)


def render_summary(
    *,
    args: argparse.Namespace,
    camera_command: list[str],
    camera_result: subprocess.CompletedProcess[str],
    camera_payload: dict[str, Any] | None,
    dryrun_command: list[str] | None,
    dryrun_result: subprocess.CompletedProcess[str] | None,
    dryrun_payload: dict[str, Any] | None,
    result: str,
) -> str:
    camera_verdict = payload_verdict(camera_payload, camera_result.returncode)
    dryrun_verdict = payload_verdict(
        dryrun_payload,
        None if dryrun_result is None else dryrun_result.returncode,
    )
    lines = [
        "# Real Camera Policy Preflight Summary",
        "",
        f"- Overall: **{result}**",
        f"- Camera verdict: **{camera_verdict}**",
        f"- Dry-run verdict: **{dryrun_verdict}**",
        f"- Image input: `{args.image_input}`",
        f"- Camera summary: `{args.camera_summary_md}`",
        f"- Dry-run summary: `{args.dryrun_summary_md}`",
        f"- Dry-run trace: `{args.dryrun_trace_output}`",
        "",
        "## Commands",
        "",
        "Camera preflight:",
        "",
        "```powershell",
        command_text(camera_command),
        "```",
        "",
    ]
    if dryrun_command is not None:
        lines.extend(
            [
                "Dry-run preflight:",
                "",
                "```powershell",
                command_text(dryrun_command),
                "```",
                "",
            ]
        )

    metric_rows = [
        ("camera.frames_ok", metric_value(camera_payload, "frames_ok")),
        ("camera.frames_failed", metric_value(camera_payload, "frames_failed")),
        ("camera.processed_mean_avg", metric_value(camera_payload, "processed_mean_avg")),
        ("camera.processed_std_avg", metric_value(camera_payload, "processed_std_avg")),
        ("camera.frame_diff_mean_avg", metric_value(camera_payload, "frame_diff_mean_avg")),
        ("dryrun.rows", metric_value(dryrun_payload, "rows")),
        ("dryrun.safe_action_max_abs_component", metric_value(dryrun_payload, "safe_action_max_abs_component")),
        ("dryrun.workspace_limited_rows", metric_value(dryrun_payload, "workspace_limited_rows")),
        ("dryrun.guard_active_rows", metric_value(dryrun_payload, "guard_active_rows")),
        ("dryrun.tcp_to_peg_tip_max_error", metric_value(dryrun_payload, "tcp_to_peg_tip_max_error")),
    ]
    lines.extend(
        [
            "## Key Metrics",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
        ]
    )
    for key, value in metric_rows:
        if value is not None:
            lines.append(f"| `{key}` | {value} |")

    issues = issue_rows("camera", camera_payload) + issue_rows("dryrun", dryrun_payload)
    lines.extend(
        [
            "",
            "## Issues",
            "",
            "| Source | Severity | Code | Count | Message |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    if not issues:
        lines.append("| all | INFO | `no_issues` | 0 | No issues detected. |")
    else:
        for issue in issues:
            lines.append(
                "| {source} | {severity} | `{code}` | {count} | {message} |".format(
                    **issue
                )
            )
    lines.append("")
    return "\n".join(lines)


def write_json_summary(
    *,
    path: Path,
    result: str,
    camera_command: list[str],
    camera_result: subprocess.CompletedProcess[str],
    camera_payload: dict[str, Any] | None,
    dryrun_command: list[str] | None,
    dryrun_result: subprocess.CompletedProcess[str] | None,
    dryrun_payload: dict[str, Any] | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "verdict": result,
        "camera": {
            "returncode": camera_result.returncode,
            "command": camera_command,
            "payload": camera_payload,
        },
        "dryrun": {
            "returncode": None if dryrun_result is None else dryrun_result.returncode,
            "command": dryrun_command,
            "payload": dryrun_payload,
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    camera_command = build_camera_command(args)
    camera_result = run_command(camera_command)
    camera_payload = load_json(args.camera_output_json)

    dryrun_command = None
    dryrun_result = None
    dryrun_payload = None
    if camera_result.returncode == 0:
        dryrun_command = build_dryrun_command(args)
        dryrun_result = run_command(dryrun_command)
        dryrun_payload = load_json(args.dryrun_check_output_json)

    camera_verdict = payload_verdict(camera_payload, camera_result.returncode)
    dryrun_verdict = payload_verdict(
        dryrun_payload,
        None if dryrun_result is None else dryrun_result.returncode,
    )
    result = overall_verdict(
        camera_verdict,
        dryrun_verdict,
        camera_result.returncode,
        None if dryrun_result is None else dryrun_result.returncode,
    )

    summary_path = repo_path(args.summary_md)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        render_summary(
            args=args,
            camera_command=camera_command,
            camera_result=camera_result,
            camera_payload=camera_payload,
            dryrun_command=dryrun_command,
            dryrun_result=dryrun_result,
            dryrun_payload=dryrun_payload,
            result=result,
        ),
        encoding="utf-8",
    )
    write_json_summary(
        path=repo_path(args.output_json),
        result=result,
        camera_command=camera_command,
        camera_result=camera_result,
        camera_payload=camera_payload,
        dryrun_command=dryrun_command,
        dryrun_result=dryrun_result,
        dryrun_payload=dryrun_payload,
    )
    print(f"saved combined summary to {args.summary_md}")
    print(f"verdict={result}")
    if result == "FAIL":
        exit_code = camera_result.returncode
        if exit_code == 0 and dryrun_result is not None:
            exit_code = dryrun_result.returncode
        sys.exit(exit_code or 1)


if __name__ == "__main__":
    main()
