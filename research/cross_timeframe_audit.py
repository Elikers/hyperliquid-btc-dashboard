"""Fail-closed cross-timeframe Hyperliquid BTC OHLCV reconstruction.

Rebuild fully-covered 30m/1h candles from four/two contiguous 15m bars.
Partial nonoverlap at history edges is excluded. Research-only; no alerts.
"""
from math import isclose, isfinite

STEP_MS=900000
MULTIPLES={"30m":2,"1h":4}
FIELDS=("o","h","l","c","v")


def _normalize(rows,interval):
    result={}
    previous=None
    for raw in rows:
        t,end=int(raw["t"]),int(raw["T"])
        values={k:float(raw[k]) for k in FIELDS}
        if t%interval or end!=t+interval-1:
            raise ValueError("Misaligned candle timestamp")
        if previous is not None and t!=previous+interval:
            raise ValueError("Duplicate or missing candle")
        if not all(isfinite(x) for x in values.values()) or values["v"]<0:
            raise ValueError("Nonfinite OHLCV/negative volume")
        if values["h"]<max(values["o"],values["c"],values["l"]) or values["l"]>min(values["o"],values["c"],values["h"]):
            raise ValueError("Invalid candle OHLC")
        result[t]=values
        previous=t
    return result


def audit_cross_timeframe(candles,*,min_complete_per_timeframe=20,
                          price_tolerance=1e-6,volume_tolerance=1e-5):
    """Compare candles; an OK result never certifies original Pine parity."""
    if min_complete_per_timeframe<1 or price_tolerance<0 or volume_tolerance<0:
        raise ValueError("Invalid audit thresholds")
    if set(candles)!={"15m","30m","1h"}:
        raise ValueError("Exactly 15m, 30m, and 1h candles required")
    normalized={tf:_normalize(candles[tf],STEP_MS*MULTIPLES.get(tf,1))
                for tf in ("15m","30m","1h")}
    base=normalized["15m"]
    passed=True
    detail={}
    for tf,multiple in MULTIPLES.items():
        complete=0
        partial=0
        mismatches=[]
        for t,actual in normalized[tf].items():
            sub=[base.get(t+i*STEP_MS) for i in range(multiple)]
            if any(bar is None for bar in sub):
                partial+=1
                continue
            complete+=1
            calc={"o":sub[0]["o"],"h":max(b["h"] for b in sub),
                  "l":min(b["l"] for b in sub),"c":sub[-1]["c"],
                  "v":sum(b["v"] for b in sub)}
            for field,predicted in calc.items():
                tolerance=volume_tolerance if field=="v" else price_tolerance
                if not isclose(predicted,actual[field],rel_tol=1e-10,abs_tol=tolerance):
                    mismatches.append({"start_ms":t,"field":field,
                        "aggregated":predicted,"provided":actual[field]})
        tf_ok=complete>=min_complete_per_timeframe and not mismatches
        passed=passed and tf_ok
        detail[tf]={"complete_groups":complete,"partial_or_nonoverlap":partial,
            "mismatch_count":len(mismatches),"examples":mismatches[:10],
            "minimum_required":min_complete_per_timeframe,"passed":tf_ok}
    return {"kind":"cross_timeframe_ohlcv_reconstruction","passed":bool(passed),
        "timeframes":detail,"source":"Hyperliquid BTC 15m/30m/1h closed candles",
        "research_only":True,"viprasol_parity_verified":False,
        "discord_eligible":False}
