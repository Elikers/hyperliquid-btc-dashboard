# Real BTC historical research backtest + actual forward evidence

This research-only workflow reads the **latest retained raw capture ZIP from successful GitHub main-branch captures** (not synthetic data). It must contain valid source-stamped 15m, 30m, 1h BTC snapshots with a single UTC capture instant, **2600,1300,650** closed candles respectively in the current capture configuration. That is roughly 27 days per timeframe, but complete ADR14 history starts only after 14 fully completed UTC trading days, leaving about 12 days of eligible evaluation.

## Historical replay

`research/backtest_real_btc_snapshot.py` performs a chronological, *no-future-input* replay of the current seven-factor **Python research approximation** of Viprasol Classic Macro-Off. It detects EMA9/21 crosses from historical closes and only evaluates full seven-factor and ADR gate checks at those closes. Candidate creation receives only bars ending by that point; future OHLC is used **only** for hypothetical outcome simulation. Original score threshold 5/7 and session/weekend/ADR settings remain unchanged.

Idealized entry assumes the **signal close**, which may be unfillable. The replay uses stop-first OHLC logic, adverse stop-gap pricing, TP1 activation of a breakeven stop for subsequent bars and full-size TP3/SL/BE exits. It reports gross and hypothetical net R sums for illustrative one-way combined fee+slippage sensitivity **0, 7 and 15 bps**, and unresolved positions separately. There is a precommitted early/later chronological split within the eligible period, **not** an independent live forward test or calibrated walk-forward validation. Overlapping candidate R sums are not a realistic portfolio curve.

## Genuine forward evidence

The same GitHub Actions run also executes the existing immutable `research.collect_forward_artifacts` against actual retained compact forward observations, with SHA-256 and data-gap checks, separately uploaded to `forward_audit.json`. The historical replay does not replace missing live forward observations, generate "past" signals on unobserved wall-clock times, or count historical candles as forward trades. Incomplete forward records produce unresolved or data-gap outcomes, never favorable invented trades.

## Hard limitations

This is **NOT** verified original TradingView Viprasol Pine parity: current Python EMA/RMA/VWAP/day anchoring, original lower-timeframe `request.security` behavior and historical Pine indicator state remain independently unverified. No genuine full-bar TradingView reference export exists yet; our one earlier source screenshot had ≈0.2978 USDC ATR stop disagreement. Even a positive result on the research replay cannot establish profitability or suitability for live capital.

GitHub Actions artifacts have limited retention. A failed retrieval/invalid source must fail the workflow; no substitution with fabricated data. The workflow is manually dispatchable and also smoke-runs on changes to its own workflow or replay script. It is **not a guaranteed recurring forward sampling service**. No real orders, webhooks, or trading permission are used. Both reports explicitly keep original Pine parity, Discord and automatic trading disabled.
