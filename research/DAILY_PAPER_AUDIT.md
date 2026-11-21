# Daily automated forward paper audit

Workflow: [`.github/workflows/btc-paper-audit.yml`](../.github/workflows/btc-paper-audit.yml).

A new **read-only** daily GitHub Actions workflow runs at **23:28 UTC**, may also run by manual dispatch, and receives one smoke test upon merge through the workflow-file `push` trigger. It does **not** contact broker/wallet execution APIs or Discord.

## How it works

1. Verify all Python research unit tests using Python 3.12.
2. List retained GitHub Actions artifacts through the GitHub API using the ephemeral built-in `GITHUB_TOKEN` with `actions: read` and `contents: read` only; no third-party credentials.
3. Select main-branch `btc-paper-evidence-<run_id>` artifacts created within the most recent 24 hours. Exclude unrelated, expired and off-branch artifacts.
4. Download up to 110 research artifact ZIPs, validate file membership/size and each record's SHA-256 and research-only flags. Missing or conflicting evidence triggers a failed run (not a fabricated performance estimate).
5. Feed the existing, CI-tested [forward paper ledger](forward_paper_ledger.py). Every 15m/30m/1h close is counted once; duplicate samples are removed and missing future candles keep hypothetical setups unresolved.
6. Upload `paper-output/daily_forward_audit.json` as a **90-day GitHub Actions artifact**, with explicit unverified profit/Pine-parity flags and source run IDs.

The daily report is intentionally a **rolling 24-hour window**, not a 30-day cumulative performance claim. Historical 30-day source artifacts remain separately available for deeper on-demand replays while retained. Costs default to illustrative 7 bps *per side*, not observed exchange fills.

## Limits and interpretation

- `event=schedule` jobs may be delayed/skipped; inspect actual Actions runs.
- A single successful scheduled capture occurred in [run #44897289838](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44897289838), but one run is not recurrent reliability.
- An audit with zero downloaded artifacts, zero hypothetical candidates or unresolved trades must **not** be represented as a profitable strategy.
- If 110 compact source artifacts are already present, `truncatedAtArtifactLimit=true`: coverage may be incomplete. Missing bars are recorded where the partial sample exposes them.
- Forward model risk ladder is *not* independently certified as identical to original Pine Viprasol. Discrepancies remain around 15m ATR/SL, bar merge and VWAP.
- This workflow does not modify `docs/`, send notifications, enable live alerts, create orders, or alter original Viprasol Classic settings.

Use the [project handoff](../HANDOFF.md) and actual Actions logs rather than assuming a scheduled workflow has executed.

## Closed-candle coverage measurement (November 22 improvement)

The daily output now contains `closedCandleCoverage` for **15m, 30m, and 1h**, independently of the hypothetical trade ledger. For the rolling UTC window, it counts expected fully closed candle intervals, distinct timestamps actually observed in retained artifacts, and unobserved leading / interior / trailing candle closes. This prevents a sparse hourly Actions schedule from appearing complete merely because the gaps *between* a few observations are small. Duplicate source artifacts never increase the count. No historical candles are inserted to fill absent observations.

These counts represent **observation coverage**, not successful GitHub cron execution rate. A failed or skipped scheduled job may result in an unobserved candle; a late capture can also repeat an earlier close. The coverage metric must not certify original Viprasol parity, win rate, live prices or profitability. All signals, Discord and wallet execution stay disabled.
