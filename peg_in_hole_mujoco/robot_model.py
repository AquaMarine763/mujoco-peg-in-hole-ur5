from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mujoco


REQUIRED_JOINTS = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow",
    "wrist_1",
    "wrist_2",
    "wrist_3",
)

REQUIRED_ACTUATORS = tuple(f"{joint}_ctrl" for joint in REQUIRED_JOINTS)

REQUIRED_BODIES = (
    "hole_body",
    "tool0",
)

REQUIRED_SITES = (
    "peg_tip",
    "eef_site",
    "hole_site",
)

REQUIRED_CAMERAS = (
    "overview",
    "wrist_cam",
)

REQUIRED_GEOMS = (
    "table_top",
    "peg_geom",
    "hole_plate",
    "hole_north",
    "hole_south",
    "hole_east",
    "hole_west",
)


@dataclass(frozen=True)
class RobotModelReport:
    model_path: Path
    valid: bool
    missing: dict[str, list[str]]
    counts: dict[str, int]
    warnings: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_path": str(self.model_path),
            "valid": self.valid,
            "missing": self.missing,
            "counts": self.counts,
            "warnings": self.warnings,
        }


def named_id(model: mujoco.MjModel, object_type: mujoco.mjtObj, name: str) -> int:
    return mujoco.mj_name2id(model, object_type, name)


def missing_names(model: mujoco.MjModel, object_type: mujoco.mjtObj, names: tuple[str, ...]) -> list[str]:
    return [name for name in names if named_id(model, object_type, name) < 0]


def validate_robot_model(model_path: str | Path) -> RobotModelReport:
    path = Path(model_path)
    warnings: list[str] = []
    model = mujoco.MjModel.from_xml_path(str(path))

    missing = {
        "joints": missing_names(model, mujoco.mjtObj.mjOBJ_JOINT, REQUIRED_JOINTS),
        "actuators": missing_names(model, mujoco.mjtObj.mjOBJ_ACTUATOR, REQUIRED_ACTUATORS),
        "bodies": missing_names(model, mujoco.mjtObj.mjOBJ_BODY, REQUIRED_BODIES),
        "sites": missing_names(model, mujoco.mjtObj.mjOBJ_SITE, REQUIRED_SITES),
        "cameras": missing_names(model, mujoco.mjtObj.mjOBJ_CAMERA, REQUIRED_CAMERAS),
        "geoms": missing_names(model, mujoco.mjtObj.mjOBJ_GEOM, REQUIRED_GEOMS),
    }

    hole_body_id = named_id(model, mujoco.mjtObj.mjOBJ_BODY, "hole_body")
    if hole_body_id >= 0 and int(model.body_mocapid[hole_body_id]) < 0:
        warnings.append("hole_body exists but is not a mocap body.")

    counts = {
        "nq": int(model.nq),
        "nv": int(model.nv),
        "nu": int(model.nu),
        "nbody": int(model.nbody),
        "njnt": int(model.njnt),
        "ngeom": int(model.ngeom),
        "nsite": int(model.nsite),
        "ncam": int(model.ncam),
    }
    valid = all(not values for values in missing.values()) and not warnings
    return RobotModelReport(
        model_path=path,
        valid=valid,
        missing=missing,
        counts=counts,
        warnings=warnings,
    )


def write_robot_model_report(path: Path, report: RobotModelReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Robot Model Compatibility Report",
        "",
        f"- Model path: `{report.model_path}`",
        f"- Compatible with current task interface: `{report.valid}`",
        "",
        "## Counts",
        "",
        "| Field | Value |",
        "| --- | ---: |",
    ]
    for key, value in report.counts.items():
        lines.append(f"| {key} | {value} |")

    lines.extend(
        [
            "",
            "## Missing Required Names",
            "",
            "| Category | Missing |",
            "| --- | --- |",
        ]
    )
    for category, values in report.missing.items():
        missing_text = ", ".join(values) if values else "-"
        lines.append(f"| {category} | {missing_text} |")

    lines.extend(["", "## Warnings", ""])
    if report.warnings:
        lines.extend(f"- {warning}" for warning in report.warnings)
    else:
        lines.append("- None")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
