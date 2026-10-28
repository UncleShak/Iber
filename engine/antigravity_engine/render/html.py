"""report.html from the report model only (s2.3 row 9, s4.10).

One self-contained file: inline CSS, no script, no external fonts, images or
links, so it opens offline from a file path. Autoescape is always on: app
names, versions and errors come from the scan (s4.10, scan.xss.json).

Standalone: python -m antigravity_engine.render.html report.json report.html
"""

import json
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from antigravity_engine.parser import validate_schema
from antigravity_engine.report_model import REPORT_SCHEMA

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
TEMPLATE = "report.html.j2"

PRODUCT = "Antigravity"
NOT_CHECKED = "Not checked"
COULDNT_READ = "Couldn't read:"
EM_DASH = "\u2014"

# s4.3 RAG tokens; the only hex values the template may use.
RAG_COLOURS = {
    "red": "#b42318",
    "red-bg": "#fef3f2",
    "amber": "#b54708",
    "amber-bg": "#fffaeb",
    "green": "#067647",
    "green-bg": "#ecfdf3",
    "grey": "#475467",
    "grey-bg": "#f2f4f7",
}

# s4.9.3 badge words, s4.10 Unicode symbols: icon + word + colour, never colour alone.
BADGES = {
    "red": {"symbol": "\u25cf", "word": "Act now", "tone": "red"},
    "amber": {"symbol": "\u25b2", "word": "Improve", "tone": "amber"},
    "green": {"symbol": "\u2713", "word": "Good", "tone": "green"},
    "unavailable": {"symbol": "\u2298", "word": "Not checked", "tone": "grey"},
    "failed": {"symbol": "\u2715", "word": "Check failed", "tone": "grey"},
}


def badge(status: str) -> dict:
    return BADGES[status]


def evidence_value(row: dict) -> str:
    """s4.10 evidence rules: grey rows always say why nothing was rated."""
    value = row["value"]
    status = row.get("status")
    if status == "unavailable" and not value.startswith(NOT_CHECKED):
        return f"{NOT_CHECKED} {EM_DASH} {value[:1].lower()}{value[1:]}"
    if status == "failed" and not value.startswith(COULDNT_READ):
        return f"{COULDNT_READ} {value}"
    return value


def human_date(stamp: str) -> str:
    """"2026-11-14T17:02:46Z" -> "14 Nov 2026" (s0.8 date style, no %-d on Windows)."""
    dt = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
    return f"{dt.day} {dt:%b %Y}"


def _env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=True,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals.update(badge=badge, rag=RAG_COLOURS, product=PRODUCT)
    env.filters.update(evidence_value=evidence_value, human_date=human_date)
    return env


def render_string(report: dict, org: str | None = None, evidence_id: str | None = None) -> str:
    """org is the licence organisation, known only to the app (D16); omitted if None.

    evidence_id ("AG-...", s2.14.1) is derived from report.json's hash, so it is
    passed in, never stored in the report; omitted if None.
    """
    fixes = {f["id"]: f for f in report["fixes"]}
    rank = {fix_id: n for n, fix_id in enumerate(report["top_fixes"], start=1)}
    titles = {c["id"]: c["title"] for c in report["categories"]}
    return _env().get_template(TEMPLATE).render(
        report=report, fixes=fixes, rank=rank, titles=titles, org=org, evidence_id=evidence_id
    )


def render(
    report: dict, path: Path, org: str | None = None, evidence_id: str | None = None
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_string(report, org, evidence_id), encoding="utf-8", newline="\n")


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: python -m antigravity_engine.render.html REPORT_JSON OUT_HTML",
              file=sys.stderr)
        return 2
    report = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    validate_schema(report, REPORT_SCHEMA)
    render(report, Path(args[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
