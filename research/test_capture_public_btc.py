import unittest
from research.capture_public_btc import capture_one
from research.parity_checks import TF_MS


def sample(tf="15m", count=150):
    step=TF_MS[tf]
    return [
        {"t":i*step,"T":(i+1)*step-1,"o":"100",
         "h":"102","l":"99","c":"101","v":"3"}
        for i in range(count)
    ]


class CaptureTests(unittest.TestCase):
    def test_all_three_supported_timeframes(self):
        for tf in TF_MS:
            with self.subTest(tf=tf):
                bars=sample(tf)
                now=bars[-1]["T"]+5000
                x=capture_one(tf,now_ms=now,fetch=lambda query:bars)
                self.assertEqual(x["timeframe"],tf)
                self.assertEqual(len(x["closedCandles"]),150)
                self.assertFalse(x["discordEligible"])
                self.assertFalse(x["viprasolVerified"])

    def test_drops_open_bar(self):
        bars=sample(count=151)
        step=TF_MS["15m"]
        x=capture_one("15m",now_ms=150*step+4000,
            fetch=lambda query:bars)
        self.assertEqual(len(x["closedCandles"]),150)

    def test_refuses_gaps(self):
        bars=sample()
        bars.pop(20)
        with self.assertRaises(RuntimeError):
            capture_one("15m",now_ms=bars[-1]["T"]+5000,
                fetch=lambda query:bars)

    def test_refuses_stale_feed(self):
        bars=sample()
        with self.assertRaises(RuntimeError):
            capture_one("15m",now_ms=bars[-1]["T"]+
                10*TF_MS["15m"],fetch=lambda query:bars)

    def test_rejects_nonarray(self):
        with self.assertRaises(RuntimeError):
            capture_one("15m",now_ms=150*TF_MS["15m"],
                fetch=lambda query:{"error":"denied"})

    def test_rejects_unknown_timeframe(self):
        with self.assertRaises(ValueError):
            capture_one("5m")


if __name__=="__main__":
    unittest.main()
