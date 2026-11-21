# Verified end-to-end BTC research capture — 2026-11-21

## Verified GitHub Actions evidence

**Status: SUCCESS (not merely an assumed schedule).**

- GitHub Actions run: https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44895884495
- Trigger: push smoke test of `.github/workflows/btc-forward-capture.yml`
- Branch/commit: `main`, `abddf098ba231c6d260439a992c53bf50d2180d6`
- Job: `capture` — **completed successfully**; all steps passed:
  - Checkout/setup, full offline research test suite
  - Hyperliquid BTC public closed candle capture
  - Research-only seven-factor / macro-OFF Classic / BTC-only Lab scoring
  - Compact paper-evidence generation
  - 30-day compact-artifact upload
  - 2-day full-snapshot upload
- Additional verified post-merge CI run: https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44895831768 — **success**.

## Actual downloaded artifact inspection

Compact artifact `btc-paper-evidence-44895884495` (GitHub artifact ID `14704385107`), created at 2026-11-21 10:46 UTC, expires 2026-12-21. Full-snapshot artifact `btc-research-candles-44895884495` (ID `14704150706`), expires 2026-11-23. Downloaded both and inspected their JSON payloads.

Snapshot observation time: **2026-11-21T10:46:04.197Z**.

| TF | Closed candles | First open (UTC) | Last close (UTC) | Internal consistency |
|---|---:|---|---|---|
| 15m | 2,600 | 2026-10-25 08:45 | 2026-11-21 10:44:59.999 | Source feed, reference |
| 30m | 1,300 | 2026-10-25 08:30 | 2026-11-21 10:29:59.999 | 1,299 overlapping complete groups; 0 OHLCV mismatches |
| 1h | 650 | 2026-10-25 08:00 | 2026-11-21 09:59:59.999 | 649 overlapping complete groups; 0 OHLCV mismatches |

The compact evidence for **Macro-Off Classic** recorded these sample scores:
- 15m: 5 bullish / 0 bearish; hypothetical candidate NONE
- 30m: 5 bullish / 1 bearish; candidate NONE
- 1h: 4 bullish / 2 bearish; candidate NONE

For all three timeframes the record explicitly included `WEEKEND`, `ADR_EXHAUSTED`, and `NO_NEW_EMA_CROSS` blocks. In this specific sample, ADR values were available, the research model emitted no hypothetical new entries, and `discordEligible=false`. The capture was on a Saturday in Asia/Manila and New York.

**What this proves:** Our current GitHub pipeline can successfully fetch 27 days of BTC data, validate aggregated candles, evaluate configured research modes, produce immutable compact evidence, and save the artifact for a longer forward sample. It also confirms the fail-closed checks passed on this run.

**What this does NOT prove:** the 15-minute scheduled cron has successfully fired (this first verified run was a push-triggered smoke test); a profitable strategy; exact Viprasol/Pine bar-by-bar parity; continuously available cloud monitoring; live Discord delivery or trade readiness.

## Next evidence gates

1. Observe at least one run with `event=schedule` at the new 15-minute cron, and monitor subsequent skipped/failed runs.
2. After multiple future artifacts, **deduplicate** observations per timeframe and resolve hypothetical SL/BE/TP outcomes using subsequent full OHLCV candles, after fees/slippage and with missing-data flags.
3. Compare independently exported original Viprasol bar-by-bar factors/events to the Macro-Off Classic outputs; do not mistake model-generated observations for an independent source.
4. Keep live trading, webhook trade alerts and automatic execution disabled.
