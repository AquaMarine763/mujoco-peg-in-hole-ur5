from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[1]
RESERVED_PREFLIGHT_FLAGS = {"--image-input", "--tcp-pose-trace"}


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description=(
            "Record a read-only real camera + UR TCP capture bundle, then run "
            "the combined real camera policy preflight. Unrecognized arguments "
            "are forwarded to scripts/run_real_camera_policy_preflight.py."
        ),
        allow_abbrev=False,
    )
    parser.add_argument("--config", type=Path, default=Path("configs/real_ur5_dryrun.yaml"))
    parser.add_argument("--skip-config-check", action="store_true")
    parser.add_argument("--config-check-fail-on-warn", action="store_true")
    parser.add_argument(
        "--config-check-output-md",
        type=Path,
        default=Path("results/real_capture_bundle_config_check.md"),
    )
    parser.add_argument(
        "--config-check-output-json",
        type=Path,
        default=Path("results/real_capture_bundle_config_check.json"),
    )
    parser.add_argument("--record-camera-source", default=None)
    parser.add_argument("--record-camera-device-index", type=int, default=0)
    parser.add_argument("--record-camera-output-dir", type=Path, default=Path("results/real_capture_bundle_camera_frames"))
    parser.add_argument(
        "--record-camera-stats-output",
        type=Path,
        default=Path("results/real_capture_bundle_camera_stats.csv"),
    )
    parser.add_argument(
        "--record-camera-summary-md",
        type=Path,
        default=Path("results/real_capture_bundle_camera_summary.md"),
    )
    parser.add_argument("--record-camera-frames", type=int, default=20)
    parser.add_argument("--record-camera-frequency-hz", type=float, default=5.0)
    parser.add_argument("--record-camera-warmup-frames", type=int, default=10)
    parser.add_argument("--record-camera-width", type=int, default=None)
    parser.add_argument("--record-camera-height", type=int, default=None)
    parser.add_argument("--record-camera-prefix", default="camera_frame")
    parser.add_argument("--record-camera-synthetic-smoke", action="store_true")

    parser.add_argument("--record-tcp-host", default=None)
    parser.add_argument("--record-tcp-output", type=Path, default=Path("results/real_capture_bundle_tcp_pose_trace.csv"))
    parser.add_argument("--record-tcp-samples", type=int, default=100)
    parser.add_argument("--record-tcp-frequency-hz", type=float, default=20.0)
    parser.add_argument("--record-tcp-pose-frame", default="robot_base")
    parser.add_argument("--record-tcp-target-pos", nargs=3, type=float, default=(0.55, 0.05, 0.65))
    parser.add_argument("--record-tcp-no-target-columns", action="store_true")
    parser.add_argument("--record-tcp-synthetic-smoke", action="store_true")

    parser.add_argument(
        "--target-calibration",
        type=Path,
        default=None,
        help=(
            "Target calibration forwarded to the combined preflight. When set, "
            "the TCP recorder omits embedded target columns so this calibration is used."
        ),
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Capture session id written into both camera and TCP recorder outputs.",
    )
    parser.add_argument(
        "--preflight-summary-md",
        type=Path,
        default=Path("results/real_capture_bundle_preflight_summary.md"),
    )
    parser.add_argument(
        "--preflight-output-json",
        type=Path,
        default=Path("results/real_capture_bundle_preflight_summary.json"),
    )
    parser.add_argument("--summary-md", type=Path, default=Path("results/real_capture_bundle_summary.md"))
    parser.add_argument("--output-json", type=Path, default=Path("results/real_capture_bundle_summary.json"))
    return parser.parse_known_args()


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


def extend_optional(command: list[str], flag: str, value: Any) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def extend_values(command: list[str], flag: str, values: list[float] | tuple[float, ...] | None) -> None:
    if values is not None:
        command.append(flag)
        command.extend(f"{float(value):.12g}" for value in values)


