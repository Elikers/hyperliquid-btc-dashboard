"""Conservative OHLC-only research replay of exported candidate trades.

Not the original Viprasol verified strategy; candidate CSV is exploratory.
Stop checked before target in same candle. No wallet actions, no Discord.
TP1/TP2 are monitored markers; assume entire position exits at TP3/SL/BE.
Overlapping trades are counted separately; sums of R are not portfolio PnL.
"""
import csv
import json
from collections import Counter
from pathlib import Path
from math import isfinite

TIMEFRAMES=("15m","30m","1h")


def load_csv(path):
    with open(path,newline="",encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def replay_one(candidate,candles,*,one_way_cost_bps=0):
    if not 0<=one_way_cost_bps<=100 or not isfinite(one_way_cost_bps):
        raise ValueError("Invalid hypothetical trading cost")
    tf=candidate["timeframe"]
    side=candidate["side"]
    if tf not in TIMEFRAMES or side not in ("LONG","SHORT"):
        raise ValueError("Unsupported candidate")
    sign=1 if side=="LONG" else -1
    bar_end=int(candidate["T"])
    entry=float(candidate["entry"])
    stop=float(candidate["sl"])
    targets=[float(candidate["tp"+str(i)]) for i in (1,2,3)]
    risk=abs(entry-stop)
    if (not all(isfinite(x) and x>0 for x in (entry,stop,*targets))
            or risk<=0 or (sign*(entry-stop)<=0)
            or not all(sign*(targets[i]-entry)>0 for i in range(3))
            or not all(sign*(targets[i+1]-targets[i])>0 for i in range(2))):
        raise ValueError("Invalid risk ladder")
    breakeven=False
    result="OPEN"
    exit_price=None
    exit_bar=None
    for candle in candles:
        close_ms=int(candle["T"])
        if close_ms<=bar_end:
            continue
        high=float(candle["high"])
        low=float(candle["low"])
        if not all(isfinite(x) for x in (high,low)) or high<low:
            raise ValueError("Invalid price candle")
        working_stop=entry if breakeven else stop
        if low<=working_stop if sign==1 else high>=working_stop:
            result="BE" if breakeven else "SL"
            exit_price=working_stop
            exit_bar=close_ms
            break
        if high>=targets[0] if sign==1 else low<=targets[0]:
            breakeven=True
        if high>=targets[2] if sign==1 else low<=targets[2]:
            result="TP3"
            exit_price=targets[2]
            exit_bar=close_ms
            break
    gross_r=None if exit_price is None else sign*(exit_price-entry)/risk
    net_r=None if exit_price is None else (
        gross_r - one_way_cost_bps/10000*(entry+exit_price)/risk)
    return {"timeframe":tf,"side":side,"signalCloseMs":bar_end,
            "outcome":result,"exitCloseMs":exit_bar,
            "grossR":gross_r,"netR":net_r,
            "oneWayCostBps":one_way_cost_bps,
            "researchOnly":True,"discordEligible":False}


def replay_csv(candidate_file,candle_file,*,one_way_cost_bps=0):
    candidates=load_csv(candidate_file)
    candles_by_tf={tf:[] for tf in TIMEFRAMES}
    for candle in load_csv(candle_file):
        tf=candle["timeframe"]
        if tf not in TIMEFRAMES:
            raise ValueError("Unexpected candle timeframe")
        candles_by_tf[tf].append(candle)
    for tf,candles in candles_by_tf.items():
        candles.sort(key=lambda c:int(c["T"]))
        if len(set(int(c["T"]) for c in candles))!=len(candles):
            raise ValueError("Duplicate candle close")
    trades=[replay_one(event,candles_by_tf[event["timeframe"]],
                       one_way_cost_bps=one_way_cost_bps)
            for event in candidates]
    by_tf={}
    for tf in (*TIMEFRAMES,"ALL"):
        subset=[t for t in trades if tf=="ALL" or t["timeframe"]==tf]
        resolved=[t for t in subset if t["outcome"]!="OPEN"]
        outcomes=Counter(t["outcome"] for t in subset)
        by_tf[tf]={
            "candidates":len(subset),"resolved":len(resolved),
            "outcomes":dict(outcomes),
            "grossRSum":sum(t["grossR"] for t in resolved),
            "hypotheticalNetRSum":sum(t["netR"] for t in resolved),
            "unresolvedExcluded":len(subset)-len(resolved),
        }
    return {
        "kind":"historical_seven_factor_research_candidate_replay",
        "oneWayCostBpsHypothesis":one_way_cost_bps,"byTimeframe":by_tf,
        "assumptions":[
            "Stop first when the same bar crosses stop and targets",
            "Entire hypothetical position exits at TP3, SL or breakeven",
            "No partial TP1/TP2 fills or independent intra-bar timestamps",
            "Overlapping trades measured separately; not portfolio returns",
            "Cost bps is illustrative, not an actual Hyperliquid fee quote",
            "Only exported candidates, not full Pine source signal parity",
            "Synthetic/slippage assumptions cannot establish live profitability",
        ],
        "originalViprasolVerified":False,"discordEligible":False,
        "automaticTrading":False,
    }


def main():
    root=Path("research")
    result=replay_csv(root/"reference_7factor_candidates.csv",
        root/"reference_btc_candles.csv",one_way_cost_bps=7)
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
