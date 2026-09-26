from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.models.evidence import Evidence, Source, ConflictRecord, ConfidenceBreakdown


class ReportMetadata(BaseModel):
    goal: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_time_seconds: float = 0.0
    agent_version: str = "0.1.0"


class KeyFinding(BaseModel):
    title: str
    summary: str
    category: str = Field(default="general", description="e.g. Architecture, Maturity, Market Share")
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class EntityAnalysis(BaseModel):
    name: str
    category: str = "Framework/Platform"
    description: str
    key_capabilities: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    authoritative_source_url: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class ComparisonDimension(BaseModel):
    dimension: str = Field(description="e.g. Ecosystem Maturity, Multi-agent Support, Latency")
    analysis: str = Field(description="Synthesized comparative overview across entities")
    entity_ratings_or_notes: Dict[str, str] = Field(default_factory=dict)


class CalculationRecord(BaseModel):
    description: str
    expression: str
    result: float
    interpretation: str


class LimitationRecord(BaseModel):
    factor: str
    impact: str
    mitigation_or_note: str


class ExecutionSummary(BaseModel):
    steps_planned: int = 0
    steps_completed: int = 0
    tool_calls_total: int = 0
    search_queries_executed: int = 0
    pages_fetched: int = 0
    calculations_performed: int = 0
    failures_detected: int = 0
    recoveries_performed: int = 0
    loop_detections_triggered: int = 0


class ResearchReport(BaseModel):
    metadata: ReportMetadata
    executive_summary: str
    research_scope: Dict[str, Any] = Field(default_factory=dict)
    key_findings: List[KeyFinding] = Field(default_factory=list)
    entities: List[EntityAnalysis] = Field(default_factory=list)
    comparison: List[ComparisonDimension] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    calculations: List[CalculationRecord] = Field(default_factory=list)
    conflicts: List[ConflictRecord] = Field(default_factory=list)
    limitations: List[LimitationRecord] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)
    execution_summary: ExecutionSummary
    confidence_summary: Dict[str, Any] = Field(default_factory=dict)
