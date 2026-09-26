import pytest
from app.tools.failure_injector import FailureInjector
from app.tools.fetch import FetchUrlTool
from app.agent.replanner import AutonomousReplanner
from app.agent.state import AgentState
from app.models.plan import PlanStep, PlanStepStatus
from app.models.tool import ToolExecutionResult
from app.providers.llm import MockLLMProvider


@pytest.mark.asyncio
async def test_failure_injector_fails_once_then_resets():
    injector = FailureInjector(mode="timeout")
    assert injector.should_fail("fetch_url") is True
    # Second check should return False because it already failed once
    assert injector.should_fail("fetch_url") is False

    # Reset
    injector.set_mode("none")
    assert injector.should_fail("fetch_url") is False


@pytest.mark.asyncio
async def test_replanner_retries_under_threshold():
    llm = MockLLMProvider()
    replanner = AutonomousReplanner(llm_provider=llm, max_retries_per_tool=2)
    state = AgentState(goal="Test failure recovery")

    step = PlanStep(
        id=1,
        description="Fetch primary docs",
        purpose="Testing",
        expected_output="Evidence",
        preferred_tools=["fetch_url"]
    )
    failed_result = ToolExecutionResult(
        tool_name="fetch_url",
        success=False,
        error="Simulated HTTP connection timeout"
    )

    # First failure -> retry 1
    decision1 = await replanner.evaluate_failure(state, step, failed_result)
    assert decision1.suggested_action == "retry"
    assert decision1.needs_replanning is False
    assert state.get_retry_count("1:fetch_url") == 1

    # Second failure -> retry 2
    decision2 = await replanner.evaluate_failure(state, step, failed_result)
    assert decision2.suggested_action == "retry"
    assert decision2.needs_replanning is False
    assert state.get_retry_count("1:fetch_url") == 2

    # Third failure -> max retries exceeded -> alternative source / replan!
    decision3 = await replanner.evaluate_failure(state, step, failed_result)
    assert decision3.suggested_action in ["alternative_source", "skip"]
    assert decision3.needs_replanning is True
