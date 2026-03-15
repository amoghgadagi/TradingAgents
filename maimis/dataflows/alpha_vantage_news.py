from __future__ import annotations

from .alpha_vantage_common import av_get


def fetch_news(symbol: str, api_key: str, limit: int = 50) -> list[dict]:
    if not api_key:
        raise ValueError("Missing ALPHA_VANTAGE_API_KEY")

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": symbol,
        "sort": "LATEST",
        "limit": limit,
        "apikey": api_key,
    }
    data = av_get(params)
    if "Note" in data or "Information" in data:
        raise RuntimeError(data.get("Note") or data.get("Information"))

    feed = data.get("feed", [])
    return [
        {
            "title": item.get("title", ""),
            "provider": item.get("source", "alpha_vantage"),
            "link": item.get("url", ""),
            "published_at": item.get("time_published", ""),
            "summary": item.get("summary", ""),
        }
        for item in feed
        if item.get("title")
    ]
