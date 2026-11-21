"""No-lookahead native CME futures eight-factor *research preview*.

Combines separately computed native NQ EMA and BTC seven factors, without
fabricating futures bars or mistaking a third-party proxy for CME_MINI:NQ1!.
Neither the supplied vendor flag nor result can certify Pine equivalence.
"""
from research.factors import STEPS, clean, compute_seven_factors
from research.futures_alignment import align_native_nq_to_btc
from research.macro_factor import macro_factor
from research.classic_decision import Context, evaluate
from research.risk_ladder import atr, ladder


def preview_native_nq(btc_candles, confirm_15m_candles, native_nq_candles,
                      *, timeframe, current_ms, macro_source_verified=False,
                      maximum_age_intervals=96):
    if timeframe not in STEPS:
        raise ValueError("Unsupported timeframe")
    btc = clean([b for b in btc_candles if int(b["T"]) < current_ms],
                STEPS[timeframe])
    confirmed = [b for b in confirm_15m_candles if int(b["T"]) < current_ms]
    seven = compute_seven_factors(btc,confirmed,timeframe=timeframe)
    alignment=align_native_nq_to_btc(
        btc,native_nq_candles,timeframe=timeframe,
        current_ms=current_ms,max_age_intervals=maximum_age_intervals)
    macro=macro_factor(
        [bar["c"] for bar in btc],alignment["macroClose"],
        alignment["macroEma"],source_verified=macro_source_verified)
    bulls={**seven["bullFactors"],"macro":macro["bull"]}
    bears={**seven["bearFactors"],"macro":macro["bear"]}
    decision=evaluate(
        previous_fast=seven["previousFast"],
        previous_slow=seven["previousSlow"],
        fast=seven["fast"],slow=seven["slow"],
        bull_factors=bulls,bear_factors=bears,
        context=Context(
            timeframe=timeframe,symbol_verified=True,
            candle_closed=True,bar_open_ms=btc[-1]["t"],
            macro_provenance_verified=macro_source_verified))
    setup=None
    if decision["candidate"]:
        a=atr(btc)
        if a is not None and a>0:
            setup=ladder(btc[-1]["c"],decision["candidate"],a)
    return {
        "timeframe":timeframe,"closedThroughMs":btc[-1]["T"],
        "sevenBullScore":seven["bullScoreSeven"],
        "sevenBearScore":seven["bearScoreSeven"],
        "macro":macro,"macroAlignment":{
            "missingCount":alignment["missingCount"],
            "nativeFuturesBars":alignment["nativeFuturesBars"],
            "ageMsLast":alignment["macroAgeMs"][-1],
            "tradingviewBarmergeVerified":False,
        },
        "decision":decision,"hypotheticalRiskLadder":setup,
        "originalViprasolVerified":False,"discordEligible":False,
        "automaticTrading":False,
        "limitations":[
            "CME continuous contract roll construction unverified",
            "Historical Pine request.security barmerge equivalence unverified",
            "VWAP/session and TradingView BTC candle parity unverified",
            "No independent all-timeframe out-of-sample signal certification",
        ],
    }
