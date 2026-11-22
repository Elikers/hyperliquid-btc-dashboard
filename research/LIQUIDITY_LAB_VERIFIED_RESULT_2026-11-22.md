# Verified BTC single-entry-swap Lab execution — November 22, 2026

## What was built and verified

- [PR #18](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/18) merged a **single** research-only alternative event trigger (confirmed pivot high/low sweep + closing reclaim), keeping Classic untouched. It uses a 3-left/3-right-bar confirmation, rejects ambiguous same-bar sweeps, and preserves seven-factor min 5/7 confluence, New York EU/US sessions, weekends, ADR14 and ATR14*1.5 original signal-time stop and 1R/2R/3R targets.
- A **separate** next-bar-open fill stress applies 3bps adverse entry price plus additional 0/7/15bps one-way cost sensitivity to both original Python Classic historical entries and Lab entries. This is not a broker or tick-level simulator: unknown intrabar ordering conservatively stops first, and unfillable ladder entries are quarantined.
- [PR safety #44966273019](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44966273019) and [main safety #44966302295](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44966302295) passed.
- [Full real-data research workflow #44966302324](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44966302324) **success**, 283 offline tests, fetched saved Hyperliquid recent and strict earlier non-overlapping historical source history and uploaded artifact **14731950612**, whose SHA256 was independently verified against GitHub metadata: `eca1552eb14acf266c2cf59fb4d3cd162e1a0ac0f3a721a27a915a40db3818dc`. Its JSON member `liquidity_lab_replay.json` was opened and all frame totals/rows independently inspected. Recent has 30 entries across engines; older holdout has 13 entries across engines.
- [PR #19](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/19) adds best-effort **daily 04:11 UTC** historical Lab execution through GitHub Actions. The immediate **post-merge push smoke run #44966453324 succeeded**, including tests, real-data Lab comparison and artifact upload. A genuine daily `event=schedule` execution has **not yet been verified**; the daily cron is configured, not guaranteed. Cron is not an always-on ChatGPT agent; rolling windows heavily overlap and must not be labeled prospective forward performance.

## Exact sample results (7bps one-way cost sensitivity *in addition* to 3bps adverse entry slippage)

| Dataset | Timeframe | Classic hypothetical candidates / net R | Liquidity Lab candidates / net R |
|---|---|---:|---:|
| Recent saved candles | 15m | 13 / -3.3952R | 3 / +0.1212R |
| Recent saved candles | 30m | 7 / -3.3559R | 0 / 0R (NO TRADES, NOT BREAK-EVEN) |
| Recent saved candles | 1h | 7 / +0.0246R | 0 / 0R (NO TRADES, NOT BREAK-EVEN) |
| Older nonoverlapping history | 15m | 7 / +1.6881R | 1 / +2.3447R |
| Older nonoverlapping history | 30m | 2 / +1.3354R | 1 / -1.3035R |
| Older nonoverlapping history | 1h | 1 / -0.1758R | 1 / -1.1971R |

The *recent Lab 15m* consists of **two SL (-1.2596R, -1.3335R) and one TP3 (+2.7143R)**. With 15bps additional one-way cost, recent Lab 15m becomes **-0.7359R**, while Classic 15m becomes **-6.7323R**. In the older market period, Lab 15m comprises one TP3; 30m/1h each one SL. Such samples have severe uncertainty and selection/exposure differences. The alternative's fewer trades may just mean abstention. Sum R across differently overlapping risks/timeframes is **not account PnL**. All fills are hypotheticals, not measured.

## Decision

**Do not activate the liquidity Lab or CHOP in production.** Entry change and next-open fill stress are implemented, CI-tested and run end-to-end; *positive future profitability is not established*. Original TradingView Viprasol Pine parity, including its 2026-11-20 ATR difference, remains unverified. Continue best-effort scheduled public BTC research capture and prospective paper observation separately, monitor future outcomes without optimizing this sample. Original `docs/` GitHub Pages chart, Viprasol Classic rules and permissions unchanged. `discordEligible=false`, `automaticTrading=false`, `profitabilityClaimAllowed=false`.
