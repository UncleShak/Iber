"""report.html from the report model only (s2.3 row 9, s4.10).

Minimal version wired in by the CLI (phase 7); phase 8 builds out the
template. Autoescape is always on: app names and errors come from the scan.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
TEMPLATE = "report.html.j2"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=True,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def render_string(report: dict) -> str:
    fixes = {f["id"]: f for f in report["fixes"]}
    return _env().get_template(TEMPLATE).render(report=report, fixes=fixes)


def render(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_string(report), encoding="utf-8", newline="\n")
