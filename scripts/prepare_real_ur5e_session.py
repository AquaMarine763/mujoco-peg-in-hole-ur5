from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = Path(
    "checkpoints_image_bc_ur5e_adapter_fixedcam_full_light_geometry_"
    "staged_crop_full_light_replay_750k_oracle_e4/sac_image_bc.zip"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare an ignored local UR5e real-data read-only session. "
            "This writes a local config copy and a command checklist; it does "
            "not connect to the robot or camera."
        )
    )
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--template", type=Path, default=Path("configs/real/ur5e/dryrun_template.yaml"))
    parser.add_argument("--config-output", type=Path, default=None)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--ur-host", default="<UR5E_IP>")
    parser.add_argument("--camera-source", default=None)
    parser.add_argument("--camera-device-index", type=int, default=0)
    parser.add_argument("--record-camera-frames", type=int, default=100)
    parser.add_argument("--record-camera-frequency-hz", type=float, default=5.0)
    parser.add_argument("--record-camera-warmup-frames", type=int, default=20)
    parser.add_argument("--record-tcp-samples", type=int, default=300)
    parser.add_argument("--record-tcp-frequency-hz", type=float, default=20.0)
    parser.add_argument("--target-measurement-samples", type=int, default=30)
    parser.add_argument("--target-measurement-frequency-hz", type=float, default=5.0)
    parser.add_argument("--tcp-to-target-xyz", nargs=3, type=float, default=(0.0, 0.0, 0.0))
    parser.add_argument("--tcp-to-peg-tip-xyz", nargs=3, type=float, default=(0.0, 0.0, -0.11))
    parser.add_argument("--max-steps", type=int, default=50)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def make_session_id() -> str:
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"real_ur5e_{timestamp}"


def repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def repo_text(path: Path) -> str:
    try:
        return repo_path(path).resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def ps_path(path: Path) -> str:
    return repo_text(path).replace("/", "\\")


def float_text(value: float) -> str:
    return f"{float(value):.12g}"


def command_block(parts: list[str]) -> str:
    if not parts:
        return "```powershell\n# no command\n```"
    lines = ["```powershell", parts[0]]
    for part in parts[1:]:
        lines[-1] += " `"
        lines.append(f"  {part}")
    lines.append("```")
    return "\n".join(lines)


def ensure_writable(path: Path, overwrite: bool) -> None:
    resolved = repo_path(path)
    if resolved.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists; pass --overwrite to replace it.")
    resolved.parent.mkdir(parents=True, exist_ok=True)


def write_local_config(
    *,
    template: Path,
    config_output: Path,
    target_calibration: Path,
    tcp_to_peg_tip_xyz: tuple[float, float, float],
    max_steps: int,
    overwrite: bool,
) -> None:
    ensure_writable(config_output, overwrite)
    template_text = repo_path(template).read_text(encoding="utf-8")
    replacements = {
        "target_calibration": repo_text(target_calibration),
        "pose_trace": "none",
        "tcp_pose_trace": "none",
        "tcp_to_peg_tip_xyz": "[{}]".format(", ".join(float_text(value) for value in tcp_to_peg_tip_xyz)),
        "tool0_to_peg_tip_xyz": "[{}]".format(", ".join(float_text(value) for value in tcp_to_peg_tip_xyz)),
        "max_steps": str(max_steps),
    }
    lines = [
        "# Local real UR5e read-only config generated from dryrun_template.yaml.",
        "# This file is ignored by git. Replace placeholders with measured cell values.",
    ]
    for raw_line in template_text.splitlines():
        stripped = raw_line.strip()
        if ":" not in stripped or stripped.startswith("#"):
            lines.append(raw_line)
            continue
        key = stripped.split(":", 1)[0].strip()
        if key in replacements:
            lines.append(f"{key}: {replacements[key]}")
        else:
            lines.append(raw_line)
    repo_path(config_output).write_text("\n".join(lines) + "\n", encoding="utf-8")


