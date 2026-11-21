"""Diagnose ATR14 stop differences without fitting the strategy to screenshots.

Given a trusted closed-candle CSV and reference entry/stop, compare ATR
recomputed with multiple earlier warmup windows. This cannot establish
TradingView OHLC/ATR parity without matching independent source candles.
"""
import argparse
import csv
import json
from math import isfinite

from research.risk_ladder import atr


def audit_atr_warmup(candles, *, entry, reference_stop, side,
                     multiplier=1.5, length=14, start_indices=(0, 100, 300, 500)):
    """Recalculate stop with alternative EMA/RMA seeding windows."""
    if side not in ("LONG", "SHORT"):
        raise ValueError("Invalid trade direction")
    if not all(isfinite(float(v)) for v in (entry,reference_stop,multiplier)):
        raise ValueError("Nonfinite stop inputs")
    if float(multiplier)<=0 or length<1:
        raise ValueError("Invalid ATR parameters")
    if len(candles)<length:
        raise ValueError("Insufficient candles")
    direction=1 if side=="LONG" else -1
    if direction*(float(entry)-float(reference_stop))<=0:
        raise ValueError("Stop is on the wrong side of entry")
    results=[]
    for start in start_indices:
        if not isinstance(start,int) or start<0 or start>=len(candles):
            raise ValueError("Invalid seed start")
        selected=candles[start:]
        if len(selected)<length:
            continue
        a=atr(selected,length=length)
        if a is None:
            continue
        stop=float(entry)-direction*float(multiplier)*a
        results.append({"startIndex":start,"warmupBars":len(selected),
                        "atr":a,"researchStop":stop,
                        "stopMinusReference":stop-float(reference_stop)})
    if not results or results[0]["startIndex"]!=0:
        raise ValueError("Full-history ATR reference required")
    baseline=results[0]["researchStop"]
    longest=max(abs(row["researchStop"]-baseline) for row in results)
    return {
        "kind":"closed_bar_atr_seed_sensitivity",
        "side":side,"entry":float(entry),
        "displayedReferenceStop":float(reference_stop),
        "lookbackCandles":len(candles),"length":length,
        "multiplier":float(multiplier),"scenarios":results,
        "maxSeedShift":longest,
        "baselineStopGap":baseline-float(reference_stop),
        "inputSourceParityVerified":False,
        "originalViprasolVerified":False,
        "discordEligible":False,
        "interpretation":"A small seed effect does not prove matching exchange/history/indicator settings",
    }


def main():
    parser=argparse.ArgumentParser(description="Research-only ATR reference check")
    parser.add_argument("--csv",required=True)
    parser.add_argument("--timeframe",default="15m")
    parser.add_argument("--bar-open-ms",required=True,type=int)
    parser.add_argument("--entry",required=True,type=float)
    parser.add_argument("--stop",required=True,type=float)
    parser.add_argument("--side",required=True,choices=("LONG","SHORT"))
    args=parser.parse_args()
    with open(args.csv,newline="",encoding="utf-8") as f:
        entries=[row for row in csv.DictReader(f)
                 if row["timeframe"]==args.timeframe
                 and int(row["t"])<=args.bar_open_ms]
    if not entries or int(entries[-1]["t"])!=args.bar_open_ms:
        raise ValueError("Reference bar absent")
    steps={"15m":900000,"30m":1800000,"1h":3600000}
    step=steps[args.timeframe]
    if any(int(b["t"])-int(a["t"])!=step for a,b in zip(entries,entries[1:])):
        raise ValueError("Gaps in supplied closed candles")
    candles=[{"h":float(row["high"]),"l":float(row["low"]),
              "c":float(row["close"])} for row in entries]
    print(json.dumps(audit_atr_warmup(candles,entry=args.entry,
        reference_stop=args.stop,side=args.side),indent=2))


if __name__=="__main__":
    main()
