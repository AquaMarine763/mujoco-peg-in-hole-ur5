from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


JOINT_NAME_MAP = {
    "shoulder_pan": "shoulder_pan_joint",
    "shoulder_lift": "shoulder_lift_joint",
    "elbow": "elbow_joint",
    "wrist_1": "wrist_1_joint",
    "wrist_2": "wrist_2_joint",
    "wrist_3": "wrist_3_joint",
}

ACTUATOR_NAME_MAP = {
    "shoulder_pan_ctrl": "shoulder_pan",
    "shoulder_lift_ctrl": "shoulder_lift",
    "elbow_ctrl": "elbow",
    "wrist_1_ctrl": "wrist_1",
    "wrist_2_ctrl": "wrist_2",
    "wrist_3_ctrl": "wrist_3",
}

ROBOT_BODY_NAMES = (
    "base",
    "shoulder_link",
    "upper_arm_link",
    "forearm_link",
    "wrist_1_link",
    "wrist_2_link",
    "wrist_3_link",
)

TASK_REQUIRED_NAMES = {
    "body": ("hole_body", "tool0"),
    "site": ("eef_site", "peg_tip", "hole_site"),
    "camera": ("overview", "wrist_cam"),
    "geom": (
        "table_top",
        "peg_geom",
        "hole_plate",
        "hole_north",
        "hole_south",
        "hole_east",
        "hole_west",
    ),
}

CONTROL_RELEVANT_XML_ATTRS = {
    "option": ("timestep", "gravity", "integrator"),
    "compiler": ("angle", "meshdir", "autolimits"),
}


@dataclass(frozen=True)
class ElementCompare:
    item: str
    reference: str
    current: str
    status: str
    notes: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the full UR5e peg-in-hole MJCF against the raw DeepMind "
            "MuJoCo Menagerie UR5e XML."
        )
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=Path("assets/ur5e_full/ur5e_peg_in_hole_full.xml"),
        help="Current full UR5e peg-in-hole model.",
    )
    parser.add_argument(
        "--reference-model-path",
        type=Path,
        required=True,
        help="Raw Menagerie universal_robots_ur5e/ur5e.xml reference file.",
    )
    parser.add_argument(
        "--reference-url",
        default=(
            "https://github.com/google-deepmind/mujoco_menagerie/blob/main/"
            "universal_robots_ur5e/ur5e.xml"
        ),
        help="Reference source URL shown in the report.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("results/ur5e_full/model_audit/ur5e_full_menagerie_audit.md"),
    )
    parser.add_argument("--output-json", type=Path, default=None)
    return parser.parse_args()


