from datetime import UTC, datetime

import pytest

from antigravity_engine import __version__
from antigravity_engine.aggregator import order, overall
from antigravity_engine.parser import validate_schema
from antigravity_engine.report_model import ReportError, build_error_report, build_report
from antigravity_engine.risk import risk_score, summary
from antigravity_engine.scoring.fixes import resolve
from antigravity_engine.scoring.result import (
    CATEGORY_ORDER,
    RATED,
    TITLES,
    CategoryResult,
    EvidenceRow,
    Status,
    plain_explanation,
    plain_reason,
)

R = CategoryResult.rated
FIXED_NOW = datetime(2026, 11, 14, 17, 2, 46, tzinfo=UTC)

# A fix id that is valid for each category, for hand-built red/amber results.
FIX_FOR = {
    "backup": "turn-on-file-history",
    "patch": "install-updates",
    "software": "update-outdated-apps",
    "protection": "enable-defender",
    "recovery": "enable-winre",
}


def _result(cid, status):
    if status == "unavailable":
        return CategoryResult.unavailable(cid, "Requires administrator rights")
    if status == "failed":
        return CategoryResult.failed(cid, "RuntimeException: boom")
    fixes = [] if status == "green" else [FIX_FOR[cid]]
    return R(cid, status, f"{cid} is {status}.", fix_ids=fixes)


def _results(**statuses):
    """_results(backup="red") -> five results, unspecified ones green."""
    return [_result(c, statuses.get(c, "green")) for c in CATEGORY_ORDER]


def _report(scan, results):
    fixes, top = resolve(p for r in results for p in r.fix_pairs())
    return build_report(scan, results, fixes, top, overall(results), summary(results),
                        __version__, "2026-11-01", generated_at=FIXED_NOW)


# --- result types ----------------------------------------------------------


def test_status_values_and_rated_set():
    assert [s.value for s in Status] == ["red", "amber", "green", "unavailable", "failed"]
    assert RATED == {Status.RED, Status.AMBER, Status.GREEN}


@pytest.mark.parametrize("status", ["unavailable", "failed", Status.UNAVAILABLE, Status.FAILED])
def test_unrated_status_cannot_be_constructed_directly(status):
    with pytest.raises(ValueError):
        CategoryResult("backup", "Backup evidence", status, "x")
    with pytest.raises(ValueError):
        R("backup", status, "x")


def test_unrated_factories():
    u = CategoryResult.unavailable("protection", "Requires administrator rights")
    f = CategoryResult.failed("patch", "RuntimeException: boom")
    assert u.status == "unavailable" and not u.is_rated
    assert f.status == "failed" and not f.is_rated
    assert u.title == "Ransomware protections"
    assert "administrator" in u.explanation
    assert f.explanation == "This check couldn't run on this PC. (RuntimeException: boom)"
    assert f.evidence == () and f.fix_ids == ()


def test_failed_explanation_clipped_to_200():
    f = CategoryResult.failed("patch", "x" * 500)
    assert len(f.explanation) == 200


def test_unknown_status_rejected():
    with pytest.raises(ValueError):
        R("backup", "purple", "x")


def test_unknown_category_rejected():
    with pytest.raises(ValueError):
        R("printers", "green", "x")


def test_green_cannot_attach_fixes():
    with pytest.raises(ValueError):
        R("backup", "green", "x", fix_ids=["run-backup-now"])


def test_explanation_length_enforced():
    with pytest.raises(ValueError):
        R("backup", "green", "")
    with pytest.raises(ValueError):
        R("backup", "green", "x" * 201)


def test_evidence_capped_at_eight_rows():
    rows = [EvidenceRow(f"r{i}", "v") for i in range(9)]
    with pytest.raises(ValueError):
        R("backup", "green", "x", evidence=rows)


