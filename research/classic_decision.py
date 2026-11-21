"""Faithful *decision gates* from the supplied Viprasol Pine v6, research only.

Inputs are independently computed, closed-bar Pine-equivalent factors.
This module does NOT calculate RSI, MACD, VWAP, DMI, ATR, macro feeds,
request.security alignment, or broker execution. Never send its output to Discord.
"""
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from math import isfinite

FACTORS = ("vwap", "rsi", "macd", "ema", "adx", "volume", "confirmation_rsi", "macro")
TIMEFRAMES = ("15m", "30m", "1h")


@dataclass(frozen=True)
class Context:
    timeframe: str
    symbol_verified: bool
    candle_closed: bool
    bar_open_ms: int
    macro_provenance_verified: bool
    macro_factor_enabled: bool = True
    min_score: int = 5
    confluence_enabled: bool = True
    session_filter_enabled: bool = True
    block_weekends: bool = True
    adr_filter_enabled: bool = True
    adr_percent_used: float | None = None
    adr_block_at_percent: float = 100.0


def evaluate(
    *,
    previous_fast: float,
    previous_slow: float,
    fast: float,
    slow: float,
    bull_factors: dict[str, bool],
    bear_factors: dict[str, bool],
    context: Context,
) -> dict:
    """Return an explainable research decision that always blocks live delivery.

    The original indicator only enters on a NEW EMA9/21 crossover on bar close,
    with confluence and gates. Scores alone NEVER create a trade.
    """
    missing = [name for name in FACTORS if name not in bull_factors or name not in bear_factors]
    if missing:
        raise ValueError("Missing mandatory factors: " + ", ".join(missing))
    for values in (previous_fast, previous_slow, fast, slow):
        if not isfinite(float(values)):
            raise ValueError("EMA must be finite")
    if context.timeframe not in TIMEFRAMES:
        raise ValueError("Unsupported timeframe")
    if not 1 <= context.min_score <= (8 if context.macro_factor_enabled else 7):
        raise ValueError("Invalid confluence threshold")
    if context.bar_open_ms < 0:
        raise ValueError("Invalid candle open timestamp")
    active = FACTORS if context.macro_factor_enabled else FACTORS[:-1]
    for name in FACTORS:
        if not isinstance(bull_factors[name], bool) or not isinstance(bear_factors[name], bool):
            raise ValueError("Factors must be explicit booleans")
    bull = sum(bull_factors[k] for k in active)
    bear = sum(bear_factors[k] for k in active)
    crossed_up = fast > slow and previous_fast <= previous_slow
    crossed_down = fast < slow and previous_fast >= previous_slow
    raw = "LONG" if crossed_up else "SHORT" if crossed_down else None
    score = bull if raw == "LONG" else bear
    problems = []
    if not context.candle_closed:
        problems.append("CANDLE_NOT_CLOSED")
    if not context.symbol_verified:
        problems.append("BTC_SYMBOL_UNVERIFIED")
    if context.macro_factor_enabled and not context.macro_provenance_verified:
        problems.append("NQ1_MACRO_UNVERIFIED")
    local = datetime.fromtimestamp(context.bar_open_ms / 1000, ZoneInfo("America/New_York"))
    minutes = local.hour * 60 + local.minute
    if context.session_filter_enabled and not (180 <= minutes < 720 or 480 <= minutes < 1020):
        problems.append("OUTSIDE_EU_US_SESSION")
    if context.block_weekends and local.weekday() >= 5:
        problems.append("WEEKEND")
    if context.adr_filter_enabled and context.adr_percent_used is not None:
        if not isfinite(context.adr_percent_used) or context.adr_percent_used < 0:
            problems.append("INVALID_ADR")
        elif context.adr_percent_used >= context.adr_block_at_percent:
            problems.append("ADR_EXHAUSTED")
    if context.confluence_enabled and raw and score < context.min_score:
        problems.append("INSUFFICIENT_CONFLUENCE")
    if not raw:
        problems.append("NO_NEW_EMA_CROSS")
    candidate = raw if not problems else None
    return {
        "timeframe": context.timeframe,
        "rawCrossover": raw,
        "bullScore": bull,
        "bearScore": bear,
        "factorTotal": len(active),
        "candidate": candidate,
        "reasons": problems,
        "researchOnly": True,
        "originalViprasolVerified": False,
        "discordEligible": False,
        "discordReason": "Full source/input parity and licensed NQ1! feed remain unverified",
    }
