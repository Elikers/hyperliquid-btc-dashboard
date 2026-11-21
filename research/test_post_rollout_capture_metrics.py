import unittest
from datetime import timedelta

from research.post_rollout_capture_metrics import PILOT_START_UTC, assess_pilot


def run(i,minutes,*,event="schedule",status="completed",conclusion="success"):
    return {
        "id":i,"name":"Capture BTC research candles","event":event,
        "head_branch":"main","status":status,"conclusion":conclusion,
        "created_at":(PILOT_START_UTC+timedelta(minutes=minutes)).isoformat(),
    }


def observation(minutes):
    frames={}
    for tf,step in (("15m",900000),("30m",1800000),("1h",3600000)):
        # Correctly aligned close. No trading fields; the pilot coverage
        # reader needs only real-close timestamp and capture instant.
        when=int((PILOT_START_UTC+timedelta(minutes=minutes)).timestamp()*1000)
        close=(when//step)*step-1
        frames[tf]={"closedBarEndMs":close}
    return {"capturedAtUtc":(PILOT_START_UTC+timedelta(minutes=minutes)).isoformat(),
            "timeframes":frames}


class PostRolloutTests(unittest.TestCase):
    def test_not_ready_before_full_day(self):
        result=assess_pilot([],[],through=PILOT_START_UTC+timedelta(hours=1))
        self.assertFalse(result["fullPostRolloutWindowAvailable"])
        self.assertEqual(result["scheduledSuccessfulRunCount"],0)
        self.assertEqual(result["closedBarCoverageFromScheduledRunsOnly"]["byTimeframe"]["15m"]["expectedClosedBars"],4)

    def test_push_smoke_never_inflates_scheduled_coverage(self):
        when=PILOT_START_UTC+timedelta(minutes=35)
        result=assess_pilot([{"runId":1,"record":observation(35)}],
                             [run(1,34,event="push")],through=when)
        self.assertEqual(result["scheduledSuccessfulRunCount"],0)
        self.assertEqual(result["closedBarCoverageFromScheduledRunsOnly"]["byTimeframe"]["15m"]["observedUniqueClosedBars"],0)

    def test_successful_schedule_counts_distinct_bar_only(self):
        result=assess_pilot([
            {"runId":2,"record":observation(23)},
            {"runId":3,"record":observation(27)},
            {"runId":4,"record":observation(23)}
        ],[run(2,22),run(3,26),run(4,22,event="workflow_dispatch")],
          through=PILOT_START_UTC+timedelta(minutes=40))
        self.assertEqual(result["scheduledSuccessfulRunCount"],2)
        self.assertEqual(result["scheduledRunsWithVerifiableForwardArtifacts"],2)
        self.assertEqual(result["closedBarCoverageFromScheduledRunsOnly"]["byTimeframe"]["15m"]["observedUniqueClosedBars"],1)

    def test_incomplete_or_failed_runs_cannot_supply_evidence(self):
        r=assess_pilot([{"runId":2,"record":observation(8)}],
            [run(2,7,conclusion="failure")],
            through=PILOT_START_UTC+timedelta(minutes=40))
        self.assertEqual(r["scheduledRunsWithVerifiableForwardArtifacts"],0)

    def test_missing_artifact_is_reported(self):
        r=assess_pilot([], [run(2,7)],
           through=PILOT_START_UTC+timedelta(minutes=30))
        self.assertEqual(r["missingForwardEvidenceForSuccessfulRunCount"],1)

    def test_exact_full_day_is_reviewable_not_approved(self):
        r=assess_pilot([],[],through=PILOT_START_UTC+timedelta(hours=24))
        self.assertTrue(r["fullPostRolloutWindowAvailable"])
        self.assertEqual(r["outcome"],"READY_FOR_MANUAL_EVIDENCE_REVIEW")
        self.assertTrue(r["doesNotClaimImprovedReliability"])
        self.assertFalse(r["profitabilityClaimAllowed"])
        self.assertFalse(r["discordEligible"])

    def test_before_baseline_fails_closed(self):
        r=assess_pilot([],[],through=PILOT_START_UTC)
        self.assertEqual(r["outcome"],"NOT_ENOUGH_ELAPSED_TIME")


if __name__=="__main__":
    unittest.main()
