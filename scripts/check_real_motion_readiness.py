from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}
DEFAULT_POLICY_MODEL = (
    "checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_"
    "staged_crop_full_light_replay_750k_oracle_e4"
)


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    count: int = 1
    details: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether a real capture bundle is ready for the first "
            "low-speed real-robot motion test. This script only reads files."
        )
    )
    parser.add_argument(
        "--bundle-summary-json",
        type=Path,
        default=Path("results/real_capture_bundle_summary.json"),
    )
    parser.add_argument("--output-md", type=Path, default=Path("results/real_motion_readiness_check.md"))
    parser.add_argument("--output-json", type=Path, default=Path("results/real_motion_readiness_check.json"))
    parser.add_argument("--expected-pose-frame", default="robot_base")
    parser.add_argument("--expected-target-source", default="fixture_calibration")
    parser.add_argument("--expected-guard-blend", type=float, default=0.75)
    parser.add_argument("--min-camera-frames", type=int, default=10)
    parser.add_argument("--min-tcp-samples", type=int, default=10)
    parser.add_argument("--min-dryrun-rows", type=int, default=2)
    parser.add_argument("--max-safe-action", type=float, default=0.002)
    parser.add_argument("--policy-model-substring", default=DEFAULT_POLICY_MODEL)
    parser.add_argument("--allow-synthetic", action="store_true")
    parser.add_argument("--allow-zero-policy", action="store_true")
    parser.add_argument("--allow-smoke-paths", action="store_true")
    parser.add_argument("--allow-missing-guard", action="store_true")
    parser.add_argument("--fail-on-warn", action="store_true")
    return parser.parse_args()


def repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    resolved = repo_path(path)
    with resolved.open("r", encoding="utf-8") as file:
        return json.load(file)


def add_issue(
    issues: list[Issue],
    severity: str,
    code: str,
    message: str,
    *,
    count: int = 1,
    details: str = "",
) -> None:
    issues.append(Issue(severity=severity, code=code, message=message, count=count, details=details))


