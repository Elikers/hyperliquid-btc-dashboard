"""Strictly non-overlapping HISTORICAL-ONLY Hyperliquid BTC holdout attempt.

All candidate rules stay frozen. If the public candle API cannot serve enough
old contiguous bars, report NOT_AVAILABLE and refuse any inference.
Never identify reconstructed past candles as true forward observations.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from research.capture_public_btc import make_request
from research.factors import STEPS, clean
from research.instant_paper_comparison import compare_historical_paper

# Predeclared, before running this holdout. Prior tested snapshot started
# around 2026-10-25 21:30 UTC, so even holdout exit observations end before
# 2026-10-25 00:00 UTC: no overlapping OHLC input or trade lifecycle.
HOLDOUT_END_MS = 1792886400000  # 2026-10-25T00:00:00Z
BARS = {"15m":2200, "30m":1100, "1h":550}
SOURCE = "Hyperliquid official public candleSnapshot API"


def build_holdout_snapshots(*, acquired_ms=None, fetch=make_request):
    acquired_ms = int(time.time()*1000) if acquired_ms is None else int(acquired_ms)
    if acquired_ms <= HOLDOUT_END_MS + 86400000:
        raise ValueError("Holdout must be strictly historical at acquisition")
    stamp = datetime.fromtimestamp(acquired_ms/1000, timezone.utc).isoformat()
    snapshots = {}
    for tf, step in STEPS.items():
        end = HOLDOUT_END_MS
        start = end - step*BARS[tf]
        response = fetch({"type":"candleSnapshot","req":{
            "coin":"BTC","interval":tf,"startTime":start,"endTime":end}})
        if not isinstance(response, list):
            raise ValueError(f"{tf} exchange response is not candle array")
        # Request returns may include bars outside requested range; exclude
        # those explicitly, and verify exact chronological continuity.
        history = sorted([b for b in response
                          if start <= int(b["t"]) and int(b["T"]) < end],
                         key=lambda b:int(b["t"]))
        if len(history) != BARS[tf]:
            raise ValueError(f"{tf} historical non-overlap window unavailable: "
                             f"received {len(history)}/{BARS[tf]} closed bars")
        cleaned = clean(history, step)
        if cleaned[0]["t"] != start or cleaned[-1]["T"] != end-1:
            raise ValueError(f"{tf} non-overlap window edges invalid")
        snapshots[tf] = {
            "market":"HYPERLIQUID:BTCUSDC.P","coin":"BTC",
            "source":SOURCE,"timeframe":tf,"capturedAtUtc":stamp,
            "closedCandles":cleaned,"lastCloseMs":cleaned[-1]["T"],
            "researchOnly":True,"viprasolVerified":False,
            "discordEligible":False,
        }
    return snapshots


def research_holdout(*, acquired_ms=None, fetch=make_request):
    acquisition = int(time.time()*1000) if acquired_ms is None else int(acquired_ms)
    result={
        "selectedWindowBars":dict(BARS),
        "minimumWarmupBars":500,
        "kind":"NONOVERLAPPING_HISTORICAL_HYPERLIQUID_BTC_HOLDOUT_V1",
        "market":"HYPERLIQUID:BTCUSDC.P",
        "fixedHoldoutEndMs":HOLDOUT_END_MS,
        "acquiredAtUtc":datetime.fromtimestamp(acquisition/1000,timezone.utc).isoformat(),
        "status":"NOT_AVAILABLE",
        "reason":None,
        "comparison":None,
        "historicalOnly":True,
        "recoveredCandlesAreForwardObservations":False,
        "originalViprasolVerified":False,
        "discordEligible":False,
        "automaticTrading":False,
        "profitabilityClaimAllowed":False,
    }
    try:
        snapshots=build_holdout_snapshots(acquired_ms=acquisition,fetch=fetch)
        result["comparison"]=compare_historical_paper(snapshots, min_history_bars=500)
        result["status"]="COMPLETED_HISTORICAL_ONLY"
    except (ValueError, RuntimeError, OSError, TimeoutError) as exc:
        # No fallback to overlapping or third-party source data. Transport
        # errors and source insufficiency must not masquerade as zero trades.
        result["reason"]=type(exc).__name__+": "+str(exc)[:350]
    return result


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=Path("test-output/holdout_research.json"))
    args=parser.parse_args()
    result=research_holdout()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("NONOVERLAPPING HISTORICAL BTC HOLDOUT",result["status"])
    if result["reason"]:
        print("No holdout metrics:",result["reason"])
    elif result["comparison"]:
        for tf,frame in result["comparison"]["timeframes"].items():
            print(tf,"Classic",frame["unchangedClassic"]["resolved"],
                  "CHOP",frame["fixedChopGate"]["resolved"],
                  "net R at 7 bps",frame["unchangedClassic"]["netRSumByOneWayCostBps"]["7"],
                  frame["fixedChopGate"]["netRSumByOneWayCostBps"]["7"])
    print("No original Pine parity, future forward evidence, Discord alerts or trading")


if __name__=="__main__":
    main()
