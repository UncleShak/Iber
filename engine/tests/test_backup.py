"""s2.5.1 backup rules B1-B7. Healthy fixture: collected_at 2026-11-14T16:42:07Z,
File History last backup 2026-11-13 (1 day), KFM 3 folders, 3 shadow copies."""

import pytest

from antigravity_engine.scoring import backup
from antigravity_engine.scoring.result import MAX_EXPLANATION, NEEDS_ADMIN

# No dated backup and nothing else: the B7 starting point.
NOTHING = {
    "file_history_enabled": False,
    "file_history_last_backup": None,
    "windows_backup_last_success": None,
    "onedrive_kfm_folders": [],
    "shadow_copy_count": 0,
    "third_party_agents": [],
}


def _nothing(**overrides) -> dict:
    return {"backup": {**NOTHING, **overrides}}


def _row(result, label):
    return next(r for r in result.evidence if r.label == label)


# --- examples from s2.10 ---


def test_recent_file_history_is_green(make_scan):
    r = backup.score(make_scan())  # healthy: FH 1 day old
    assert r.status == "green"
    assert r.fix_ids == ()


def test_onedrive_only_is_amber_not_green(make_scan):
    s = make_scan({"backup": {"file_history_enabled": False, "file_history_last_backup": None,
                              "shadow_copy_count": 0, "third_party_agents": []}})
    r = backup.score(s)  # KFM still present in healthy fixture
    assert r.status == "amber" and "turn-on-file-history" in r.fix_ids


def test_no_evidence_is_red(make_scan):
    s = make_scan({"backup": {"file_history_enabled": False, "file_history_last_backup": None,
                              "onedrive_kfm_folders": [], "shadow_copy_count": 0,
                              "third_party_agents": []}})
    assert backup.score(s).status == "red"


def test_old_backup_over_30_days_is_red(make_scan):
    s = make_scan({"backup": {"file_history_last_backup": "2026-09-01T22:00:00Z"}})
    assert backup.score(s).status == "red"


# --- B1 ---


def test_b1_unavailable_passes_through(make_scan):
    r = backup.score(make_scan({"backup": {"status": "unavailable",
                                           "error": "Requires administrator rights"}}))
    assert r.status == "unavailable"
    assert r.fix_ids == ()
    assert "administrator" in r.explanation


def test_b1_failed_passes_through(make_scan):
    r = backup.score(make_scan({"backup": {"status": "failed", "error": "probe threw"}}))
    assert r.status == "failed"
    assert r.fix_ids == ()
    assert "probe threw" in r.explanation


# --- B2 / B3 / B6 age boundaries ---


@pytest.mark.parametrize(
    ("last", "expected", "fixes"),
    [
        ("2026-11-14T08:00:00Z", "green", ()),                          # 0 days
        ("2026-11-07T22:00:00Z", "green", ()),                          # 7 days (B2 edge)
        ("2026-11-06T22:00:00Z", "amber", ("run-backup-now",)),         # 8 days (B3 start)
        ("2026-10-15T22:00:00Z", "amber", ("run-backup-now",)),         # 30 days (B3 edge)
        ("2026-10-14T22:00:00Z", "red", ("turn-on-file-history",)),     # 31 days (B6)
    ],
)
def test_backup_age_boundaries(make_scan, last, expected, fixes):
    r = backup.score(make_scan({"backup": {"file_history_last_backup": last}}))
    assert r.status == expected
    assert r.fix_ids == fixes


def test_b2_windows_backup_alone_counts(make_scan):
    r = backup.score(make_scan(_nothing(windows_backup_last_success="2026-11-12T01:00:00Z")))
    assert r.status == "green"
    assert _row(r, "Windows Backup last success").value == "12 Nov 2026 (2 days ago)"


def test_newest_is_max_of_both_dates(make_scan):
    # FH is 60 days old (red alone) but Windows Backup is 3 days old -> green.
    s = make_scan({"backup": {"file_history_last_backup": "2026-09-15T22:00:00Z",
                              "windows_backup_last_success": "2026-11-11T03:00:00Z"}})
    r = backup.score(s)
    assert r.status == "green"
    assert _row(r, "File History last backup").status == "red"
    assert _row(r, "Windows Backup last success").status == "green"


