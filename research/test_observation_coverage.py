import unittest
from datetime import datetime, timezone, timedelta

from research.observation_coverage import observation_coverage
from research.forward_paper_ledger import STEPS

ORIGIN=datetime(2026,11,21,12,0,tzinfo=timezone.utc)


def evidence(capture_minute, candle_index):
    stamp=ORIGIN+timedelta(minutes=capture_minute)
    frames={}
    for tf,step in STEPS.items():
        interval=int(timedelta(minutes=15).total_seconds()*1000)
        # Choose an exchange bar that closes exactly at or before capture
        close=int((ORIGIN.timestamp()*1000)//step)*step+step-1+step*candle_index
        frames[tf]={"closedBarEndMs":close}
    return {"capturedAtUtc":stamp.isoformat(),"timeframes":frames}


def bar_end(tf,index):
    step=STEPS[tf]
    return int(ORIGIN.timestamp()*1000)+step*(index+1)-1


class ObservationCoverageTests(unittest.TestCase):
    def test_empty_window_reports_edges_without_inventing_data(self):
        out=observation_coverage([],after=ORIGIN,through=ORIGIN+timedelta(hours=1))
        self.assertEqual(out["byTimeframe"]["15m"]["expectedClosedBars"],4)
        self.assertEqual(out["byTimeframe"]["15m"]["unobservedClosedBars"],4)
        self.assertEqual(out["byTimeframe"]["15m"]["leadingUnobservedBars"],4)
        self.assertEqual(out["byTimeframe"]["15m"]["trailingUnobservedBars"],4)
        self.assertEqual(out["byTimeframe"]["15m"]["internalUnobservedBars"],0)
        self.assertFalse(out["profitabilityClaimAllowed"])

    def test_interior_and_edge_gaps(self):
        # Three distinct 15m bar closes in a one-hour window:
        # 12:14:59.999, 12:29:59.999, 12:44:59.999, 12:59:59.999.
        records=[]
        for idx,minute in [(0,15),(2,45)]:
            data=evidence(minute,idx)
            data["timeframes"]["15m"]["closedBarEndMs"]=bar_end("15m",idx)
            records.append(data)
        out=observation_coverage(records,after=ORIGIN,
                                  through=ORIGIN+timedelta(hours=1))
        score=out["byTimeframe"]["15m"]
        self.assertEqual(score["expectedClosedBars"],4)
        self.assertEqual(score["observedUniqueClosedBars"],2)
        self.assertEqual(score["leadingUnobservedBars"],0)
        self.assertEqual(score["internalUnobservedBars"],1)
        self.assertEqual(score["trailingUnobservedBars"],1)
        self.assertEqual(score["observationCoverageFraction"],0.5)

    def test_duplicates_do_not_increase_observation_coverage(self):
        r=evidence(15,0)
        r["timeframes"]["15m"]["closedBarEndMs"]=bar_end("15m",0)
        out=observation_coverage([r,r],after=ORIGIN,
                                  through=ORIGIN+timedelta(minutes=15))
        s=out["byTimeframe"]["15m"]
        self.assertEqual(s["capturesWithinWindow"],2)
        self.assertEqual(s["observedUniqueClosedBars"],1)
        self.assertTrue(s["continuousClosedBarCoverage"])

    def test_future_capture_ignored(self):
        r=evidence(80,0)
        r["timeframes"]["15m"]["closedBarEndMs"]=bar_end("15m",0)
        s=observation_coverage([r],after=ORIGIN,
                               through=ORIGIN+timedelta(minutes=15))["byTimeframe"]["15m"]
        self.assertEqual(s["observedUniqueClosedBars"],0)

    def test_no_closed_bars_returns_null_fraction(self):
        out=observation_coverage([],after=ORIGIN,
                                  through=ORIGIN+timedelta(seconds=1))
        s=out["byTimeframe"]["15m"]
        self.assertEqual(s["expectedClosedBars"],0)
        self.assertIsNone(s["observationCoverageFraction"])

    def test_reject_naive_date_window(self):
        with self.assertRaises(ValueError):
            observation_coverage([],after=ORIGIN.replace(tzinfo=None),through=ORIGIN)

    def test_reject_inverted_window(self):
        with self.assertRaises(ValueError):
            observation_coverage([],after=ORIGIN,through=ORIGIN)

    def test_independent_1h_coverage(self):
        r=evidence(60,0)
        r["timeframes"]["1h"]["closedBarEndMs"]=bar_end("1h",0)
        out=observation_coverage([r],after=ORIGIN,through=ORIGIN+timedelta(hours=1))
        self.assertEqual(out["byTimeframe"]["1h"]["observedUniqueClosedBars"],1)


if __name__=="__main__":
    unittest.main()
