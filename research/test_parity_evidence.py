import unittest
from research.parity_evidence import audit_references


def entry(timeframe="15m", side="LONG", close_ms=1000, price=100):
    direction = 1 if side == "LONG" else -1
    return {
        "timeframe":timeframe,"side":side,"close_ms":close_ms,
        "entry":price,"stop":price-direction,
        "tp1":price+direction,"tp2":price+2*direction,
        "tp3":price+3*direction,
    }


class EvidenceTests(unittest.TestCase):
    def test_exact_one_frame_is_not_complete(self):
        r = audit_references([entry()], [entry()],
                source_independent=True, settings_matched=True,
                all_closed_bars_compared=True)
        self.assertTrue(r["sample_exact"])
        self.assertFalse(r["source_evidence_complete"])
        self.assertFalse(r["discord_eligible"])

    def test_three_frame_sample_never_certifies_alerts(self):
        rows=[entry("15m"), entry("30m", close_ms=2000),
              entry("1h","SHORT",close_ms=3000)]
        r=audit_references(rows,rows,source_independent=True,
                settings_matched=True,all_closed_bars_compared=True)
        self.assertTrue(r["source_evidence_complete"])
        self.assertFalse(r["full_original_viprasol_verified"])
        self.assertFalse(r["discord_eligible"])

    def test_shifted_bar_is_missing_and_extra(self):
        r=audit_references([entry()],[entry(close_ms=2000)])
        self.assertEqual(len(r["missing"]),1)
        self.assertEqual(len(r["extra"]),1)

    def test_target_difference_detected(self):
        b=entry()
        b["tp2"]+=0.5
        r=audit_references([entry()],[b])
        self.assertEqual(r["price_differences"][0]["field"],"tp2")

    def test_unsupported_timeframe_rejected(self):
        with self.assertRaises(ValueError):
            audit_references([entry("5m")],[])

    def test_duplicate_reference_rejected(self):
        with self.assertRaises(ValueError):
            audit_references([entry(),entry()],[])

    def test_empty_reference_not_validation(self):
        r=audit_references([],[],source_independent=True,
                settings_matched=True,all_closed_bars_compared=True)
        self.assertFalse(r["sample_exact"])
        self.assertFalse(r["source_evidence_complete"])

    def test_price_ladder_must_be_monotonic(self):
        bad=entry()
        bad["stop"]=bad["entry"]+1
        with self.assertRaises(ValueError):
            audit_references([bad],[])

    def test_price_tolerance(self):
        candidate=entry()
        candidate["entry"]+=0.05
        r=audit_references([entry()],[candidate],max_price_delta=0.1)
        self.assertTrue(r["sample_exact"])

    def test_short_side_supported(self):
        e=entry("1h","SHORT")
        r=audit_references([e],[e])
        self.assertTrue(r["sample_exact"])
        self.assertFalse(r["discord_eligible"])


if __name__=="__main__":
    unittest.main()
