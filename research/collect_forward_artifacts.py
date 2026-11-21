"""Read-only GitHub Actions artifact ingestion for the BTC paper ledger.

Consumes existing research-only artifacts, never contacts exchanges or wallets.
Outputs only offline evidence summaries, never actionable trading signals.
"""
import argparse
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit
import zipfile

from research.forward_paper_ledger import analyze_forward_records
from research.observation_coverage import observation_coverage
from research.schedule_reliability import schedule_reliability

PREFIX="btc-paper-evidence-"
MAX_ARCHIVE_BYTES=2_000_000
MAX_RECORD_BYTES=100_000
REPO_PATTERN=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ARTIFACT_PATTERN=re.compile(r"^btc-paper-evidence-([0-9]+)$")


class _SafeArtifactRedirect(HTTPRedirectHandler):
    """GitHub signs cross-host artifact redirects; never forward API tokens."""
    def redirect_request(self,request,response,code,message,headers,newurl):
        next_request=super().redirect_request(
            request,response,code,message,headers,newurl)
        if next_request is None:
            return None
        target=urlsplit(newurl)
        if target.scheme!="https":
            raise ValueError("Non-HTTPS artifact redirect rejected")
        if target.hostname!=urlsplit(request.full_url).hostname:
            name=target.hostname or ""
            # GitHub Actions archive downloads use short-lived signed blobs,
            # not the GitHub REST host. A GitHub token on that redirected URL
            # causes 401 and needlessly exposes credentials to blob storage.
            allowed=(name.endswith(".blob.core.windows.net")
                     or name.endswith(".actions.githubusercontent.com")
                     or name.endswith(".githubusercontent.com"))
            if not allowed:
                raise ValueError("Unexpected external artifact storage host")
            return Request(newurl,headers={
                "User-Agent":"btc-research-paper-ledger/1.0"})
        return next_request


def _github_open(request,timeout=30):
    return build_opener(_SafeArtifactRedirect()).open(request,timeout=timeout)


def _read(url,token,*,opener=_github_open,limit=MAX_ARCHIVE_BYTES):
    if not token or not url.startswith("https://api.github.com/repos/"):
        raise ValueError("Only authenticated GitHub API access allowed")
    request=Request(url,headers={"Authorization":f"Bearer {token}",
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"btc-research-paper-ledger/1.0"})
    with opener(request,timeout=30) as response:
        value=response.read(limit+1)
    if len(value)>limit:
        raise ValueError("GitHub response exceeded expected size limit")
    return value


def select_artifacts(artifacts,*,after,limit=110):
    """Filter GitHub API metadata: only verified main-branch evidence artifacts.

    Returns newest first. The archive payload itself must pass the ledger's
    immutable SHA-256 and disabled-trading checks.
    """
    if not isinstance(after,datetime) or after.utcoffset() is None:
        raise ValueError("An offset-aware cutoff is required")
    if not 1<=limit<=500:
        raise ValueError("Invalid artifact limit")
    selected={}
    for item in artifacts:
        if not isinstance(item,dict) or item.get("expired") is not False:
            continue
        match=ARTIFACT_PATTERN.fullmatch(str(item.get("name","")))
        if not match:
            continue
        run_id=int(match.group(1))
        run=item.get("workflow_run") or {}
        if run.get("head_branch")!="main" or int(run.get("id",0))!=run_id:
            continue
        created=datetime.fromisoformat(str(item["created_at"]).replace("Z","+00:00"))
        if created<after:
            continue
        artifact_id=int(item["id"])
        if artifact_id<=0:
            raise ValueError("Invalid artifact id")
        selected[artifact_id]={"id":artifact_id,"runId":run_id,
            "createdAtUtc":created.isoformat()}
    return sorted(selected.values(),key=lambda x:x["createdAtUtc"],reverse=True)[:limit]


def decode_paper_archive(data):
    if len(data)>MAX_ARCHIVE_BYTES:
        raise ValueError("Unreasonably large artifact")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        files=archive.infolist()
        if len(files)!=1 or files[0].filename!="forward_observation.json":
            raise ValueError("Unexpected artifact ZIP members")
        info=files[0]
        if info.file_size>MAX_RECORD_BYTES or info.is_dir():
            raise ValueError("Unsafe artifact entry")
        record=json.loads(archive.read(info))
        if not isinstance(record,dict):
            raise ValueError("Malformed research observation")
        return record


