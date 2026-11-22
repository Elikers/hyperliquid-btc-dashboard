"""Same-trade historical walk-forward paper comparison, isolated from live forward evidence.

Uses source-derived Classic hypothetical trades and *only candles known at their close*
to decide whether a fixed, preregistered CHOP gate would skip that trade.
This is historical replay, not real forward paper trading or Pine parity.
"""
import json
from pathlib import Path

from research.backtest_real_btc_snapshot import backtest_research, validated_candles, fetch_latest_snapshots
from research.regime_sweep_research import diagnostic

CHOP_CUTOFF = 61.8
COST_KEYS = ("0", "7", "15")


def compare_historical_paper(snapshots, *, source_run_id=None, min_history_bars=650):
    candles, _ = validated_candles(snapshots, min_history_bars=min_history_bars)
    baseline = backtest_research(snapshots, source_run_id=source_run_id, min_history_bars=min_history_bars)
    outcomes = {}
    comparisons = []
    for tf, bars in candles.items():
        location = {bar["T"]: i for i, bar in enumerate(bars)}
        original = [t for t in baseline["hypotheticalTrades"] if t["timeframe"] == tf]
        records = []
        for trade in original:
            idx = location.get(trade["closedBarEndMs"])
            if idx is None or idx < 21:
                raise ValueError("Missing signal candle or insufficient past diagnostics")
            observation = diagnostic(bars[:idx+1])
            chop = observation["choppinessIndex"]
            # No training, no future bars, no signal reinterpretation.
            allowed = chop is not None and chop <= CHOP_CUTOFF
            record = {
                "timeframe": tf, "closedBarEndMs": trade["closedBarEndMs"],
                "side": trade["side"], "choppinessAtEntry": chop,
                "sweepAtEntry": observation["sweepSignal"],
                "regimeGateAllowed": allowed, "outcome": trade["outcome"],
                "netRByOneWayCostBps": trade["netRByOneWayCostBps"],
            }
            records.append(record)
            comparisons.append(record)
        def rollup(items):
            resolved = [x for x in items if x["netRByOneWayCostBps"] is not None]
            return {
                "candidates": len(items), "resolved": len(resolved),
                "unresolved": len(items)-len(resolved),
                "netRSumByOneWayCostBps": {
                    cost: sum(x["netRByOneWayCostBps"][cost] for x in resolved)
                    for cost in COST_KEYS
                },
                "netPositiveShareAt7Bps": (
                    sum(x["netRByOneWayCostBps"]["7"] > 0 for x in resolved)/len(resolved)
                    if resolved else None
                ),
            }
        allowed = [x for x in records if x["regimeGateAllowed"]]
        blocked = [x for x in records if not x["regimeGateAllowed"]]
        outcomes[tf] = {
            "unchangedClassic": rollup(records),
            "fixedChopGate": rollup(allowed),
            "skipped": rollup(blocked),
            "sweepsObservedAtEntry": sum(x["sweepAtEntry"] != "NONE" for x in records),
        }
    return {
        "kind": "HISTORICAL_ONLY_WALK_FORWARD_PAPER_COMPARISON_V1",
        "sourceRunId": source_run_id, "market": "HYPERLIQUID:BTCUSDC.P",
        "candidate": "Classic candidates filtered at candle close by CHOP(14)<=61.8",
        "fixedGateNotOptimized": True,
        "timeframes": outcomes, "hypotheticalTradeComparison": comparisons,
        "assumptions": [
            "Uses already-generated Classic Python candidate trades and original hypothetical outcomes",
            "CHOP and sweep annotations use only closed candles up to each decision",
            "The same historical dataset is used for a descriptive paired comparison; not held-out validation",
            "No partial exits or changed fills; original conservative exit assumptions carried through",
            "Per-trade net R values cannot be added to imply account equity or independent portfolio performance",
            "No guarantee selected trades repeat or perform similarly on unseen live candles",
        ],
        "historicalOnly": True, "recoveredCandlesAreForwardObservations": False,
        "independentTradingViewSourceVerified": False,
        "originalViprasolVerified": False, "independentForwardProfitable": False,
        "discordEligible": False, "automaticTrading": False,
        "profitabilityClaimAllowed": False,
    }


def main():
    import argparse, os
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="Elikers/hyperliquid-btc-dashboard")
    parser.add_argument("--out", type=Path, default=Path("test-output/instant_paper_comparison.json"))
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Read-only GITHUB_TOKEN required")
    snapshots, run_id, artifact_id = fetch_latest_snapshots(args.repo, token)
    result = compare_historical_paper(snapshots, source_run_id=run_id)
    result["sourceArtifactId"] = artifact_id
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print("Historical paper replay only; source run:", run_id)
    for tf, v in result["timeframes"].items():
        print(tf, "classic", v["unchangedClassic"]["candidates"],
              "gate retained", v["fixedChopGate"]["candidates"],
              "netR@7bps", round(v["fixedChopGate"]["netRSumByOneWayCostBps"]["7"], 4))
    print("No forward profitability or original Pine parity implied; alerts/orders OFF")


if __name__ == "__main__":
    main()
