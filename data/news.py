from __future__ import annotations

import datetime as dt
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import pandas as pd
import requests
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
    try:
        return get_company_news("SPY", limit=limit)
    except DataUnavailableError as exc:
        raise DataUnavailableError(f"Couldn't fetch market news: {exc}") from exc


_GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
_MNA_PHRASES = {
    "potential": (
        "merger talks",
        "acquisition talks",
        "in talks to acquire",
        "in talks to buy",
        "explores sale",
        "exploring a sale",
        "takeover bid",
        "buyout offer",
    ),
    "announced": (
        "agrees to acquire",
        "agreed to acquire",
        "agrees to buy",
        "to be acquired",
        "definitive agreement",
        "merger agreement",
        "completes acquisition",
    ),
}

_MNA_STAGES = {
    "potential": (
        ("Bid", re.compile(r"\b(bids?|offers?|hostile|unsolicited|approach)\b", re.IGNORECASE)),
        ("Talks", re.compile(r"\btalks?\b", re.IGNORECASE)),
        ("Exploring sale", re.compile(r"\b(explor\w*|weigh\w*|consider\w*|mull\w*|review|options)\b", re.IGNORECASE)),
    ),
    "announced": (
        ("Terminated", re.compile(r"\b(terminat\w*|scrap\w*|abandon\w*|walks? away|calls? off)\b", re.IGNORECASE)),
        ("Completed", re.compile(r"\b(complet\w*|closes|closed|closing of)\b", re.IGNORECASE)),
        ("Agreed", re.compile(r"\b(agree\w*|definitive|to be acquired|to acquire|to buy|merger agreement)\b",
                              re.IGNORECASE)),
    ),
}
MNA_STAGE_LABELS = {kind: [label for label, _ in stages] for kind, stages in _MNA_STAGES.items()}


def _mna_stage(title: str, kind: str) -> str | None:
    for label, pattern in _MNA_STAGES[kind]:
        if pattern.search(title):
            return label
    return None


@ttl_cache(CACHE_TTL_NEWS)
def get_mna_news(kind: str = "potential", days: int = 3, limit: int = 25) -> pd.DataFrame:
    query = "(" + " OR ".join(f'"{p}"' for p in _MNA_PHRASES[kind]) + f") when:{days}d"
    try:
        resp = requests.get(
            _GOOGLE_NEWS_RSS,
            params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.raise_for_status()
        stories = ET.fromstring(resp.content).findall("./channel/item")
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch M&A news: {exc}") from exc

    rows = []
    for story in stories:
        try:
            date = parsedate_to_datetime(story.findtext("pubDate", ""))
        except (TypeError, ValueError):
            continue
        title = story.findtext("title", "").strip()
        source = story.findtext("source", "").strip()
        if source and title.endswith(f" - {source}"):
            title = title[: -len(source) - 3].rstrip()
        rows.append({"date": date, "title": title, "url": story.findtext("link"),
                     "source": source, "tag": _mna_stage(title, kind)})

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days + 1)
    rows = sorted((r for r in rows if r["date"] >= cutoff), key=lambda r: r["date"], reverse=True)

    deduped, seen = [], set()
    for r in rows:
        key = " ".join(re.findall(r"[a-z0-9]+", r["title"].lower())[:6])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    if not deduped:
        raise DataUnavailableError(f"No {kind} M&A headlines in the last {days} days.")
    return pd.DataFrame(deduped[:limit])
