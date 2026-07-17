"""CNN Fear & Greed Index — not part of the OpenBB extension set, so this hits
CNN's unofficial public JSON endpoint directly. Best-effort: the endpoint is
undocumented and can change or rate-limit without notice."""
from __future__ import annotations

import requests

from config import CACHE_TTL_SENTIMENT
from data.cache import ttl_cache
from data.errors import DataUnavailableError

_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://www.cnn.com/markets/fear-and-greed",
    "Accept": "application/json",
}


@ttl_cache(CACHE_TTL_SENTIMENT)
def get_fear_greed() -> dict:
    try:
        resp = requests.get(_URL, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data["fear_and_greed"]
        return {
            "score": round(current["score"], 1),
            "rating": current["rating"],
            "timestamp": current["timestamp"],
            "previous_close": round(current["previous_close"], 1),
            "previous_week": round(current["previous_1_week"], 1),
            "previous_month": round(current["previous_1_month"], 1),
            "previous_year": round(current["previous_1_year"], 1),
            "historical": data.get("fear_and_greed_historical", {}).get("data", []),
        }
    except Exception as exc:
        raise DataUnavailableError(f"Couldn't fetch the Fear & Greed Index: {exc}") from exc
