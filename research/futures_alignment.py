"""Time-aware futures/BTC research joining, never certified TradingView parity.

Compute NQ EMA on native CME bars before merging onto BTC candles.
CME weekend/holiday gaps are valid; BTC continues trading during them.
"""
from bisect import bisect_right
from math import isfinite
from research.factors import STEPS, clean, ema


def _native_cme_bars(candles, step):
    parsed, last = [], None
    if not candles:
        raise ValueError("Empty native futures bars")
    for raw in candles:
        t, end = int(raw["t"]), int(raw["T"])
        row = {k: float(raw[k]) for k in ("o","h","l","c","v")}
        if (t < 0 or t % step or end != t + step - 1
                or any(not isfinite(v) for v in row.values())
                or row["v"] < 0 or row["h"] < max(row["o"],row["c"],row["l"])
                or row["l"] > min(row["o"],row["c"],row["h"])):
            raise ValueError("Invalid native CME candle")
        if last is not None and t <= last:
            raise ValueError("Out-of-order or duplicate futures candle")
        parsed.append({**row,"t":t,"T":end})
        last = t
    return parsed


def align_native_nq_to_btc(btc_candles, native_nq_candles, *,
                           timeframe="15m", macro_ema_length=21,
                           current_ms=None, max_age_intervals=96):
    """Join only previously closed NQ bars to BTC; stale data becomes None.

    The age ceiling is a research safety policy, NOT a TradingView setting.
    Real source roll/session configuration and Pine barmerge remain unverified.
    """
    if timeframe not in STEPS:
        raise ValueError("Unsupported timeframe")
    if macro_ema_length < 2 or max_age_intervals < 1:
        raise ValueError("Invalid alignment settings")
    step = STEPS[timeframe]
    btc = clean(btc_candles,step)
    nq = _native_cme_bars(native_nq_candles,step)
    if current_ms is not None:
        if not isinstance(current_ms,int) or current_ms < 0:
            raise ValueError("Invalid current time")
        if any(b["T"] >= current_ms for b in btc):
            raise ValueError("Unclosed BTC bar supplied")
        nq = [bar for bar in nq if bar["T"] < current_ms]
        if not nq:
            raise ValueError("No closed futures history")
    native_ema = ema([row["c"] for row in nq],macro_ema_length)
    times = [row["T"] for row in nq]
    aligned_close, aligned_ema, matched_times, ages = [], [], [], []
    for b in btc:
        i = bisect_right(times,b["T"]) - 1
        age = b["T"] - times[i] if i >= 0 else None
        eligible = i >= 0 and age is not None and age <= max_age_intervals*step
        aligned_close.append(nq[i]["c"] if eligible else None)
        aligned_ema.append(native_ema[i] if eligible else None)
        matched_times.append(times[i] if eligible else None)
        ages.append(age if eligible else None)
    return {
        "timeframe":timeframe,"macroClose":aligned_close,
        "macroEma":aligned_ema,"matchedNativeCloseMs":matched_times,
        "macroAgeMs":ages,
        "missingCount":sum(x is None for x in aligned_close),
        "nativeFuturesBars":len(nq),
        "sourceVerified":False,"tradingviewBarmergeVerified":False,
        "reason":"Research-only alignment; CME roll and Pine barmerge parity unverified",
    }
