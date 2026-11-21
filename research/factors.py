"""Seven Viprasol technical-factor calculations; RESEARCH ONLY, not signal parity.

Source basis: user-provided Viprasol Pine v6, core indicators and confluence.
Exact TradingView VWAP session anchoring, higher-timeframe request.security
barmerge and continuous CME_MINI:NQ1! data are not verified.
DO NOT use to send Discord trading alerts or execute orders.
"""
from math import isfinite

FACTOR_NAMES = ("vwap", "rsi", "macd", "ema", "adx", "volume", "confirmation_rsi")
STEPS = {"15m": 900000, "30m": 1800000, "1h": 3600000}


def ema(values, length):
    """EMA initialized on the first non-na observation as in Pine ta.ema."""
    out, prev = [], None
    alpha = 2 / (length + 1)
    for value in values:
        if value is None or not isfinite(value):
            out.append(prev)
            continue
        prev = value if prev is None else prev + alpha * (value - prev)
        out.append(prev)
    return out


def rma(values, length):
    """Wilder RMA initialized with SMA of the first length valid samples."""
    out, window, prev = [], [], None
    for value in values:
        if value is None or not isfinite(value):
            out.append(None)
            continue
        if prev is None:
            window.append(value)
            if len(window) >= length:
                prev = sum(window) / length
        else:
            prev = ((length - 1) * prev + value) / length
        out.append(prev)
    return out


def sma(values, length):
    return [None if i < length - 1 else sum(values[i+1-length:i+1]) / length
            for i in range(len(values))]


def rsi(closes, length=14):
    ups, downs = [None], [None]
    for a, b in zip(closes, closes[1:]):
        ups.append(max(b-a, 0))
        downs.append(max(a-b, 0))
    u, d = rma(ups, length), rma(downs, length)
    result = []
    for a, b in zip(u, d):
        if a is None or b is None:
            result.append(None)
        elif a == 0 and b == 0:
            result.append(50.0)
        elif b == 0:
            result.append(100.0)
        else:
            result.append(100 - 100/(1+a/b))
    return result


def dmi_adx(highs, lows, closes, length=14):
    tr = [highs[0]-lows[0]]
    pos, neg = [None], [None]
    for i in range(1, len(closes)):
        up = highs[i]-highs[i-1]
        down = lows[i-1]-lows[i]
        pos.append(up if up > down and up > 0 else 0.0)
        neg.append(down if down > up and down > 0 else 0.0)
        tr.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]),
                      abs(lows[i]-closes[i-1])))
    atr, plus, minus = rma(tr, length), rma(pos, length), rma(neg, length)
    dx = []
    for a, b, c in zip(atr, plus, minus):
        if a is None or b is None or c is None:
            dx.append(None)
            continue
        p, m = (100*b/a, 100*c/a) if a else (0.0, 0.0)
        dx.append(100*abs(p-m)/(p+m) if p+m else 0.0)
    return rma(dx, length)


def clean(candles, step):
    result, previous = [], None
    if step not in STEPS.values():
        raise ValueError("Unsupported timeframe")
    for raw in candles:
        c = {k: float(raw[k]) for k in ("o", "h", "l", "c", "v")}
        t, end = int(raw["t"]), int(raw["T"])
        if not all(isfinite(x) for x in c.values()) or c["v"] < 0:
            raise ValueError("Invalid non-finite or negative candle data")
        if c["h"] < max(c["o"], c["c"], c["l"]) or c["l"] > min(c["o"], c["c"], c["h"]):
            raise ValueError("Invalid candle OHLC")
        if t % step or end != t + step - 1 or (previous is not None and t != previous + step):
            raise ValueError("Nonconsecutive candle timestamps")
        result.append(dict(c, t=t, T=end))
        previous = t
    return result


def vwap_utc_day(bars):
    """Research approximation only: VWAP anchor may differ from TradingView."""
    total, amount, day = 0.0, 0.0, None
    out = []
    for bar in bars:
        this_day = bar["t"] // 86400000
        if day != this_day:
            total, amount, day = 0.0, 0.0, this_day
        quantity = bar["v"]
        total += (bar["h"]+bar["l"]+bar["c"])/3 * quantity
        amount += quantity
        out.append(total/amount if amount else None)
    return out


