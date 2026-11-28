# Research forward-paper ledger

The [ledger](forward_paper_ledger.py) consumes **extracted** `forward_observation.json` files from GitHub Actions `btc-paper-evidence-*` artifacts, retained up to 30 days. The prior step [forward_observation.py](forward_observation.py) produces a compact, research-only record from each successful capture.

Run locally (after extracting the evidence JSONs):

```bash
python -m research.forward_paper_ledger records/*.json --one-way-cost-bps 7 --out paper_report.json
```

Input validations:
- Requires SHA-256 record digest, correct model identity, disabled alerts and trading, aligned closed bars, positive OHLCV and valid hypothetical risk ladder.
- Deduplicates by **(timeframe, closedBarEndMs)**, rejecting contradictory duplicates rather than picking a convenient price or signal. First valid observation supplies the observation timestamp.
- Detects missing timeframe bars. A trade that spans even one missing candle becomes **DATA_GAP** and never receives an estimated outcome.
- The signal is first observed only after its candle has closed. Every later observed candle whose **open time precedes the first observation timestamp is excluded**; entry waits for the first subsequent observed candle open at or after that timestamp. If none exists, the record is `AWAITING_CAUSAL_ENTRY`, not an open or resolved trade.
- The signal-time ATR14 × 1.5 risk distance is preserved, while the 1R/2R/3R ladder is re-anchored around that first causally executable open. From entry onward, a missing candle quarantines the outcome as `DATA_GAP`; stop-first intrabar handling and adverse stop-gap open pricing are used. This is an explicit execution sensitivity, not a change to the Classic signal rules or proof of Pine execution parity.
- The default 7 bps is an *illustrative one-way cost per side* applied to entry plus exit notional. It is **not** a live fee quote or measured slippage. It excludes partial fills, market impact, funding, margin and portfolio overlap.

Interpretation: all output `originalViprasolVerified=false`, `discordEligible=false`, `automaticTrading=false`, and `profitableStrategyVerified=false`. No historical 30-day sample exists until enough **actual repeated runs** have occurred. A single push-triggered smoke capture does not establish recurring scheduled capture.

Implementation intentionally does **not** expose a dashboard button, send Discord messages, change trading rules, upload trading credentials, or claim profitable performance. This is only the offline scoring foundation, with tests covering deduplication, contradictory observations, gaps, ATR-style stop-first conventions and disabled alerts.

Next verification gate is an independently authenticated original TradingView Pine closed-bar export for 15m/30m/1h. Keep prospective execution evidence separate from historical replay; do not overwrite raw evidence or invent missing bars.
