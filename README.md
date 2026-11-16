# Finance Research Dashboard

A Python/Dash research terminal for equity analysis and investment-banking-style
workflows, built on the [OpenBB Platform](https://docs.openbb.co/platform) for
market data.

## Live updates

The Overview, Company, Commodities, Heatmap, Movers, and M&A pages auto-refresh every 30 seconds
(configurable via `DASHBOARD_REFRESH_MS` in `.env`) via a `dcc.Interval` —
no manual reload needed. A small green "Live · updated HH:MM:SS" indicator
at the top of each shows when it last pulled fresh data. Prices themselves
come from recent daily bars (the most reliable free field yfinance exposes
outside exact real-time ticks), so movements show up within one refresh
cycle of happening, not tick-by-tick.

Each underlying data call still has its own cache TTL (`config.py`), so if a
value hasn't changed since the last cache window, the refresh just re-renders
the same number — that's expected, not a bug. Comps and the Screener are
intentionally NOT on a timer: comps multiples are cached for hours (they're
fundamentals, not quotes) and the screener is a deliberate "hit Run to see
current results" workflow rather than a live feed.

## Features

- **Overview** — a single-screen dashboard (no scrolling): Fear & Greed gauge,
  major indices, commodities, market heatmap, top gainers/losers/most active,
  top headlines, and potential M&A news. Every panel has an **Expand** button
  into its full page; commodity tiles open that commodity's chart, and
  clicking a stock in the heatmap opens its Company page. Below ~1100px wide
  or ~540px tall it falls back to a normal scrolling layout.
- **Heatmap** — the largest S&P 500 names by sector (list in `config.py`),
  sized by market cap and colored by daily % change, with sector drill-down,
  sector ETF performance, and a sortable table of every stock.
- **Movers** — top gainers / losers / most active, up to 50 rows, with market
  cap, 52-week range, and forward P/E.
- **M&A** — potential deals (talks, bids, sale processes) and announced deals
  (agreed / completed / terminated), filterable by stage and lookback.
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

## Data providers

Everything above runs out of the box on **free, no-key providers** —
mostly `yfinance`, plus `sec` for ticker search, CNN for Fear & Greed, and
Google News search RSS for M&A headlines. No signup required. (The heatmap
calls `yfinance` directly rather than through OpenBB for its one batched price
download — ~2s instead of ~10s for ~65 symbols.)

Some workflows are stronger with a free-tier key from
[Financial Modeling Prep](https://financialmodelingprep.com) (`OPENBB_FMP_API_KEY`
in `.env`):
- True peer lookup (`equity.compare.peers`) instead of the sector/industry
  screener fallback used by the Comps page.
- Full ratios statements and a richer screener (dividend filters, more industries).

See `.env.example` for all supported provider keys — OpenBB auto-detects any
`OPENBB_<PROVIDER>_API_KEY` env var.

## Deploying to Render (make it a public website)

The repo is already set up for this: `requirements.txt` includes `gunicorn`,
`render.yaml` declares the service, and `runtime.txt` pins the Python
version. Render builds and deploys straight from a GitHub repo, so:

**1. Push this repo to GitHub** (skip if already done):
```bash
# create a new empty repo at https://github.com/new first, then:
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

**2. Deploy on Render:**
1. Go to [render.com](https://render.com) and sign up / log in (GitHub login is easiest).
2. Click **New +** → **Blueprint**.
3. Connect your GitHub account if prompted, then select this repo.
4. Render reads `render.yaml` automatically and shows one service,
   `finance-research-dashboard`, on the **Free** plan. Click **Apply**.
5. Wait for the build+deploy log to finish (a few minutes the first time).
6. Your site is live at `https://finance-research-dashboard-XXXX.onrender.com`
   (Render assigns the exact subdomain — shown at the top of the service page).

**That's it** — no server to manage. Every time you `git push` to `main`,
Render automatically rebuilds and redeploys.

### Things to know about the free plan
- **Cold starts**: the free tier spins the service down after ~15 minutes of
  no traffic. The next visitor waits ~30-60s for it to wake up — normal, not
  a bug.
- **Single worker by design**: `render.yaml` runs one gunicorn worker with
  multiple threads, not multiple workers. This is intentional — the app's
  in-memory cache (`data/cache.py`) is a plain Python dict shared across
  threads in one process; running multiple worker *processes* would give
  each its own cache and multiply the load on yfinance's free, unofficial
  API. Don't raise `--workers` above 1 without also moving the cache to
  something shared (e.g. Redis).
- **Public + no login** (as configured): anyone with the URL can load it,
  and every open tab polls the live pages every 30s. The shared cache keeps
  this cheap even with several visitors, but if you ever share the link
  widely, consider raising `DASHBOARD_REFRESH_MS` in the Render dashboard's
  environment variables to reduce load.
- To use a custom domain later: Render's dashboard → your service → **Settings**
  → **Custom Domains** → follow the DNS instructions there.

## Project layout

```
config.py        # env-driven settings, cache TTLs, index/commodity/sector lists
data/             # pure-Python data layer wrapping OpenBB — no Dash imports.
                  # Reusable as-is by a future desktop shell.
  cache.py        # tiny TTL cache decorator
  errors.py       # DataUnavailableError — caught by pages to render inline errors
  company.py      # quote, profile, historical prices, statements, estimates
  comps.py        # peer suggestion + multiples table
  market.py       # indices, movers, sector performance, heatmap, screener
  commodities.py  # futures price/volume
  news.py         # company & market news, M&A headlines (Google News RSS)
  sentiment.py    # CNN Fear & Greed Index (unofficial endpoint)
ui/               # Dash-specific presentation layer
  theme.py        # color tokens for Plotly figures (dark terminal palette)
  components.py   # stat cards, delta badges, charts, tables
  navbar.py       # top nav + global ticker search
pages/            # one module per route, via dash.register_page
app.py            # Dash app instance + layout shell
run.py            # entry point (`python run.py`)
assets/style.css  # dark theme, auto-loaded by Dash
```

## Becoming a desktop app later

The data layer (`data/`) has zero Dash dependencies, and `app.py` exposes the
underlying Flask server as `app.server`. To wrap this as a desktop app without
restructuring anything:

1. `pip install pywebview`
2. Run the existing Dash server (`app.run(...)`) in a background thread.
3. Open a `webview.create_window(...)` pointing at `http://127.0.0.1:8050`.

Because `data/` never imports Dash, it can also be reused directly by a native
UI (e.g. the `PySide6` toolkit already in this project's `.venv`) if you'd
rather build native widgets than embed the web view.

## Notes & limitations

- The Fear & Greed Index uses CNN's unofficial public JSON endpoint — it isn't
  part of OpenBB and can change or rate-limit without notice.
- The free-tier `equity.screener` (yfinance) supports sector/industry/market
  cap/price/beta/volume filters but not dividend filters — those need FMP.
- Peer suggestions on the Comps page are sector/industry-based, not a curated
  "true peers" list — edit the ticker list freely; it's meant as a starting
  point.
- M&A headlines come from Google News' public search RSS — unofficial, like
  the CNN endpoint. Deal-stage tags (Bid, Talks, Agreed, …) are inferred from
  headline wording, so treat them as a guide rather than a classification.
- The heatmap's first load after a server start takes ~10s while it fetches
  prices and market caps; after that it's served from cache.
