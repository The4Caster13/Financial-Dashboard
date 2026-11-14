# Finance Research Dashboard

A Python/Dash research terminal for equity analysis and investment-banking-style
workflows, built on the [OpenBB Platform](https://docs.openbb.co/platform) for
market data. The dashboard offers an easy and accesible dashboard for me to monitor the market conditions, before coming up with an investment thesis or idea. 

## Features

- **Overview** — Fear & Greed Index, major indices, sector performance, top
  gainers/losers/most active, commodities snapshot.
- **Company** — profile, key stats, 12-month price chart, analyst consensus,
  income statement / balance sheet / cash flow.
- **Comps** — auto-suggested peer group (same sector/industry) with an editable
  ticker list, a multiples table (P/E, EV/EBITDA, EV/Revenue, P/B, margins,
  growth, leverage), comparison bar charts, and peer median/mean/range summary.
- **Screener** — filter the market by sector, market cap, price, beta, and
  volume.
- **Commodities** — snapshot grid (gold, silver, WTI, Brent, natural gas,
  copper, corn, wheat) with a price + volume detail chart per commodity.
- **News & Sentiment** — CNN Fear & Greed history, ticker-specific news, and a
  broad-market news feed.

## Setup

```bash
# from this directory
source .venv/bin/activate   # already created; recreate with `python3 -m venv .venv` if needed
pip install -r requirements.txt
cp .env.example .env        # optional — defaults work with no API keys
python run.py
```
Then open http://127.0.0.1:8050.
