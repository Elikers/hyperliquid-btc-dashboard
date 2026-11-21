"""Deduplicate closed-bar BTC research observations and audit paper trades.

Inputs are the 30-day compact, research-only observation JSON files uploaded
by GitHub Actions. This never places orders or produces actionable alerts.
The first observation of each closed timeframe bar wins; contradictory
repeated values are rejected. Forward outcomes require uninterrupted later
closed bars, with stop-first conservative intrabar assumptions.

All reported execution costs are sensitivity assumptions, not measured fills.
An OPEN trade or a DATA_GAP is never counted as a realized outcome.
"""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from math import isfinite
from pathlib import Path

STEPS={"15m":900000,"30m":1800000,"1h":3600000}
KIND="HYPERLIQUID_BTC_FORWARD_PAPER_EVIDENCE_V1"


def _valid_number(value):
    try:
        result=float(value)
    except (TypeError,ValueError):
        raise ValueError("Invalid numeric evidence") from None
    if not isfinite(result):
        raise ValueError("Nonfinite numeric evidence")
    return result


def _levels(ladder,side):
    if not isinstance(ladder,dict) or ladder.get("researchOnly") is not True or ladder.get("discordEligible") is not False:
        raise ValueError("Invalid or trade-enabled hypothetical ladder")
    if ladder.get("side")!=side:
        raise ValueError("Candidate direction does not match ladder")
    entry=_valid_number(ladder.get("entry"))
    stop=_valid_number(ladder.get("stop"))
    targets=ladder.get("targets")
    if not isinstance(targets,list) or len(targets)!=3:
        raise ValueError("Expected three hypothetical targets")
    targets=[_valid_number(t) for t in targets]
    sign=1 if side=="LONG" else -1
    if min(entry,stop,*targets)<=0 or sign*(entry-stop)<=0 or any(sign*(t-entry)<=0 for t in targets) or any(sign*(b-a)<=0 for a,b in zip(targets,targets[1:])):
        raise ValueError("Invalid hypothetical stop/target ordering")
    return entry,stop,targets


def _check_record(record):
    if record.get("kind")!=KIND or record.get("model")!="VIPRASOL_CLASSIC_MACRO_OFF":
        raise ValueError("Unsupported evidence record")
    if record.get("discordEligible") is not False or record.get("automaticTrading") is not False or record.get("originalViprasolVerified") is not False:
        raise ValueError("Unverified alerts or trading must remain off")
    captured=record.get("capturedAtUtc")
    try:
        timestamp=datetime.fromisoformat(captured)
        if timestamp.utcoffset() is None:
            raise ValueError()
    except (ValueError,TypeError):
        raise ValueError("Missing offset-aware capture timestamp") from None
    frames=record.get("timeframes")
    if not isinstance(frames,dict) or set(frames)!=set(STEPS):
        raise ValueError("Missing timeframe observation")
    digest=record.get("recordSha256")
    payload={k:v for k,v in record.items() if k!="recordSha256"}
    expected=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    if digest!=expected:
        raise ValueError("Forward observation checksum mismatch")
    for tf,item in frames.items():
        if not isinstance(item,dict) or item.get("sourceVerified") is not False:
            raise ValueError("Unverified source provenance flag missing")
        start,end=int(item["closedBarStartMs"]),int(item["closedBarEndMs"])
        if end-start!=STEPS[tf]-1 or start%STEPS[tf]:
            raise ValueError("Misaligned or wrong-duration candle")
        if int(timestamp.timestamp()*1000)<=end:
            raise ValueError("Observation precedes its closed candle")
        bar=item.get("bar")
        if not isinstance(bar,dict):
            raise ValueError("No source candle")
        for k in ("o","h","l","c","v"):
            _valid_number(bar.get(k))
        if bar["v"]<0 or not bar["l"]<=min(bar["o"],bar["c"])<=max(bar["o"],bar["c"])<=bar["h"] or bar["l"]<=0:
            raise ValueError("Invalid source OHLCV")
        side=item.get("hypotheticalDirection")
        if side not in (None,"LONG","SHORT"):
            raise ValueError("Invalid hypothetical direction")
        ladder=item.get("hypotheticalRiskLadder")
        if side is None and ladder is not None:
            raise ValueError("Risk ladder without qualifying candidate")
        if side is not None:
            _levels(ladder,side)
        if not isinstance(item.get("blockedReasons"),list):
            raise ValueError("Blocked reasons missing")
    return timestamp


