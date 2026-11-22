"""Read-only forward observation of the experimental BTC liquidity Lab.

This snapshot is evaluated only at the GitHub capture instant, unlike a
historical replay. It records no future outcome or claim of fill/profit.
Classic compact artifacts and signal engine are unchanged.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from research.factors import STEPS, clean
from research.lab_liquidity import lab_entry
from research.cross_timeframe_audit import audit_cross_timeframe

KIND = "HYPERLIQUID_BTC_LIQUIDITY_LAB_PROSPECTIVE_OBSERVATION_V1"


def observe(snapshots, *, evaluate=lab_entry):
    if set(snapshots) != set(STEPS):
        raise ValueError("Missing BTC timeframes")
    stamps = {snapshots[tf].get("capturedAtUtc") for tf in STEPS}
    if len(stamps) != 1 or None in stamps:
        raise ValueError("Mixed capture timestamps")
    captured = stamps.pop()
    capture_time = datetime.fromisoformat(captured.replace("Z","+00:00"))
    if capture_time.utcoffset() is None:
        raise ValueError("Naive capture time")
    capture_ms = int(capture_time.timestamp()*1000)
    bars = {}
    for tf in STEPS:
        snap = snapshots[tf]
        if (snap.get("coin")!="BTC" or snap.get("timeframe")!=tf or
            snap.get("market")!="HYPERLIQUID:BTCUSDC.P" or
            snap.get("source")!="Hyperliquid official public candleSnapshot API" or
            snap.get("researchOnly") is not True or
            snap.get("viprasolVerified") is not False or
            snap.get("discordEligible") is not False):
            raise ValueError("Untrusted timeframe source")
        bars[tf] = clean(snap.get("closedCandles",[]), STEPS[tf])
        if len(bars[tf]) < 100 or bars[tf][-1]["T"] != snap.get("lastCloseMs"):
            raise ValueError("Missing or inconsistent final candle")
        if bars[tf][-1]["T"] >= capture_ms-3000:
            raise ValueError("Latest bar not safely closed")
    if not audit_cross_timeframe(bars)["passed"]:
        raise ValueError("Cross-timeframe candle integrity failed")
    frames = {}
    for tf, history in bars.items():
        end = history[-1]["T"]
        confirmation = [bar for bar in bars["15m"] if bar["T"]<=end]
        decision = evaluate(history,confirmation,timeframe=tf)
        if decision is not None:
            if (decision.get("closedBarEndMs")!=end or
                decision.get("researchOnly") is not True or
                decision.get("originalViprasolVerified") is not False or
                decision.get("discordEligible") is not False or
                decision.get("automaticTrading") is not False or
                decision.get("side") not in ("LONG","SHORT")):
                raise ValueError("Unsafe or off-bar Lab candidate")
        frames[tf] = {
            "closedBarStartMs":history[-1]["t"],
            "closedBarEndMs":end,
            "bar":{k:history[-1][k] for k in ("o","h","l","c","v")},
            "researchCandidate":decision,
            "originalViprasolVerified":False,
        }
    output = {
        "kind":KIND,"capturedAtUtc":captured,
        "market":"HYPERLIQUID:BTCUSDC.P",
        "timeframes":frames,"researchOnly":True,
        "futureOutcomeKnown":False,"prospectivelyObserved":True,
        "historicalOnly":False,
        "originalViprasolVerified":False,"discordEligible":False,
        "automaticTrading":False,"profitabilityClaimAllowed":False,
    }
    payload=json.dumps(output,sort_keys=True,separators=(",",":"),allow_nan=False)
    output["recordSha256"]=hashlib.sha256(payload.encode()).hexdigest()
    return output


def main(folder="capture-output"):
    base=Path(folder)
    snapshots={tf:json.loads((base/f"btc_{tf}.json").read_text(encoding="utf-8"))
               for tf in STEPS}
    result=observe(snapshots)
    target=base/"liquidity_lab_forward_observation.json"
    target.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",
                      encoding="utf-8")
    print("LIQUIDITY LAB observation, research only:",
          ", ".join(f"{tf}={'CANDIDATE' if v['researchCandidate'] else 'NONE'}"
                    for tf,v in result["timeframes"].items()),
          "no known future outcomes; alerts and trading OFF")
    return target


if __name__=="__main__":
    main()
