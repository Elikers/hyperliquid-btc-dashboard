import unittest
from research.futures_alignment import align_native_nq_to_btc

STEP = 900000


def bars(count, *, first=0, step=STEP, start_value=100):
    return [{"t":first+i*step, "T":first+(i+1)*step-1,
             "o":start_value+i, "h":start_value+i+2,
             "l":start_value+i-1, "c":start_value+i+1,
             "v":10} for i in range(count)]


class FuturesAlignmentTests(unittest.TestCase):
    def test_no_future_cme_candle_leaks_into_btc(self):
        btc = bars(7)
        nq = bars(7,start_value=1000)
        result = align_native_nq_to_btc(btc,nq)
        self.assertEqual(result["macroClose"],[1001+i for i in range(7)])
        self.assertEqual(result["matchedNativeCloseMs"][3],btc[3]["T"])
        self.assertFalse(result["sourceVerified"])

    def test_pre_first_cme_bar_is_missing(self):
        btc=bars(6)
        nq=bars(3,first=2*STEP)
        result=align_native_nq_to_btc(btc,nq)
        self.assertEqual(result["macroClose"][:2],[None,None])
        self.assertEqual(result["missingCount"],2)

    def test_weekend_gap_is_forward_held_not_ema_recalculated(self):
        btc=bars(7)
        nq=[bars(1,start_value=1000)[0],
            bars(1,first=4*STEP,start_value=1100)[0]]
        result=align_native_nq_to_btc(btc,nq,max_age_intervals=5)
        self.assertEqual(result["macroClose"][:4],[1001]*4)
        self.assertEqual(result["macroClose"][4:], [1101]*3)
        self.assertAlmostEqual(result["macroEma"][4],
                               1001+2/22*100)
        self.assertEqual(result["macroEma"][1],1001+0.0)

    def test_data_is_marked_stale_after_age_limit(self):
        btc=bars(7)
        nq=bars(1,start_value=1000)
        result=align_native_nq_to_btc(btc,nq,max_age_intervals=2)
        self.assertEqual(result["macroClose"][:3],[1001]*3)
        self.assertTrue(all(x is None for x in result["macroClose"][3:]))

    def test_malformed_futures_bar_rejected(self):
        btc=bars(3)
        nq=bars(3)
        nq[1]["h"]=nq[1]["l"]-1
        with self.assertRaises(ValueError):
            align_native_nq_to_btc(btc,nq)

    def test_duplicate_futures_bar_rejected(self):
        btc=bars(3)
        nq=bars(3)
        nq.insert(1,dict(nq[0]))
        with self.assertRaises(ValueError):
            align_native_nq_to_btc(btc,nq)

    def test_unclosed_btc_bar_fails(self):
        btc=bars(3)
        nq=bars(3)
        with self.assertRaises(ValueError):
            align_native_nq_to_btc(btc,nq,current_ms=btc[-1]["T"])

    def test_futures_unclosed_bar_is_dropped(self):
        btc=bars(3)
        nq=bars(4,start_value=1000)
        result=align_native_nq_to_btc(
            btc,nq,current_ms=btc[-1]["T"]+1)
        self.assertEqual(result["nativeFuturesBars"],3)
        self.assertEqual(result["macroClose"][-1],1003)


if __name__ == "__main__":
    unittest.main()
