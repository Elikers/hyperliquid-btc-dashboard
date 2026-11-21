# PROJECT_STATE — Hyperliquid BTC / Viprasol Research
**Last reviewed:** 2026-11-21 (Asia/Manila)
**Authoritative repository:** https://github.com/Elikers/hyperliquid-btc-dashboard
**Public chart:** https://elikers.github.io/hyperliquid-btc-dashboard/
**How to resume:** Read this file, [DECISIONS.md](DECISIONS.md), [HANDOFF.md](HANDOFF.md), then check current `main`, GitHub Actions runs and the relevant source files. GitHub is the technical source of truth; this document is a dated snapshot, not a substitute for current CI evidence.

## Objective
Develop a dependable, independently verified **Hyperliquid BTCUSDC perpetual** research and eventually notification system based on the user's original Viprasol Pine v6 indicator. Reduce the user's repetitive downloads, prompts, manual approvals and chat-dependent continuity. Optimize for verifiable signal quality and risk-adjusted performance, not merely high win rate. **No orders, no wallets, and no live trade-signal Discord notifications** without a separate verified readiness decision.

## Working components — distinguished by evidence
| Component | Verified state as of review | Evidence |
| --- | --- | --- |
| Browser-based live chart, 15m/30m/1h | Deployed; user previously confirmed the chart and prices worked. Not a permanently running backend | `docs/`, Pages workflow, user acceptance |
| Offline research test suite | Latest checked main-branch research run **succeeded**, including safety gate | [run 44895978108](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44895978108) |
| Full public BTC capture and research evaluation | **One end-to-end push-triggered smoke run succeeded** | [run 44895884495](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44895884495), [verified report](research/VERIFIED_CAPTURE_RUN_2026-11-21.md) |
| 15-minute GitHub Actions capture schedule | Configured at `:02, :17, :32, :47 UTC`; **one successful scheduled capture verified**, ongoing cadence still not established | [workflow](.github/workflows/btc-forward-capture.yml). Scheduled jobs can be delayed/skipped |
| Cross-timeframe candle checks | Enabled: 30m/1h OHLCV reconstructed from 15m; failed inputs block scoring | `research/cross_timeframe_audit.py` |
| Source-supported Viprasol Classic, macro OFF | Seven-factor research evaluator with EMA9/21 entry gates and ADR14 checks; **not Pine-parity verified** | `research/classic_macro_off.py`; `research/adr_gate.py` |
| Original Viprasol macro ON | 8-factor research audit; real `CME_MINI:NQ1!` symbol, continuous roll/session parity unresolved | `research/eight_factor_audit.py` |
| Separate BTC-only Lab | Experimental; not represented as the original strategy | `research/btc_only_lab.py` |
| Forward paper-evidence collection | Compact artifact for each successful run, 30-day GitHub Actions retention; test run generated artifact | `research/forward_observation.py`, [run 44895884495](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44895884495) |
| Live Discord trade alerts / 24x7 backend | **Not deployed**; Discord webhook delivery was tested previously on the user's computer, but this does not authorize alerts | No trade-alert sending in this repository |
| Profitability | **Unproven** | [limited historical replay](research/HISTORICAL_CANDIDATE_REPLAY_2026-11-21.md) |

## Source and methodology
- Original reference: user-supplied Viprasol Pine Script v6 (see `research/VERIFICATION_STATUS.md` for provenance/hash). Avoid publishing copyrighted source unnecessarily.
- Pine Macro-Off mode is original-source-supported (`macroFactorOnInput=false`): **seven** factors rather than eight; Nasdaq NQ1! is not required for that configuration.
- Original model boundaries: EMA9/EMA21 cross on closed bar; seven-factor 5/7 confluence by default; selected session/weekend and 14-day ADR gates; ATR(14) × 1.5 stop; TP1/TP2/TP3 at 1R/2R/3R. Confirm exact switches and Pine details against source rather than assuming defaults are identical in every version.
- 15m, 30m and 1h all rely on genuinely closed Hyperliquid BTC public candles and bar-aligned 15m confirmation. ATR and indicator warmup, VWAP anchoring, `request.security` merge and source-series comparison still need independent evidence.
- Data safeguards: common capture timestamp; reject missing/stale/misaligned OHLCV and inconsistent timeframe aggregation; generated outputs are `researchOnly`, `discordEligible=false`.

## Verified update — 2026-11-21, paper ledger foundation

