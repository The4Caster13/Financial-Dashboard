from __future__ import annotations

import datetime as dt
import time

from openbb import obb

from config import CACHE_TTL_QUOTE, DEFAULT_PROVIDER
from data.cache import ttl_cache

_UNAVAILABLE = {"last": None, "prev_close": None, "change": None, "pct_change": None, "volume": None}


def get_last_and_change(symbol: str) -> dict:
    try:
        return _fetch_last_and_change(symbol)
    except Exception:
        return dict(_UNAVAILABLE)


@ttl_cache(CACHE_TTL_QUOTE)
def _fetch_last_and_change(symbol: str) -> dict:
    start = (dt.date.today() - dt.timedelta(days=10)).isoformat()
    try:
        df = obb.equity.price.historical(symbol=symbol, provider=DEFAULT_PROVIDER, start_date=start).to_df()
    except Exception:
        time.sleep(0.5)
        df = obb.equity.price.historical(symbol=symbol, provider=DEFAULT_PROVIDER, start_date=start).to_df()
    if df is None or df.empty:
        raise ValueError(f"No recent prices for '{symbol}'.")

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
