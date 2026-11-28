import hashlib
import json
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from research.forward_paper_ledger import analyze_forward_records, STEPS, KIND


def record(index, *, event_tf=None, side=None, high=104, low=98,
           open_price=100, close_price=100, altered=False):
    frames={}
    for tf,step in STEPS.items():
        end=(index+1)*step-1
        ladder=None
        direction=None
        if event_tf==tf:
            direction=side
            ladder={"entry":100,"stop":99 if side=="LONG" else 101,
                    "targets":[101,102,103] if side=="LONG" else [99,98,97],
                    "side":side,"researchOnly":True,"discordEligible":False}
        frames[tf]={"closedBarStartMs":index*step,
            "closedBarEndMs":end,
            "bar":{"o":open_price,"h":max(high,open_price,close_price),
                   "l":min(low,open_price,close_price),"c":close_price,
                   "v":10 if not altered else 11},
            "bullScore":5,"bearScore":0,"threshold":5,
            "rawCrossover":direction,"hypotheticalDirection":direction,
            "hypotheticalRiskLadder":ladder,"blockedReasons":[],
            "adr":{"available":True},"sourceVerified":False}
    # Each record is captured just after its latest 1h candle closes.
    obs={"kind":KIND,"model":"VIPRASOL_CLASSIC_MACRO_OFF",
         "capturedAtUtc":datetime.fromtimestamp(
              ((index+1)*STEPS["1h"]+1000)/1000,tz=timezone.utc).isoformat(),
         "source":"Hyperliquid BTC public closed candles",
         "originalViprasolVerified":False,"discordEligible":False,
         "automaticTrading":False,"timeframes":frames}
    return reseal(obs)


