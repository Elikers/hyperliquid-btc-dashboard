import unittest
from research.eight_factor_audit import audit_eight_factors

TF=900000
def candles(n=150,*,step=TF,shift=0,up=True):
    return [{
        "t":i*step+shift,"T":(i+1)*step+shift-1,
        "o":100+i*(.1 if up else -.1),
        "h":101+i*(.1 if up else -.1),
        "l":99+i*(.1 if up else -.1),
        "c":100+i*(.1 if up else -.1),
        "v":10+i%10
    } for i in range(n)]


class EightFactorAuditTests(unittest.TestCase):
    def test_all_eight_votes_no_alert(self):
        btc=candles()
        n=candles()
        report=audit_eight_factors(btc,btc,n,[1.]*150,
            timeframe="15m",current_ms=btc[-1]["T"]+1)
        self.assertEqual(len(report["factorVotesBull"]),8)
        self.assertEqual(len(report["factorVotesBear"]),8)
        self.assertFalse(report["discordEligible"])
        self.assertFalse(report["originalViprasolVerified"])
        self.assertEqual(report["macro"]["reason"],"SOURCE_UNVERIFIED")
        self.assertIn("NQ1_MACRO_UNVERIFIED",report["decision"]["reasons"])

    def test_audited_flag_not_enough_for_full_parity(self):
        btc=candles()
        r=audit_eight_factors(btc,btc,btc,[1.]*150,
            timeframe="15m",current_ms=btc[-1]["T"]+1,
            macro_source_verified=True)
        self.assertTrue(r["macro"]["sourceVerified"])
        self.assertFalse(r["originalViprasolVerified"])
        self.assertFalse(r["discordEligible"])

    def test_timestamp_shift_rejected(self):
        btc=candles()
        nq=candles(shift=TF)
        with self.assertRaises(ValueError):
            audit_eight_factors(btc,btc,nq,[1.]*150,
                timeframe="15m",current_ms=nq[-1]["T"]+1)

    def test_unclosed_macro_rejected(self):
        btc=candles()
        nq=candles()
        with self.assertRaises(ValueError):
            audit_eight_factors(btc,btc,nq,[1.]*150,
                timeframe="15m",current_ms=btc[-1]["t"]+1)

    def test_unaligned_source_length_rejected(self):
        btc=candles()
        nq=candles(149)
        with self.assertRaises(ValueError):
            audit_eight_factors(btc,btc,nq,[1.]*149,
                timeframe="15m",current_ms=btc[-1]["T"]+1)

    def test_macro_unavailable_ema_blocks_vote(self):
        btc=candles()
        r=audit_eight_factors(btc,btc,btc,[None]*150,
            timeframe="15m",current_ms=btc[-1]["T"]+1,
            macro_source_verified=True)
        self.assertFalse(r["factorVotesBull"]["macro"])
        self.assertFalse(r["factorVotesBear"]["macro"])
        self.assertEqual(r["macro"]["reason"],"MACRO_EMA_UNAVAILABLE")

    def test_thirty_minute_timestamp_alignment(self):
        btc=candles(step=TF*2)
        confirm=candles(n=300)
        r=audit_eight_factors(btc,confirm,btc,[1.]*150,
            timeframe="30m",current_ms=btc[-1]["T"]+1)
        self.assertEqual(r["timeframe"],"30m")
        self.assertFalse(r["discordEligible"])


if __name__=="__main__":
    unittest.main()
