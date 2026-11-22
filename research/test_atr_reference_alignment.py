import unittest
from unittest.mock import patch

from research.atr_reference_alignment import (
    audit_alignment,REFERENCE_START_MS,ENTRY,DISPLAYED_STOP,STEP_MS,
)


def sample():
    start=REFERENCE_START_MS-150*STEP_MS
    return [{"t":start+i*STEP_MS,"T":start+(i+1)*STEP_MS-1,
             "o":100.,"h":110.,"l":90.,"c":100.,"v":1.}
            for i in range(160)]


class AtrReferenceAlignmentTests(unittest.TestCase):
    @patch("research.atr_reference_alignment.validated_candles")
    def test_five_historical_offsets_and_safety_flags(self,validated):
        validated.return_value=({"15m":sample()},None)
        result=audit_alignment({})
        self.assertTrue(result["allOffsetWindowsAvailable"])
        self.assertEqual([r["offsetBars"] for r in result["rows"]],[-2,-1,0,1,2])
        self.assertEqual(result["rows"][2]["screenshotEntryMinusMarketClose"],ENTRY-100)
        self.assertAlmostEqual(result["rows"][2]["hypotheticalStop"],ENTRY-30)
        self.assertFalse(result["originalViprasolVerified"])
        self.assertFalse(result["discordEligible"])
        self.assertFalse(result["automaticTrading"])

    @patch("research.atr_reference_alignment.validated_candles")
    def test_missing_reference_interval_not_fabricated(self,validated):
        bars=sample()
        bars[:]=[bar for bar in bars if bar["t"]!=REFERENCE_START_MS]
        validated.return_value=({"15m":bars},None)
        output=audit_alignment({})
        self.assertFalse(output["rows"][2]["available"])
        self.assertFalse(output["allOffsetWindowsAvailable"])

    @patch("research.atr_reference_alignment.validated_candles")
    def test_no_future_bars_in_reference_atr(self,validated):
        bars=sample()
        validated.return_value=({"15m":bars},None)
        original=audit_alignment({})["rows"][2]["atr14"]
        for bar in bars:
            if bar["t"]>REFERENCE_START_MS:
                bar["h"]=99999.
                bar["l"]=1.
        self.assertEqual(audit_alignment({})["rows"][2]["atr14"],original)

    @patch("research.atr_reference_alignment.validated_candles")
    def test_reference_stop_never_claims_authenticated_feed(self,validated):
        validated.return_value=({"15m":sample()},None)
        x=audit_alignment({})
        self.assertEqual(x["screenshotStopRoundedToTenths"],DISPLAYED_STOP)
        self.assertFalse(x["sourceOHLCMatchesTradingViewVerified"])
        self.assertFalse(x["referenceScreenshotOriginalPineVerified"])
        self.assertFalse(x["profitabilityClaimAllowed"])


if __name__=="__main__":
    unittest.main()
