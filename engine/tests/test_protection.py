"""s2.5.4 protection sub-checks. Healthy fixture: Defender on, signatures 0
days, tamper on; BitLocker on at 100%; CFA enabled; all 3 recommended ASR
rules blocking. Category status is the worst rated row (D12-D14)."""

import pytest

from antigravity_engine.parser import parse_path
from antigravity_engine.scoring import protection
from antigravity_engine.scoring.fixes import resolve
from antigravity_engine.scoring.result import NEEDS_ADMIN, Status

from conftest import FIXTURES

ASR_IDS = (
    "d4f940ab-401b-4efc-aadc-ad5f3c50688a",
    "c1db55ab-c21a-4637-bb3f-a12568109d35",
    "be9ba2d9-53ea-4cdc-84e5-9b1eeee46550",
)
ADMIN_SENTENCE = "Run as administrator for a full check"


def _prot(**sections) -> dict:
    return {"protection": sections}


def _row(result, label):
    return next(r for r in result.evidence if r.label == label)


def _asr_rules(*actions):
    return [{"id": i, "action": a} for i, a in zip(ASR_IDS, actions)]


# --- examples from s2.10 ---


def test_bitlocker_off_on_pro_is_red(make_scan, baseline):
    s = make_scan({"protection": {"bitlocker": {"os_volume_protection": "off",
                                                "os_volume_encryption_pct": 0}}})
    r = protection.score(s, baseline)
    assert r.status == "red" and "turn-on-bitlocker" in r.fix_ids


def test_missing_bitlocker_on_home_is_amber_not_grey(make_scan, baseline):
    s = make_scan({"host": {"os_edition": "Core"},
                   "protection": {"bitlocker": {"status": "unavailable",
                                                "error": "BitLocker management not available on Windows Home",
                                                "os_volume_protection": None,
                                                "os_volume_encryption_pct": None}}})
    r = protection.score(s, baseline)
    assert r.status == "amber" and "encrypt-device-home" in r.fix_ids


def test_bitlocker_unavailable_non_admin_is_grey_row_only(make_scan, baseline):
    s = make_scan({"host": {"is_admin": False},
                   "protection": {"bitlocker": {"status": "unavailable", "error": "Requires administrator rights",
                                                "os_volume_protection": None}}})
    r = protection.score(s, baseline)
    assert r.status == "green"            # other sub-checks healthy
    assert any(row.status == "unavailable" for row in r.evidence)


def test_defender_service_stopped_is_red(make_scan, baseline):
    s = make_scan({"protection": {"defender": {"antivirus_enabled": False,
                                               "realtime_enabled": False,
                                               "third_party_av": None}}})
    assert protection.score(s, baseline).status == "red"


def test_third_party_av_is_not_penalised(make_scan, baseline):
    s = make_scan({"protection": {"defender": {"antivirus_enabled": False, "realtime_enabled": False,
                                               "third_party_av": "ESET Security"}}})
    r = protection.score(s, baseline)
    assert "enable-defender" not in r.fix_ids


def test_cfa_off_alone_is_amber(make_scan, baseline):
    s = make_scan({"protection": {"cfa": {"mode": "disabled"}}})
    assert protection.score(s, baseline).status == "amber"


# --- phase 6 gate: fixtures ---


def _fixture(name):
    return parse_path(FIXTURES / f"scan.{name}.json")


def test_fixture_healthy_is_green_with_four_rows(baseline):
    r = protection.score(_fixture("healthy"), baseline)
    assert r.status == Status.GREEN and r.fix_ids == ()
    assert [row.status for row in r.evidence] == [Status.GREEN] * 4
    assert r.explanation.startswith("Antivirus, drive encryption")


def test_fixture_home_edition_is_amber(baseline):
    r = protection.score(_fixture("home-edition"), baseline)
    assert r.status == Status.AMBER
    assert r.fix_ids == ("encrypt-device-home",)
    assert _row(r, protection.BITLOCKER).status == Status.AMBER


def test_fixture_no_bitlocker_is_red(baseline):
    r = protection.score(_fixture("no-bitlocker"), baseline)
    assert r.status == Status.RED
    # BitLocker off (red) ranks before ASR 1 of 3 (amber).
    assert r.fix_ids == ("turn-on-bitlocker", "enable-asr-rules")
    assert r.fix_severity == {"enable-asr-rules": Status.AMBER}
    assert _row(r, protection.ASR).value == "1 of 3 recommended rules on"


