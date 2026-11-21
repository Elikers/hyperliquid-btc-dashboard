"""Historical-only research replay using REAL saved Hyperliquid BTC candles.

Replays source-supported Python Macro-Off candidate logic. Not exact
TradingView Pine parity, observed forward signals, or executable orders.
No parameter fitting, no future candles used for candidate generation.
"""
from datetime import datetime, timezone
import hashlib
import io
import json
from math import isfinite
from pathlib import Path
import re
import zipfile

from research.collect_forward_artifacts import _read, _github_open, REPO_PATTERN
from research.factors import STEPS, clean, ema
from research.classic_macro_off import evaluate_classic_macro_off

SOURCE="Hyperliquid official public candleSnapshot API"
ARTIFACT=re.compile(r"^btc-research-candles-([1-9][0-9]*)$")
MAX_ZIP=2_000_000
MAX_UNCOMPRESSED=2_000_000
COSTS=(0,7,15)


def select_raw_snapshots(items, *, limit=10):
    selected=[]
    for item in items:
        if not isinstance(item,dict) or item.get("expired") is not False:
            continue
        match=ARTIFACT.fullmatch(str(item.get("name","")))
        run=item.get("workflow_run") or {}
        if not match or run.get("head_branch")!="main":
            continue
        if int(run.get("id",0))!=int(match.group(1)):
            continue
        selected.append((str(item["created_at"]),int(item["id"]),int(match.group(1))))
    selected.sort(reverse=True)
    return selected[:limit]


def decode_snapshot_zip(raw):
    if len(raw)>MAX_ZIP:
        raise ValueError("Oversized capture ZIP")
    result={}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members=archive.infolist()
        names={m.filename for m in members}
        required={f"btc_{tf}.json" for tf in STEPS}
        if not required.issubset(names) or any(m.is_dir() or m.file_size>MAX_UNCOMPRESSED for m in members):
            raise ValueError("Missing or oversized capture snapshots")
        for tf in STEPS:
            payload=archive.read(f"btc_{tf}.json")
            if len(payload)>MAX_UNCOMPRESSED:
                raise ValueError("Oversized snapshot")
            result[tf]=json.loads(payload)
    return result


def validated_candles(snapshots):
    if set(snapshots)!=set(STEPS):
        raise ValueError("Unexpected source timeframes")
    instants={snapshots[tf].get("capturedAtUtc") for tf in STEPS}
    if len(instants)!=1:
        raise ValueError("Mixed snapshot capture instants")
    captured=datetime.fromisoformat(next(iter(instants)).replace("Z","+00:00"))
    if captured.utcoffset() is None:
        raise ValueError("Invalid snapshot capture instant")
    capture_ms=int(captured.timestamp()*1000)
    output={}
    for tf,step in STEPS.items():
        snap=snapshots[tf]
        if (snap.get("market")!="HYPERLIQUID:BTCUSDC.P" or
            snap.get("coin")!="BTC" or snap.get("timeframe")!=tf or
            snap.get("source")!=SOURCE or snap.get("researchOnly") is not True or
            snap.get("viprasolVerified") is not False or snap.get("discordEligible") is not False):
            raise ValueError("Unverified or wrong market snapshot")
        bars=clean(snap.get("closedCandles",[]),step)
        if len(bars)<650:
            raise ValueError("Insufficient backtest warmup history")
        if int(snap.get("lastCloseMs",-1))!=bars[-1]["T"]:
            raise ValueError("Snapshot latest close mismatch")
        if bars[-1]["T"]>=capture_ms-3000:
            raise ValueError("Source final candle not safely closed")
        output[tf]=bars
    return output,captured


