# Daily automated forward paper audit

Workflow: [`.github/workflows/btc-paper-audit.yml`](../.github/workflows/btc-paper-audit.yml).

A new **read-only** daily GitHub Actions workflow runs at **23:28 UTC**, may also run by manual dispatch, and receives one smoke test upon merge through the workflow-file `push` trigger. It does **not** contact broker/wallet execution APIs or Discord.

## How it works

1. Verify all Python research unit tests using Python 3.12.
2. List retained GitHub Actions artifacts through the GitHub API using the ephemeral built-in `GITHUB_TOKEN` with `actions: read` and `contents: read` only; no third-party credentials.
3. Select main-branch `btc-paper-evidence-<run_id>` artifacts created within the most recent 24 hours. Exclude unrelated, expired and off-branch artifacts.
4. Download up to 250 research artifact ZIPs, validate file membership/size and each record's SHA-256 and research-only flags. Missing or conflicting evidence triggers a failed run (not a fabricated performance estimate).
5. Feed the existing, CI-tested [forward paper ledger](forward_paper_ledger.py). Every 15m/30m/1h close is counted once; duplicate samples are removed. The first observation timestamp is the earliest time a signal could be acted on: any subsequent candle that opened before that instant is excluded, and entry waits for the first future candle open at/after observation. Missing candles after that entry quarantine outcomes as `DATA_GAP`.
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

## Scheduled GitHub execution audit

The report additionally includes `githubScheduleReliability`, obtained with the read-only GitHub Actions API filtered to the actual capture workflow and `event=schedule`. It counts **completed successes, failures, pending and all observed scheduled runs** in the requested window, compares the count with the current redundant pilot's eight configured opportunities/hour (`7,12,22,27,37,42,52,57 UTC`) and records time gaps *between run creations*. This is **not** an exact count of skipped triggers: GitHub exposes creation time rather than an authoritative scheduled-slot timestamp, and delayed starts can cross a window boundary.

This is intentionally separate from `closedCandleCoverage`: a scheduled run may collect the same close as another run, and a missing run does not mean a historical candle is unavailable from the exchange. Historical recovery is research-only and **cannot** be presented as a forward signal collected at the time. Never impute a trade, entry, or verified Pine signal into missed windows.

## November 22 redundant-capture research pilot

The latest workflow offers two nominal capture attempts after each 15m candle close, eight configured UTC cron opportunities/hour. The rolling 24h forward archive cap is **250**, not 110. Schedule-volume comparisons spanning the cron change are not valid reliability rates. See [pilot design and reversibility](REDUNDANT_CAPTURE_PILOT.md). No guarantee of wall-clock execution or live alerts.


## Causal Classic forward-entry correction (2026-11-28)

A compact observation is captured **after** the signal candle closes. The ledger therefore must not score a later candle whose open already occurred before that observation. The corrected model excludes those pre-observation opens, waits for the first later candle open at/after the observation timestamp, and re-anchors the signal-time ATR14 × 1.5 risk distance and 1R/2R/3R levels around that executable open. If no such open is present, the setup is `AWAITING_CAUSAL_ENTRY`; if later observed candles have a gap after entry, the outcome is `DATA_GAP`. Stops crossed by an adverse opening gap are priced at that open.

This is a research execution correction only. It does not change EMA9/21 crossover, 5/7 score, ADR14, ATR14 multiplier or target multiples; it does not certify TradingView parity or exchange fills. The 7 bps per-side cost remains illustrative, not measured. All alert, wallet and automatic-trading flags remain false.
