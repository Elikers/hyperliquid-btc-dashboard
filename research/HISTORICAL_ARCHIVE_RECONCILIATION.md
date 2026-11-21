# Offline historical candle archive reconciliation

Run `research/reconcile_historical_archives.py` as a pure function against decoded `btc-historical-candles-<runid>` JSON archives, produced by the existing research-only capture workflow. The function `reconcile_archives(records)` validates each archive's SHA-256 and metadata, rejects inconsistent duplicates, counts unique exchange candle close times, and reports internal historical OHLCV gaps for 15m, 30m and 1h.

It is intentionally **not connected to** `collect_forward_artifacts.py` or the forward paper-trading ledger. Overlapping candle copies are counted only once; conflicting copies cause the entire reconciliation to fail. Gaps at the start or end of an unknown historical target period are not implied by the observed edges. A future enhancement could collect and reconcile successive archives using GitHub's read-only artifact API and upload a historical-only summary.

**Historical candles are not evidence that we scored or observed signals at those earlier clock times.** No retrospective LONG/SHORT setups, entry levels, fills, profit, Discord notifications, automatic trades, or Pine parity are reconstructed. This does not solve GitHub's irregular cron executions or change the candle coverage measured from actual compact forward records.

Run tests: `python -m unittest research.test_reconcile_historical_archives -v`

## Automated read-only collector (November 22)

The separate `.github/workflows/btc-historical-audit.yml` workflow requests `actions: read` and `contents: read` only. It runs once daily on a best-effort GitHub schedule (`23:38 UTC`), supports manual dispatch and smoke-tests when its own code changes. It discovers retained `btc-historical-candles-<runid>` archives from main, downloads a bounded set of recent 72-hour artifacts over HTTPS with safe credential-stripping redirect handling, validates each archive and SHA-256, and invokes the offline reconciler. The JSON `btc-historical-audit-<runid>` report has 90-day artifact retention.

**Important:** Its 72-hour window filters **artifact creation times**, not the exact full historical span of the recovered candles. The result describes the union between the oldest and newest available recorded historical bar, not a validated forward capture record. It is allowed to report no archives or a partial collection; `artifactLimitReached` and `exhaustiveWithinWindow` surface this limitation explicitly. It never supplies data to the forward paper ledger or alters its 15-minute observation-coverage fractions. This scheduled report, like all GitHub schedules, is best-effort and cannot ensure an exact daily execution time.

Run: `python -m research.collect_historical_artifacts --hours 72` with a short-lived GitHub Actions read-only `GITHUB_TOKEN`, or inspect its uploaded report. Do not place tokens in source files.

## Updated bounded audit intake during cron pilot

The research-only audit now filters artifacts created over the latest **24 hours** and limits to **250** historical sources (previously 72h/120), to bound work under the redundant capture pilot. Each source includes up to 24h of trailing candles, so its covered market window can begin before that artifact-creation cutoff. Do not call this a 72-hour report or a forward observation feed.