def _exit_simulation(candidate, future):
    ladder=candidate["hypotheticalRiskLadder"]
    side=candidate["hypotheticalDirection"]
    if side not in ("LONG","SHORT") or ladder is None:
        raise ValueError("No qualifying candidate ladder")
    entry=float(ladder["entry"])
    stop=float(ladder["stop"])
    tp1,tp2,tp3=map(float,ladder["targets"])
    sign=1 if side=="LONG" else -1
    risk=abs(entry-stop)
    if risk<=0 or not all(isfinite(x) and x>0 for x in (entry,stop,tp1,tp2,tp3)):
        raise ValueError("Bad ATR ladder")
    breakeven=False
    for count,bar in enumerate(future,1):
        high,low,opened=bar["h"],bar["l"],bar["o"]
        active_stop=entry if breakeven else stop
        if (low<=active_stop if side=="LONG" else high>=active_stop):
            # Favor adverse gap-open pricing over implausible stops at old levels.
            actual=min(active_stop,opened) if side=="LONG" else max(active_stop,opened)
            gross=sign*(actual-entry)/risk
            return {"status":"BE" if breakeven else "SL",
                    "barsHeld":count,"exitPrice":actual,"grossR":gross,
                    "oneWayCostsNetR":{str(c):gross-(c/10000)*(entry+actual)/risk for c in COSTS}}
        touched_tp1=high>=tp1 if side=="LONG" else low<=tp1
        touched_tp3=high>=tp3 if side=="LONG" else low<=tp3
        if touched_tp1:
            breakeven=True
        if touched_tp3:
            gross=sign*(tp3-entry)/risk
            return {"status":"TP3","barsHeld":count,"exitPrice":tp3,"grossR":gross,
                    "oneWayCostsNetR":{str(c):gross-(c/10000)*(entry+tp3)/risk for c in COSTS}}
    return {"status":"OPEN","barsHeld":len(future),"exitPrice":None,
            "grossR":None,"oneWayCostsNetR":None}


