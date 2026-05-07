from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable


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


def load_flat_yaml(path: Path) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        config[normalize_key(key)] = parse_scalar(value)
    return config


def normalize_key(key: str) -> str:
    return key.strip().replace("-", "_")


def get_action_by_dest(parser: argparse.ArgumentParser) -> dict[str, argparse.Action]:
    return {
        action.dest: action
        for action in parser._actions
        if action.dest and action.dest != argparse.SUPPRESS
    }


def coerce_value(action: argparse.Action, value: Any) -> Any:
    if value is None:
        return None
    if isinstance(action, argparse._StoreTrueAction) or isinstance(action, argparse._StoreFalseAction):
        return bool(value)

    converter = action.type
    if converter is None:
        return value
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Path)):
        return [converter(item) for item in value]
    return converter(value)


def add_config_argument(parser: argparse.ArgumentParser) -> None:
    if "--config" not in parser._option_string_actions:
        parser.add_argument(
            "--config",
            type=Path,
            default=None,
            help="Optional flat YAML file that supplies argparse defaults.",
        )


def parse_args_with_config(parser: argparse.ArgumentParser) -> argparse.Namespace:
    add_config_argument(parser)
    config_probe = argparse.ArgumentParser(add_help=False)
    config_probe.add_argument("--config", type=Path, default=None)
    probe_args, _ = config_probe.parse_known_args()

    if probe_args.config is not None:
        config_path = probe_args.config
        if not config_path.exists():
            raise FileNotFoundError(f"config file not found: {config_path}")
        if config_path.suffix.lower() not in (".yaml", ".yml"):
            raise ValueError("sim config files must use .yaml or .yml")

        actions = get_action_by_dest(parser)
        defaults: dict[str, Any] = {}
        unknown_keys: list[str] = []
        for raw_key, raw_value in load_flat_yaml(config_path).items():
            key = normalize_key(raw_key)
            action = actions.get(key)
            if action is None:
                unknown_keys.append(raw_key)
                continue
            defaults[key] = coerce_value(action, raw_value)
            action.required = False

        if unknown_keys:
            keys = ", ".join(sorted(unknown_keys))
            raise ValueError(f"unknown config key(s) for {parser.prog}: {keys}")
        parser.set_defaults(**defaults)

    return parser.parse_args()
