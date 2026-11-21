import unittest
from datetime import datetime, timezone
from research.classic_decision import Context, FACTORS, evaluate


def context(at="2026-11-20T15:00:00+00:00", **kwargs):
    return Context(timeframe="15m", symbol_verified=True, candle_closed=True,
                   bar_open_ms=int(datetime.fromisoformat(at).timestamp()*1000),
                   macro_provenance_verified=True, **kwargs)


def factors(*enabled):
    return {f: f in enabled for f in FACTORS}


def run(ctx=None, up=True, long_factors=None, short_factors=None):
    return evaluate(
        previous_fast=99 if up else 101, previous_slow=100,
        fast=101 if up else 99, slow=100,
        bull_factors=long_factors if long_factors is not None else factors(*FACTORS),
        bear_factors=short_factors if short_factors is not None else factors(),
        context=ctx or context(),
    )


class ClassicGateTests(unittest.TestCase):
    def test_long_qualified_research_only(self):
        r=run()
        self.assertEqual(r["candidate"], "LONG")
        self.assertEqual(r["bullScore"], 8)
        self.assertFalse(r["discordEligible"])

    def test_short_qualified_research_only(self):
        r=run(up=False, short_factors=factors(*FACTORS))
        self.assertEqual(r["candidate"], "SHORT")

    def test_no_cross_no_entry_even_eight_of_eight(self):
        x=evaluate(previous_fast=101,previous_slow=100,fast=102,slow=100,
          bull_factors=factors(*FACTORS),bear_factors=factors(),
          context=context())
        self.assertIsNone(x["candidate"])
        self.assertIn("NO_NEW_EMA_CROSS",x["reasons"])

    def test_less_than_five_blocks(self):
        x=run(long_factors=factors("ema","rsi","macd","vwap"))
        self.assertIsNone(x["candidate"])
        self.assertIn("INSUFFICIENT_CONFLUENCE",x["reasons"])

    def test_weekend_blocks(self):
        x=run(ctx=context("2026-11-21T15:00:00+00:00"))
        self.assertIn("WEEKEND",x["reasons"])

    def test_asia_session_blocks(self):
        x=run(ctx=context("2026-11-20T04:00:00+00:00"))
        self.assertIn("OUTSIDE_EU_US_SESSION",x["reasons"])

    def test_unverified_nasdaq_blocks(self):
        ctx=Context(timeframe="15m",symbol_verified=True,candle_closed=True,
          bar_open_ms=context().bar_open_ms,macro_provenance_verified=False)
        self.assertIn("NQ1_MACRO_UNVERIFIED",run(ctx)["reasons"])

    def test_open_bar_blocks(self):
        ctx=Context(timeframe="15m",symbol_verified=True,candle_closed=False,
          bar_open_ms=context().bar_open_ms,macro_provenance_verified=True)
        self.assertIn("CANDLE_NOT_CLOSED",run(ctx)["reasons"])

    def test_adr_equal_threshold_blocks(self):
        x=run(ctx=context(adr_percent_used=100))
        self.assertIn("ADR_EXHAUSTED",x["reasons"])

    def test_adr_unavailable_is_not_assumed_exhausted(self):
        x=run(ctx=context(adr_percent_used=None))
        self.assertEqual(x["candidate"],"LONG")

    def test_macro_disabled_has_seven_factor_denominator(self):
        x=run(ctx=context(macro_factor_enabled=False))
        self.assertEqual(x["factorTotal"],7)
        self.assertEqual(x["candidate"],"LONG")

    def test_missing_factor_rejected(self):
        with self.assertRaises(ValueError):
            run(long_factors={"rsi":True})


if __name__ == "__main__":
    unittest.main()
