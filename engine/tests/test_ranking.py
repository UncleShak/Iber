import re

import pytest

from antigravity_engine.scoring.fixes import CATALOGUE, resolve
from antigravity_engine.scoring.result import CategoryResult, EvidenceRow, Status

R = CategoryResult.rated

# s2.9 table: id -> (category, effort_minutes, needs_admin, max severity)
SPEC_TABLE = {
    "enable-defender": ("protection", 5, True, "red"),
    "update-defender-definitions": ("protection", 5, False, "red"),
    "turn-on-bitlocker": ("protection", 20, True, "red"),
    "encrypt-device-home": ("protection", 15, True, "amber"),
    "enable-tamper-protection": ("protection", 3, True, "amber"),
    "enable-cfa": ("protection", 5, True, "amber"),
    "enable-asr-rules": ("protection", 15, True, "amber"),
    "turn-on-file-history": ("backup", 15, False, "red"),
    "run-backup-now": ("backup", 10, False, "amber"),
    "verify-backup-agent": ("backup", 10, False, "amber"),
    "install-updates": ("patch", 30, True, "red"),
    "restart-to-finish-updates": ("patch", 10, False, "amber"),
    "plan-windows-11": ("patch", 60, True, "amber"),
    "update-outdated-apps": ("software", 20, False, "red"),
    # Added beyond s2.9 by decision D11 (S7 empty installed list).
    "rescan-installed-apps": ("software", 5, False, "amber"),
    "enable-winre": ("recovery", 10, True, "red"),
    "turn-on-system-restore": ("recovery", 5, True, "red"),
    "create-restore-point": ("recovery", 5, True, "amber"),
}


def _pairs(results):
    return [p for r in results for p in r.fix_pairs()]


def _green(cid):
    return R(cid, "green", "All good.")


# --- catalogue -------------------------------------------------------------


def test_catalogue_matches_spec_table():
    assert set(CATALOGUE) == set(SPEC_TABLE)
    for fix_id, (category, effort, admin, cap) in SPEC_TABLE.items():
        fix = CATALOGUE[fix_id]
        assert (fix.category, fix.effort_minutes, fix.needs_admin, fix.max_severity) == \
            (category, effort, admin, cap), fix_id


@pytest.mark.parametrize("fix_id", sorted(SPEC_TABLE))
def test_catalogue_entry_fits_report_schema_limits(fix_id):
    fix = CATALOGUE[fix_id]
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fix.id)
    assert 0 < len(fix.title) <= 80
    assert 0 < len(fix.why) <= 160
    assert 1 <= len(fix.steps) <= 5
    assert all(0 < len(s) <= 160 for s in fix.steps)
    assert fix.effort_minutes >= 1


# --- s0.8 ranking ----------------------------------------------------------


def test_defender_off_stale_patch_no_backup():
    # Hand-built results for: Defender off, latest hotfix 70 days old, no backup evidence.
    results = [
        R("backup", "red", "No backup found.", fix_ids=["turn-on-file-history"]),
        R("patch", "red", "Last update was 70 days ago.", fix_ids=["install-updates"]),
        _green("software"),
        R(
            "protection", "red", "Defender is off.",
            evidence=[EvidenceRow("Defender antivirus", "Off", Status.RED)],
            fix_ids=["enable-defender", "enable-cfa"],
            fix_severity={"enable-cfa": Status.AMBER},
        ),
        _green("recovery"),
    ]
    fixes, top = resolve(_pairs(results))
    assert top == ["enable-defender", "turn-on-file-history", "install-updates"]
    assert [f["id"] for f in fixes] == top + ["enable-cfa"]


def test_all_green_has_no_fixes():
    results = [_green(c) for c in ("backup", "patch", "software", "protection", "recovery")]
    assert resolve(_pairs(results)) == ([], [])


def test_red_beats_amber_regardless_of_category():
    fixes, top = resolve([("enable-cfa", "amber"), ("update-outdated-apps", "red")])
    assert top == ["update-outdated-apps", "enable-cfa"]


def test_category_order_within_same_severity():
    pairs = [
        ("update-outdated-apps", "amber"),
        ("create-restore-point", "amber"),
        ("restart-to-finish-updates", "amber"),
        ("run-backup-now", "amber"),
        ("enable-cfa", "amber"),
    ]
    fixes, top = resolve(pairs)
    assert [f["category"] for f in fixes] == ["protection", "backup", "patch", "recovery", "software"]
    assert top == ["enable-cfa", "run-backup-now", "restart-to-finish-updates"]


