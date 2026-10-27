"""Ransomware protections scorer (s2.5.4).

Four sub-checks (Defender, BitLocker, CFA, ASR), each one evidence row with
its own status; each sub-check table is first match wins. The category status
is the worst rated row. A sub-check whose section is unavailable/failed, or
whose deciding field is null, is a grey row and is skipped for rating.

Defender counts as "not your antivirus" when third_party_av is set (s3.6:
never penalised) or when Defender's antivirus or real-time protection is off.
CFA and ASR only work with Defender as the active antivirus, so in that case
their rows carry a note and are excluded from rating (D13).

BitLocker "still encrypting" is amber, so it attaches finish-bitlocker-encryption
to keep RPT-03 (D12). If no row can be rated the category is unavailable (or
failed when every section failed) with the grey rows as evidence (D14).
"""

from dataclasses import dataclass

from antigravity_engine.baseline import Baseline
from antigravity_engine.contract import Section, ScanModel
from antigravity_engine.contract import Status as SectionStatus
from antigravity_engine.scoring.result import (
    NEEDS_ADMIN,
    CategoryResult,
    EvidenceRow,
    Status,
    plain_reason,
    worst,
)

CATEGORY = "protection"
SIGNATURE_RED_DAYS = 7  # > 7 days is red
SIGNATURE_AMBER_DAYS = 4  # 4-7 days is amber
ENCRYPTION_DONE_PCT = 100

DEFENDER = "Antivirus"
BITLOCKER = "Drive encryption"
CFA = "Controlled folder access"
ASR = "Anti-ransomware rules"

DEFENDER_ONLY = "Only works when Microsoft Defender is your antivirus"
_ADMIN_HINT = " Run as administrator for a full check."
_SEVERITY_ORDER = {Status.RED: 0, Status.AMBER: 1}


@dataclass(frozen=True)
class _Check:
    row: EvidenceRow
    fix: str | None = None
    sentence: str | None = None  # explanation when this row is the worst finding

    @property
    def finding(self) -> bool:
        return self.row.status in (Status.RED, Status.AMBER)


def _usable(section: Section) -> bool:
    return section.status == SectionStatus.OK


def _grey_section(label: str, section: Section) -> _Check:
    return _Check(EvidenceRow(label, plain_reason(section.error), Status.UNAVAILABLE))


def _grey_null(label: str, is_admin: bool) -> _Check:
    """Grey row for a null field in an ok section."""
    return _Check(EvidenceRow(label, "Not checked" if is_admin else NEEDS_ADMIN, Status.UNAVAILABLE))


def _defender_not_primary(scan: ScanModel) -> bool:
    d = scan.protection.defender
    if not _usable(d):
        return False
    return d.third_party_av is not None or d.antivirus_enabled is False or d.realtime_enabled is False


def _defender(scan: ScanModel) -> _Check:
    d = scan.protection.defender
    if not _usable(d):
        return _grey_section(DEFENDER, d)
    # s3.6: a third-party antivirus puts Defender in passive mode; not penalised.
    if d.third_party_av is not None:
        return _Check(EvidenceRow(DEFENDER, f"Protected by {d.third_party_av}", Status.GREEN))
    if d.antivirus_enabled is False:
        return _Check(
            EvidenceRow(DEFENDER, "Microsoft Defender is off and no other antivirus was found",
                        Status.RED),
            "enable-defender",
            "Microsoft Defender is off and no other antivirus was found, so ransomware can run "
            "unnoticed.",
        )
    if d.realtime_enabled is False:
        return _Check(
            EvidenceRow(DEFENDER, "Microsoft Defender real-time protection is off", Status.RED),
            "enable-defender",
            "Microsoft Defender's real-time protection is off, so new threats aren't blocked.",
        )
    age = d.signature_age_days
    if age is not None and age >= SIGNATURE_AMBER_DAYS:
        status = Status.RED if age > SIGNATURE_RED_DAYS else Status.AMBER
        return _Check(
            EvidenceRow(DEFENDER, f"Microsoft Defender on, virus list {age} days old", status),
            "update-defender-definitions",
            f"Microsoft Defender's virus list is {age} days old, so it can miss new ransomware.",
        )
    if d.tamper_protected is False:
        return _Check(
            EvidenceRow(DEFENDER, "Microsoft Defender on, Tamper Protection off", Status.AMBER),
            "enable-tamper-protection",
            "Tamper Protection is off, so ransomware could switch Microsoft Defender off.",
        )
    if d.antivirus_enabled is None or d.realtime_enabled is None:
        return _grey_null(DEFENDER, scan.host.is_admin)
    return _Check(EvidenceRow(DEFENDER, "Microsoft Defender on and up to date", Status.GREEN))