def test_fixture_defender_off_is_red(baseline):
    r = protection.score(_fixture("defender-off"), baseline)
    assert r.status == Status.RED
    # Defender off: CFA/ASR excluded, BitLocker grey (non-admin).
    assert r.fix_ids == ("enable-defender",)
    assert _row(r, protection.BITLOCKER).value == NEEDS_ADMIN
    assert _row(r, protection.CFA).status is None
    assert _row(r, protection.ASR).status is None


# --- Defender table, first match wins ---


def test_defender_off_without_third_party_is_red_row(make_scan, baseline):
    r = protection.score(make_scan(_prot(defender={"antivirus_enabled": False})), baseline)
    assert _row(r, protection.DEFENDER).status == Status.RED
    assert r.fix_ids == ("enable-defender",)
    assert r.explanation.startswith("Microsoft Defender is off")


def test_third_party_av_row_reads_protected_by(make_scan, baseline):
    s = make_scan(_prot(defender={"antivirus_enabled": False, "realtime_enabled": False,
                                  "third_party_av": "ESET Security"}))
    r = protection.score(s, baseline)
    row = _row(r, protection.DEFENDER)
    assert (row.value, row.status) == ("Protected by ESET Security", Status.GREEN)
    assert r.status == Status.GREEN


def test_third_party_av_wins_over_stale_signatures_and_tamper_off(make_scan, baseline):
    # D13 / s3.6: a passive Defender's own settings are never penalised.
    s = make_scan(_prot(defender={"antivirus_enabled": True, "realtime_enabled": False,
                                  "tamper_protected": False, "signature_age_days": 30,
                                  "third_party_av": "Sophos"}))
    r = protection.score(s, baseline)
    assert _row(r, protection.DEFENDER).status == Status.GREEN
    assert r.fix_ids == ()


def test_realtime_off_is_red(make_scan, baseline):
    r = protection.score(make_scan(_prot(defender={"realtime_enabled": False})), baseline)
    assert r.status == Status.RED and r.fix_ids == ("enable-defender",)
    assert "real-time" in _row(r, protection.DEFENDER).value


def test_realtime_off_wins_over_old_signatures(make_scan, baseline):
    s = make_scan(_prot(defender={"realtime_enabled": False, "signature_age_days": 20}))
    assert protection.score(s, baseline).fix_ids == ("enable-defender",)


@pytest.mark.parametrize("days,status", [
    (3, Status.GREEN), (4, Status.AMBER), (7, Status.AMBER), (8, Status.RED),
])
def test_signature_age_boundaries(make_scan, baseline, days, status):
    r = protection.score(make_scan(_prot(defender={"signature_age_days": days})), baseline)
    assert _row(r, protection.DEFENDER).status == status
    assert r.status == status
    expected = () if status == Status.GREEN else ("update-defender-definitions",)
    assert r.fix_ids == expected


def test_old_signatures_win_over_tamper_off(make_scan, baseline):
    s = make_scan(_prot(defender={"signature_age_days": 5, "tamper_protected": False}))
    assert protection.score(s, baseline).fix_ids == ("update-defender-definitions",)


def test_tamper_off_is_amber(make_scan, baseline):
    r = protection.score(make_scan(_prot(defender={"tamper_protected": False})), baseline)
    assert r.status == Status.AMBER and r.fix_ids == ("enable-tamper-protection",)


def test_defender_section_failed_is_grey_and_cfa_asr_still_rated(make_scan, baseline):
    s = make_scan(_prot(defender={"status": "failed", "error": "Get-MpComputerStatus threw"},
                        cfa={"mode": "disabled"}))
    r = protection.score(s, baseline)
    row = _row(r, protection.DEFENDER)
    assert row.status == Status.FAILED and row.value == "Get-MpComputerStatus threw"
    assert r.status == Status.AMBER and r.fix_ids == ("enable-cfa",)


def test_defender_null_running_state_is_grey_not_red(make_scan, baseline):
    s = make_scan(_prot(defender={"antivirus_enabled": None, "realtime_enabled": None}))
    r = protection.score(s, baseline)
    assert _row(r, protection.DEFENDER).status == Status.UNAVAILABLE
    assert r.status == Status.GREEN


# --- BitLocker table ---


@pytest.mark.parametrize("edition", ["Core", "CoreSingleLanguage", "CoreN"])
def test_home_editions_are_rated_amber(make_scan, baseline, edition):
    s = make_scan({"host": {"os_edition": edition},
                   **_prot(bitlocker={"status": "unavailable", "error": "x",
                                      "os_volume_protection": None,
                                      "os_volume_encryption_pct": None})})
    r = protection.score(s, baseline)
    assert _row(r, protection.BITLOCKER).status == Status.AMBER
    assert "encrypt-device-home" in r.fix_ids


