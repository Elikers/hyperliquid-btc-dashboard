"""Strict offline reconciliation of overlapping HISTORICAL-ONLY candle archives.

Never interpret candles retrieved after the fact as forward observations.
No network, trades, Discord, strategy scoring or synthetic candle filling.
"""
import hashlib
import json
from datetime import datetime, timezone

from research.parity_checks import TF_MS, check_candles
from research.historical_candle_archive import SOURCE, MODEL

KIND = "HYPERLIQUID_BTC_HISTORICAL_CANDLE_ARCHIVE_V1"


def _capture_ms(text):
    if not isinstance(text, str):
        raise ValueError("Missing capture timestamp")
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.utcoffset() is None:
        raise ValueError("Capture timestamp requires timezone")
    return int(dt.timestamp() * 1000)


def validate_archive(record):
    """Validate source schema, digest and individual contiguous exchange series."""
    if not isinstance(record, dict):
        raise ValueError("Not a historical archive")
    for name, expected in (
        ("kind", KIND), ("model", MODEL), ("source", SOURCE),
        ("market", "HYPERLIQUID:BTCUSDC.P"),
        ("historicalOnly", True),
        ("recoveredCandlesAreForwardObservations", False),
        ("originalViprasolVerified", False),
        ("discordEligible", False),
        ("automaticTrading", False),
        ("profitabilityClaimAllowed", False),
    ):
        if record.get(name) is not expected and record.get(name) != expected:
            raise ValueError(f"Unsafe historical archive metadata: {name}")
    sha = record.get("archiveSha256")
    if not isinstance(sha, str) or len(sha) != 64:
        raise ValueError("Missing archive integrity checksum")
    unsigned = {k: v for k, v in record.items() if k != "archiveSha256"}
    digest = hashlib.sha256(json.dumps(unsigned, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if digest != sha:
        raise ValueError("Historical archive checksum mismatch")
    captured = _capture_ms(record.get("capturedAtUtc"))
    if type(record.get("historicalWindowHours")) is not int or not 1 <= record["historicalWindowHours"] <= 72:
        raise ValueError("Invalid historical window")
    if set(record.get("timeframes", {})) != set(TF_MS):
        raise ValueError("Missing historical timeframe")
    cutoff = captured - record["historicalWindowHours"] * 3_600_000
    for tf, step in TF_MS.items():
        series = record["timeframes"][tf]
        if series.get("historicalOnly") is not True:
            raise ValueError("Timeframe is not historical-only")
        bars = series.get("candles")
        if not isinstance(bars, list) or not bars:
            raise ValueError("Empty historical series")
        checked = check_candles(bars, tf, min_count=1)
        if not checked.acceptable:
            raise ValueError("Invalid OHLCV: " + "; ".join(checked.reasons))
        if series.get("barCount") != len(bars):
            raise ValueError("Incorrect historical candle count")
        if series.get("firstCloseMs") != int(bars[0]["T"]) or series.get("lastCloseMs") != int(bars[-1]["T"]):
            raise ValueError("Incorrect historical edge")
        for bar in bars:
            end = int(bar["T"])
            if not cutoff <= end < captured - 3000:
                raise ValueError("Historical candle outside verified capture window")
    return captured


def reconcile_archives(records):
    """Deduplicate exact historical OHLCV, reject contradictions and expose gaps."""
    if not isinstance(records, list):
        raise ValueError("Archive list required")
    dedup = {tf: {} for tf in TF_MS}
    sources = set()
    overlaps = {tf: 0 for tf in TF_MS}
    for archive in records:
        capture = validate_archive(archive)
        sources.add(capture)
        for tf in TF_MS:
            for bar in archive["timeframes"][tf]["candles"]:
                end = int(bar["T"])
                normalized = tuple(float(bar[k]) for k in ("o", "h", "l", "c", "v"))
                if end in dedup[tf]:
                    if dedup[tf][end] != normalized:
                        raise ValueError(f"Conflicting historical OHLCV: {tf} {end}")
                    overlaps[tf] += 1
                else:
                    dedup[tf][end] = normalized
    result = {}
    for tf, step in TF_MS.items():
        ends = sorted(dedup[tf])
        gaps = []
        for prev, curr in zip(ends, ends[1:]):
            missing = (curr - prev) // step - 1
            if missing:
                gaps.append({"afterClosedBarEndMs": prev,
                             "beforeClosedBarEndMs": curr,
                             "missingBarCount": missing})
        missing_total = sum(g["missingBarCount"] for g in gaps)
        result[tf] = {
            "uniqueHistoricalClosedBars": len(ends),
            "overlappingIdenticalCandleCopies": overlaps[tf],
            "firstHistoricalClosedBarEndMs": ends[0] if ends else None,
            "lastHistoricalClosedBarEndMs": ends[-1] if ends else None,
            "internalHistoricalMissingBarCount": missing_total,
            "internalHistoricalGaps": gaps,
            "contiguousBetweenObservedEdges": bool(ends) and not gaps,
        }
    return {
        "kind": "BTC_HISTORICAL_ONLY_ARCHIVE_RECONCILIATION_V1",
        "archivesIngested": len(records),
        "uniqueCaptureTimes": len(sources),
        "byTimeframe": result,
        "historicalOnly": True,
        "recoveredCandlesAreForwardObservations": False,
        "originalViprasolVerified": False,
        "discordEligible": False,
        "automaticTrading": False,
        "profitabilityClaimAllowed": False,
        "noHistoricalTradeSignalsGenerated": True,
    }
