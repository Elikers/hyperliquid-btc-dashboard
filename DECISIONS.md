# DECISIONS — Stable project constraints

This is a standing technical decision log for the Hyperliquid BTC project. Changes to strategy, trading, account access, or spending require explicit user authorization. Research-only implementation fixes and tests may proceed autonomously, provided they preserve these boundaries.

| ID | Decision | Rationale / consequence |
| --- | --- | --- |
| D-001 | Keep a working static public Hyperliquid BTC dashboard at https://elikers.github.io/hyperliquid-btc-dashboard/ | User confirmed chart and price display; do not destabilize it for research changes. |
| D-002 | Use **Viprasol Classic** as an unchanged source baseline, including any explicitly selected original Pine settings. | Prevent experiments from silently rewriting the original indicator. |
| D-003 | Prioritize original-source-supported `macroFactorOnInput=false` **Classic Macro-Off** for seven-factor research. | This configuration legitimately avoids requiring licensed NQ1! futures data; it is not yet parity verified. |
| D-004 | Preserve original eight-factor **Macro-On** separately; never silently replace `CME_MINI:NQ1!` with Yahoo `NQ=F` or another proxy. | Contract rolls, market closures, session and vendor differences invalidate an exact-equivalence claim. |
| D-005 | Keep BTC-only Lab alternatives separate and explicitly experimental. | Don't promote Lab performance or changed risk settings as original Classic. |
| D-006 | Do not activate live Discord trade signals or wallet trading until separately verified, reviewed and explicitly approved. | Current source/parity/profitability evidence is insufficient. The existing public repo must contain no secrets. |
| D-007 | Data capture is read-only and research-only. Collect closed 15m/30m/1h candles, reject incomplete/misaligned data, and keep cross-timeframe checks. | Avoid repainting, look-ahead, inconsistent time cutoffs and invalid score reports. |
| D-008 | Run research via GitHub Actions; the 15-minute capture cron is `:02,:17,:32,:47 UTC` and ChatGPT QA is hourly. | GitHub Actions cron is best-effort, not a continuous execution or guaranteed delivery service. |
| D-009 | Require independently sourced Pine parity before calling signals accurate; require realistic net-forward research before claiming profit. | Backtests can overfit, simple fee assumptions and one event cannot prove profitability. |
| D-010 | Prefer no-cost resources and minimal user manual steps. Ask the user only for genuine authorization, purchases, missing rights, or hard blockers. | The user explicitly wants less context loss, fewer downloads and less repetitive approval. |
| D-011 | Keep one durable project memory in GitHub rather than relying on a single enormous ChatGPT thread. | New chats should start from `PROJECT_STATE.md`, `DECISIONS.md`, `HANDOFF.md` plus live repo/CI evidence. |
| D-012 | Keep permanent records concise and honest: separate **implemented**, **CI-verified**, **forward-observed**, **unverified**, and **proposed**. | Avoid repeated false completion claims. |

### Source preservation
The original Viprasol Pine implementation belongs to its copyright owner; do not casually republish it in this public GitHub repository. Default relevant settings presently tracked: EMA 9/21 cross, Macro-Off 5/7 score, ADR14 and trading session/weekend filters, ATR14×1.5 stop, targets at 1R/2R/3R. Reconfirm exact signal conditions against the original source before making parity claims.

### Scope and personal authorization
Autonomous work includes safe code hygiene, tests, non-sensitive public market data analysis, GitHub research workflows and documenting evidence. It excludes purchases, paid data subscriptions, changing trading permissions, using API keys/secrets, wallet execution, and activating real trade-alert systems. Preserve source code licensing and users' data privacy.

### Updating this log
Append a new numbered decision with date, what changed, and approval evidence whenever a stable project boundary changes. Do not rewrite history without a clear revision note.

### D-013 — Redundant scheduled-capture research pilot (2026-11-22)

For the next 24h+ observation window, test **two best-effort GitHub Actions schedule opportunities after each 15m candle boundary** at minutes `7,12,22,27,37,42,52,57` UTC. This supersedes D-008's earlier four-slot cron for the **research-only pilot**, not D-008's prohibition on treating Actions as always-on service. Monitor actual scheduled executions, unique forward candle coverage, costs/artifact volumes and API reliability, and revert if regressions are observed. Zero changes to strategy rules, risk, TradingView parity claims, Discord or wallet trading. See [pilot gates](research/REDUNDANT_CAPTURE_PILOT.md).
