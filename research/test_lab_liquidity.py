import unittest

from research.lab_liquidity import confirmed_sweep, next_open_stress, summarize_paper


def bars():
    values=[{"t":i*900000,"T":(i+1)*900000-1,
             "o":100.,"h":105.,"l":95.,"c":100.,"v":10.}
            for i in range(80)]
    values[60].update(h=110.)
    return values


class LiquidityLabTests(unittest.TestCase):
    def test_confirmed_high_sweep_only_after_right_bars(self):
        values=bars()
        values[-1].update(o=103.,h=111.,c=102.)
        self.assertEqual(confirmed_sweep(values),("SHORT",110.))

    def test_confirmed_low_reclaim(self):
        values=bars()
        values[60].update(h=105.,l=90.)
        values[-1].update(o=97.,l=89.,c=98.)
        self.assertEqual(confirmed_sweep(values),("LONG",90.))

    def test_unconfirmed_pivot_not_available(self):
        values=bars()
        values[60]["h"]=105.
        values[-4].update(h=110.)
        values[-1].update(o=103.,h=111.,c=102.)
        self.assertEqual(confirmed_sweep(values),(None,None))

    def test_no_sweep(self):
        self.assertEqual(confirmed_sweep(bars()),(None,None))

    def test_fill_price_not_signal_close(self):
        levels={"entry":100.,"stop":95.,"targets":[105.,110.,115.]}
        future=[{"o":101.,"h":115.,"l":100.,"c":110.}]
        result=next_open_stress("LONG",levels,future,adverse_entry_bps=3)
        self.assertEqual(result["status"],"TP3")
        self.assertGreater(result["fillPrice"],101.)
        self.assertNotEqual(result["fillPrice"],levels["entry"])
        self.assertGreater(result["netRByOneWayCostBps"]["0"],
                           result["netRByOneWayCostBps"]["15"])

    def test_open_outside_ladder_quarantined(self):
        levels={"entry":100.,"stop":95.,"targets":[105.,110.,115.]}
        future=[{"o":94.,"h":100.,"l":90.,"c":95.}]
        result=next_open_stress("LONG",levels,future)
        self.assertEqual(result["status"],"ENTRY_OUTSIDE_LADDER")
        self.assertIsNone(result["netRByOneWayCostBps"])

    def test_unresolved_does_not_create_return(self):
        levels={"entry":100.,"stop":95.,"targets":[105.,110.,115.]}
        self.assertIsNone(next_open_stress("LONG",levels,[])["netRByOneWayCostBps"])

    def test_summaries_fail_closed_on_unfillable(self):
        records=[{"timeframe":"15m","Classic":{
            "status":"ENTRY_OUTSIDE_LADDER","netRByOneWayCostBps":None}}]
        frame=summarize_paper(records)["15m"]["Classic"]
        self.assertEqual(frame["candidates"],1)
        self.assertEqual(frame["resolved"],0)
        self.assertEqual(frame["unresolvedOrUnfillable"],1)
        self.assertEqual(frame["netRSumByOneWayCostBps"]["7"],0)


if __name__=="__main__":
    unittest.main()
