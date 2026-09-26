from typing import Optional
from app.providers.search.base import SearchProvider
from app.providers.search.tavily import TavilySearchProvider
from app.providers.search.duckduckgo import DuckDuckGoSearchProvider
from app.providers.search.mock import MockSearchProvider


def get_search_provider(
    provider_name: str,
    tavily_key: Optional[str] = None,
    mock_mode: bool = False
) -> SearchProvider:
    """Factory to instantiate the requested SearchProvider."""
    if mock_mode or provider_name.lower() == "mock":
        return MockSearchProvider()
    if provider_name.lower() == "tavily" and tavily_key:
        return TavilySearchProvider(api_key=tavily_key)
    return DuckDuckGoSearchProvider()


__all__ = [
    "SearchProvider",
    "TavilySearchProvider",
    "DuckDuckGoSearchProvider",
    "MockSearchProvider",
    "get_search_provider",
]
