import json
import unittest
from datetime import datetime,timezone

from research.backtest_real_btc_snapshot import (
    backtest_research, validated_candles, select_raw_snapshots,
    _exit_simulation, decode_snapshot_zip, fetch_latest_snapshots, SOURCE)
from research.factors import STEPS


def synthetic():
    # Real replay is performed from a GitHub market-data archive, never this fixture.
    length={"15m":1700,"30m":850,"1h":650}
    base=1792972800000
    return {tf:{
        "market":"HYPERLIQUID:BTCUSDC.P","coin":"BTC",
        "source":SOURCE,"timeframe":tf,
        "researchOnly":True,"viprasolVerified":False,"discordEligible":False,
        "capturedAtUtc":datetime.fromtimestamp(
            (base+1700*STEPS["15m"]+10000)/1000,timezone.utc).isoformat(),
        "closedCandles":[{"t":base+i*step,"T":base+(i+1)*step-1,
                          "o":100+i/100,"h":101+i/100,
                          "l":99+i/100,"c":100+i/100,"v":10}
                        for i in range(n)],
        "lastCloseMs":base+n*step-1,
    } for tf,(n,step) in ((tf,(length[tf],STEPS[tf])) for tf in length)}


class RealHistoricalResearchTests(unittest.TestCase):
    def test_reject_mixed_capture_instants(self):
        sample=synthetic()
        sample["1h"]["capturedAtUtc"]="2026-11-22T00:00:00+00:00"
        with self.assertRaises(ValueError):
            validated_candles(sample)

    def test_reject_trading_flags(self):
        sample=synthetic()
        sample["15m"]["discordEligible"]=True
        with self.assertRaises(ValueError):
            validated_candles(sample)

    def test_snapshot_artifacts_only_main_and_run_match(self):
        items=[
            {"id":1,"name":"btc-research-candles-10","expired":False,
             "created_at":"2026-11-21T23:00:00Z","workflow_run":{"id":10,"head_branch":"main"}},
            {"id":2,"name":"btc-paper-evidence-11","expired":False,
             "created_at":"2026-11-21T23:00:00Z","workflow_run":{"id":11,"head_branch":"main"}},
            {"id":3,"name":"btc-research-candles-22","expired":False,
             "created_at":"2026-11-21T23:00:00Z","workflow_run":{"id":22,"head_branch":"feature"}}
        ]
        self.assertEqual([x[1] for x in select_raw_snapshots(items)],[1])

    def test_long_intrabar_stop_precedes_target(self):
        candidate={"hypotheticalDirection":"LONG","hypotheticalRiskLadder":{
            "entry":100,"stop":99,"targets":[101,102,103]}}
        out=_exit_simulation(candidate,[{"o":100,"h":105,"l":98}])
        self.assertEqual(out["status"],"SL")
        self.assertEqual(out["grossR"],-1)
        self.assertLess(out["oneWayCostsNetR"]["7"],-1)

    def test_gap_open_is_adversely_priced(self):
        candidate={"hypotheticalDirection":"LONG","hypotheticalRiskLadder":{
            "entry":100,"stop":99,"targets":[101,102,103]}}
        out=_exit_simulation(candidate,[{"o":97,"h":100,"l":96}])
        self.assertEqual(out["grossR"],-3)

    def test_no_forward_bars_cannot_be_realized(self):
        candidate={"hypotheticalDirection":"SHORT","hypotheticalRiskLadder":{
            "entry":100,"stop":101,"targets":[99,98,97]}}
        out=_exit_simulation(candidate,[])
        self.assertEqual(out["status"],"OPEN")
        self.assertIsNone(out["grossR"])

    def test_breakeven_only_after_prior_tp1(self):
        candidate={"hypotheticalDirection":"LONG","hypotheticalRiskLadder":{
            "entry":100,"stop":99,"targets":[101,102,103]}}
        out=_exit_simulation(candidate,[{"o":100,"h":101.5,"l":99.5},
                                        {"o":100.2,"h":100.5,"l":99.9}])
        self.assertEqual(out["status"],"BE")
        self.assertLess(out["oneWayCostsNetR"]["7"],0)

    def test_reject_unsupported_market_repo(self):
        with self.assertRaises(ValueError):
            fetch_latest_snapshots("../bad","fake")

    def test_failed_empty_record_is_not_performance(self):
        with self.assertRaises(ValueError):
            backtest_research({})


if __name__=="__main__":
    unittest.main()
