import unittest
from research.native_macro_audit import preview_native_nq

STEP=900000


def bars(n=160,*, start=0, price=100, spacing=1):
    return [{"t":i*STEP,"T":(i+1)*STEP-1,
             "o":price+i*.3,"h":price+i*.3+1,
             "l":price+i*.3-1,"c":price+i*.3,
             "v":10+i%7}
            for i in range(start,n,spacing)]


class NativeMacroAuditTests(unittest.TestCase):
    def test_sparse_realistic_futures_does_not_break_join(self):
        btc=bars()
        nq=bars(price=1000,spacing=4)
        r=preview_native_nq(btc,btc,nq,timeframe="15m",
                            current_ms=btc[-1]["T"]+1000)
        self.assertEqual(r["macroAlignment"]["nativeFuturesBars"],40)
        self.assertEqual(r["macroAlignment"]["missingCount"],0)
        self.assertFalse(r["discordEligible"])
        self.assertFalse(r["originalViprasolVerified"])

    def test_even_vendor_verified_does_not_enable_alerts(self):
        btc=bars()
        nq=bars(price=1000,spacing=3)
        r=preview_native_nq(btc,btc,nq,timeframe="15m",
                            current_ms=btc[-1]["T"]+1000,
                            macro_source_verified=True)
        self.assertFalse(r["discordEligible"])
        self.assertFalse(r["decision"]["discordEligible"])

    def test_future_cme_candles_are_ignored(self):
        btc=bars()
        nq=bars(161,price=1000)
        r=preview_native_nq(btc,btc,nq,timeframe="15m",
                            current_ms=btc[-1]["T"]+1000)
        self.assertEqual(r["macroAlignment"]["nativeFuturesBars"],160)

    def test_stale_macro_cannot_create_trade(self):
        btc=bars()
        nq=bars(15,price=1000)
        r=preview_native_nq(btc,btc,nq,timeframe="15m",
                            current_ms=btc[-1]["T"]+1000,
                            maximum_age_intervals=4,
                            macro_source_verified=False)
        self.assertEqual(r["macro"]["reason"],"MISSING_ALIGNED_MACRO_CLOSE")
        self.assertIsNone(r["decision"]["candidate"])
        self.assertFalse(r["discordEligible"])


if __name__=="__main__":
    unittest.main()
