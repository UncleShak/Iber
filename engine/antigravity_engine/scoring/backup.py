"""Backup evidence scorer (s2.5.1). Rules B1-B7, first match wins.

"Backup evidence" is a dated, completed backup: File History or Windows
Backup. OneDrive sync and shadow copies are not backups (ransomware encrypts
synced files and deletes snapshots), so on their own they are amber (B5).
A null left by a non-elevated scan is a grey "needs admin" row, never red by
itself; but if nothing else is found the category is still red (s0.9 rule 3).
"""

from antigravity_engine import clock
from antigravity_engine.baseline import Baseline
from antigravity_engine.contract import ScanModel
from antigravity_engine.scoring.result import (
    NEEDS_ADMIN,
    CategoryResult,
    EvidenceRow,
    Status,
)

CATEGORY = "backup"
GREEN_MAX_DAYS = 7
AMBER_MAX_DAYS = 30

_ADMIN_HINT = " Run as administrator for a full check."


def _age_status(days: int) -> Status:
    if days <= GREEN_MAX_DAYS:
        return Status.GREEN
    if days <= AMBER_MAX_DAYS:
        return Status.AMBER
    return Status.RED


def _dated_row(label: str, iso: str, now) -> tuple[EvidenceRow, int]:
    when = clock.parse_iso(iso)
    days = max(clock.days_between(when, now), 0)
    value = f"{clock.fmt_date(when)} ({clock.fmt_age(days)})"
    return EvidenceRow(label, value, _age_status(days)), days


def score(scan: ScanModel, ctx: Baseline | None = None) -> CategoryResult:
    b = scan.backup
    # B1
    if b.status == "unavailable":
        return CategoryResult.unavailable(CATEGORY, b.error)
    if b.status == "failed":
        return CategoryResult.failed(CATEGORY, b.error)

    now = clock.now(scan)
    is_admin = scan.host.is_admin
    rows: list[EvidenceRow] = []
    ages: list[int] = []
    admin_gap = False

    # File History
    if b.file_history_last_backup is not None:
        row, days = _dated_row("File History last backup", b.file_history_last_backup, now)
        if b.file_history_enabled is False:
            row = EvidenceRow(row.label, f"{row.value}, now switched off", row.status)
        rows.append(row)
        ages.append(days)
    elif b.file_history_enabled is True:
        rows.append(EvidenceRow("File History", "On, but no backup has finished yet"))
    elif b.file_history_enabled is False:
        rows.append(EvidenceRow("File History", "Off"))
    else:
        rows.append(EvidenceRow("File History", "Not checked", Status.UNAVAILABLE))

    # Windows Backup (wbadmin needs admin, so null is unknown when not elevated)
    if b.windows_backup_last_success is not None:
        row, days = _dated_row("Windows Backup last success", b.windows_backup_last_success, now)
        rows.append(row)
        ages.append(days)
    elif not is_admin:
        rows.append(EvidenceRow("Windows Backup", NEEDS_ADMIN, Status.UNAVAILABLE))
        admin_gap = True
    else:
        rows.append(EvidenceRow("Windows Backup", "No completed backup found"))

    if b.third_party_agents:
        rows.append(EvidenceRow("Backup programs found", ", ".join(b.third_party_agents)))
    else:
        rows.append(EvidenceRow("Backup programs found", "None"))

    if b.onedrive_kfm_folders:
        folders = ", ".join(b.onedrive_kfm_folders)
        rows.append(EvidenceRow("OneDrive folder sync", f"{folders} (sync, not a backup)"))
    else:
        rows.append(EvidenceRow("OneDrive folder sync", "Not set up"))

    if b.shadow_copy_count is None:
        if not is_admin:
            rows.append(EvidenceRow("Shadow copies", NEEDS_ADMIN, Status.UNAVAILABLE))
            admin_gap = True
        else:
            rows.append(EvidenceRow("Shadow copies", "Not checked", Status.UNAVAILABLE))
    elif b.shadow_copy_count >= 1:
        n = b.shadow_copy_count
        noun = "snapshot" if n == 1 else "snapshots"
        rows.append(EvidenceRow("Shadow copies", f"{n} {noun} (not a backup)"))
    else:
        rows.append(EvidenceRow("Shadow copies", "None"))

    hint = _ADMIN_HINT if admin_gap else ""
    newest = min(ages) if ages else None

    # B2
    if newest is not None and newest <= GREEN_MAX_DAYS:
        return CategoryResult.rated(
            CATEGORY, Status.GREEN,
            f"Your newest backup finished {clock.fmt_age(newest)}. Keep backing up at least weekly.",
            rows,
        )
    # B3
    if newest is not None and newest <= AMBER_MAX_DAYS:
        return CategoryResult.rated(
            CATEGORY, Status.AMBER,
            f"Your newest backup is {newest} days old. Work changed since then would be lost "
            "in a ransomware attack.",
            rows, ["run-backup-now"],
        )
    if newest is None:
        # B4
        if b.third_party_agents:
            return CategoryResult.rated(
                CATEGORY, Status.AMBER,
                "A backup program is installed, but we couldn't see a recent completed backup "
                "from it." + hint,
                rows, ["verify-backup-agent"],
            )
        # B5
        has_sync = bool(b.onedrive_kfm_folders)
        has_shadow = (b.shadow_copy_count or 0) >= 1
        if has_sync or has_shadow:
            if has_sync and has_shadow:
                what = "OneDrive sync and shadow copies are not backups: ransomware can lock " \
                    "synced files and delete snapshots."
            elif has_sync:
                what = "OneDrive sync is not a backup: ransomware can lock synced files too."
            else:
                what = "Shadow copies are not a backup: ransomware deletes them first."
            return CategoryResult.rated(
                CATEGORY, Status.AMBER,
                f"{what} Set up a real backup." + hint,
                rows, ["turn-on-file-history"],
            )
        # B7
        return CategoryResult.rated(
            CATEGORY, Status.RED,
            "We found no backup of any kind. If ransomware locked your files, there would be "
            "no copy to get them back from." + hint,
            rows, ["turn-on-file-history"],
        )
    # B6
    return CategoryResult.rated(
        CATEGORY, Status.RED,
        f"Your newest backup is {newest} days old, which is too old to rely on after a "
        "ransomware attack." + hint,
        rows, ["turn-on-file-history"],
    )
