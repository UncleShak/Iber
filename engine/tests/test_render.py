"""report.html: s4.10 rules, autoescape, unavailable vs failed rows (phase 8)."""

import copy
import json
import re

import pytest

from antigravity_engine.__main__ import assess
from markupsafe import escape

from antigravity_engine.parser import ContractError, parse_path
from antigravity_engine.render import html
from conftest import FIXTURES

SCAN_FIXTURES = sorted(FIXTURES.glob("scan.*.json"))
XSS = FIXTURES / "scan.xss.json"
FOOTER_LOCAL = "Generated locally on this PC. Nothing was uploaded."
FOOTER_AUDIT = "This is a guidance check, not a full security audit."
ALL_NULL_RECOVERY = {
    "host": {"is_admin": False},
    "recovery": {
        "winre_enabled": None,
        "system_restore_enabled": None,
        "restore_point_count": None,
        "latest_restore_point": None,
    },
}


def _report(path, baseline) -> dict:
    return assess(parse_path(path), baseline)


def _section(page: str, category_id: str) -> str:
    start = page.index(f'<section class="category" id="{category_id}">')
    return page[start : page.index("</section>", start)]


def html_escape(text: str) -> str:
    return str(escape(text))


def _rows(section: str) -> list[str]:
    """Body rows only; the header row holds <th> cells."""
    return [r for r in re.findall(r"<tr>.*?</tr>", section, flags=re.S) if "<td" in r]


@pytest.fixture
def defender_off(baseline) -> dict:
    return _report(FIXTURES / "scan.defender-off.json", baseline)


# --- every fixture renders ---


@pytest.mark.parametrize("path", SCAN_FIXTURES, ids=lambda p: p.name)
def test_every_fixture_renders(path, baseline, tmp_path):
    report = _report(path, baseline)
    out = tmp_path / "report.html"
    html.render(report, out)
    page = out.read_text(encoding="utf-8")
    assert page.startswith("<!doctype html>")
    assert page.rstrip().endswith("</html>")
    for c in report["categories"]:
        assert f'id="{c["id"]}"' in page


# --- self-contained (s4.10 row 1) ---


@pytest.mark.parametrize("path", SCAN_FIXTURES, ids=lambda p: p.name)
def test_page_is_self_contained(path, baseline):
    page = html.render_string(_report(path, baseline)).lower()
    assert "<script" not in page
    for external in ("http://", "https://", "//cdn", "<link", "<img", "@import", "url(", "@font-face"):
        assert external not in page, external
    assert page.count("<style>") == 1


# --- autoescape (s4.10 row 2) ---


def test_environment_autoescapes():
    assert html._env().autoescape is True


def test_xss_fixture_renders_without_raw_script(baseline):
    page = html.render_string(_report(XSS, baseline))
    assert "<script>alert" not in page
    assert "<img" not in page


def test_xss_app_name_is_escaped_wherever_the_report_carries_it(baseline):
    # The xss app isn't on the watch list, so the engine only counts it; put the
    # fixture's own name into every scan-driven text field to prove escaping.
    name = json.loads(XSS.read_text(encoding="utf-8"))["software"]["installed"][0]["name"]
    report = copy.deepcopy(_report(FIXTURES / "scan.defender-off.json", baseline))
    software = next(c for c in report["categories"] if c["id"] == "software")
    software["evidence"][0]["label"] = name
    software["evidence"][0]["value"] = name
    report["fixes"][0]["steps"][0] = f"Update {name}"
    report["summary"] = name

    page = html.render_string(report, org=name)
    assert "<script>alert" not in page
    assert "<img src=x" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert page.count("&lt;script&gt;alert(1)") == 5


# --- RAG tokens and badges (s4.3, s4.9.3) ---


def test_exact_s4_3_hex_values():
    assert html.RAG_COLOURS == {
        "red": "#b42318", "red-bg": "#fef3f2",
        "amber": "#b54708", "amber-bg": "#fffaeb",
        "green": "#067647", "green-bg": "#ecfdf3",
        "grey": "#475467", "grey-bg": "#f2f4f7",
    }


