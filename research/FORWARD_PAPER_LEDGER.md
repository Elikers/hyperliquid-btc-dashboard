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
- Only candles after entry-close can settle a hypothetical trade, with intrabar stop-first, TP1-to-future-breakeven and full-notional TP3 rules. These rules match the separate conservative [research replay convention](replay_reference_candidates.py), not confirmed exchange execution.
- Cost hypothesis is an *illustrative* one-way number of basis points applied to entry plus exit notional. It is **not** a live fee quote or proven slippage. It excludes partial fills, market impact, funding, margin and portfolio overlap.

Interpretation: all output `originalViprasolVerified=false`, `discordEligible=false`, `automaticTrading=false`, and `profitableStrategyVerified=false`. No historical 30-day sample exists until enough **actual repeated runs** have occurred. A single push-triggered smoke capture does not establish recurring scheduled capture.

Implementation intentionally does **not** expose a dashboard button, send Discord messages, change trading rules, upload trading credentials, or claim profitable performance. This is only the offline scoring foundation, with tests covering deduplication, contradictory observations, gaps, ATR-style stop-first conventions and disabled alerts.

Next integration task is a read-only GitHub Actions artifact discovery/replay/report workflow with a persistent, sufficiently complete historical sample; do not overwrite original raw evidence or invent missing bars.
