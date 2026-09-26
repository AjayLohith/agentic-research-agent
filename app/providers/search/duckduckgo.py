import logging
from typing import List
from urllib.parse import parse_qs, unquote, urlparse
import httpx
from bs4 import BeautifulSoup

from app.providers.search.base import SearchProvider
from app.models.tool import SearchResponse, SearchResult
from app.exceptions import ProviderError

logger = logging.getLogger("agentic_research.duckduckgo")


class DuckDuckGoSearchProvider(SearchProvider):
    """
    Keyless web search provider using DuckDuckGo Lite as a free zero-setup option.
    """

    def __init__(self, timeout: float = 12.0):
        super().__init__()
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
            timeout=self.timeout
        )

    async def _execute_search(self, query: str, max_results: int) -> SearchResponse:
        url = "https://lite.duckduckgo.com/lite/"
        try:
            resp = await self.client.post(url, data={"q": query})
            if resp.status_code != 200:
                raise ProviderError(f"DuckDuckGo returned HTTP {resp.status_code}")

            soup = BeautifulSoup(resp.text, "html.parser")
            results: List[SearchResult] = []
            link_tags = soup.select(".result-link")
            snippet_tags = soup.select(".result-snippet")

            for i, link in enumerate(link_tags):
                if len(results) >= max_results:
                    break

                raw_href = link.get("href", "")
                actual_url = self._extract_url(raw_href)
                if not actual_url or not actual_url.startswith("http"):
                    continue

                title = link.get_text(strip=True) or "Web Source"
                snippet = snippet_tags[i].get_text(strip=True) if i < len(snippet_tags) else ""
                parsed_domain = urlparse(actual_url).netloc

                results.append(
                    SearchResult(
                        title=title,
                        url=actual_url,
                        snippet=snippet,
                        source=parsed_domain or "duckduckgo",
                        relevance=max(0.6, round(0.95 - (len(results) * 0.05), 2))
                    )
                )

            return SearchResponse(query=query, results=results, total_results=len(results))

        except Exception as e:
            raise ProviderError(f"DuckDuckGo search failed for '{query}': {e}") from e

    def _extract_url(self, raw_url: str) -> str:
        if not raw_url:
            return ""
        if "uddg=" in raw_url:
            try:
                parsed = urlparse(raw_url)
                params = parse_qs(parsed.query)
                if "uddg" in params:
                    return unquote(params["uddg"][0])
            except Exception:
                pass
        if raw_url.startswith("//"):
            return f"https:{raw_url}"
        return raw_url

    async def close(self):
        await self.client.aclose()
