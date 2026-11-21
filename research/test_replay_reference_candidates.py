import unittest
from research.replay_reference_candidates import replay_one


def setup(side="LONG"):
    return {"timeframe":"15m","side":side,"T":"899999",
            "entry":"100","sl":"99" if side=="LONG" else "101",
            "tp1":"101" if side=="LONG" else "99",
            "tp2":"102" if side=="LONG" else "98",
            "tp3":"103" if side=="LONG" else "97"}


def candle(t, high, low):
    return {"T":str(t),"high":str(high),"low":str(low)}


class CandidateReplayTests(unittest.TestCase):
    def test_stop_first_on_ambiguous_candle(self):
        trade=replay_one(setup(),[candle(1799999,104,98)])
        self.assertEqual(trade["outcome"],"SL")
        self.assertEqual(trade["grossR"],-1)

    def test_break_even_after_tp1(self):
        trade=replay_one(setup(),[candle(1799999,101.1,99.2),
                                  candle(2699999,100.5,99.9)])
        self.assertEqual(trade["outcome"],"BE")
        self.assertEqual(trade["grossR"],0)

    def test_three_r_target(self):
        trade=replay_one(setup(),[candle(1799999,103.1,99.1)])
        self.assertEqual(trade["outcome"],"TP3")
        self.assertEqual(trade["grossR"],3)

    def test_short_side(self):
        trade=replay_one(setup("SHORT"),[candle(1799999,100.2,96.9)])
        self.assertEqual(trade["outcome"],"TP3")
        self.assertEqual(trade["grossR"],3)

    def test_no_future_bar_is_open(self):
        trade=replay_one(setup(),[candle(899999,104,98)])
        self.assertEqual(trade["outcome"],"OPEN")
        self.assertIsNone(trade["grossR"])

    def test_hypothetical_fees_reduce_r(self):
        trade=replay_one(setup(),[candle(1799999,103.1,99.1)],
                         one_way_cost_bps=7)
        self.assertAlmostEqual(trade["netR"],3-0.0007*(100+103))

    def test_invalid_ladder_rejected(self):
        invalid=setup()
        invalid["tp2"]="99"
        with self.assertRaises(ValueError):
            replay_one(invalid,[])

    def test_bad_cost_rejected(self):
        with self.assertRaises(ValueError):
            replay_one(setup(),[],one_way_cost_bps=-2)

    def test_no_alert_permission(self):
        r=replay_one(setup(),[candle(1799999,103.1,99.1)])
        self.assertFalse(r["discordEligible"])
        self.assertTrue(r["researchOnly"])


if __name__=="__main__":
    unittest.main()
