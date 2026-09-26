from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.models.plan import PlanStep, ResearchPlan, PlanStepStatus
from app.models.evidence import Evidence, Source
from app.models.tool import ToolExecutionResult
from app.models.report import ResearchReport, CalculationRecord


class AgentState(BaseModel):
    """
    Complete state representation of the autonomous research agent throughout an execution run.
    Maintains all observations, evidence, plans, execution traces, and recovery attempts.
    """

    goal: str = Field(description="The original user-specified research goal")
    constraints: List[str] = Field(default_factory=list, description="Operational boundaries or constraints")
    plan: Optional[ResearchPlan] = Field(default=None, description="Current decomposed research plan")
    current_step: Optional[PlanStep] = Field(default=None, description="Currently active execution step")
    completed_steps: List[PlanStep] = Field(default_factory=list, description="Steps successfully executed")
    pending_steps: List[PlanStep] = Field(default_factory=list, description="Steps queued for execution")

    observations: List[Dict[str, Any]] = Field(default_factory=list, description="Chronological log of tool observations")
    sources: List[Source] = Field(default_factory=list, description="Discovered web sources with authority classifications")
    evidence: List[Evidence] = Field(default_factory=list, description="Extracted factual evidence items")
    tool_history: List[ToolExecutionResult] = Field(default_factory=list, description="Full audit history of tool executions")
    calculations: List[CalculationRecord] = Field(default_factory=list, description="Mathematical calculations performed")

    failures: List[Dict[str, Any]] = Field(default_factory=list, description="Encountered tool or network failures")
    retries: Dict[str, int] = Field(default_factory=dict, description="Retry attempt counters keyed by tool/action")
    intermediate_findings: List[str] = Field(default_factory=list, description="Working deductions and verified facts")

    final_report: Optional[ResearchReport] = Field(default=None, description="Final synthesized research report")
    status: str = Field(default="initialized", description="Current agent status: initialized, planning, executing, recovering, synthesizing, completed, failed")

    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_time_seconds: float = 0.0

    # Filtering & Deduplication Metrics
    sources_considered: int = 0
    sources_deduplicated: int = 0
    items_filtered_for_irrelevance: int = 0

    def record_observation(self, tool_name: str, input_params: Any, result_summary: str):
        self.observations.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step_id": self.current_step.id if self.current_step else 0,
            "tool": tool_name,
            "input": input_params,
            "observation": result_summary
        })

    def record_failure(self, tool_name: str, error: str, step_id: Optional[int] = None):
        self.failures.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step_id": step_id or (self.current_step.id if self.current_step else 0),
            "tool": tool_name,
            "error": error
        })

    def increment_retry(self, key: str) -> int:
        count = self.retries.get(key, 0) + 1
        self.retries[key] = count
        return count

    def get_retry_count(self, key: str) -> int:
        return self.retries.get(key, 0)

    def add_source(self, source: Source):
        from app.services.deduplication import DeduplicationService
        self.sources_considered += 1
        norm_url = DeduplicationService.normalize_url(source.url)
        source.url = norm_url

        existing_urls = {DeduplicationService.normalize_url(s.url) for s in self.sources}
        if norm_url in existing_urls:
            self.sources_deduplicated += 1
            # If new source has higher authority, replace
            for idx, existing in enumerate(self.sources):
                if DeduplicationService.normalize_url(existing.url) == norm_url:
                    if source.authority_score > existing.authority_score:
                        self.sources[idx] = source
                    break
        else:
            self.sources.append(source)

    def add_evidence(self, ev: Evidence):
        self.evidence.append(ev)

    def is_repeated_action(self, tool_name: str, arguments: Dict[str, Any], history_depth: int = 4) -> bool:
        """
        Loop detection: checks whether the exact same tool and arguments were called repeatedly.
        """
        recent = self.tool_history[-history_depth:] if self.tool_history else []
        matches = 0
        for th in recent:
            if th.tool_name == tool_name:
                matches += 1
        return matches >= 3
