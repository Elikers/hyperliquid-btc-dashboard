import unittest
from research.classic_macro_off import evaluate_classic_macro_off
from research.factors import STEPS


def bars(tf="15m",days=16,extra=8):
    step=STEPS[tf]
    per_day=86400000//step
    return [{"t":i*step,"T":(i+1)*step-1,
             "o":100+i*.03,"h":101+i*.03,
             "l":99+i*.03,"c":100+i*.03,
             "v":10+i%7}
            for i in range(days*per_day+extra)]


class ClassicMacroOffTests(unittest.TestCase):
    def test_original_macro_off_configuration_needs_no_nasdaq(self):
        x=bars()
        r=evaluate_classic_macro_off(x,x,timeframe="15m",
                                     current_ms=x[-1]["T"]+1000)
        self.assertEqual(r["configuration"],"VIPRASOL_CLASSIC_MACRO_OFF")
        self.assertEqual(r["scoreDenominator"],7)
        self.assertFalse(r["nasdaqFeedRequired"])
        self.assertTrue(r["adr"]["available"])
        self.assertFalse(r["discordEligible"])
        self.assertFalse(r["originalViprasolVerified"])
        self.assertNotIn("NQ1_MACRO_UNVERIFIED",r["reasons"])

    def test_no_full_daily_history_no_signal(self):
        x=bars(days=12)
        r=evaluate_classic_macro_off(x,x,timeframe="15m",
                                     current_ms=x[-1]["T"]+1000)
        self.assertFalse(r["adr"]["available"])
        self.assertIsNone(r["hypotheticalDirection"])
        self.assertIn("ADR_INPUT_NOT_VERIFIED",r["reasons"])

    def test_one_hour_macro_off(self):
        btc=bars("1h")
        confirm=bars("15m",days=17)
        r=evaluate_classic_macro_off(btc,confirm,timeframe="1h",
                                     current_ms=btc[-1]["T"]+1000)
        self.assertTrue(r["adr"]["available"])
        self.assertFalse(r["automaticTrading"])

    def test_open_candle_excluded(self):
        x=bars()
        r=evaluate_classic_macro_off(x,x,timeframe="15m",
                                     current_ms=x[-1]["t"]+1000)
        self.assertEqual(r["closedThroughMs"],x[-2]["T"])

    def test_original_threshold_eight_clamps_to_seven(self):
        x=bars()
        result=evaluate_classic_macro_off(x,x,timeframe="15m",
                                         current_ms=x[-1]["T"]+1000,
                                         min_score=8)
        self.assertEqual(result["originalInputMinScore"],8)
        self.assertEqual(result["scoreThreshold"],7)
        self.assertEqual(result["scoreDenominator"],7)
        self.assertFalse(result["discordEligible"])

    def test_wrong_min_score_rejected(self):
        x=bars()
        with self.assertRaises(ValueError):
            evaluate_classic_macro_off(x,x,timeframe="15m",
                current_ms=x[-1]["T"]+1000,min_score=9)


if __name__=="__main__":
    unittest.main()
