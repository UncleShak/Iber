from datetime import UTC, date, datetime

import pytest

from antigravity_engine import clock
from conftest import FIXTURES
from antigravity_engine.parser import parse_path


def test_parse_iso_timestamp_is_aware_utc():
    assert clock.parse_iso("2026-11-14T16:42:07Z") == datetime(2026, 11, 14, 16, 42, 7, tzinfo=UTC)


def test_parse_iso_date_is_midnight_utc():
    assert clock.parse_iso("2026-11-05") == datetime(2026, 11, 5, tzinfo=UTC)


def test_parse_iso_rejects_garbage():
    with pytest.raises(ValueError):
        clock.parse_iso("13 Nov 2026")


def test_now_is_collected_at_not_wall_clock():
    scan = parse_path(FIXTURES / "scan.healthy.json")
    assert clock.now(scan) == datetime(2026, 11, 14, 16, 42, 7, tzinfo=UTC)


@pytest.mark.parametrize(
    ("name", "expected"),
    [("scan.healthy.json", 9), ("scan.defender-off.json", 55)],
)
def test_days_between_matches_fixture_hotfix_age(name, expected):
    scan = parse_path(FIXTURES / name)
    latest = clock.parse_iso(scan.patch.latest_hotfix_installed_on)
    assert clock.days_between(latest, clock.now(scan)) == expected
    assert scan.patch.days_since_latest_hotfix == expected


def test_days_between_counts_calendar_days_not_24h_blocks():
    a = datetime(2026, 11, 13, 23, 59, tzinfo=UTC)
    b = datetime(2026, 11, 14, 0, 1, tzinfo=UTC)
    assert clock.days_between(a, b) == 1


def test_days_between_negative_when_reversed():
    assert clock.days_between(date(2026, 11, 14), date(2026, 11, 10)) == -4


def test_days_between_mixes_date_and_datetime():
    assert clock.days_between(date(2026, 11, 1), datetime(2026, 11, 14, 16, 0, tzinfo=UTC)) == 13


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (date(2026, 11, 13), "13 Nov 2026"),
        (date(2026, 1, 5), "5 Jan 2026"),
        (datetime(2026, 12, 31, 23, 0, tzinfo=UTC), "31 Dec 2026"),
    ],
)
def test_fmt_date(value, expected):
    assert clock.fmt_date(value) == expected


@pytest.mark.parametrize(
    ("days", "expected"),
    [(-2, "today"), (0, "today"), (1, "1 day ago"), (9, "9 days ago")],
)
def test_fmt_age(days, expected):
    assert clock.fmt_age(days) == expected
