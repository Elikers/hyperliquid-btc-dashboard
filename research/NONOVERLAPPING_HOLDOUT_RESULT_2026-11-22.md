# Strict non-overlapping BTC holdout: verified result (2026-11-22)

## Provenance and integrity
- Independent pre-existing earlier market window: **2026-10-25 00:00:00 UTC exclusive** fixed before test run, before the previous baseline snapshot's market-data window. Actual closed BTC OHLCV fetched from the **Hyperliquid official public candleSnapshot API**, historical-only after the fact.
- Source bars required in each timeframe: **15m 2,200, 30m 1,100, 1h 550**, each contiguous and ending **2026-10-24 23:59:59.999 UTC**. The source returned 2,319/2,600 when the longer first attempt ran; [run #44965372590](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44965372590) correctly recorded NOT_AVAILABLE with no fabricated metrics.
- Shorter follow-up implemented in [PR #17](https://github.com/Elikers/hyperliquid-btc-dashboard/pull/17) with research-only per-call 500-bar minimum; original 650-bar default, indicator settings, CHOP(14)<=61.8 cutoff and fees unchanged.
- [PR #17 safety CI #44965456667](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44965456667) passed. Successful main holdout [run #44965488058](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44965488058) executed **275 tests**, retrieved full earlier source window, completed the paper replay, and uploaded artifact **14731357577**.
- **Downloaded and opened actual `holdout_research.json`** and matched its ZIP SHA-256 to official GitHub artifact digest **7130cfd1dae6f41dee62234f42d9d74a5aaa09e7aea29fef3ace7d8f5980ef3b**. Status `COMPLETED_HISTORICAL_ONLY`, all safety flags false.
- Separate unchanged baseline historical+forward workflow on main [#44965488051](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44965488051) also completed successfully; independent capture audit is a different evidence type.

## Results: untouched earlier market period, fixed rules

All 10 sampled Python Classic Macro-Off candidate trades were retained by the CHOP gate. **No indicator filtering advantage was observed.** Net R is a per-hypothetical-trade unit, not account equity and not certified Pine parity. Fee/slippage sensitivity is illustrative **one-way cost** of 0/7/15 bps applied to entry and exit.

| Frame | Resolved Classic / Hybrid | Filter skipped | Classic and Hybrid net R 0bps | 7bps | 15bps |
| --- | ---: | ---: | ---: | ---: | ---: |
| 15m | 7 / 7 | 0 | +5.0000R | +2.4078R | **-0.5547R** |
| 30m | 2 / 2 | 0 | +2.0000R | +1.5024R | +0.9338R |
| 1h | 1 / 1 | 0 | +0.0000R | -0.1824R | -0.3910R |

### Evidence-based conclusion
1. Apparent prior in-sample improvement from excluding **3 older losses** at 30m/1h did **not** reproduce on this non-overlapping period: the gate excluded **zero** trades. That is not evidence of reliable or profitable filtering.
2. A BTC 15m result that looks positive at assumed 7bps switches **negative at 15bps**, revealing execution-cost sensitivity. Ten trades with overlapping price exposure cannot substantiate profitable net expectancy or tradable account PnL.
3. Earlier periods were obtained *after the fact*. This is a strict historical non-overlap holdout, **not actual forward trading**. The original TradingView Viprasol Pine output/ATR parity remains unverified; direct trades cannot be authenticated as the original indicator.
4. **Do not activate the CHOP filter for live signals or change its threshold to fit this result.** Keep Classic/dashboard, Discord alerts and automatic trading unchanged. Continue independently observing true forward paper evidence; seek new non-overlapping data without changing the frozen rules.

