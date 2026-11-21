import unittest
from research.independent_pine_full_bar_audit import compare_full_bar_pine,FACTORS

P={"sourcePlatform":"TradingView","sourceMode":"VIPRASOL_CLASSIC_MACRO_OFF",
   "pineSourceSha256":"00d41c3abfccb3747506185bf0515684b5d8cdaa4b85c4546384914e623f34de",
   "symbol":"HYPERLIQUID:BTCUSDC.P","settings":"original_unchanged",
   "exportMethod":"independently exported original Pine closed bars"}
STEPS={"15m":900000,"30m":1800000,"1h":3600000}


def bar(tf="15m",idx=0,signal=None):
    step=STEPS[tf]
    d={"timeframe":tf,"closedBarEndMs":step*(idx+1)-1,
       "signal":signal,"factors":{k:False for k in FACTORS}}
    if signal:
        p=100
        direction=1 if signal=="LONG" else -1
        d.update({"entry":p,"stop":p-direction,
                  "tp1":p+direction,"tp2":p+2*direction,
                  "tp3":p+3*direction})
    return d


class PineFullBarEvidenceTests(unittest.TestCase):
    def test_full_aligned_three_tf_sample_is_not_certification(self):
        rows=[bar(tf,0) for tf in STEPS]+[bar(tf,1,"LONG") for tf in STEPS]
        r=compare_full_bar_pine(rows,rows,provenance=P)
        self.assertTrue(r["allAlignedSampleFieldsMatch"])
        self.assertTrue(r["alignedSampleComplete"])
        self.assertFalse(r["independentTradingViewSourceVerified"])
        self.assertFalse(r["originalViprasolVerified"])
        self.assertFalse(r["discordEligible"])

    def test_reference_no_signal_bar_detects_extra_candidate(self):
        a=[bar(tf) for tf in STEPS]
        b=[bar(tf) for tf in STEPS]
        b[0]=bar("15m",0,"LONG")
        r=compare_full_bar_pine(a,b,provenance=P)
        self.assertEqual(len(r["signalDifferences"]),1)
        self.assertFalse(r["allAlignedSampleFieldsMatch"])

    def test_missing_no_signal_bar_detected(self):
        a=[bar(tf) for tf in STEPS]+[bar("15m",1)]
        b=a[:-1]
        r=compare_full_bar_pine(a,b,provenance=P)
        self.assertEqual(r["perTimeframe"]["15m"]["referenceBarsAbsentFromCandidate"],1)
        self.assertFalse(r["alignedSampleComplete"])

    def test_false_factor_agreement_is_rejected(self):
        a=[bar(tf) for tf in STEPS]
        b=[bar(tf) for tf in STEPS]
        b[1]["factors"]["vwap"]=True
        r=compare_full_bar_pine(a,b,provenance=P)
        self.assertEqual(r["factorDifferences"][0]["factor"],"vwap")
        self.assertFalse(r["allAlignedSampleFieldsMatch"])

    def test_price_ladder_difference_detected_including_atr_stop(self):
        a=[bar(tf,0,"LONG") for tf in STEPS]
        b=[bar(tf,0,"LONG") for tf in STEPS]
        b[0]["stop"]+=0.29780477
        r=compare_full_bar_pine(a,b,provenance=P)
        self.assertEqual(r["priceDifferences"][0]["field"],"stop")
        self.assertAlmostEqual(r["priceDifferences"][0]["absoluteDifference"],0.29780477)

    def test_unaligned_closed_bar_rejected(self):
        a=[bar("15m")]
        a[0]["closedBarEndMs"]+=1
        with self.assertRaises(ValueError):
            compare_full_bar_pine(a,[],provenance=P)

    def test_duplicate_closed_bar_rejected(self):
        x=bar("15m")
        with self.assertRaises(ValueError):
            compare_full_bar_pine([x,x],[],provenance=P)

    def test_false_optional_price_on_no_signal_rejected(self):
        x=bar("15m")
        x["entry"]=100
        with self.assertRaises(ValueError):
            compare_full_bar_pine([x],[],provenance=P)

    def test_missing_provenance_fails(self):
        with self.assertRaises(ValueError):
            compare_full_bar_pine([],[],provenance={})

    def test_wrong_market_fails(self):
        p={**P,"symbol":"BINANCE:BTCUSDT"}
        with self.assertRaises(ValueError):
            compare_full_bar_pine([],[],provenance=p)

    def test_reference_can_be_empty_but_not_complete(self):
        r=compare_full_bar_pine([],[],provenance=P)
        self.assertFalse(r["alignedSampleComplete"])
        self.assertFalse(r["profitabilityClaimAllowed"])

    def test_gap_in_both_reference_and_candidate_not_full_evidence(self):
        a=[bar(tf,0) for tf in STEPS]+[bar("15m",2)]
        r=compare_full_bar_pine(a,a,provenance=P)
        self.assertFalse(r["perTimeframe"]["15m"]["closedBarsGapFree"])
        self.assertFalse(r["alignedSampleComplete"])

    def test_unreasonable_tolerance_rejected(self):
        with self.assertRaises(ValueError):
            compare_full_bar_pine([],[],provenance=P,max_price_delta=-1)


if __name__=="__main__":
    unittest.main()
