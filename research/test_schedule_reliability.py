import unittest
from datetime import datetime, timezone, timedelta
from research.schedule_reliability import schedule_reliability

START = datetime(2026,11,21,10,0,tzinfo=timezone.utc)


def run(i,minute,*,event="schedule",conclusion="success",status="completed",
        branch="main",name="Capture BTC research candles"):
    return {"id":i,"name":name,"event":event,"head_branch":branch,
            "created_at":(START+timedelta(minutes=minute)).isoformat(),
            "status":status,"conclusion":conclusion}


class ScheduleAuditTests(unittest.TestCase):
    def test_four_configured_opportunities_and_one_actual_run(self):
        result=schedule_reliability([run(11,3)],after=START,
                          through=START+timedelta(hours=1))
        self.assertEqual(result["configuredCronOpportunities"],4)
        self.assertEqual(result["observedScheduledRunCount"],1)
        self.assertEqual(result["completedSuccesses"],1)
        self.assertFalse(result["exactMissedCronSlotsVerified"])
        self.assertFalse(result["profitabilityClaimAllowed"])

    def test_failed_and_pending_are_not_success(self):
        result=schedule_reliability([run(1,3),run(2,18,conclusion="failure"),
                       run(3,33,status="queued",conclusion=None)],
                       after=START, through=START+timedelta(hours=1))
        self.assertEqual(result["completedSuccesses"],1)
        self.assertEqual(result["completedFailures"],1)
        self.assertEqual(result["notCompleted"],1)

    def test_exclude_push_other_branches_and_other_workflows(self):
        a=[run(1,3,event="push"),run(2,3,branch="feature"),
           run(3,3,name="Verify research safety")]
        out=schedule_reliability(a,after=START,through=START+timedelta(hours=1))
        self.assertEqual(out["observedScheduledRunCount"],0)

    def test_delayed_creations_not_mapped_to_cron_slots(self):
        r=schedule_reliability([run(1,25),run(2,58)],after=START,
                                through=START+timedelta(hours=1))
        self.assertEqual(r["largestRunCreationGapMinutes"],33)
        self.assertFalse(r["exactMissedCronSlotsVerified"])

    def test_duplicate_run_not_counted_twice(self):
        r=run(3,18)
        result=schedule_reliability([r,r],after=START,
                                     through=START+timedelta(hours=1))
        self.assertEqual(result["observedScheduledRunCount"],1)

    def test_conflicting_duplicate_fails(self):
        with self.assertRaises(ValueError):
            schedule_reliability([run(1,18),run(1,18,conclusion="failure")],
                                 after=START,through=START+timedelta(hours=1))

    def test_no_observations_is_not_success(self):
        result=schedule_reliability([],after=START,
                                     through=START+timedelta(hours=1))
        self.assertEqual(result["completedSuccesses"],0)
        self.assertEqual(result["observedRunToConfiguredOpportunityRatio"],0)

    def test_reject_naive_window(self):
        with self.assertRaises(ValueError):
            schedule_reliability([],after=START.replace(tzinfo=None),
                                 through=START+timedelta(hours=1))


if __name__=="__main__":
    unittest.main()