@pytest.mark.parametrize("error,expected", [
    ("Requires administrator rights", "Not checked \u2014 needs admin"),
    ("BitLocker management not available on Windows Home", "Not available on Windows Home"),
    ("Probe timed out after 20s", "Check timed out"),
    ("Get-BitLockerVolume not available", "Not available on this PC"),
    ("something unexpected", "Not checked"),
    (None, "Not checked"),
])
def test_plain_reason_maps_collector_errors(error, expected):
    assert plain_reason(error) == expected
    assert 0 < len(plain_explanation(error)) <= 200


# --- aggregator ------------------------------------------------------------


@pytest.mark.parametrize("statuses,expected", [
    ({}, "green"),
    ({"software": "amber"}, "amber"),
    ({"recovery": "amber", "patch": "red"}, "red"),
    ({"backup": "amber", "protection": "unavailable"}, "amber"),
    ({"backup": "failed", "patch": "unavailable"}, "green"),
])
def test_overall_is_worst_rated(statuses, expected):
    assert overall(_results(**statuses)) == expected


def test_all_unrated_is_amber():
    mixed = {c: ("unavailable" if i % 2 else "failed") for i, c in enumerate(CATEGORY_ORDER)}
    assert overall(_results(**mixed)) == "amber"
    assert overall(_results(**{c: "unavailable" for c in CATEGORY_ORDER})) == "amber"


def test_order_is_fixed():
    shuffled = list(reversed(_results()))
    assert [r.id for r in order(shuffled)] == ["backup", "patch", "software", "protection", "recovery"]


def test_order_rejects_missing_or_duplicate():
    with pytest.raises(ValueError):
        order(_results()[:4])
    with pytest.raises(ValueError):
        order(_results() + [_result("backup", "green")])


# --- risk score and summary (s2.6) -----------------------------------------


def test_risk_score_weights():
    assert risk_score(_results()) == 0
    assert risk_score(_results(protection="red")) == 30
    assert risk_score(_results(backup="amber", patch="amber")) == 25


def test_unrated_removed_from_numerator_and_denominator():
    # protection red (30) over backup + protection (60) rated -> 50.
    s = {"patch": "unavailable", "software": "failed", "recovery": "unavailable",
         "protection": "red"}
    assert risk_score(_results(**s)) == 50


def test_nothing_rated_has_no_score():
    assert risk_score(_results(**{c: "failed" for c in CATEGORY_ORDER})) is None


def test_summary_one_urgent_issue_singular():
    assert summary(_results(backup="red")) == "1 urgent issue needs attention this week."


def test_summary_urgent_issues_plural():
    assert summary(_results(backup="red", protection="red", software="amber")) == \
        "2 urgent issues need attention this week."


def test_summary_tighten_up_plural():
    assert summary(_results(backup="amber", patch="amber")) == \
        "No urgent issues, but 2 things to tighten up."


def test_summary_tighten_up_singular():
    # backup amber with only backup + recovery rated: 30*0.5/40 = 37.5 >= 25.
    s = {"patch": "unavailable", "software": "unavailable", "protection": "unavailable",
         "backup": "amber"}
    assert summary(_results(**s)) == "No urgent issues, but 1 thing to tighten up."


def test_summary_good_shape_below_25():
    # One amber protection: 15 < 25.
    assert summary(_results(protection="amber")) == "This PC is in good shape. Keep it that way."
    assert summary(_results()) == "This PC is in good shape. Keep it that way."


def test_summary_failed_suffix():
    assert summary(_results(backup="red", patch="failed")) == \
        "1 urgent issue needs attention this week. Some checks couldn't run."


def test_unavailable_does_not_add_failed_suffix():
    assert summary(_results(patch="unavailable")) == "This PC is in good shape. Keep it that way."


def test_summary_nothing_rated():
    assert summary(_results(**{c: "unavailable" for c in CATEGORY_ORDER})) == \
        "We couldn't check enough of this PC to rate it."
    assert summary(_results(**{c: "failed" for c in CATEGORY_ORDER})) == \
        "We couldn't check enough of this PC to rate it. Some checks couldn't run."