def test_page_uses_only_token_hexes_for_rag(defender_off):
    page = html.render_string(defender_off)
    for name, hex_value in html.RAG_COLOURS.items():
        assert f"--rag-{name}: {hex_value};" in page


@pytest.mark.parametrize(
    "status, symbol, word",
    [
        ("red", "\u25cf", "Act now"),
        ("amber", "\u25b2", "Improve"),
        ("green", "\u2713", "Good"),
        ("unavailable", "\u2298", "Not checked"),
        ("failed", "\u2715", "Check failed"),
    ],
)
def test_badge_has_symbol_and_word(status, symbol, word):
    assert html.badge(status)["symbol"] == symbol
    assert html.badge(status)["word"] == word


def test_overall_badge_shows_symbol_word_and_colour(defender_off):
    page = html.render_string(defender_off)
    header = page[page.index("<header>") : page.index("</header>")]
    assert 'class="badge badge-red badge-lg"' in header
    assert "\u25cf</span> Act now" in header


def test_failed_badge_is_dashed(defender_off):
    report = copy.deepcopy(defender_off)
    report["categories"][4].update(status="failed", evidence=[], fix_ids=[])
    page = html.render_string(report)
    assert "badge badge-grey badge-failed" in _section(page, "recovery")


# --- section order (s4.10 structure) ---


def test_sections_in_fixed_order(defender_off):
    page = html.render_string(defender_off)
    marks = [
        "<header>",
        '<section id="actions">',
        '<section id="overview">',
        *[f'<section class="category" id="{c}">' for c in
          ("backup", "patch", "software", "protection", "recovery")],
        "<footer>",
    ]
    positions = [page.index(m) for m in marks]
    assert positions == sorted(positions)


def test_header_has_product_summary_and_date(defender_off):
    page = html.render_string(defender_off)
    header = page[page.index("<header>") : page.index("</header>")]
    assert "Antigravity" in header
    assert html_escape(defender_off["summary"]) in header
    assert f"Checked on {html.human_date(defender_off['generated_at'])}" in header


def test_licence_org_only_when_given(defender_off):
    assert "Licensed to" not in html.render_string(defender_off)
    assert "Licensed to Acme Bakery" in html.render_string(defender_off, org="Acme Bakery")


def test_top_fixes_numbered_in_report_order(defender_off):
    page = html.render_string(defender_off)
    actions = page[page.index('<section id="actions">') : page.index('<section id="overview">')]
    expected = [f["title"] for fid in defender_off["top_fixes"]
                for f in defender_off["fixes"] if f["id"] == fid]
    found = re.findall(r'<span class="rank">(\d)</span>\s*<div>\s*<h3>(.*?) <span', actions)
    assert [int(n) for n, _ in found] == list(range(1, len(expected) + 1))
    assert [t for _, t in found] == [html_escape(t) for t in expected]


def test_no_top_fixes_says_nothing_urgent(baseline):
    page = html.render_string(_report(FIXTURES / "scan.healthy.json", baseline))
    assert "Nothing urgent. Re-check monthly." in page
    assert 'class="top"' not in page


def test_strip_has_five_anchor_tiles(defender_off):
    page = html.render_string(defender_off)
    for c in defender_off["categories"]:
        assert f'<a class="tile" href="#{c["id"]}">' in page
    assert page.count('class="tile"') == 5


def test_each_category_lists_its_fixes_with_why_and_steps(defender_off):
    page = html.render_string(defender_off)
    fixes = {f["id"]: f for f in defender_off["fixes"]}
    for c in defender_off["categories"]:
        section = _section(page, c["id"])
        for fix_id in c["fix_ids"]:
            assert f'id="fix-{fix_id}"' in section
            assert html_escape(fixes[fix_id]["why"]) in section
            for step in fixes[fix_id]["steps"]:
                assert f"<li>{html_escape(step)}</li>" in section


