"""Assemble report.json (s0.8, Appendix A.2) and validate it before returning.

Renderers and the UI read only this dict (s2.3 row 8), never the scan.
"""

import re
from collections.abc import Iterable
from datetime import UTC, datetime

from antigravity_engine.aggregator import order
from antigravity_engine.contract import ScanModel
from antigravity_engine.parser import ContractError, validate_schema
from antigravity_engine.risk import MAX_SUMMARY
from antigravity_engine.scoring.result import CATEGORY_ORDER, RATED, CategoryResult, Status

REPORT_SCHEMA_VERSION = "1.0.0"
REPORT_SCHEMA = "report.schema.json"
_RUN_ID = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z_[0-9a-f]{4}$")
CONTRACT_ERROR_EXPLANATION = "This check couldn't run because the scan results couldn't be read."


class ReportError(Exception):
    """The engine built a report that breaks its own contract (an engine bug)."""


def _timestamp(generated_at: datetime | None) -> datetime:
    return (generated_at or datetime.now(UTC)).astimezone(UTC)


def _finish(report: dict) -> dict:
    try:
        validate_schema(report, REPORT_SCHEMA)
    except ContractError as e:
        raise ReportError(f"report.json failed schema validation: {e}") from e
    return report


def build_report(
    scan: ScanModel,
    results: Iterable[CategoryResult],
    fixes: list[dict],
    top_fixes: list[str],
    overall: Status,
    summary: str,
    engine_version: str,
    baseline_version: str,
    generated_at: datetime | None = None,
) -> dict:
    ordered = order(results)

    fix_ids = [f["id"] for f in fixes]
    referenced = {fid for r in ordered for fid in r.fix_ids}
    if set(fix_ids) != referenced:
        raise ReportError("fixes[] must hold exactly the fixes referenced by categories")
    if not set(top_fixes) <= set(fix_ids):
        raise ReportError("top_fixes must be a subset of fixes[]")
    if Status(overall) not in RATED:
        raise ReportError(f"overall must be red, amber or green, got {overall}")

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": scan.run_id,
        "generated_at": _timestamp(generated_at).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine_version": engine_version,
        "baseline_version": baseline_version,
        "overall": str(overall),
        "summary": summary,
        "categories": [r.to_dict() for r in ordered],
        "fixes": fixes,
        "top_fixes": list(top_fixes),
        "scan": {
            "is_admin": scan.host.is_admin,
            "duration_ms": scan.duration_ms,
            "os_caption": scan.host.os_caption,
        },
    }
    return _finish(report)


def build_error_report(
    error: str,
    engine_version: str,
    baseline_version: str,
    run_id: str | None = None,
    generated_at: datetime | None = None,
) -> dict:
    """Report written by the CLI on ContractError (s2.4 step 4): all five failed."""
    ts = _timestamp(generated_at)
    if not (isinstance(run_id, str) and _RUN_ID.match(run_id)):
        run_id = ts.strftime("%Y-%m-%dT%H-%M-%SZ") + "_0000"

    summary = f"We couldn't read the scan results: {error}" if error else "We couldn't read the scan results."
    if len(summary) > MAX_SUMMARY:
        summary = summary[: MAX_SUMMARY - 3] + "..."

    categories = [
        CategoryResult.failed(c, error, explanation=CONTRACT_ERROR_EXPLANATION).to_dict()
        for c in CATEGORY_ORDER
    ]
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine_version": engine_version,
        "baseline_version": baseline_version,
        "overall": str(Status.AMBER),
        "summary": summary,
        "categories": categories,
        "fixes": [],
        "top_fixes": [],
        "scan": {"is_admin": False, "duration_ms": 0, "os_caption": "Unknown"},
    }
    return _finish(report)
