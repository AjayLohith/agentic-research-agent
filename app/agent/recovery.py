import logging
from typing import Optional
from app.models.plan import ReplanningDecision, PlanStep, PlanStepStatus
from app.models.tool import ToolExecutionResult
from app.providers.llm import LLMProvider
from app.agent.prompts.replanner import REPLANNING_SYSTEM_PROMPT, REPLANNING_USER_PROMPT
from app.agent.state import AgentState

logger = logging.getLogger("agentic_research.recovery")


class AutonomousReplanner:
    """
    Evaluates execution failures and manages two-tier recovery:
    immediate transient retry, or dynamic replanning to alternative sources.
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
        error_msg = failed_result.error or "Unknown failure"
        retry_key = f"{step.id}:{tool_name}"
        current_retries = state.get_retry_count(retry_key)

        logger.warning(
            f"Step {step.id} failed ({tool_name}): '{error_msg}' (Attempt {current_retries}/{self.max_retries})"
        )

        # 1. Immediate retry if within retry budget
        if current_retries < self.max_retries:
            state.increment_retry(retry_key)
            logger.info(f"Retrying {tool_name} (Attempt {current_retries + 1}/{self.max_retries})")
            return ReplanningDecision(
                needs_replanning=False,
                reason=f"Transient failure in {tool_name}. Executing retry {current_retries + 1}/{self.max_retries}.",
                suggested_action="retry",
                new_steps=[]
            )

        # 2. Budget exceeded: Consult LLM replanner
        sources_summary = "\n".join([f"- {s.title} ({s.url})" for s in state.sources[:5]]) or "None discovered"

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
            return await self.llm.structured_output(
                schema=ReplanningDecision,
                prompt=prompt,
                system_prompt=REPLANNING_SYSTEM_PROMPT
            )
        except Exception as e:
            logger.error(f"Replanner invocation failed: {e}. Falling back to rule-based recovery.")
            if tool_name == "fetch_url":
                fallback_step = PlanStep(
                    id=len(state.completed_steps) + len(state.pending_steps) + 1,
                    description=f"Search for alternative source regarding {step.description}",
                    purpose="Recover from unreachable primary URL by finding an alternative reference",
                    expected_output="Alternative verified URL and extracted content",
                    preferred_tools=["search_web", "fetch_url"],
                    status=PlanStepStatus.PENDING
                )
                return ReplanningDecision(
                    needs_replanning=True,
                    reason=f"URL fetch failed after {current_retries} retries. Switching to alternative search.",
                    suggested_action="alternative_source",
                    new_steps=[fallback_step]
                )

            return ReplanningDecision(
                needs_replanning=True,
                reason=f"Tool {tool_name} failed. Continuing with existing evidence.",
                suggested_action="skip",
                new_steps=[]
            )
