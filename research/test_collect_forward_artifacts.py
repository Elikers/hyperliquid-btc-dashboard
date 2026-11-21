import hashlib
import io
import json
import unittest
import zipfile
from datetime import datetime,timezone
from urllib.parse import urlsplit,parse_qs
from urllib.request import Request

from research.collect_forward_artifacts import (
    select_artifacts,decode_paper_archive,collect_daily,_read,_SafeArtifactRedirect)


NOW=datetime(2026,11,21,12,0,tzinfo=timezone.utc)


def metadata(id,run,*,branch="main",name=None,created="2026-11-21T11:03:00Z",
             expired=False):
    return {"id":id,"name":name or f"btc-paper-evidence-{run}",
            "expired":expired,"created_at":created,
            "workflow_run":{"id":run,"head_branch":branch}}


def observation():
    steps={"15m":900000,"30m":1800000,"1h":3600000}
    frames={}
    for tf,step in steps.items():
        frames[tf]={"closedBarStartMs":0,"closedBarEndMs":step-1,
            "bar":{"o":100.0,"h":101.0,"l":99.0,"c":100.0,"v":8.0},
            "bullScore":4,"bearScore":2,"threshold":5,"rawCrossover":None,
            "hypotheticalDirection":None,"hypotheticalRiskLadder":None,
            "blockedReasons":["NO_NEW_EMA_CROSS"],"adr":{"available":True},
            "sourceVerified":False}
    value={"kind":"HYPERLIQUID_BTC_FORWARD_PAPER_EVIDENCE_V1",
           "model":"VIPRASOL_CLASSIC_MACRO_OFF",
           "source":"Hyperliquid BTC public closed candles",
           "capturedAtUtc":"2026-11-21T10:46:00+00:00",
           "originalViprasolVerified":False,"discordEligible":False,
           "automaticTrading":False,"timeframes":frames}
    value["recordSha256"]=hashlib.sha256(json.dumps(
        value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return value


def zipped(data,*,extra=False):
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as archive:
        archive.writestr("forward_observation.json",json.dumps(data))
        if extra:
            archive.writestr("unexpected.txt","oops")
    return out.getvalue()


class Response:
    def __init__(self,content):
        self.buf=io.BytesIO(content)
    def read(self,n=-1):
        return self.buf.read(n)
    def __enter__(self):
        return self
    def __exit__(self,*args):
        pass


class CollectTests(unittest.TestCase):
    def test_cross_host_signed_artifact_redirect_strips_bearer(self):
        original=Request("https://api.github.com/repos/Elikers/x/actions/artifacts/42/zip",
                         headers={"Authorization":"Bearer TEST_SECRET",
                                  "X-GitHub-Api-Version":"2022-11-28"})
        url="https://productionresultssa1.blob.core.windows.net/signed.zip?sig=test"
        redirected=_SafeArtifactRedirect().redirect_request(
            original,None,302,"Found",{},url)
        self.assertEqual(redirected.full_url,url)
        self.assertIsNone(redirected.get_header("Authorization"))
        self.assertNotIn("TEST_SECRET",str(redirected.headers))

    def test_unknown_archive_redirect_host_rejected(self):
        original=Request("https://api.github.com/repos/Elikers/x/actions/artifacts/42/zip")
        with self.assertRaisesRegex(ValueError,"Unexpected external"):
            _SafeArtifactRedirect().redirect_request(
                original,None,302,"Found",{},"https://example.org/archive.zip")

    def test_unencrypted_redirect_rejected(self):
        original=Request("https://api.github.com/repos/Elikers/x/actions/artifacts/42/zip")
        with self.assertRaises(ValueError):
            _SafeArtifactRedirect().redirect_request(
                original,None,302,"Found",{},"http://productionresultssa1.blob.core.windows.net/test")

    def test_select_only_main_valid_nonexpired_recent(self):
        items=[metadata(1,10),metadata(2,20,branch="test"),
               metadata(3,30,expired=True),metadata(4,40,name="btc-research-candles-40"),
               metadata(5,50,created="2026-11-18T11:03:00Z")]
        picked=select_artifacts(items,after=NOW.replace(hour=10))
        self.assertEqual([x["id"] for x in picked],[1])

    def test_reject_artifact_run_name_mismatch(self):
        self.assertEqual(select_artifacts([metadata(1,10,name="btc-paper-evidence-11")],
                         after=NOW.replace(hour=10)),[])

    def test_archive_decode(self):
        self.assertEqual(decode_paper_archive(zipped(observation()))["model"],
                         "VIPRASOL_CLASSIC_MACRO_OFF")

    def test_reject_extra_zip_members(self):
        with self.assertRaisesRegex(ValueError,"ZIP members"):
            decode_paper_archive(zipped(observation(),extra=True))

    def test_collect_once_with_fake_api(self):
        docs=[metadata(41,4100)]
        record=observation()
        def opener(request,timeout=30):
            url=request.full_url
            self.assertEqual(request.get_header("Authorization"),"Bearer fake-token")
            if "/actions/artifacts/41/zip" in url:
                return Response(zipped(record))
            if "page=1" in url:
                return Response(json.dumps({"artifacts":docs}).encode())
            return Response(json.dumps({"artifacts":[]}).encode())
        output=collect_daily("Elikers/hyperliquid-btc-dashboard",
                             "fake-token",now=NOW,opener=opener)
        self.assertEqual(output["collection"]["artifactCount"],1)
        self.assertEqual(output["byTimeframe"]["15m"]["uniqueClosedBars"],1)
        self.assertFalse(output["profitabilityClaimAllowed"])
        self.assertFalse(output["discordEligible"])
        self.assertIn("closedCandleCoverage",output)
        self.assertGreater(output["closedCandleCoverage"]["byTimeframe"]["15m"]["unobservedClosedBars"],0)
        self.assertFalse(output["closedCandleCoverage"]["profitabilityClaimAllowed"])

    def test_missing_artifacts_not_profitable(self):
        def empty(request,timeout=30):
            return Response(json.dumps({"artifacts":[]}).encode())
        output=collect_daily("Elikers/hyperliquid-btc-dashboard","t",
                             now=NOW,opener=empty)
        self.assertEqual(output["collection"]["artifactCount"],0)
        self.assertEqual(output["byTimeframe"]["1h"]["resolved"],0)
        self.assertFalse(output["profitabilityClaimAllowed"])

    def test_reject_corrupted_record_end_to_end(self):
        def broken(request,timeout=30):
            if "/zip" in request.full_url:
                record=observation()
                record["automaticTrading"]=True
                return Response(zipped(record))
            if "page=1" in request.full_url:
                return Response(json.dumps({"artifacts":[metadata(42,4200)]}).encode())
            return Response(json.dumps({"artifacts":[]}).encode())
        with self.assertRaises(ValueError):
            collect_daily("Elikers/hyperliquid-btc-dashboard","t",
                          now=NOW,opener=broken)

    def test_invalid_repo_rejected(self):
        with self.assertRaises(ValueError):
            collect_daily("../../secret","t",now=NOW)

    def test_empty_token_refused(self):
        with self.assertRaises(ValueError):
            _read("https://api.github.com/repos/example/r/actions/artifacts","")

    def test_pagination_stops_after_old_artifact_page(self):
        old=[metadata(i,1000+i,created="2026-11-17T11:03:00Z")
             for i in range(1,101)]
        pages=[]
        def opener(request,timeout=30):
            pages.append(request.full_url)
            return Response(json.dumps({"artifacts":old}).encode())
        data=collect_daily("Elikers/hyperliquid-btc-dashboard","t",
                           now=NOW,opener=opener)
        self.assertEqual(len(pages),1)
        self.assertEqual(data["collection"]["artifactCount"],0)

    def test_explicit_limit(self):
        with self.assertRaises(ValueError):
            select_artifacts([],after=NOW,limit=0)


if __name__=="__main__":
    unittest.main()
