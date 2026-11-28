# Original Viprasol Pine v6 source-to-research parity matrix — 2026-11-28

## Provenance and scope

The user-supplied original Pine v6 source was recovered from the private ChatGPT Library copy named `Pasted text(20261120-173911).txt`. Its original bytes were materialized for this audit and SHA-256 verified:

- Size: 64,246 bytes
- SHA-256: `00d41c3abfccb3747506185bf0515684b5d8cdaa4b85c4546384914e623f34de`
- Pine version: v6
- Indicator: `[Viprasol] Bitcoin Sniper Confluence`
- The source declares an `indicator()`, not a broker-executing strategy. Its chart trade tracker is a visual hypothetical tracker, not exchange fills.

The source file itself is not copied into this repository. This document records only settings, formula references and verification gaps. Source identity is revalidated; calculated parity is not.

## Exact Macro-Off input selection

The Pine source defaults `macroFactorOnInput=true`. The requested Classic Macro-Off configuration explicitly overrides that input to `false`; it is not the unmodified source default.

| Setting | Original Pine input / behavior | Macro-Off selection |
|---|---|---|
| Fast / slow EMA | 9 / 21 | 9 / 21 |
| Entry trigger | `ta.crossover` / `ta.crossunder`, bar-close confirmation on | Closed-bar cross only |
| Confluence gate | Enabled; minimum score input 5 | 5 of 7 |
| Macro factor | Source default ON; `factorTotal=8` when on | OFF; `factorTotal=7`, `minScoreEff=min(5,7)=5` |
| Technical factors | VWAP, RSI, MACD, EMA, ADX, volume, confirmation-timeframe RSI | All seven retained |
| Confirmation RSI | RSI(14), default confirmation timeframe 15m, `lookahead_off` | 15m RSI(14) |
| Session filter | Enabled; Europe 03:00–12:00 and US 08:00–17:00, America/New_York | Enabled |
| Weekend filter | Enabled | Enabled |
| ADR exhaustion | Enabled; 14 completed daily ranges; block at 100% used | ADR14, 100% threshold |
| Stop | ATR(14) × 1.5 | ATR14 × 1.5 |
| Targets | Three levels at 1R / 2R / 3R | 1R / 2R / 3R |
| Breakeven | Move working stop to entry after TP1 | Enabled |

Pine source locations:
- Inputs: EMA/confluence lines 44–56; macro lines 64–76; session/weekend lines 78–90; ADR lines 92–98; risk lines 100–110; confirmation timeframe lines 112–114.
- Core indicators: lines 208–216.
- Seven technical factor definitions and scores: lines 255–280.
- Session and weekend gates: lines 293–301.
- Completed-day ADR and current-day range: lines 304–324.
- Signal-bar-close entry and visual ladder: lines 350–359 and 468–495.
- Visual trade tracker: lines 378–399; it skips the entry candle, checks stop before targets, and moves the stop to breakeven after TP1.

The macro symbol default is `CME_MINI:NQ1!`, but it is not required in Macro-Off. Macro-On eight-factor research remains a separate configuration and is not altered by this matrix.

## Python implementation mapping

| Pine behavior | Current research implementation | Status |
|---|---|---|
| EMA9/21 closed-bar crossover | `classic_macro_off.py`, `classic_decision.py`, `factors.py` | Source mapping reviewed; independent event parity unverified |
| Seven factor votes and 5/7 threshold | `compute_seven_factors()`; `Context(macro_factor_enabled=False,min_score=5)` | Definitions mapped; bar-by-bar values unverified |
| VWAP of HLC3 | `vwap_utc_day()` using volume-weighted HLC3 and UTC-day reset | Approximation only; TradingView anchor/exchange timezone not certified |
| RSI14, MACD(12,26,9), DMI/ADX(14,14), volume SMA20 | `factors.py` | Formula families mapped; initialization and exact Pine series values unverified |
| 15m RSI14 confirmation | `compute_seven_factors()` selects the last closed 15m bar not later than the chart-bar close | Historical lower-timeframe `request.security(..., lookahead_off)` merge semantics not independently checked |
| Europe/US and weekend gates | `classic_decision.py`, America/New_York | Session windows and weekday rules mapped; no complete independent event export |
| ADR14 | `adr_gate.py` groups complete UTC days and averages the prior 14 daily ranges | Deliberately fail-closed deviation when history is unavailable; see below |
| ATR14 and risk ladder | `risk_ladder.py` uses Wilder RMA, 1.5× risk and 1R/2R/3R levels | Formula mapping reviewed; known numeric mismatch remains |
| Prospective outcome ledger | `forward_paper_ledger.py` | Separate causal first-open-after-observation model, not the Pine signal-close visual tracker |

## Explicit differences and unresolved checks

