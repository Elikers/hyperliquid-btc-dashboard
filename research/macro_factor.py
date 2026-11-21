"""Macro eighth-factor calculation for independently audited NQ1! inputs.

No price-feed fetch, TradingView equivalence claim, or live trading functionality.
CME_MINI:NQ1! continuous-futures rolls/closures must be externally verified.
"""
from math import isfinite, sqrt

def correlation(xs, ys):
    """Pearson correlation over identical, aligned nonmissing observations."""
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("Paired observations required")
    if not all(isfinite(float(x)) for x in xs+ys):
        raise ValueError("Missing or nonfinite macro observation")
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    dx, dy = [x-mx for x in xs], [y-my for y in ys]
    vx, vy = sum(v*v for v in dx), sum(v*v for v in dy)
    if vx <= 0 or vy <= 0:
        return None
    return sum(a*b for a,b in zip(dx,dy))/sqrt(vx*vy)


def macro_factor(btc_close, macro_close, macro_ema, *, length=20,
                 threshold=0.3, link_mode="positive",
                 source_verified=False):
    """Compute latest macro factor on pre-aligned chart bars.

    Pass None where CME futures is closed; never forward-fill without matching
    TradingView request.security barmerge behavior. Strictly refuse unknown data.
    """
    if link_mode not in ("positive","inverse"):
        raise ValueError("Unsupported link mode")
    if length < 2 or not 0 <= threshold <= 1:
        raise ValueError("Invalid correlation parameters")
    if len(btc_close) != len(macro_close) or len(macro_close) != len(macro_ema):
        raise ValueError("Unaligned input lengths")
    if len(btc_close) < length:
        return {"bull":False,"bear":False,"active":False,"correlation":None,
                "reason":"INSUFFICIENT_HISTORY","sourceVerified":False}
    xs, ys = btc_close[-length:], macro_close[-length:]
    if not all(isinstance(z,(int,float)) and isfinite(z)
               for z in (*xs,*ys)):
        return {"bull":False,"bear":False,"active":False,"correlation":None,
                "reason":"MISSING_ALIGNED_MACRO_CLOSE","sourceVerified":False}
    current, avg = macro_close[-1], macro_ema[-1]
    if not all(isinstance(z,(int,float)) and isfinite(z) for z in (current,avg)):
        return {"bull":False,"bear":False,"active":False,"correlation":None,
                "reason":"MACRO_EMA_UNAVAILABLE","sourceVerified":False}
    rho = correlation(xs,ys)
    if rho is None:
        return {"bull":False,"bear":False,"active":False,"correlation":None,
                "reason":"CORRELATION_UNDEFINED","sourceVerified":False}
    active = rho >= threshold if link_mode == "positive" else rho <= -threshold
    rising, falling = current > avg, current < avg
    bull = active and (rising if link_mode == "positive" else falling)
    bear = active and (falling if link_mode == "positive" else rising)
    reason = "ACTIVE" if active else "DECOUPLED"
    # Source provenance is separate from the formula. An unverified vendor is
    # never allowed to provide an actionable factor or Discord alert.
    if not source_verified:
        return {"bull":False,"bear":False,"active":active,
                "correlation":rho,"reason":"SOURCE_UNVERIFIED",
                "hypotheticalBull":bull,"hypotheticalBear":bear,
                "sourceVerified":False}
    return {"bull":bull,"bear":bear,"active":active,"correlation":rho,
            "reason":reason,"sourceVerified":True,
            "discordEligible":False}
