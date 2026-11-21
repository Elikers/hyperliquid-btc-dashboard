"""Non-repainting ADR14 on fully completed UTC BTC trading days.

Source: Viprasol Pine v6 uses daily SMA(high-low,14)[1] for ADR,
then compares the *current* chart-day range to completed-day ADR.
Historical BTC candle gaps/partial days must not silently enter the mean.
"""
from collections import defaultdict
from datetime import datetime, timezone
from math import isfinite
from research.factors import STEPS, clean

DAY_MS=86400000


def adr_percent_used(candles, *, timeframe="15m", days=14):
    if timeframe not in STEPS or not 2<=days<=100:
        raise ValueError("Invalid ADR settings")
    interval=STEPS[timeframe]
    bars=clean(candles,interval)
    if not bars:
        raise ValueError("No completed BTC candles")
    per_day=DAY_MS//interval
    groups=defaultdict(list)
    for b in bars:
        groups[b["t"]//DAY_MS].append(b)
    today=bars[-1]["t"]//DAY_MS
    past=sorted(day for day in groups if day<today)
    if len(past)<days:
        return {"available":False,"reason":"INSUFFICIENT_COMPLETED_DAYS",
                "adr":None,"usedPercent":None,"exhausted":None}
    chosen=past[-days:]
    if chosen!=list(range(today-days,today)):
        return {"available":False,"reason":"MISSING_TRADING_DAY",
                "adr":None,"usedPercent":None,"exhausted":None}
    ranges=[]
    for day in chosen:
        group=groups[day]
        if len(group)!=per_day or group[0]["t"]!=day*DAY_MS:
            return {"available":False,"reason":"PARTIAL_HISTORICAL_DAY",
                    "adr":None,"usedPercent":None,"exhausted":None}
        ranges.append(max(x["h"] for x in group)-min(x["l"] for x in group))
    mean=sum(ranges)/days
    if not isfinite(mean) or mean<=0:
        return {"available":False,"reason":"INVALID_AVERAGE_DAILY_RANGE",
                "adr":None,"usedPercent":None,"exhausted":None}
    current=groups[today]
    if current[0]["t"]!=today*DAY_MS:
        return {"available":False,"reason":"INCOMPLETE_CURRENT_DAY_OBSERVATION",
                "adr":mean,"usedPercent":None,"exhausted":None}
    used=100*(max(x["h"] for x in current)-min(x["l"] for x in current))/mean
    return {"available":True,"reason":"COMPLETE_CLOSED_DAY_HISTORY",
            "adr":mean,"usedPercent":used,"days":days,
            "todayUtc":datetime.fromtimestamp(today*DAY_MS/1000,timezone.utc).date().isoformat(),
            "dataScope":"UTC Hyperliquid candles; Pine daily-session parity not certified"}
