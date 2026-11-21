import unittest
from research.pipeline import calculate_research_candidate

STEP=900000

def candles(n=150, *, step=STEP):
    return [{"t":i*step,"T":(i+1)*step-1,
             "o":100+i*.2,"h":101+i*.2,"l":99+i*.2,
             "c":100+i*.2,"v":10+i%7} for i in range(n)]

class PipelineTests(unittest.TestCase):
    def test_closed_bars_are_research_only(self):
        x=candles()
        r=calculate_research_candidate(x,x,timeframe="15m",
            current_ms=x[-1]["T"]+1)
        self.assertFalse(r["discordEligible"])
        self.assertFalse(r["originalViprasolVerified"])
        self.assertIsNone(r["researchDecision"]["candidate"])
        self.assertIn("NQ1_MACRO_UNVERIFIED",
            r["researchDecision"]["reasons"])

    def test_unclosed_last_bar_is_dropped(self):
        x=candles(151)
        r=calculate_research_candidate(x,x,timeframe="15m",
            current_ms=x[-1]["t"]+1000)
        self.assertEqual(r["closedThrough"], x[-2]["T"])

    def test_insufficient_closed_history_fails(self):
        x=candles(100)
        with self.assertRaises(ValueError):
            calculate_research_candidate(x,x,timeframe="15m",
                current_ms=x[-1]["t"]+1)

if __name__ == "__main__":
    unittest.main()
