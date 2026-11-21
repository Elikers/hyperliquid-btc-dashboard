# Viprasol Classic verification — research only

The public Pages chart is working, but the eight-factor Viprasol indicator is **not certified**. Nothing in this directory sends Discord messages or opens positions.

## Original-source audit notes

From the user-supplied Viprasol Pine Script v6 (MPL 2.0, copyright Viprasol):

| Behavior | Baseline | Validation concern |
|---|---|---|
| Trigger | 9/21 EMA crossover on the bar close | A bullish score by itself is not a trade |
| Confluence | Minimum 5/8 | Seven BTC technical factors and one macro factor |
| Macro | CME_MINI:NQ1!; 21 EMA; 20-bar rolling correlation; minimum +0.3 | A continuous futures symbol is not interchangeable with Yahoo NQ=F |
| Momentum | RSI 14, MACD 12/26/9, ADX 14 | Pine warm-up/seed and higher-timeframe alignment matter |
| Confirmation | 15-minute RSI14 via request.security | 30m/1h behavior requires Pine-aligned bar merging |
| Volume | Bar volume > SMA20, bullish/bearish candle direction | No substitutions without disclosure |
| VWAP | ta.vwap(hlc3) | Must match Pine session anchoring |
| Time gate | Europe 03:00–12:00 / US 08:00–17:00, America/New_York, weekend block | DST and session bar boundaries matter |
| ADR gate | Prior 14 daily high-low ranges; blocks at >= 100% used | In Pine, unavailable ADR is not automatically a block |
| Risk | 1.5 × ATR14 SL; 1R, 2R, 3R targets | Intra-candle stop-first and TP1 breakeven behavior needs verification |

## Audit gates

The standard-library `parity_checks.py` rejects missing/gapped/invalid candle inputs, non-NQ1 proxy data, and any unsupported macro provenance. Its event comparator compares the *entire reference set*, not just matched events, and checks exact close times and entry/stop/targets.

**Important:** a synthetically clean macro sample or a 100% sample event match is not proof of source equivalence. `originalViprasolVerified` is always `false`; no test can enable a webhook. There is no automated trading-alert worker in this repository.

## Automated CI

[Verify research safety](../.github/workflows/research-checks.yml) runs Python standard-library unit tests with no API keys, trading accounts, or exchange data. The workflow does not connect to Discord.

## Remaining independent verification

1. Obtain legally accessible CME_MINI:NQ1! history with roll/session construction comparable to TradingView; CME data may require licensed access. Do not scrape subscriber-only feeds.
2. Verify exact Pine-equivalent BTC candles, TA calculations and 15m/30m/1h `request.security` bar merges.
3. Import independent, dated reference signals and compare both false negatives and false positives, then SL/TP levels.
4. Build a separately hosted *read-only research monitor* first. A live alert worker would be a separately reviewed decision; it remains off here.

## Classic decision gate (new)

[`classic_decision.py`](classic_decision.py) implements the **closed-bar EMA9/21 crossover decision**, seven technical-factor booleans plus optional eighth macro boolean, the 5/8 score gate, America/New_York EU/US session hours, weekend block and ADR exhaustion. It returns the reason when a prospective entry is blocked. Tests cover false entries on existing trends, wrong sessions, weekend, invalid macro provenance, and ADR.

**Scope:** It evaluates *already computed* factors, not Pine-equivalent factor calculations or an authenticated macro data feed. `discordEligible` is always `false`. The website and Discord settings are unchanged.

## Seven-factor calculation module

[`factors.py`](factors.py) now calculates research-side EMA9/21, RSI14, MACD12/26/9, DMI/ADX14, 20-bar volume mean, intraday UTC-day VWAP approximation, and last-confirmed 15m RSI for 15m/30m/1h. It returns the seven bullish and bearish factor booleans and scores plus crossover inputs for the existing [Classic decision gate](classic_decision.py). The [unit tests](test_factors.py) cover indicator initialization, future/stale confirmation rejection, invalid candles, and explicit disabled-Discord status.

**Not yet done:** validate against TradingView exact OHLC/volume, VWAP session anchoring, multi-timeframe bar merge; acquire exact `CME_MINI:NQ1!` macro candles; verify factor-by-factor and entry/SL/TP parity. The new module intentionally is **not a live signal engine or automatic alert connector**.
