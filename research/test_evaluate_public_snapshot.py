import tempfile
import json
import unittest
from pathlib import Path
from datetime import datetime, timezone

from research.parity_checks import TF_MS
from research.evaluate_public_snapshot import score_snapshots


def sample_feeds():
    """Aggregate common 15m candles into independently verifiable 30m/1h."""
    step=TF_MS["15m"]
    base=[]
    for i in range(2600):
        low=99+i*.1
        high=102+i*.1
        base.append({"t":i*step,"T":(i+1)*step-1,
                     "o":100+i*.1,"h":high,"l":low,
                     "c":101+i*.1,"v":10+i%5})
    output={"15m":base}
    for tf,multiple in (("30m",2),("1h",4)):
        aggregated=[]
        for start in range(0,len(base),multiple):
            chunk=base[start:start+multiple]
            aggregated.append({
                "t":chunk[0]["t"],"T":chunk[-1]["T"],
                "o":chunk[0]["o"],"h":max(x["h"] for x in chunk),
                "l":min(x["l"] for x in chunk),
                "c":chunk[-1]["c"],"v":sum(x["v"] for x in chunk)})
        output[tf]=aggregated
    return output


def write_feeds(path, feeds):
    stamp=datetime.fromtimestamp(2600*TF_MS["15m"]/1000+30,
                                 timezone.utc).isoformat()
    for tf in TF_MS:
        (path/f"btc_{tf}.json").write_text(json.dumps({
            "timeframe":tf,"coin":"BTC","discordEligible":False,
            "capturedAtUtc":stamp,"closedCandles":feeds[tf],
        }),encoding="utf-8")


class SnapshotScoringTests(unittest.TestCase):
    def test_three_timeframes_are_safe_and_daily_adr_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            write_feeds(p,sample_feeds())
            result=score_snapshots(p)
            self.assertTrue(result["candleIntegrity"]["passed"])
            self.assertEqual(set(result["timeframes"]),set(TF_MS))
            self.assertFalse(result["discordEligible"])
            self.assertEqual(set(result["viprasolClassicMacroOff"]),set(TF_MS))
            self.assertEqual(set(result["btcOnlyLab"]),set(TF_MS))
            for value in result["viprasolClassicMacroOff"].values():
                self.assertEqual(value["configuration"],
                                 "VIPRASOL_CLASSIC_MACRO_OFF")
                self.assertFalse(value["discordEligible"])
                self.assertFalse(value["originalViprasolVerified"])
                self.assertTrue(value["adr"]["available"],
                    "Production history must exercise 14 completed days")
            for value in result["timeframes"].values():
                self.assertFalse(value["discordEligible"])
                self.assertFalse(value["originalViprasolVerified"])

    def test_disagreeing_hourly_candle_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            feeds=sample_feeds()
            feeds["1h"][100]["o"]+=0.05
            write_feeds(p,feeds)
            with self.assertRaisesRegex(RuntimeError,"Cross-timeframe"):
                score_snapshots(p)

    def test_mixed_capture_times_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            write_feeds(p,sample_feeds())
            path=p/"btc_1h.json"
            payload=json.loads(path.read_text(encoding="utf-8"))
            payload["capturedAtUtc"]="1970-01-01T00:00:01+00:00"
            path.write_text(json.dumps(payload),encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"Mixed observation"):
                score_snapshots(p)

    def test_missing_files_do_not_create_fake_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                score_snapshots(tmp)


if __name__=="__main__":
    unittest.main()