def test_b3_explanation_names_age(make_scan):
    r = backup.score(make_scan({"backup": {"file_history_last_backup": "2026-11-01T22:00:00Z"}}))
    assert r.status == "amber"
    assert "13 days old" in r.explanation


def test_b6_old_backup_beats_agents_and_sync(make_scan):
    # B4/B5 only apply when there is NO dated backup; a stale one is still red.
    s = make_scan({"backup": {"file_history_last_backup": "2026-08-01T22:00:00Z",
                              "third_party_agents": ["Veeam Agent"]}})
    r = backup.score(s)
    assert r.status == "red"
    assert r.fix_ids == ("turn-on-file-history",)
    assert "105 days old" in r.explanation


# --- B4 / B5 ---


def test_b4_agent_without_dated_backup_is_amber(make_scan):
    r = backup.score(make_scan(_nothing(third_party_agents=["Veeam Agent"])))
    assert r.status == "amber"
    assert r.fix_ids == ("verify-backup-agent",)
    assert _row(r, "Backup programs found").value == "Veeam Agent"


def test_b4_wins_over_b5(make_scan):
    s = make_scan(_nothing(third_party_agents=["Acronis"], onedrive_kfm_folders=["Desktop"],
                           shadow_copy_count=2))
    r = backup.score(s)
    assert r.status == "amber"
    assert r.fix_ids == ("verify-backup-agent",)


def test_b5_shadow_copies_only_is_amber_not_green(make_scan):
    r = backup.score(make_scan(_nothing(shadow_copy_count=1)))
    assert r.status == "amber"
    assert r.fix_ids == ("turn-on-file-history",)
    assert "Shadow copies are not a backup" in r.explanation
    assert _row(r, "Shadow copies").value == "1 snapshot (not a backup)"


def test_b5_onedrive_only_explanation_and_row(make_scan):
    r = backup.score(make_scan(_nothing(onedrive_kfm_folders=["Desktop", "Documents"])))
    assert r.status == "amber"
    assert "OneDrive sync is not a backup" in r.explanation
    assert _row(r, "OneDrive folder sync").value == "Desktop, Documents (sync, not a backup)"


def test_b5_sync_and_shadow_together(make_scan):
    r = backup.score(make_scan(_nothing(onedrive_kfm_folders=["Pictures"], shadow_copy_count=4)))
    assert r.status == "amber"
    assert "OneDrive sync and shadow copies are not backups" in r.explanation


# --- B7 ---


def test_b7_nothing_found_is_red_with_fix(make_scan):
    r = backup.score(make_scan(_nothing()))
    assert r.status == "red"
    assert r.fix_ids == ("turn-on-file-history",)
    assert _row(r, "File History").value == "Off"
    assert _row(r, "Shadow copies").value == "None"


def test_b7_file_history_on_but_never_ran_is_still_red(make_scan):
    r = backup.score(make_scan(_nothing(file_history_enabled=True)))
    assert r.status == "red"
    assert _row(r, "File History").value == "On, but no backup has finished yet"


# --- RPT-02: the rows that decided B4/B5/B7 carry the category status ---


def test_b4_agent_row_is_amber(make_scan):
    r = backup.score(make_scan(_nothing(third_party_agents=["Veeam Agent"],
                                        onedrive_kfm_folders=["Desktop"])))
    assert _row(r, "Backup programs found").status == "amber"
    assert _row(r, "OneDrive folder sync").status is None


@pytest.mark.parametrize(
    ("sync", "shadow", "amber_rows"),
    [
        (["Desktop"], 0, {"OneDrive folder sync"}),
        ([], 2, {"Shadow copies"}),
        (["Desktop"], 2, {"OneDrive folder sync", "Shadow copies"}),
    ],
)
def test_b5_only_the_deciding_rows_are_amber(make_scan, sync, shadow, amber_rows):
    r = backup.score(make_scan(_nothing(onedrive_kfm_folders=sync, shadow_copy_count=shadow)))
    assert {row.label for row in r.evidence if row.status == "amber"} == amber_rows
    assert all(row.status in ("amber", None) for row in r.evidence)


