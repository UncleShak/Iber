"""CLI flags, exit codes and failure isolation (s2.4, s2.7, s2.11)."""

import json
import subprocess
import sys

import pytest

from antigravity_engine import __main__ as cli
from antigravity_engine import __version__
from antigravity_engine.parser import validate_schema
from antigravity_engine.render import html
from antigravity_engine.report_model import CONTRACT_ERROR_EXPLANATION
from antigravity_engine.scoring.result import CATEGORY_ORDER
from conftest import FIXTURES, ROOT

HEALTHY = FIXTURES / "scan.healthy.json"
OUTPUTS = {"report.json", "report.html", "action-plan.pdf", "evidence.json"}


def _run(in_path, out_dir, *extra) -> int:
    return cli.main(["--in", str(in_path), "--out", str(out_dir), *extra])


def _report(out_dir) -> dict:
    report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    validate_schema(report, "report.schema.json")
    return report


def _statuses(report: dict) -> dict[str, str]:
    return {c["id"]: c["status"] for c in report["categories"]}


# --- --version ---


def test_version_prints_engine_and_contract(capsys):
    assert cli.main(["--version"]) == 0
    assert capsys.readouterr().out == f"antigravity-engine {__version__} contract 1.0.0\n"


def test_version_runs_as_module():
    proc = subprocess.run(
        [sys.executable, "-m", "antigravity_engine", "--version"],
        cwd=ROOT / "engine", capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == f"antigravity-engine {__version__} contract 1.0.0"


def test_in_and_out_are_required(tmp_path):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--in", str(HEALTHY)])
    assert exc.value.code == 2


# --- contract errors: exit 2, report.json with all five failed ---


def test_text_file_exits_2_with_all_categories_failed(tmp_path, capsys):
    bad = tmp_path / "scan.txt"
    bad.write_text("this is not json", encoding="utf-8")
    out = tmp_path / "out" / "nested"

    assert _run(bad, out) == 2

    report = _report(out)
    assert report["overall"] == "amber"
    assert [c["id"] for c in report["categories"]] == list(CATEGORY_ORDER)
    assert all(c["status"] == "failed" for c in report["categories"])
    assert all(c["explanation"] == CONTRACT_ERROR_EXPLANATION for c in report["categories"])
    assert "not valid JSON" in report["summary"]
    assert report["fixes"] == [] and report["top_fixes"] == []
    assert "not valid JSON" in capsys.readouterr().err
    assert {p.name for p in out.iterdir()} == {"report.json"}


def test_missing_input_exits_2(tmp_path):
    assert _run(tmp_path / "nope.json", tmp_path / "out") == 2
    assert all(s == "failed" for s in _statuses(_report(tmp_path / "out")).values())


def test_wrong_major_schema_version_exits_2(tmp_path, make_raw, write_json, capsys):
    path = write_json(make_raw({"schema_version": "2.0.0"}))

    assert _run(path, tmp_path / "out") == 2

    report = _report(tmp_path / "out")
    assert set(_statuses(report).values()) == {"failed"}
    assert "unsupported schema version" in report["summary"]
    assert "unsupported schema version" in capsys.readouterr().err


def test_error_report_records_baseline_version(tmp_path):
    bad = tmp_path / "scan.txt"
    bad.write_text("x", encoding="utf-8")
    _run(bad, tmp_path / "out")
    baseline = json.loads((ROOT / "baseline" / "software-baseline.json").read_text("utf-8"))
    assert _report(tmp_path / "out")["baseline_version"] == baseline["baseline_version"]


# --- per-category failure isolation (s2.7) ---


def test_collector_failed_section_fails_only_that_category(tmp_path, make_raw, write_json):
    raw = make_raw()
    raw["patch"]["status"] = "failed"
    raw["patch"]["error"] = "Get-HotFix threw: RPC server unavailable"

    assert _run(write_json(raw), tmp_path / "out", "--json-only") == 0

    statuses = _statuses(_report(tmp_path / "out"))
    assert statuses["patch"] == "failed"
    assert all(statuses[c] in {"red", "amber", "green"} for c in CATEGORY_ORDER if c != "patch")


def test_scorer_exception_fails_only_that_category(tmp_path, monkeypatch, capsys):
    def boom(scan, baseline):
        raise RuntimeError("scorer bug")

    monkeypatch.setitem(cli.SCORERS, "protection", boom)

    assert _run(HEALTHY, tmp_path / "out", "--json-only") == 0

    report = _report(tmp_path / "out")
    protection = next(c for c in report["categories"] if c["id"] == "protection")
    assert protection["status"] == "failed"
    assert protection["explanation"] == "Internal error while checking."
    statuses = _statuses(report)
    assert all(statuses[c] in {"red", "amber", "green"} for c in CATEGORY_ORDER if c != "protection")
    assert report["summary"].endswith("Some checks couldn't run.")
    err = capsys.readouterr().err
    assert "Traceback" in err and "RuntimeError: scorer bug" in err


def test_every_scorer_raising_still_writes_report(tmp_path, monkeypatch):
    def boom(scan, baseline):
        raise ValueError("bug")

    for category in CATEGORY_ORDER:
        monkeypatch.setitem(cli.SCORERS, category, boom)

    assert _run(HEALTHY, tmp_path / "out", "--json-only") == 0

    report = _report(tmp_path / "out")
    assert set(_statuses(report).values()) == {"failed"}
    assert report["overall"] == "amber"


# --- outputs ---


def test_json_only_skips_html_and_pdf(tmp_path):
    assert _run(HEALTHY, tmp_path / "out", "--json-only") == 0
    assert {p.name for p in (tmp_path / "out").iterdir()} == {"report.json", "evidence.json"}


def test_report_json_is_ascii_but_keeps_the_em_dash(tmp_path):
    # D6: escaped on disk, the same text once parsed.
    out = tmp_path / "out"
    assert _run(FIXTURES / "scan.defender-off.json", out, "--json-only") == 0
    raw = (out / "report.json").read_bytes()
    assert raw.isascii()
    assert b"\\u2014" in raw
    values = [row["value"] for c in _report(out)["categories"] for row in c["evidence"]]
    assert "Not checked \u2014 needs admin" in values


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("scan.*.json")), ids=lambda p: p.name)
def test_fixture_writes_all_four_outputs(path, tmp_path):
    out = tmp_path / "out"
    assert _run(path, out) == 0
    assert {p.name for p in out.iterdir()} == OUTPUTS
    assert all((out / name).stat().st_size > 0 for name in OUTPUTS)
    assert _report(out)["run_id"] == json.loads(path.read_text("utf-8"))["run_id"]


