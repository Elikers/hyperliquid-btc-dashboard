import unittest
from math import isclose
from research.risk_ladder import atr,ladder,audit_outcome


def bar(o=100,h=103,l=99,c=101):
    return {"o":o,"h":h,"l":l,"c":c}

class RiskTests(unittest.TestCase):
    def test_atr_constant_true_range(self):
        bars=[bar() for _ in range(20)]
        self.assertTrue(isclose(atr(bars,14),4))

    def test_atr_short_history_no_result(self):
        self.assertIsNone(atr([bar() for _ in range(10)],14))

    def test_atr_gap_uses_previous_close(self):
        candles=[bar(100,101,99,100) for _ in range(14)]
        candles[-1]=bar(120,125,119,123)
        self.assertGreater(atr(candles,14),2)

    def test_long_levels(self):
        t=ladder(100,"LONG",2)
        self.assertAlmostEqual(t["risk"],3)
        self.assertAlmostEqual(t["stop"],97)
        self.assertEqual(t["targets"],[103,106,109])
        self.assertFalse(t["discordEligible"])

    def test_short_levels(self):
        t=ladder(100,"SHORT",2)
        self.assertEqual(t["stop"],103)
        self.assertEqual(t["targets"],[97,94,91])

    def test_invalid_risk_input(self):
        with self.assertRaises(ValueError):
            ladder(100,"LONG",float("nan"))

    def test_same_bar_stop_before_tp(self):
        t=ladder(100,"LONG",2)
        r=audit_outcome(t,[bar(100,110,95,102)])
        self.assertEqual(r["outcome"],"SL")
        self.assertFalse(r["targetsHit"][0])

    def test_tp1_then_breakeven_next_bar(self):
        t=ladder(100,"LONG",2)
        r=audit_outcome(t,[bar(100,104,100.5,103),
                             bar(100,101,99,100)])
        self.assertEqual(r["outcome"],"BE")
        self.assertEqual(r["bars"],2)
        self.assertTrue(r["targetsHit"][0])

    def test_three_targets_closes_trade(self):
        t=ladder(100,"LONG",2)
        r=audit_outcome(t,[bar(100,110,100,109)])
        self.assertEqual(r["outcome"],"TP3")
        self.assertTrue(all(r["targetsHit"]))

    def test_short_stop(self):
        t=ladder(100,"SHORT",2)
        self.assertEqual(audit_outcome(t,[bar(100,104,90,95)])["outcome"],"SL")

    def test_open_outcome(self):
        t=ladder(100,"LONG",2)
        self.assertEqual(audit_outcome(t,[])["outcome"],"OPEN")


if __name__=="__main__":
    unittest.main()