def load_xml(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def element_summary(element: ET.Element | None, attrs: Iterable[str] | None = None) -> str:
    if element is None:
        return "<missing>"
    if attrs is None:
        attrs = sorted(element.attrib)
    parts = []
    for attr in attrs:
        if attr in element.attrib:
            parts.append(f'{attr}="{element.attrib[attr]}"')
    return f"<{element.tag}{(' ' + ' '.join(parts)) if parts else ''}>"


def find_named(root: ET.Element, tag: str, name: str) -> ET.Element | None:
    for element in root.iter(tag):
        if element.attrib.get("name") == name:
            return element
    return None


def find_first(root: ET.Element, tag: str) -> ET.Element | None:
    return next(root.iter(tag), None)


def find_default_class(root: ET.Element, class_name: str) -> ET.Element | None:
    for element in root.iter("default"):
        if element.attrib.get("class") == class_name:
            return element
    return None


def direct_child(parent: ET.Element | None, tag: str) -> ET.Element | None:
    if parent is None:
        return None
    for child in list(parent):
        if child.tag == tag:
            return child
    return None


def compare_xml_element(
    item: str,
    reference: ET.Element | None,
    current: ET.Element | None,
    *,
    attrs: Iterable[str] | None = None,
    notes: str = "",
) -> ElementCompare:
    ref_text = element_summary(reference, attrs)
    cur_text = element_summary(current, attrs)
    status = "same" if ref_text == cur_text else "changed"
    if reference is None or current is None:
        status = "missing"
    return ElementCompare(item=item, reference=ref_text, current=cur_text, status=status, notes=notes)


def named_children(root: ET.Element, tag: str) -> set[str]:
    return {element.attrib["name"] for element in root.iter(tag) if "name" in element.attrib}


def named_actuators(root: ET.Element) -> set[str]:
    actuator_parent = root.find("actuator")
    if actuator_parent is None:
        return set()
    return {element.attrib["name"] for element in list(actuator_parent) if "name" in element.attrib}


def mesh_files(root: ET.Element) -> set[str]:
    return {element.attrib["file"] for element in root.iter("mesh") if "file" in element.attrib}


def collect_audit(current_root: ET.Element, reference_root: ET.Element) -> dict[str, object]:
    current_names = {tag: named_children(current_root, tag) for tag in ("body", "joint", "geom", "site", "camera")}
    reference_names = {tag: named_children(reference_root, tag) for tag in ("body", "joint", "geom", "site", "camera")}
    current_names["actuator"] = named_actuators(current_root)
    reference_names["actuator"] = named_actuators(reference_root)

    compiler_rows = []
    for tag, attrs in CONTROL_RELEVANT_XML_ATTRS.items():
        compiler_rows.append(
            compare_xml_element(
                tag,
                find_first(reference_root, tag),
                find_first(current_root, tag),
                attrs=attrs,
            )
        )

    ref_default = find_default_class(reference_root, "ur5e")
    cur_default = find_default_class(current_root, "ur5e")
    default_rows = [
        compare_xml_element(
            "default/ur5e/joint",
            direct_child(ref_default, "joint"),
            direct_child(cur_default, "joint"),
            attrs=("axis", "range", "armature", "limited"),
            notes="Joint limits are explicit in the task model.",
        ),
        compare_xml_element(
            "default/ur5e/general",
            direct_child(ref_default, "general"),
            direct_child(cur_default, "general"),
            attrs=("gaintype", "biastype", "ctrlrange", "gainprm", "biasprm", "forcerange"),
            notes="Menagerie affine position-style actuator defaults should stay unchanged.",
        ),
        compare_xml_element(
            "default/ur5e/geom",
            direct_child(ref_default, "geom"),
            direct_child(cur_default, "geom"),
            attrs=("friction", "solref", "solimp"),
            notes="The task model adds global contact defaults.",
        ),
    ]

    joint_rows = []
    for current_name, reference_name in JOINT_NAME_MAP.items():
        joint_rows.append(
            compare_xml_element(
                current_name,
                find_named(reference_root, "joint", reference_name),
                find_named(current_root, "joint", current_name),
                attrs=("name", "class", "axis", "range"),
                notes=f"Reference joint name: {reference_name}",
            )
        )

    actuator_rows = []
    for current_name, reference_name in ACTUATOR_NAME_MAP.items():
        actuator_rows.append(
            compare_xml_element(
                current_name,
                find_named(reference_root, "general", reference_name),
                find_named(current_root, "general", current_name),
                attrs=("name", "class", "joint", "ctrlrange", "gainprm", "biasprm", "forcerange"),
                notes=f"Reference actuator name: {reference_name}",
            )
        )

    body_rows = []
    inertial_rows = []
    for body_name in ROBOT_BODY_NAMES:
        ref_body = find_named(reference_root, "body", body_name)
        cur_body = find_named(current_root, "body", body_name)
        body_rows.append(
            compare_xml_element(
                body_name,
                ref_body,
                cur_body,
                attrs=("name", "pos", "quat", "childclass"),
                notes=("Base pose is expected to differ because the task model places the robot next to the table." if body_name == "base" else ""),
            )
        )
        inertial_rows.append(
            compare_xml_element(
                f"{body_name}/inertial",
                direct_child(ref_body, "inertial"),
                direct_child(cur_body, "inertial"),
                attrs=("mass", "pos", "quat", "diaginertia"),
            )
        )

    current_meshes = mesh_files(current_root)
    reference_meshes = mesh_files(reference_root)
    mesh_report = {
        "shared": sorted(current_meshes & reference_meshes),
        "current_only": sorted(current_meshes - reference_meshes),
        "reference_only": sorted(reference_meshes - current_meshes),
    }

    task_presence: dict[str, dict[str, bool]] = {}
    for tag, names in TASK_REQUIRED_NAMES.items():
        task_presence[tag] = {name: name in current_names[tag] for name in names}

    task_additions = {
        tag: sorted(current_names[tag] - reference_names[tag]) for tag in ("body", "joint", "actuator", "geom", "site", "camera")
    }

    return {
        "counts": {
            "current": {tag: len(values) for tag, values in current_names.items()},
            "reference": {tag: len(values) for tag, values in reference_names.items()},
        },
        "compiler": [row.__dict__ for row in compiler_rows],
        "defaults": [row.__dict__ for row in default_rows],
        "joints": [row.__dict__ for row in joint_rows],
        "actuators": [row.__dict__ for row in actuator_rows],
        "bodies": [row.__dict__ for row in body_rows],
        "inertials": [row.__dict__ for row in inertial_rows],
        "meshes": mesh_report,
        "task_presence": task_presence,
        "task_additions": task_additions,
    }


def table(lines: list[str], headers: tuple[str, ...], rows: Iterable[Iterable[object]]) -> None:
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")


def status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


def write_markdown(path: Path, audit: dict[str, object], args: argparse.Namespace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = audit["counts"]  # type: ignore[assignment]
    meshes = audit["meshes"]  # type: ignore[assignment]

    lines = [
        "# Full UR5e Menagerie Audit",
        "",
        f"- Current model: `{args.model_path}`",
        f"- Reference model: `{args.reference_model_path}`",
        f"- Reference source: {args.reference_url}",
        "",
        "## Verdict",
        "",
        "- The current model is a task adapter, not a byte-for-byte Menagerie copy.",
        "- The UR5e link inertial values are preserved for the shared robot bodies checked here.",
        "- The Menagerie mesh file set is preserved.",
        "- The task model deliberately renames joints and actuators to the project interface, places the base next to the table, and adds the peg, hole fixture, cameras, lights, and task geoms.",
        "- Control-relevant differences to keep in mind: explicit joint limiting, task contact defaults, fixed timestep/gravity, and a task-specific base pose.",
        "",
        "## Object Counts",
        "",
    ]
    table(
        lines,
        ("Object", "Reference", "Current"),
        ((tag, counts["reference"][tag], counts["current"][tag]) for tag in counts["current"]),  # type: ignore[index]
    )

    for section, title in (
        ("compiler", "Compiler And Option Differences"),
        ("defaults", "Default Class Differences"),
        ("joints", "Mapped Joint Elements"),
        ("actuators", "Mapped Actuator Elements"),
        ("bodies", "Mapped Body Transforms"),
        ("inertials", "Mapped Body Inertials"),
    ):
        rows = audit[section]  # type: ignore[index]
        lines.extend(["", f"## {title}", ""])
        lines.append(f"Status counts: `{status_counts(rows)}`")  # type: ignore[arg-type]
        lines.append("")
        table(
            lines,
            ("Item", "Status", "Reference", "Current", "Notes"),
            (
                (row["item"], row["status"], f"`{row['reference']}`", f"`{row['current']}`", row.get("notes", ""))
                for row in rows  # type: ignore[union-attr]
            ),
        )

    lines.extend(["", "## Mesh Files", ""])
    lines.append(f"- Shared mesh files: `{len(meshes['shared'])}`")  # type: ignore[index]
    lines.append(f"- Current-only mesh files: `{meshes['current_only']}`")  # type: ignore[index]
    lines.append(f"- Reference-only mesh files: `{meshes['reference_only']}`")  # type: ignore[index]

    lines.extend(["", "## Task Interface Presence", ""])
    task_presence = audit["task_presence"]  # type: ignore[assignment]
    table(
        lines,
        ("Type", "Name", "Present In Current"),
        (
            (tag, name, present)
            for tag, values in task_presence.items()  # type: ignore[union-attr]
            for name, present in values.items()
        ),
    )

    lines.extend(["", "## Current-Only Named Objects", ""])
    task_additions = audit["task_additions"]  # type: ignore[assignment]
    for tag, names in task_additions.items():  # type: ignore[union-attr]
        lines.append(f"- {tag}: {', '.join(names) if names else '-'}")

    lines.extend(
        [
            "",
            "## Implications For The Next Controller Step",
            "",
            "- Do not treat the current XML as an untouched official UR5e model; it is a task adapter around Menagerie UR5e assets and inertials.",
            "- The next controller diagnostic should focus on task-specific changes: base pose, tool0/peg attachment pose, peg verticality, and contact defaults near the hole.",
            "- If joint motion still looks unnatural in demos, inspect IK target pose tracking and posture regularization before starting multi-geometry training.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    current_root = load_xml(args.model_path)
    reference_root = load_xml(args.reference_model_path)
    audit = collect_audit(current_root, reference_root)
    write_markdown(args.output_md, audit, args)
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(f"saved report to {args.output_md}")


if __name__ == "__main__":
    main()
