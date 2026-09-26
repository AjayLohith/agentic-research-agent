import json
import pytest
from pathlib import Path
from app.services.search_memory import SearchMemoryStore


def test_search_memory_save_and_lookup(tmp_path: Path):
    mem_file = tmp_path / "search_history.json"
    memory = SearchMemoryStore(storage_path=str(mem_file))

    memory.save_session(
        goal="Compare FastAPI and Spring Boot for microservices",
        summary="FastAPI provides async developer velocity while Spring Boot provides enterprise Java stability.",
        key_points=["FastAPI is async-first", "Spring Boot has mature enterprise governance"],
        sources=[{"url": "https://fastapi.tiangolo.com", "title": "FastAPI"}],
        execution_time_seconds=12.4
    )

    # Exact or near-match lookup
    match = memory.lookup_previous_research("FastAPI and Spring Boot comparison", min_similarity=0.40)
    assert match is not None
    assert "FastAPI" in match["summary"]
    assert match["execution_time_seconds"] == 12.4

    # Unrelated lookup returns None
    unrelated = memory.lookup_previous_research("Autonomous electric vehicles battery chemistry", min_similarity=0.50)
    assert unrelated is None


def test_search_memory_lists_recent_sessions(tmp_path: Path):
    mem_file = tmp_path / "search_history.json"
    memory = SearchMemoryStore(storage_path=str(mem_file))

    memory.save_session(goal="Goal 1", summary="Sum 1", key_points=[], sources=[])
    memory.save_session(goal="Goal 2", summary="Sum 2", key_points=[], sources=[])

    recent = memory.list_recent_sessions(limit=5)
    assert len(recent) == 2
    assert recent[0]["goal"] == "Goal 2"
