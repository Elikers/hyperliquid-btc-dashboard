"""Independent real BTC candle alignment audit for the Nov 20 Pine screenshot.

No TradingView source access is implied. Tests whether a timestamp offset or
the source-vs-exchange bar close explains the 0.2978 USD ATR stop discrepancy.
Does not change indicator settings, baseline entries or trading permissions.
"""
import json
from datetime import datetime,timezone
from pathlib import Path

from research.backtest_real_btc_snapshot import fetch_latest_snapshots,validated_candles
from research.risk_ladder import atr

REFERENCE_START_MS=1795184100000  # 2026-11-20 14:15:00 UTC
ENTRY=62077.0
DISPLAYED_STOP=61667.1
MULTIPLIER=1.5
STEP_MS=900000


def audit_alignment(snapshots):
    candles,_=validated_candles(snapshots)
    bars=candles["15m"]
    locations={b["t"]:i for i,b in enumerate(bars)}
    rows=[]
    for offset in (-2,-1,0,1,2):
        t=REFERENCE_START_MS+offset*STEP_MS
        idx=locations.get(t)
        if idx is None:
            rows.append({"offsetBars":offset,"available":False})
            continue
        selected=bars[:idx+1]
        current=selected[-1]
        value=atr(selected,14)
        stop=ENTRY-MULTIPLIER*value
        rows.append({
            "offsetBars":offset,
            "available":True,
            "barStartUtc":datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),
            "barEndMs":current["T"],
            "marketOHLC":{"o":current["o"],"h":current["h"],
                          "l":current["l"],"c":current["c"]},
            "screenshotEntryMinusMarketClose":ENTRY-current["c"],
            "atr14":value,"hypotheticalStop":stop,
            "hypotheticalStopMinusDisplayedStop":stop-DISPLAYED_STOP,
        })
    known=[x for x in rows if x["available"]]
    return {
        "kind":"RESEARCH_ONLY_ATR_REFERENCE_TIME_ALIGNMENT_V1",
        "referenceEventStartUtc":"2026-11-20T14:15:00Z",
        "screenshotEntry":ENTRY,"screenshotStopRoundedToTenths":DISPLAYED_STOP,
        "atrPeriod":14,"atrMultiplier":MULTIPLIER,
        "source":"Hyperliquid official public 15m candleSnapshot",
        "rows":rows,"allOffsetWindowsAvailable":len(known)==5,
        "sourceOHLCMatchesTradingViewVerified":False,
        "referenceScreenshotOriginalPineVerified":False,
        "originalViprasolVerified":False,"discordEligible":False,
        "automaticTrading":False,"profitabilityClaimAllowed":False,
        "limitations":[
            "Candle offsets diagnose timing uncertainty only",
            "The screenshot's original TradingView OHLC and ATR series are not independently accessible",
            "Even a near match would not authenticate original source parity",
            "No trading setup, signal delivery or wallet action",
        ],
    }


def main():
    import os,argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",default="Elikers/hyperliquid-btc-dashboard")
    parser.add_argument("--out",type=Path,default=Path("test-output/atr_alignment.json"))
    args=parser.parse_args()
    token=os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Read-only GitHub token required")
    snapshots,source_run,source_artifact=fetch_latest_snapshots(args.repo,token)
    result=audit_alignment(snapshots)
    result["historicalSourceRunId"]=source_run
    result["historicalSourceArtifactId"]=source_artifact
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("Historical ATR screenshot alignment research ONLY",source_run)
    for row in result["rows"]:
        if row["available"]:
            print(row["offsetBars"],"close",row["marketOHLC"]["c"],
                  "ATR",round(row["atr14"],6),
                  "stop delta",round(row["hypotheticalStopMinusDisplayedStop"],6))
        else:
            print(row["offsetBars"],"NOT_AVAILABLE")
    print("Original TradingView Pine and feed parity remain UNVERIFIED")


if __name__=="__main__":
    main()
