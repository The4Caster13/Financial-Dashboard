"""Commodities pricing & volume — via liquid front-month futures tickers (yfinance)."""
from __future__ import annotations

import pandas as pd
from openbb import obb

from config import CACHE_TTL_HISTORICAL, CACHE_TTL_QUOTE, COMMODITIES, DEFAULT_PROVIDER
from data.cache import ttl_cache
from data.errors import DataUnavailableError
from data.pricing import get_last_and_change


@ttl_cache(CACHE_TTL_QUOTE)
def get_commodities_snapshot() -> pd.DataFrame:
    rows = []
    for sym, label in COMMODITIES.items():
        pc = get_last_and_change(sym)
        rows.append({
            "symbol": sym,
            "label": label,
            "last": pc["last"],
            "change": pc["change"],
            "pct_change": pc["pct_change"],
            "volume": pc["volume"],
        })
    return pd.DataFrame(rows)


@ttl_cache(CACHE_TTL_HISTORICAL)
def get_commodity_history(symbol: str, start_date: str | None = None) -> pd.DataFrame:
    try:
        r = obb.equity.price.historical(symbol=symbol, provider=DEFAULT_PROVIDER, start_date=start_date)
        df = r.to_df()
        if df.empty:
            raise DataUnavailableError(f"No history for '{symbol}'.")
        return df
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch history for '{symbol}': {exc}") from exc
