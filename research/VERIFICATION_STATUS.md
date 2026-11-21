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
