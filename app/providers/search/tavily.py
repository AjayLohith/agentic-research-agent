import logging
from urllib.parse import urlparse
import httpx
from app.providers.search.base import SearchProvider
from app.models.tool import SearchResponse, SearchResult
from app.exceptions import ProviderError

logger = logging.getLogger("agentic_research.tavily")


class TavilySearchProvider(SearchProvider):
    """
    Search provider using Tavily's AI-optimized search API (free tier: 1,000 requests/mo).
    """

    def __init__(self, api_key: str, timeout: float = 12.0):
        super().__init__()
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def _execute_search(self, query: str, max_results: int) -> SearchResponse:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False
        }

        try:
            resp = await self.client.post(url, json=payload)
            if resp.status_code == 429:
                raise ProviderError("Tavily search rate limit exceeded (429). Please wait before retrying.")
            if resp.status_code == 401:
                raise ProviderError("Invalid TAVILY_API_KEY. Please verify your credentials in .env.")
            resp.raise_for_status()

            data = resp.json()
            results = []
            for item in data.get("results", []):
                item_url = item.get("url", "")
                results.append(
                    SearchResult(
                        title=item.get("title", "") or "Web Reference",
                        url=item_url,
                        snippet=item.get("content", ""),
                        source=urlparse(item_url).netloc or "tavily",
                        relevance=float(item.get("score", 0.85))
                    )
                )

            return SearchResponse(query=query, results=results, total_results=len(results))

        except httpx.HTTPError as e:
            logger.error(f"Tavily search request failed: {e}")
            raise ProviderError(f"Tavily search failed: {e}") from e

    async def close(self):
        await self.client.aclose()
