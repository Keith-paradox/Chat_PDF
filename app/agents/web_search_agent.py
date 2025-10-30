from app.core.web_search import search_web

class WebSearchAgent:
    def search(self, query: str) -> str:
        return search_web(query)
