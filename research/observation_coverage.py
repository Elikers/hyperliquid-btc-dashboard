"""Research-only observation coverage across a bounded UTC time window.

Compares *closed candle timestamps present in actual compact artifacts*
against expected exchange candle closes. This measures observation coverage,
not whether GitHub cron fires on time, nor Pine parity or strategy quality.
No market data is fabricated to fill gaps.
"""
from datetime import datetime
from research.forward_paper_ledger import STEPS


def _utc_ms(dt):
    if not isinstance(dt, datetime) or dt.utcoffset() is None:
        raise ValueError("Expected timezone-aware datetime")
    return int(dt.timestamp() * 1000)


def observation_coverage(records, *, after, through):
    """Summarize per-TF calendar coverage, including the edges of the window.

    A bar is expected only if its final millisecond lies within the time
    window and its interval is fully closed as of `through`.
    Repeated observations of the same close count once. The canonical
    ledger validates all untrusted record integrity before this call.
    """
    begin_ms, end_ms = _utc_ms(after), _utc_ms(through)
    if end_ms <= begin_ms:
        raise ValueError("Coverage end must follow the window start")
    result = {}
    for tf, step in STEPS.items():
        first = ((begin_ms + 1 + step - 1) // step) * step - 1
        last = (end_ms // step) * step - 1
        expected = 0 if last < first else (last - first) // step + 1
        seen = set()
        captures = 0
        for rec in records:
            frames = rec.get("timeframes", {})
            if tf not in frames:
                raise ValueError("Expected timeframe missing")
            candle_end = int(frames[tf]["closedBarEndMs"])
            # Observations captured outside this window cannot establish
            # whether its bars were seen during the requested period.
            # Bars are filtered by close time and the matching capture time.
            captured = datetime.fromisoformat(rec["capturedAtUtc"])
            if _utc_ms(captured) < begin_ms or _utc_ms(captured) > end_ms:
                continue
            captures += 1
            if first <= candle_end <= last:
                seen.add(candle_end)
        # Only sample individual timestamps; never build a huge set of
        # every theoretical bar across an arbitrary multi-month window.
        observed = len(seen)
        if observed > expected:
            raise ValueError("Observed more bars than physically possible")
        missing = expected - observed
        leading = (min(seen) - first) // step if seen else expected
        trailing = (last - max(seen)) // step if seen else expected
        internal = missing - leading - trailing if seen else 0
        if min(leading, trailing, internal) < 0:
            raise ValueError("Inconsistent candle coverage")
        result[tf] = {
            "expectedClosedBars": expected,
            "observedUniqueClosedBars": observed,
            "unobservedClosedBars": missing,
            "leadingUnobservedBars": leading,
            "internalUnobservedBars": internal,
            "trailingUnobservedBars": trailing,
            "observationCoverageFraction": None if expected == 0 else observed / expected,
            "firstObservedClosedBarEndMs": min(seen) if seen else None,
            "lastObservedClosedBarEndMs": max(seen) if seen else None,
            "capturesWithinWindow": captures,
            "continuousClosedBarCoverage": expected > 0 and missing == 0,
            "researchOnly": True,
        }
    return {
        "kind": "research_only_closed_candle_coverage_v1",
        "windowStartUtc": after.isoformat(),
        "windowEndUtc": through.isoformat(),
        "byTimeframe": result,
        "coverageDoesNotProveScheduleReliability": True,
        "originalViprasolVerified": False,
        "discordEligible": False,
        "automaticTrading": False,
        "profitabilityClaimAllowed": False,
    }
