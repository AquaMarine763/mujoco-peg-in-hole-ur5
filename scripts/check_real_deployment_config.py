from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from peg_in_hole_mujoco.real_backend import IMAGE_SUFFIXES, RealTargetCalibration


REPO_ROOT = Path(__file__).resolve().parents[1]
SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}
DEFAULTS: dict[str, Any] = {
    "control_frequency_hz": 20.0,
    "image_width": 100,
    "image_height": 100,
    "include_near_hole_crop": False,
    "near_hole_crop_size": 64,
    "crop_xywh": None,
    "rotate_k": 0,
    "max_steps": 50,
    "safety_max_action": 0.002,
    "safety_action_filter_alpha": 0.6,
    "safety_workspace_low": (0.45, -0.10, 0.60),
    "safety_workspace_high": (0.65, 0.15, 0.82),
    "peg_tip_pos": (0.55, 0.05, 0.78),
    "target_pos": (0.55, 0.05, 0.65),
    "target_calibration": None,
    "pose_trace": None,
    "tcp_pose_trace": None,
    "pose_frame": "robot_base",
    "tcp_to_peg_tip_xyz": (0.0, 0.0, -0.11),
    "tool0_to_peg_tip_xyz": (0.0, 0.0, -0.11),
    "camera_fx": None,
    "camera_fy": None,
    "camera_cx": None,
    "camera_cy": None,
    "tool0_to_camera_xyz": None,
    "tool0_to_camera_rpy": None,
}


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
            "Statically validate real-robot dry-run/deployment configuration "
            "before collecting real camera/TCP data. This does not connect to hardware."
        )
    )
    parser.add_argument("--config", type=Path, default=Path("configs/real_ur5_dryrun.yaml"))
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--require-model", action="store_true")
    parser.add_argument("--target-calibration", type=Path, default=None)
    parser.add_argument("--require-target-calibration", action="store_true", default=True)
    parser.add_argument("--allow-missing-target-calibration", dest="require_target_calibration", action="store_false")
    parser.add_argument("--pose-trace", type=Path, default=None)
    parser.add_argument("--tcp-pose-trace", type=Path, default=None)
    parser.add_argument("--image-input", type=Path, default=None)
    parser.add_argument("--expected-pose-frame", default="robot_base")
    parser.add_argument("--expected-target-source", default="fixture_calibration")
    parser.add_argument("--tcp-to-peg-tip-xyz", nargs=3, type=float, default=None)
    parser.add_argument("--max-safe-action", type=float, default=None)
    parser.add_argument(
        "--require-camera-calibration",
        action="store_true",
        help="Require measured camera intrinsics and tool0_to_camera transform fields in the config.",
    )
    parser.add_argument(
        "--require-image-crop",
        action="store_true",
        help="Require crop_xywh to be set before using real camera frames.",
    )
    parser.add_argument("--output-md", type=Path, default=Path("results/real_deployment_config_check.md"))
    parser.add_argument("--output-json", type=Path, default=Path("results/real_deployment_config_check.json"))
    parser.add_argument("--fail-on-warn", action="store_true")
    return parser.parse_args()


def repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return ""
    lowered = text.lower()
    if lowered in ("none", "null"):
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if text.startswith("[") and text.endswith("]"):
        content = text[1:-1].strip()
        if not content:
            return []
        return [parse_scalar(part) for part in content.split(",")]
    try:
        if any(char in lowered for char in (".", "e")):
            return float(text)
        return int(text)
    except ValueError:
        return text.strip("'\"")


def load_simple_yaml(path: Path) -> dict[str, Any]:
    config: dict[str, Any] = {}
    resolved = repo_path(path)
    with resolved.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            config[key.strip()] = parse_scalar(value)
    return config


def config_value(config: dict[str, Any], key: str) -> Any:
    return config.get(key, DEFAULTS.get(key))


def is_none_like(value: Any) -> bool:
    return value is None or str(value).strip().lower() in {"", "none", "null"}


def optional_path(value: Any) -> Path | None:
    if is_none_like(value):
        return None
    return Path(str(value))


