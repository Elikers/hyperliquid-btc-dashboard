import hashlib
import json
import unittest
from unittest.mock import patch

from research.liquidity_forward_observation import observe
from research.factors import STEPS


def snapshots():
    now=360000000
    captured="1970-01-05T04:01:00+00:00"
    out={}
    for tf,step in STEPS.items():
        count=400 if tf=="15m" else 200 if tf=="30m" else 100
        start=now-count*step
        bars=[{"t":start+i*step,"T":start+(i+1)*step-1,
               "o":100.,"h":102.,"l":98.,"c":100.,"v":10.}
              for i in range(count)]
        out[tf]={"market":"HYPERLIQUID:BTCUSDC.P","coin":"BTC",
                 "source":"Hyperliquid official public candleSnapshot API",
                 "timeframe":tf,"capturedAtUtc":captured,
                 "closedCandles":bars,"lastCloseMs":bars[-1]["T"],
                 "researchOnly":True,"viprasolVerified":False,
                 "discordEligible":False}
    return out


class ForwardLiquidityObservationTests(unittest.TestCase):
    @patch("research.liquidity_forward_observation.audit_cross_timeframe",
           return_value={"passed":True})
    def test_no_candidate_prospectively_observed(self,_):
        record=observe(snapshots(),evaluate=lambda *_args,**_kwargs:None)
        self.assertTrue(record["prospectivelyObserved"])
        self.assertFalse(record["futureOutcomeKnown"])
        self.assertFalse(record["discordEligible"])
        self.assertFalse(record["automaticTrading"])
        self.assertFalse(record["profitabilityClaimAllowed"])
        self.assertTrue(all(v["researchCandidate"] is None
                            for v in record["timeframes"].values()))
        supplied=record.pop("recordSha256")
        canonical=json.dumps(record,sort_keys=True,separators=(",",":"),allow_nan=False)
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(),supplied)

    @patch("research.liquidity_forward_observation.audit_cross_timeframe",
           return_value={"passed":True})
    def test_rejects_trade_enabled_candidate(self,_):
        def unsafe(history,confirmation,*,timeframe):
            return {"closedBarEndMs":history[-1]["T"],"side":"LONG",
                    "researchOnly":True,"originalViprasolVerified":False,
                    "discordEligible":True,"automaticTrading":False}
        with self.assertRaises(ValueError):
            observe(snapshots(),evaluate=unsafe)

    def test_mismatched_timestamps_rejected(self):
        data=snapshots()
        data["1h"]["capturedAtUtc"]="1970-01-05T04:02:00+00:00"
        with self.assertRaises(ValueError):
            observe(data)

    def test_bad_market_rejected(self):
        data=snapshots()
        data["15m"]["coin"]="ETH"
        with self.assertRaises(ValueError):
            observe(data)

    def test_not_yet_closed_rejected(self):
        data=snapshots()
        data["1h"]["capturedAtUtc"]="1970-01-05T04:00:00+00:00"
        data["15m"]["capturedAtUtc"]=data["1h"]["capturedAtUtc"]
        data["30m"]["capturedAtUtc"]=data["1h"]["capturedAtUtc"]
        with self.assertRaises(ValueError):
            observe(data)

    @patch("research.liquidity_forward_observation.audit_cross_timeframe",
           return_value={"passed":True})
    def test_candidate_requires_matching_closed_bar(self,_):
        def stale(history,confirmation,*,timeframe):
            return {"closedBarEndMs":history[-1]["T"]-STEPS[timeframe],
                    "side":"LONG","researchOnly":True,
                    "originalViprasolVerified":False,
                    "discordEligible":False,"automaticTrading":False}
        with self.assertRaises(ValueError):
            observe(snapshots(),evaluate=stale)


if __name__=="__main__":
    unittest.main()
