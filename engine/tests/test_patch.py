"""s2.5.2 patch rules P1-P6 and the OS support overlay. Healthy fixture:
collected_at 2026-11-14, newest hotfix 2026-11-05 (9 days), build 22631, no
pending reboot. Baseline: win11 min build 22631, Windows 10 EOS 2025-10-14."""

import pytest

from antigravity_engine.scoring import patch
from antigravity_engine.scoring.fixes import resolve
from antigravity_engine.scoring.result import MAX_EXPLANATION

WIN10_SENTENCE = (
    "Windows 10 support ended on 14 Oct 2025 unless you've enrolled in Extended Security Updates."
)
WIN10 = {"host": {"os_build": "19045", "os_caption": "Microsoft Windows 10 Pro"}}


def _row(result, label):
    return next(r for r in result.evidence if r.label == label)


def _labels(result):
    return [r.label for r in result.evidence]


# --- 30/60 heuristic (examples from s2.10, plus fix ids) ---


@pytest.mark.parametrize(
    ("latest", "expected", "fixes"),
    [
        ("2026-11-14", "green", ()),                       # 0 days
        ("2026-11-05", "green", ()),                       # 9 days before collected_at
        ("2026-10-15", "green", ()),                       # 30 days - inclusive green
        ("2026-10-14", "amber", ("install-updates",)),     # 31 days
        ("2026-09-15", "amber", ("install-updates",)),     # 60 days
        ("2026-09-14", "red", ("install-updates",)),       # 61 days - stale hotfix
    ],
)
def test_30_60_heuristic(make_scan, baseline, latest, expected, fixes):
    s = make_scan({"patch": {"latest_hotfix_installed_on": latest,
                             "days_since_latest_hotfix": None}})
    r = patch.score(s, baseline)
    assert r.status == expected
    assert r.fix_ids == fixes


# --- P1 ---


def test_p1_unavailable_passes_through(make_scan, baseline):
    r = patch.score(make_scan({"patch": {"status": "unavailable",
                                         "error": "Requires administrator rights"}}), baseline)
    assert r.status == "unavailable"
    assert r.fix_ids == ()


def test_p1_failed_passes_through(make_scan, baseline):
    r = patch.score(make_scan({"patch": {"status": "failed", "error": "Get-HotFix timed out"}}),
                    baseline)
    assert r.status == "failed"
    assert "Get-HotFix timed out" in r.explanation


def test_p1_wins_over_os_overlay(make_scan, baseline):
    r = patch.score(make_scan({**WIN10, "patch": {"status": "failed", "error": "x"}}), baseline)
    assert r.status == "failed"
    assert r.fix_ids == ()


# --- P2 ---


def test_no_hotfixes_is_red(make_scan, baseline):
    s = make_scan({"patch": {"hotfix_count": 0, "latest_hotfix_installed_on": None,
                             "days_since_latest_hotfix": None, "hotfixes": []}})
    r = patch.score(s, baseline)
    assert r.status == "red"
    assert r.fix_ids == ("install-updates",)
    assert _row(r, "Newest Windows update").value == "None found"


def test_p2_zero_count_is_red_even_with_a_date(make_scan, baseline):
    r = patch.score(make_scan({"patch": {"hotfix_count": 0}}), baseline)
    assert r.status == "red"
    assert r.fix_ids == ("install-updates",)


def test_p2_null_date_is_red_even_with_a_count(make_scan, baseline):
    s = make_scan({"patch": {"latest_hotfix_installed_on": None, "days_since_latest_hotfix": None}})
    r = patch.score(s, baseline)
    assert r.status == "red"


# --- s2.4 rule 5: engine recomputes days ---


def test_engine_recomputes_days_ignoring_collector_value(make_scan, baseline):
    s = make_scan({"patch": {"latest_hotfix_installed_on": "2026-08-01",
                             "days_since_latest_hotfix": 3}})  # collector lied/bugged
    r = patch.score(s, baseline)
    assert r.status == "red"
    note = _row(r, "Note")
    assert "3 days" in note.value and "105 days" in note.value


def test_collector_overstating_age_does_not_make_it_red(make_scan, baseline):
    r = patch.score(make_scan({"patch": {"days_since_latest_hotfix": 90}}), baseline)
    assert r.status == "green"
    assert "Note" in _labels(r)


@pytest.mark.parametrize("reported", [8, 9, 10])
def test_one_day_disagreement_adds_no_note(make_scan, baseline, reported):
    r = patch.score(make_scan({"patch": {"days_since_latest_hotfix": reported}}), baseline)
    assert "Note" not in _labels(r)


