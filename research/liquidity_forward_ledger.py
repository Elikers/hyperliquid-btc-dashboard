"""Deduplicated, genuinely captured BTC liquidity Lab paper outcomes.

Only prospective signed records and later independently captured closed bars.
No historical gap reconstruction. Missing observations quarantine outcomes.
"""
import hashlib
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from math import isfinite

from research.factors import STEPS
from research.lab_liquidity import next_open_stress
from research.collect_forward_artifacts import _read, REPO_PATTERN

KIND="HYPERLIQUID_BTC_LIQUIDITY_LAB_PROSPECTIVE_OBSERVATION_V1"
PREFIX="btc-liquidity-forward-"
MAX_BYTES=2_000_000


def verify_record(record):
    if (not isinstance(record,dict) or record.get("kind")!=KIND or
        record.get("prospectivelyObserved") is not True or
        record.get("futureOutcomeKnown") is not False or
        record.get("historicalOnly") is not False or
        record.get("originalViprasolVerified") is not False or
        record.get("discordEligible") is not False or
        record.get("automaticTrading") is not False or
        record.get("profitabilityClaimAllowed") is not False):
        raise ValueError("Wrong or unsafe prospective Lab record")
    digest=record.get("recordSha256")
    payload={k:v for k,v in record.items() if k!="recordSha256"}
    expected=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    if digest!=expected:
        raise ValueError("Prospective record digest mismatch")
    stamp=datetime.fromisoformat(record["capturedAtUtc"].replace("Z","+00:00"))
    if stamp.utcoffset() is None:
        raise ValueError("Missing time zone")
    frames=record.get("timeframes")
    if not isinstance(frames,dict) or set(frames)!=set(STEPS):
        raise ValueError("Missing BTC frames")
    for tf,item in frames.items():
        end=item["closedBarEndMs"]
        start=item["closedBarStartMs"]
        if end-start!=STEPS[tf]-1 or start%STEPS[tf] or end>=stamp.timestamp()*1000:
            raise ValueError("Wrong candle timing")
        bar=item["bar"]
        values=[float(bar[k]) for k in ("o","h","l","c","v")]
        if not all(isfinite(v) for v in values) or min(values[:4])<=0 or values[4]<0 or bar["h"]<max(bar["o"],bar["c"]) or bar["l"]>min(bar["o"],bar["c"]):
            raise ValueError("Bad OHLCV")
        candidate=item.get("researchCandidate")
        if candidate is not None:
            if (candidate.get("side") not in ("LONG","SHORT") or
                candidate.get("closedBarEndMs")!=end or
                candidate.get("researchOnly") is not True or
                candidate.get("originalViprasolVerified") is not False or
                candidate.get("discordEligible") is not False or
                candidate.get("automaticTrading") is not False):
                raise ValueError("Unsafe Lab candidate")
    return stamp


