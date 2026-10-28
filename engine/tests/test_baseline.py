import copy
import json

import pytest

from antigravity_engine.baseline import (
    BaselineError,
    baseline_from_dict,
    compare_versions,
    is_below,
    load_baseline,
)
from conftest import FIXTURES, ROOT

BASELINE = ROOT / "baseline" / "software-baseline.json"

EXPECTED_IDS = {
    "chrome", "edge", "firefox", "acrobat-reader", "7zip", "winrar", "zoom",
    "oracle-java", "vlc", "ms-office", "anydesk", "teamviewer",
}

ASR_IDS = {
    "d4f940ab-401b-4efc-aadc-ad5f3c50688a",
    "c1db55ab-c21a-4637-bb3f-a12568109d35",
    "be9ba2d9-53ea-4cdc-84e5-9b1eeee46550",
}


@pytest.fixture(scope="module")
def baseline():
    return load_baseline(BASELINE)


@pytest.fixture
def raw() -> dict:
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def _fixture_apps() -> list[tuple[str, dict]]:
    apps = []
    for f in sorted(FIXTURES.glob("scan.*.json")):
        if f.name == "scan.xss.json":
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for app in data["software"]["installed"]:
            apps.append((f.name, app))
    return apps


# --- loading ---------------------------------------------------------------

def test_loads_cleanly(baseline):
    assert len(baseline.entries) == 12
    assert {e.id for e in baseline.entries} == EXPECTED_IDS
    assert baseline.baseline_version == "2026-10-27"
    assert baseline.checked_on == "2026-10-27"
    assert baseline.win11_min_build == "22631"
    assert baseline.win10_eos_date == "2025-10-14"


def test_asr_recommended_is_exactly_three_rules(baseline):
    assert baseline.asr_recommended == ASR_IDS
    assert baseline.asr_names["c1db55ab-c21a-4637-bb3f-a12568109d35"] == (
        "Block credential stealing from lsass.exe"
    )


def test_every_min_safe_version_is_readable(baseline):
    for e in baseline.entries:
        assert compare_versions(e.min_safe_version, e.min_safe_version) == 0, e.id


def test_only_high_or_medium_severity(baseline):
    assert {e.severity for e in baseline.entries} <= {"high", "medium"}


def test_missing_file_raises(tmp_path):
    with pytest.raises(BaselineError, match="not found"):
        load_baseline(tmp_path / "nope.json")


def test_invalid_json_raises(write_json):
    with pytest.raises(BaselineError, match="not valid JSON"):
        load_baseline(write_json(b"{not json", name="b.json"))


def test_bom_is_tolerated(write_json):
    p = write_json(b"\xef\xbb\xbf" + BASELINE.read_bytes(), name="b.json")
    assert len(load_baseline(p).entries) == 12


def test_schema_rejects_bad_severity(raw):
    raw["entries"][0]["severity"] = "low"
    with pytest.raises(BaselineError) as exc:
        baseline_from_dict(raw)
    assert exc.value.path == "$.entries[0].severity"


def test_schema_rejects_missing_required_field(raw):
    del raw["entries"][3]["source_url"]
    with pytest.raises(BaselineError, match="source_url"):
        baseline_from_dict(raw)


def test_schema_rejects_unanchored_regex(raw):
    raw["entries"][0]["match"]["name_regex"] = "Google Chrome"
    with pytest.raises(BaselineError):
        baseline_from_dict(raw)


def test_schema_rejects_missing_win11_build(raw):
    del raw["os"]["min_supported_build"]["win11"]
    with pytest.raises(BaselineError, match="win11"):
        baseline_from_dict(raw)


def test_duplicate_ids_rejected(raw):
    raw["entries"].append(copy.deepcopy(raw["entries"][0]))
    with pytest.raises(BaselineError, match="duplicate entry id 'chrome'"):
        baseline_from_dict(raw)