def nested(payload: dict[str, Any] | None, *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def payload_verdict(payload: dict[str, Any] | None) -> str:
    verdict = nested(payload, "verdict")
    if verdict is None:
        return "MISSING"
    return str(verdict)


def command(payload: dict[str, Any] | None, *keys: str) -> list[str]:
    value = nested(payload, *keys, "command") if keys else nested(payload, "command")
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def command_has_flag(command_items: list[str], flag: str) -> bool:
    return any(item == flag or item.startswith(f"{flag}=") for item in command_items)


def command_value(command_items: list[str], flag: str, count: int = 1) -> list[str] | None:
    for index, item in enumerate(command_items):
        if item == flag:
            values = command_items[index + 1:index + 1 + count]
            return values if len(values) == count else None
        if count == 1 and item.startswith(f"{flag}="):
            return [item.split("=", 1)[1]]
    return None


def command_contains(command_items: list[str], text: str) -> bool:
    needle = text.lower()
    return any(needle in item.lower() for item in command_items)


def finite_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return math.nan
    return number if math.isfinite(number) else math.nan


def nonnegative_int(value: Any) -> int:
    number = finite_float(value)
    if not math.isfinite(number):
        return 0
    return max(0, int(number))


def issue_count(payload: dict[str, Any] | None, severity: str) -> int:
    issues = nested(payload, "issues")
    if not isinstance(issues, list):
        return 0
    return sum(1 for item in issues if isinstance(item, dict) and str(item.get("severity")) == severity)


def path_is_smoke(value: Any) -> bool:
    return "smoke" in str(value).replace("\\", "/").lower()


def check_returncode(
    issues: list[Issue],
    section: dict[str, Any] | None,
    section_name: str,
) -> None:
    if not isinstance(section, dict):
        add_issue(issues, "ERROR", f"{section_name}_missing", f"{section_name} section is missing.")
        return
    returncode = section.get("returncode")
    if returncode != 0:
        add_issue(
            issues,
            "ERROR",
            f"{section_name}_returncode",
            f"{section_name} did not exit cleanly.",
            details=str(returncode),
        )


def check_section_verdict(
    issues: list[Issue],
    section: dict[str, Any] | None,
    section_name: str,
) -> None:
    verdict = payload_verdict(section)
    if verdict == "FAIL":
        add_issue(issues, "ERROR", f"{section_name}_failed", f"{section_name} verdict is FAIL.")
    elif verdict == "WARN":
        add_issue(issues, "WARN", f"{section_name}_warn", f"{section_name} verdict is WARN.")
    elif verdict == "MISSING":
        add_issue(issues, "ERROR", f"{section_name}_missing_verdict", f"{section_name} verdict is missing.")
    elif verdict != "PASS":
        add_issue(
            issues,
            "ERROR",
            f"{section_name}_unknown_verdict",
            f"{section_name} verdict is not recognized.",
            details=verdict,
        )


def check_nested_issues(
    issues: list[Issue],
    section: dict[str, Any] | None,
    section_name: str,
) -> None:
    errors = issue_count(section, "ERROR")
    warnings = issue_count(section, "WARN")
    if errors:
        add_issue(
            issues,
            "ERROR",
            f"{section_name}_nested_errors",
            f"{section_name} reported nested errors.",
            count=errors,
        )
    if warnings:
        add_issue(
            issues,
            "WARN",
            f"{section_name}_nested_warnings",
            f"{section_name} reported nested warnings.",
            count=warnings,
        )


def check_top_level(args: argparse.Namespace, payload: dict[str, Any], issues: list[Issue]) -> None:
    check_section_verdict(issues, payload, "capture_bundle")
    if payload.get("verdict") != "PASS":
        add_issue(
            issues,
            "ERROR",
            "capture_bundle_not_pass",
            "Capture bundle must be PASS before first real motion.",
            details=str(payload.get("verdict")),
        )


def check_commands(args: argparse.Namespace, payload: dict[str, Any], issues: list[Issue]) -> None:
    all_commands = {
        "config_check": command(payload, "config_check"),
        "camera_record": command(payload, "camera_record"),
        "tcp_record": command(payload, "tcp_record"),
        "preflight": command(payload, "preflight"),
        "dryrun_preflight": command(payload, "preflight", "payload", "dryrun"),
    }
    synthetic_sections = [
        name for name, items in all_commands.items()
        if command_has_flag(items, "--synthetic-smoke")
    ]
    if synthetic_sections and not args.allow_synthetic:
        add_issue(
            issues,
            "ERROR",
            "synthetic_inputs",
            "Synthetic smoke inputs are not valid for real motion readiness.",
            count=len(synthetic_sections),
            details=", ".join(synthetic_sections),
        )
    elif synthetic_sections:
        add_issue(
            issues,
            "INFO",
            "synthetic_inputs_allowed",
            "Synthetic smoke inputs were explicitly allowed.",
            count=len(synthetic_sections),
            details=", ".join(synthetic_sections),
        )

    preflight_command = all_commands["preflight"]
    dryrun_command = all_commands["dryrun_preflight"]
    policy_commands = preflight_command + dryrun_command
    if command_has_flag(policy_commands, "--zero-policy") and not args.allow_zero_policy:
        add_issue(
            issues,
            "ERROR",
            "zero_policy",
            "Zero-policy dry-runs validate plumbing only; use a real model before robot motion.",
        )
    elif command_has_flag(policy_commands, "--zero-policy"):
        add_issue(issues, "INFO", "zero_policy_allowed", "Zero-policy dry-run was explicitly allowed.")

    if not policy_commands:
        return

    if args.policy_model_substring and not command_contains(policy_commands, args.policy_model_substring):
        if not args.allow_zero_policy or not command_has_flag(policy_commands, "--zero-policy"):
            add_issue(
                issues,
                "WARN",
                "recommended_model_not_seen",
                "The preflight command does not appear to use the current recommended model.",
                details=args.policy_model_substring,
            )

    if not args.allow_missing_guard:
        if not command_has_flag(policy_commands, "--guarded-policy"):
            add_issue(
                issues,
                "ERROR",
                "guarded_policy_missing",
                "Guarded insertion must be enabled for first real insertion tests.",
            )
        guard_blend = command_value(policy_commands, "--guard-blend")
        if guard_blend is None:
            add_issue(issues, "ERROR", "guard_blend_missing", "--guard-blend is missing.")
        else:
            blend = finite_float(guard_blend[0])
            if not math.isfinite(blend) or abs(blend - args.expected_guard_blend) > 1e-9:
                add_issue(
                    issues,
                    "WARN",
                    "guard_blend_unexpected",
                    "Guard blend differs from the current deployment recommendation.",
                    details=f"{blend:.9g} vs {args.expected_guard_blend:.9g}",
                )


def check_config(args: argparse.Namespace, payload: dict[str, Any], issues: list[Issue], metrics: dict[str, Any]) -> None:
    section = nested(payload, "config_check")
    check_returncode(issues, section, "config_check")
    config_payload = nested(section, "payload")
    if isinstance(config_payload, dict):
        check_section_verdict(issues, config_payload, "config_check")
        check_nested_issues(issues, config_payload, "config_check")
        config_metrics = nested(config_payload, "metrics")
        if isinstance(config_metrics, dict):
            metrics["config.pose_frame"] = config_metrics.get("pose_frame")
            metrics["config.target_source"] = config_metrics.get("target_source")
            metrics["config.target_frame"] = config_metrics.get("target_frame")
            metrics["config.target_id"] = config_metrics.get("target_id")
            metrics["config.tcp_to_peg_tip_norm"] = config_metrics.get("tcp_to_peg_tip_norm")
            if config_metrics.get("pose_frame") != args.expected_pose_frame:
                add_issue(
                    issues,
                    "ERROR",
                    "config_pose_frame",
                    "Config pose frame does not match the expected robot frame.",
                    details=str(config_metrics.get("pose_frame")),
                )
            if config_metrics.get("target_source") != args.expected_target_source:
                add_issue(
                    issues,
                    "ERROR",
                    "target_source",
                    "Target source should come from fixture calibration.",
                    details=str(config_metrics.get("target_source")),
                )
            if config_metrics.get("target_frame") != args.expected_pose_frame:
                add_issue(
                    issues,
                    "ERROR",
                    "target_frame",
                    "Target frame does not match the expected robot frame.",
                    details=str(config_metrics.get("target_frame")),
                )
            safe_action = finite_float(config_metrics.get("safety_max_action"))
            if math.isfinite(safe_action) and safe_action > args.max_safe_action + 1e-12:
                add_issue(
                    issues,
                    "ERROR",
                    "safety_max_action_too_large",
                    "Configured safety_max_action is above the readiness limit.",
                    details=f"{safe_action:.9g} > {args.max_safe_action:.9g}",
                )
            for key in ("config_path", "target_calibration_path"):
                if path_is_smoke(config_metrics.get(key)) and not args.allow_smoke_paths:
                    add_issue(
                        issues,
                        "ERROR",
                        f"{key}_is_smoke",
                        f"{key} points at a smoke fixture/config file.",
                        details=str(config_metrics.get(key)),
                    )
    else:
        add_issue(issues, "ERROR", "config_check_payload_missing", "Config check payload is missing.")


def check_recorders(args: argparse.Namespace, payload: dict[str, Any], issues: list[Issue], metrics: dict[str, Any]) -> None:
    camera = nested(payload, "camera_record")
    tcp = nested(payload, "tcp_record")
    check_returncode(issues, camera, "camera_record")
    check_returncode(issues, tcp, "tcp_record")
    camera_metrics = nested(camera, "metrics")
    tcp_metrics = nested(tcp, "metrics")
    session_id = str(payload.get("session_id", "")).strip()
    if isinstance(camera, dict) and camera.get("returncode") != 0:
        pass
    elif isinstance(camera_metrics, dict):
        camera_rows = nonnegative_int(camera_metrics.get("rows"))
        metrics["camera.rows"] = camera_rows
        metrics["camera.session_ids"] = camera_metrics.get("session_ids")
        if camera_rows < args.min_camera_frames:
            add_issue(
                issues,
                "ERROR",
                "camera_rows_too_low",
                "Not enough camera frames were recorded for readiness.",
                details=f"{camera_rows} < {args.min_camera_frames}",
            )
        if camera_rows > 0 and camera_metrics.get("timestamp_monotonic") is not True:
            add_issue(issues, "ERROR", "camera_timestamp_not_monotonic", "Camera timestamps are not monotonic.")
        if camera_rows > 0 and camera_metrics.get("wall_time_monotonic") is not True:
            add_issue(issues, "ERROR", "camera_wall_time_not_monotonic", "Camera wall times are not monotonic.")
        if camera_rows > 0 and session_id and str(camera_metrics.get("session_ids")) != session_id:
            add_issue(
                issues,
                "ERROR",
                "camera_session_mismatch",
                "Camera recorder session id does not match the capture bundle session.",
                details=str(camera_metrics.get("session_ids")),
            )
    else:
        add_issue(issues, "ERROR", "camera_metrics_missing", "Camera recorder metrics are missing.")

    if isinstance(tcp, dict) and tcp.get("returncode") != 0:
        pass
    elif isinstance(tcp_metrics, dict):
        tcp_rows = nonnegative_int(tcp_metrics.get("rows"))
        metrics["tcp.rows"] = tcp_rows
        metrics["tcp.session_ids"] = tcp_metrics.get("session_ids")
        if tcp_rows < args.min_tcp_samples:
            add_issue(
                issues,
                "ERROR",
                "tcp_rows_too_low",
                "Not enough TCP samples were recorded for readiness.",
                details=f"{tcp_rows} < {args.min_tcp_samples}",
            )
        if tcp_rows > 0 and tcp_metrics.get("timestamp_monotonic") is not True:
            add_issue(issues, "ERROR", "tcp_timestamp_not_monotonic", "TCP timestamps are not monotonic.")
        if tcp_rows > 0 and tcp_metrics.get("wall_time_monotonic") is not True:
            add_issue(issues, "ERROR", "tcp_wall_time_not_monotonic", "TCP wall times are not monotonic.")
        if tcp_rows > 0 and session_id and str(tcp_metrics.get("session_ids")) != session_id:
            add_issue(
                issues,
                "ERROR",
                "tcp_session_mismatch",
                "TCP recorder session id does not match the capture bundle session.",
                details=str(tcp_metrics.get("session_ids")),
            )
    else:
        add_issue(issues, "ERROR", "tcp_metrics_missing", "TCP recorder metrics are missing.")


def check_preflight(args: argparse.Namespace, payload: dict[str, Any], issues: list[Issue], metrics: dict[str, Any]) -> None:
    preflight = nested(payload, "preflight")
    check_returncode(issues, preflight, "preflight")
    preflight_payload = nested(preflight, "payload")
    if not isinstance(preflight_payload, dict):
        add_issue(issues, "ERROR", "preflight_payload_missing", "Combined preflight payload is missing.")
        return

    check_section_verdict(issues, preflight_payload, "preflight")
    camera_payload = nested(preflight_payload, "camera", "payload")
    dryrun_payload = nested(preflight_payload, "dryrun", "payload")
    if isinstance(camera_payload, dict):
        check_section_verdict(issues, camera_payload, "camera_preflight")
        check_nested_issues(issues, camera_payload, "camera_preflight")
        camera_metrics = nested(camera_payload, "metrics")
        if isinstance(camera_metrics, dict):
            frames_ok = nonnegative_int(camera_metrics.get("frames_ok"))
            metrics["camera_preflight.frames_ok"] = frames_ok
            metrics["camera_preflight.frame_diff_mean_min"] = camera_metrics.get("frame_diff_mean_min")
            if frames_ok < args.min_camera_frames:
                add_issue(
                    issues,
                    "ERROR",
                    "camera_preflight_frames_too_low",
                    "Camera preflight processed too few frames.",
                    details=f"{frames_ok} < {args.min_camera_frames}",
                )
            if nonnegative_int(camera_metrics.get("identical_adjacent_pairs")) > 0:
                add_issue(
                    issues,
                    "ERROR",
                    "camera_identical_adjacent_frames",
                    "Camera preflight found identical adjacent frames.",
                    details=str(camera_metrics.get("identical_adjacent_pairs")),
                )
    else:
        add_issue(issues, "ERROR", "camera_preflight_payload_missing", "Camera preflight payload is missing.")

    if isinstance(dryrun_payload, dict):
        check_section_verdict(issues, dryrun_payload, "dryrun_preflight")
        check_nested_issues(issues, dryrun_payload, "dryrun_preflight")
        dryrun_metrics = nested(dryrun_payload, "metrics")
        if isinstance(dryrun_metrics, dict):
            rows = nonnegative_int(dryrun_metrics.get("rows"))
            metrics["dryrun.rows"] = rows
            metrics["dryrun.pose_frames"] = dryrun_metrics.get("pose_frames")
            metrics["dryrun.pose_sources"] = dryrun_metrics.get("pose_sources")
            metrics["dryrun.target_sources"] = dryrun_metrics.get("target_sources")
            metrics["dryrun.guard_enabled_rows"] = dryrun_metrics.get("guard_enabled_rows")
            metrics["dryrun.guard_active_rows"] = dryrun_metrics.get("guard_active_rows")
            metrics["dryrun.safe_action_max_abs_component"] = dryrun_metrics.get("safe_action_max_abs_component")
            if rows < args.min_dryrun_rows:
                add_issue(
                    issues,
                    "ERROR",
                    "dryrun_rows_too_low",
                    "Dry-run trace has too few rows for readiness.",
                    details=f"{rows} < {args.min_dryrun_rows}",
                )
            if str(dryrun_metrics.get("pose_frames")) != args.expected_pose_frame:
                add_issue(
                    issues,
                    "ERROR",
                    "dryrun_pose_frame",
                    "Dry-run pose frame does not match expected robot frame.",
                    details=str(dryrun_metrics.get("pose_frames")),
                )
            if str(dryrun_metrics.get("target_sources")) != args.expected_target_source:
                add_issue(
                    issues,
                    "ERROR",
                    "dryrun_target_source",
                    "Dry-run target source should be fixture calibration.",
                    details=str(dryrun_metrics.get("target_sources")),
                )
            if nonnegative_int(dryrun_metrics.get("action_limited_rows")) > 0:
                add_issue(
                    issues,
                    "ERROR",
                    "dryrun_action_limited",
                    "Dry-run action limiter activated; inspect policy scale before motion.",
                    details=str(dryrun_metrics.get("action_limited_rows")),
                )
            if nonnegative_int(dryrun_metrics.get("workspace_limited_rows")) > 0:
                add_issue(
                    issues,
                    "ERROR",
                    "dryrun_workspace_limited",
                    "Workspace limiter activated; inspect target/workspace before motion.",
                    details=str(dryrun_metrics.get("workspace_limited_rows")),
                )
            safe_abs = finite_float(dryrun_metrics.get("safe_action_max_abs_component"))
            if math.isfinite(safe_abs) and safe_abs > args.max_safe_action + 1e-12:
                add_issue(
                    issues,
                    "ERROR",
                    "dryrun_safe_action_too_large",
                    "Dry-run safe action exceeds readiness limit.",
                    details=f"{safe_abs:.9g} > {args.max_safe_action:.9g}",
                )
            if not args.allow_missing_guard and nonnegative_int(dryrun_metrics.get("guard_enabled_rows")) <= 0:
                add_issue(
                    issues,
                    "ERROR",
                    "dryrun_guard_not_enabled",
                    "Dry-run trace does not show guarded policy enabled.",
                )
    else:
        add_issue(issues, "ERROR", "dryrun_preflight_payload_missing", "Dry-run preflight payload is missing.")


def verdict_from_issues(issues: list[Issue], fail_on_warn: bool) -> str:
    severities = {issue.severity for issue in issues}
    if "ERROR" in severities:
        return "FAIL"
    if "WARN" in severities:
        return "FAIL" if fail_on_warn else "WARN"
    return "PASS"


def render_md(args: argparse.Namespace, verdict: str, metrics: dict[str, Any], issues: list[Issue]) -> str:
    lines = [
        "# Real Motion Readiness Check",
        "",
        f"- Verdict: **{verdict}**",
        f"- Bundle summary: `{args.bundle_summary_json}`",
        f"- Expected pose frame: `{args.expected_pose_frame}`",
        f"- Expected target source: `{args.expected_target_source}`",
        f"- Minimum camera frames: `{args.min_camera_frames}`",
        f"- Minimum TCP samples: `{args.min_tcp_samples}`",
        f"- Minimum dry-run rows: `{args.min_dryrun_rows}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in sorted(metrics):
        lines.append(f"| `{key}` | {metrics[key]} |")
    lines.extend(["", "## Issues", "", "| Severity | Code | Count | Details |", "| --- | --- | ---: | --- |"])
    if not issues:
        lines.append("| INFO | none | 0 | No issues found. |")
    else:
        for issue in sorted(issues, key=lambda item: (SEVERITY_ORDER.get(item.severity, 99), item.code)):
            detail = issue.details or issue.message
            lines.append(f"| {issue.severity} | `{issue.code}` | {issue.count} | {detail} |")
    lines.append("")
    return "\n".join(lines)


def write_outputs(args: argparse.Namespace, verdict: str, metrics: dict[str, Any], issues: list[Issue]) -> None:
    payload = {
        "verdict": verdict,
        "bundle_summary_json": str(args.bundle_summary_json),
        "metrics": metrics,
        "issues": [asdict(issue) for issue in issues],
    }
    output_json = repo_path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md = repo_path(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_md(args, verdict, metrics, issues), encoding="utf-8")


def main() -> None:
    args = parse_args()
    payload = load_json(args.bundle_summary_json)
    issues: list[Issue] = []
    metrics: dict[str, Any] = {
        "session_id": payload.get("session_id", ""),
        "capture_bundle.verdict": payload.get("verdict", ""),
    }
    check_top_level(args, payload, issues)
    check_commands(args, payload, issues)
    check_config(args, payload, issues, metrics)
    check_recorders(args, payload, issues, metrics)
    check_preflight(args, payload, issues, metrics)
    verdict = verdict_from_issues(issues, args.fail_on_warn)
    write_outputs(args, verdict, metrics, issues)
    print(f"verdict={verdict}")
    print(f"saved_summary_to={args.output_md}")
    print(f"saved_json_to={args.output_json}")
    if verdict == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
