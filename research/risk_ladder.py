"""Viprasol ATR-based entry SL/TP ladder and stop-first outcome audit.

Research only. A constructed ladder does not imply an approved trade signal.
Based on user's original Pine: ATR14, multiplier 1.5, 1R/2R/3R targets.
"""
from math import isfinite
from research.factors import rma


def atr(closed_bars, length=14):
    if length < 1 or not closed_bars:
        raise ValueError("Insufficient ATR input")
    true_ranges=[]
    for i, b in enumerate(closed_bars):
        high, low, close = (float(b[k]) for k in ("h","l","c"))
        if not all(isfinite(v) for v in (high,low,close)) or high < low:
            raise ValueError("Invalid bar for ATR")
        if i:
            prev_close=float(closed_bars[i-1]["c"])
            if not isfinite(prev_close):
                raise ValueError("Invalid previous close")
            true_ranges.append(max(high-low, abs(high-prev_close),abs(low-prev_close)))
        else:
            true_ranges.append(high-low)
    return rma(true_ranges,length)[-1]


def ladder(entry, side, atr_value, *, multiplier=1.5):
    if side not in ("LONG","SHORT"):
        raise ValueError("Side must be LONG or SHORT")
    if any(not isfinite(float(x)) or float(x)<=0 for x in (entry,atr_value,multiplier)):
        raise ValueError("Entry, ATR, and multiplier must be finite positive")
    risk=float(atr_value)*multiplier
    direction=1 if side=="LONG" else -1
    stop=float(entry)-direction*risk
    targets=[float(entry)+direction*risk*i for i in (1,2,3)]
    if min(stop,*targets)<=0:
        raise ValueError("Ladder crosses zero")
    return {
        "entry":float(entry),"side":side,"risk":risk,
        "stop":stop,"targets":targets,"breakevenAfterTp1":True,
        "researchOnly":True,"discordEligible":False
    }


def audit_outcome(setup, future_closed_bars):
    """Approximate Pine's conservative stop-first OHLC-only trade tracking.

    Skip the entry candle by passing only subsequent bars. A bar that touches
    both stop and TP is assigned SL/BE first; intrabar timing is unknowable.
    """
    side=setup["side"]
    if side not in ("LONG","SHORT"):
        raise ValueError("Invalid trade side")
    stop=setup["stop"]
    targets=setup["targets"]
    entry=setup["entry"]
    tp_hits=[False,False,False]
    breakeven=False
    for number, bar in enumerate(future_closed_bars,1):
        high,low=float(bar["h"]),float(bar["l"])
        if not all(isfinite(x) for x in (high,low)) or low>high:
            raise ValueError("Invalid outcome candle")
        working_stop=entry if breakeven else stop
        stop_hit=low<=working_stop if side=="LONG" else high>=working_stop
        if stop_hit:
            return {"outcome":"BE" if breakeven else "SL",
                    "bars":number,"targetsHit":list(tp_hits),
                    "researchOnly":True}
        for i, level in enumerate(targets):
            if high>=level if side=="LONG" else low<=level:
                tp_hits[i]=True
        if tp_hits[0]:
            breakeven=True
        if all(tp_hits):
            return {"outcome":"TP3","bars":number,"targetsHit":list(tp_hits),
                    "researchOnly":True}
    return {"outcome":"OPEN","bars":len(future_closed_bars),
            "targetsHit":tp_hits,"researchOnly":True}
