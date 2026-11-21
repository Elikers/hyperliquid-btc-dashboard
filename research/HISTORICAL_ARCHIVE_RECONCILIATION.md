# Offline historical candle archive reconciliation

Run `research/reconcile_historical_archives.py` as a pure function against decoded `btc-historical-candles-<runid>` JSON archives, produced by the existing research-only capture workflow. The function `reconcile_archives(records)` validates each archive's SHA-256 and metadata, rejects inconsistent duplicates, counts unique exchange candle close times, and reports internal historical OHLCV gaps for 15m, 30m and 1h.

It is intentionally **not connected to** `collect_forward_artifacts.py` or the forward paper-trading ledger. Overlapping candle copies are counted only once; conflicting copies cause the entire reconciliation to fail. Gaps at the start or end of an unknown historical target period are not implied by the observed edges. A future enhancement could collect and reconcile successive archives using GitHub's read-only artifact API and upload a historical-only summary.

**Historical candles are not evidence that we scored or observed signals at those earlier clock times.** No retrospective LONG/SHORT setups, entry levels, fills, profit, Discord notifications, automatic trades, or Pine parity are reconstructed. This does not solve GitHub's irregular cron executions or change the candle coverage measured from actual compact forward records.

Run tests: `python -m unittest research.test_reconcile_historical_archives -v`
