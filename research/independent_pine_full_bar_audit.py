"""Conservative full-closed-bar independent Pine comparison gate.

No attempt to manufacture TradingView exports from Python or screenshots.
Input must be independently obtained source output and separate candidate
closed bars. Even a perfect sample can never enable trading or Discord.
"""
from math import isfinite

TIMEFRAMES=("15m","30m","1h")
STEP={"15m":900000,"30m":1800000,"1h":3600000}
FACTORS=("ema","rsi","macd","vwap","adx","volume","rsi15m")
PRICES=("entry","stop","tp1","tp2","tp3")


def _finite(value):
    if isinstance(value,bool):
        raise ValueError("Boolean is not a numeric measurement")
    value=float(value)
    if not isfinite(value):
        raise ValueError("Nonfinite numeric measurement")
    return value


def _index(rows, *, side):
    if not isinstance(rows,list):
        raise ValueError(f"{side} must be an array of closed bars")
    out={tf:{} for tf in TIMEFRAMES}
    for item in rows:
        if not isinstance(item,dict):
            raise ValueError("Malformed comparison bar")
        tf=item.get("timeframe")
        if tf not in STEP:
            raise ValueError("Unsupported comparison timeframe")
        end=item.get("closedBarEndMs")
        if type(end) is not int or end<0 or (end+1)%STEP[tf]:
            raise ValueError("Not an aligned closed-bar timestamp")
        if end in out[tf]:
            raise ValueError("Duplicate timeframe and close")
        outcome=item.get("signal")
        if outcome not in (None,"LONG","SHORT"):
            raise ValueError("Signal must be LONG/SHORT/null")
        factors=item.get("factors")
        if not isinstance(factors,dict) or set(factors)!=set(FACTORS):
            raise ValueError("All seven factor values must be explicit")
        if any(type(factors[k]) is not bool for k in FACTORS):
            raise ValueError("Factor values must be booleans")
        if outcome:
            if not all(k in item for k in PRICES):
                raise ValueError("Signal requires complete price ladder")
            values={k:_finite(item[k]) for k in PRICES}
            entry,stop=values["entry"],values["stop"]
            targets=[values["tp1"],values["tp2"],values["tp3"]]
            if min(values.values())<=0 or (outcome=="LONG" and not
              (stop<entry<targets[0]<targets[1]<targets[2])) or (
              outcome=="SHORT" and not
              (stop>entry>targets[0]>targets[1]>targets[2])):
                raise ValueError("Invalid signal price ladder")
        elif any(k in item and item[k] is not None for k in PRICES):
            raise ValueError("No-signal bar cannot have a trade ladder")
        out[tf][end]=item
    return out


def compare_full_bar_pine(reference, candidate, *, provenance,
                          max_price_delta=0.1):
    """Fail closed: compare all signal and no-signal bars and seven factors.

    A provenance declaration is caller metadata, never cryptographic proof
    that a file came from TradingView. Unproven independent origin remains
    an explicit external blocker to original-source parity certification.
    """
    tol=_finite(max_price_delta)
    if tol<0:
        raise ValueError("Invalid price tolerance")
    if not isinstance(provenance,dict):
        raise ValueError("Reference provenance required")
    required=("sourcePlatform","sourceMode","pineSourceSha256","symbol",
              "settings","exportMethod")
    if any(not isinstance(provenance.get(k),str) or not provenance[k].strip()
           for k in required):
        raise ValueError("Missing independent source-provenance fields")
    if provenance["sourcePlatform"]!="TradingView" or provenance["sourceMode"]!="VIPRASOL_CLASSIC_MACRO_OFF":
        raise ValueError("Reference must be original TradingView Macro-Off configuration")
    if provenance["symbol"]!="HYPERLIQUID:BTCUSDC.P":
        raise ValueError("Wrong TradingView reference market")
    if provenance["settings"]!="original_unchanged":
        raise ValueError("Original settings need confirmation")
    r=_index(reference,side="reference")
    c=_index(candidate,side="candidate")
    result={}
    signal_errors=[]
    factor_errors=[]
    price_errors=[]
    for tf in TIMEFRAMES:
        common=sorted(r[tf].keys()&c[tf].keys())
        missing=sorted(r[tf].keys()-c[tf].keys())
        extra=sorted(c[tf].keys()-r[tf].keys())
        signal_bad=0
        for end in common:
            a,b=r[tf][end],c[tf][end]
            if a["signal"]!=b["signal"]:
                signal_bad+=1
                signal_errors.append({"timeframe":tf,"closedBarEndMs":end,
                     "reference":a["signal"],"candidate":b["signal"]})
            for k in FACTORS:
                if a["factors"][k]!=b["factors"][k]:
                    factor_errors.append({"timeframe":tf,"closedBarEndMs":end,
                     "factor":k,"reference":a["factors"][k],"candidate":b["factors"][k]})
            if a["signal"]==b["signal"] and a["signal"] is not None:
                for k in PRICES:
                    delta=abs(_finite(a[k])-_finite(b[k]))
                    if delta>tol:
                        price_errors.append({"timeframe":tf,"closedBarEndMs":end,
                             "field":k,"absoluteDifference":delta})
        result[tf]={
            "referenceClosedBars":len(r[tf]),
            "candidateClosedBars":len(c[tf]),
            "alignedClosedBars":len(common),
            "referenceBarsAbsentFromCandidate":len(missing),
            "candidateBarsAbsentFromReference":len(extra),
            "signalMismatches":signal_bad,
            "factorMismatches":sum(x["timeframe"]==tf for x in factor_errors),
            "priceMismatches":sum(x["timeframe"]==tf for x in price_errors),
            "referenceNoSignalBars":sum(row["signal"] is None for row in r[tf].values()),
            "referenceSignalBars":sum(row["signal"] is not None for row in r[tf].values()),
            "closedBarsGapFree": bool(common) and
                all(b-a==STEP[tf] for a,b in zip(common,common[1:])),
        }
    complete=all(result[tf]["referenceClosedBars"]>0 and
            result[tf]["referenceClosedBars"]==result[tf]["candidateClosedBars"]==
            result[tf]["alignedClosedBars"] and result[tf]["closedBarsGapFree"]
            for tf in TIMEFRAMES)
    all_match=(complete and not signal_errors and not factor_errors and
               not price_errors)
    return {
        "kind":"INDEPENDENT_PINE_CLOSED_BAR_RESEARCH_COMPARISON_V1",
        "provenanceDeclaredOnlyNotVerified":True,
        "sourceSha256Claimed":provenance["pineSourceSha256"],
        "perTimeframe":result,
        "signalDifferences":signal_errors,
        "factorDifferences":factor_errors,
        "priceDifferences":price_errors,
        "alignedSampleComplete":complete,
        "allAlignedSampleFieldsMatch":all_match,
        "independentTradingViewSourceVerified":False,
        "originalViprasolVerified":False,
        "discordEligible":False,
        "automaticTrading":False,
        "profitabilityClaimAllowed":False,
        "remaining":["Independently authenticate TradingView export and Pine/settings",
                     "Validate exchange OHLC and TradingView data equivalence",
                     "Accumulate sufficiently long multi-period evidence including no-signal bars"],
    }