def analyze_forward_records(records,*,one_way_cost_bps=7):
    """Analyze independently captured compact records, not original Pine signals."""
    cost=_valid_number(one_way_cost_bps)
    if not 0<=cost<=100:
        raise ValueError("Hypothetical one-way cost must be 0..100 bps")
    per_tf={tf:{} for tf in STEPS}
    audit={"readRecords":0,"duplicateObservations":0,"missingClosedBars":{}}
    for record in records:
        stamp=_check_record(record)
        audit["readRecords"]+=1
        for tf,item in record["timeframes"].items():
            end=int(item["closedBarEndMs"])
            key=per_tf[tf]
            candidate={"captureTime":stamp,"data":item}
            if end in key:
                prior=key[end]["data"]
                # Recorded market and model results must remain identical
                # regardless of duplicate captures of the same closed bar.
                comparable=lambda obj:{k:v for k,v in obj.items() if k!="captureTime"}
                if comparable(prior)!=comparable(item):
                    raise ValueError("Contradictory duplicate closed-bar evidence")
                audit["duplicateObservations"]+=1
                if stamp<key[end]["captureTime"]:
                    key[end]=candidate
            else:
                key[end]=candidate
    trades=[]
    summary={}
    for tf,step in STEPS.items():
        ordered=sorted(per_tf[tf])
        gaps=[]
        for a,b in zip(ordered,ordered[1:]):
            if b-a!=step:
                if b<=a or (b-a)%step:
                    raise ValueError("Misaligned forward sample chronology")
                gaps.append({"afterCloseMs":a,"beforeCloseMs":b,
                             "missingBars":(b-a)//step-1})
        audit["missingClosedBars"][tf]=sum(x["missingBars"] for x in gaps)
        for idx,signal_close in enumerate(ordered):
            setup=per_tf[tf][signal_close]["data"]
            side=setup["hypotheticalDirection"]
            if side is None:
                continue
            entry,stop,targets=_levels(setup["hypotheticalRiskLadder"],side)
            sign=1 if side=="LONG" else -1
            risk=abs(entry-stop)
            be=False
            outcome="OPEN"
            exit_price=None
            exit_close=None
            seen=0
            for future_close in ordered[idx+1:]:
                if future_close!=signal_close+(seen+1)*step:
                    outcome="DATA_GAP"
                    break
                seen+=1
                bar=per_tf[tf][future_close]["data"]["bar"]
                high,low=_valid_number(bar["h"]),_valid_number(bar["l"])
                current_stop=entry if be else stop
                if low<=current_stop if side=="LONG" else high>=current_stop:
                    outcome="BE" if be else "SL"
                    exit_price=current_stop
                    exit_close=future_close
                    break
                if high>=targets[0] if side=="LONG" else low<=targets[0]:
                    be=True
                if high>=targets[2] if side=="LONG" else low<=targets[2]:
                    outcome="TP3"
                    exit_price=targets[2]
                    exit_close=future_close
                    break
            gross=None if exit_price is None else sign*(exit_price-entry)/risk
            net=None if exit_price is None else gross-(cost/10000)*(entry+exit_price)/risk
            trades.append({"timeframe":tf,"side":side,"signalCloseMs":signal_close,
                "firstObservedAtUtc":per_tf[tf][signal_close]["captureTime"].isoformat(),
                "exitCloseMs":exit_close,"outcome":outcome,
                "forwardBarsObserved":seen,"grossR":gross,"hypotheticalNetR":net,
                "researchOnly":True,"discordEligible":False})
        sample=[x for x in trades if x["timeframe"]==tf]
        resolved=[x for x in sample if x["grossR"] is not None]
        summary[tf]={"uniqueClosedBars":len(ordered),
                     "missingBars":audit["missingClosedBars"][tf],
                     "hypotheticalCandidates":len(sample),
                     "resolved":len(resolved),
                     "unresolved":len(sample)-len(resolved),
                     "outcomes":dict(Counter(x["outcome"] for x in sample)),
                     "grossRSum":sum(x["grossR"] for x in resolved),
                     "illustrativeNetRSum":sum(x["hypotheticalNetR"] for x in resolved)}
    return {"kind":"research_only_forward_paper_replay_v1",
            "evidence":audit,"byTimeframe":summary,"trades":trades,
            "oneWayCostBpsHypothesis":cost,
            "assumptions":["First capture of each closed bar; repeated observations deduplicated",
                "Only later uninterrupted closed bars resolve hypothetical trades",
                "Stop wins when stop and target both touched within one bar",
                "Full notional exits at TP3/SL/BE; TP1 only moves future stop to breakeven",
                "Overlapping candidates are not a portfolio equity model",
                "Illustrative fees and slippage are not measured execution",
                "Unverified original Pine parity; no live signal authorization"],
            "originalViprasolVerified":False,"discordEligible":False,
            "automaticTrading":False,"profitableStrategyVerified":False}


def main():
    parser=argparse.ArgumentParser(description="Research-only paper outcome audit of extracted forward_observation.json artifacts")
    parser.add_argument("files",nargs="+",type=Path,
                        help="Previously extracted GitHub 30-day compact JSON artifacts")
    parser.add_argument("--one-way-cost-bps",type=float,default=7)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    records=[json.loads(path.read_text(encoding="utf-8")) for path in args.files]
    result=analyze_forward_records(records,one_way_cost_bps=args.one_way_cost_bps)
    text=json.dumps(result,indent=2)+"\n"
    if args.out:
        args.out.write_text(text,encoding="utf-8")
    else:
        print(text)


if __name__=="__main__":
    main()
