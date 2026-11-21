"""GitHub Actions schedule reliability audit, separate from BTC candle coverage.

GitHub exposes run creation time, NOT the intended cron firing time.
Never infer exact skipped slots or continuous market observation from these
counts. Do not change the trading engine, collect orders, or send alerts.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone

EXPECTED_MINUTES = (2, 17, 32, 47)
CAPTURE_WORKFLOW = "Capture BTC research candles"


def _timestamp(text):
    if not isinstance(text, str):
        raise ValueError("Missing GitHub run timestamp")
    date = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if date.utcoffset() is None:
        raise ValueError("GitHub timestamps must be timezone-aware")
    return date.astimezone(timezone.utc)


def schedule_reliability(runs, *, after, through):
    """Audit completed and failed scheduled runs in an exact UTC window.

    `observedRunFraction` is a *volume comparison*, not per-slot success.
    A delayed job may begin after its intended time, and GitHub can skip
    queued schedules, so no "confirmed missed slot" claim is made.
    """
    if after.tzinfo is None or through.tzinfo is None or through <= after:
        raise ValueError("Invalid timezone-aware window")
    first = after.astimezone(timezone.utc)
    last = through.astimezone(timezone.utc)
    # Count cron instants strictly AFTER the start and up to the end.
    cursor = first.replace(second=0, microsecond=0)
    if cursor <= first:
        cursor += timedelta(minutes=1)
    expected = 0
    while cursor <= last:
        if cursor.minute in EXPECTED_MINUTES:
            expected += 1
        cursor += timedelta(minutes=1)
    seen = {}
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("Malformed Actions run")
        if run.get("name") != CAPTURE_WORKFLOW or run.get("event") != "schedule":
            continue
        if run.get("head_branch") != "main":
            continue
        created = _timestamp(run.get("created_at"))
        if not first < created <= last:
            continue
        run_id = int(run["id"])
        if run_id <= 0:
            raise ValueError("Invalid Actions run ID")
        if run_id in seen and seen[run_id] != run:
            raise ValueError("Conflicting run metadata")
        seen[run_id] = run
    sorted_runs = sorted(seen.values(), key=lambda r: _timestamp(r["created_at"]))
    status_counts = Counter(r.get("conclusion") if r.get("status") == "completed" else "not_completed"
                            for r in sorted_runs)
    created = [_timestamp(r["created_at"]) for r in sorted_runs]
    gaps = [round((b-a).total_seconds()/60, 2) for a,b in zip(created,created[1:])]
    return {
        "kind": "research_only_github_schedule_run_audit_v1",
        "windowStartUtc": first.isoformat(),
        "windowEndUtc": last.isoformat(),
        "configuredCronUtc": "2,17,32,47 * * * *",
        "configuredCronOpportunities": expected,
        "observedScheduledRunCount": len(sorted_runs),
        "completedSuccesses": status_counts.get("success", 0),
        "completedFailures": sum(v for k,v in status_counts.items()
                                 if k not in ("success", "not_completed")),
        "notCompleted": status_counts.get("not_completed", 0),
        "observedRunToConfiguredOpportunityRatio": None if not expected else len(sorted_runs)/expected,
        "runCreationGapMinutes": gaps,
        "largestRunCreationGapMinutes": max(gaps) if gaps else None,
        "firstObservedRunId": sorted_runs[0]["id"] if sorted_runs else None,
        "lastObservedRunId": sorted_runs[-1]["id"] if sorted_runs else None,
        "sampledRunIds": [r["id"] for r in sorted_runs],
        "exactMissedCronSlotsVerified": False,
        "scheduledRunCountDoesNotProveCandleCoverage": True,
        "researchOnly": True,
        "originalViprasolVerified": False,
        "discordEligible": False,
        "automaticTrading": False,
        "profitabilityClaimAllowed": False,
    }
