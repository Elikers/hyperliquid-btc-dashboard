import unittest
from math import isclose
from research.macro_factor import correlation, macro_factor


def inp(mode="positive", verified=True, flip=False):
    xs=[float(i*i+2*i) for i in range(1,31)]
    ys=[-x if flip else x for x in xs]
    return macro_factor(xs,ys,[0.]*30,link_mode=mode,
                        source_verified=verified)


class MacroFormulaTests(unittest.TestCase):
    def test_positive_correlation(self):
        r=inp()
        self.assertTrue(isclose(r["correlation"],1))
        self.assertTrue(r["bull"])
        self.assertFalse(r["bear"])

    def test_inverse_correlation(self):
        r=inp(mode="inverse",flip=True)
        self.assertTrue(isclose(r["correlation"],-1))
        self.assertTrue(r["bull"])
        self.assertFalse(r["bear"])

    def test_direction_gate_macro_below_ema(self):
        xs=[float(i*i) for i in range(1,31)]
        r=macro_factor(xs,xs,[1000.]*30,source_verified=True)
        self.assertFalse(r["bull"])
        self.assertTrue(r["bear"])

    def test_decoupling_zero_factor(self):
        xs=[float(i*i) for i in range(1,31)]
        ys=[float((-1)**i*1000) for i in range(1,31)]
        r=macro_factor(xs,ys,[0.]*30,source_verified=True,threshold=.9)
        self.assertFalse(r["active"])
        self.assertFalse(r["bull"])
        self.assertFalse(r["bear"])

    def test_unverified_feed_never_gets_score(self):
        r=inp(verified=False)
        self.assertFalse(r["bull"])
        self.assertEqual(r["reason"],"SOURCE_UNVERIFIED")
        self.assertTrue(r["hypotheticalBull"])

    def test_missing_exchange_close_refused(self):
        xs=[float(i) for i in range(1,31)]
        xs[-3]=None
        r=macro_factor([float(i) for i in range(30)],xs,[0.]*30,
                       source_verified=True)
        self.assertEqual(r["reason"],"MISSING_ALIGNED_MACRO_CLOSE")
        self.assertFalse(r["bull"])

    def test_zero_variance_is_not_active(self):
        xs=[100.]*30
        r=macro_factor(xs,list(range(30)),[0.]*30,source_verified=True)
        self.assertEqual(r["reason"],"CORRELATION_UNDEFINED")
        self.assertFalse(r["active"])

    def test_length_mismatch_is_error(self):
        with self.assertRaises(ValueError):
            macro_factor([1.]*20,[2.]*21,[0.]*21)

    def test_short_history_inactive(self):
        r=macro_factor([1.,2.],[1.,2.],[0.,0.])
        self.assertEqual(r["reason"],"INSUFFICIENT_HISTORY")

    def test_threshold_edge_inclusive(self):
        r=inp()
        self.assertTrue(r["active"])

    def test_wrong_link_mode_error(self):
        with self.assertRaises(ValueError):
            inp(mode="neither")

    def test_negative_pearson(self):
        self.assertTrue(isclose(correlation([1.,2.,3.],[3.,2.,1.]),-1))


if __name__ == "__main__":
    unittest.main()
