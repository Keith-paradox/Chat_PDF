from duckduckgo_search import DDGS
import logging

def search_web(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, safesearch="Moderate", max_results=3))
            if results:
                return results[0]["body"]
        return "No relevant web search result found."
    except Exception as e:
        logging.exception("Web search failed")
        return "Web search error."
