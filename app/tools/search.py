from typing import Optional
from pydantic import BaseModel, Field

from app.tools.base import BaseTool
from app.models.tool import SearchResponse
from app.providers.search import SearchProvider
from app.tools.failure_injector import failure_injector


class SearchInput(BaseModel):
    query: str = Field(description="Search query terms focusing on entities, capabilities, benchmarks, or documentation")
    max_results: int = Field(default=5, ge=1, le=10, description="Maximum number of search results to retrieve")


class SearchWebTool(BaseTool):
    """
    Searches current public web sources for authoritative information relevant to the research goal.
    Returns structured results including title, URL, snippet, source domain, and relevance.
    """

    name: str = "search_web"
    description: str = (
        "Search public web sources for authoritative information, product documentation, "
        "framework capabilities, benchmarks, or recent developments."
    )
    input_schema = SearchInput
    output_schema = SearchResponse

    def __init__(self, provider: SearchProvider):
        self.provider = provider

    async def _execute(self, inputs: SearchInput) -> SearchResponse:
        # Failure injection hook for demonstration
        failure_injector.trigger_failure_if_needed(self.name)

        clean_query = inputs.query.strip()
        if not clean_query:
            raise ValueError("Query string cannot be empty.")

        response = await self.provider.search(clean_query, max_results=inputs.max_results)
        return response