def build_camera_record_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "scripts/record_real_camera_frames.py",
        "--output-dir",
        path_arg(args.record_camera_output_dir) or "",
        "--stats-output",
        path_arg(args.record_camera_stats_output) or "",
        "--summary-md",
        path_arg(args.record_camera_summary_md) or "",
        "--frames",
        str(args.record_camera_frames),
        "--frequency-hz",
        f"{float(args.record_camera_frequency_hz):.12g}",
        "--warmup-frames",
        str(args.record_camera_warmup_frames),
        "--prefix",
        args.record_camera_prefix,
        "--session-id",
        args.session_id,
    ]
    if args.record_camera_source is not None:
        command.extend(["--source", str(args.record_camera_source)])
    else:
        command.extend(["--device-index", str(args.record_camera_device_index)])
    extend_optional(command, "--camera-width", args.record_camera_width)
    extend_optional(command, "--camera-height", args.record_camera_height)
    if args.record_camera_synthetic_smoke:
        command.append("--synthetic-smoke")
    return command


def tcp_should_omit_target_columns(args: argparse.Namespace) -> bool:
    return bool(args.record_tcp_no_target_columns or args.target_calibration is not None)


def build_tcp_record_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "scripts/record_ur_rtde_tcp_pose_trace.py",
        "--output",
        path_arg(args.record_tcp_output) or "",
        "--samples",
        str(args.record_tcp_samples),
        "--frequency-hz",
        f"{float(args.record_tcp_frequency_hz):.12g}",
        "--pose-frame",
        args.record_tcp_pose_frame,
        "--session-id",
        args.session_id,
    ]
    extend_values(command, "--target-pos", args.record_tcp_target_pos)
    if args.record_tcp_host is not None:
        command.extend(["--host", str(args.record_tcp_host)])
    if args.record_tcp_synthetic_smoke:
        command.append("--synthetic-smoke")
    if tcp_should_omit_target_columns(args):
        command.append("--no-target-columns")
    return command


def argument_values(args: list[str], flag: str, count: int) -> list[str] | None:
    for index, item in enumerate(args):
        if item == flag:
            values = args[index + 1:index + 1 + count]
            return values if len(values) == count else None
        if count == 1 and item.startswith(f"{flag}="):
            return [item.split("=", 1)[1]]
    return None


def preflight_has_flag(args: list[str], flag: str) -> bool:
    return any(item == flag or item.startswith(f"{flag}=") for item in args)


def extend_argument_values(command: list[str], output_flag: str, values: list[str] | None) -> None:
    if values is not None:
        command.append(output_flag)
        command.extend(values)


def build_config_check_command(args: argparse.Namespace, preflight_args: list[str]) -> list[str]:
    command = [
        sys.executable,
        "scripts/check_real_deployment_config.py",
        "--config",
        path_arg(args.config) or "",
        "--output-md",
        path_arg(args.config_check_output_md) or "",
        "--output-json",
        path_arg(args.config_check_output_json) or "",
    ]
    if args.target_calibration is not None:
        command.extend(["--target-calibration", path_arg(args.target_calibration) or ""])

    model_values = argument_values(preflight_args, "--model", 1)
    if model_values is not None:
        command.extend(["--model", model_values[0]])
    elif not preflight_has_flag(preflight_args, "--zero-policy"):
        command.append("--require-model")

    extend_argument_values(command, "--tcp-to-peg-tip-xyz", argument_values(preflight_args, "--tcp-to-peg-tip-xyz", 3))
    safety_values = argument_values(preflight_args, "--safety-max-action", 1)
    if safety_values is not None:
        command.extend(["--max-safe-action", safety_values[0]])
    expected_pose_values = argument_values(preflight_args, "--expected-pose-frame", 1)
    if expected_pose_values is not None:
        command.extend(["--expected-pose-frame", expected_pose_values[0]])
    if args.config_check_fail_on_warn:
        command.append("--fail-on-warn")
    return command


