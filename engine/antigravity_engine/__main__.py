"""Command line entry point (s2.11): python -m antigravity_engine --in scan.json --out DIR

Exit codes:
  0  success (individual categories may still be failed)
  1  anything else (crash before report.json is written)
  2  invalid input (s2.4); report.json written with all five categories failed
  3  rendering failed; report.json written, report.html / action-plan.pdf may be missing
"""

import argparse
import json
import sys
import traceback
from collections.abc import Callable, Sequence
from pathlib import Path

from antigravity_engine import __version__
from antigravity_engine.aggregator import overall
from antigravity_engine.baseline import Baseline, BaselineError, load_baseline
from antigravity_engine.contract import ScanModel
from antigravity_engine.parser import ContractError, parse_path
from antigravity_engine.paths import default_baseline_path
from antigravity_engine.report_model import REPORT_SCHEMA_VERSION, build_error_report, build_report
from antigravity_engine.risk import summary
from antigravity_engine.scoring import backup, fixes, patch, protection, recovery, software
from antigravity_engine.scoring.result import CATEGORY_ORDER, CategoryResult

EXIT_OK = 0
EXIT_CRASH = 1
EXIT_BAD_INPUT = 2
EXIT_RENDER = 3

REPORT_JSON = "report.json"
REPORT_HTML = "report.html"
ACTION_PLAN_PDF = "action-plan.pdf"

INTERNAL_ERROR = "Internal error while checking."
UNKNOWN_BASELINE = "unknown"

Scorer = Callable[[ScanModel, Baseline], CategoryResult]
SCORERS: dict[str, Scorer] = {
    "backup": backup.score,
    "patch": patch.score,
    "software": software.score,
    "protection": protection.score,
    "recovery": recovery.score,
}


def version_line() -> str:
    return f"antigravity-engine {__version__} contract {REPORT_SCHEMA_VERSION}"


def score_all(scan: ScanModel, baseline: Baseline) -> list[CategoryResult]:
    """Score in fixed order; a scorer that raises fails only its own category (s2.7)."""
    results = []
    for category in CATEGORY_ORDER:
        try:
            results.append(SCORERS[category](scan, baseline))
        except Exception:
            print(f"antigravity-engine: internal error scoring {category}:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            results.append(CategoryResult.failed(category, None, explanation=INTERNAL_ERROR))
    return results


def assess(scan: ScanModel, baseline: Baseline) -> dict:
    """Score, aggregate, summarise and resolve fixes into a validated report.json dict."""
    results = score_all(scan, baseline)
    pairs = [pair for r in results for pair in r.fix_pairs()]
    steps = {fix_id: s for r in results for fix_id, s in r.fix_steps.items()}
    resolved, top = fixes.resolve(pairs, steps)
    return build_report(
        scan,
        results,
        resolved,
        top,
        overall(results),
        summary(results, resolved),
        engine_version=__version__,
        baseline_version=baseline.baseline_version,
    )


def write_json(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # ASCII on disk (D6): non-ASCII text such as the em dash is written as \uXXXX.
    text = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def _baseline_version(path: Path) -> str:
    """Best effort for the error report: bad input must still produce report.json."""
    try:
        return load_baseline(path).baseline_version
    except (BaselineError, OSError):
        return UNKNOWN_BASELINE


def _render(report: dict, out_dir: Path) -> None:
    # Imported here so a broken renderer dependency is a render failure (exit 3),
    # not a crash before report.json exists.
    from antigravity_engine.render import html, pdf

    html.render(report, out_dir / REPORT_HTML)
    pdf.render(report, out_dir / ACTION_PLAN_PDF)


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="antigravity-engine", description="Score a scan.json into report.json."
    )
    ap.add_argument("--in", dest="in_path", metavar="PATH", help="scan.json to read")
    ap.add_argument("--out", dest="out_dir", metavar="DIR", help="folder for the report files")
    ap.add_argument("--baseline", metavar="PATH", help="software-baseline.json")
    ap.add_argument("--json-only", action="store_true", help="skip report.html and action-plan.pdf")
    ap.add_argument("--version", action="store_true", help="print versions and exit")
    return ap


def main(argv: Sequence[str] | None = None) -> int:
    ap = _parser()
    args = ap.parse_args(argv)
    if args.version:
        print(version_line())
        return EXIT_OK
    if not args.in_path or not args.out_dir:
        ap.error("--in and --out are required")

    out_dir = Path(args.out_dir)
    report_path = out_dir / REPORT_JSON
    baseline_path = Path(args.baseline) if args.baseline else default_baseline_path()

    try:
        scan = parse_path(Path(args.in_path))
    except ContractError as e:
        report = build_error_report(str(e), __version__, _baseline_version(baseline_path))
        write_json(report, report_path)
        print(f"antigravity-engine: invalid input: {e}", file=sys.stderr)
        return EXIT_BAD_INPUT

    try:
        baseline = load_baseline(baseline_path)
    except (BaselineError, OSError) as e:
        print(f"antigravity-engine: cannot load baseline: {e}", file=sys.stderr)
        return EXIT_CRASH

    report = assess(scan, baseline)
    write_json(report, report_path)

    if args.json_only:
        return EXIT_OK
    try:
        _render(report, out_dir)
    except Exception:
        print("antigravity-engine: rendering failed:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return EXIT_RENDER
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
