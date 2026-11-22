"""Strict per-closed-bar Viprasol Pine reference comparison; no synthetic parity.

The reference must be an independently supplied original TradingView Pine
export, not a Python research-engine backfill. Caller declarations alone cannot
authenticate it. Even zero mismatches NEVER enable alerts or trading.
"""
import json
from pathlib import Path

from research.backtest_real_btc_snapshot import validated_candles,fetch_latest_snapshots
from research.classic_macro_off import evaluate_classic_macro_off
from research.factors import FACTOR_NAMES,STEPS

SOURCE_SHA="00d41c3abfccb3747506185bf0515684b5d8cdaa4b85c4546384914e623f34de"
REFERENCE_KIND="VIPRASOL_ORIGINAL_PINE_CLOSED_BAR_EXPORT_V1"
FACTOR_SET=set(FACTOR_NAMES)
MAX_ROWS_PER_FRAME=300

def unavailable(reason):
    return {"kind":"VIPRASOL_PINE_PARITY_GATE_V1","status":"BLOCKED",
            "blockers":[reason],"byTimeframe":{},
            "independentPineExportAuthenticated":False,
            "fullOriginalViprasolVerified":False,"discordEligible":False,
            "automaticTrading":False,"profitabilityClaimAllowed":False}

def audit(snapshots, reference, *, evaluator=evaluate_classic_macro_off):
    if reference is None:
        return unavailable("INDEPENDENT_ORIGINAL_PINE_BAR_EXPORT_NOT_AVAILABLE")
    if (not isinstance(reference,dict) or
        reference.get("kind")!=REFERENCE_KIND or
        reference.get("sourcePineSha256")!=SOURCE_SHA or
        reference.get("source")!="TradingView original Viprasol Pine" or
        reference.get("macroFactorOnInput") is not False or
        reference.get("minScoreInput")!=5):
        return unavailable("PINE_REFERENCE_PROVENANCE_OR_SETTINGS_UNCONFIRMED")
    frames=reference.get("timeframes")
    if not isinstance(frames,dict) or set(frames)!=set(STEPS):
        return unavailable("ORIGINAL_PINE_REFERENCE_TIMEFRAMES_MISSING")
    candles,_=validated_candles(snapshots,min_history_bars=500)
    out={}
    blockers=[]
    for tf,bars in candles.items():
        refs=frames[tf]
        if not isinstance(refs,list) or not 1<=len(refs)<=MAX_ROWS_PER_FRAME:
            blockers.append(f"{tf}:INVALID_REFERENCE_COUNT")
            continue
        location={b["T"]:i for i,b in enumerate(bars)}
        seen=set()
        mismatch=[]
        skipped=0
        for row in refs:
            if not isinstance(row,dict):
                blockers.append(f"{tf}:MALFORMED_REFERENCE_ROW")
                continue
            end=row.get("closedBarEndMs")
            if not isinstance(end,int) or end in seen or end not in location:
                blockers.append(f"{tf}:DUPLICATE_OR_UNMATCHED_REFERENCE_BAR")
                continue
            seen.add(end)
            idx=location[end]
            if idx<101:
                skipped+=1
                blockers.append(f"{tf}:INSUFFICIENT_WARMUP_AT_REFERENCE_BAR")
                continue
            refbull=row.get("bullFactors")
            refbear=row.get("bearFactors")
            if (not isinstance(refbull,dict) or not isinstance(refbear,dict) or
                set(refbull)!=FACTOR_SET or set(refbear)!=FACTOR_SET or
                any(type(x) is not bool for x in list(refbull.values())+list(refbear.values())) or
                row.get("hypotheticalDirection") not in (None,"LONG","SHORT") or
                row.get("rawCrossover") not in (None,"LONG","SHORT")):
                blockers.append(f"{tf}:MISSING_SOURCE_FACTOR_OR_EVENT")
                continue
            # The precise candle cutoff is independent of acquisition time.
            closed=bars[:idx+1]
            confirm=[b for b in candles["15m"] if b["T"]<=end]
            computed=evaluator(closed,confirm,timeframe=tf,current_ms=end+1)
            # Existing Classic output has aggregate score but not full factor
            # dictionary. Compute those as independent research diagnostics;
            # never treat it as the original Pine reference.
            from research.factors import compute_seven_factors
            factors=compute_seven_factors(closed,confirm,timeframe=tf)
            for prefix,source,calc in (("bull",refbull,factors["bullFactors"]),
                                       ("bear",refbear,factors["bearFactors"])):
                for factor in FACTOR_NAMES:
                    if source[factor]!=calc[factor]:
                        mismatch.append({"closedBarEndMs":end,"field":f"{prefix}.{factor}",
                                         "pine":source[factor],"research":calc[factor]})
            for field,research_field in (("rawCrossover","rawCrossover"),
                                         ("hypotheticalDirection","hypotheticalDirection")):
                if row[field]!=computed[research_field]:
                    mismatch.append({"closedBarEndMs":end,"field":field,
                                     "pine":row[field],"research":computed[research_field]})
        if skipped:
            blockers.append(f"{tf}:WARMUP_ROWS_SKIPPED")
        if mismatch:
            blockers.append(f"{tf}:PINE_VS_RESEARCH_MISMATCH")
        out[tf]={"referenceRows":len(refs),"matchedTimestamps":len(seen),
                 "factorAndSignalMismatches":len(mismatch),"examples":mismatch[:30]}
    # A candidate-only list, even if matched, cannot verify absence of
    # signals. Require entire contiguous reference windows per timeframe.
    for tf,rows in frames.items():
        if not isinstance(rows,list) or not rows:
            continue
        timestamps=[r.get("closedBarEndMs") for r in rows if isinstance(r,dict)]
        if len(timestamps)!=len(rows) or any(
            b-a!=STEPS[tf] for a,b in zip(timestamps,timestamps[1:])):
            blockers.append(f"{tf}:REFERENCE_NOT_CONTIGUOUS_FULL_CLOSED_BARS")
        if len(rows)<100:
            blockers.append(f"{tf}:REFERENCE_WINDOW_TOO_SHORT")
    # Source identity/matching labels are supplied by caller, not independently
    # attested by GitHub. Never auto-upgrade to verified.
    blockers.append("PINE_EXPORT_AUTHENTICITY_NOT_INDEPENDENTLY_ATTESTED")
    return {"kind":"VIPRASOL_PINE_PARITY_GATE_V1",
            "status":"BLOCKED" if blockers else "NUMERICALLY_MATCHED_NOT_AUTHENTICATED",
            "blockers":sorted(set(blockers)),"byTimeframe":out,
            "independentPineExportAuthenticated":False,
            "fullOriginalViprasolVerified":False,"discordEligible":False,
            "automaticTrading":False,"profitabilityClaimAllowed":False}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--reference",type=Path)
    p.add_argument("--repo",default="Elikers/hyperliquid-btc-dashboard")
    p.add_argument("--out",type=Path,default=Path("test-output/pine_parity_gate.json"))
    args=p.parse_args()
    if args.reference is None or not args.reference.exists():
        result=unavailable("INDEPENDENT_ORIGINAL_PINE_BAR_EXPORT_NOT_AVAILABLE")
    else:
        import os
        token=os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("Read-only GitHub token required")
        snapshots,run,artifact=fetch_latest_snapshots(args.repo,token)
        result=audit(snapshots,json.loads(args.reference.read_text(encoding="utf-8")))
        result["historicalSourceRunId"]=run
        result["historicalSourceArtifactId"]=artifact
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("Pine parity gate:",result["status"],"blockers:",result["blockers"])
    print("Unverified Pine parity never allows Discord alerts or trading")

if __name__=="__main__":
    main()