def test_uncompilable_regex_rejected(raw):
    raw["entries"][1]["match"]["name_regex"] = "^Microsoft (Edge$"
    with pytest.raises(BaselineError, match="invalid regex") as exc:
        baseline_from_dict(raw)
    assert exc.value.path == "$.entries[1].match.name_regex"


# --- matching --------------------------------------------------------------

def test_fixtures_have_apps_to_match():
    assert len(_fixture_apps()) >= 3


@pytest.mark.parametrize("fixture,app", _fixture_apps(), ids=lambda v: v if isinstance(v, str) else v["name"])
def test_fixture_app_names_match_exactly_one_entry(baseline, fixture, app):
    hits = [e.id for e in baseline.entries if e.matches(app["name"], app["publisher"])]
    assert len(hits) == 1, f"{fixture}: {app['name']!r} matched {hits}"


@pytest.mark.parametrize("name,publisher,expected", [
    ("Google Chrome", "Google LLC", "chrome"),
    ("google chrome", "GOOGLE LLC", "chrome"),
    ("Adobe Acrobat Reader", "Adobe", "acrobat-reader"),
    ("Adobe Acrobat Reader DC - English", "Adobe Systems Incorporated", "acrobat-reader"),
    ("7-Zip", "Igor Pavlov", "7zip"),
    ("7-Zip 24.08 (x64)", "Igor Pavlov", "7zip"),
    ("Microsoft Edge", "Microsoft Corporation", "edge"),
    ("Mozilla Firefox (x64 en-US)", "Mozilla", "firefox"),
    ("WinRAR 7.01 (64-bit)", "win.rar GmbH", "winrar"),
    ("Zoom Workplace (64-bit)", "Zoom Video Communications, Inc.", "zoom"),
    ("Java 8 Update 451 (64-bit)", "Oracle Corporation", "oracle-java"),
    ("VLC media player", "VideoLAN", "vlc"),
    ("Microsoft 365 Apps for business - en-us", "Microsoft Corporation", "ms-office"),
    ("AnyDesk", "AnyDesk Software GmbH", "anydesk"),
    ("TeamViewer", "TeamViewer", "teamviewer"),
])
def test_real_world_names_match(baseline, name, publisher, expected):
    entry = baseline.match(name, publisher)
    assert entry is not None and entry.id == expected


@pytest.mark.parametrize("name,publisher", [
    ("Google Chrome Beta", "Google LLC"),
    ("Microsoft Edge WebView2 Runtime", "Microsoft Corporation"),
    ("Mozilla Maintenance Service", "Mozilla"),
    ("Mozilla Firefox ESR (x64 en-US)", "Mozilla"),
    ("Pastel Partner", "Sage"),
    ("Google Chrome", "Evil Corp"),
    ("Google Chrome", ""),
])
def test_non_matches(baseline, name, publisher):
    assert baseline.match(name, publisher) is None


# --- version comparison ----------------------------------------------------

def test_chrome_versions_compare_numerically():
    assert compare_versions("131.0.6778.86", "118.0.5993.118") == 1
    assert compare_versions("118.0.5993.118", "131.0.6778.86") == -1


def test_two_part_versions_compare_numerically():
    assert compare_versions("24.08", "23.01") == 1


def test_equal_versions_with_different_padding():
    assert compare_versions("25.00", "25") == 0
    assert compare_versions("25.001.20937", "25.1.20937") == 0


def test_unparseable_returns_none():
    assert compare_versions("latest", "131.0.0.0") is None
    assert compare_versions("131.0.0.0", "") is None
    assert is_below("unknown", "1.0") is None


def test_dotted_fallback_when_packaging_rejects():
    assert compare_versions("131.0.6778.86 (Official Build)", "131.0.6778.85") == 1
    assert compare_versions("24.4.20220 build 7", "25.1") == -1


def test_is_below():
    assert is_below("118.0.5993.118", "131.0.0.0") is True
    assert is_below("131.0.0.0", "131.0.0.0") is False
