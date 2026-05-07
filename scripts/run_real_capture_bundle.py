from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
    ]
    extend_values(command, "--target-pos", args.record_tcp_target_pos)
    if args.record_tcp_host is not None:
        command.extend(["--host", str(args.record_tcp_host)])
    if args.record_tcp_synthetic_smoke:
        command.append("--synthetic-smoke")
    if tcp_should_omit_target_columns(args):
        command.append("--no-target-columns")
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


def parse_float(value: Any) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return math.nan


def timestamp_metrics(rows: list[dict[str, str]]) -> dict[str, Any]:
    timestamps = [parse_float(row.get("timestamp")) for row in rows]
    timestamps = [value for value in timestamps if math.isfinite(value)]
    metrics: dict[str, Any] = {"rows": len(rows), "timestamp_rows": len(timestamps)}
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
    return metrics


def load_json(path: Path) -> dict[str, Any] | None:
    resolved = repo_path(path)
    if not resolved.exists():
        return None
    return json.loads(resolved.read_text(encoding="utf-8"))


def preflight_verdict(payload: dict[str, Any] | None, result: CommandResult | None) -> str:
    if payload is not None and "verdict" in payload:
        return str(payload["verdict"])
    if result is None:
        return "SKIPPED"
    return "PASS" if result.returncode == 0 else "FAIL"


def overall_verdict(
    *,
    camera_result: CommandResult,
    tcp_result: CommandResult,
    preflight_result: CommandResult | None,
    preflight_payload: dict[str, Any] | None,
    camera_metrics: dict[str, Any],
    tcp_metrics: dict[str, Any],
) -> str:
    if camera_result.returncode != 0 or tcp_result.returncode != 0:
        return "FAIL"
    if camera_metrics.get("timestamp_monotonic") is False:
        return "FAIL"
    if tcp_metrics.get("timestamp_monotonic") is False:
        return "FAIL"
    if preflight_result is None:
        return "FAIL"
    verdict = preflight_verdict(preflight_payload, preflight_result)
    if preflight_result.returncode != 0 or verdict == "FAIL":
        return "FAIL"
    if verdict == "WARN":
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


def render_summary(
    *,
    args: argparse.Namespace,
    camera_result: CommandResult,
    tcp_result: CommandResult,
    preflight_result: CommandResult | None,
    preflight_payload: dict[str, Any] | None,
    camera_metrics: dict[str, Any],
    tcp_metrics: dict[str, Any],
    result: str,
) -> str:
    preflight_result_text = preflight_verdict(preflight_payload, preflight_result)
    lines = [
        "# Real Capture Bundle Summary",
        "",
        f"- Overall: **{result}**",
        f"- Camera recorder return code: `{camera_result.returncode}`",
        f"- TCP recorder return code: `{tcp_result.returncode}`",
        f"- Combined preflight verdict: **{preflight_result_text}**",
        f"- Camera frames: `{args.record_camera_output_dir}`",
        f"- Camera stats: `{args.record_camera_stats_output}`",
        f"- TCP trace: `{args.record_tcp_output}`",
        f"- Target calibration: `{args.target_calibration if args.target_calibration is not None else 'trace_or_config'}`",
        f"- TCP target columns: `{'omitted' if tcp_should_omit_target_columns(args) else 'included'}`",
        f"- Combined preflight summary: `{args.preflight_summary_md}`",
        "",
        "## Commands",
        "",
        "Camera recorder:",
        "",
        "```powershell",
        command_text(camera_result.command),
        "```",
        "",
        "TCP recorder:",
        "",
        "```powershell",
        command_text(tcp_result.command),
        "```",
        "",
    ]
    if preflight_result is not None:
        lines.extend(
            [
                "Combined preflight:",
                "",
                "```powershell",
                command_text(preflight_result.command),
                "```",
                "",
            ]
        )
    lines.extend(["## Metrics", "", "| Metric | Value |", "| --- | ---: |"])
    for key, value in metric_rows("camera", camera_metrics) + metric_rows("tcp", tcp_metrics):
        lines.append(f"| `{key}` | {format_value(value)} |")
    if preflight_payload is not None:
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
    validate_args(args, preflight_args)

    camera_command = build_camera_record_command(args)
    tcp_command = build_tcp_record_command(args)
    camera_result, tcp_result = run_recorders(camera_command, tcp_command)

    preflight_result = None
    preflight_payload = None
    if camera_result.returncode == 0 and tcp_result.returncode == 0:
        preflight_command = build_preflight_command(args, preflight_args)
        preflight_result = run_command("combined_preflight", preflight_command)
        preflight_payload = load_json(args.preflight_output_json)

    camera_metrics = timestamp_metrics(load_csv_rows(args.record_camera_stats_output))
    tcp_metrics = timestamp_metrics(load_csv_rows(args.record_tcp_output))
    result = overall_verdict(
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
        if camera_result.returncode != 0:
            sys.exit(camera_result.returncode)
        if tcp_result.returncode != 0:
            sys.exit(tcp_result.returncode)
        if preflight_result is not None:
            sys.exit(preflight_result.returncode or 1)
        sys.exit(1)


if __name__ == "__main__":
    main()