def camera_record_args(args: argparse.Namespace) -> list[str]:
    if args.camera_source is not None:
        return [f"--record-camera-source {args.camera_source}"]
    return [f"--record-camera-device-index {args.camera_device_index}"]


def xyz_args(values: tuple[float, float, float] | list[float]) -> list[str]:
    return [float_text(float(value)) for value in values]


def render_commands(
    *,
    args: argparse.Namespace,
    session_id: str,
    config_output: Path,
    results_dir: Path,
    target_measurements: Path,
    target_calibration: Path,
) -> str:
    camera_frames = results_dir / "camera_frames"
    camera_stats = results_dir / "camera_stats.csv"
    camera_summary = results_dir / "camera_summary.md"
    tcp_trace = results_dir / "tcp_pose_trace.csv"
    config_check_md = results_dir / "config_check.md"
    config_check_json = results_dir / "config_check.json"
    bundle_md = results_dir / "capture_bundle_summary.md"
    bundle_json = results_dir / "capture_bundle_summary.json"
    preflight_md = results_dir / "preflight_summary.md"
    preflight_json = results_dir / "preflight_summary.json"
    readiness_md = results_dir / "motion_readiness.md"
    readiness_json = results_dir / "motion_readiness.json"

    target_measurement_command = [
        "python scripts\\record_ur_rtde_target_measurements.py",
        f"--host {args.ur_host}",
        f"--output {ps_path(target_measurements)}",
        f"--summary-md {ps_path(results_dir / 'target_measurements_summary.md')}",
        f"--samples {args.target_measurement_samples}",
        f"--frequency-hz {float_text(args.target_measurement_frequency_hz)}",
        "--pose-frame robot_base",
        "--target-id real_hole",
        "--target-source fixture_calibration",
        "--tcp-to-target-xyz " + " ".join(xyz_args(args.tcp_to_target_xyz)),
    ]
    target_calibration_command = [
        "python scripts\\make_real_target_calibration.py",
        f"--input-csv {ps_path(target_measurements)}",
        f"--output {ps_path(target_calibration)}",
        f"--summary-md {ps_path(results_dir / 'target_calibration_summary.md')}",
        "--target-id real_hole",
        "--target-source fixture_calibration",
        "--pose-frame robot_base",
        "--method mean",
        "--fail-on-warn",
    ]
    config_check_command = [
        "python scripts\\check_real_deployment_config.py",
        f"--config {ps_path(config_output)}",
        f"--target-calibration {ps_path(target_calibration)}",
        f"--model {ps_path(args.model)}",
        "--tcp-to-peg-tip-xyz " + " ".join(xyz_args(args.tcp_to_peg_tip_xyz)),
        "--require-camera-calibration",
        "--require-image-crop",
        "--fail-on-warn",
        f"--output-md {ps_path(config_check_md)}",
        f"--output-json {ps_path(config_check_json)}",
    ]
    capture_command = [
        "python scripts\\run_real_capture_bundle.py",
        f"--session-id {session_id}",
        f"--config {ps_path(config_output)}",
        *camera_record_args(args),
        f"--record-camera-output-dir {ps_path(camera_frames)}",
        f"--record-camera-stats-output {ps_path(camera_stats)}",
        f"--record-camera-summary-md {ps_path(camera_summary)}",
        f"--record-camera-frames {args.record_camera_frames}",
        f"--record-camera-frequency-hz {float_text(args.record_camera_frequency_hz)}",
        f"--record-camera-warmup-frames {args.record_camera_warmup_frames}",
        f"--record-tcp-host {args.ur_host}",
        f"--record-tcp-output {ps_path(tcp_trace)}",
        f"--record-tcp-samples {args.record_tcp_samples}",
        f"--record-tcp-frequency-hz {float_text(args.record_tcp_frequency_hz)}",
        "--record-tcp-pose-frame robot_base",
        f"--target-calibration {ps_path(target_calibration)}",
        "--require-camera-calibration",
        "--require-image-crop",
        "--config-check-fail-on-warn",
        f"--summary-md {ps_path(bundle_md)}",
        f"--output-json {ps_path(bundle_json)}",
        f"--preflight-summary-md {ps_path(preflight_md)}",
        f"--preflight-output-json {ps_path(preflight_json)}",
        f"--model {ps_path(args.model)}",
        "--device cpu",
        "--episodes 1",
        f"--max-steps {args.max_steps}",
        "--tcp-to-peg-tip-xyz " + " ".join(xyz_args(args.tcp_to_peg_tip_xyz)),
        "--guarded-policy",
        "--guard-scenario-filter geometry",
        "--guard-start-xy 0.060",
        "--guard-start-z 0.080",
        "--guard-blend 0.75",
        "--guard-min-policy-steps 0",
        "--guarded-align-xy-tolerance 0.025",
        "--guarded-max-down-action 0.0035",
    ]
    readiness_command = [
        "python scripts\\check_real_motion_readiness.py",
        f"--bundle-summary-json {ps_path(bundle_json)}",
        f"--output-md {ps_path(readiness_md)}",
        f"--output-json {ps_path(readiness_json)}",
        "--fail-on-warn",
    ]

    return "\n".join(
        [
            "# UR5e Real Read-Only Session Commands",
            "",
            f"- Session id: `{session_id}`",
            f"- Local config: `{ps_path(config_output)}`",
            f"- Results dir: `{ps_path(results_dir)}`",
            f"- Model: `{ps_path(args.model)}`",
            "",
            "Edit the local config first. Replace `crop_xywh`, camera intrinsics, `tool0_to_camera_*`, "
            "`safety_workspace_*`, and `tcp_to_peg_tip_xyz` with measured values.",
            "",
            "## 1. Record Target Measurements",
            "",
            command_block(target_measurement_command),
            "",
            "## 2. Build Target Calibration",
            "",
            command_block(target_calibration_command),
            "",
            "## 3. Strict Static Check",
            "",
            command_block(config_check_command),
            "",
            "## 4. Capture Camera/TCP And Run Policy Preflight",
            "",
            command_block(capture_command),
            "",
            "## 5. Motion Readiness Gate",
            "",
            command_block(readiness_command),
            "",
            "This workflow is read-only until a separate motion executor is explicitly enabled. "
            "Do not add `--allow-synthetic`, `--allow-smoke-paths`, or `--allow-action-limited` for a real readiness gate.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    session_id = args.session_id or make_session_id()
    config_output = args.config_output or Path(f"configs/real/ur5e/{session_id}_local.yaml")
    results_dir = args.results_dir or Path(f"results/real/ur5e/{session_id}")
    target_measurements = results_dir / "target_measurements.csv"
    target_calibration = results_dir / "target_calibration.yaml"
    commands_md = results_dir / "COMMANDS.md"

    if args.record_camera_frames <= 0:
        raise ValueError("--record-camera-frames must be positive.")
    if args.record_tcp_samples <= 0:
        raise ValueError("--record-tcp-samples must be positive.")
    if args.target_measurement_samples <= 0:
        raise ValueError("--target-measurement-samples must be positive.")

    write_local_config(
        template=args.template,
        config_output=config_output,
        target_calibration=target_calibration,
        tcp_to_peg_tip_xyz=tuple(float(value) for value in args.tcp_to_peg_tip_xyz),
        max_steps=args.max_steps,
        overwrite=args.overwrite,
    )

    ensure_writable(commands_md, args.overwrite)
    repo_path(commands_md).write_text(
        render_commands(
            args=args,
            session_id=session_id,
            config_output=config_output,
            results_dir=results_dir,
            target_measurements=target_measurements,
            target_calibration=target_calibration,
        ),
        encoding="utf-8",
    )

    print(f"session_id={session_id}")
    print(f"saved_config={config_output}")
    print(f"saved_commands={commands_md}")


if __name__ == "__main__":
    main()
