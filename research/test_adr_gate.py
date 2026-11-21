import unittest
from research.adr_gate import adr_percent_used, DAY_MS
from research.factors import STEPS

STEP=STEPS["15m"]

def bars(*,full_days=16,current_bars=8,start_bar=0):
    total=full_days*96+current_bars
    return [{"t":i*STEP,"T":(i+1)*STEP-1,
             "o":100,"h":105,"l":95,"c":100,"v":10}
            for i in range(start_bar,total)]


class ADRGateTests(unittest.TestCase):
    def test_fourteen_completed_days(self):
        r=adr_percent_used(bars())
        self.assertTrue(r["available"])
        self.assertAlmostEqual(r["adr"],10)
        self.assertAlmostEqual(r["usedPercent"],100)

    def test_incomplete_observation_rejected(self):
        r=adr_percent_used(bars(full_days=16,start_bar=2*96+5))
        self.assertFalse(r["available"])
        self.assertEqual(r["reason"],"PARTIAL_HISTORICAL_DAY")

    def test_insufficient_days_does_not_guess(self):
        r=adr_percent_used(bars(full_days=12))
        self.assertFalse(r["available"])
        self.assertIsNone(r["usedPercent"])

    def test_gap_rejected(self):
        x=bars()
        x.pop(5)
        with self.assertRaises(ValueError):
            adr_percent_used(x)

    def test_partial_current_day_used_only_until_last_close(self):
        x=bars(current_bars=2)
        x[-1]["h"]=115
        r=adr_percent_used(x)
        self.assertAlmostEqual(r["usedPercent"],200)

    def test_default_one_hour_support(self):
        step=STEPS["1h"]
        x=[{"t":i*step,"T":(i+1)*step-1,
            "o":100,"h":105,"l":95,"c":100,"v":10}
           for i in range(16*24+3)]
        r=adr_percent_used(x,timeframe="1h")
        self.assertTrue(r["available"])

    def test_adr_does_not_depend_on_future_days(self):
        x=bars()
        r=adr_percent_used(x)
        y=x+[{"t":(len(x))*STEP,"T":(len(x)+1)*STEP-1,
              "o":100,"h":105,"l":95,"c":100,"v":10}]
        self.assertEqual(r["adr"],adr_percent_used(y)["adr"])


if __name__=="__main__":
    unittest.main()
