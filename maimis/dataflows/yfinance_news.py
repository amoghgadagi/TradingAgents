from __future__ import annotations

import yfinance as yf


def fetch_news(symbol: str, limit: int = 50) -> list[dict]:
    ticker = yf.Ticker(symbol)
    raw = ticker.news or []
    out: list[dict] = []
    for item in raw[:limit]:
        content = item.get("content") or {}
        title = content.get("title") or item.get("title") or ""
        if not title:
            continue
        out.append(
            {
                "title": title,
                "provider": content.get("provider") or item.get("publisher") or "yahoo",
                "link": content.get("canonicalUrl", {}).get("url") or item.get("link") or "",
                "published_at": content.get("pubDate") or item.get("providerPublishTime") or "",
                "summary": content.get("summary") or "",
            }
        )
    return out
