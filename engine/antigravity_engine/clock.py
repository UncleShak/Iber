"""Date helpers. "Now" is always scan.collected_at, never the wall clock (s2.3)."""

from datetime import UTC, date, datetime

from antigravity_engine.contract import ScanModel

# Fixed English month names: strftime("%b") follows the OS locale.
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def parse_iso(s: str) -> datetime:
    """Parse "2026-11-14T16:42:07Z" or "2026-11-05" into an aware UTC datetime."""
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def now(scan: ScanModel) -> datetime:
    return parse_iso(scan.collected_at)


def _utc_date(d: date | datetime) -> date:
    if isinstance(d, datetime):
        return (d.astimezone(UTC) if d.tzinfo else d).date()
    return d


def days_between(a: date | datetime, b: date | datetime) -> int:
    """Whole calendar days (UTC) from a to b; negative if b is before a."""
    return (_utc_date(b) - _utc_date(a)).days


def fmt_date(d: date | datetime) -> str:
    """Report display format, e.g. "13 Nov 2026"."""
    d = _utc_date(d)
    return f"{d.day} {_MONTHS[d.month - 1]} {d.year}"


def fmt_age(days: int) -> str:
    """Evidence phrase for an age in days: "today", "1 day ago", "9 days ago"."""
    if days <= 0:
        return "today"
    return "1 day ago" if days == 1 else f"{days} days ago"
