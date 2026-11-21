"""Evidence-only pilot assessment for the new 8-per-hour BTC capture cron.

Uses ONLY completed successful main-branch schedule runs and compact forward
observations from those same run IDs. Push/manual smoke runs never inflate the
pilot's schedule or candle coverage. Never invent missed run slots or signals.
"""
from datetime import datetime, timezone, timedelta

from research.observation_coverage import observation_coverage
from research.schedule_reliability import schedule_reliability

# Align after the Nov 21 23:04:46Z main deployment. The first complete
# candidate 15m bar after this baseline closes at 23:29:59.999Z.
PILOT_START_UTC = datetime(2026, 11, 21, 23, 15, tzinfo=timezone.utc)
MIN_DURATION = timedelta(hours=24)


def assess_pilot(records_with_runs, scheduled_runs, *, through):
    if not isinstance(through, datetime) or through.utcoffset() is None:
        raise ValueError("Timezone-aware pilot end required")
    through=through.astimezone(timezone.utc)
    if through <= PILOT_START_UTC:
        return {
            "kind": "BTC_RESEARCH_REDUNDANT_SCHEDULE_PILOT_V1",
            "startedUtc": PILOT_START_UTC.isoformat(),
            "elapsedMinutes": 0,
            "fullPostRolloutWindowAvailable": False,
            "outcome": "NOT_ENOUGH_ELAPSED_TIME",
            "researchOnly": True,
            "discordEligible": False,
            "automaticTrading": False,
            "profitabilityClaimAllowed": False,
        }
    run_ids = set()
    for run in scheduled_runs:
        if run.get("name")!="Capture BTC research candles" or run.get("event")!="schedule":
            continue
        if run.get("head_branch")!="main" or run.get("status")!="completed" or run.get("conclusion")!="success":
            continue
        dt=datetime.fromisoformat(str(run["created_at"]).replace("Z","+00:00"))
        if dt.utcoffset() is None:
            raise ValueError("Naive run creation time")
        if PILOT_START_UTC < dt <= through:
            run_ids.add(int(run["id"]))
    evidence = []
    source_run_ids=set()
    for item in records_with_runs:
        run_id=int(item["runId"])
        if run_id not in run_ids:
            continue
        rec=item["record"]
        captured=datetime.fromisoformat(str(rec["capturedAtUtc"]).replace("Z","+00:00"))
        if captured.utcoffset() is None:
            raise ValueError("Naive evidence capture time")
        if PILOT_START_UTC < captured <= through:
            evidence.append(rec)
            source_run_ids.add(run_id)
    coverage=observation_coverage(evidence,after=PILOT_START_UTC,through=through)
    schedule=schedule_reliability(scheduled_runs,after=PILOT_START_UTC,through=through)
    elapsed=through-PILOT_START_UTC
    ready=elapsed>=MIN_DURATION
    return {
        "kind": "BTC_RESEARCH_REDUNDANT_SCHEDULE_PILOT_V1",
        "startedUtc": PILOT_START_UTC.isoformat(),
        "evaluatedThroughUtc": through.isoformat(),
        "elapsedMinutes": int(elapsed.total_seconds()//60),
        "fullPostRolloutWindowAvailable": ready,
        "outcome": "READY_FOR_MANUAL_EVIDENCE_REVIEW" if ready else "INSUFFICIENT_POST_ROLLOUT_DURATION",
        "scheduledSuccessfulRunCount": len(run_ids),
        "scheduledRunsWithVerifiableForwardArtifacts": len(source_run_ids),
        "missingForwardEvidenceForSuccessfulRunCount": len(run_ids-source_run_ids),
        "postRolloutScheduledRunIds": sorted(run_ids),
        "closedBarCoverageFromScheduledRunsOnly": coverage,
        "scheduledRunCountAudit": schedule,
        "pushAndManualRunsExcluded": True,
        "cronCountNotExactMissedSlots": True,
        "doesNotClaimImprovedReliability": True,
        "originalViprasolVerified": False,
        "researchOnly": True,
        "discordEligible": False,
        "automaticTrading": False,
        "profitabilityClaimAllowed": False,
    }
