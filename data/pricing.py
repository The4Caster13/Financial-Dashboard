"""Shared last-price / day-change helper.

The yfinance `quote` endpoint's bid/ask/last_price fields are unreliable
outside active market hours (often stale or missing) in the OpenBB yfinance
extension. Recent daily closes from the `historical` endpoint are much more
consistent, so snapshot views (indices, sectors, commodities) derive last
price and day-over-day change from the last two daily bars instead."""
from __future__ import annotations

import datetime as dt

from openbb import obb

from config import CACHE_TTL_QUOTE, DEFAULT_PROVIDER
from data.cache import ttl_cache


@ttl_cache(CACHE_TTL_QUOTE)
def get_last_and_change(symbol: str) -> dict:
    start = (dt.date.today() - dt.timedelta(days=10)).isoformat()
    try:
        r = obb.equity.price.historical(symbol=symbol, provider=DEFAULT_PROVIDER, start_date=start)
        df = r.to_df()
        if df is None or df.empty or len(df) < 1:
            return {"last": None, "prev_close": None, "change": None, "pct_change": None, "volume": None}
        last_row = df.iloc[-1]
        prev_close = float(df.iloc[-2]["close"]) if len(df) >= 2 else None
        last = float(last_row["close"])
        change = (last - prev_close) if prev_close else None
        pct_change = (change / prev_close * 100) if change is not None and prev_close else None
        return {
            "last": last,
            "prev_close": prev_close,
            "change": change,
            "pct_change": pct_change,
            "volume": last_row.get("volume"),
        }
    except Exception:
        return {"last": None, "prev_close": None, "change": None, "pct_change": None, "volume": None}
