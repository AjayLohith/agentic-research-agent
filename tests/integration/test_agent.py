import pytest
from app.main import create_agent
from app.agent.state import AgentState


@pytest.mark.asyncio
async def test_agent_graph_full_execution_mock():
    graph = create_agent(mock_mode=True, demo_failure_mode="none")
    goal = "Analyze the competitive landscape for AI agent frameworks."

    state = await graph.run(goal=goal)

    assert state.status == "completed"
    assert state.plan is not None
    assert len(state.plan.steps) >= 3
    assert len(state.completed_steps) >= 3
    assert len(state.sources) >= 1
    assert len(state.evidence) >= 1
    assert state.final_report is not None
    assert len(state.final_report.key_findings) >= 1
    assert len(state.final_report.entities) >= 1


@pytest.mark.asyncio
async def test_agent_graph_failure_recovery_flow():
    # Inject intentional timeout on first fetch
    graph = create_agent(mock_mode=True, demo_failure_mode="timeout")
    goal = "Analyze AI agent frameworks with simulated failure recovery."

    state = await graph.run(goal=goal)

    assert state.status == "completed"
    # Verify a failure was logged and recovered
    assert len(state.failures) >= 1
    assert any("fetch_url" in f["tool"] for f in state.failures)
    # The final report should still succeed and be generated!
    assert state.final_report is not None
    assert state.final_report.execution_summary.failures_detected >= 1
    assert state.final_report.execution_summary.recoveries_performed >= 1


@pytest.mark.asyncio
async def test_agent_graph_loop_detection():
    state = AgentState(goal="Loop detection test")
    # Simulate calling the same search 3 times
    for _ in range(3):
        from app.models.tool import ToolExecutionResult
        state.tool_history.append(
            ToolExecutionResult(tool_name="search_web", success=True, data={"query": "repeated query"})
        )

    assert state.is_repeated_action("search_web", {"query": "repeated query"}) is True
    assert state.is_repeated_action("calculator", {"expression": "1 + 1"}) is False
