from __future__ import annotations

import datetime as dt
import threading

import pandas as pd
import yfinance as yf
from openbb import obb

from config import (
    CACHE_TTL_FUNDAMENTALS,
    CACHE_TTL_HISTORICAL,
    CACHE_TTL_INTRADAY,
    CACHE_TTL_QUOTE,
    CACHE_TTL_SCREENER,
    DEFAULT_PROVIDER,
    HEATMAP_UNIVERSE,
    MAJOR_INDICES,
)
from data.cache import ttl_cache
from data.errors import DataUnavailableError
from data.pricing import get_last_and_change

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


@ttl_cache(CACHE_TTL_FUNDAMENTALS)
def _get_profiles(symbols: tuple[str, ...]) -> pd.DataFrame:
    df = obb.equity.profile(symbol=",".join(symbols), provider=DEFAULT_PROVIDER).to_df()
    with_cap = df["market_cap"].notna().sum()
    if with_cap < 0.9 * len(symbols):
        raise DataUnavailableError(f"Market caps incomplete ({with_cap}/{len(symbols)}).")
    return df


_YF_DOWNLOAD_LOCK = threading.Lock()


def _download_closes(symbols: list[str], start: str) -> pd.DataFrame:
    with _YF_DOWNLOAD_LOCK:
        prices = yf.download(symbols, start=start, progress=False, threads=True, auto_adjust=False)
    if prices.empty:
        raise DataUnavailableError("No heatmap prices returned.")
    return prices["Close"]


@ttl_cache(CACHE_TTL_INTRADAY)
def get_heatmap_data() -> pd.DataFrame:
    stocks = [s for group in HEATMAP_UNIVERSE.values() for s in group]
    etfs = list(HEATMAP_UNIVERSE)
    start = (dt.date.today() - dt.timedelta(days=10)).isoformat()
    try:
        closes = _download_closes(stocks + etfs, start)
    except DataUnavailableError:
        raise
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch heatmap prices: {exc}") from exc

    def last_and_pct(sym: str) -> tuple[float | None, float | None]:
        series = closes[sym].dropna()
        last = float(series.iloc[-1]) if len(series) else None
        prev = float(series.iloc[-2]) if len(series) >= 2 else None
        return last, ((last / prev - 1) * 100 if last is not None and prev else None)

    try:
        profiles = _get_profiles(tuple(stocks)).set_index("symbol")
    except Exception:
        profiles = pd.DataFrame(columns=["name", "market_cap"])

    rows = []
    for etf, group in HEATMAP_UNIVERSE.items():
        sector_pct = last_and_pct(etf)[1]
        for sym in group:
            last, pct = last_and_pct(sym)
            cap = profiles["market_cap"].get(sym)
            rows.append({
                "symbol": sym,
                "name": profiles["name"].get(sym, sym),
                "sector_etf": etf,
                "sector": SECTOR_ETFS[etf],
                "sector_pct": sector_pct,
                "market_cap": float(cap) if pd.notna(cap) else None,
                "last": last,
                "pct_change": pct,
            })
    return pd.DataFrame(rows)


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