def test_lower_effort_first_within_category():
    _, top = resolve([("enable-asr-rules", "amber"), ("enable-tamper-protection", "amber"),
                      ("enable-cfa", "amber")])
    assert top == ["enable-tamper-protection", "enable-cfa", "enable-asr-rules"]


def test_id_alphabetical_breaks_full_tie():
    # Same severity, category and effort (5 min): alphabetical id decides.
    _, top = resolve([("update-defender-definitions", "red"), ("enable-defender", "red")])
    assert top == ["enable-defender", "update-defender-definitions"]


def test_duplicates_merge_with_worst_severity():
    fixes, top = resolve([("enable-defender", "amber"), ("enable-defender", "red"),
                          ("enable-defender", "amber")])
    assert top == ["enable-defender"]
    assert len(fixes) == 1 and fixes[0]["severity"] == "red"


def test_top_fixes_capped_at_three_and_subset_of_fixes():
    pairs = [(f, "amber") for f in SPEC_TABLE]
    fixes, top = resolve(pairs)
    assert len(fixes) == len(SPEC_TABLE)
    assert len(top) == 3
    assert top == [f["id"] for f in fixes][:3]


def test_result_order_does_not_change_ranking():
    pairs = [("install-updates", "red"), ("turn-on-file-history", "red"), ("enable-defender", "red")]
    assert resolve(pairs) == resolve(list(reversed(pairs)))


def test_fix_dict_has_report_fields():
    fixes, _ = resolve([("install-updates", "amber")])
    assert fixes[0] == {
        "id": "install-updates",
        "category": "patch",
        "severity": "amber",
        "title": CATALOGUE["install-updates"].title,
        "why": CATALOGUE["install-updates"].why,
        "steps": list(CATALOGUE["install-updates"].steps),
        "effort_minutes": 30,
        "needs_admin": True,
    }


def test_unknown_fix_id_rejected():
    with pytest.raises(KeyError):
        resolve([("reboot-the-moon", "red")])


@pytest.mark.parametrize("severity", ["green", "unavailable", "failed"])
def test_non_red_amber_severity_rejected(severity):
    with pytest.raises(ValueError):
        resolve([("enable-cfa", severity)])


def test_fix_severity_defaults_to_category_status():
    r = R("patch", "amber", "Updates are a bit old.", fix_ids=["install-updates", "plan-windows-11"])
    assert r.fix_pairs() == [("install-updates", Status.AMBER), ("plan-windows-11", Status.AMBER)]


def test_fix_severity_cannot_exceed_category():
    with pytest.raises(ValueError):
        R("protection", "amber", "CFA off.", fix_ids=["enable-cfa"], fix_severity={"enable-cfa": "red"})


# --- D1: catalogue severity caps -------------------------------------------

AMBER_ONLY = sorted(f for f, row in SPEC_TABLE.items() if row[3] == "amber")


@pytest.mark.parametrize("fix_id", AMBER_ONLY)
def test_amber_only_fix_is_capped_in_a_red_category(fix_id):
    fixes, _ = resolve([(fix_id, "red")])
    assert fixes[0]["severity"] == "amber"


@pytest.mark.parametrize("fix_id", ["enable-defender", "install-updates", "enable-winre",
                                    "update-defender-definitions"])
def test_red_capable_fix_keeps_red(fix_id):
    fixes, _ = resolve([(fix_id, "red")])
    assert fixes[0]["severity"] == "red"


def test_cap_without_fix_severity_keeps_cfa_out_of_top_three():
    # Same scenario as test_defender_off_stale_patch_no_backup, but the scorer
    # gave no fix_severity: the catalogue cap alone ranks CFA as amber.
    results = [
        R("backup", "red", "No backup found.", fix_ids=["turn-on-file-history"]),
        R("patch", "red", "Last update was 70 days ago.", fix_ids=["install-updates"]),
        R("protection", "red", "Defender is off.", fix_ids=["enable-defender", "enable-cfa"]),
    ]
    fixes, top = resolve(_pairs(results))
    assert top == ["enable-defender", "turn-on-file-history", "install-updates"]
    assert (fixes[-1]["id"], fixes[-1]["severity"]) == ("enable-cfa", "amber")


def test_fix_severity_still_lowers_a_red_capable_fix():
    # Definitions 5 days old (amber rule) while BitLocker is off (red category).
    r = R("protection", "red", "BitLocker is off.",
          fix_ids=["turn-on-bitlocker", "update-defender-definitions"],
          fix_severity={"update-defender-definitions": Status.AMBER})
    fixes, _ = resolve(r.fix_pairs())
    assert {f["id"]: f["severity"] for f in fixes} == {"turn-on-bitlocker": "red",
                                                      "update-defender-definitions": "amber"}
