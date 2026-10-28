"""The engine never talks to the network (CLAUDE.md, s2.11 acceptance).

Same check as
  Select-String -Path engine\\antigravity_engine\\**\\*.py -Pattern 'requests|urllib.request|http.client'
plus an import scan, so an aliased or from-import of a network module is caught too.
"""

import ast
import re

import pytest

from conftest import ROOT

ENGINE = ROOT / "engine"
SOURCES = sorted([*(ENGINE / "antigravity_engine").rglob("*.py"), *(ENGINE / "tools").rglob("*.py")])
TEXT_PATTERN = re.compile(r"requests|urllib\.request|http\.client")
NETWORK_MODULES = {
    "socket", "ssl", "http", "urllib", "requests", "httpx", "aiohttp",
    "ftplib", "smtplib", "poplib", "imaplib", "telnetlib", "xmlrpc", "asyncio",
}


def _id(path) -> str:
    return path.relative_to(ENGINE).as_posix()


def test_sources_found():
    assert any(p.name == "__main__.py" for p in SOURCES)


@pytest.mark.parametrize("path", SOURCES, ids=_id)
def test_no_network_text(path):
    hits = [
        f"{n}: {line.strip()}"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if TEXT_PATTERN.search(line)
    ]
    assert hits == []


@pytest.mark.parametrize("path", SOURCES, ids=_id)
def test_no_network_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    assert imported & NETWORK_MODULES == set()


def test_text_pattern_catches_a_network_import():
    assert TEXT_PATTERN.search("import urllib.request")
    assert TEXT_PATTERN.search("from http.client import HTTPSConnection")
