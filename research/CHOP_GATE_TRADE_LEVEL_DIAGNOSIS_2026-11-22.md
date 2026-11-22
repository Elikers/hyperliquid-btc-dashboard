# Fixed CHOP gate: trade-level historical diagnostic (2026-11-22)

## Provenance
- Research source: uploaded GitHub Actions artifact `btc-backtest-forward-research-44964122779`, artifact **14730284722**, from [successful main run #44964122779](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/44964122779) at commit `dec16f8d368418b1722507ea1580ee118489ac60`.
- ZIP SHA-256 **verified** against GitHub's artifact digest: `1d6793ef067ff7de47bf6a281ccc4a3e54f4369f8947edbcc418c7638d92d018`. All 27 trade entries and each timeframe's retained/skipped Classic net-R arithmetic were independently re-summed and matched the saved report. ZIP was downloaded and its three JSON members **opened and parsed**: `historical_backtest.json`, `instant_paper_comparison.json`, `forward_audit.json`. The source historical snapshot run is `44963073368`. The comparison is Python Classic **approximation**, not independent original Viprasol Pine output.
- Costs are illustrative combined fee+slippage **7 bps per side**; net R is normalized per hypothetical entry, not portfolio PnL.
- Exact run artifact includes all 27 trade records, filter decisions, 0/7/15 bps sensitivities, and safety flags. This is **descriptive research on the same sampled dataset**, not untouched out-of-sample or live forward validation.

## Matched-trade comparison

| TF | Classic resolved / net sum at 7bps | CHOP(14) <= 61.8 retained / net sum | Skipped trades / skipped net sum | Verdict |
|---|---:|---:|---:|---|
| 15m | 13 / -3.073838R | 11 / -5.602752R | 2 / +2.528914R | Filter harmed results |
| 30m | 7 / -3.246308R | 6 / -2.005734R | 1 / -1.240574R | In-sample improvement only |
| 1h | 7 / +0.192830R | 5 / +2.459011R | 2 / -2.266181R | In-sample improvement only |

## All five excluded trades

| UTC closed candle end | TF | Direction | Outcome | CHOP at entry | Net R at 7bps |
|---|---|---|---|---:|---:|
| 2026-11-19 15:14:59.999 | 15m | SHORT | TP3 | 61.9739 | +2.741158 |
| 2026-11-20 08:44:59.999 | 15m | LONG | BE | 64.9764 | -0.212244 |
| 2026-11-11 14:29:59.999 | 30m | SHORT | SL | 62.1368 | -1.240574 |
| 2026-11-11 16:59:59.999 | 1h | LONG | SL | 64.9098 | -1.139695 |
| 2026-11-17 13:59:59.999 | 1h | LONG | SL | 63.4413 | -1.126486 |

The excluded 15m TP3 occurred at CHOP approximately 61.97, only 0.17 above the fixed threshold. This illustrates threshold sensitivity; **do not retune on this sample**.

## Diagnostic chronological trade halves

Split the **existing candidate list** for each timeframe at its chronological midpoint (not a separate unseen dataset; not a forward test). Differences are filter minus Classic at 7bps.

| TF | Earlier trades: Classic vs filter | Later trades: Classic vs filter |
|---|---|---|
| 15m | 6: -3.438R vs -3.438R (no difference) | 7: +0.364R vs -2.165R (filter worse ~2.529R) |
| 30m | 3: -3.556R vs -2.315R (filter less negative ~1.241R) | 4: +0.310R vs +0.310R (no difference) |
| 1h | 3: -3.361R vs -1.095R (filter less negative ~2.266R) | 4: +3.554R vs +3.554R (no difference) |

The 30m/1h apparent improvements are **not replicated as incremental benefits in later trades**: the later halves had no newly excluded candidates. Do not infer profitable robustness from this. Trade count is too small for robust inference and the price history overlaps between timeframes.

## Authentic forward evidence
The same report's forward audit had 19 distinct closed 15m observations, 18 distinct 30m and 14 distinct 1h; **zero hypothetical candidates and zero resolved forward trades**. Missing observations and insufficient forward trade evidence remain. The redundant-schedule pilot was only about 40 minutes into its designated 24h measurement; no reliability comparison is warranted.

## Decision and next safe test
**Do not promote or activate the CHOP filter on any timeframe.** The 15m evidence is adverse; 30m/1h evidence is only three excluded losses in a short sample. Keep one research candidate and the original Classic frozen. Obtain **new non-overlapping historic periods** or genuinely new captured future-market observations, run the **unchanged 61.8 cutoff**, compare entry/exit results and all 0/7/15 bps costs; obtain independent TradingView full-bar Pine parity. Data captured after the fact must be labeled historical, even if simulation advances one candle at a time. Discord trading alerts, wallets, and automatic trading stay OFF.
