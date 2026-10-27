"""Resolve bundled files for the frozen (PyInstaller) build and for dev (s2.12)."""

import sys
from pathlib import Path

# engine/antigravity_engine/paths.py -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def resource(rel: str) -> Path:
    """Frozen: <_MEIPASS>/rel. Dev: <repo>/shared/rel."""
    if _frozen():
        return Path(sys._MEIPASS) / rel
    return _REPO_ROOT / "shared" / rel


def schema_path(name: str) -> Path:
    """e.g. schema_path("scan.schema.json"); engine.spec bundles schemas under contract/."""
    return resource(f"contract/{name}")


def default_baseline_path() -> Path:
    """Frozen: <exe_dir>/../baseline/. Dev: <repo>/baseline/."""
    if _frozen():
        return Path(sys.executable).resolve().parent.parent / "baseline" / "software-baseline.json"
    return _REPO_ROOT / "baseline" / "software-baseline.json"