def validate_args(args: argparse.Namespace, preflight_args: list[str]) -> None:
    if args.record_camera_frames <= 0:
        raise ValueError("--record-camera-frames must be positive.")
    if args.record_camera_frequency_hz <= 0.0:
        raise ValueError("--record-camera-frequency-hz must be positive.")
    if args.record_camera_warmup_frames < 0:
        raise ValueError("--record-camera-warmup-frames cannot be negative.")
    if args.record_tcp_samples <= 0:
        raise ValueError("--record-tcp-samples must be positive.")
    if args.record_tcp_frequency_hz <= 0.0:
        raise ValueError("--record-tcp-frequency-hz must be positive.")
    if args.record_tcp_host is None and not args.record_tcp_synthetic_smoke:
        raise ValueError("Provide --record-tcp-host or use --record-tcp-synthetic-smoke.")
    reserved = sorted(
        flag
        for flag in preflight_args
        if flag in RESERVED_PREFLIGHT_FLAGS
        or any(flag.startswith(f"{reserved_flag}=") for reserved_flag in RESERVED_PREFLIGHT_FLAGS)
    )
    if reserved:
        raise ValueError(
            "The capture bundle supplies these preflight inputs automatically: "
            + ", ".join(reserved)
        )


def launch_command(name: str, command: list[str]) -> subprocess.Popen[str]:
    print(f"\n[{name}] > {command_text(command)}")
    return subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def finish_command(name: str, command: list[str], process: subprocess.Popen[str]) -> CommandResult:
    stdout, stderr = process.communicate()
    if stdout:
        print(stdout, end="")
    if stderr:
        print(stderr, end="", file=sys.stderr)
    return CommandResult(
        name=name,
        command=command,
        returncode=int(process.returncode or 0),
        stdout=stdout or "",
        stderr=stderr or "",
    )


def run_command(name: str, command: list[str]) -> CommandResult:
    process = launch_command(name, command)
    return finish_command(name, command, process)


def skipped_result(name: str) -> CommandResult:
    return CommandResult(name=name, command=[], returncode=-1, stdout="", stderr="skipped")


def run_recorders(camera_command: list[str], tcp_command: list[str]) -> tuple[CommandResult, CommandResult]:
    camera_process = launch_command("camera_record", camera_command)
    tcp_process = launch_command("tcp_record", tcp_command)
    camera_result = finish_command("camera_record", camera_command, camera_process)
    tcp_result = finish_command("tcp_record", tcp_command, tcp_process)
    return camera_result, tcp_result


def build_preflight_command(args: argparse.Namespace, preflight_args: list[str]) -> list[str]:
    command = [
        sys.executable,
        "scripts/run_real_camera_policy_preflight.py",
        "--config",
        path_arg(args.config) or "",
        "--image-input",
        path_arg(args.record_camera_output_dir) or "",
        "--tcp-pose-trace",
        path_arg(args.record_tcp_output) or "",
        "--summary-md",
        path_arg(args.preflight_summary_md) or "",
        "--output-json",
        path_arg(args.preflight_output_json) or "",
    ]
    if args.target_calibration is not None:
        command.extend(["--target-calibration", path_arg(args.target_calibration) or ""])
    command.extend(preflight_args)
    return command


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    resolved = repo_path(path)
    if not resolved.exists():
        return []
    with resolved.open("r", newline="", encoding="utf-8-sig") as file:
        return [dict(row) for row in csv.DictReader(file)]


def make_session_id() -> str:
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"real_capture_{timestamp}_{uuid4().hex[:8]}"


def parse_float(value: Any) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return math.nan