def test_b7_every_nothing_found_row_is_red(make_scan):
    r = backup.score(make_scan(_nothing()))
    assert all(row.status == "red" for row in r.evidence)


def test_b7_keeps_grey_rows_grey(make_scan):
    s = make_scan({"host": {"is_admin": False},
                   **_nothing(windows_backup_last_success=None, shadow_copy_count=None)})
    r = backup.score(s)
    assert r.status == "red"
    assert _row(r, "Windows Backup").status == "unavailable"
    assert _row(r, "Shadow copies").status == "unavailable"
    assert _row(r, "File History").status == "red"


# --- non-admin nulls ---

NON_ADMIN = {"host": {"is_admin": False}}


def test_non_admin_nulls_are_grey_rows_not_red(make_scan):
    s = make_scan({**NON_ADMIN, "backup": {"windows_backup_last_success": None,
                                           "shadow_copy_count": None}})
    r = backup.score(s)
    assert r.status == "green"  # dated FH backup still decides
    for label in ("Windows Backup", "Shadow copies"):
        row = _row(r, label)
        assert row.value == NEEDS_ADMIN
        assert row.status == "unavailable"


def test_non_admin_with_no_other_evidence_is_red_and_says_run_as_admin(make_scan):
    s = make_scan({**NON_ADMIN, **_nothing(shadow_copy_count=None)})
    r = backup.score(s)
    assert r.status == "red"  # absence is the finding (s0.9 rule 3)
    assert r.explanation.endswith("Run as administrator for a full check.")
    assert _row(r, "Shadow copies").status == "unavailable"


def test_admin_null_windows_backup_means_none_found(make_scan):
    r = backup.score(make_scan())
    row = _row(r, "Windows Backup")
    assert row.value == "No completed backup found"
    assert row.status is None


def test_admin_null_shadow_count_is_grey_not_checked(make_scan):
    r = backup.score(make_scan({"backup": {"shadow_copy_count": None}}))
    assert _row(r, "Shadow copies").value == "Not checked"
    assert _row(r, "Shadow copies").status == "unavailable"


def test_unknown_file_history_state_is_grey(make_scan):
    r = backup.score(make_scan(_nothing(file_history_enabled=None, shadow_copy_count=1)))
    assert _row(r, "File History").status == "unavailable"


# --- evidence formatting and limits ---


def test_evidence_dates_are_human_formatted(make_scan):
    r = backup.score(make_scan())
    assert _row(r, "File History last backup").value == "13 Nov 2026 (1 day ago)"


def test_file_history_switched_off_after_last_backup(make_scan):
    r = backup.score(make_scan({"backup": {"file_history_enabled": False}}))
    assert r.status == "green"
    assert _row(r, "File History last backup").value.endswith(", now switched off")


@pytest.mark.parametrize(
    "patch",
    [
        {},
        {"backup": {"file_history_last_backup": "2026-11-01T22:00:00Z"}},
        {"backup": {"file_history_last_backup": "1990-01-01T00:00:00Z"}, **NON_ADMIN},
        _nothing(third_party_agents=["Veeam Agent"]),
        _nothing(onedrive_kfm_folders=["Desktop"], shadow_copy_count=3),
        {**NON_ADMIN, **_nothing(shadow_copy_count=None, third_party_agents=["X" * 300])},
        {**NON_ADMIN, **_nothing(onedrive_kfm_folders=["Desktop"], shadow_copy_count=None)},
        {**NON_ADMIN, **_nothing(shadow_copy_count=None)},
    ],
)
def test_explanation_and_evidence_within_limits(make_scan, patch):
    r = backup.score(make_scan(patch))
    assert 0 < len(r.explanation) <= MAX_EXPLANATION
    assert 1 <= len(r.evidence) <= 8
