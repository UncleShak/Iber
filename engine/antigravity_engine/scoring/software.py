"""Outdated software scorer (s2.5.3). Rules S1-S7, first match wins.

Evaluation order is S1, S7, S6, S2, S3, S4, S5 (decision D7): S6 "nothing
matched" must come before S5, or "all matched apps are safe" is vacuously
true on an empty match set.

Only apps that match a baseline entry are assessed. Everything else is
counted in one "not on our watch list" row and never affects the status.
When several installed apps match one entry, the lowest readable version is
assessed (worst case). A version that can't be read is a neutral row.
"""

from dataclasses import dataclass
from functools import cmp_to_key

from antigravity_engine.baseline import Baseline, BaselineEntry, compare_versions, is_below
from antigravity_engine.contract import InstalledApp, ScanModel
from antigravity_engine.scoring.fixes import CATALOGUE
from antigravity_engine.scoring.result import (
    MAX_EVIDENCE,
    CategoryResult,
    EvidenceRow,
    Status,
)

CATEGORY = "software"
FIX_ID = "update-outdated-apps"
# S7 fix (D11): RPT-03 needs every amber finding to carry a fix.
RESCAN_FIX_ID = "rescan-installed-apps"
MAX_OUTDATED_ROWS = 6
MAX_NAMED_IN_STEPS = 4
MAX_NAMED_IN_EXPLANATION = 2


@dataclass(frozen=True)
class _Assessed:
    entry: BaselineEntry
    version: str | None  # lowest readable version, None if none readable
    raw_versions: tuple[str, ...]
    below: bool  # version is below min_safe_version

    @property
    def outdated(self) -> bool:
        return self.entry.eol or self.below

    @property
    def status(self) -> Status | None:
        if self.entry.eol or (self.below and self.entry.severity == "high"):
            return Status.RED
        if self.below:
            return Status.AMBER
        if self.version is None:
            return None
        return Status.GREEN


def _lowest(versions: list[str]) -> str | None:
    """Lowest version that can be read, or None if none can."""
    readable = [v for v in versions if compare_versions(v, v) is not None]
    if not readable:
        return None
    return min(readable, key=cmp_to_key(lambda a, b: compare_versions(a, b) or 0))


def _assess(entry: BaselineEntry, apps: list[InstalledApp]) -> _Assessed:
    versions = [a.version for a in apps]
    version = _lowest(versions)
    below = version is not None and bool(is_below(version, entry.min_safe_version))
    return _Assessed(entry, version, tuple(versions), below)


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def _join_names(names: list[str], limit: int) -> str:
    """"A", "A and B", "A, B and C", or "A, B and 3 more" past the limit."""
    if len(names) > limit:
        shown = names[:limit]
        return f"{', '.join(shown)} and {len(names) - limit} more"
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} and {names[-1]}"


def _row(a: _Assessed) -> EvidenceRow:
    e = a.entry
    copies = len(a.raw_versions)
    if e.eol:
        value = "No longer supported" if a.version is None else f"{a.version}, no longer supported"
    elif a.version is None:
        shown = ", ".join(f'"{v}"' for v in a.raw_versions)
        value = f"Version not readable ({shown})"
    elif a.below:
        value = f"{a.version}, needs {e.min_safe_version} or newer"
    else:
        value = f"{a.version}, up to date"
    if copies > 1 and a.version is not None:
        value += f" (oldest of {copies} copies)"
    return EvidenceRow(e.display_name, value, a.status)


def _steps(outdated: list[_Assessed]) -> tuple[str, ...]:
    names = [a.entry.display_name for a in outdated]
    generic = CATALOGUE[FIX_ID].steps
    steps = [f"Update these programs: {_join_names(names, MAX_NAMED_IN_STEPS)}.", generic[1]]
    eol = [a.entry.display_name for a in outdated if a.entry.eol]
    if eol:
        steps.append(
            f"Uninstall {_join_names(eol, MAX_NAMED_IN_STEPS)} from Settings > Apps: "
            "no update will make it safe."
        )
    return tuple(steps)


