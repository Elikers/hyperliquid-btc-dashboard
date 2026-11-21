# HANDOFF — How any fresh chat resumes immediately

**Repo:** https://github.com/Elikers/hyperliquid-btc-dashboard
**Dashboard:** https://elikers.github.io/hyperliquid-btc-dashboard/
**Last reviewed:** 2026-11-21, Asia/Manila

## Mandatory bootstrap (do this instead of asking the user to repeat prior work)
1. Use the connected GitHub integration to read `PROJECT_STATE.md`, `DECISIONS.md`, `HANDOFF.md` and `research/VERIFICATION_STATUS.md`. These are state snapshots, not proof that current CI is healthy.
2. Read current `main` commit and latest GitHub Actions runs via `https://api.github.com/repos/Elikers/hyperliquid-btc-dashboard/actions/runs?per_page=100`. This GitHub GET path has been confirmed accessible through the connected GitHub fetch action. Inspect job logs when a run fails.
3. Distinguish `event=push` smoke runs, `event=pull_request` tests and genuine `event=schedule` research captures; a workflow file or a passing unit test is not a scheduled data run.
4. Read source files relevant to the next task and verify actual behavior. Preserve working `docs/` chart, original Viprasol Classic strategy and strict `discordEligible=false` in research.
5. Implement the next narrow safe priority, test locally or through GitHub CI, review evidence, and update `PROJECT_STATE.md` / this handoff **only after verified material progress**.
6. Do not request routine approvals or require repetitive ZIP downloads/PowerShell steps. If blocked, explain the precise authorization or external evidence needed.

## Known verified evidence, not a promise about current status
- Latest verified full research safety suite on `main`: [GitHub Actions 44895978108](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44895978108), success at the time checked.
- Verified full Hyperliquid capture and both artifact uploads: [GitHub Actions 44895884495](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44895884495), **event=push**, success. [Evidence](research/VERIFIED_CAPTURE_RUN_2026-11-21.md).
- 15m cron: `2,17,32,47 * * * *` UTC in [workflow](.github/workflows/btc-forward-capture.yml). **No confirmed scheduled execution at time of this handoff.** Check again before claiming recurring collection works.
- Compact `btc-paper-evidence-<run_id>` artifacts: 30-day retention; full candles: 2-day retention. Deduplicate by timeframe + closedBarEndMs.
- Macro-Off Classic: source-supported and coded, but **exact Pine factor/signal parity unverified**.
- One known ATR/SL mismatch: +0.2978 USDC research minus reference for a November 20 15m LONG, explained in [ATR diagnosis](research/FEED_PARITY_ATR_DIAGNOSIS_2026-11-21.md).
- User-facing GitHub Pages chart was previously confirmed functioning. No 24/7 server, Discord trade alerts or automatic wallet trading.

## New verified milestone — 2026-11-21

