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

## Eight-factor research audit and risk ladder

- [`macro_factor.py`](macro_factor.py): rolling 20-bar Pearson BTC/NQ correlation, Nasdaq EMA direction, positive/inverse link and +/−0.3 threshold; insufficient or unverified macro feeds cannot count as confirmed votes.
- [`risk_ladder.py`](risk_ladder.py): Pine-style ATR14 × 1.5 stop and 1R/2R/3R targets; future OHLC stop-before-target outcome audit and TP1 breakeven.
- [`eight_factor_audit.py`](eight_factor_audit.py): combines seven calculations, eighth factor, original crossover/session/ADR gates and risk levels on already closed BTC/NQ bars, rejecting missing/misaligned NQ candles.
- [`test_macro_factor.py`](test_macro_factor.py), [`test_risk_ladder.py`](test_risk_ladder.py), [`test_eight_factor_audit.py`](test_eight_factor_audit.py): local/no-network unit tests, automatically picked up by the existing GitHub research safety workflow.
- [`capture_public_btc.py`](capture_public_btc.py): offline-testable official Hyperliquid public candle snapshot retrieval.
- [`BTC forward capture`](../.github/workflows/btc-forward-capture.yml): scheduled hourly snapshot attempt, with seven-day GitHub Actions artifacts. This workflow does **not** provide 24/7 streaming data, exact NQ1! input, TradingView parity, Discord alerts or trading.

### Why alerts are still OFF

Original Pine calculates the NQ1! EMA inside `request.security` on the futures instrument before merging it onto BTC candles. A clean, aligned set of arbitrary BTC/NQ candles is *not* necessarily the same as TradingView's macro series, and a verified license alone does not prove equivalent roll sessions. VWAP session anchoring and 15m `request.security` merging also require exchange-matched parity checks. All audit functions hardcode `discordEligible=False` and `originalViprasolVerified=False`, regardless of test scores.

## Native NQ1! session-gap alignment (new)

- [`futures_alignment.py`](futures_alignment.py) uses only futures bars already closed before a BTC bar; computes the NQ EMA **before** forward joining onto 24/7 BTC candles; rejects duplicated/invalid exchange bars and marks stale CME observations unavailable. In particular, it doesn't treat a Saturday/Sunday market closure as corrupt futures history.
- [`native_macro_audit.py`](native_macro_audit.py) connects that join to the existing seven-factor calculations, Pearson macro vote, entry gates and ATR ladder. Synthetic regression tests are in [`test_futures_alignment.py`](test_futures_alignment.py) and [`test_native_macro_audit.py`](test_native_macro_audit.py).
- These functions are still *research only* and cannot emit Discord signals. A naive daily/UTC alignment or an EMA calculated on forward-filled CME bars is **not** a Pine-equivalent implementation.

**Official-source research (2026-11-21):** [Hyperliquid documents a 5000 recent-candle limit](https://hyperliquid.gitbook.io/Hyperliquid-docs/for-developers/api/info-endpoint). [CME Group lists licensed real-time/historical data services](https://www.cmegroup.com/market-data/market-data-api.html), plus [licensed distributors](https://www.cmegroup.com/market-data/license-data/licensed-market-data-distributors.html). Public delayed CME **quotes** alone do not provide a verified, continuous, timestamp-aligned historical `CME_MINI:NQ1!` feed. We will not scrape protected quotes or replace CME data with `NQ=F` silently.

### Verification evidence still missing

1. A rights-compliant source for native NQ futures OHLC bars, exact symbol/roll policy, and evidence of access terms;
2. Replay proof that Pine `request.security` session/time-merge and `ta.vwap` match our implementation;
3. Exact bar-by-bar factors, both missed and extra LONG/SHORT signals, and ATR/TP levels on independent datasets;
4. Forward evidence after costs and feed outages. **No live trading or Discord trade-alert activation.**

## Parallel BTC-only Lab research — not a substitute for Classic

A separately labeled [BTC-only 7-factor Lab](btc_only_lab.py) now computes hypothetical research candidates without NQ1!. It does **not** inherit Classic's eight-factor parity claim; the ADR gate is deliberately disabled and disclosed in Lab until daily-input parity is verified. [Regression tests](test_btc_only_lab.py) assert that it never produces trade alerts.

The 15-minute scheduled [research evaluator](evaluate_public_snapshot.py) writes both blocked Classic observations and `btcOnlyLab` hypothetical observations into the same GitHub Actions JSON artifact. Results are forward samples for **research**, not validated entry recommendations. Fees, execution slippage and risk-adjusted profitability remain unproven. All wallet actions and webhook sending are absent.

## New practical route: original Viprasol Classic, Nasdaq factor OFF

The *original supplied Pine v6* includes `macroFactorOnInput = input.bool(true, ...)`, sets `factorTotal = macroFactorOnInput ? 8 : 7`, and uses `minScoreEff = min(minScoreInput, factorTotal)`. Therefore the user's baseline **already supports disabling the macro factor**, without needing a paid NQ1! feed. This is not an invented replacement strategy.

[`classic_macro_off.py`](classic_macro_off.py) implements the **source-supported 7-factor Classic configuration**, including EMA crossovers, Europe/US sessions, weekend restrictions, and the [14 completed UTC-day ADR gate](adr_gate.py). [Its tests](test_classic_macro_off.py) assert Nasdaq is not required, ADR history is checked, unfinished candles are ignored, and alerts stay disabled. The separate BTC-only Lab does not currently enforce ADR and must not be conflated with this Classic configuration.

The scheduled research artifact now contains three explicitly distinguished outputs:
- `timeframes`: prior seven-factor diagnostic blocked by unverified NQ1!;
- `viprasolClassicMacroOff`: original source's supported **macro OFF** configuration, research-only;
- `btcOnlyLab`: separately experimental BTC-only model with ADR disabled.

**Path to operational signals:** Validate VWAP session anchoring, 15m confirmation merge, EMA/RSI/MACD/ADX and ATR against the source and independent reference events; test net results after fees/slippage; only then consider enabling notification delivery. Even Macro-Off Classic is not yet parity-verified or proven profitable. The original Macro-On eight-factor version stays intact and blocked pending actual NQ1! data.
