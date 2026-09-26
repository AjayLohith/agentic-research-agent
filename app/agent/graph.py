import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.agent.state import AgentState
from app.models.plan import PlanStepStatus, PlanStep
from app.models.report import ResearchReport
from app.agent.planner import AutonomousPlanner
from app.agent.executor import AutonomousExecutor
from app.agent.replanner import AutonomousReplanner
from app.agent.synthesizer import AutonomousSynthesizer
from app.services.evidence_service import EvidenceService

logger = logging.getLogger("agentic_research.graph")


class ResearchAgentGraph:
    """
    State Graph orchestrator for the Autonomous Research & Competitive Intelligence Agent.
    Implements explicit state transitions:
    GOAL -> VALIDATE -> PLAN -> EXECUTION LOOP (SELECT -> EXECUTE -> OBSERVE -> EVALUATE / REPLAN) -> EVIDENCE VALIDATION -> SYNTHESIS -> STRUCTURED REPORT.
    """

    def __init__(
        self,
        planner: AutonomousPlanner,
        executor: AutonomousExecutor,
        replanner: AutonomousReplanner,
        synthesizer: AutonomousSynthesizer,
        max_agent_steps: int = 15,
        max_research_time_seconds: int = 300
    ):
        self.planner = planner
        self.executor = executor
        self.replanner = replanner
        self.synthesizer = synthesizer
        self.max_agent_steps = max_agent_steps
        self.max_research_time_seconds = max_research_time_seconds

    async def run(self, goal: str, constraints: Optional[list] = None) -> AgentState:
        """Executes the full agent graph loop until completion or terminal boundary."""
        start_time = time.perf_counter()
        state = AgentState(
            goal=goal,
            original_goal=goal,
            constraints=constraints or [],
            status="planning"
        )
        logger.info(f"[GRAPH TRANSITION] Starting execution for goal: '{goal}'")

        # 1. NODE: PLANNER
        state.plan = await self.planner.plan(goal, constraints)
        state.interpreted_objective = state.plan.objective if state.plan else goal
        state.pending_steps = list(state.plan.steps)
        state.status = "executing"

        # Query-specific observability logging (Section 15)
        logger.info(f"Original Goal: '{state.original_goal}'")
        logger.info(f"Interpreted Objective: '{state.interpreted_objective}'")
        logger.info(f"Autonomous Source Strategy: '{state.plan.source_strategy}'")
        logger.info(f"Target Source Types: {state.plan.target_source_types}")

        step_cycle = 0

        # 2. EXECUTION LOOP
        while state.pending_steps and step_cycle < self.max_agent_steps:
            elapsed = time.perf_counter() - start_time
            if elapsed > self.max_research_time_seconds:
                logger.warning(f"Research time limit reached ({self.max_research_time_seconds}s). Halting execution loop.")
                break

            step_cycle += 1
            current_step = state.pending_steps.pop(0)
            state.current_step = current_step
            current_step.status = PlanStepStatus.IN_PROGRESS
            logger.info(f"[CYCLE {step_cycle}] Executing Step {current_step.id}: {current_step.description}")

            # 2a. SELECT ACTION & EXECUTE
            tool_call = await self.executor.select_action(state, current_step)
            result = await self.executor.execute_tool(tool_call, state)

            # 2b. OBSERVE & EVALUATE
            if result.success:
                current_step.status = PlanStepStatus.COMPLETED
                current_step.result_summary = f"Executed {tool_call.tool_name} successfully."
                state.completed_steps.append(current_step)
                logger.info(f"Step {current_step.id} completed successfully.")
            else:
                # Failure Detected -> Recovery & Replanning
                logger.warning(f"Failure detected on step {current_step.id}. Initiating replanning node.")
                state.status = "recovering"
                replanning_decision = await self.replanner.evaluate_failure(state, current_step, result)

                if replanning_decision.suggested_action == "retry":
                    logger.info(f"Retrying step {current_step.id} (Action: retry).")
                    current_step.status = PlanStepStatus.PENDING
                    state.pending_steps.insert(0, current_step)

                elif replanning_decision.suggested_action == "alternative_source":
                    logger.info(f"Adding alternative recovery steps from replanner ({len(replanning_decision.new_steps)} steps).")
                    current_step.status = PlanStepStatus.FAILED
                    state.completed_steps.append(current_step)
                    # Prepend new recovery steps
                    for new_step in reversed(replanning_decision.new_steps):
                        state.pending_steps.insert(0, new_step)

                else:
                    # Skip or Complete
                    logger.info(f"Replanner decided to skip or terminate step: {replanning_decision.reason}")
                    current_step.status = PlanStepStatus.SKIPPED
                    state.completed_steps.append(current_step)

                state.status = "executing"

        # 3. NODE: EVIDENCE VALIDATION
        state.status = "validating_evidence"
        is_valid, issues = EvidenceService.validate_coverage(state.evidence)
        if not is_valid:
            logger.warning(f"Evidence coverage check noted issues: {issues}")
        else:
            logger.info(f"Evidence coverage validated successfully: {len(state.evidence)} grounded items.")

        # 4. NODE: SYNTHESIS
        state.status = "synthesizing"
        state.execution_time_seconds = time.perf_counter() - start_time
        report = await self.synthesizer.synthesize(state)
        state.final_report = report
        state.status = "completed"
        logger.info(f"[GRAPH COMPLETE] Research completed in {state.execution_time_seconds:.2f}s.")

        return state
