"""Independent closed-bar-only BTC Lab diagnostics; never an alert or order.

Generic Choppiness Index and prior-range sweep calculations; not copied
from third-party TradingView scripts.
"""
from math import isfinite, log10


def _valid(bars):
    if not isinstance(bars, list) or not bars:
        raise ValueError("Candles required")
    previous = None
    for b in bars:
        if not all(k in b for k in ("t", "T", "o", "h", "l", "c")):
            raise ValueError("Incomplete candle")
        values = [float(b[k]) for k in ("o", "h", "l", "c")]
        if not all(isfinite(v) and v > 0 for v in values):
            raise ValueError("Invalid prices")
        if values[1] < max(values[0], values[3]) or values[2] > min(values[0], values[3]):
            raise ValueError("Invalid OHLC")
        start, end = int(b["t"]), int(b["T"])
        if start >= end or (previous is not None and start != previous + 1):
            raise ValueError("Nonconsecutive candles")
        previous = end


def diagnostic(bars, *, chop_length=14, swing_lookback=20):
    """Research-only calculations on the last closed bar; no future pivots."""
    if not isinstance(chop_length, int) or not 2 <= chop_length <= 100:
        raise ValueError("Invalid CHOP length")
    if not isinstance(swing_lookback, int) or not 2 <= swing_lookback <= 200:
        raise ValueError("Invalid lookback")
    _valid(bars)
    if len(bars) < max(chop_length + 1, swing_lookback + 1):
        raise ValueError("Insufficient closed bars")
    last = bars[-1]
    recent = bars[-chop_length:]
    ranges = []
    for idx in range(len(bars) - chop_length, len(bars)):
        b, prev = bars[idx], bars[idx - 1]
        ranges.append(max(b["h"] - b["l"], abs(b["h"] - prev["c"]), abs(b["l"] - prev["c"])))
    high, low = max(b["h"] for b in recent), min(b["l"] for b in recent)
    span = high - low
    chop = None if span <= 0 else 100 * log10(sum(ranges) / span) / log10(chop_length)
    preceding = bars[-swing_lookback - 1:-1]
    prior_high = max(b["h"] for b in preceding)
    prior_low = min(b["l"] for b in preceding)
    sweep_high = last["h"] > prior_high and last["c"] < prior_high
    sweep_low = last["l"] < prior_low and last["c"] > prior_low
    return {
        "kind": "RESEARCH_ONLY_BTC_LAB_DIAGNOSTIC_V1",
        "closedBarEndMs": int(last["T"]),
        "choppinessIndex": chop,
        "priorHigh": prior_high, "priorLow": prior_low,
        "rejectedHighSweep": sweep_high, "rejectedLowSweep": sweep_low,
        "sweepSignal": "BEARISH_SWEEP" if sweep_high else ("BULLISH_SWEEP" if sweep_low else "NONE"),
        "classicChanged": False, "researchOnly": True,
        "discordEligible": False, "automaticTrading": False,
        "profitabilityClaimAllowed": False, "originalViprasolVerified": False,
    }
