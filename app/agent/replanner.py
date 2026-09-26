import logging
from typing import Optional, List
from app.models.plan import ReplanningDecision, PlanStep, PlanStepStatus
from app.models.tool import ToolExecutionResult
from app.providers.llm import LLMProvider
from app.agent.prompts import REPLANNING_SYSTEM_PROMPT, REPLANNING_USER_PROMPT
from app.agent.state import AgentState

logger = logging.getLogger("agentic_research.replanner")


class AutonomousReplanner:
    """
    Handles failure recovery, anomaly mitigation, and adaptive plan revision.
    When a tool fails or an information gap is detected, decides whether to retry,
    fallback to alternative sources, adjust queries, or inject new plan steps.
    """

    def __init__(self, llm_provider: LLMProvider, max_retries_per_tool: int = 2):
        self.llm = llm_provider
        self.max_retries = max_retries_per_tool

    async def evaluate_failure(
        self,
        state: AgentState,
        step: PlanStep,
        failed_result: ToolExecutionResult
    ) -> ReplanningDecision:
        tool_name = failed_result.tool_name
        error_msg = failed_result.error or "Unknown tool execution failure"
        retry_key = f"{step.id}:{tool_name}"
        current_retries = state.get_retry_count(retry_key)

        logger.warning(
            f"Evaluating failure on step {step.id} ({tool_name}): '{error_msg}' (Attempt {current_retries}/{self.max_retries})"
        )

        # 1. Deterministic immediate retry check
        if current_retries < self.max_retries:
            state.increment_retry(retry_key)
            logger.info(f"Issuing immediate retry {current_retries + 1}/{self.max_retries} for tool '{tool_name}'")
            return ReplanningDecision(
                needs_replanning=False,
                reason=f"Transient tool error in {tool_name}. Executing retry attempt {current_retries + 1}/{self.max_retries}.",
                suggested_action="retry",
                new_steps=[]
            )

        # 2. Max retries exceeded: Call LLM replanner for autonomous recovery strategy
        sources_summary = "\n".join([f"- {s.title} ({s.url})" for s in state.sources[:5]]) or "None yet discovered"

        prompt = REPLANNING_USER_PROMPT.format(
            goal=state.goal,
            step_id=step.id,
            step_description=step.description,
            tool_name=tool_name,
            error_message=error_msg,
            retry_count=current_retries,
            max_retries=self.max_retries,
            sources=sources_summary
        )

        try:
            decision = await self.llm.structured_output(
                schema=ReplanningDecision,
                prompt=prompt,
                system_prompt=REPLANNING_SYSTEM_PROMPT
            )
        except Exception as e:
            logger.error(f"Error invoking LLM replanner, using rule-based fallback recovery: {e}")
            # Robust fallback recovery logic
            if tool_name == "fetch_url":
                fallback_step = PlanStep(
                    id=len(state.completed_steps) + len(state.pending_steps) + 1,
                    description=f"Search for alternative mirror or documentation regarding {step.description}",
                    purpose="Recover from unreachable primary URL by finding secondary authoritative source",
                    expected_output="Alternative verified URL and extracted content",
                    preferred_tools=["search_web", "fetch_url"],
                    status=PlanStepStatus.PENDING
                )
                decision = ReplanningDecision(
                    needs_replanning=True,
                    reason=f"Primary URL fetch failed after {current_retries} retries. Switching to alternative search.",
                    suggested_action="alternative_source",
                    new_steps=[fallback_step]
                )
            else:
                decision = ReplanningDecision(
                    needs_replanning=True,
                    reason=f"Tool {tool_name} failed. Continuing with existing evidence.",
                    suggested_action="skip",
                    new_steps=[]
                )

        logger.info(
            f"Replanning decision: Action='{decision.suggested_action}', Reason='{decision.reason}', New steps={len(decision.new_steps)}"
        )
        return decision
