"""Compact, immutable, research-only forward evidence for each capture.

Store the latest closed exchange bar plus blocked candidate details for each
timeframe. Downstream replays must deduplicate by (timeframe, close_ms) because
the 1h bar is sampled repeatedly by 15-minute GitHub Actions. This record
is NOT a validated Pine signal or authorization to deliver trade alerts.
"""
import hashlib
import json
from pathlib import Path

TIMEFRAMES=("15m","30m","1h")
FIELDS=("o","h","l","c","v")


def compact_observation(snapshot, scores):
    if snapshot.get("discordEligible") is not False or scores.get("discordEligible") is not False:
        raise ValueError("Unverified source must explicitly block Discord")
    if scores.get("originalViprasolVerified") is not False:
        raise ValueError("Unverified research result cannot claim Pine parity")
    if scores.get("liveSignalAlerts") is not False:
        raise ValueError("Research cannot allow live signal alerts")
    if not scores.get("candleIntegrity",{}).get("passed"):
        raise ValueError("Cross-timeframe integrity was not verified")
    captured=scores.get("capturedAtUtc")
    if not isinstance(captured,str) or not captured:
        raise ValueError("Capture timestamp absent")
    output={"kind":"HYPERLIQUID_BTC_FORWARD_PAPER_EVIDENCE_V1",
            "capturedAtUtc":captured,"model":"VIPRASOL_CLASSIC_MACRO_OFF",
            "source":"Hyperliquid BTC public closed candles",
            "originalViprasolVerified":False,
            "discordEligible":False,"automaticTrading":False,
            "timeframes":{}}
    for tf in TIMEFRAMES:
        item=snapshot.get(tf)
        research=scores.get("viprasolClassicMacroOff",{}).get(tf)
        if not isinstance(item,dict) or not isinstance(research,dict):
            raise ValueError("Missing market or research timeframe: "+tf)
        if item.get("timeframe")!=tf or item.get("coin")!="BTC":
            raise ValueError("Unexpected exchange market")
        if item.get("capturedAtUtc")!=captured:
            raise ValueError("Mixed observation instants")
        if research.get("configuration")!="VIPRASOL_CLASSIC_MACRO_OFF":
            raise ValueError("Wrong research configuration")
        if research.get("discordEligible") is not False or research.get("originalViprasolVerified") is not False:
            raise ValueError("Unverified Classic must remain blocked")
        bars=item.get("closedCandles")
        if not isinstance(bars,list) or not bars:
            raise ValueError("No closed exchange bars")
        bar=bars[-1]
        close_ms=int(bar["T"])
        if close_ms!=int(research.get("closedThroughMs")):
            raise ValueError("Model and market used different bars")
        ohlcv={k:float(bar[k]) for k in FIELDS}
        from math import isfinite
        if not all(isfinite(x) for x in ohlcv.values()) or ohlcv["v"]<0:
            raise ValueError("Invalid OHLCV evidence")
        if not ohlcv["l"]<=min(ohlcv["o"],ohlcv["c"])<=max(ohlcv["o"],ohlcv["c"])<=ohlcv["h"]:
            raise ValueError("Invalid price evidence")
        ladder=research.get("hypotheticalRiskLadder")
        if ladder is not None and (ladder.get("researchOnly") is not True
                                  or ladder.get("discordEligible") is not False):
            raise ValueError("Risk ladder is not marked research only")
        output["timeframes"][tf]={
            "closedBarStartMs":int(bar["t"]),
            "closedBarEndMs":close_ms,
            "bar":ohlcv,"bullScore":int(research["bullScore"]),
            "bearScore":int(research["bearScore"]),
            "threshold":int(research["scoreThreshold"]),
            "rawCrossover":research["rawCrossover"],
            "hypotheticalDirection":research["hypotheticalDirection"],
            "hypotheticalRiskLadder":ladder,
            "blockedReasons":research["reasons"],
            "adr":research["adr"],
            "sourceVerified":False}
    payload=json.dumps(output,sort_keys=True,separators=(",",":"))
    output["recordSha256"]=hashlib.sha256(payload.encode()).hexdigest()
    return output


def main(folder="capture-output"):
    base=Path(folder)
    scores=json.loads((base/"research_candidates.json").read_text(encoding="utf-8"))
    source={tf:json.loads((base/f"btc_{tf}.json").read_text(encoding="utf-8"))
            for tf in TIMEFRAMES}
    output=compact_observation(source,scores)
    path=base/"forward_observation.json"
    path.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("Paper-only evidence: "+", ".join(
        f"{tf}={output['timeframes'][tf]['closedBarEndMs']}" for tf in TIMEFRAMES))
    return path


if __name__=="__main__":
    main()