def test_bitlocker_failed_on_home_is_grey_not_rated(make_scan, baseline):
    # s2.5.4 rates Home only when the section is "unavailable".
    s = make_scan({"host": {"os_edition": "Core"},
                   **_prot(bitlocker={"status": "failed", "error": "boom",
                                      "os_volume_protection": None})})
    r = protection.score(s, baseline)
    assert _row(r, protection.BITLOCKER).status == Status.FAILED
    assert r.status == Status.GREEN


def test_bitlocker_unavailable_non_admin_row_says_needs_admin(make_scan, baseline):
    s = make_scan({"host": {"is_admin": False},
                   **_prot(bitlocker={"status": "unavailable",
                                      "error": "Requires administrator rights",
                                      "os_volume_protection": None})})
    r = protection.score(s, baseline)
    assert _row(r, protection.BITLOCKER).value == NEEDS_ADMIN
    assert ADMIN_SENTENCE in r.explanation


def test_bitlocker_still_encrypting_is_amber_with_finish_fix(make_scan, baseline):
    s = make_scan(_prot(bitlocker={"os_volume_protection": "on", "os_volume_encryption_pct": 63}))
    r = protection.score(s, baseline)
    assert r.status == Status.AMBER
    assert r.fix_ids == ("finish-bitlocker-encryption",)  # D12
    assert "63%" in _row(r, protection.BITLOCKER).value
    assert "leave the PC on" in r.explanation


def test_bitlocker_on_without_percentage_is_green(make_scan, baseline):
    # Non-admin COM fallback only reads protection status (s3.5).
    s = make_scan(_prot(bitlocker={"os_volume_protection": "on", "os_volume_encryption_pct": None}))
    assert _row(protection.score(s, baseline), protection.BITLOCKER).status == Status.GREEN


def test_bitlocker_ok_with_null_protection_is_grey(make_scan, baseline):
    s = make_scan(_prot(bitlocker={"os_volume_protection": None, "os_volume_encryption_pct": None}))
    r = protection.score(s, baseline)
    assert _row(r, protection.BITLOCKER).status == Status.UNAVAILABLE
    assert r.status == Status.GREEN


# --- CFA table ---


@pytest.mark.parametrize("mode,status", [
    ("enabled", Status.GREEN), ("audit", Status.AMBER), ("disabled", Status.AMBER),
])
def test_cfa_modes(make_scan, baseline, mode, status):
    r = protection.score(make_scan(_prot(cfa={"mode": mode})), baseline)
    assert _row(r, protection.CFA).status == status
    assert r.status == status
    assert r.fix_ids == (() if status == Status.GREEN else ("enable-cfa",))


def test_cfa_never_red_even_with_everything_else_fine(make_scan, baseline):
    r = protection.score(make_scan(_prot(cfa={"mode": "disabled"})), baseline)
    assert r.status != Status.RED


def test_cfa_unavailable_is_grey(make_scan, baseline):
    s = make_scan(_prot(cfa={"status": "unavailable", "error": "not available", "mode": None}))
    r = protection.score(s, baseline)
    assert _row(r, protection.CFA).status == Status.UNAVAILABLE
    assert r.status == Status.GREEN


# --- ASR table ---


@pytest.mark.parametrize("actions,value,status", [
    (("block", "block", "block"), "3 of 3 recommended rules on", Status.GREEN),
    (("warn", "block", "warn"), "3 of 3 recommended rules on", Status.GREEN),
    (("block", "audit", "off"), "1 of 3 recommended rules on", Status.AMBER),
    (("audit", "audit", "off"), "0 of 3 recommended rules on", Status.AMBER),
])
def test_asr_counts_block_and_warn_only(make_scan, baseline, actions, value, status):
    r = protection.score(make_scan(_prot(asr={"rules": _asr_rules(*actions)})), baseline)
    row = _row(r, protection.ASR)
    assert (row.value, row.status) == (value, status)
    assert r.fix_ids == (() if status == Status.GREEN else ("enable-asr-rules",))


def test_asr_no_rules_is_amber_not_red(make_scan, baseline):
    r = protection.score(make_scan(_prot(asr={"rules": []})), baseline)
    assert r.status == Status.AMBER
    assert r.explanation.startswith("None of Microsoft Defender's")


