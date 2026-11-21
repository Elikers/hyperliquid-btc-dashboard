# Historical-only BTC candle recovery

The scheduled capture workflow now retains an additional **30-day GitHub Actions artifact** named `btc-historical-candles-<runid>`, containing `historical_candles_only.json`. It uses the exchange candles already fetched, checked and used by the existing capture stage. It makes **no additional exchange API requests**.

Each archive contains up to the **most recent 24 hours of closed and contiguous BTC 15m/30m/1h OHLCV candles**, their original exchange timestamps, a common UTC capture time, provenance, an integrity SHA-256 and immutable conservative flags. The current capture must succeed for it to be produced. Archives from a late or sparse capture can preserve OHLCV of market periods missed by *forward observation jobs*, provided those periods remain retrievable in the market history at capture time.

## Critical separation

Historical market candles **are not historical forward signal observations**. In particular, their scores, Entry/SL/TP, hypothetical trade actions, Discord eligibility and wall-clock presence at the missed time are **not reconstructed**. Source-Pine parity remains unverified. The file lacks `recordSha256` and `timeframes[tf].bar` from the compact forward evidence schema, preventing ingestion through the existing forward-paper ledger.

Coverage in `closedCandleCoverage` still measures *actual forward artifacts only* and is intentionally **not increased** when this archive includes previously missed intervals. Recovery improves retention of historical OHLCV, not a best-effort GitHub cron's exact 15-minute scheduling. The existing full snapshots are retained for 2 days; this separate 24-hour historical subset lasts 30 days, subject to GitHub Actions artifact retention and deletion.

## Independent validation

`python -m unittest research.test_historical_candle_archive -v`

The capture workflow also runs the complete safety suite before fetching public candles. Do not merge this new archive into forward trade outcomes. Real-time alerting and automatic trading remain disabled.
