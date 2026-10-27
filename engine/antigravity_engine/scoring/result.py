"""Scorer output types (s2.3 row 4, s0.8, s0.9, s2.7).

A rated CategoryResult (red/amber/green) is built with CategoryResult.rated()
or the constructor. "unavailable" and "failed" can ONLY be built through
CategoryResult.unavailable() / .failed(); the constructor rejects them, so a
RAG comparison can never produce an unrated status by accident (s2.7 rule 1).
"""

import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum


class Status(StrEnum):
    RED = "red"
    AMBER = "amber"
    GREEN = "green"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


# The single set used everywhere to decide what counts toward overall (s2.7 rule 2).
RATED = frozenset({Status.RED, Status.AMBER, Status.GREEN})

# Fixed report order (s0.8) and display titles (s2.5 headings).
CATEGORY_ORDER = ("backup", "patch", "software", "protection", "recovery")
TITLES = {
    "backup": "Backup evidence",
    "patch": "Patch status",
    "software": "Outdated software",
    "protection": "Ransomware protections",
    "recovery": "Recovery readiness",
}

_SEVERITY_RANK = {Status.GREEN: 0, Status.AMBER: 1, Status.RED: 2}
MAX_EXPLANATION = 200
MAX_EVIDENCE = 8
# report.schema.json fixes[].steps limits.
MAX_STEPS = 5
MAX_STEP_LEN = 160

# Only the factory classmethods hold this; passing it is the one way past the guard.
_UNRATED_TOKEN = object()


def worst(statuses) -> Status | None:
    """Worst of the rated statuses given; unrated ones are ignored. None if none rated."""
    rated = [Status(s) for s in statuses if s in RATED]
    if not rated:
        return None
    return max(rated, key=_SEVERITY_RANK.__getitem__)


class ClippedWarning(UserWarning):
    """Scan-driven text or rows went past a report.schema.json limit and were cut (D3).

    Raised as an error in the test suite (conftest.py), so clipping stays a
    runtime safety net and never becomes normal output.
    """


def _clip(text: str, limit: int = MAX_EXPLANATION) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


# Evidence value for a field left null because the scan wasn't elevated (s0.8, s2.5.1).
NEEDS_ADMIN = "Not checked \u2014 needs admin"

# Raw collector error text (s3.4) -> (evidence value, category explanation).
# Matched case-insensitively by substring, first match wins.
_ERROR_TABLE = (
    (
        "administrator",
        NEEDS_ADMIN,
        "Not checked because it needs administrator rights. Run as administrator for a full check.",
    ),
    (
        "windows home",
        "Not available on Windows Home",
        "Windows Home doesn't include this feature, so it couldn't be checked.",
    ),
    (
        "timed out",
        "Check timed out",
        "This check took too long and was stopped.",
    ),
    (
        "timeout",
        "Check timed out",
        "This check took too long and was stopped.",
    ),
    (
        "not available",
        "Not available on this PC",
        "This feature isn't available on this PC, so it couldn't be checked.",
    ),
)
_DEFAULT_UNAVAILABLE = ("Not checked", "This couldn't be checked on this PC.")


def plain_reason(error: str | None) -> str:
    """Short evidence-row text for a collector error, e.g. "Not checked \u2014 needs admin"."""
    return _lookup(error)[0]


def plain_explanation(error: str | None) -> str:
    """One-sentence category explanation for a collector "unavailable" error."""
    return _lookup(error)[1]


def _lookup(error: str | None) -> tuple[str, str]:
    lowered = (error or "").lower()
    for needle, short, long in _ERROR_TABLE:
        if needle in lowered:
            return short, long
    return _DEFAULT_UNAVAILABLE


def failure_explanation(error: str | None) -> str:
    """s2.7: "This check couldn't run on this PC." plus the short error, <= 200 chars."""
    base = "This check couldn't run on this PC."
    detail = (error or "").strip()
    return _clip(f"{base} ({detail})") if detail else base


@dataclass(frozen=True)
class EvidenceRow:
    label: str
    value: str
    status: Status | None = None

    def __post_init__(self) -> None:
        if self.status is not None:
            object.__setattr__(self, "status", Status(self.status))

    def to_dict(self) -> dict:
        d = {"label": self.label, "value": self.value}
        if self.status is not None:
            d["status"] = str(self.status)
        return d


