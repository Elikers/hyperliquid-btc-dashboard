# BTC feed consistency and ATR diagnosis — 2026-11-21

## Source basis

Offline research used the previously supplied local Hyperliquid BTC dataset `Hyperliquid_BTC_GitHub_Ready/research/reference_btc_candles.csv` (3,612 rows across 15m/30m/1h) and the user-supplied original Viprasol Pine v6 source. It did **not** use a TradingView authenticated chart feed or a licensed NQ1! service.

## Independently reconstructed BTC timeframes

Using 15-minute candle OHLC and the **sum of 15m volumes**, we reconstructed every higher-timeframe bar that had all its constituent lower-timeframe candles present. The historical CSV contains 1,204 candles per timeframe, but their historical starting times differ, so only overlapping complete groups are comparable.

| Higher timeframe | Complete overlapping groups | OHLC mismatches | Volume mismatches |
| --- | ---: | ---: | ---: |
| 30m | 601 | 0 | 0 |
| 1h | 300 | 0 | 0 |

All comparisons were exact to 1e-6 for OHLC and 1e-5 for volume. This suggests the existing public research files are internally consistent across 15m/30m/1h. It does **not** establish exact TradingView candle/session parity, signal accuracy, or strategy profitability.

**Protection implemented:** [`cross_timeframe_audit.py`](cross_timeframe_audit.py) reconstructs complete groups on each fresh capture and refuses inconsistent or too-short comparisons. [`evaluate_public_snapshot.py`](evaluate_public_snapshot.py) now fails closed before computing candidate signals when this audit fails. [Regression tests](test_cross_timeframe_audit.py) cover OHLC/volume corruption, missing bars, duplicate bars and boundary conditions. All 9 local cross-timeframe unit tests passed before publishing.

## Concrete 15m ATR/SL discrepancy still unresolved

For the previously supplied original Viprasol 15m LONG screenshot, the candle opened **2026-11-20 14:15 UTC** with entry **62,077.0 USDC** and a displayed stop of **61,667.1**.

Recomputed using the **1,187 provided 15m candles up to and including that close**, Wilder RMA(14) initialized with the SMA of the first 14 true-range values:

- Research ATR14: **273.068130152965**;
- Research stop distance (1.5×ATR): **409.602195229447**, stop **61,667.39780477**;
- Screenshot-implied ATR from its rounded stop: approximately **273.26666667**;
- Stop discrepancy: **0.29780477 USDC**.

The displayed stop's nearest-tenth rounding uncertainty is only about 0.05 USDC, so the gap is larger than display rounding alone can explain. The discrepancy may reflect different source OHLC bars, indicator history, applied chart settings, or candle/series alignment. **Do not claim which cause is responsible without independently comparing the underlying historical bars and Pine ATR values.** The Pine source's stop formula itself is `ta.atr(14) * 1.5`, which is faithfully represented by the research ladder formula.

## Important limitation of the older historical dataset

The local history exported **1,204 bars per timeframe**, but that means different time spans: **15m = 12.54 days** (November 8–20 UTC), **30m = 25.08 days** (October 26–November 20 UTC), and **1h = 50.17 days** (October 1–November 20 UTC). The 15-minute history **cannot independently reproduce the original 14 fully completed daily ranges** used by the source's ADR gate. Therefore, the older 35-candidate analysis is **not** a validated complete Viprasol Classic Macro-Off backtest, regardless of its recorded outcomes. The scheduled snapshot collector now requests approximately **27 days of candles for every timeframe** specifically to resolve that historical-coverage problem.

## Unverified work remaining

1. Compare original Viprasol's 15m, 30m, and 1h factors and signals **bar by bar** against independent source outputs, including exact VWAP and lower-timeframe `request.security` behavior.
2. Investigate the ATR discrepancy against matching source candles/settings rather than fitting parameters to one screenshot.
3. Confirm the production GitHub Actions tests and 15-minute data capture actually succeed (the available connector does not expose a general list of scheduled/push runs).
4. Measure true out-of-sample forward metrics with fees, slippage and uncertainty; retain the separate macro-OFF Classic, macro-ON Classic, and experimental Lab boundaries.

**No Discord live trade signals, wallet trading, or profitability claim is authorized by this document.**
