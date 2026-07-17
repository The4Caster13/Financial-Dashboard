"""Market overview — indices, movers, sector performance, and the stock screener."""
from __future__ import annotations

import pandas as pd
from openbb import obb

from config import CACHE_TTL_HISTORICAL, CACHE_TTL_QUOTE, CACHE_TTL_SCREENER, DEFAULT_PROVIDER, MAJOR_INDICES
from data.cache import ttl_cache
from data.errors import DataUnavailableError
from data.pricing import get_last_and_change

# Sector SPDR ETFs used as a liquid, no-key-required proxy for sector performance.
SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Health Care",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLU": "Utilities",
    "XLC": "Communication Services",
}


@ttl_cache(CACHE_TTL_QUOTE)
def get_index_snapshot() -> pd.DataFrame:
    rows = []
    for sym, label in MAJOR_INDICES.items():
        pc = get_last_and_change(sym)
        rows.append({"symbol": sym, "label": label, "last": pc["last"], "change": pc["change"],
                      "pct_change": pc["pct_change"]})
    return pd.DataFrame(rows)


@ttl_cache(CACHE_TTL_HISTORICAL)
def get_index_history(symbol: str, start_date: str | None = None) -> pd.DataFrame:
    try:
        r = obb.equity.price.historical(symbol=symbol, provider=DEFAULT_PROVIDER, start_date=start_date)
        df = r.to_df()
        if df.empty:
            raise DataUnavailableError(f"No history for '{symbol}'.")
        return df
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch history for '{symbol}': {exc}") from exc


@ttl_cache(CACHE_TTL_SCREENER)
def get_movers(category: str = "active", limit: int = 10) -> pd.DataFrame:
    fn = {"gainers": obb.equity.discovery.gainers, "losers": obb.equity.discovery.losers,
          "active": obb.equity.discovery.active}.get(category)
    if fn is None:
        raise DataUnavailableError(f"Unknown movers category '{category}'.")
    try:
        r = fn(provider=DEFAULT_PROVIDER)
        df = r.to_df()
        return df.head(limit)
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch '{category}' movers: {exc}") from exc


@ttl_cache(CACHE_TTL_QUOTE)
def get_sector_performance() -> pd.DataFrame:
    rows = []
    for sym, label in SECTOR_ETFS.items():
        pc = get_last_and_change(sym)
        rows.append({"symbol": sym, "sector": label, "pct_change": pc["pct_change"]})
    return pd.DataFrame(rows).sort_values("pct_change", ascending=False, na_position="last")


@ttl_cache(CACHE_TTL_SCREENER)
def run_screener(
    sector: str | None = None,
    industry: str | None = None,
    mktcap_min: float | None = None,
    mktcap_max: float | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    beta_min: float | None = None,
    beta_max: float | None = None,
    volume_min: float | None = None,
) -> pd.DataFrame:
    kwargs = {
        "provider": "yfinance",
        "sector": sector,
        "industry": industry,
        "mktcap_min": mktcap_min,
        "mktcap_max": mktcap_max,
        "price_min": price_min,
        "price_max": price_max,
        "beta_min": beta_min,
        "beta_max": beta_max,
        "volume_min": volume_min,
    }
    kwargs = {k: v for k, v in kwargs.items() if v not in (None, "")}
    try:
        r = obb.equity.screener(**kwargs)
        return r.to_df()
    except Exception as exc:
        raise DataUnavailableError(f"Screener query failed: {exc}") from exc
