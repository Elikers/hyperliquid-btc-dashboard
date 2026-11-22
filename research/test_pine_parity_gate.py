import unittest
from unittest.mock import patch

from research.pine_parity_gate import (
    SOURCE_SHA, REFERENCE_KIND, FACTOR_SET, audit, unavailable,
)


def reference(rows=None):
    return {
        "kind":REFERENCE_KIND,
        "source":"TradingView original Viprasol Pine",
        "sourcePineSha256":SOURCE_SHA,
        "macroFactorOnInput":False,"minScoreInput":5,
        "timeframes":rows or {"15m":[],"30m":[],"1h":[]},
    }


class PineParityGateTests(unittest.TestCase):
    def test_absent_independent_export_blocked(self):
        x=audit({},None)
        self.assertIn("INDEPENDENT_ORIGINAL_PINE_BAR_EXPORT_NOT_AVAILABLE",x["blockers"])
        self.assertFalse(x["fullOriginalViprasolVerified"])
        self.assertFalse(x["discordEligible"])
        self.assertFalse(x["automaticTrading"])

    def test_wrong_provenance_blocked(self):
        ref=reference()
        ref["source"]="Python generated samples"
        x=audit({},ref)
        self.assertIn("PINE_REFERENCE_PROVENANCE_OR_SETTINGS_UNCONFIRMED",x["blockers"])

    def test_missing_timeframe_blocked(self):
        ref=reference()
        ref["timeframes"].pop("1h")
        x=audit({},ref)
        self.assertIn("ORIGINAL_PINE_REFERENCE_TIMEFRAMES_MISSING",x["blockers"])

    @patch("research.pine_parity_gate.validated_candles")
    def test_empty_reference_is_not_parity(self,loaded):
        loaded.return_value=({tf:[{"T":i*step+step-1,"t":i*step}
                          for i in range(550)] for tf,step in
                          (("15m",900000),("30m",1800000),("1h",3600000))},None)
        x=audit({},reference())
        self.assertEqual(x["status"],"BLOCKED")
        self.assertFalse(x["independentPineExportAuthenticated"])
        self.assertFalse(x["profitabilityClaimAllowed"])

    @patch("research.factors.compute_seven_factors")
    @patch("research.pine_parity_gate.validated_candles")
    def test_factor_mismatch_is_reported_and_never_promoted(self,loaded,factors):
        intervals={"15m":900000,"30m":1800000,"1h":3600000}
        bars={}
        frames={}
        for tf,step in intervals.items():
            bars[tf]=[{"t":step*i,"T":step*(i+1)-1} for i in range(600)]
            frames[tf]=[]
            for idx in range(400,500):
                end=bars[tf][idx]["T"]
                bull={name:False for name in FACTOR_SET}
                bear={name:False for name in FACTOR_SET}
                if idx==450 and tf=="15m":
                    bull["ema"]=True
                frames[tf].append({
                    "closedBarEndMs":end,"bullFactors":bull,"bearFactors":bear,
                    "rawCrossover":None,"hypotheticalDirection":None})
        loaded.return_value=(bars,None)
        factors.return_value={"bullFactors":{n:False for n in FACTOR_SET},
                              "bearFactors":{n:False for n in FACTOR_SET}}
        def evaluator(*a,**kw):
            return {"rawCrossover":None,"hypotheticalDirection":None}
        output=audit({},reference(frames),evaluator=evaluator)
        self.assertEqual(output["byTimeframe"]["15m"]["factorAndSignalMismatches"],1)
        self.assertFalse(output["fullOriginalViprasolVerified"])
        self.assertFalse(output["discordEligible"])
        self.assertIn("15m:PINE_VS_RESEARCH_MISMATCH",output["blockers"])


if __name__=="__main__":
    unittest.main()
