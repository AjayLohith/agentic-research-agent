from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class SearchResult(BaseModel):
    title: str = Field(description="Title of the search result")
    url: str = Field(description="URL of the search result")
    snippet: str = Field(description="Summary or text snippet")
    source: str = Field(default="web", description="Domain or search source identifier")
    relevance: float = Field(default=0.8, ge=0.0, le=1.0, description="Estimated relevance score")


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult] = Field(default_factory=list)
    total_results: int = 0


class FetchResult(BaseModel):
    url: str
    status_code: int
    title: str = ""
    content: str = ""
    content_length: int = 0
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: Optional[str] = None


class CalculatorResult(BaseModel):
    expression: str
    result: float
    formatted: str = ""


class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    rationale: Optional[str] = Field(default=None, description="Objective justification for choosing this tool")


class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
