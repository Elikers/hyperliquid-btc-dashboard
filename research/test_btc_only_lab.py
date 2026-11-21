import unittest
from research.btc_only_lab import evaluate_btc_only_lab

STEP=900000

def bars(n=160, *, step=STEP):
    return [{"t":i*step,"T":(i+1)*step-1,
             "o":100+i*.2,"h":101+i*.2,"l":99+i*.2,
             "c":100+i*.2,"v":10+i%7} for i in range(n)]


class BtcOnlyLabTests(unittest.TestCase):
    def test_seven_factor_is_separate_and_no_alerts(self):
        x=bars()
        r=evaluate_btc_only_lab(x,x,timeframe="15m",
                                current_ms=x[-1]["T"]+1000)
        self.assertEqual(r["model"],"BTC_ONLY_LAB_SEVEN_FACTOR")
        self.assertEqual(r["scoreDenominator"],7)
        self.assertEqual(r["nasdaqFactor"],"NOT_USED")
        self.assertFalse(r["discordEligible"])
        self.assertFalse(r["originalViprasolVerified"])

    def test_skip_unclosed_bar(self):
        x=bars()
        r=evaluate_btc_only_lab(x,x,timeframe="15m",
                                current_ms=x[-1]["t"]+1000)
        self.assertEqual(r["barCloseMs"],x[-2]["T"])

    def test_30m_lab_with_15m_confirmation(self):
        btc=bars(150,step=STEP*2)
        confirm=bars(300)
        r=evaluate_btc_only_lab(btc,confirm,timeframe="30m",
                                current_ms=btc[-1]["T"]+1000)
        self.assertEqual(r["timeframe"],"30m")
        self.assertFalse(r["automaticTrading"])

    def test_wrong_score_threshold_fails(self):
        x=bars()
        with self.assertRaises(ValueError):
            evaluate_btc_only_lab(x,x,timeframe="15m",
                                  current_ms=x[-1]["T"]+1000,
                                  threshold=8)


if __name__=="__main__":
    unittest.main()
