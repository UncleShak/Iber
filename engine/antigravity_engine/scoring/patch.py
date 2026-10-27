"""Patch status scorer (s2.5.2). Rules P1-P6, first match wins, then the OS
support overlay, which can only make the result worse.

Days since the newest hotfix are always recomputed from
latest_hotfix_installed_on and collected_at; the collector's
days_since_latest_hotfix is only compared, never trusted (s2.4 rule 5).
"""

from antigravity_engine import clock
from antigravity_engine.baseline import Baseline
from antigravity_engine.contract import ScanModel
from antigravity_engine.scoring.result import (
    MAX_EXPLANATION,
    CategoryResult,
    EvidenceRow,
    Status,
    worst,
)

CATEGORY = "patch"
GREEN_MAX_DAYS = 30
AMBER_MAX_DAYS = 60
# s2.4 rule 5: disagreement beyond this many days gets an evidence note.
MISMATCH_TOLERANCE_DAYS = 1


def _age_status(days: int) -> Status:
    if days > AMBER_MAX_DAYS:
        return Status.RED
    if days > GREEN_MAX_DAYS:
        return Status.AMBER
    return Status.GREEN


def _os_overlay(scan: ScanModel, ctx: Baseline) -> str | None:
    """Sentence to add when this Windows build is out of support, else None."""
    build = scan.host.os_build
    if build.startswith("19"):
        eos = clock.fmt_date(clock.parse_iso(ctx.win10_eos_date))
        return (
            f"Windows 10 support ended on {eos} unless you've enrolled in "
            "Extended Security Updates."
        )
    # Both are digit strings (scan and baseline schemas); compare as numbers.
    if int(build) < int(ctx.win11_min_build):
        return "This Windows version is no longer supported, so it stops getting security fixes."
    return None


def _rate(scan: ScanModel, rows: list[EvidenceRow]) -> tuple[Status, str, list[str]]:
    """P2-P6 on an ok section. Appends evidence rows; returns status, explanation, fixes."""
    p = scan.patch
    # P2
    if p.hotfix_count == 0 or p.latest_hotfix_installed_on is None:
        rows.append(EvidenceRow("Newest Windows update", "None found", Status.RED))
        return (
            Status.RED,
            "We found no installed Windows updates, so this PC is likely missing security fixes.",
            ["install-updates"],
        )

    latest = clock.parse_iso(p.latest_hotfix_installed_on)
    days = max(clock.days_between(latest, clock.now(scan)), 0)
    value = f"{clock.fmt_date(latest)} ({clock.fmt_age(days)})"
    kbs = [h.kb for h in p.hotfixes if h.installed_on == p.latest_hotfix_installed_on]
    if kbs:
        value += f", {kbs[0]}"
    age_status = _age_status(days)
    rows.append(EvidenceRow("Newest Windows update", value, age_status))

    reported = p.days_since_latest_hotfix
    if reported is not None and abs(reported - days) > MISMATCH_TOLERANCE_DAYS:
        rows.append(
            EvidenceRow(
                "Note",
                f"The scan reported {reported} days; recalculated as {days} days "
                "from the install date.",
            )
        )

    # P3
    if age_status == Status.RED:
        return (
            Status.RED,
            f"The newest Windows update is {days} days old, so this PC has probably missed "
            "security fixes.",
            ["install-updates"],
        )
    # P4
    if age_status == Status.AMBER:
        return (
            Status.AMBER,
            f"The newest Windows update is {days} days old. Install the latest updates soon.",
            ["install-updates"],
        )
    # P5
    if p.pending_reboot is True:
        return (
            Status.AMBER,
            "Updates are installed but waiting for a restart. They don't protect you until "
            "you restart.",
            ["restart-to-finish-updates"],
        )
    # P6
    return (
        Status.GREEN,
        f"Windows updates are current: the newest was installed {clock.fmt_age(days)}.",
        [],
    )


def score(scan: ScanModel, ctx: Baseline) -> CategoryResult:
    p = scan.patch
    # P1
    if p.status == "unavailable":
        return CategoryResult.unavailable(CATEGORY, p.error)
    if p.status == "failed":
        return CategoryResult.failed(CATEGORY, p.error)

    rows: list[EvidenceRow] = []
    status, explanation, fix_ids = _rate(scan, rows)

    if p.hotfix_count is not None:
        noun = "update" if p.hotfix_count == 1 else "updates"
        rows.append(EvidenceRow("Updates installed", f"{p.hotfix_count} {noun}"))

    if p.pending_reboot is None:
        rows.append(EvidenceRow("Restart needed to finish updates", "Not checked", Status.UNAVAILABLE))
    elif p.pending_reboot:
        rows.append(EvidenceRow("Restart needed to finish updates", "Yes", Status.AMBER))
    else:
        rows.append(EvidenceRow("Restart needed to finish updates", "No", Status.GREEN))

    # OS support overlay: at least amber, never better than P1-P6 gave.
    fix_severity: dict[str, Status] = {}
    os_value = f"{scan.host.os_caption} (build {scan.host.os_build})"
    overlay = _os_overlay(scan, ctx)
    if overlay is None:
        rows.append(EvidenceRow("Windows version", os_value, Status.GREEN))
    else:
        rows.append(EvidenceRow("Windows version", f"{os_value}, out of support", Status.AMBER))
        status = worst([status, Status.AMBER])
        if status == Status.RED:
            fix_severity["plan-windows-11"] = Status.AMBER
        fix_ids = [*fix_ids, "plan-windows-11"]
        joined = f"{explanation} {overlay}"
        explanation = joined if len(joined) <= MAX_EXPLANATION else overlay

    return CategoryResult.rated(CATEGORY, status, explanation, rows, fix_ids, fix_severity)
