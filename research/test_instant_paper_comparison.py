import unittest
from unittest.mock import patch

from research.instant_paper_comparison import compare_historical_paper


def bars(step, n=50):
    return [dict(t=i*step, T=(i+1)*step-1, o=100., h=102., l=98., c=100., v=12.) for i in range(n)]


def example():
    frames = {"15m": bars(900000), "30m": bars(1800000), "1h": bars(3600000)}
    return frames


class PairedReplayTests(unittest.TestCase):
    @patch("research.instant_paper_comparison.backtest_research")
    @patch("research.instant_paper_comparison.validated_candles")
    def test_closed_bar_gate_and_independent_forward_flags(self, read, backtest):
        frames = example()
        read.return_value = (frames, None)
        entry = frames["15m"][30]["T"]
        backtest.return_value = {"hypotheticalTrades": [
            {"timeframe":"15m", "closedBarEndMs":entry, "side":"LONG",
             "outcome":"SL", "netRByOneWayCostBps":{"0":-1, "7":-1.1, "15":-1.2}}
        ]}
        r = compare_historical_paper({}, source_run_id=123)
        self.assertEqual(r["sourceRunId"], 123)
        self.assertEqual(r["timeframes"]["15m"]["unchangedClassic"]["candidates"], 1)
        self.assertEqual(r["timeframes"]["30m"]["unchangedClassic"]["candidates"], 0)
        self.assertFalse(r["discordEligible"])
        self.assertFalse(r["automaticTrading"])
        self.assertFalse(r["profitabilityClaimAllowed"])
        self.assertFalse(r["recoveredCandlesAreForwardObservations"])

    @patch("research.instant_paper_comparison.backtest_research")
    @patch("research.instant_paper_comparison.validated_candles")
    def test_fail_closed_if_signal_missing(self, read, backtest):
        read.return_value = (example(), None)
        backtest.return_value = {"hypotheticalTrades": [
            {"timeframe":"15m", "closedBarEndMs":777, "side":"LONG",
             "outcome":"SL", "netRByOneWayCostBps":{"0":-1,"7":-1,"15":-1}}
        ]}
        with self.assertRaises(ValueError):
            compare_historical_paper({})

    @patch("research.instant_paper_comparison.backtest_research")
    @patch("research.instant_paper_comparison.validated_candles")
    def test_gate_selection_excludes_post_signal_candles(self, read, backtest):
        frames=example()
        entry=frames["15m"][30]["T"]
        backtest.return_value={"hypotheticalTrades":[
            {"timeframe":"15m","closedBarEndMs":entry,"side":"SHORT",
             "outcome":"TP3","netRByOneWayCostBps":{"0":3.,"7":2.8,"15":2.5}}
        ]}
        read.return_value=(frames,None)
        original=compare_historical_paper({})["timeframes"]["15m"]
        for later in frames["15m"][31:]:
            later.update(o=900.,h=1000.,l=800.,c=950.)
        changed=compare_historical_paper({})["timeframes"]["15m"]
        self.assertEqual(original,changed)


if __name__ == "__main__":
    unittest.main()
