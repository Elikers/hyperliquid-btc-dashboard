import unittest
from copy import deepcopy
from research.forward_observation import compact_observation

TFS=("15m","30m","1h")
STEPS={"15m":900000,"30m":1800000,"1h":3600000}
CAPTURED="2026-11-21T12:02:00+00:00"


def fixture():
    source={}
    classics={}
    for tf in TFS:
        end=STEPS[tf]-1
        source[tf]={
            "timeframe":tf,"coin":"BTC","capturedAtUtc":CAPTURED,
            "discordEligible":False,
            "closedCandles":[{"t":0,"T":end,"o":"100",
                              "h":"110","l":"95","c":"105","v":"1000"}],
        }
        classics[tf]={
            "configuration":"VIPRASOL_CLASSIC_MACRO_OFF",
            "closedThroughMs":end,"bullScore":5,"bearScore":1,
            "scoreThreshold":5,"rawCrossover":"LONG",
            "hypotheticalDirection":None,"hypotheticalRiskLadder":None,
            "reasons":["OUTSIDE_EU_US_SESSION"],"adr":{"available":True},
            "originalViprasolVerified":False,"discordEligible":False,
        }
    scores={"capturedAtUtc":CAPTURED,
            "candleIntegrity":{"passed":True},
            "viprasolClassicMacroOff":classics,
            "discordEligible":False,"originalViprasolVerified":False,
            "liveSignalAlerts":False}
    return source,scores


class CompactForwardTests(unittest.TestCase):
    def test_compact_bar_and_source_are_auditable(self):
        source,scores=fixture()
        result=compact_observation(source,scores)
        self.assertEqual(set(result["timeframes"]),set(TFS))
        self.assertEqual(len(result["recordSha256"]),64)
        self.assertEqual(result["timeframes"]["1h"]["closedBarEndMs"],3599999)
        self.assertFalse(result["discordEligible"])
        self.assertFalse(result["originalViprasolVerified"])

    def test_not_a_live_trading_alert(self):
        source,scores=fixture()
        scores["liveSignalAlerts"]=True
        with self.assertRaises(ValueError):
            compact_observation(source,scores)

    def test_market_provenance_cannot_change(self):
        source,scores=fixture()
        source["15m"]["coin"]="ETH"
        with self.assertRaises(ValueError):
            compact_observation(source,scores)

    def test_reject_different_capture_time(self):
        source,scores=fixture()
        source["30m"]["capturedAtUtc"]="2026-11-21T12:17:00+00:00"
        with self.assertRaises(ValueError):
            compact_observation(source,scores)

    def test_reject_source_model_timestamp_mismatch(self):
        source,scores=fixture()
        scores["viprasolClassicMacroOff"]["1h"]["closedThroughMs"]=100
        with self.assertRaises(ValueError):
            compact_observation(source,scores)

    def test_reject_missing_timeframe(self):
        source,scores=fixture()
        del source["1h"]
        with self.assertRaises(ValueError):
            compact_observation(source,scores)

    def test_refuse_unverified_discord_ladder(self):
        source,scores=fixture()
        scores["viprasolClassicMacroOff"]["15m"]["hypotheticalRiskLadder"]={
            "researchOnly":True,"discordEligible":True}
        with self.assertRaises(ValueError):
            compact_observation(source,scores)

    def test_reject_failed_cross_timeframe_integrity(self):
        source,scores=fixture()
        scores["candleIntegrity"]["passed"]=False
        with self.assertRaises(ValueError):
            compact_observation(source,scores)

    def test_digest_stable_for_same_capture(self):
        source,scores=fixture()
        a=compact_observation(source,scores)
        b=compact_observation(deepcopy(source),deepcopy(scores))
        self.assertEqual(a["recordSha256"],b["recordSha256"])

    def test_bad_high_rejected(self):
        source,scores=fixture()
        source["15m"]["closedCandles"][0]["h"]="101"
        with self.assertRaises(ValueError):
            compact_observation(source,scores)


if __name__=="__main__":
    unittest.main()
