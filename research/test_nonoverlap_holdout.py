import unittest

from research.nonoverlap_holdout import (
    BARS, HOLDOUT_END_MS, build_holdout_snapshots, research_holdout,
)
from research.factors import STEPS


def fake_fetch(request):
    tf=request["req"]["interval"]
    start=request["req"]["startTime"]
    step=STEPS[tf]
    return [dict(t=start+i*step,T=start+(i+1)*step-1,
                 o=100.,h=102.,l=98.,c=100.,v=10.)
            for i in range(BARS[tf])]


class HoldoutTests(unittest.TestCase):
    def test_nonoverlap_window_and_provenance(self):
        result=build_holdout_snapshots(
            acquired_ms=HOLDOUT_END_MS+86400000*30,fetch=fake_fetch)
        self.assertEqual(result["15m"]["closedCandles"][-1]["T"],HOLDOUT_END_MS-1)
        self.assertEqual(result["1h"]["closedCandles"][0]["t"],
                         HOLDOUT_END_MS-BARS["1h"]*STEPS["1h"])
        self.assertFalse(result["30m"]["viprasolVerified"])
        self.assertFalse(result["30m"]["discordEligible"])

    def test_missing_source_candles_fail_closed(self):
        def incomplete(request):
            return fake_fetch(request)[:-1]
        output=research_holdout(
            acquired_ms=HOLDOUT_END_MS+86400000*30,fetch=incomplete)
        self.assertEqual(output["status"],"NOT_AVAILABLE")
        self.assertIsNone(output["comparison"])
        self.assertFalse(output["profitabilityClaimAllowed"])
        self.assertFalse(output["recoveredCandlesAreForwardObservations"])

    def test_gaps_are_rejected(self):
        def gap(request):
            rows=fake_fetch(request)
            rows.pop(70)
            return rows
        with self.assertRaises(ValueError):
            build_holdout_snapshots(
                acquired_ms=HOLDOUT_END_MS+86400000*30,fetch=gap)

    def test_fails_if_acquired_in_holdout_period(self):
        with self.assertRaises(ValueError):
            build_holdout_snapshots(acquired_ms=HOLDOUT_END_MS,fetch=fake_fetch)

    def test_transport_error_is_not_zero_trades(self):
        def bad(_):
            raise OSError("network unavailable")
        x=research_holdout(acquired_ms=HOLDOUT_END_MS+86400000*30,fetch=bad)
        self.assertEqual(x["status"],"NOT_AVAILABLE")
        self.assertIn("network unavailable",x["reason"])


if __name__=="__main__":
    unittest.main()
