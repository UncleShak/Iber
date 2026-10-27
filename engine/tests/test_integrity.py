"""Cross-cutting checks over the shared fixtures (s7.6, s2.13).

Phase 10 extends this file; for now it holds the D3 check that no fixture
needs clipping in any scorer that exists.
"""

import warnings

import pytest

from antigravity_engine.parser import parse_path
from antigravity_engine.scoring import backup, patch, recovery, software
from antigravity_engine.scoring.result import ClippedWarning
from conftest import FIXTURES

SCORERS = (backup, patch, software, recovery)


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("scan.*.json")), ids=lambda p: p.name)
def test_no_fixture_needs_clipping(path, baseline):
    scan = parse_path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ClippedWarning)
        for scorer in SCORERS:
            scorer.score(scan, baseline)
