import unittest
from research.cross_timeframe_audit import audit_cross_timeframe

STEP=900000

def fixture(groups=24):
    base=[{"t":i*STEP,"T":(i+1)*STEP-1,
           "o":101+i,"h":105+i,"l":99+i,"c":102+i,"v":10+i}
          for i in range(groups*4)]
    data={"15m":base}
    for tf,n in (("30m",2),("1h",4)):
        out=[]
        for start in range(0,len(base),n):
            chunk=base[start:start+n]
            out.append({"t":chunk[0]["t"],"T":chunk[-1]["T"],
                "o":chunk[0]["o"],"h":max(b["h"] for b in chunk),
                "l":min(b["l"] for b in chunk),"c":chunk[-1]["c"],
                "v":sum(b["v"] for b in chunk)})
        data[tf]=out
    return data

class CrossTFTests(unittest.TestCase):
    def test_identical_market_bars_pass(self):
        r=audit_cross_timeframe(fixture())
        self.assertTrue(r["passed"])
        self.assertFalse(r["discord_eligible"])
        self.assertEqual(r["timeframes"]["1h"]["complete_groups"],24)

    def test_hourly_low_difference_detected(self):
        data=fixture()
        data["1h"][0]["l"]+=1
        r=audit_cross_timeframe(data)
        self.assertFalse(r["passed"])
        self.assertEqual(r["timeframes"]["1h"]["mismatch_count"],1)

    def test_volume_difference_detected(self):
        data=fixture()
        data["30m"][3]["v"]+=100
        self.assertFalse(audit_cross_timeframe(data)["passed"])

    def test_incomplete_coverage_fails_closed(self):
        data=fixture()
        data["15m"]=data["15m"][-20:]
        r=audit_cross_timeframe(data)
        self.assertFalse(r["passed"])
        self.assertEqual(r["timeframes"]["1h"]["complete_groups"],5)

    def test_edge_partial_is_ignored(self):
        data=fixture()
        data["15m"]=data["15m"][1:]
        r=audit_cross_timeframe(data)
        self.assertTrue(r["passed"])
        self.assertEqual(r["timeframes"]["1h"]["partial_or_nonoverlap"],1)

    def test_midstream_missing_bar_rejected(self):
        data=fixture()
        data["15m"].pop(12)
        with self.assertRaises(ValueError):
            audit_cross_timeframe(data)

    def test_duplicate_bar_rejected(self):
        data=fixture()
        data["15m"].insert(1,dict(data["15m"][0]))
        with self.assertRaises(ValueError):
            audit_cross_timeframe(data)

    def test_invalid_high_rejected(self):
        data=fixture()
        data["30m"][0]["h"]=0
        with self.assertRaises(ValueError):
            audit_cross_timeframe(data)

    def test_all_timeframes_required(self):
        with self.assertRaises(ValueError):
            audit_cross_timeframe({"15m":[]})

if __name__=="__main__":
    unittest.main()