@dataclass(frozen=True)
class CategoryResult:
    id: str
    title: str
    status: Status
    explanation: str
    evidence: tuple[EvidenceRow, ...] = ()
    fix_ids: tuple[str, ...] = ()
    # Per-fix severity when it differs from the category status (e.g. an amber
    # CFA fix inside a red protection category). Missing ids use self.status.
    fix_severity: Mapping[str, Status] = field(default_factory=dict)
    # Run-specific steps replacing a catalogue fix's steps (e.g. naming the
    # outdated apps). Internal, like fix_severity; never written to report.json.
    fix_steps: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    _token: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        status = Status(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "fix_ids", tuple(dict.fromkeys(self.fix_ids)))
        object.__setattr__(
            self, "fix_severity", {k: Status(v) for k, v in self.fix_severity.items()}
        )
        object.__setattr__(self, "fix_steps", {k: tuple(v) for k, v in self.fix_steps.items()})
        self._clip_scan_driven()

        if self.id not in TITLES:
            raise ValueError(f"unknown category id {self.id!r}")
        if status not in RATED and self._token is not _UNRATED_TOKEN:
            raise ValueError(
                f"{status} results must be built with CategoryResult.{status}(), not directly"
            )
        if not self.explanation:
            raise ValueError(f"{self.id}: explanation must not be empty")
        if status not in (Status.RED, Status.AMBER) and self.fix_ids:
            raise ValueError(f"{self.id}: a {status} category cannot attach fixes")
        for fix_id, sev in self.fix_severity.items():
            if fix_id not in self.fix_ids:
                raise ValueError(f"{self.id}: severity given for unattached fix {fix_id!r}")
            if sev not in (Status.RED, Status.AMBER):
                raise ValueError(f"{self.id}: fix severity must be red or amber, got {sev}")
            if _SEVERITY_RANK[sev] > _SEVERITY_RANK[status]:
                raise ValueError(f"{self.id}: fix {fix_id!r} is worse than its category")
        for fix_id, steps in self.fix_steps.items():
            if fix_id not in self.fix_ids:
                raise ValueError(f"{self.id}: steps given for unattached fix {fix_id!r}")
            if not 1 <= len(steps) <= MAX_STEPS:
                raise ValueError(f"{self.id}: fix {fix_id!r} needs 1..{MAX_STEPS} steps")
            if any(not step for step in steps):
                raise ValueError(f"{self.id}: fix {fix_id!r} has an empty step")

    def _clip_scan_driven(self) -> None:
        """Cut limits that scan data can push past, instead of failing the category (D3).

        Explanation length, evidence row count and step length depend on day
        counts, program names and how many apps are installed. A real finding
        with a trimmed sentence beats "Check failed". Logic bugs (fixes on a
        green result, bad severities) still raise.
        """
        if len(self.explanation) > MAX_EXPLANATION:
            warnings.warn(
                f"{self.id}: explanation clipped from {len(self.explanation)} chars",
                ClippedWarning, stacklevel=4,
            )
            object.__setattr__(self, "explanation", _clip(self.explanation))
        if len(self.evidence) > MAX_EVIDENCE:
            warnings.warn(
                f"{self.id}: evidence cut from {len(self.evidence)} rows to {MAX_EVIDENCE}",
                ClippedWarning, stacklevel=4,
            )
            object.__setattr__(self, "evidence", self.evidence[:MAX_EVIDENCE])
        for fix_id, steps in self.fix_steps.items():
            if any(len(step) > MAX_STEP_LEN for step in steps):
                warnings.warn(
                    f"{self.id}: steps for {fix_id!r} clipped to {MAX_STEP_LEN} chars",
                    ClippedWarning, stacklevel=4,
                )
                self.fix_steps[fix_id] = tuple(_clip(step, MAX_STEP_LEN) for step in steps)

    @classmethod
    def rated(
        cls,
        category_id: str,
        status: Status | str,
        explanation: str,
        evidence: Sequence[EvidenceRow] = (),
        fix_ids: Sequence[str] = (),
        fix_severity: Mapping[str, Status] | None = None,
        fix_steps: Mapping[str, Sequence[str]] | None = None,
    ) -> "CategoryResult":
        return cls(
            id=category_id,
            title=TITLES.get(category_id, category_id),
            status=Status(status),
            explanation=explanation,
            evidence=tuple(evidence),
            fix_ids=tuple(fix_ids),
            fix_severity=dict(fix_severity or {}),
            fix_steps=dict(fix_steps or {}),
        )

    @classmethod
    def unavailable(
        cls, category_id: str, reason: str | None, evidence: Sequence[EvidenceRow] = ()
    ) -> "CategoryResult":
        return cls(
            id=category_id,
            title=TITLES.get(category_id, category_id),
            status=Status.UNAVAILABLE,
            explanation=plain_explanation(reason),
            evidence=tuple(evidence),
            _token=_UNRATED_TOKEN,
        )

    @classmethod
    def failed(
        cls, category_id: str, reason: str | None, explanation: str | None = None
    ) -> "CategoryResult":
        return cls(
            id=category_id,
            title=TITLES.get(category_id, category_id),
            status=Status.FAILED,
            explanation=_clip(explanation) if explanation else failure_explanation(reason),
            _token=_UNRATED_TOKEN,
        )

    @property
    def is_rated(self) -> bool:
        return self.status in RATED

    def fix_pairs(self) -> list[tuple[str, Status]]:
        """(fix_id, severity) for every attached fix, for scoring.fixes.resolve()."""
        return [(f, self.fix_severity.get(f, self.status)) for f in self.fix_ids]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": TITLES[self.id],
            "status": str(self.status),
            "explanation": self.explanation,
            "evidence": [row.to_dict() for row in self.evidence],
            "fix_ids": list(self.fix_ids),
        }
