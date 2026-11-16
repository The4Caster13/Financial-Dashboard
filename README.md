# Finance Research Dashboard

A Python/Dash research terminal for equity analysis and investment-banking-style
workflows, built on the [OpenBB Platform](https://docs.openbb.co/platform) for
market data. The dashboard offers an easy and accesible dashboard for me to monitor the market conditions, before coming up with an investment thesis or idea. 

<img width="957" height="499" alt="Financial_Dashboard" src="https://github.com/user-attachments/assets/5c5e86be-83b0-4b04-bd91-de00a55691cb" />

## Features

- **Overview** — a single-screen dashboard: Fear & Greed gauge, major indices,
  commodities, market heatmap, top gainers/losers/most active, top headlines,
  and potential M&A news. Each panel has an Expand button into its full page.
- **Heatmap** — the largest S&P 500 names by sector, sized by market cap and
  colored by daily % change, with sector drill-down and a sortable stock table.
- **Movers** — top gainers / losers / most active with market cap, 52-week
  range, and forward P/E.
- **M&A** — potential deals (talks, bids, sale processes) and announced deals,
  filterable by stage and lookback.
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
source .venv/bin/activate  
pip install -r requirements.txt
cp .env.example .env        
python run.py
```
Then open http://127.0.0.1:8050.
