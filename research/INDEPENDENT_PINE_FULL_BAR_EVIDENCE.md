# Independent Viprasol Classic Macro-Off closed-bar reference gate

Research tool: `research/independent_pine_full_bar_audit.py` (`compare_full_bar_pine`).

## Required independent inputs

A **genuine original TradingView Pine** reference (not derived from research Python candidates), for `HYPERLIQUID:BTCUSDC.P`, with original unchanged Viprasol Macro-Off settings and original Pine source checksum, covering **every closed bar including bars with NO SIGNAL**, across 15m, 30m, 1h. Separate candidate calculations must be aligned to the same exchange candle ends. Each row has `timeframe`, `closedBarEndMs` (Unix ms end inclusive), `signal` (`LONG`, `SHORT`, or JSON null), and `factors` with exactly seven explicitly boolean keys: `ema,rsi,macd,vwap,adx,volume,rsi15m`. Every signal also requires `entry,stop,tp1,tp2,tp3` prices; no-signal bars must not have prices.

The metadata declaration is `sourcePlatform=TradingView`, `sourceMode=VIPRASOL_CLASSIC_MACRO_OFF`, `pineSourceSha256`, `symbol=HYPERLIQUID:BTCUSDC.P`, `settings=original_unchanged`, `exportMethod`. Merely filling these fields in **does not prove** TradingView provenance; a reviewer must independently establish it.

The comparison rejects nonaligned closed candles, duplicate timeframe+close, malformed factor input and invalid price ladders. It reports reference bars absent from candidate, candidate bars absent from reference, extra/missing signals **including no-signal bars**, individual factor disagreements and Entry/SL/TP differences. Both sides having the same *gap* is not evidence of complete coverage. Precision and certification are not inferred from no-event periods.

## Current evidence status

As of November 22, 2026, we possess a **single** user-provided original Viprasol reference 15m LONG from November 20 with entry 62,077.0 and displayed stop 61,667.1; independent local reconstruction yielded stop ~61,667.3978, discrepancy ~0.2978. Other 15m/30m/1h source-output rows, no-event closed bars, exact TradingView bar series and authenticated settings/export origin are **not yet available** in this repository. This test suite uses only constructed fixtures, **not** invented TradingView source outputs.

The audit's `independentTradingViewSourceVerified`, `originalViprasolVerified`, `discordEligible`, `automaticTrading`, and `profitabilityClaimAllowed` are always false, even for perfect synthetic or self-declared source rows. No strategy setting changes, source-code copyright publishing, trading signals, wallet use, or webhook calls are authorized by this work.

Test: `python -m unittest research.test_independent_pine_full_bar_audit -v`