- Merged [PR #2](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/2) as [`cdf2b0c5`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/cdf2b0c5be46a7e0d39843498e3414e4310f4021), adding [`research/forward_paper_ledger.py`](research/forward_paper_ledger.py), [11 regression tests](research/test_forward_paper_ledger.py), and [usage/limitations](research/FORWARD_PAPER_LEDGER.md).
- Verified [pull request CI #44897218955](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897218955) **success** and [main push CI #44897257025](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897257025) **success**.
- Ledger deduplicates each closed timeframe bar, checks immutable digest and candidate provenance, quarantines missing bars, computes research-only hypothetical outcomes after entry candle, and never enables Discord or trading.
- **Not yet integrated into autonomous artifact fetching or periodic reporting.** No claim of real trading profitability; scheduled `event=schedule` run remains unverified.

## Verified capture and current daily-audit failure — 2026-11-21

- First successful real scheduled capture: [Actions #44897289838](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897289838), `event=schedule`, success; no multi-hour uptime proof.
- Read-only daily artifact audit added in [PR #3](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/3) and merged at `602fd6e455e0889ec6255cf663f903a3d548dad0`. [Offline CI #44897696487](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897696487) passed.
- First real daily smoke [Actions #44897739711](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897739711) **failed** after 186 passing offline tests: GitHub artifact ZIP download redirected to external signed blob URL and returned HTTP 401 when bearer token was forwarded.
- [PR #4](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/4) contains an HTTPS allowlisted, credential-stripping redirect fix and regression tests. Its actual CI and end-to-end result must be checked before considering the daily workflow operational.
- No change to the dashboard, Classic strategy settings, Discord trade alerts or wallet trading.

## Verified daily research artifact integration — 2026-11-21

- Integrated read-only daily paper ledger artifact discovery/download (see [PR #3](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/3)); initial [smoke #44897739711](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897739711) failed HTTP 401 on cross-host GitHub signed ZIP redirect. Fixed through [PR #4](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/4), merged as [`2a587f0`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/2a587f0004e9587e856f96d2c5e57a8159ea5be5).
- **Verified successful full run:** [daily audit #44898036259](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44898036259), `event=push`, all steps and audit artifact upload succeeded. [Pull request CI #44898035246](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44898035246) and [main CI #44898036198](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44898036198) succeeded.
- Inspected output artifact `btc-paper-audit-44898036259`, ID `14704572593`: 2 source captures, 2 unique closed candles per 15m/30m/1h, no gaps between the two observed closes, **0 candidates and 0 resolved trades**. `profitabilityClaimAllowed=false`, `discordEligible=false`, `automaticTrading=false`.
- First genuine scheduled 15-minute source capture was [#44897289838](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897289838), successful. A **daily** `event=schedule` paper audit and repeated multi-hour 15m source runs are **not yet confirmed**.
- Workflow: [`.github/workflows/btc-paper-audit.yml`](.github/workflows/btc-paper-audit.yml) scheduled `23:28 UTC`, read-only `actions:read` token, daily rolling 24h data and 90-day report artifact. No cumulative 30-day performance dataset yet. Independent original Viprasol Pine parity, especially ATR stop difference, still unverified.

## Verified capture-cadence finding — 2026-11-22 Asia/Manila

- GitHub main at last check: `36fe95119667d0344834d3a640d6a012988375e9`.
- **13** genuinely scheduled BTC capture runs completed successfully from **2026-11-21 11:03:53 UTC** through **21:24:31 UTC**, latest [Actions #44951382679](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44951382679). Run creation times have **41–63 minute gaps**, markedly sparser than configured `:02, :17, :32, :47 UTC`. Do not claim four observations/hour or exact reason for skipped/delayed scheduling; check candle artifact timestamps separately.
- Daily paper audit only confirmed as successful push smoke, not as scheduled execution, in latest run history. Its configured daily schedule is 23:28 UTC.
- Priority: rigorous schedule/candle coverage metrics and missing-data quarantine, then cumulative evidence and independent Pine parity. Do not activate any trading alerts.

## Verified coverage milestone — 2026-11-22

- [PR #5](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/5) merged at [`956d9ba6`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/956d9ba620b0a8b4d10b450835c59160b0aca6c0): [`research/observation_coverage.py`](research/observation_coverage.py) computes full-window expected versus observed 15m/30m/1h closed-bar coverage, separately from paper trade lifecycle.
- Verified [PR CI #44953904949](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44953904949), [main CI #44953938041](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44953938041) and **full daily-audit push smoke** [#44953938033](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44953938033), whose uploaded artifact `14727350084` was inspected.
- Actual 24h window ending 2026-11-21 21:54 UTC: 14 source artifacts, **15m 14/96 (14.6%), 30m 14/48 (29.2%), 1h 12/24 (50.0%)**, including leading and internal gaps; 0 hypothetical candidate setups. Not a full day of observed signals, no profit claims. Daily audit `event=schedule` unverified; only `event=push` proven.
- Next check: scheduled-run timing/true artifact candle coverage, then cross-day continuous evidence and original-Pine reference parity. Do not activate real alerts/trading.

## Verified schedule execution audit — 2026-11-22

- Merged [PR #6](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/6), [`becb4e8`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/becb4e805b7dd093523bd55f749ab7da4b8c6a50), adding independently reported run-level GitHub schedule health to the existing 24-hour research-only paper audit.
- Verified [PR CI #44954350415](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44954350415), [main CI #44954379390](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44954379390), and [audit smoke #44954379350](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44954379350), all **success**. Real log reported **205 passing tests**, 13 actual scheduled captures versus 96 configured cron opportunities over rolling 24h, 14 source artifacts; per-frame candle coverage unchanged at 14/96 (15m), 14/48 (30m), 12/24 (1h), no hypothetical trade candidates. Uploaded JSON artifact ID `14727231425`.
- A `13/96` observed-to-configured ratio is a volume comparison **not proof of exactly 83 skipped cron triggers**; GitHub can delay runs and records creation timestamps. No true 15m coverage, profitability, source-Pine parity or live alert readiness proven.
- Next: improve *actual* data reliability with safe historical-only reconstruction/retrieval clearly isolated from forward observations, evaluate scheduling options, protect read-only policies; continue independent Viprasol reference comparison.

## Verified historical-only capture archive — 2026-11-22

- Merged [PR #7](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/7), [`ebae51b`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/ebae51bb7119d466afa7b53d9cbaa5a99c0da160): `research/historical_candle_archive.py` with 9 tests and `research/HISTORICAL_CANDLE_RECOVERY.md`. Every successful capture additionally uploads 30-day `btc-historical-candles-<runid>` containing historical-only 24h BTC 15m/30m/1h candles already fetched during that run.
- Verified successful [PR CI #44956126470](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44956126470), [main CI #44956151263](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44956151263), and live public-market [capture smoke #44956151280](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44956151280) with source, paper and historical uploads. Historical artifact ID `14727154786` was downloaded and inspected: digest passed, 15m=96 bars, 30m=48 bars, 1h=24 bars, historicalOnly=true, `recoveredCandlesAreForwardObservations=false`, all alert/trade/profit flags false.
- This mitigation persists 24h historical OHLCV; it **cannot** recover past scored forward observations, guarantee a 15m GitHub cron, or prove Viprasol parity.

## Verified historical-only archive reconciliation — 2026-11-22

- Merged [PR #8](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/8), [`70f150c`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/70f150c0ca28d60205dfcc5b0d2f38485995a69a): new `research/reconcile_historical_archives.py`, 9 tests and `research/HISTORICAL_ARCHIVE_RECONCILIATION.md`. Pure offline collector **not yet automatically ingesting multiple stored archive artifacts**. Checks SHA256, metadata, duplicate candles, contradictory OHLCV and genuine interior historical gaps; output is research-only and **never** a forward signal/trade.
- [PR CI #44956457313](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44956457313) and [main CI #44956485399](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44956485399) passed. No change to working dashboard, original Classic config, capture schedule, Discord trading alerts, automatic trading.
- Next safe step: a strictly read-only, separate historical-artifact fetch/report workflow with documented limits and real artifact validation. Do not silently increase forward observation coverage or claim source Pine parity.

## Verified automated historical archive audit — 2026-11-22

- [PR #9](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/9) merged as [`3d17d27`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/3d17d2701a87637baa6df7a15ada2a3244e10c7c). Independent historical-only collector and daily workflow `23:38 UTC`; authenticated read-only GitHub Actions API, signed artifact redirects handled without sharing credentials, strict ZIP/archive SHA256 checks, per-timeframe OHLCV de-duplication and gap detection. The existing forward observation collector is not modified.
- **PR CI #44956846630, main CI #44956876951, end-to-end audit #44956876971 succeeded.** Inspected actual downloaded audit artifact ID `14727911898`: one source archive, 15m 96 / 30m 48 / 1h 24 historical candles, 0 internal gaps, all trading/Discord/profit flags false. Reconciliation across **multiple real** archives awaits additional source archives. First genuine daily scheduled audit run is unverified.
- Next priority: actual free scheduling reliability and independent Pine signal-factor/event parity, then net forward evidence. Do not treat historical archive union as a live captured signal history.

## Redundant BTC capture pilot deployed and smoke-verified — 2026-11-22

- [PR #10](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/10) merged as [`b279fbf`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/b279fbf17689d8d70c37b6f873b9b7fc5f1de36e); UTC cron `7,12,22,27,37,42,52,57 * * * *` offers twice-per-candle best-effort research attempts (8 opportunities/hour), preserves deduplication of actual forward closed bars, and expands bounded daily audit caps to 250 sources. Historical daily artifact collection lookback reduced to 24h to keep work bounded. [Pilot contract](research/REDUNDANT_CAPTURE_PILOT.md), stable decision D-013.
- Verified [PR CI #44959940737](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44959940737), [main CI #44959978798](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44959978798), [capture smoke #44959978832](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44959978832), [historical audit smoke #44959978804](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44959978804), [paper audit smoke #44959978841](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44959978841), all **success**. Research audit ran **230 passing tests**. All three workflows uploaded real artifacts.
- Actual output: forward distinct 15m **17/96**, 30m **16/48**, 1h **13/24** closed bars in a rolling 24h window, no hypothetical trades; two independent historical source archives combined to 15m **98**, 30m **49**, 1h **24** unique historical bars, no interior historical gaps. These are not proof of profit or original Pine event parity.
- **Important:** `15/192` scheduled-run-to-expected volume ratio in initial audit spans old and new cron and MUST NOT be interpreted as reliable before/after performance. Need fully post-deployment 24h data before judging pilot. Discord/wallet/automatic trades remain OFF.

## Post-rollout scheduled-only pilot audit — verified 2026-11-22

- [PR #11](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/11), [`8fe7033`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/8fe7033261ea5d02937224d6dae5003000171100): `research/post_rollout_capture_metrics.py` and tests; collects actual successful main-branch `event=schedule` run IDs **only**, matches them with SHA-256-validated compact forward observations, and excludes push/manual/historical artifacts. Clean baseline **2026-11-21 23:15 UTC**, no reliability-pass claims before 24h.
- [PR #12](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/12), [`04e1546`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/04e15463e5a82bd63e92ae99aee27579fc3e6231) fixes later evaluations to use the latest **rolling 24h** rather than all time since rollout, to match retained daily artifact horizon.
- Verified [corrected PR CI #44961532738](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44961532738), [main CI #44961559773](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44961559773), [paper audit smoke #44961559745](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44961559745), [rolling fix PR CI #44961688640](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44961688640) and [main CI #44961719164](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44961719164), all successful. Actual downloaded paper report ID `14730095911` says 8 minutes after baseline, 0 eligible post-rollout scheduled runs, 0 eligible bars, insufficient duration. Do **not** claim scheduling improved or degraded until a complete clean sample. PR #12 did not cause an additional audit smoke because its filename is outside that workflow's `push.paths`; no new production audit output yet for rolling case.
- No strategy/dashboard modifications. Viprasol Pine reference parity still missing. Discord and automatic trading OFF.

## Source Pine full-bar evidence checker CI-verified — November 22, 2026

- Merged [PR #13](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/13), commit [`03c514d`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/03c514dca430eff3f7feb1adf555e5ff720c7c5f). Added `research/independent_pine_full_bar_audit.py`, 13 regressions, and `research/INDEPENDENT_PINE_FULL_BAR_EVIDENCE.md`. It compares **separately sourced** original TradingView 15m/30m/1h Viprasol Macro-Off closed bars, including **no-signal bars**, seven factors and Entry/SL/TP; rejects gaps, duplicates and inconsistent prices. This **does not** generate/obtain any authentic Pine reference data or grant certification from self-declared metadata.
- [PR CI #44961938301](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44961938301) and [main CI #44961978942](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44961978942) passed. No changes to original Viprasol strategy/dashboard, capture schedule, Discord or wallet permissions.
- As of this check, 24h post-rollout schedule pilot not yet complete, and genuine TradingView per-bar original Pine outputs remain unavailable. **ATR stop delta ~0.2978 USD** on one legacy 15m reference LONG still unresolved, and profitability unproven.

## Verified real BTC research replay and forward test — 2026-11-22

- [PR #14](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/14), commit [`145efc3`](https://github.com/Elikers/hyperliquid-btc-dashboard/commit/145efc36578457d3a0a7777f5113ef29b819d846): read-only historical BTC research backtest from latest retained raw GitHub BTC snapshots, **separate** real forward paper audit, 0/7/15 bps cost sensitivity, stop-first and gap-worse exits; no source settings changes. [PR CI #44962408746](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44962408746), [main CI #44962464226](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44962464226), and full [backtest-forward run #44962464184](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44962464184) **passed**. Downloaded and inspected actual artifact `14729679858`.
- Real saved historical source: BTC closed 15m=2600/30m=1300/1h=650, approximately 27 days each. Post-warmup eligible 1160/580/290 closed bars. **Research Python approximation**, 27 resolved candidates (15m 13,30m 7,1h 7). At assumed **7 bps per side**, net sum: **15m -3.073838R, 30m -3.246308R, 1h +0.192830R**; not account PnL. Outcomes 15m 6SL/5BE/2TP3; 30m 5SL/1BE/1TP3; 1h 5SL/0BE/2TP3. This small-sample testing does not prove original Viprasol signal parity nor profitability.
- Actual forward audit in same run: **18 source captures**, 15m **18/96**, 30m **17/48**, 1h **14/24** unique closed-bar observations, **zero candidate trades**, zero resolved outcomes. Forward fee-adjusted performance cannot be computed.
- Current roadmap: independent genuine original TradingView Pine full-bar 15m/30m/1h reference and ATR parity before calling original indicator accurate; collect longer non-lookahead forward evidence; assess new cron only after **2026-11-22 23:15 UTC** with clean 24h. Keep original Classic/dashboard frozen, unverified Discord trade alerts and automatic trading OFF.

## Next unfinished task
1. **Independent original TradingView Viprasol Classic Macro-Off 15m/30m/1h reference**: compare verified Pine complete closed bars (including no-signal bars, all seven factors, Entry/SL/TP, ATR stop) against the current Python replay; source authenticity and provider candle parity required. Do not treat backtested Python candidates as original indicator outputs.
2. **True forward outcomes and capture cadence**: continue actual read-only GitHub-scheduled source observations. Use `postRolloutPilot` after clean 24h boundary **2026-11-22 23:15 UTC / Nov 23 07:15 Manila**, compare unique candle coverage vs baseline, monitor resource use. Data gaps and zero candidates are not profit evidence.
3. Work with existing real backtest research result (historical run #44962464184) for integrity/error diagnostics and cost-aware robustness, **without optimization to this sample**. Retain no trading, no Discord, no unsupported profitability claims.

## Prompt for any new chat
> Partner, continue our Hyperliquid BTC development in `Elikers/hyperliquid-btc-dashboard`. Read `PROJECT_STATE.md`, `DECISIONS.md`, `HANDOFF.md`, and the current GitHub Actions runs before working. Continue from the next unfinished verified task without repeating previous questions. Preserve Viprasol Classic unchanged, the working dashboard, no live Discord trade signals, no wallet trading, and no unverified profit claims. Commit safe fixes and update the handoff only after confirming evidence.

## Response style
Keep updates concise and actionable. The user prefers autonomous sequential action within authorized scope, no gratuitous questions, no repetitive status-only messages and no false claims of future background work. Scheduled automation exists separately from interactive chat and cannot exceed its own cadence.

## When this file needs revision
Update the current next-step blocker, most recent confirmed run links/commits, relevant artifacts and any user-approved scope changes. Do not duplicate full source documents, expose credentials or embed private data.
