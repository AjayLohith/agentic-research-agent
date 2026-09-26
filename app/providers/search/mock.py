from typing import List
from app.providers.search.base import SearchProvider
from app.models.tool import SearchResponse, SearchResult


class MockSearchProvider(SearchProvider):
    """
    Deterministic search provider for unit testing, offline demonstrations, and CI.
    """

    async def _execute_search(self, query: str, max_results: int = 5) -> SearchResponse:
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
                )
            ]
        elif "fastapi" in q_lower or "spring" in q_lower:
            results = [
                SearchResult(
                    title="FastAPI: High Performance Modern Python Web Framework",
                    url="https://fastapi.tiangolo.com/",
                    snippet="FastAPI is a modern, fast (high-performance) web framework for building APIs with Python based on standard Python type hints.",
                    source="fastapi.tiangolo.com",
                    relevance=0.95
                ),
                SearchResult(
                    title="Spring Boot Overview and Enterprise Architecture",
                    url="https://spring.io/projects/spring-boot",
                    snippet="Spring Boot makes it easy to create stand-alone, production-grade Spring based Applications with enterprise maturity.",
                    source="spring.io",
                    relevance=0.93
                )
            ]
        else:
            clean_term = query.replace('"', '').strip()
            results = [
                SearchResult(
                    title=f"Technical Overview of {clean_term}",
                    url=f"https://docs.example.org/topics/{clean_term.replace(' ', '-').lower()}",
                    snippet=f"Detailed documentation and architectural overview regarding {clean_term}.",
                    source="docs.example.org",
                    relevance=0.90
                )
            ]

        return SearchResponse(query=query, results=results[:max_results], total_results=len(results[:max_results]))
