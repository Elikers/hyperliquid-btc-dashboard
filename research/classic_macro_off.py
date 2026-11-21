"""Viprasol source-supported Classic configuration: macro factor OFF.

Original Pine v6 input macroFactorOnInput=false gives 7-factor scoring
and minScoreEff=min(minScoreInput,7). Unlike BTC-only experimental Lab,
this path also enforces the original EMA-cross, session, weekend and
ADR14 gates. No TradingView data or exact parity certification is implied.
"""
from research.factors import STEPS, clean, compute_seven_factors
from research.classic_decision import Context, evaluate
from research.adr_gate import adr_percent_used
from research.risk_ladder import atr, ladder


def evaluate_classic_macro_off(btc_candles, confirm_15m_candles, *,
                               timeframe, current_ms, min_score=5):
    if timeframe not in STEPS:
        raise ValueError("Unsupported timeframe")
    if not isinstance(current_ms,int) or current_ms<=0:
        raise ValueError("Invalid current time")
    closed=clean([b for b in btc_candles if int(b["T"]) < current_ms],
                 STEPS[timeframe])
    confirm=[b for b in confirm_15m_candles if int(b["T"]) < current_ms]
    factors=compute_seven_factors(closed,confirm,timeframe=timeframe)
    adr=adr_percent_used(closed,timeframe=timeframe,days=14)
    bull={**factors["bullFactors"],"macro":False}
    bear={**factors["bearFactors"],"macro":False}
    decision=evaluate(
        previous_fast=factors["previousFast"],
        previous_slow=factors["previousSlow"],
        fast=factors["fast"],slow=factors["slow"],
        bull_factors=bull,bear_factors=bear,
        context=Context(
            timeframe=timeframe,candle_closed=True,symbol_verified=True,
            macro_provenance_verified=False,macro_factor_enabled=False,
            min_score=min_score,bar_open_ms=closed[-1]["t"],
            adr_filter_enabled=True,adr_percent_used=adr["usedPercent"]))
    reasons=list(decision["reasons"])
    # The Pine source ignores unavailable ADR, but for a *claim of proven*
    # signal parity we reject incomplete market history rather than guess.
    candidate=decision["candidate"]
    if not adr["available"]:
        reasons.append("ADR_INPUT_NOT_VERIFIED")
        candidate=None
    risk=None
    if candidate:
        value=atr(closed,14)
        if value is not None and value>0:
            risk=ladder(closed[-1]["c"],candidate,value)
    return {
        "configuration":"VIPRASOL_CLASSIC_MACRO_OFF",
        "sourceSupportedSetting":"macroFactorOnInput = false",
        "timeframe":timeframe,"closedThroughMs":closed[-1]["T"],
        "scoreDenominator":7,"scoreThreshold":min_score,
        "bullScore":factors["bullScoreSeven"],
        "bearScore":factors["bearScoreSeven"],
        "adr":adr,"rawCrossover":decision["rawCrossover"],
        "hypotheticalDirection":candidate,
        "hypotheticalRiskLadder":risk,
        "reasons":reasons,"nasdaqFeedRequired":False,
        "originalViprasolVerified":False,"discordEligible":False,
        "automaticTrading":False,
        "limitations":[
            "Source supports macro OFF, but computed 7-factor Pine equivalence unverified",
            "UTC Hyperliquid VWAP/day sessions versus Pine not certified",
            "Pine lower-timeframe security merge and ATR parity unverified",
            "Independent 15m/30m/1h signal and fee-adjusted forward validation pending",
        ],
    }
