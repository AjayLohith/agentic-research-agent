import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from app.models.tool import SearchResponse, SearchResult

logger = logging.getLogger("agentic_research.search")


class SearchProvider(ABC):
    """
    Abstract search provider with per-session in-memory caching to minimize external API consumption.
    """

    def __init__(self):
        self._cache: Dict[str, SearchResponse] = {}

    def _normalize_key(self, query: str, max_results: int) -> str:
        return f"{query.strip().lower()}::{max_results}"

    async def search(self, query: str, max_results: int = 5) -> SearchResponse:
        key = self._normalize_key(query, max_results)
        if key in self._cache:
            logger.info(f"Returning cached search results for query: '{query}'")
            return self._cache[key]

        response = await self._execute_search(query, max_results)
        self._cache[key] = response
        return response

    @abstractmethod
    async def _execute_search(self, query: str, max_results: int) -> SearchResponse:
        """Concrete search implementation to override."""
        pass

    async def close(self):
        pass
