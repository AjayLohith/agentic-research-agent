from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    OFFICIAL_DOCS = "official documentation"
    OFFICIAL_PAGE = "official company page"
    OFFICIAL_API = "official API/documentation"
    ACADEMIC_GOV = "government/academic source"
    REPUTABLE_PUB = "reputable publication"
    COMMUNITY = "community source"
    UNKNOWN = "unknown"


class Source(BaseModel):
    url: str
    title: str
    source_type: SourceType = SourceType.UNKNOWN
    authority_score: float = Field(default=0.5, ge=0.0, le=1.0)
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConfidenceBreakdown(BaseModel):
    source_authority: float = Field(ge=0.0, le=1.0, description="Weight based on verified domain type")
    evidence_directness: float = Field(ge=0.0, le=1.0, description="Direct quote vs secondary reference")
    independent_sources: float = Field(ge=0.0, le=1.0, description="Corroboration across distinct domains")
    conflict_penalty: float = Field(default=0.0, ge=0.0, le=1.0, description="Deduction for unresolved discrepancies")
    overall: float = Field(ge=0.0, le=1.0, description="Final calculated confidence")


class Evidence(BaseModel):
    id: Optional[str] = None
    claim: str = Field(description="Factual claim or assertion")
    supporting_quote_or_excerpt: str = Field(description="Direct verifiable textual excerpt from source")
    source_url: str = Field(description="Exact URL where evidence was found")
    source_title: str = Field(default="", description="Title of the source")
    source_type: SourceType = Field(default=SourceType.UNKNOWN)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    confidence_factors: Optional[ConfidenceBreakdown] = None
    entity_name: Optional[str] = Field(default=None, description="Related entity or product name")


class ConflictRecord(BaseModel):
    topic: str = Field(description="The topic or metric where disagreement occurs")
    source_a_claim: str
    source_a_url: str
    source_b_claim: str
    source_b_url: str
    resolution: str = Field(description="Methodological rationale for selecting or weighting one source")
    resolved_claim: str = Field(description="Synthesized consensus or preserved uncertainty statement")
    confidence_penalty: float = Field(default=0.1, description="Deduction applied to confidence score")
