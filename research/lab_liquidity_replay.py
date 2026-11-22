"""Automated matched BTC research: Classic vs one liquidity-sweep Lab candidate.

Each strategy sees only completed candle history at the signal close.
Next-open fill and subsequent OHLC outcome use a separate execution stress
model; historical data obtained later is never live forward evidence.
"""
import json
from pathlib import Path

from research.backtest_real_btc_snapshot import (
    backtest_research, fetch_latest_snapshots, validated_candles)
from research.factors import STEPS
from research.lab_liquidity import lab_entry, next_open_stress, summarize_paper
from research.nonoverlap_holdout import build_holdout_snapshots


def compare_entry_swap(snapshots, *, min_history_bars=650, label="recent_historical"):
    candles,_=validated_candles(snapshots,min_history_bars=min_history_bars)
    baseline=backtest_research(snapshots,min_history_bars=min_history_bars)
    records=[]
    for tf, bars in candles.items():
        where={bar["T"]:i for i,bar in enumerate(bars)}
        for entry in baseline["hypotheticalTrades"]:
            if entry["timeframe"]!=tf:
                continue
            idx=where[entry["closedBarEndMs"]]
            # Original Classic signal/risk unchanged. Only the fill model differs.
            levels={"entry":entry["entry"],"stop":entry["stop"],
                    "targets":[entry["entry"]+
                               (1 if entry["side"]=="LONG" else -1)*
                               abs(entry["entry"]-entry["stop"])*j
                               for j in (1,2,3)]}
            result=next_open_stress(entry["side"],levels,bars[idx+1:])
            records.append({"timeframe":tf,"closedBarEndMs":entry["closedBarEndMs"],
                            "engine":"Classic","side":entry["side"],
                            "comparison":{"Classic":result}})
        earliest=bars[0]["t"]+15*86400000
        for idx in range(max(101,15*86400000//STEPS[tf]),len(bars)-1):
            bar=bars[idx]
            if bar["T"]<earliest:
                continue
            # Confirmed pivot/sweep is determined from this *closed* bar only.
            # Avoid computing 7 factors/ADR unless the sweep trigger actually fires.
            from research.lab_liquidity import confirmed_sweep
            if confirmed_sweep(bars[:idx+1])[0] is None:
                continue
            confirm=[b for b in candles["15m"] if b["T"]<=bar["T"]]
            if len(confirm)<100:
                continue
            candidate=lab_entry(bars[:idx+1],confirm,timeframe=tf)
            if candidate is None:
                continue
            outcome=next_open_stress(candidate["side"],
                                      candidate["hypotheticalRiskLadder"],
                                      bars[idx+1:])
            records.append({"timeframe":tf,"closedBarEndMs":bar["T"],
                            "engine":"LiquidityLab","side":candidate["side"],
                            "confirmedPivotLevel":candidate["confirmedPivotLevel"],
                            "factorScoreSeven":candidate["factorScoreSeven"],
                            "comparison":{"LiquidityLab":outcome}})
    shaped=[{"timeframe":r["timeframe"],**r["comparison"]} for r in records]
    return {
        "kind":"HISTORICAL_ONLY_LIQUIDITY_ENTRY_SWAP_NEXT_OPEN_STRESS_V1",
        "market":"HYPERLIQUID:BTCUSDC.P","datasetLabel":label,
        "entryEvents":"Original Classic EMA cross vs Lab confirmed pivot sweep-reclaim",
        "frozenParameters":{"swingLeft":3,"swingRight":3,"pivotMaxAge":48,
                            "minimumSevenFactorScore":5,"atrMultiplier":1.5,
                            "adverseEntrySlippageBps":3,
                            "additionalOneWayCostsBps":[0,7,15]},
        "timeframes":summarize_paper(shaped),"hypotheticalTrades":records,
        "assumptions":[
            "Historical source-derived Python baseline, not original Pine parity",
            "Both entry decisions use only candle closes available at that instant",
            "Next candle open shifted adversely 3bps for entry, with fixed signal-time SL/TP levels",
            "Additional 0/7/15bps one-way cost sensitivity, not measured exchange fills",
            "Unfillable entries quarantined; unresolved exits excluded from R sums",
            "Classic original research output not altered; alternative is separate BTC Lab",
            "No leverage, funding, portfolio position constraints or actual exchange fills modeled",
        ],
        "historicalOnly":True,"recoveredCandlesAreForwardObservations":False,
        "originalViprasolVerified":False,"independentForwardProfitable":False,
        "discordEligible":False,"automaticTrading":False,
        "profitabilityClaimAllowed":False,
    }


def main():
    import argparse,os
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,
                        default=Path("test-output/liquidity_lab_replay.json"))
    parser.add_argument("--repo",default="Elikers/hyperliquid-btc-dashboard")
    args=parser.parse_args()
    token=os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Read-only GITHUB_TOKEN required")
    snapshots,run,artifact=fetch_latest_snapshots(args.repo,token)
    recent=compare_entry_swap(snapshots,label="recent_historical")
    recent["sourceRunId"]=run
    recent["sourceArtifactId"]=artifact
    result={"recent":recent,"earlierHoldout":None,
            "earlierHoldoutStatus":"NOT_AVAILABLE",
            "historicalOnly":True,"discordEligible":False,
            "automaticTrading":False,"profitabilityClaimAllowed":False}
    try:
        older=build_holdout_snapshots()
        result["earlierHoldout"]=compare_entry_swap(
            older,min_history_bars=500,label="older_nonoverlap_historical")
        result["earlierHoldoutStatus"]="COMPLETED_HISTORICAL_ONLY"
    except (ValueError,RuntimeError,OSError,TimeoutError) as error:
        result["earlierHoldoutReason"]=str(error)[:300]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    for name,data in (("recent",recent),("older",result["earlierHoldout"])):
        if data is None:
            print(name,"UNAVAILABLE",result.get("earlierHoldoutReason"))
            continue
        for tf,v in data["timeframes"].items():
            print(name,tf,"Classic",v["Classic"],"Lab",v["LiquidityLab"])
    print("RESEARCH ONLY; original Pine parity, real forward profit, alerts and orders OFF")


if __name__=="__main__":
    main()
