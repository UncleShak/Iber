"""s2.5.5 recovery rules R1-R7. Healthy fixture: collected_at 2026-11-14T16:42:07Z,
WinRE on, System Restore on, 2 restore points, newest 2026-11-10 (4 days)."""

import pytest

from antigravity_engine.scoring import recovery
from antigravity_engine.scoring.result import NEEDS_ADMIN, Status

ADMIN_SENTENCE = "Run as administrator for a full check"


def _rec(**fields) -> dict:
    return {"recovery": fields}


def _row(result, label):
    return next(r for r in result.evidence if r.label == label)


# --- examples from s2.10 ---


def test_healthy_is_green(make_scan):
    assert recovery.score(make_scan()).status == "green"


def test_no_winre_and_no_restore_points_is_red(make_scan):
    s = make_scan({"recovery": {"winre_enabled": False, "restore_point_count": 0}})
    assert recovery.score(s).status == "red"


def test_non_admin_nulls_stay_green_with_grey_rows(make_scan):
    s = make_scan({"host": {"is_admin": False},
                   "recovery": {"winre_enabled": None, "restore_point_count": None,
                                "latest_restore_point": None}})
    r = recovery.score(s)
    assert r.status == "green"
    assert sum(row.status == "unavailable" for row in r.evidence) >= 2


# --- R1 ---


def test_r1_unavailable_passes_through(make_scan):
    r = recovery.score(make_scan(_rec(status="unavailable", error="Requires administrator rights")))
    assert r.status == "unavailable" and r.fix_ids == ()


def test_r1_failed_passes_through(make_scan):
    r = recovery.score(make_scan(_rec(status="failed", error="reagentc threw")))
    assert r.status == "failed" and r.fix_ids == ()


# --- R2 ---


def test_r2_no_points_with_restore_on_asks_for_a_restore_point(make_scan):
    # D9: System Restore is already on, so don't tell the owner to turn it on.
    r = recovery.score(make_scan(_rec(winre_enabled=False, restore_point_count=0,
                                      latest_restore_point=None)))
    assert r.status == "red"
    assert r.fix_ids == ("enable-winre", "create-restore-point")
    assert r.fix_pairs() == [("enable-winre", Status.RED), ("create-restore-point", Status.RED)]
    assert _row(r, "Windows recovery tools").status == Status.RED


def test_r2_no_winre_and_restore_off_is_red(make_scan):
    r = recovery.score(make_scan(_rec(winre_enabled=False, system_restore_enabled=False)))
    assert r.status == "red"
    assert r.fix_ids == ("enable-winre", "turn-on-system-restore")
    assert _row(r, "System Restore").status == Status.RED


def test_r2_restore_unknown_and_no_points_keeps_turn_on_fix(make_scan):
    r = recovery.score(make_scan(_rec(winre_enabled=False, system_restore_enabled=None,
                                      restore_point_count=0, latest_restore_point=None)))
    assert r.status == "red"
    assert r.fix_ids == ("enable-winre", "turn-on-system-restore")


# --- R3 ---


def test_r3_winre_off_alone_is_amber(make_scan):
    r = recovery.score(make_scan(_rec(winre_enabled=False)))
    assert r.status == "amber"
    assert r.fix_ids == ("enable-winre",)
    assert _row(r, "Windows recovery tools").status == Status.AMBER


# --- R4 ---


def test_r4_restore_off_is_amber(make_scan):
    r = recovery.score(make_scan(_rec(system_restore_enabled=False)))
    assert r.status == "amber"
    assert r.fix_ids == ("turn-on-system-restore",)


def test_r4_wins_over_r5(make_scan):
    r = recovery.score(make_scan(_rec(system_restore_enabled=False, restore_point_count=0,
                                      latest_restore_point=None)))
    assert r.fix_ids == ("turn-on-system-restore",)


# --- R5 ---


def test_r5_no_restore_points_is_amber(make_scan):
    r = recovery.score(make_scan(_rec(restore_point_count=0, latest_restore_point=None)))
    assert r.status == "amber"
    assert r.fix_ids == ("create-restore-point",)
    assert _row(r, "Restore points").value == "None"


def test_r5_restore_point_31_days_old_is_amber(make_scan):
    r = recovery.score(make_scan(_rec(latest_restore_point="2026-10-14T09:00:00Z")))
    assert r.status == "amber"
    assert r.fix_ids == ("create-restore-point",)
    assert "31 days old" in r.explanation


