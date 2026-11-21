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

## Next unfinished task
**Complete GitHub PR #4 by checking CI and a successful post-merge read-only daily audit artifact smoke test.** Then monitor consecutive scheduled capture runs (one success exists) and evaluate multi-capture paper outcomes without inventing trades or continuity. Continue independent Pine parity work. Continue full source parity checks independently. See priorities in `PROJECT_STATE.md`.

## Prompt for any new chat
> Partner, continue our Hyperliquid BTC development in `Elikers/hyperliquid-btc-dashboard`. Read `PROJECT_STATE.md`, `DECISIONS.md`, `HANDOFF.md`, and the current GitHub Actions runs before working. Continue from the next unfinished verified task without repeating previous questions. Preserve Viprasol Classic unchanged, the working dashboard, no live Discord trade signals, no wallet trading, and no unverified profit claims. Commit safe fixes and update the handoff only after confirming evidence.

## Response style
Keep updates concise and actionable. The user prefers autonomous sequential action within authorized scope, no gratuitous questions, no repetitive status-only messages and no false claims of future background work. Scheduled automation exists separately from interactive chat and cannot exceed its own cadence.

## When this file needs revision
Update the current next-step blocker, most recent confirmed run links/commits, relevant artifacts and any user-approved scope changes. Do not duplicate full source documents, expose credentials or embed private data.
