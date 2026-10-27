import copy
import json
from pathlib import Path

import pytest

from antigravity_engine.parser import parse_dict
from antigravity_engine.baseline import load_baseline

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "shared" / "fixtures"


def _deep_merge(base: dict, patch: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


@pytest.fixture(scope="session")
def healthy_raw() -> dict:
    return json.loads((FIXTURES / "scan.healthy.json").read_text(encoding="utf-8"))


@pytest.fixture
def make_scan(healthy_raw):
    """make_scan({"patch": {"days_since_latest_hotfix": 70}}) -> ScanModel"""

    def _make(patch: dict | None = None):
        return parse_dict(_deep_merge(healthy_raw, patch or {}))

    return _make


@pytest.fixture(scope="session")
def baseline():
    return load_baseline(ROOT / "baseline" / "software-baseline.json")


# --- helpers beyond s2.10, used by the phase 1-3 tests ---


@pytest.fixture
def make_raw(healthy_raw):
    """make_raw({"patch": {"hotfixes": {}}}) -> dict (healthy fixture with overrides)"""

    def _make(patch: dict | None = None) -> dict:
        return _deep_merge(healthy_raw, patch or {})

    return _make


@pytest.fixture
def write_json(tmp_path):
    """Write a dict (or raw bytes) to a temp file and return its path."""

    def _write(data, name: str = "scan.json") -> Path:
        p = tmp_path / name
        p.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode("utf-8"))
        return p

    return _write
