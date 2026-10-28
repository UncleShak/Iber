"""paths.py resolves bundled files in dev and in the frozen one-folder build (s2.12)."""

import sys
from pathlib import Path

import pytest

from antigravity_engine import paths

SCHEMAS = ["scan.schema.json", "report.schema.json"]


@pytest.fixture
def frozen(monkeypatch, tmp_path):
    """Simulate PyInstaller: dist/engine/engine.exe with _internal/ as _MEIPASS."""
    exe_dir = tmp_path / "dist" / "engine"
    meipass = exe_dir / "_internal"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass), raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_dir / "engine.exe"))
    return exe_dir, meipass


@pytest.mark.parametrize("name", SCHEMAS)
def test_dev_schema_path_is_shared_contract(name):
    p = paths.schema_path(name)
    assert p == paths._REPO_ROOT / "shared" / "contract" / name
    assert p.is_file()


def test_dev_baseline_paths_exist():
    assert paths.baseline_schema_path().is_file()
    assert paths.default_baseline_path().is_file()


@pytest.mark.parametrize("name", SCHEMAS)
def test_frozen_schema_path_is_meipass_contract(frozen, name):
    _, meipass = frozen
    assert paths.schema_path(name) == meipass / "contract" / name


def test_frozen_baseline_schema_is_bundled_under_contract(frozen):
    _, meipass = frozen
    assert paths.baseline_schema_path() == meipass / "contract" / "software-baseline.schema.json"


def test_frozen_default_baseline_is_sibling_of_engine_folder(frozen):
    # Installed layout (s5.4): resources/engine/engine.exe -> resources/baseline/
    exe_dir, _ = frozen
    expected = exe_dir.parent / "baseline" / "software-baseline.json"
    assert paths.default_baseline_path() == Path(expected).resolve()


def test_meipass_without_frozen_flag_stays_dev(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert paths.schema_path("scan.schema.json").parent == paths._REPO_ROOT / "shared" / "contract"
