"""Read-only GitHub artifact collector for HISTORICAL-ONLY BTC candles.

Separate from the forward paper-trade ledger. Never reconstruct trades,
trade signals or missed forward-time observations.
"""
import argparse
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import re
import zipfile

from research.collect_forward_artifacts import _read, _github_open, REPO_PATTERN
from research.reconcile_historical_archives import reconcile_archives

PREFIX="btc-historical-candles-"
NAME=re.compile(r"^btc-historical-candles-([1-9][0-9]*)$")
MAX_COMPRESSED=2_000_000
MAX_JSON=2_000_000


def select_history_artifacts(artifacts, *, after, limit=120):
    if not isinstance(after,datetime) or after.utcoffset() is None:
        raise ValueError("A timezone-aware cutoff is required")
    if type(limit) is not int or not 1<=limit<=300:
        raise ValueError("Invalid artifact limit")
    chosen={}
    for item in artifacts:
        if not isinstance(item,dict) or item.get("expired") is not False:
            continue
        match=NAME.fullmatch(str(item.get("name","")))
        if not match:
            continue
        run=item.get("workflow_run") or {}
        if run.get("head_branch")!="main" or int(run.get("id",0))!=int(match.group(1)):
            continue
        created=datetime.fromisoformat(str(item["created_at"]).replace("Z","+00:00"))
        if created.utcoffset() is None or created<after:
            continue
        aid=int(item["id"])
        if aid<=0:
            raise ValueError("Invalid artifact ID")
        chosen[aid]={"id":aid,"runId":int(match.group(1)),
                     "createdAtUtc":created.isoformat()}
    return sorted(chosen.values(),key=lambda x:x["createdAtUtc"],reverse=True)[:limit]


def decode_history_zip(data):
    if len(data)>MAX_COMPRESSED:
        raise ValueError("Historical ZIP exceeds safety limit")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members=z.infolist()
        if len(members)!=1 or members[0].filename!="historical_candles_only.json":
            raise ValueError("Unexpected historical artifact ZIP contents")
        info=members[0]
        if info.is_dir() or info.file_size>MAX_JSON:
            raise ValueError("Unsafe historical JSON entry")
        data=z.read(info)
        if len(data)>MAX_JSON:
            raise ValueError("Historical JSON exceeds safety limit")
        result=json.loads(data)
        if not isinstance(result,dict):
            raise ValueError("Invalid historical archive")
        return result


def collect_historical(repo,token,*,now=None,lookback_hours=72,
                       max_artifacts=120,opener=_github_open):
    if not REPO_PATTERN.fullmatch(repo):
        raise ValueError("Invalid repository")
    if not token:
        raise ValueError("GitHub read-only token required")
    if type(lookback_hours) is not int or not 1<=lookback_hours<=720:
        raise ValueError("Invalid lookback")
    if type(max_artifacts) is not int or not 1<=max_artifacts<=300:
        raise ValueError("Invalid archive limit")
    now=now or datetime.now(timezone.utc)
    if now.utcoffset() is None:
        raise ValueError("Timezone-aware current time required")
    after=now-timedelta(hours=lookback_hours)
    items=[]
    pages_read=0
    reached_end=False
    for page in range(1,21):
        url=(f"https://api.github.com/repos/{repo}/actions/artifacts"
             f"?per_page=100&page={page}")
        result=json.loads(_read(url,token,opener=opener))
        batch=result.get("artifacts")
        if not isinstance(batch,list):
            raise ValueError("Invalid GitHub artifact listing")
        pages_read+=1
        items.extend(batch)
        if not batch:
            reached_end=True
            break
        dates=[datetime.fromisoformat(str(x["created_at"]).replace("Z","+00:00"))
               for x in batch]
        if max(dates)<after:
            reached_end=True
            break
    # Never silently present a partial historical dataset as exhaustive.
    if not reached_end:
        raise ValueError("Historical artifact listing exceeded pagination safety cap")
    chosen=select_history_artifacts(items,after=after,limit=max_artifacts)
    records=[]
    for item in chosen:
        data=_read(f"https://api.github.com/repos/{repo}/actions/artifacts/{item['id']}/zip",
                   token,opener=opener,limit=MAX_COMPRESSED)
        records.append(decode_history_zip(data))
    result=reconcile_archives(records)  # validates each archive digest and safety flags
    result["collection"]={
        "repository":repo,
        "lookbackHours":lookback_hours,
        "cutoffUtc":after.isoformat(),
        "generatedAtUtc":now.isoformat(),
        "artifactCount":len(chosen),
        "sourceArtifactIds":[x["id"] for x in chosen],
        "sourceRunIds":[x["runId"] for x in chosen],
        "artifactLimitReached":len(chosen)==max_artifacts,
        "pagesRead":pages_read,
        "exhaustiveWithinWindow":len(chosen)<max_artifacts,
        "historicalOnly":True,
    }
    result["forwardObservationCoverageUnchanged"]=True
    result["profitabilityClaimAllowed"]=False
    result["discordEligible"]=False
    result["automaticTrading"]=False
    return result


def main():
    parser=argparse.ArgumentParser(description="Historical-only BTC audit")
    parser.add_argument("--repo",default="Elikers/hyperliquid-btc-dashboard")
    parser.add_argument("--hours",type=int,default=72)
    parser.add_argument("--max-artifacts",type=int,default=120)
    parser.add_argument("--out",type=Path,default=Path("history-output/historical_audit.json"))
    args=parser.parse_args()
    token=os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN required")
    result=collect_historical(args.repo,token,lookback_hours=args.hours,
                              max_artifacts=args.max_artifacts)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("HISTORICAL ONLY:",result["archivesIngested"],"verified archives")
    for tf,stats in result["byTimeframe"].items():
        print(tf,stats["uniqueHistoricalClosedBars"],"unique candles,",
              stats["internalHistoricalMissingBarCount"],"internal missing")
    print("Forward evidence, Pine parity, Discord and wallet trading unchanged / OFF")


if __name__=="__main__":
    main()
