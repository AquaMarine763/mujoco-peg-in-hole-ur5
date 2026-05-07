from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_ROOT = REPO_ROOT / "assets"

UR5E_MAINLINE_MODEL = ASSETS_ROOT / "ur5e_adapter" / "ur5e_peg_in_hole.xml"
UR5_LIKE_LEGACY_MODEL = ASSETS_ROOT / "ur5_peg_in_hole.xml"
DEFAULT_MODEL_PATH = UR5E_MAINLINE_MODEL


def resolve_model_path(model_path: str | Path | None = None) -> Path:
    if model_path is None:
        return DEFAULT_MODEL_PATH
    return Path(model_path)
