"""Verifiable evidence bundle: evidence.json and --verify (s2.14).

Trust comes from deterministic recomputation, not a signing key: the verifier
re-runs the published rules on the embedded scan and compares the result with
the embedded report (s2.14.2).
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from antigravity_engine import __version__
from antigravity_engine.clock import fmt_date, now
from antigravity_engine.baseline import Baseline, BaselineError, load_baseline
from antigravity_engine.contract import ScanModel
from antigravity_engine.parser import ContractError, load_json, parse_dict, validate_schema

EVIDENCE_VERSION = "1.0.0"
SUPPORTED_MAJOR = "1"
MAX_BYTES = 4 * 1024 * 1024
IGNORED_REPORT_KEYS = frozenset({"generated_at"})

VERIFIED = 0
TAMPERED = 5
CANNOT_VERIFY = 6

NOT_EVIDENCE = "CANNOT_VERIFY: not an Antigravity evidence file"

EVIDENCE_SCHEMA = "evidence.schema.json"

Assess = Callable[[ScanModel, Baseline], dict]


@dataclass(frozen=True)
class VerifyResult:
    code: int
    message: str


def canonical_hash(obj: Any) -> str:
    """s2.14.1 canonical hash rule; the one place it is computed."""
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def baseline_hash(path: Path) -> str:
    """Canonical hash of the parsed baseline (D19), so CRLF checkouts hash the same."""
    return canonical_hash(load_json(path))


def evidence_id(report_sha256: str) -> str:
    return "AG-" + report_sha256.removeprefix("sha256:")[:12]


def build_bundle(
    scan: dict,
    report: dict,
    baseline_sha256: str,
    created_at: datetime | None = None,
) -> dict:
    """scan is the scan.json object exactly as read; report is report.json."""
    report_sha = canonical_hash(report)
    return {
        "evidence_version": EVIDENCE_VERSION,
        "run_id": report["run_id"],
        "created_at": (created_at or datetime.now(UTC)).astimezone(UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "engine_version": report["engine_version"],
        "baseline_version": report["baseline_version"],
        "baseline_sha256": baseline_sha256,
        "scan": scan,
        "report": report,
        "scan_sha256": canonical_hash(scan),
        "report_sha256": report_sha,
        "evidence_id": evidence_id(report_sha),
    }


def _major_minor(version: str) -> tuple[str, ...]:
    return tuple(version.split(".")[:2])


def first_difference(a: Any, b: Any, path: str = "$") -> str | None:
    """JSON path of the first place a and b differ, or None if equal."""
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                return f"{path}.{key}"
            found = first_difference(a[key], b[key], f"{path}.{key}")
            if found:
                return found
        return None
    if isinstance(a, list) and isinstance(b, list):
        for i, (x, y) in enumerate(zip(a, b)):
            found = first_difference(x, y, f"{path}[{i}]")
            if found:
                return found
        return None if len(a) == len(b) else f"{path}[{min(len(a), len(b))}]"
    if type(a) is not type(b) or a != b:
        return path
    return None


def _not_checked(report: dict) -> int:
    return sum(
        row.get("status") in ("unavailable", "failed")
        for c in report["categories"]
        for row in c["evidence"]
    )


def _load(path: Path) -> dict | None:
    """Step 1: size, JSON, evidence_version major 1, shared/contract/evidence.schema.json."""
    try:
        if path.stat().st_size > MAX_BYTES:
            return None
        data = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    version = data.get("evidence_version")
    if not isinstance(version, str) or version.split(".")[0] != SUPPORTED_MAJOR:
        return None
    try:
        validate_schema(data, EVIDENCE_SCHEMA)
    except ContractError:
        return None
    return data


def _comparable(report: dict) -> dict:
    return {k: v for k, v in report.items() if k not in IGNORED_REPORT_KEYS}


def verify(path: Path, baseline_path: Path, assess: Assess) -> VerifyResult:
    """s2.14.2 steps 1-5, first failure wins. assess is the CLI's scan -> report."""
    bundle = _load(path)
    if bundle is None:
        return VerifyResult(CANNOT_VERIFY, NOT_EVIDENCE)

    # Step 2: lazy edits.
    if canonical_hash(bundle["scan"]) != bundle["scan_sha256"]:
        return VerifyResult(TAMPERED, "TAMPERED: scan edited")
    if canonical_hash(bundle["report"]) != bundle["report_sha256"]:
        return VerifyResult(TAMPERED, "TAMPERED: report edited")
    if evidence_id(bundle["report_sha256"]) != bundle["evidence_id"]:
        return VerifyResult(TAMPERED, "TAMPERED: evidence ID edited")

    # Step 3: same rules as the producer.
    wanted = ".".join(_major_minor(bundle["engine_version"]))
    other = VerifyResult(
        CANNOT_VERIFY, f"CANNOT_VERIFY: different engine/baseline - use verifier v{wanted}"
    )
    if _major_minor(bundle["engine_version"]) != _major_minor(__version__):
        return other
    try:
        if baseline_hash(baseline_path) != bundle["baseline_sha256"]:
            return other
        baseline = load_baseline(baseline_path)
    except (BaselineError, ContractError, OSError):
        return other

    # Step 4: recompute and compare, ignoring only generated_at.
    report = bundle["report"]
    try:
        scan = parse_dict(bundle["scan"])
    except ContractError as e:
        where = e.path or "$"
        return VerifyResult(
            TAMPERED, f"TAMPERED: report does not match the scan (first difference: $.scan{where[1:]})"
        )
    expected = assess(scan, baseline)
    if _major_minor(str(report.get("engine_version", ""))) == _major_minor(__version__):
        # A patch release must not change output; let it verify its own minor line.
        expected["engine_version"] = report["engine_version"]
    diff = first_difference(_comparable(report), _comparable(expected))
    if diff is not None:
        return VerifyResult(
            TAMPERED, f"TAMPERED: report does not match the scan (first difference: {diff})"
        )

    # Step 5.
    return VerifyResult(
        VERIFIED,
        f"VERIFIED - report matches the measured scan. Evidence ID {bundle['evidence_id']}  "
        f"Collected {fmt_date(now(scan))}. Not checked: {_not_checked(report)} items",
    )
