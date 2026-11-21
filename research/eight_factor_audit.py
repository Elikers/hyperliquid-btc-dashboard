"""End-to-end eight-factor AUDIT (not Pine parity and not trade execution).

Inputs MUST be pre-aligned, already-closed bars with separately provided
NQ1! EMA computed on that exchange's bars BEFORE alignment/forward filling.
Never use this output for Discord; the pipeline hardcodes a denial.
"""
from dataclasses import replace
from research.factors import STEPS, clean, compute_seven_factors
from research.classic_decision import Context, evaluate
from research.macro_factor import macro_factor
from research.risk_ladder import atr, ladder


def audit_eight_factors(btc, confirm15m, aligned_nq_bars, aligned_nq_ema,
                        *, timeframe, current_ms, macro_source_verified=False,
                        macro_mode="positive", corr_length=20, corr_threshold=.3):
    if timeframe not in STEPS:
        raise ValueError("Invalid timeframe")
    if not isinstance(current_ms, int) or current_ms < 0:
        raise ValueError("Invalid clock")
    step = STEPS[timeframe]
    closed_btc=[x for x in btc if int(x["T"]) < current_ms]
    closed_15m=[x for x in confirm15m if int(x["T"]) < current_ms]
    # Data deliberately passes through the same checks as the seven-factor
    # engine. A missing NQ1! bar is NOT made up with a proxy.
    c=clean(closed_btc,step)
    n=clean(aligned_nq_bars,step)
    if not c or len(c)!=len(n) or len(c)!=len(aligned_nq_ema):
        raise ValueError("Missing, extra, or mismatched Nasdaq bars")
    if any(x["t"]!=y["t"] or x["T"]!=y["T"] for x,y in zip(c,n)):
        raise ValueError("Nasdaq timestamps do not align with BTC bars")
    if n[-1]["T"]>=current_ms:
        raise ValueError("Macro candle not yet closed")
    seven=compute_seven_factors(c,closed_15m,timeframe=timeframe)
    nq=[x["c"] for x in n]
    macro=macro_factor([x["c"] for x in c],nq,aligned_nq_ema,
                       length=corr_length,threshold=corr_threshold,
                       link_mode=macro_mode,source_verified=macro_source_verified)
    bullish={**seven["bullFactors"],"macro":macro["bull"]}
    bearish={**seven["bearFactors"],"macro":macro["bear"]}
    ctx=Context(
        timeframe=timeframe,symbol_verified=True,candle_closed=True,
        bar_open_ms=c[-1]["t"],macro_provenance_verified=macro_source_verified,
    )
    decision=evaluate(
        previous_fast=seven["previousFast"],previous_slow=seven["previousSlow"],
        fast=seven["fast"],slow=seven["slow"],bull_factors=bullish,
        bear_factors=bearish,context=ctx)
    setup=None
    if decision["candidate"]:
        # No full parity claim: candidate is hypothetical, even if macro source
        # was user-claimed 'verified'.
        volatility=atr(c,14)
        if volatility:
            setup=ladder(c[-1]["c"],decision["candidate"],volatility)
    return {
        "symbol":"HYPERLIQUID:BTCUSDC.P",
        "timeframe":timeframe,
        "barCloseMs":c[-1]["T"],
        "factorVotesBull":bullish,
        "factorVotesBear":bearish,
        "bullScore":sum(bullish.values()),
        "bearScore":sum(bearish.values()),
        "macro":macro,
        "decision":decision,
        "hypotheticalRiskLadder":setup,
        "originalViprasolVerified":False,
        "discordEligible":False,
        "automaticTrading":False,
        "limitations":[
            "NQ1! TradingView continuous contract/roll construction unverified",
            "NQ1! request.security exchange-bar EMA/merge unverified",
            "BTC TradingView OHLC/VWAP/MTF calculation parity unverified",
            "No independent exact reference-signal comparison on all timeframes",
        ],
    }
