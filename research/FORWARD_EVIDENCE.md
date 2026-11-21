# Longitudinal BTC paper evidence

The existing 15-minute GitHub Actions job captures 15m/30m/1h BTC candles and computes research-only Viprasol Classic Macro-Off, the experimental Lab, and the original eight-factor diagnostic. Prior to this feature, full candle artifacts expired after **2 days**, which was insufficient to collect a meaningful forward sample.

## New capture format

The optional [`forward_observation.py`](forward_observation.py) writes `capture-output/forward_observation.json` after the source checks and computation succeed. It contains:

- A single UTC capture timestamp and SHA-256 digest of the canonical record
- Latest fully closed 15m/30m/1h candle with exchange OHLCV, close timestamps and identity
- Source-supported **Macro-Off Classic** seven-factor scores, EMA crossover, gate reasons, ADR status, and any hypothetical Entry / SL / TP1–TP3 ladder
- Fixed `originalViprasolVerified:false`, `discordEligible:false`, `automaticTrading:false`

Its independent [unit tests](test_forward_observation.py) reject unverified/contradictory flags, mixed timestamp windows, wrong market, inconsistent close times, malformed prices or inappropriate ladders.

The scheduled workflow uploads a separate **small 30-day artifact per successful 15-minute run**; the much larger full candle artifacts stay at **2 days**. These artifacts remain in GitHub Actions; they are not added as repository commits, they do not contain API keys or webhook URLs, and they do not transmit messages.

**Critical interpretation:** 15-minute runs observe the *same 1-hour candle four times* and the same 30-minute candle twice. Any performance analysis must deduplicate each timeframe by `closedBarEndMs`, use the first after-close observation, resolve only on later bars, avoid same-bar look-ahead, and report skipped/missing capture windows. Passing tests or collecting 30 days is **not** proof of Pine parity, profitability or live readiness.

The workflow is best-effort and can be delayed or skipped. Preserve original Viprasol's settings: EMA9/21 cross, confluence5/7, ADR14, 1.5×ATR14 stops and 1R/2R/3R targets. Do not turn on Discord trade alerts or wallet trading automatically.