def test_footer_lines_and_versions(defender_off):
    page = html.render_string(defender_off)
    footer = page[page.index("<footer>") :]
    assert FOOTER_LOCAL in footer
    assert FOOTER_AUDIT in footer
    assert f"Engine {defender_off['engine_version']}" in footer
    assert f"Baseline {defender_off['baseline_version']}" in footer


# --- evidence rows (s4.10 evidence table) ---


def test_unavailable_category_row_says_not_checked_never_check_failed(make_scan, baseline):
    report = assess(make_scan(ALL_NULL_RECOVERY), baseline)
    recovery = next(c for c in report["categories"] if c["id"] == "recovery")
    assert recovery["status"] == "unavailable"

    section = _section(html.render_string(report), "recovery")
    rows = _rows(section)
    assert len(rows) == len(recovery["evidence"]) == 4
    for row in rows:
        assert "Not checked" in row
        assert "Check failed" not in row
        assert 'class="grey"' in row
    assert "Check failed" not in section


def test_unavailable_value_gets_not_checked_prefix():
    row = {"label": "BitLocker", "value": "Not available on Windows Home", "status": "unavailable"}
    assert html.evidence_value(row) == "Not checked \u2014 not available on Windows Home"


def test_unavailable_value_already_prefixed_is_kept():
    row = {"label": "BitLocker", "value": "Not checked \u2014 needs admin", "status": "unavailable"}
    assert html.evidence_value(row) == "Not checked \u2014 needs admin"


def test_failed_value_gets_couldnt_read_prefix(defender_off):
    report = copy.deepcopy(defender_off)
    report["categories"][3]["evidence"][0].update(value="Cmdlet threw", status="failed")
    row = _rows(_section(html.render_string(report), "protection"))[0]
    assert '<td class="grey">Couldn&#39;t read: Cmdlet threw</td>' in row
    assert "\u2715</span> Check failed" in row
    assert "Not checked" not in row


def test_rated_row_shows_coloured_symbol_and_normal_text(defender_off):
    rows = _rows(_section(html.render_string(defender_off), "protection"))
    red = [r for r in rows if "state-red" in r]
    assert red
    for r in red:
        assert "\u25cf</span> Act now" in r
        assert 'class="grey"' not in r


def test_row_without_status_is_neutral(defender_off):
    report = copy.deepcopy(defender_off)
    report["categories"][0]["evidence"] = [{"label": "Note", "value": "Plain fact"}]
    row = _rows(_section(html.render_string(report), "backup"))[0]
    assert '<td class="state"></td>' in row
    for b in html.BADGES.values():
        assert b["symbol"] not in row
    assert 'class="grey"' not in row


# --- print and width (s4.10 rows 5, 6) ---


def test_print_rules_and_max_width(defender_off):
    page = html.render_string(defender_off)
    style = page[page.index("<style>") : page.index("</style>")]
    assert "max-width: 860px;" in style
    printing = style[style.index("@media print") :]
    assert "size: A4;" in printing
    assert "background: none !important;" in printing
    assert "page-break-inside: avoid;" in printing
    assert ".category" in printing


def test_human_date():
    assert html.human_date("2026-11-04T17:02:46Z") == "4 Nov 2026"


# --- standalone entry point ---


def test_main_renders_report_json(defender_off, tmp_path):
    src = tmp_path / "report.json"
    src.write_text(json.dumps(defender_off), encoding="utf-8")
    out = tmp_path / "out" / "report.html"
    assert html.main([str(src), str(out)]) == 0
    assert FOOTER_LOCAL in out.read_text(encoding="utf-8")


def test_main_rejects_invalid_report(tmp_path):
    src = tmp_path / "report.json"
    src.write_text(json.dumps({"overall": "red"}), encoding="utf-8")
    with pytest.raises(ContractError):
        html.main([str(src), str(tmp_path / "report.html")])


def test_main_usage(capsys):
    assert html.main([]) == 2
    assert "usage" in capsys.readouterr().err




def test_renderer_never_reads_the_scan():
    # s2.3 row 9: render from the report model only.
    source = (html.TEMPLATES.parent / "render" / "html.py").read_text(encoding="ascii")
    assert "parse_path" not in source and "ScanModel" not in source