def collect_daily(repo,token,*,now=None,lookback_hours=24,
                  max_artifacts=110,opener=_github_open):
    if not REPO_PATTERN.fullmatch(repo):
        raise ValueError("Invalid GitHub repository path")
    if not 1<=lookback_hours<=720:
        raise ValueError("Invalid lookback window")
    now=now or datetime.now(timezone.utc)
    if now.utcoffset() is None:
        raise ValueError("UTC-aware observation time required")
    after=now-timedelta(hours=lookback_hours)
    items=[]
    # GitHub lists up to 100 items/page; older pages are not relevant once
    # we've passed the beginning of the selected window.
    for page in range(1,21):
        url=(f"https://api.github.com/repos/{repo}/actions/artifacts"
             f"?per_page=100&page={page}")
        response=json.loads(_read(url,token,opener=opener))
        page_items=response.get("artifacts")
        if not isinstance(page_items,list):
            raise ValueError("Invalid GitHub artifact listing response")
        items.extend(page_items)
        if not page_items:
            break
        # The API returns newest artifacts first. Stop only when ALL of
        # the current page's timestamps predate the requested cutoff.
        timestamps=[datetime.fromisoformat(str(x["created_at"]).replace("Z","+00:00"))
                    for x in page_items]
        if max(timestamps)<after:
            break
    chosen=select_artifacts(items,after=after,limit=max_artifacts)
    records=[]
    for item in chosen:
        # Construct archive URL ourselves rather than following an
        # arbitrary untrusted URL from artifact metadata.
        url=f"https://api.github.com/repos/{repo}/actions/artifacts/{item['id']}/zip"
        data=_read(url,token,opener=opener)
        records.append(decode_paper_archive(data))
    # Audit GitHub scheduled executions separately from exchange candle
    # coverage. Only actual run records count, never synthetic cron events.
    scheduled_runs=[]
    for page in range(1,11):
        url=(f"https://api.github.com/repos/{repo}/actions/workflows/"
             f"btc-forward-capture.yml/runs?event=schedule&per_page=100&page={page}")
        payload=json.loads(_read(url,token,opener=opener))
        batch=payload.get("workflow_runs")
        if not isinstance(batch,list):
            raise ValueError("Invalid GitHub scheduled run API response")
        scheduled_runs.extend(batch)
        if not batch:
            break
        created=[datetime.fromisoformat(str(x["created_at"]).replace("Z","+00:00"))
                 for x in batch]
        if max(created)<after:
            break
    results=analyze_forward_records(records,one_way_cost_bps=7)
    # The ledger validates integrity and trading-disabled flags before we
    # measure expected-vs-observed closes over the ENTIRE requested window.
    results["closedCandleCoverage"]=observation_coverage(
        records,after=after,through=now)
    results["githubScheduleReliability"]=schedule_reliability(
        scheduled_runs,after=after,through=now)
    for tf,entry in results["byTimeframe"].items():
        entry["performanceSufficient"]=False
    results["collection"]={"repository":repo,"lookbackHours":lookback_hours,
        "artifactCount":len(chosen),"cutoffUtc":after.isoformat(),
        "generatedAtUtc":now.isoformat(),
        "sourceRunIds":[a["runId"] for a in chosen],
        "truncatedAtArtifactLimit":len(chosen)==max_artifacts,
        "hasEnoughSamplesForProfitClaim":False}
    results["sourceRunsMayBeDelayed"]=True
    results["profitabilityClaimAllowed"]=False
    return results


def main():
    parser=argparse.ArgumentParser(description="Read-only daily GitHub paper-trading audit")
    parser.add_argument("--repo",default="Elikers/hyperliquid-btc-dashboard")
    parser.add_argument("--hours",type=int,default=24)
    parser.add_argument("--max-artifacts",type=int,default=110)
    parser.add_argument("--out",type=Path,default=Path("paper-output/daily_forward_audit.json"))
    args=parser.parse_args()
    token=os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN required for read-only artifact access")
    result=collect_daily(args.repo,token,lookback_hours=args.hours,
                         max_artifacts=args.max_artifacts)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Research-only artifact audit:",result["collection"]["artifactCount"],
          "capture artifacts")
    for tf,stat in result["byTimeframe"].items():
        print(tf,"closed bars:",stat["uniqueClosedBars"],
              "missing:",stat["missingBars"],
              "hypothetical setups:",stat["hypotheticalCandidates"],
              "resolved:",stat["resolved"])
    for tf,score in result["closedCandleCoverage"]["byTimeframe"].items():
        print(tf,"coverage:",score["observedUniqueClosedBars"],"/",
              score["expectedClosedBars"],"closed candles; unobserved:",
              score["unobservedClosedBars"])
    health=result["githubScheduleReliability"]
    print("GitHub scheduled capture runs:",health["observedScheduledRunCount"],
          "/",health["configuredCronOpportunities"],
          "configured opportunities (NOT exact missed-slot count)")
    print("Profitability and Pine parity NOT verified; Discord and trading OFF")


if __name__=="__main__":
    main()