1. **VWAP anchor:** Python resets at UTC midnight. Pine calls `ta.vwap(hlc3)` without an explicit anchor. Exact exchange/chart daily-boundary equivalence has not been independently proven.
2. **Lower-timeframe confirmation:** Pine requests 15m RSI through `request.security` with `lookahead_off`. The Python engine chooses the latest completed 15m candle at or before the 30m/1h close. This is plausible for closed bars but is not a verified reproduction of Pine's historical and realtime merge behavior.
3. **ADX / ATR initialization:** Python uses explicit Wilder RMA implementations. The original source uses `ta.dmi(14,14)` and `ta.atr(14)`. No complete TradingView indicator-value export exists to verify every warmup and first-valid value.
4. **ADR unavailable behavior:** Pine's `adrExhausted` is false when ADR is `na`, so the source does not block solely because ADR is unavailable. Python intentionally rejects a candidate with `ADR_INPUT_NOT_VERIFIED` unless it has 14 complete prior UTC days. This is a safety deviation, not exact parity.
5. **Daily boundary:** Python uses UTC-day grouping. Pine uses the symbol's daily request and chart `time("D")`. The Hyperliquid symbol's exact TradingView daily-session alignment has not been independently compared.
6. **ATR discrepancy:** The saved 15m screenshot reference at 2026-11-20 14:30 UTC has matching OHLC, entry and LONG direction, but the screenshot stop is 61,667.1 versus Python 61,667.3978 (difference +0.2978 USDC); TP1/TP2/TP3 also differ. Prior warmup sensitivity showed ordinary long-history ATR seeding does not explain this. Do not fit the multiplier or period to this one event.
7. **Entry/exit model:** Pine's visual tracker enters at the signal-bar close and skips that candle for exit checks. The prospective ledger instead waits until a capture has actually observed the close, excludes already-opened bars, and enters at the first subsequent bar open. This is intentionally a separate causal paper-execution model, not Pine parity. The historical replay now keeps signal-close baseline and next-open sensitivity separate.

## Evidence currently available

- One saved 15m screenshot comparison exists for the 2026-11-20 14:15–14:30 UTC bar. OHLC and entry price (62,077.0) match; the BUY marker time/direction line up. Stop/target values do not match exactly.
- No independent, contiguous TradingView original-Pine exports were found for all 15m, 30m and 1h bars, including zero-signal bars, factor booleans, scores, crossover events, session/ADR gates, ATR and risk levels.
- The parity gate requires at least 100 contiguous rows per timeframe and compares both positive and negative events. A single screenshot or a candidate-only list cannot prove absence of extra/missing signals.

## Next verification steps

1. Obtain independent original-Pine closed-bar exports for 15m, 30m and 1h with timestamps, all seven bull/bear factor booleans, raw crossover, final direction, gate reasons, ADR, ATR and entry/SL/TP1/TP2/TP3. Include zero-signal bars and enough warmup / completed daily history.
2. Compare every exported bar and event in both directions using the existing parity gate; reject missing, extra, duplicated or misaligned rows.
3. Investigate VWAP and daily-session boundaries, lower-timeframe RSI merge behavior, DMI/ATR initialization and the existing ATR discrepancy across multiple independent events before any code change.
4. Keep any deliberate safety divergence (especially missing-ADR fail-closed behavior) explicitly labeled rather than silently changing source semantics.
5. Preserve separate Macro-On eight-factor and experimental Lab paths. Do not alter source settings, dashboard/Pages, live alerts or trading permissions to make a comparison pass.

**Status:** Original source identity and requested Macro-Off input mapping are now verified. Full numerical Pine parity, forward profitability and execution quality remain unverified. No paid feed, secret, Discord trade alert, wallet order or automatic trading is used or authorized.


## Fresh raw-candle ATR recheck — 2026-11-28 16:50 UTC

- Re-materialized the original Library Pine v6 file `Pasted text(20261120-173911).txt`: 64,246 bytes, SHA-256 `00d41c3abfccb3747506185bf0515684b5d8cdaa4b85c4546384914e623f34de`. Relevant source lines were rechecked: EMA/score inputs 45–56; macro OFF override 65–76; sessions/weekend 79–90; ADR14 92–98; ATR/risk 101–108; confirmation RSI 112–114; core indicators 208–216; factor votes 257–280; session/ADR logic 293–324; crossover and entry 468–495.
- The current scheduled raw artifact [#46165868476](https://github.com/Elikers/hyperliquid-btc-dashboard/actions/runs/46165868476) contains the 2026-11-20 14:15–14:30 UTC 15m candle with OHLC 61,893 / 62,150 / 61,837 / 62,077, matching the saved screenshot note. Recomputed Python Wilder ATR14 from that historical candle and the full available raw series is 273.068130152965; 1.5× risk is 409.602195229447. The screenshot stop 61,667.1 implies about 409.9 risk, retaining the +0.2978 USDC difference. Starting the RMA history 0, 1, 10, 50, 100, 200, 500 or 1,000 earlier bars before the target yields the same ATR to displayed precision; simple warmup-length truncation does not explain the mismatch.
- A fresh Library search found the existing 15m comparison note only; no independent 30m/1h reference exports or contiguous zero-signal-inclusive per-bar factor exports were found. This remains a genuine evidence blocker. Do not tune ATR or claim parity from one 15m screenshot.
- No strategy code or settings changed. Macro-Off remains EMA9/21, seven factors with 5/7, ADR14, ATR14×1.5 and 1R/2R/3R; Macro-On eight-factor and Lab remain separate. Numerical Pine parity and profitability remain unverified.
