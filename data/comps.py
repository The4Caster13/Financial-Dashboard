"""Comparable company analysis — peer discovery and side-by-side multiples."""
from __future__ import annotations

import pandas as pd
from openbb import obb

from config import CACHE_TTL_FUNDAMENTALS, DEFAULT_PROVIDER
from data.cache import ttl_cache
from data.errors import DataUnavailableError

METRIC_LABELS = {
    "market_cap": "Market Cap",
    "pe_ratio": "P/E (TTM)",
    "forward_pe": "Forward P/E",
    "peg_ratio": "PEG Ratio",
    "price_to_book": "P/B",
    "enterprise_to_ebitda": "EV/EBITDA",
    "enterprise_to_revenue": "EV/Revenue",
    "revenue_growth": "Revenue Growth",
    "earnings_growth": "Earnings Growth",
    "gross_margin": "Gross Margin",
    "operating_margin": "Operating Margin",
    "profit_margin": "Net Margin",
    "return_on_equity": "ROE",
    "return_on_assets": "ROA",
    "debt_to_equity": "Debt/Equity",
    "dividend_yield": "Dividend Yield",
    "beta": "Beta",
}

# Display kind per metric label, for ui.components.format_number. yfinance's
# `metrics.dividend_yield` is already in percent units (an upstream
# inconsistency vs. the other "normalized percent" fields) — see
# ui/components.py's `percent_raw` kind.
METRIC_FORMATS = {
    "Market Cap": "compact",
    "Revenue Growth": "percent",
    "Earnings Growth": "percent",
    "Gross Margin": "percent",
    "Operating Margin": "percent",
    "Net Margin": "percent",
    "ROE": "percent",
    "ROA": "percent",
    "Dividend Yield": "percent_raw",
}


@ttl_cache(CACHE_TTL_FUNDAMENTALS)
def suggest_peers(symbol: str, limit: int = 8) -> list[str]:
    """Suggest a peer set by screening the target's own sector/industry.
    Best-effort — the yfinance screener needs a sector/industry lookup first."""
    try:
        profile_r = obb.equity.profile(symbol=symbol, provider=DEFAULT_PROVIDER)
        profile = profile_r.to_df().iloc[0].to_dict()
        sector = profile.get("sector")
        industry_raw = profile.get("industry_category") or profile.get("industry")
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't determine sector/industry for '{symbol}': {exc}") from exc

    industry_slug = _slugify_industry(industry_raw)
    sector_slug = _slugify_sector(sector)

    try:
        kwargs = {"provider": "yfinance"}
        if sector_slug:
            kwargs["sector"] = sector_slug
        if industry_slug:
            kwargs["industry"] = industry_slug
        r = obb.equity.screener(**kwargs)
        df = r.to_df()
    except Exception:
        df = pd.DataFrame()

    peers = [s for s in df["symbol"].tolist() if s.upper() != symbol.upper()] if not df.empty else []
    return peers[:limit]


def _slugify_sector(sector: str | None) -> str | None:
    if not sector:
        return None
    return sector.strip().lower().replace(" ", "_").replace("-", "_")


def _slugify_industry(industry: str | None) -> str | None:
    if not industry:
        return None
    return industry.strip().lower().replace(" ", "_").replace("-", "_").replace("&", "")


@ttl_cache(CACHE_TTL_FUNDAMENTALS)
def get_comps_table(symbols: tuple[str, ...]) -> pd.DataFrame:
    """Multiples comparison table for a target + peer symbols. Index is the
    metric key; columns are tickers, first column is always the target."""
    if not symbols:
        raise DataUnavailableError("No symbols provided for comps.")
    try:
        r = obb.equity.fundamental.metrics(symbol=",".join(symbols), provider=DEFAULT_PROVIDER)
        df = r.to_df()
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch comps metrics: {exc}") from exc

    if df.empty:
        raise DataUnavailableError("No comps metrics returned.")

    df = df.set_index("symbol").T
    ordered_cols = [s for s in symbols if s in df.columns] + [c for c in df.columns if c not in symbols]
    df = df[ordered_cols]
    keep = [k for k in METRIC_LABELS if k in df.index]
    df = df.loc[keep]
    df.index = [METRIC_LABELS[k] for k in keep]
    return df