def _who(items: list[_Assessed], one: str, many: str) -> str:
    """Names for an explanation plus the matching verb, e.g. "Zoom is"."""
    names = _join_names([a.entry.display_name for a in items], MAX_NAMED_IN_EXPLANATION)
    return f"{names} {_plural(len(items), one, many)}"


def _not_watched_row(count: int, any_matched: bool) -> EvidenceRow:
    other = "other " if any_matched else ""
    noun = _plural(count, "app", "apps")
    return EvidenceRow("Other programs", f"{count} {other}{noun} not on our watch list")


def score(scan: ScanModel, ctx: Baseline) -> CategoryResult:
    s = scan.software
    # S1
    if s.status == "unavailable":
        return CategoryResult.unavailable(CATEGORY, s.error)
    if s.status == "failed":
        return CategoryResult.failed(CATEGORY, s.error)

    # S7
    if not s.installed:
        return CategoryResult.rated(
            CATEGORY, Status.AMBER,
            "We couldn't read the installed-apps list, so outdated programs weren't checked.",
            [EvidenceRow("Installed programs", "None found", Status.AMBER)],
            [RESCAN_FIX_ID],
        )

    groups: dict[str, list[InstalledApp]] = {}
    unmatched = 0
    for app in s.installed:
        entry = ctx.match(app.name, app.publisher)
        if entry is None:
            unmatched += 1
        else:
            groups.setdefault(entry.id, []).append(app)

    # S6
    total = len(s.installed)
    if not groups:
        noun = _plural(total, "app is", "apps are")
        return CategoryResult.rated(
            CATEGORY, Status.GREEN,
            f"None of your {total} {noun} on our watch list, so there is nothing to update.",
            [_not_watched_row(unmatched, any_matched=False)],
        )

    # Baseline order keeps results stable whatever order the collector used.
    assessed = [_assess(e, groups[e.id]) for e in ctx.entries if e.id in groups]
    eol = [a for a in assessed if a.entry.eol]
    high = [a for a in assessed if not a.entry.eol and a.below and a.entry.severity == "high"]
    medium = [a for a in assessed if not a.entry.eol and a.below and a.entry.severity == "medium"]
    outdated = eol + high + medium
    others = [a for a in assessed if not a.outdated]
    # Unreadable rows before up-to-date ones; both after the outdated apps.
    others.sort(key=lambda a: a.version is not None)

    rows = [_row(a) for a in outdated[:MAX_OUTDATED_ROWS]]
    room = MAX_EVIDENCE - 1 - len(rows)
    rows += [_row(a) for a in others[:room]]
    rows.append(_not_watched_row(unmatched, any_matched=True))

    if outdated:
        steps = {FIX_ID: _steps(outdated)}
        # S2
        if eol:
            return CategoryResult.rated(
                CATEGORY, Status.RED,
                f"{_who(eol, 'is', 'are')} no longer supported and will never get security "
                "fixes again.",
                rows, [FIX_ID], fix_steps=steps,
            )
        # S3
        if high:
            have = _plural(len(high), "has", "have")
            return CategoryResult.rated(
                CATEGORY, Status.RED,
                f"{_who(high, 'is', 'are')} out of date and {have} known security holes "
                "that attackers use.",
                rows, [FIX_ID], fix_steps=steps,
            )
        # S4
        return CategoryResult.rated(
            CATEGORY, Status.AMBER,
            f"{_who(medium, 'is', 'are')} out of date. Update when you can.",
            rows, [FIX_ID], fix_steps=steps,
        )

    # S5
    checked = sum(1 for a in assessed if a.version is not None)
    if checked == 0:
        explanation = "We couldn't read the versions of the programs on our watch list."
    else:
        noun = _plural(checked, "program on our watch list is", "programs on our watch list are")
        explanation = f"The {checked} {noun} up to date."
    return CategoryResult.rated(CATEGORY, Status.GREEN, explanation, rows)