def _bitlocker(scan: ScanModel) -> _Check:
    b = scan.protection.bitlocker
    if b.status == SectionStatus.UNAVAILABLE and scan.host.os_edition.startswith("Core"):
        return _Check(
            EvidenceRow(BITLOCKER, "BitLocker not available on Windows Home", Status.AMBER),
            "encrypt-device-home",
            "Windows Home has no BitLocker, so turn on Device encryption to protect files if the "
            "PC is stolen.",
        )
    if not _usable(b):
        return _grey_section(BITLOCKER, b)
    if b.os_volume_protection == "off":
        return _Check(
            EvidenceRow(BITLOCKER, "BitLocker is off", Status.RED),
            "turn-on-bitlocker",
            "The hard drive isn't encrypted, so anyone who steals the PC can read your files.",
        )
    if b.os_volume_protection is None:
        return _grey_null(BITLOCKER, scan.host.is_admin)
    pct = b.os_volume_encryption_pct
    if pct is not None and pct < ENCRYPTION_DONE_PCT:
        return _Check(
            EvidenceRow(BITLOCKER, f"BitLocker is still encrypting ({pct}% done)", Status.AMBER),
            "finish-bitlocker-encryption",
            "BitLocker is still encrypting the drive; leave the PC on until it finishes.",
        )
    return _Check(EvidenceRow(BITLOCKER, "BitLocker is on", Status.GREEN))


def _cfa(scan: ScanModel, excluded: bool) -> _Check:
    c = scan.protection.cfa
    if not _usable(c):
        return _grey_section(CFA, c)
    if excluded:
        return _Check(EvidenceRow(CFA, DEFENDER_ONLY))
    if c.mode == "enabled":
        return _Check(EvidenceRow(CFA, "On", Status.GREEN))
    if c.mode == "audit":
        return _Check(
            EvidenceRow(CFA, "Audit only, not blocking", Status.AMBER),
            "enable-cfa",
            "Controlled folder access only logs changes, so it won't stop ransomware locking your "
            "files.",
        )
    if c.mode == "disabled":
        return _Check(
            EvidenceRow(CFA, "Off", Status.AMBER),
            "enable-cfa",
            "Controlled folder access is off, so any program can change files in your main "
            "folders.",
        )
    return _grey_null(CFA, scan.host.is_admin)


def _asr(scan: ScanModel, ctx: Baseline, excluded: bool) -> _Check:
    a = scan.protection.asr
    if not _usable(a):
        return _grey_section(ASR, a)
    if excluded:
        return _Check(EvidenceRow(ASR, DEFENDER_ONLY))
    on = {r.id.lower() for r in a.rules if r.action in ("block", "warn")}
    total = len(ctx.asr_recommended)
    count = len(ctx.asr_recommended & on)
    value = f"{count} of {total} recommended rules on"
    if count == total:
        return _Check(EvidenceRow(ASR, value, Status.GREEN))
    if count == 0:
        sentence = "None of Microsoft Defender's recommended anti-ransomware rules are switched on."
    else:
        sentence = (
            f"Only {count} of {total} of Microsoft Defender's recommended anti-ransomware rules "
            "are switched on."
        )
    return _Check(EvidenceRow(ASR, value, Status.AMBER), "enable-asr-rules", sentence)


def _explanation(findings: list[_Check]) -> str:
    first = findings[0].sentence
    others = len(findings) - 1
    if others == 0:
        return first
    noun = "protection also needs" if others == 1 else "protections also need"
    return f"{first} {others} other {noun} attention."


def score(scan: ScanModel, ctx: Baseline) -> CategoryResult:
    excluded = _defender_not_primary(scan)
    checks = [_defender(scan), _bitlocker(scan), _cfa(scan, excluded), _asr(scan, ctx, excluded)]
    rows = [c.row for c in checks]
    status = worst(row.status for row in rows if row.status is not None)

    if status is None:
        p = scan.protection
        sections = (p.defender, p.bitlocker, p.cfa, p.asr)
        unavailable = [s for s in sections if s.status == SectionStatus.UNAVAILABLE]
        if all(s.status == SectionStatus.FAILED for s in sections):
            return CategoryResult.failed(CATEGORY, sections[0].error)
        reason = unavailable[0].error if unavailable else None
        return CategoryResult.unavailable(CATEGORY, reason, rows)

    if status == Status.GREEN:
        grey = any(row.status == Status.UNAVAILABLE for row in rows)
        if not grey and not excluded:
            explanation = (
                "Antivirus, drive encryption and Microsoft Defender's anti-ransomware protections "
                "are all on."
            )
        else:
            explanation = "The protections we could check are all on."
            if grey and not scan.host.is_admin:
                explanation += _ADMIN_HINT
        return CategoryResult.rated(CATEGORY, status, explanation, rows)

    # Worst finding first; ties keep sub-check order (sort is stable).
    findings = sorted((c for c in checks if c.finding),
                      key=lambda c: _SEVERITY_ORDER[c.row.status])
    fix_ids = [c.fix for c in findings]
    # A fix ranks by the row that attached it, not the category (D1).
    fix_severity = {c.fix: c.row.status for c in findings if c.row.status != status}
    return CategoryResult.rated(
        CATEGORY, status, _explanation(findings), rows, fix_ids, fix_severity=fix_severity,
    )
