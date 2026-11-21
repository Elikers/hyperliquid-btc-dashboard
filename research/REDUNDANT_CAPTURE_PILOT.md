# Redundant 15-minute BTC capture opportunity pilot (2026-11-22)

## Why this experiment exists
The prior research-only GitHub Actions cron at :02,:17,:32,:47 UTC provided four configured opportunities per hour, but observed successful scheduled run starts were often 41-63 minutes apart. GitHub's official documentation warns that scheduled workflows can be delayed or dropped entirely under load. A cron is **not** a continuous background server, and neither a passing manual/push smoke nor a configured schedule proves recurring execution.

## Change
The existing BTC public-market capture workflow has **one** cron expression:
`7,12,22,27,37,42,52,57 * * * *` UTC.
This offers **two chances (7 and 12 minutes after) for each of the four 15-minute UTC candle boundaries**, for up to eight scheduled opportunities per hour. It avoids the busiest hour start. A run still captures only what is actually closed at its real execution timestamp. There is no attempt to pretend a delayed job ran on schedule. The research ledger already deduplicates repeated timeframe + candle-close pairs. There are no additional secrets, external hosts, chart changes, or trading permissions. Public Hyperliquid API read volume, GitHub runner utilization and artifact volume may increase, with up to 192 configured opportunities/day (versus 96).

The 24-hour forward and historical audit source caps were raised to **250** artifacts. The historical audit now uses a **24-hour artifact-creation lookback** rather than 72 hours to keep its bounded downloads and memory use safe with potentially increased archive generation. Each historical source archive itself still contains its own trailing 24h OHLCV, and all history remains separate from forward observation records. Other retention durations remain unchanged.

## Gates and limitations
- This is a **controlled, reversible scheduling experiment**, not proof that GitHub will actually run twice every 15 minutes. Compare real `event=schedule` run creation times and **distinct 15m/30m/1h closed bar end timestamps** over at least a clean full day after rollout.
- The GitHub-schedule volume metric projects the **current** cron over the entire rolling window. For its initial 24 hours spanning the rollout, the denominator is NOT a valid before-after reliability estimate. Use a fully post-rollout 24h observation window before comparing.
- Extra runs may repeat the same closed candle. Forward evidence deduplication must never invent missing signals. Historical-only archives may preserve missed candles for research, **not missed forward alerts**.
- GitHub workflow schedules can still be delayed, skipped or disabled with inactivity. No free GitHub-only configuration guarantees 15-minute wall-clock delivery. A dependable future always-on collector would require separate operational hosting, authorization and cost review.
- Stop/revert to four configured opportunities/hour if API failures, runtime/storage pressure or unexpectedly high Actions usage is observed.
- Viprasol Classic original thresholds unchanged. `discordEligible=false`, `automaticTrading=false`, `profitabilityClaimAllowed=false`.

Official documentation: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
