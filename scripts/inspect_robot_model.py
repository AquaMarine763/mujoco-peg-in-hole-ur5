from __future__ import annotations

import argparse
import json
from pathlib import Path

from peg_in_hole_mujoco.robot_model import validate_robot_model, write_robot_model_report
from peg_in_hole_mujoco.paths import DEFAULT_MODEL_PATH


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect whether an MJCF model satisfies the peg-in-hole task interface.")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output-md", type=Path, default=Path("results/robot_model_current.md"))
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--fail-on-missing", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = validate_robot_model(args.model_path)
    write_robot_model_report(args.output_md, report)
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report.as_dict(), indent=2), encoding="utf-8")

    print(f"model_path={report.model_path}")
    print(f"compatible={report.valid}")
    for category, values in report.missing.items():
        print(f"missing_{category}={','.join(values) if values else '-'}")
    if report.warnings:
        for warning in report.warnings:
            print(f"warning={warning}")
    print(f"saved report to {args.output_md}")

    if args.fail_on_missing and not report.valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
