import pytest
from app.models.plan import PlanStep, ResearchPlan, PlanStepStatus
from app.models.evidence import Evidence, Source, SourceType, ConfidenceBreakdown
from app.models.report import (
    ResearchReport,
    ReportMetadata,
    KeyFinding,
    EntityAnalysis,
    ComparisonDimension,
    ExecutionSummary
)
from app.services.source_service import SourceClassificationService
from app.services.evidence_service import EvidenceService


def test_source_classification():
    # Official docs
    s1 = SourceClassificationService.classify_url("https://docs.langchain.com/langgraph")
    assert s1 == SourceType.OFFICIAL_DOCS

    # Academic
    s2 = SourceClassificationService.classify_url("https://arxiv.org/abs/2308.08155")
    assert s2 == SourceType.ACADEMIC_GOV

    # Reputable publication
    s3 = SourceClassificationService.classify_url("https://techcrunch.com/2026/article")
    assert s3 == SourceType.REPUTABLE_PUB

    # Community
    s4 = SourceClassificationService.classify_url("https://reddit.com/r/MachineLearning")
    assert s4 == SourceType.COMMUNITY


def test_confidence_breakdown_calculation():
    breakdown = EvidenceService.calculate_confidence(
        source_type=SourceType.OFFICIAL_DOCS,
        is_direct_quote=True,
        corroborating_domains_count=3,
        has_conflict=False
    )
    assert breakdown.source_authority == 0.95
    assert breakdown.evidence_directness == 0.95
    assert breakdown.independent_sources == 0.95
    assert breakdown.conflict_penalty == 0.0
    assert breakdown.overall >= 0.90


def test_research_report_serialization():
    report = ResearchReport(
        metadata=ReportMetadata(goal="Unit test goal", execution_time_seconds=1.5),
        executive_summary="Summary of test",
        research_scope={"assumptions": ["test assumption"]},
        key_findings=[
            KeyFinding(
                title="Finding 1",
                summary="Detail 1",
                category="General",
                supporting_evidence_ids=["ev-1"],
                confidence=0.9
            )
        ],
        entities=[
            EntityAnalysis(
                name="FrameworkX",
                description="Test framework",
                key_capabilities=["Cap1"],
                strengths=["Str1"],
                tradeoffs=["Trade1"],
                authoritative_source_url="https://docs.example.org",
                confidence=0.92
            )
        ],
        comparison=[
            ComparisonDimension(
                dimension="Perf",
                analysis="Good",
                entity_ratings_or_notes={"FrameworkX": "Fast"}
            )
        ],
        evidence=[],
        calculations=[],
        conflicts=[],
        limitations=[],
        sources=[
            Source(
                url="https://docs.example.org",
                title="Test Source",
                source_type=SourceType.OFFICIAL_DOCS,
                authority_score=0.95
            )
        ],
        execution_summary=ExecutionSummary(steps_planned=1, steps_completed=1),
        confidence_summary={"overall": "90%"}
    )

    json_str = report.model_dump_json()
    assert "FrameworkX" in json_str

    # Deserialization test
    parsed = ResearchReport.model_validate_json(json_str)
    assert parsed.metadata.goal == "Unit test goal"
    assert len(parsed.entities) == 1


def test_report_service_markdown_generation(tmp_path):
    from app.services.report_service import ReportService
    from app.models.report import KeyFinding, EntityAnalysis, ComparisonDimension, ExecutionSummary

    report = ResearchReport(
        metadata=ReportMetadata(goal="Markdown generation test", execution_time_seconds=2.0),
        executive_summary="Executive summary test text.",
        research_scope={"assumptions": ["Assumption 1"], "constraints": ["Constraint 1"]},
        key_findings=[
            KeyFinding(
                title="Finding Title",
                summary="Finding Summary",
                category="Performance",
                supporting_evidence_ids=["ev-1"],
                confidence=0.95
            )
        ],
        entities=[
            EntityAnalysis(
                name="TestEntity",
                category="Platform",
                description="Entity description.",
                key_capabilities=["Cap A", "Cap B"],
                strengths=["Strength A"],
                tradeoffs=["Tradeoff A"],
                authoritative_source_url="https://docs.test.org",
                confidence=0.9
            )
        ],
        comparison=[
            ComparisonDimension(
                dimension="Throughput",
                analysis="Analysis text",
                entity_ratings_or_notes={"TestEntity": "High"}
            )
        ],
        evidence=[],
        calculations=[],
        conflicts=[],
        limitations=[],
        sources=[
            Source(
                url="https://docs.test.org",
                title="Test Source",
                source_type=SourceType.OFFICIAL_DOCS,
                authority_score=0.95
            )
        ],
        execution_summary=ExecutionSummary(
            steps_planned=2,
            steps_completed=2,
            tool_calls_total=3
        ),
        confidence_summary={"overall_confidence": "92%"}
    )

    md = ReportService.generate_markdown(report)
    assert "# Autonomous Research & Competitive Intelligence Report" in md
    assert "TestEntity" in md
    assert "Executive summary test text." in md

    paths = ReportService.save_reports(report, tmp_path)
    assert paths["json"].exists()
    assert paths["markdown"].exists()


def test_config_validation_raises_when_keys_missing():
    from app.config import Settings
    from app.exceptions import ConfigurationError

    # Groq selected without key
    cfg1 = Settings(LLM_PROVIDER="groq", GROQ_API_KEY=None, MOCK_MODE=False)
    with pytest.raises(ConfigurationError) as exc1:
        cfg1.validate_runtime(is_mock=False)
    assert "GROQ_API_KEY" in str(exc1.value)

    # Tavily selected without key
    cfg2 = Settings(LLM_PROVIDER="groq", GROQ_API_KEY="test-key", SEARCH_PROVIDER="tavily", TAVILY_API_KEY=None, MOCK_MODE=False)
    with pytest.raises(ConfigurationError) as exc2:
        cfg2.validate_runtime(is_mock=False)
    assert "TAVILY_API_KEY" in str(exc2.value)


def test_groq_provider_json_extraction():
    from app.providers.llm.groq import GroqProvider

    provider = GroqProvider(api_key="dummy")

    # Clean JSON
    res1 = provider._extract_json('{"key": "value"}')
    assert res1 == {"key": "value"}

    # Markdown fenced JSON
    res2 = provider._extract_json('```json\n{"status": "ok", "count": 5}\n```')
    assert res2 == {"status": "ok", "count": 5}

    # Text preamble and postamble surrounding JSON
    res3 = provider._extract_json('Here is the requested output:\n{"data": [1, 2, 3]}\nHope this helps!')
    assert res3 == {"data": [1, 2, 3]}
