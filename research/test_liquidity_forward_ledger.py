import hashlib
import json
import unittest
from datetime import datetime,timezone

from research.factors import STEPS
from research.liquidity_forward_ledger import ledger,verify_record,read_archive


def make_record(index=0, candidate=False):
    stamp=datetime.fromtimestamp((7200000+index*3600000)/1000,timezone.utc).isoformat()
    frames={}
    for tf,step in STEPS.items():
        start=index*step
        end=start+step-1
        entry=None
        if candidate and tf=="1h":
            entry={"closedBarEndMs":end,"side":"LONG",
                   "researchOnly":True,"originalViprasolVerified":False,
                   "discordEligible":False,"automaticTrading":False,
                   "hypotheticalRiskLadder":{
                       "entry":100.,"stop":95.,"targets":[105.,110.,115.],
                       "side":"LONG","researchOnly":True,"discordEligible":False}}
        frames[tf]={"closedBarStartMs":start,"closedBarEndMs":end,
                    "bar":{"o":100.,"h":120. if index else 102.,
                           "l":99. if index else 98.,"c":110. if index else 100.,
                           "v":5.},"researchCandidate":entry,
                    "originalViprasolVerified":False}
    record={"kind":"HYPERLIQUID_BTC_LIQUIDITY_LAB_PROSPECTIVE_OBSERVATION_V1",
            "capturedAtUtc":stamp,"market":"HYPERLIQUID:BTCUSDC.P",
            "timeframes":frames,"researchOnly":True,
            "futureOutcomeKnown":False,"prospectivelyObserved":True,
            "historicalOnly":False,"originalViprasolVerified":False,
            "discordEligible":False,"automaticTrading":False,
            "profitabilityClaimAllowed":False}
    record["recordSha256"]=hashlib.sha256(json.dumps(record,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    return record


class LabForwardLedgerTests(unittest.TestCase):
    def test_zero_candidates_not_reported_profitable(self):
        report=ledger([make_record()])
        self.assertEqual(report["timeframes"]["15m"]["candidateCount"],0)
        self.assertFalse(report["independentForwardProfitable"])
        self.assertFalse(report["discordEligible"])

    def test_resolve_only_with_actual_later_record(self):
        report=ledger([make_record(0,True),make_record(1)])
        self.assertEqual(report["timeframes"]["1h"]["candidateCount"],1)
        self.assertEqual(report["timeframes"]["1h"]["resolved"],1)
        self.assertEqual(report["trades"][0]["status"],"TP3")
        self.assertGreater(report["timeframes"]["1h"]["netRSumByOneWayCostBps"]["7"],0)

    def test_missing_future_is_not_resolved(self):
        report=ledger([make_record(0,True)])
        self.assertEqual(report["trades"][0]["status"],"OPEN")
        self.assertEqual(report["timeframes"]["1h"]["resolved"],0)

    def test_gap_is_quarantined(self):
        report=ledger([make_record(0,True),make_record(2)])
        self.assertEqual(report["trades"][0]["status"],"DATA_GAP")
        self.assertEqual(report["timeframes"]["1h"]["resolved"],0)

    def test_duplicate_deduplicated(self):
        x=make_record()
        report=ledger([x,x])
        self.assertEqual(report["timeframes"]["1h"]["uniqueObservedCloses"],1)
        self.assertEqual(report["duplicateObservedCloses"],3)

    def test_digest_tampering_fails(self):
        x=make_record()
        x["timeframes"]["1h"]["bar"]["c"]=999
        with self.assertRaises(ValueError):verify_record(x)

    def test_live_trading_flag_fails(self):
        x=make_record()
        x["automaticTrading"]=True
        with self.assertRaises(ValueError):verify_record(x)


if __name__=="__main__":
    unittest.main()