def test_r5_boundary_30_days_is_green(make_scan):
    r = recovery.score(make_scan(_rec(latest_restore_point="2026-10-15T09:00:00Z")))
    assert r.status == "green"


# --- R6 ---


def test_r6_all_fine_is_green_without_fixes_or_grey_rows(make_scan):
    r = recovery.score(make_scan())
    assert r.fix_ids == ()
    assert all(row.status == Status.GREEN for row in r.evidence)
    assert _row(r, "Newest restore point").value == "10 Nov 2026 (4 days ago)"
    assert ADMIN_SENTENCE not in r.explanation


# --- R7 ---


def test_r7_non_admin_nulls_add_admin_sentence(make_scan):
    s = make_scan({"host": {"is_admin": False},
                   "recovery": {"winre_enabled": None, "restore_point_count": None,
                                "latest_restore_point": None}})
    r = recovery.score(s)
    assert r.status == "green"
    assert r.fix_ids == ()
    assert ADMIN_SENTENCE in r.explanation
    assert _row(r, "Windows recovery tools").value == NEEDS_ADMIN
    assert _row(r, "Restore points").value == NEEDS_ADMIN
    assert _row(r, "System Restore").status == Status.GREEN


def test_r7_elevated_nulls_are_grey_without_admin_sentence(make_scan):
    s = make_scan(_rec(winre_enabled=None, restore_point_count=None, latest_restore_point=None))
    r = recovery.score(s)
    assert r.status == "green"
    assert ADMIN_SENTENCE not in r.explanation
    assert _row(r, "Windows recovery tools").value == "Not checked"


@pytest.mark.parametrize("patch", [
    {"winre_enabled": None, "system_restore_enabled": False},  # R4, not R2
    {"winre_enabled": None, "restore_point_count": 0, "latest_restore_point": None},  # R5
])
def test_unknown_winre_never_makes_it_red(make_scan, patch):
    r = recovery.score(make_scan({"host": {"is_admin": False}, "recovery": patch}))
    assert r.status == "amber"


def test_r7_does_not_apply_when_restore_is_off(make_scan):
    s = make_scan({"host": {"is_admin": False},
                   "recovery": {"winre_enabled": None, "system_restore_enabled": False,
                                "restore_point_count": None, "latest_restore_point": None}})
    r = recovery.score(s)
    assert r.status == "amber" and r.fix_ids == ("turn-on-system-restore",)


# --- D15: every field null ---

_ALL_NULL = {"winre_enabled": None, "system_restore_enabled": None,
             "restore_point_count": None, "latest_restore_point": None}


def test_all_null_non_admin_is_unavailable_with_grey_rows(make_scan):
    r = recovery.score(make_scan({"host": {"is_admin": False}, "recovery": _ALL_NULL}))
    assert r.status == "unavailable"
    assert r.fix_ids == ()
    assert ADMIN_SENTENCE in r.explanation
    assert [row.label for row in r.evidence] == [
        "Windows recovery tools", "System Restore", "Restore points", "Newest restore point",
    ]
    assert all(row.status == Status.UNAVAILABLE for row in r.evidence)
    assert _row(r, "System Restore").value == NEEDS_ADMIN


def test_all_null_elevated_is_unavailable_without_admin_sentence(make_scan):
    r = recovery.score(make_scan(_rec(**_ALL_NULL)))
    assert r.status == "unavailable"
    assert ADMIN_SENTENCE not in r.explanation
    assert _row(r, "Windows recovery tools").value == "Not checked"


def test_one_known_field_keeps_null_mix_green(make_scan):
    # Only System Restore unknown: WinRE on and a fresh point are real evidence.
    r = recovery.score(make_scan({"host": {"is_admin": False},
                                  "recovery": {"system_restore_enabled": None}}))
    assert r.status == "green"
    assert _row(r, "System Restore").status == Status.UNAVAILABLE
    assert ADMIN_SENTENCE in r.explanation


def test_points_counted_but_newest_date_null_is_grey_and_green(make_scan):
    r = recovery.score(make_scan(_rec(restore_point_count=2, latest_restore_point=None)))
    assert r.status == "green"
    assert _row(r, "Newest restore point").status == Status.UNAVAILABLE