def timestamp_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    timestamps = [parse_float(row.get("timestamp")) for row in rows]
    timestamps = [value for value in timestamps if math.isfinite(value)]
    metrics: dict[str, Any] = {"rows": len(rows), "timestamp_rows": len(timestamps)}
    session_ids = sorted({row.get("session_id", "").strip() for row in rows if row.get("session_id", "").strip()})
    if session_ids:
        metrics["session_ids"] = ", ".join(session_ids)
        metrics["session_id_count"] = len(session_ids)
    if timestamps:
        metrics["timestamp_monotonic"] = all(
            timestamps[index] > timestamps[index - 1]
            for index in range(1, len(timestamps))
        )
        metrics["timestamp_first"] = timestamps[0]
        metrics["timestamp_last"] = timestamps[-1]
        metrics["timestamp_span_s"] = timestamps[-1] - timestamps[0]
        if len(timestamps) > 1:
            intervals = [
                timestamps[index] - timestamps[index - 1]
                for index in range(1, len(timestamps))
            ]
            metrics["interval_avg_s"] = sum(intervals) / len(intervals)
            metrics["interval_min_s"] = min(intervals)
            metrics["interval_max_s"] = max(intervals)
    wall_times = [parse_float(row.get("wall_time_unix")) for row in rows]
    wall_times = [value for value in wall_times if math.isfinite(value)]
    if wall_times:
        metrics["wall_time_rows"] = len(wall_times)
        metrics["wall_time_monotonic"] = all(
            wall_times[index] > wall_times[index - 1]
            for index in range(1, len(wall_times))
        )
        metrics["wall_time_first_unix"] = wall_times[0]
        metrics["wall_time_last_unix"] = wall_times[-1]
        metrics["wall_time_span_s"] = wall_times[-1] - wall_times[0]
    return metrics


def load_json(path: Path) -> dict[str, Any] | None:
    resolved = repo_path(path)
    if not resolved.exists():
        return None
    return json.loads(resolved.read_text(encoding="utf-8"))


def clear_output_file(path: Path) -> None:
    resolved = repo_path(path)
    if resolved.exists() and resolved.is_file():
        resolved.unlink()


def payload_verdict(payload: dict[str, Any] | None, result: CommandResult | None) -> str:
    if payload is not None and "verdict" in payload:
        return str(payload["verdict"])
    if result is None:
        return "SKIPPED"
    if result.returncode < 0:
        return "SKIPPED"
    return "PASS" if result.returncode == 0 else "FAIL"


def overall_verdict(
    *,
    config_result: CommandResult | None,
    config_payload: dict[str, Any] | None,
    camera_result: CommandResult,
    tcp_result: CommandResult,
    preflight_result: CommandResult | None,
    preflight_payload: dict[str, Any] | None,
    camera_metrics: dict[str, Any],
    tcp_metrics: dict[str, Any],
) -> str:
    config_status = payload_verdict(config_payload, config_result)
    if config_result is not None and (config_result.returncode != 0 or config_status == "FAIL"):
        return "FAIL"
    has_warning = config_status == "WARN"
    if camera_result.returncode != 0 or tcp_result.returncode != 0:
        return "FAIL"
    if camera_metrics.get("timestamp_monotonic") is False:
        return "FAIL"
    if tcp_metrics.get("timestamp_monotonic") is False:
        return "FAIL"
    if camera_metrics.get("wall_time_monotonic") is False:
        return "FAIL"
    if tcp_metrics.get("wall_time_monotonic") is False:
        return "FAIL"
    camera_sessions = str(camera_metrics.get("session_ids", "")).strip()
    tcp_sessions = str(tcp_metrics.get("session_ids", "")).strip()
    if camera_sessions and tcp_sessions and camera_sessions != tcp_sessions:
        return "FAIL"
    if preflight_result is None:
        return "FAIL"
    verdict = payload_verdict(preflight_payload, preflight_result)
    if preflight_result.returncode != 0 or verdict == "FAIL":
        return "FAIL"
    if verdict == "WARN":
        has_warning = True
    if has_warning:
        return "WARN"
    return "PASS"


