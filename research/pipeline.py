"""Research-only adapter: seven computed inputs -> original Viprasol entry gates.

The macro factor is always explicitly unavailable; no NQ1! approximation.
No trading calls and NO Discord delivery.
"""
from dataclasses import dataclass
from time import time
from research.factors import compute_seven_factors, FACTOR_NAMES
from research.classic_decision import Context, evaluate


def calculate_research_candidate(btc_candles, confirm_15m_candles, *,
                                 timeframe, current_ms=None):
    if current_ms is None:
        current_ms = int(time()*1000)
    if not btc_candles:
        raise ValueError("No BTC candles")
    # Input candles must be closed; the current unfinished candle is excluded.
    closed = [b for b in btc_candles if int(b["T"]) < current_ms]
    confirmed = [b for b in confirm_15m_candles if int(b["T"]) < current_ms]
    if not closed or not confirmed:
        raise ValueError("No closed candles")
    values = compute_seven_factors(closed, confirmed, timeframe=timeframe)
    bulls = {**values["bullFactors"], "macro": False}
    bears = {**values["bearFactors"], "macro": False}
    context = Context(
        timeframe=timeframe,
        symbol_verified=True,
        candle_closed=True,
        bar_open_ms=int(closed[-1]["t"]),
        macro_provenance_verified=False,
        macro_factor_enabled=True,
    )
    decision = evaluate(
        previous_fast=values["previousFast"],
        previous_slow=values["previousSlow"],
        fast=values["fast"],
        slow=values["slow"],
        bull_factors=bulls,
        bear_factors=bears,
        context=context,
    )
    # Even a calculated candidate can never be used as a real trade alert.
    if decision["candidate"] is not None or decision["discordEligible"]:
        raise RuntimeError("Research pipeline failed to block unverified macro")
    return {
        "timeframe": timeframe,
        "closedThrough": values["barCloseMs"],
        "bullScoreSeven": values["bullScoreSeven"],
        "bearScoreSeven": values["bearScoreSeven"],
        "rawCrossover": decision["rawCrossover"],
        "researchDecision": decision,
        "discordEligible": False,
        "automaticTrading": False,
        "originalViprasolVerified": False,
        "status": "BLOCKED_UNVERIFIED_NQ1_AND_TV_PARITY",
    }
