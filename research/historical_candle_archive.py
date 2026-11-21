"""Archive closed Hyperliquid BTC candles for HISTORICAL-ONLY gap research.

The existing capture stage has already fetched and validated these candles.
This module does not call a market API, replay signals, create trades or
alter the source strategy. A recovered old candle is NOT a candle that the
system observed or scored in real time.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from research.parity_checks import TF_MS, check_candles

HISTORY_WINDOW_MS = 24 * 60 * 60 * 1000
SOURCE = "Hyperliquid official public candleSnapshot API"
MODEL = "HISTORICAL_CANDLES_ONLY_NO_FORWARD_SIGNALS"


def build_historical_archive(snapshots, *, hours=24):
    if not isinstance(hours, int) or isinstance(hours, bool) or not 1 <= hours <= 72:
        raise ValueError("Invalid historical archive window")
    if set(snapshots) != set(TF_MS):
        raise ValueError("Exactly 15m/30m/1h BTC snapshots required")
    captures = {x.get("capturedAtUtc") for x in snapshots.values()}
    if len(captures) != 1:
        raise ValueError("Mixed capture instants are unsafe")
    capture = captures.pop()
    if not isinstance(capture, str):
        raise ValueError("Capture timestamp missing")
    captured_at = datetime.fromisoformat(capture.replace("Z", "+00:00"))
    if captured_at.utcoffset() is None:
        raise ValueError("Capture timestamp must include timezone")
    capture_ms = int(captured_at.timestamp() * 1000)
    cutoff = capture_ms - hours * 60 * 60 * 1000
    out = {
        "kind": "HYPERLIQUID_BTC_HISTORICAL_CANDLE_ARCHIVE_V1",
        "model": MODEL,
        "source": SOURCE,
        "market": "HYPERLIQUID:BTCUSDC.P",
        "capturedAtUtc": capture,
        "historicalWindowHours": hours,
        "historicalOnly": True,
        "recoveredCandlesAreForwardObservations": False,
        "originalViprasolVerified": False,
        "discordEligible": False,
        "automaticTrading": False,
        "profitabilityClaimAllowed": False,
        "timeframes": {},
    }
    for tf, step in TF_MS.items():
        snap = snapshots[tf]
        if snap.get("coin") != "BTC" or snap.get("timeframe") != tf:
            raise ValueError("Wrong market/timeframe")
        if snap.get("source") != SOURCE or snap.get("researchOnly") is not True:
            raise ValueError("Unverified input provenance")
        if snap.get("viprasolVerified") is not False or snap.get("discordEligible") is not False:
            raise ValueError("Research and alert flags must remain disabled")
        original = snap.get("closedCandles")
        if not isinstance(original, list):
            raise ValueError("Missing closed candle history")
        check = check_candles(original, tf)
        if not check.acceptable:
            raise ValueError("Invalid source candles: " + "; ".join(check.reasons))
        selected = []
        for bar in original:
            end = int(bar["T"])
            if cutoff <= end < capture_ms - 3000:
                selected.append({
                    "t": int(bar["t"]), "T": end,
                    "o": float(bar["o"]), "h": float(bar["h"]),
                    "l": float(bar["l"]), "c": float(bar["c"]),
                    "v": float(bar["v"]),
                })
        if not selected:
            raise ValueError("Historical window contains no closed candles")
        if not check_candles(selected, tf, min_count=1).acceptable:
            raise ValueError("Historical window has missing or inconsistent bars")
        if int(snap.get("lastCloseMs", -1)) != int(original[-1]["T"]):
            raise ValueError("Snapshot latest close disagrees with candle array")
        out["timeframes"][tf] = {
            "barCount": len(selected),
            "firstCloseMs": selected[0]["T"],
            "lastCloseMs": selected[-1]["T"],
            "candles": selected,
            "historicalOnly": True,
        }
    payload = json.dumps(out, sort_keys=True, separators=(",", ":"), allow_nan=False)
    out["archiveSha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return out


def main(folder="capture-output", *, hours=24):
    base = Path(folder)
    data = {
        tf: json.loads((base / f"btc_{tf}.json").read_text(encoding="utf-8"))
        for tf in TF_MS
    }
    output = build_historical_archive(data, hours=hours)
    target = base / "historical_candles_only.json"
    target.write_text(json.dumps(output, sort_keys=True, indent=2, allow_nan=False) + "\n",
                      encoding="utf-8")
    print("HISTORICAL ONLY archive:", ", ".join(
        f"{tf}={output['timeframes'][tf]['barCount']} bars" for tf in TF_MS
    ), "NO forward signals, Discord or trading")
    return target


if __name__ == "__main__":
    main()