def backtest_research(snapshots, *, source_run_id=None):
    candles,captured=validated_candles(snapshots)
    result={}
    entries=[]
    for tf,step in STEPS.items():
        bars=candles[tf]
        closes=[b["c"] for b in bars]
        fast=ema(closes,9)
        slow=ema(closes,21)
        earliest=bars[0]["t"]+15*86400000
        checked=0
        raw_cross=0
        blocked=0
        for i in range(100,len(bars)):
            bar=bars[i]
            if bar["T"]<earliest:
                continue
            checked+=1
            crossed=(fast[i]>slow[i] and fast[i-1]<=slow[i-1]) or (
                     fast[i]<slow[i] and fast[i-1]>=slow[i-1])
            if not crossed:
                continue
            raw_cross+=1
            # 15m confirmation stops at the close being evaluated.
            confirm=[b for b in candles["15m"] if b["T"]<=bar["T"]]
            candidate=evaluate_classic_macro_off(
                bars[:i+1],confirm,timeframe=tf,current_ms=bar["T"]+1)
            if candidate["hypotheticalDirection"] is None:
                blocked+=1
                continue
            outcome=_exit_simulation(candidate,bars[i+1:])
            entries.append({
                "timeframe":tf,"closedBarEndMs":bar["T"],
                "side":candidate["hypotheticalDirection"],
                "entry":candidate["hypotheticalRiskLadder"]["entry"],
                "stop":candidate["hypotheticalRiskLadder"]["stop"],
                "tp3":candidate["hypotheticalRiskLadder"]["targets"][-1],
                "grossR":outcome["grossR"],
                "netRByOneWayCostBps":outcome["oneWayCostsNetR"],
                "outcome":outcome["status"],
                "barsHeld":outcome["barsHeld"],"researchOnly":True
            })
        frame=[t for t in entries if t["timeframe"]==tf]
        total=len(frame)
        resolved=[t for t in frame if t["grossR"] is not None]
        # Precommitted chronological halves of the eligible sample, no tuning.
        eligible=[b for b in bars if b["T"]>=earliest]
        halfway=eligible[len(eligible)//2]["T"] if eligible else None
        segments={}
        for name,predicate in (("early",lambda x:x["closedBarEndMs"]<halfway),
                               ("later",lambda x:x["closedBarEndMs"]>=halfway)):
            rr=[t for t in resolved if predicate(t)] if halfway is not None else []
            segments[name]={"resolvedTrades":len(rr),
                "illustrativeNetRSumAt7Bps":sum(t["netRByOneWayCostBps"]["7"] for t in rr),
                "winRate":None if not rr else sum(t["netRByOneWayCostBps"]["7"]>0 for t in rr)/len(rr)}
        result[tf]={
            "sourceClosedBars":len(bars),"eligibleClosedBars":checked,
            "rawEmaCrosses":raw_cross,"blockedCrosses":blocked,
            "hypotheticalCandidates":total,"resolvedTrades":len(resolved),
            "unresolvedTrades":total-len(resolved),
            "outcomes":{k:sum(t["outcome"]==k for t in frame) for k in ("SL","BE","TP3","OPEN")},
            "illustrativeNetRSumByOneWayCostBps":{
                str(c):sum(t["netRByOneWayCostBps"][str(c)] for t in resolved) for c in COSTS},
            "netWinRateAt7Bps":None if not resolved else sum(t["netRByOneWayCostBps"]["7"]>0 for t in resolved)/len(resolved),
            "chronologicalEarlyLater":segments,
        }
    return {"kind":"RESEARCH_ONLY_UNVERIFIED_VIPRASOL_MACRO_OFF_HISTORICAL_REPLAY_V1",
            "market":"HYPERLIQUID:BTCUSDC.P",
            "capturedAtUtc":captured.isoformat(),"sourceRunId":source_run_id,
            "timeframes":result,"hypotheticalTrades":entries,
            "assumptions":[
                "Candidate calculated only from closed bars at or before signal time",
                "Historical source-derived Python Macro-Off approximation, NOT independently TradingView Pine-verified",
                "All entries assume idealized signal-bar CLOSE execution, even if actual next open differs",
                "Exit replay uses future closed-bar OHLC only; stop-first and adverse stop gap opens",
                "TP1 moves later-bar stop to breakeven; full hypothetical exit TP3, SL, or BE",
                "One-way illustrative combined fee/slippage sensitivity 0,7,15 bps, not measured fills",
                "Unresolved trades excluded from sums; overlapping trades not realistic portfolio equity",
                "Early/later chronological splits are NOT optimized nor independent forward testing",
                "Historical market candles retrieved after the fact are NOT live forward observations",
            ],
            "backtestNotOriginalPineCertified":True,
            "originalViprasolVerified":False,
            "independentForwardProfitable":False,
            "discordEligible":False,"automaticTrading":False,
            "profitabilityClaimAllowed":False}


def fetch_latest_snapshots(repo,token,*,opener=_github_open):
    if not REPO_PATTERN.fullmatch(repo) or any(p in (".","..") for p in repo.split("/")):
        raise ValueError("Invalid repo")
    items=[]
    for page in range(1,4):
        raw=_read(f"https://api.github.com/repos/{repo}/actions/artifacts?per_page=100&page={page}",
                  token,opener=opener)
        batch=json.loads(raw).get("artifacts")
        if not isinstance(batch,list):
            raise ValueError("Invalid artifact API response")
        items.extend(batch)
        if len(batch)<100:
            break
    matches=select_raw_snapshots(items)
    if not matches:
        raise ValueError("No retained nonexpired raw source capture artifacts")
    _,aid,run=matches[0]
    raw=_read(f"https://api.github.com/repos/{repo}/actions/artifacts/{aid}/zip",
             token,opener=opener,limit=MAX_ZIP)
    return decode_snapshot_zip(raw),run,aid


def main():
    import argparse,os
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",default="Elikers/hyperliquid-btc-dashboard")
    parser.add_argument("--out",type=Path,default=Path("test-output/historical_backtest.json"))
    a=parser.parse_args()
    token=os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Read-only GITHUB_TOKEN required")
    snapshots,run,artifact=fetch_latest_snapshots(a.repo,token)
    output=backtest_research(snapshots,source_run_id=run)
    output["sourceArtifactId"]=artifact
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(output,indent=2,allow_nan=False)+"\n")
    print("RESEARCH-ONLY historical BTC replay; source run",run)
    for tf,x in output["timeframes"].items():
        print(tf,"eligible closes",x["eligibleClosedBars"],"raw crosses",x["rawEmaCrosses"],
              "hypothetical candidates",x["hypotheticalCandidates"],
              "resolved",x["resolvedTrades"],"NetR@7bps",round(x["illustrativeNetRSumByOneWayCostBps"]["7"],3))
    print("Original Pine parity and forward profitability UNVERIFIED; Discord and orders OFF")


if __name__=="__main__":
    main()
