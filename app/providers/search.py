from abc import ABC, abstractmethod
from typing import List
from urllib.parse import parse_qs, unquote, urlparse
import httpx
from bs4 import BeautifulSoup

from app.models.tool import SearchResponse, SearchResult


class SearchProvider(ABC):
    """Abstract interface for pluggable search engines."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> SearchResponse:
        """Execute a web search query and return normalized results."""
        pass


class DuckDuckGoSearchProvider(SearchProvider):
    """
    Public, keyless web search provider using DuckDuckGo Lite.
    Robust, real-time public access without requiring external API keys.
    """

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
            timeout=self.timeout
        )

    async def search(self, query: str, max_results: int = 5) -> SearchResponse:
        url = "https://lite.duckduckgo.com/lite/"
        try:
            resp = await self.client.post(url, data={"q": query})
            if resp.status_code != 200:
                return SearchResponse(query=query, results=[], total_results=0)

            soup = BeautifulSoup(resp.text, "html.parser")
            results: List[SearchResult] = []

            # DuckDuckGo Lite renders results in table rows
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
                snippet = ""
                if i < len(snippet_tags):
                    snippet = snippet_tags[i].get_text(strip=True)

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

            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results)
            )

        except Exception as e:
            # Propagate or return empty with error handling
            raise RuntimeError(f"DuckDuckGo search error for '{query}': {str(e)}") from e

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


class TavilySearchProvider(SearchProvider):
    """Search provider utilizing Tavily Search API if an API key is configured."""

    def __init__(self, api_key: str, timeout: float = 10.0):
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def search(self, query: str, max_results: int = 5) -> SearchResponse:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False
        }
        resp = await self.client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=urlparse(item.get("url", "")).netloc or "tavily",
                    relevance=float(item.get("score", 0.85))
                )
            )
        return SearchResponse(query=query, results=results, total_results=len(results))

    async def close(self):
        await self.client.aclose()


class MockSearchProvider(SearchProvider):
    """
    Deterministic mock search provider for unit tests, offline demos, and CI.
    Generates realistic, domain-relevant fixtures based on the input query keywords.
    """

    async def search(self, query: str, max_results: int = 5) -> SearchResponse:
        q_lower = query.lower()
        results: List[SearchResult] = []

        if "agent" in q_lower or "framework" in q_lower:
            results = [
                SearchResult(
                    title="LangGraph: Building Stateful Multi-Agent Applications",
                    url="https://docs.langchain.com/langgraph/overview",
                    snippet="LangGraph is a library for building stateful, multi-actor applications with LLMs, extending LangChain with cyclicity and fine-grained agent state management.",
                    source="docs.langchain.com",
                    relevance=0.96
                ),
                SearchResult(
                    title="CrewAI Documentation - Multi-Agent Orchestration",
                    url="https://docs.crewai.com/introduction",
                    snippet="CrewAI is an open-source framework for orchestrating role-playing autonomous AI agents that collaborate as a cohesive crew to solve complex tasks.",
                    source="docs.crewai.com",
                    relevance=0.92
                ),
                SearchResult(
                    title="Microsoft AutoGen: Multi-Agent Conversation Framework",
                    url="https://microsoft.github.io/autogen/docs/Getting-Started",
                    snippet="AutoGen is a framework that enables the development of LLM applications using multiple conversational agents that can communicate to solve tasks.",
                    source="microsoft.github.io",
                    relevance=0.88
                ),
                SearchResult(
                    title="AI Agent Frameworks Comparison 2026",
                    url="https://techcrunch.com/2026/01/ai-agent-frameworks-landscape",
                    snippet="A comprehensive breakdown of enterprise AI agent architectures, memory management, tool execution protocols, and production deployment patterns.",
                    source="techcrunch.com",
                    relevance=0.82
                )
            ]
        elif "fastapi" in q_lower or "spring" in q_lower or "backend" in q_lower:
            results = [
                SearchResult(
                    title="FastAPI: High Performance Modern Python Web Framework",
                    url="https://fastapi.tiangolo.com/",
                    snippet="FastAPI is a modern, fast (high-performance) web framework for building APIs with Python based on standard Python type hints and Starlette.",
                    source="fastapi.tiangolo.com",
                    relevance=0.95
                ),
                SearchResult(
                    title="Spring Boot Overview and Enterprise Architecture",
                    url="https://spring.io/projects/spring-boot",
                    snippet="Spring Boot makes it easy to create stand-alone, production-grade Spring based Applications that you can just run with enterprise maturity.",
                    source="spring.io",
                    relevance=0.93
                ),
                SearchResult(
                    title="FastAPI vs Spring Boot: Performance and Productivity Comparison",
                    url="https://infoworld.com/article/fastapi-vs-spring-boot-architecture",
                    snippet="Benchmarking Python async vs Java virtual threads for enterprise microservices, memory consumption, and developer velocity.",
                    source="infoworld.com",
                    relevance=0.85
                )
            ]
        else:
            # Generic fallback mock results for arbitrary topics
            clean_term = query.replace('"', '').strip()
            results = [
                SearchResult(
                    title=f"Authoritative Overview of {clean_term}",
                    url=f"https://docs.example.org/topics/{clean_term.replace(' ', '-').lower()}",
                    snippet=f"Detailed documentation, architectural overview, and core specifications regarding {clean_term}.",
                    source="docs.example.org",
                    relevance=0.90
                ),
                SearchResult(
                    title=f"Industry Trends and Analysis: {clean_term}",
                    url=f"https://techcrunch.com/analysis/{clean_term.replace(' ', '-').lower()}",
                    snippet=f"Current industry benchmarks, adoption trends, and comparative metrics for {clean_term}.",
                    source="techcrunch.com",
                    relevance=0.84
                )
            ]

        return SearchResponse(
            query=query,
            results=results[:max_results],
            total_results=len(results[:max_results])
        )


def get_search_provider(
    provider_name: str,
    tavily_key: str | None = None,
    mock_mode: bool = False
) -> SearchProvider:
    """Factory method to instantiate the requested SearchProvider."""
    if mock_mode or provider_name.lower() == "mock":
        return MockSearchProvider()
    if provider_name.lower() == "tavily" and tavily_key:
        return TavilySearchProvider(api_key=tavily_key)
    return DuckDuckGoSearchProvider()
