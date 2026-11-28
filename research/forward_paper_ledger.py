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
    """Analyze records with a causal first-open-after-observation entry model."""
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
                # Repeated captures of a closed bar must carry identical data.
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
            signal_record=per_tf[tf][signal_close]
            setup=signal_record["data"]
            side=setup["hypotheticalDirection"]
            if side is None:
                continue
            reference_entry,reference_stop,_=_levels(
                setup["hypotheticalRiskLadder"],side)
            sign=1 if side=="LONG" else -1
            risk=abs(reference_entry-reference_stop)
            capture_time=signal_record["captureTime"]
            capture_ms=int(capture_time.timestamp()*1000)

            # A capture is made after the signal candle closes. Any later
            # candle whose OPEN already occurred before that observation was
            # not executable and must never settle this hypothetical trade.
            later=ordered[idx+1:]
            pre_observation=[close for close in later
                if int(per_tf[tf][close]["data"]["closedBarStartMs"])<capture_ms]
            executable=next((close for close in later
                if int(per_tf[tf][close]["data"]["closedBarStartMs"])>=capture_ms),None)
            if executable is None:
                trades.append({
                    "timeframe":tf,"side":side,"signalCloseMs":signal_close,
                    "firstObservedAtUtc":capture_time.isoformat(),
                    "preObservationOpensExcluded":len(pre_observation),
                    "firstExecutableBarOpenMs":None,"entryTimeCausal":False,
                    "entryPrice":None,"signalReferenceEntry":reference_entry,
                    "riskDistance":risk,"exitCloseMs":None,
                    "outcome":"AWAITING_CAUSAL_ENTRY","forwardBarsObserved":0,
                    "grossR":None,"hypotheticalNetR":None,
                    "researchOnly":True,"discordEligible":False})
                continue

            entry_item=per_tf[tf][executable]["data"]
            entry_open_ms=int(entry_item["closedBarStartMs"])
            if entry_open_ms<capture_ms or executable<=signal_close:
                raise ValueError("Noncausal executable entry chronology")
            entry_bar=entry_item["bar"]
            entry=_valid_number(entry_bar["o"])
            stop=entry-sign*risk
            targets=[entry+sign*risk*n for n in (1,2,3)]
            if entry<=0 or stop<=0 or any(x<=0 for x in targets):
                raise ValueError("Causally re-anchored risk ladder crosses zero")

            be=False
            outcome="OPEN"
            exit_price=None
            exit_close=None
            seen=0
            previous_close=None
            for future_close in ordered[ordered.index(executable):]:
                if previous_close is not None and future_close!=previous_close+step:
                    outcome="DATA_GAP"
                    break
                seen+=1
                bar=per_tf[tf][future_close]["data"]["bar"]
                opened=_valid_number(bar["o"])
                high,low=_valid_number(bar["h"]),_valid_number(bar["l"])
                current_stop=entry if be else stop
                stop_hit=low<=current_stop if side=="LONG" else high>=current_stop
                if stop_hit:
                    # Model adverse gaps through the active stop at the bar open.
                    exit_price=(min(current_stop,opened) if side=="LONG"
                                else max(current_stop,opened))
                    outcome="BE" if be else "SL"
                    exit_close=future_close
                    break
                if high>=targets[0] if side=="LONG" else low<=targets[0]:
                    be=True
                if high>=targets[2] if side=="LONG" else low<=targets[2]:
                    outcome="TP3"
                    exit_price=targets[2]
                    exit_close=future_close
                    break
                previous_close=future_close
            gross=None if exit_price is None else sign*(exit_price-entry)/risk
            net=None if exit_price is None else gross-(cost/10000)*(entry+exit_price)/risk
            trades.append({
                "timeframe":tf,"side":side,"signalCloseMs":signal_close,
                "firstObservedAtUtc":capture_time.isoformat(),
                "preObservationOpensExcluded":len(pre_observation),
                "firstExecutableBarOpenMs":entry_open_ms,
                "entryTimeCausal":True,"entryPrice":entry,
                "signalReferenceEntry":reference_entry,"riskDistance":risk,
                "stop":stop,"targets":targets,
                "exitCloseMs":exit_close,"exitPrice":exit_price,
                "outcome":outcome,"forwardBarsObserved":seen,
                "grossR":gross,"hypotheticalNetR":net,
                "researchOnly":True,"discordEligible":False})
        sample=[x for x in trades if x["timeframe"]==tf]
        resolved=[x for x in sample if x["grossR"] is not None]
        summary[tf]={
            "uniqueClosedBars":len(ordered),
            "missingBars":audit["missingClosedBars"][tf],
            "hypotheticalCandidates":len(sample),
            "resolved":len(resolved),
            "unresolved":len(sample)-len(resolved),
            "awaitingCausalEntry":sum(x["outcome"]=="AWAITING_CAUSAL_ENTRY" for x in sample),
            "outcomes":dict(Counter(x["outcome"] for x in sample)),
            "grossRSum":sum(x["grossR"] for x in resolved),
            "illustrativeNetRSum":sum(x["hypotheticalNetR"] for x in resolved)}
    return {
        "kind":"research_only_forward_paper_replay_v2_causal_open",
        "evidence":audit,"byTimeframe":summary,"trades":trades,
        "oneWayCostBpsHypothesis":cost,
        "assumptions":[
            "First capture of each closed bar; repeated observations deduplicated",
            "A capture occurs after the signal close; observed bars opened before that capture are excluded from executable entries",
            "Entry is the first later observed candle open at or after the first observation timestamp",
            "ATR14 x 1.5 risk distance from the signal ladder is preserved and 1R/2R/3R levels are re-anchored around that executable open",
            "Only uninterrupted bars from the executable entry bar onward resolve a hypothetical trade; later gaps produce DATA_GAP",
            "Stop wins when stop and target are both touched within one bar; stop gaps are priced adversely at the bar open",
            "Full notional exits at TP3/SL/BE; TP1 only moves the stop to breakeven on later bars",
            "The 7 bps default is an illustrative one-way cost per side applied to entry plus exit notional, not measured execution",
            "Overlapping candidates are not a portfolio equity model",
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
