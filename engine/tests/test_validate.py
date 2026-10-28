import importlib.util
import json
import subprocess
import sys

import pytest

from conftest import FIXTURES, ROOT

VALIDATE = ROOT / "engine" / "tools" / "validate.py"

_spec = importlib.util.spec_from_file_location("validate_tool", VALIDATE)
validate_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_tool)

CATEGORY_IDS = ["backup", "patch", "software", "protection", "recovery"]


def _report() -> dict:
    return {
        "schema_version": "1.0.0",
        "run_id": "2026-11-14T16-42-07Z_0001",
        "generated_at": "2026-11-14T16:42:09Z",
        "engine_version": "0.1.0",
        "baseline_version": "2026-11-01",
        "overall": "green",
        "summary": "No urgent issues found.",
        "categories": [
            {"id": c, "title": c.title(), "status": "green", "explanation": "All good.",
             "evidence": [], "fix_ids": []}
            for c in CATEGORY_IDS
        ],
        "fixes": [],
        "top_fixes": [],
        "scan": {"is_admin": True, "duration_ms": 8420, "os_caption": "Microsoft Windows 11 Pro"},
    }


def run(capsys, *argv):
    code = validate_tool.main(list(argv))
    return code, capsys.readouterr().out.strip()


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("scan.*.json")), ids=lambda p: p.name)
def test_valid_scan_fixtures(capsys, path):
    assert run(capsys, "scan", str(path)) == (0, "VALID scan 1.0.0")


def test_invalid_scan_prints_path(capsys, make_raw, write_json):
    p = write_json(make_raw({"patch": {"hotfixes": {}}}))
    code, out = run(capsys, "scan", str(p))
    assert code == 1
    assert out == "INVALID $.patch.hotfixes: {} is not of type 'array'"


def test_wrong_major_scan(capsys, make_raw, write_json):
    code, out = run(capsys, "scan", str(write_json(make_raw({"schema_version": "2.0.0"}))))
    assert code == 1
    assert out.startswith("INVALID $.schema_version: unsupported schema version '2.0.0'")


def test_bad_json_uses_root_path(capsys, write_json):
    code, out = run(capsys, "scan", str(write_json(b"{oops")))
    assert code == 1
    assert out.startswith("INVALID $: not valid JSON")


def test_missing_file(capsys, tmp_path):
    code, out = run(capsys, "scan", str(tmp_path / "missing.json"))
    assert code == 1
    assert out.startswith("INVALID $: input missing or too large")


def test_valid_report(capsys, write_json):
    assert run(capsys, "report", str(write_json(_report(), "report.json"))) == (0, "VALID report 1.0.0")


def test_report_needs_five_categories(capsys, write_json):
    report = _report()
    report["categories"].pop()
    code, out = run(capsys, "report", str(write_json(report, "report.json")))
    assert code == 1
    assert out.startswith("INVALID $.categories: ")


def test_report_category_order_enforced(capsys, write_json):
    report = _report()
    report["categories"][0], report["categories"][1] = report["categories"][1], report["categories"][0]
    code, out = run(capsys, "report", str(write_json(report, "report.json")))
    assert code == 1
    assert out.startswith(("INVALID $.categories[0].id: ", "INVALID $.categories[1].id: "))
    assert out.endswith("was expected")


def test_scan_file_is_not_a_valid_report(capsys):
    code, out = run(capsys, "report", str(FIXTURES / "scan.healthy.json"))
    assert code == 1
    assert out.startswith("INVALID $: ")


def test_bad_kind_is_usage_error():
    with pytest.raises(SystemExit) as exc:
        validate_tool.main(["evidence", "x.json"])
    assert exc.value.code == 2


@pytest.mark.parametrize("cwd", [ROOT, ROOT / "engine"], ids=["repo-root", "engine"])
def test_runs_as_script_from_any_cwd(cwd):
    proc = subprocess.run(
        [sys.executable, str(VALIDATE), "scan", str(FIXTURES / "scan.defender-off.json")],
        cwd=cwd, capture_output=True, text=True, check=False,
    )
    assert (proc.returncode, proc.stdout.strip()) == (0, "VALID scan 1.0.0"), proc.stderr


def test_script_exit_code_on_invalid(make_raw, write_json):
    p = write_json(json.loads(json.dumps(make_raw({"duration_ms": -1}))))
    proc = subprocess.run([sys.executable, str(VALIDATE), "scan", str(p)],
                          capture_output=True, text=True, check=False)
    assert proc.returncode == 1
    assert proc.stdout.startswith("INVALID $.duration_ms: -1 is less than the minimum of 0")
