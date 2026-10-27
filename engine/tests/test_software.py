"""s2.5.3 software rules S1-S7, evaluated S1, S7, S6, S2, S3, S4, S5 (D7).

Baseline minimums used here: Chrome 142.0.7444.175 (high), 7-Zip 25.00 (high),
Zoom 6.5.0 (medium), VLC 3.0.21 (medium). No shipped entry is eol, so the S2
tests use a copy of the baseline with one entry flipped.
"""

import copy
import json

import pytest

from antigravity_engine.baseline import baseline_from_dict
from antigravity_engine.scoring import software
from antigravity_engine.scoring.fixes import CATALOGUE, resolve
from antigravity_engine.scoring.result import CategoryResult, Status

from conftest import ROOT

FIX = "update-outdated-apps"

CHROME_OLD = {"name": "Google Chrome", "version": "118.0.5993.118", "publisher": "Google LLC"}
CHROME_NEW = {"name": "Google Chrome", "version": "142.0.7444.176", "publisher": "Google LLC"}
SEVEN_ZIP_NEW = {"name": "7-Zip 25.01 (x64)", "version": "25.01", "publisher": "Igor Pavlov"}
ZOOM_OLD = {"name": "Zoom Workplace (64-bit)", "version": "6.1.0",
            "publisher": "Zoom Video Communications, Inc."}
VLC_OLD = {"name": "VLC media player", "version": "3.0.18", "publisher": "VideoLAN"}
PASTEL = {"name": "Pastel Partner", "version": "1.0", "publisher": "Sage"}
NOTEPADPP = {"name": "Notepad++ (64-bit x64)", "version": "8.6", "publisher": "Notepad++ Team"}


def _with(make_scan, apps):
    return make_scan({"software": {"installed": apps}})


def _labels(result):
    return [row.label for row in result.evidence]


@pytest.fixture(scope="module")
def eol_baseline():
    """Shipped baseline with VLC marked end of life."""
    data = json.loads((ROOT / "baseline" / "software-baseline.json").read_text(encoding="utf-8"))
    data = copy.deepcopy(data)
    for e in data["entries"]:
        if e["id"] == "vlc":
            e["eol"] = True
            e["eol_note"] = "Test: no longer supported"
    return baseline_from_dict(data)


# --- examples from s2.10 ---


def test_outdated_high_severity_is_red(make_scan, baseline):
    s = _with(make_scan, [CHROME_OLD])
    assert software.score(s, baseline).status == "red"


def test_software_absent_from_baseline_is_not_assessed(make_scan, baseline):
    s = _with(make_scan, [PASTEL])
    r = software.score(s, baseline)
    assert r.status == "green"
    assert any("not on our watch list" in row.value for row in r.evidence)


def test_unparseable_version_does_not_crash(make_scan, baseline):
    s = _with(make_scan, [{"name": "Google Chrome", "version": "latest", "publisher": "Google LLC"}])
    r = software.score(s, baseline)
    assert r.status in {"green", "amber"}


def test_empty_list_is_amber(make_scan, baseline):
    assert software.score(_with(make_scan, []), baseline).status == "amber"


# --- S1 ---


def test_s1_unavailable_passes_through(make_scan, baseline):
    s = make_scan({"software": {"status": "unavailable", "error": "Requires administrator rights",
                                "installed": []}})
    r = software.score(s, baseline)
    assert r.status == "unavailable" and r.fix_ids == ()


def test_s1_failed_passes_through(make_scan, baseline):
    s = make_scan({"software": {"status": "failed", "error": "Registry read threw",
                                "installed": []}})
    r = software.score(s, baseline)
    assert r.status == "failed" and r.fix_ids == ()


def test_s1_failed_wins_over_outdated_apps(make_scan, baseline):
    s = make_scan({"software": {"status": "failed", "error": "boom", "installed": [CHROME_OLD]}})
    assert software.score(s, baseline).status == "failed"


# --- S7 ---


def test_s7_empty_list_explanation_and_no_fix(make_scan, baseline):
    r = software.score(_with(make_scan, []), baseline)
    assert r.explanation.startswith("We couldn't read the installed-apps list")
    assert r.fix_ids == ()
    assert any(row.status == Status.AMBER for row in r.evidence)


# --- S6 ---


def test_s6_no_matches_is_green_with_count(make_scan, baseline):
    r = software.score(_with(make_scan, [PASTEL, NOTEPADPP]), baseline)
    assert r.status == "green"
    assert r.explanation.startswith("None of your 2 apps are on our watch list")
    assert r.fix_ids == ()
    assert [row.value for row in r.evidence] == ["2 apps not on our watch list"]


