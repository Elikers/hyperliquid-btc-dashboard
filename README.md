# Hyperliquid BTC Live Dashboard

A **read-only public market-data dashboard** for the native Hyperliquid BTC perpetual contract (TradingView label: `HYPERLIQUID:BTCUSDC.P`).

**Website (after Pages deployment):** https://elikers.github.io/hyperliquid-btc-dashboard/

## Included

- Live last-executed BTC trade prices via Hyperliquid WebSocket
- BTC mark price and 24-hour price context
- 15m, 30m, and 1h candlestick chart
- Independently calculated EMA 9 and EMA 21 overlays
- Connection freshness warnings and reconnects
- GitHub Pages deployment workflow

## Important limitations

The **Viprasol Classic eight-factor signal engine is NOT deployed or verified** on this static website. This chart does **not** generate BUY/SELL, Entry, TP1–TP3, or Stop Loss alerts. Lab research signals and the local Python backend remain separate and disabled on Pages. No automatic trading or Discord trade notifications.

Prices arrive while the browser page is open; GitHub Pages does not operate an always-on Python bot. Exchange access, browser permissions, CDN availability and network latency affect price delivery. The historical candle endpoint uses a browser POST to the Hyperliquid public API; cross-origin restrictions may prevent data loading on some devices.

## Pages setup

1. Visit **Settings → Pages** in this repository.
2. Under **Build and deployment**, select **GitHub Actions** as Source.
3. Open **Actions → Deploy BTC Dashboard to GitHub Pages**, then run the workflow if it has not started automatically.
4. Visit the website link above once GitHub reports successful deployment.

## Security

This is a **public repository**. Never commit Discord webhook URLs, wallet credentials, keys, or other secrets. No such credentials are required for this chart.

## Attribution

Charts use [TradingView Lightweight Charts™](https://www.tradingview.com/lightweight-charts/) (open-source chart library). Market data is provided by public Hyperliquid APIs. The original Viprasol Pine Script belongs to its creator and is not represented here as an exact implementation.

## Research verification update (November 21, 2026)

- Added [Viprasol source audit and parity requirements](research/README.md).
- Added [strict candle/macro provenance and event comparison code](research/parity_checks.py).
- Added [automated offline research safety checks](.github/workflows/research-checks.yml).

**This does not enable automatic Discord trade alerts.** Nasdaq `CME_MINI:NQ1!` data provenance and full original Pine parity are still unverified, so all Classic research results remain non-actionable. The public Pages chart continues operating independently of the research checks.

