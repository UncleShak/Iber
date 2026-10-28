"""Fixed category order and overall RAG (s0.8, s2.6)."""

from collections.abc import Iterable

from antigravity_engine.scoring.result import CATEGORY_ORDER, CategoryResult, Status, worst


def order(results: Iterable[CategoryResult]) -> list[CategoryResult]:
    """Exactly one result per category, in the fixed report order."""
    by_id: dict[str, CategoryResult] = {}
    for r in results:
        if r.id in by_id:
            raise ValueError(f"duplicate result for category {r.id!r}")
        by_id[r.id] = r
    missing = [c for c in CATEGORY_ORDER if c not in by_id]
    if missing:
        raise ValueError(f"missing results for categories: {', '.join(missing)}")
    return [by_id[c] for c in CATEGORY_ORDER]


def overall(results: Iterable[CategoryResult]) -> Status:
    """Worst rated category; if none is rated, amber."""
    return worst(r.status for r in results) or Status.AMBER