# --- report model ----------------------------------------------------------


@pytest.mark.parametrize("statuses", [
    {},
    {"backup": "red", "patch": "red", "protection": "red"},
    {"software": "amber", "recovery": "unavailable", "patch": "failed"},
    {c: "unavailable" for c in CATEGORY_ORDER},
    {c: "failed" for c in CATEGORY_ORDER},
])
def test_built_report_validates(make_scan, statuses):
    report = _report(make_scan(), _results(**statuses))
    validate_schema(report, "report.schema.json")
    assert [c["id"] for c in report["categories"]] == list(CATEGORY_ORDER)
    assert [c["title"] for c in report["categories"]] == [TITLES[c] for c in CATEGORY_ORDER]
    assert set(report["top_fixes"]) <= {f["id"] for f in report["fixes"]}


def test_report_fields(make_scan):
    scan = make_scan()
    results = _results(protection="red")
    results[3] = R("protection", "red", "Defender is off.",
                   evidence=[EvidenceRow("Defender antivirus", "Off", Status.RED),
                             EvidenceRow("BitLocker (C:)", "Not checked", None)],
                   fix_ids=["enable-defender"])
    report = _report(scan, results)
    assert report["schema_version"] == "1.0.0"
    assert report["run_id"] == scan.run_id
    assert report["generated_at"] == "2026-11-14T17:02:46Z"
    assert report["engine_version"] == __version__
    assert report["baseline_version"] == "2026-11-01"
    assert report["overall"] == "red"
    assert report["top_fixes"] == ["enable-defender"]
    assert report["scan"] == {"is_admin": scan.host.is_admin, "duration_ms": scan.duration_ms,
                              "os_caption": scan.host.os_caption}
    prot = report["categories"][3]
    assert prot["evidence"] == [
        {"label": "Defender antivirus", "value": "Off", "status": "red"},
        {"label": "BitLocker (C:)", "value": "Not checked"},
    ]


def test_report_rejects_fixes_not_matching_categories(make_scan):
    results = _results(backup="red")
    with pytest.raises(ReportError):
        build_report(make_scan(), results, [], [], "red", "x", "0", "b", generated_at=FIXED_NOW)


def test_report_rejects_top_fix_outside_fixes(make_scan):
    results = _results(backup="red")
    fixes, _ = resolve(p for r in results for p in r.fix_pairs())
    with pytest.raises(ReportError):
        build_report(make_scan(), results, fixes, ["enable-cfa"], "red", "x", "0", "b",
                     generated_at=FIXED_NOW)


def test_report_rejects_overlong_summary(make_scan):
    results = _results()
    with pytest.raises(ReportError):
        build_report(make_scan(), results, [], [], "green", "x" * 201, "0", "b",
                     generated_at=FIXED_NOW)


def test_error_report():
    report = build_error_report("not valid JSON: Expecting value at line 1 column 1",
                                __version__, "2026-11-01", generated_at=FIXED_NOW)
    validate_schema(report, "report.schema.json")
    assert [c["status"] for c in report["categories"]] == ["failed"] * 5
    assert all(c["evidence"] == [] and c["fix_ids"] == [] for c in report["categories"])
    assert report["fixes"] == [] and report["top_fixes"] == []
    assert report["overall"] == "amber"
    assert report["scan"] == {"is_admin": False, "duration_ms": 0, "os_caption": "Unknown"}
    assert "not valid JSON" in report["summary"]
    assert report["run_id"] == "2026-11-14T17-02-46Z_0000"


def test_error_report_keeps_valid_run_id_and_clips_summary():
    report = build_error_report("e" * 400, "0.1.0", "unknown",
                                run_id="2026-11-14T17-02-44Z_0003", generated_at=FIXED_NOW)
    assert report["run_id"] == "2026-11-14T17-02-44Z_0003"
    assert len(report["summary"]) == 200
