import hashlib
import io
import json
import unittest
import zipfile
from datetime import datetime, timezone

from research.collect_historical_artifacts import (
    select_history_artifacts,decode_history_zip,collect_historical)
from research.test_reconcile_historical_archives import make_archive, BASE

NOW=datetime(2026,11,21,23,0,tzinfo=timezone.utc)


def metadata(aid,run,*,name=None,branch="main",expired=False,
             created="2026-11-21T22:30:00Z"):
    return {"id":aid,"name":name or f"btc-historical-candles-{run}",
            "expired":expired,"created_at":created,
            "workflow_run":{"id":run,"head_branch":branch}}


def zipped(record,*,extra=False):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("historical_candles_only.json",json.dumps(record))
        if extra:
            z.writestr("other.txt","oops")
    return b.getvalue()


class Response:
    def __init__(self,content):
        self.source=io.BytesIO(content)
    def read(self,n=-1):
        return self.source.read(n)
    def __enter__(self):
        return self
    def __exit__(self,*args):
        pass


class HistoricalCollectorTests(unittest.TestCase):
    def test_valid_archive_selection_and_filters(self):
        data=[metadata(3,30),metadata(4,40,branch="dev"),
              metadata(5,50,expired=True),metadata(6,60,name="btc-paper-evidence-60"),
              metadata(7,70,name="btc-historical-candles-71")]
        found=select_history_artifacts(data,after=NOW.replace(hour=21))
        self.assertEqual([v["id"] for v in found],[3])

    def test_decode_only_one_expected_member(self):
        a=make_archive(BASE)
        self.assertEqual(decode_history_zip(zipped(a))["archiveSha256"],a["archiveSha256"])
        with self.assertRaisesRegex(ValueError,"Unexpected historical artifact"):
            decode_history_zip(zipped(a,extra=True))

    def test_fake_api_reconciles_overlapping_real_schema_archives(self):
        a,b=make_archive(BASE),make_archive(BASE+3600000)
        data=[metadata(1,1001),metadata(2,1002)]
        calls=[]
        def opener(request,timeout=30):
            url=request.full_url
            calls.append(url)
            self.assertEqual(request.get_header("Authorization"),"Bearer fake-token")
            if "/artifacts/1/zip" in url:
                return Response(zipped(a))
            if "/artifacts/2/zip" in url:
                return Response(zipped(b))
            if url.endswith("page=1"):
                return Response(json.dumps({"artifacts":data}).encode())
            return Response(json.dumps({"artifacts":[]}).encode())
        result=collect_historical("Elikers/hyperliquid-btc-dashboard","fake-token",
                    now=NOW,opener=opener)
        self.assertEqual(result["collection"]["artifactCount"],2)
        self.assertEqual(result["byTimeframe"]["15m"]["uniqueHistoricalClosedBars"],100)
        self.assertEqual(result["byTimeframe"]["15m"]["internalHistoricalMissingBarCount"],0)
        self.assertFalse(result["recoveredCandlesAreForwardObservations"])
        self.assertFalse(result["profitabilityClaimAllowed"])
        self.assertTrue(all(url.startswith("https://api.github.com/repos/") for url in calls))

    def test_absent_archives_remain_unverified(self):
        def opener(req,timeout=30):
            return Response(json.dumps({"artifacts":[]}).encode())
        r=collect_historical("Elikers/hyperliquid-btc-dashboard","t",now=NOW,
                             opener=opener)
        self.assertEqual(r["archivesIngested"],0)
        self.assertFalse(r["profitabilityClaimAllowed"])

    def test_corrupt_payload_fails_closed(self):
        a=make_archive(BASE)
        a["timeframes"]["15m"]["candles"][0]["c"]=99.0
        def opener(req,timeout=30):
            if "/zip" in req.full_url:
                return Response(zipped(a))
            if req.full_url.endswith("page=1"):
                return Response(json.dumps({"artifacts":[metadata(8,80)]}).encode())
            return Response(json.dumps({"artifacts":[]}).encode())
        with self.assertRaisesRegex(ValueError,"checksum mismatch"):
            collect_historical("Elikers/hyperliquid-btc-dashboard","t",
                               now=NOW,opener=opener)

    def test_reject_wrong_repo_and_token(self):
        with self.assertRaises(ValueError):
            collect_historical("../bad","x",now=NOW)
        with self.assertRaises(ValueError):
            collect_historical("Elikers/hyperliquid-btc-dashboard","",now=NOW)

    def test_artifact_limit_is_reported_not_hidden(self):
        data=[metadata(1,1001),metadata(2,1002)]
        a=make_archive(BASE)
        def opener(req,timeout=30):
            if "/zip" in req.full_url:
                return Response(zipped(a))
            if "page=1" in req.full_url:
                return Response(json.dumps({"artifacts":data}).encode())
            return Response(json.dumps({"artifacts":[]}).encode())
        r=collect_historical("Elikers/hyperliquid-btc-dashboard","t",now=NOW,
                            max_artifacts=1,opener=opener)
        self.assertTrue(r["collection"]["artifactLimitReached"])
        self.assertFalse(r["collection"]["exhaustiveWithinWindow"])


if __name__=="__main__":
    unittest.main()