def reseal(r):
    r["recordSha256"]=hashlib.sha256(json.dumps(
        {k:v for k,v in r.items() if k!="recordSha256"},
        sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return r


class ForwardLedgerTests(unittest.TestCase):
    def test_causal_next_open_then_tp3(self):
        first=record(0,event_tf="15m",side="LONG",high=100,low=99.5)
        entry_bar=record(5,high=104,low=99.5)
        out=analyze_forward_records([first,entry_bar])
        trade=out["trades"][0]
        self.assertEqual(trade["outcome"],"TP3")
        self.assertAlmostEqual(trade["grossR"],3)
        self.assertEqual(trade["entryPrice"],100)
        self.assertEqual(trade["firstExecutableBarOpenMs"],5*STEPS["15m"])
        self.assertTrue(trade["entryTimeCausal"])
        self.assertEqual(trade["preObservationOpensExcluded"],0)
        self.assertLess(trade["hypotheticalNetR"],3)
        self.assertFalse(out["discordEligible"])

    def test_pre_observation_open_is_excluded_and_ladder_reanchored(self):
        first=record(0,event_tf="1h",side="LONG",high=100,low=99.5)
        already_open=record(1)
        executable=record(2,open_price=102,close_price=103,
                          high=106,low=101.5)
        out=analyze_forward_records([first,already_open,executable])
        trade=out["trades"][0]
        self.assertEqual(trade["preObservationOpensExcluded"],1)
        self.assertEqual(trade["firstExecutableBarOpenMs"],2*STEPS["1h"])
        self.assertTrue(trade["entryTimeCausal"])
        self.assertEqual(trade["entryPrice"],102)
        self.assertEqual(trade["stop"],101)
        self.assertEqual(trade["targets"],[103,104,105])
        self.assertEqual(trade["outcome"],"TP3")
        self.assertEqual(trade["grossR"],3)

    def test_no_future_executable_open_is_not_a_trade(self):
        first=record(0,event_tf="1h",side="LONG",high=100,low=99.5)
        already_open=record(1)
        out=analyze_forward_records([first,already_open])
        trade=out["trades"][0]
        self.assertEqual(trade["outcome"],"AWAITING_CAUSAL_ENTRY")
        self.assertFalse(trade["entryTimeCausal"])
        self.assertIsNone(trade["firstExecutableBarOpenMs"])
        self.assertIsNone(trade["grossR"])
        self.assertEqual(out["byTimeframe"]["1h"]["awaitingCausalEntry"],1)

    def test_same_entry_bar_stop_precedes_target(self):
        first=record(0,event_tf="15m",side="LONG",high=100,low=99.5)
        entry_bar=record(5,high=104,low=98.5)
        result=analyze_forward_records([first,entry_bar])
        self.assertEqual(result["trades"][0]["outcome"],"SL")
        self.assertEqual(result["trades"][0]["grossR"],-1)

    def test_tp1_moves_stop_to_breakeven_only_on_later_bar(self):
        first=record(0,event_tf="15m",side="LONG",high=100,low=99.5)
        tp1_bar=record(5,high=101.5,low=99.5)
        be_bar=record(6,high=100.5,low=99.9)
        out=analyze_forward_records([first,tp1_bar,be_bar])
        self.assertEqual(out["trades"][0]["outcome"],"BE")
        self.assertEqual(out["trades"][0]["grossR"],0)

    def test_short_tp3(self):
        first=record(0,event_tf="30m",side="SHORT",high=100.5,low=99)
        entry_bar=record(3,high=100.5,low=96)
        result=analyze_forward_records([first,entry_bar])
        self.assertEqual(result["trades"][0]["outcome"],"TP3")
        self.assertEqual(result["trades"][0]["grossR"],3)

    def test_adverse_gap_stop_is_priced_at_open(self):
        first=record(0,event_tf="1h",side="LONG",high=100,low=99.5)
        entry_bar=record(2,high=100.5,low=99.5)
        gap_bar=record(3,open_price=97,close_price=98,high=99,low=96)
        result=analyze_forward_records([first,entry_bar,gap_bar])
        trade=result["trades"][0]
        self.assertEqual(trade["outcome"],"SL")
        self.assertEqual(trade["exitPrice"],97)
        self.assertEqual(trade["grossR"],-3)

    def test_duplicate_data_is_not_double_counted(self):
        first=record(0,event_tf="1h",side="LONG",high=100,low=99.5)
        second=deepcopy(first)
        result=analyze_forward_records([first,second])
        self.assertEqual(result["byTimeframe"]["1h"]["hypotheticalCandidates"],1)
        self.assertEqual(result["evidence"]["duplicateObservations"],3)
        self.assertEqual(result["trades"][0]["outcome"],"AWAITING_CAUSAL_ENTRY")

    def test_conflicting_duplicate_rejected(self):
        a=record(0)
        b=record(0,altered=True)
        with self.assertRaisesRegex(ValueError,"Contradictory"):
            analyze_forward_records([a,b])

    def test_gap_after_executable_entry_quarantines_trade(self):
        first=record(0,event_tf="1h",side="LONG",high=100,low=99.5)
        pre_observation=record(1)
        entry_bar=record(2,high=100,low=99.5)
        after_gap=record(4,high=104,low=99.5)
        result=analyze_forward_records(
            [first,pre_observation,entry_bar,after_gap])
        self.assertEqual(result["trades"][0]["outcome"],"DATA_GAP")
        self.assertIsNone(result["trades"][0]["grossR"])
        self.assertEqual(result["evidence"]["missingClosedBars"]["1h"],1)

    def test_bad_digest_rejected(self):
        a=record(0)
        a["timeframes"]["15m"]["bar"]["v"]=300
        with self.assertRaisesRegex(ValueError,"checksum"):
            analyze_forward_records([a])

    def test_reject_live_trading_flags(self):
        a=record(0)
        a["automaticTrading"]=True
        reseal(a)
        with self.assertRaisesRegex(ValueError,"remain off"):
            analyze_forward_records([a])

    def test_no_candidates_is_not_proof_of_profit(self):
        result=analyze_forward_records([record(0),record(1)])
        self.assertEqual(result["byTimeframe"]["15m"]["resolved"],0)
        self.assertFalse(result["profitableStrategyVerified"])

    def test_cost_bounds_rejected(self):
        with self.assertRaises(ValueError):
            analyze_forward_records([record(0)],one_way_cost_bps=-1)


if __name__=="__main__":
    unittest.main()
