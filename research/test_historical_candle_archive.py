import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research.historical_candle_archive import (
    build_historical_archive, main, SOURCE)
from research.parity_checks import TF_MS

CAPTURE_MS = 1_700_006_400_000  # rounded to hour, actual timezone date not important
CAPTURE_MS -= CAPTURE_MS % 3_600_000


def fixtures():
    snapshot = {}
    for tf, step in TF_MS.items():
        # At least 110 valid previous bars including a closed most-recent bar.
        end = CAPTURE_MS - 1
        bars = [
            {"t": end - (109-i)*step - step + 1,
             "T": end - (109-i)*step,
             "o": "100", "h": "102", "l": "99", "c": "101", "v": "3"}
            for i in range(110)
        ]
        snapshot[tf] = {
            "timeframe": tf, "coin": "BTC", "source": SOURCE,
            "capturedAtUtc": datetime.fromtimestamp(
                CAPTURE_MS / 1000, tz=timezone.utc).isoformat(),
            "researchOnly": True, "viprasolVerified": False,
            "discordEligible": False, "lastCloseMs": bars[-1]["T"],
            "closedCandles": bars,
        }
    return snapshot


class HistoryArchiveTests(unittest.TestCase):
    def test_closed_historical_bars_preserved_and_separated(self):
        data = build_historical_archive(fixtures())
        self.assertTrue(data["historicalOnly"])
        self.assertFalse(data["recoveredCandlesAreForwardObservations"])
        self.assertFalse(data["profitabilityClaimAllowed"])
        self.assertFalse(data["discordEligible"])
        self.assertFalse(data["automaticTrading"])
        self.assertEqual(data["timeframes"]["15m"]["barCount"], 96)
        self.assertEqual(data["timeframes"]["30m"]["barCount"], 48)
        self.assertEqual(data["timeframes"]["1h"]["barCount"], 24)
        payload = {k:v for k,v in data.items() if k != "archiveSha256"}
        self.assertEqual(data["archiveSha256"], hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       allow_nan=False).encode()).hexdigest())

    def test_not_mergeable_as_forward_record(self):
        data=build_historical_archive(fixtures())
        self.assertNotIn("recordSha256", data)
        self.assertNotIn("hypotheticalDirection", json.dumps(data))
        self.assertNotIn("hypotheticalRiskLadder", json.dumps(data))

    def test_refuse_mixed_capture_time(self):
        data = fixtures()
        data["1h"]["capturedAtUtc"] = "2026-11-22T00:00:00+00:00"
        with self.assertRaises(ValueError):
            build_historical_archive(data)

    def test_refuse_corrupted_interval(self):
        data = fixtures()
        data["15m"]["closedCandles"].pop(15)
        with self.assertRaises(ValueError):
            build_historical_archive(data)

    def test_refuse_source_with_alert_permission(self):
        data = fixtures()
        data["30m"]["discordEligible"] = True
        with self.assertRaises(ValueError):
            build_historical_archive(data)

    def test_refuse_latest_close_mismatch(self):
        data = fixtures()
        data["1h"]["lastCloseMs"] += 1
        with self.assertRaises(ValueError):
            build_historical_archive(data)

    def test_refuse_nonpositive_window(self):
        with self.assertRaises(ValueError):
            build_historical_archive(fixtures(), hours=0)

    def test_refuse_wrong_timeframe(self):
        data = fixtures()
        data["5m"] = data.pop("15m")
        with self.assertRaises(ValueError):
            build_historical_archive(data)

    def test_file_output_keeps_flags(self):
        data=fixtures()
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            for tf, snap in data.items():
                (folder / f"btc_{tf}.json").write_text(json.dumps(snap))
            target=main(folder)
            self.assertTrue(target.exists())
            result=json.loads(target.read_text())
            self.assertTrue(result["historicalOnly"])
            self.assertFalse(result["recoveredCandlesAreForwardObservations"])


if __name__=="__main__":
    unittest.main()
