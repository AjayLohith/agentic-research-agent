import pytest
from pathlib import Path
from app.models.report import ResearchReport, ReportMetadata, KeyFinding, ExecutionSummary
from app.models.evidence import Source, Evidence, SourceType
from app.services.pdf_export import PdfExportService


def test_pdf_export_generates_valid_pdf_file(tmp_path: Path):
    pdf_path = tmp_path / "test_report.pdf"

    report = ResearchReport(
        metadata=ReportMetadata(
            goal="Analyze the current competitive landscape for AI agent frameworks",
            execution_time_seconds=15.2
        ),
        executive_summary="Stateful graph orchestration frameworks lead enterprise agent architectures in 2026.",
        methodology="Autonomous goal decomposition, multi-source external search, relevance filtering, deduplication, and grounded evidence synthesis.",
        key_points=[
            "LangGraph leads enterprise workflows requiring cyclic state and human-in-the-loop controls.",
            "CrewAI excels in role-playing agent orchestration and rapid prototyping."
        ],
        key_findings=[
            KeyFinding(
                title="Cyclic State Management Dominance",
                summary="Production systems increasingly adopt explicit state graphs over unstructured LLM loops.",
                category="Architecture",
                confidence=0.92
            )
        ],
        actionable_insights=[
            "Adopt explicit graph frameworks for mission-critical workflows with multi-step validation.",
            "Evaluate team skillsets between Python-centric async frameworks and enterprise Java."
        ],
        sources=[
            Source(
                url="https://docs.langchain.com/langgraph",
                title="LangGraph Documentation",
                source_type=SourceType.OFFICIAL_DOCS,
                authority_score=0.95
            )
        ],
        evidence=[
            Evidence(
                claim="LangGraph provides stateful multi-agent graphs",
                supporting_quote_or_excerpt="LangGraph enables stateful multi-agent graphs with cyclic execution.",
                source_url="https://docs.langchain.com/langgraph",
                confidence=0.90
            )
        ],
        execution_summary=ExecutionSummary(
            steps_planned=5,
            steps_completed=5,
            tool_calls_total=7,
            sources_considered=10,
            sources_deduplicated=2,
            items_filtered_for_irrelevance=3
        )
    )

    result_path = PdfExportService.export_report_to_pdf(report, pdf_path)
    assert result_path is not None
    assert result_path.exists()
    assert result_path.stat().st_size > 1000  # PDF should be multiple kilobytes