def format_value(value: Any) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.9g}"
    return str(value)


def metric_rows(prefix: str, metrics: dict[str, Any]) -> list[tuple[str, Any]]:
    return [(f"{prefix}.{key}", metrics[key]) for key in sorted(metrics)]


def append_command_section(lines: list[str], title: str, result: CommandResult | None) -> None:
    lines.extend([title, ""])
    if result is None or not result.command:
        lines.extend(["SKIPPED", ""])
        return
    lines.extend([
        "```powershell",
        command_text(result.command),
        "```",
        "",
    ])


def render_summary(
    *,
    args: argparse.Namespace,
    config_result: CommandResult | None,
    config_payload: dict[str, Any] | None,
    camera_result: CommandResult,
    tcp_result: CommandResult,
    preflight_result: CommandResult | None,
    preflight_payload: dict[str, Any] | None,
    camera_metrics: dict[str, Any],
    tcp_metrics: dict[str, Any],
    result: str,
) -> str:
    config_result_text = payload_verdict(config_payload, config_result)
    preflight_result_text = payload_verdict(preflight_payload, preflight_result)
    lines = [
        "# Real Capture Bundle Summary",
        "",
        f"- Overall: **{result}**",
        f"- Config check verdict: **{config_result_text}**",
        f"- Camera recorder return code: `{camera_result.returncode}`",
        f"- TCP recorder return code: `{tcp_result.returncode}`",
        f"- Combined preflight verdict: **{preflight_result_text}**",
        f"- Session id: `{args.session_id}`",
        f"- Camera frames: `{args.record_camera_output_dir}`",
        f"- Camera stats: `{args.record_camera_stats_output}`",
        f"- TCP trace: `{args.record_tcp_output}`",
        f"- Target calibration: `{args.target_calibration if args.target_calibration is not None else 'trace_or_config'}`",
        f"- TCP target columns: `{'omitted' if tcp_should_omit_target_columns(args) else 'included'}`",
        f"- Combined preflight summary: `{args.preflight_summary_md}`",
        "",
        "## Commands",
        "",
    ]
    append_command_section(lines, "Config check:", config_result)
    append_command_section(lines, "Camera recorder:", camera_result)
    append_command_section(lines, "TCP recorder:", tcp_result)
    append_command_section(lines, "Combined preflight:", preflight_result)
    lines.extend(["## Metrics", "", "| Metric | Value |", "| --- | ---: |"])
    for key, value in metric_rows("camera", camera_metrics) + metric_rows("tcp", tcp_metrics):
        lines.append(f"| `{key}` | {format_value(value)} |")
    if preflight_payload is not None:
        if config_payload is not None:
            lines.append(f"| `config_check.verdict` | {config_payload.get('verdict', '')} |")
        lines.append(f"| `preflight.verdict` | {preflight_payload.get('verdict', '')} |")
        camera_payload = preflight_payload.get("camera", {}).get("payload")
        dryrun_payload = preflight_payload.get("dryrun", {}).get("payload")
        if isinstance(camera_payload, dict):
            lines.append(f"| `preflight.camera_verdict` | {camera_payload.get('verdict', '')} |")
        if isinstance(dryrun_payload, dict):
            lines.append(f"| `preflight.dryrun_verdict` | {dryrun_payload.get('verdict', '')} |")
    lines.append("")
    return "\n".join(lines)


