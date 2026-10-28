"""Report integrity (s7.6 RPT-01, RPT-02, RPT-03, RPT-06) over every fixture.

Each scan.*.json is checked as is and with each collector section in turn
forced to "unavailable" and to "failed", so RPT-01 is exercised in both
directions. The ranking and ordering rules are restated here from s0.8
rather than imported, so the tests do not trust the code they check.
"""

import copy
import json

import pytest

from antigravity_engine.__main__ import assess
from antigravity_engine.parser import parse_dict, validate_schema
from antigravity_engine.scoring import protection
from conftest import FIXTURES

CATEGORY_ORDER = ["backup", "patch", "software", "protection", "recovery"]
FIX_CATEGORY_RANK = {"protection": 0, "backup": 1, "patch": 2, "recovery": 3, "software": 4}
SEVERITY_RANK = {"red": 0, "amber": 1}
RAG_RANK = {"green": 0, "amber": 1, "red": 2}
GREY = ("unavailable", "failed")

PROTECTION_ROWS = {
    "defender": protection.DEFENDER,
    "bitlocker": protection.BITLOCKER,
    "cfa": protection.CFA,
    "asr": protection.ASR,
}
SECTIONS = [("backup",), ("patch",), ("software",), ("recovery",)] + [
    ("protection", sub) for sub in PROTECTION_ROWS
]


def _scans() -> list:
    cases = []
    for path in sorted(FIXTURES.glob("scan.*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        name = path.name.removeprefix("scan.").removesuffix(".json")
        cases.append(pytest.param(raw, id=name))
        for section in SECTIONS:
            for status in GREY:
                variant = copy.deepcopy(raw)
                target = variant
                for key in section:
                    target = target[key]
                target.update(status=status, error=f"forced {status}")
                cases.append(pytest.param(variant, id=f"{name}-{'.'.join(section)}-{status}"))
    return cases


SCANS = _scans()


@pytest.fixture(params=SCANS)
def pair(request, baseline):
    raw = request.param
    report = assess(parse_dict(raw), baseline)
    validate_schema(report, "report.schema.json")
    return raw, report


def _category(report: dict, category_id: str) -> dict:
    return next(c for c in report["categories"] if c["id"] == category_id)


# --- RPT-01: unavailable and failed never swap ---


@pytest.mark.parametrize("section", ["backup", "patch", "software", "recovery"])
def test_status_mapping_whole_sections(pair, section):
    raw, report = pair
    source = raw[section]["status"]
    cat = _category(report, section)
    if source in GREY:
        assert cat["status"] == source
    else:
        assert cat["status"] != "failed"
        assert all(row.get("status") != "failed" for row in cat["evidence"])


def test_status_mapping_protection_rows(pair):
    raw, report = pair
    cat = _category(report, "protection")
    rows = {row["label"]: row for row in cat["evidence"]}
    sources = {sub: raw["protection"][sub]["status"] for sub in PROTECTION_ROWS}
    home = raw["host"]["os_edition"].startswith("Core")

    for sub, source in sources.items():
        status = rows[PROTECTION_ROWS[sub]].get("status")
        if source == "failed":
            assert status == "failed"
        elif source == "unavailable":
            # Home BitLocker is rated amber, not grey (s2.5.4).
            allowed = {"unavailable", "amber"} if sub == "bitlocker" and home else {"unavailable"}
            assert status in allowed
        else:
            assert status != "failed"

    if all(s == "failed" for s in sources.values()):
        assert cat["status"] == "failed"
    else:
        assert cat["status"] != "failed"


# --- RPT-02: every finding cites evidence ---


def test_findings_cite_evidence(pair):
    _, report = pair
    for cat in report["categories"]:
        if cat["status"] in SEVERITY_RANK:
            assert len(cat["evidence"]) >= 1, cat["id"]
            assert any(row.get("status") == cat["status"] for row in cat["evidence"]), cat["id"]


# --- RPT-03: every finding has a fix ---


def test_findings_have_fixes(pair):
    _, report = pair
    fix_ids = {f["id"] for f in report["fixes"]}
    for cat in report["categories"]:
        if cat["status"] in SEVERITY_RANK:
            assert cat["fix_ids"], cat["id"]
            assert set(cat["fix_ids"]) <= fix_ids, cat["id"]


def test_every_fix_is_referenced_by_a_category(pair):
    _, report = pair
    referenced = {fid for cat in report["categories"] for fid in cat["fix_ids"]}
    assert {f["id"] for f in report["fixes"]} == referenced


# --- RPT-06: report invariants ---


def test_five_categories_in_fixed_order(pair):
    _, report = pair
    assert [c["id"] for c in report["categories"]] == CATEGORY_ORDER


def test_overall_is_worst_rated(pair):
    _, report = pair
    rated = [c["status"] for c in report["categories"] if c["status"] in RAG_RANK]
    expected = max(rated, key=RAG_RANK.__getitem__) if rated else "amber"
    assert report["overall"] == expected


def _rank_key(fix: dict) -> tuple:
    return (SEVERITY_RANK[fix["severity"]], FIX_CATEGORY_RANK[fix["category"]],
            fix["effort_minutes"])


def test_top_fixes_are_ranked_subset(pair):
    _, report = pair
    top = report["top_fixes"]
    fixes = {f["id"]: f for f in report["fixes"]}
    assert len(top) <= 3
    assert len(set(top)) == len(top)
    assert set(top) <= set(fixes)
    best = sorted(_rank_key(f) for f in fixes.values())[: len(top)]
    assert [_rank_key(fixes[fid]) for fid in top] == best
    assert len(top) == min(3, len(fixes))


def test_top_fixes_empty_only_without_findings(pair):
    _, report = pair
    has_finding = any(c["status"] in SEVERITY_RANK for c in report["categories"])
    assert bool(report["top_fixes"]) == has_finding