def finite_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return math.nan
    return number if math.isfinite(number) else math.nan


def vector3(value: Any, key: str) -> tuple[float, float, float] | None:
    if value is None or isinstance(value, str):
        return None
    try:
        values = list(value)
    except TypeError:
        return None
    if len(values) != 3:
        raise ValueError(f"{key} must contain exactly three values.")
    parsed = tuple(finite_float(item) for item in values)
    if not all(math.isfinite(item) for item in parsed):
        return None
    return parsed  # type: ignore[return-value]


def vector_norm(values: tuple[float, float, float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def in_workspace(
    point: tuple[float, float, float],
    low: tuple[float, float, float],
    high: tuple[float, float, float],
) -> bool:
    return all(low[index] <= point[index] <= high[index] for index in range(3))


def load_csv_header(path: Path) -> list[str]:
    with repo_path(path).open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        return next(reader, [])


def image_count(path: Path) -> int:
    resolved = repo_path(path)
    if resolved.is_file():
        return int(resolved.suffix.lower() in IMAGE_SUFFIXES)
    if not resolved.is_dir():
        return 0
    return sum(1 for item in resolved.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES)


def add_issue(issues: list[Issue], severity: str, code: str, message: str, *, count: int = 1, details: str = "") -> None:
    issues.append(Issue(severity=severity, code=code, message=message, count=count, details=details))


def validate_positive_number(
    config: dict[str, Any],
    issues: list[Issue],
    metrics: dict[str, Any],
    key: str,
) -> float | None:
    value = finite_float(config_value(config, key))
    metrics[key] = value
    if not math.isfinite(value) or value <= 0.0:
        add_issue(issues, "ERROR", f"{key}_invalid", f"{key} must be positive.", details=str(config_value(config, key)))
        return None
    return value


def validate_positive_int(
    config: dict[str, Any],
    issues: list[Issue],
    metrics: dict[str, Any],
    key: str,
) -> int | None:
    value = finite_float(config_value(config, key))
    metrics[key] = value
    if not math.isfinite(value) or int(value) != value or value <= 0:
        add_issue(issues, "ERROR", f"{key}_invalid", f"{key} must be a positive integer.", details=str(config_value(config, key)))
        return None
    return int(value)


def validate_config_scalars(args: argparse.Namespace, config: dict[str, Any], issues: list[Issue], metrics: dict[str, Any]) -> None:
    validate_positive_number(config, issues, metrics, "control_frequency_hz")
    validate_positive_int(config, issues, metrics, "image_width")
    validate_positive_int(config, issues, metrics, "image_height")
    validate_positive_int(config, issues, metrics, "near_hole_crop_size")
    validate_positive_int(config, issues, metrics, "max_steps")
    include_crop = config_value(config, "include_near_hole_crop")
    metrics["include_near_hole_crop"] = bool(include_crop)
    if not isinstance(include_crop, bool):
        add_issue(
            issues,
            "WARN",
            "include_near_hole_crop_not_bool",
            "include_near_hole_crop should be true or false.",
            details=str(include_crop),
        )
    config_safe_action = validate_positive_number(config, issues, metrics, "safety_max_action")
    if args.max_safe_action is not None:
        metrics["requested_max_safe_action"] = args.max_safe_action
        if args.max_safe_action <= 0.0:
            add_issue(issues, "ERROR", "requested_max_safe_action_invalid", "--max-safe-action must be positive.")
        elif config_safe_action is not None and abs(args.max_safe_action - config_safe_action) > 1e-12:
            add_issue(
                issues,
                "WARN",
                "max_safe_action_override_differs",
                "--max-safe-action differs from safety_max_action in config.",
                details=f"{args.max_safe_action:.9g} vs {config_safe_action:.9g}",
            )

    pose_frame = str(config_value(config, "pose_frame"))
    metrics["pose_frame"] = pose_frame
    if args.expected_pose_frame and pose_frame != args.expected_pose_frame:
        add_issue(
            issues,
            "ERROR",
            "pose_frame_mismatch",
            f"Config pose_frame differs from expected frame '{args.expected_pose_frame}'.",
            details=pose_frame,
        )

    alpha = finite_float(config_value(config, "safety_action_filter_alpha"))
    metrics["safety_action_filter_alpha"] = alpha
    if not math.isfinite(alpha) or not 0.0 < alpha <= 1.0:
        add_issue(
            issues,
            "ERROR",
            "safety_action_filter_alpha_invalid",
            "safety_action_filter_alpha must be in (0, 1].",
            details=str(config_value(config, "safety_action_filter_alpha")),
        )

    crop = config_value(config, "crop_xywh")
    if crop is not None:
        try:
            crop_values = list(crop)
        except TypeError:
            crop_values = []
        if len(crop_values) != 4 or finite_float(crop_values[2]) <= 0 or finite_float(crop_values[3]) <= 0:
            add_issue(
                issues,
                "ERROR",
                "crop_xywh_invalid",
                "crop_xywh must be none or four values with positive width and height.",
                details=str(crop),
            )
    if crop is None:
        metrics["crop_xywh"] = "none"
    else:
        try:
            metrics["crop_xywh"] = list(crop)
        except TypeError:
            metrics["crop_xywh"] = str(crop)


def validate_camera_requirements(
    args: argparse.Namespace,
    config: dict[str, Any],
    issues: list[Issue],
    metrics: dict[str, Any],
) -> None:
    crop = config_value(config, "crop_xywh")
    if args.require_image_crop and crop is None:
        add_issue(
            issues,
            "ERROR",
            "crop_xywh_missing",
            "Set crop_xywh from measured real camera frames before real capture preflight.",
        )

    if not args.require_camera_calibration:
        return

    for key in ("camera_fx", "camera_fy", "camera_cx", "camera_cy"):
        raw_value = config_value(config, key)
        value = finite_float(raw_value)
        metrics[key] = value
        if raw_value is None or not math.isfinite(value):
            add_issue(
                issues,
                "ERROR",
                f"{key}_missing",
                f"{key} must be set from measured camera calibration.",
            )
            continue
        if key in {"camera_fx", "camera_fy"} and value <= 1.0:
            add_issue(
                issues,
                "ERROR",
                f"{key}_invalid",
                f"{key} must be greater than 1 pixel.",
                details=str(raw_value),
            )
        if key in {"camera_cx", "camera_cy"} and value < 0.0:
            add_issue(
                issues,
                "ERROR",
                f"{key}_invalid",
                f"{key} must be non-negative.",
                details=str(raw_value),
            )

    for key in ("tool0_to_camera_xyz", "tool0_to_camera_rpy"):
        raw_value = config_value(config, key)
        try:
            vector = vector3(raw_value, key)
        except ValueError as exc:
            add_issue(
                issues,
                "ERROR",
                f"{key}_invalid",
                f"{key} must contain exactly three values.",
                details=str(exc),
            )
            continue
        if vector is None:
            add_issue(
                issues,
                "ERROR",
                f"{key}_missing",
                f"{key} must be a measured finite 3D vector.",
                details=str(raw_value),
            )
            continue
        metrics[key] = list(vector)
        if key == "tool0_to_camera_xyz" and vector_norm(vector) < 0.005:
            add_issue(
                issues,
                "WARN",
                "tool0_to_camera_xyz_near_zero",
                "tool0_to_camera_xyz is near zero; this usually means the template placeholder was not replaced.",
                details=f"{vector_norm(vector):.6g}",
            )


def validate_workspace(
    config: dict[str, Any],
    issues: list[Issue],
    metrics: dict[str, Any],
    target_pos: tuple[float, float, float] | None,
) -> tuple[tuple[float, float, float] | None, tuple[float, float, float] | None]:
    low = vector3(config_value(config, "safety_workspace_low"), "safety_workspace_low")
    high = vector3(config_value(config, "safety_workspace_high"), "safety_workspace_high")
    if low is None or high is None:
        add_issue(issues, "ERROR", "safety_workspace_invalid", "safety workspace bounds must be finite 3D vectors.")
        return low, high

    metrics["safety_workspace_low"] = list(low)
    metrics["safety_workspace_high"] = list(high)
    if any(low[index] >= high[index] for index in range(3)):
        add_issue(issues, "ERROR", "safety_workspace_order_invalid", "Each workspace low bound must be lower than high.")
        return low, high

    peg_tip = vector3(config_value(config, "peg_tip_pos"), "peg_tip_pos")
    if peg_tip is not None:
        metrics["peg_tip_pos"] = list(peg_tip)
        if not in_workspace(peg_tip, low, high):
            add_issue(issues, "WARN", "peg_tip_outside_workspace", "Configured peg_tip_pos is outside safety workspace.")

    if target_pos is not None:
        metrics["target_pos"] = list(target_pos)
        if not in_workspace(target_pos, low, high):
            add_issue(
                issues,
                "ERROR",
                "target_outside_workspace",
                "Target calibration position is outside safety workspace.",
            )
    return low, high


def resolve_target_calibration_path(args: argparse.Namespace, config: dict[str, Any]) -> Path | None:
    if args.target_calibration is not None:
        return args.target_calibration
    return optional_path(config_value(config, "target_calibration"))


def validate_target_calibration(
    args: argparse.Namespace,
    config: dict[str, Any],
    issues: list[Issue],
    metrics: dict[str, Any],
) -> tuple[RealTargetCalibration | None, Path | None]:
    path = resolve_target_calibration_path(args, config)
    if path is None:
        if args.require_target_calibration:
            add_issue(
                issues,
                "ERROR",
                "missing_target_calibration",
                "Provide --target-calibration or set target_calibration in config.",
            )
        return None, None

    resolved = repo_path(path)
    metrics["target_calibration_path"] = str(path)
    if not resolved.exists():
        add_issue(issues, "ERROR", "target_calibration_not_found", "Target calibration file does not exist.", details=str(path))
        return None, path

    try:
        calibration = RealTargetCalibration.from_file(resolved)
    except Exception as exc:
        add_issue(issues, "ERROR", "target_calibration_load_failed", "Could not load target calibration.", details=str(exc))
        return None, path

    metrics["target_id"] = calibration.target_id
    metrics["target_source"] = calibration.target_source
    metrics["target_frame"] = calibration.pose_frame
    metrics["target_pos"] = list(calibration.target_pos)
    if args.expected_pose_frame and calibration.pose_frame != args.expected_pose_frame:
        add_issue(
            issues,
            "ERROR",
            "target_frame_mismatch",
            f"Target calibration frame differs from expected frame '{args.expected_pose_frame}'.",
            details=calibration.pose_frame,
        )
    if args.expected_target_source and calibration.target_source != args.expected_target_source:
        add_issue(
            issues,
            "WARN",
            "target_source_unexpected",
            f"Target source differs from expected source '{args.expected_target_source}'.",
            details=calibration.target_source,
        )
    return calibration, path


def validate_tcp_offset(
    args: argparse.Namespace,
    config: dict[str, Any],
    issues: list[Issue],
    metrics: dict[str, Any],
) -> tuple[float, float, float] | None:
    value = args.tcp_to_peg_tip_xyz if args.tcp_to_peg_tip_xyz is not None else config_value(config, "tcp_to_peg_tip_xyz")
    offset = vector3(value, "tcp_to_peg_tip_xyz")
    if offset is None:
        add_issue(issues, "ERROR", "tcp_to_peg_tip_invalid", "tcp_to_peg_tip_xyz must be a finite 3D vector.")
        return None

    metrics["tcp_to_peg_tip_xyz"] = list(offset)
    metrics["tcp_to_peg_tip_norm"] = vector_norm(offset)
    if vector_norm(offset) < 0.02 or vector_norm(offset) > 0.25:
        add_issue(
            issues,
            "WARN",
            "tcp_to_peg_tip_norm_unusual",
            "TCP-to-peg-tip offset norm is unusual for this setup.",
            details=f"{vector_norm(offset):.6g}",
        )
    if offset[2] >= 0.0:
        add_issue(
            issues,
            "WARN",
            "tcp_to_peg_tip_z_nonnegative",
            "Expected peg tip to be below the active TCP in the TCP frame.",
            details=str(offset),
        )

    tool0_offset = vector3(config_value(config, "tool0_to_peg_tip_xyz"), "tool0_to_peg_tip_xyz")
    if tool0_offset is not None:
        mismatch = vector_norm(tuple(offset[index] - tool0_offset[index] for index in range(3)))  # type: ignore[arg-type]
        metrics["tool0_tcp_offset_mismatch"] = mismatch
        if mismatch > 1e-9:
            add_issue(
                issues,
                "WARN",
                "tool0_tcp_offset_mismatch",
                "tcp_to_peg_tip_xyz and tool0_to_peg_tip_xyz differ.",
                details=f"{mismatch:.6g}",
            )
    return offset


def validate_model(args: argparse.Namespace, issues: list[Issue], metrics: dict[str, Any]) -> None:
    if args.model is None:
        if args.require_model:
            add_issue(issues, "ERROR", "missing_model", "Provide --model for real policy preflight.")
        return
    metrics["model_path"] = str(args.model)
    resolved = repo_path(args.model)
    if not resolved.exists():
        add_issue(issues, "ERROR", "model_not_found", "Policy model file does not exist.", details=str(args.model))
        return
    metrics["model_size_bytes"] = resolved.stat().st_size
    if resolved.suffix.lower() != ".zip":
        add_issue(issues, "WARN", "model_suffix_unexpected", "Stable-Baselines3 models are normally .zip files.", details=str(args.model))


def validate_observation_contract(
    args: argparse.Namespace,
    config: dict[str, Any],
    issues: list[Issue],
    metrics: dict[str, Any],
) -> None:
    if args.model is None:
        return
    model_text = str(args.model).replace("\\", "/").lower()
    expects_crop = "staged_crop" in model_text or "near_hole_crop" in model_text
    include_crop = bool(config_value(config, "include_near_hole_crop"))
    metrics["model_expects_near_hole_crop"] = expects_crop
    if expects_crop and not include_crop:
        add_issue(
            issues,
            "ERROR",
            "near_hole_crop_missing_for_model",
            "The configured policy model expects a near_hole_crop observation.",
            details=str(args.model),
        )


def resolve_trace_path(args_path: Path | None, config: dict[str, Any], key: str) -> Path | None:
    if args_path is not None:
        return args_path
    return optional_path(config_value(config, key))


def validate_trace_inputs(args: argparse.Namespace, config: dict[str, Any], issues: list[Issue], metrics: dict[str, Any]) -> None:
    pose_trace = resolve_trace_path(args.pose_trace, config, "pose_trace")
    tcp_trace = resolve_trace_path(args.tcp_pose_trace, config, "tcp_pose_trace")
    if pose_trace is not None and tcp_trace is not None:
        add_issue(issues, "ERROR", "multiple_pose_trace_sources", "Use either pose_trace or tcp_pose_trace, not both.")

    for key, path in (("pose_trace", pose_trace), ("tcp_pose_trace", tcp_trace)):
        if path is None:
            continue
        resolved = repo_path(path)
        metrics[f"{key}_path"] = str(path)
        if not resolved.exists():
            add_issue(issues, "ERROR", f"{key}_not_found", f"{key} file does not exist.", details=str(path))
            continue
        try:
            header = load_csv_header(path)
        except Exception as exc:
            add_issue(issues, "ERROR", f"{key}_read_failed", f"Could not read {key} CSV header.", details=str(exc))
            continue
        metrics[f"{key}_columns"] = ", ".join(header)
        required = ("tcp_x", "tcp_y", "tcp_z", "tcp_rx", "tcp_ry", "tcp_rz") if key == "tcp_pose_trace" else (
            "peg_tip_x",
            "peg_tip_y",
            "peg_tip_z",
        )
        missing = [column for column in required if column not in header]
        if missing:
            add_issue(issues, "ERROR", f"{key}_missing_columns", f"{key} is missing required columns.", details=", ".join(missing))
        if key == "tcp_pose_trace" and args.target_calibration is not None and {"target_x", "target_y", "target_z"} & set(header):
            add_issue(
                issues,
                "WARN",
                "tcp_trace_embeds_target_with_calibration",
                "TCP trace contains target columns while a separate target calibration is provided.",
            )


def validate_image_input(args: argparse.Namespace, issues: list[Issue], metrics: dict[str, Any]) -> None:
    if args.image_input is None:
        return
    resolved = repo_path(args.image_input)
    metrics["image_input"] = str(args.image_input)
    if not resolved.exists():
        add_issue(issues, "ERROR", "image_input_not_found", "Image input path does not exist.", details=str(args.image_input))
        return
    count = image_count(args.image_input)
    metrics["image_count"] = count
    if count <= 0:
        add_issue(issues, "ERROR", "image_input_empty", "Image input path contains no supported image files.")


def verdict(issues: list[Issue], fail_on_warn: bool) -> str:
    if any(issue.severity == "ERROR" for issue in issues):
        return "FAIL"
    if any(issue.severity == "WARN" for issue in issues):
        return "FAIL" if fail_on_warn else "WARN"
    return "PASS"


def format_value(value: Any) -> str:
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.9g}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(format_value(item) for item in value) + "]"
    return str(value)


def render_markdown(
    *,
    args: argparse.Namespace,
    result: str,
    metrics: dict[str, Any],
    issues: list[Issue],
) -> str:
    lines = [
        "# Real Deployment Config Check",
        "",
        f"- Verdict: **{result}**",
        f"- Config: `{args.config}`",
        f"- Target calibration: `{metrics.get('target_calibration_path', args.target_calibration)}`",
        f"- Model: `{args.model}`",
        f"- Expected pose frame: `{args.expected_pose_frame}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in sorted(metrics):
        lines.append(f"| `{key}` | {format_value(metrics[key])} |")
    lines.extend(
        [
            "",
            "## Issues",
            "",
            "| Severity | Code | Count | Details |",
            "| --- | --- | ---: | --- |",
        ]
    )
    if not issues:
        lines.append("| INFO | `no_issues` | 0 | No issues detected. |")
    else:
        for issue in issues:
            details = issue.details or issue.message
            lines.append(f"| {issue.severity} | `{issue.code}` | {issue.count} | {details} |")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, result: str, metrics: dict[str, Any], issues: list[Issue]) -> None:
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "verdict": result,
        "metrics": metrics,
        "issues": [asdict(issue) for issue in issues],
    }
    resolved.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    metrics: dict[str, Any] = {}
    issues: list[Issue] = []

    config_path = repo_path(args.config)
    if not config_path.exists():
        add_issue(issues, "ERROR", "config_not_found", "Config file does not exist.", details=str(args.config))
        config: dict[str, Any] = {}
    else:
        try:
            config = load_simple_yaml(args.config)
            metrics["config_path"] = str(args.config)
        except Exception as exc:
            add_issue(issues, "ERROR", "config_load_failed", "Could not load config file.", details=str(exc))
            config = {}

    validate_config_scalars(args, config, issues, metrics)
    validate_camera_requirements(args, config, issues, metrics)
    calibration, _ = validate_target_calibration(args, config, issues, metrics)
    target_pos = calibration.target_pos if calibration is not None else vector3(config_value(config, "target_pos"), "target_pos")
    validate_workspace(config, issues, metrics, target_pos)
    validate_tcp_offset(args, config, issues, metrics)
    validate_model(args, issues, metrics)
    validate_observation_contract(args, config, issues, metrics)
    validate_trace_inputs(args, config, issues, metrics)
    validate_image_input(args, issues, metrics)

    issues = sorted(issues, key=lambda issue: (SEVERITY_ORDER[issue.severity], issue.code))
    result = verdict(issues, args.fail_on_warn)

    output_md = repo_path(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(args=args, result=result, metrics=metrics, issues=issues), encoding="utf-8")
    write_json(args.output_json, result, metrics, issues)

    print(f"verdict={result}")
    print(f"saved_summary_to={args.output_md}")
    print(f"saved_json_to={args.output_json}")
    for issue in issues:
        print(f"{issue.severity}: {issue.code} ({issue.count}) {issue.message}")
    if result == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
