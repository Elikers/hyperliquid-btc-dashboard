import copy
import unittest
from datetime import datetime, timezone

from research.parity_checks import TF_MS
from research.historical_candle_archive import build_historical_archive, SOURCE
from research.reconcile_historical_archives import reconcile_archives, validate_archive


def make_archive(end_at_ms):
    snaps = {}
    for tf, step in TF_MS.items():
        last_close = end_at_ms - end_at_ms % step - 1
        bars = []
        for i in range(110):
            end = last_close - (109-i) * step
            bars.append({"t": end-step+1, "T": end,
                         "o": "100", "h": "102", "l": "99",
                         "c": "101", "v": "3"})
        snaps[tf] = {
            "timeframe": tf, "coin": "BTC", "source": SOURCE,
            "researchOnly": True, "viprasolVerified": False,
            "discordEligible": False,
            "capturedAtUtc": datetime.fromtimestamp(
                (end_at_ms+5000)/1000,timezone.utc).isoformat(),
            "lastCloseMs": bars[-1]["T"], "closedCandles": bars,
        }
    return build_historical_archive(snaps)


BASE = 1_700_006_400_000
BASE -= BASE % 3_600_000


class HistoricalReconciliationTests(unittest.TestCase):
    def test_single_archive_verified(self):
        a=make_archive(BASE)
        self.assertGreater(validate_archive(a), 0)
        r=reconcile_archives([a])
        self.assertEqual(r["byTimeframe"]["15m"]["uniqueHistoricalClosedBars"],96)
        self.assertEqual(r["byTimeframe"]["15m"]["internalHistoricalMissingBarCount"],0)
        self.assertFalse(r["recoveredCandlesAreForwardObservations"])
        self.assertFalse(r["discordEligible"])

    def test_overlapping_archives_are_deduplicated(self):
        a,b=make_archive(BASE),make_archive(BASE+3_600_000)
        r=reconcile_archives([a,b])
        self.assertEqual(r["byTimeframe"]["15m"]["uniqueHistoricalClosedBars"],100)
        self.assertEqual(r["byTimeframe"]["30m"]["uniqueHistoricalClosedBars"],50)
        self.assertEqual(r["byTimeframe"]["1h"]["uniqueHistoricalClosedBars"],25)
        self.assertEqual(r["byTimeframe"]["15m"]["overlappingIdenticalCandleCopies"],92)
        self.assertEqual(r["byTimeframe"]["15m"]["internalHistoricalMissingBarCount"],0)

    def test_duplicate_archive_only_one_capture(self):
        a=make_archive(BASE)
        r=reconcile_archives([a,a])
        self.assertEqual(r["uniqueCaptureTimes"],1)
        self.assertEqual(r["byTimeframe"]["1h"]["uniqueHistoricalClosedBars"],24)

    def test_distant_archives_report_real_internal_gap(self):
        a=make_archive(BASE)
        b=make_archive(BASE + 3 * 24 * 3_600_000)
        r=reconcile_archives([a,b])
        self.assertGreater(r["byTimeframe"]["15m"]["internalHistoricalMissingBarCount"],0)
        self.assertFalse(r["byTimeframe"]["15m"]["contiguousBetweenObservedEdges"])

    def test_conflicting_overlapping_candle_is_rejected(self):
        a,b=make_archive(BASE),make_archive(BASE+3_600_000)
        # Modify a single overlapping candle, then recompute the archive digest:
        b["timeframes"]["15m"]["candles"][0]["c"]=100.5
        import hashlib,json
        payload={k:v for k,v in b.items() if k!="archiveSha256"}
        b["archiveSha256"]=hashlib.sha256(json.dumps(payload,sort_keys=True,
             separators=(",",":"),allow_nan=False).encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,"Conflicting historical OHLCV"):
            reconcile_archives([a,b])

    def test_tampered_digest_is_rejected(self):
        a=make_archive(BASE)
        a["timeframes"]["15m"]["candles"][0]["c"]=100.5
        with self.assertRaisesRegex(ValueError,"checksum mismatch"):
            reconcile_archives([a])

    def test_forward_record_not_accepted_as_archive(self):
        with self.assertRaises(ValueError):
            reconcile_archives([{"kind":"HYPERLIQUID_BTC_FORWARD_PAPER_EVIDENCE_V1"}])

    def test_alert_enabled_rejected_even_if_digest_is_recomputed(self):
        a=make_archive(BASE)
        a["discordEligible"]=True
        import hashlib,json
        payload={k:v for k,v in a.items() if k!="archiveSha256"}
        a["archiveSha256"]=hashlib.sha256(json.dumps(payload,sort_keys=True,
             separators=(",",":"),allow_nan=False).encode()).hexdigest()
        with self.assertRaises(ValueError):
            reconcile_archives([a])

    def test_empty_reconciliation_never_claims_coverage(self):
        r=reconcile_archives([])
        self.assertEqual(r["archivesIngested"],0)
        self.assertIsNone(r["byTimeframe"]["15m"]["firstHistoricalClosedBarEndMs"])
        self.assertFalse(r["byTimeframe"]["15m"]["contiguousBetweenObservedEdges"])
        self.assertFalse(r["profitabilityClaimAllowed"])


if __name__=="__main__":
    unittest.main()