def ledger(records):
    indexed={tf:{} for tf in STEPS}
    duplicates=0
    for record in records:
        stamp=verify_record(record)
        for tf,item in record["timeframes"].items():
            end=item["closedBarEndMs"]
            prev=indexed[tf].get(end)
            if prev:
                if prev["data"]!=item:
                    raise ValueError("Contradictory duplicate Lab observation")
                duplicates+=1
                if stamp<prev["stamp"]:
                    indexed[tf][end]={"stamp":stamp,"data":item}
            else:
                indexed[tf][end]={"stamp":stamp,"data":item}
    result={}
    trades=[]
    for tf,step in STEPS.items():
        ends=sorted(indexed[tf])
        missing=sum((b-a)//step-1 for a,b in zip(ends,ends[1:]))
        if any((b-a)%step for a,b in zip(ends,ends[1:])):
            raise ValueError("Misaligned prospective observations")
        for pos,end in enumerate(ends):
            candidate=indexed[tf][end]["data"]["researchCandidate"]
            if candidate is None:
                continue
            subsequent=[]
            expected=end+step
            gap=False
            for later in ends[pos+1:]:
                if later!=expected:
                    gap=True
                    break
                later_bar=indexed[tf][later]["data"]["bar"]
                subsequent.append(later_bar)
                expected+=step
            if not subsequent:
                status="DATA_GAP" if gap else "OPEN"
                outcome={"status":status,"netRByOneWayCostBps":None}
            else:
                outcome=next_open_stress(candidate["side"],
                                         candidate["hypotheticalRiskLadder"],
                                         subsequent)
                if outcome["status"]=="OPEN" and gap:
                    outcome["status"]="DATA_GAP"
            trades.append({
                "timeframe":tf,"side":candidate["side"],
                "signalCloseMs":end,"firstObservedUtc":indexed[tf][end]["stamp"].isoformat(),
                "status":outcome["status"],
                "laterConsecutiveBars":len(subsequent),
                "netRByOneWayCostBps":outcome["netRByOneWayCostBps"],
                "researchOnly":True,"discordEligible":False,
            })
        sample=[x for x in trades if x["timeframe"]==tf]
        resolved=[x for x in sample if x["netRByOneWayCostBps"] is not None]
        result[tf]={
            "uniqueObservedCloses":len(ends),"missingIntermediateCloses":missing,
            "candidateCount":len(sample),"resolved":len(resolved),
            "unresolved":len(sample)-len(resolved),
            "netRSumByOneWayCostBps":{
                str(cost):sum(x["netRByOneWayCostBps"][str(cost)] for x in resolved)
                for cost in (0,7,15)},
        }
    return {
        "kind":"RESEARCH_ONLY_PROSPECTIVE_LIQUIDITY_LAB_LEDGER_V1",
        "recordCount":len(records),"duplicateObservedCloses":duplicates,
        "timeframes":result,"trades":trades,
        "historicalOnly":False,"prospectiveRecordsOnly":True,
        "sourcePineParityVerified":False,"independentForwardProfitable":False,
        "discordEligible":False,"automaticTrading":False,
        "profitabilityClaimAllowed":False,
        "limitations":[
            "Only outcomes from later actual captured consecutive closed candles",
            "Missing observations quarantine paper outcomes, never backfilled",
            "Next-open fill adverse 3bps plus hypothetical 0/7/15bps one-way costs",
            "No broker fills, intrabar sequence, funding, leverage or portfolio equity",
            "No original TradingView Pine bar-by-bar parity",
        ],
    }


def read_archive(raw):
    if len(raw)>MAX_BYTES:
        raise ValueError("Oversized forward archive")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        if names!=["liquidity_lab_forward_observation.json"]:
            raise ValueError("Unexpected forward archive files")
        info=z.getinfo(names[0])
        if info.file_size>MAX_BYTES:
            raise ValueError("Oversized forward record")
        return json.loads(z.read(info))


def collect(repo,token,*,hours=24):
    if not REPO_PATTERN.fullmatch(repo) or not token or not 1<=hours<=720:
        raise ValueError("Invalid public GitHub capture audit arguments")
    after=datetime.now(timezone.utc)-timedelta(hours=hours)
    items=[]
    for page in range(1,11):
        url=f"https://api.github.com/repos/{repo}/actions/artifacts?per_page=100&page={page}"
        batch=json.loads(_read(url,token)).get("artifacts")
        if not isinstance(batch,list):
            raise ValueError("Bad GitHub artifact listing")
        items.extend(batch)
        if len(batch)<100:
            break
    selected=[]
    for item in items:
        if item.get("expired") is not False:
            continue
        name=item.get("name","")
        if not name.startswith(PREFIX) or not name[len(PREFIX):].isdigit():
            continue
        run=item.get("workflow_run") or {}
        if run.get("head_branch")!="main" or str(run.get("id"))!=name[len(PREFIX):]:
            continue
        when=datetime.fromisoformat(item["created_at"].replace("Z","+00:00"))
        if when>=after:
            selected.append((when,int(item["id"])))
    selected.sort()
    records=[]
    for _,aid in selected[-250:]:
        raw=_read(f"https://api.github.com/repos/{repo}/actions/artifacts/{aid}/zip",token)
        records.append(read_archive(raw))
    output=ledger(records)
    output["sourceArtifactCount"]=len(records)
    return output


def main():
    import argparse,os
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",default="Elikers/hyperliquid-btc-dashboard")
    parser.add_argument("--hours",type=int,default=24)
    parser.add_argument("--out",type=Path,default=Path("test-output/liquidity_forward_ledger.json"))
    args=parser.parse_args()
    result=collect(args.repo,os.environ.get("GITHUB_TOKEN"),hours=args.hours)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("Prospective LAB source observations:",result["sourceArtifactCount"])
    for tf,frame in result["timeframes"].items():
        print(tf,frame["uniqueObservedCloses"],"closed observations",
              frame["candidateCount"],"Lab candidates",frame["resolved"],"resolved")
    print("No order execution or independent profitability established")


if __name__=="__main__":
    main()
