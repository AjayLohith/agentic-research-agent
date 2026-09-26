import pytest
from app.main import ResearchAgent
from app.agent.state import AgentState
from app.services.search_memory import SearchMemoryStore


@pytest.mark.asyncio
async def test_query_independence_different_plans_and_queries():
    """
    Verifies Section 8 requirement:
    Different goals must yield different plans, search queries, and source sets.
    """
    agent = ResearchAgent(mock_mode=True)

    goal_a = "Compare FastAPI and Spring Boot for production microservices"
    goal_b = "Research the current landscape of AI agent frameworks"

    state_a = await agent.run(goal=goal_a)
    state_b = await agent.run(goal=goal_b)

    # 1. Plans must differ
    assert state_a.plan.objective != state_b.plan.objective
    assert "FastAPI" in state_a.plan.objective or "microservices" in state_a.plan.objective
    assert "agent" in state_b.plan.objective.lower() or "frameworks" in state_b.plan.objective.lower()

    # 2. Search queries must differ
    queries_a = [
        th.data.get("query")
        for th in state_a.tool_history
        if th.tool_name == "search_web" and isinstance(th.data, dict)
    ]
    queries_b = [
        th.data.get("query")
        for th in state_b.tool_history
        if th.tool_name == "search_web" and isinstance(th.data, dict)
    ]

    assert queries_a != queries_b
    assert any("FastAPI" in q for q in queries_a)
    assert any("LangGraph" in q or "Agent" in q for q in queries_b)

    # 3. Sources must differ
    sources_a = {s.url for s in state_a.sources}
    sources_b = {s.url for s in state_b.sources}
    assert sources_a != sources_b
    assert any("fastapi.tiangolo.com" in u for u in sources_a)

    # 4. Report A must NOT contain LangGraph, CrewAI, AutoGen
    report_a_summary = state_a.final_report.executive_summary
    assert "LangGraph" not in report_a_summary
    assert "CrewAI" not in report_a_summary
    assert "AutoGen" not in report_a_summary


@pytest.mark.asyncio
async def test_query_independence_gpt6_astra():
    """
    Verifies that 'Analyze the current GPT 6 Astra for AI agent frameworks'
    researches GPT 6 Astra and does not default to the generic agent frameworks report.
    """
    agent = ResearchAgent(mock_mode=True)
    goal = "Analyze the current GPT 6 Astra for AI agent frameworks"

    state = await agent.run(goal=goal)

    assert state.original_goal == goal
    assert "GPT 6 Astra" in state.plan.objective

    # Ensure search was for GPT 6 Astra
    queries = [
        th.data.get("query")
        for th in state.tool_history
        if th.tool_name == "search_web" and isinstance(th.data, dict)
    ]
    assert any("GPT 6 Astra" in q for q in queries)

    # Report must focus on GPT 6 Astra
    assert state.final_report.metadata.goal == goal
    assert "GPT 6 Astra" in state.final_report.executive_summary
    entity_names = [e.name for e in state.final_report.entities]
    assert "GPT 6 Astra" in entity_names


@pytest.mark.asyncio
async def test_query_contamination_across_consecutive_sessions(tmp_path):
    """
    Verifies Section 9 requirement:
    Consecutive runs (e.g. AI agent frameworks followed by PostgreSQL vs MongoDB)
    must NOT cross-contaminate state, search queries, or final report findings.
    """
    memory_file = tmp_path / "search_history.json"
    memory = SearchMemoryStore(storage_path=str(memory_file))

    agent = ResearchAgent(mock_mode=True)

    # Run 1: Agent frameworks
    goal_1 = "Analyze the current competitive landscape for AI agent frameworks"
    state_1 = await agent.run(goal=goal_1)
    memory.save_session(
        goal=state_1.goal,
        summary=state_1.final_report.executive_summary,
        key_points=state_1.final_report.key_points,
        sources=[{"url": s.url, "title": s.title} for s in state_1.sources],
        execution_time_seconds=state_1.execution_time_seconds
    )

    # Run 2: Database comparison
    goal_2 = "Compare PostgreSQL and MongoDB for backend applications"
    state_2 = await agent.run(goal=goal_2)
    memory.save_session(
        goal=state_2.goal,
        summary=state_2.final_report.executive_summary,
        key_points=state_2.final_report.key_points,
        sources=[{"url": s.url, "title": s.title} for s in state_2.sources],
        execution_time_seconds=state_2.execution_time_seconds
    )

    # Assert Session 2 has no contamination from Session 1
    assert state_2.original_goal == goal_2
    assert "PostgreSQL" in state_2.plan.objective
    assert "MongoDB" in state_2.plan.objective
    assert "LangGraph" not in state_2.plan.objective

    # Verify search queries in Session 2
    queries_2 = [
        th.data.get("query")
        for th in state_2.tool_history
        if th.tool_name == "search_web" and isinstance(th.data, dict)
    ]
    for q in queries_2:
        assert "LangGraph" not in q
        assert "CrewAI" not in q
        assert "AutoGen" not in q

    # Verify sources in Session 2
    sources_2 = [s.url for s in state_2.sources]
    assert any("postgresql.org" in u for u in sources_2)
    assert any("mongodb.com" in u for u in sources_2)
    assert not any("docs.langchain.com" in u for u in sources_2)

    # Verify final report in Session 2
    report_2 = state_2.final_report
    assert "PostgreSQL" in report_2.executive_summary
    assert "MongoDB" in report_2.executive_summary
    assert "LangGraph" not in report_2.executive_summary
    assert "CrewAI" not in report_2.executive_summary

    entity_names_2 = [e.name for e in report_2.entities]
    assert "PostgreSQL" in entity_names_2
    assert "MongoDB" in entity_names_2
    assert "LangGraph" not in entity_names_2
