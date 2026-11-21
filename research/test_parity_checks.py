import unittest
from research.parity_checks import (
    TF_MS, check_candles, check_macro_source, compare_reference_events, readiness_report
)


def bars(tf="15m", count=105, first=0):
    step = TF_MS[tf]
    return [{"t": first+i*step, "T": first+(i+1)*step-1,
             "o": "100", "h": "103", "l": "99", "c": "101", "v": "12"}
            for i in range(count)]


def trade(price=101):
    return {"tf": "15m", "side": "LONG", "closeTime": 900,
            "entry": price, "stop": 100, "targets": [102, 103, 104]}


class CandleTests(unittest.TestCase):
    def test_consecutive_bars_accepted(self):
        self.assertTrue(check_candles(bars(), "15m").acceptable)

    def test_both_hourly_and_half_hourly(self):
        for tf in ("30m", "1h"):
            with self.subTest(tf=tf):
                self.assertTrue(check_candles(bars(tf), tf).acceptable)

    def test_missing_history_fails(self):
        self.assertFalse(check_candles(bars(count=20), "15m").acceptable)

    def test_gap_fails(self):
        x = bars()
        x.pop(30)
        self.assertFalse(check_candles(x, "15m").acceptable)

    def test_bad_ohlc_fails(self):
        x = bars()
        x[5]["l"] = "104"
        self.assertFalse(check_candles(x, "15m").acceptable)

    def test_nan_and_negative_volume_fail(self):
        x = bars()
        x[4]["c"] = "nan"
        self.assertFalse(check_candles(x, "15m").acceptable)
        x = bars()
        x[4]["v"] = "-1"
        self.assertFalse(check_candles(x, "15m").acceptable)

    def test_wrong_timeframe_fails(self):
        self.assertFalse(check_candles(bars(), "2h").acceptable)


class MacroTests(unittest.TestCase):
    def test_yahoo_proxy_rejected(self):
        x = check_macro_source(symbol="NQ=F", provider="yahoo", timeframe="15m",
                               btc_bars=bars(), macro_bars=bars(),
                               same_tradingview_construction=True)
        self.assertFalse(x.acceptable)

    def test_unverified_roll_rejected(self):
        x = check_macro_source(symbol="CME_MINI:NQ1!", provider="licensed CME provider",
                               timeframe="15m", btc_bars=bars(), macro_bars=bars(),
                               same_tradingview_construction=False)
        self.assertFalse(x.acceptable)

    def test_source_audit_can_pass_without_certifying(self):
        x = check_macro_source(symbol="CME_MINI:NQ1!", provider="licensed CME provider",
                               timeframe="15m", btc_bars=bars(), macro_bars=bars(),
                               same_tradingview_construction=True)
        self.assertTrue(x.acceptable)
        self.assertFalse(readiness_report(x, {})["originalViprasolVerified"])


class ParityTests(unittest.TestCase):
    def test_matching_sample_not_full_verified(self):
        x = compare_reference_events([trade()], [trade()])
        self.assertTrue(x["sampleExactWithinTolerance"])
        self.assertFalse(x["originalViprasolVerified"])

    def test_empty_sample_is_not_evidence(self):
        self.assertFalse(compare_reference_events([], [])["sampleExactWithinTolerance"])

    def test_missing_and_extra_events_detected(self):
        a = trade()
        b = dict(trade(), closeTime=1800)
        x = compare_reference_events([a], [b])
        self.assertEqual(len(x["missing"]), 1)
        self.assertEqual(len(x["extra"]), 1)

    def test_price_mismatch_detected(self):
        x = compare_reference_events([trade()], [trade(102)])
        self.assertEqual(x["priceDifferences"][0]["field"], "entry")

    def test_duplicate_events_rejected(self):
        with self.assertRaises(ValueError):
            compare_reference_events([trade(), trade()], [trade()])

    def test_invalid_tolerance_rejected(self):
        with self.assertRaises(ValueError):
            compare_reference_events([], [], price_tolerance=-1)


if __name__ == "__main__":
    unittest.main()