def test_s6_is_checked_before_s5(make_scan, baseline):
    # With nothing matched, S5 ("all matched apps safe") is vacuously true;
    # the S6 explanation must win.
    r = software.score(_with(make_scan, [PASTEL]), baseline)
    assert "watch list" in r.explanation
    assert "up to date" not in r.explanation


def test_s6_publisher_mismatch_is_not_assessed(make_scan, baseline):
    fake = {"name": "Google Chrome", "version": "1.0", "publisher": "Totally Not Google"}
    r = software.score(_with(make_scan, [fake]), baseline)
    assert r.status == "green"
    assert r.explanation.startswith("None of your 1 app is on our watch list")


# --- S2 ---


def test_s2_eol_is_red_even_when_version_is_new(make_scan, eol_baseline):
    vlc_new = {**VLC_OLD, "version": "9.9.9"}
    r = software.score(_with(make_scan, [vlc_new]), eol_baseline)
    assert r.status == "red"
    assert r.fix_ids == (FIX,)
    assert "no longer supported" in r.explanation
    assert r.evidence[0].value == "9.9.9, no longer supported"


def test_s2_eol_with_unreadable_version_is_still_red(make_scan, eol_baseline):
    vlc_odd = {**VLC_OLD, "version": "unknown"}
    r = software.score(_with(make_scan, [vlc_odd]), eol_baseline)
    assert r.status == "red"
    assert r.evidence[0].value == "No longer supported"


def test_s2_eol_wins_over_s3(make_scan, eol_baseline):
    r = software.score(_with(make_scan, [CHROME_OLD, VLC_OLD]), eol_baseline)
    assert r.status == "red"
    assert "no longer supported" in r.explanation
    # eol app listed first, then the high-severity one.
    assert _labels(r)[:2] == ["VLC media player", "Google Chrome"]


def test_s2_steps_say_to_uninstall_eol_app(make_scan, eol_baseline):
    r = software.score(_with(make_scan, [VLC_OLD]), eol_baseline)
    steps = r.fix_steps[FIX]
    assert any(step.startswith("Uninstall VLC media player") for step in steps)


# --- S3 ---


def test_s3_high_below_min_is_red_with_red_fix(make_scan, baseline):
    r = software.score(_with(make_scan, [CHROME_OLD]), baseline)
    assert r.status == "red"
    assert r.fix_pairs() == [(FIX, Status.RED)]
    assert r.evidence[0].status == Status.RED
    assert "needs 142.0.7444.175 or newer" in r.evidence[0].value


def test_s3_wins_over_s4(make_scan, baseline):
    r = software.score(_with(make_scan, [ZOOM_OLD, CHROME_OLD]), baseline)
    assert r.status == "red"
    assert r.fix_pairs() == [(FIX, Status.RED)]
    # Both outdated apps are still named in the steps.
    assert "Google Chrome" in r.fix_steps[FIX][0] and "Zoom" in r.fix_steps[FIX][0]


def test_s3_dotted_int_fallback(make_scan, baseline):
    # "24.09 (x64)" is not a PEP 440 version; dotted-int gives (24, 9) < (25, 0).
    old = {"name": "7-Zip", "version": "24.09 (x64)", "publisher": "Igor Pavlov"}
    assert software.score(_with(make_scan, [old]), baseline).status == "red"


# --- S4 ---


def test_s4_medium_below_min_is_amber(make_scan, baseline):
    r = software.score(_with(make_scan, [ZOOM_OLD]), baseline)
    assert r.status == "amber"
    assert r.fix_pairs() == [(FIX, Status.AMBER)]
    assert r.evidence[0].status == Status.AMBER


# --- S5 ---


def test_s5_all_matched_at_or_above_min_is_green(make_scan, baseline):
    at_min = {"name": "VLC media player", "version": "3.0.21", "publisher": "VideoLAN"}
    r = software.score(_with(make_scan, [CHROME_NEW, at_min, PASTEL]), baseline)
    assert r.status == "green"
    assert r.fix_ids == ()
    assert "2 programs on our watch list are up to date" in r.explanation


def test_absent_outdated_app_never_affects_status(make_scan, baseline):
    ancient = {"name": "Pastel Partner", "version": "0.0.1", "publisher": "Sage"}
    r = software.score(_with(make_scan, [CHROME_NEW, ancient]), baseline)
    assert r.status == "green"
    assert "Pastel Partner" not in _labels(r)
    assert r.evidence[-1].value == "1 other app not on our watch list"


# --- matching ---


def test_match_is_case_insensitive(make_scan, baseline):
    shouty = {"name": "GOOGLE CHROME", "version": "118.0.0.0", "publisher": "google llc"}
    assert software.score(_with(make_scan, [shouty]), baseline).status == "red"


