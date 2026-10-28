"""End-to-end checks over the shared fixtures (s0.7, s2.10, s7.6).

Each scan.*.json runs through the CLI in-process; report.json must validate
against report.schema.json and carry the RAG that s0.7 expects.
"""

import json
import warnings

import pytest

from antigravity_engine import __main__ as cli
from antigravity_engine.parser import parse_path, validate_schema
from antigravity_engine.scoring import backup, patch, recovery, software
from antigravity_engine.scoring.result import ClippedWarning
from conftest import FIXTURES

SCORERS = (backup, patch, software, recovery)
SCAN_FIXTURES = sorted(FIXTURES.glob("scan.*.json"))
XSS_NAME = "<script>alert(1)</script><img src=x onerror=alert(2)>"

ALL_GREEN = {c: "green" for c in ("backup", "patch", "software", "protection", "recovery")}

# s0.7 expected RAG per fixture: (overall, {category: status}).
EXPECTED = {
    "healthy": ("green", ALL_GREEN),
    "no-bitlocker": ("red", {**ALL_GREEN, "protection": "red"}),
    "home-edition": ("amber", {**ALL_GREEN, "protection": "amber"}),
    "defender-off": (
        "red",
        {"backup": "amber", "patch": "amber", "software": "red",
         "protection": "red", "recovery": "green"},
    ),
    "xss": ("green", ALL_GREEN),
}


def _name(path) -> str:
    return path.name.removeprefix("scan.").removesuffix(".json")


def _run(path, out_dir, *extra) -> dict:
    assert cli.main(["--in", str(path), "--out", str(out_dir), *extra]) == cli.EXIT_OK
    return json.loads((out_dir / cli.REPORT_JSON).read_text(encoding="utf-8"))


def test_every_fixture_has_an_expectation():
    assert {_name(p) for p in SCAN_FIXTURES} == set(EXPECTED)


@pytest.mark.parametrize("path", SCAN_FIXTURES, ids=_name)
def test_report_validates_and_matches_expected_rag(path, tmp_path):
    report = _run(path, tmp_path, "--json-only")
    validate_schema(report, "report.schema.json")
    overall, categories = EXPECTED[_name(path)]
    assert {c["id"]: c["status"] for c in report["categories"]} == categories
    assert report["overall"] == overall


def test_home_edition_protection_fix_is_encrypt_device_home(tmp_path):
    report = _run(FIXTURES / "scan.home-edition.json", tmp_path, "--json-only")
    protection = next(c for c in report["categories"] if c["id"] == "protection")
    assert protection["fix_ids"] == ["encrypt-device-home"]


def test_xss_name_is_escaped_in_html(tmp_path):
    report = _run(FIXTURES / "scan.xss.json", tmp_path)
    assert report["overall"] == "green"
    # The app isn't on the watch list, so the page only counts it; escaping of the
    # name itself when it is printed is covered in test_render.py.
    page = (tmp_path / cli.REPORT_HTML).read_text(encoding="utf-8")
    assert XSS_NAME not in page
    assert "<script>alert" not in page
    assert "<img" not in page


@pytest.mark.parametrize("path", SCAN_FIXTURES, ids=lambda p: p.name)
def test_no_fixture_needs_clipping(path, baseline):
    scan = parse_path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ClippedWarning)
        for scorer in SCORERS:
            scorer.score(scan, baseline)
