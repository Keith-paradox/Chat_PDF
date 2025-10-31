import logging
import httpx
from app.config import settings

def search_web(query: str) -> str:
    """Use SearchAPI.io (Google engine) to fetch fresh results.

    - Restrict to last day using tbs=qdr:d
    - Return compact digest: Title, URL, Snippet, Date if present
    """
    try:
        api_key = settings.searchapi_api_key
        if not api_key:
            return "Web search error: missing SEARCHAPI_API_KEY."
        params = {
            "api_key": api_key,
            "engine": "google",
            "q": query,
            "num": 8,
            "tbs": "qdr:d",  # last day
            "hl": "en",
            "safe": "active",
        }
        resp = httpx.get("https://www.searchapi.io/api/v1/search", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        items = []
        # Prefer news_results if present and fresh
        news = data.get("news_results") or []
        for r in news:
            title = r.get("title") or "(no title)"
            href = r.get("link") or r.get("url") or ""
            date = r.get("date") or r.get("age") or ""
            snippet = r.get("snippet") or r.get("excerpt") or ""
            source = r.get("source") or ""
            items.append(f"- Title: {title}\n  URL: {href}\n  Source: {source}\n  Date: {date}\n  Snippet: {snippet}")
        # Fallback to organic_results
        if not items:
            for r in data.get("organic_results", []):
                title = r.get("title") or "(no title)"
                href = r.get("link") or ""
                snippet = r.get("snippet") or ""
                date = r.get("date") or ""
                items.append(f"- Title: {title}\n  URL: {href}\n  Date: {date}\n  Snippet: {snippet}")
        if not items:
            return "No relevant web search result found."
        return "\n".join(items)
    except Exception:
        logging.exception("Web search failed")
        return "Web search error."
