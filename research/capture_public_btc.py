"""Capture public, closed Hyperliquid BTC candles without trading or secrets.

Run in GitHub Actions every 15 minutes and upload JSON artifacts (not Git commits).
This is scheduled RESEARCH SAMPLING, NOT continuous signal monitoring.
"""
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import json
import time

from research.parity_checks import TF_MS, check_candles

API = "https://api.hyperliquid.xyz/info"


def make_request(body):
    req = Request(API, method="POST", headers={
        "Content-Type":"application/json",
        "User-Agent":"btc-research-candle-capture/1.0",
    }, data=json.dumps(body).encode("utf-8"))
    with urlopen(req, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"Exchange HTTP {response.status}")
        return json.load(response)


def capture_one(timeframe, *, now_ms=None, fetch=make_request):
    if timeframe not in TF_MS:
        raise ValueError("Unsupported interval")
    now_ms = int(time.time()*1000) if now_ms is None else int(now_ms)
    step = TF_MS[timeframe]
    # Keep a common 650-hour lookback across timeframes. The 1h engine
    # needs 600+ closed candles, while the same time span requires 2600
    # separate 15m candles for a fresh confirmation on the final 1h bar.
    # Hyperliquid candleSnapshot supports up to 5000 recent candles.
    lookback_bars = {"15m": 2600, "30m": 1300, "1h": 650}[timeframe]
    query = {"type":"candleSnapshot","req":{
        "coin":"BTC","interval":timeframe,
        "startTime":now_ms-step*lookback_bars,"endTime":now_ms}}
    candles=fetch(query)
    if not isinstance(candles,list):
        raise RuntimeError("Unexpected exchange response")
    closed=sorted((c for c in candles if int(c["T"]) < now_ms-3000),
                  key=lambda x:int(x["t"]))
    result=check_candles(closed,timeframe)
    if not result.acceptable:
        raise RuntimeError("Candle integrity: "+"; ".join(result.reasons))
    latest=int(closed[-1]["T"])
    if now_ms-latest>3*step:
        raise RuntimeError("Stale exchange history")
    return {
        "market":"HYPERLIQUID:BTCUSDC.P","coin":"BTC",
        "source":"Hyperliquid official public candleSnapshot API",
        "timeframe":timeframe,"capturedAtUtc":datetime.fromtimestamp(
            now_ms/1000,timezone.utc).isoformat(),
        "closedCandles":closed,"lastCloseMs":latest,
        "researchOnly":True,"viprasolVerified":False,
        "discordEligible":False,
    }


def main():
    root=Path("capture-output")
    root.mkdir(exist_ok=True)
    # Freeze the observation timestamp for all three independent API calls.
    # Otherwise a 15m boundary between requests gives inconsistent close
    # cutoffs and mismatched confirmation-bar context.
    capture_time_ms=int(time.time()*1000)
    for tf in TF_MS:
        data=capture_one(tf,now_ms=capture_time_ms)
        path=root/f"btc_{tf}.json"
        path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
        print(f"{tf}: {len(data['closedCandles'])} checked closed bars -> {path}")
    (root/"STATUS.txt").write_text(
        "Research only. No macro NQ1 data, no Discord and no trade signals.\n",
        encoding="utf-8")


if __name__=="__main__":
    main()
