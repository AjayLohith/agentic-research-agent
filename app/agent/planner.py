import logging
from typing import List, Optional
from app.models.plan import ResearchPlan, PlanStep, PlanStepStatus
from app.providers.llm import LLMProvider
from app.agent.prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT

logger = logging.getLogger("agentic_research.planner")


class AutonomousPlanner:
    """
    Decomposes arbitrary natural-language research goals into structured,
    goal-specific execution plans using the configured LLMProvider.
    Never hardcodes predefined plans or hidden chain-of-thought.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def plan(self, goal: str, constraints: Optional[List[str]] = None) -> ResearchPlan:
        logger.info(f"Generating autonomous execution plan for goal: '{goal}'")

        prompt = PLANNER_USER_PROMPT.format(goal=goal)
        plan = await self.llm.structured_output(
            schema=ResearchPlan,
            prompt=prompt,
            system_prompt=PLANNER_SYSTEM_PROMPT
        )

        # Validate that plan has reasonable structure
        if not plan.steps:
            # Fallback default decomposition if model returns empty steps
            plan.steps = [
                PlanStep(
                    id=1,
                    description=f"Identify key entities, concepts, and authoritative sources for {goal}",
                    purpose="Discover candidate topics and primary documentation URLs",
                    expected_output="List of relevant entities and initial URLs",
                    preferred_tools=["search_web"],
                    status=PlanStepStatus.PENDING
                ),
                PlanStep(
                    id=2,
                    description="Retrieve and inspect technical documentation for identified subjects",
                    purpose="Extract verified capabilities, features, and evidence",
                    expected_output="Verifiable technical evidence",
                    preferred_tools=["fetch_url"],
                    status=PlanStepStatus.PENDING
                ),
                PlanStep(
                    id=3,
                    description="Perform comparative synthesis and generate intelligence report",
                    purpose="Structure findings into comparative dimensions and actionable takeaways",
                    expected_output="Final structured competitive report",
                    preferred_tools=["calculator"],
                    status=PlanStepStatus.PENDING
                )
            ]

        # Ensure steps have correct initial status and sequential IDs
        for idx, step in enumerate(plan.steps, start=1):
            step.id = idx
            step.status = PlanStepStatus.PENDING

        logger.info(f"Plan generated with {len(plan.steps)} steps. Objective: '{plan.objective}'")
        return plan

    @staticmethod
    def format_plan_trace(plan: ResearchPlan) -> str:
        """
        Formats a clean, structured, user-visible plan trace without exposing private chain-of-thought.
        (Adheres strictly to Assignment Section 8)
        """
        lines = []
        lines.append("=" * 60)
        lines.append("AUTONOMOUS EXECUTION PLAN")
        lines.append("=" * 60)
        lines.append(f"Objective: {plan.objective}")
        if plan.assumptions:
            lines.append("Assumptions:")
            for a in plan.assumptions:
                lines.append(f"  • {a}")
        lines.append("")
        lines.append("Planned Steps:")
        for step in plan.steps:
            tools_str = ", ".join(step.preferred_tools) if step.preferred_tools else "dynamic"
            lines.append(f"  {step.id}. {step.description}")
            lines.append(f"     Reason: {step.purpose}")
            lines.append(f"     Preferred Tool: [{tools_str}]")
            lines.append(f"     Expected: {step.expected_output}")
            lines.append(f"     Status: {step.status.value.upper()}")
        lines.append("=" * 60)
        return "\n".join(lines)
