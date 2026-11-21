# Signal-engine verification status
Updated: 2026-11-21

## Reality check

- Public Hyperliquid BTC candlestick/last-trade chart: confirmed working by the user.
- GitHub Actions capture every 15m: workflow committed; the latest successful scheduled run is **not verified** from available connector outputs.
- Viprasol Classic macro OFF: the supplied original Pine Script supports the configuration, with 7-factor scoring. The source-equivalent Python calculations are **not yet certified**.
- Macro ON: exact `CME_MINI:NQ1!` continuous-futures data and roll/sessions missing.
- Live Discord trade alerts: **disabled**.
- Continuous cloud signal worker: **not deployed**.
- Profitability after fees/slippage: **unproven**.

## Real historical evidence: one 15m LONG (November 20, 2026)

An offline rerun using the previously supplied 15m candidate and candle CSV files compared a user-provided original-indicator reference bar opened at 14:15 UTC.

| Field | Difference: research engine minus reference |
|---|---:|
| Candle open, high, low, close | 0.0 each |
| LONG direction | match |
| Entry | 0.0 |
| Stop loss | +0.2978 USD |
| TP1 | -0.2978 USD |
| TP2 | -0.49561 USD |
| TP3 | -0.79341 USD |

This is a **single partial match**, not a statistically meaningful accuracy score. The reference prices were displayed rounded to 0.1, and the old candidate series was a 7-factor research calculation, not a verified Classic replay.

## What counts as evidence

The independent [parity evidence audit](parity_evidence.py) checks missed/extra LONG/SHORT events, candle-close timing, and Entry/SL/TP1/TP2/TP3 differences for each timeframe. Its [10 regression tests](test_parity_evidence.py) were run successfully in the local development environment before commit. CI checks in GitHub remain separately unverified.

No event collection or module in this repository has approval to send a live trading alert. A synthetic fixture, a 100% match on one event, or a single successful workflow run must not be represented as full original-Pine parity.

## Next substantive engineering work

1. Obtain independent Pine export data for all 15m, 30m, 1h closed bars and exact Macro-Off settings without requesting the user to repeatedly test or install anything.
2. Produce per-factor bar-aligned comparisons, including VWAP day session, RSI initialization, MACD, ADX, 15m `request.security` merge, 14-day ADR and ATR.
3. Check full event series (not only candidate bars) for false negatives, false positives and latency.
4. Analyze multi-period paper outcomes with fees, slippage and drawdowns; do not promote on one test.
5. Only after independently verified evidence and secure hosting should sending trade notifications be reconsidered. Never execute wallet trades without explicit authorization.

## November 21 next-iteration evidence

- Exact user-supplied Viprasol Pine v6 source SHA-256: `00d41c3abfccb3747506185bf0515684b5d8cdaa4b85c4546384914e623f34de`. This makes later source revisions distinguishable; source checksum **does not** prove Pine/engine parity.
- Original Pine default includes `ta.atr(14)`, 1.5× multiplier, `ta.vwap(hlc3)`, `request.security(..., "15", ta.rsi(close,14), lookahead_off)`, and Macro-OFF score denominator 7. The Python defaults are source-aligned but still require independent output comparisons.
- 1,187 real 15m candles before the 2026-11-20 reference event independently yield ATR `273.0681301530` and LONG stop `61,667.39780477` vs screenshot `61,667.1`. Seed starts 0, 100, 300, 500, and 800 bars earlier converge to essentially the same result. This is documented in [the detailed analysis](FEED_PARITY_ATR_DIAGNOSIS_2026-11-21.md). The unresolved stop discrepancy cannot be responsibly "fixed" by adjusting ATR to fit one screenshot.
- The GitHub 15-minute capture now freezes **one timestamp across all three timeframe requests**. The scorer rejects mixed-timestamp 15m/30m/1h snapshots, so cross-timeframe integrity cannot silently combine different observation instants. [Capture regression tests](test_capture_public_btc.py) and [scorer regression tests](test_evaluate_public_snapshot.py) cover this.
- Two existing independently runnable local test suites were executed here: `viprasol_research_work` **15/15 passing**, `btc_validation_current/research` **19/19 passing**. These are legacy/offline suites; they **do not** certify the latest connected GitHub commit's full CI.
- The GitHub Actions push/schedule run history was not obtainable through available connector APIs; **success or failure of the newly committed Actions tests remains unverified**. Do not equate confirmed GitHub commits with successful workflow execution.

Official external source: [TradingView's current docs](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/) explain that `request.security` on a lower timeframe returns the last intrabar historically under `lookahead_off`, while realtime behavior has caveats. This matters for the Pine 15m RSI confirmation running on a 30m or 1h chart.

### Strict next gate

Obtain **bar-aligned independent Pine reference events** for macro-OFF Classic (including zero-signal closed bars) and measure exact per-factor, entry, SL, and TP agreement across all three chart timeframes. Then collect enough fresh forward samples for fee-adjusted expectancy and drawdown. No trading, Discord trade alerts, or claims of profitability before those gates.