def test_multiple_chrome_versions_use_the_lowest(make_scan, baseline):
    for apps in ([CHROME_NEW, CHROME_OLD], [CHROME_OLD, CHROME_NEW]):
        r = software.score(_with(make_scan, apps), baseline)
        assert r.status == "red"
        assert r.evidence[0].value.startswith("118.0.5993.118")
        assert "oldest of 2 copies" in r.evidence[0].value
        assert _labels(r).count("Google Chrome") == 1


def test_multiple_copies_ignore_an_unreadable_one(make_scan, baseline):
    odd = {**CHROME_OLD, "version": "latest"}
    r = software.score(_with(make_scan, [odd, CHROME_NEW]), baseline)
    assert r.status == "green"
    assert r.evidence[0].value.startswith("142.0.7444.176")


# --- unreadable versions ---


def test_unreadable_version_is_neutral_row(make_scan, baseline):
    odd = {**CHROME_OLD, "version": "latest"}
    r = software.score(_with(make_scan, [odd]), baseline)
    assert r.status == "green"
    row = r.evidence[0]
    assert row.label == "Google Chrome"
    assert row.value == 'Version not readable ("latest")'
    assert row.status is None


def test_unreadable_version_does_not_change_status(make_scan, baseline):
    odd = {**CHROME_OLD, "version": ""}
    r = software.score(_with(make_scan, [odd, ZOOM_OLD]), baseline)
    assert r.status == "amber"  # Zoom alone decides; Chrome is neutral
    assert "Chrome" not in r.fix_steps[FIX][0]


# --- fix and evidence shape ---

MANY_OUTDATED = [
    CHROME_OLD,
    {"name": "Microsoft Edge", "version": "120.0.0.0", "publisher": "Microsoft Corporation"},
    {"name": "Mozilla Firefox (x64 en-US)", "version": "120.0", "publisher": "Mozilla"},
    {"name": "Adobe Acrobat Reader DC", "version": "23.0", "publisher": "Adobe Inc."},
    {"name": "7-Zip 24.08 (x64)", "version": "24.08", "publisher": "Igor Pavlov"},
    {"name": "WinRAR 7.01 (64-bit)", "version": "7.01", "publisher": "win.rar GmbH"},
    ZOOM_OLD,
    VLC_OLD,
]


def test_one_fix_whose_steps_name_at_most_four_apps(make_scan, baseline):
    r = software.score(_with(make_scan, MANY_OUTDATED + [PASTEL, NOTEPADPP]), baseline)
    assert r.fix_ids == (FIX,)
    first = r.fix_steps[FIX][0]
    assert first == (
        "Update these programs: Google Chrome, Microsoft Edge, Mozilla Firefox, "
        "Adobe Acrobat Reader and 4 more."
    )


def test_steps_list_all_names_when_four_or_fewer(make_scan, baseline):
    r = software.score(_with(make_scan, [CHROME_OLD, ZOOM_OLD]), baseline)
    assert r.fix_steps[FIX][0] == "Update these programs: Google Chrome and Zoom."


def test_evidence_caps_outdated_rows_then_watch_list_row(make_scan, baseline):
    r = software.score(_with(make_scan, MANY_OUTDATED + [PASTEL, NOTEPADPP]), baseline)
    assert len(r.evidence) == 7
    assert all(row.status in (Status.RED, Status.AMBER) for row in r.evidence[:6])
    assert r.evidence[-1].value == "2 other apps not on our watch list"


def test_outdated_rows_come_before_up_to_date_rows(make_scan, baseline):
    r = software.score(_with(make_scan, [CHROME_NEW, SEVEN_ZIP_NEW, ZOOM_OLD]), baseline)
    assert [row.status for row in r.evidence] == [Status.AMBER, Status.GREEN, Status.GREEN, None]


def test_resolve_uses_run_specific_steps(make_scan, baseline):
    r = software.score(_with(make_scan, [CHROME_OLD]), baseline)
    fixes, top = resolve(r.fix_pairs(), r.fix_steps)
    assert top == [FIX]
    assert fixes[0]["severity"] == "red"
    assert fixes[0]["steps"] == list(r.fix_steps[FIX])
    assert fixes[0]["steps"] != list(CATALOGUE[FIX].steps)


def test_fix_steps_for_unattached_fix_rejected():
    with pytest.raises(ValueError):
        CategoryResult.rated("software", "amber", "Old.", fix_ids=[FIX],
                             fix_steps={"install-updates": ["Do it."]})


@pytest.mark.parametrize("steps", [[], ["x"] * 6, [""], ["x" * 161]])
def test_fix_steps_must_fit_report_schema(steps):
    with pytest.raises(ValueError):
        CategoryResult.rated("software", "amber", "Old.", fix_ids=[FIX], fix_steps={FIX: steps})
