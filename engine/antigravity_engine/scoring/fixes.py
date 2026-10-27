"""Fix catalogue (s2.9) and top-3 ranking (s0.8, s2.6).

Steps are written for a non-technical owner-manager: 1-5 short items, no jargon.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from antigravity_engine.scoring.result import Status

MAX_TOP = 3

# s0.8 ranking: category order used after severity.
FIX_CATEGORY_RANK = {"protection": 0, "backup": 1, "patch": 2, "recovery": 3, "software": 4}
_SEVERITY_RANK = {Status.RED: 0, Status.AMBER: 1}


@dataclass(frozen=True)
class Fix:
    id: str
    category: str
    title: str
    why: str
    steps: tuple[str, ...]
    effort_minutes: int
    needs_admin: bool

    def to_dict(self, severity: Status, steps: Sequence[str] | None = None) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "severity": str(severity),
            "title": self.title,
            "why": self.why,
            "steps": list(steps or self.steps),
            "effort_minutes": self.effort_minutes,
            "needs_admin": self.needs_admin,
        }


_FIXES = (
    # --- protection ---
    Fix(
        "enable-defender", "protection",
        "Turn Microsoft Defender back on",
        "Without antivirus, ransomware can run unnoticed.",
        (
            "Click Start and open Windows Security.",
            "Choose Virus & threat protection, then Manage settings.",
            "Switch Real-time protection to On.",
            "If it switches itself off again, ask your IT helper to check for other security software.",
        ),
        5, True,
    ),
    Fix(
        "update-defender-definitions", "protection",
        "Update Microsoft Defender's virus list",
        "Defender only spots threats it knows about. An old virus list misses new ransomware.",
        (
            "Click Start and open Windows Security.",
            "Choose Virus & threat protection.",
            "Under Protection updates, click Check for updates.",
            "Wait until it says the list is up to date.",
        ),
        5, False,
    ),
    Fix(
        "turn-on-bitlocker", "protection",
        "Encrypt this PC's hard drive with BitLocker",
        "If the PC is lost or stolen, encryption stops anyone reading your business files.",
        (
            "Click Start, type BitLocker and open Manage BitLocker.",
            "Next to the C: drive, click Turn on BitLocker.",
            "Save the recovery key to your Microsoft account or print it, and keep it somewhere safe.",
            "Choose to encrypt the used disk space only, then Start encrypting.",
            "Keep the PC switched on and plugged in until it finishes.",
        ),
        20, True,
    ),
    Fix(
        "encrypt-device-home", "protection",
        "Turn on Device encryption (Windows Home)",
        "Windows Home has no BitLocker, but Device encryption still protects files if the PC is stolen.",
        (
            "Click Start and open Settings.",
            "Go to Privacy & security (Windows 11) or Update & Security (Windows 10), then Device encryption.",
            "Switch Device encryption On. You must be signed in with a Microsoft account.",
            "If the option is missing, ask your IT helper about upgrading to Windows Pro.",
        ),
        15, True,
    ),
    Fix(
        "enable-tamper-protection", "protection",
        "Turn on Tamper Protection",
        "Ransomware often tries to switch antivirus off first. Tamper Protection blocks that.",
        (
            "Click Start and open Windows Security.",
            "Choose Virus & threat protection, then Manage settings.",
            "Switch Tamper Protection to On.",
        ),
        3, True,
    ),
    Fix(
        "enable-cfa", "protection",
        "Turn on Controlled folder access",
        "It stops unknown programs from changing files in your Documents and Desktop folders.",
        (
            "Click Start and open Windows Security.",
            "Choose Virus & threat protection, then Manage ransomware protection.",
            "Switch Controlled folder access to On.",
            "If a trusted program gets blocked, click Allow an app through Controlled folder access and add it.",
        ),
        5, True,
    ),
    Fix(
        "enable-asr-rules", "protection",
        "Switch on Defender's anti-ransomware rules",
        "These rules block common tricks ransomware uses, such as harmful email attachments.",
        (
            "Ask your IT helper to turn on Microsoft Defender's Attack Surface Reduction rules.",
            "Ask for the ransomware-related rules to be set to Block.",
            "Use the PC as normal for a day and report anything that stops working.",
        ),
        15, True,
    ),
    # --- backup ---
    Fix(
        "turn-on-file-history", "backup",
        "Start backing up your files with File History",
        "If ransomware locks your files, a recent backup is the only way to get them back for free.",
        (
            "Plug in an external USB drive with enough space for your files.",
            "Click Start, type File History and open it.",
            "Choose the USB drive and click Turn on.",
            "Click Run now to make the first backup.",
            "Unplug the drive when it finishes and store it away from the PC.",
        ),
        15, False,
    ),
    Fix(
        "run-backup-now", "backup",
        "Run a fresh backup today",
        "Your last backup is more than a week old. Anything changed since then could be lost.",
        (
            "Plug in your backup drive.",
            "Click Start, type File History and open it.",
            "Click Run now and wait for it to finish.",
            "Set a weekly reminder to plug the drive in.",
        ),
        10, False,
    ),
    Fix(
        "verify-backup-agent", "backup",
        "Check your backup program is actually working",
        "A backup program is installed, but we couldn't see a recent completed backup.",
        (
            "Open your backup program from the Start menu.",
            "Look for the date of the last successful backup.",
            "If it is older than a week or shows errors, run a backup now.",
            "Try restoring one file to make sure the backup really works.",
        ),
        10, False,
    ),
    # --- patch ---
    Fix(
        "install-updates", "patch",
        "Install the latest Windows updates",
        "Missing updates are the most common way attackers get into a PC.",
        (
            "Save your work and close your programs.",
            "Click Start, open Settings and go to Windows Update.",
            "Click Check for updates, then Download and install.",
            "Restart the PC when asked.",
        ),
        30, True,
    ),
    Fix(
        "restart-to-finish-updates", "patch",
        "Restart to finish installing updates",
        "Updates are downloaded but don't protect you until the PC restarts.",
        (
            "Save your work and close your programs.",
            "Click Start, then Power, then Restart.",
            "Wait for Windows to finish installing before you log back in.",
        ),
        10, False,
    ),
    Fix(
        "plan-windows-11", "patch",
        "Plan your move to a supported Windows version",
        "Old Windows versions stop getting security fixes, so new attacks stay open.",
        (
            "Click Start, open Settings and go to Windows Update.",
            "If an upgrade to Windows 11 is offered, back up your files first, then install it.",
            "If this PC can't run Windows 11, ask your IT helper about Extended Security Updates or a new PC.",
        ),
        60, True,
    ),
    # --- software ---
    Fix(
        "update-outdated-apps", "software",
        "Update or remove outdated programs",
        "Old versions of everyday programs have known holes that attackers use.",
        (
            "Open each outdated program listed in the report.",
            "Look for Help, then About or Check for updates, and install the update.",
            "If a program is no longer supported, uninstall it from Settings > Apps.",
        ),
        20, False,
    ),
    # Not in the s2.9 table: attached by S7 so an amber finding always has a fix (D11).
    Fix(
        "rescan-installed-apps", "software",
        "Run the scan again to check your programs",
        "We couldn't see which programs are installed, so outdated ones may have been missed.",
        (
            "Restart the PC.",
            "Run the scan again.",
            "If the programs list is still empty, ask your IT helper to check the PC.",
        ),
        5, False,
    ),
    # --- recovery ---
    Fix(
        "enable-winre", "recovery",
        "Turn on the Windows recovery tools",
        "If Windows won't start, the recovery tools let you repair it without losing files.",
        (
            "Ask your IT helper to turn on the Windows Recovery Environment.",
            "They can do it by running one command as administrator: reagentc /enable.",
            "Ask them to confirm it shows as Enabled afterwards.",
        ),
        10, True,
    ),
    Fix(
        "turn-on-system-restore", "recovery",
        "Turn on System Restore",
        "System Restore can undo a bad change to Windows in a few minutes.",
        (
            "Click Start, type Create a restore point and open it.",
            "Select the C: drive and click Configure.",
            "Choose Turn on system protection and set Max Usage to about 5%.",
            "Click OK.",
        ),
        5, True,
    ),
    Fix(
        "create-restore-point", "recovery",
        "Create a fresh restore point",
        "Your newest restore point is missing or old, so there is nothing recent to roll back to.",
        (
            "Click Start, type Create a restore point and open it.",
            "Click Create, type today's date as the name and click Create again.",
            "Wait for the success message.",
        ),
        5, True,
    ),
)

CATALOGUE: dict[str, Fix] = {f.id: f for f in _FIXES}


def _rank_key(fix_id: str, severity: Status) -> tuple:
    fix = CATALOGUE[fix_id]
    return (
        _SEVERITY_RANK[severity],
        FIX_CATEGORY_RANK[fix.category],
        fix.effort_minutes,
        fix.id,
    )


def resolve(
    fix_ids_with_severity: Iterable[tuple[str, Status | str]],
    steps: Mapping[str, Sequence[str]] | None = None,
) -> tuple[list[dict], list[str]]:
    """Merge (fix_id, severity) pairs into ranked fixes[] and top_fixes[] (s0.8).

    steps maps a fix id to run-specific steps (CategoryResult.fix_steps) that
    replace the catalogue steps; ids not in it keep the catalogue text.

    Duplicates collapse to one entry whose severity is the worst attaching rule.
    fixes[] is returned in rank order; top_fixes is its first <= 3 ids.
    All green (no pairs) -> ([], []).
    """
    merged: dict[str, Status] = {}
    for fix_id, severity in fix_ids_with_severity:
        if fix_id not in CATALOGUE:
            raise KeyError(f"unknown fix id {fix_id!r}")
        sev = Status(severity)
        if sev not in _SEVERITY_RANK:
            raise ValueError(f"fix {fix_id!r}: severity must be red or amber, got {sev}")
        current = merged.get(fix_id)
        if current is None or _SEVERITY_RANK[sev] < _SEVERITY_RANK[current]:
            merged[fix_id] = sev

    ranked = sorted(merged, key=lambda f: _rank_key(f, merged[f]))
    steps = steps or {}
    fixes = [CATALOGUE[f].to_dict(merged[f], steps.get(f)) for f in ranked]
    return fixes, ranked[:MAX_TOP]
