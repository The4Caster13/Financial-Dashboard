"""News — company-specific and general market headlines."""
from __future__ import annotations

import pandas as pd
from openbb import obb

from config import CACHE_TTL_NEWS, DEFAULT_PROVIDER
from data.cache import ttl_cache
from data.errors import DataUnavailableError


@ttl_cache(CACHE_TTL_NEWS)
def get_company_news(symbol: str, limit: int = 15) -> pd.DataFrame:
    try:
        r = obb.news.company(symbol=symbol, provider=DEFAULT_PROVIDER, limit=limit)
        df = r.to_df()
        if df.empty:
            raise DataUnavailableError(f"No news found for '{symbol}'.")
        df = df.reset_index()
        if "date" in df.columns:
            df = df.sort_values("date", ascending=False)
        return df
    except DataUnavailableError:
        raise
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch news for '{symbol}': {exc}") from exc


@ttl_cache(CACHE_TTL_NEWS)
def get_world_news(limit: int = 15) -> pd.DataFrame:
    """General market news. `obb.news.world` needs a paid provider (benzinga/fmp/
    intrinio/tiingo), so on the free tier we use SPY's news feed as a broad-market
    stand-in — yfinance is the only no-key provider for the news endpoints."""
    try:
        return get_company_news("SPY", limit=limit)
    except DataUnavailableError as exc:
        raise DataUnavailableError(f"Couldn't fetch market news: {exc}") from exc
