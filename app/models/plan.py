from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    id: int = Field(description="Sequential step index starting from 1")
    description: str = Field(description="Actionable description of the planned task")
    purpose: str = Field(description="Reason for task and how it advances the research objective")
    expected_output: str = Field(description="Concrete expected data or finding from this step")
    preferred_tools: List[str] = Field(default_factory=list, description="Recommended tools e.g. ['search_web', 'fetch_url']")
    status: PlanStepStatus = Field(default=PlanStepStatus.PENDING)
    result_summary: Optional[str] = Field(default=None, description="Summary of step execution outcome")


class ResearchPlan(BaseModel):
    objective: str = Field(description="Decomposed understanding of the user research goal")
    assumptions: List[str] = Field(default_factory=list, description="Core assumptions made prior to execution")
    constraints: List[str] = Field(default_factory=list, description="Scope boundaries or domain constraints")
    steps: List[PlanStep] = Field(default_factory=list, description="Ordered execution steps")


class ReplanningDecision(BaseModel):
    needs_replanning: bool = Field(description="True if an unexpected failure or information gap requires plan adjustment")
    reason: str = Field(description="Objective justification for replanning or continuing")
    suggested_action: str = Field(description="Action to take: 'retry', 'alternative_source', 'adjust_query', 'skip', 'complete'")
    new_steps: List[PlanStep] = Field(default_factory=list, description="Any new steps to append or replace")
    step_id_to_modify: Optional[int] = Field(default=None, description="ID of step being modified")
