import unittest
from research.regime_sweep_research import diagnostic

STEP = 900000


def bars(n=40):
    return [dict(t=i*STEP, T=(i+1)*STEP-1, o=100., h=102., l=98., c=100.) for i in range(n)]


class RegimeSweepResearchTests(unittest.TestCase):
    def test_rejected_high_sweep_only_uses_preceding_bars(self):
        data = bars()
        data[-1].update(h=103., c=99.)
        d = diagnostic(data)
        self.assertEqual(d["sweepSignal"], "BEARISH_SWEEP")
        self.assertFalse(d["discordEligible"])
        self.assertFalse(d["automaticTrading"])

    def test_rejected_low_sweep(self):
        data = bars()
        data[-1].update(l=97., c=101.)
        self.assertEqual(diagnostic(data)["sweepSignal"], "BULLISH_SWEEP")

    def test_no_sweep_on_flat_range(self):
        self.assertEqual(diagnostic(bars())["sweepSignal"], "NONE")

    def test_incomplete_history_rejected(self):
        with self.assertRaises(ValueError): diagnostic(bars(10))

    def test_gapped_bar_rejected(self):
        data = bars()
        data[-1]["t"] += STEP
        with self.assertRaises(ValueError): diagnostic(data)

    def test_zero_range_chop_is_not_invented(self):
        data = bars()
        for b in data: b.update(o=100., h=100., l=100., c=100.)
        self.assertIsNone(diagnostic(data)["choppinessIndex"])

    def test_invalid_lookback_rejected(self):
        with self.assertRaises(ValueError): diagnostic(bars(), swing_lookback=0)


if __name__ == "__main__":
    unittest.main()
