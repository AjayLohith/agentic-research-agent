import pytest
from app.tools.search import SearchWebTool
from app.tools.fetch import FetchUrlTool
from app.providers.search import MockSearchProvider


@pytest.fixture
def search_tool():
    return SearchWebTool(provider=MockSearchProvider())


@pytest.fixture
def fetch_tool():
    return FetchUrlTool(max_content_length=500, mock_mode=True)


@pytest.mark.asyncio
async def test_search_web_valid_query(search_tool):
    res = await search_tool.run(query="AI agent frameworks", max_results=3)
    assert res.success is True
    assert "results" in res.data
    assert len(res.data["results"]) == 3
    assert res.data["results"][0]["url"].startswith("http")


@pytest.mark.asyncio
async def test_search_web_empty_query(search_tool):
    res = await search_tool.run(query="   ")
    assert res.success is False
    assert "empty" in res.error.lower()


@pytest.mark.asyncio
async def test_fetch_url_valid_mock(fetch_tool):
    res = await fetch_tool.run(url="https://docs.langchain.com/langgraph/overview")
    assert res.success is True
    assert res.data["status_code"] == 200
    assert "LangGraph" in res.data["title"]
    assert len(res.data["content"]) > 0


@pytest.mark.asyncio
async def test_fetch_url_invalid_protocol(fetch_tool):
    res = await fetch_tool.run(url="ftp://files.example.com")
    assert res.success is False
    assert "protocol" in res.error.lower()


@pytest.mark.asyncio
async def test_fetch_url_length_truncation():
    tool = FetchUrlTool(max_content_length=80, mock_mode=True)
    res = await tool.run(url="https://docs.crewai.com/introduction")
    assert res.success is True
    assert "[TRUNCATED" in res.data["content"]


@pytest.mark.asyncio
async def test_search_provider_in_memory_caching(search_tool):
    # First search
    res1 = await search_tool.run(query="caching test query", max_results=2)
    assert res1.success is True

    # Provider cache should now have the entry
    provider = search_tool.provider
    key = provider._normalize_key("caching test query", 2)
    assert key in provider._cache

    # Second search should return cached object without reprocessing
    res2 = await search_tool.run(query="caching test query", max_results=2)
    assert res2.success is True
    assert res2.data["results"] == res1.data["results"]
