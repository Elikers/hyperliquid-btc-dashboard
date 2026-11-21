import tempfile
import json
import unittest
from pathlib import Path
from datetime import datetime, timezone

from research.parity_checks import TF_MS
from research.evaluate_public_snapshot import score_snapshots


def bars(tf,n):
    step=TF_MS[tf]
    return [{"t":i*step, "T":(i+1)*step-1,
             "o":100+i*.1,"h":102+i*.1,"l":99+i*.1,
             "c":101+i*.1,"v":10+i%5} for i in range(n)]


class SnapshotScoringTests(unittest.TestCase):
    def test_three_timeframes_are_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            stamp=datetime.fromtimestamp(2600*TF_MS["15m"]/1000+30,
                                         timezone.utc).isoformat()
            for tf,n in (("15m",2600),("30m",1300),("1h",650)):
                (p/f"btc_{tf}.json").write_text(json.dumps({
                    "timeframe":tf,"coin":"BTC","discordEligible":False,
                    "capturedAtUtc":stamp,"closedCandles":bars(tf,n),
                }))
            result=score_snapshots(p)
            self.assertEqual(set(result["timeframes"]),set(TF_MS))
            self.assertFalse(result["discordEligible"])
            self.assertEqual(set(result["viprasolClassicMacroOff"]),
                             set(TF_MS))
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

    def test_missing_files_do_not_create_fake_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                score_snapshots(tmp)


if __name__=="__main__":
    unittest.main()
