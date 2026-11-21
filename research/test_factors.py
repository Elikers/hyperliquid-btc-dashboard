import unittest
from math import isclose
from research.factors import ema, rma, rsi, sma, dmi_adx, compute_seven_factors

STEP = 900000


def candles(n=150, *, start=0, step=STEP):
    return [{"t": start+i*step, "T": start+(i+1)*step-1,
             "o": 100+i*.25, "h": 101+i*.25, "l": 99+i*.25,
             "c": 100+i*.25+(.1 if i%2 else -.1), "v": 10+i%9}
            for i in range(n)]


class FactorTests(unittest.TestCase):
    def test_ema_first_value_seed(self):
        x = ema([5., 7., 9.], 9)
        self.assertTrue(isclose(x[0], 5))
        self.assertTrue(isclose(x[1], 5.4))
        self.assertTrue(isclose(x[2], 6.12))

    def test_wilder_rma_seed(self):
        self.assertEqual(rma([1.,2.,3.,4.],3), [None,None,2.,8/3])

    def test_flat_rsi_is_50(self):
        self.assertEqual(rsi([100.]*30)[-1],50)

    def test_rising_rsi_is_100(self):
        self.assertEqual(rsi(list(range(30)))[-1],100)

    def test_volume_sma(self):
        self.assertEqual(sma([1.,2.,3.],2),[None,1.5,2.5])

    def test_adx_is_bounded(self):
        x=candles()
        a=dmi_adx([z["h"] for z in x],[z["l"] for z in x],[z["c"] for z in x])
        self.assertTrue(0<=a[-1]<=100)

    def test_all_seven_factors(self):
        x=candles()
        result=compute_seven_factors(x,x)
        self.assertEqual(len(result["bullFactors"]),7)
        self.assertEqual(len(result["bearFactors"]),7)
        self.assertEqual(result["macroFactor"],"UNAVAILABLE")
        self.assertFalse(result["discordEligible"])
        self.assertFalse(result["originalViprasolVerified"])

    def test_30m_confirm_never_uses_future(self):
        x=compute_seven_factors(candles(160,step=STEP*2),candles(320),timeframe="30m")
        self.assertLessEqual(x["confirmationBarCloseMs"],x["barCloseMs"])

    def test_1h_confirm_never_uses_future(self):
        x=compute_seven_factors(candles(150,step=STEP*4),candles(600),timeframe="1h")
        self.assertLessEqual(x["confirmationBarCloseMs"],x["barCloseMs"])

    def test_stale_confirmation_rejected(self):
        with self.assertRaises(ValueError):
            compute_seven_factors(candles(start=STEP*1000),candles())

    def test_missing_candle_rejected(self):
        x=candles()
        x.pop(3)
        with self.assertRaises(ValueError):
            compute_seven_factors(x,candles())

    def test_negative_volume_rejected(self):
        x=candles()
        x[-1]["v"]=-5
        with self.assertRaises(ValueError):
            compute_seven_factors(x,candles())

    def test_insufficient_history_rejected(self):
        with self.assertRaises(ValueError):
            compute_seven_factors(candles(50),candles())

    def test_nan_rejected(self):
        x=candles()
        x[40]["c"]=float("nan")
        with self.assertRaises(ValueError):
            compute_seven_factors(x,candles())

    def test_scores_sum_exact_factor_booleans(self):
        x=candles()
        r=compute_seven_factors(x,x)
        self.assertEqual(r["bullScoreSeven"],sum(r["bullFactors"].values()))
        self.assertEqual(r["bearScoreSeven"],sum(r["bearFactors"].values()))


if __name__=="__main__":
    unittest.main()
