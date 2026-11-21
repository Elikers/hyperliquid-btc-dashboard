# Conservative historical candidate replay — 2026-11-21

**STATUS: RESEARCH ONLY. NOT A VALIDATED VIPRASOL STRATEGY.**

This study replayed 35 **previously exported seven-factor Python candidates**, not independently confirmed TradingView Viprasol Classic signals, through the later fully closed Hyperliquid OHLC candles in the user's existing local research package `Hyperliquid_BTC_GitHub_Ready/research`. No real orders were placed.

## Provenance

- Input `reference_7factor_candidates.csv`: 35 candidate rows; SHA-256 `07675581e5a1cec38716964b9a94e1d6e99426fc359ef94c4c529116ecd12a69`
- Input `reference_btc_candles.csv`: 3,612 OHLC rows (1,204 per timeframe); SHA-256 `56792fe1b7036dc7f497e47d7ec7df7c814218df4accdeab60cf1161d6b20293`
- All three 15m/30m/1h candle series were contiguous and each exported candidate's signal bar was present. Actual raw input CSVs are held in the earlier local project package, **not published in this GitHub repo**. This summary therefore does not constitute independently reproducible public evidence until inputs are published with appropriate rights.
- Research replay implementation: [`replay_reference_candidates.py`](replay_reference_candidates.py); [automated tests](test_replay_reference_candidates.py).

## Outcomes (entire hypothetical position until final TP3/stop/BE)

| Timeframe | Candidates | SL | BE after TP1 | TP3 | Gross R sum | Hypothetical net R sum* |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 15m | 18 | 8 | 7 | 3 | +1.0 | -3.2344 |
| 30m | 10 | 7 | 2 | 1 | -4.0 | -5.7475 |
| 1h | 7 | 5 | 0 | 2 | +1.0 | +0.1928 |
| **All** | **35** | **20** | **9** | **6** | **-2.0** | **-8.7890** |

*Illustrative net = gross R minus a hypothetical **7 basis points per side**, i.e. 14 bps round trip for combined execution drag. NOT a quoted Hyperliquid fee or an empirical slippage estimate. Different position risks lead to different fees in R, so net sums are illustrative, not account-equity returns.*

## Conservative rules and limitations

- Only candles **after** the signal candle can resolve a trade.
- If a stop and target are touched in one candle, stop wins.
- After TP1 is touched, the working stop advances to entry on subsequent candles.
- This model assumes the **entire hypothetical position** exits at TP3/SL/BE. TP1/TP2 are recorded milestones, not partial-exit fills.
- Candidate trades can overlap; summing R across them **is not** a portfolio backtest, margin model, or drawdown estimate.
- All 35 candidates reached a stop, breakeven, or TP3 within the supplied time span; no open observations were counted in the table.
- Exact Pine source calculation parity, full event-selection parity, execution fees, and out-of-sample generalizability are **not established**.

**Interpretation:** This small existing candidate dataset offers *no basis to claim profitability*. The appropriate follow-up is to correct signal calculation differences and run clean, independent forward and out-of-sample tests, not activate live Discord alerts. Original Macro-On Classic and source-supported Macro-Off Classic remain separate from this exported research-candidate series.
