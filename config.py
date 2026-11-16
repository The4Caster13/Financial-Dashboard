from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Finance Research Dashboard"

HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.getenv("DASHBOARD_PORT", "8050"))
DEBUG = os.getenv("DASHBOARD_DEBUG", "true").lower() == "true"

REFRESH_INTERVAL_MS = int(os.getenv("DASHBOARD_REFRESH_MS", "30000"))

CACHE_TTL_QUOTE = 30
CACHE_TTL_INTRADAY = 60
CACHE_TTL_HISTORICAL = 60 * 15
CACHE_TTL_FUNDAMENTALS = 60 * 60 * 6
CACHE_TTL_NEWS = 60 * 5
CACHE_TTL_SENTIMENT = 60 * 10
CACHE_TTL_SCREENER = 60 * 10

DEFAULT_PROVIDER = os.getenv("OPENBB_DEFAULT_PROVIDER", "yfinance")

MAJOR_INDICES = {
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "Nasdaq",
    "^RUT": "Russell 2000",
    "^VIX": "VIX",
}

COMMODITIES = {
    "GC=F": "Gold",
    "SI=F": "Silver",
    "CL=F": "Crude Oil (WTI)",
    "BZ=F": "Crude Oil (Brent)",
    "NG=F": "Natural Gas",
    "HG=F": "Copper",
    "ZC=F": "Corn",
    "ZW=F": "Wheat",
}

HEATMAP_UNIVERSE = {
    "XLK": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "PLTR", "AMD", "CSCO", "CRM", "IBM"],
    "XLC": ["GOOGL", "META", "NFLX", "TMUS", "DIS"],
    "XLY": ["AMZN", "TSLA", "HD", "MCD", "BKNG"],
    "XLF": ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS"],
    "XLV": ["LLY", "UNH", "JNJ", "ABBV", "MRK"],
    "XLI": ["GE", "CAT", "RTX", "UBER", "HON"],
    "XLP": ["WMT", "COST", "PG", "KO", "PM"],
    "XLE": ["XOM", "CVX", "COP"],
    "XLU": ["NEE", "SO", "DUK"],
    "XLRE": ["PLD", "AMT", "WELL"],
    "XLB": ["LIN", "SHW", "NEM"],
}

SECTORS = [
    "technology",
    "healthcare",
    "financial_services",
    "consumer_cyclical",
    "consumer_defensive",
    "energy",
    "industrials",
    "basic_materials",
    "real_estate",
    "utilities",
    "communication_services",
]
