import unittest
from research.atr_seed_audit import audit_atr_warmup


def bars(n=300):
    return [{"h":110+i*.02,"l":90+i*.02,"c":100+i*.02}
            for i in range(n)]


class AtrSeedAuditTests(unittest.TestCase):
    def test_long_stop_stable_after_warmup(self):
        result=audit_atr_warmup(bars(),entry=100,
            reference_stop=70,side="LONG",start_indices=(0,100,150))
        self.assertLess(result["maxSeedShift"],1e-5)
        self.assertFalse(result["discordEligible"])
        self.assertFalse(result["inputSourceParityVerified"])

    def test_short_side(self):
        result=audit_atr_warmup(bars(),entry=100,
            reference_stop=130,side="SHORT",start_indices=(0,100))
        self.assertGreater(result["scenarios"][0]["researchStop"],100)

    def test_wrong_stop_side_rejected(self):
        with self.assertRaises(ValueError):
            audit_atr_warmup(bars(),entry=100,reference_stop=101,side="LONG")

    def test_invalid_seed_rejected(self):
        with self.assertRaises(ValueError):
            audit_atr_warmup(bars(),entry=100,reference_stop=70,
                             side="LONG",start_indices=(0,-2))

    def test_full_seed_required(self):
        with self.assertRaises(ValueError):
            audit_atr_warmup(bars(),entry=100,reference_stop=70,
                             side="LONG",start_indices=(100,150))

    def test_inadequate_history_rejected(self):
        with self.assertRaises(ValueError):
            audit_atr_warmup(bars(5),entry=100,reference_stop=70,side="LONG")

    def test_bad_multiplier_rejected(self):
        with self.assertRaises(ValueError):
            audit_atr_warmup(bars(),entry=100,reference_stop=70,
                             side="LONG",multiplier=0)


if __name__=="__main__":
    unittest.main()
