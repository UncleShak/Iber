"""Internal risk score and the header summary sentence (s2.6)."""

from collections.abc import Iterable, Sequence

from antigravity_engine.scoring.result import RATED, CategoryResult, Status

WEIGHTS = {"protection": 30, "backup": 30, "patch": 20, "recovery": 10, "software": 10}
POINTS = {Status.RED: 1.0, Status.AMBER: 0.5, Status.GREEN: 0.0}
TIGHTEN_THRESHOLD = 25
MAX_SUMMARY = 200

NOTHING_RATED = "We couldn't check enough of this PC to rate it."
FAILED_SUFFIX = " Some checks couldn't run."


def risk_score(results: Iterable[CategoryResult]) -> float | None:
    """0-100 over rated categories only; None if nothing is rated."""
    rated = [r for r in results if r.status in RATED]
    denominator = sum(WEIGHTS[r.id] for r in rated)
    if denominator == 0:
        return None
    return 100 * sum(WEIGHTS[r.id] * POINTS[r.status] for r in rated) / denominator


def summary(results: Iterable[CategoryResult], fixes: Sequence[dict]) -> str:
    """Header sentence (s2.6). fixes is the resolved fixes[] from scoring.fixes.

    "{n} things to tighten up": n is the number of amber fixes, so the headline
    matches the fix cards below it; if no amber result attached a fix, n falls
    back to the number of amber categories (D2).
    """
    results = list(results)
    score = risk_score(results)
    reds = sum(r.status == Status.RED for r in results)
    ambers = sum(f["severity"] == Status.AMBER for f in fixes) or sum(
        r.status == Status.AMBER for r in results
    )

    if score is None:
        text = NOTHING_RATED
    elif reds:
        text = (
            "1 urgent issue needs attention this week."
            if reds == 1
            else f"{reds} urgent issues need attention this week."
        )
    elif score >= TIGHTEN_THRESHOLD:
        noun = "thing" if ambers == 1 else "things"
        text = f"No urgent issues, but {ambers} {noun} to tighten up."
    else:
        text = "This PC is in good shape. Keep it that way."

    if any(r.status == Status.FAILED for r in results):
        text += FAILED_SUFFIX
    return text[:MAX_SUMMARY]