def write_json_summary(
    *,
    path: Path,
    result: str,
    session_id: str,
    config_result: CommandResult | None,
    config_payload: dict[str, Any] | None,
    camera_result: CommandResult,
    tcp_result: CommandResult,
    preflight_result: CommandResult | None,
    preflight_payload: dict[str, Any] | None,
    camera_metrics: dict[str, Any],
    tcp_metrics: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "verdict": result,
        "session_id": session_id,
        "config_check": (
            None
            if config_result is None
            else {
                "returncode": config_result.returncode,
                "command": config_result.command,
                "payload": config_payload,
            }
        ),
        "camera_record": {
            "returncode": camera_result.returncode,
            "command": camera_result.command,
            "metrics": camera_metrics,
        },
        "tcp_record": {
            "returncode": tcp_result.returncode,
            "command": tcp_result.command,
            "metrics": tcp_metrics,
        },
        "preflight": (
            None
            if preflight_result is None
            else {
                "returncode": preflight_result.returncode,
                "command": preflight_result.command,
                "payload": preflight_payload,
            }
        ),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args, preflight_args = parse_args()
    if args.session_id is None:
        args.session_id = make_session_id()
    validate_args(args, preflight_args)

    config_result = None
    config_payload = None
    if not args.skip_config_check:
        clear_output_file(args.config_check_output_json)
        config_command = build_config_check_command(args, preflight_args)
        config_result = run_command("config_check", config_command)
        config_payload = load_json(args.config_check_output_json)

    can_continue = config_result is None or (
        config_result.returncode == 0 and payload_verdict(config_payload, config_result) != "FAIL"
    )

    if can_continue:
        camera_command = build_camera_record_command(args)
        tcp_command = build_tcp_record_command(args)
        clear_output_file(args.record_camera_stats_output)
        clear_output_file(args.record_tcp_output)
        camera_result, tcp_result = run_recorders(camera_command, tcp_command)
    else:
        camera_result = skipped_result("camera_record")
        tcp_result = skipped_result("tcp_record")

    preflight_result = None
    preflight_payload = None
    if camera_result.returncode == 0 and tcp_result.returncode == 0:
        preflight_command = build_preflight_command(args, preflight_args)
        clear_output_file(args.preflight_output_json)
        preflight_result = run_command("combined_preflight", preflight_command)
        preflight_payload = load_json(args.preflight_output_json)

    camera_metrics = timestamp_metrics(load_csv_rows(args.record_camera_stats_output)) if camera_result.command else {}
    tcp_metrics = timestamp_metrics(load_csv_rows(args.record_tcp_output)) if tcp_result.command else {}
    result = overall_verdict(
        config_result=config_result,
        config_payload=config_payload,
        camera_result=camera_result,
        tcp_result=tcp_result,
        preflight_result=preflight_result,
        preflight_payload=preflight_payload,
        camera_metrics=camera_metrics,
        tcp_metrics=tcp_metrics,
    )

    summary_path = repo_path(args.summary_md)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        render_summary(
            args=args,
            config_result=config_result,
            config_payload=config_payload,
            camera_result=camera_result,
            tcp_result=tcp_result,
            preflight_result=preflight_result,
            preflight_payload=preflight_payload,
            camera_metrics=camera_metrics,
            tcp_metrics=tcp_metrics,
            result=result,
        ),
        encoding="utf-8",
    )
    write_json_summary(
        path=repo_path(args.output_json),
        result=result,
        session_id=args.session_id,
        config_result=config_result,
        config_payload=config_payload,
        camera_result=camera_result,
        tcp_result=tcp_result,
        preflight_result=preflight_result,
        preflight_payload=preflight_payload,
        camera_metrics=camera_metrics,
        tcp_metrics=tcp_metrics,
    )
    print(f"saved capture bundle summary to {args.summary_md}")
    print(f"verdict={result}")
    if result == "FAIL":
        config_status = payload_verdict(config_payload, config_result)
        if config_result is not None and (config_result.returncode != 0 or config_status == "FAIL"):
            sys.exit(config_result.returncode if config_result.returncode != 0 else 1)
        if camera_result.returncode != 0:
            sys.exit(camera_result.returncode)
        if tcp_result.returncode != 0:
            sys.exit(tcp_result.returncode)
        if preflight_result is not None:
            sys.exit(preflight_result.returncode or 1)
        sys.exit(1)


if __name__ == "__main__":
    main()
