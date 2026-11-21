"""Strict, stdlib-only input/parity checks for Viprasol research.

No orders, webhook delivery, or automatic promotion of candidate signals.
The default TradingView macro symbol is CME_MINI:NQ1!, not a generic NQ proxy.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Mapping, Sequence

TF_MS = {"15m": 900_000, "30m": 1_800_000, "1h": 3_600_000}
MACRO_SYMBOL = "CME_MINI:NQ1!"
MARKET_SYMBOL = "HYPERLIQUID:BTCUSDC.P"


@dataclass(frozen=True)
class Validation:
    acceptable: bool
    reasons: tuple[str, ...]


def _num(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("boolean is not a price")
    value = float(value)
    if not isfinite(value):
        raise ValueError("nonfinite number")
    return value


def check_candles(candles: Sequence[Mapping], timeframe: str, *, min_count: int = 100) -> Validation:
    reasons = []
    step = TF_MS.get(timeframe)
    if step is None:
        return Validation(False, ("Unsupported timeframe",))
    if len(candles) < min_count:
        reasons.append("Too few candles for indicator warmup")
    previous = None
    for index, bar in enumerate(candles):
        try:
            start, end = int(bar["t"]), int(bar["T"])
            o, h, l, c = (_num(bar[k]) for k in ("o", "h", "l", "c"))
            volume = _num(bar["v"])
            if start < 0 or end != start + step - 1:
                raise ValueError("unexpected candle period boundaries")
            if start % step:
                raise ValueError("candle time not aligned to interval")
            if min(o, h, l, c) <= 0 or l > min(o, c) or h < max(o, c) or h < l or volume < 0:
                raise ValueError("invalid OHLCV")
            if previous is not None and start - previous != step:
                raise ValueError("candle gap, overlap, or wrong ordering")
            previous = start
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            reasons.append(f"Candle {index}: {exc}")
            break
    return Validation(not reasons, tuple(reasons))


def check_macro_source(
    *,
    symbol: str,
    provider: str,
    timeframe: str,
    btc_bars: Sequence[Mapping],
    macro_bars: Sequence[Mapping],
    same_tradingview_construction: bool,
) -> Validation:
    """Fail closed if the series is a proxy or if missing market-session candles
    are silently filled. Having the same ticker label is NOT proof of identical
    TradingView continuous-contract construction.
    """
    reasons = []
    if symbol != MACRO_SYMBOL:
        reasons.append("Not CME_MINI:NQ1!: proxy macros cannot establish parity")
    if provider.strip().lower() in {"", "yahoo", "yfinance", "proxy", "synthetic"}:
        reasons.append("Macro provider unverified or explicitly a proxy")
    if not same_tradingview_construction:
        reasons.append("Continuous-contract construction/roll adjustment not verified")
    btc = check_candles(btc_bars, timeframe)
    if not btc.acceptable:
        reasons.append("BTC candles invalid: " + "; ".join(btc.reasons))
    if not macro_bars:
        reasons.append("Macro candles absent")
    else:
        macro = check_candles(macro_bars, timeframe, min_count=20)
        if not macro.acceptable:
            reasons.append("Macro candles invalid: " + "; ".join(macro.reasons))
        # The source request.security may carry forward the previous macro
        # value during exchange closures. Never claim parity by filling a
        # public dataset's session gaps on our own.
        if btc_bars and macro_bars:
            overlap = set(int(b["t"]) for b in btc_bars) & set(int(m["t"]) for m in macro_bars)
            if not overlap:
                reasons.append("BTC and macro histories have no common timestamps")
    return Validation(not reasons, tuple(reasons))


def compare_reference_events(
    reference: Sequence[Mapping], candidate: Sequence[Mapping], *,
    price_tolerance: float = 0.01
) -> dict:
    """Deterministic one-to-one comparison, not a certification process.

    A reference event has tf, side, closeTime, entry, stop, targets (three).
    Every event must match in both directions. A zero-reference/zero-candidate
    sample cannot constitute evidence of signal parity.
    """
    if not isfinite(price_tolerance) or price_tolerance < 0:
        raise ValueError("invalid tolerance")
    def index(events):
        result = {}
        for e in events:
            key = (e["tf"], e["side"], int(e["closeTime"]))
            if key in result:
                raise ValueError("duplicate signal event")
            if e["tf"] not in TF_MS or e["side"] not in {"LONG", "SHORT"}:
                raise ValueError("unsupported signal market dimension")
            prices = (e["entry"], e["stop"], *e["targets"])
            if len(e["targets"]) != 3 or not all(_num(x) > 0 for x in prices):
                raise ValueError("invalid signal prices")
            result[key] = e
        return result
    r, c = index(reference), index(candidate)
    missing = sorted([list(k) for k in r.keys() - c.keys()])
    extra = sorted([list(k) for k in c.keys() - r.keys()])
    discrepancies = []
    for key in sorted(r.keys() & c.keys()):
        a, b = r[key], c[key]
        for name, x, y in [("entry", a["entry"], b["entry"]),
                           ("stop", a["stop"], b["stop"]),
                           *[(f"TP{i}", a["targets"][i-1], b["targets"][i-1]) for i in (1, 2, 3)]]:
            if abs(_num(x) - _num(y)) > price_tolerance:
                discrepancies.append({"event": list(key), "field": name,
                                      "reference": float(x), "candidate": float(y)})
    return {
        "referenceCount": len(r), "candidateCount": len(c),
        "matchingEventCount": len(r.keys() & c.keys()),
        "missing": missing, "extra": extra, "priceDifferences": discrepancies,
        "sampleExactWithinTolerance": bool(r) and not missing and not extra and not discrepancies,
        "originalViprasolVerified": False,
        "reason": "Mechanical sample agreement alone cannot prove full Pine/market-data equivalence",
    }


def readiness_report(macro: Validation, comparison: Mapping) -> dict:
    return {
        "originalViprasolVerified": False,
        "automatedDiscordTradingAlerts": "DISABLED",
        "macroInputsAcceptableForFurtherAudit": macro.acceptable,
        "macroBlockers": list(macro.reasons),
        "sampleExactWithinTolerance": comparison.get("sampleExactWithinTolerance", False),
        "remaining": [
            "Independently prove NQ1! exchange/TradingView data construction",
            "Validate Pine indicator calculations across 15m, 30m, and 1h",
            "Conduct fresh out-of-sample time-aligned signal comparisons",
            "Approve a separately hosted read-only monitoring backend",
        ],
    }
