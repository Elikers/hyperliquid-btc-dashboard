import hashlib
import json
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from research.forward_paper_ledger import analyze_forward_records, STEPS, KIND


def record(index, *, event_tf=None, side=None, high=104, low=98, altered=False):
    frames={}
    for tf,step in STEPS.items():
        end=(index+1)*step-1
        entry=100
        ladder=None
        direction=None
        if event_tf==tf:
            direction=side
            ladder={"entry":entry,"stop":99 if side=="LONG" else 101,
                    "targets":[101,102,103] if side=="LONG" else [99,98,97],
                    "side":side,"researchOnly":True,"discordEligible":False}
        frames[tf]={"closedBarStartMs":index*step,
            "closedBarEndMs":end,
            "bar":{"o":100,"h":high,"l":low,"c":100,"v":10 if not altered else 11},
            "bullScore":5,"bearScore":0,"threshold":5,
            "rawCrossover":direction,"hypotheticalDirection":direction,
            "hypotheticalRiskLadder":ladder,"blockedReasons":[],
            "adr":{"available":True},"sourceVerified":False}
    obs={"kind":KIND,"model":"VIPRASOL_CLASSIC_MACRO_OFF",
         "capturedAtUtc":datetime.fromtimestamp(
              (index+2)*STEPS["1h"]/1000,tz=timezone.utc).isoformat(),
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
    def test_one_candidate_then_tp3_next_bar(self):
        first=record(0,event_tf="15m",side="LONG",high=100,low=99.5)
        next_=record(1,high=104,low=99.5)
        out=analyze_forward_records([first,next_])
        trade=out["trades"][0]
        self.assertEqual(trade["outcome"],"TP3")
        self.assertAlmostEqual(trade["grossR"],3)
        self.assertLess(trade["hypotheticalNetR"],3)
        self.assertFalse(out["discordEligible"])

    def test_same_bar_stop_first(self):
        a=record(0,event_tf="15m",side="LONG",high=100,low=99.5)
        b=record(1,high=104,low=98.5)
        result=analyze_forward_records([a,b])
        self.assertEqual(result["trades"][0]["outcome"],"SL")
        self.assertEqual(result["trades"][0]["grossR"],-1)

    def test_opens_then_break_even_on_following_bar(self):
        a=record(0,event_tf="15m",side="LONG",high=100,low=99.5)
        b=record(1,high=101.5,low=99.5)
        c=record(2,high=100.5,low=99.5)
        out=analyze_forward_records([a,b,c])
        self.assertEqual(out["trades"][0]["outcome"],"BE")
        self.assertEqual(out["trades"][0]["grossR"],0)

    def test_short_tp3(self):
        a=record(0,event_tf="30m",side="SHORT",high=100.5,low=99)
        b=record(1,high=100.5,low=96)
        result=analyze_forward_records([a,b])
        self.assertEqual(result["trades"][0]["outcome"],"TP3")

    def test_duplicate_data_is_not_double_counted(self):
        first=record(0,event_tf="1h",side="LONG",high=100,low=99.5)
        second=deepcopy(first)
        result=analyze_forward_records([first,second])
        self.assertEqual(result["byTimeframe"]["1h"]["hypotheticalCandidates"],1)
        self.assertEqual(result["evidence"]["duplicateObservations"],3)
        self.assertEqual(result["trades"][0]["outcome"],"OPEN")

    def test_conflicting_duplicate_rejected(self):
        a=record(0)
        b=record(0,altered=True)
        with self.assertRaisesRegex(ValueError,"Contradictory"):
            analyze_forward_records([a,b])

    def test_gap_quarantines_trade(self):
        a=record(0,event_tf="1h",side="LONG",high=100,low=99.5)
        b=record(2,high=104,low=99.5)
        result=analyze_forward_records([a,b])
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
