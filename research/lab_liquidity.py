"""BTC-only experimental liquidity-sweep entry trigger and next-open paper fills.

Does not modify Classic signal rules, alerts, dashboard, or wallet execution.
A confirmed swing is recognized only AFTER its right-hand bars close.
"""
from datetime import datetime
from math import isfinite
from zoneinfo import ZoneInfo

from research.factors import STEPS, compute_seven_factors, clean
from research.adr_gate import adr_percent_used
from research.risk_ladder import atr, ladder
from research.backtest_real_btc_snapshot import _exit_simulation

SWING_LEFT = 3
SWING_RIGHT = 3
MAX_PIVOT_AGE = 48
COSTS = ("0", "7", "15")


def confirmed_sweep(bars):
    """Return direction, prior *confirmed* swing level, or (None,None).

    Pivot at k can be used only at i>=k+SWING_RIGHT. The signal bar
    cannot itself be used to define the pivot. No future-bar leakage.
    """
    if len(bars) < MAX_PIVOT_AGE+SWING_RIGHT+SWING_LEFT+2:
        return None, None
    i=len(bars)-1
    # Only newest confirmed pivot per side; no hindsight center selection.
    piv_hi=piv_lo=None
    for k in range(max(SWING_LEFT,i-MAX_PIVOT_AGE),i-SWING_RIGHT+1):
        center=bars[k]
        surrounding=bars[k-SWING_LEFT:k]+bars[k+1:k+SWING_RIGHT+1]
        if all(center["h"]>b["h"] for b in surrounding):
            piv_hi=(k,center["h"])
        if all(center["l"]<b["l"] for b in surrounding):
            piv_lo=(k,center["l"])
    last=bars[-1]
    high_reject=(piv_hi is not None and last["h"]>piv_hi[1] and
                 last["c"]<piv_hi[1] and last["o"]<=piv_hi[1] and
                 max(b["h"] for b in bars[piv_hi[0]+1:-1])<=piv_hi[1])
    low_reclaim=(piv_lo is not None and last["l"]<piv_lo[1] and
                 last["c"]>piv_lo[1] and last["o"]>=piv_lo[1] and
                 min(b["l"] for b in bars[piv_lo[0]+1:-1])>=piv_lo[1])
    if high_reject and low_reclaim:
        return None,None  # Ambiguous same-bar reversal; no intrabar order
    if high_reject:
        return "SHORT",piv_hi[1]
    if low_reclaim:
        return "LONG",piv_lo[1]
    return None,None


def lab_entry(bars, confirmation, *, timeframe):
    """One swap: EMA crossover *trigger* -> confirmed swing sweep/reclaim.

    Seven factors, score 5, ADR14, and original session/weekend/ATR gates
    remain identical in definition to research Classic Macro-Off.
    """
    if timeframe not in STEPS or not bars:
        raise ValueError("Unsupported timeframe or empty bars")
    direction,level=confirmed_sweep(bars)
    if direction is None:
        return None
    end=bars[-1]["T"]
    factors=compute_seven_factors(bars,confirmation,timeframe=timeframe)
    score=factors["bullScoreSeven"] if direction=="LONG" else factors["bearScoreSeven"]
    if score<5:
        return None
    local=datetime.fromtimestamp(bars[-1]["t"]/1000, ZoneInfo("America/New_York"))
    minute=local.hour*60+local.minute
    if local.weekday()>=5 or not (180<=minute<720 or 480<=minute<1020):
        return None
    adr=adr_percent_used(bars,timeframe=timeframe,days=14)
    if not adr["available"] or adr["usedPercent"]>=100:
        return None
    value=atr(bars,14)
    if value is None or not isfinite(value) or value<=0:
        return None
    levels=ladder(bars[-1]["c"],direction,value)
    return {
        "timeframe":timeframe,"closedBarEndMs":end,"side":direction,
        "confirmedPivotLevel":level,"factorScoreSeven":score,
        "hypotheticalRiskLadder":levels,
        "researchOnly":True,"originalViprasolVerified":False,
        "discordEligible":False,"automaticTrading":False,
    }


def next_open_stress(side, levels, next_bars, *, adverse_entry_bps=3):
    """Fixed signal-time stop/TP levels; next-open + adverse fill slippage.

    Additional 0/7/15 bps one-way *cost sensitivity* in original simulator.
    A fill already outside planned stop/TP3 is quarantined, not scored as
    a favorable or executable trade. No order-book execution is inferred.
    """
    if not next_bars or side not in ("LONG","SHORT"):
        return {"status":"UNRESOLVED","netRByOneWayCostBps":None}
    if adverse_entry_bps<0 or not isfinite(adverse_entry_bps):
        raise ValueError("Invalid entry slippage")
    sign=1 if side=="LONG" else -1
    opened=next_bars[0]["o"]
    fill=opened*(1+sign*adverse_entry_bps/10000)
    stop=levels["stop"]
    tp3=levels["targets"][-1]
    if not (stop<fill<tp3 if sign==1 else tp3<fill<stop):
        return {"status":"ENTRY_OUTSIDE_LADDER","netRByOneWayCostBps":None}
    shifted={"hypotheticalDirection":side,
             "hypotheticalRiskLadder":{**levels,"entry":fill}}
    outcome=_exit_simulation(shifted,next_bars)
    return {"status":outcome["status"],"fillPrice":fill,
            "signalClose":levels["entry"],"nextOpen":opened,
            "netRByOneWayCostBps":outcome["oneWayCostsNetR"],
            "grossR":outcome["grossR"],"barsHeld":outcome["barsHeld"]}


def summarize_paper(records):
    out={}
    for tf in STEPS:
        subset=[r for r in records if r["timeframe"]==tf]
        out[tf]={}
        for engine in ("Classic","LiquidityLab"):
            rows=[x[engine] for x in subset if x.get(engine) is not None]
            done=[x for x in rows if x["netRByOneWayCostBps"] is not None]
            out[tf][engine]={
                "candidates":len(rows),"resolved":len(done),
                "unresolvedOrUnfillable":len(rows)-len(done),
                "netRSumByOneWayCostBps":{
                    cost:sum(d["netRByOneWayCostBps"][cost] for d in done)
                    for cost in COSTS},
            }
    return out
