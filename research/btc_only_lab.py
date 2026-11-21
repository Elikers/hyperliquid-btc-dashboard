"""BTC-only seven-factor Lab candidate, not original Viprasol Classic.

The original source defaults to 8/8 factor scoring with CME NQ1!. This
explicitly different seven-factor Lab mode removes that dependency and
remains strictly paper research; it can never send Discord trade alerts.
"""
from research.factors import STEPS, clean, compute_seven_factors
from research.classic_decision import Context, evaluate
from research.risk_ladder import atr, ladder


def evaluate_btc_only_lab(btc_candles, confirm_15m_candles, *,
                          timeframe, current_ms, threshold=5):
    if timeframe not in STEPS:
        raise ValueError("Unsupported timeframe")
    if not isinstance(current_ms,int) or current_ms <= 0:
        raise ValueError("Invalid current time")
    bars=clean([b for b in btc_candles if int(b["T"]) < current_ms],
               STEPS[timeframe])
    confirm=[b for b in confirm_15m_candles if int(b["T"]) < current_ms]
    data=compute_seven_factors(bars,confirm,timeframe=timeframe)
    bullish={**data["bullFactors"],"macro":False}
    bearish={**data["bearFactors"],"macro":False}
    gate=evaluate(
        previous_fast=data["previousFast"],previous_slow=data["previousSlow"],
        fast=data["fast"],slow=data["slow"],
        bull_factors=bullish,bear_factors=bearish,
        context=Context(
            timeframe=timeframe,symbol_verified=True,candle_closed=True,
            bar_open_ms=bars[-1]["t"],macro_provenance_verified=False,
            macro_factor_enabled=False,min_score=threshold,
            # Lab deliberately disables ADR until daily-source parity is
            # implemented; never represent its decision as original Classic.
            adr_filter_enabled=False))
    suggestion=gate["candidate"]
    risk=None
    if suggestion:
        a=atr(bars)
        if a is not None and a>0:
            risk=ladder(bars[-1]["c"],suggestion,a)
    return {
        "model":"BTC_ONLY_LAB_SEVEN_FACTOR",
        "timeframe":timeframe,"barCloseMs":bars[-1]["T"],
        "bullScore":data["bullScoreSeven"],
        "bearScore":data["bearScoreSeven"],
        "scoreDenominator":7,"threshold":threshold,
        "rawCrossover":gate["rawCrossover"],
        "hypotheticalDirection":suggestion,
        "hypotheticalRiskLadder":risk,
        "reasons":gate["reasons"],
        "dataStatus":"RESEARCH_UNVERIFIED",
        "adrFilter":"DISABLED_IN_LAB_UNTIL_DAILY_DATA_AUDIT",
        "nasdaqFactor":"NOT_USED",
        "originalViprasolVerified":False,
        "discordEligible":False,
        "automaticTrading":False,
        "limitations":[
            "Independent BTC-only model, not 8-factor Viprasol Classic",
            "UTC-day VWAP and higher-timeframe merge are unverified",
            "ADR disabled in Lab; historical performance unverified",
            "No fee/slippage-adjusted forward profitability evidence",
        ],
    }