def test_report_json_is_utf8_without_bom(tmp_path):
    _run(HEALTHY, tmp_path / "out", "--json-only")
    raw = (tmp_path / "out" / "report.json").read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    raw.decode("utf-8")


def test_render_failure_exits_3_and_keeps_report_json(tmp_path, monkeypatch, capsys):
    def boom(report, path, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(html, "render", boom)

    assert _run(HEALTHY, tmp_path / "out") == 3

    _report(tmp_path / "out")
    assert "OSError: disk full" in capsys.readouterr().err


# --- --baseline ---


def test_baseline_flag_overrides_default(tmp_path, write_json):
    baseline = json.loads((ROOT / "baseline" / "software-baseline.json").read_text("utf-8"))
    baseline["baseline_version"] = "2099-01-01"
    path = write_json(baseline, "baseline.json")

    assert _run(HEALTHY, tmp_path / "out", "--json-only", "--baseline", str(path)) == 0
    assert _report(tmp_path / "out")["baseline_version"] == "2099-01-01"


def test_unloadable_baseline_exits_1_without_report(tmp_path, capsys):
    out = tmp_path / "out"
    assert _run(HEALTHY, out, "--baseline", str(tmp_path / "missing.json")) == 1
    assert not (out / "report.json").exists()
    assert "cannot load baseline" in capsys.readouterr().err


# --- D8: run-specific steps reach report.json ---


def test_outdated_app_names_reach_update_steps(tmp_path, make_raw, write_json):
    raw = make_raw()
    chrome = next(a for a in raw["software"]["installed"] if a["name"] == "Google Chrome")
    chrome["version"] = "100.0.0.1"

    assert _run(write_json(raw), tmp_path / "out", "--json-only") == 0

    report = _report(tmp_path / "out")
    fix = next(f for f in report["fixes"] if f["id"] == "update-outdated-apps")
    assert any("Google Chrome" in step for step in fix["steps"])