def compute_seven_factors(btc_candles, confirm_15m_candles, *, timeframe="15m"):
    """Return last *closed* candle factors; macro/Discord ALWAYS unavailable."""
    if timeframe not in STEPS:
        raise ValueError("Unsupported timeframe")
    bars = clean(btc_candles, STEPS[timeframe])
    confirm = clean(confirm_15m_candles, STEPS["15m"])
    if len(bars) < 100 or len(confirm) < 100:
        raise ValueError("Insufficient indicator warmup history")
    opens = [x["o"] for x in bars]
    highs = [x["h"] for x in bars]
    lows = [x["l"] for x in bars]
    closes = [x["c"] for x in bars]
    volumes = [x["v"] for x in bars]
    fast, slow = ema(closes, 9), ema(closes, 21)
    relative_strength = rsi(closes, 14)
    macd_line = [a-b for a,b in zip(ema(closes,12),ema(closes,26))]
    macd_signal = ema(macd_line,9)
    adx = dmi_adx(highs,lows,closes)
    volume_sma = sma(volumes,20)
    vwap = vwap_utc_day(bars)
    confirmation_rsi = rsi([x["c"] for x in confirm], 14)
    end = bars[-1]["T"]
    j = next((i for i in range(len(confirm)-1, -1, -1)
              if confirm[i]["T"] <= end), None)
    if j is None or confirmation_rsi[j] is None:
        raise ValueError("15m confirmation not available")
    if end - confirm[j]["T"] >= STEPS["15m"]:
        raise ValueError("Stale 15m confirmation data")
    i = len(bars)-1
    if any(x is None for x in (relative_strength[i], adx[i], volume_sma[i],vwap[i])):
        raise ValueError("Indicator warmup incomplete")
    bullish = {
        "vwap": closes[i] > vwap[i],
        "rsi": relative_strength[i] > 50,
        "macd": macd_line[i] > macd_signal[i],
        "ema": fast[i] > slow[i],
        "adx": adx[i] > 25 and closes[i] > fast[i],
        "volume": volumes[i] > 0 and volumes[i] > volume_sma[i] and closes[i] > opens[i],
        "confirmation_rsi": confirmation_rsi[j] > 50,
    }
    bearish = {
        "vwap": closes[i] < vwap[i],
        "rsi": relative_strength[i] < 50,
        "macd": macd_line[i] < macd_signal[i],
        "ema": fast[i] < slow[i],
        "adx": adx[i] > 25 and closes[i] < fast[i],
        "volume": volumes[i] > 0 and volumes[i] > volume_sma[i] and closes[i] < opens[i],
        "confirmation_rsi": confirmation_rsi[j] < 50,
    }
    return {
        "timeframe": timeframe,
        "barCloseMs": end,
        "bullFactors": bullish,
        "bearFactors": bearish,
        "bullScoreSeven": sum(bullish.values()),
        "bearScoreSeven": sum(bearish.values()),
        "previousFast": fast[-2], "previousSlow": slow[-2],
        "fast": fast[-1], "slow": slow[-1],
        "rsi": relative_strength[-1], "adx": adx[-1],
        "macd": macd_line[-1], "macdSignal": macd_signal[-1],
        "vwap": vwap[-1], "confirmationRsi": confirmation_rsi[j],
        "confirmationBarCloseMs": confirm[j]["T"],
        "macroFactor": "UNAVAILABLE",
        "reproductionStatus": "RESEARCH_ONLY_UNVERIFIED",
        "originalViprasolVerified": False,
        "discordEligible": False,
        "limitations": [
            "CME_MINI:NQ1! feed and roll adjustment unverified",
            "TradingView VWAP anchor unverified",
            "TradingView higher-timeframe request.security barmerge unverified",
            "TradingView historical OHLC and indicator warmup parity unverified"
        ],
    }
