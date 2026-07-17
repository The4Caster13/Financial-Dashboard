"""Company snapshot & financials — profile, quote, price history, statements, estimates."""
from __future__ import annotations

import pandas as pd
from openbb import obb

from config import CACHE_TTL_FUNDAMENTALS, CACHE_TTL_HISTORICAL, CACHE_TTL_QUOTE, DEFAULT_PROVIDER
from data.cache import ttl_cache
from data.errors import DataUnavailableError


def _to_df(obbject) -> pd.DataFrame:
    df = obbject.to_df()
    if df is None or df.empty:
        raise DataUnavailableError("No data returned.")
    return df


@ttl_cache(CACHE_TTL_QUOTE)
def get_quote(symbol: str) -> dict:
    try:
        r = obb.equity.price.quote(symbol=symbol, provider=DEFAULT_PROVIDER)
        df = _to_df(r)
        return df.iloc[0].to_dict()
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch a quote for '{symbol}': {exc}") from exc


@ttl_cache(CACHE_TTL_FUNDAMENTALS)
def get_profile(symbol: str) -> dict:
    try:
        r = obb.equity.profile(symbol=symbol, provider=DEFAULT_PROVIDER)
        df = _to_df(r)
        return df.iloc[0].to_dict()
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch a profile for '{symbol}': {exc}") from exc


@ttl_cache(CACHE_TTL_HISTORICAL)
def get_historical_prices(symbol: str, start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
    try:
        r = obb.equity.price.historical(
            symbol=symbol, provider=DEFAULT_PROVIDER, start_date=start_date, end_date=end_date
        )
        return _to_df(r)
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch price history for '{symbol}': {exc}") from exc


@ttl_cache(CACHE_TTL_FUNDAMENTALS)
def get_metrics(symbol: str) -> dict:
    """Key valuation/profitability/leverage metrics — the free-tier stand-in for
    a full ratios statement (which requires a paid provider)."""
    try:
        r = obb.equity.fundamental.metrics(symbol=symbol, provider=DEFAULT_PROVIDER)
        df = _to_df(r)
        return df.iloc[0].to_dict()
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch metrics for '{symbol}': {exc}") from exc


@ttl_cache(CACHE_TTL_FUNDAMENTALS)
def get_income_statement(symbol: str, limit: int = 5) -> pd.DataFrame:
    try:
        r = obb.equity.fundamental.income(symbol=symbol, provider=DEFAULT_PROVIDER, limit=limit)
        return _to_df(r)
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch the income statement for '{symbol}': {exc}") from exc


@ttl_cache(CACHE_TTL_FUNDAMENTALS)
def get_balance_sheet(symbol: str, limit: int = 5) -> pd.DataFrame:
    try:
        r = obb.equity.fundamental.balance(symbol=symbol, provider=DEFAULT_PROVIDER, limit=limit)
        return _to_df(r)
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch the balance sheet for '{symbol}': {exc}") from exc


@ttl_cache(CACHE_TTL_FUNDAMENTALS)
def get_cash_flow(symbol: str, limit: int = 5) -> pd.DataFrame:
    try:
        r = obb.equity.fundamental.cash(symbol=symbol, provider=DEFAULT_PROVIDER, limit=limit)
        return _to_df(r)
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch the cash flow statement for '{symbol}': {exc}") from exc


@ttl_cache(CACHE_TTL_FUNDAMENTALS)
def get_analyst_consensus(symbol: str) -> dict:
    try:
        r = obb.equity.estimates.consensus(symbol=symbol, provider=DEFAULT_PROVIDER)
        df = _to_df(r)
        return df.iloc[0].to_dict()
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch analyst estimates for '{symbol}': {exc}") from exc


def search_symbol(query: str, limit: int = 10) -> pd.DataFrame:
    """Symbol search. Uses the SEC provider — it requires no API key, unlike
    the yfinance extension which doesn't implement this endpoint."""
    try:
        r = obb.equity.search(query=query, provider="sec")
        df = _to_df(r)
        return df.head(limit)
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't search for '{query}': {exc}") from exc