def test_asr_ignores_rules_not_recommended_and_matches_guid_case(make_scan, baseline):
    rules = [{"id": ASR_IDS[0].upper(), "action": "block"},
             {"id": "56a863a9-875e-4185-98a7-b882c64b5ce5", "action": "block"}]
    r = protection.score(make_scan(_prot(asr={"rules": rules})), baseline)
    assert _row(r, protection.ASR).value == "1 of 3 recommended rules on"


# --- Defender not primary: CFA/ASR excluded (D13) ---


@pytest.mark.parametrize("defender", [
    {"third_party_av": "ESET Security"},
    {"antivirus_enabled": False},
    {"realtime_enabled": False},
])
def test_cfa_and_asr_excluded_when_defender_not_primary(make_scan, baseline, defender):
    s = make_scan(_prot(defender=defender, cfa={"mode": "disabled"}, asr={"rules": []}))
    r = protection.score(s, baseline)
    for label in (protection.CFA, protection.ASR):
        row = _row(r, label)
        assert (row.value, row.status) == (protection.DEFENDER_ONLY, None)
    assert "enable-cfa" not in r.fix_ids and "enable-asr-rules" not in r.fix_ids


def test_excluded_rows_leave_third_party_pc_green(make_scan, baseline):
    s = make_scan(_prot(defender={"third_party_av": "ESET Security", "antivirus_enabled": False},
                        cfa={"mode": "disabled"}, asr={"rules": []}))
    r = protection.score(s, baseline)
    assert r.status == Status.GREEN
    assert r.explanation == "The protections we could check are all on."


# --- category: worst row, explanation, fix order and severity ---


def test_worst_row_wins_and_red_finding_explains(make_scan, baseline):
    s = make_scan(_prot(bitlocker={"os_volume_protection": "off"}, cfa={"mode": "audit"},
                        defender={"tamper_protected": False}))
    r = protection.score(s, baseline)
    assert r.status == Status.RED
    assert r.fix_ids == ("turn-on-bitlocker", "enable-tamper-protection", "enable-cfa")
    assert r.explanation.startswith("The hard drive isn't encrypted")
    assert r.explanation.endswith("2 other protections also need attention.")


def test_one_other_finding_is_singular(make_scan, baseline):
    s = make_scan(_prot(cfa={"mode": "audit"}, asr={"rules": []}))
    r = protection.score(s, baseline)
    assert r.explanation.endswith("1 other protection also needs attention.")


def test_amber_fix_inside_red_category_ranks_amber(make_scan, baseline):
    # D1: update-defender-definitions can be red, so 5 days must be pinned amber.
    s = make_scan(_prot(bitlocker={"os_volume_protection": "off"},
                        defender={"signature_age_days": 5}))
    r = protection.score(s, baseline)
    assert r.fix_severity == {"update-defender-definitions": Status.AMBER}
    sev = {f["id"]: f["severity"] for f in resolve(r.fix_pairs())[0]}
    assert sev == {"turn-on-bitlocker": "red", "update-defender-definitions": "amber"}


def test_every_finding_has_a_fix_and_explanation_fits(make_scan, baseline):
    s = make_scan({"host": {"os_edition": "Core"},
                   **_prot(defender={"antivirus_enabled": False},
                           bitlocker={"status": "unavailable", "error": "x",
                                      "os_volume_protection": None}),
                   })
    r = protection.score(s, baseline)
    assert r.fix_ids == ("enable-defender", "encrypt-device-home")
    assert len(r.explanation) <= 200


def test_all_sections_unavailable_is_unavailable_with_grey_rows(make_scan, baseline):
    off = {"status": "unavailable", "error": "Requires administrator rights"}
    s = make_scan(_prot(defender={**off, "antivirus_enabled": None, "realtime_enabled": None},
                        bitlocker={**off, "os_volume_protection": None},
                        cfa={**off, "mode": None}, asr={**off, "rules": []}))
    r = protection.score(s, baseline)
    assert r.status == Status.UNAVAILABLE
    assert len(r.evidence) == 4
    assert all(row.status == Status.UNAVAILABLE for row in r.evidence)


def test_all_sections_failed_is_failed(make_scan, baseline):
    bad = {"status": "failed", "error": "probe crashed"}
    s = make_scan(_prot(defender=bad, bitlocker=bad, cfa=bad, asr=bad))
    r = protection.score(s, baseline)
    assert r.status == Status.FAILED
    assert "probe crashed" in r.explanation