def test_two_day_disagreement_adds_note(make_scan, baseline):
    r = patch.score(make_scan({"patch": {"days_since_latest_hotfix": 11}}), baseline)
    assert "Note" in _labels(r)


# --- P5 / P6 ---


def test_pending_reboot_downgrades_green(make_scan, baseline):
    r = patch.score(make_scan({"patch": {"pending_reboot": True}}), baseline)
    assert r.status == "amber"
    assert r.fix_ids == ("restart-to-finish-updates",)
    assert _row(r, "Restart needed to finish updates").value == "Yes"


def test_pending_reboot_on_stale_patches_attaches_install_only(make_scan, baseline):
    # First match wins: P4 fires before P5 can.
    s = make_scan({"patch": {"latest_hotfix_installed_on": "2026-10-01",
                             "days_since_latest_hotfix": None, "pending_reboot": True}})
    r = patch.score(s, baseline)
    assert r.status == "amber"
    assert r.fix_ids == ("install-updates",)


def test_p6_green_evidence(make_scan, baseline):
    r = patch.score(make_scan(), baseline)
    assert r.status == "green"
    assert r.fix_ids == ()
    assert _row(r, "Newest Windows update").value == "5 Nov 2026 (9 days ago), KB5044285"
    assert _row(r, "Updates installed").value == "14 updates"
    assert _row(r, "Windows version").status == "green"


def test_unknown_pending_reboot_is_grey_and_still_green(make_scan, baseline):
    r = patch.score(make_scan({"patch": {"pending_reboot": None}}), baseline)
    assert r.status == "green"
    row = _row(r, "Restart needed to finish updates")
    assert row.value == "Not checked" and row.status == "unavailable"


# --- OS support overlay ---


def test_windows10_is_at_least_amber(make_scan, baseline):
    r = patch.score(make_scan(WIN10), baseline)
    assert r.status == "amber" and "plan-windows-11" in r.fix_ids
    assert WIN10_SENTENCE in r.explanation
    assert _row(r, "Windows version").status == "amber"


def test_windows10_keeps_red_and_marks_plan_fix_amber(make_scan, baseline):
    s = make_scan({**WIN10, "patch": {"latest_hotfix_installed_on": "2026-08-01",
                                      "days_since_latest_hotfix": None}})
    r = patch.score(s, baseline)
    assert r.status == "red"  # overlay never improves a result
    assert r.fix_ids == ("install-updates", "plan-windows-11")
    fixes, _ = resolve(r.fix_pairs())
    assert {f["id"]: f["severity"] for f in fixes} == {"install-updates": "red",
                                                      "plan-windows-11": "amber"}
    assert WIN10_SENTENCE in r.explanation


def test_windows10_with_pending_reboot_attaches_both(make_scan, baseline):
    r = patch.score(make_scan({**WIN10, "patch": {"pending_reboot": True}}), baseline)
    assert r.status == "amber"
    assert r.fix_ids == ("restart-to-finish-updates", "plan-windows-11")


def test_win11_build_below_minimum_is_amber(make_scan, baseline):
    r = patch.score(make_scan({"host": {"os_build": "22000"}}), baseline)
    assert r.status == "amber"
    assert r.fix_ids == ("plan-windows-11",)
    assert "no longer supported" in r.explanation
    assert WIN10_SENTENCE not in r.explanation


@pytest.mark.parametrize("build", ["22631", "26100"])
def test_supported_win11_builds_are_not_flagged(make_scan, baseline, build):
    r = patch.score(make_scan({"host": {"os_build": build}}), baseline)
    assert r.status == "green"
    assert "plan-windows-11" not in r.fix_ids


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        WIN10,
        {**WIN10, "patch": {"latest_hotfix_installed_on": "2000-01-01",
                            "days_since_latest_hotfix": 3}},
        {**WIN10, "patch": {"hotfix_count": 0, "latest_hotfix_installed_on": None,
                            "days_since_latest_hotfix": None, "hotfixes": []}},
        {**WIN10, "patch": {"pending_reboot": True}},
        {"host": {"os_build": "22000"}, "patch": {"latest_hotfix_installed_on": "2026-10-01"}},
    ],
)
def test_explanation_and_evidence_within_limits(make_scan, baseline, overrides):
    r = patch.score(make_scan(overrides), baseline)
    assert 0 < len(r.explanation) <= MAX_EXPLANATION
    assert 1 <= len(r.evidence) <= 8