- **New research-only offline forward paper ledger merged to `main`**, commit [`cdf2b0c5`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/cdf2b0c5be46a7e0d39843498e3414e4310f4021) via [PR #2](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/2).
- [Pull-request CI #44897218955](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897218955) **passed**, followed by [main-branch CI #44897257025](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897257025) **passed**.
- New [`research/forward_paper_ledger.py`](research/forward_paper_ledger.py) and **11 regression tests** implement SHA-256 evidence integrity checking, de-duplication by timeframe and closed-candle timestamp, rejection of inconsistent duplicate records, fail-closed missing-bar audit, and hypothetical SL/BE/TP3 outcomes after the entry bar. All results remain research-only, with illustrative execution costs and explicit unverified profitability/Pine-parity flags.
- **This is the offline analysis engine, not yet unattended artifact ingestion or historical profitable results.** [Usage and limits](research/FORWARD_PAPER_LEDGER.md).
- As of this check, only a previously verified **push-triggered** BTC capture ([#44895884495](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44895884495)) was present. Successful recurring scheduled runs have **not** been confirmed.

## Engineering update — 2026-11-21, scheduled capture and paper audit rollout

- Verified the first successful scheduled public BTC capture: [Actions #44897289838](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897289838), `event=schedule`, full pipeline and paper artifacts. This proves one scheduled run, not continuous reliability.
- Implemented and merged [PR #3](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/3), commit `602fd6e455e0889ec6255cf663f903a3d548dad0`: read-only artifact listing/download, compact ZIP verification, feed into existing paper ledger and a daily audit GitHub Actions workflow. The PR offline suite [#44897696487](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897696487) passed.
- **The first end-to-end daily audit run failed**: [Actions #44897739711](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897739711), 401 while downloading an Actions artifact from external signed storage after GitHub's 302 redirect. Unit tests had passed (186), but that was insufficient.
- [Fix PR #4](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/4) strips the bearer token from cross-host signed artifact redirects, validates HTTPS/host, and adds tests. **Not yet merged or CI-verified as of this update.** Do not report daily audit production success until a real smoke run uploads a valid report.

## Verified daily paper audit integration — 2026-11-21

- Automated, read-only daily GitHub artifact audit merged via [PR #3](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/3) and secure redirect correction [PR #4](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/4); deployed fix commit [`2a587f0`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/2a587f0004e9587e856f96d2c5e57a8159ea5be5).
- **Verified full production smoke success:** [BTC paper research daily audit run #44898036259](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44898036259), `event=push`, after correcting a genuine external artifact redirect HTTP 401 ([earlier failed run #44897739711](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897739711)).
- CI passed at both [pull-request #44898035246](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44898035246) and [main #44898036198](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44898036198); **186+ research tests** ran at the earlier integration check.
- Downloaded actual audit artifact `btc-paper-audit-44898036259` (ID `14704572593`), which reported **2 raw source artifacts**, IDs of runs **44897289838** (`schedule`) and **44895884495** (`push`). Per 15m/30m/1h: **2 distinct closed bars, 0 gaps between those two, 0 hypothetical candidates, 0 resolved trades**. All alert/trading/profitability flags explicitly false.
- [Daily workflow](.github/workflows/btc-paper-audit.yml) is configured for `23:28 UTC`, with rolling 24h artifact inputs and 90-day audit-report retention. **One successful push smoke does not establish that the daily schedule has executed.** [Implementation/limitations](research/DAILY_PAPER_AUDIT.md).
- Next work: monitor more `event=schedule` capture and audit executions; build durable cross-day cumulative research reporting (daily 24h reports are not yet a 30-day trade history), and obtain independent source-Pine parity evidence before any profitability or Discord claims.

## Specific unresolved evidence
1. **Scheduled recurrence:** First real `event=schedule` capture **succeeded** in [run #44897289838](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897289838), 2026-11-21 11:03 UTC. Multiple-hour coverage and missed-trigger rate remain unverified.
2. **Bar-by-bar parity:** Need independent original-Pine closed-bar factors, zero-signal periods, LONG/SHORT entry times and exits across all three timeframes; unit tests and model-vs-model comparisons are insufficient.
3. **ATR discrepancy:** On a 2026-11-20 reference LONG, Python stop ≈61,667.3978 vs screenshot ≈61,667.1 (difference ≈0.2978). Numerous ATR warmup seeds converge; source candle/provider/settings parity remains unresolved. See [diagnosis](research/FEED_PARITY_ATR_DIAGNOSIS_2026-11-21.md).
4. **Profit:** Older 35 candidate examples (not verified Classic events) yielded 20 SL, 9 BE, 6 TP3, summed gross -2R under a simplified full-position model. The 15m historical export was too short to certify ADR14. **Do not quote this as strategy win rate or expected return.**
5. **Forward evaluation:** Need de-duplicated, non-lookahead paper-trade lifecycle tracking (one record per timeframe + candle close), fee/slippage uncertainty, missed schedule detection and statistical confidence.
6. **Live service:** No always-on monitoring server; GitHub Pages is browser-only and scheduled Actions are not 24/7 real-time alert delivery.

## Priorities (execute sequentially; no routine user approvals)
P0 **First scheduled run verified**, monitor multiple-hour continuity and failed jobs via live GitHub API. P1 **Read-only 24h artifact ingestion and offline ledger both implemented; end-to-end push smoke CI verified**. Next verify genuine daily scheduled execution and develop cross-day cumulative history without false claims. P2 Pursue independent Pine parity and ATR discrepancies without changing original thresholds. P3 Evaluate out-of-sample net expectancy, drawdown and execution assumptions. P4 Consider secure continuous hosting and Discord only after an explicit readiness and risk review.

## Operational rules
- Read [DECISIONS.md](DECISIONS.md) before modifying strategy or infrastructure.
- Keep `docs/` and existing Pages workflow functional. Do not replace the browser chart as part of research.
- Commit narrow changes with tests; verify GitHub CI, artifact inputs and output whenever accessible. Never claim an automation or schedule succeeded without a run record.
- Never paste/store secrets or private webhook URLs in this public repository.
- Update this file for **verified material** changes, not every routine chat message.
