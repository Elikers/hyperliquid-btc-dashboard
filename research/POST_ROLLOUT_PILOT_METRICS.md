# Post-rollout capture pilot: clean evidence window

The redundant cron was merged and first push-smoked on **2026-11-21 at 23:04:46 UTC**. A conservative clean evaluation window begins **2026-11-21 23:15:00 UTC**. Do not divide the first rolling 24-hour historical schedule count by the new 192-opportunity daily target; doing so improperly mixes the earlier 4/hour and current 8/hour configurations.

`postRolloutPilot` is embedded in the existing read-only BTC daily paper audit output. It separately counts *actual successful main-branch `event=schedule` runs*, and unique **forward closed bars actually captured inside those same run artifacts**. Push/manual workflows are deliberately excluded even if the actual candle is valid. Repeated candle closes count once; absent compact evidence for a successful scheduled job is reported rather than treated as observed. This is intentionally separate from historical-only archived bars and the overall paper ledger.

`fullPostRolloutWindowAvailable` remains false until **2026-11-22 23:15:00 UTC** (November 23 at 07:15 Asia/Manila), and even afterwards marks the pilot only `READY_FOR_MANUAL_EVIDENCE_REVIEW`, not a reliability pass. At least one full clean observation window and measured market-data/capture evidence are necessary before comparing. GitHub Actions may delay or drop scheduled triggers.

No changes to Viprasol Classic factors/thresholds/ATR/Entry/SL/TP, the Pages dashboard, Discord, wallet trading or profit authorization.

After the first complete day, the metric uses a **rolling 24-hour UTC window** beginning at `max(clean_pilot_start, report_time - 24h)`. This avoids penalizing later reports for archived observations outside the rolling collection horizon. Reports remain ineligible for any automatic reliability approval; schedule delay and skipped triggers are still possible.
