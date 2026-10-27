"""Recovery readiness scorer (s2.5.5). Rules R1-R7, first match wins.

reagentc and Get-ComputerRestorePoint need admin, so a non-elevated scan
leaves winre_enabled and restore_point_count null (s3.5). R2-R5 only fire on
known values; a null field is a grey row and never makes the category worse.
R7 (both admin fields null, System Restore on) is green with grey rows and
the "Run as administrator" sentence. The same green-with-grey-rows result is
used for any other mix of nulls that R2-R5 leave unrated.
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

CATEGORY = "recovery"
RESTORE_POINT_MAX_DAYS = 30

_ADMIN_HINT = " Run as administrator for a full check."


def _grey(label: str, is_admin: bool) -> EvidenceRow:
    """Grey row for a null field: "needs admin" when the scan wasn't elevated."""
    return EvidenceRow(label, "Not checked" if is_admin else NEEDS_ADMIN, Status.UNAVAILABLE)


def score(scan: ScanModel, ctx: Baseline | None = None) -> CategoryResult:
    r = scan.recovery
    # R1
    if r.status == "unavailable":
        return CategoryResult.unavailable(CATEGORY, r.error)
    if r.status == "failed":
        return CategoryResult.failed(CATEGORY, r.error)

    is_admin = scan.host.is_admin
    winre_off = r.winre_enabled is False
    restore_off = r.system_restore_enabled is False
    no_points = r.restore_point_count == 0
    r2 = winre_off and (restore_off or no_points)
    # Rows that caused R2 are red so the category cites matching evidence.
    off = Status.RED if r2 else Status.AMBER

    rows: list[EvidenceRow] = []
    if r.winre_enabled is None:
        rows.append(_grey("Windows recovery tools", is_admin))
    else:
        rows.append(EvidenceRow("Windows recovery tools", "On" if r.winre_enabled else "Off",
                                Status.GREEN if r.winre_enabled else off))

    if r.system_restore_enabled is None:
        rows.append(_grey("System Restore", is_admin))
    else:
        rows.append(EvidenceRow("System Restore", "On" if r.system_restore_enabled else "Off",
                                Status.GREEN if r.system_restore_enabled else off))

    point_days: int | None = None
    if r.restore_point_count is None:
        rows.append(_grey("Restore points", is_admin))
    elif no_points:
        rows.append(EvidenceRow("Restore points", "None", off))
    else:
        rows.append(EvidenceRow("Restore points", str(r.restore_point_count), Status.GREEN))

    if not no_points:
        if r.latest_restore_point is None:
            rows.append(_grey("Newest restore point", is_admin))
        else:
            when = clock.parse_iso(r.latest_restore_point)
            point_days = max(clock.days_between(when, clock.now(scan)), 0)
            old = point_days > RESTORE_POINT_MAX_DAYS
            rows.append(EvidenceRow(
                "Newest restore point",
                f"{clock.fmt_date(when)} ({clock.fmt_age(point_days)})",
                Status.AMBER if old else Status.GREEN,
            ))

    # R2
    if r2:
        return CategoryResult.rated(
            CATEGORY, Status.RED,
            "If Windows stopped starting, this PC has no recovery tools and no restore point "
            "to roll back to.",
            rows, ["enable-winre", "turn-on-system-restore"],
        )
    # R3
    if winre_off:
        return CategoryResult.rated(
            CATEGORY, Status.AMBER,
            "The Windows recovery tools are off, so repairing Windows after a failure is "
            "much harder.",
            rows, ["enable-winre"],
        )
    # R4
    if restore_off:
        return CategoryResult.rated(
            CATEGORY, Status.AMBER,
            "System Restore is off, so you can't undo a bad change to Windows.",
            rows, ["turn-on-system-restore"],
        )
    # R5
    if no_points:
        return CategoryResult.rated(
            CATEGORY, Status.AMBER,
            "System Restore is on, but there is no restore point to roll back to.",
            rows, ["create-restore-point"],
        )
    if point_days is not None and point_days > RESTORE_POINT_MAX_DAYS:
        return CategoryResult.rated(
            CATEGORY, Status.AMBER,
            f"Your newest restore point is {point_days} days old, so rolling back would undo "
            "a lot of changes.",
            rows, ["create-restore-point"],
        )

    unknown = any(row.status == Status.UNAVAILABLE for row in rows)
    # R6
    if not unknown:
        return CategoryResult.rated(
            CATEGORY, Status.GREEN,
            f"The Windows recovery tools and System Restore are on, with a restore point from "
            f"{clock.fmt_age(point_days or 0)}.",
            rows,
        )
    # R7 (and any other mix of unknown fields that R2-R5 left unrated)
    hint = _ADMIN_HINT if not is_admin else ""
    if r.system_restore_enabled:
        base = "System Restore is on, but some recovery settings couldn't be checked."
    else:
        base = "Some recovery settings couldn't be checked."
    return CategoryResult.rated(CATEGORY, Status.GREEN, base + hint, rows)
